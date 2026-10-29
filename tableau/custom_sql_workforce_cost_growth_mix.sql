/*
  custom_sql_workforce_cost_growth_mix.sql
  Tableau Custom SQL for Dashboard #6, Workforce Cost Bridge: the growth mix (SQL Server, database ArcadiaHR).
  1,224 rows, the same columns and rows as data/marts/mart_workforce_cost_growth_mix.csv, so a workbook built on
  either can switch with Data > Replace Data Source.

  Reads the reporting view rpt.vw_workforce_cost_growth_mix (sqlserver/04b_create_reporting_views_contingent.sql).
  The columns are listed so the data source documents itself (data dictionary:
  docs/warehouse/data_dictionary.md).

  One row per year-over-year pair of quarter-ends x view (Company, Function) x group x factor: Opening cost (factor_order 0), the six factors (1-6) and Closing cost (7), with the Shapley effect, the sequential effect and the order bias. Filter to one to_month_end, view_name and group_name; Opening + the six Shapley effects = Closing.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SELECT
    v.from_month_end,
    v.to_month_end,
    v.fiscal_year,
    v.fiscal_quarter_label,
    v.pair_type,
    v.view_order,
    v.view_name,
    v.group_name,
    v.factor_order,
    v.factor,
    v.factor_meaning,
    v.shapley_effect_usd,
    v.sequential_effect_usd,
    v.order_bias_usd,
    v.opening_headcount,
    v.closing_headcount,
    v.opening_employees,
    v.closing_employees,
    v.opening_contingent,
    v.closing_contingent
FROM rpt.vw_workforce_cost_growth_mix AS v
