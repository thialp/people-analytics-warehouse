"""
Benchmark three ways to build a monthly headcount walk.

    python pipeline/run_pipeline.py --no-export        # build the warehouse first
    python benchmarks/benchmark_headcount_walk.py      # scale 1 and 10 (~190k workers)
    python benchmarks/benchmark_headcount_walk.py --scales 1 5 20

The question is a design one: at what grain should workforce history be stored
so that a walk (opening, hires, leavers, moves, closing) is cheap to compute and
small enough for a BI tool?

  1. Daily scaffold      one row per worker per day employed, the classic
                         "date scaffolding" pattern done in Tableau or SQL.
                         Every month-end question is answered from this table.
  2. As-of join, twice   no stored history: for every month, find each worker's
                         job record in effect at the prior AND current month-end
                         with a date-range (band) join, then compare.
  3. Snapshot, then join build one row per worker per month-end once (what
                         int_worker_month_end_snapshot does), then compare
                         consecutive months with an equality join.

Strategies 2 and 3 must return identical hires, leavers and department moves;
the script stops if they don't. Larger scales copy every worker N times with a
new ID, which multiplies volume while keeping the same shape of history.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse" / "arcadia.duckdb"
OUT = ROOT / "docs" / "projects" / "headcount-fte-walk" / "performance_results.md"
TABLEAU_PUBLIC_ROW_LIMIT = 15_000_000

WALK_COUNTS = """
SELECT
    COUNT(*) FILTER (WHERE pri.worker_id IS NULL)                     AS hires,
    COUNT(*) FILTER (WHERE cur.worker_id IS NULL)                     AS leavers,
    COUNT(*) FILTER (WHERE cur.department_id <> pri.department_id)    AS department_moves
FROM cur
FULL OUTER JOIN pri
  ON cur.month_end_date = pri.month_end_date
 AND cur.worker_id      = pri.worker_id
"""

AS_OF = """
SELECT p.{side} AS month_end_date, p.month_end_date AS walk_month, j.worker_id, j.department_id
FROM pairs AS p
JOIN w ON w.original_hire_date <= p.{side}
      AND (w.termination_date IS NULL OR w.termination_date >= p.{side})
JOIN j ON j.worker_id = w.worker_id
      AND p.{side} BETWEEN j.effective_start_date AND j.effective_end_date_filled
