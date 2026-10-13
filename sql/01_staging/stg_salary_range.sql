-- stg_salary_range
-- Pay ranges in local currency by fiscal year, level and country (85% to 135% of the
-- level base, at pay zone 1.00). Structures move every July 1: structure_increase_pct is
-- the move into that fiscal year (Arcadia pay policy; NULL in the first year).
CREATE OR REPLACE TABLE staging.stg_salary_range AS
SELECT
    CAST(fiscal_year AS INTEGER)           AS fiscal_year,
    CAST(job_level AS INTEGER)             AS grade,
    country_code,
    currency_code,
    CAST(range_min AS DECIMAL(18, 2))      AS range_min,
    CAST(range_mid AS DECIMAL(18, 2))      AS range_mid,
    CAST(range_max AS DECIMAL(18, 2))      AS range_max,
    CAST(NULLIF(structure_increase_pct, '') AS DECIMAL(6, 4)) AS structure_increase_pct
FROM raw.ref_salary_range;
