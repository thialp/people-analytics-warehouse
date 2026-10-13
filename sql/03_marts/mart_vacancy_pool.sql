-- mart_vacancy_pool
-- Grain: one row per vacant seat (Open or Frozen) per month-end.
-- The pool of empty seats at each month-end: where they are, at what level, how long
-- they have been empty, why (who left, or never filled), and whether hiring is open.
-- A seat empty 90 days or more is stale: it is what a net-new seat could have reused
-- (see reuse_candidate in mart_position_fill).
CREATE OR REPLACE TABLE marts.mart_vacancy_pool AS
WITH last_exit AS (   -- the most recent incumbent to leave each seat before the month-end
    SELECT s.month_end_date, s.position_id,
           MAX(a.end_date)                         AS vacated_date,
           ARG_MAX(a.vacate_reason, a.end_date)    AS vacate_reason
    FROM intermediate.int_position_snapshot AS s
    JOIN staging.stg_position_assignment AS a
      ON a.position_id = s.position_id AND a.end_date < s.month_end_date
    WHERE s.status IN ('Open', 'Frozen')
    GROUP BY ALL
)
SELECT
    s.month_end_date,
    s.fiscal_year,
    cal.fiscal_quarter_label,
    cal.is_fiscal_year_end,
    s.position_id,
    s.status,
    s.status_since,
    s.days_in_status,
    COALESCE(e.vacate_reason, 'Never filled')                                    AS vacated_by,
    e.vacated_date,
    DATE_DIFF('day', COALESCE(e.vacated_date + INTERVAL 1 DAY, s.created_date), s.month_end_date) + 1 AS days_vacant,
    CASE WHEN DATE_DIFF('day', COALESCE(e.vacated_date + INTERVAL 1 DAY, s.created_date), s.month_end_date) + 1 <= 30  THEN '0-30 days'
         WHEN DATE_DIFF('day', COALESCE(e.vacated_date + INTERVAL 1 DAY, s.created_date), s.month_end_date) + 1 <= 90  THEN '31-90 days'
         WHEN DATE_DIFF('day', COALESCE(e.vacated_date + INTERVAL 1 DAY, s.created_date), s.month_end_date) + 1 <= 180 THEN '91-180 days'
         ELSE 'Over 180 days' END                                               AS vacancy_age_band,
    DATE_DIFF('day', COALESCE(e.vacated_date + INTERVAL 1 DAY, s.created_date), s.month_end_date) + 1 >= 90 AS is_stale,
    s.open_requisition_id,
    q.req_type,
    q.approved_date                                                             AS requisition_approved_date,
    s.department_id,
    d.department_name,
    d.sub_function,
    d.function_name,
    s.cost_center_id,
    s.location_id,
    l.office_name,
    s.country_code,
    l.country_name,
    l.region,
    s.job_profile_id,
    jp.job_title,
    jp.job_family,
    s.grade,
    s.is_manager_seat,
    s.created_date,
    s.created_reason
FROM intermediate.int_position_snapshot AS s
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = s.month_end_date
LEFT JOIN last_exit AS e ON e.month_end_date = s.month_end_date AND e.position_id = s.position_id
LEFT JOIN staging.stg_requisition AS q ON q.requisition_id = s.open_requisition_id
JOIN staging.stg_department  AS d  ON d.department_id   = s.department_id
JOIN staging.stg_location    AS l  ON l.location_id     = s.location_id
JOIN staging.stg_job_profile AS jp ON jp.job_profile_id = s.job_profile_id
WHERE s.status IN ('Open', 'Frozen')
ORDER BY s.month_end_date, s.position_id;
