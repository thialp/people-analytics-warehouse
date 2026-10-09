-- int_worker_pay_ledger
-- Grain: one row per worker per month-end, the same rows as int_worker_month_end_snapshot.
--
-- A running ledger of WHY each worker's annualized cost has moved since their first
-- month-end in the warehouse. Every column is cumulative, so the change between ANY two
-- month-ends is a subtraction:
--
--     driver amount between d0 and d1  =  cum_<driver>(d1) - cum_<driver>(d0)
--
-- That is what lets the compensation walk (tableau/custom_sql_compensation_walk.sql)
-- price every pair of month-ends without re-reading the pay history: a prefix sum turns
-- an O(months) range scan into one equality join per endpoint.
--
-- HOW ONE MONTH IS SPLIT (worker present at the prior and the current month-end)
--   Values: b = annual base (local), f = FTE, r = fringe rate, x = USD per local at a
--   month-end, k = constant USD per local. 0 = prior month-end, 1 = current month-end,
--   x1p = the current currency at the PRIOR month-end rate.
--   The month's change is applied in a fixed order, each step valued at the state the
--   previous step left behind, so the steps add up exactly (telescoping):
--     1. pay events  each pay record that took effect in the month, minus the record
--                    it replaced, valued at the prior month-end FX rate and the prior
--                    FTE and fringe rate. Split by the record's action reason:
--                    Promotion, Demotion, Tenure Increase, Market Adjustment,
--                    Relocation Adjustment, International Transfer.
--                    Two changes in one month (a promotion and an anniversary raise,
--                    817 worker-months) are therefore two separate amounts.
--     2. FTE         b1 * x1p * (f1 - f0), at the prior fringe rate
--     3. fringe      b1 * x1p * f1 * (r1 - r0)            (loaded measures only)
--     4. FX          b1 * f1 * (x1 - x1p)                  (nominal measures only)
--   For every worker and month:
--     sum of steps = value(current month-end) - value(prior month-end)
--   on all four measures (base / loaded x nominal / constant). Test 34 enforces it.
--
-- MOVE REASONS (as of the month-end)
--   org_move_reason       reason on the latest job record that changed the department:
--                         Transfer or Reorganization (the only two that do)
--   location_move_reason  latest job record that changed the office: International
--                         Transfer (a transfer that also changed country) or Relocation
--   A walk between two dates uses the closing-date value whenever the department or
--   office differs between the two dates.
CREATE OR REPLACE TABLE intermediate.int_worker_pay_ledger AS
WITH snap AS (
    SELECT month_end_date, worker_id, currency_code, base_salary_annual_local AS b, fte AS f,
           fringe_rate AS r, fx_rate_actual AS x, fx_rate_constant AS k
    FROM intermediate.int_worker_month_end_snapshot
),

-- worker present at both ends of a month
month_pair AS (
    SELECT
        c.month_end_date, cal.prior_month_end_date, c.worker_id,
        p.b AS b0, p.f AS f0, p.r AS r0, p.x AS x0, p.k AS k0,
        c.b AS b1, c.f AS f1, c.r AS r1, c.x AS x1, c.k AS k1,
        fx.usd_per_local_actual AS x1p
    FROM snap AS c
    JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = c.month_end_date
    JOIN snap AS p ON p.month_end_date = cal.prior_month_end_date AND p.worker_id = c.worker_id
    JOIN staging.stg_fx_rate AS fx
      ON fx.currency_code = c.currency_code AND fx.rate_date = cal.prior_month_end_date
),

-- every pay record beside the record it replaced
pay_record AS (
    SELECT
        worker_id, effective_start_date, action_reason, currency_code, base_salary_annual_local AS s,
        LAG(currency_code)            OVER w AS prev_currency_code,
        LAG(base_salary_annual_local) OVER w AS prev_s
    FROM intermediate.int_compensation_history_usd
    WINDOW w AS (PARTITION BY worker_id ORDER BY effective_start_date, comp_record_id)
),

