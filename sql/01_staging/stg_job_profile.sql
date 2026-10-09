-- stg_job_profile
-- Job family x job level, with the individual-contributor and people-manager
-- variants of levels 5 and 6. job_level is renamed grade (see stg_job_history).
CREATE OR REPLACE TABLE staging.stg_job_profile AS
SELECT
    job_profile_id,
    job_family_code,
    job_family,
    job_title,
    CAST(job_level AS INTEGER) AS grade,
    level_name                 AS grade_level,
    career_track
FROM raw.dim_job_profile;
