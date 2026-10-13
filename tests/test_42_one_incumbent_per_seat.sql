-- A seat never has two incumbents at once: each assignment on a seat ends before the
-- next one starts.
WITH ordered AS (
    SELECT
        position_id,
        assignment_id,
        worker_id,
        start_date,
        end_date,
        LEAD(start_date) OVER (PARTITION BY position_id ORDER BY start_date, assignment_id) AS next_start_date
    FROM staging.stg_position_assignment
)
SELECT *
FROM ordered
WHERE next_start_date IS NOT NULL
  AND (end_date IS NULL OR next_start_date <= end_date)
