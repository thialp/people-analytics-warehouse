-- mart_dim_grade
-- Grain: one row per job level (grade 1-12), with its code (L1-L12), name, career
-- track and the US base salary for a new hire at that level.
CREATE OR REPLACE TABLE marts.mart_dim_grade AS
SELECT
    grade,
    level_code,
    grade_level,
    career_track,
    us_base_salary_usd
FROM staging.stg_job_level
ORDER BY grade;
