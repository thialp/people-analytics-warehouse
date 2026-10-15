/*
  custom_sql_cw_spend.sql
  Tableau Custom SQL for Contingent spend (Dashboards #2 panel and #5) (SQL Server, database ArcadiaHR).
  216,025 rows, the same columns and rows as data/marts/mart_cw_spend.csv, so a workbook built on
  either can switch with Data > Replace Data Source.

  Reads the reporting view rpt.vw_cw_spend (sqlserver/04b_create_reporting_views_contingent.sql).
  The columns are listed so the data source documents itself (data dictionary:
  docs/warehouse/data_dictionary.md).

  One row per month x cost center x supplier x contingent type x role family x billing currency: billed in the month (hours, units, amount in billing currency and in USD at nominal and constant rates) beside the workers at the month-end and their annualized run-rate. Billed amounts are flows (sum months); run-rates and workers_at_month_end are levels (read one month-end).

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SELECT
    v.month_end_date,
    v.fiscal_year,
    v.fiscal_quarter_label,
    v.cost_center_id,
    v.department_id,
    v.country_code,
    v.supplier_id,
    v.supplier_name,
    v.cw_type,
    v.role_family,
    v.billing_currency,
    v.workers_billed,
    v.billed_hours,
    v.billed_units,
    v.billed_amount_local,
    v.billed_usd_nominal,
    v.billed_usd_constant,
    v.workers_at_month_end,
    v.run_rate_local,
    v.run_rate_usd_nominal,
    v.run_rate_usd_constant
FROM rpt.vw_cw_spend AS v
