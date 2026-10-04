/*
  03_build_dw.sql
  Builds the typed warehouse layer (dw) from the raw landing tables:

    dimensions   DimWorker, DimDepartment, DimLocation, DimJobProfile
    facts        FactJobHistory, FactCompensationHistory   (SCD Type 2)
    reference    RefFxRate, RefFringeRate, RefSalaryRange
    derived      MonthEndCalendar, WorkerMonthEndSnapshot

  WorkerMonthEndSnapshot is pre-computed and indexed on (MonthEndDate, WorkerID).
  Reporting queries then join snapshots to each other on equality instead of
  re-running date-range joins against the SCD2 history every time.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ---------------------------------------------------------------- dimensions */
DROP TABLE IF EXISTS dw.DimWorker;
SELECT
    CAST(worker_id AS VARCHAR(12))                         AS WorkerID,
    CONVERT(DATE, original_hire_date)                      AS OriginalHireDate,
    CONVERT(DATE, NULLIF(termination_date, ''))            AS TerminationDate,
    CAST(NULLIF(termination_type, '') AS VARCHAR(20))      AS TerminationType,
    CAST(worker_type AS VARCHAR(40))                       AS WorkerType,
    CAST(CASE WHEN is_executive_officer IN ('True', 'true', '1') THEN 1 ELSE 0 END AS BIT) AS IsExecutiveOfficer
INTO dw.DimWorker
FROM raw.dim_worker;
ALTER TABLE dw.DimWorker ALTER COLUMN WorkerID VARCHAR(12) NOT NULL;
ALTER TABLE dw.DimWorker ADD CONSTRAINT PK_DimWorker PRIMARY KEY (WorkerID);
GO

DROP TABLE IF EXISTS dw.DimDepartment;
SELECT
    CAST(department_id   AS VARCHAR(10))   AS DepartmentID,
    CAST(department_name AS VARCHAR(60))   AS DepartmentName,
    CAST(sub_function    AS VARCHAR(60))   AS SubFunction,
    CAST([function]      AS VARCHAR(60))   AS FunctionName,
    CAST(cost_center     AS VARCHAR(10))   AS CostCenter,
    CONVERT(DATE, effective_from_date)     AS EffectiveFromDate
INTO dw.DimDepartment
FROM raw.dim_department;
GO

DROP TABLE IF EXISTS dw.DimLocation;
SELECT
    CAST(location_id   AS VARCHAR(10))  AS LocationID,
    CAST(city          AS VARCHAR(60))  AS City,
    CAST(country_code  AS CHAR(2))      AS CountryCode,
    CAST(country_name  AS VARCHAR(60))  AS CountryName,
    CAST(region        AS VARCHAR(40))  AS Region,
    CAST(currency_code AS CHAR(3))      AS CurrencyCode,
    CAST(site_type     AS VARCHAR(30))  AS SiteType
INTO dw.DimLocation
FROM raw.dim_location;
GO

DROP TABLE IF EXISTS dw.DimJobProfile;
SELECT
    CAST(job_profile_id  AS VARCHAR(10))  AS JobProfileID,
    CAST(job_family_code AS VARCHAR(5))   AS JobFamilyCode,
    CAST(job_family      AS VARCHAR(60))  AS JobFamily,
    CAST(job_title       AS VARCHAR(80))  AS JobTitle,
    CAST(grade AS INT)                    AS Grade,
    CAST(grade_level     AS VARCHAR(40))  AS GradeLevel,
    CAST(career_track    AS VARCHAR(40))  AS CareerTrack
INTO dw.DimJobProfile
FROM raw.dim_job_profile;
GO

/* --------------------------------------------------------------------- facts */
DROP TABLE IF EXISTS dw.FactJobHistory;
SELECT
    CAST(job_record_id AS VARCHAR(12))                     AS JobRecordID,
    CAST(worker_id     AS VARCHAR(12))                     AS WorkerID,
    CONVERT(DATE, effective_start_date)                    AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))          AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')),
           CONVERT(DATE, '9999-12-31'))                    AS EffectiveEndDateFilled,
    CAST(action_reason  AS VARCHAR(30))                    AS ActionReason,
    CAST(position_id    AS VARCHAR(12))                    AS PositionID,
    CAST(department_id  AS VARCHAR(10))                    AS DepartmentID,
    CAST(location_id    AS VARCHAR(10))                    AS LocationID,
    CAST(job_profile_id AS VARCHAR(10))                    AS JobProfileID,
    CAST(grade AS INT)                                     AS Grade,
    CAST(fte AS DECIMAL(4, 2))                             AS FTE
