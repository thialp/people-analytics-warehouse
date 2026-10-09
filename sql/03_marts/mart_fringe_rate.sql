-- mart_fringe_rate
-- Grain: one row per country per calendar year (2022-2026).
--
-- The researched fringe rate and its four components, with the number of sources
-- behind it and whether the year is an estimate (2026 carried forward where the
-- OECD has not published yet). Joins to the workforce marts on country and year.
CREATE OR REPLACE TABLE marts.mart_fringe_rate AS
SELECT
    f.country_code,
    c.country_name,
    c.region,
    f.fringe_year,
    f.social_contribution_rate,
    f.retirement_severance_rate,
    f.statutory_pay_rate,
    f.employer_benefits_rate,
    f.fringe_rate,
    f.is_estimate,
    f.method_note,
    (SELECT COUNT(DISTINCT source_id) FROM staging.stg_fringe_source AS s
      WHERE s.country_code = f.country_code AND s.fringe_year = f.fringe_year) AS source_count
FROM staging.stg_fringe_rate AS f
JOIN staging.stg_country AS c USING (country_code)
ORDER BY f.country_code, f.fringe_year;
