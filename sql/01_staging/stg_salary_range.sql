-- stg_salary_range
-- Pay ranges in local currency by fiscal year, level and country (85% to 135% of the
-- level base, at pay zone 1.00).
CREATE OR REPLACE TABLE staging.stg_salary_range AS
SELECT
    CAST(fiscal_year AS INTEGER)           AS fiscal_year,
    CAST(job_level AS INTEGER)             AS grade,
    country_code,
    currency_code,
    CAST(range_min AS DECIMAL(18, 2))      AS range_min,
    CAST(range_mid AS DECIMAL(18, 2))      AS range_mid,
    CAST(range_max AS DECIMAL(18, 2))      AS range_max
FROM raw.ref_salary_range;
