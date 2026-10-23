# Release 3.1 on SQL Server: run guide

Rebuild `ArcadiaHR` on your Mac after release 3.1 (contingent PIDs and the hiring pipeline at the extract) and confirm it matches DuckDB. About 20 minutes, most of it waiting. All data is synthetic.

**Already checked before this run.** `python sqlserver/check_tsql_in_duckdb.py` translated the T-SQL to DuckDB and built every table: every reporting view and every Tableau Custom SQL file matched the DuckDB marts, and every check in 05, 08, 10, 12 and 14 passed ("All checks match.").

## What changed

| File | Change |
|---|---|
| `data/raw/dim_position.csv`, `fact_position_assignment.csv` | Contingent PIDs and assignments added, with `worker_type`, `cw_type`, `cw_role_family`, `bw_worker_id` |
| `data/raw/fact_requisition.csv`, `dim_candidate.csv`, `fact_candidate_stage_event.csv` | The hiring pipeline run six months past the extract, so requisitions open on 30 Jun 2026 have their new PIDs and applicants |
| `sqlserver/02_load_raw.sql` | The new columns |
| `sqlserver/03b_build_dw_workforce_planning.sql` | `dw.DimPosition` and `dw.FactPositionAssignment` keep employees; new `dw.DimContingentPosition`, `dw.FactContingentPositionAssignment`, `dw.ContingentPositionMonthEndSnapshot` |
| `sqlserver/04_create_reporting_views.sql` | `rpt.vw_vacancy_pool` adds contingent PIDs (`worker_type`, `cw_type`, `cw_role_family`); new `rpt.vw_pid_month_end`, `rpt.vw_cw_pid_fill` |
| `sqlserver/08_…`, `14_…` | New expected values; 14 adds section 5, the PID ledger |
| `tableau/custom_sql_wfp_summary.sql`, `custom_sql_vacancy_pool.sql` | The PID ledger, level and office changes, contingent fills, month-named periods |

Employee people data did not move: Dashboards #1 and #2 and their checks are unchanged.

## Step 1. Get the branch

```bash
cd ~/GitHub/people-analytics-warehouse
git fetch
git checkout dashboard-3-pids      # or main, once the PR is merged
git pull
```

## Step 2. Start SQL Server

```bash
docker start arcadia-sql
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
```

## Step 3. Rebuild

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/build_all.sql
```

Look for:

```
raw.dim_position                    222161 rows
raw.fact_position_assignment        98389 rows
raw.fact_requisition                31614 rows
raw.dim_candidate                   189964 rows
raw.fact_candidate_stage_event      533671 rows
...
dw.DimPosition                       99689
dw.DimContingentPosition            122472
dw.FactContingentPositionAssignment  44295
dw.PositionMonthEndSnapshot        1702178
dw.ContingentPositionMonthEndSnapshot 975547
```

`build_all` runs 05, 08 and 12: every line should read PASS.

## Step 4. The dashboard checks

```bash
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd \
  -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C \
  -i /repo/sqlserver/14_validate_workforce_planning_dashboard.sql
```

Every line PASS. Section 5, the PID ledger on 30 Jun 2026:

| Measure | Expected |
|---|---:|
| PIDs | 51,163 |
| Filled by employees | 30,005 |
| Filled by contractors | 11,941 |
| Vacant, previously held | 8,689 |
| Vacant, new | 528 |
| Net-new approved while a match stood vacant 90+ days (FY26) | 631, $55,680,160.14 |

## Step 5. Refresh Tableau

Workforce Planning workbook: Data → each data source → Refresh (or Edit Custom SQL, paste the new `custom_sql_wfp_summary.sql` and `custom_sql_vacancy_pool.sql`, then Refresh). New fields appear at the bottom of the data pane.
