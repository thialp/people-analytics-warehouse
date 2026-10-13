"""
Check the SQL Server build without a SQL Server: translate the T-SQL to DuckDB with
sqlglot, run it on the same raw CSVs, and compare every reporting view and Tableau
Custom SQL with the DuckDB pipeline's marts, row for row.

    pip install sqlglot==30.22.0
    python pipeline/run_pipeline.py          # the marts to compare against
    python sqlserver/check_tsql_in_duckdb.py

What it runs
  1. 03_build_dw.sql, 03b_build_dw_workforce_planning.sql, 04_create_reporting_views.sql
     (index, constraint and ALTER COLUMN statements are skipped: DuckDB does not need them)
  2. every rpt view against its mart (numbers to the cent, flags as 0/1, the rest as text)
  3. the Tableau Custom SQL: office moves in full, the compensation walk for the pairs that
     end in FY26 (the full walk needs more memory than a laptop-sized DuckDB run allows)
  4. the PASS/FAIL tables of 05_validate.sql and 08_validate_workforce_planning.sql

Translation rules that make DuckDB behave like SQL Server: integers divide as integers,
FLOAT is an 8-byte double, BIT is a 0/1 flag, OUTER/CROSS APPLY become LATERAL joins.
This is evidence that the T-SQL logic matches the pipeline; the run on SQL Server itself
(build_all.sql, 06, 07) is still the final check.
"""

from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

import duckdb
import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DB = ROOT / "warehouse" / "arcadia.duckdb"
BUILD = ["03_build_dw.sql", "03b_build_dw_workforce_planning.sql", "04_create_reporting_views.sql"]
VIEWS = [("mart_workforce_cost_snapshot", "rpt.vw_workforce_cost_snapshot"),
         ("mart_org_leader_summary", "rpt.vw_org_leader_summary"),
         ("mart_fringe_rate", "rpt.vw_fringe_rate"),
         ("mart_position_fill", "rpt.vw_position_fill"),
         ("mart_vacancy_pool", "rpt.vw_vacancy_pool"),
         ("mart_plan_vs_actual", "rpt.vw_plan_vs_actual"),
         ("mart_seat_corridors", "rpt.vw_seat_corridors")]
SKIP = re.compile(r"^\s*(CREATE\s+(CLUSTERED\s+|UNIQUE\s+)?INDEX|ALTER\s+TABLE|SET\s+NOCOUNT|USE\s|PRINT\s|DECLARE\s"
                  r"|IF\s+DB_ID|IF\s+SCHEMA_ID)", re.I)


def add_on_true(sql: str) -> str:
    """OUTER / CROSS APPLY become LEFT / INNER JOIN LATERAL (...) AS x, which DuckDB wants followed by ON."""
    out, i = [], 0
    while True:
        hits = [(sql.find(key, i), key) for key in ("LEFT JOIN LATERAL (", "INNER JOIN LATERAL (")]
        hits = [h for h in hits if h[0] >= 0]
        if not hits:
            out.append(sql[i:])
            return "".join(out)
        k, key = min(hits)
        depth, j = 0, k + len(key) - 1
        while True:
            depth += {"(": 1, ")": -1}.get(sql[j], 0)
            if depth == 0:
                break
            j += 1
        m = re.match(r"\s+AS\s+\w+(\s*\([^()]*\))?", sql[j + 1:])
        end = j + 1 + (m.end() if m else 0)
        out.append(sql[i:end])
        if not re.match(r"\s+ON\b", sql[end:]):
            out.append(" ON TRUE")
        i = end


def to_duckdb(stmt: exp.Expression) -> str:
    for t in stmt.find_all(exp.Table):                 # #temp tables become ordinary tables
        if t.name.startswith("#"):
            t.set("this", exp.to_identifier("tmp_" + t.name[1:]))
    for dt in stmt.find_all(exp.DataType):             # SQL Server FLOAT is a double, BIT a 0/1 flag
        if dt.this == exp.DataType.Type.FLOAT:
            dt.set("this", exp.DataType.Type.DOUBLE)
        elif dt.this == exp.DataType.Type.BIT:
            dt.set("this", exp.DataType.Type.BOOLEAN)
    sql = add_on_true(stmt.sql(dialect="duckdb"))
    if "UNION ALL" in sql and re.search(r"\bchain\b", sql) and "RECURSIVE" not in sql:
        sql = sql.replace("WITH ", "WITH RECURSIVE ", 1)
    return sql


def batches(path: Path):
    text = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
    text = "\n".join(line for line in text.splitlines() if not line.lstrip().startswith(":"))
    yield from re.split(r"^\s*GO\s*$", text, flags=re.M)


def connect(path: Path) -> duckdb.DuckDBPyConnection:
    con = duckdb.connect(str(path))
    con.execute("SET integer_division = true")         # T-SQL divides integers as integers
    con.execute("SET memory_limit = '5GB'")
    con.execute("SET preserve_insertion_order = false")
    con.execute(f"SET temp_directory = '{path.parent / 'spill'}'")
    return con


