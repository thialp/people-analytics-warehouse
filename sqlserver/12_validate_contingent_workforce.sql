/*
  12_validate_contingent_workforce.sql
  Release 3: checks the contingent workforce build (03c, 04b) and the cost bridge Custom SQL
  (tableau/custom_sql_workforce_cost_bridge.sql, included unchanged with sqlcmd's :r, exactly as
  Tableau runs it) against the DuckDB pipeline's values. Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/12_validate_contingent_workforce.sql

  Every "expected" value comes from the DuckDB marts (data/marts/) and
  docs/projects/contingent-workforce/case_study_4.md. Every row should say PASS.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #cb;
SELECT *
INTO #cb
FROM (
:r /repo/tableau/custom_sql_workforce_cost_bridge.sql
) AS b;
DECLARE @n INT = (SELECT COUNT(*) FROM #cb);
PRINT CONCAT('Workforce cost bridge Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Every raw row landed in dw';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'dw.BwSupplier' AS check_name, (SELECT COUNT(*) FROM dw.BwSupplier) AS actual, 23 AS expected
    UNION ALL SELECT 'dw.BwContingentWorker',         (SELECT COUNT(*) FROM dw.BwContingentWorker), 43484
    UNION ALL SELECT 'dw.BwServiceOrder',             (SELECT COUNT(*) FROM dw.BwServiceOrder), 58276
    UNION ALL SELECT 'dw.BwServiceOrderRevision',     (SELECT COUNT(*) FROM dw.BwServiceOrderRevision), 160499
    UNION ALL SELECT 'dw.BwTimesheetMonth',           (SELECT COUNT(*) FROM dw.BwTimesheetMonth), 632504
    UNION ALL SELECT 'dw.KsContingentWorker',         (SELECT COUNT(*) FROM dw.KsContingentWorker), 141791
    UNION ALL SELECT 'dw.FeedBridgewayKeystoneEvent', (SELECT COUNT(*) FROM dw.FeedBridgewayKeystoneEvent), 106357
    UNION ALL SELECT 'dw.RefCwDiscrepancyType',       (SELECT COUNT(*) FROM dw.RefCwDiscrepancyType), 13
    UNION ALL SELECT 'dw.GenCwDiscrepancyTruth',      (SELECT COUNT(*) FROM dw.GenCwDiscrepancyTruth), 28948
) AS c;
GO

PRINT '2. Population and spend';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'contingent workers working on 30 Jun 2026' AS check_name,
                     (SELECT COUNT(*) FROM dw.CwMonthEndSnapshot WHERE MonthEndDate = '2026-06-30') AS actual, 11941 AS expected
    UNION ALL SELECT 'conversions linked to Bridgeway',     (SELECT COUNT(*) FROM dw.CwConversion), 1174
    UNION ALL SELECT 'conversions that land in the walk',   (SELECT COUNT(*) FROM dw.CwConversion WHERE IsWalkConversion = 1), 1174
    UNION ALL SELECT 'billed in billing currency, to the cent, vw_cw_spend = timesheets',
                     (SELECT CASE WHEN (SELECT SUM(billed_amount_local) FROM rpt.vw_cw_spend)
                                     = (SELECT SUM(BilledAmountLocal) FROM dw.BwTimesheetMonth) THEN 1 ELSE 0 END), 1
    UNION ALL SELECT 'billed in billing currency, whole units',
                     (SELECT CAST(ROUND(SUM(billed_amount_local), 0) AS BIGINT) FROM rpt.vw_cw_spend), 21451717557
    UNION ALL SELECT 'plan FY26 Q4 (latest version): contingent workers planned',
                     (SELECT SUM(planned_cw_headcount) FROM rpt.vw_plan_vs_actual
                      WHERE is_latest_version = 1 AND fiscal_year = 2026 AND fiscal_quarter = 4), 11977
    UNION ALL SELECT 'plan FY26 Q4 (latest version): contingent workers actual',
                     (SELECT SUM(actual_cw_headcount) FROM rpt.vw_plan_vs_actual
                      WHERE is_latest_version = 1 AND fiscal_year = 2026 AND fiscal_quarter = 4), 11941
) AS c;
GO

PRINT '3. Who is who: identity resolution';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'Keystone supplier spellings' AS check_name, (SELECT COUNT(*) FROM dw.CwSupplierAlias) AS actual, 59 AS expected
    UNION ALL SELECT 'spellings that map to no Bridgeway supplier', (SELECT COUNT(*) FROM dw.CwSupplierAlias WHERE SupplierID IS NULL), 0
    UNION ALL SELECT 'Bridgeway workers not listed exactly once',
                     (SELECT COUNT(*) FROM dw.BwContingentWorker AS w
                      LEFT JOIN (SELECT BwWorkerID, COUNT(*) AS n FROM dw.CwIdentityResolution
                                 WHERE BwWorkerID IS NOT NULL GROUP BY BwWorkerID) AS i ON i.BwWorkerID = w.BwWorkerID
                      WHERE ISNULL(i.n, 0) <> 1), 0
    UNION ALL SELECT 'Keystone people not listed exactly once',
                     (SELECT COUNT(*) FROM (SELECT DISTINCT PersonID FROM dw.KsContingentWorker) AS k
                      LEFT JOIN (SELECT PersonID, COUNT(*) AS n FROM dw.CwIdentityResolution
                                 WHERE PersonID IS NOT NULL GROUP BY PersonID) AS i ON i.PersonID = k.PersonID
                      WHERE ISNULL(i.n, 0) <> 1), 0
    UNION ALL SELECT 'tier 1 matches (High)',   (SELECT COUNT(*) FROM dw.CwIdentityResolution WHERE MatchTier = 1), 41900
    UNION ALL SELECT 'tier 2 matches (Medium)', (SELECT COUNT(*) FROM dw.CwIdentityResolution WHERE MatchTier = 2), 130
    UNION ALL SELECT 'tier 3 matches (Low)',    (SELECT COUNT(*) FROM dw.CwIdentityResolution WHERE MatchTier = 3), 0
    UNION ALL SELECT 'Keystone only',           (SELECT COUNT(*) FROM dw.CwIdentityResolution WHERE MatchStatus = 'Keystone only'), 68
    UNION ALL SELECT 'Bridgeway only',          (SELECT COUNT(*) FROM dw.CwIdentityResolution WHERE MatchStatus = 'Bridgeway only'), 126
    UNION ALL SELECT 'never started',           (SELECT COUNT(*) FROM dw.CwIdentityResolution WHERE MatchStatus = 'Never started'), 1328
) AS c;
GO

PRINT '4. The discrepancies, open on 30 Jun 2026 (the work list), and the score';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'differences no recorded cause explains' AS check_name,
                     (SELECT COUNT(*) FROM dw.CwDiscrepancy WHERE DiscrepancyCode = 'Unexplained') AS actual, 0 AS expected
    UNION ALL SELECT 'workers with a discrepancy beyond a change in transit',
                     (SELECT SUM(workers_with_any_discrepancy) FROM rpt.vw_cw_reconciliation
                      WHERE row_type = 'Population' AND month_end_date = '2026-06-30'), 416
    UNION ALL SELECT 'CW01 Change arrived late',          (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW01'), 26
    UNION ALL SELECT 'CW02 Extension never arrived',      (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW02'), 65
    UNION ALL SELECT 'CW03 Early end never arrived',      (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW03'), 6
    UNION ALL SELECT 'CW04 Ended but not closed',         (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW04'), 99
    UNION ALL SELECT 'CW05 Changed in Keystone only',     (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW05'), 219
    UNION ALL SELECT 'CW06 Link ID missing or mistyped',  (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW06'), 49
    UNION ALL SELECT 'CW07 One person, two IDs',          (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW07'), 27
    UNION ALL SELECT 'CW08 Never reached Keystone',       (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW08'), 25
    UNION ALL SELECT 'CW09 Keystone-only',                (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW09'), 6
    UNION ALL SELECT 'CW10 Over the duration cap',        (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW10'), 1
    UNION ALL SELECT 'CW11 Billed after the assignment',  (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW11'), 1
    UNION ALL SELECT 'CW12 Attribute change never arrived', (SELECT COUNT(*) FROM rpt.vw_cw_discrepancy_detail WHERE month_end_date = '2026-06-30' AND discrepancy_code = 'CW12'), 16
    UNION ALL SELECT 'detection score: injected',         (SELECT SUM(injected) FROM rpt.vw_cw_detection_score), 28530
    UNION ALL SELECT 'detection score: detected',         (SELECT SUM(detected) FROM rpt.vw_cw_detection_score), 28530
    UNION ALL SELECT 'detection score: false flags',      (SELECT SUM(false_flags) FROM rpt.vw_cw_detection_score), 42
    UNION ALL SELECT 'engagements within 6 months of the cap', (SELECT COUNT(*) FROM rpt.vw_cw_engagement_cap WHERE cap_band = 'Under 6 months left'), 132
    UNION ALL SELECT 'engagements over the cap',          (SELECT COUNT(*) FROM rpt.vw_cw_engagement_cap WHERE cap_band = 'Over the cap'), 15
) AS c;
GO

PRINT '5. Cost: the bridge closes per department, worker type and month, and the Shapley effects add up';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'bridge department-months that do not close (loaded, nominal)' AS check_name,
                     (SELECT COUNT(*) FROM (
                          SELECT month_end_date, department_id, worker_type,
                                 SUM(CASE WHEN driver = 'Closing Run-Rate' THEN -loaded_usd_nominal ELSE loaded_usd_nominal END) AS gap
                          FROM #cb GROUP BY month_end_date, department_id, worker_type) AS g
                      WHERE ABS(gap) > 0.10) AS actual, 0 AS expected
    UNION ALL SELECT 'FY26 conversions out of Contingent, USD nominal (whole dollars)',
                     (SELECT CAST(ROUND(SUM(loaded_usd_nominal), 0) AS BIGINT) FROM #cb
                      WHERE worker_type = 'Contingent' AND driver = 'Conversions'
                        AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), -32702296
    UNION ALL SELECT 'FY26 conversions into Employee, USD nominal (whole dollars)',
                     (SELECT CAST(ROUND(SUM(loaded_usd_nominal), 0) AS BIGINT) FROM #cb
                      WHERE worker_type = 'Employee' AND driver = 'Conversions'
                        AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 19677620
    UNION ALL SELECT 'growth mix: pairs and groups where the six effects do not add up (to the dollar)',
                     (SELECT COUNT(*) FROM (
                          SELECT to_month_end, view_name, group_name,
                                 SUM(CASE WHEN factor_order BETWEEN 1 AND 6 THEN shapley_effect_usd ELSE 0 END)
                               - SUM(CASE WHEN factor_order = 7 THEN shapley_effect_usd
                                          WHEN factor_order = 0 THEN -shapley_effect_usd ELSE 0 END) AS gap
                          FROM rpt.vw_workforce_cost_growth_mix
                          GROUP BY to_month_end, view_name, group_name) AS g
                      WHERE ABS(gap) > 1), 0
    UNION ALL SELECT 'growth mix FY26: closing cost, company (whole dollars)',
                     (SELECT CAST(ROUND(shapley_effect_usd, 0) AS BIGINT) FROM rpt.vw_workforce_cost_growth_mix
                      WHERE to_month_end = '2026-06-30' AND view_name = 'Company' AND factor = 'Closing cost'), 4648108953
    UNION ALL SELECT 'growth mix FY26: volume effect, company (whole dollars)',
                     (SELECT CAST(ROUND(shapley_effect_usd, 0) AS BIGINT) FROM rpt.vw_workforce_cost_growth_mix
                      WHERE to_month_end = '2026-06-30' AND view_name = 'Company' AND factor = 'Volume'), 307094838
) AS c;
GO

DROP TABLE IF EXISTS #cb;
GO
