/*
  04b_create_reporting_views_contingent.sql
  Release 3: reporting views for the contingent workforce, on 03c_build_dw_contingent.sql.
  Column names match the CSV marts in data/marts/, so a workbook built on SQL Server can be
  repointed to the CSVs (for Tableau Public) with Data > Replace Data Source.

  rpt.vw_cw_spend                     month x cost center x supplier x type x role family x currency:
                                      billed in the month beside the run-rate at the month-end
  rpt.vw_workforce_cost_growth_mix    year-over-year cost change in six factors, Shapley and sequential
  rpt.vw_cw_discrepancy_detail        case study 4: the work list (latest 13 month-ends)
  rpt.vw_cw_reconciliation            case study 4: the trend, beside the population each system shows
  rpt.vw_cw_engagement_cap            case study 4: engagements against the 48-month cap
  rpt.vw_cw_detection_score           case study 4: the rules scored against the answer key

  Checked row for row against the DuckDB marts by sqlserver/check_tsql_in_duckdb.py.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ------------------------------------------------------------------ contingent spend
   A month's billing is placed on the cost center and role of the revision in effect at the
   month-end (the order's last revision once it has ended; its first for work billed before a
   late approval). */
CREATE OR ALTER VIEW rpt.vw_cw_spend AS
WITH placed AS (
    SELECT t.*, o.SupplierID, w.CwType, r.CostCenterCode AS CostCenterID, r.RoleFamily
    FROM (
        SELECT t.TimesheetID, r.RevisionID,
               ROW_NUMBER() OVER (
                   PARTITION BY t.TimesheetID
                   ORDER BY CASE WHEN r.EffectiveStartDate <= t.MonthEndDate THEN 0 ELSE 1 END,
                            CASE WHEN r.EffectiveStartDate <= t.MonthEndDate THEN r.RevisionNo END DESC,
                            r.RevisionNo) AS rn
        FROM dw.BwTimesheetMonth AS t
        JOIN dw.BwServiceOrderRevision AS r ON r.ServiceOrderID = t.ServiceOrderID
    ) AS pick
    JOIN dw.BwTimesheetMonth AS t ON t.TimesheetID = pick.TimesheetID
    JOIN dw.BwServiceOrderRevision AS r ON r.RevisionID = pick.RevisionID
    JOIN dw.BwServiceOrder AS o ON o.ServiceOrderID = t.ServiceOrderID
    JOIN dw.BwContingentWorker AS w ON w.BwWorkerID = o.BwWorkerID
    WHERE pick.rn = 1
),
billed AS (
    SELECT p.MonthEndDate, p.CostCenterID, p.SupplierID, p.CwType, p.RoleFamily, p.BillingCurrency,
           COUNT(DISTINCT p.BwWorkerID)                                                 AS WorkersBilled,
           SUM(p.BilledHours)                                                           AS BilledHours,
           SUM(p.BilledUnits)                                                           AS BilledUnits,
           SUM(p.BilledAmountLocal)                                                     AS BilledAmountLocal,
           SUM(CAST(p.BilledAmountLocal * fx.UsdPerLocalActual AS DECIMAL(38, 10)))     AS BilledUsdNominal,
           SUM(CAST(p.BilledAmountLocal * fx.UsdPerLocalConstant AS DECIMAL(38, 10)))   AS BilledUsdConstant
    FROM placed AS p
    JOIN dw.RefFxRate AS fx ON fx.CurrencyCode = p.BillingCurrency AND fx.RateDate = p.MonthEndDate
    GROUP BY p.MonthEndDate, p.CostCenterID, p.SupplierID, p.CwType, p.RoleFamily, p.BillingCurrency
),
working AS (
    SELECT MonthEndDate, CostCenterID, SupplierID, CwType, RoleFamily, BillingCurrency,
           COUNT(*)                                                                     AS WorkersAtMonthEnd,
           SUM(CAST(RunRateLocal AS DECIMAL(38, 10)))                                   AS RunRateLocal,
           SUM(CAST(RunRateUsdNominal AS DECIMAL(38, 10)))                              AS RunRateUsdNominal,
           SUM(CAST(RunRateUsdConstant AS DECIMAL(38, 10)))                             AS RunRateUsdConstant
    FROM dw.CwMonthEndSnapshot
    GROUP BY MonthEndDate, CostCenterID, SupplierID, CwType, RoleFamily, BillingCurrency
),
keys AS (
    SELECT MonthEndDate, CostCenterID, SupplierID, CwType, RoleFamily, BillingCurrency FROM billed
    UNION
    SELECT MonthEndDate, CostCenterID, SupplierID, CwType, RoleFamily, BillingCurrency FROM working
)
SELECT
    k.MonthEndDate                                                                   AS month_end_date,
    cal.FiscalYear                                                                   AS fiscal_year,
    cal.FiscalQuarterLabel                                                           AS fiscal_quarter_label,
    k.CostCenterID                                                                   AS cost_center_id,
    cc.DepartmentID                                                                  AS department_id,
    cc.CountryCode                                                                   AS country_code,
    k.SupplierID                                                                     AS supplier_id,
    sp.SupplierName                                                                  AS supplier_name,
    k.CwType                                                                         AS cw_type,
    k.RoleFamily                                                                     AS role_family,
    k.BillingCurrency                                                                AS billing_currency,
    ISNULL(b.WorkersBilled, 0)                                                       AS workers_billed,
    CAST(ISNULL(b.BilledHours, 0) AS DECIMAL(18, 2))                                 AS billed_hours,
    CAST(ISNULL(b.BilledUnits, 0) AS DECIMAL(18, 4))                                 AS billed_units,
    CAST(ISNULL(b.BilledAmountLocal, 0) AS DECIMAL(18, 2))                           AS billed_amount_local,
    CAST(ROUND(ISNULL(b.BilledUsdNominal, 0), 2) AS DECIMAL(18, 2))                  AS billed_usd_nominal,
    CAST(ROUND(ISNULL(b.BilledUsdConstant, 0), 2) AS DECIMAL(18, 2))                 AS billed_usd_constant,
    ISNULL(w.WorkersAtMonthEnd, 0)                                                   AS workers_at_month_end,
    CAST(ROUND(ISNULL(w.RunRateLocal, 0), 2) AS DECIMAL(18, 2))                      AS run_rate_local,
    CAST(ROUND(ISNULL(w.RunRateUsdNominal, 0), 2) AS DECIMAL(18, 2))                 AS run_rate_usd_nominal,
    CAST(ROUND(ISNULL(w.RunRateUsdConstant, 0), 2) AS DECIMAL(18, 2))                AS run_rate_usd_constant
