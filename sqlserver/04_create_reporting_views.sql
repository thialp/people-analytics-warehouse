/*
  04_create_reporting_views.sql
  Reporting views for Tableau. Column names match the CSV marts in data/marts/,
  so a workbook built on SQL Server can be repointed to the CSVs (for Tableau
  Public) with Data > Replace Data Source and nothing else changes.

  rpt.vw_workforce_cost_snapshot
      Grain: month-end x department x country x grade x job family.
      Same content as data/marts/mart_workforce_cost_snapshot.csv.
  rpt.vw_org_leader_summary
      Grain: org leader x fiscal year-end (and the latest month-end).
      Same content as data/marts/mart_org_leader_summary.csv.
  rpt.vw_fringe_rate
      Grain: country x calendar year. Same content as data/marts/mart_fringe_rate.csv.

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
    ctry.CountryName                     AS country_name,
    ctry.Region                          AS region,
    s.CurrencyCode                       AS currency_code,
    s.Grade                              AS grade,
    jp.GradeLevel                        AS grade_level,
    jp.CareerTrack                       AS career_track,
    s.JobFamily                          AS job_family,
    COUNT(*)                                                               AS headcount,
    CAST(ROUND(SUM(CAST(s.FTE                 AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS fte,
    CAST(ROUND(SUM(CAST(s.BaseUsdNominal      AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS base_usd_nominal,
    CAST(ROUND(SUM(CAST(s.BaseUsdConstant     AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS base_usd_constant,
    CAST(ROUND(SUM(CAST(s.LoadedUsdNominal    AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS loaded_usd_nominal,
    CAST(ROUND(SUM(CAST(s.LoadedUsdConstant   AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS loaded_usd_constant,
    CAST(ROUND(SUM(CAST(s.RangeMidUsdConstant AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2)) AS range_mid_usd_constant
FROM dw.WorkerMonthEndSnapshot AS s
JOIN dw.MonthEndCalendar AS cal   ON cal.MonthEndDate = s.MonthEndDate
LEFT JOIN dw.DimDepartment AS d   ON d.DepartmentID   = s.DepartmentID
LEFT JOIN dw.DimCountry AS ctry   ON ctry.CountryCode = s.CountryCode
LEFT JOIN dw.DimJobLevel AS jp    ON jp.Grade         = s.Grade
WHERE s.IsExecutiveOfficer = 0
GROUP BY
    s.MonthEndDate, cal.FiscalYear, cal.FiscalQuarterLabel, cal.FiscalPeriod, cal.IsFiscalYearEnd,
    s.DepartmentID, d.DepartmentName, d.SubFunction, d.FunctionName,
    s.CountryCode, ctry.CountryName, ctry.Region, s.CurrencyCode,
    s.Grade, jp.GradeLevel, jp.CareerTrack, s.JobFamily;
GO

CREATE OR ALTER VIEW rpt.vw_org_leader_summary AS
SELECT
    s.MonthEndDate                                   AS month_end_date,
    cal.FiscalYear                                   AS fiscal_year,
    ou.OrgUnitType                                   AS org_unit_type,
    s.LeadsOrgUnitID                                 AS org_unit_id,
    ou.OrgUnitName                                   AS org_unit_name,
    ou.ParentOrgUnitID                               AS parent_org_unit_id,
    ou.FunctionName                                  AS function_name,
    ou.LeaderTitle                                   AS leader_title,
    s.WorkerID                                       AS worker_id,
    CONCAT(w.FirstName, ' ', w.LastName)             AS worker_name,
    jp.JobTitle                                      AS job_title,
    s.Grade                                          AS grade,
    s.DepartmentID                                   AS department_id,
    loc.OfficeName                                   AS office_name,
    s.ManagerWorkerID                                AS manager_worker_id,
    CONCAT(mw.FirstName, ' ', mw.LastName)           AS manager_name,
    ISNULL(sp.DirectReports, 0)                      AS direct_reports,
    ISNULL(sp.TotalReports, 0)                       AS total_reports,
    ISNULL(lay.LayersFromCeo, 0)                     AS layers_from_ceo
FROM dw.WorkerMonthEndSnapshot AS s
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
JOIN dw.DimOrgUnit AS ou        ON ou.OrgUnitID = s.LeadsOrgUnitID
JOIN dw.DimWorker AS w          ON w.WorkerID = s.WorkerID
LEFT JOIN dw.DimWorker AS mw    ON mw.WorkerID = s.ManagerWorkerID
LEFT JOIN dw.DimJobProfile AS jp ON jp.JobProfileID = s.JobProfileID
LEFT JOIN dw.DimLocation AS loc ON loc.LocationID = s.LocationID
LEFT JOIN (
    SELECT MonthEndDate, AncestorWorkerID,
           SUM(CASE WHEN Hops = 1 THEN 1 ELSE 0 END) AS DirectReports,
           COUNT(*)                                  AS TotalReports
    FROM dw.WorkerReportingChain
    GROUP BY MonthEndDate, AncestorWorkerID
) AS sp ON sp.MonthEndDate = s.MonthEndDate AND sp.AncestorWorkerID = s.WorkerID
LEFT JOIN (
    SELECT MonthEndDate, WorkerID, MAX(Hops) AS LayersFromCeo
    FROM dw.WorkerReportingChain
    GROUP BY MonthEndDate, WorkerID
) AS lay ON lay.MonthEndDate = s.MonthEndDate AND lay.WorkerID = s.WorkerID
WHERE cal.IsFiscalYearEnd = 1
   OR s.MonthEndDate = (SELECT MAX(MonthEndDate) FROM dw.MonthEndCalendar);
GO

CREATE OR ALTER VIEW rpt.vw_fringe_rate AS
SELECT
    f.CountryCode                  AS country_code,
    c.CountryName                  AS country_name,
    c.Region                       AS region,
    f.FringeYear                   AS fringe_year,
    f.SocialContributionRate       AS social_contribution_rate,
    f.RetirementSeveranceRate      AS retirement_severance_rate,
    f.StatutoryPayRate             AS statutory_pay_rate,
    f.EmployerBenefitsRate         AS employer_benefits_rate,
    f.FringeRate                   AS fringe_rate,
    f.IsEstimate                   AS is_estimate,
    f.MethodNote                   AS method_note,
    (SELECT COUNT(DISTINCT s.SourceID) FROM dw.RefFringeSource AS s
      WHERE s.CountryCode = f.CountryCode AND s.FringeYear = f.FringeYear) AS source_count
FROM dw.RefFringeRate AS f
JOIN dw.DimCountry AS c ON c.CountryCode = f.CountryCode;
GO

PRINT 'Created views rpt.vw_workforce_cost_snapshot, rpt.vw_org_leader_summary, rpt.vw_fringe_rate';
GO
