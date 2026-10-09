-- mart_compensation_walk
-- Grain: one row per date pair x view x group x walk step x movement reason.
--
-- The DuckDB twin of tableau/custom_sql_compensation_walk.sql (same rules, same
-- columns, same numbers; the Tableau file is the documented one). It answers, for any
-- two month-ends on the grid and any group in six views, why compensation moved:
--
--   Opening + Hires + Exits + Transfers In + Transfers Out
--           + Promotions + Demotions + Tenure Increases + Market Adjustments
--           + Relocation Adjustments + International Transfer Adjustments
--           + FTE Changes + Fringe Rate Changes + FX Translation  =  Closing
--
-- exactly, in headcount, FTE and all four dollar measures, for every row group.
-- Field reference and worked examples: docs/projects/compensation-walk/compensation_walk.md
CREATE OR REPLACE TABLE marts.mart_compensation_walk AS
WITH grid AS (
    -- === GRID === every quarter-end to every later quarter-end (136 pairs) plus every
    -- month-end to the next one (48). Remove both conditions for every month-end to every
    -- later month-end (1,176 pairs, about 8x the rows and run time).
    SELECT f.month_end_date AS from_date, t.month_end_date AS to_date
    FROM intermediate.int_month_end_calendar AS f
    JOIN intermediate.int_month_end_calendar AS t ON t.month_end_date > f.month_end_date
    WHERE (MONTH(f.month_end_date) IN (3, 6, 9, 12) AND MONTH(t.month_end_date) IN (3, 6, 9, 12))
       OR t.prior_month_end_date = f.month_end_date
),

snap AS (
    SELECT s.month_end_date, s.worker_id, s.department_id, s.location_id, s.fte,
           s.base_usd_nominal, s.base_usd_constant, s.loaded_usd_nominal, s.loaded_usd_constant, l.*
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN intermediate.int_worker_pay_ledger AS l USING (month_end_date, worker_id)
),