FROM keys AS k
LEFT JOIN billed AS b
  ON b.MonthEndDate = k.MonthEndDate AND b.CostCenterID = k.CostCenterID AND b.SupplierID = k.SupplierID
 AND b.CwType = k.CwType AND b.RoleFamily = k.RoleFamily AND b.BillingCurrency = k.BillingCurrency
LEFT JOIN working AS w
  ON w.MonthEndDate = k.MonthEndDate AND w.CostCenterID = k.CostCenterID AND w.SupplierID = k.SupplierID
 AND w.CwType = k.CwType AND w.RoleFamily = k.RoleFamily AND w.BillingCurrency = k.BillingCurrency
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = k.MonthEndDate
JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = k.CostCenterID
JOIN dw.BwSupplier AS sp ON sp.SupplierID = k.SupplierID;
GO

/* ------------------------------------------------------------------ growth mix
   Year-over-year total workforce cost (employees' loaded pay + contingent bill run-rate) split
   into volume, workforce mix, location mix, level mix, rate and currency, by Shapley values and
   sequentially. Precomputed in dw.WorkforceCostGrowthMix (03c_build_dw_contingent.sql).
   Methodology: docs/projects/workforce-cost-bridge/methodology.md */
CREATE OR ALTER VIEW rpt.vw_workforce_cost_growth_mix AS
SELECT
    g.FromMonthEnd                             AS from_month_end,
    g.ToMonthEnd                               AS to_month_end,
    g.FiscalYear                               AS fiscal_year,
    g.FiscalQuarterLabel                       AS fiscal_quarter_label,
    g.PairType                                 AS pair_type,
    g.ViewOrder                                AS view_order,
    g.ViewName                                 AS view_name,
    g.GroupName                                AS group_name,
    g.FactorOrder                              AS factor_order,
    g.Factor                                   AS factor,
    g.FactorMeaning                            AS factor_meaning,
    g.ShapleyEffectUsd                         AS shapley_effect_usd,
    g.SequentialEffectUsd                      AS sequential_effect_usd,
    g.OrderBiasUsd                             AS order_bias_usd,
    g.OpeningHeadcount                         AS opening_headcount,
    g.ClosingHeadcount                         AS closing_headcount
