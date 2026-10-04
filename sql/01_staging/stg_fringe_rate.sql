-- stg_fringe_rate
-- Employer-paid benefits and payroll taxes as a share of base pay, by country and fiscal year.
CREATE OR REPLACE TABLE staging.stg_fringe_rate AS
SELECT
    country_code,
    CAST(fiscal_year AS INTEGER)     AS fiscal_year,
    CAST(fringe_rate AS DOUBLE)      AS fringe_rate
FROM raw.ref_fringe_rate;
