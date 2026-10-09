-- mart_reporting_line
-- Grain: one row per active worker per fiscal year-end (June 30).
--
-- Who reports to whom, for an org explorer in Tableau: direct manager, skip-level
-- manager, department head and function head, layers below the CEO, and the size of
-- each person's own organization. Fiscal year-ends only, to keep the export small;
-- the warehouse holds every month-end in intermediate.int_worker_reporting_line.
CREATE OR REPLACE TABLE marts.mart_reporting_line AS
SELECT
    rl.month_end_date,
    cal.fiscal_year,
    rl.worker_id,
    s.department_id,
    s.location_id,
    s.grade,
    s.job_profile_id,
    s.is_people_manager,
    rl.manager_worker_id,
    rl.skip_level_manager_id,
    rl.department_head_id,
    rl.function_head_id,
    rl.function_org_unit_id,
    rl.layers_from_ceo,
    rl.direct_reports,
    rl.total_reports
FROM intermediate.int_worker_reporting_line AS rl
JOIN intermediate.int_month_end_calendar AS cal
  ON cal.month_end_date = rl.month_end_date AND cal.is_fiscal_year_end
JOIN intermediate.int_worker_month_end_snapshot AS s
  ON s.month_end_date = rl.month_end_date AND s.worker_id = rl.worker_id
ORDER BY rl.month_end_date, rl.worker_id;