-- pay records that took effect inside a month, valued at the prior month-end rates
pay_event AS (
    SELECT
        mp.month_end_date, mp.worker_id, pr.action_reason,
        (pr.s * fxn.usd_per_local_actual   - pr.prev_s * fxo.usd_per_local_actual)   * mp.f0 AS d_base_nom,
        (pr.s * fxn.usd_per_local_constant - pr.prev_s * fxo.usd_per_local_constant) * mp.f0 AS d_base_con,
        (pr.s * fxn.usd_per_local_actual   - pr.prev_s * fxo.usd_per_local_actual)   * mp.f0 * (1 + mp.r0) AS d_load_nom,
        (pr.s * fxn.usd_per_local_constant - pr.prev_s * fxo.usd_per_local_constant) * mp.f0 * (1 + mp.r0) AS d_load_con
    FROM month_pair AS mp
    JOIN pay_record AS pr
      ON pr.worker_id = mp.worker_id
     AND pr.effective_start_date >  mp.prior_month_end_date
     AND pr.effective_start_date <= mp.month_end_date
    JOIN staging.stg_fx_rate AS fxn
      ON fxn.currency_code = pr.currency_code AND fxn.rate_date = mp.prior_month_end_date
    JOIN staging.stg_fx_rate AS fxo
      ON fxo.currency_code = pr.prev_currency_code AND fxo.rate_date = mp.prior_month_end_date
),

pay_by_reason AS (
    SELECT
        month_end_date, worker_id,
        SUM(CASE WHEN action_reason = 'Promotion'              THEN d_base_nom ELSE 0 END) AS promo_base_nom,
        SUM(CASE WHEN action_reason = 'Promotion'              THEN d_base_con ELSE 0 END) AS promo_base_con,
        SUM(CASE WHEN action_reason = 'Promotion'              THEN d_load_nom ELSE 0 END) AS promo_load_nom,
        SUM(CASE WHEN action_reason = 'Promotion'              THEN d_load_con ELSE 0 END) AS promo_load_con,
        SUM(CASE WHEN action_reason = 'Demotion'               THEN d_base_nom ELSE 0 END) AS demo_base_nom,
        SUM(CASE WHEN action_reason = 'Demotion'               THEN d_base_con ELSE 0 END) AS demo_base_con,
        SUM(CASE WHEN action_reason = 'Demotion'               THEN d_load_nom ELSE 0 END) AS demo_load_nom,
        SUM(CASE WHEN action_reason = 'Demotion'               THEN d_load_con ELSE 0 END) AS demo_load_con,
        SUM(CASE WHEN action_reason = 'Tenure Increase'        THEN d_base_nom ELSE 0 END) AS tenure_base_nom,
        SUM(CASE WHEN action_reason = 'Tenure Increase'        THEN d_base_con ELSE 0 END) AS tenure_base_con,
        SUM(CASE WHEN action_reason = 'Tenure Increase'        THEN d_load_nom ELSE 0 END) AS tenure_load_nom,
        SUM(CASE WHEN action_reason = 'Tenure Increase'        THEN d_load_con ELSE 0 END) AS tenure_load_con,
        SUM(CASE WHEN action_reason = 'Market Adjustment'      THEN d_base_nom ELSE 0 END) AS market_base_nom,
        SUM(CASE WHEN action_reason = 'Market Adjustment'      THEN d_base_con ELSE 0 END) AS market_base_con,
        SUM(CASE WHEN action_reason = 'Market Adjustment'      THEN d_load_nom ELSE 0 END) AS market_load_nom,
        SUM(CASE WHEN action_reason = 'Market Adjustment'      THEN d_load_con ELSE 0 END) AS market_load_con,
        SUM(CASE WHEN action_reason = 'Relocation Adjustment'  THEN d_base_nom ELSE 0 END) AS reloc_base_nom,
        SUM(CASE WHEN action_reason = 'Relocation Adjustment'  THEN d_base_con ELSE 0 END) AS reloc_base_con,
        SUM(CASE WHEN action_reason = 'Relocation Adjustment'  THEN d_load_nom ELSE 0 END) AS reloc_load_nom,
        SUM(CASE WHEN action_reason = 'Relocation Adjustment'  THEN d_load_con ELSE 0 END) AS reloc_load_con,
        SUM(CASE WHEN action_reason = 'International Transfer' THEN d_base_nom ELSE 0 END) AS intl_base_nom,
        SUM(CASE WHEN action_reason = 'International Transfer' THEN d_base_con ELSE 0 END) AS intl_base_con,
        SUM(CASE WHEN action_reason = 'International Transfer' THEN d_load_nom ELSE 0 END) AS intl_load_nom,
        SUM(CASE WHEN action_reason = 'International Transfer' THEN d_load_con ELSE 0 END) AS intl_load_con
    FROM pay_event
    GROUP BY month_end_date, worker_id
),

