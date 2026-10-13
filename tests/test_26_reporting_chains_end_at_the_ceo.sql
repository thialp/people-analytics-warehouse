-- No loops and no dead ends: every worker's chain of managers reaches the CEO in
-- fewer than 15 steps, at every month-end.
WITH top AS (
    SELECT month_end_date, worker_id, ARG_MAX(ancestor_worker_id, hops) AS top_id, MAX(hops) AS hops
    FROM intermediate.int_worker_reporting_chain
    GROUP BY ALL
)
SELECT t.month_end_date, t.worker_id, t.top_id, t.hops
FROM top AS t
JOIN intermediate.int_worker_month_end_snapshot AS c
  ON c.month_end_date = t.month_end_date AND c.worker_id = t.top_id
WHERE COALESCE(c.leads_org_unit_id, '') <> 'ORG-000' OR t.hops >= 15
UNION ALL
SELECT s.month_end_date, s.worker_id, NULL, NULL
FROM intermediate.int_worker_month_end_snapshot AS s
LEFT JOIN top AS t ON t.month_end_date = s.month_end_date AND t.worker_id = s.worker_id
WHERE t.worker_id IS NULL AND COALESCE(s.leads_org_unit_id, '') <> 'ORG-000'
