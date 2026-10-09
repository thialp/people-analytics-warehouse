-- stg_job_level
-- The 12-level ladder, with the US base salary for a new hire at each level and the
-- range width (min and max as a share of the level base).
CREATE OR REPLACE TABLE staging.stg_job_level AS
SELECT
    CAST(job_level AS INTEGER)            AS grade,
    level_code,
    level_name                            AS grade_level,
    career_track,
    CAST(us_base_salary_usd AS DECIMAL(18, 2)) AS us_base_salary_usd,
    CAST(range_min_pct AS DOUBLE)         AS range_min_pct,
    CAST(range_max_pct AS DOUBLE)         AS range_max_pct
FROM raw.dim_job_level;