-- the month's steps for every worker present at both ends
step AS (
    SELECT
        mp.month_end_date, mp.worker_id, pb.* EXCLUDE (month_end_date, worker_id),
        mp.b1 * mp.x1p * (mp.f1 - mp.f0)                         AS fte_base_nom,
        mp.b1 * mp.k1  * (mp.f1 - mp.f0)                         AS fte_base_con,
        mp.b1 * mp.x1p * (mp.f1 - mp.f0) * (1 + mp.r0)           AS fte_load_nom,
        mp.b1 * mp.k1  * (mp.f1 - mp.f0) * (1 + mp.r0)           AS fte_load_con,
        mp.b1 * mp.x1p * mp.f1 * (mp.r1 - mp.r0)                 AS fringe_load_nom,
        mp.b1 * mp.k1  * mp.f1 * (mp.r1 - mp.r0)                 AS fringe_load_con,
        mp.b1 * mp.f1 * (mp.x1 - mp.x1p)                         AS fx_base_nom,
        mp.b1 * mp.f1 * (1 + mp.r1) * (mp.x1 - mp.x1p)           AS fx_load_nom
    FROM month_pair AS mp
    LEFT JOIN pay_by_reason AS pb ON pb.month_end_date = mp.month_end_date AND pb.worker_id = mp.worker_id
),

-- job records that changed the department or the office
job_move AS (
    SELECT
        worker_id, effective_start_date, action_reason,
        department_id <> LAG(department_id) OVER w AS dept_changed,
        location_id   <> LAG(location_id)   OVER w AS loc_changed,
        country_code  <> LAG(country_code)  OVER w AS country_changed
    FROM (
        SELECT j.*, l.country_code
        FROM staging.stg_job_history AS j
        JOIN staging.stg_location AS l ON l.location_id = j.location_id
    )
    WINDOW w AS (PARTITION BY worker_id ORDER BY effective_start_date, job_record_id)
),

org_move AS (
    SELECT worker_id, effective_start_date, action_reason AS org_move_reason
    FROM job_move WHERE dept_changed
),

location_move AS (
    SELECT worker_id, effective_start_date,
           CASE WHEN country_changed THEN 'International Transfer' ELSE 'Relocation' END AS location_move_reason
    FROM job_move WHERE loc_changed
)

