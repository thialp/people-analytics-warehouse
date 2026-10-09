-- Every country has a fringe rate for every year 2022-2026, its components add up to
-- the total, the total is a plausible share of salary, and every non-zero component
-- cites at least one source.
WITH expected AS (
    SELECT c.country_code, y.fringe_year
    FROM staging.stg_country AS c
    CROSS JOIN (SELECT UNNEST(RANGE(2022, 2027)) AS fringe_year) AS y
),
components AS (
    SELECT country_code, fringe_year, component, rate
    FROM staging.stg_fringe_rate
    UNPIVOT (rate FOR component IN (social_contribution_rate, retirement_severance_rate,
                                    statutory_pay_rate, employer_benefits_rate))
)
SELECT e.country_code, e.fringe_year, 'missing year' AS issue
FROM expected AS e
LEFT JOIN staging.stg_fringe_rate AS f USING (country_code, fringe_year)
WHERE f.country_code IS NULL
UNION ALL
SELECT country_code, fringe_year, 'components do not add up or rate out of range'
FROM staging.stg_fringe_rate
WHERE ABS(social_contribution_rate + retirement_severance_rate + statutory_pay_rate
          + employer_benefits_rate - fringe_rate) > 0.0002
   OR fringe_rate <= 0 OR fringe_rate >= 1
UNION ALL
SELECT c.country_code, c.fringe_year, 'no source for ' || c.component
FROM components AS c
LEFT JOIN staging.stg_fringe_source AS s
       ON s.country_code = c.country_code AND s.fringe_year = c.fringe_year AND s.component = c.component
WHERE c.rate <> 0 AND s.source_id IS NULL
