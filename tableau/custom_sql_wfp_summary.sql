/*
  custom_sql_wfp_summary.sql
  Tableau Custom SQL for Dashboard #3, Workforce Planning (SQL Server, database ArcadiaHR).
  Summary: one row per fiscal year x period x plan version x view x group, 10,080 rows.

  ONE data source for the KPI band (five cards drawn as map layers on one sheet, so every card
  must come from one source), the page and chart headlines, and the rail's Period, Version and
  Group lists. It reads the two reporting views the other Dashboard #3 sources read
  (rpt.vw_plan_vs_actual, rpt.vw_position_fill), so its numbers tie to them.

  NO EMPTY VIEW. Every fiscal year x period x version x view x group has a row (72 groups:
  Company, 8 functions, 10 sub-functions, 31 departments, 22 countries), and has_plan says
  whether that combination has a plan to compare with. The rail greys out, and makes
  unclickable, every Period, Version or Group whose row has has_plan = 0 for the other two
  current choices, so the page can never land on a combination without data. A View pick
  lands on the view's largest group (is_view_default = 1), which has a plan everywhere.

  PERIODS (pair_code) sit inside one fiscal year and compare quarter-ends, because the plan is
  quarterly: FY (Q1-Q4), H1, H2, Q1, Q2, Q3, Q4. from_date is the quarter-end before the first
  quarter, to_date the last quarter's end. pair_name reads like Dashboard #2: "FY26 · Jun 25 → Jun 26".

  VERSIONS. A reforecast plans only the quarters still ahead (RF1 Q2-Q4, RF2 Q3-Q4, RF3 Q4), so
  each row counts plan AND actual over eff_first_quarter..eff_last_quarter only (covered_label,
  eff_from_date); a version that plans none of the period has is_covered = 0 and zeros.

  MEASURES. Flows (net-new, backfills, fills, reuse candidates) are summed over the effective
  quarters; levels (headcount, cost, contingent workers and spend) are read at to_date and
  never summed. Medians are for backfills, excluding immediate refills. The actual_* plan
  columns equal the seat fills for every row (test 80).

  WHO IS COUNTED. Employees, without the 9 executive officers (department D-901), as on
  Dashboards #1 and #2: FY26 year-end 30,005. Contingent columns are Bridgeway's count.

  Checked row for row against the DuckDB mart mart_wfp_summary by sqlserver/check_tsql_in_duckdb.py.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    g.fiscal_year,
    g.fiscal_year_label,
    g.pair_code,
    g.pair_order,
    CONCAT(g.fiscal_year_label,
           CASE WHEN g.pair_code = 'FY' THEN N'' ELSE CONCAT(N' ', g.pair_code) END,
           N' · ', LEFT(DATENAME(MONTH, g.from_date), 3), N' ', RIGHT(CONVERT(VARCHAR(4), YEAR(g.from_date)), 2),
           N' → ', LEFT(DATENAME(MONTH, g.to_date), 3), N' ', RIGHT(CONVERT(VARCHAR(4), YEAR(g.to_date)), 2))
                                                                                   AS pair_name,
    g.from_date,
    g.to_date,
    g.last_quarter - g.first_quarter + 1                                           AS quarters_in_pair,
    g.version_type,
    g.version_order,
    CONCAT(g.fiscal_year_label, N' ', g.version_type)                              AS plan_version,
    g.eff_first_quarter,
    g.eff_last_quarter,
    CASE WHEN g.eff_first_quarter <= g.eff_last_quarter
         THEN EOMONTH(DATEADD(MONTH, 3 * (g.eff_first_quarter - 1), DATEFROMPARTS(g.fiscal_year - 1, 6, 1))) END
                                                                                   AS eff_from_date,
    CASE WHEN g.eff_first_quarter <= g.eff_last_quarter
         THEN g.eff_last_quarter - g.eff_first_quarter + 1 ELSE 0 END             AS quarters_covered,
    CAST(CASE WHEN g.eff_first_quarter <= g.eff_last_quarter THEN 1 ELSE 0 END AS BIT) AS is_covered,
    CASE WHEN g.eff_first_quarter > g.eff_last_quarter THEN NULL
         WHEN g.eff_first_quarter = g.eff_last_quarter THEN CONCAT(N'Q', g.eff_first_quarter)
         ELSE CONCAT(N'Q', g.eff_first_quarter, N'–Q', g.eff_last_quarter) END    AS covered_label,
    l.view_name,
    l.view_order,
    l.group_name,
    l.is_view_default,
    COALESCE(pa.plan_rows, 0)                                                      AS plan_rows,
    CAST(CASE WHEN COALESCE(pa.plan_rows, 0) > 0 THEN 1 ELSE 0 END AS BIT)         AS has_plan,
    COALESCE(pa.planned_net_new, 0)                                                AS planned_net_new,
    COALESCE(pa.actual_net_new, 0)                                                 AS actual_net_new,
    COALESCE(pa.actual_net_new_reuse_candidates, 0)                                AS actual_net_new_reuse_candidates,
    COALESCE(pa.planned_backfills, 0)                                              AS planned_backfills,
    COALESCE(pa.actual_backfills, 0)                                               AS actual_backfills,
    COALESCE(pa.actual_external_hires, 0)                                          AS actual_external_hires,
    COALESCE(pa.actual_internal_moves, 0)                                          AS actual_internal_moves,
    COALESCE(pa.planned_ending_headcount, 0)                                       AS planned_ending_headcount,
    COALESCE(pa.actual_ending_headcount, 0)                                        AS actual_ending_headcount,
    ROUND(COALESCE(pa.planned_cost_usd, 0), 2)                                     AS planned_cost_usd,
    ROUND(COALESCE(pa.actual_cost_usd_plan_fx, 0), 2)                              AS actual_cost_usd_plan_fx,
    COALESCE(pa.planned_cw_headcount, 0)                                           AS planned_cw_headcount,
    COALESCE(pa.actual_cw_headcount, 0)                                            AS actual_cw_headcount,
    ROUND(COALESCE(pa.planned_cw_spend_usd, 0), 2)                                 AS planned_cw_spend_usd,
    ROUND(COALESCE(pa.actual_cw_spend_usd_plan_fx, 0), 2)                          AS actual_cw_spend_usd_plan_fx,
    COALESCE(fa.fills, 0)                                                          AS fills,
    COALESCE(fa.backfill_fills, 0)                                                 AS backfill_fills,
    COALESCE(fa.net_new_fills, 0)                                                  AS net_new_fills,
    COALESCE(fa.internal_fills, 0)                                                 AS internal_fills,
    COALESCE(fa.reuse_candidate_fills, 0)                                          AS reuse_candidate_fills,
    ROUND(COALESCE(fa.reuse_new_pay_usd_constant, 0), 2)                           AS reuse_new_pay_usd_constant,
    ROUND(COALESCE(fa.backfill_pay_change_usd_constant, 0), 2)                     AS backfill_pay_change_usd_constant,
    md.median_time_to_fill_days,
    md.median_vacancy_days
FROM (
    /* === PERIOD GRID === fiscal year x period x version, with the quarters the version plans */
    SELECT fy.fiscal_year,
           CONCAT(N'FY', RIGHT(CONVERT(VARCHAR(4), fy.fiscal_year), 2))                         AS fiscal_year_label,
           p.pair_code, p.pair_order, p.first_quarter, p.last_quarter,
           EOMONTH(DATEADD(MONTH, 3 * (p.first_quarter - 1), DATEFROMPARTS(fy.fiscal_year - 1, 6, 1))) AS from_date,
           EOMONTH(DATEADD(MONTH, 3 * p.last_quarter, DATEFROMPARTS(fy.fiscal_year - 1, 6, 1)))       AS to_date,
           v.version_type, v.version_order,
           CASE WHEN p.first_quarter > v.version_order THEN p.first_quarter ELSE v.version_order END AS eff_first_quarter,
           p.last_quarter                                                                       AS eff_last_quarter
    FROM (SELECT DISTINCT fiscal_year FROM rpt.vw_plan_vs_actual) AS fy
    CROSS JOIN (VALUES ('FY', 1, 1, 4), ('H1', 2, 1, 2), ('H2', 3, 3, 4),
                       ('Q1', 4, 1, 1), ('Q2', 5, 2, 2), ('Q3', 6, 3, 3), ('Q4', 7, 4, 4))
               AS p(pair_code, pair_order, first_quarter, last_quarter)
    CROSS JOIN (VALUES ('Budget', 1), ('RF1', 2), ('RF2', 3), ('RF3', 4)) AS v(version_type, version_order)
) AS g
CROSS JOIN (
    /* === GROUP LIST === every group that ever had a plan row; the view's largest is its default */
    SELECT s.view_name, s.view_order, s.group_name,
           CAST(CASE WHEN ROW_NUMBER() OVER (PARTITION BY s.view_name
                                             ORDER BY s.year_end_headcount DESC, s.group_name) = 1
                     THEN 1 ELSE 0 END AS BIT)                                          AS is_view_default
    FROM (
        SELECT gv.view_name, gv.view_order, gv.group_name,
               SUM(CASE WHEN p.version_type = 'Budget'
                         AND p.quarter_end_date = mx.last_quarter_end
                        THEN p.actual_ending_headcount ELSE 0 END)                       AS year_end_headcount
        FROM rpt.vw_plan_vs_actual AS p
        CROSS JOIN (SELECT MAX(quarter_end_date) AS last_quarter_end FROM rpt.vw_plan_vs_actual) AS mx
        CROSS APPLY (VALUES (N'Company', 1, N'Arcadia Systems'), (N'Function', 2, p.function_name),
                            (N'Sub-function', 3, p.sub_function), (N'Department', 4, p.department_name),
                            (N'Country', 5, p.country_name)) AS gv(view_name, view_order, group_name)
        WHERE p.department_id <> 'D-901'
        GROUP BY gv.view_name, gv.view_order, gv.group_name
    ) AS s
) AS l
LEFT JOIN (
    /* === PLAN === flows over the effective quarters, levels at to_date */
    SELECT g2.fiscal_year, g2.pair_code, g2.version_type, gv.view_name, gv.group_name,
           COUNT(*)                                                                             AS plan_rows,
           SUM(p.planned_net_new)                                                               AS planned_net_new,
           SUM(p.actual_net_new)                                                                AS actual_net_new,
           SUM(p.actual_net_new_reuse_candidates)                                               AS actual_net_new_reuse_candidates,
           SUM(p.planned_backfills)                                                             AS planned_backfills,
           SUM(p.actual_backfills)                                                              AS actual_backfills,
           SUM(p.actual_external_hires)                                                         AS actual_external_hires,
           SUM(p.actual_internal_moves)                                                         AS actual_internal_moves,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.planned_ending_headcount END)    AS planned_ending_headcount,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.actual_ending_headcount END)     AS actual_ending_headcount,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.planned_cost_usd END)            AS planned_cost_usd,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.actual_cost_usd_plan_fx END)     AS actual_cost_usd_plan_fx,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.planned_cw_headcount END)        AS planned_cw_headcount,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.actual_cw_headcount END)         AS actual_cw_headcount,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.planned_cw_spend_usd END)        AS planned_cw_spend_usd,
           SUM(CASE WHEN p.quarter_end_date = g2.to_date THEN p.actual_cw_spend_usd_plan_fx END) AS actual_cw_spend_usd_plan_fx
    FROM (
        SELECT fy.fiscal_year, p.pair_code, p.last_quarter, v.version_type,
               EOMONTH(DATEADD(MONTH, 3 * p.last_quarter, DATEFROMPARTS(fy.fiscal_year - 1, 6, 1))) AS to_date,
               CASE WHEN p.first_quarter > v.version_order THEN p.first_quarter ELSE v.version_order END AS eff_first_quarter
        FROM (SELECT DISTINCT fiscal_year FROM rpt.vw_plan_vs_actual) AS fy
        CROSS JOIN (VALUES ('FY', 1, 4), ('H1', 1, 2), ('H2', 3, 4), ('Q1', 1, 1), ('Q2', 2, 2), ('Q3', 3, 3), ('Q4', 4, 4))
                   AS p(pair_code, first_quarter, last_quarter)
        CROSS JOIN (VALUES ('Budget', 1), ('RF1', 2), ('RF2', 3), ('RF3', 4)) AS v(version_type, version_order)
    ) AS g2
    JOIN rpt.vw_plan_vs_actual AS p
      ON p.fiscal_year = g2.fiscal_year AND p.version_type = g2.version_type
     AND p.fiscal_quarter BETWEEN g2.eff_first_quarter AND g2.last_quarter
    CROSS APPLY (VALUES (N'Company', N'Arcadia Systems'), (N'Function', p.function_name),
                        (N'Sub-function', p.sub_function), (N'Department', p.department_name),
                        (N'Country', p.country_name)) AS gv(view_name, group_name)
    WHERE p.department_id <> 'D-901'
    GROUP BY g2.fiscal_year, g2.pair_code, g2.version_type, gv.view_name, gv.group_name
) AS pa
  ON pa.fiscal_year = g.fiscal_year AND pa.pair_code = g.pair_code AND pa.version_type = g.version_type
 AND pa.view_name = l.view_name AND pa.group_name = l.group_name
