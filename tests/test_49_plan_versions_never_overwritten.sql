-- Plan versions are kept side by side, never overwritten: one row per version, cost
-- center and quarter; the budget is dated before its fiscal year starts; each
-- reforecast is dated after the quarter it follows and covers only the quarters still
-- ahead (it is dated after the quarter it follows has closed); versions of a year are
-- dated in order; every cost center exists.
WITH versions AS (
    SELECT fiscal_year, plan_version, version_type, version_date, MIN(quarter_end_date) AS first_quarter_end
    FROM staging.stg_workforce_plan
    GROUP BY ALL
),
v AS (
    SELECT *, LAG(version_date) OVER (PARTITION BY fiscal_year ORDER BY version_type) AS prior_version_date
    FROM versions
)
SELECT plan_version, cost_center_id, fiscal_quarter, COUNT(*) AS rows, 'duplicate' AS problem
FROM staging.stg_workforce_plan
GROUP BY ALL
HAVING COUNT(*) > 1
UNION ALL
SELECT p.plan_version, p.cost_center_id, p.fiscal_quarter, NULL, 'quarter not covered by this version'
FROM staging.stg_workforce_plan AS p
WHERE p.fiscal_quarter < CASE p.version_type WHEN 'Budget' THEN 1 WHEN 'RF1' THEN 2 WHEN 'RF2' THEN 3 WHEN 'RF3' THEN 4 END
   OR p.version_date >= p.quarter_end_date
   OR p.plan_version <> 'FY' || RIGHT(CAST(p.fiscal_year AS VARCHAR), 2) || ' ' || p.version_type
UNION ALL
SELECT v.plan_version, NULL, NULL, NULL, 'version date'
FROM v
WHERE (v.version_type = 'Budget' AND v.version_date >= MAKE_DATE(v.fiscal_year - 1, 7, 1))
   OR (v.version_type LIKE 'RF%' AND v.version_date <= LAST_DAY(v.first_quarter_end - INTERVAL 3 MONTH))
   OR v.version_date <= v.prior_version_date
UNION ALL
SELECT DISTINCT p.plan_version, p.cost_center_id, NULL, NULL, 'unknown cost center'
FROM staging.stg_workforce_plan AS p
LEFT JOIN staging.stg_cost_center AS c USING (cost_center_id)
WHERE c.cost_center_id IS NULL
