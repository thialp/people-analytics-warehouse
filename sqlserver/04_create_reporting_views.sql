/*
  04_create_reporting_views.sql
  Reporting views for Tableau. Column names match the CSV marts in data/marts/,
  so a workbook built on SQL Server can be repointed to the CSVs (for Tableau
  Public) with Data > Replace Data Source and nothing else changes.

  rpt.vw_workforce_cost_snapshot
      Grain: month-end x department x country x grade x job family.
      Same content as data/marts/mart_workforce_cost_snapshot.csv.

  The cost bridge is deliberately NOT a view: it lives in Tableau as Custom SQL
  (tableau/custom_sql_workforce_cost_bridge.sql), the way many enterprise
  Tableau data sources are built.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

CREATE OR ALTER VIEW rpt.vw_workforce_cost_snapshot AS
SELECT
    s.MonthEndDate                       AS month_end_date,
    cal.FiscalYear                       AS fiscal_year,
    cal.FiscalQuarterLabel               AS fiscal_quarter_label,
    cal.FiscalPeriod                     AS fiscal_period,
    cal.IsFiscalYearEnd                  AS is_fiscal_year_end,
    s.DepartmentID                       AS department_id,
    d.DepartmentName                     AS department_name,
    d.SubFunction                        AS sub_function,
    d.FunctionName                       AS function_name,
    s.CountryCode                        AS country_code,
    loc.CountryName                      AS country_name,
    loc.Region                           AS region,
    s.CurrencyCode                       AS currency_code,
    s.Grade                              AS grade,
    g.GradeLevel                         AS grade_level,
    g.CareerTrack                        AS career_track,
    s.JobFamily                          AS job_family,
    COUNT(*)                                                               AS headcount,
    CAST(ROUND(SUM(CAST(s.FTE                 AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS fte,
    CAST(ROUND(SUM(CAST(s.BaseUsdNominal      AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS base_usd_nominal,
    CAST(ROUND(SUM(CAST(s.BaseUsdConstant     AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS base_usd_constant,
    CAST(ROUND(SUM(CAST(s.LoadedUsdNominal    AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS loaded_usd_nominal,
    CAST(ROUND(SUM(CAST(s.LoadedUsdConstant   AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS loaded_usd_constant,
    CAST(ROUND(SUM(CAST(s.RangeMidUsdConstant AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS range_mid_usd_constant
FROM dw.WorkerMonthEndSnapshot AS s
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
LEFT JOIN dw.DimDepartment AS d ON d.DepartmentID = s.DepartmentID
LEFT JOIN (SELECT DISTINCT CountryCode, CountryName, Region FROM dw.DimLocation) AS loc
       ON loc.CountryCode = s.CountryCode
LEFT JOIN (SELECT DISTINCT Grade, GradeLevel, CareerTrack FROM dw.DimJobProfile
           WHERE JobFamilyCode <> 'EXE') AS g
       ON g.Grade = s.Grade
WHERE s.IsExecutiveOfficer = 0
GROUP BY
    s.MonthEndDate, cal.FiscalYear, cal.FiscalQuarterLabel, cal.FiscalPeriod, cal.IsFiscalYearEnd,
    s.DepartmentID, d.DepartmentName, d.SubFunction, d.FunctionName,
    s.CountryCode, loc.CountryName, loc.Region, s.CurrencyCode,
    s.Grade, g.GradeLevel, g.CareerTrack, s.JobFamily;
GO

PRINT 'Created view rpt.vw_workforce_cost_snapshot';
GO
