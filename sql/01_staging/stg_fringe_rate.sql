-- stg_fringe_rate
-- Employer cost on top of base salary, as a share of base, by country and calendar
-- year (rates change on January 1). Built from OECD, BLS and statutory sources; see
-- stg_fringe_source for the citation behind every component.
CREATE OR REPLACE TABLE staging.stg_fringe_rate AS
SELECT
    country_code,
    CAST("year" AS INTEGER)                        AS fringe_year,
    CAST(effective_start_date AS DATE)             AS effective_start_date,
    CAST(effective_end_date AS DATE)               AS effective_end_date,
    CAST(social_contribution_rate AS DOUBLE)       AS social_contribution_rate,
    CAST(retirement_severance_rate AS DOUBLE)      AS retirement_severance_rate,
    CAST(statutory_pay_rate AS DOUBLE)             AS statutory_pay_rate,
    CAST(employer_benefits_rate AS DOUBLE)         AS employer_benefits_rate,
    CAST(fringe_rate AS DOUBLE)                    AS fringe_rate,
    CAST(reference_salary_local AS DECIMAL(18, 2)) AS reference_salary_local,
    CAST(is_estimate AS BOOLEAN)                   AS is_estimate,
    NULLIF(method_note, '')                        AS method_note
FROM raw.ref_fringe_rate;
