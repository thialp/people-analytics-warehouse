/*
  03_build_dw.sql
  Builds the typed warehouse layer (dw) from the raw landing tables:

    dimensions   DimWorker, DimCountry, DimDepartment, DimOrgUnit, DimLocation,
                 DimJobLevel, DimJobProfile
    facts        FactJobHistory, FactCompensationHistory   (SCD Type 2)
                 FactPerformanceReview, FactBonusPayout
    reference    RefFxRateDaily, RefFxRate, RefFringeRate, RefFringeSource,
                 RefSalaryRange, RefJobLevelBaseSalary, RefTenureIncrease,
                 RefPerformanceBonus
    derived      MonthEndCalendar, CompensationHistoryUsd,
                 WorkerMonthEndSnapshot, WorkerReportingChain

  The raw files call the 1-12 ladder "job level"; dw and rpt call it Grade, the
  name the published marts and dashboards use.

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
    CAST(first_name AS VARCHAR(40))                        AS FirstName,
    CAST(last_name  AS VARCHAR(40))                        AS LastName,
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

DROP TABLE IF EXISTS dw.DimCountry;
SELECT
    CAST(country_code  AS CHAR(2))        AS CountryCode,
    CAST(country_name  AS VARCHAR(60))    AS CountryName,
    CAST(region        AS VARCHAR(40))    AS Region,
    CAST(currency_code AS CHAR(3))        AS CurrencyCode,
    CAST(pay_index AS DECIMAL(5, 2))      AS PayIndex
INTO dw.DimCountry
FROM raw.dim_country;
GO

DROP TABLE IF EXISTS dw.DimDepartment;
SELECT
    CAST(department_id      AS VARCHAR(10))   AS DepartmentID,
    CAST(department_name    AS VARCHAR(60))   AS DepartmentName,
    CAST(sub_function       AS VARCHAR(60))   AS SubFunction,
    CAST([function]         AS VARCHAR(60))   AS FunctionName,
    CAST(parent_org_unit_id AS VARCHAR(15))   AS ParentOrgUnitID,
    CAST(cost_center        AS VARCHAR(10))   AS CostCenter,
    CAST(head_job_level AS INT)               AS HeadGrade,
    CONVERT(DATE, effective_from_date)        AS EffectiveFromDate
INTO dw.DimDepartment
FROM raw.dim_department;
GO

DROP TABLE IF EXISTS dw.DimOrgUnit;
SELECT
    CAST(org_unit_id   AS VARCHAR(15))                     AS OrgUnitID,
    CAST(org_unit_name AS VARCHAR(60))                     AS OrgUnitName,
    CAST(org_unit_type AS VARCHAR(20))                     AS OrgUnitType,
    CAST(NULLIF(parent_org_unit_id, '') AS VARCHAR(15))    AS ParentOrgUnitID,
    CAST(NULLIF([function], '') AS VARCHAR(60))            AS FunctionName,
    CAST(leader_title  AS VARCHAR(80))                     AS LeaderTitle,
    CAST(leader_job_level AS INT)                          AS LeaderGrade
INTO dw.DimOrgUnit
FROM raw.dim_org_unit;
GO

DROP TABLE IF EXISTS dw.DimLocation;
SELECT
    CAST(location_id    AS VARCHAR(10))              AS LocationID,
    CAST(office_name    AS VARCHAR(60))              AS OfficeName,
    CAST(site_type      AS VARCHAR(30))              AS SiteType,
    CAST(street_address AS VARCHAR(100))             AS StreetAddress,
    CAST(city           AS VARCHAR(60))              AS City,
    CAST(state_province AS VARCHAR(60))              AS StateProvince,
    CAST(NULLIF(postal_code, '') AS VARCHAR(12))     AS PostalCode,
    CAST(country_code   AS CHAR(2))                  AS CountryCode,
    CAST(country_name   AS VARCHAR(60))              AS CountryName,
    CAST(region         AS VARCHAR(40))              AS Region,
    CAST(currency_code  AS CHAR(3))                  AS CurrencyCode,
    CAST(latitude  AS DECIMAL(9, 4))                 AS Latitude,
    CAST(longitude AS DECIMAL(9, 4))                 AS Longitude,
    CAST(geo_source     AS VARCHAR(120))             AS GeoSource,
    CAST(pay_zone_factor AS DECIMAL(5, 2))           AS PayZoneFactor,
    CONVERT(DATE, opened_date)                       AS OpenedDate
INTO dw.DimLocation
FROM raw.dim_location;
GO

DROP TABLE IF EXISTS dw.DimJobLevel;
SELECT
    CAST(job_level AS INT)                       AS Grade,
    CAST(level_code   AS VARCHAR(4))             AS LevelCode,
    CAST(level_name   AS VARCHAR(40))            AS GradeLevel,
    CAST(career_track AS VARCHAR(40))            AS CareerTrack,
    CAST(us_base_salary_usd AS DECIMAL(18, 2))   AS UsBaseSalaryUsd,
    CAST(range_min_pct AS FLOAT)                 AS RangeMinPct,
    CAST(range_max_pct AS FLOAT)                 AS RangeMaxPct
INTO dw.DimJobLevel
FROM raw.dim_job_level;
GO

DROP TABLE IF EXISTS dw.DimJobProfile;
SELECT
    CAST(job_profile_id  AS VARCHAR(10))  AS JobProfileID,
    CAST(job_family_code AS VARCHAR(5))   AS JobFamilyCode,
    CAST(job_family      AS VARCHAR(60))  AS JobFamily,
    CAST(job_title       AS VARCHAR(80))  AS JobTitle,
    CAST(job_level AS INT)                AS Grade,
    CAST(level_name      AS VARCHAR(40))  AS GradeLevel,
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
    CAST(action_reason  AS VARCHAR(40))                    AS ActionReason,
    CAST(position_id    AS VARCHAR(12))                    AS PositionID,
    CAST(department_id  AS VARCHAR(10))                    AS DepartmentID,
    CAST(location_id    AS VARCHAR(10))                    AS LocationID,
    CAST(job_profile_id AS VARCHAR(10))                    AS JobProfileID,
    CAST(job_level AS INT)                                 AS Grade,
    CAST(fte AS DECIMAL(4, 2))                             AS FTE,
    CAST(NULLIF(manager_worker_id, '') AS VARCHAR(12))     AS ManagerWorkerID,
    CAST(CASE WHEN is_people_manager IN ('True', 'true', '1') THEN 1 ELSE 0 END AS BIT) AS IsPeopleManager,
    CAST(NULLIF(leads_org_unit_id, '') AS VARCHAR(15))     AS LeadsOrgUnitID
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

DROP TABLE IF EXISTS dw.FactPerformanceReview;
SELECT
    CAST(review_id AS VARCHAR(12))     AS ReviewID,
    CAST(worker_id AS VARCHAR(12))     AS WorkerID,
    CAST(fiscal_year AS INT)           AS FiscalYear,
    CONVERT(DATE, review_date)         AS ReviewDate,
    CAST(rating AS VARCHAR(20))        AS Rating,
    CAST(bonus_pct AS FLOAT)           AS BonusPct
INTO dw.FactPerformanceReview
FROM raw.fact_performance_review;
GO

DROP TABLE IF EXISTS dw.FactBonusPayout;
SELECT
    CAST(bonus_id  AS VARCHAR(12))                     AS BonusID,
    CAST(worker_id AS VARCHAR(12))                     AS WorkerID,
    CAST(fiscal_year AS INT)                           AS FiscalYear,
    CONVERT(DATE, payout_date)                         AS PayoutDate,
    CAST(currency_code AS CHAR(3))                     AS CurrencyCode,
    CAST(base_salary_annual_local AS DECIMAL(18, 2))   AS BaseSalaryAnnualLocal,
    CAST(fte AS DECIMAL(4, 2))                         AS FTE,
    CAST(proration_factor AS DECIMAL(6, 4))            AS ProrationFactor,
    CAST(bonus_pct AS FLOAT)                           AS BonusPct,
    CAST(bonus_amount_local AS DECIMAL(18, 2))         AS BonusAmountLocal,
    CAST(payout_status AS VARCHAR(12))                 AS PayoutStatus
INTO dw.FactBonusPayout
FROM raw.fact_bonus_payout;
GO

/* ----------------------------------------------------------------- reference */
DROP TABLE IF EXISTS dw.RefFxRateDaily;
SELECT
    CAST(currency_code AS CHAR(3))    AS CurrencyCode,
    CONVERT(DATE, rate_date)          AS RateDate,
    CAST(usd_per_local AS FLOAT)      AS UsdPerLocal,
    CAST(source AS VARCHAR(60))       AS Source
