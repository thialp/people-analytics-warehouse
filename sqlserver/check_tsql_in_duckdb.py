"""
Check the SQL Server build without a SQL Server: translate the T-SQL to DuckDB with
sqlglot, run it on the same raw CSVs, and compare every reporting view and Tableau
Custom SQL with the DuckDB pipeline's marts, row for row.

    pip install sqlglot==30.22.0
    python pipeline/run_pipeline.py          # the marts to compare against
    python sqlserver/check_tsql_in_duckdb.py

What it runs
  1. 03_build_dw.sql, 03b_build_dw_workforce_planning.sql, 03c_build_dw_contingent.sql,
     03d_build_dw_cw_reconciliation.sql, 04_create_reporting_views.sql,
     04b_create_reporting_views_contingent.sql, 04c_create_reporting_views_reconciliation.sql
     (index, constraint and ALTER COLUMN statements are skipped: DuckDB does not need them)
  2. every rpt view against its mart (numbers to the cent, flags as 0/1, the rest as text)
  3. the Tableau Custom SQL: the headcount & FTE walk (against its six CSVs), office moves,
     region walk, career moves, workforce planning (with its summary) and the workforce cost bridge in full, the
     compensation walk for the pairs that end in FY26 (the full walk needs more memory
     than a laptop-sized DuckDB run allows)
  4. the PASS/FAIL tables of 05, 08, 10, 12 (the contingent workforce), 14 (Dashboard #3) and
     15 (Dashboard #4, the reconciliation)
  and, before all that, SQL Server rules DuckDB does not enforce: primary-key columns must be
  made NOT NULL first, text must fit its declared VARCHAR length, PRINT takes no subquery, and
  ordered STRING_AGGs in one SELECT must share one ordering (Msg 8711).

Translation rules that make DuckDB behave like SQL Server: integers divide as integers,
FLOAT is an 8-byte double, BIT is a 0/1 flag, OUTER/CROSS APPLY become LATERAL joins.
This is evidence that the T-SQL logic matches the pipeline; the run on SQL Server itself
(build_all.sql, 06, 07) is still the final check.
"""

from __future__ import annotations

import csv
import re
import sys
import tempfile
import time
from pathlib import Path

import duckdb
import sqlglot
from sqlglot import exp

ROOT = Path(__file__).resolve().parents[1]
PIPELINE_DB = ROOT / "warehouse" / "arcadia.duckdb"
BUILD = ["03_build_dw.sql", "03b_build_dw_workforce_planning.sql", "03c_build_dw_contingent.sql",
         "03d_build_dw_cw_reconciliation.sql",
         "04_create_reporting_views.sql", "04b_create_reporting_views_contingent.sql",
         "04c_create_reporting_views_reconciliation.sql"]
VIEWS = [("mart_workforce_cost_snapshot", "rpt.vw_workforce_cost_snapshot"),
         ("mart_org_leader_summary", "rpt.vw_org_leader_summary"),
         ("mart_fringe_rate", "rpt.vw_fringe_rate"),
         ("mart_position_fill", "rpt.vw_position_fill"),
         ("mart_vacancy_pool", "rpt.vw_vacancy_pool"),
         ("mart_plan_vs_actual", "rpt.vw_plan_vs_actual"),
         ("mart_seat_corridors", "rpt.vw_seat_corridors"),
         ("mart_cw_spend", "rpt.vw_cw_spend"),
         ("mart_workforce_cost_growth_mix", "rpt.vw_workforce_cost_growth_mix"),
         ("mart_cw_discrepancy_detail", "rpt.vw_cw_discrepancy_detail"),
         ("mart_cw_reconciliation", "rpt.vw_cw_reconciliation"),
         ("mart_cw_engagement_cap", "rpt.vw_cw_engagement_cap"),
         ("mart_cw_detection_score", "rpt.vw_cw_detection_score"),
         ("mart_pid_month_end", "rpt.vw_pid_month_end"),
         ("mart_cw_pid_fill", "rpt.vw_cw_pid_fill"),
         ("mart_cw_gap_close", "rpt.vw_cw_gap_close"),
         ("mart_cw_gap_rate_close", "rpt.vw_cw_gap_rate_close"),
         ("mart_itsm_ticket_close", "rpt.vw_itsm_ticket_close")]
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
                started = time.time()
                con.execute(to_duckdb(stmt))
                if time.time() - started > 60:            # say which statements are slow
                    head = " ".join(stmt.sql(dialect="tsql").split())[:70]
                    print(f"      {time.time() - started:4.0f}s  {head}")
        print(f"   ran {name}")


