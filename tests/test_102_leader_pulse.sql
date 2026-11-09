-- Release 7 Team pulse: one row per leader on the report date x worker type x month-end they led;
-- hub people never exceed people; people and gaps equal int_leader_org; the dip day is a weekday
-- in the next seven days with the lowest share at work; the lightest team reports to the leader.
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar),
p AS (SELECT * FROM marts.mart_leader_pulse)
SELECT 'duplicate pulse row' AS problem, leader_id || ' ' || worker_type || ' ' || CAST(month_index AS VARCHAR) AS id, '' AS detail
FROM p GROUP BY leader_id, worker_type, month_index HAVING COUNT(*) > 1
UNION ALL
SELECT 'leader on the report date without a pulse row', l.leader_id, ''
FROM intermediate.int_org_leader AS l JOIN rc ON l.month_end_date = rc.report_as_of_date
WHERE NOT EXISTS (SELECT 1 FROM p WHERE p.leader_id = l.leader_id AND p.month_index = 12)
UNION ALL
SELECT 'more hub people than people', leader_id || ' ' || worker_type, CAST(month_index AS VARCHAR)
FROM p WHERE hub_people > people
UNION ALL
SELECT 'people or gaps differ from int_leader_org', p.leader_id || ' ' || p.worker_type, CAST(p.month_end_date AS VARCHAR)
FROM p JOIN intermediate.int_leader_org AS o
  ON o.leader_id = p.leader_id AND o.worker_type = p.worker_type AND o.month_end_date = p.month_end_date
WHERE o.people <> p.people OR o.gap_people <> p.gap_people
UNION ALL
SELECT 'dip on a weekend or outside the next seven days', leader_id || ' ' || worker_type, CAST(dip_day_offset AS VARCHAR)
FROM p WHERE dip_day IS NOT NULL AND (dip_day_offset NOT BETWEEN 0 AND 6 OR dayofweek(dip_day) IN (0, 6))
UNION ALL
SELECT 'a weekday ahead has a lower share at work than the dip', p.leader_id || ' ' || p.worker_type, CAST(a.day_offset AS VARCHAR)
FROM p JOIN marts.mart_leader_availability AS a
  ON a.leader_id = p.leader_id AND a.worker_type = p.worker_type AND a.day_offset BETWEEN 0 AND 6 AND NOT a.is_weekend AND a.people > 0
WHERE p.month_index = 12 AND p.dip_people > 0 AND a.at_work * p.dip_people < p.dip_at_work * a.people
UNION ALL
SELECT 'lightest team does not report to the leader', p.leader_id, p.lightest_team_leader_id
FROM p JOIN intermediate.int_org_leader AS l ON l.leader_id = p.lightest_team_leader_id
JOIN rc ON l.month_end_date = rc.report_as_of_date
WHERE p.lightest_team_leader_id IS NOT NULL AND l.parent_leader_id <> p.leader_id