INTO dw.RefFxRateDaily
FROM raw.ref_fx_rate_daily;
CREATE CLUSTERED INDEX CIX_RefFxRateDaily ON dw.RefFxRateDaily (CurrencyCode, RateDate);
GO

DROP TABLE IF EXISTS dw.RefFxRate;
SELECT
    CAST(m.currency_code AS CHAR(3))              AS CurrencyCode,
    CONVERT(DATE, m.rate_date)                    AS RateDate,
    CAST(m.usd_per_local AS FLOAT)                AS UsdPerLocalActual,
    CAST(c.usd_per_local AS FLOAT)                AS UsdPerLocalConstant,
    CAST(c.rate_set AS VARCHAR(40))               AS ConstantRateSet
INTO dw.RefFxRate
FROM raw.ref_fx_rate_monthly AS m
JOIN raw.ref_fx_rate_constant AS c ON c.currency_code = m.currency_code;
GO

DROP TABLE IF EXISTS dw.RefFringeRate;
SELECT
    CAST(country_code AS CHAR(2))                     AS CountryCode,
    CAST([year] AS INT)                               AS FringeYear,
    CONVERT(DATE, effective_start_date)               AS EffectiveStartDate,
    CONVERT(DATE, effective_end_date)                 AS EffectiveEndDate,
    CAST(social_contribution_rate  AS FLOAT)          AS SocialContributionRate,
    CAST(retirement_severance_rate AS FLOAT)          AS RetirementSeveranceRate,
    CAST(statutory_pay_rate        AS FLOAT)          AS StatutoryPayRate,
    CAST(employer_benefits_rate    AS FLOAT)          AS EmployerBenefitsRate,
    CAST(fringe_rate AS FLOAT)                        AS FringeRate,
    CAST(reference_salary_local AS DECIMAL(18, 2))    AS ReferenceSalaryLocal,
    CAST(CASE WHEN is_estimate IN ('True', 'true', '1') THEN 1 ELSE 0 END AS BIT) AS IsEstimate,
    CAST(NULLIF(method_note, '') AS VARCHAR(300))     AS MethodNote
