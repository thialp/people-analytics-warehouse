-- int_position_snapshot
-- One row per seat per month-end, for every seat that exists and is not eliminated on
-- that day: its status, incumbent, department, office, job and level, and how long it
-- has been in its current status. Feeds the vacancy pool and plan vs actual.
--
-- Control: on every month-end the Filled seats equal the worker snapshot headcount
-- (test 45), so the seat view and the people view of the company always agree.
CREATE OR REPLACE TABLE intermediate.int_position_snapshot AS
SELECT
    c.month_end_date,
    c.fiscal_year,
    h.position_id,
    h.status,
    h.status_since,
    DATE_DIFF('day', h.status_since, c.month_end_date) + 1 AS days_in_status,
    a.worker_id                                            AS incumbent_worker_id,
    h.department_id,
    h.cost_center_id,
    h.location_id,
    h.country_code,
    h.job_profile_id,
    h.job_family_code,
    h.grade,
    h.is_manager_seat,
    h.fte,
    h.created_date,
    h.created_reason,
    q.requisition_id                                       AS open_requisition_id
FROM intermediate.int_month_end_calendar AS c
JOIN intermediate.int_position_history AS h
  ON c.month_end_date BETWEEN h.effective_start_date AND h.effective_end_date_filled
 AND h.status <> 'Eliminated'
LEFT JOIN staging.stg_position_assignment AS a
  ON a.position_id = h.position_id
 AND c.month_end_date BETWEEN a.start_date AND a.end_date_filled
LEFT JOIN staging.stg_requisition AS q
  ON q.position_id = h.position_id
 AND c.month_end_date >= q.opened_date
 AND c.month_end_date < COALESCE(q.filled_date, q.cancelled_date, DATE '9999-12-31');
