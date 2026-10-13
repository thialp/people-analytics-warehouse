-- Position history is a continuous SCD2 chain per seat: the first record starts on the
-- day the seat was created, each later record starts the day after the previous one
-- ends, and only the last record is open.
WITH ordered AS (
    SELECT
        position_id,
        position_record_id,
        effective_start_date,
        effective_end_date,
        created_date,
        ROW_NUMBER() OVER (PARTITION BY position_id ORDER BY effective_start_date)            AS n,
        LEAD(effective_start_date) OVER (PARTITION BY position_id ORDER BY effective_start_date) AS next_start_date
    FROM staging.stg_position
)
SELECT *
FROM ordered
WHERE (n = 1 AND effective_start_date <> created_date)
   OR (next_start_date IS NOT NULL
       AND (effective_end_date IS NULL OR next_start_date <> effective_end_date + INTERVAL 1 DAY))
   OR (next_start_date IS NULL AND effective_end_date IS NOT NULL)