def compare(con: duckdb.DuckDBPyConnection, mart: str, other: str, where: str = "") -> bool:
    if mart.startswith("tmp_"):                        # an expected table built in this database
        cols = [(r[0], r[1]) for r in con.execute(f"DESCRIBE {mart}").fetchall()]
    else:
        cols = con.execute(f"SELECT column_name, data_type FROM information_schema.columns WHERE table_catalog = 'p' "
                           f"AND table_schema = 'marts' AND table_name = '{mart}' ORDER BY ordinal_position").fetchall()

    def norm(c, d):
        q = f'"{c}"'
        if d == "BOOLEAN":
            return f"CASE WHEN LOWER(CAST({q} AS VARCHAR)) IN ('true', '1') THEN 1 ELSE 0 END"
        if any(k in d for k in ("DOUBLE", "DECIMAL", "FLOAT", "INT")):
            return f"ROUND(CAST({q} AS DOUBLE) + 1e-6, 2)"   # off the half-cent boundary
        return f"CAST({q} AS {'DATE' if d == 'DATE' else 'VARCHAR'})"

    other_cols = {r[0] for r in con.execute(f"DESCRIBE SELECT * FROM {other}").fetchall()}
    missing = [c for c, _ in cols if c not in other_cols]
    if missing:                                        # the mart moved ahead of the T-SQL: say what is missing
        print(f"   DIFF   {other:<34} lacks the mart's columns {', '.join(missing)} ({mart})")
        return False
    sel = ", ".join(f"{norm(c, d)} AS \"{c}\"" for c, d in cols)
    src = mart if mart.startswith("tmp_") else f"p.marts.{mart}"
    a, b = f"SELECT {sel} FROM {src} {where}", f"SELECT {sel} FROM {other}"
    n_a, n_b = (con.execute(f"SELECT COUNT(*) FROM ({x})").fetchone()[0] for x in (a, b))
    only_a, only_b = (con.execute(f"SELECT COUNT(*) FROM ({x} EXCEPT ALL {y})").fetchone()[0] for x, y in ((a, b), (b, a)))
    ok = n_a == n_b and only_a == only_b == 0
    print(f"   {'MATCH' if ok else 'DIFF '}  {other:<34} {n_b:>9,} rows   vs {mart:<30} {n_a:>9,} rows"
          + ("" if ok else f"   ({only_a:,} only in the mart, {only_b:,} only in SQL Server's)"))
    if not ok:                                         # which columns disagree, on a few rows
        diff = [c for c, _ in cols if con.execute(
            f'SELECT COUNT(*) FROM (SELECT "{c}" FROM ({a}) EXCEPT ALL SELECT "{c}" FROM ({b}))').fetchone()[0]]
        print(f"          columns that differ: {', '.join(diff) or 'none on their own (row pairing)'}")
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
        if "INTO #" in batch:                  # the batch that runs a Custom SQL file with :r
            continue
        for stmt in sqlglot.parse(batch, read="tsql"):
            if not isinstance(stmt, exp.Select):
                continue
            df = con.execute(to_duckdb(stmt)).fetchdf()
            if "result" in df.columns:
                bad = df[df["result"] != "PASS"]
                ok &= bad.empty
                print(f"   {name}: {len(df) - len(bad)} of {len(df)} checks PASS" + ("" if bad.empty else f"\n{bad}"))
    return ok