"""


def setup(scale: int) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect()
    con.execute(f"ATTACH '{DB_PATH.as_posix()}' AS src (READ_ONLY)")
    con.execute(f"""
        CREATE TABLE w AS
        SELECT s.r || '-' || worker_id AS worker_id, original_hire_date, termination_date
        FROM src.staging.stg_worker, range({scale}) AS s(r)""")
    con.execute(f"""
        CREATE TABLE j AS
        SELECT s.r || '-' || worker_id AS worker_id, effective_start_date, effective_end_date_filled, department_id
        FROM src.staging.stg_job_history, range({scale}) AS s(r)""")
    con.execute("CREATE TABLE cal AS SELECT month_end_date, prior_month_end_date FROM src.intermediate.int_month_end_calendar")
    con.execute("CREATE TABLE pairs AS SELECT * FROM cal WHERE prior_month_end_date IS NOT NULL")
    return con


def timed(con, sql: str):
    start = time.perf_counter()
    result = con.execute(sql).fetchall()
    return time.perf_counter() - start, result


def run(scale: int) -> list[dict]:
    con = setup(scale)
    workers = con.execute("SELECT COUNT(*) FROM w").fetchone()[0]
    rows = []

    # 1. daily scaffold: materialize one row per worker per day employed
    first_day = con.execute("SELECT MIN(month_end_date) - INTERVAL 29 DAY FROM cal").fetchone()[0]
    secs, _ = timed(con, f"""
        CREATE TABLE daily AS
        SELECT d.day, w.worker_id
        FROM (SELECT UNNEST(generate_series(DATE '{first_day:%Y-%m-%d}', (SELECT MAX(month_end_date) FROM cal),
                                            INTERVAL 1 DAY))::DATE AS day) AS d
        JOIN w ON w.original_hire_date <= d.day
              AND (w.termination_date IS NULL OR w.termination_date >= d.day)""")
    n_daily = con.execute("SELECT COUNT(*) FROM daily").fetchone()[0]
    rows.append({"strategy": "1. Daily scaffold", "rows": n_daily, "seconds": secs})
    con.execute("DROP TABLE daily")

    # 2. as-of band join for both month-ends, recomputed inside the walk query
    secs, as_of_result = timed(con, f"""
        WITH cur AS ({AS_OF.format(side='month_end_date')}),
             pri AS (SELECT walk_month AS month_end_date, worker_id, department_id
                     FROM ({AS_OF.format(side='prior_month_end_date')}))
        {WALK_COUNTS}""")
    rows.append({"strategy": "2. As-of join, twice", "rows": None, "seconds": secs})

    # 3. snapshot once (timed), then an equality join
    build_secs, _ = timed(con, f"""
        CREATE TABLE snap AS
        SELECT p.month_end_date, j.worker_id, j.department_id
        FROM cal AS p
        JOIN w ON w.original_hire_date <= p.month_end_date
              AND (w.termination_date IS NULL OR w.termination_date >= p.month_end_date)
        JOIN j ON j.worker_id = w.worker_id
              AND p.month_end_date BETWEEN j.effective_start_date AND j.effective_end_date_filled""")
    n_snap = con.execute("SELECT COUNT(*) FROM snap").fetchone()[0]
    walk_secs, snap_result = timed(con, f"""
        WITH cur AS (SELECT s.* FROM snap AS s JOIN pairs USING (month_end_date)),
             pri AS (SELECT p.month_end_date, s.worker_id, s.department_id
                     FROM snap AS s JOIN pairs AS p ON s.month_end_date = p.prior_month_end_date)
        {WALK_COUNTS}""")
    rows.append({"strategy": "3. Snapshot, then join", "rows": n_snap, "seconds": build_secs + walk_secs,
                 "build": build_secs, "walk": walk_secs})

    if as_of_result != snap_result:
        sys.exit(f"Strategies 2 and 3 disagree at scale {scale}: {as_of_result} vs {snap_result}")
    for r in rows:
        r.update(scale=scale, workers=workers, hires_leavers_moves=snap_result[0])
    con.close()
    return rows


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--scales", type=int, nargs="+", default=[1, 10])
    args = parser.parse_args()
    if not DB_PATH.exists():
        sys.exit("Build the warehouse first: python pipeline/run_pipeline.py --no-export")

    results = []
    for scale in args.scales:
        print(f"scale {scale} ...", flush=True)
        results.extend(run(scale))

    lines = [
        "# Benchmark results",
        "",
        "Generated by `benchmarks/benchmark_headcount_walk.py` on DuckDB "
        f"{duckdb.__version__}. Timings depend on the machine; the row counts don't.",
        "",
        "| Scale | Workers | Strategy | Rows stored | Over Tableau Public's 15M-row limit? | Seconds |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for r in results:
        stored = f"{r['rows']:,}" if r["rows"] else "none (recomputed every run)"
        over = "" if r["rows"] is None else ("yes" if r["rows"] > TABLEAU_PUBLIC_ROW_LIMIT else "no")
        secs = f"{r['seconds']:.2f}"
        if "build" in r:
            secs += f" ({r['build']:.2f} build + {r['walk']:.2f} walk)"
        lines.append(f"| {r['scale']}x | {r['workers']:,} | {r['strategy']} | {stored} | {over} | {secs} |")
    hires, leavers, moves = results[-1]["hires_leavers_moves"]
    lines += ["", f"Strategies 2 and 3 returned identical results at every scale "
                  f"(largest scale: {hires:,} hires, {leavers:,} leavers, {moves:,} department moves)."]
    OUT.write_text("\n".join(lines) + "\n")
    print("\n".join(lines))
    print(f"\nWritten to {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
