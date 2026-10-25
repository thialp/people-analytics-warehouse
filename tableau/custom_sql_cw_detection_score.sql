/*
  custom_sql_cw_detection_score.sql
  Tableau Custom SQL for Dashboard #4, Contingent Workforce: methodology page (detection score) (SQL Server, database ArcadiaHR).
  761 rows, the same columns and rows as data/marts/mart_cw_detection_score.csv, so a workbook built on
  either can switch with Data > Replace Data Source.

  Reads the reporting view rpt.vw_cw_detection_score (sqlserver/04b_create_reporting_views_contingent.sql).
  The columns are listed so the data source documents itself (data dictionary:
  docs/warehouse/data_dictionary.md).

  One row per month-end x discrepancy type: injected (planted by the generator), detected, missed, false flags, recall, precision. Sum the counts, then divide; never average recall across rows.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SELECT
    v.month_end_date,
    v.fiscal_year,
    v.discrepancy_code,
    v.discrepancy_name,
    v.severity,
    v.injected,
    v.detected,
    v.missed,
    v.false_flags,
    v.recall,
    v.[precision]
FROM rpt.vw_cw_detection_score AS v