FROM dw.WorkforceCostGrowthMix AS g;
GO

/* ------------------------------------------------------------------ case study 4: the work list */
CREATE OR ALTER VIEW rpt.vw_cw_discrepancy_detail AS
SELECT
    d.MonthEndDate                                                       AS month_end_date,
    d.DiscrepancyCode                                                    AS discrepancy_code,
    t.DiscrepancyName                                                    AS discrepancy_name,
    t.Severity                                                           AS severity,
    t.WhoCanFixIt                                                        AS who_can_fix_it,
    d.RootCauseCode                                                      AS root_cause_code,
    rt.DiscrepancyName                                                   AS root_cause_name,
    d.IdentityID                                                         AS identity_id,
    d.BwWorkerID                                                         AS bw_worker_id,
    d.PersonID                                                           AS person_id,
    CASE WHEN i.FirstName IS NOT NULL AND i.LastName IS NOT NULL
         THEN CONCAT(i.FirstName, ' ', i.LastName) END                   AS worker_name,
    i.CwType                                                             AS cw_type,
    i.MatchConfidence                                                    AS match_confidence,
    s.SupplierName                                                       AS supplier_name,
    COALESCE(p.CostCenterID, oc.CostCenterID)                            AS cost_center_id,
    cc.DepartmentID                                                      AS department_id,
    dep.DepartmentName                                                   AS department_name,
    dep.FunctionName                                                     AS function_name,
    cc.CountryCode                                                       AS country_code,
    COALESCE(p.BwManagerWorkerID, p.KsManagerWorkerID)                   AS manager_worker_id,
    d.FieldsAffected                                                     AS fields_affected,
    d.SinceDate                                                          AS since_date,
    d.AgeDays                                                            AS age_days,
    CASE WHEN d.AgeDays <= 7 THEN '0-7 days' WHEN d.AgeDays <= 30 THEN '8-30 days'
         WHEN d.AgeDays <= 90 THEN '31-90 days' ELSE 'Over 90 days' END  AS age_band,
    d.ServiceOrderID                                                     AS service_order_id,
    d.FeedEventID                                                        AS feed_event_id,
    d.TimesheetID                                                        AS timesheet_id,
    d.Evidence                                                           AS evidence
FROM dw.CwDiscrepancy AS d
JOIN (SELECT MonthEndDate, ROW_NUMBER() OVER (ORDER BY MonthEndDate DESC) AS rn FROM dw.MonthEndCalendar) AS m
  ON m.MonthEndDate = d.MonthEndDate AND m.rn <= 13
JOIN dw.RefCwDiscrepancyType AS t ON t.DiscrepancyCode = d.DiscrepancyCode
LEFT JOIN dw.RefCwDiscrepancyType AS rt ON rt.DiscrepancyCode = d.RootCauseCode
LEFT JOIN dw.CwIdentityResolution AS i ON i.IdentityID = d.IdentityID
LEFT JOIN dw.BwSupplier AS s ON s.SupplierID = i.SupplierID
LEFT JOIN (SELECT MonthEndDate, IdentityID, COALESCE(BwCostCenterID, KsCostCenterID) AS CostCenterID,
                  BwManagerWorkerID, KsManagerWorkerID
           FROM dw.CwReconciliationSnapshot) AS p
  ON p.MonthEndDate = d.MonthEndDate AND p.IdentityID = d.IdentityID
LEFT JOIN (SELECT ServiceOrderID, CostCenterCode AS CostCenterID,
                  ROW_NUMBER() OVER (PARTITION BY ServiceOrderID ORDER BY RevisionNo DESC) AS rn
           FROM dw.BwServiceOrderRevision) AS oc
  ON oc.ServiceOrderID = d.ServiceOrderID AND oc.rn = 1
LEFT JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = COALESCE(p.CostCenterID, oc.CostCenterID)
LEFT JOIN dw.DimDepartment AS dep ON dep.DepartmentID = cc.DepartmentID;
GO

/* ------------------------------------------------------------------ case study 4: the trend
   Two row types, never summed together: 'Population' (month-end x function x supplier) and
   'Discrepancy' (month-end x function x supplier x type). */
