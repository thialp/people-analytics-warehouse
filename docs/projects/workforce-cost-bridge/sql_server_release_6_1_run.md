# Release 6.1 on SQL Server: run guide

Release 6.1 adds the employee and contingent headcounts to the growth mix, for the rail of Dashboard #6 (Workforce Cost Bridge). About two minutes. All data is synthetic.

**Already checked before this run.** `python sqlserver/check_tsql_in_duckdb.py` translated the T-SQL to DuckDB: the view and the Custom SQL match `mart_workforce_cost_growth_mix` row for row, and every check in 12 passes ("All checks match.").

## What changed

| File | Change |
|---|---|
| `sql/03_marts/mart_workforce_cost_growth_mix.sql`, `data/marts/mart_workforce_cost_growth_mix.csv` | Four columns: `opening_employees`, `closing_employees`, `opening_contingent`, `closing_contingent` (employees + contingent = headcount on every row) |
| `sqlserver/03f_build_dw_cost_growth_mix.sql` | New: `dw.WorkforceCostGrowthMix`, moved out of 03c so it can be rebuilt alone, with the four columns |
| `sqlserver/03c_build_dw_contingent.sql` | No longer builds the growth mix |
| `sqlserver/04b_create_reporting_views_contingent.sql` | `rpt.vw_workforce_cost_growth_mix` passes the four columns |
| `sqlserver/12_validate_contingent_workforce.sql` | Three checks: employees + contingent = headcount (0 rows), FY26 company employees 30,005, contingent workers 11,941 |
| `sqlserver/build_all.sql`, `check_tsql_in_duckdb.py` | Run 03f after 03e; the column check is case-insensitive, like T-SQL |
| `tableau/custom_sql_workforce_cost_growth_mix.sql` | The four columns |

## Steps

```bash
cd ~/GitHub/people-analytics-warehouse
git fetch origin && git checkout d6-builder && git pull      # or main, once merged
docker start arcadia-sql
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
for f in 03f_build_dw_cost_growth_mix 04b_create_reporting_views_contingent 12_validate_contingent_workforce; do
  docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/$f.sql
done
```

Look for `dw.WorkforceCostGrowthMix 1224`, and PASS on every line of 12.

Then in Tableau: Data → Workforce Cost Bridge → Extract → Refresh (or Edit Custom SQL with the new file, then refresh).

**Run 2026-10-29 on the Mac:** done; Dashboard #6 published on this data.
