-- Job history is a continuous SCD2 chain: each record starts the day after the
-- previous one ends. A gap would drop the worker from snapshots; an overlap
-- would count them twice.
WITH ordered AS (
    SELECT
        worker_id,
        job_record_id,
        effective_start_date,
        effective_end_date,
        LEAD(effective_start_date) OVER (PARTITION BY worker_id ORDER BY effective_start_date) AS next_start_date
    FROM staging.stg_job_history
)
SELECT *
FROM ordered
WHERE next_start_date IS NOT NULL
  AND (effective_end_date IS NULL OR next_start_date <> effective_end_date + INTERVAL 1 DAY)
