-- int_person_availability_day
-- Grain: one row per person in the workforce on the report date x day, for the report date and the
-- 30 days after it (release 7, case study 7: "who is at work on ...").
--
-- The organization is the one on the report date: a leader planning the next 30 days looks at the
-- team they have today. A day's status, first match wins:
--   Not in the team    an employee whose termination is on file for an earlier day; a contingent
--                      worker whose Bridgeway assignment has ended (many end on the fiscal year-end
--                      with no extension on file yet: the page says how many)
--   Weekend            Saturday or Sunday
--   Public holiday     a national holiday in the country they sit in
--   Leave / Time off   int_time_off_day
--   At work            everyone else
-- Requests are known only once they are made, so the further a day lies past the data-through
-- date, the fewer people show as off: the page says so.
CREATE OR REPLACE TABLE intermediate.int_person_availability_day AS
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar),
days AS (
    SELECT CAST(rc.report_as_of_date + t.i * INTERVAL 1 DAY AS DATE) AS day, t.i AS day_offset
    FROM rc CROSS JOIN range(0, 31) AS t (i)
),
ppl AS (
    SELECT p.person_id, p.worker_type, p.country_code, w.termination_date, s.assignment_end_date
    FROM intermediate.int_person_month_end AS p
    JOIN rc ON p.month_end_date = rc.report_as_of_date
    LEFT JOIN staging.stg_worker AS w ON p.worker_type = 'Employee' AND w.worker_id = p.person_id
    LEFT JOIN intermediate.int_cw_month_end_snapshot AS s
           ON p.worker_type = 'Contingent' AND s.month_end_date = rc.report_as_of_date AND s.bw_worker_id = p.bw_worker_id
    WHERE NOT p.is_executive_officer
)
SELECT ppl.person_id, ppl.worker_type, d.day, d.day_offset,
       CASE WHEN (ppl.worker_type = 'Employee' AND ppl.termination_date < d.day)
              OR (ppl.worker_type = 'Contingent' AND ppl.assignment_end_date < d.day) THEN 'Not in the team'
            WHEN isodow(d.day) > 5 THEN 'Weekend'
            WHEN h.holiday_date IS NOT NULL THEN 'Public holiday'
            WHEN t.off_reason IS NOT NULL THEN t.off_reason
            ELSE 'At work' END AS day_status
FROM ppl
CROSS JOIN days AS d
LEFT JOIN staging.stg_public_holiday AS h ON h.country_code = ppl.country_code AND h.holiday_date = d.day
LEFT JOIN intermediate.int_time_off_day AS t ON t.person_id = ppl.person_id AND t.off_date = d.day;
