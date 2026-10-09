-- stg_job_level_base_salary
-- Base salary for a new hire by level and country, in local currency. Fixed in local
-- currency at the reference FX date, so currency moves change its USD value.
CREATE OR REPLACE TABLE staging.stg_job_level_base_salary AS
SELECT
    CAST(job_level AS INTEGER)                          AS grade,
    country_code,
    currency_code,
    CAST(base_salary_local AS DECIMAL(18, 2))           AS base_salary_local,
    CAST(base_salary_usd_at_reference AS DECIMAL(18, 2)) AS base_salary_usd_at_reference,
    CAST(fx_reference_date AS DATE)                     AS fx_reference_date
FROM raw.ref_job_level_base_salary;