def static_checks() -> bool:
    """SQL Server rules the translated run cannot see, because DuckDB ignores them:
    a primary key needs every column made NOT NULL first (SELECT ... INTO keeps the source's
    nullability), and text cast from a raw column must fit its declared length (SQL Server
    would cut it silently)."""
    ok = True
    for name in BUILD:
        text = re.sub(r"/\*.*?\*/", "", (ROOT / "sqlserver" / name).read_text(), flags=re.S)
        not_null = {(t.lower(), c.lower()) for t, c in
                    re.findall(r"ALTER TABLE\s+([\w.]+)\s+ALTER COLUMN\s+(\w+)\s+[^;]*NOT NULL", text, flags=re.I)}
        for table, cols in re.findall(r"ALTER TABLE\s+([\w.]+)\s+ADD CONSTRAINT\s+\w+\s+PRIMARY KEY[^(]*\(([^)]*)\)", text, flags=re.I):
            for col in (c.strip() for c in cols.split(",")):
                if (table.lower(), col.lower()) not in not_null:
                    ok = False
                    print(f"   FAIL  {name}: {table}.{col} is in the primary key but never made NOT NULL")
        for batch in re.split(r"^\s*GO\s*$", text, flags=re.M):
            # SQL Server checks the key against the columns as they were when the batch compiled:
            # if a nullable copy of the table is left from an earlier run, an ALTER COLUMN in the
            # same batch does not count. The key goes in the batch after the ALTER COLUMN.
            altered = {(t.lower(), c.lower()) for t, c in
                       re.findall(r"ALTER TABLE\s+([\w.]+)\s+ALTER COLUMN\s+(\w+)\s+[^;]*NOT NULL", batch, flags=re.I)}
            for table, cols in re.findall(r"ALTER TABLE\s+([\w.]+)\s+ADD CONSTRAINT\s+\w+\s+PRIMARY KEY[^(]*\(([^)]*)\)", batch, flags=re.I):
                if any((table.lower(), c.strip().lower()) in altered for c in cols.split(",")):
                    ok = False
                    print(f"   FAIL  {name}: {table} gets its primary key in the same batch as its ALTER COLUMN")
        for stmt in re.split(r"(?=DROP TABLE IF EXISTS)", text):
            src = re.search(r"FROM\s+raw\.(\w+)", stmt, flags=re.I)
            if not src:
                continue
            csv_path = ROOT / "data" / "raw" / f"{src.group(1)}.csv"
            with csv_path.open(newline="") as f:
                rows = list(csv.reader(f))
            header = rows[0]
            for raw_col, n in re.findall(r"CAST\(\s*(?:NULLIF\(\s*)?\[?(\w+)\]?(?:\s*,\s*''\s*\))?\s+AS\s+N?VARCHAR\((\d+)\)\)",
                                         stmt, flags=re.I):
                if raw_col not in header:
                    continue
                k = header.index(raw_col)
                longest = max((len(r[k]) for r in rows[1:] if len(r) > k), default=0)
                if longest > int(n):
                    ok = False
                    print(f"   FAIL  {name}: raw.{src.group(1)}.{raw_col} holds values of {longest} characters, cast to VARCHAR({n})")
    for name in BUILD:   # ordered STRING_AGGs in one SELECT must share their ordering (Msg 8711)
        for batch in batches(ROOT / "sqlserver" / name):
            for stmt in sqlglot.parse(batch, read="tsql"):
                for sel in (stmt.find_all(exp.Select) if stmt else []):
                    orders = {tuple(o.sql("tsql") for o in g.this.expressions)
                              for g in sel.find_all(exp.GroupConcat)
                              if isinstance(g.this, exp.Order) and g.find_ancestor(exp.Select) is sel}
                    if len(orders) > 1:
                        ok = False
                        print(f"   FAIL  {name}: STRING_AGGs in one SELECT with different orderings {sorted(orders)}")
    for path in sorted((ROOT / "sqlserver").glob("*.sql")):   # PRINT takes no subquery (Msg 1046)
        text = re.sub(r"/\*.*?\*/", "", path.read_text(), flags=re.S)
        for line in re.findall(r"^\s*PRINT\b[^;]*\(\s*SELECT\b", text, flags=re.I | re.M):
            ok = False
            print(f"   FAIL  {path.name}: PRINT holds a subquery: {line.strip()[:60]}")
    print("   primary keys, text lengths, PRINT and STRING_AGG orderings: "
          + ("all fit SQL Server's rules" if ok else "see above"))
    return ok