def build(con: duckdb.DuckDBPyConnection):
    for s in ("raw", "dw", "rpt", "cs"):
        con.execute(f"CREATE SCHEMA IF NOT EXISTS {s}")
    for csv in sorted((ROOT / "data" / "raw").glob("*.csv")):  # like BULK INSERT: text, empty not NULL
        con.execute(f"CREATE OR REPLACE TABLE raw.{csv.stem} AS SELECT * FROM read_csv('{csv}', header = true, all_varchar = true)")
        cols = [r[0] for r in con.execute(f"DESCRIBE raw.{csv.stem}").fetchall()]
        con.execute(f"UPDATE raw.{csv.stem} SET " + ", ".join(f'"{c}" = COALESCE("{c}", \'\')' for c in cols))
    for name in BUILD:
        for batch in batches(ROOT / "sqlserver" / name):
            for stmt in sqlglot.parse(batch, read="tsql"):
                if stmt is None or SKIP.match(stmt.sql(dialect="tsql")):
                    continue
                con.execute(to_duckdb(stmt))
        print(f"   ran {name}")


def compare(con: duckdb.DuckDBPyConnection, mart: str, other: str, where: str = "") -> bool:
    cols = con.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_catalog = 'p' "
                       f"AND table_schema = 'marts' AND table_name = '{mart}' ORDER BY ordinal_position").fetchall()

    def norm(c, d):
        q = f'"{c}"'
        if d == "BOOLEAN":
            return f"CASE WHEN LOWER(CAST({q} AS VARCHAR)) IN ('true', '1') THEN 1 ELSE 0 END"
        if any(k in d for k in ("DOUBLE", "DECIMAL", "FLOAT", "INT")):
            return f"ROUND(CAST({q} AS DOUBLE) + 1e-6, 2)"   # off the half-cent boundary
        return f"CAST({q} AS {'DATE' if d == 'DATE' else 'VARCHAR'})"

    sel = ", ".join(f"{norm(c, d)} AS \"{c}\"" for c, d in cols)
    a, b = f"SELECT {sel} FROM p.marts.{mart} {where}", f"SELECT {sel} FROM {other}"
    n_a, n_b = (con.execute(f"SELECT COUNT(*) FROM ({x})").fetchone()[0] for x in (a, b))
    only_a, only_b = (con.execute(f"SELECT COUNT(*) FROM ({x} EXCEPT ALL {y})").fetchone()[0] for x, y in ((a, b), (b, a)))
    ok = n_a == n_b and only_a == only_b == 0
    print(f"   {'MATCH' if ok else 'DIFF '}  {other:<34} {n_b:>9,} rows   vs {mart:<30} {n_a:>9,} rows"
          + ("" if ok else f"   ({only_a:,} only in the mart, {only_b:,} only in SQL Server's)"))
    return ok


def custom_sql(con: duckdb.DuckDBPyConnection, file: str, name: str, extra_grid_filter: str = ""):
    text = re.sub(r"/\*.*?\*/", "", (ROOT / "tableau" / file).read_text(), flags=re.S)
    if extra_grid_filter:
        anchor = "WHERE t2.MonthEndDate > DATEADD(MONTH, 12, (SELECT MIN(MonthEndDate) FROM dw.MonthEndCalendar))"
        assert text.count(anchor) == 1, f"grid marker not found in {file}"
        text = text.replace(anchor, f"{anchor} AND {extra_grid_filter}")
    con.execute(f"CREATE OR REPLACE TABLE cs.{name} AS {to_duckdb(sqlglot.parse_one(text, read='tsql'))}")


def validation(con: duckdb.DuckDBPyConnection, name: str) -> bool:
    """Run the PASS/FAIL tables of a validation script; return False if any row fails."""
    ok = True
    for batch in batches(ROOT / "sqlserver" / name):
        for stmt in sqlglot.parse(batch, read="tsql"):
            if not isinstance(stmt, exp.Select):
                continue
            df = con.execute(to_duckdb(stmt)).fetchdf()
            if "result" in df.columns:
                bad = df[df["result"] != "PASS"]
                ok &= bad.empty
                print(f"   {name}: {len(df) - len(bad)} of {len(df)} checks PASS" + ("" if bad.empty else f"\n{bad}"))
    return ok


def main() -> int:
    if not PIPELINE_DB.exists():
        print("Run python pipeline/run_pipeline.py first: the marts are what the T-SQL is compared with.")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        con = connect(Path(tmp) / "sqlserver.duckdb")
        print("1. Building the SQL Server warehouse (T-SQL translated to DuckDB)")
        build(con)
        con.execute(f"ATTACH '{PIPELINE_DB}' AS p (READ_ONLY)")
        print("\n2. Reporting views vs the pipeline marts")
        ok = all([compare(con, m, v) for m, v in VIEWS])
        print("\n3. Tableau Custom SQL vs the pipeline marts")
        custom_sql(con, "custom_sql_office_moves.sql", "office_moves")
        ok &= compare(con, "mart_office_moves", "cs.office_moves")
        custom_sql(con, "custom_sql_compensation_walk.sql", "walk_fy26", "t2.MonthEndDate >= '2025-06-30'")
        ok &= compare(con, "mart_compensation_walk", "cs.walk_fy26", "WHERE to_month_end >= DATE '2025-06-30'")
        print("\n4. Validation scripts")
        ok &= validation(con, "05_validate.sql")
        ok &= validation(con, "08_validate_workforce_planning.sql")
        con.close()
    print("\nAll checks match." if ok else "\nDifferences found.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
