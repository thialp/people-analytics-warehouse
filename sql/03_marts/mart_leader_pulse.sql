-- mart_leader_pulse
-- Grain: one row per leader on the report date x worker type (All, Employees, Contingent) x month-end,
-- for the 13 month-ends that end on the report date (release 7, case study 7: the Team pulse card and
-- the Tableau Cloud Pulse metrics).
--
--   people, gap_people   as in int_leader_org (executive officers excluded), for the trend lines
--   hub_people           people below the leader whose office is one of their own function's hubs
--                        (stg_function_hub)
-- On the report date's row only (month_index 12), the days ahead:
--   dip_*                the weekday with the lowest share at work in the next seven days (the report
--                        date included; ties go to the earlier day), and the public holiday (and its
--                        country) that keeps the most of the leader's people off that day
--   lightest_team_*      the leader's direct report leader whose team has the lowest share at work that
--                        day (ties: name, then id); empty when nobody who reports to the leader leads
-- A leader who did not lead yet at an earlier month-end has no row for it.
CREATE OR REPLACE TABLE marts.mart_leader_pulse AS
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar),
wt AS (SELECT * FROM (VALUES ('All'), ('Employees'), ('Contingent')) AS t (worker_type)),
months AS (
    SELECT month_end_date, CAST(ROW_NUMBER() OVER (ORDER BY month_end_date) - 1 AS INTEGER) AS month_index
    FROM (SELECT DISTINCT month_end_date FROM intermediate.int_leader_org) AS m
),
now_leaders AS (
    SELECT l.leader_id, l.parent_leader_id, l.leader_name
    FROM intermediate.int_org_leader AS l JOIN rc ON l.month_end_date = rc.report_as_of_date
),
below AS (
    SELECT c.month_end_date, c.ancestor_id AS leader_id, d.worker_type AS person_type,
           CASE WHEN h.location_id IS NULL THEN 0 ELSE 1 END AS in_hub
    FROM intermediate.int_org_closure AS c
    JOIN now_leaders AS n ON n.leader_id = c.ancestor_id
    JOIN intermediate.int_org_leader AS l ON l.month_end_date = c.month_end_date AND l.leader_id = c.ancestor_id
    JOIN intermediate.int_person_month_end AS d ON d.month_end_date = c.month_end_date AND d.person_id = c.descendant_id
    LEFT JOIN staging.stg_function_hub AS h ON h.function_name = d.function_name AND h.location_id = d.location_id
    WHERE c.depth >= 1 AND NOT d.is_executive_officer
),
hub AS (
    SELECT b.month_end_date, b.leader_id, wt.worker_type, CAST(SUM(b.in_hub) AS BIGINT) AS hub_people
    FROM below AS b
    JOIN wt ON wt.worker_type = 'All'
            OR (wt.worker_type = 'Employees' AND b.person_type = 'Employee')
            OR (wt.worker_type = 'Contingent' AND b.person_type = 'Contingent')
    GROUP BY 1, 2, 3
),
week AS (               -- the weekdays of the next seven days
    SELECT leader_id, worker_type, day_offset, day, people, at_work, off_public_holiday,
           ROW_NUMBER() OVER (PARTITION BY leader_id, worker_type
                              ORDER BY CAST(at_work AS DOUBLE) / people, day_offset) AS rk
    FROM marts.mart_leader_availability
    WHERE day_offset BETWEEN 0 AND 6 AND NOT is_weekend AND people > 0
),
dip AS (SELECT * FROM week WHERE rk = 1),
holiday AS (            -- the holiday on the dip day that keeps the most of the leader's people off
    SELECT x.leader_id, x.worker_type, x.holiday_name, x.country_code,
           ROW_NUMBER() OVER (PARTITION BY x.leader_id, x.worker_type ORDER BY x.off DESC, x.country_code) AS rk
    FROM (
        SELECT dp.leader_id, dp.worker_type, ph.holiday_name, ph.country_code, COUNT(*) AS off
        FROM dip AS dp
        JOIN intermediate.int_org_closure AS c ON c.ancestor_id = dp.leader_id AND c.depth >= 1
        JOIN rc ON c.month_end_date = rc.report_as_of_date
        JOIN intermediate.int_person_availability_day AS a
          ON a.person_id = c.descendant_id AND a.day_offset = dp.day_offset AND a.day_status = 'Public holiday'
        JOIN intermediate.int_person_month_end AS d ON d.month_end_date = c.month_end_date AND d.person_id = c.descendant_id
        JOIN staging.stg_public_holiday AS ph ON ph.country_code = d.country_code AND ph.holiday_date = dp.day
        WHERE dp.worker_type = 'All'
           OR (dp.worker_type = 'Employees' AND a.worker_type = 'Employee')
           OR (dp.worker_type = 'Contingent' AND a.worker_type = 'Contingent')
        GROUP BY 1, 2, 3, 4
    ) AS x
),
lightest AS (
    SELECT dp.leader_id, dp.worker_type, k.leader_id AS team_leader_id, k.leader_name AS team_leader_name,
           a.people, a.at_work,
           ROW_NUMBER() OVER (PARTITION BY dp.leader_id, dp.worker_type
                              ORDER BY CAST(a.at_work AS DOUBLE) / a.people, k.leader_name, k.leader_id) AS rk
    FROM dip AS dp
    JOIN now_leaders AS k ON k.parent_leader_id = dp.leader_id
    JOIN marts.mart_leader_availability AS a
      ON a.leader_id = k.leader_id AND a.worker_type = dp.worker_type AND a.day_offset = dp.day_offset
    WHERE a.people > 0
)
SELECT o.month_end_date, m.month_index, o.leader_id, o.worker_type, o.people, o.gap_people,
       COALESCE(h.hub_people, 0)                              AS hub_people,
       dp.day_offset                                          AS dip_day_offset,
       dp.day                                                 AS dip_day,
       dp.people                                              AS dip_people,
       dp.at_work                                             AS dip_at_work,
       dp.off_public_holiday                                  AS dip_off_public_holiday,
       hol.holiday_name                                       AS dip_holiday_name,
       hol.country_code                                       AS dip_holiday_country_code,
       lt.team_leader_id                                      AS lightest_team_leader_id,
       lt.team_leader_name                                    AS lightest_team_leader_name,
       lt.people                                              AS lightest_team_people,
       lt.at_work                                             AS lightest_team_at_work
FROM intermediate.int_leader_org AS o
JOIN months AS m ON m.month_end_date = o.month_end_date
JOIN now_leaders AS n ON n.leader_id = o.leader_id
LEFT JOIN hub AS h ON h.month_end_date = o.month_end_date AND h.leader_id = o.leader_id AND h.worker_type = o.worker_type
LEFT JOIN dip AS dp ON m.month_index = 12 AND dp.leader_id = o.leader_id AND dp.worker_type = o.worker_type
LEFT JOIN holiday AS hol ON m.month_index = 12 AND hol.leader_id = o.leader_id AND hol.worker_type = o.worker_type AND hol.rk = 1
LEFT JOIN lightest AS lt ON m.month_index = 12 AND lt.leader_id = o.leader_id AND lt.worker_type = o.worker_type AND lt.rk = 1
ORDER BY ALL;