-- 1. one row per worker per date pair: everyone present at the From or the To month-end
worker_pair AS (
    SELECT
        g.from_date, g.to_date,
        CASE WHEN o.worker_id IS NULL THEN 'Hire'
             WHEN c.worker_id IS NULL THEN 'Exit'
             ELSE 'Continuing' END                                             AS worker_class,
        CASE WHEN c.worker_id IS NULL THEN w.termination_type END              AS exit_reason,
        o.department_id AS o_dept, o.location_id AS o_loc,
        c.department_id AS c_dept, c.location_id AS c_loc,
        CASE WHEN o.department_id <> c.department_id THEN c.org_move_reason END      AS org_move_reason,
        CASE WHEN o.location_id   <> c.location_id   THEN c.location_move_reason END AS location_move_reason,
        -- every amount becomes an exact decimal here, so all later sums are exact and
        -- repeatable (the published CSVs do not change between runs)
        CAST(o.fte AS DECIMAL(38, 10)) AS f0,                 CAST(c.fte AS DECIMAL(38, 10)) AS f1,
        CAST(o.base_usd_nominal    AS DECIMAL(38, 10)) AS bn0, CAST(o.base_usd_constant   AS DECIMAL(38, 10)) AS bc0,
        CAST(o.loaded_usd_nominal  AS DECIMAL(38, 10)) AS ln0, CAST(o.loaded_usd_constant AS DECIMAL(38, 10)) AS lc0,
        CAST(c.base_usd_nominal    AS DECIMAL(38, 10)) AS bn1, CAST(c.base_usd_constant   AS DECIMAL(38, 10)) AS bc1,
        CAST(c.loaded_usd_nominal  AS DECIMAL(38, 10)) AS ln1, CAST(c.loaded_usd_constant AS DECIMAL(38, 10)) AS lc1,
        CAST(c.cum_promotion_base_nominal        - o.cum_promotion_base_nominal AS DECIMAL(38, 10))        AS promo_bn,
        CAST(c.cum_promotion_base_constant       - o.cum_promotion_base_constant AS DECIMAL(38, 10))       AS promo_bc,
        CAST(c.cum_promotion_loaded_nominal      - o.cum_promotion_loaded_nominal AS DECIMAL(38, 10))      AS promo_ln,
        CAST(c.cum_promotion_loaded_constant     - o.cum_promotion_loaded_constant AS DECIMAL(38, 10))     AS promo_lc,
        CAST(c.cum_demotion_base_nominal         - o.cum_demotion_base_nominal AS DECIMAL(38, 10))         AS demo_bn,
        CAST(c.cum_demotion_base_constant        - o.cum_demotion_base_constant AS DECIMAL(38, 10))        AS demo_bc,
        CAST(c.cum_demotion_loaded_nominal       - o.cum_demotion_loaded_nominal AS DECIMAL(38, 10))       AS demo_ln,
        CAST(c.cum_demotion_loaded_constant      - o.cum_demotion_loaded_constant AS DECIMAL(38, 10))      AS demo_lc,
        CAST(c.cum_tenure_base_nominal           - o.cum_tenure_base_nominal AS DECIMAL(38, 10))           AS tenure_bn,
        CAST(c.cum_tenure_base_constant          - o.cum_tenure_base_constant AS DECIMAL(38, 10))          AS tenure_bc,
        CAST(c.cum_tenure_loaded_nominal         - o.cum_tenure_loaded_nominal AS DECIMAL(38, 10))         AS tenure_ln,
        CAST(c.cum_tenure_loaded_constant        - o.cum_tenure_loaded_constant AS DECIMAL(38, 10))        AS tenure_lc,
        CAST(c.cum_market_base_nominal           - o.cum_market_base_nominal AS DECIMAL(38, 10))           AS market_bn,
        CAST(c.cum_market_base_constant          - o.cum_market_base_constant AS DECIMAL(38, 10))          AS market_bc,
        CAST(c.cum_market_loaded_nominal         - o.cum_market_loaded_nominal AS DECIMAL(38, 10))         AS market_ln,
        CAST(c.cum_market_loaded_constant        - o.cum_market_loaded_constant AS DECIMAL(38, 10))        AS market_lc,
        CAST(c.cum_relocation_base_nominal       - o.cum_relocation_base_nominal AS DECIMAL(38, 10))       AS reloc_bn,
        CAST(c.cum_relocation_base_constant      - o.cum_relocation_base_constant AS DECIMAL(38, 10))      AS reloc_bc,
        CAST(c.cum_relocation_loaded_nominal     - o.cum_relocation_loaded_nominal AS DECIMAL(38, 10))     AS reloc_ln,
        CAST(c.cum_relocation_loaded_constant    - o.cum_relocation_loaded_constant AS DECIMAL(38, 10))    AS reloc_lc,
        CAST(c.cum_intl_transfer_base_nominal    - o.cum_intl_transfer_base_nominal AS DECIMAL(38, 10))    AS intl_bn,
        CAST(c.cum_intl_transfer_base_constant   - o.cum_intl_transfer_base_constant AS DECIMAL(38, 10))   AS intl_bc,
        CAST(c.cum_intl_transfer_loaded_nominal  - o.cum_intl_transfer_loaded_nominal AS DECIMAL(38, 10))  AS intl_ln,
        CAST(c.cum_intl_transfer_loaded_constant - o.cum_intl_transfer_loaded_constant AS DECIMAL(38, 10)) AS intl_lc,
        CAST(c.cum_fte_base_nominal              - o.cum_fte_base_nominal AS DECIMAL(38, 10))              AS fte_bn,
        CAST(c.cum_fte_base_constant             - o.cum_fte_base_constant AS DECIMAL(38, 10))             AS fte_bc,
        CAST(c.cum_fte_loaded_nominal            - o.cum_fte_loaded_nominal AS DECIMAL(38, 10))            AS fte_ln,
        CAST(c.cum_fte_loaded_constant           - o.cum_fte_loaded_constant AS DECIMAL(38, 10))           AS fte_lc,
        CAST(c.cum_fringe_loaded_nominal         - o.cum_fringe_loaded_nominal AS DECIMAL(38, 10))         AS fringe_ln,
        CAST(c.cum_fringe_loaded_constant        - o.cum_fringe_loaded_constant AS DECIMAL(38, 10))        AS fringe_lc,
        CAST(c.cum_fx_base_nominal               - o.cum_fx_base_nominal AS DECIMAL(38, 10))               AS fx_bn,
        CAST(c.cum_fx_loaded_nominal             - o.cum_fx_loaded_nominal AS DECIMAL(38, 10))             AS fx_ln,
        c.cum_promotion_events     - o.cum_promotion_events     AS promo_events,
        c.cum_demotion_events      - o.cum_demotion_events      AS demo_events,
        c.cum_tenure_events        - o.cum_tenure_events        AS tenure_events,
        c.cum_market_events        - o.cum_market_events        AS market_events,
        c.cum_relocation_events    - o.cum_relocation_events    AS reloc_events,
        c.cum_intl_transfer_events - o.cum_intl_transfer_events AS intl_events,
        c.cum_fte_events           - o.cum_fte_events           AS fte_events
    FROM grid AS g
    -- everyone employed at some point between the two dates; the WHERE keeps those
    -- present at the From or the To month-end
    JOIN staging.stg_worker AS w
      ON w.original_hire_date <= g.to_date
     AND (w.termination_date IS NULL OR w.termination_date >= g.from_date)
     AND NOT w.is_executive_officer
    LEFT JOIN snap AS o ON o.month_end_date = g.from_date AND o.worker_id = w.worker_id
    LEFT JOIN snap AS c ON c.month_end_date = g.to_date   AND c.worker_id = w.worker_id
    WHERE o.worker_id IS NOT NULL OR c.worker_id IS NOT NULL
),

