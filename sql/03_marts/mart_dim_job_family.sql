-- mart_dim_job_family
-- Grain: one row per job family.
CREATE OR REPLACE TABLE marts.mart_dim_job_family AS
SELECT DISTINCT job_family_code, job_family
FROM staging.stg_job_profile
ORDER BY job_family_code;
