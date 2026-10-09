-- mart_workforce_cost_bridge
-- Grain: one row per month x department x driver.
--
-- Explains how each department's annualized pay run-rate moved from the prior
-- month-end to the current month-end. For every department and month:
--
--   Opening Run-Rate
--   + Hires                    new workers, valued at their current pay
--   - Terminations             leavers, valued at their prior pay
--   + Transfers In             movers into the department, valued at their PRIOR pay
--   - Transfers Out            movers out of the department, valued at their prior pay
--   + Promotions               pay change for workers whose job level went up
--   + Demotions                pay change for workers whose job level went down
--   + Tenure & Market Adj.     pay change for everyone else: anniversary (tenure)
--                              raises, market adjustments, same-country relocations
--   + International Mobility   pay and fringe re-levelling when someone changes country
--   + FTE Changes              moves between full-time and part-time
--   + Fringe Rate Changes      new calendar-year fringe rates for the same country
--   + FX Rate Changes          month-over-month currency movement (nominal only)
--   = Closing Run-Rate
--
-- Why transfers are valued at prior pay: it makes transfers net to exactly zero
-- for the company as a whole. Any pay change a mover receives shows up as a
-- driver (promotion, tenure raise, mobility...) in the department they moved into.
--
-- Rate decomposition for a continuing worker, with B = local base salary,
-- F = FTE, X = USD per local unit, R = fringe rate, 0 = prior month-end,
-- 1 = current month-end and X1p = the CURRENT currency at the PRIOR month-end rate:
--
--   pay change    = (B1 * X1p - B0 * X0) * F0 * (1 + R0)
--   FTE change    =  B1 * X1p * (F1 - F0) * (1 + R0)
--   fringe change =  B1 * X1p * F1 * (R1 - R0)
--   FX change     =  B1 * F1 * (1 + R1) * (X1 - X1p)
--
-- The four terms telescope: they always sum to exactly (current value - prior value).
-- In constant currency X never moves, so the FX term is zero by construction.
-- Base (unloaded) measures use the same formulas with R = 0.
--
-- Executive officers are excluded from compensation reporting.
CREATE OR REPLACE TABLE marts.mart_workforce_cost_bridge AS
WITH snap AS (
    SELECT *
    FROM intermediate.int_worker_month_end_snapshot
    WHERE NOT is_executive_officer
),

month_pairs AS (
    SELECT month_end_date, prior_month_end_date
    FROM intermediate.int_month_end_calendar
    WHERE prior_month_end_date IS NOT NULL
),

-- each month's population at the prior month-end ...
prior_side AS (
    SELECT mp.month_end_date, mp.prior_month_end_date, s.*  EXCLUDE (month_end_date)
    FROM month_pairs AS mp
    JOIN snap AS s ON s.month_end_date = mp.prior_month_end_date
),

-- ... and at the current month-end
current_side AS (
    SELECT mp.month_end_date, mp.prior_month_end_date, s.* EXCLUDE (month_end_date)
    FROM month_pairs AS mp
    JOIN snap AS s ON s.month_end_date = mp.month_end_date
),

-- every worker active at either end of each month, prior state (p) beside current state (c)
worker_pairs AS (
    SELECT
        COALESCE(c.month_end_date, p.month_end_date)               AS month_end_date,
        COALESCE(c.worker_id, p.worker_id)                         AS worker_id,
        CASE
            WHEN p.worker_id IS NULL               THEN 'Hire'
            WHEN c.worker_id IS NULL               THEN 'Termination'
            WHEN p.department_id <> c.department_id THEN 'Transfer'
            ELSE 'Stayer'
        END                                              AS movement_type,
        p.department_id AS dept_p,   c.department_id AS dept_c,
        p.country_code  AS country_p, c.country_code AS country_c,
        p.grade         AS grade_p,   c.grade        AS grade_c,
        p.fte           AS f0,        c.fte          AS f1,
        p.base_salary_annual_local AS b0, c.base_salary_annual_local AS b1,
        p.fx_rate_actual   AS x0,     c.fx_rate_actual   AS x1,
        p.fx_rate_constant AS k0,     c.fx_rate_constant AS k1,
        p.fringe_rate      AS r0,     c.fringe_rate      AS r1,
        fx_cp.usd_per_local_actual AS x1p          -- current currency at prior month-end
    FROM prior_side AS p
    FULL OUTER JOIN current_side AS c
           ON c.month_end_date = p.month_end_date
          AND c.worker_id      = p.worker_id
    LEFT JOIN staging.stg_fx_rate AS fx_cp
           ON fx_cp.currency_code = c.currency_code
          AND fx_cp.rate_date     = c.prior_month_end_date
),