CREATE OR ALTER VIEW rpt.vw_cw_reconciliation AS
WITH disc AS (
    SELECT x.MonthEndDate, x.DiscrepancyCode, x.IdentityID, x.SinceDate, x.AgeDays,
           COALESCE(sp.SupplierName, 'Unknown')                          AS SupplierName,
           COALESCE(dep.FunctionName, 'Unknown')                         AS FunctionName
    FROM dw.CwDiscrepancy AS x
    LEFT JOIN dw.CwIdentityResolution AS i ON i.IdentityID = x.IdentityID
    LEFT JOIN dw.BwSupplier AS sp ON sp.SupplierID = i.SupplierID
    LEFT JOIN dw.CwReconciliationSnapshot AS r ON r.MonthEndDate = x.MonthEndDate AND r.IdentityID = x.IdentityID
    LEFT JOIN (SELECT ServiceOrderID, CostCenterCode AS CostCenterID,
                      ROW_NUMBER() OVER (PARTITION BY ServiceOrderID ORDER BY RevisionNo DESC) AS rn
               FROM dw.BwServiceOrderRevision) AS oc ON oc.ServiceOrderID = x.ServiceOrderID AND oc.rn = 1
    LEFT JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = COALESCE(r.BwCostCenterID, r.KsCostCenterID, oc.CostCenterID)
    LEFT JOIN dw.DimDepartment AS dep ON dep.DepartmentID = cc.DepartmentID
),
flagged AS (    /* workers with at least one discrepancy beyond a change in transit */
    SELECT DISTINCT MonthEndDate, IdentityID FROM dw.CwDiscrepancy WHERE DiscrepancyCode <> 'CW00'
),
pop AS (
    SELECT r.MonthEndDate,
           COALESCE(dep.FunctionName, 'Unknown')                         AS FunctionName,
           COALESCE(sp.SupplierName, 'Unknown')                          AS SupplierName,
           SUM(CASE WHEN r.BwWorking = 1 THEN 1 ELSE 0 END)              AS CwWorkingBridgeway,
           SUM(CASE WHEN r.KsWorking = 1 THEN 1 ELSE 0 END)              AS CwWorkingKeystone,
           COUNT(DISTINCT f.IdentityID)                                  AS WorkersWithAnyDiscrepancy
    FROM dw.CwReconciliationSnapshot AS r
    LEFT JOIN flagged AS f ON f.MonthEndDate = r.MonthEndDate AND f.IdentityID = r.IdentityID
    LEFT JOIN dw.BwSupplier AS sp ON sp.SupplierID = r.SupplierID
    LEFT JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = COALESCE(r.BwCostCenterID, r.KsCostCenterID)
    LEFT JOIN dw.DimDepartment AS dep ON dep.DepartmentID = cc.DepartmentID
    GROUP BY r.MonthEndDate, COALESCE(dep.FunctionName, 'Unknown'), COALESCE(sp.SupplierName, 'Unknown')
)
SELECT p.MonthEndDate AS month_end_date, cal.FiscalYear AS fiscal_year, cal.FiscalQuarterLabel AS fiscal_quarter_label,
       'Population' AS row_type, p.FunctionName AS function_name, p.SupplierName AS supplier_name,
       CAST(NULL AS VARCHAR(12)) AS discrepancy_code, CAST(NULL AS VARCHAR(60)) AS discrepancy_name,
       CAST(NULL AS VARCHAR(20)) AS severity, CAST(NULL AS VARCHAR(80)) AS who_can_fix_it,
       p.CwWorkingBridgeway AS cw_working_bridgeway, p.CwWorkingKeystone AS cw_working_keystone,
       p.WorkersWithAnyDiscrepancy AS workers_with_any_discrepancy,
       CAST(NULL AS INT) AS workers_affected, CAST(NULL AS INT) AS new_this_month, CAST(NULL AS INT) AS aged_0_7,
       CAST(NULL AS INT) AS aged_8_30, CAST(NULL AS INT) AS aged_31_90, CAST(NULL AS INT) AS aged_over_90
