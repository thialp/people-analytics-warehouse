/*
  custom_sql_plan_vs_actual.sql
  Tableau Custom SQL for Dashboard #3, Workforce Planning (SQL Server, database ArcadiaHR).
  Plan vs actual: one row per plan version x cost center x fiscal quarter, 29,365 rows (615 of them
  are cost centers with contingent workers only: zero on every employee measure).

  Reads the reporting view rpt.vw_plan_vs_actual (built by sqlserver/04_create_reporting_views.sql
  from the seat layer in 03b). The columns are listed so the data source documents itself and
  keeps the warehouse names (data dictionary: docs/warehouse/data_dictionary.md); the view has
  the same columns as the DuckDB mart, so a workbook can switch with Replace Data Source.

  Grain: one row per PLAN VERSION x COST CENTER x QUARTER. The actual_* columns repeat in
  every version that covers the quarter, so ALWAYS filter to one plan_version (or
  is_latest_version) before summing. planned/actual_net_new and _backfills are flows (sum
  over quarters); planned/actual_ending_headcount, _fte and _cost are levels (read the
  quarter you want, usually quarter_end_date = the fiscal year-end, never sum quarters).

  Release 3: the plan's contingent line beside its actuals. actual_cw_headcount is the contingent
  workers Bridgeway counted on the quarter-end; actual_cw_spend_usd_plan_fx their annualized bill
  run-rate at the plan's FX rates (compare with planned_cw_spend_usd), _constant at the constant
  rate set. Like headcount, these are levels.

  Executive officers excluded (department D-901, the CEO and the eight function heads), as on
  Dashboards #1 and #2 and in custom_sql_wfp_summary.sql, so every Arcadia dashboard counts the
  same people. The plan carries 50 such rows; fills and the vacancy pool have none.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    v.plan_version,
    v.version_type,
    v.version_order,
    v.version_date,
    v.is_latest_version,
    v.fiscal_year,
    v.fiscal_quarter,
    v.fiscal_quarter_label,
    v.quarter_end_date,
    v.cost_center_id,
    v.cost_center_name,
    v.department_id,
    v.department_name,
    v.sub_function,
    v.function_name,
    v.country_code,
    v.country_name,
    v.region,
    v.planned_ending_headcount,
    v.actual_ending_headcount,
    v.planned_ending_fte,
    v.actual_ending_fte,
    v.planned_net_new,
    v.actual_net_new,
    v.actual_net_new_reuse_candidates,
    v.planned_backfills,
    v.actual_backfills,
    v.actual_external_hires,
    v.actual_internal_moves,
    v.planned_cost_usd,
    v.actual_cost_usd_plan_fx,
    v.actual_cost_usd_constant,
    v.planned_cw_headcount,
    v.actual_cw_headcount,
    v.planned_cw_spend_usd,
    v.actual_cw_spend_usd_plan_fx,
    v.actual_cw_spend_usd_constant,
    v.plan_fx_rate_date
FROM rpt.vw_plan_vs_actual AS v
WHERE v.department_id <> 'D-901'
