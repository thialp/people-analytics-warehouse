/*
  custom_sql_position_fill.sql
  Tableau Custom SQL for Dashboard #3, Workforce Planning (SQL Server, database ArcadiaHR).
  Seat fills: one row per fill (external hire or internal move), FY22 to FY26, 30,575 rows.

  Reads the reporting view rpt.vw_position_fill (built by sqlserver/04_create_reporting_views.sql
  from the seat layer in 03b). The columns are listed so the data source documents itself and
  keeps the warehouse names (data dictionary: docs/warehouse/data_dictionary.md); the view has
  the same columns as the DuckDB mart, so a workbook can switch with Replace Data Source.

  Grain: one row per FILL. Count fills with COUNTD([Fill Id]) (or the row count); every
  measure on the row (pay walk, days) belongs to that one fill, so SUM and AVG are safe.
  Backfill columns (prior_*, level_change, location_change, pay walk) are NULL on net-new
  fills; reuse_candidate is TRUE only on net-new fills.

  Executive officers excluded (department D-901, the CEO and the eight function heads), as on
  Dashboards #1 and #2 and in custom_sql_wfp_summary.sql, so every Arcadia dashboard counts the
  same people. This view has no rows for them; the filter states the rule.

  Checked row for row against the DuckDB mart by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    v.fill_id,
    v.fill_date,
    v.fiscal_year,
    v.fiscal_quarter_label,
    v.fiscal_period,
    v.fill_type,
    v.seat_type,
    v.seat_decision,
    v.was_frozen,
    v.requisition_id,
    v.requisition_opened_date,
    v.requisition_approved_date,
    v.time_to_fill_days,
    v.vacancy_days,
    v.position_id,
    v.seat_created_date,
    v.seat_created_reason,
    v.worker_id,
    v.department_id,
    v.department_name,
    v.sub_function,
    v.function_name,
    v.cost_center_id,
    v.location_id,
    v.office_name,
    v.city,
    v.country_code,
    v.country_name,
    v.region,
    v.latitude,
    v.longitude,
    v.job_profile_id,
    v.job_title,
    v.job_family,
    v.grade,
    v.is_manager_seat,
    v.prior_worker_id,
    v.prior_end_date,
    v.prior_vacate_reason,
    v.prior_department_id,
    v.prior_location_id,
    v.prior_office_name,
    v.prior_city,
    v.prior_country_code,
    v.prior_country_name,
    v.prior_latitude,
    v.prior_longitude,
    v.prior_job_profile_id,
    v.prior_job_title,
    v.prior_grade,
    v.prior_is_manager_seat,
    v.level_change,
    v.location_change,
    v.prior_pay_usd_constant,
    v.new_pay_usd_constant,
    v.pay_change_usd_constant,
    v.level_effect_usd_constant,
    v.location_effect_usd_constant,
    v.market_effect_usd_constant,
    v.positioning_effect_usd_constant,
    v.reuse_candidate,
    v.reuse_candidate_seats,
    v.reuse_candidate_position_id,
    v.reuse_candidate_vacant_since,
    v.chain_id,
    v.parent_fill_id,
    v.chain_depth,
    v.chain_length,
    v.chain_trigger
FROM rpt.vw_position_fill AS v
WHERE v.department_id <> 'D-901'