FROM pop AS p JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = p.MonthEndDate
UNION ALL
SELECT x.MonthEndDate, cal.FiscalYear, cal.FiscalQuarterLabel, 'Discrepancy',
       x.FunctionName, x.SupplierName, x.DiscrepancyCode, t.DiscrepancyName, t.Severity, t.WhoCanFixIt,
       NULL, NULL, NULL,
       COUNT(DISTINCT x.IdentityID),
       COUNT(DISTINCT CASE WHEN x.SinceDate > DATEADD(MONTH, -1, cal.MonthEndDate) THEN x.IdentityID END),
       COUNT(DISTINCT CASE WHEN x.AgeDays <= 7 THEN x.IdentityID END),
       COUNT(DISTINCT CASE WHEN x.AgeDays BETWEEN 8 AND 30 THEN x.IdentityID END),
       COUNT(DISTINCT CASE WHEN x.AgeDays BETWEEN 31 AND 90 THEN x.IdentityID END),
       COUNT(DISTINCT CASE WHEN x.AgeDays > 90 THEN x.IdentityID END)
FROM disc AS x
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = x.MonthEndDate
JOIN dw.RefCwDiscrepancyType AS t ON t.DiscrepancyCode = x.DiscrepancyCode
GROUP BY x.MonthEndDate, cal.FiscalYear, cal.FiscalQuarterLabel, x.FunctionName, x.SupplierName,
         x.DiscrepancyCode, t.DiscrepancyName, t.Severity, t.WhoCanFixIt;
GO

/* ------------------------------------------------------------------ case study 4: the 48-month cap
   One row per Bridgeway worker who started, as Bridgeway holds it on the extract date. */
CREATE OR ALTER VIEW rpt.vw_cw_engagement_cap AS
WITH ext AS (SELECT MAX(MonthEndDate) AS ExtractDate FROM dw.MonthEndCalendar),
orders AS (
    SELECT o.BwWorkerID,
           SUM(CASE WHEN o.OrderType = 'Renewal' THEN 1 ELSE 0 END)     AS Renewals,
           MAX(r.AssignmentEndDate)                                      AS LastDay
    FROM dw.BwServiceOrder AS o
    JOIN dw.BwServiceOrderRevision AS r ON r.ServiceOrderID = o.ServiceOrderID AND r.IsCurrent = 1
    WHERE r.Status IN ('Approved', 'Closed')
    GROUP BY o.BwWorkerID
),
extensions AS (
    SELECT o.BwWorkerID, COUNT(*) AS Extensions,
           SUM(CASE WHEN r.RevisionReason = 'Early end' THEN 1 ELSE 0 END) AS EarlyEnds
    FROM dw.BwServiceOrder AS o
    JOIN dw.BwServiceOrderRevision AS r ON r.ServiceOrderID = o.ServiceOrderID
    WHERE r.RevisionReason IN ('Extension', 'Early end')
    GROUP BY o.BwWorkerID
),
base AS (
    SELECT w.*, e.ExtractDate, o.Renewals, o.LastDay,
           DATEADD(MONTH, 48, w.OriginalStartDate)                       AS CapStart,
           DATEADD(DAY, -1, DATEADD(MONTH, 48, w.OriginalStartDate))     AS CapDate
    FROM dw.BwContingentWorker AS w
    CROSS JOIN ext AS e
    JOIN orders AS o ON o.BwWorkerID = w.BwWorkerID
    WHERE w.OriginalStartDate IS NOT NULL
)
SELECT
    b.BwWorkerID                                                         AS bw_worker_id,
    i.IdentityID                                                         AS identity_id,
    i.PersonID                                                           AS person_id,
    CONCAT(b.FirstName, ' ', b.LastName)                                 AS worker_name,
    b.CwType                                                             AS cw_type,
    s.SupplierName                                                       AS supplier_name,
    b.OriginalStartDate                                                  AS original_start_date,
    b.LastDay                                                            AS last_day,
    CAST(CASE WHEN b.LastDay >= b.ExtractDate THEN 1 ELSE 0 END AS BIT)  AS is_working_at_extract,
    CASE WHEN c.WorkerID IS NOT NULL THEN 'Converted to employee'
         WHEN b.LastDay >= b.ExtractDate THEN 'Working'
         WHEN ISNULL(x.EarlyEnds, 0) > 0 THEN 'Ended early'
         ELSE 'Completed' END                                            AS engagement_status,
    DATEDIFF(MONTH, b.OriginalStartDate,
             DATEADD(DAY, 1, CASE WHEN b.LastDay < b.ExtractDate THEN b.LastDay ELSE b.ExtractDate END)) AS months_engaged,
    ISNULL(x.Extensions, 0) - ISNULL(x.EarlyEnds, 0)                     AS extensions,
    b.Renewals                                                           AS renewals,
    CASE WHEN b.CwType <> 'BPO' THEN b.CapDate END                       AS cap_date,
    CASE WHEN b.CwType <> 'BPO' AND b.LastDay >= b.ExtractDate
         THEN DATEDIFF(MONTH, b.ExtractDate, b.CapDate) END              AS months_left_at_extract,
    CAST(CASE WHEN b.CwType <> 'BPO' AND b.LastDay >= b.CapStart THEN 1 ELSE 0 END AS BIT) AS is_over_cap,
    CASE WHEN b.CwType = 'BPO' THEN 'No cap'
         WHEN b.LastDay >= b.CapStart THEN 'Over the cap'
         WHEN b.LastDay < b.ExtractDate THEN 'Ended within the cap'
         WHEN DATEDIFF(MONTH, b.ExtractDate, b.CapDate) < 6 THEN 'Under 6 months left'
         WHEN DATEDIFF(MONTH, b.ExtractDate, b.CapDate) < 12 THEN '6 to 12 months left'
         ELSE 'More than 12 months left' END                             AS cap_band
