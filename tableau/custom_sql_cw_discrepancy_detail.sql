/*
  custom_sql_cw_discrepancy_detail.sql
  Tableau Custom SQL for Dashboard #6, Contingent Workforce: the work list (SQL Server, database ArcadiaHR).
  6,908 rows, the same columns and rows as data/marts/mart_cw_discrepancy_detail.csv, so a workbook built on
  either can switch with Data > Replace Data Source.

  Reads the reporting view rpt.vw_cw_discrepancy_detail (sqlserver/04b_create_reporting_views_contingent.sql).
  The columns are listed so the data source documents itself (data dictionary:
  docs/warehouse/data_dictionary.md).

  One row per month-end x discrepancy x worker (or order, or timesheet), for the latest 13 month-ends. Filter to one month_end_date (usually the latest) before counting; count DISTINCT identity_id for people. Sort by severity, then age_days.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SELECT
    v.month_end_date,
    v.discrepancy_code,
    v.discrepancy_name,
    v.severity,
    v.who_can_fix_it,
    v.root_cause_code,
    v.root_cause_name,
    v.identity_id,
    v.bw_worker_id,
    v.person_id,
    v.worker_name,
    v.cw_type,
    v.match_confidence,
    v.supplier_name,
    v.cost_center_id,
    v.department_id,
    v.department_name,
    v.function_name,
    v.country_code,
    v.manager_worker_id,
    v.fields_affected,
    v.since_date,
    v.age_days,
    v.age_band,
    v.service_order_id,
    v.feed_event_id,
    v.timesheet_id,
    v.evidence
FROM rpt.vw_cw_discrepancy_detail AS v
