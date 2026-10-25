"""
Build the Arcadia Systems people analytics warehouse end to end.

    python pipeline/run_pipeline.py            # build, test and export
    python pipeline/run_pipeline.py --no-export

Steps
  1. Load every CSV in data/raw/ into the `raw` schema, as text (like a landing zone).
  2. Run the SQL models in sql/ in folder order: staging -> intermediate -> marts.
  3. Run every data test in tests/. A test is a query that returns the rows that
     break a rule, so zero rows means pass. Any failure stops the build.
  4. Export the marts to data/marts/ as CSV for Tableau, and write docs/company/org_chart.md
     and the dashboards' check tables (docs/projects/*/expected_values.md).

The warehouse is a single DuckDB file (warehouse/arcadia.duckdb) that you can
open with any DuckDB client to explore the tables yourself.
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path

import duckdb

import build_org_chart
import expected_values

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
MART_DIR = ROOT / "data" / "marts"
SQL_DIR = ROOT / "sql"
TEST_DIR = ROOT / "tests"
DB_PATH = ROOT / "warehouse" / "arcadia.duckdb"

SCHEMAS = ["raw", "staging", "intermediate", "marts"]
EXPORTS = [
    "mart_workforce_cost_bridge",
    "mart_compensation_walk",
    "mart_workforce_cost_snapshot",
    "mart_headcount_fte_walk",
    "mart_dim_month",
    "mart_dim_department",
    "mart_dim_country",
    "mart_dim_job_family",
    "mart_dim_grade",
    "mart_dim_location",
    "mart_location_headcount",
    "mart_mobility_flows",
    "mart_dim_org_unit",
    "mart_org_leader_summary",
    "mart_reporting_line",
    "mart_fringe_rate",
    "mart_position_fill",
    "mart_vacancy_pool",
    "mart_plan_vs_actual",
    "mart_cw_spend",
    "mart_workforce_cost_growth_mix",
    "mart_cw_reconciliation",
    "mart_cw_discrepancy_detail",
    "mart_cw_engagement_cap",
    "mart_cw_detection_score",
    "mart_seat_corridors",
    "mart_region_walk",
    "mart_career_moves",
    "mart_wfp_summary",
    "mart_pid_month_end",
    "mart_cw_pid_fill",
    "mart_cw_gap_close",
    "mart_cw_gap_rate_close",
    "mart_itsm_ticket_close",
    "mart_cw_reconciliation_dashboard",
]


def log(msg: str = ""):
    print(msg, flush=True)


def load_raw(con: duckdb.DuckDBPyConnection):
    log("1. Loading raw files")
    for csv in sorted(RAW_DIR.glob("*.csv")):
        con.execute(
            f"CREATE OR REPLACE TABLE raw.{csv.stem} AS "
            f"SELECT * FROM read_csv('{csv.as_posix()}', header = true, all_varchar = true)"
        )
        n = con.execute(f"SELECT COUNT(*) FROM raw.{csv.stem}").fetchone()[0]
        log(f"   raw.{csv.stem:<32}{n:>10,} rows")


LAYERS = {"01_staging": "staging", "02_intermediate": "intermediate", "03_marts": "marts"}


def model_order() -> list[Path]:
    """Every model file, layer by layer, each after the models it reads.

    Within a layer the order is alphabetical unless a model reads another model of the same
    layer (`intermediate.int_x`), in which case it runs after it, as dbt does with ref().
    A cycle is an error.
    """
    ordered: list[Path] = []
    for folder in sorted(LAYERS):
        layer = LAYERS[folder]
        files = {f.stem: f for f in sorted((SQL_DIR / folder).glob("*.sql"))}
        deps = {name: {m for m in re.findall(rf"\b{layer}\.(\w+)", f.read_text())
                       if m in files and m != name} for name, f in files.items()}
        done: set[str] = set()
        while len(done) < len(files):
            ready = [n for n in files if n not in done and deps[n] <= done]
            if not ready:
                raise RuntimeError(f"Circular model references in {folder}: {sorted(set(files) - done)}")
            done.add(ready[0])
            ordered.append(files[ready[0]])
    return ordered


def run_models(con: duckdb.DuckDBPyConnection):
    log("\n2. Building models")
    for sql_file in model_order():
        layer = LAYERS[sql_file.parent.name]
        start = time.perf_counter()
        con.execute(sql_file.read_text())
        n = con.execute(f"SELECT COUNT(*) FROM {layer}.{sql_file.stem}").fetchone()[0]
        log(f"   {layer}.{sql_file.stem:<40}{n:>10,} rows  ({time.perf_counter() - start:.1f}s)")


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    log("\n3. Running data tests")
    all_passed = True
    for test_file in sorted(TEST_DIR.glob("*.sql")):
        query = test_file.read_text()
        failures = con.execute(f"SELECT COUNT(*) FROM ({query.rstrip().rstrip(';')})").fetchone()[0]
        status = "PASS" if failures == 0 else f"FAIL ({failures:,} rows)"
        log(f"   {status:<18}{test_file.stem}")
        if failures:
            all_passed = False
            sample = con.execute(f"SELECT * FROM ({query.rstrip().rstrip(';')}) LIMIT 5").fetchdf()
            log(sample.to_string(index=False))
    return all_passed


# A mart whose full CSV would pass GitHub's 100 MB file limit is exported on the dates the
# dashboards use. The warehouse table (and rpt.vw_vacancy_pool on SQL Server) keeps every month-end.
EXPORT_FILTERS = {
    # release 3.1: contingent PIDs made the vacancy pool 439,286 rows (121 MB); quarter-ends only
    "mart_vacancy_pool": "WHERE MONTH(month_end_date) IN (3, 6, 9, 12)",
}


def export_marts(con: duckdb.DuckDBPyConnection):
    log("\n4. Exporting marts for Tableau")
    MART_DIR.mkdir(parents=True, exist_ok=True)
    for name in EXPORTS:
        out = MART_DIR / f"{name}.csv"
        source = f"(SELECT * FROM marts.{name} {EXPORT_FILTERS[name]})" if name in EXPORT_FILTERS else f"marts.{name}"
        con.execute(f"COPY {source} TO '{out.as_posix()}' (HEADER, DELIMITER ',')")
        log(f"   {out.relative_to(ROOT)}  ({out.stat().st_size / 1e6:.1f} MB)")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--no-export", action="store_true", help="build and test without writing CSVs")
    args = parser.parse_args()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))
    for schema in SCHEMAS:
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")

    started = time.perf_counter()
    load_raw(con)
    run_models(con)
    passed = run_tests(con)
    if not passed:
        log("\nData tests failed. Marts were not exported.")
        sys.exit(1)
    if not args.no_export:
        export_marts(con)
        build_org_chart.main(con)
        expected_values.main(con)
    log(f"\nDone in {time.perf_counter() - started:.1f}s. All tests passed.")


if __name__ == "__main__":
    main()