-- 2. aggregate early: workers with the same dates, groups and reasons become one row
pair_group AS MATERIALIZED (
    SELECT
        from_date, to_date, worker_class, exit_reason, o_dept, o_loc, c_dept, c_loc,
        org_move_reason, location_move_reason,
        COUNT(*) AS n, SUM(f0) AS f0, SUM(f1) AS f1,
        SUM(bn0) AS bn0, SUM(bc0) AS bc0, SUM(ln0) AS ln0, SUM(lc0) AS lc0,
        SUM(bn1) AS bn1, SUM(bc1) AS bc1, SUM(ln1) AS ln1, SUM(lc1) AS lc1,
        SUM(promo_bn) AS promo_bn, SUM(promo_bc) AS promo_bc, SUM(promo_ln) AS promo_ln, SUM(promo_lc) AS promo_lc,
        SUM(demo_bn) AS demo_bn, SUM(demo_bc) AS demo_bc, SUM(demo_ln) AS demo_ln, SUM(demo_lc) AS demo_lc,
        SUM(tenure_bn) AS tenure_bn, SUM(tenure_bc) AS tenure_bc, SUM(tenure_ln) AS tenure_ln, SUM(tenure_lc) AS tenure_lc,
        SUM(market_bn) AS market_bn, SUM(market_bc) AS market_bc, SUM(market_ln) AS market_ln, SUM(market_lc) AS market_lc,
        SUM(reloc_bn) AS reloc_bn, SUM(reloc_bc) AS reloc_bc, SUM(reloc_ln) AS reloc_ln, SUM(reloc_lc) AS reloc_lc,
        SUM(intl_bn) AS intl_bn, SUM(intl_bc) AS intl_bc, SUM(intl_ln) AS intl_ln, SUM(intl_lc) AS intl_lc,
        SUM(fte_bn) AS fte_bn, SUM(fte_bc) AS fte_bc, SUM(fte_ln) AS fte_ln, SUM(fte_lc) AS fte_lc,
        SUM(fringe_ln) AS fringe_ln, SUM(fringe_lc) AS fringe_lc, SUM(fx_bn) AS fx_bn, SUM(fx_ln) AS fx_ln,
        SUM(CASE WHEN promo_events  > 0 THEN 1 ELSE 0 END) AS promo_people,
        SUM(CASE WHEN demo_events   > 0 THEN 1 ELSE 0 END) AS demo_people,
        SUM(CASE WHEN tenure_events > 0 THEN 1 ELSE 0 END) AS tenure_people,
        SUM(CASE WHEN market_events > 0 THEN 1 ELSE 0 END) AS market_people,
        SUM(CASE WHEN reloc_events  > 0 THEN 1 ELSE 0 END) AS reloc_people,
        SUM(CASE WHEN intl_events   > 0 THEN 1 ELSE 0 END) AS intl_people,
        SUM(CASE WHEN fte_events    > 0 THEN 1 ELSE 0 END) AS fte_people,
        SUM(CASE WHEN fringe_lc <> 0 OR fringe_ln <> 0 THEN 1 ELSE 0 END) AS fringe_people,
        SUM(CASE WHEN fx_bn <> 0 OR fx_ln <> 0 THEN 1 ELSE 0 END)         AS fx_people
    FROM worker_pair
    GROUP BY ALL
),

