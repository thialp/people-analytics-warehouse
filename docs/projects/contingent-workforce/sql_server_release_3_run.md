# Release 3 on SQL Server: run guide

Rebuild the `ArcadiaHR` database on your Mac from `main` (release 3) and confirm it matches the DuckDB pipeline. About 20 minutes, most of it waiting. Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.

**Already checked before this run.** The same T-SQL, translated to DuckDB with `sqlglot`, built every table; every reporting view and every Tableau Custom SQL file matched the DuckDB marts row for row, to the cent, and every check in 05, 08, 10 and 12 passed (`python sqlserver/check_tsql_in_duckdb.py`). The contingent intermediates matched too, down to the text of each discrepancy's evidence. This run is the final check on SQL Server itself.

## What is new in release 3

| File | What it adds |
|---|---|
| `sqlserver/03c_build_dw_contingent.sql` | Bridgeway VMS and Keystone HR's contingent records typed into `dw`; the contingent month-end snapshot, conversions, movement and the plan's contingent actuals; case study 6's identity resolution, side-by-side snapshot and discrepancy rules |
| `sqlserver/04b_create_reporting_views_contingent.sql` | `rpt.vw_cw_spend`, `rpt.vw_workforce_cost_growth_mix` (Shapley), and case study 6's `rpt.vw_cw_discrepancy_detail`, `rpt.vw_cw_reconciliation`, `rpt.vw_cw_engagement_cap`, `rpt.vw_cw_detection_score` |
| `sqlserver/12_validate_contingent_workforce.sql` | 51 PASS/FAIL checks on all of the above, and on the cost bridge Custom SQL |
| `sqlserver/03_build_dw.sql`, `03b_…` | `dw.DimWorker.WorkEmail` (how Bridgeway names a contractor's manager); the plan's `PlannedCwHeadcount` and `PlannedCwSpendUsd` |
| `rpt.vw_plan_vs_actual` | five contingent columns: `planned_cw_headcount`, `actual_cw_headcount`, `planned_cw_spend_usd`, `actual_cw_spend_usd_plan_fx`, `actual_cw_spend_usd_constant` |
| `tableau/custom_sql_headcount_fte_walk.sql` | `worker_type` and `walk_step`; contingent lines (Starts, Ends, Internal Moves); Conversions (`movement_order` 7) |
| `tableau/custom_sql_workforce_cost_bridge.sql` | `worker_type`; the contingent drivers and Conversions (driver 10) |
| `tableau/custom_sql_plan_vs_actual.sql` | the five contingent columns |

## Step 1. Get the latest `main`

Release 3 is merged into `main` (PR #22). In Terminal, in the folder SQL Server sees as `/repo` (Step 2 of the [setup guide](../../setup/sql_server_local_setup.md)):

```bash
cd ~/GitHub/people-analytics-warehouse
git checkout main
git pull
git status
```

Expected: `Fast-forward` (or `Already up to date.`), then `On branch main` and `nothing to commit, working tree clean`. The container reads this folder directly, so SQL Server now sees the release 3 CSVs and scripts.

## Step 2. Start SQL Server and load the password

```bash
docker start arcadia-sql
docker ps --filter name=arcadia-sql --format '{{.Names}}  {{.Status}}'
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
echo ${#MSSQL_SA_PASSWORD}
```

Expected: `arcadia-sql  Up …`, then a number that is not `0`. (If Docker Desktop is closed, open it first and wait for the whale icon to stop animating.)

## Step 3. Rebuild the warehouse

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/build_all.sql
```

10 to 15 minutes under emulation. `build_all` now also runs 03c, 04b and 12. Look for:

```
raw.bw_contingent_worker            43484 rows
raw.bw_service_order_revision       160499 rows
raw.bw_timesheet_month              632504 rows
raw.feed_bridgeway_keystone_event   106357 rows
raw.gen_cw_discrepancy_truth        28948 rows
raw.ks_contingent_worker            141791 rows
...
dw.PlanVsActual                      29415
TableName                       RowsLoaded
dw.BwContingentWorker                43484
dw.BwServiceOrderRevision           160499
dw.BwTimesheetMonth                 632504
dw.KsContingentWorker               141791
dw.FeedBridgewayKeystoneEvent       106357
dw.CwMonthEndSnapshot               598752
dw.CwConversion                       1174
dw.CwMovement                       616469
dw.CwIdentityResolution              43552
dw.CwReconciliationSnapshot         599228
dw.CwDiscrepancy                     28586
```

Then the checks:

| Script, section | Expected |
|---|---|
| 05, section 1 | 11 rows, all `PASS` |
| 05, sections 2, 3, 5 | `0` each; control totals 2026-06-30: 30005 employees (contingent workers are not in them) |
| 08, sections 1–4 | 12, 5, 12 and 4 rows, all `PASS` (29,415 plan rows) |
| 12, `Workforce cost bridge Custom SQL returned 29123 rows` | the seconds are about what a Tableau extract refresh of the bridge will take |
| 12, section 1 (raw rows landed) | 9 rows, all `PASS` |
| 12, section 2 (population and spend) | 7 rows, all `PASS`: 11,941 contingent workers on 30 Jun 2026; 1,174 conversions; billed 21,451,717,557 in billing currency; plan FY26 Q4 11,977 planned vs 11,941 actual |
| 12, section 3 (identity resolution) | 10 rows, all `PASS`: tiers 41,900 / 130 / 0; Keystone only 68, Bridgeway only 126, never started 1,328; 59 supplier spellings, none unmapped |
| 12, section 4 (discrepancies, score) | 19 rows, all `PASS`: nothing unexplained; 416 workers flagged; injected 28,530, detected 28,530, 42 false flags |
| 12, section 5 (cost) | 6 rows, all `PASS`: the bridge closes everywhere; FY26 conversions −32,702,296 out of Contingent and +19,677,620 into Employee; growth mix closing cost 4,648,108,953, volume effect +307,094,838 |

A whole-dollar check may differ by one: SQL Server rounds each group before adding.

**First run, 2026-10-14:** 03c stopped at the last statement with `Msg 8711 … Multiple ordered aggregate functions in the same scope have mutually incompatible orderings`. DuckDB accepts two `STRING_AGG … WITHIN GROUP` with different orderings in one `SELECT`; SQL Server does not. Fixed by aggregating the field list in its own derived table, and the checker now flags the pattern. 10 passed on that run (597,097 rows in 14 seconds).

**If 03c stops with "String or binary data would be truncated"**, send the message: it names the column. **If a discrepancy evidence line shows a month in another language** (CW11, "bills … units for June 2026"), the login's language is not English: `DATENAME(MONTH, …)` follows it. The `sa` login defaults to `us_english`.

## Step 4. Validate the headcount walk Custom SQL

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/10_validate_headcount_fte_walk.sql
```

Expected: `Headcount & FTE walk Custom SQL returned 597097 rows`, then every row `PASS`:

| Section | Expected |
|---|---|
| 1. Shape | 7 rows: 597,097 rows and keys, 60 month-ends, 2 worker types, 9 functions, no missing names, no contingent row with a job family or grade |
| 2. Every slice closes | `0` |
| 3. FY26, employees | opening 28,447; hires 4,965; conversions in 270; voluntary 2,942; involuntary 726; internal moves 3,633 (promotions 2,015); closing 30,014 |
| 4. FY26, contingent | opening 10,707; starts 7,033; ends 5,529; conversions out 270; closing 11,941; total workforce 41,955; conversions net to zero every month |

## Step 5. The other Custom SQL checks (unchanged in phase 8)

06 (compensation walk), 07 (office moves), 09 (region walk and career moves) and 11 (workforce footprint) cover employees only and did not change in phase 8. Run them as before ([release 2 run guide](../workforce-planning/sql_server_release_2_run.md), steps 5 and after); their expected values are in each script.

## Step 6. Send back

A screenshot of each output, or just any line that is not `PASS` or `0`. If everything passes, phase 8 is closed.

## What this does not change yet

Workbooks on SQL Server hold their own copy of the Custom SQL text. Dashboard #1 and the cost bridge pick up worker types only when the new `tableau/custom_sql_headcount_fte_walk.sql` and `custom_sql_workforce_cost_bridge.sql` are pasted in, and every sheet then needs a **Worker Type** filter (see [migration notes](release_3_migration_notes.md), phase 6). That, with the republish of Dashboards #1 and #2, is phase 10.
