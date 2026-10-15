-- mart_plan_vs_actual
-- Grain: one row per plan version, cost center and fiscal quarter.
-- The plan beside what happened: ending headcount and FTE at the quarter-end, net-new
-- and backfill hires in the quarter, and the quarter-end loaded run-rate. Every version
-- is kept, so a quarter can be judged against the budget or against any reforecast.
--
-- Cost is compared like for like: actual_cost_usd_plan_fx converts the actual local
-- run-rate at the plan's own FX rates (ECB rates on the version date), so an FX move
-- after the plan was set is not a variance. actual_cost_usd_constant is also given.
-- is_latest_version marks the last version made before the quarter started (the
-- budget for Q1, RF1 for Q2, RF2 for Q3, RF3 for Q4).
--
-- Release 3: the plan's contingent line beside its actuals. actual_cw_headcount is the
-- contingent workers Bridgeway counted on the quarter-end (int_cw_month_end_snapshot);
-- actual_cw_spend_usd_plan_fx is their annualized bill run-rate (hourly rate x contracted
-- hours x 52, or monthly rate x 12) at the plan's FX rates, the same basis as
-- planned_cw_spend_usd; actual_cw_spend_usd_constant is at the constant rate set.
-- 615 rows exist only for the contingent line (zero on every employee measure).
CREATE OR REPLACE TABLE marts.mart_plan_vs_actual AS
WITH quarters AS (
    SELECT fiscal_year, fiscal_quarter, MAX(month_end_date) AS quarter_end_date,
           ANY_VALUE(fiscal_quarter_label) AS fiscal_quarter_label
    FROM intermediate.int_month_end_calendar
    GROUP BY ALL
),
people AS (   -- actuals at the quarter-end, by cost center and pay currency
    SELECT s.month_end_date AS quarter_end_date,
           d.cost_center || '-' || s.country_code              AS cost_center_id,
           s.currency_code,
           COUNT(*)                                            AS headcount,
           SUM(s.fte)                                          AS fte,
           SUM(CAST(s.base_salary_annual_local * s.fte * (1 + s.fringe_rate) AS DECIMAL(38, 10))) AS loaded_local,
           SUM(CAST(s.loaded_usd_constant AS DECIMAL(38, 10))) AS loaded_usd_constant
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN staging.stg_department AS d USING (department_id)
    WHERE s.month_end_date IN (SELECT quarter_end_date FROM quarters)
    GROUP BY ALL
),
fills AS (    -- hires and internal moves into seats during the quarter, by the seat's cost center
    SELECT q.quarter_end_date,
           f.new_cost_center_id                                AS cost_center_id,
           SUM(CASE WHEN f.seat_type = 'Net-new'  THEN 1 ELSE 0 END)            AS net_new,
           SUM(CASE WHEN f.seat_type = 'Backfill' THEN 1 ELSE 0 END)            AS backfills,
           SUM(CASE WHEN f.seat_type = 'Net-new' AND f.reuse_candidate THEN 1 ELSE 0 END) AS net_new_reuse_candidates,
           SUM(CASE WHEN f.fill_type = 'External Hire' THEN 1 ELSE 0 END)       AS external_hires,
           SUM(CASE WHEN f.fill_type = 'Internal Move' THEN 1 ELSE 0 END)       AS internal_moves
    FROM intermediate.int_seat_fill AS f
    JOIN intermediate.int_month_end_calendar AS c ON c.month_end_date = LAST_DAY(f.fill_date)
    JOIN quarters AS q ON q.fiscal_year = c.fiscal_year AND q.fiscal_quarter = c.fiscal_quarter
    GROUP BY ALL
),
cost_at_plan_fx AS (
    SELECT p.plan_version, p.cost_center_id, p.fiscal_quarter,
           SUM(CAST(pe.loaded_local * fx.usd_per_local AS DECIMAL(38, 10))) AS actual_cost_usd_plan_fx
    FROM staging.stg_workforce_plan AS p
    JOIN people AS pe ON pe.quarter_end_date = p.quarter_end_date AND pe.cost_center_id = p.cost_center_id
    ASOF JOIN staging.stg_fx_rate_daily AS fx
      ON fx.currency_code = pe.currency_code AND fx.rate_date <= p.plan_fx_rate_date
    GROUP BY ALL
),
cw AS (      -- contingent actuals at the quarter-end, by cost center and billing currency
    SELECT s.month_end_date AS quarter_end_date, s.cost_center_id, s.billing_currency AS currency_code,
           COUNT(*)                                                       AS headcount,
           SUM(CAST(s.run_rate_local AS DECIMAL(38, 10)))                 AS run_rate_local,
           SUM(CAST(s.run_rate_usd_constant AS DECIMAL(38, 10)))          AS run_rate_usd_constant
    FROM intermediate.int_cw_month_end_snapshot AS s
    WHERE s.month_end_date IN (SELECT quarter_end_date FROM quarters)
    GROUP BY ALL
),
cw_at_plan_fx AS (
    SELECT p.plan_version, p.cost_center_id, p.fiscal_quarter,
           SUM(CAST(c.run_rate_local * fx.usd_per_local AS DECIMAL(38, 10))) AS actual_cw_spend_usd_plan_fx
    FROM staging.stg_workforce_plan AS p
    JOIN cw AS c ON c.quarter_end_date = p.quarter_end_date AND c.cost_center_id = p.cost_center_id
    ASOF JOIN staging.stg_fx_rate_daily AS fx
      ON fx.currency_code = c.currency_code AND fx.rate_date <= p.plan_fx_rate_date
    GROUP BY ALL
),
cw_cc AS (
    SELECT quarter_end_date, cost_center_id, SUM(headcount) AS headcount,
           SUM(run_rate_usd_constant) AS run_rate_usd_constant
    FROM cw GROUP BY ALL
),
people_cc AS (
    SELECT quarter_end_date, cost_center_id, SUM(headcount) AS headcount, SUM(fte) AS fte,
           SUM(loaded_usd_constant) AS loaded_usd_constant
    FROM people GROUP BY ALL
)
SELECT
    p.plan_version,
    p.version_type,
    CASE p.version_type WHEN 'Budget' THEN 1 WHEN 'RF1' THEN 2 WHEN 'RF2' THEN 3 WHEN 'RF3' THEN 4 END AS version_order,
    p.version_date,
    p.fiscal_quarter = CASE p.version_type WHEN 'Budget' THEN 1 WHEN 'RF1' THEN 2 WHEN 'RF2' THEN 3 WHEN 'RF3' THEN 4 END
                                                                                               AS is_latest_version,
    p.fiscal_year,
    p.fiscal_quarter,
    q.fiscal_quarter_label,
    p.quarter_end_date,
    p.cost_center_id,
    cc.cost_center_name,
    cc.department_id,
    d.department_name,
    d.sub_function,
    d.function_name,
    cc.country_code,
    l.country_name,
    l.region,
    p.planned_ending_headcount,
    COALESCE(a.headcount, 0)                                 AS actual_ending_headcount,
    p.planned_ending_fte,
    COALESCE(a.fte, 0)                                       AS actual_ending_fte,
    p.planned_net_new,
    COALESCE(f.net_new, 0)                                   AS actual_net_new,
    COALESCE(f.net_new_reuse_candidates, 0)                  AS actual_net_new_reuse_candidates,
    p.planned_backfills,
    COALESCE(f.backfills, 0)                                 AS actual_backfills,
    COALESCE(f.external_hires, 0)                            AS actual_external_hires,
    COALESCE(f.internal_moves, 0)                            AS actual_internal_moves,
    p.planned_cost_usd,
    CAST(ROUND(COALESCE(x.actual_cost_usd_plan_fx, 0), 2) AS DECIMAL(18, 2)) AS actual_cost_usd_plan_fx,
    CAST(ROUND(COALESCE(a.loaded_usd_constant, 0), 2) AS DECIMAL(18, 2))     AS actual_cost_usd_constant,
    p.planned_cw_headcount,
    COALESCE(w.headcount, 0)                                 AS actual_cw_headcount,
    p.planned_cw_spend_usd,
    CAST(ROUND(COALESCE(y.actual_cw_spend_usd_plan_fx, 0), 2) AS DECIMAL(18, 2)) AS actual_cw_spend_usd_plan_fx,
    CAST(ROUND(COALESCE(w.run_rate_usd_constant, 0), 2) AS DECIMAL(18, 2))       AS actual_cw_spend_usd_constant,
    p.plan_fx_rate_date
