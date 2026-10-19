-- Dashboard #3's summary (mart_wfp_summary) must tie to the plan and the seat fills, and no
-- choice on the page may lead to a combination without data. Returns the rows that break:
--   1. one row per fiscal year x period x version x view x group, and every group in every period
--   2. plan actuals equal the seat fills over the same quarters (net-new, backfills, reuse)
--   3. every view's groups add up to Company, for flows and for year-end levels
--   4. Company FY rows equal mart_plan_vs_actual summed directly (executive officers excluded)
--   5. a version plans exactly the quarters ahead of it: covered = last quarter >= version order
--   6. each view's default group has a plan in every covered period and version
WITH s AS (SELECT * FROM marts.mart_wfp_summary),
checks AS (
    SELECT 'duplicate key' AS rule, COUNT(*) - COUNT(DISTINCT (fiscal_year, pair_code, version_type, view_name, group_name)) AS n
    FROM s
    UNION ALL
    SELECT 'group missing from a period', COUNT(*)
    FROM (SELECT DISTINCT view_name, group_name FROM s) AS gl
    CROSS JOIN (SELECT DISTINCT fiscal_year, pair_code, version_type FROM s) AS pr
    WHERE NOT EXISTS (SELECT 1 FROM s WHERE s.view_name = gl.view_name AND s.group_name = gl.group_name
                        AND s.fiscal_year = pr.fiscal_year AND s.pair_code = pr.pair_code AND s.version_type = pr.version_type)
    UNION ALL
    SELECT 'plan actuals differ from the fills', COUNT(*)
    FROM s
    WHERE actual_net_new <> net_new_fills OR actual_backfills <> backfill_fills
       OR actual_net_new_reuse_candidates <> reuse_candidate_fills
       OR actual_external_hires + actual_internal_moves <> fills
    UNION ALL
    SELECT 'groups do not add up to Company', COUNT(*)
    FROM (
        SELECT fiscal_year, pair_code, version_type, view_name,
               SUM(planned_net_new) AS a, SUM(actual_net_new) AS b, SUM(planned_backfills) AS c,
               SUM(actual_ending_headcount) AS d, SUM(planned_ending_headcount) AS e, SUM(actual_cw_headcount) AS f,
               SUM(fills) AS h
        FROM s WHERE view_name <> 'Company' GROUP BY ALL
    ) AS v
    JOIN s AS c ON c.view_name = 'Company' AND c.fiscal_year = v.fiscal_year
               AND c.pair_code = v.pair_code AND c.version_type = v.version_type
    WHERE v.a <> c.planned_net_new OR v.b <> c.actual_net_new OR v.c <> c.planned_backfills
       OR v.d <> c.actual_ending_headcount OR v.e <> c.planned_ending_headcount
       OR v.f <> c.actual_cw_headcount OR v.h <> c.fills
    UNION ALL
    SELECT 'Company FY differs from mart_plan_vs_actual', COUNT(*)
    FROM (
        SELECT fiscal_year, version_type,
               SUM(planned_net_new) AS pnn, SUM(actual_net_new) AS ann,
               SUM(planned_backfills) AS pbf, SUM(actual_backfills) AS abf,
               SUM(CASE WHEN fiscal_quarter = 4 THEN actual_ending_headcount END) AS ahc,
               SUM(CASE WHEN fiscal_quarter = 4 THEN planned_ending_headcount END) AS phc,
               SUM(CASE WHEN fiscal_quarter = 4 THEN planned_cw_headcount END) AS pcw
        FROM marts.mart_plan_vs_actual WHERE department_id <> 'D-901' GROUP BY ALL
    ) AS m
    JOIN s ON s.view_name = 'Company' AND s.pair_code = 'FY'
          AND s.fiscal_year = m.fiscal_year AND s.version_type = m.version_type
    WHERE s.planned_net_new <> m.pnn OR s.actual_net_new <> m.ann OR s.planned_backfills <> m.pbf
       OR s.actual_backfills <> m.abf OR s.actual_ending_headcount <> m.ahc
       OR s.planned_ending_headcount <> m.phc OR s.planned_cw_headcount <> m.pcw
    UNION ALL
    SELECT 'coverage does not follow the version', COUNT(*)
    FROM s
    WHERE is_covered <> (CASE pair_code WHEN 'FY' THEN 4 WHEN 'H1' THEN 2 WHEN 'H2' THEN 4
                                        ELSE CAST(RIGHT(pair_code, 1) AS INTEGER) END >= version_order)
       OR (NOT is_covered AND (planned_net_new <> 0 OR fills <> 0 OR plan_rows <> 0))
    UNION ALL
    SELECT 'a view default without a plan', COUNT(*)
    FROM s WHERE is_view_default AND is_covered AND NOT has_plan
    UNION ALL
    SELECT 'executive officers counted', COUNT(*)
    FROM s WHERE view_name = 'Department' AND group_name = 'Office of the CEO'
)
SELECT rule, n FROM checks WHERE n <> 0
