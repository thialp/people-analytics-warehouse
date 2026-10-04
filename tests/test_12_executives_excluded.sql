-- Executive officers never appear in compensation reporting: each month, the
-- marts' headcount must equal the non-executive population exactly.
WITH expected AS (
    SELECT month_end_date, COUNT(*) AS non_exec_headcount
    FROM intermediate.int_worker_month_end_snapshot
    WHERE NOT is_executive_officer
    GROUP BY month_end_date
),
snapshot_mart AS (
    SELECT month_end_date, SUM(headcount) AS headcount
    FROM marts.mart_workforce_cost_snapshot
    GROUP BY month_end_date
),
walk_mart AS (
    SELECT month_end_date, SUM(headcount) AS headcount
    FROM marts.mart_workforce_cost_bridge
    WHERE driver = 'Closing Run-Rate'
    GROUP BY month_end_date
)
SELECT e.month_end_date, e.non_exec_headcount, s.headcount AS snapshot_headcount, w.headcount AS walk_headcount
FROM expected AS e
LEFT JOIN snapshot_mart AS s ON s.month_end_date = e.month_end_date
LEFT JOIN walk_mart     AS w ON w.month_end_date = e.month_end_date
WHERE s.headcount IS DISTINCT FROM e.non_exec_headcount
   OR (w.headcount IS DISTINCT FROM e.non_exec_headcount
       AND e.month_end_date > (SELECT MIN(month_end_date) FROM intermediate.int_month_end_calendar))
