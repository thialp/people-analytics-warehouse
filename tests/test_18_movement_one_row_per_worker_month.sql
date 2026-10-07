-- The movement model compares two snapshots per worker per month. A second row
-- for the same worker and month would double-count a hire, leaver or move.
SELECT month_end_date, worker_id, COUNT(*) AS rows_per_worker
FROM intermediate.int_worker_movement
GROUP BY month_end_date, worker_id
HAVING COUNT(*) > 1
