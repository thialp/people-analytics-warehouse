-- stg_job_history
-- Effective-dated (SCD Type 2) job assignments: department, location, job, grade, FTE.
-- effective_end_date is inclusive; NULL means the record is still current.
CREATE OR REPLACE TABLE staging.stg_job_history AS
SELECT
    job_record_id,
    worker_id,
    CAST(effective_start_date AS DATE)                       AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE),
             DATE '9999-12-31')                              AS effective_end_date_filled,
    action_reason,
    position_id,
    department_id,
    location_id,
    job_profile_id,
    CAST(grade AS INTEGER)                                   AS grade,
    CAST(fte AS DECIMAL(4, 2))                               AS fte
FROM raw.fact_job_history;
