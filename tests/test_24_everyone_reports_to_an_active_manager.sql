-- Everyone reports to someone: at every month-end each worker except the CEO has a
-- manager who is employed that day, the CEO has none, and there is exactly one CEO.
SELECT s.month_end_date, s.worker_id, s.manager_worker_id, 'manager missing or not employed' AS issue
FROM intermediate.int_worker_month_end_snapshot AS s
LEFT JOIN intermediate.int_worker_month_end_snapshot AS m
       ON m.month_end_date = s.month_end_date AND m.worker_id = s.manager_worker_id
WHERE COALESCE(s.leads_org_unit_id, '') <> 'ORG-000' AND m.worker_id IS NULL
UNION ALL
SELECT month_end_date, worker_id, manager_worker_id, 'CEO has a manager'
FROM intermediate.int_worker_month_end_snapshot
WHERE leads_org_unit_id = 'ORG-000' AND manager_worker_id IS NOT NULL
UNION ALL
SELECT month_end_date, NULL, NULL, 'not exactly one CEO'
FROM intermediate.int_worker_month_end_snapshot
GROUP BY month_end_date
HAVING COUNT(*) FILTER (WHERE leads_org_unit_id = 'ORG-000') <> 1
