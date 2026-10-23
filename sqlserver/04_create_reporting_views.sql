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
  rpt.vw_position_fill, rpt.vw_vacancy_pool, rpt.vw_plan_vs_actual, rpt.vw_seat_corridors,
  rpt.vw_pid_month_end, rpt.vw_cw_pid_fill
      Workforce Planning (seats, requisitions, plan). Same content as the marts of
      the same names in data/marts/; built on 03b_build_dw_workforce_planning.sql
      (the plan's contingent line, actual_cw_*, on 03c_build_dw_contingent.sql).

  The contingent workforce views (release 3) are in 04b_create_reporting_views_contingent.sql.

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
    NULLIF(CONCAT(mw.FirstName, ' ', mw.LastName), ' ') AS manager_name,  /* NULL for the CEO, as in the mart */
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

/* ------------------------------------------------- Workforce Planning (case study 1)
   Built on the seat tables from 03b_build_dw_workforce_planning.sql. Same columns as
   data/marts/mart_position_fill, mart_vacancy_pool, mart_plan_vs_actual and
   mart_seat_corridors. */
CREATE OR ALTER VIEW rpt.vw_position_fill AS
SELECT
    f.FillID                       AS fill_id,
    f.FillDate                     AS fill_date,
    f.FillFiscalYear               AS fiscal_year,
    cal.FiscalQuarterLabel         AS fiscal_quarter_label,
    cal.FiscalPeriod               AS fiscal_period,
    f.FillType                     AS fill_type,
    f.SeatType                     AS seat_type,
    f.SeatDecision                 AS seat_decision,
    f.WasFrozen                    AS was_frozen,
    f.RequisitionID                AS requisition_id,
    f.RequisitionOpenedDate        AS requisition_opened_date,
    f.RequisitionApprovedDate      AS requisition_approved_date,
    f.TimeToFillDays               AS time_to_fill_days,
    f.VacancyDays                  AS vacancy_days,
    f.PositionID                   AS position_id,
    f.SeatCreatedDate              AS seat_created_date,
    f.SeatCreatedReason            AS seat_created_reason,
    f.WorkerID                     AS worker_id,
    f.NewDepartmentID              AS department_id,
    nd.DepartmentName              AS department_name,
    nd.SubFunction                 AS sub_function,
    nd.FunctionName                AS function_name,
    f.NewCostCenterID              AS cost_center_id,
    f.NewLocationID                AS location_id,
    nl.OfficeName                  AS office_name,
    nl.City                        AS city,
    f.NewCountryCode               AS country_code,
    nl.CountryName                 AS country_name,
    nl.Region                      AS region,
    nl.Latitude                    AS latitude,
    nl.Longitude                   AS longitude,
    f.NewJobProfileID              AS job_profile_id,
    nj.JobTitle                    AS job_title,
    nj.JobFamily                   AS job_family,
    f.NewGrade                     AS grade,
    f.NewIsManagerSeat             AS is_manager_seat,
    f.PriorWorkerID                AS prior_worker_id,
    f.PriorEndDate                 AS prior_end_date,
    f.PriorVacateReason            AS prior_vacate_reason,
    f.PriorDepartmentID            AS prior_department_id,
    f.PriorLocationID              AS prior_location_id,
    pl.OfficeName                  AS prior_office_name,
    pl.City                        AS prior_city,
    f.PriorCountryCode             AS prior_country_code,
    pl.CountryName                 AS prior_country_name,
    pl.Latitude                    AS prior_latitude,
    pl.Longitude                   AS prior_longitude,
    f.PriorJobProfileID            AS prior_job_profile_id,
    pj.JobTitle                    AS prior_job_title,
    f.PriorGrade                   AS prior_grade,
    f.PriorIsManagerSeat           AS prior_is_manager_seat,
    f.LevelChange                  AS level_change,
    f.LocationChange               AS location_change,
    f.PriorPayUsdConstant          AS prior_pay_usd_constant,
    f.NewPayUsdConstant            AS new_pay_usd_constant,
    f.PayChangeUsdConstant         AS pay_change_usd_constant,
    f.LevelEffectUsdConstant       AS level_effect_usd_constant,
    f.LocationEffectUsdConstant    AS location_effect_usd_constant,
    f.MarketEffectUsdConstant      AS market_effect_usd_constant,
    f.PositioningEffectUsdConstant AS positioning_effect_usd_constant,
    f.ReuseCandidate               AS reuse_candidate,
    f.ReuseCandidateSeats          AS reuse_candidate_seats,
    f.ReuseCandidatePositionID     AS reuse_candidate_position_id,
    f.ReuseCandidateVacantSince    AS reuse_candidate_vacant_since,
    c.ChainID                      AS chain_id,
    c.ParentFillID                 AS parent_fill_id,
    c.ChainDepth                   AS chain_depth,
    c.ChainLength                  AS chain_length,
    c.ChainTrigger                 AS chain_trigger
FROM dw.SeatFill AS f
JOIN dw.SeatVacancyChain AS c  ON c.FillID = f.FillID
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = EOMONTH(f.FillDate)
JOIN dw.DimDepartment    AS nd ON nd.DepartmentID = f.NewDepartmentID
JOIN dw.DimLocation      AS nl ON nl.LocationID   = f.NewLocationID
JOIN dw.DimJobProfile    AS nj ON nj.JobProfileID = f.NewJobProfileID
LEFT JOIN dw.DimLocation   AS pl ON pl.LocationID   = f.PriorLocationID
LEFT JOIN dw.DimJobProfile AS pj ON pj.JobProfileID = f.PriorJobProfileID;
GO

CREATE OR ALTER VIEW rpt.vw_vacancy_pool AS
SELECT
    s.MonthEndDate                 AS month_end_date,
    s.FiscalYear                   AS fiscal_year,
    cal.FiscalQuarterLabel         AS fiscal_quarter_label,
    cal.IsFiscalYearEnd            AS is_fiscal_year_end,
    s.PositionID                   AS position_id,
    s.Status                       AS status,
    s.StatusSince                  AS status_since,
    s.DaysInStatus                 AS days_in_status,
    ISNULL(e.VacateReason, 'Never filled')                                       AS vacated_by,
    e.EndDate                      AS vacated_date,
    v.DaysVacant                   AS days_vacant,
    CASE WHEN v.DaysVacant <= 30  THEN '0-30 days'
         WHEN v.DaysVacant <= 90  THEN '31-90 days'
         WHEN v.DaysVacant <= 180 THEN '91-180 days'
         ELSE 'Over 180 days' END                                               AS vacancy_age_band,
    CAST(CASE WHEN v.DaysVacant >= 90 THEN 1 ELSE 0 END AS BIT)                 AS is_stale,
    s.OpenRequisitionID            AS open_requisition_id,
    q.ReqType                      AS req_type,
    q.ApprovedDate                 AS requisition_approved_date,
    s.DepartmentID                 AS department_id,
    d.DepartmentName               AS department_name,
    d.SubFunction                  AS sub_function,
    d.FunctionName                 AS function_name,
    s.CostCenterID                 AS cost_center_id,
    s.LocationID                   AS location_id,
    l.OfficeName                   AS office_name,
    s.CountryCode                  AS country_code,
    l.CountryName                  AS country_name,
    l.Region                       AS region,
    s.JobProfileID                 AS job_profile_id,
    jp.JobTitle                    AS job_title,
    jp.JobFamily                   AS job_family,
    s.Grade                        AS grade,
    s.IsManagerSeat                AS is_manager_seat,
    s.CreatedDate                  AS created_date,
    s.CreatedReason                AS created_reason,
    CAST('Employee' AS VARCHAR(10)) AS worker_type,
    CAST(NULL AS VARCHAR(12))      AS cw_type,
    CAST(NULL AS VARCHAR(30))      AS cw_role_family
FROM dw.PositionMonthEndSnapshot AS s
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
OUTER APPLY (   /* the most recent incumbent to leave the seat before the month-end */
    SELECT TOP 1 a.EndDate, a.VacateReason
    FROM dw.FactPositionAssignment AS a
    WHERE a.PositionID = s.PositionID AND a.EndDate < s.MonthEndDate
    ORDER BY a.EndDate DESC
) AS e
CROSS APPLY (
    SELECT DATEDIFF(DAY, ISNULL(DATEADD(DAY, 1, e.EndDate), s.CreatedDate), s.MonthEndDate) + 1 AS DaysVacant
) AS v
LEFT JOIN dw.FactRequisition AS q ON q.RequisitionID = s.OpenRequisitionID
JOIN dw.DimDepartment AS d  ON d.DepartmentID  = s.DepartmentID
JOIN dw.DimLocation   AS l  ON l.LocationID    = s.LocationID
JOIN dw.DimJobProfile AS jp ON jp.JobProfileID = s.JobProfileID
WHERE s.Status IN ('Open', 'Frozen')
UNION ALL
/* release 3.1: contingent PIDs, vacant from the end of the last assignment, or since they were
   created for a request that has not started ('Never filled'); no grade, job or requisition */
SELECT
    s.MonthEndDate, s.FiscalYear, cal.FiscalQuarterLabel, cal.IsFiscalYearEnd, s.PositionID, s.Status,
    s.StatusSince, s.DaysInStatus,
    ISNULL(e.VacateReason, 'Never filled'),
    e.EndDate,
    v.DaysVacant,
    CASE WHEN v.DaysVacant <= 30  THEN '0-30 days'
         WHEN v.DaysVacant <= 90  THEN '31-90 days'
         WHEN v.DaysVacant <= 180 THEN '91-180 days'
         ELSE 'Over 180 days' END,
    CAST(CASE WHEN v.DaysVacant >= 90 THEN 1 ELSE 0 END AS BIT),
    NULL, NULL, NULL,
    s.DepartmentID, d.DepartmentName, d.SubFunction, d.FunctionName, s.CostCenterID, s.LocationID,
    l.OfficeName, s.CountryCode, l.CountryName, l.Region,
    NULL, NULL, NULL, NULL, CAST(0 AS BIT),
    s.CreatedDate, s.CreatedReason,
    'Contingent', s.CwType, s.CwRoleFamily
FROM dw.ContingentPositionMonthEndSnapshot AS s
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
OUTER APPLY (
    SELECT TOP 1 a.EndDate, a.VacateReason
    FROM dw.FactContingentPositionAssignment AS a
    WHERE a.PositionID = s.PositionID AND a.EndDate < s.MonthEndDate
    ORDER BY a.EndDate DESC
) AS e
CROSS APPLY (
    SELECT DATEDIFF(DAY, ISNULL(DATEADD(DAY, 1, e.EndDate), s.CreatedDate), s.MonthEndDate) + 1 AS DaysVacant
) AS v
JOIN dw.DimDepartment AS d ON d.DepartmentID = s.DepartmentID
JOIN dw.DimLocation   AS l ON l.LocationID   = s.LocationID
WHERE s.Status = 'Open';
GO

/* release 3.1: the PID ledger, every PID on every month-end by worker type and kind */
CREATE OR ALTER VIEW rpt.vw_pid_month_end AS
SELECT x.month_end_date, x.worker_type, x.pid_kind, x.is_stale, x.department_id, x.country_name, COUNT(*) AS pids
FROM (
    SELECT s.MonthEndDate AS month_end_date, CAST('Employee' AS VARCHAR(10)) AS worker_type,
           CAST('Filled' AS VARCHAR(30)) AS pid_kind, CAST(0 AS BIT) AS is_stale,
           s.DepartmentID AS department_id, l.CountryName AS country_name
    FROM dw.PositionMonthEndSnapshot AS s
    JOIN dw.DimLocation AS l ON l.LocationID = s.LocationID
    WHERE s.Status = 'Filled'
    UNION ALL
    SELECT s.MonthEndDate, 'Contingent', 'Filled', CAST(0 AS BIT), s.DepartmentID, l.CountryName
    FROM dw.ContingentPositionMonthEndSnapshot AS s
    JOIN dw.DimLocation AS l ON l.LocationID = s.LocationID
    WHERE s.Status = 'Filled'
    UNION ALL
    SELECT v.month_end_date, v.worker_type,
           CASE WHEN v.vacated_by = 'Never filled' THEN 'Vacant new' ELSE 'Vacant previously held' END,
           v.is_stale, v.department_id, v.country_name
    FROM rpt.vw_vacancy_pool AS v
) AS x
GROUP BY x.month_end_date, x.worker_type, x.pid_kind, x.is_stale, x.department_id, x.country_name;
GO

/* release 3.1: every contingent assignment that starts in a PID, held before or new */
CREATE OR ALTER VIEW rpt.vw_cw_pid_fill AS
SELECT
    a.AssignmentID                 AS assignment_id,
    a.PositionID                   AS position_id,
    a.StartDate                    AS start_date,
    YEAR(a.StartDate) + CASE WHEN MONTH(a.StartDate) >= 7 THEN 1 ELSE 0 END AS fiscal_year,
    ((MONTH(a.StartDate) + 5) % 12) / 3 + 1                                  AS fiscal_quarter,
    CAST(CASE WHEN LAG(a.AssignmentID) OVER (PARTITION BY a.PositionID ORDER BY a.StartDate) IS NOT NULL
              THEN 1 ELSE 0 END AS BIT)                                       AS is_backfill,
    p.DepartmentID                 AS department_id,
    l.CountryName                  AS country_name
FROM dw.FactContingentPositionAssignment AS a
JOIN dw.DimContingentPosition AS p
  ON p.PositionID = a.PositionID AND a.StartDate BETWEEN p.EffectiveStartDate AND p.EffectiveEndDateFilled
JOIN dw.DimLocation AS l ON l.LocationID = p.LocationID;
GO

CREATE OR ALTER VIEW rpt.vw_plan_vs_actual AS
SELECT
    p.PlanVersion                  AS plan_version,
    p.VersionType                  AS version_type,
    p.VersionOrder                 AS version_order,
    p.VersionDate                  AS version_date,
    p.IsLatestVersion              AS is_latest_version,
    p.FiscalYear                   AS fiscal_year,
    p.FiscalQuarter                AS fiscal_quarter,
    p.FiscalQuarterLabel           AS fiscal_quarter_label,
    p.QuarterEndDate               AS quarter_end_date,
    p.CostCenterID                 AS cost_center_id,
    cc.CostCenterName              AS cost_center_name,
    cc.DepartmentID                AS department_id,
    d.DepartmentName               AS department_name,
    d.SubFunction                  AS sub_function,
    d.FunctionName                 AS function_name,
    cc.CountryCode                 AS country_code,
    c.CountryName                  AS country_name,
    c.Region                       AS region,
    p.PlannedEndingHeadcount       AS planned_ending_headcount,
    p.ActualEndingHeadcount        AS actual_ending_headcount,
    p.PlannedEndingFTE             AS planned_ending_fte,
    p.ActualEndingFTE              AS actual_ending_fte,
    p.PlannedNetNew                AS planned_net_new,
    p.ActualNetNew                 AS actual_net_new,
    p.ActualNetNewReuseCandidates  AS actual_net_new_reuse_candidates,
    p.PlannedBackfills             AS planned_backfills,
    p.ActualBackfills              AS actual_backfills,
    p.ActualExternalHires          AS actual_external_hires,
    p.ActualInternalMoves          AS actual_internal_moves,
    p.PlannedCostUsd               AS planned_cost_usd,
    p.ActualCostUsdPlanFx          AS actual_cost_usd_plan_fx,
    p.ActualCostUsdConstant        AS actual_cost_usd_constant,
    p.PlannedCwHeadcount           AS planned_cw_headcount,
    ISNULL(w.ActualCwHeadcount, 0) AS actual_cw_headcount,
    p.PlannedCwSpendUsd            AS planned_cw_spend_usd,
    CAST(ROUND(ISNULL(w.ActualCwSpendUsdPlanFx, 0), 2) AS DECIMAL(18, 2))   AS actual_cw_spend_usd_plan_fx,
    CAST(ROUND(ISNULL(w.ActualCwSpendUsdConstant, 0), 2) AS DECIMAL(18, 2)) AS actual_cw_spend_usd_constant,
    p.PlanFxRateDate               AS plan_fx_rate_date
FROM dw.PlanVsActual AS p
LEFT JOIN dw.CwPlanActual AS w
  ON w.PlanVersion = p.PlanVersion AND w.CostCenterID = p.CostCenterID AND w.FiscalQuarter = p.FiscalQuarter
JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = p.CostCenterID
JOIN dw.DimDepartment AS d  ON d.DepartmentID  = cc.DepartmentID
JOIN dw.DimCountry    AS c  ON c.CountryCode   = cc.CountryCode;
GO

CREATE OR ALTER VIEW rpt.vw_seat_corridors AS
SELECT
    f.FillFiscalYear               AS fiscal_year,
    cal.FiscalQuarterLabel         AS fiscal_quarter_label,
    f.LocationChange               AS location_change,
    f.PriorLocationID              AS from_location_id,
    fl.OfficeName                  AS from_office_name,
    fl.City                        AS from_city,
    fl.CountryCode                 AS from_country_code,
    fl.CountryName                 AS from_country_name,
    fl.Latitude                    AS from_latitude,
    fl.Longitude                   AS from_longitude,
    fl.PayZoneFactor               AS from_pay_zone,
    f.NewLocationID                AS to_location_id,
    tl.OfficeName                  AS to_office_name,
    tl.City                        AS to_city,
    tl.CountryCode                 AS to_country_code,
    tl.CountryName                 AS to_country_name,
    tl.Latitude                    AS to_latitude,
    tl.Longitude                   AS to_longitude,
    tl.PayZoneFactor               AS to_pay_zone,
    COUNT(*)                                                     AS seats,
    SUM(CASE WHEN f.LevelChange = 'Down' THEN 1 ELSE 0 END)      AS seats_levelled_down,
    SUM(CASE WHEN f.LevelChange = 'Up'   THEN 1 ELSE 0 END)      AS seats_levelled_up,
    SUM(CASE WHEN f.SeatDecision = 'Relocated' THEN 1 ELSE 0 END) AS seats_relocated_for_backfill,
    SUM(f.PayChangeUsdConstant)                                  AS pay_change_usd_constant,
    SUM(f.LocationEffectUsdConstant)                             AS location_effect_usd_constant
FROM dw.SeatFill AS f
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = EOMONTH(f.FillDate)
JOIN dw.DimLocation AS fl ON fl.LocationID = f.PriorLocationID
JOIN dw.DimLocation AS tl ON tl.LocationID = f.NewLocationID
WHERE f.SeatType = 'Backfill'
  AND f.LocationChange <> 'Same office'
GROUP BY f.FillFiscalYear, cal.FiscalQuarterLabel, f.LocationChange,
         f.PriorLocationID, fl.OfficeName, fl.City, fl.CountryCode, fl.CountryName, fl.Latitude, fl.Longitude, fl.PayZoneFactor,
         f.NewLocationID, tl.OfficeName, tl.City, tl.CountryCode, tl.CountryName, tl.Latitude, tl.Longitude, tl.PayZoneFactor;
GO

PRINT 'Created views rpt.vw_workforce_cost_snapshot, rpt.vw_org_leader_summary, rpt.vw_fringe_rate,';
PRINT '              rpt.vw_position_fill, rpt.vw_vacancy_pool, rpt.vw_plan_vs_actual, rpt.vw_seat_corridors';
GO
