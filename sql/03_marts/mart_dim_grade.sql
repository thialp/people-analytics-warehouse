-- mart_dim_grade
-- Grain: one row per grade. Level names come from the non-executive job
-- profiles, where a grade always maps to the same level and career track.
CREATE OR REPLACE TABLE marts.mart_dim_grade AS
SELECT
    grade,
    MIN(grade_level)  AS grade_level,
    MIN(career_track) AS career_track
FROM staging.stg_job_profile
WHERE job_family_code <> 'EXE'
GROUP BY grade
ORDER BY grade;
