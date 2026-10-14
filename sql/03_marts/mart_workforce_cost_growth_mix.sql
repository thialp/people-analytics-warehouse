-- mart_workforce_cost_growth_mix
-- Grain: one row per date pair (each fiscal quarter-end against the same quarter-end a year
-- earlier) x view (Company, Function) x group x factor.
--
-- Why did total workforce cost change? Total workforce cost on a date is the employees' loaded
-- pay run-rate (executive officers excluded, as in every cost mart) plus the contingent
-- workers' annualized bill run-rate, in USD at that month-end's rates (nominal). Splitting the
-- population into segments k = worker type t x country c x level l (the grade for employees;
-- Contractor, Consultant or BPO for contingent workers), the cost is a product of six factors:
--
--   C = N x SUM_k  a_t x b_c|t x g_l|t,c x r_k x f_k
--
--   Volume          N          people
--   Workforce mix   a_t        share of employees and of contingent workers
--   Location mix    b_c|t      share of each country within the worker type
--   Level mix       g_l|t,c    share of each grade (or contingent type) within type and country
--   Rate            r_k        cost per head at the constant rate set: pay and bill rates
--   Currency        f_k        nominal / constant: what exchange rates did to the reported cost
--
-- Move the factors from the earlier date (0) to the later one (1) one at a time and each step
-- is an effect; the effects add up to C1 - C0 exactly. But the answer depends on the ORDER: the
-- factor moved first is valued at old levels of the others, the last one at new levels. The
-- Shapley value removes that bias: each factor's effect is its average contribution over every
-- order of the six factors. With v(S) = C evaluated with the factors in S at their later value
-- and the rest at their earlier value,
--
--   effect_i = SUM over S not containing i of  |S|! (6 - |S| - 1)! / 6!  x [ v(S + i) - v(S) ]
--
-- 64 evaluations per pair and group. The effects still add up to C1 - C0 exactly (test 78), and
-- the sequential split (in the order listed above) is kept beside it, so the size of the order
-- bias can be shown.
--
-- A segment present on only one date has a share of 0 on the other; its rate and currency
-- factor are taken from the date where it exists, so its whole arrival or departure is a mix
-- effect, never a rate effect.
CREATE OR REPLACE TABLE marts.mart_workforce_cost_growth_mix AS
WITH pairs AS (
    SELECT c.month_end_date AS to_month_end, f.month_end_date AS from_month_end,
           c.fiscal_year, c.fiscal_quarter_label
    FROM intermediate.int_month_end_calendar AS c
    JOIN intermediate.int_month_end_calendar AS f
      ON f.month_end_date = LAST_DAY(c.month_end_date - INTERVAL 12 MONTH)
    WHERE c.fiscal_month IN (3, 6, 9, 12)
),

population AS (
    SELECT s.month_end_date, d.function_name, 'Employee' AS worker_type, s.country_code,
           CAST(s.grade AS VARCHAR) AS level, s.loaded_usd_nominal AS nom, s.loaded_usd_constant AS con
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN staging.stg_department AS d USING (department_id)
    WHERE NOT s.is_executive_officer
    UNION ALL
    SELECT s.month_end_date, d.function_name, 'Contingent', s.country_code, s.cw_type,
           s.run_rate_usd_nominal, s.run_rate_usd_constant
    FROM intermediate.int_cw_month_end_snapshot AS s
    JOIN staging.stg_department AS d USING (department_id)
),

grouped AS (
    SELECT 1 AS view_order, 'Company' AS view_name, 'Arcadia Systems' AS group_name, * EXCLUDE (function_name)
    FROM population
    UNION ALL
    SELECT 2, 'Function', function_name, * EXCLUDE (function_name)
    FROM population
),

