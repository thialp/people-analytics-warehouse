"""
Build the Arcadia Systems people analytics warehouse end to end.

    python pipeline/run_pipeline.py            # build, test and export
    python pipeline/run_pipeline.py --no-export

Steps
  1. Load every CSV in data/raw/ into the `raw` schema, as text (like a landing zone).
  2. Run the SQL models in sql/ in folder order: staging -> intermediate -> marts.
  3. Run every data test in tests/. A test is a query that returns the rows that
     break a rule, so zero rows means pass. Any failure stops the build.
  4. Export the marts to data/marts/ as CSV for Tableau.

The warehouse is a single DuckDB file (warehouse/arcadia.duckdb) that you can
open with any DuckDB client to explore the tables yourself.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
MART_DIR = ROOT / "data" / "marts"
SQL_DIR = ROOT / "sql"
TEST_DIR = ROOT / "tests"
DB_PATH = ROOT / "warehouse" / "arcadia.duckdb"

SCHEMAS = ["raw", "staging", "intermediate", "marts"]
EXPORTS = [
    "mart_workforce_cost_bridge",
    "mart_workforce_cost_snapshot",
    "mart_headcount_fte_walk",
    "mart_dim_month",
    "mart_dim_department",
    "mart_dim_country",
    "mart_dim_job_family",
    "mart_dim_grade",
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


def run_models(con: duckdb.DuckDBPyConnection):
    log("\n2. Building models")
    for sql_file in sorted(SQL_DIR.rglob("*.sql")):
        layer = {"01_staging": "staging", "02_intermediate": "intermediate", "03_marts": "marts"}[sql_file.parent.name]
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


def export_marts(con: duckdb.DuckDBPyConnection):
    log("\n4. Exporting marts for Tableau")
    MART_DIR.mkdir(parents=True, exist_ok=True)
    for name in EXPORTS:
        out = MART_DIR / f"{name}.csv"
        con.execute(f"COPY marts.{name} TO '{out.as_posix()}' (HEADER, DELIMITER ',')")
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
    log(f"\nDone in {time.perf_counter() - started:.1f}s. All tests passed.")


if __name__ == "__main__":
    main()
