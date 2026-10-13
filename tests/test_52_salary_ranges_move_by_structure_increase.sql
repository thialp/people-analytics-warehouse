-- Salary structures move once a year: each fiscal year's range midpoint is the prior
-- year's times (1 + structure_increase_pct), within rounding to 100 local units, and
-- min < mid < max.
WITH r AS (
    SELECT *, LAG(range_mid) OVER (PARTITION BY grade, country_code ORDER BY fiscal_year) AS prior_mid
    FROM staging.stg_salary_range
)
SELECT fiscal_year, grade, country_code, prior_mid, structure_increase_pct, range_mid
FROM r
WHERE NOT (range_min < range_mid AND range_mid < range_max)
   OR (prior_mid IS NULL) <> (structure_increase_pct IS NULL)
   OR ABS(range_mid - prior_mid * (1 + structure_increase_pct)) > 110
