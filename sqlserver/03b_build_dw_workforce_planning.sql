/*
  03b_build_dw_workforce_planning.sql
  Builds the seat (position) layer for the Workforce Planning case study, after
  03_build_dw.sql. Same rules as the DuckDB pipeline (sql/01_staging/stg_position*,
  sql/02_intermediate/int_position_*, int_seat_*, sql/03_marts/mart_plan_vs_actual):

    dimensions   DimCostCenter, DimPosition (SCD Type 2), DimCandidate
    facts        FactPositionAssignment, FactRequisition, FactWorkforcePlan,
                 FactCandidateStageEvent
    derived      PositionHistory          seat records with the start of the current status run
                 PositionMonthEndSnapshot seat x month-end (Filled seats = WorkerMonthEndSnapshot)
                 SeatFill                 one row per fill: prior incumbent, seat decision,
                                          level and location change, pay walk, reuse check
                 SeatVacancyChain         chains of internal moves set off by one vacancy
                 PlanVsActual             plan version x cost center x quarter, with actuals

  Dates: EffectiveEndDate / EndDate are inclusive, NULL while current; the *Filled
  columns replace NULL with 9999-12-31 so range joins use BETWEEN.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ------------------------------------------------------------------ dimensions */
DROP TABLE IF EXISTS dw.DimCostCenter;
SELECT
    CAST(cost_center_id         AS VARCHAR(16))   AS CostCenterID,
    CAST(cost_center_name       AS VARCHAR(100))  AS CostCenterName,
    CAST(department_id          AS VARCHAR(10))   AS DepartmentID,
    CAST(department_cost_center AS VARCHAR(10))   AS DepartmentCostCenter,
    CAST(country_code           AS CHAR(2))       AS CountryCode,
    CAST([function]             AS VARCHAR(60))   AS FunctionName
INTO dw.DimCostCenter
FROM raw.dim_cost_center;
GO

DROP TABLE IF EXISTS dw.DimPosition;
SELECT
    CAST(position_record_id AS VARCHAR(12))                AS PositionRecordID,
    CAST(position_id        AS VARCHAR(12))                AS PositionID,
    CONVERT(DATE, effective_start_date)                    AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))          AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')),
           CONVERT(DATE, '9999-12-31'))                    AS EffectiveEndDateFilled,
    CAST(change_reason  AS VARCHAR(40))                    AS ChangeReason,
    CAST(status         AS VARCHAR(12))                    AS Status,
    CAST(department_id  AS VARCHAR(10))                    AS DepartmentID,
    CAST(cost_center_id AS VARCHAR(16))                    AS CostCenterID,
    CAST(location_id    AS VARCHAR(10))                    AS LocationID,
    CAST(job_profile_id AS VARCHAR(10))                    AS JobProfileID,
    CAST(job_level AS INT)                                 AS Grade,
    CAST(fte AS DECIMAL(4, 2))                             AS FTE,
    CONVERT(DATE, created_date)                            AS CreatedDate,
    CAST(created_reason AS VARCHAR(20))                    AS CreatedReason
INTO dw.DimPosition
FROM raw.dim_position;
CREATE CLUSTERED INDEX CIX_DimPosition ON dw.DimPosition (PositionID, EffectiveStartDate);
GO

DROP TABLE IF EXISTS dw.DimCandidate;
SELECT
    CAST(candidate_id     AS VARCHAR(12))                  AS CandidateID,
    CAST(requisition_id   AS VARCHAR(12))                  AS RequisitionID,
    CAST(CASE WHEN is_internal IN ('True', 'true', '1') THEN 1 ELSE 0 END AS BIT) AS IsInternal,
    CAST(candidate_source AS VARCHAR(20))                  AS CandidateSource,
    CAST(NULLIF(worker_id, '') AS VARCHAR(12))             AS WorkerID,
    CAST(final_status     AS VARCHAR(12))                  AS FinalStatus
INTO dw.DimCandidate
FROM raw.dim_candidate;
GO

/* ----------------------------------------------------------------------- facts */
DROP TABLE IF EXISTS dw.FactPositionAssignment;
SELECT
    CAST(assignment_id  AS VARCHAR(12))                    AS AssignmentID,
    CAST(position_id    AS VARCHAR(12))                    AS PositionID,
    CAST(worker_id      AS VARCHAR(12))                    AS WorkerID,
    CONVERT(DATE, start_date)                              AS StartDate,
    CONVERT(DATE, NULLIF(end_date, ''))                    AS EndDate,
    ISNULL(CONVERT(DATE, NULLIF(end_date, '')),
           CONVERT(DATE, '9999-12-31'))                    AS EndDateFilled,
    CAST(fill_type      AS VARCHAR(20))                    AS FillType,
    CAST(NULLIF(requisition_id, '') AS VARCHAR(12))        AS RequisitionID,
    CAST(NULLIF(vacate_reason, '')  AS VARCHAR(20))        AS VacateReason
