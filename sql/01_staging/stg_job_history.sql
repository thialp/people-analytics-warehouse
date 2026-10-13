-- stg_job_history
-- Effective-dated (SCD Type 2) job assignments: department, office, job, level, FTE
-- and the reporting line (manager, people-manager flag, org unit led).
-- effective_end_date is inclusive; NULL means the record is still current.
--
-- The source calls the 1-12 ladder "job level". Downstream models and the published
-- marts call it "grade", so it is renamed here once.
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
    CAST(job_level AS INTEGER)                               AS grade,
    CAST(fte AS DECIMAL(4, 2))                               AS fte,
    NULLIF(manager_worker_id, '')                            AS manager_worker_id,
    CAST(is_people_manager AS BOOLEAN)                       AS is_people_manager,
    NULLIF(leads_org_unit_id, '')                            AS leads_org_unit_id
FROM raw.fact_job_history;