INTO dw.FactJobHistory
FROM raw.fact_job_history;
CREATE CLUSTERED INDEX CIX_FactJobHistory ON dw.FactJobHistory (WorkerID, EffectiveStartDate);
GO

/*
  Compensation corrections: the source records a correction as a second row with
  the SAME worker and effective date. Only the latest entry (highest record id)
  is true; keeping both would double-count that worker's pay.
*/
DROP TABLE IF EXISTS dw.FactCompensationHistory;
SELECT
    CompRecordID, WorkerID, EffectiveStartDate, EffectiveEndDate,
    ISNULL(EffectiveEndDate, CONVERT(DATE, '9999-12-31'))  AS EffectiveEndDateFilled,
    ActionReason, CurrencyCode, BaseSalaryAnnualLocal,
    CAST(CASE WHEN VersionsLoaded > 1 THEN 1 ELSE 0 END AS BIT) AS WasCorrected
INTO dw.FactCompensationHistory
FROM (
    SELECT
        CAST(comp_record_id AS VARCHAR(12))                AS CompRecordID,
        CAST(worker_id      AS VARCHAR(12))                AS WorkerID,
        CONVERT(DATE, effective_start_date)                AS EffectiveStartDate,
        CONVERT(DATE, NULLIF(effective_end_date, ''))      AS EffectiveEndDate,
        CAST(action_reason  AS VARCHAR(30))                AS ActionReason,
        CAST(currency_code  AS CHAR(3))                    AS CurrencyCode,
        CAST(base_salary_annual_local AS DECIMAL(18, 2))   AS BaseSalaryAnnualLocal,
        ROW_NUMBER() OVER (PARTITION BY worker_id, effective_start_date
                           ORDER BY comp_record_id DESC)   AS VersionRank,
        COUNT(*)     OVER (PARTITION BY worker_id, effective_start_date) AS VersionsLoaded
    FROM raw.fact_compensation_history
) AS ranked
WHERE VersionRank = 1;
CREATE CLUSTERED INDEX CIX_FactCompensationHistory ON dw.FactCompensationHistory (WorkerID, EffectiveStartDate);
GO

/* ----------------------------------------------------------------- reference */
DROP TABLE IF EXISTS dw.RefFxRate;
SELECT
    CAST(m.currency_code AS CHAR(3))              AS CurrencyCode,
    CONVERT(DATE, m.rate_date)                    AS RateDate,
    CAST(m.usd_per_local AS FLOAT)                AS UsdPerLocalActual,
    CAST(c.usd_per_local AS FLOAT)                AS UsdPerLocalConstant,
    CAST(c.rate_set AS VARCHAR(20))               AS ConstantRateSet
INTO dw.RefFxRate
FROM raw.ref_fx_rate_monthly AS m
JOIN raw.ref_fx_rate_constant AS c ON c.currency_code = m.currency_code;
GO

DROP TABLE IF EXISTS dw.RefFringeRate;
SELECT
    CAST(country_code AS CHAR(2))   AS CountryCode,
    CAST(fiscal_year AS INT)        AS FiscalYear,
    CAST(fringe_rate AS FLOAT)      AS FringeRate
INTO dw.RefFringeRate
FROM raw.ref_fringe_rate;
GO

DROP TABLE IF EXISTS dw.RefSalaryRange;
SELECT
    CAST(fiscal_year AS INT)                AS FiscalYear,
    CAST(grade AS INT)                      AS Grade,
    CAST(country_code AS CHAR(2))           AS CountryCode,
    CAST(currency_code AS CHAR(3))          AS CurrencyCode,
    CAST(range_min AS DECIMAL(18, 2))       AS RangeMin,
    CAST(range_mid AS DECIMAL(18, 2))       AS RangeMid,
    CAST(range_max AS DECIMAL(18, 2))       AS RangeMax
INTO dw.RefSalaryRange
FROM raw.ref_salary_range;
GO

/* ------------------------------------------------------------------ calendar
   One row per month-end that has FX rates loaded. Fiscal year starts July 1. */
DROP TABLE IF EXISTS dw.MonthEndCalendar;
SELECT
    MonthEndDate,
    LAG(MonthEndDate) OVER (ORDER BY MonthEndDate)                            AS PriorMonthEndDate,
    FiscalYear,
    FiscalMonth,
    (FiscalMonth + 2) / 3                                                     AS FiscalQuarter,
    CONCAT('FY', RIGHT(FiscalYear, 2), ' Q', (FiscalMonth + 2) / 3)           AS FiscalQuarterLabel,
    CONCAT('FY', RIGHT(FiscalYear, 2), ' P', RIGHT(CONCAT('0', FiscalMonth), 2)) AS FiscalPeriod,
    CAST(CASE WHEN FiscalMonth = 12 THEN 1 ELSE 0 END AS BIT)                 AS IsFiscalYearEnd