INTO dw.FactPositionAssignment
FROM raw.fact_position_assignment;
CREATE CLUSTERED INDEX CIX_FactPositionAssignment ON dw.FactPositionAssignment (PositionID, StartDate);
CREATE INDEX IX_FactPositionAssignment_Worker ON dw.FactPositionAssignment (WorkerID, StartDate) INCLUDE (EndDate, PositionID, FillType);
GO

DROP TABLE IF EXISTS dw.FactRequisition;
SELECT
    CAST(requisition_id AS VARCHAR(12))                    AS RequisitionID,
    CAST(position_id    AS VARCHAR(12))                    AS PositionID,
    CAST(req_type       AS VARCHAR(10))                    AS ReqType,
    CONVERT(DATE, opened_date)                             AS OpenedDate,
    CONVERT(DATE, approved_date)                           AS ApprovedDate,
    CONVERT(DATE, target_start_date)                       AS TargetStartDate,
    CONVERT(DATE, NULLIF(filled_date, ''))                 AS FilledDate,
    CONVERT(DATE, NULLIF(cancelled_date, ''))              AS CancelledDate,
    CAST(status         AS VARCHAR(12))                    AS Status,
    CAST(department_id  AS VARCHAR(10))                    AS DepartmentID,
    CAST(cost_center_id AS VARCHAR(16))                    AS CostCenterID,
    CAST(location_id    AS VARCHAR(10))                    AS LocationID,
    CAST(job_profile_id AS VARCHAR(10))                    AS JobProfileID,
    CAST(job_level AS INT)                                 AS Grade,
    CAST(NULLIF(hiring_manager_id, '')   AS VARCHAR(12))   AS HiringManagerID,
    CAST(NULLIF(filled_by_worker_id, '') AS VARCHAR(12))   AS FilledByWorkerID,
    CAST(NULLIF(fill_source, '')         AS VARCHAR(10))   AS FillSource
INTO dw.FactRequisition
FROM raw.fact_requisition;
ALTER TABLE dw.FactRequisition ALTER COLUMN RequisitionID VARCHAR(12) NOT NULL;
GO

ALTER TABLE dw.FactRequisition ADD CONSTRAINT PK_FactRequisition PRIMARY KEY (RequisitionID);
CREATE INDEX IX_FactRequisition_Position ON dw.FactRequisition (PositionID, OpenedDate);
GO

DROP TABLE IF EXISTS dw.FactWorkforcePlan;
SELECT
    CAST(plan_version   AS VARCHAR(16))                    AS PlanVersion,
    CAST(version_type   AS VARCHAR(8))                     AS VersionType,
    CONVERT(DATE, version_date)                            AS VersionDate,
    CAST(fiscal_year    AS INT)                            AS FiscalYear,
    CAST(fiscal_quarter AS INT)                            AS FiscalQuarter,
    CONVERT(DATE, quarter_end_date)                        AS QuarterEndDate,
    CAST(cost_center_id AS VARCHAR(16))                    AS CostCenterID,
    CAST(planned_ending_headcount AS INT)                  AS PlannedEndingHeadcount,
    CAST(planned_ending_fte AS DECIMAL(10, 2))             AS PlannedEndingFTE,
    CAST(planned_net_new AS INT)                           AS PlannedNetNew,
    CAST(planned_backfills AS INT)                         AS PlannedBackfills,
    CAST(planned_cost_usd AS DECIMAL(18, 2))               AS PlannedCostUsd,
    CONVERT(DATE, plan_fx_rate_date)                       AS PlanFxRateDate
INTO dw.FactWorkforcePlan
FROM raw.fact_workforce_plan;
CREATE CLUSTERED INDEX CIX_FactWorkforcePlan ON dw.FactWorkforcePlan (QuarterEndDate, CostCenterID, PlanVersion);
GO

DROP TABLE IF EXISTS dw.FactCandidateStageEvent;
SELECT
    CAST(candidate_event_id AS VARCHAR(12))                AS CandidateEventID,
    CAST(candidate_id       AS VARCHAR(12))                AS CandidateID,
    CAST(stage              AS VARCHAR(12))                AS Stage,
    CAST(stage_order AS INT)                               AS StageOrder,
    CONVERT(DATE, stage_date)                              AS StageDate
INTO dw.FactCandidateStageEvent
FROM raw.fact_candidate_stage_event;
CREATE CLUSTERED INDEX CIX_FactCandidateStageEvent ON dw.FactCandidateStageEvent (CandidateID, StageOrder);
GO

/* ------------------------------------------------------------ seat history
   Seat records with what the seat models need beside them: the start of the
   current status run (consecutive records with the same status), the office's
   country, currency and pay zone, the job family, and whether it is a manager seat. */
