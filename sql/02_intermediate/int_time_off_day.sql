-- int_time_off_day
-- Grain: one row per person x weekday they are off, from the start of the report's fiscal year to
-- 60 days past the report date (release 7, case study 7).
--
-- For a leader it does not matter whether someone is on time off or on leave: they are off. The
-- warehouse keeps the reason for analysis (Leave wins over Time off on the same day).
--   * Employees: approved Keystone requests, full days only (a half day still counts as at work),
--     minus the days a later correction took back; and Keystone leaves of absence, every weekday
--     from the first day of leave to the actual last day, or the estimated one while it is unknown.
--   * Contingent workers: their bookings in Bridgeway, the source of truth for their time
--     (Keystone holds a copy the feed delivered). Keyed like int_person_month_end: the Keystone
--     person ID when the worker is matched, otherwise the Bridgeway worker ID.
-- Public holidays are applied by the availability mart, by country, and win over both.
CREATE OR REPLACE TABLE intermediate.int_time_off_day AS
WITH rc AS (
    SELECT make_date(CAST(current_fiscal_year AS INTEGER) - 1, 7, 1) AS window_start,
           report_as_of_date + INTERVAL 60 DAY                        AS window_end
    FROM staging.stg_report_calendar
),
emp_req AS (
    SELECT r.person_id, r.time_off_request_id AS source_id, CAST(d.day AS DATE) AS off_date
    FROM staging.stg_time_off_request AS r
    CROSS JOIN rc
    CROSS JOIN generate_series(r.first_day, r.last_day, INTERVAL 1 DAY) AS d(day)
    WHERE r.source_system = 'KS' AND r.request_type = 'Absence Request' AND r.days_requested >= 1
      AND isodow(d.day) <= 5 AND CAST(d.day AS DATE) BETWEEN rc.window_start AND rc.window_end
),
emp_back AS (
    SELECT r.person_id, CAST(d.day AS DATE) AS off_date
    FROM staging.stg_time_off_request AS r
    CROSS JOIN generate_series(r.first_day, r.last_day, INTERVAL 1 DAY) AS d(day)
    WHERE r.source_system = 'KS' AND r.request_type = 'Absence Correction'
),
emp_pto AS (
    SELECT e.person_id, 'Employee' AS worker_type, e.off_date, 'Time off' AS off_reason, e.source_id
    FROM emp_req AS e
    ANTI JOIN emp_back AS b ON b.person_id = e.person_id AND b.off_date = e.off_date
),
leave AS (
    SELECT l.worker_id AS person_id, 'Employee' AS worker_type, CAST(d.day AS DATE) AS off_date,
           'Leave' AS off_reason, l.leave_id AS source_id
    FROM staging.stg_leave_of_absence AS l
    CROSS JOIN rc
    CROSS JOIN generate_series(l.first_day_of_leave, COALESCE(l.actual_last_day_of_leave, l.estimated_last_day_of_leave),
                               INTERVAL 1 DAY) AS d(day)
    WHERE isodow(d.day) <= 5 AND CAST(d.day AS DATE) BETWEEN rc.window_start AND rc.window_end
),
cw AS (
    SELECT COALESCE(ir.person_id, b.bw_worker_id) AS person_id, 'Contingent' AS worker_type,
           CAST(d.day AS DATE) AS off_date, 'Time off' AS off_reason, b.booking_id AS source_id
    FROM staging.stg_bw_time_off AS b
    CROSS JOIN rc
    CROSS JOIN generate_series(b.first_day, b.last_day, INTERVAL 1 DAY) AS d(day)
    LEFT JOIN intermediate.int_cw_identity_resolution AS ir
           ON ir.bw_worker_id = b.bw_worker_id AND ir.person_id IS NOT NULL
    WHERE isodow(d.day) <= 5 AND CAST(d.day AS DATE) BETWEEN rc.window_start AND rc.window_end
)
SELECT person_id, worker_type, off_date, off_reason, source_id
FROM (SELECT * FROM emp_pto UNION ALL SELECT * FROM leave UNION ALL SELECT * FROM cw)
QUALIFY ROW_NUMBER() OVER (PARTITION BY person_id, off_date
                           ORDER BY CASE off_reason WHEN 'Leave' THEN 1 ELSE 2 END, source_id) = 1;
