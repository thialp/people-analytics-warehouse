-- stg_workforce_plan
-- The workforce plan by cost center and fiscal quarter, one row per plan version.
-- Each fiscal year has a Budget (set in May, before the year starts) and three
-- reforecasts (RF1 in October, RF2 in January, RF3 in April), each covering only the
-- quarters still ahead. Versions are never overwritten, so actuals can be compared with
-- the budget or with any reforecast.
-- planned_cost_usd is the quarter-end loaded run-rate (annual base x FTE x (1 + fringe)),
-- in USD at the plan's FX rates (ECB rates on the version date).
CREATE OR REPLACE TABLE staging.stg_workforce_plan AS
SELECT
    plan_version,
    version_type,
    CAST(version_date AS DATE)                               AS version_date,
    CAST(fiscal_year AS INTEGER)                             AS fiscal_year,
    CAST(fiscal_quarter AS INTEGER)                          AS fiscal_quarter,
    CAST(quarter_end_date AS DATE)                           AS quarter_end_date,
    cost_center_id,
    CAST(planned_ending_headcount AS INTEGER)                AS planned_ending_headcount,
    CAST(planned_ending_fte AS DECIMAL(10, 2))               AS planned_ending_fte,
    CAST(planned_net_new AS INTEGER)                         AS planned_net_new,
    CAST(planned_backfills AS INTEGER)                       AS planned_backfills,
    CAST(planned_cost_usd AS DECIMAL(18, 2))                 AS planned_cost_usd,
    CAST(plan_fx_rate_date AS DATE)                          AS plan_fx_rate_date
FROM raw.fact_workforce_plan;