DROP TABLE IF EXISTS dw.PositionHistory;
WITH flagged AS (
    SELECT p.*,
           LAG(p.Status) OVER (PARTITION BY p.PositionID ORDER BY p.EffectiveStartDate) AS PrevStatus
    FROM dw.DimPosition AS p
),
runs AS (
    SELECT *,
           SUM(CASE WHEN Status = PrevStatus THEN 0 ELSE 1 END)
               OVER (PARTITION BY PositionID ORDER BY EffectiveStartDate ROWS UNBOUNDED PRECEDING) AS RunID
    FROM flagged
)
SELECT
    r.PositionRecordID,
    r.PositionID,
    r.EffectiveStartDate,
    r.EffectiveEndDate,
    r.EffectiveEndDateFilled,
    r.ChangeReason,
    r.Status,
    MIN(r.EffectiveStartDate) OVER (PARTITION BY r.PositionID, r.RunID)          AS StatusSince,
    r.DepartmentID,
    r.CostCenterID,
    r.LocationID,
    l.CountryCode,
    l.CurrencyCode,
    l.PayZoneFactor,
    r.JobProfileID,
    jp.JobFamilyCode,
    jp.JobFamily,
    r.Grade,
    CAST(CASE WHEN jp.CareerTrack <> 'Individual Contributor' THEN 1 ELSE 0 END AS BIT) AS IsManagerSeat,
    r.FTE,
    r.CreatedDate,
    r.CreatedReason
INTO dw.PositionHistory
FROM runs AS r
JOIN dw.DimLocation   AS l  ON l.LocationID    = r.LocationID
JOIN dw.DimJobProfile AS jp ON jp.JobProfileID = r.JobProfileID;
CREATE CLUSTERED INDEX CIX_PositionHistory ON dw.PositionHistory (PositionID, EffectiveStartDate);
CREATE INDEX IX_PositionHistory_Vacant ON dw.PositionHistory (DepartmentID, JobFamilyCode, CountryCode, Status)
    INCLUDE (EffectiveStartDate, EffectiveEndDateFilled, Grade, StatusSince);
GO

/* ------------------------------------------------- seat month-end snapshot
   One row per seat per month-end, every seat that exists and is not eliminated. */
DROP TABLE IF EXISTS dw.PositionMonthEndSnapshot;
SELECT
    c.MonthEndDate,
    c.FiscalYear,
    h.PositionID,
    h.Status,
    h.StatusSince,
    DATEDIFF(DAY, h.StatusSince, c.MonthEndDate) + 1      AS DaysInStatus,
    a.WorkerID                                            AS IncumbentWorkerID,
    h.DepartmentID,
    h.CostCenterID,
    h.LocationID,
    h.CountryCode,
    h.JobProfileID,
    h.JobFamilyCode,
    h.Grade,
    h.IsManagerSeat,
    h.FTE,
    h.CreatedDate,
    h.CreatedReason,
    q.RequisitionID                                       AS OpenRequisitionID
INTO dw.PositionMonthEndSnapshot
FROM dw.MonthEndCalendar AS c
JOIN dw.PositionHistory AS h
  ON c.MonthEndDate BETWEEN h.EffectiveStartDate AND h.EffectiveEndDateFilled
 AND h.Status <> 'Eliminated'
LEFT JOIN dw.FactPositionAssignment AS a
  ON a.PositionID = h.PositionID
 AND c.MonthEndDate BETWEEN a.StartDate AND a.EndDateFilled
LEFT JOIN dw.FactRequisition AS q
  ON q.PositionID = h.PositionID
 AND c.MonthEndDate >= q.OpenedDate
 AND c.MonthEndDate < COALESCE(q.FilledDate, q.CancelledDate, CONVERT(DATE, '9999-12-31'));
ALTER TABLE dw.PositionMonthEndSnapshot ALTER COLUMN PositionID VARCHAR(12) NOT NULL;
ALTER TABLE dw.PositionMonthEndSnapshot ALTER COLUMN MonthEndDate DATE NOT NULL;
GO

ALTER TABLE dw.PositionMonthEndSnapshot
    ADD CONSTRAINT PK_PositionMonthEndSnapshot PRIMARY KEY CLUSTERED (MonthEndDate, PositionID);
GO

/* ----------------------------------------------------------------- seat fills
   One row per fill (external hire or internal move) between the first and the last
   month-end. For a backfill: the seat as the prior incumbent left it beside the seat
   as filled, and a pay walk that adds up exactly (constant USD, annual base rate):
     new pay - prior pay = level + location + market + positioning
   with mid(grade, office, FY) = range midpoint x office pay zone, in constant USD.
   Pays and the level, location and market effects are rounded to the cent; positioning
   is what remains, so the walk adds up to the cent (as in the DuckDB pipeline).
   For a net-new seat: whether a seat it could have reused stood vacant 90+ days
   when it was approved (same department, job family, country; grade within one). */