LEFT JOIN (
    /* === SEAT FILLS === over the effective quarters */
    SELECT g3.fiscal_year, g3.pair_code, g3.version_type, gv.view_name, gv.group_name,
           COUNT(*)                                                                             AS fills,
           SUM(CASE WHEN f.seat_type = 'Backfill' THEN 1 ELSE 0 END)                            AS backfill_fills,
           SUM(CASE WHEN f.seat_type = 'Net-new' THEN 1 ELSE 0 END)                             AS net_new_fills,
           SUM(CASE WHEN f.fill_type = 'Internal Move' THEN 1 ELSE 0 END)                       AS internal_fills,
           SUM(CASE WHEN f.reuse_candidate = 1 THEN 1 ELSE 0 END)                               AS reuse_candidate_fills,
           SUM(CASE WHEN f.reuse_candidate = 1 THEN f.new_pay_usd_constant END)                 AS reuse_new_pay_usd_constant,
           SUM(CASE WHEN f.seat_type = 'Backfill' THEN f.pay_change_usd_constant END)           AS backfill_pay_change_usd_constant
    FROM (
        SELECT fy.fiscal_year, p.pair_code, p.last_quarter, v.version_type,
               CASE WHEN p.first_quarter > v.version_order THEN p.first_quarter ELSE v.version_order END AS eff_first_quarter
        FROM (SELECT DISTINCT fiscal_year FROM rpt.vw_plan_vs_actual) AS fy
        CROSS JOIN (VALUES ('FY', 1, 4), ('H1', 1, 2), ('H2', 3, 4), ('Q1', 1, 1), ('Q2', 2, 2), ('Q3', 3, 3), ('Q4', 4, 4))
                   AS p(pair_code, first_quarter, last_quarter)
        CROSS JOIN (VALUES ('Budget', 1), ('RF1', 2), ('RF2', 3), ('RF3', 4)) AS v(version_type, version_order)
    ) AS g3
    JOIN rpt.vw_position_fill AS f
      ON f.fiscal_year = g3.fiscal_year
     AND CAST(RIGHT(f.fiscal_quarter_label, 1) AS INT) BETWEEN g3.eff_first_quarter AND g3.last_quarter
    CROSS APPLY (VALUES (N'Company', N'Arcadia Systems'), (N'Function', f.function_name),
                        (N'Sub-function', f.sub_function), (N'Department', f.department_name),
                        (N'Country', f.country_name)) AS gv(view_name, group_name)
    WHERE f.department_id <> 'D-901'
    GROUP BY g3.fiscal_year, g3.pair_code, g3.version_type, gv.view_name, gv.group_name
) AS fa
  ON fa.fiscal_year = g.fiscal_year AND fa.pair_code = g.pair_code AND fa.version_type = g.version_type
 AND fa.view_name = l.view_name AND fa.group_name = l.group_name
