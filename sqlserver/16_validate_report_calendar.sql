/*
  16_validate_report_calendar.sql
  Release 5 (Dashboard #5, Seats to Fill): checks the report calendar and the forward budget as
  SQL Server loaded them. Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/16_validate_report_calendar.sql

  The report calendar is the one place the dashboards read their dates from (the as-of date, the
  current and forward fiscal years). The forward budget (FY27 Budget, approved May 15, 2026) plans
  the year after the as-of date and never reaches the plan vs actual view. Every expected value
  comes from the DuckDB warehouse (release 5).
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

PRINT '1. The report calendar';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'calendar rows' AS check_name, CAST((SELECT COUNT(*) FROM raw.ref_report_calendar) AS NVARCHAR(40)) AS actual, N'1' AS expected
    UNION ALL SELECT 'as-of date',          (SELECT MAX(report_as_of_date) FROM raw.ref_report_calendar), N'2026-06-30'
    UNION ALL SELECT 'as-of label',         (SELECT MAX(report_as_of_label) FROM raw.ref_report_calendar), N'Jun 30, 2026'
    UNION ALL SELECT 'current fiscal year', (SELECT MAX(current_fiscal_year_label) FROM raw.ref_report_calendar), N'FY26'
    UNION ALL SELECT 'forward fiscal year', (SELECT MAX(forward_fiscal_year_label) FROM raw.ref_report_calendar), N'FY27'
    UNION ALL SELECT 'forward budget',      (SELECT MAX(forward_budget_version) FROM raw.ref_report_calendar), N'FY27 Budget'
    UNION ALL SELECT 'quarters in window',  CAST((SELECT COUNT(*) FROM raw.ref_report_quarter) AS NVARCHAR(40)), N'24'
    UNION ALL SELECT 'forward quarters',    CAST((SELECT COUNT(*) FROM raw.ref_report_quarter WHERE is_forward = 'True') AS NVARCHAR(40)), N'4'
    UNION ALL SELECT 'quarter 0',           (SELECT MAX(quarter_label) FROM raw.ref_report_quarter WHERE quarter_offset = '0'), N'FY26 Q4'
    UNION ALL SELECT 'quarter offsets',     (SELECT CONCAT(MIN(CAST(quarter_offset AS INT)), ' to ', MAX(CAST(quarter_offset AS INT))) FROM raw.ref_report_quarter), N'-19 to 4'
    UNION ALL SELECT 'as-of is the last month-end',
                     CAST((SELECT MAX(MonthEndDate) FROM dw.MonthEndCalendar) AS NVARCHAR(40)),
                     (SELECT MAX(report_as_of_date) FROM raw.ref_report_calendar)
) AS c;
GO

PRINT '2. The forward budget (FY27 Budget)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'forward plan rows' AS check_name, (SELECT COUNT(*) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027) AS actual, 2520 AS expected
    UNION ALL SELECT 'cost centers',             (SELECT COUNT(DISTINCT CostCenterID) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027), 630
    UNION ALL SELECT 'versions',                 (SELECT COUNT(DISTINCT PlanVersion) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027), 1
    UNION ALL SELECT 'planned net-new PIDs',     (SELECT SUM(PlannedNetNew) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027), 2593
    UNION ALL SELECT 'planned backfills',        (SELECT SUM(PlannedBackfills) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027), 5116
    UNION ALL SELECT 'planned employees, Q4',    (SELECT SUM(PlannedEndingHeadcount) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027 AND FiscalQuarter = 4), 31498
    UNION ALL SELECT 'planned contingent, Q4',   (SELECT SUM(PlannedCwHeadcount) FROM dw.FactWorkforcePlan WHERE FiscalYear = 2027 AND FiscalQuarter = 4), 13097
    UNION ALL SELECT 'forward rows in plan vs actual', (SELECT COUNT(*) FROM rpt.vw_plan_vs_actual WHERE fiscal_year >= 2027), 0
) AS c;
GO