DROP TABLE IF EXISTS #Fills;
WITH cal AS (
    SELECT MIN(MonthEndDate) AS FirstME, MAX(MonthEndDate) AS LastME FROM dw.MonthEndCalendar
),
seq AS (
    SELECT a.*,
           LAG(a.WorkerID)     OVER (PARTITION BY a.PositionID ORDER BY a.StartDate) AS PriorWorkerID,
           LAG(a.EndDate)      OVER (PARTITION BY a.PositionID ORDER BY a.StartDate) AS PriorEndDate,
           LAG(a.VacateReason) OVER (PARTITION BY a.PositionID ORDER BY a.StartDate) AS PriorVacateReason
    FROM dw.FactPositionAssignment AS a
)
SELECT s.*
INTO #Fills
FROM seq AS s
CROSS JOIN cal
WHERE s.FillType <> 'Initial'
  AND s.StartDate > cal.FirstME AND s.StartDate <= cal.LastME;
GO

DROP TABLE IF EXISTS #Base;
SELECT
    f.AssignmentID                                                   AS FillID,
    f.PositionID,
    f.WorkerID,
    f.StartDate                                                      AS FillDate,
    YEAR(f.StartDate) + CASE WHEN MONTH(f.StartDate) >= 7 THEN 1 ELSE 0 END AS FillFiscalYear,
    f.FillType,
    f.RequisitionID,
    CAST(CASE WHEN f.PriorWorkerID IS NULL THEN 'Net-new' ELSE 'Backfill' END AS VARCHAR(10)) AS SeatType,
    r.OpenedDate                                                     AS RequisitionOpenedDate,
    r.ApprovedDate                                                   AS RequisitionApprovedDate,
    DATEDIFF(DAY, r.ApprovedDate, f.StartDate)                       AS TimeToFillDays,
    f.PriorWorkerID,
    f.PriorEndDate,
    f.PriorVacateReason,
    YEAR(f.PriorEndDate) + CASE WHEN MONTH(f.PriorEndDate) >= 7 THEN 1 ELSE 0 END AS ExitFiscalYear,
    DATEDIFF(DAY, f.PriorEndDate, f.StartDate) - 1                   AS VacancyDays,
    ps.DepartmentID AS PriorDepartmentID, ps.CostCenterID AS PriorCostCenterID,
    ps.LocationID AS PriorLocationID, ps.CountryCode AS PriorCountryCode,
    ps.CurrencyCode AS PriorCurrencyCode, ps.PayZoneFactor AS PriorPayZone,
    ps.JobProfileID AS PriorJobProfileID, ps.JobFamilyCode AS PriorJobFamilyCode,
    ps.Grade AS PriorGrade, ps.IsManagerSeat AS PriorIsManagerSeat,
    ns.DepartmentID AS NewDepartmentID, ns.CostCenterID AS NewCostCenterID,
    ns.LocationID AS NewLocationID, ns.CountryCode AS NewCountryCode,
    ns.CurrencyCode AS NewCurrencyCode, ns.PayZoneFactor AS NewPayZone,
    ns.JobProfileID AS NewJobProfileID, ns.JobFamilyCode AS NewJobFamilyCode,
    ns.Grade AS NewGrade, ns.IsManagerSeat AS NewIsManagerSeat,
    ns.CreatedDate AS SeatCreatedDate, ns.CreatedReason AS SeatCreatedReason,
    fa.ChangeReason                                                  AS FirstChangeAfterVacate,
    CAST(CASE WHEN EXISTS (SELECT 1 FROM dw.PositionHistory AS h
                           WHERE h.PositionID = f.PositionID AND h.Status = 'Frozen'
                             AND h.EffectiveStartDate > f.PriorEndDate AND h.EffectiveStartDate < f.StartDate)
              THEN 1 ELSE 0 END AS BIT)                              AS WasFrozen,
    pc.BaseSalaryAnnualUsdConstant                                   AS PriorPayUsdConstant,
    nc.BaseSalaryAnnualUsdConstant                                   AS NewPayUsdConstant
INTO #Base
FROM #Fills AS f
JOIN dw.FactRequisition AS r ON r.RequisitionID = f.RequisitionID
JOIN dw.PositionHistory AS ns
  ON ns.PositionID = f.PositionID
 AND f.StartDate BETWEEN ns.EffectiveStartDate AND ns.EffectiveEndDateFilled
LEFT JOIN dw.PositionHistory AS ps
  ON ps.PositionID = f.PositionID
 AND f.PriorEndDate BETWEEN ps.EffectiveStartDate AND ps.EffectiveEndDateFilled
LEFT JOIN dw.PositionHistory AS fa
  ON fa.PositionID = f.PositionID
 AND fa.EffectiveStartDate = DATEADD(DAY, 1, f.PriorEndDate)