-- prior and current values in all four bases, plus the rate decomposition for continuing workers
valued AS (
    SELECT
        *,
        -- values at each end
        b0 * f0 * x0                  AS base_nom_0,
        b0 * f0 * k0                  AS base_con_0,
        b0 * f0 * x0 * (1 + r0)       AS load_nom_0,
        b0 * f0 * k0 * (1 + r0)       AS load_con_0,
        b1 * f1 * x1                  AS base_nom_1,
        b1 * f1 * k1                  AS base_con_1,
        b1 * f1 * x1 * (1 + r1)       AS load_nom_1,
        b1 * f1 * k1 * (1 + r1)       AS load_con_1,

        -- pay-rate effect
        (b1 * x1p - b0 * x0) * f0                 AS pay_base_nom,
        (b1 * k1  - b0 * k0) * f0                 AS pay_base_con,
        (b1 * x1p - b0 * x0) * f0 * (1 + r0)      AS pay_load_nom,
        (b1 * k1  - b0 * k0) * f0 * (1 + r0)      AS pay_load_con,
        -- FTE effect
        b1 * x1p * (f1 - f0)                      AS fte_base_nom,
        b1 * k1  * (f1 - f0)                      AS fte_base_con,
        b1 * x1p * (f1 - f0) * (1 + r0)           AS fte_load_nom,
        b1 * k1  * (f1 - f0) * (1 + r0)           AS fte_load_con,
        -- fringe effect (loaded measures only)
        b1 * x1p * f1 * (r1 - r0)                 AS fringe_load_nom,
        b1 * k1  * f1 * (r1 - r0)                 AS fringe_load_con,
        -- FX effect (nominal only; constant currency has no FX movement)
        b1 * f1 * (x1 - x1p)                      AS fx_base_nom,
        b1 * f1 * (1 + r1) * (x1 - x1p)           AS fx_load_nom,

        CASE
            WHEN country_c <> country_p THEN 'International Mobility'
            WHEN grade_c   >  grade_p   THEN 'Promotions'
            WHEN grade_c   <  grade_p   THEN 'Demotions'
            ELSE 'Tenure & Market Adjustments'
        END                                       AS pay_driver
    FROM worker_pairs
),

