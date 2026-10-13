# Release 2 on SQL Server: run guide

Rebuild the `ArcadiaHR` database on your Mac from branch `warehouse-release-2` and confirm it matches the DuckDB pipeline. About 15 minutes, most of it waiting. Arcadia Systems is fictional and all data is synthetic.

What was already checked before this run: the same T-SQL, translated to DuckDB with `sqlglot`, built every table, and every reporting view and both Custom SQL files matched the DuckDB marts row for row (`python sqlserver/check_tsql_in_duckdb.py`). This run is the final check on SQL Server itself.

## Step 1. Switch the repo to the release branch

Open Terminal and go to the folder you cloned in Step 2 of the [setup guide](../../setup/sql_server_local_setup.md) (the one SQL Server sees as `/repo`):

```bash
cd ~/Documents/GitHub/people-analytics-warehouse
git fetch origin
git checkout warehouse-release-2
git pull
```

Expected (the last line):

```
Already up to date.
```

or a list of changed files. `git status` should then say `On branch warehouse-release-2` and `nothing to commit, working tree clean`.

The container reads the repo folder directly, so SQL Server now sees the release 2 CSVs and scripts. Nothing is copied.

## Step 2. Make sure SQL Server is running

```bash
docker start arcadia-sql
docker ps --filter name=arcadia-sql --format '{{.Names}}  {{.Status}}'
```

Expected:

```
arcadia-sql
arcadia-sql  Up 10 seconds
```

(`Up` followed by any time. If Docker Desktop is closed, open it first and wait for the whale icon to stop animating.)

## Step 3. Load the password into this Terminal window

```bash
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
echo ${#MSSQL_SA_PASSWORD}
```

Expected: a number (the password's length, for example `17`), not `0`.

## Step 4. Rebuild the warehouse

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/build_all.sql
```

This drops and recreates every table and view (5–10 minutes under emulation). Look for these lines:

```
raw.dim_worker                      46980 rows
...
dw.WorkerMonthEndSnapshot          1639687
...
dw.SeatFill                          30575
dw.PlanVsActual                      28800
...
4. Control totals (executive officers excluded)
2022-06-30      25052      24725.50  2450138920.49       2487093187.74
2026-06-30      30005      29354.50  3336539181.84       3336539181.84
```

Then the checks:

| Section | Expected |
|---|---|
| 05, section 1 (row counts) | 11 rows, all `PASS` |
| 05, sections 2, 3, 5 | `0` each |
| 08, section 1 (row counts) | 12 rows, all `PASS` |
| 08, section 2 (seat integrity) | 5 rows, `0` failures, all `PASS` |
| 08, section 3 (FY26 seat fills) | 12 rows, all `PASS` (6,849 fills; pay change −7,004,254.10) |
| 08, section 4 (vacancy pool, Jun 30, 2026) | 4 rows, all `PASS` (725 open, 252 frozen) |
| 08, section 5 (FY26 plan vs actual) | matches the expected block printed under it in the script |

A control total may differ by a cent: SQL Server rounds each group before adding.

## Step 5. Validate the two Tableau Custom SQL queries

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/06_validate_compensation_walk.sql
```

Expected: `Custom SQL returned 115544 rows in <n> seconds`; section 1 `PASS` three times (115,544 rows, 88 date pairs, 6 views); section 2 `0`; section 3 Opening `25052` and Closing `26932`; section 4 matches the FY26 table in the script (Opening 28,438 → Closing 30,005).

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/07_validate_office_moves.sql
```

Expected: sections 1 and 2 all `PASS` (89,611 rows, 88 pairs; FY26 725 people changed office, 600 within one country, 125 across a border; FY23 560); sections 3 and 4 show `0`.

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/09_validate_region_walk_and_career_moves.sql
```

Expected (added in phase 7): three "returned ... rows" lines (region walk 26,520, career moves 34,532, walk 115,544); section 1 all `PASS`; section 2 three rows with `0` failures, all `PASS`; section 3 all `PASS` (FY26: 1,850 promotions, 148 demotions, 16 into Director and above; North America 9,909 → 10,426).

07 also has a new check, 4b (`open_headcount` equals the walk's Opening headcount): expected `0`.

The seconds 06 and 07 print are roughly what a Tableau extract refresh of each data source will take; with 88 pairs instead of 184 they should be about half of what you saw before.

## Step 6. Send back

A screenshot of each output, or just any line that is not `PASS` or `0`. If everything passes, phase 6 is closed.

## What this does not change yet

The published dashboards and your workbooks still hold the old data. Their Custom SQL text lives inside each workbook, so Dashboard #2 picks up the new pair grid only when the new `tableau/custom_sql_compensation_walk.sql` and `custom_sql_office_moves.sql` are pasted in. That, the new expected values and the republish of Dashboards #1 and #2 are phase 8. Until then, do not refresh the extracts of the published workbooks.

## Dashboard #1 on SQL Server (added 2026-10-13)

Dashboard #1 moves from the CSVs to [`tableau/custom_sql_headcount_fte_walk.sql`](../../../tableau/custom_sql_headcount_fte_walk.sql). Check it after `build_all`:

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/10_validate_headcount_fte_walk.sql
```

Expected: 521,029 rows; every check PASS (shape, every slice closes, FY26 opening 28,447, hires 5,235, closing 30,014). Tableau steps: [Replace References guide](release_2_replace_references.md).
