-- Release 7 time off: requests and leaves sit inside employment and run forward; no employee is off
-- twice on one day once corrections have taken days back (a sick day can fall on a day a
-- correction returned); every contingent request Keystone holds is a Bridgeway booking with the same days;
-- every booking sits inside its Bridgeway assignment.
SELECT 'request outside employment' AS problem, r.time_off_request_id AS id
FROM staging.stg_time_off_request AS r
JOIN staging.stg_worker AS w ON w.worker_id = r.person_id
WHERE r.source_system = 'KS'
  AND (r.first_day < w.original_hire_date OR r.last_day > COALESCE(w.termination_date, DATE '9999-12-31')
       OR r.last_day < r.first_day)
UNION ALL
SELECT 'leave runs backward', leave_id FROM staging.stg_leave_of_absence
WHERE COALESCE(actual_last_day_of_leave, estimated_last_day_of_leave) < first_day_of_leave
UNION ALL
SELECT 'two requests on one day', r.person_id || ' ' || CAST(r.day AS VARCHAR)
FROM (
    SELECT q.person_id, CAST(d.day AS DATE) AS day,
           SUM(CASE WHEN q.request_type = 'Absence Request' THEN 1 ELSE -1 END) AS net
    FROM staging.stg_time_off_request AS q
    CROSS JOIN generate_series(q.first_day, q.last_day, INTERVAL 1 DAY) AS d (day)
    WHERE q.source_system = 'KS' AND isodow(d.day) <= 5
    GROUP BY 1, 2
) AS r
WHERE r.net > 1
UNION ALL
SELECT 'Keystone copy differs from Bridgeway', r.time_off_request_id
FROM staging.stg_time_off_request AS r
LEFT JOIN staging.stg_bw_time_off AS b ON b.booking_id = r.bw_booking_id
WHERE r.source_system = 'BW'
  AND (b.booking_id IS NULL OR b.first_day <> r.first_day OR b.last_day <> r.last_day)
UNION ALL
SELECT 'booking outside the assignment', b.booking_id
FROM staging.stg_bw_time_off AS b
JOIN staging.stg_bw_service_order_revision AS v ON v.service_order_id = b.service_order_id AND v.is_current
WHERE b.first_day < v.assignment_start_date OR b.last_day > v.assignment_end_date