seg AS (
    SELECT p.from_month_end, p.to_month_end, g.view_order, g.view_name, g.group_name,
           g.worker_type AS t, g.country_code AS c, g.level AS l,
           COUNT(*) FILTER (WHERE g.month_end_date = p.from_month_end)                    AS n0,
           COUNT(*) FILTER (WHERE g.month_end_date = p.to_month_end)                      AS n1,
           COALESCE(SUM(g.nom) FILTER (WHERE g.month_end_date = p.from_month_end), 0)     AS nom0,
           COALESCE(SUM(g.nom) FILTER (WHERE g.month_end_date = p.to_month_end), 0)       AS nom1,
           COALESCE(SUM(g.con) FILTER (WHERE g.month_end_date = p.from_month_end), 0)     AS con0,
           COALESCE(SUM(g.con) FILTER (WHERE g.month_end_date = p.to_month_end), 0)       AS con1
    FROM pairs AS p
    JOIN grouped AS g ON g.month_end_date IN (p.from_month_end, p.to_month_end)
    GROUP BY ALL
),

sized AS (
    SELECT *,
           SUM(n0) OVER w_g AS big_n0,          SUM(n1) OVER w_g AS big_n1,
           SUM(n0) OVER w_t AS nt0,             SUM(n1) OVER w_t AS nt1,
           SUM(n0) OVER w_tc AS ntc0,           SUM(n1) OVER w_tc AS ntc1
    FROM seg
    WINDOW w_g  AS (PARTITION BY from_month_end, to_month_end, view_name, group_name),
           w_t  AS (PARTITION BY from_month_end, to_month_end, view_name, group_name, t),
           w_tc AS (PARTITION BY from_month_end, to_month_end, view_name, group_name, t, c)
),

-- the six factors at each date; where a factor is undefined on one date (the segment is
-- absent there), the other date's value stands in
factors AS (
    SELECT from_month_end, to_month_end, view_order, view_name, group_name, t, c, l,
           CAST(big_n0 AS DOUBLE) AS v0, CAST(big_n1 AS DOUBLE) AS v1,
           nt0 / big_n0 AS a0, nt1 / big_n1 AS a1,
           COALESCE(ntc0 / NULLIF(nt0, 0), ntc1 / NULLIF(nt1, 0)) AS b0,
           COALESCE(ntc1 / NULLIF(nt1, 0), ntc0 / NULLIF(nt0, 0)) AS b1,
           COALESCE(n0 / NULLIF(ntc0, 0), n1 / NULLIF(ntc1, 0)) AS g0,
           COALESCE(n1 / NULLIF(ntc1, 0), n0 / NULLIF(ntc0, 0)) AS g1,
           COALESCE(con0 / NULLIF(n0, 0), con1 / NULLIF(n1, 0)) AS r0,
           COALESCE(con1 / NULLIF(n1, 0), con0 / NULLIF(n0, 0)) AS r1,
           COALESCE(nom0 / NULLIF(con0, 0), nom1 / NULLIF(con1, 0)) AS f0,
           COALESCE(nom1 / NULLIF(con1, 0), nom0 / NULLIF(con0, 0)) AS f1,
           n0, n1
    FROM sized
),

-- every subset S of the six factors, as bits: 1 Volume, 2 Workforce mix, 4 Location mix,
-- 8 Level mix, 16 Rate, 32 Currency
subsets AS (
    SELECT s AS bits, BIT_COUNT(s) AS size FROM range(64) AS r(s)
),

v AS (   -- the cost with the factors in S at their later value
    SELECT f.from_month_end, f.to_month_end, f.view_order, f.view_name, f.group_name, s.bits, s.size,
           -- each product is rounded to exact decimals before summing, so the result does not
           -- depend on the order a parallel sum adds rows in (the exports must be reproducible)
           SUM(CAST(  (CASE WHEN s.bits & 1  > 0 THEN f.v1 ELSE f.v0 END)
                    * (CASE WHEN s.bits & 2  > 0 THEN f.a1 ELSE f.a0 END)
                    * (CASE WHEN s.bits & 4  > 0 THEN f.b1 ELSE f.b0 END)
                    * (CASE WHEN s.bits & 8  > 0 THEN f.g1 ELSE f.g0 END)
                    * (CASE WHEN s.bits & 16 > 0 THEN f.r1 ELSE f.r0 END)
                    * (CASE WHEN s.bits & 32 > 0 THEN f.f1 ELSE f.f0 END) AS DECIMAL(38, 6))) AS cost
    FROM factors AS f CROSS JOIN subsets AS s
    GROUP BY ALL
),