LEFT JOIN (
    /* === MEDIANS === backfills, excluding immediate refills (SQL Server's median is a window function) */
    SELECT DISTINCT g4.fiscal_year, g4.pair_code, g4.version_type, gv.view_name, gv.group_name,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.time_to_fill_days)
               OVER (PARTITION BY g4.fiscal_year, g4.pair_code, g4.version_type, gv.view_name, gv.group_name) AS median_time_to_fill_days,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY f.vacancy_days)
               OVER (PARTITION BY g4.fiscal_year, g4.pair_code, g4.version_type, gv.view_name, gv.group_name) AS median_vacancy_days
    FROM (
        SELECT fy.fiscal_year, p.pair_code, p.last_quarter, v.version_type,
               CASE WHEN p.first_quarter > v.version_order THEN p.first_quarter ELSE v.version_order END AS eff_first_quarter
        FROM (SELECT DISTINCT fiscal_year FROM rpt.vw_plan_vs_actual) AS fy
        CROSS JOIN (VALUES ('FY', 1, 4), ('H1', 1, 2), ('H2', 3, 4), ('Q1', 1, 1), ('Q2', 2, 2), ('Q3', 3, 3), ('Q4', 4, 4))
                   AS p(pair_code, first_quarter, last_quarter)
        CROSS JOIN (VALUES ('Budget', 1), ('RF1', 2), ('RF2', 3), ('RF3', 4)) AS v(version_type, version_order)
    ) AS g4
    JOIN rpt.vw_position_fill AS f
      ON f.fiscal_year = g4.fiscal_year
     AND CAST(RIGHT(f.fiscal_quarter_label, 1) AS INT) BETWEEN g4.eff_first_quarter AND g4.last_quarter
    CROSS APPLY (VALUES (N'Company', N'Arcadia Systems'), (N'Function', f.function_name),
                        (N'Sub-function', f.sub_function), (N'Department', f.department_name),
                        (N'Country', f.country_name)) AS gv(view_name, group_name)
    WHERE f.department_id <> 'D-901' AND f.seat_type = 'Backfill' AND f.seat_decision <> 'Immediate refill'
) AS md
  ON md.fiscal_year = g.fiscal_year AND md.pair_code = g.pair_code AND md.version_type = g.version_type
 AND md.view_name = l.view_name AND md.group_name = l.group_name
