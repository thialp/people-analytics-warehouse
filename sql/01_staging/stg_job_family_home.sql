-- stg_job_family_home
-- The function that usually hires each job family; shared families are hired everywhere.
-- Source: ref_job_family_home (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_job_family_home AS
SELECT
    NULLIF(job_family_code, '')                              AS job_family_code,
    NULLIF(home_function, '')                                AS home_function,
    CAST(NULLIF(is_shared, '') AS BOOLEAN)                   AS is_shared
FROM raw.ref_job_family_home;