-- the group each department and office rolls up to
dept_map AS (
    SELECT d.department_id,
           CASE WHEN p.org_unit_type = 'Sub-function' THEN p.parent_org_unit_id ELSE p.org_unit_id END AS function_id,
           d.parent_org_unit_id AS leader_org_id
    FROM staging.stg_department AS d
    JOIN staging.stg_org_unit AS p ON p.org_unit_id = d.parent_org_unit_id
),

-- 3. expand late: each pre-aggregated row into the six views ...
view_row AS MATERIALIZED (
    SELECT
        pg.*, v.view_order, v.view_name,
        CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN od.function_id WHEN 3 THEN od.leader_org_id
                          WHEN 4 THEN pg.o_dept WHEN 5 THEN pg.o_loc   WHEN 6 THEN ol.country_code END AS open_key,
        CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN cd.function_id WHEN 3 THEN cd.leader_org_id
                          WHEN 4 THEN pg.c_dept WHEN 5 THEN pg.c_loc   WHEN 6 THEN cl.country_code END AS close_key,
        CASE WHEN v.view_order IN (2, 3, 4) THEN pg.org_move_reason
             WHEN v.view_order IN (5, 6)    THEN pg.location_move_reason END                      AS move_reason
    FROM pair_group AS pg
    LEFT JOIN dept_map AS od ON od.department_id = pg.o_dept
    LEFT JOIN dept_map AS cd ON cd.department_id = pg.c_dept
    LEFT JOIN staging.stg_location AS ol ON ol.location_id = pg.o_loc
    LEFT JOIN staging.stg_location AS cl ON cl.location_id = pg.c_loc
    CROSS JOIN (VALUES (1, 'Company'), (2, 'Function'), (3, 'Leader'),
                       (4, 'Department'), (5, 'Office'), (6, 'Country')) AS v(view_order, view_name)
),

-- ... and then into the fifteen walk steps (the Tableau file does both with CROSS APPLY VALUES)
walk_line AS (
    SELECT from_date, to_date, view_order, view_name, open_key AS group_id, 1 AS step_order, 'Opening' AS step, 'Balance' AS step_group,
           CAST(NULL AS VARCHAR) AS movement_reason, n AS people, n AS hc, f0 AS fte, bn0 AS bn, bc0 AS bc, ln0 AS ln, lc0 AS lc
    FROM view_row WHERE worker_class <> 'Hire'
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 2, 'Hires', 'Headcount', 'New Hire', n, n, f1, bn1, bc1, ln1, lc1
    FROM view_row WHERE worker_class = 'Hire'
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, open_key, 3, 'Exits', 'Headcount', exit_reason, n, -n, -f0, -bn0, -bc0, -ln0, -lc0
    FROM view_row WHERE worker_class = 'Exit'
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 4, 'Transfers In', 'Headcount', move_reason, n, n, f0, bn0, bc0, ln0, lc0
    FROM view_row WHERE worker_class = 'Continuing' AND open_key <> close_key
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, open_key, 5, 'Transfers Out', 'Headcount', move_reason, n, -n, -f0, -bn0, -bc0, -ln0, -lc0
    FROM view_row WHERE worker_class = 'Continuing' AND open_key <> close_key
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 6, 'Promotions', 'Career', NULL, promo_people, 0, 0, promo_bn, promo_bc, promo_ln, promo_lc
    FROM view_row WHERE promo_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 7, 'Demotions', 'Career', NULL, demo_people, 0, 0, demo_bn, demo_bc, demo_ln, demo_lc
    FROM view_row WHERE demo_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 8, 'Tenure Increases', 'Pay Rate', NULL, tenure_people, 0, 0, tenure_bn, tenure_bc, tenure_ln, tenure_lc
    FROM view_row WHERE tenure_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 9, 'Market Adjustments', 'Pay Rate', NULL, market_people, 0, 0, market_bn, market_bc, market_ln, market_lc
    FROM view_row WHERE market_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 10, 'Relocation Adjustments', 'Location', NULL, reloc_people, 0, 0, reloc_bn, reloc_bc, reloc_ln, reloc_lc
    FROM view_row WHERE reloc_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 11, 'International Transfer Adjustments', 'Location', NULL, intl_people, 0, 0, intl_bn, intl_bc, intl_ln, intl_lc
    FROM view_row WHERE intl_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 12, 'FTE Changes', 'Workforce Rate', NULL, fte_people, 0, f1 - f0, fte_bn, fte_bc, fte_ln, fte_lc
    FROM view_row WHERE fte_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 13, 'Fringe Rate Changes', 'Statutory', NULL, fringe_people, 0, 0, 0, 0, fringe_ln, fringe_lc
    FROM view_row WHERE fringe_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 14, 'FX Translation', 'Currency', NULL, fx_people, 0, 0, fx_bn, 0, fx_ln, 0
    FROM view_row WHERE fx_people > 0
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 15, 'Closing', 'Balance', NULL, n, n, f1, bn1, bc1, ln1, lc1
    FROM view_row WHERE worker_class <> 'Exit'
),

