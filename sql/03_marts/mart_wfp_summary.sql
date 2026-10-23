-- mart_wfp_summary: one row per fiscal year x period x plan version x view x group.
-- Feeds Dashboard #3 (Workforce Planning): the KPI band, the page and chart headlines, and the
-- rail's Period, Version and Group lists. Its job is that no choice on the page can lead to an
-- empty view: every combination has a row, and has_plan says whether it has a plan to compare.
--
-- Periods (pair_code) inside one fiscal year, compared at quarter-ends, because the plan is
-- quarterly: FY (Q1-Q4), H1 (Q1-Q2), H2 (Q3-Q4), Q1, Q2, Q3, Q4. from_date is the quarter-end
-- before the first quarter (the period opens there), to_date the last quarter's end.
--
-- Versions: a reforecast covers only the quarters still ahead (RF1 Q2-Q4, RF2 Q3-Q4, RF3 Q4).
-- eff_first_quarter .. eff_last_quarter is the part of the period the version plans, and every
-- flow (plan and actual alike) is counted over those quarters only, so plan and actual always
-- cover the same dates. A version that plans none of the period has is_covered = FALSE.
--
-- Levels (headcount, cost, contingent workers and spend) are read at to_date, never summed.
-- Seat-fill measures come from mart_position_fill over the same effective quarters.
--
-- Population: the 9 executive officers (department D-901) are excluded, as on Dashboards #1 and
-- #2, so FY26 year-end employees read 30,005 here and there.
--
-- PIDs (release 3.1): every PID in Keystone on to_date, employee and contingent, filled or
-- vacant, and a vacant PID either previously held (someone left it) or new (created for a
-- request, never filled yet). Version-independent: the same in every version row. Filled
-- employee PIDs equal actual_ending_headcount and filled contingent PIDs the contingent
-- headcount (tests 45 and 81). Level and office changes count employee backfills in the
-- effective quarters; contingent fills count contingent assignments starting in them.
CREATE OR REPLACE TABLE marts.mart_wfp_summary AS
WITH fy AS (
    SELECT DISTINCT fiscal_year FROM marts.mart_plan_vs_actual
),
pair_def AS (
    SELECT * FROM (VALUES ('FY', 1, 1, 4), ('H1', 2, 1, 2), ('H2', 3, 3, 4),
                          ('Q1', 4, 1, 1), ('Q2', 5, 2, 2), ('Q3', 6, 3, 3), ('Q4', 7, 4, 4))
                  AS t(pair_code, pair_order, first_quarter, last_quarter)
),
version_def AS (
    -- a version's first quarter equals its order: Budget plans Q1 on, RF1 Q2 on, ...
    SELECT * FROM (VALUES ('Budget', 1), ('RF1', 2), ('RF2', 3), ('RF3', 4)) AS t(version_type, version_order)
),
grid_period AS (
    SELECT f.fiscal_year,
           'FY' || RIGHT(CAST(f.fiscal_year AS VARCHAR), 2)                                     AS fiscal_year_label,
           p.pair_code, p.pair_order, p.first_quarter, p.last_quarter,
           CAST(last_day(make_date(f.fiscal_year - 1, 6, 1) + INTERVAL (3 * (p.first_quarter - 1)) MONTH) AS DATE) AS from_date,
           CAST(last_day(make_date(f.fiscal_year - 1, 6, 1) + INTERVAL (3 * p.last_quarter) MONTH) AS DATE)         AS to_date,
           v.version_type, v.version_order,
           GREATEST(p.first_quarter, v.version_order)                                           AS eff_first_quarter,
           p.last_quarter                                                                       AS eff_last_quarter
    FROM fy AS f CROSS JOIN pair_def AS p CROSS JOIN version_def AS v
),
plan_rows AS (
    SELECT p.*, CAST(RIGHT(p.fiscal_quarter_label, 1) AS INTEGER) AS q
    FROM marts.mart_plan_vs_actual AS p
    WHERE p.department_id <> 'D-901'
),
plan_groups AS (
    SELECT p.*, g.view_name, g.view_order, g.group_name
    FROM plan_rows AS p
    CROSS JOIN LATERAL (VALUES ('Company', 1, 'Arcadia Systems'), ('Function', 2, p.function_name),
                               ('Sub-function', 3, p.sub_function), ('Department', 4, p.department_name),
                               ('Country', 5, p.country_name)) AS g(view_name, view_order, group_name)
),
fill_groups AS (
    SELECT f.*, CAST(RIGHT(f.fiscal_quarter_label, 1) AS INTEGER) AS q, g.view_name, g.group_name
    FROM marts.mart_position_fill AS f
    CROSS JOIN LATERAL (VALUES ('Company', 'Arcadia Systems'), ('Function', f.function_name),
                               ('Sub-function', f.sub_function), ('Department', f.department_name),
                               ('Country', f.country_name)) AS g(view_name, group_name)
    WHERE f.department_id <> 'D-901'
),
group_list AS (   -- every group that ever had a plan row, in every period: no choice can drop a row.
                  -- is_view_default marks each view's first group alphabetically, which is where a
                  -- View pick lands, as on Dashboards #1 and #2 (it has a plan in every period and version)
    SELECT view_name, view_order, group_name,
           ROW_NUMBER() OVER (PARTITION BY view_name ORDER BY group_name) = 1 AS is_view_default   -- first alphabetically (release 3.1)
    FROM (
        SELECT view_name, view_order, group_name,
               SUM(CASE WHEN version_type = 'Budget'
                         AND quarter_end_date = (SELECT MAX(quarter_end_date) FROM plan_rows)
                        THEN actual_ending_headcount ELSE 0 END) AS year_end_headcount
        FROM plan_groups
        GROUP BY view_name, view_order, group_name
    ) AS s
),
plan_agg AS (
    SELECT g.fiscal_year, g.pair_code, g.version_type, p.view_name, p.group_name,
           COUNT(*)                                                                  AS plan_rows,
           SUM(p.planned_net_new)                                                    AS planned_net_new,
           SUM(p.actual_net_new)                                                     AS actual_net_new,
           SUM(p.actual_net_new_reuse_candidates)                                    AS actual_net_new_reuse_candidates,
           SUM(p.planned_backfills)                                                  AS planned_backfills,
           SUM(p.actual_backfills)                                                   AS actual_backfills,
           SUM(p.actual_external_hires)                                              AS actual_external_hires,
           SUM(p.actual_internal_moves)                                              AS actual_internal_moves,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.planned_ending_headcount END)    AS planned_ending_headcount,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.actual_ending_headcount END)     AS actual_ending_headcount,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.planned_cost_usd END)            AS planned_cost_usd,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.actual_cost_usd_plan_fx END)     AS actual_cost_usd_plan_fx,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.planned_cw_headcount END)        AS planned_cw_headcount,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.actual_cw_headcount END)         AS actual_cw_headcount,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.planned_cw_spend_usd END)        AS planned_cw_spend_usd,
           SUM(CASE WHEN p.quarter_end_date = g.to_date THEN p.actual_cw_spend_usd_plan_fx END) AS actual_cw_spend_usd_plan_fx
    FROM grid_period AS g
    JOIN plan_groups AS p
      ON p.fiscal_year = g.fiscal_year AND p.version_type = g.version_type
     AND p.q BETWEEN g.eff_first_quarter AND g.eff_last_quarter
    GROUP BY ALL
),
fill_agg AS (
    SELECT g.fiscal_year, g.pair_code, g.version_type, f.view_name, f.group_name,
           COUNT(*)                                                                  AS fills,
           COUNT(*) FILTER (WHERE f.seat_type = 'Backfill')                          AS backfill_fills,
           COUNT(*) FILTER (WHERE f.seat_type = 'Net-new')                           AS net_new_fills,
           COUNT(*) FILTER (WHERE f.fill_type = 'Internal Move')                     AS internal_fills,
           COUNT(*) FILTER (WHERE f.reuse_candidate)                                 AS reuse_candidate_fills,
           SUM(CASE WHEN f.reuse_candidate THEN f.new_pay_usd_constant END)          AS reuse_new_pay_usd_constant,
           SUM(CASE WHEN f.seat_type = 'Backfill' THEN f.pay_change_usd_constant END) AS backfill_pay_change_usd_constant,
           median(f.time_to_fill_days) FILTER (WHERE f.seat_type = 'Backfill' AND f.seat_decision <> 'Immediate refill') AS median_time_to_fill_days,
           median(f.vacancy_days)      FILTER (WHERE f.seat_type = 'Backfill' AND f.seat_decision <> 'Immediate refill') AS median_vacancy_days,
           COUNT(*) FILTER (WHERE f.seat_type = 'Backfill' AND f.level_change = 'Down')                        AS level_down,
           COUNT(*) FILTER (WHERE f.seat_type = 'Backfill' AND f.level_change = 'Up')                          AS level_up,
           COUNT(*) FILTER (WHERE f.seat_type = 'Backfill' AND f.level_change <> 'Same'
                              AND f.location_change <> 'Same office')                                         AS level_and_office,
           COUNT(*) FILTER (WHERE f.seat_type = 'Backfill' AND f.location_change <> 'Same office')            AS moved_office
    FROM grid_period AS g
    JOIN fill_groups AS f
      ON f.fiscal_year = g.fiscal_year AND f.q BETWEEN g.eff_first_quarter AND g.eff_last_quarter
    GROUP BY ALL
),
org AS (
    SELECT d.department_id, d.function_name, d.sub_function, d.department_name FROM staging.stg_department AS d
),
pid_rows AS (     -- the PID ledger on every month-end (mart_pid_month_end)
    SELECT month_end_date, worker_type, pid_kind, is_stale, department_id, country_name, pids
    FROM marts.mart_pid_month_end
),
pid_groups AS (
    SELECT r.*, g.view_name, g.group_name
    FROM pid_rows AS r
    JOIN org AS o ON o.department_id = r.department_id
    CROSS JOIN LATERAL (VALUES ('Company', 'Arcadia Systems'), ('Function', o.function_name),
                               ('Sub-function', o.sub_function), ('Department', o.department_name),
                               ('Country', r.country_name)) AS g(view_name, group_name)
    WHERE r.department_id <> 'D-901'
),
pid_agg AS (
    SELECT month_end_date, view_name, group_name,
           SUM(pids) FILTER (WHERE pid_kind = 'Filled' AND worker_type = 'Employee')                 AS pids_filled_employee,
           SUM(pids) FILTER (WHERE pid_kind = 'Filled' AND worker_type = 'Contingent')               AS pids_filled_contingent,
           SUM(pids) FILTER (WHERE pid_kind = 'Vacant previously held')                              AS vacant_previously_held,
           SUM(pids) FILTER (WHERE pid_kind = 'Vacant previously held' AND worker_type = 'Contingent') AS vacant_previously_held_contingent,
           SUM(pids) FILTER (WHERE pid_kind = 'Vacant previously held' AND is_stale)                 AS vacant_previously_held_stale,
           SUM(pids) FILTER (WHERE pid_kind = 'Vacant new')                                          AS vacant_new,
           SUM(pids) FILTER (WHERE pid_kind = 'Vacant new' AND worker_type = 'Contingent')           AS vacant_new_contingent,
           SUM(pids) FILTER (WHERE pid_kind = 'Vacant new' AND is_stale)                             AS vacant_new_stale
    FROM pid_groups
    GROUP BY ALL
),
cw_fill_groups AS (   -- contingent assignments that start in the quarter (mart_cw_pid_fill)
    SELECT c.fiscal_year, c.fiscal_quarter AS q, c.is_backfill, g.view_name, g.group_name
    FROM marts.mart_cw_pid_fill AS c
    JOIN org AS o ON o.department_id = c.department_id
    CROSS JOIN LATERAL (VALUES ('Company', 'Arcadia Systems'), ('Function', o.function_name),
                               ('Sub-function', o.sub_function), ('Department', o.department_name),
                               ('Country', c.country_name)) AS g(view_name, group_name)
    WHERE c.department_id <> 'D-901'
),
cw_fill_agg AS (
    SELECT g.fiscal_year, g.pair_code, g.version_type, c.view_name, c.group_name,
           COUNT(*)                                  AS contingent_fills,
           COUNT(*) FILTER (WHERE c.is_backfill)     AS contingent_backfill_fills
    FROM grid_period AS g
    JOIN cw_fill_groups AS c
      ON c.fiscal_year = g.fiscal_year AND c.q BETWEEN g.eff_first_quarter AND g.eff_last_quarter
    GROUP BY ALL
)
SELECT
    g.fiscal_year,
    g.fiscal_year_label,
    g.pair_code,
    g.pair_order,
    g.fiscal_year_label || CASE WHEN g.pair_code = 'FY' THEN '' ELSE ' ' || g.pair_code END
        || ' · ' || strftime(g.from_date, '%b %y') || ' → ' || strftime(g.to_date, '%b %y')        AS pair_name,
    g.from_date,
    g.to_date,
    g.last_quarter - g.first_quarter + 1                                            AS quarters_in_pair,
    g.version_type,
    g.version_order,
    g.fiscal_year_label || ' ' || g.version_type                                     AS plan_version,
    g.eff_first_quarter,
    g.eff_last_quarter,
    CASE WHEN g.eff_first_quarter <= g.eff_last_quarter
         THEN CAST(last_day(make_date(g.fiscal_year - 1, 6, 1) + INTERVAL (3 * (g.eff_first_quarter - 1)) MONTH) AS DATE) END
                                                                                     AS eff_from_date,
    GREATEST(g.eff_last_quarter - g.eff_first_quarter + 1, 0)                        AS quarters_covered,
    g.eff_first_quarter <= g.eff_last_quarter                                        AS is_covered,
    CASE WHEN g.eff_first_quarter > g.eff_last_quarter THEN NULL
         WHEN g.eff_first_quarter = g.eff_last_quarter THEN 'Q' || g.eff_first_quarter
         ELSE 'Q' || g.eff_first_quarter || '–Q' || g.eff_last_quarter END          AS covered_label,
    l.view_name,
    l.view_order,
    l.group_name,
    l.is_view_default,
    COALESCE(p.plan_rows, 0)                                                         AS plan_rows,
    COALESCE(p.plan_rows, 0) > 0                                                     AS has_plan,
    COALESCE(p.planned_net_new, 0)                                                   AS planned_net_new,
    COALESCE(p.actual_net_new, 0)                                                    AS actual_net_new,
    COALESCE(p.actual_net_new_reuse_candidates, 0)                                   AS actual_net_new_reuse_candidates,
    COALESCE(p.planned_backfills, 0)                                                 AS planned_backfills,
    COALESCE(p.actual_backfills, 0)                                                  AS actual_backfills,
    COALESCE(p.actual_external_hires, 0)                                             AS actual_external_hires,
    COALESCE(p.actual_internal_moves, 0)                                             AS actual_internal_moves,
    COALESCE(p.planned_ending_headcount, 0)                                          AS planned_ending_headcount,
    COALESCE(p.actual_ending_headcount, 0)                                           AS actual_ending_headcount,
    ROUND(COALESCE(p.planned_cost_usd, 0), 2)                                        AS planned_cost_usd,
    ROUND(COALESCE(p.actual_cost_usd_plan_fx, 0), 2)                                 AS actual_cost_usd_plan_fx,
    COALESCE(p.planned_cw_headcount, 0)                                              AS planned_cw_headcount,
    COALESCE(p.actual_cw_headcount, 0)                                               AS actual_cw_headcount,
    ROUND(COALESCE(p.planned_cw_spend_usd, 0), 2)                                    AS planned_cw_spend_usd,
    ROUND(COALESCE(p.actual_cw_spend_usd_plan_fx, 0), 2)                             AS actual_cw_spend_usd_plan_fx,
    COALESCE(f.fills, 0)                                                             AS fills,
    COALESCE(f.backfill_fills, 0)                                                    AS backfill_fills,
    COALESCE(f.net_new_fills, 0)                                                     AS net_new_fills,
    COALESCE(f.internal_fills, 0)                                                    AS internal_fills,
    COALESCE(f.reuse_candidate_fills, 0)                                             AS reuse_candidate_fills,
    ROUND(COALESCE(f.reuse_new_pay_usd_constant, 0), 2)                              AS reuse_new_pay_usd_constant,
    ROUND(COALESCE(f.backfill_pay_change_usd_constant, 0), 2)                        AS backfill_pay_change_usd_constant,
    f.median_time_to_fill_days,
    f.median_vacancy_days,
    -- release 3.1: periods named by months, and the PID ledger
    CASE WHEN g.pair_code = 'FY' THEN 'Fiscal year' WHEN g.pair_code IN ('H1', 'H2') THEN 'Half year' ELSE 'Quarter' END AS span_name,
    CASE WHEN g.pair_code = 'FY' THEN 1 WHEN g.pair_code IN ('H1', 'H2') THEN 2 ELSE 3 END                      AS span_order,
    g.fiscal_year_label || CASE WHEN g.pair_code = 'FY' THEN '' ELSE ' ' || g.pair_code END                      AS period_short,
    CASE WHEN g.pair_code = 'FY'
         THEN strftime(g.from_date + INTERVAL 1 DAY, '%b %y') || ' – ' || strftime(g.to_date, '%b %y')
         ELSE strftime(g.from_date + INTERVAL 1 DAY, '%b') || ' – ' || strftime(g.to_date, '%b %y') END           AS period_months,
    COALESCE(x.pids_filled_employee, 0) + COALESCE(x.pids_filled_contingent, 0)
        + COALESCE(x.vacant_previously_held, 0) + COALESCE(x.vacant_new, 0)                                     AS pids_total,
    COALESCE(x.pids_filled_employee, 0)                                              AS pids_filled_employee,
    COALESCE(x.pids_filled_contingent, 0)                                            AS pids_filled_contingent,
    COALESCE(x.vacant_previously_held, 0)                                            AS vacant_previously_held,
    COALESCE(x.vacant_previously_held_contingent, 0)                                 AS vacant_previously_held_contingent,
    COALESCE(x.vacant_previously_held_stale, 0)                                      AS vacant_previously_held_stale,
    COALESCE(x.vacant_new, 0)                                                        AS vacant_new,
    COALESCE(x.vacant_new_contingent, 0)                                             AS vacant_new_contingent,
    COALESCE(x.vacant_new_stale, 0)                                                  AS vacant_new_stale,
    COALESCE(f.level_down, 0)                                                        AS level_down,
    COALESCE(f.level_up, 0)                                                          AS level_up,
    COALESCE(f.level_and_office, 0)                                                  AS level_and_office,
    COALESCE(f.moved_office, 0)                                                      AS moved_office,
    COALESCE(c.contingent_fills, 0)                                                  AS contingent_fills,
    COALESCE(c.contingent_backfill_fills, 0)                                         AS contingent_backfill_fills
FROM grid_period AS g
CROSS JOIN group_list AS l
LEFT JOIN plan_agg AS p
  ON p.fiscal_year = g.fiscal_year AND p.pair_code = g.pair_code AND p.version_type = g.version_type
 AND p.view_name = l.view_name AND p.group_name = l.group_name
LEFT JOIN fill_agg AS f
  ON f.fiscal_year = g.fiscal_year AND f.pair_code = g.pair_code AND f.version_type = g.version_type
 AND f.view_name = l.view_name AND f.group_name = l.group_name
LEFT JOIN pid_agg AS x
  ON x.month_end_date = g.to_date AND x.view_name = l.view_name AND x.group_name = l.group_name
LEFT JOIN cw_fill_agg AS c
  ON c.fiscal_year = g.fiscal_year AND c.pair_code = g.pair_code AND c.version_type = g.version_type
 AND c.view_name = l.view_name AND c.group_name = l.group_name
ORDER BY g.fiscal_year, g.pair_order, g.version_order, l.view_order, l.group_name;
