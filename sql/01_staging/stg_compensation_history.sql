-- stg_compensation_history
-- Effective-dated (SCD Type 2) base pay in local currency, stated as a full-time annual rate.
--
-- The source system records a correction as a second row with the SAME effective date.
-- Both rows land in raw; only the latest entry (highest comp_record_id) is the truth.
-- Keeping both would double-count pay for that worker, so we keep one row per
-- worker + effective date and flag the ones that were corrected.
CREATE OR REPLACE TABLE staging.stg_compensation_history AS
WITH typed AS (
    SELECT
        comp_record_id,
        worker_id,
        CAST(effective_start_date AS DATE)                   AS effective_start_date,
        CAST(NULLIF(effective_end_date, '') AS DATE)         AS effective_end_date,
        action_reason,
        transaction_type,
        currency_code,
        CAST(base_salary_annual_local AS DECIMAL(18, 2))     AS base_salary_annual_local
    FROM raw.fact_compensation_history
),
ranked AS (
    SELECT
        *,
        ROW_NUMBER() OVER (PARTITION BY worker_id, effective_start_date
                           ORDER BY comp_record_id DESC)     AS version_rank,
        COUNT(*)     OVER (PARTITION BY worker_id, effective_start_date) AS versions_loaded
    FROM typed
)
SELECT
    comp_record_id,
    worker_id,
    effective_start_date,
    effective_end_date,
    COALESCE(effective_end_date, DATE '9999-12-31')          AS effective_end_date_filled,
    action_reason,
    currency_code,
    base_salary_annual_local,
    versions_loaded > 1                                      AS was_corrected
FROM ranked
WHERE version_rank = 1;