LEFT JOIN dw.CompensationHistoryUsd AS pc
  ON pc.WorkerID = f.PriorWorkerID
 AND f.PriorEndDate BETWEEN pc.EffectiveStartDate AND pc.EffectiveEndDateFilled
JOIN dw.CompensationHistoryUsd AS nc
  ON nc.WorkerID = f.WorkerID
 AND f.StartDate BETWEEN nc.EffectiveStartDate AND nc.EffectiveEndDateFilled;
GO

DROP TABLE IF EXISTS #Mids;
SELECT
    b.*,
    r1.RangeMid * b.PriorPayZone * k1.UsdPerLocalConstant AS MidPriorGradePriorOfficeExit,
    r2.RangeMid * b.PriorPayZone * k1.UsdPerLocalConstant AS MidNewGradePriorOfficeExit,
    r3.RangeMid * b.NewPayZone   * k2.UsdPerLocalConstant AS MidNewGradeNewOfficeExit,
    r4.RangeMid * b.NewPayZone   * k2.UsdPerLocalConstant AS MidNewGradeNewOfficeFill
INTO #Mids
FROM #Base AS b
LEFT JOIN (SELECT DISTINCT CurrencyCode, UsdPerLocalConstant FROM dw.RefFxRate) AS k1 ON k1.CurrencyCode = b.PriorCurrencyCode
LEFT JOIN (SELECT DISTINCT CurrencyCode, UsdPerLocalConstant FROM dw.RefFxRate) AS k2 ON k2.CurrencyCode = b.NewCurrencyCode
LEFT JOIN dw.RefSalaryRange AS r1
  ON r1.FiscalYear = b.ExitFiscalYear AND r1.Grade = b.PriorGrade AND r1.CountryCode = b.PriorCountryCode
LEFT JOIN dw.RefSalaryRange AS r2
  ON r2.FiscalYear = b.ExitFiscalYear AND r2.Grade = b.NewGrade AND r2.CountryCode = b.PriorCountryCode
LEFT JOIN dw.RefSalaryRange AS r3
  ON r3.FiscalYear = b.ExitFiscalYear AND r3.Grade = b.NewGrade AND r3.CountryCode = b.NewCountryCode
LEFT JOIN dw.RefSalaryRange AS r4
  ON r4.FiscalYear = b.FillFiscalYear AND r4.Grade = b.NewGrade AND r4.CountryCode = b.NewCountryCode;
GO

DROP TABLE IF EXISTS #Reuse;
WITH matches AS (
    SELECT
        m.FillID,
        h.PositionID      AS CandidatePositionID,
        h.StatusSince,
        ROW_NUMBER() OVER (PARTITION BY m.FillID ORDER BY h.StatusSince, h.PositionID) AS rn,
        COUNT(*)     OVER (PARTITION BY m.FillID)                                     AS n
    FROM #Mids AS m
    JOIN dw.PositionHistory AS h
      ON m.SeatType = 'Net-new'
     AND h.PositionID <> m.PositionID
     AND h.Status IN ('Open', 'Frozen')
     AND m.RequisitionApprovedDate BETWEEN h.EffectiveStartDate AND h.EffectiveEndDateFilled
     AND h.DepartmentID  = m.NewDepartmentID
     AND h.JobFamilyCode = m.NewJobFamilyCode
     AND h.CountryCode   = m.NewCountryCode
     AND ABS(h.Grade - m.NewGrade) <= 1
     AND h.StatusSince  <= DATEADD(DAY, -90, m.RequisitionApprovedDate)    /* reuse threshold */
)
SELECT FillID, n AS ReuseCandidateSeats, CandidatePositionID AS ReuseCandidatePositionID,
       StatusSince AS ReuseCandidateVacantSince
INTO #Reuse
FROM matches
WHERE rn = 1;
GO

