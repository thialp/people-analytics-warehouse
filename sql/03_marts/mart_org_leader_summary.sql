-- mart_org_leader_summary
-- Grain: one row per org leader per fiscal year-end (June 30) and the latest month-end.
--
-- The org chart at the top of the company: the CEO, the eight function heads, the
-- sub-function heads and every department head, with the unit they lead, who they
-- report to, and how many people report to them directly and in total (direct plus
-- everyone below them, from the reporting chain). Names and people are fictional.
CREATE OR REPLACE TABLE marts.mart_org_leader_summary AS
WITH dates AS (
    SELECT month_end_date FROM intermediate.int_month_end_calendar
    WHERE is_fiscal_year_end OR month_end_date = (SELECT MAX(month_end_date) FROM intermediate.int_month_end_calendar)
)
SELECT
    s.month_end_date,
    cal.fiscal_year,
    ou.org_unit_type,
    s.leads_org_unit_id                         AS org_unit_id,
    ou.org_unit_name,
    ou.parent_org_unit_id,
    ou.function_name,
    ou.leader_title,
    s.worker_id,
    w.worker_name,
    jp.job_title,
    s.grade,
    s.department_id,
    loc.office_name,
    s.manager_worker_id,
    mw.worker_name                              AS manager_name,
    rl.direct_reports,
    rl.total_reports,
    rl.layers_from_ceo
FROM intermediate.int_worker_month_end_snapshot AS s
JOIN dates                                  ON dates.month_end_date = s.month_end_date
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = s.month_end_date
JOIN staging.stg_org_unit AS ou             ON ou.org_unit_id = s.leads_org_unit_id
JOIN staging.stg_worker AS w                ON w.worker_id = s.worker_id
LEFT JOIN staging.stg_worker AS mw          ON mw.worker_id = s.manager_worker_id
LEFT JOIN staging.stg_job_profile AS jp     ON jp.job_profile_id = s.job_profile_id
LEFT JOIN staging.stg_location AS loc       ON loc.location_id = s.location_id
JOIN intermediate.int_worker_reporting_line AS rl
  ON rl.month_end_date = s.month_end_date AND rl.worker_id = s.worker_id
ORDER BY s.month_end_date,
         CASE ou.org_unit_type WHEN 'Company' THEN 1 WHEN 'Function' THEN 2 WHEN 'Sub-function' THEN 3 ELSE 4 END,
         s.leads_org_unit_id;
