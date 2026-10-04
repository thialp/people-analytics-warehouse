-- stg_job_profile
CREATE OR REPLACE TABLE staging.stg_job_profile AS
SELECT
    job_profile_id,
    job_family_code,
    job_family,
    job_title,
    CAST(grade AS INTEGER) AS grade,
    grade_level,
    career_track
FROM raw.dim_job_profile;
