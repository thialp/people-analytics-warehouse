-- int_position_snapshot
-- One row per seat per month-end, for every seat that exists and is not eliminated on
-- that day: its status, incumbent, department, office, job and level, and how long it
-- has been in its current status. Feeds the vacancy pool and plan vs actual.
--
-- Control: on every month-end the Filled seats equal the worker snapshot headcount
-- (test 45), so the seat view and the people view of the company always agree.
CREATE OR REPLACE TABLE intermediate.int_position_snapshot AS
WITH status_runs AS (
    -- consecutive records with the same status form one run; status_since is its start
    SELECT
        p.*,
        SUM(CASE WHEN p.status = p.prev_status THEN 0 ELSE 1 END)
            OVER (PARTITION BY p.position_id ORDER BY p.effective_start_date) AS run_id
    FROM (
        SELECT *, LAG(status) OVER (PARTITION BY position_id ORDER BY effective_start_date) AS prev_status
        FROM staging.stg_position
    ) AS p
),
runs AS (
    SELECT *, MIN(effective_start_date) OVER (PARTITION BY position_id, run_id) AS status_since
    FROM status_runs
)
SELECT
    c.month_end_date,
    c.fiscal_year,
    r.position_id,
    r.status,
    r.status_since,
    DATE_DIFF('day', r.status_since, c.month_end_date) + 1 AS days_in_status,
    a.worker_id                                            AS incumbent_worker_id,
    r.department_id,
    r.location_id,
    l.country_code,
    r.job_profile_id,
    jp.job_family_code,
    r.grade,
    r.fte,
    r.created_date,
    r.created_reason,
    q.requisition_id                                       AS open_requisition_id
FROM intermediate.int_month_end_calendar AS c
JOIN runs AS r
  ON c.month_end_date BETWEEN r.effective_start_date AND r.effective_end_date_filled
 AND r.status <> 'Eliminated'
JOIN staging.stg_location AS l ON l.location_id = r.location_id
JOIN staging.stg_job_profile AS jp ON jp.job_profile_id = r.job_profile_id
LEFT JOIN staging.stg_position_assignment AS a
  ON a.position_id = r.position_id
 AND c.month_end_date BETWEEN a.start_date AND a.end_date_filled
LEFT JOIN staging.stg_requisition AS q
  ON q.position_id = r.position_id
 AND c.month_end_date >= q.opened_date
 AND c.month_end_date < COALESCE(q.filled_date, q.cancelled_date, DATE '9999-12-31');