def main() -> int:
    if not PIPELINE_DB.exists():
        print("Run python pipeline/run_pipeline.py first: the marts are what the T-SQL is compared with.")
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        con = connect(Path(tmp) / "sqlserver.duckdb")
        print("0. SQL Server rules DuckDB does not enforce")
        static = static_checks()
        print("\n1. Building the SQL Server warehouse (T-SQL translated to DuckDB)")
        build(con)
        con.execute(f"ATTACH '{PIPELINE_DB}' AS p (READ_ONLY)")
        print("\n2. Reporting views vs the pipeline marts")
        ok = all([compare(con, m, v) for m, v in VIEWS])
        print("\n3. Tableau Custom SQL vs the pipeline marts")
        custom_sql(con, "custom_sql_office_moves.sql", "office_moves")
        ok &= compare(con, "mart_office_moves", "cs.office_moves")
        custom_sql(con, "custom_sql_region_walk.sql", "region_walk")
        ok &= compare(con, "mart_region_walk", "cs.region_walk")
        custom_sql(con, "custom_sql_career_moves.sql", "career_moves")
        ok &= compare(con, "mart_career_moves", "cs.career_moves")
        # Dashboard #1: the walk CSV with its five dimension CSVs, joined, is what the Custom SQL replaces
        con.execute("""CREATE OR REPLACE TABLE tmp_headcount_fte_walk_csvs AS
            SELECT w.*, m.prior_month_end_date, CAST(m.fiscal_year AS VARCHAR) AS fiscal_year, m.fiscal_year_label,
                   m.fiscal_quarter_label, m.fiscal_period, m.fiscal_month, m.is_fiscal_year_end,
                   d.department_name, d.sub_function, d.function_name, d.parent_org_unit_id, d.cost_center, d.head_grade,
                   c.country_name, c.region, c.currency_code, c.pay_index, j.job_family,
                   g.level_code, g.grade_level, g.career_track, g.us_base_salary_usd
            FROM p.marts.mart_headcount_fte_walk AS w
            JOIN p.marts.mart_dim_month      AS m USING (month_end_date)
            JOIN p.marts.mart_dim_department AS d USING (department_id)
            JOIN p.marts.mart_dim_country    AS c USING (country_code)
            LEFT JOIN p.marts.mart_dim_job_family AS j USING (job_family_code)
            LEFT JOIN p.marts.mart_dim_grade      AS g USING (grade)""")
        custom_sql(con, "custom_sql_headcount_fte_walk.sql", "headcount_fte_walk")
        ok &= compare(con, "tmp_headcount_fte_walk_csvs", "cs.headcount_fte_walk")
        con.execute("CREATE OR REPLACE TABLE tmp_hc AS SELECT * FROM cs.headcount_fte_walk")
        con.execute("CREATE OR REPLACE VIEW hc AS SELECT * FROM tmp_hc")
        for name in ("position_fill", "vacancy_pool", "plan_vs_actual", "seat_corridors"):   # Dashboard #3
            custom_sql(con, f"custom_sql_{name}.sql", name)
            ok &= compare(con, f"mart_{name}", f"cs.{name}",
                          "" if name == "seat_corridors" else "WHERE department_id <> 'D-901'")
        custom_sql(con, "custom_sql_wfp_summary.sql", "wfp_summary")   # Dashboard #3 KPI band and rail
        ok &= compare(con, "mart_wfp_summary", "cs.wfp_summary")
        for tmp, src in (("tmp_wfp", "cs.wfp_summary"), ("tmp_pva", "cs.plan_vs_actual"),   # #wfp, #pva, #fill in 14_validate
                         ("tmp_fill", "cs.position_fill")):
            con.execute(f"CREATE OR REPLACE TABLE {tmp} AS SELECT * FROM {src}")
            con.execute(f"CREATE OR REPLACE VIEW {tmp[4:]} AS SELECT * FROM {tmp}")
        custom_sql(con, "custom_sql_workforce_cost_bridge.sql", "workforce_cost_bridge")
        ok &= compare(con, "mart_workforce_cost_bridge", "cs.workforce_cost_bridge")
        con.execute("CREATE OR REPLACE VIEW cb AS SELECT * FROM cs.workforce_cost_bridge")   # #cb in 12_validate
        for name in ("cw_spend", "workforce_cost_growth_mix", "cw_discrepancy_detail",   # thin reads of the views
                     "cw_reconciliation", "cw_engagement_cap", "cw_detection_score"):
            custom_sql(con, f"custom_sql_{name}.sql", name)
            ok &= compare(con, f"mart_{name}", f"cs.{name}")
        custom_sql(con, "custom_sql_cw_reconciliation_dashboard.sql", "cw_reconciliation_dashboard")   # Dashboard #4
        ok &= compare(con, "mart_cw_reconciliation_dashboard", "cs.cw_reconciliation_dashboard")
        con.execute("CREATE OR REPLACE TABLE tmp_d6 AS SELECT * FROM cs.cw_reconciliation_dashboard")   # #d6 in 15_validate
        con.execute("CREATE OR REPLACE VIEW d6 AS SELECT * FROM tmp_d6")
        custom_sql(con, "custom_sql_compensation_walk.sql", "walk_fy26", "t2.MonthEndDate >= '2025-06-30'")
        ok &= compare(con, "mart_compensation_walk", "cs.walk_fy26", "WHERE to_month_end >= DATE '2025-06-30'")
        print("\n4. Validation scripts")
        ok &= validation(con, "05_validate.sql")
        ok &= validation(con, "08_validate_workforce_planning.sql")
        ok &= validation(con, "10_validate_headcount_fte_walk.sql")
        ok &= validation(con, "12_validate_contingent_workforce.sql")
        ok &= validation(con, "14_validate_workforce_planning_dashboard.sql")
        ok &= validation(con, "15_validate_cw_reconciliation.sql")
        con.close()
    ok &= static
    print("\nAll checks match." if ok else "\nDifferences found.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
