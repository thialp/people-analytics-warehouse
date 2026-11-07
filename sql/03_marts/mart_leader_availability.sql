-- mart_leader_availability
-- Grain: one row per leader x worker type x day, for the report date and the 30 days after it
-- (release 7, case study 7: the "At work on" calendar).
--
-- People are everyone below the leader on the report date (executive officers excluded) who is
-- still in the team that day. At work = people - time off - leave - public holiday, on weekdays;
-- weekends carry the people count and no at-work number. A half day off counts as at work.
-- left_team counts the people of the report date who are gone by that day: mostly contingent
-- assignments that end on the fiscal year-end with no extension on file yet.
CREATE OR REPLACE TABLE marts.mart_leader_availability AS
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar),
wt AS (SELECT * FROM (VALUES ('All'), ('Employees'), ('Contingent')) AS t (worker_type)),
below AS (
    SELECT c.ancestor_id AS leader_id, a.*
    FROM intermediate.int_org_closure AS c
    JOIN rc ON c.month_end_date = rc.report_as_of_date
    JOIN intermediate.int_org_leader AS l ON l.month_end_date = c.month_end_date AND l.leader_id = c.ancestor_id
    JOIN intermediate.int_person_availability_day AS a ON a.person_id = c.descendant_id
    WHERE c.depth >= 1
)
SELECT b.leader_id, wt.worker_type, b.day, b.day_offset,
       isodow(b.day) > 5                                                     AS is_weekend,
       COUNT(*) FILTER (WHERE b.day_status <> 'Not in the team')             AS people,
       CASE WHEN isodow(b.day) <= 5 THEN COUNT(*) FILTER (WHERE b.day_status = 'At work') END AS at_work,
       COUNT(*) FILTER (WHERE b.day_status IN ('Time off', 'Leave', 'Public holiday')) AS off,
       COUNT(*) FILTER (WHERE b.day_status = 'Time off')                     AS off_time_off,
       COUNT(*) FILTER (WHERE b.day_status = 'Leave')                        AS off_leave,
       COUNT(*) FILTER (WHERE b.day_status = 'Public holiday')               AS off_public_holiday,
       COUNT(*) FILTER (WHERE b.day_status = 'Not in the team')              AS left_team
FROM below AS b
JOIN wt ON wt.worker_type = 'All'
        OR (wt.worker_type = 'Employees' AND b.worker_type = 'Employee')
        OR (wt.worker_type = 'Contingent' AND b.worker_type = 'Contingent')
GROUP BY 1, 2, 3, 4, 5;