FROM staging.stg_workforce_plan AS p
JOIN quarters AS q ON q.quarter_end_date = p.quarter_end_date
JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = p.cost_center_id
JOIN staging.stg_department  AS d  ON d.department_id   = cc.department_id
JOIN (SELECT DISTINCT country_code, country_name, region FROM staging.stg_location) AS l ON l.country_code = cc.country_code
LEFT JOIN people_cc AS a ON a.quarter_end_date = p.quarter_end_date AND a.cost_center_id = p.cost_center_id
LEFT JOIN fills AS f ON f.quarter_end_date = p.quarter_end_date AND f.cost_center_id = p.cost_center_id
LEFT JOIN cost_at_plan_fx AS x
  ON x.plan_version = p.plan_version AND x.cost_center_id = p.cost_center_id AND x.fiscal_quarter = p.fiscal_quarter
LEFT JOIN cw_cc AS w ON w.quarter_end_date = p.quarter_end_date AND w.cost_center_id = p.cost_center_id
LEFT JOIN cw_at_plan_fx AS y
  ON y.plan_version = p.plan_version AND y.cost_center_id = p.cost_center_id AND y.fiscal_quarter = p.fiscal_quarter
ORDER BY p.fiscal_year, p.version_date, p.cost_center_id, p.fiscal_quarter;