FROM base AS b
LEFT JOIN extensions AS x ON x.BwWorkerID = b.BwWorkerID
LEFT JOIN dw.BwSupplier AS s ON s.SupplierID = b.SupplierID
LEFT JOIN dw.CwIdentityResolution AS i ON i.BwWorkerID = b.BwWorkerID
LEFT JOIN dw.CwConversion AS c ON c.BwWorkerID = b.BwWorkerID;
GO

/* ------------------------------------------------------------------ case study 4: the score
   On each month-end a seeded discrepancy open that day is injected; detected when the rules flag
   the same type on the same worker that month-end; a flag with nothing seeded is a false flag.
   The only place the answer key is read. */
CREATE OR ALTER VIEW rpt.vw_cw_detection_score AS
WITH truth AS (
    SELECT DISTINCT me.MonthEndDate, t.DiscrepancyCode, COALESCE(t.BwWorkerID, t.PersonID) AS Who
    FROM dw.MonthEndCalendar AS me
    JOIN dw.GenCwDiscrepancyTruth AS t ON t.StartDate <= me.MonthEndDate AND t.EndDateFilled >= me.MonthEndDate
),
flags AS (
    SELECT DISTINCT MonthEndDate, DiscrepancyCode,
           CASE WHEN DiscrepancyCode = 'CW09' THEN PersonID ELSE BwWorkerID END AS Who
    FROM dw.CwDiscrepancy
),
scored AS (
    SELECT COALESCE(t.MonthEndDate, f.MonthEndDate)                     AS MonthEndDate,
           COALESCE(t.DiscrepancyCode, f.DiscrepancyCode)               AS DiscrepancyCode,
           CASE WHEN t.Who IS NOT NULL THEN 1 ELSE 0 END                AS Injected,
           CASE WHEN t.Who IS NOT NULL AND f.Who IS NOT NULL THEN 1 ELSE 0 END AS Detected,
           CASE WHEN t.Who IS NULL THEN 1 ELSE 0 END                    AS FalseFlag
    FROM truth AS t
    FULL OUTER JOIN flags AS f
      ON f.MonthEndDate = t.MonthEndDate AND f.DiscrepancyCode = t.DiscrepancyCode AND f.Who = t.Who
)
SELECT
    s.MonthEndDate                                                       AS month_end_date,
    cal.FiscalYear                                                       AS fiscal_year,
    s.DiscrepancyCode                                                    AS discrepancy_code,
    ty.DiscrepancyName                                                   AS discrepancy_name,
    ty.Severity                                                          AS severity,
    SUM(s.Injected)                                                      AS injected,
    SUM(s.Detected)                                                      AS detected,
    SUM(s.Injected - s.Detected)                                         AS missed,
    SUM(s.FalseFlag)                                                     AS false_flags,
    ROUND(CAST(SUM(s.Detected) AS FLOAT) / NULLIF(SUM(s.Injected), 0), 4)                 AS recall,
    ROUND(CAST(SUM(s.Detected) AS FLOAT) / NULLIF(SUM(s.Detected) + SUM(s.FalseFlag), 0), 4) AS [precision]
FROM scored AS s
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
LEFT JOIN dw.RefCwDiscrepancyType AS ty ON ty.DiscrepancyCode = s.DiscrepancyCode
GROUP BY s.MonthEndDate, cal.FiscalYear, s.DiscrepancyCode, ty.DiscrepancyName, ty.Severity;
GO
