-- mart_workforce_cost_snapshot
-- Grain: one row per month-end x department x country x grade x job family.
--
-- Point-in-time workforce and pay composition. Use it for "where is the money"
-- questions (mix by country, grade, family; nominal vs constant currency;
-- compa-ratio), while mart_workforce_cost_bridge answers "why did it change".
--
-- Privacy rule: pay for groups of fewer than 5 people can identify individuals.
-- Whether a group is "small" depends on how the dashboard slices the data
-- (a department total is safe; one grade in one country may not be), so the
-- suppression is applied in Tableau at the level of the view:
--   IF SUM([Headcount]) < 5 THEN NULL ELSE SUM([Loaded Usd Nominal]) END
-- A row-level flag here would hide far too much at this fine grain.
--
-- Executive officers are excluded from compensation reporting.
CREATE OR REPLACE TABLE marts.mart_workforce_cost_snapshot AS
SELECT
    s.month_end_date,
    cal.fiscal_year,
    cal.fiscal_quarter_label,
    cal.fiscal_period,
    cal.is_fiscal_year_end,
    s.department_id,
    d.department_name,
    d.sub_function,
    d.function_name,
    s.country_code,
    loc.country_name,
    loc.region,
    s.currency_code,
    s.grade,
    jp.grade_level,
    jp.career_track,
    s.job_family,
    CAST(COUNT(*) AS INTEGER)                                          AS headcount,
    -- sum as exact decimals so exports are identical from run to run
    ROUND(SUM(CAST(s.fte                    AS DECIMAL(18, 4))), 2)    AS fte,
    ROUND(SUM(CAST(s.base_usd_nominal       AS DECIMAL(18, 4))), 2)    AS base_usd_nominal,
    ROUND(SUM(CAST(s.base_usd_constant      AS DECIMAL(18, 4))), 2)    AS base_usd_constant,
    ROUND(SUM(CAST(s.loaded_usd_nominal     AS DECIMAL(18, 4))), 2)    AS loaded_usd_nominal,
    ROUND(SUM(CAST(s.loaded_usd_constant    AS DECIMAL(18, 4))), 2)    AS loaded_usd_constant,
    ROUND(SUM(CAST(s.range_mid_usd_constant AS DECIMAL(18, 4))), 2)    AS range_mid_usd_constant
FROM intermediate.int_worker_month_end_snapshot AS s
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = s.month_end_date
LEFT JOIN staging.stg_department AS d ON d.department_id = s.department_id
LEFT JOIN (SELECT DISTINCT country_code, country_name, region FROM staging.stg_location) AS loc
       ON loc.country_code = s.country_code
LEFT JOIN staging.stg_job_level AS jp ON jp.grade = s.grade
WHERE NOT s.is_executive_officer
GROUP BY ALL
ORDER BY s.month_end_date, s.department_id, s.country_code, s.grade, s.job_family;