DROP TABLE IF EXISTS dw.SeatFill;
SELECT
    m.FillID, m.PositionID, m.WorkerID, m.FillDate, m.FillFiscalYear, m.FillType, m.RequisitionID, m.SeatType,
    m.RequisitionOpenedDate, m.RequisitionApprovedDate, m.TimeToFillDays,
    m.PriorWorkerID, m.PriorEndDate, m.PriorVacateReason, m.ExitFiscalYear, m.VacancyDays,
    m.PriorDepartmentID, m.PriorCostCenterID, m.PriorLocationID, m.PriorCountryCode, m.PriorPayZone,
    m.PriorJobProfileID, m.PriorJobFamilyCode, m.PriorGrade, m.PriorIsManagerSeat,
    m.NewDepartmentID, m.NewCostCenterID, m.NewLocationID, m.NewCountryCode, m.NewPayZone,
    m.NewJobProfileID, m.NewJobFamilyCode, m.NewGrade, m.NewIsManagerSeat,
    m.SeatCreatedDate, m.SeatCreatedReason, m.FirstChangeAfterVacate, m.WasFrozen,
    w.PriorPayUsdConstant, w.NewPayUsdConstant,
    CAST(CASE WHEN m.SeatType = 'Net-new' THEN NULL
              WHEN m.NewGrade > m.PriorGrade THEN 'Up'
              WHEN m.NewGrade < m.PriorGrade THEN 'Down'
              ELSE 'Same' END AS VARCHAR(4))                                       AS LevelChange,
    CAST(CASE WHEN m.SeatType = 'Net-new' THEN NULL
              WHEN m.NewLocationID = m.PriorLocationID THEN 'Same office'
              WHEN m.NewCountryCode = m.PriorCountryCode THEN 'Other office, same country'
              ELSE 'Other country' END AS VARCHAR(30))                             AS LocationChange,
    CAST(CASE WHEN m.SeatType = 'Net-new' THEN NULL
              WHEN m.FirstChangeAfterVacate = 'Re-levelled for backfill' THEN 'Re-levelled'
              WHEN m.FirstChangeAfterVacate = 'Relocated for backfill'   THEN 'Relocated'
              WHEN m.FirstChangeAfterVacate = 'Frozen'                   THEN 'Frozen, then reopened'
              WHEN m.FirstChangeAfterVacate = 'Vacated' AND m.VacancyDays <= 1
                   AND m.RequisitionOpenedDate = m.RequisitionApprovedDate THEN 'Immediate refill'
              WHEN m.FirstChangeAfterVacate = 'Vacated'                  THEN 'Backfill as is'
              ELSE 'Immediate refill' END AS VARCHAR(30))                          AS SeatDecision,
    w.NewPayUsdConstant - w.PriorPayUsdConstant                                    AS PayChangeUsdConstant,
    w.LevelEffectUsdConstant,
    w.LocationEffectUsdConstant,
    w.MarketEffectUsdConstant,
    (w.NewPayUsdConstant - w.PriorPayUsdConstant) - w.LevelEffectUsdConstant
      - w.LocationEffectUsdConstant - w.MarketEffectUsdConstant                    AS PositioningEffectUsdConstant,
    CAST(CASE WHEN u.FillID IS NOT NULL THEN 1 ELSE 0 END AS BIT)                  AS ReuseCandidate,
    ISNULL(u.ReuseCandidateSeats, 0)                                               AS ReuseCandidateSeats,
    u.ReuseCandidatePositionID,
    u.ReuseCandidateVacantSince
