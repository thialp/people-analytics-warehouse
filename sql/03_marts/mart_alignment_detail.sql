-- mart_alignment_detail
-- Grain: one row per person x alignment signal on the report date: the roster behind every gap
-- (release 7, case study 7), with the L0, L1 and L2 leaders above the person so any leader's page
-- can list their own. A flag, never an error.
CREATE OR REPLACE TABLE marts.mart_alignment_detail AS
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar),
above AS (      -- the deepest L0 (the function head over the CEO), the L1 and the L2 above each person
    SELECT c.descendant_id AS person_id,
           ARG_MAX(l.leader_id, l.depth_from_top) FILTER (WHERE l.leader_level = 'L0') AS l0_leader_id,
           MAX(l.leader_id) FILTER (WHERE l.leader_level = 'L1')                      AS l1_leader_id,
           MAX(l.leader_id) FILTER (WHERE l.leader_level = 'L2')                      AS l2_leader_id
    FROM intermediate.int_org_closure AS c
    JOIN rc ON c.month_end_date = rc.report_as_of_date
    JOIN intermediate.int_org_leader AS l ON l.month_end_date = c.month_end_date AND l.leader_id = c.ancestor_id
    WHERE c.depth >= 1
    GROUP BY 1
)
SELECT s.month_end_date AS as_of_date, s.person_id, p.person_name, p.worker_type, p.job_title,
       p.department_name, p.function_name, loc.office_name, p.country_code, p.region,
       p.manager_worker_id, m.person_name AS manager_name, m.department_name AS manager_department_name,
       p.manager_source,
       s.signal_code, s.signal_name, s.signal_line, s.signal_detail,
       a.l0_leader_id, a.l1_leader_id, a.l2_leader_id
FROM intermediate.int_alignment_signal AS s
JOIN rc ON s.month_end_date = rc.report_as_of_date
JOIN intermediate.int_person_month_end AS p ON p.month_end_date = s.month_end_date AND p.person_id = s.person_id
JOIN staging.stg_location AS loc ON loc.location_id = p.location_id
LEFT JOIN intermediate.int_person_month_end AS m ON m.month_end_date = p.month_end_date AND m.person_id = p.manager_worker_id
LEFT JOIN above AS a ON a.person_id = s.person_id
ORDER BY ALL;
