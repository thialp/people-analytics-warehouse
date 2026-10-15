/*
  custom_sql_cw_reconciliation.sql
  Tableau Custom SQL for Dashboard #6, Contingent Workforce: the trend (SQL Server, database ArcadiaHR).
  18,072 rows, the same columns and rows as data/marts/mart_cw_reconciliation.csv, so a workbook built on
  either can switch with Data > Replace Data Source.

  Reads the reporting view rpt.vw_cw_reconciliation (sqlserver/04b_create_reporting_views_contingent.sql).
  The columns are listed so the data source documents itself (data dictionary:
  docs/warehouse/data_dictionary.md).

  Two row types, never summed together: filter row_type in every calculation. Population rows (month-end x function x supplier) carry cw_working_bridgeway, cw_working_keystone and workers_with_any_discrepancy; Discrepancy rows (x type) carry workers_affected, new_this_month and the age bands. Share = workers_with_any_discrepancy / cw_working_bridgeway, on Population rows.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SELECT
    v.month_end_date,
    v.fiscal_year,
    v.fiscal_quarter_label,
    v.row_type,
    v.function_name,
    v.supplier_name,
    v.discrepancy_code,
    v.discrepancy_name,
    v.severity,
    v.who_can_fix_it,
    v.cw_working_bridgeway,
    v.cw_working_keystone,
    v.workers_with_any_discrepancy,
    v.workers_affected,
    v.new_this_month,
    v.aged_0_7,
    v.aged_8_30,
    v.aged_31_90,
    v.aged_over_90
FROM rpt.vw_cw_reconciliation AS v