INTO dw.MonthEndCalendar
FROM (
    SELECT DISTINCT
        RateDate                                                              AS MonthEndDate,
        YEAR(RateDate) + CASE WHEN MONTH(RateDate) >= 7 THEN 1 ELSE 0 END     AS FiscalYear,
        ((MONTH(RateDate) + 5) % 12) + 1                                      AS FiscalMonth
    FROM dw.RefFxRate
) AS m;
GO

/* ------------------------------------------------- worker month-end snapshot
   One row per active worker per month-end: the job and pay records in effect on
   that date, with FX, fringe and pay range attached. Pay measures are
   annualized run-rates (annual base x FTE), in nominal and constant USD. */
DROP TABLE IF EXISTS dw.WorkerMonthEndSnapshot;
SELECT
    cal.MonthEndDate,
    cal.FiscalYear,
    w.WorkerID,
    w.IsExecutiveOfficer,
    j.PositionID,
    j.DepartmentID,
    j.LocationID,
    loc.CountryCode,
    j.JobProfileID,
    jp.JobFamily,
    j.Grade,
    j.FTE,
    c.CompRecordID,
    c.CurrencyCode,
    c.BaseSalaryAnnualLocal,
    fx.UsdPerLocalActual                                                         AS FxRateActual,
    fx.UsdPerLocalConstant                                                       AS FxRateConstant,
    fr.FringeRate,
    rng.RangeMid                                                                 AS RangeMidLocal,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalActual                       AS BaseUsdNominal,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalConstant                     AS BaseUsdConstant,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalActual   * (1 + fr.FringeRate) AS LoadedUsdNominal,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalConstant * (1 + fr.FringeRate) AS LoadedUsdConstant,
    rng.RangeMid * j.FTE * fx.UsdPerLocalConstant                                AS RangeMidUsdConstant
INTO dw.WorkerMonthEndSnapshot
FROM dw.MonthEndCalendar AS cal
JOIN dw.DimWorker AS w
  ON w.OriginalHireDate <= cal.MonthEndDate
 AND (w.TerminationDate IS NULL OR w.TerminationDate >= cal.MonthEndDate)
JOIN dw.FactJobHistory AS j
  ON j.WorkerID = w.WorkerID
 AND cal.MonthEndDate BETWEEN j.EffectiveStartDate AND j.EffectiveEndDateFilled
LEFT JOIN dw.FactCompensationHistory AS c
  ON c.WorkerID = w.WorkerID
 AND cal.MonthEndDate BETWEEN c.EffectiveStartDate AND c.EffectiveEndDateFilled
LEFT JOIN dw.DimLocation   AS loc ON loc.LocationID  = j.LocationID
LEFT JOIN dw.DimJobProfile AS jp  ON jp.JobProfileID = j.JobProfileID
LEFT JOIN dw.RefFxRate     AS fx
  ON fx.CurrencyCode = c.CurrencyCode
 AND fx.RateDate     = cal.MonthEndDate
LEFT JOIN dw.RefFringeRate AS fr
  ON fr.CountryCode = loc.CountryCode
 AND fr.FiscalYear  = cal.FiscalYear
LEFT JOIN dw.RefSalaryRange AS rng
  ON rng.FiscalYear  = cal.FiscalYear
 AND rng.Grade       = j.Grade
 AND rng.CountryCode = loc.CountryCode;

ALTER TABLE dw.WorkerMonthEndSnapshot ALTER COLUMN WorkerID VARCHAR(12) NOT NULL;
ALTER TABLE dw.WorkerMonthEndSnapshot ALTER COLUMN MonthEndDate DATE NOT NULL;
ALTER TABLE dw.WorkerMonthEndSnapshot
    ADD CONSTRAINT PK_WorkerMonthEndSnapshot PRIMARY KEY CLUSTERED (MonthEndDate, WorkerID);
GO

/* -------------------------------------------------------------------- summary */
SELECT 'dw.DimWorker' AS TableName, COUNT(*) AS RowsLoaded FROM dw.DimWorker
UNION ALL SELECT 'dw.FactJobHistory', COUNT(*) FROM dw.FactJobHistory
UNION ALL SELECT 'dw.FactCompensationHistory', COUNT(*) FROM dw.FactCompensationHistory
UNION ALL SELECT 'dw.MonthEndCalendar', COUNT(*) FROM dw.MonthEndCalendar
UNION ALL SELECT 'dw.WorkerMonthEndSnapshot', COUNT(*) FROM dw.WorkerMonthEndSnapshot;
GO