-- one row per worker per driver line
driver_lines AS (
    -- opening balance: everyone active at the prior month-end, in their prior department
    SELECT month_end_date, dept_p AS department_id, 'Opening Run-Rate' AS driver, worker_id,
           1 AS headcount, f0 AS fte, base_nom_0 AS base_nom, base_con_0 AS base_con,
           load_nom_0 AS load_nom, load_con_0 AS load_con
    FROM valued WHERE movement_type <> 'Hire'

    UNION ALL
    SELECT month_end_date, dept_c, 'Hires', worker_id,
           1, f1, base_nom_1, base_con_1, load_nom_1, load_con_1
    FROM valued WHERE movement_type = 'Hire'

    UNION ALL
    SELECT month_end_date, dept_p, 'Terminations', worker_id,
           -1, -f0, -base_nom_0, -base_con_0, -load_nom_0, -load_con_0
    FROM valued WHERE movement_type = 'Termination'

    UNION ALL
    SELECT month_end_date, dept_c, 'Transfers In', worker_id,
           1, f0, base_nom_0, base_con_0, load_nom_0, load_con_0
    FROM valued WHERE movement_type = 'Transfer'

    UNION ALL
    SELECT month_end_date, dept_p, 'Transfers Out', worker_id,
           -1, -f0, -base_nom_0, -base_con_0, -load_nom_0, -load_con_0
    FROM valued WHERE movement_type = 'Transfer'

    -- pay-rate effect; for country moves the fringe re-levelling is included here too
    UNION ALL
    SELECT month_end_date, dept_c, pay_driver, worker_id,
           0, 0, pay_base_nom, pay_base_con,
           pay_load_nom + CASE WHEN pay_driver = 'International Mobility' THEN fringe_load_nom ELSE 0 END,
           pay_load_con + CASE WHEN pay_driver = 'International Mobility' THEN fringe_load_con ELSE 0 END
    FROM valued
    WHERE movement_type IN ('Stayer', 'Transfer')
      AND (pay_base_nom <> 0 OR pay_base_con <> 0 OR pay_driver = 'International Mobility')

    UNION ALL
    SELECT month_end_date, dept_c, 'FTE Changes', worker_id,
           0, f1 - f0, fte_base_nom, fte_base_con, fte_load_nom, fte_load_con
    FROM valued WHERE movement_type IN ('Stayer', 'Transfer') AND f1 <> f0

    UNION ALL
    SELECT month_end_date, dept_c, 'Fringe Rate Changes', worker_id,
           0, 0, 0, 0, fringe_load_nom, fringe_load_con
    FROM valued
    WHERE movement_type IN ('Stayer', 'Transfer') AND pay_driver <> 'International Mobility' AND r1 <> r0

    UNION ALL
    SELECT month_end_date, dept_c, 'FX Rate Changes', worker_id,
           0, 0, fx_base_nom, 0, fx_load_nom, 0
    FROM valued WHERE movement_type IN ('Stayer', 'Transfer') AND x1 <> x1p

    -- closing balance: everyone active at the current month-end, in their current department
    UNION ALL
    SELECT month_end_date, dept_c, 'Closing Run-Rate', worker_id,
           1, f1, base_nom_1, base_con_1, load_nom_1, load_con_1
    FROM valued WHERE movement_type <> 'Termination'
),

driver_order AS (
    SELECT * FROM (VALUES
        (1,  'Opening Run-Rate',       'Balance'),
        (2,  'Hires',                  'Headcount Movement'),
        (3,  'Terminations',           'Headcount Movement'),
        (4,  'Transfers In',           'Headcount Movement'),
        (5,  'Transfers Out',          'Headcount Movement'),
        (6,  'Promotions',                  'Pay Rate'),
        (7,  'Demotions',                   'Pay Rate'),
        (8,  'Tenure & Market Adjustments', 'Pay Rate'),
        (9,  'International Mobility',      'Pay Rate'),
        (10, 'FTE Changes',                 'Workforce Mix'),
        (11, 'Fringe Rate Changes',         'Fringe & FX'),
        (12, 'FX Rate Changes',             'Fringe & FX'),
        (13, 'Closing Run-Rate',            'Balance')
    ) AS t(driver_order, driver, driver_group)
)

SELECT
    dl.month_end_date,
    cal.prior_month_end_date,
    cal.fiscal_year,
    cal.fiscal_quarter_label,
    cal.fiscal_period,
    dl.department_id,
    d.department_name,
    d.sub_function,
    d.function_name,
    d.cost_center,
    o.driver_order,
    dl.driver,
    o.driver_group,
    CAST(COUNT(DISTINCT dl.worker_id) AS INTEGER)           AS worker_count,
    CAST(SUM(dl.headcount) AS INTEGER)                      AS headcount,
    -- sum as exact decimals: floating-point sums can differ in the last cent
    -- from run to run, which would make the exported files non-reproducible
    ROUND(SUM(CAST(dl.fte      AS DECIMAL(18, 4))), 2)      AS fte,
    ROUND(SUM(CAST(dl.base_nom AS DECIMAL(18, 4))), 2)      AS base_usd_nominal,
    ROUND(SUM(CAST(dl.base_con AS DECIMAL(18, 4))), 2)      AS base_usd_constant,
    ROUND(SUM(CAST(dl.load_nom AS DECIMAL(18, 4))), 2)      AS loaded_usd_nominal,
    ROUND(SUM(CAST(dl.load_con AS DECIMAL(18, 4))), 2)      AS loaded_usd_constant
FROM driver_lines AS dl
JOIN driver_order AS o                          ON o.driver = dl.driver
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = dl.month_end_date
LEFT JOIN staging.stg_department AS d           ON d.department_id = dl.department_id
GROUP BY ALL
ORDER BY dl.month_end_date, dl.department_id, o.driver_order;
