-- mart_office_moves
-- Grain: one row per date pair x view x group x group side x origin office x destination office
--        x move reason.
--
-- The DuckDB twin of tableau/custom_sql_office_moves.sql (same rules, same columns, same
-- numbers; the Tableau file is the documented one). It answers, for any two month-ends on the
-- compensation walk's grid and any group in the walk's six views, which people changed office
-- between the two dates and where they went, so a flow map follows the same filters as the walk.
--
-- A mover is a worker present at BOTH month-ends whose office differs. The comparison is
-- From vs To only, exactly as in the walk: a person who moved A -> B -> C counts once as A -> C,
-- and A -> B -> A is not a move. Executive officers are excluded, as in the walk.
--
-- Which group does a move belong to? The group the person is in at each end of the pair, using
-- the walk's rule for that view:
--   group_side = 'Both'  the group is the same at both ends (a move inside the group);
--   group_side = 'From'  the person was in this group at the From date and left it;
--   group_side = 'To'    the person joined this group by the To date.
-- In the Office view a move always has two sides (the office it left, the office it joined), so
-- 'To' rows equal the walk's Transfers In and 'From' rows equal Transfers Out. In the Country
-- view the same holds for moves across a border; moves inside one country are 'Both'.
--
-- Field reference: docs/projects/compensation-walk/office_moves.md
CREATE OR REPLACE TABLE marts.mart_office_moves AS
WITH grid AS (
    -- === GRID === same rule as mart_compensation_walk: every quarter-end to every later
    -- quarter-end (136 pairs) plus every month-end to the next one (48)
    SELECT f.month_end_date AS from_date, t.month_end_date AS to_date
    FROM intermediate.int_month_end_calendar AS f
    JOIN intermediate.int_month_end_calendar AS t ON t.month_end_date > f.month_end_date
    WHERE (MONTH(f.month_end_date) IN (3, 6, 9, 12) AND MONTH(t.month_end_date) IN (3, 6, 9, 12))
       OR t.prior_month_end_date = f.month_end_date
),

-- 1. one row per mover per date pair
mover AS (
    SELECT
        g.from_date, g.to_date,
        o.department_id AS o_dept, o.location_id AS o_loc,
        c.department_id AS c_dept, c.location_id AS c_loc,
        COALESCE(lc.location_move_reason, 'Other') AS move_reason
    FROM grid AS g
    JOIN intermediate.int_worker_month_end_snapshot AS o ON o.month_end_date = g.from_date AND NOT o.is_executive_officer
    JOIN intermediate.int_worker_month_end_snapshot AS c ON c.month_end_date = g.to_date AND c.worker_id = o.worker_id
    JOIN intermediate.int_worker_pay_ledger         AS lc ON lc.month_end_date = g.to_date AND lc.worker_id = o.worker_id
    WHERE o.location_id <> c.location_id
),

-- 2. aggregate early: movers with the same dates, departments, offices and reason become one row
mover_group AS (
    SELECT from_date, to_date, o_dept, o_loc, c_dept, c_loc, move_reason, COUNT(*) AS n
    FROM mover
    GROUP BY ALL
),

-- the function and leader organization each department rolls up to (same as the walk)
dept_map AS (
    SELECT d.department_id,
           CASE WHEN p.org_unit_type = 'Sub-function' THEN p.parent_org_unit_id ELSE p.org_unit_id END AS function_id,
           d.parent_org_unit_id AS leader_org_id
    FROM staging.stg_department AS d
    JOIN staging.stg_org_unit AS p ON p.org_unit_id = d.parent_org_unit_id
),