INTO dw.SeatFill
FROM #Mids AS m
CROSS APPLY (
    SELECT
        CAST(ROUND(CAST(m.PriorPayUsdConstant AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS PriorPayUsdConstant,
        CAST(ROUND(CAST(m.NewPayUsdConstant   AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS NewPayUsdConstant,
        CAST(ROUND(CAST(m.MidNewGradePriorOfficeExit AS DECIMAL(38, 10))
                 - CAST(m.MidPriorGradePriorOfficeExit AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS LevelEffectUsdConstant,
        CAST(ROUND(CAST(m.MidNewGradeNewOfficeExit AS DECIMAL(38, 10))
                 - CAST(m.MidNewGradePriorOfficeExit AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS LocationEffectUsdConstant,
        CAST(ROUND(CAST(m.MidNewGradeNewOfficeFill AS DECIMAL(38, 10))
                 - CAST(m.MidNewGradeNewOfficeExit AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS MarketEffectUsdConstant
) AS w
LEFT JOIN #Reuse AS u ON u.FillID = m.FillID;
ALTER TABLE dw.SeatFill ALTER COLUMN FillID VARCHAR(12) NOT NULL;
GO

ALTER TABLE dw.SeatFill ADD CONSTRAINT PK_SeatFill PRIMARY KEY CLUSTERED (FillID);
CREATE INDEX IX_SeatFill_Worker ON dw.SeatFill (WorkerID, FillDate);
DROP TABLE IF EXISTS #Fills;
DROP TABLE IF EXISTS #Base;
DROP TABLE IF EXISTS #Mids;
DROP TABLE IF EXISTS #Reuse;
GO

/* --------------------------------------------------------- vacancy chains
   A fill's parent is the internal move that emptied its seat (the prior incumbent
   moved out the day before into another seat). A fill without a parent starts a
   chain; its trigger is why that seat was empty. */
DROP TABLE IF EXISTS dw.SeatVacancyChain;
WITH linked AS (
    SELECT f.FillID, f.SeatType, f.PriorVacateReason, p.FillID AS ParentFillID
    FROM dw.SeatFill AS f
    LEFT JOIN dw.SeatFill AS p
      ON f.PriorVacateReason = 'Internal Move Out'
     AND p.WorkerID = f.PriorWorkerID
     AND p.FillDate = DATEADD(DAY, 1, f.PriorEndDate)
),
chain AS (
    SELECT FillID, FillID AS ChainID, 1 AS ChainDepth,
           CAST(CASE WHEN SeatType = 'Net-new' THEN 'Net-new seat'
                     WHEN PriorVacateReason = 'Internal Move Out' THEN 'Internal move before history'
                     ELSE CONCAT(PriorVacateReason, ' exit') END AS VARCHAR(30)) AS ChainTrigger
    FROM linked
    WHERE ParentFillID IS NULL
    UNION ALL
    SELECT l.FillID, c.ChainID, c.ChainDepth + 1, c.ChainTrigger
    FROM linked AS l
    JOIN chain AS c ON l.ParentFillID = c.FillID
)
SELECT
    c.FillID,
    l.ParentFillID,
    c.ChainID,
    c.ChainDepth,
    MAX(c.ChainDepth) OVER (PARTITION BY c.ChainID) AS ChainLength,
    c.ChainTrigger
INTO dw.SeatVacancyChain
FROM chain AS c
JOIN linked AS l ON l.FillID = c.FillID
OPTION (MAXRECURSION 50);
CREATE CLUSTERED INDEX CIX_SeatVacancyChain ON dw.SeatVacancyChain (FillID);
GO

/* ------------------------------------------------------------- plan vs actual
   One row per plan version, cost center and quarter, with the actuals beside it.
   Cost is compared like for like: actual local run-rate converted at the plan's own
   FX rates (latest ECB rate on or before the version date). */
DROP TABLE IF EXISTS #Quarters;
SELECT FiscalYear, FiscalQuarter, MAX(MonthEndDate) AS QuarterEndDate, MAX(FiscalQuarterLabel) AS FiscalQuarterLabel
INTO #Quarters
FROM dw.MonthEndCalendar
GROUP BY FiscalYear, FiscalQuarter;

DROP TABLE IF EXISTS #People;
SELECT s.MonthEndDate AS QuarterEndDate,
       CAST(CONCAT(d.CostCenter, '-', s.CountryCode) AS VARCHAR(16))    AS CostCenterID,
       s.CurrencyCode,
       COUNT(*)                                                       AS Headcount,
       SUM(s.FTE)                                                     AS FTE,
       SUM(CAST(s.BaseSalaryAnnualLocal * s.FTE * (1 + s.FringeRate) AS DECIMAL(38, 10))) AS LoadedLocal,
       SUM(CAST(s.LoadedUsdConstant AS DECIMAL(38, 10)))              AS LoadedUsdConstant
INTO #People
FROM dw.WorkerMonthEndSnapshot AS s
JOIN dw.DimDepartment AS d ON d.DepartmentID = s.DepartmentID
WHERE s.MonthEndDate IN (SELECT QuarterEndDate FROM #Quarters)
GROUP BY s.MonthEndDate, CONCAT(d.CostCenter, '-', s.CountryCode), s.CurrencyCode;

DROP TABLE IF EXISTS #QFills;
SELECT q.QuarterEndDate, f.NewCostCenterID AS CostCenterID,
       SUM(CASE WHEN f.SeatType = 'Net-new'  THEN 1 ELSE 0 END)                         AS NetNew,
       SUM(CASE WHEN f.SeatType = 'Backfill' THEN 1 ELSE 0 END)                         AS Backfills,
       SUM(CASE WHEN f.SeatType = 'Net-new' AND f.ReuseCandidate = 1 THEN 1 ELSE 0 END) AS NetNewReuseCandidates,
       SUM(CASE WHEN f.FillType = 'External Hire' THEN 1 ELSE 0 END)                    AS ExternalHires,
       SUM(CASE WHEN f.FillType = 'Internal Move' THEN 1 ELSE 0 END)                    AS InternalMoves
INTO #QFills
FROM dw.SeatFill AS f
JOIN dw.MonthEndCalendar AS c ON c.MonthEndDate = EOMONTH(f.FillDate)
JOIN #Quarters AS q ON q.FiscalYear = c.FiscalYear AND q.FiscalQuarter = c.FiscalQuarter
GROUP BY q.QuarterEndDate, f.NewCostCenterID;

DROP TABLE IF EXISTS #CostAtPlanFx;
SELECT p.PlanVersion, p.CostCenterID, p.FiscalQuarter,
       SUM(CAST(pe.LoadedLocal * fx.UsdPerLocal AS DECIMAL(38, 10))) AS ActualCostUsdPlanFx
INTO #CostAtPlanFx
FROM dw.FactWorkforcePlan AS p
JOIN #People AS pe ON pe.QuarterEndDate = p.QuarterEndDate AND pe.CostCenterID = p.CostCenterID
OUTER APPLY (
    SELECT TOP 1 d.UsdPerLocal
    FROM dw.RefFxRateDaily AS d
    WHERE d.CurrencyCode = pe.CurrencyCode AND d.RateDate <= p.PlanFxRateDate
    ORDER BY d.RateDate DESC
) AS fx
GROUP BY p.PlanVersion, p.CostCenterID, p.FiscalQuarter;

DROP TABLE IF EXISTS dw.PlanVsActual;
SELECT
    p.PlanVersion,
    p.VersionType,
    CASE p.VersionType WHEN 'Budget' THEN 1 WHEN 'RF1' THEN 2 WHEN 'RF2' THEN 3 WHEN 'RF3' THEN 4 END AS VersionOrder,
    p.VersionDate,
    CAST(CASE WHEN p.FiscalQuarter = CASE p.VersionType WHEN 'Budget' THEN 1 WHEN 'RF1' THEN 2
                                                         WHEN 'RF2' THEN 3 WHEN 'RF3' THEN 4 END
              THEN 1 ELSE 0 END AS BIT)                    AS IsLatestVersion,
    p.FiscalYear,
    p.FiscalQuarter,
    q.FiscalQuarterLabel,
    p.QuarterEndDate,
    p.CostCenterID,
    p.PlannedEndingHeadcount,
    ISNULL(a.Headcount, 0)                                 AS ActualEndingHeadcount,
    p.PlannedEndingFTE,
    ISNULL(a.FTE, 0)                                       AS ActualEndingFTE,
    p.PlannedNetNew,
    ISNULL(f.NetNew, 0)                                    AS ActualNetNew,
    ISNULL(f.NetNewReuseCandidates, 0)                     AS ActualNetNewReuseCandidates,
    p.PlannedBackfills,
    ISNULL(f.Backfills, 0)                                 AS ActualBackfills,
    ISNULL(f.ExternalHires, 0)                             AS ActualExternalHires,
    ISNULL(f.InternalMoves, 0)                             AS ActualInternalMoves,
    p.PlannedCostUsd,
    CAST(ROUND(ISNULL(x.ActualCostUsdPlanFx, 0), 2) AS DECIMAL(18, 2)) AS ActualCostUsdPlanFx,
    CAST(ROUND(ISNULL(a.LoadedUsdConstant, 0), 2) AS DECIMAL(18, 2))   AS ActualCostUsdConstant,
    p.PlanFxRateDate
INTO dw.PlanVsActual
FROM dw.FactWorkforcePlan AS p
JOIN #Quarters AS q ON q.QuarterEndDate = p.QuarterEndDate
LEFT JOIN (SELECT QuarterEndDate, CostCenterID, SUM(Headcount) AS Headcount, SUM(FTE) AS FTE,
                  SUM(LoadedUsdConstant) AS LoadedUsdConstant
           FROM #People GROUP BY QuarterEndDate, CostCenterID) AS a
  ON a.QuarterEndDate = p.QuarterEndDate AND a.CostCenterID = p.CostCenterID
LEFT JOIN #QFills AS f ON f.QuarterEndDate = p.QuarterEndDate AND f.CostCenterID = p.CostCenterID
LEFT JOIN #CostAtPlanFx AS x
  ON x.PlanVersion = p.PlanVersion AND x.CostCenterID = p.CostCenterID AND x.FiscalQuarter = p.FiscalQuarter;
CREATE CLUSTERED INDEX CIX_PlanVsActual ON dw.PlanVsActual (FiscalYear, PlanVersion, CostCenterID, FiscalQuarter);
DROP TABLE IF EXISTS #Quarters;
DROP TABLE IF EXISTS #People;
DROP TABLE IF EXISTS #QFills;
DROP TABLE IF EXISTS #CostAtPlanFx;
GO

/* -------------------------------------------------------------------- summary */
SELECT 'dw.DimCostCenter' AS TableName, COUNT(*) AS RowsLoaded FROM dw.DimCostCenter
UNION ALL SELECT 'dw.DimPosition', COUNT(*) FROM dw.DimPosition
UNION ALL SELECT 'dw.FactPositionAssignment', COUNT(*) FROM dw.FactPositionAssignment
UNION ALL SELECT 'dw.FactRequisition', COUNT(*) FROM dw.FactRequisition
UNION ALL SELECT 'dw.FactWorkforcePlan', COUNT(*) FROM dw.FactWorkforcePlan
UNION ALL SELECT 'dw.DimCandidate', COUNT(*) FROM dw.DimCandidate
UNION ALL SELECT 'dw.FactCandidateStageEvent', COUNT(*) FROM dw.FactCandidateStageEvent
UNION ALL SELECT 'dw.PositionMonthEndSnapshot', COUNT(*) FROM dw.PositionMonthEndSnapshot
UNION ALL SELECT 'dw.SeatFill', COUNT(*) FROM dw.SeatFill
UNION ALL SELECT 'dw.SeatVacancyChain', COUNT(*) FROM dw.SeatVacancyChain
UNION ALL SELECT 'dw.PlanVsActual', COUNT(*) FROM dw.PlanVsActual;
GO