INTO dw.RefFringeRate
FROM raw.ref_fringe_rate;
GO

DROP TABLE IF EXISTS dw.RefFringeSource;
SELECT
    CAST(country_code AS CHAR(2))      AS CountryCode,
    CAST([year] AS INT)                AS FringeYear,
    CAST(component AS VARCHAR(40))     AS Component,
    CAST(source_id AS VARCHAR(20))     AS SourceID,
    CAST(source_title AS VARCHAR(300)) AS SourceTitle,
    CAST(source_url AS VARCHAR(300))   AS SourceUrl
INTO dw.RefFringeSource
FROM raw.ref_fringe_source;
GO

DROP TABLE IF EXISTS dw.RefSalaryRange;
SELECT
    CAST(fiscal_year AS INT)                AS FiscalYear,
    CAST(job_level AS INT)                  AS Grade,
    CAST(country_code AS CHAR(2))           AS CountryCode,
    CAST(currency_code AS CHAR(3))          AS CurrencyCode,
    CAST(range_min AS DECIMAL(18, 2))       AS RangeMin,
    CAST(range_mid AS DECIMAL(18, 2))       AS RangeMid,
    CAST(range_max AS DECIMAL(18, 2))       AS RangeMax
INTO dw.RefSalaryRange
FROM raw.ref_salary_range;
GO

DROP TABLE IF EXISTS dw.RefJobLevelBaseSalary;
SELECT
    CAST(job_level AS INT)                              AS Grade,
    CAST(country_code AS CHAR(2))                       AS CountryCode,
    CAST(currency_code AS CHAR(3))                      AS CurrencyCode,
    CAST(base_salary_local AS DECIMAL(18, 2))           AS BaseSalaryLocal,
    CAST(base_salary_usd_at_reference AS DECIMAL(18, 2)) AS BaseSalaryUsdAtReference,
    CONVERT(DATE, fx_reference_date)                    AS FxReferenceDate
INTO dw.RefJobLevelBaseSalary
FROM raw.ref_job_level_base_salary;
GO

DROP TABLE IF EXISTS dw.RefTenureIncrease;
SELECT
    CAST(tenure_year_from AS INT)    AS TenureYearFrom,
    CAST(tenure_year_to AS INT)      AS TenureYearTo,
    CAST(increase_pct AS FLOAT)      AS IncreasePct
