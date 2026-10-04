-- The as-of join must return exactly one row per worker per month-end.
SELECT month_end_date, worker_id, COUNT(*) AS rows_found
FROM intermediate.int_worker_month_end_snapshot
GROUP BY month_end_date, worker_id
HAVING COUNT(*) > 1
