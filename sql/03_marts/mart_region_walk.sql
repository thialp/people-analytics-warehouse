-- mart_region_walk
-- Grain: one row per date pair x view x group x region.
--
-- The DuckDB twin of tableau/custom_sql_region_walk.sql. A headcount walk by region for
-- every group of the compensation walk's six views, on the walk's date-pair grid, so a
-- "growth by region" chart follows the selected group (the walk itself has no region
-- split inside a group). Per region it reconciles exactly:
--
--   opening + hires - exits + transfers_in - transfers_out + moves_in - moves_out = closing
--
--   transfers  people who joined or left the GROUP (as the walk's Transfers In / Out)
--   moves      people who stayed in the group but changed region (an office in another
--              region): out of the old region, into the new one. Departures by region are
--              exits + transfers_out + moves_out.
--
-- Same population and rules as the walk: executive officers excluded; a person is placed
-- by the office they are in at each end of the pair; someone hired and gone between the
-- two dates is in neither snapshot. Summed over regions, each group's opening, hires,
-- exits, transfers and closing equal the walk's headcount lines (test 57).
CREATE OR REPLACE TABLE marts.mart_region_walk AS
WITH grid AS (
    -- === GRID === same rule as mart_compensation_walk (88 pairs)
    SELECT f.month_end_date AS from_date, t.month_end_date AS to_date
    FROM intermediate.int_month_end_calendar AS f
    JOIN intermediate.int_month_end_calendar AS t ON t.month_end_date > f.month_end_date
    WHERE t.month_end_date > (SELECT MIN(month_end_date) FROM intermediate.int_month_end_calendar) + INTERVAL 12 MONTH
      AND (   t.prior_month_end_date = f.month_end_date
           OR (    MONTH(f.month_end_date) IN (3, 6, 9, 12) AND MONTH(t.month_end_date) IN (3, 6, 9, 12)
               AND (   date_diff('month', f.month_end_date, t.month_end_date) IN (3, 12)
                    OR (MONTH(f.month_end_date) = 6 AND date_diff('month', f.month_end_date, t.month_end_date) < 12))))
),

-- 1. everyone present at the From or the To month-end, pre-aggregated
pair_group AS (
    SELECT
        g.from_date, g.to_date,
        CASE WHEN o.worker_id IS NULL THEN 'Hire' WHEN c.worker_id IS NULL THEN 'Exit' ELSE 'Continuing' END AS worker_class,
        o.department_id AS o_dept, o.location_id AS o_loc,
        c.department_id AS c_dept, c.location_id AS c_loc,
        COUNT(*) AS n
    FROM grid AS g
    JOIN staging.stg_worker AS w
      ON w.original_hire_date <= g.to_date
     AND (w.termination_date IS NULL OR w.termination_date >= g.from_date)
     AND NOT w.is_executive_officer
    LEFT JOIN intermediate.int_worker_month_end_snapshot AS o ON o.month_end_date = g.from_date AND o.worker_id = w.worker_id
    LEFT JOIN intermediate.int_worker_month_end_snapshot AS c ON c.month_end_date = g.to_date   AND c.worker_id = w.worker_id
    WHERE o.worker_id IS NOT NULL OR c.worker_id IS NOT NULL
    GROUP BY ALL
),

dept_map AS (
    SELECT d.department_id,
           CASE WHEN p.org_unit_type = 'Sub-function' THEN p.parent_org_unit_id ELSE p.org_unit_id END AS function_id,
           d.parent_org_unit_id AS leader_org_id
    FROM staging.stg_department AS d
    JOIN staging.stg_org_unit AS p ON p.org_unit_id = d.parent_org_unit_id
),

-- 2. the six views, with the region at each end
view_row AS (
    SELECT
        pg.*, v.view_order, v.view_name, ol.region AS o_region, cl.region AS c_region,
        CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN od.function_id WHEN 3 THEN od.leader_org_id
                          WHEN 4 THEN pg.o_dept WHEN 5 THEN pg.o_loc   WHEN 6 THEN ol.country_code END AS open_key,
        CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN cd.function_id WHEN 3 THEN cd.leader_org_id
                          WHEN 4 THEN pg.c_dept WHEN 5 THEN pg.c_loc   WHEN 6 THEN cl.country_code END AS close_key
    FROM pair_group AS pg
    LEFT JOIN dept_map AS od ON od.department_id = pg.o_dept
    LEFT JOIN dept_map AS cd ON cd.department_id = pg.c_dept
    LEFT JOIN staging.stg_location AS ol ON ol.location_id = pg.o_loc
    LEFT JOIN staging.stg_location AS cl ON cl.location_id = pg.c_loc
    CROSS JOIN (VALUES (1, 'Company'), (2, 'Function'), (3, 'Sub-function'),
                       (4, 'Department'), (5, 'Office'), (6, 'Country')) AS v(view_order, view_name)
),

-- 3. two lines per row: the From side (group and region at the From date) and the To side
line AS (
    SELECT from_date, to_date, view_order, view_name, open_key AS group_id, o_region AS region,
           CASE WHEN worker_class <> 'Hire' THEN n ELSE 0 END                                         AS opening,
           0                                                                                           AS hires,
           CASE WHEN worker_class = 'Exit' THEN n ELSE 0 END                                          AS exits,
           0                                                                                           AS transfers_in,
           CASE WHEN worker_class = 'Continuing' AND open_key <> close_key THEN n ELSE 0 END          AS transfers_out,
           0                                                                                           AS moves_in,
           CASE WHEN worker_class = 'Continuing' AND open_key = close_key AND o_region <> c_region THEN n ELSE 0 END AS moves_out,
           0                                                                                           AS closing
    FROM view_row WHERE worker_class <> 'Hire'
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, c_region,
           0,
           CASE WHEN worker_class = 'Hire' THEN n ELSE 0 END,
           0,
           CASE WHEN worker_class = 'Continuing' AND open_key <> close_key THEN n ELSE 0 END,
           0,
           CASE WHEN worker_class = 'Continuing' AND open_key = close_key AND o_region <> c_region THEN n ELSE 0 END,
           0,
           CASE WHEN worker_class <> 'Exit' THEN n ELSE 0 END
    FROM view_row WHERE worker_class <> 'Exit'
),

walk AS (
    SELECT from_date, to_date, view_order, view_name, group_id, region,
           SUM(opening) AS opening, SUM(hires) AS hires, SUM(exits) AS exits,
           SUM(transfers_in) AS transfers_in, SUM(transfers_out) AS transfers_out,
           SUM(moves_in) AS moves_in, SUM(moves_out) AS moves_out, SUM(closing) AS closing
    FROM line
    GROUP BY ALL
    HAVING SUM(opening) + SUM(hires) + SUM(exits) + SUM(transfers_in) + SUM(transfers_out)
         + SUM(moves_in) + SUM(moves_out) + SUM(closing) > 0
)

SELECT
    t.from_date                                                         AS from_month_end,
    t.to_date                                                           AS to_month_end,
    (SELECT CAST(MIN(month_end_date) + INTERVAL 12 MONTH AS DATE) FROM intermediate.int_month_end_calendar) AS report_start_date,
    (SELECT MAX(month_end_date) FROM intermediate.int_month_end_calendar)                                  AS report_as_of_date,
    cf.fiscal_period                                                    AS from_fiscal_period,
    ct.fiscal_period                                                    AS to_fiscal_period,
    date_diff('month', t.from_date, t.to_date)                          AS months_between,
    t.view_order,
    t.view_name,
    t.group_id,
    CASE t.view_name
        WHEN 'Office'  THEN lo.office_name
        WHEN 'Country' THEN co.country_name
        ELSE ou.org_unit_name
    END                                                                 AS group_name,
    t.region,
    CAST(t.opening       AS INTEGER)                                    AS opening_headcount,
    CAST(t.hires         AS INTEGER)                                    AS hires,
    CAST(t.exits         AS INTEGER)                                    AS exits,
    CAST(t.transfers_in  AS INTEGER)                                    AS transfers_in,
    CAST(t.transfers_out AS INTEGER)                                    AS transfers_out,
    CAST(t.moves_in      AS INTEGER)                                    AS region_moves_in,
    CAST(t.moves_out     AS INTEGER)                                    AS region_moves_out,
    CAST(t.closing       AS INTEGER)                                    AS closing_headcount
FROM walk AS t
JOIN intermediate.int_month_end_calendar AS cf ON cf.month_end_date = t.from_date
JOIN intermediate.int_month_end_calendar AS ct ON ct.month_end_date = t.to_date
LEFT JOIN staging.stg_org_unit AS ou ON ou.org_unit_id = t.group_id
LEFT JOIN staging.stg_location AS lo ON t.view_name = 'Office'  AND lo.location_id  = t.group_id
LEFT JOIN staging.stg_country  AS co ON t.view_name = 'Country' AND co.country_code = t.group_id
ORDER BY t.from_date, t.to_date, t.view_order, t.group_id, t.region;