-- 4. aggregate to the published grain
walk AS (
    SELECT
        from_date, to_date, view_order, view_name, group_id, step_order, step, step_group, movement_reason,
        SUM(people) AS worker_count, SUM(hc) AS headcount, SUM(fte) AS fte,
        SUM(bn) AS base_usd_nominal, SUM(bc) AS base_usd_constant,
        SUM(ln) AS loaded_usd_nominal, SUM(lc) AS loaded_usd_constant
    FROM walk_line
    GROUP BY ALL
),

-- 5. group totals beside every line, for the average walk and the percent walk
with_totals AS (
    SELECT
        w.*,
        SUM(CASE WHEN step = 'Opening' THEN fte END)                 OVER grp AS open_fte,
        SUM(CASE WHEN step = 'Closing' THEN fte END)                 OVER grp AS close_fte,
        SUM(CASE WHEN step = 'Opening' THEN base_usd_nominal END)    OVER grp AS open_bn,
        SUM(CASE WHEN step = 'Opening' THEN base_usd_constant END)   OVER grp AS open_bc,
        SUM(CASE WHEN step = 'Opening' THEN loaded_usd_nominal END)  OVER grp AS open_ln,
        SUM(CASE WHEN step = 'Opening' THEN loaded_usd_constant END) OVER grp AS open_lc,
        SUM(CASE WHEN step = 'Closing' THEN base_usd_nominal END)    OVER grp AS close_bn,
        SUM(CASE WHEN step = 'Closing' THEN base_usd_constant END)   OVER grp AS close_bc,
        SUM(CASE WHEN step = 'Closing' THEN loaded_usd_nominal END)  OVER grp AS close_ln,
        SUM(CASE WHEN step = 'Closing' THEN loaded_usd_constant END) OVER grp AS close_lc
    FROM walk AS w
    WINDOW grp AS (PARTITION BY from_date, to_date, view_name, group_id)
)