-- 3. expand late: the six views, then the sides that apply
view_row AS (
    SELECT
        mg.*, v.view_order, v.view_name,
        CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN od.function_id WHEN 3 THEN od.leader_org_id
                          WHEN 4 THEN mg.o_dept WHEN 5 THEN mg.o_loc   WHEN 6 THEN ol.country_code END AS open_key,
        CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN cd.function_id WHEN 3 THEN cd.leader_org_id
                          WHEN 4 THEN mg.c_dept WHEN 5 THEN mg.c_loc   WHEN 6 THEN cl.country_code END AS close_key
    FROM mover_group AS mg
    LEFT JOIN dept_map AS od ON od.department_id = mg.o_dept
    LEFT JOIN dept_map AS cd ON cd.department_id = mg.c_dept
    LEFT JOIN staging.stg_location AS ol ON ol.location_id = mg.o_loc
    LEFT JOIN staging.stg_location AS cl ON cl.location_id = mg.c_loc
    CROSS JOIN (VALUES (1, 'Company'), (2, 'Function'), (3, 'Leader'),
                       (4, 'Department'), (5, 'Office'), (6, 'Country')) AS v(view_order, view_name)
),

move_line AS (
    SELECT from_date, to_date, view_order, view_name, open_key AS group_id, 'Both' AS group_side,
           o_loc, c_loc, move_reason, n
    FROM view_row WHERE open_key = close_key
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, open_key, 'From', o_loc, c_loc, move_reason, n
    FROM view_row WHERE open_key <> close_key
    UNION ALL
    SELECT from_date, to_date, view_order, view_name, close_key, 'To', o_loc, c_loc, move_reason, n
    FROM view_row WHERE open_key <> close_key
),

-- 4. aggregate to the published grain
move_total AS (
    SELECT from_date, to_date, view_order, view_name, group_id, group_side, o_loc, c_loc, move_reason,
           SUM(n) AS workers
    FROM move_line
    GROUP BY ALL
)

SELECT
    t.from_date                                                         AS from_month_end,
    t.to_date                                                           AS to_month_end,
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
    CASE t.view_name
        WHEN 'Company'    THEN NULL
        WHEN 'Function'   THEN 'Arcadia Systems'
        WHEN 'Leader'     THEN ou.function_name
        WHEN 'Department' THEN ou.function_name
        WHEN 'Office'     THEN lo.country_name
        WHEN 'Country'    THEN co.region
    END                                                                 AS group_parent,
    t.group_side,
    t.o_loc                                                             AS from_location_id,
    fl.office_name                                                      AS from_office,
    fl.city                                                             AS from_city,
    fl.country_name                                                     AS from_country,
    fl.region                                                           AS from_region,
    fl.latitude                                                         AS from_latitude,
    fl.longitude                                                        AS from_longitude,
    t.c_loc                                                             AS to_location_id,
    tl.office_name                                                      AS to_office,
    tl.city                                                             AS to_city,
    tl.country_name                                                     AS to_country,
    tl.region                                                           AS to_region,
    tl.latitude                                                         AS to_latitude,
    tl.longitude                                                        AS to_longitude,
    CASE WHEN fl.country_code = tl.country_code THEN 'Domestic' ELSE 'International' END AS flow_scope,
    CASE WHEN fl.country_code = tl.country_code THEN 'Within one country' ELSE 'Across a border' END AS flow_scope_label,
    CASE WHEN fl.region = tl.region THEN 'Same region' ELSE 'Across regions' END           AS region_scope,
    t.move_reason,
    CAST(t.workers AS INTEGER)                                          AS workers
FROM move_total AS t
JOIN intermediate.int_month_end_calendar AS cf ON cf.month_end_date = t.from_date
JOIN intermediate.int_month_end_calendar AS ct ON ct.month_end_date = t.to_date
JOIN marts.mart_dim_location AS fl ON fl.location_id = t.o_loc
JOIN marts.mart_dim_location AS tl ON tl.location_id = t.c_loc
LEFT JOIN staging.stg_org_unit AS ou ON ou.org_unit_id = t.group_id
LEFT JOIN staging.stg_location AS lo ON t.view_name = 'Office'  AND lo.location_id  = t.group_id
LEFT JOIN staging.stg_country  AS co ON t.view_name = 'Country' AND co.country_code = t.group_id
ORDER BY t.from_date, t.to_date, t.view_order, t.group_id, t.group_side, t.o_loc, t.c_loc, t.move_reason;
