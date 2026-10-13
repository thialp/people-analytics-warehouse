-- The seat view and the people view agree: on every month-end the Filled seats equal
-- the number of workers in the month-end snapshot, and they are the same people.
WITH seats AS (
    SELECT month_end_date, incumbent_worker_id AS worker_id
    FROM intermediate.int_position_snapshot
    WHERE status = 'Filled'
),
people AS (
    SELECT month_end_date, worker_id
    FROM intermediate.int_worker_month_end_snapshot
)
SELECT COALESCE(s.month_end_date, p.month_end_date) AS month_end_date,
       COALESCE(s.worker_id, p.worker_id)           AS worker_id,
       s.worker_id IS NOT NULL                      AS in_a_filled_seat,
       p.worker_id IS NOT NULL                      AS in_the_snapshot
FROM seats AS s
FULL OUTER JOIN people AS p
  ON p.month_end_date = s.month_end_date AND p.worker_id = s.worker_id
WHERE s.worker_id IS NULL OR p.worker_id IS NULL
