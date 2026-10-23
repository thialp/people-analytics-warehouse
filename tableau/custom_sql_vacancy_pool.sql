/*
  custom_sql_vacancy_pool.sql
  Tableau Custom SQL for Dashboard #3, Workforce Planning (SQL Server, database ArcadiaHR).
  Vacancy pool: one row per vacant PID (Open or Frozen) per month-end, employee and contingent
  (release 3.1: contingent PIDs added; worker_type says which).

  Reads the reporting view rpt.vw_vacancy_pool (built by sqlserver/04_create_reporting_views.sql
  from the seat layer in 03b). The columns are listed so the data source documents itself and
  keeps the warehouse names (data dictionary: docs/warehouse/data_dictionary.md); the view has
  the same columns as the DuckDB mart, so a workbook can switch with Replace Data Source.

  Grain: one row per SEAT per MONTH-END. The same seat appears every month it stays empty,
  so ALWAYS filter to one month_end_date (or use is_fiscal_year_end + fiscal_year) before
  counting: COUNTD([Position Id]) for seats, SUM(INT([Is Stale])) for seats empty 90+ days.

  Executive officers excluded (department D-901, the CEO and the eight function heads), as on
  Dashboards #1 and #2 and in custom_sql_wfp_summary.sql, so every Arcadia dashboard counts the
  same people. This view has no rows for them; the filter states the rule.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    v.month_end_date,
    v.fiscal_year,
    v.fiscal_quarter_label,
    v.is_fiscal_year_end,
    v.position_id,
    v.status,
    v.status_since,
    v.days_in_status,
    v.vacated_by,
    v.vacated_date,
    v.days_vacant,
    v.vacancy_age_band,
    v.is_stale,
    v.open_requisition_id,
    v.req_type,
    v.requisition_approved_date,
    v.department_id,
    v.department_name,
    v.sub_function,
    v.function_name,
    v.cost_center_id,
    v.location_id,
    v.office_name,
    v.country_code,
    v.country_name,
    v.region,
    v.job_profile_id,
    v.job_title,
    v.job_family,
    v.grade,
    v.is_manager_seat,
    v.created_date,
    v.created_reason,
    v.worker_type,
    v.cw_type,
    v.cw_role_family
FROM rpt.vw_vacancy_pool AS v
WHERE v.department_id <> 'D-901'