SELECT
    t.from_date                                                         AS from_month_end,
    t.to_date                                                           AS to_month_end,
    cf.fiscal_period                                                    AS from_fiscal_period,
    ct.fiscal_period                                                    AS to_fiscal_period,
    cf.fiscal_quarter_label                                             AS from_fiscal_quarter,
    ct.fiscal_quarter_label                                             AS to_fiscal_quarter,
    date_diff('month', t.from_date, t.to_date)                          AS months_between,
    CASE
        WHEN date_diff('month', t.from_date, t.to_date) = 1  THEN 'Month over Month'
        WHEN date_diff('month', t.from_date, t.to_date) = 3  THEN 'Quarter over Quarter'
        WHEN date_diff('month', t.from_date, t.to_date) = 12 THEN 'Year over Year'
        WHEN MONTH(t.from_date) = 6 AND t.to_date < t.from_date + INTERVAL 12 MONTH THEN 'Fiscal Year to Date'
        ELSE 'Custom Range'
    END                                                                 AS pair_type,
    t.view_order,
    t.view_name,
    t.group_id,
    CASE t.view_name
        WHEN 'Office'  THEN lo.office_name
        WHEN 'Country' THEN co.country_name
        ELSE ou.org_unit_name
    END                                                                 AS group_name,
    CASE t.view_name
        WHEN 'Company'    THEN NULL
        WHEN 'Function'   THEN 'Arcadia Systems'
        WHEN 'Leader'     THEN ou.function_name
        WHEN 'Department' THEN ou.function_name
        WHEN 'Office'     THEN lo.country_name
        WHEN 'Country'    THEN co.region
    END                                                                 AS group_parent,
    lw.worker_name                                                      AS group_leader,
    t.step_order,
    t.step,
    t.step_group,
    t.movement_reason,
    t.worker_count,
    t.headcount,
    ROUND(t.fte, 2)                                                     AS fte,
    ROUND(t.base_usd_nominal, 2)                                        AS base_usd_nominal,
    ROUND(t.base_usd_constant, 2)                                       AS base_usd_constant,
    ROUND(t.loaded_usd_nominal, 2)                                      AS loaded_usd_nominal,
    ROUND(t.loaded_usd_constant, 2)                                     AS loaded_usd_constant,
    -- average walk (per FTE): Opening = opening average, Closing = closing average,
    -- every other step = (amount - FTE moved x opening average) / closing FTE
    ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_bn / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_bn / NULLIF(t.close_fte, 0)
        ELSE (t.base_usd_nominal - t.fte * COALESCE(t.open_bn / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4)                                                             AS avg_base_usd_nominal,
    ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_bc / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_bc / NULLIF(t.close_fte, 0)
        ELSE (t.base_usd_constant - t.fte * COALESCE(t.open_bc / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4)                                                             AS avg_base_usd_constant,
    ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_ln / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_ln / NULLIF(t.close_fte, 0)
        ELSE (t.loaded_usd_nominal - t.fte * COALESCE(t.open_ln / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4)                                                             AS avg_loaded_usd_nominal,
    ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_lc / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_lc / NULLIF(t.close_fte, 0)
        ELSE (t.loaded_usd_constant - t.fte * COALESCE(t.open_lc / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4)                                                             AS avg_loaded_usd_constant,
    -- percent walk: each line as a share of the group's opening total
    ROUND(t.base_usd_nominal    / NULLIF(t.open_bn, 0), 6)              AS pct_base_usd_nominal,
    ROUND(t.base_usd_constant   / NULLIF(t.open_bc, 0), 6)              AS pct_base_usd_constant,
    ROUND(t.loaded_usd_nominal  / NULLIF(t.open_ln, 0), 6)              AS pct_loaded_usd_nominal,
    ROUND(t.loaded_usd_constant / NULLIF(t.open_lc, 0), 6)              AS pct_loaded_usd_constant
FROM with_totals AS t
JOIN intermediate.int_month_end_calendar AS cf ON cf.month_end_date = t.from_date
JOIN intermediate.int_month_end_calendar AS ct ON ct.month_end_date = t.to_date
LEFT JOIN staging.stg_org_unit  AS ou ON ou.org_unit_id = t.group_id
LEFT JOIN staging.stg_location  AS lo ON t.view_name = 'Office'  AND lo.location_id  = t.group_id
LEFT JOIN staging.stg_country   AS co ON t.view_name = 'Country' AND co.country_code = t.group_id
LEFT JOIN (
    -- the leader of each org unit on each month-end (offices and countries have none)
    SELECT s.month_end_date, s.leads_org_unit_id, w.worker_name
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN staging.stg_worker AS w ON w.worker_id = s.worker_id
    WHERE s.leads_org_unit_id IS NOT NULL
) AS lw ON lw.month_end_date = t.to_date AND lw.leads_org_unit_id = t.group_id
ORDER BY t.from_date, t.to_date, t.view_order, t.group_id, t.step_order, t.movement_reason;
