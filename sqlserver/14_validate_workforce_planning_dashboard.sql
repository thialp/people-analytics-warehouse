/*
  14_validate_workforce_planning_dashboard.sql
  Runs Dashboard #3's Tableau Custom SQL inside SQL Server exactly as Tableau would (each file is
  included unchanged with sqlcmd's :r): the summary that feeds the KPI band and the rail, and the
  plan vs actual and position fill sources beside it. Checks that the summary has a row for every
  choice on the page, that it ties to the other two sources, and that the KPI card values are the
  ones the build guide expects. Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/14_validate_workforce_planning_dashboard.sql

  Every expected value comes from the DuckDB mart data/marts/mart_wfp_summary.csv (release 3).
  Money is compared to within 5 cents. Executive officers (D-901) are excluded everywhere, so
  FY26 year-end employees read 30,005, as on Dashboards #1 and #2.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #wfp;
SELECT *
INTO #wfp
FROM (
:r /repo/tableau/custom_sql_wfp_summary.sql
) AS s;
DECLARE @n INT = (SELECT COUNT(*) FROM #wfp);
PRINT CONCAT('WFP summary Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #pva;
SELECT *
INTO #pva
FROM (
:r /repo/tableau/custom_sql_plan_vs_actual.sql
) AS p;
DECLARE @n INT = (SELECT COUNT(*) FROM #pva);
PRINT CONCAT('Plan vs actual Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #fill;
SELECT *
INTO #fill
FROM (
:r /repo/tableau/custom_sql_position_fill.sql
) AS f;
DECLARE @n INT = (SELECT COUNT(*) FROM #fill);
PRINT CONCAT('Position fill Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Shape: one row for every choice on the page';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'summary rows'                      AS check_name, (SELECT COUNT(*) FROM #wfp) AS actual, 10080 AS expected
    UNION ALL SELECT 'distinct keys',
                     (SELECT COUNT(*) FROM (SELECT DISTINCT fiscal_year, pair_code, version_type, view_name, group_name FROM #wfp) AS k), 10080
    UNION ALL SELECT 'fiscal years',                     (SELECT COUNT(DISTINCT fiscal_year) FROM #wfp), 5
    UNION ALL SELECT 'groups (1 + 8 + 10 + 31 + 22)',    (SELECT COUNT(*) FROM (SELECT DISTINCT view_name, group_name FROM #wfp) AS g), 72
    UNION ALL SELECT 'rows a version plans',             (SELECT COUNT(*) FROM #wfp WHERE is_covered = 1), 7200
    UNION ALL SELECT 'rows with a plan',                 (SELECT COUNT(*) FROM #wfp WHERE has_plan = 1), 7040
    UNION ALL SELECT 'planned rows of groups not yet open (greyed)', (SELECT COUNT(*) FROM #wfp WHERE is_covered = 1 AND has_plan = 0), 160
    UNION ALL SELECT 'view defaults without a plan (expect 0)',
                     (SELECT COUNT(*) FROM #wfp WHERE is_view_default = 1 AND is_covered = 1 AND has_plan = 0), 0
    UNION ALL SELECT 'executive officers counted (expect 0)',
                     (SELECT COUNT(*) FROM #wfp WHERE group_name = 'Office of the CEO'), 0
    UNION ALL SELECT 'plan vs actual rows (officers excluded)', (SELECT COUNT(*) FROM #pva), 29365
    UNION ALL SELECT 'position fill rows',               (SELECT COUNT(*) FROM #fill), 30575
) AS c;
GO

PRINT '2. Ties (every check expects 0)';
SELECT check_name, failures, CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
    SELECT 'plan actuals differ from the seat fills' AS check_name, COUNT(*) AS failures
    FROM #wfp
    WHERE actual_net_new <> net_new_fills OR actual_backfills <> backfill_fills
       OR actual_net_new_reuse_candidates <> reuse_candidate_fills
       OR actual_external_hires + actual_internal_moves <> fills
    UNION ALL
    SELECT 'Company FY rows differ from the plan vs actual source', COUNT(*)
    FROM (
        SELECT fiscal_year, version_type,
               SUM(planned_net_new) AS pnn, SUM(actual_net_new) AS ann, SUM(planned_backfills) AS pbf,
               SUM(CASE WHEN fiscal_quarter = 4 THEN actual_ending_headcount END) AS ahc,
               SUM(CASE WHEN fiscal_quarter = 4 THEN planned_cw_headcount END)    AS pcw
        FROM #pva
        GROUP BY fiscal_year, version_type
    ) AS m
    JOIN #wfp AS s ON s.view_name = 'Company' AND s.pair_code = 'FY'
                  AND s.fiscal_year = m.fiscal_year AND s.version_type = m.version_type
    WHERE s.planned_net_new <> m.pnn OR s.actual_net_new <> m.ann OR s.planned_backfills <> m.pbf
       OR s.actual_ending_headcount <> m.ahc OR s.planned_cw_headcount <> m.pcw
    UNION ALL
    SELECT 'FY26 reuse candidates differ from the position fill source', ABS(
        (SELECT reuse_candidate_fills FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY'
            AND version_type = 'Budget' AND view_name = 'Company')
      - (SELECT COUNT(*) FROM #fill WHERE fiscal_year = 2026 AND reuse_candidate = 1))
    UNION ALL
    SELECT 'functions do not add up to Company', COUNT(*)
    FROM (
        SELECT fiscal_year, pair_code, version_type,
               SUM(actual_net_new) AS ann, SUM(planned_net_new) AS pnn, SUM(actual_ending_headcount) AS ahc
        FROM #wfp WHERE view_name = 'Function'
        GROUP BY fiscal_year, pair_code, version_type
    ) AS f
    JOIN #wfp AS c ON c.view_name = 'Company' AND c.fiscal_year = f.fiscal_year
                  AND c.pair_code = f.pair_code AND c.version_type = f.version_type
    WHERE f.ann <> c.actual_net_new OR f.pnn <> c.planned_net_new OR f.ahc <> c.actual_ending_headcount
) AS c;
GO

PRINT '3. KPI cards, FY26 (Jun 25 -> Jun 26), Company';
SELECT check_name, actual, expected,
       CASE WHEN ABS(actual - expected) <= 0.05 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'Budget: card 1 year-end employees' AS check_name, CAST(actual_ending_headcount AS DECIMAL(18,2)) AS actual, CAST(30005 AS DECIMAL(18,2)) AS expected FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 1 planned',            planned_ending_headcount,    30337         FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 1 cost, actual at plan FX', actual_cost_usd_plan_fx, 3407541370.14 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 1 cost, planned',      planned_cost_usd,            3446544994.11 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 2 net-new filled',     actual_net_new,              2181          FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 2 net-new planned',    planned_net_new,             2762          FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 3 backfills',          actual_backfills,            4668          FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 3 backfills planned',  planned_backfills,           5031          FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 3 median days to fill', median_time_to_fill_days,   42            FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 4 reuse candidates',   reuse_candidate_fills,       631           FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 4 starting base pay',  reuse_new_pay_usd_constant,  55680160.14   FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 5 contingent workers', actual_cw_headcount,         11941         FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 5 contingent planned', planned_cw_headcount,        12673         FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 5 spend, actual at plan FX', actual_cw_spend_usd_plan_fx, 1238675225.91 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Budget: card 5 spend, planned',     planned_cw_spend_usd,        1313939421.07 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'RF2 (plans Q3-Q4): net-new filled', actual_net_new,              981           FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'RF2' AND view_name = 'Company'
    UNION ALL SELECT 'RF2: net-new planned',              planned_net_new,             1097          FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'RF2' AND view_name = 'Company'
    UNION ALL SELECT 'RF2: year-end planned',             planned_ending_headcount,    30142         FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'RF2' AND view_name = 'Company'
    UNION ALL SELECT 'RF2: reuse candidates (Q3-Q4)',     reuse_candidate_fills,       303           FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'RF2' AND view_name = 'Company'
    UNION ALL SELECT 'H1 with RF2: not covered (0)',      CAST(is_covered AS INT),     0             FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'H1' AND version_type = 'RF2' AND view_name = 'Company'
    UNION ALL SELECT 'Q3 Budget: year-end employees',     actual_ending_headcount,     29618         FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'Q3' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Q3 Budget: median days vacant',     median_vacancy_days,         56            FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'Q3' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'Function Finance: net-new filled',  actual_net_new,              83            FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Function' AND group_name = 'Finance'
    UNION ALL SELECT 'Function Finance: net-new planned', planned_net_new,             122           FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Function' AND group_name = 'Finance'
    UNION ALL SELECT 'Country India: year-end employees', actual_ending_headcount,     6967          FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Country' AND group_name = 'India'
    UNION ALL SELECT 'FY24 Budget: net-new filled (restructuring)', actual_net_new,    910           FROM #wfp WHERE fiscal_year = 2024 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'FY24 Budget: net-new planned',      planned_net_new,             2833          FROM #wfp WHERE fiscal_year = 2024 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
) AS c;
GO

PRINT '4. Period names (pair_name must read exactly as on the rail)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'FY26' AS check_name, (SELECT MAX(pair_name) FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY') AS actual, N'FY26 · Jun 25 → Jun 26' AS expected
    UNION ALL SELECT 'FY26 H1',  (SELECT MAX(pair_name) FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'H1'), N'FY26 H1 · Jun 25 → Dec 25'
    UNION ALL SELECT 'FY26 Q3',  (SELECT MAX(pair_name) FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'Q3'), N'FY26 Q3 · Dec 25 → Mar 26'
    UNION ALL SELECT 'RF2 covers', (SELECT MAX(covered_label) FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'RF2'), N'Q3–Q4'
) AS c;
GO

PRINT '5. The PID ledger on Jun 30, 2026 (release 3.1: every contingent worker holds a PID)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'PIDs in total' AS check_name, CAST(pids_total AS INT) AS actual, 51163 AS expected FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'filled by employees',               pids_filled_employee,               30005 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'filled by contingent workers',      pids_filled_contingent,             11941 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'vacant, previously held',           vacant_previously_held,              8689 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'vacant, previously held, contingent', vacant_previously_held_contingent, 7712 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'vacant, previously held, 90+ days', vacant_previously_held_stale,        6540 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'vacant, new',                       vacant_new,                           528 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'vacant, new, contingent',           vacant_new_contingent,                237 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'backfills one level down',          level_down,                           567 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'backfills one level up',            level_up,                             185 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'backfills in another office',       moved_office,                         467 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'contingent fills',                  contingent_fills,                    7358 FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'FY' AND version_type = 'Budget' AND view_name = 'Company'
    UNION ALL SELECT 'period label FY26 Q3',              CASE WHEN (SELECT MAX(CONCAT(period_short, N' · ', period_months)) FROM #wfp WHERE fiscal_year = 2026 AND pair_code = 'Q3') = N'FY26 Q3 · Jan – Mar 26' THEN 1 ELSE 0 END, 1
    UNION ALL SELECT 'View default (Country) is Australia', CASE WHEN (SELECT MAX(group_name) FROM #wfp WHERE view_name = 'Country' AND is_view_default = 1) = N'Australia' THEN 1 ELSE 0 END, 1
) AS c;
GO