SELECT
    s.month_end_date,
    s.worker_id,
    om.org_move_reason,
    lm.location_move_reason,
    -- running totals since the worker's first month-end (0 on that month-end)
    SUM(COALESCE(st.promo_base_nom, 0))   OVER run AS cum_promotion_base_nominal,
    SUM(COALESCE(st.promo_base_con, 0))   OVER run AS cum_promotion_base_constant,
    SUM(COALESCE(st.promo_load_nom, 0))   OVER run AS cum_promotion_loaded_nominal,
    SUM(COALESCE(st.promo_load_con, 0))   OVER run AS cum_promotion_loaded_constant,
    SUM(COALESCE(st.demo_base_nom, 0))    OVER run AS cum_demotion_base_nominal,
    SUM(COALESCE(st.demo_base_con, 0))    OVER run AS cum_demotion_base_constant,
    SUM(COALESCE(st.demo_load_nom, 0))    OVER run AS cum_demotion_loaded_nominal,
    SUM(COALESCE(st.demo_load_con, 0))    OVER run AS cum_demotion_loaded_constant,
    SUM(COALESCE(st.tenure_base_nom, 0))  OVER run AS cum_tenure_base_nominal,
    SUM(COALESCE(st.tenure_base_con, 0))  OVER run AS cum_tenure_base_constant,
    SUM(COALESCE(st.tenure_load_nom, 0))  OVER run AS cum_tenure_loaded_nominal,
    SUM(COALESCE(st.tenure_load_con, 0))  OVER run AS cum_tenure_loaded_constant,
    SUM(COALESCE(st.market_base_nom, 0))  OVER run AS cum_market_base_nominal,
    SUM(COALESCE(st.market_base_con, 0))  OVER run AS cum_market_base_constant,
    SUM(COALESCE(st.market_load_nom, 0))  OVER run AS cum_market_loaded_nominal,
    SUM(COALESCE(st.market_load_con, 0))  OVER run AS cum_market_loaded_constant,
    SUM(COALESCE(st.reloc_base_nom, 0))   OVER run AS cum_relocation_base_nominal,
    SUM(COALESCE(st.reloc_base_con, 0))   OVER run AS cum_relocation_base_constant,
    SUM(COALESCE(st.reloc_load_nom, 0))   OVER run AS cum_relocation_loaded_nominal,
    SUM(COALESCE(st.reloc_load_con, 0))   OVER run AS cum_relocation_loaded_constant,
    SUM(COALESCE(st.intl_base_nom, 0))    OVER run AS cum_intl_transfer_base_nominal,
    SUM(COALESCE(st.intl_base_con, 0))    OVER run AS cum_intl_transfer_base_constant,
    SUM(COALESCE(st.intl_load_nom, 0))    OVER run AS cum_intl_transfer_loaded_nominal,
    SUM(COALESCE(st.intl_load_con, 0))    OVER run AS cum_intl_transfer_loaded_constant,
    SUM(COALESCE(st.fte_base_nom, 0))     OVER run AS cum_fte_base_nominal,
    SUM(COALESCE(st.fte_base_con, 0))     OVER run AS cum_fte_base_constant,
    SUM(COALESCE(st.fte_load_nom, 0))     OVER run AS cum_fte_loaded_nominal,
    SUM(COALESCE(st.fte_load_con, 0))     OVER run AS cum_fte_loaded_constant,
    SUM(COALESCE(st.fringe_load_nom, 0))  OVER run AS cum_fringe_loaded_nominal,
    SUM(COALESCE(st.fringe_load_con, 0))  OVER run AS cum_fringe_loaded_constant,
    SUM(COALESCE(st.fx_base_nom, 0))      OVER run AS cum_fx_base_nominal,
    SUM(COALESCE(st.fx_load_nom, 0))      OVER run AS cum_fx_loaded_nominal,
    -- running counts of months with each kind of change (a pair's "people affected")
    SUM(CASE WHEN st.promo_base_con  <> 0 THEN 1 ELSE 0 END) OVER run AS cum_promotion_events,
    SUM(CASE WHEN st.demo_base_con   <> 0 THEN 1 ELSE 0 END) OVER run AS cum_demotion_events,
    SUM(CASE WHEN st.tenure_base_con <> 0 THEN 1 ELSE 0 END) OVER run AS cum_tenure_events,
    SUM(CASE WHEN st.market_base_con <> 0 THEN 1 ELSE 0 END) OVER run AS cum_market_events,
    SUM(CASE WHEN st.reloc_base_con  <> 0 THEN 1 ELSE 0 END) OVER run AS cum_relocation_events,
    SUM(CASE WHEN st.intl_base_con   <> 0 THEN 1 ELSE 0 END) OVER run AS cum_intl_transfer_events,
    SUM(CASE WHEN st.fte_base_con    <> 0 THEN 1 ELSE 0 END) OVER run AS cum_fte_events
FROM intermediate.int_worker_month_end_snapshot AS s
LEFT JOIN step AS st ON st.month_end_date = s.month_end_date AND st.worker_id = s.worker_id
ASOF LEFT JOIN org_move AS om
  ON om.worker_id = s.worker_id AND s.month_end_date >= om.effective_start_date
ASOF LEFT JOIN location_move AS lm
  ON lm.worker_id = s.worker_id AND s.month_end_date >= lm.effective_start_date
WINDOW run AS (PARTITION BY s.worker_id ORDER BY s.month_end_date ROWS UNBOUNDED PRECEDING);