INTO dw.RefTenureIncrease
FROM raw.ref_tenure_increase;
GO

DROP TABLE IF EXISTS dw.RefPerformanceBonus;
SELECT
    CAST(rating AS VARCHAR(20))      AS Rating,
    CAST(bonus_pct AS FLOAT)         AS BonusPct,
    CAST(target_share AS FLOAT)      AS TargetShare
INTO dw.RefPerformanceBonus
FROM raw.ref_performance_bonus;
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

/* --------------------------------------------- compensation in USD as booked
   Each pay record valued at the FX rate of its posting (effective) date: the
   latest ECB rate on or before that day (OUTER APPLY TOP 1 is SQL Server's as-of
   join), and at the constant rate set. */
DROP TABLE IF EXISTS dw.CompensationHistoryUsd;
SELECT
    c.CompRecordID,
    c.WorkerID,
    c.EffectiveStartDate,
    c.EffectiveEndDateFilled,
    c.ActionReason,
    c.CurrencyCode,
    c.BaseSalaryAnnualLocal,
    fx.RateDate                                          AS PostingFxRateDate,
    fx.UsdPerLocal                                       AS PostingFxRate,
    k.UsdPerLocalConstant                                AS ConstantFxRate,
    c.BaseSalaryAnnualLocal * fx.UsdPerLocal             AS BaseSalaryAnnualUsdPosting,
    c.BaseSalaryAnnualLocal * k.UsdPerLocalConstant      AS BaseSalaryAnnualUsdConstant
INTO dw.CompensationHistoryUsd
FROM dw.FactCompensationHistory AS c
OUTER APPLY (
    SELECT TOP 1 d.RateDate, d.UsdPerLocal
    FROM dw.RefFxRateDaily AS d
    WHERE d.CurrencyCode = c.CurrencyCode AND d.RateDate <= c.EffectiveStartDate
    ORDER BY d.RateDate DESC
) AS fx
LEFT JOIN (SELECT DISTINCT CurrencyCode, UsdPerLocalConstant FROM dw.RefFxRate) AS k
       ON k.CurrencyCode = c.CurrencyCode;
CREATE CLUSTERED INDEX CIX_CompensationHistoryUsd ON dw.CompensationHistoryUsd (WorkerID, EffectiveStartDate);
GO

/* ------------------------------------------------- worker month-end snapshot
   One row per active worker per month-end: the job and pay records in effect on
   that date, with FX, fringe (by calendar year) and pay range attached. Pay
   measures are annualized run-rates (annual base x FTE), in USD at the month-end
   rate (nominal), at the posting-date rate (posting) and at the constant rate. */
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
    j.ManagerWorkerID,
    j.IsPeopleManager,
    j.LeadsOrgUnitID,
    c.CompRecordID,
    c.CurrencyCode,
    c.BaseSalaryAnnualLocal,
    c.EffectiveStartDate                                                         AS PayEffectiveDate,
    fx.UsdPerLocalActual                                                         AS FxRateActual,
    fx.UsdPerLocalConstant                                                       AS FxRateConstant,
    c.PostingFxRate                                                              AS FxRatePosting,
    fr.FringeYear,
    fr.FringeRate,
    rng.RangeMid                                                                 AS RangeMidLocal,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalActual                       AS BaseUsdNominal,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalConstant                     AS BaseUsdConstant,
    c.BaseSalaryAnnualLocal * j.FTE * c.PostingFxRate                            AS BaseUsdPosting,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalActual   * (1 + fr.FringeRate) AS LoadedUsdNominal,
    c.BaseSalaryAnnualLocal * j.FTE * fx.UsdPerLocalConstant * (1 + fr.FringeRate) AS LoadedUsdConstant,
    c.BaseSalaryAnnualLocal * j.FTE * c.PostingFxRate        * (1 + fr.FringeRate) AS LoadedUsdPosting,
    rng.RangeMid * j.FTE * fx.UsdPerLocalConstant                                AS RangeMidUsdConstant
INTO dw.WorkerMonthEndSnapshot
FROM dw.MonthEndCalendar AS cal
JOIN dw.DimWorker AS w
  ON w.OriginalHireDate <= cal.MonthEndDate
 AND (w.TerminationDate IS NULL OR w.TerminationDate >= cal.MonthEndDate)
