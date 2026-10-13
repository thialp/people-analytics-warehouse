-- After same-day corrections are resolved in staging, compensation history must
-- be a continuous SCD2 chain too. This is the test that fails if the correction
-- logic in stg_compensation_history is removed.
WITH ordered AS (
    SELECT
        worker_id,
        comp_record_id,
        effective_start_date,
        effective_end_date,
        LEAD(effective_start_date) OVER (PARTITION BY worker_id ORDER BY effective_start_date) AS next_start_date
    FROM staging.stg_compensation_history
)
SELECT *
FROM ordered
WHERE next_start_date IS NOT NULL
  AND (effective_end_date IS NULL OR next_start_date <> effective_end_date + INTERVAL 1 DAY)
