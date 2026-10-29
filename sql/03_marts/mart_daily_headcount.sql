-- mart_daily_headcount (release 6)
-- Grain: one row per calendar day x department with anybody in it, from the first month-end of the
-- history to the data-through date.
--
-- Employees counted the same way as int_worker_month_end_snapshot, on every day instead of every
-- month-end: employed that day (the termination date is the last day worked), the job record in effect
-- that day, executive officers excluded. So on every month-end it equals the month-end snapshot
-- (test_92), and Jun 30, 2026 is 30,005.
--
-- Days after the report date come from Keystone's nightly Core HR extract (the data-through date,
-- generator/core_hr_extract.py): they are the period to date, not a closed month. is_closed says which.
-- This is the source for "to date" comparisons: year, quarter and month to date on the latest day,
-- against the same day of an earlier period.
CREATE OR REPLACE TABLE marts.mart_daily_headcount AS
WITH cal AS (
    SELECT report_as_of_date, data_through_date FROM staging.stg_report_calendar
),
days AS (
    SELECT CAST(d AS DATE) AS as_of_date
    FROM range((SELECT MIN(month_end_date) FROM intermediate.int_month_end_calendar),
               (SELECT data_through_date FROM cal) + INTERVAL 1 DAY,
               INTERVAL 1 DAY) AS t(d)
)
SELECT
    d.as_of_date,
    d.as_of_date <= cal.report_as_of_date                    AS is_closed,
    dep.function_name,
    dep.sub_function,
    dep.department_name,
    COUNT(*)                                                 AS employees
FROM days AS d
CROSS JOIN cal
JOIN staging.stg_worker AS w
  ON w.original_hire_date <= d.as_of_date
 AND (w.termination_date IS NULL OR w.termination_date >= d.as_of_date)
JOIN staging.stg_job_history AS j
  ON j.worker_id = w.worker_id
 AND d.as_of_date BETWEEN j.effective_start_date AND j.effective_end_date_filled
JOIN staging.stg_department AS dep
  ON dep.department_id = j.department_id
WHERE NOT w.is_executive_officer
GROUP BY ALL
ORDER BY d.as_of_date, dep.function_name, dep.department_name;