JOIN dw.FactJobHistory AS j
  ON j.WorkerID = w.WorkerID
 AND cal.MonthEndDate BETWEEN j.EffectiveStartDate AND j.EffectiveEndDateFilled
LEFT JOIN dw.CompensationHistoryUsd AS c
  ON c.WorkerID = w.WorkerID
 AND cal.MonthEndDate BETWEEN c.EffectiveStartDate AND c.EffectiveEndDateFilled
LEFT JOIN dw.DimLocation   AS loc ON loc.LocationID  = j.LocationID
LEFT JOIN dw.DimJobProfile AS jp  ON jp.JobProfileID = j.JobProfileID
LEFT JOIN dw.RefFxRate     AS fx
  ON fx.CurrencyCode = c.CurrencyCode
 AND fx.RateDate     = cal.MonthEndDate
LEFT JOIN dw.RefFringeRate AS fr
  ON fr.CountryCode = loc.CountryCode
 AND fr.FringeYear  = YEAR(cal.MonthEndDate)
LEFT JOIN dw.RefSalaryRange AS rng
  ON rng.FiscalYear  = cal.FiscalYear
 AND rng.Grade       = j.Grade
 AND rng.CountryCode = loc.CountryCode;

ALTER TABLE dw.WorkerMonthEndSnapshot ALTER COLUMN WorkerID VARCHAR(12) NOT NULL;
ALTER TABLE dw.WorkerMonthEndSnapshot ALTER COLUMN MonthEndDate DATE NOT NULL;
ALTER TABLE dw.WorkerMonthEndSnapshot
    ADD CONSTRAINT PK_WorkerMonthEndSnapshot PRIMARY KEY CLUSTERED (MonthEndDate, WorkerID);
GO

/* ------------------------------------------------------ reporting chain
   Closure table: one row per worker per manager above them, at each fiscal
   year-end and the latest month-end (the DuckDB build keeps every month-end).
   hops = 1 is the direct manager, 2 the skip-level manager, and so on. */
DROP TABLE IF EXISTS dw.WorkerReportingChain;
WITH dates AS (
    SELECT MonthEndDate FROM dw.MonthEndCalendar
    WHERE IsFiscalYearEnd = 1 OR MonthEndDate = (SELECT MAX(MonthEndDate) FROM dw.MonthEndCalendar)
),
chain AS (
    SELECT s.MonthEndDate, s.WorkerID, s.ManagerWorkerID AS AncestorWorkerID, 1 AS Hops
    FROM dw.WorkerMonthEndSnapshot AS s
    JOIN dates AS d ON d.MonthEndDate = s.MonthEndDate
    WHERE s.ManagerWorkerID IS NOT NULL
    UNION ALL
    SELECT c.MonthEndDate, c.WorkerID, s.ManagerWorkerID, c.Hops + 1
    FROM chain AS c
    JOIN dw.WorkerMonthEndSnapshot AS s
      ON s.MonthEndDate = c.MonthEndDate AND s.WorkerID = c.AncestorWorkerID
    WHERE s.ManagerWorkerID IS NOT NULL AND c.Hops < 15
)
SELECT MonthEndDate, WorkerID, AncestorWorkerID, Hops
INTO dw.WorkerReportingChain
FROM chain
OPTION (MAXRECURSION 20);
CREATE CLUSTERED INDEX CIX_WorkerReportingChain ON dw.WorkerReportingChain (MonthEndDate, AncestorWorkerID, Hops);
GO

/* -------------------------------------------------------------------- summary */
SELECT 'dw.DimWorker' AS TableName, COUNT(*) AS RowsLoaded FROM dw.DimWorker
UNION ALL SELECT 'dw.FactJobHistory', COUNT(*) FROM dw.FactJobHistory
UNION ALL SELECT 'dw.FactCompensationHistory', COUNT(*) FROM dw.FactCompensationHistory
UNION ALL SELECT 'dw.FactPerformanceReview', COUNT(*) FROM dw.FactPerformanceReview
UNION ALL SELECT 'dw.FactBonusPayout', COUNT(*) FROM dw.FactBonusPayout
UNION ALL SELECT 'dw.MonthEndCalendar', COUNT(*) FROM dw.MonthEndCalendar
UNION ALL SELECT 'dw.WorkerMonthEndSnapshot', COUNT(*) FROM dw.WorkerMonthEndSnapshot
UNION ALL SELECT 'dw.WorkerReportingChain', COUNT(*) FROM dw.WorkerReportingChain;
GO
