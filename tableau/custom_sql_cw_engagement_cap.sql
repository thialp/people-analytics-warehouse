/*
  custom_sql_cw_engagement_cap.sql
  Tableau Custom SQL for Dashboard #4, Contingent Workforce: the 48-month cap (SQL Server, database ArcadiaHR).
  42,116 rows, the same columns and rows as data/marts/mart_cw_engagement_cap.csv, so a workbook built on
  either can switch with Data > Replace Data Source.

  Reads the reporting view rpt.vw_cw_engagement_cap (sqlserver/04b_create_reporting_views_contingent.sql).
  The columns are listed so the data source documents itself (data dictionary:
  docs/warehouse/data_dictionary.md).

  One row per Bridgeway worker who started, as Bridgeway holds it on the extract date (30 Jun 2026). cap_band groups engagements by months left before the cap; BPO has no cap.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SELECT
    v.bw_worker_id,
    v.identity_id,
    v.person_id,
    v.worker_name,
    v.cw_type,
    v.supplier_name,
    v.original_start_date,
    v.last_day,
    v.is_working_at_extract,
    v.engagement_status,
    v.months_engaged,
    v.extensions,
    v.renewals,
    v.cap_date,
    v.months_left_at_extract,
    v.is_over_cap,
    v.cap_band
FROM rpt.vw_cw_engagement_cap AS v
