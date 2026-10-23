-- int_cw_position_snapshot
-- One row per contingent PID per month-end, for every contingent PID that exists and is not
-- closed that day (release 3.1): Filled or Open (vacant), the holder, the department, cost
-- center and office, the contingent type and role, and since when the PID has been vacant.
--
-- Control: on every month-end the Filled contingent PIDs equal the contingent headcount in
-- int_cw_month_end_snapshot, by department and country (test 81).
CREATE OR REPLACE TABLE intermediate.int_cw_position_snapshot AS
WITH runs AS (
    SELECT p.*,
           SUM(CASE WHEN p.status = p.prev_status THEN 0 ELSE 1 END)
               OVER (PARTITION BY p.position_id ORDER BY p.effective_start_date) AS run_id
    FROM (SELECT s.*, LAG(s.status) OVER (PARTITION BY s.position_id ORDER BY s.effective_start_date) AS prev_status
          FROM staging.stg_cw_position AS s) AS p
),
hist AS (
    SELECT r.*, MIN(r.effective_start_date) OVER (PARTITION BY r.position_id, r.run_id) AS status_since
    FROM runs AS r
)
SELECT
    c.month_end_date,
    c.fiscal_year,
    h.position_id,
    h.status,
    h.status_since,
    DATE_DIFF('day', h.status_since, c.month_end_date) + 1 AS days_in_status,
    a.worker_id                                            AS incumbent_worker_id,
    a.bw_worker_id                                         AS incumbent_bw_worker_id,
    h.department_id,
    h.cost_center_id,
    h.location_id,
    l.country_code,
    h.cw_type,
    h.cw_role_family,
    h.created_date,
    h.created_reason
FROM intermediate.int_month_end_calendar AS c
JOIN hist AS h
  ON c.month_end_date BETWEEN h.effective_start_date AND h.effective_end_date_filled
 AND h.status <> 'Eliminated'
JOIN staging.stg_location AS l ON l.location_id = h.location_id
LEFT JOIN staging.stg_cw_position_assignment AS a
  ON a.position_id = h.position_id
 AND c.month_end_date BETWEEN a.start_date AND a.end_date_filled;