factor_list AS (
    SELECT * FROM (VALUES
        (1, 1,  'Volume',        'More or fewer people'),
        (2, 2,  'Workforce mix', 'The balance of employees and contingent workers'),
        (3, 4,  'Location mix',  'Which countries the people are in'),
        (4, 8,  'Level mix',     'Which grades (or contingent types) the people are in'),
        (5, 16, 'Rate',          'What each person costs at constant exchange rates: pay and bill rates'),
        (6, 32, 'Currency',      'What exchange rates did to the reported cost')
    ) AS x(factor_order, bit, factor, factor_meaning)
),

effects AS (
    SELECT v.from_month_end, v.to_month_end, v.view_order, v.view_name, v.group_name,
           fl.factor_order, fl.factor, fl.factor_meaning,
           SUM(CAST(v.cost * CASE WHEN v.bits & fl.bit > 0
                                  THEN factorial(v.size - 1) * factorial(6 - v.size)
                                  ELSE -(factorial(v.size) * factorial(5 - v.size)) END AS DECIMAL(38, 6))) / 720 AS shapley,
           SUM(v.cost * CASE WHEN v.bits = 2 * fl.bit - 1 THEN 1
                             WHEN v.bits = fl.bit - 1     THEN -1 ELSE 0 END)               AS sequential
    FROM v CROSS JOIN factor_list AS fl
    GROUP BY ALL
),

balances AS (
    SELECT from_month_end, to_month_end, view_order, view_name, group_name,
           MAX(cost) FILTER (WHERE bits = 0)  AS opening_cost,
           MAX(cost) FILTER (WHERE bits = 63) AS closing_cost
    FROM v GROUP BY ALL
),

heads AS (
    SELECT from_month_end, to_month_end, view_name, group_name,
           SUM(n0) AS opening_headcount, SUM(n1) AS closing_headcount
    FROM factors GROUP BY ALL
),

lines AS (
    SELECT from_month_end, to_month_end, view_order, view_name, group_name,
           0 AS factor_order, 'Opening cost' AS factor, 'Total workforce cost at the earlier date' AS factor_meaning,
           opening_cost AS shapley, opening_cost AS sequential
    FROM balances
    UNION ALL
    SELECT from_month_end, to_month_end, view_order, view_name, group_name,
           factor_order, factor, factor_meaning, shapley, sequential
    FROM effects
    UNION ALL
    SELECT from_month_end, to_month_end, view_order, view_name, group_name,
           7, 'Closing cost', 'Total workforce cost at the later date', closing_cost, closing_cost
    FROM balances
)

SELECT
    l.from_month_end,
    l.to_month_end,
    p.fiscal_year,
    p.fiscal_quarter_label,
    'Year over year'                                                   AS pair_type,
    l.view_order,
    l.view_name,
    l.group_name,
    l.factor_order,
    l.factor,
    l.factor_meaning,
    CAST(ROUND(l.shapley, 2) AS DECIMAL(18, 2))                        AS shapley_effect_usd,
    CAST(ROUND(l.sequential, 2) AS DECIMAL(18, 2))                     AS sequential_effect_usd,
    CAST(ROUND(l.sequential - l.shapley, 2) AS DECIMAL(18, 2))         AS order_bias_usd,
    h.opening_headcount,
    h.closing_headcount
FROM lines AS l
JOIN pairs AS p ON p.to_month_end = l.to_month_end
JOIN heads AS h
  ON h.from_month_end = l.from_month_end AND h.to_month_end = l.to_month_end
 AND h.view_name = l.view_name AND h.group_name = l.group_name
ORDER BY l.to_month_end, l.view_order, l.group_name, l.factor_order;
