/*
  15_validate_cw_reconciliation.sql
  Release 4: checks Dashboard #4's build (03d, 04c) and its Custom SQL
  (tableau/custom_sql_cw_reconciliation_dashboard.sql, included unchanged with sqlcmd's :r, exactly
  as Tableau runs it) against the DuckDB pipeline's values. Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/15_validate_cw_reconciliation.sql

  Every "expected" value comes from the DuckDB marts (data/marts/mart_cw_*.csv,
  mart_itsm_ticket_close.csv) and docs/projects/contingent-workforce/release_4_plan.md.
  Every row should say PASS.
  Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #d6;
SELECT *
INTO #d6
FROM (
:r /repo/tableau/custom_sql_cw_reconciliation_dashboard.sql
) AS d;
DECLARE @n INT = (SELECT COUNT(*) FROM #d6);
PRINT CONCAT('Dashboard #4 Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Every raw row landed in dw, and every derived table has its rows';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'dw.FeedEventDelivery' AS check_name, (SELECT COUNT(*) FROM dw.FeedEventDelivery) AS actual, 106357 AS expected
    UNION ALL SELECT 'dw.KsContingentWorkerAudit', (SELECT COUNT(*) FROM dw.KsContingentWorkerAudit), 141791
    UNION ALL SELECT 'dw.KsCwJob',                 (SELECT COUNT(*) FROM dw.KsCwJob), 76219
    UNION ALL SELECT 'dw.GenCwJobDefect',          (SELECT COUNT(*) FROM dw.GenCwJobDefect), 827
    UNION ALL SELECT 'dw.EtlLoadRun',              (SELECT COUNT(*) FROM dw.EtlLoadRun), 7428
    UNION ALL SELECT 'dw.ItsmTicket',              (SELECT COUNT(*) FROM dw.ItsmTicket), 3091
    UNION ALL SELECT 'dw.ItsmTicketEvent',         (SELECT COUNT(*) FROM dw.ItsmTicketEvent), 13325
    UNION ALL SELECT 'dw.ItsmTicketLink',          (SELECT COUNT(*) FROM dw.ItsmTicketLink), 3091
    UNION ALL SELECT 'dw.RefTicketCategory',       (SELECT COUNT(*) FROM dw.RefTicketCategory), 11
    UNION ALL SELECT 'dw.CwCloseRun',              (SELECT COUNT(*) FROM dw.CwCloseRun), 61
    UNION ALL SELECT 'dw.CwLoadGap',               (SELECT COUNT(*) FROM dw.CwLoadGap), 8
    UNION ALL SELECT 'dw.CwFlag',                  (SELECT COUNT(*) FROM dw.CwFlag), 21665
    UNION ALL SELECT 'rpt.vw_cw_gap_close',        (SELECT COUNT(*) FROM rpt.vw_cw_gap_close), 21665
    UNION ALL SELECT 'rpt.vw_cw_gap_rate_close',   (SELECT COUNT(*) FROM rpt.vw_cw_gap_rate_close), 27324
    UNION ALL SELECT 'rpt.vw_itsm_ticket_close',   (SELECT COUNT(*) FROM rpt.vw_itsm_ticket_close), 16446
    UNION ALL SELECT 'Custom SQL rows',            (SELECT COUNT(*) FROM #d6), 68240
    UNION ALL SELECT 'Custom SQL Sankey scaffold', (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Sankey'), 2805
    UNION ALL SELECT 'Custom SQL Sankey links',    (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Sankey' AND sk_part = 'Link'), 2700
    UNION ALL SELECT 'Gap rows with a short name', (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND flag_short IS NOT NULL), 21665
) AS c;
GO

PRINT '2. The June 2026 close (also Current): KPIs and the Sankey totals';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'KPI 1 working in Bridgeway' AS check_name,
                     (SELECT SUM(contractors_working) FROM #d6 WHERE row_type = 'Population' AND month_end_date = '2026-06-30') AS actual, 11941 AS expected
    UNION ALL SELECT 'KPI 1 active in Keystone',
                     (SELECT SUM(contractors_working_keystone) FROM #d6 WHERE row_type = 'Population' AND month_end_date = '2026-06-30'), 11875
    UNION ALL SELECT 'KPI 2 contractors with a gap',
                     (SELECT SUM(contractors_with_gap) FROM #d6 WHERE row_type = 'Population' AND month_end_date = '2026-06-30'), 383
    UNION ALL SELECT 'Gaps (Sankey total)',
                     (SELECT SUM(gaps) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30'), 407
    UNION ALL SELECT 'KPI 3 open at the prior close',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30' AND was_open_prior_close = 1 AND is_counted = 1), 342
    UNION ALL SELECT 'KPI 4 no ticket',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30' AND has_ticket = 0 AND is_counted = 1), 177
    UNION ALL SELECT 'KPI 5 open over 90 days',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30' AND days_open > 90 AND is_counted = 1), 277
    UNION ALL SELECT 'Place Bridgeway',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30' AND place = 'Bridgeway'), 194
    UNION ALL SELECT 'Place Keystone',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30' AND place = 'Keystone'), 151
    UNION ALL SELECT 'Place System feed',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2026-06-30' AND place = 'System feed'), 62
    UNION ALL SELECT 'Open tickets (ticket card)',
                     (SELECT SUM(tickets) FROM #d6 WHERE row_type = 'Ticket' AND month_end_date = '2026-06-30'), 361
) AS c;
GO

PRINT '3. Earlier closes: a failed load, and the replay';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'Dec 2024 gaps (Keystone load failed)' AS check_name,
                     (SELECT SUM(gaps) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2024-12-31') AS actual, 386 AS expected
    UNION ALL SELECT 'Dec 2024 load gaps, all to the system feed',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2024-12-31' AND cause_code = 'LOAD'
                        AND place = 'System feed' AND timing_class = 'Load failed'), 6
    UNION ALL SELECT 'Sep 2023 load gaps (Bridgeway load failed)',
                     (SELECT COUNT(*) FROM #d6 WHERE row_type = 'Gap' AND month_end_date = '2023-09-30' AND cause_code = 'LOAD'), 2
    UNION ALL SELECT 'Jun 2025 contractors with a gap',
                     (SELECT SUM(contractors_with_gap) FROM #d6 WHERE row_type = 'Population' AND month_end_date = '2025-06-30'), 327
    UNION ALL SELECT 'Jun 2025 working in Bridgeway',
                     (SELECT SUM(contractors_working) FROM #d6 WHERE row_type = 'Population' AND month_end_date = '2025-06-30'), 10707
    UNION ALL SELECT 'Load gaps at closes whose loads worked',
                     (SELECT COUNT(*) FROM dw.CwFlag AS f JOIN dw.CwCloseRun AS r ON r.MonthEndDate = f.MonthEndDate
                      WHERE f.CauseCode = 'LOAD' AND r.BwDataAsOf = r.MonthEndDate AND r.KsDataAsOf = r.MonthEndDate), 0
) AS c;
GO

PRINT '4. Keystone job data flags match the answer key on every close';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'seeded job defects missed' AS check_name,
                     (SELECT COUNT(*) FROM dw.CwCloseRun AS r
                      JOIN dw.GenCwJobDefect AS d ON d.StartDate <= r.MonthEndDate AND d.EndDateFilled >= r.MonthEndDate
                      WHERE NOT EXISTS (SELECT 1 FROM dw.CwFlag AS f WHERE f.MonthEndDate = r.MonthEndDate
                                        AND f.FlagCode = d.FlagCode AND f.PersonID = d.PersonID AND f.CauseCode = 'JOB')) AS actual,
                     0 AS expected
    UNION ALL SELECT 'job flags the answer key does not have',
                     (SELECT COUNT(*) FROM dw.CwFlag AS f
                      WHERE f.CauseCode = 'JOB'
                        AND NOT EXISTS (SELECT 1 FROM dw.GenCwJobDefect AS d
                                        WHERE d.StartDate <= f.MonthEndDate AND d.EndDateFilled >= f.MonthEndDate
                                          AND d.FlagCode = f.FlagCode AND d.PersonID = f.PersonID)), 0
) AS c;
GO
