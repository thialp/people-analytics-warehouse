-- Release 7 org closure: every person with a manager has the CEO above them, nobody appears twice
-- below the same leader, and for every leader directs + indirects = people.
WITH ceo AS (
    SELECT month_end_date, person_id AS ceo_id FROM intermediate.int_person_month_end
    WHERE is_executive_officer AND manager_worker_id IS NULL
)
SELECT 'no CEO above' AS problem, p.person_id AS id, CAST(p.month_end_date AS VARCHAR) AS detail
FROM intermediate.int_person_month_end AS p
JOIN ceo USING (month_end_date)
WHERE p.manager_worker_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM intermediate.int_org_closure AS c
                  WHERE c.month_end_date = p.month_end_date AND c.descendant_id = p.person_id AND c.ancestor_id = ceo.ceo_id)
UNION ALL
SELECT 'twice below a leader', ancestor_id || ' > ' || descendant_id, CAST(month_end_date AS VARCHAR)
FROM intermediate.int_org_closure GROUP BY month_end_date, ancestor_id, descendant_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'directs + indirects <> people', leader_id || ' ' || worker_type, CAST(month_end_date AS VARCHAR)
FROM intermediate.int_leader_org WHERE directs + indirects <> people
