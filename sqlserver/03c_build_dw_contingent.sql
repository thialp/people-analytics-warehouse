/*
  03c_build_dw_contingent.sql
  Release 3: the contingent workforce in the SQL Server warehouse. Runs after 03 and 03b.
  The T-SQL twin of the DuckDB models in sql/01_staging (bw_, ks_, feed_, gen_ tables) and
  sql/02_intermediate (int_cw_*); checked row for row against the DuckDB marts by
  sqlserver/check_tsql_in_duckdb.py, and on SQL Server by 12_validate_contingent_workforce.sql.

    Bridgeway VMS   BwSupplier, BwContingentWorker, BwServiceOrder, BwServiceOrderRevision,
                    BwTimesheetMonth
    Keystone HR     KsContingentWorker
    Integration     FeedBridgewayKeystoneEvent
    Catalogue       RefCwDiscrepancyType
    Answer key      GenCwDiscrepancyTruth (a test fixture: only the detection score reads it)
    derived         CwMonthEndSnapshot      contingent workers working on each month-end, as
                                            Bridgeway held it that day, with run-rates
                    CwConversion            contingent workers hired as employees, linked
                    CwMovement              contingent starts, ends, moves and conversions
                    CwSupplierAlias         Keystone's supplier spellings -> Bridgeway suppliers
                    CwIdentityResolution    Keystone people matched to Bridgeway workers
                    CwReconciliationSnapshot  what Keystone should hold beside what it holds
                    CwDiscrepancy           the discrepancies, found from the two systems alone

  Dates: EffectiveEndDate is inclusive and NULL while current; *Filled replaces NULL with
  9999-12-31 for range joins. Flags are BIT (0/1).
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ------------------------------------------------------------------ Bridgeway VMS */
DROP TABLE IF EXISTS dw.BwSupplier;
SELECT
    CAST(supplier_id      AS VARCHAR(10))                  AS SupplierID,
    CAST(supplier_name    AS VARCHAR(60))                  AS SupplierName,
    CAST(cw_types_offered AS VARCHAR(40))                  AS CwTypesOffered,
    CAST(hq_country_code  AS CHAR(2))                      AS HqCountryCode,
    CONVERT(DATE, onboarded_date)                          AS OnboardedDate,
    CAST(CASE WHEN is_active IN ('True', 'true', '1') THEN 1 ELSE 0 END AS BIT) AS IsActive
INTO dw.BwSupplier
FROM raw.bw_supplier;
GO

DROP TABLE IF EXISTS dw.BwContingentWorker;
SELECT
    CAST(bw_worker_id AS VARCHAR(12))                      AS BwWorkerID,
    CAST(first_name   AS VARCHAR(40))                      AS FirstName,
    CAST(last_name    AS VARCHAR(40))                      AS LastName,
    CAST(email        AS VARCHAR(80))                      AS Email,
    CAST(supplier_id  AS VARCHAR(10))                      AS SupplierID,
    CAST(cw_type      AS VARCHAR(12))                      AS CwType,
    CONVERT(DATE, NULLIF(original_start_date, ''))         AS OriginalStartDate,
    CONVERT(DATE, created_date)                            AS CreatedDate
INTO dw.BwContingentWorker
FROM raw.bw_contingent_worker;
CREATE CLUSTERED INDEX CIX_BwContingentWorker ON dw.BwContingentWorker (BwWorkerID);
GO

DROP TABLE IF EXISTS dw.BwServiceOrder;
SELECT
    CAST(service_order_id AS VARCHAR(12))                  AS ServiceOrderID,
    CAST(bw_worker_id     AS VARCHAR(12))                  AS BwWorkerID,
    CAST(supplier_id      AS VARCHAR(10))                  AS SupplierID,
    CAST(order_type       AS VARCHAR(20))                  AS OrderType,
    CAST(NULLIF(renews_service_order_id, '') AS VARCHAR(12)) AS RenewsServiceOrderID,
    CONVERT(DATE, opened_date)                             AS OpenedDate,
    CONVERT(DATE, submitted_date)                          AS SubmittedDate,
    CONVERT(DATE, NULLIF(approved_date, ''))               AS ApprovedDate,
    CAST(final_status     AS VARCHAR(20))                  AS FinalStatus
INTO dw.BwServiceOrder
FROM raw.bw_service_order;
CREATE CLUSTERED INDEX CIX_BwServiceOrder ON dw.BwServiceOrder (ServiceOrderID);
GO

DROP TABLE IF EXISTS dw.BwServiceOrderRevision;
SELECT
    CAST(revision_id      AS VARCHAR(12))                  AS RevisionID,
    CAST(service_order_id AS VARCHAR(12))                  AS ServiceOrderID,
    CAST(revision_no      AS INT)                          AS RevisionNo,
    CAST(revision_reason  AS VARCHAR(20))                  AS RevisionReason,
    CONVERT(DATE, effective_start_date)                    AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))          AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')), CONVERT(DATE, '9999-12-31')) AS EffectiveEndDateFilled,
    CAST(CASE WHEN is_current IN ('True', 'true', '1') THEN 1 ELSE 0 END AS BIT) AS IsCurrent,
    CAST(status           AS VARCHAR(20))                  AS Status,
    CONVERT(DATE, assignment_start_date)                   AS AssignmentStartDate,
    CONVERT(DATE, assignment_end_date)                     AS AssignmentEndDate,
    CONVERT(DATE, NULLIF(closed_date, ''))                 AS ClosedDate,
    CAST(role_family      AS VARCHAR(30))                  AS RoleFamily,
    CAST(seniority        AS VARCHAR(10))                  AS Seniority,
    CAST(job_title        AS VARCHAR(60))                  AS JobTitle,
    CAST(cost_center_code AS VARCHAR(16))                  AS CostCenterCode,
    CAST(NULLIF(hiring_manager_email, '') AS VARCHAR(80))  AS HiringManagerEmail,
    CAST(office_code      AS VARCHAR(10))                  AS OfficeCode,
    CAST(NULLIF(bill_rate, '') AS DECIMAL(18, 4))          AS BillRate,
    CAST(NULLIF(rate_type, '') AS VARCHAR(10))             AS RateType,
    CAST(NULLIF(billing_currency, '') AS CHAR(3))          AS BillingCurrency,
    CAST(NULLIF(hours_per_week, '') AS DECIMAL(9, 2))      AS HoursPerWeek
INTO dw.BwServiceOrderRevision
FROM raw.bw_service_order_revision;
CREATE CLUSTERED INDEX CIX_BwServiceOrderRevision ON dw.BwServiceOrderRevision (ServiceOrderID, RevisionNo);
GO

DROP TABLE IF EXISTS dw.BwTimesheetMonth;
SELECT
    CAST(timesheet_id     AS VARCHAR(12))                  AS TimesheetID,
    CAST(bw_worker_id     AS VARCHAR(12))                  AS BwWorkerID,
    CAST(service_order_id AS VARCHAR(12))                  AS ServiceOrderID,
    CONVERT(DATE, month_end_date)                          AS MonthEndDate,
    CAST(billed_hours     AS DECIMAL(9, 2))                AS BilledHours,
    CAST(billed_units     AS DECIMAL(12, 4))               AS BilledUnits,
    CAST(bill_rate        AS DECIMAL(18, 4))               AS BillRate,
    CAST(billing_currency AS CHAR(3))                      AS BillingCurrency,
    CAST(billed_amount_local AS DECIMAL(18, 4))            AS BilledAmountLocal
INTO dw.BwTimesheetMonth
FROM raw.bw_timesheet_month;
CREATE CLUSTERED INDEX CIX_BwTimesheetMonth ON dw.BwTimesheetMonth (ServiceOrderID, MonthEndDate);
GO

/* ------------------------------------------------------------------ Keystone HR, the feed, the catalogue */
DROP TABLE IF EXISTS dw.KsContingentWorker;
SELECT
    CAST(ks_record_id     AS VARCHAR(12))                  AS KsRecordID,
    CAST(person_id        AS VARCHAR(12))                  AS PersonID,
    CAST(NULLIF(bw_worker_id, '') AS VARCHAR(12))          AS BwWorkerID,
    CONVERT(DATE, effective_start_date)                    AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))          AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')), CONVERT(DATE, '9999-12-31')) AS EffectiveEndDateFilled,
    CAST(change_source    AS VARCHAR(10))                  AS ChangeSource,
    CAST(NULLIF(feed_event_id, '') AS VARCHAR(12))         AS FeedEventID,
    CAST(first_name       AS VARCHAR(40))                  AS FirstName,
    CAST(last_name        AS VARCHAR(40))                  AS LastName,
    CAST(cw_type          AS VARCHAR(12))                  AS CwType,
    CAST(supplier_name    AS VARCHAR(60))                  AS SupplierName,
    CAST(status           AS VARCHAR(10))                  AS Status,
    CONVERT(DATE, contract_start_date)                     AS ContractStartDate,
    CONVERT(DATE, contract_end_date)                       AS ContractEndDate,
    CAST(NULLIF(inactive_reason, '') AS VARCHAR(30))       AS InactiveReason,
    CAST(NULLIF(converted_to_worker_id, '') AS VARCHAR(12)) AS ConvertedToWorkerID,
    CAST(department_id    AS VARCHAR(10))                  AS DepartmentID,
    CAST(cost_center_id   AS VARCHAR(16))                  AS CostCenterID,
    CAST(location_id      AS VARCHAR(10))                  AS LocationID,
    CAST(manager_worker_id AS VARCHAR(12))                 AS ManagerWorkerID
INTO dw.KsContingentWorker
FROM raw.ks_contingent_worker;
CREATE CLUSTERED INDEX CIX_KsContingentWorker ON dw.KsContingentWorker (PersonID, EffectiveStartDate);
GO

DROP TABLE IF EXISTS dw.FeedBridgewayKeystoneEvent;
SELECT
    CAST(feed_event_id AS VARCHAR(12))                     AS FeedEventID,
    CAST(revision_id   AS VARCHAR(12))                     AS RevisionID,
    CAST(bw_worker_id  AS VARCHAR(12))                     AS BwWorkerID,
    CAST(event_type    AS VARCHAR(20))                     AS EventType,
    CONVERT(DATE, sent_date)                               AS SentDate,
    CONVERT(DATE, NULLIF(applied_date, ''))                AS AppliedDate,
    CAST(outcome       AS VARCHAR(20))                     AS Outcome,
    CAST(NULLIF(error_text, '') AS VARCHAR(120))           AS ErrorText
INTO dw.FeedBridgewayKeystoneEvent
FROM raw.feed_bridgeway_keystone_event;
CREATE CLUSTERED INDEX CIX_FeedBridgewayKeystoneEvent ON dw.FeedBridgewayKeystoneEvent (BwWorkerID, SentDate);
GO

DROP TABLE IF EXISTS dw.RefCwDiscrepancyType;
SELECT
    CAST(discrepancy_code    AS VARCHAR(12))               AS DiscrepancyCode,
    CAST(discrepancy_name    AS VARCHAR(60))               AS DiscrepancyName,
    CAST(what_happened       AS VARCHAR(200))              AS WhatHappened,
    CAST(what_a_manager_sees AS VARCHAR(200))              AS WhatAManagerSees,
    CAST(who_can_fix_it      AS VARCHAR(80))               AS WhoCanFixIt,
    CAST(severity            AS VARCHAR(20))               AS Severity
INTO dw.RefCwDiscrepancyType
FROM raw.ref_cw_discrepancy_type;
GO

DROP TABLE IF EXISTS dw.GenCwDiscrepancyTruth;
SELECT
    CAST(discrepancy_id   AS VARCHAR(12))                  AS DiscrepancyID,
    CAST(discrepancy_code AS VARCHAR(12))                  AS DiscrepancyCode,
    CAST(root_cause_code  AS VARCHAR(12))                  AS RootCauseCode,
    CAST(NULLIF(bw_worker_id, '') AS VARCHAR(12))          AS BwWorkerID,
    CAST(NULLIF(person_id, '') AS VARCHAR(12))             AS PersonID,
    CAST(NULLIF(service_order_id, '') AS VARCHAR(12))      AS ServiceOrderID,
    CAST(NULLIF(feed_event_id, '') AS VARCHAR(12))         AS FeedEventID,
    CAST(NULLIF(timesheet_id, '') AS VARCHAR(12))          AS TimesheetID,
    CAST(NULLIF(fields_affected, '') AS VARCHAR(120))      AS FieldsAffected,
    CONVERT(DATE, start_date)                              AS StartDate,
    CONVERT(DATE, NULLIF(end_date, ''))                    AS EndDate,
    ISNULL(CONVERT(DATE, NULLIF(end_date, '')), CONVERT(DATE, '9999-12-31')) AS EndDateFilled,
    CAST(resolution       AS VARCHAR(60))                  AS Resolution,
    CAST(NULLIF(detail, '') AS VARCHAR(300))               AS Detail
INTO dw.GenCwDiscrepancyTruth
FROM raw.gen_cw_discrepancy_truth;
GO

/* ------------------------------------------------------------------ contingent workers on each month-end
   As Bridgeway held it that day: the service order revision in effect on the month-end says the
   assignment has started and not ended (history is never restated). Run-rate = hourly rate x
   contracted hours x 52, or monthly rate x 12, in USD at the month-end and constant rates. */
DROP TABLE IF EXISTS dw.CwMonthEndSnapshot;
SELECT
    cal.MonthEndDate,
    cal.FiscalYear,
    o.BwWorkerID,
    r.ServiceOrderID,
    r.RevisionID,
    w.CwType,
    o.SupplierID,
    cc.DepartmentID,
    cc.CountryCode,
    r.CostCenterCode                                                     AS CostCenterID,
    r.OfficeCode                                                         AS LocationID,
    r.RoleFamily,
    r.Seniority,
    r.AssignmentStartDate,
    r.AssignmentEndDate,
    r.RateType,
    r.BillRate,
    r.BillingCurrency,
    r.HoursPerWeek,
    CASE WHEN r.RateType = 'Monthly' THEN r.BillRate * 12 ELSE r.BillRate * r.HoursPerWeek * 52 END AS RunRateLocal,
    fx.UsdPerLocalActual                                                 AS FxRateActual,
    fx.UsdPerLocalConstant                                               AS FxRateConstant,
    CAST(CASE WHEN r.RateType = 'Monthly' THEN r.BillRate * 12 ELSE r.BillRate * r.HoursPerWeek * 52 END AS FLOAT)
        * fx.UsdPerLocalActual                                           AS RunRateUsdNominal,
    CAST(CASE WHEN r.RateType = 'Monthly' THEN r.BillRate * 12 ELSE r.BillRate * r.HoursPerWeek * 52 END AS FLOAT)
        * fx.UsdPerLocalConstant                                         AS RunRateUsdConstant
INTO dw.CwMonthEndSnapshot
FROM dw.MonthEndCalendar AS cal
JOIN dw.BwServiceOrderRevision AS r
  ON r.EffectiveStartDate <= cal.MonthEndDate AND r.EffectiveEndDateFilled >= cal.MonthEndDate
 AND r.Status IN ('Approved', 'Closed')
 AND r.AssignmentStartDate <= cal.MonthEndDate AND r.AssignmentEndDate >= cal.MonthEndDate
JOIN dw.BwServiceOrder AS o ON o.ServiceOrderID = r.ServiceOrderID
JOIN dw.BwContingentWorker AS w ON w.BwWorkerID = o.BwWorkerID
JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = r.CostCenterCode
LEFT JOIN dw.RefFxRate AS fx ON fx.CurrencyCode = r.BillingCurrency AND fx.RateDate = cal.MonthEndDate;
CREATE CLUSTERED INDEX CIX_CwMonthEndSnapshot ON dw.CwMonthEndSnapshot (BwWorkerID, MonthEndDate);
GO

/* ------------------------------------------------------------------ conversions to employee
   Keystone closes the contingent record as Converted to employee; linked to Bridgeway through
   the ID Keystone stored (a blank or mistyped link cannot be linked: an ordinary hire). A walk
   conversion is contingent at the prior month-end and an employee at this one. */
DROP TABLE IF EXISTS dw.CwConversion;
SELECT
    c.PersonID,
    c.BwWorkerID,
    c.WorkerID,
    w.OriginalHireDate                                                   AS HireDate,
    cal.MonthEndDate,
    cal.PriorMonthEndDate,
    CAST(CASE WHEN EXISTS (SELECT 1 FROM dw.CwMonthEndSnapshot AS s
                           WHERE s.BwWorkerID = c.BwWorkerID AND s.MonthEndDate = cal.PriorMonthEndDate)
               AND NOT EXISTS (SELECT 1 FROM dw.CwMonthEndSnapshot AS s
                               WHERE s.BwWorkerID = c.BwWorkerID AND s.MonthEndDate = cal.MonthEndDate)
               AND EXISTS (SELECT 1 FROM dw.WorkerMonthEndSnapshot AS e
                           WHERE e.WorkerID = c.WorkerID AND e.MonthEndDate = cal.MonthEndDate)
               AND NOT EXISTS (SELECT 1 FROM dw.WorkerMonthEndSnapshot AS e
                               WHERE e.WorkerID = c.WorkerID AND e.MonthEndDate = cal.PriorMonthEndDate)
              THEN 1 ELSE 0 END AS BIT)                                  AS IsWalkConversion
INTO dw.CwConversion
FROM (
    SELECT PersonID, BwWorkerID, ConvertedToWorkerID AS WorkerID,
           ROW_NUMBER() OVER (PARTITION BY PersonID ORDER BY EffectiveStartDate) AS rn
    FROM dw.KsContingentWorker
    WHERE InactiveReason = 'Converted to employee'
) AS c
JOIN dw.BwContingentWorker AS b ON b.BwWorkerID = c.BwWorkerID
JOIN dw.DimWorker AS w ON w.WorkerID = c.WorkerID
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = EOMONTH(w.OriginalHireDate)
WHERE c.rn = 1;
GO

/* ------------------------------------------------------------------ contingent movement
   One row per contingent worker per month, prior and current month-end side by side: Start (New
   engagement, or Returned after a lapse), End (Completed, Ended early, Lapsed: approved late),
   Conversion (hired as an employee), Internal Move (Transfer, Location Change), No Change. */
DROP TABLE IF EXISTS dw.CwMovement;
SELECT
    m.*,
    CASE
        WHEN m.InCurrent = 1 AND m.InPrior = 0 THEN 'Start'
        WHEN m.InPrior = 1 AND m.InCurrent = 0 AND m.ConvertedToWorkerID IS NOT NULL THEN 'Conversion'
        WHEN m.InPrior = 1 AND m.InCurrent = 0 THEN 'End'
        WHEN m.PriorDepartmentID <> m.CurrentDepartmentID OR m.PriorCountryCode <> m.CurrentCountryCode THEN 'Internal Move'
        ELSE 'No Change'
    END AS MovementType,
    CASE
        WHEN m.InCurrent = 1 AND m.InPrior = 0
            THEN CASE WHEN m.FirstMonthEnd < m.MonthEndDate THEN 'Returned after a lapse' ELSE 'New engagement' END
        WHEN m.InPrior = 1 AND m.InCurrent = 0 AND m.ConvertedToWorkerID IS NOT NULL THEN 'Contingent to Employee'
        WHEN m.InPrior = 1 AND m.InCurrent = 0 AND m.LastMonthEnd > m.MonthEndDate THEN 'Lapsed: approved late'
        WHEN m.InPrior = 1 AND m.InCurrent = 0
            THEN CASE WHEN EXISTS (SELECT 1 FROM dw.BwServiceOrderRevision AS r
                                   WHERE r.ServiceOrderID = m.PriorServiceOrderID
                                     AND r.RevisionReason = 'Early end'
                                     AND r.EffectiveStartDate <= m.MonthEndDate)
                      THEN 'Ended early' ELSE 'Completed' END
        WHEN m.PriorDepartmentID <> m.CurrentDepartmentID THEN 'Transfer'
        WHEN m.PriorCountryCode <> m.CurrentCountryCode THEN 'Location Change'
    END AS MovementReason
INTO dw.CwMovement
FROM (
    SELECT
        pr.MonthEndDate,
        pr.PriorMonthEndDate,
        pr.BwWorkerID,
        COALESCE(c.CwType, p.CwType)                                     AS CwType,
        CASE WHEN p.BwWorkerID IS NULL THEN 0 ELSE 1 END                 AS InPrior,
        CASE WHEN c.BwWorkerID IS NULL THEN 0 ELSE 1 END                 AS InCurrent,
        p.ServiceOrderID AS PriorServiceOrderID,  c.ServiceOrderID AS CurrentServiceOrderID,
        p.DepartmentID   AS PriorDepartmentID,    c.DepartmentID   AS CurrentDepartmentID,
        p.CountryCode    AS PriorCountryCode,     c.CountryCode    AS CurrentCountryCode,
        p.CostCenterID   AS PriorCostCenterID,    c.CostCenterID   AS CurrentCostCenterID,
        p.LocationID     AS PriorLocationID,      c.LocationID     AS CurrentLocationID,
        p.SupplierID     AS PriorSupplierID,      c.SupplierID     AS CurrentSupplierID,
        p.BillingCurrency AS PriorCurrency,       c.BillingCurrency AS CurrentCurrency,
        p.RunRateLocal   AS PriorRunRateLocal,    c.RunRateLocal   AS CurrentRunRateLocal,
        p.FxRateActual   AS PriorFxRateActual,    c.FxRateActual   AS CurrentFxRateActual,
        p.FxRateConstant AS PriorFxRateConstant,  c.FxRateConstant AS CurrentFxRateConstant,
        p.RunRateUsdNominal  AS PriorRunRateUsdNominal,  c.RunRateUsdNominal  AS CurrentRunRateUsdNominal,
        p.RunRateUsdConstant AS PriorRunRateUsdConstant, c.RunRateUsdConstant AS CurrentRunRateUsdConstant,
        sp.FirstMonthEnd,
        sp.LastMonthEnd,
        cv.WorkerID                                                      AS ConvertedToWorkerID
    FROM (
        SELECT cal.MonthEndDate, cal.PriorMonthEndDate, s.BwWorkerID
        FROM dw.MonthEndCalendar AS cal JOIN dw.CwMonthEndSnapshot AS s ON s.MonthEndDate = cal.PriorMonthEndDate
        UNION
        SELECT cal.MonthEndDate, cal.PriorMonthEndDate, s.BwWorkerID
        FROM dw.MonthEndCalendar AS cal JOIN dw.CwMonthEndSnapshot AS s ON s.MonthEndDate = cal.MonthEndDate
        WHERE cal.PriorMonthEndDate IS NOT NULL
    ) AS pr
    JOIN (SELECT BwWorkerID, MIN(MonthEndDate) AS FirstMonthEnd, MAX(MonthEndDate) AS LastMonthEnd
          FROM dw.CwMonthEndSnapshot GROUP BY BwWorkerID) AS sp ON sp.BwWorkerID = pr.BwWorkerID
    LEFT JOIN dw.CwMonthEndSnapshot AS p ON p.BwWorkerID = pr.BwWorkerID AND p.MonthEndDate = pr.PriorMonthEndDate
    LEFT JOIN dw.CwMonthEndSnapshot AS c ON c.BwWorkerID = pr.BwWorkerID AND c.MonthEndDate = pr.MonthEndDate
    LEFT JOIN dw.CwConversion AS cv
           ON cv.BwWorkerID = pr.BwWorkerID AND cv.MonthEndDate = pr.MonthEndDate AND cv.IsWalkConversion = 1
) AS m;
GO

/* ------------------------------------------------------------------ the plan's contingent line, actuals
   Contingent workers Bridgeway counted on each plan quarter-end, by plan version and cost center:
   headcount, run-rate at the plan's FX date (the latest daily rate on or before it) and at the
   constant rate set. rpt.vw_plan_vs_actual joins it beside the employee actuals of 03b. */
DROP TABLE IF EXISTS #CwQuarter;
SELECT s.MonthEndDate AS QuarterEndDate, s.CostCenterID, s.BillingCurrency AS CurrencyCode,
       COUNT(*)                                                       AS Headcount,
       SUM(CAST(s.RunRateLocal AS DECIMAL(38, 10)))                   AS RunRateLocal,
       SUM(CAST(s.RunRateUsdConstant AS DECIMAL(38, 10)))             AS RunRateUsdConstant
INTO #CwQuarter
FROM dw.CwMonthEndSnapshot AS s
WHERE s.MonthEndDate IN (SELECT QuarterEndDate FROM dw.FactWorkforcePlan)
GROUP BY s.MonthEndDate, s.CostCenterID, s.BillingCurrency;

DROP TABLE IF EXISTS dw.CwPlanActual;
SELECT p.PlanVersion, p.CostCenterID, p.FiscalQuarter,
       SUM(c.Headcount)                                               AS ActualCwHeadcount,
       SUM(CAST(c.RunRateLocal * fx.UsdPerLocal AS DECIMAL(38, 10)))  AS ActualCwSpendUsdPlanFx,
       SUM(c.RunRateUsdConstant)                                      AS ActualCwSpendUsdConstant
INTO dw.CwPlanActual
FROM dw.FactWorkforcePlan AS p
JOIN #CwQuarter AS c ON c.QuarterEndDate = p.QuarterEndDate AND c.CostCenterID = p.CostCenterID
OUTER APPLY (
    SELECT TOP 1 d.UsdPerLocal
    FROM dw.RefFxRateDaily AS d
    WHERE d.CurrencyCode = c.CurrencyCode AND d.RateDate <= p.PlanFxRateDate
    ORDER BY d.RateDate DESC
) AS fx
GROUP BY p.PlanVersion, p.CostCenterID, p.FiscalQuarter;
DROP TABLE IF EXISTS #CwQuarter;
GO

/* ------------------------------------------------------------------ supplier spellings
   Keystone has no supplier table: each spelling maps to a Bridgeway supplier on a normalized key,
   the first four letters and digits, lowercased. The names hold no punctuation but spaces and
   full stops, so two REPLACEs do what the DuckDB model's regular expression does; a spelling that
   maps to nothing fails 12_validate_contingent_workforce.sql. */
DROP TABLE IF EXISTS dw.CwSupplierAlias;
SELECT
    s.KeystoneSupplierName,
    s.SupplierKey,
    b.SupplierID,
    b.SupplierName                                                       AS BridgewaySupplierName
INTO dw.CwSupplierAlias
FROM (
    SELECT DISTINCT SupplierName AS KeystoneSupplierName,
           LEFT(LOWER(REPLACE(REPLACE(SupplierName, ' ', ''), '.', '')), 4) AS SupplierKey
    FROM dw.KsContingentWorker
    WHERE SupplierName IS NOT NULL
) AS s
LEFT JOIN (
    SELECT SupplierID, SupplierName, LEFT(LOWER(REPLACE(REPLACE(SupplierName, ' ', ''), '.', '')), 4) AS SupplierKey
    FROM dw.BwSupplier
) AS b ON b.SupplierKey = s.SupplierKey;
GO

/* ------------------------------------------------------------------ who is who
   Keystone contingent people matched to Bridgeway workers in tiers, each on what the earlier
   ones left: 1 High (Keystone's stored ID, last names agree), 2 Medium (same name and supplier,
   starts within 7 days), 3 Low (same name, starts within 30 days). In tiers 2 and 3 a pair is
   kept only when each is the other's closest candidate. Unmatched people and workers are kept:
   every one appears exactly once. */
DROP TABLE IF EXISTS #KsPerson;
SELECT x.PersonID, x.FirstName, x.LastName, x.BwWorkerID AS StoredBwWorkerID, x.SupplierName, x.SupplierID,
       x.CwType, x.FirstContractStart AS ContractStartDate
INTO #KsPerson
FROM (
    SELECT k.*, a.SupplierID,
           MIN(k.ContractStartDate) OVER (PARTITION BY k.PersonID) AS FirstContractStart
    FROM dw.KsContingentWorker AS k
    LEFT JOIN dw.CwSupplierAlias AS a ON a.KeystoneSupplierName = k.SupplierName
) AS x
WHERE x.EffectiveEndDate IS NULL;

DROP TABLE IF EXISTS #Matched;
SELECT PersonID, BwWorkerID, 1 AS MatchTier
INTO #Matched
FROM (
    SELECT ks.PersonID, bw.BwWorkerID,
           ROW_NUMBER() OVER (PARTITION BY bw.BwWorkerID ORDER BY ks.PersonID) AS rn
    FROM #KsPerson AS ks
    JOIN dw.BwContingentWorker AS bw ON bw.BwWorkerID = ks.StoredBwWorkerID AND bw.LastName = ks.LastName
) AS t1
WHERE rn = 1;

INSERT INTO #Matched (PersonID, BwWorkerID, MatchTier)
SELECT PersonID, BwWorkerID, 2
FROM (
    SELECT c.*, ROW_NUMBER() OVER (PARTITION BY c.PersonID ORDER BY c.Gap, c.BwWorkerID) AS r_p,
                ROW_NUMBER() OVER (PARTITION BY c.BwWorkerID ORDER BY c.Gap, c.PersonID) AS r_b
    FROM (
        SELECT ks.PersonID, bw.BwWorkerID, ABS(DATEDIFF(DAY, bw.OriginalStartDate, ks.ContractStartDate)) AS Gap
        FROM #KsPerson AS ks
        JOIN dw.BwContingentWorker AS bw
          ON bw.FirstName = ks.FirstName AND bw.LastName = ks.LastName AND bw.SupplierID = ks.SupplierID
         AND ABS(DATEDIFF(DAY, bw.OriginalStartDate, ks.ContractStartDate)) <= 7
        WHERE ks.PersonID NOT IN (SELECT PersonID FROM #Matched)
          AND bw.BwWorkerID NOT IN (SELECT BwWorkerID FROM #Matched)
    ) AS c
) AS t2
WHERE r_p = 1 AND r_b = 1;

INSERT INTO #Matched (PersonID, BwWorkerID, MatchTier)
SELECT PersonID, BwWorkerID, 3
FROM (
    SELECT c.*, ROW_NUMBER() OVER (PARTITION BY c.PersonID ORDER BY c.Gap, c.BwWorkerID) AS r_p,
                ROW_NUMBER() OVER (PARTITION BY c.BwWorkerID ORDER BY c.Gap, c.PersonID) AS r_b
    FROM (
        SELECT ks.PersonID, bw.BwWorkerID, ABS(DATEDIFF(DAY, bw.OriginalStartDate, ks.ContractStartDate)) AS Gap
        FROM #KsPerson AS ks
        JOIN dw.BwContingentWorker AS bw
          ON bw.FirstName = ks.FirstName AND bw.LastName = ks.LastName
         AND ABS(DATEDIFF(DAY, bw.OriginalStartDate, ks.ContractStartDate)) <= 30
        WHERE ks.PersonID NOT IN (SELECT PersonID FROM #Matched)
          AND bw.BwWorkerID NOT IN (SELECT BwWorkerID FROM #Matched)
    ) AS c
) AS t3
WHERE r_p = 1 AND r_b = 1;

DROP TABLE IF EXISTS dw.CwIdentityResolution;
SELECT
    CONCAT('ID', RIGHT(CONCAT('000000', ROW_NUMBER() OVER (ORDER BY COALESCE(i.BwWorkerID, 'ZZ'), i.PersonID)), 6)) AS IdentityID,
    i.PersonID,
    i.BwWorkerID,
    CASE WHEN i.PersonID IS NOT NULL AND i.BwWorkerID IS NOT NULL THEN 'Matched'
         WHEN i.PersonID IS NOT NULL THEN 'Keystone only'
         WHEN bw.OriginalStartDate IS NULL THEN 'Never started'
         ELSE 'Bridgeway only' END                                       AS MatchStatus,
    i.MatchTier,
    CASE i.MatchTier WHEN 1 THEN 'High' WHEN 2 THEN 'Medium' WHEN 3 THEN 'Low' END AS MatchConfidence,
    CASE
        WHEN i.MatchTier = 1 THEN CONCAT('Keystone stores Bridgeway ID ', i.BwWorkerID, ' and the last names agree')
        WHEN i.MatchTier IN (2, 3) THEN
            CONCAT('Same name (', ks.FirstName, ' ', ks.LastName, ')',
                   CASE WHEN i.MatchTier = 2 THEN ', same supplier' ELSE '' END,
                   ', starts ', ABS(DATEDIFF(DAY, bw.OriginalStartDate, ks.ContractStartDate)), ' days apart; Keystone stores ',
                   CASE WHEN ks.StoredBwWorkerID IS NULL THEN 'no Bridgeway ID'
                        ELSE CONCAT('Bridgeway ID ', ks.StoredBwWorkerID) END)
        WHEN i.BwWorkerID IS NULL THEN
            CONCAT('No Bridgeway worker with this name, supplier and start',
                   CASE WHEN ks.StoredBwWorkerID IS NULL THEN ''
                        ELSE CONCAT('; Keystone stores ', ks.StoredBwWorkerID, ', which is nobody''s') END)
        WHEN bw.OriginalStartDate IS NULL THEN 'Withdrawn or rejected before day one: Keystone is not expected to have them'
        ELSE 'No Keystone person with this ID, or this name and start'
    END                                                                  AS MatchEvidence,
    ks.StoredBwWorkerID,
    COALESCE(bw.FirstName, ks.FirstName)                                 AS FirstName,
    COALESCE(bw.LastName, ks.LastName)                                   AS LastName,
    COALESCE(bw.CwType, ks.CwType)                                       AS CwType,
    COALESCE(bw.SupplierID, ks.SupplierID)                               AS SupplierID,
    bw.OriginalStartDate                                                 AS BridgewayStartDate,
    ks.ContractStartDate                                                 AS KeystoneStartDate
INTO dw.CwIdentityResolution
FROM (
    SELECT PersonID, BwWorkerID, MatchTier FROM #Matched
    UNION ALL
    SELECT PersonID, NULL, NULL FROM #KsPerson WHERE PersonID NOT IN (SELECT PersonID FROM #Matched)
    UNION ALL
    SELECT NULL, BwWorkerID, NULL FROM dw.BwContingentWorker WHERE BwWorkerID NOT IN (SELECT BwWorkerID FROM #Matched)
) AS i
LEFT JOIN #KsPerson AS ks ON ks.PersonID = i.PersonID
LEFT JOIN dw.BwContingentWorker AS bw ON bw.BwWorkerID = i.BwWorkerID;
CREATE CLUSTERED INDEX CIX_CwIdentityResolution ON dw.CwIdentityResolution (IdentityID);
DROP TABLE IF EXISTS #KsPerson;
DROP TABLE IF EXISTS #Matched;
GO

/* ------------------------------------------------------------------ the two systems side by side
   One row per identity per month-end on which either system shows the person working.
   Bridgeway side = what Keystone SHOULD hold: everything Bridgeway had sent by the month-end,
   applied the day it was sent (contract dates from the last contract change sent, cost center,
   office and manager from the last change of any kind). The DuckDB model finds "the last change
   sent by then" with an ASOF join; here each change carries the date of the next one
   (NextSentFilled, 9999-12-31 for the last) and a range join picks the one in force.
   Keystone side = the version in effect that day. */
DROP TABLE IF EXISTS #Sent;
SELECT f.BwWorkerID, f.SentDate, f.EventType, f.RevisionID, r.ServiceOrderID, r.AssignmentEndDate,
       r.CostCenterCode, r.OfficeCode, r.HiringManagerEmail,
       ROW_NUMBER() OVER (PARTITION BY f.BwWorkerID, f.SentDate
                          ORDER BY CASE WHEN f.EventType = 'New Worker' THEN 0 ELSE 1 END, f.RevisionID DESC) AS LastOfDay,
       ROW_NUMBER() OVER (PARTITION BY f.BwWorkerID, f.SentDate,
                                       CASE WHEN f.EventType = 'Attribute Change' THEN 0 ELSE 1 END
                          ORDER BY CASE WHEN f.EventType = 'New Worker' THEN 0 ELSE 1 END, f.RevisionID DESC) AS LastContractOfDay
INTO #Sent
FROM dw.FeedBridgewayKeystoneEvent AS f
JOIN dw.BwServiceOrderRevision AS r ON r.RevisionID = f.RevisionID;

DROP TABLE IF EXISTS #SentAny;
SELECT s.*, ISNULL(LEAD(s.SentDate) OVER (PARTITION BY s.BwWorkerID ORDER BY s.SentDate),
                   CONVERT(DATE, '9999-12-31')) AS NextSentFilled
INTO #SentAny
FROM #Sent AS s WHERE s.LastOfDay = 1;

DROP TABLE IF EXISTS #SentContract;
SELECT s.*, ISNULL(LEAD(s.SentDate) OVER (PARTITION BY s.BwWorkerID ORDER BY s.SentDate),
                   CONVERT(DATE, '9999-12-31')) AS NextSentFilled
INTO #SentContract
FROM #Sent AS s WHERE s.LastContractOfDay = 1 AND s.EventType <> 'Attribute Change';

DROP TABLE IF EXISTS dw.CwReconciliationSnapshot;
SELECT
    j.*,
    CAST(CASE WHEN j.KsRecordID IS NOT NULL THEN 1 ELSE 0 END AS BIT)   AS KsExists,
    CAST(CASE WHEN j.KsRecordID IS NOT NULL AND j.BwServiceOrderID IS NOT NULL
                   AND (j.KsActive <> j.BwActive
                        OR j.KsContractEndDate IS DISTINCT FROM j.BwContractEndDate
                        OR j.KsContractStartDate IS DISTINCT FROM j.BwContractStartDate)
              THEN 1 ELSE 0 END AS BIT)                                 AS ContractDiffers,
    CAST(CASE WHEN j.KsRecordID IS NOT NULL AND j.BwServiceOrderID IS NOT NULL
                   AND j.KsCostCenterID IS DISTINCT FROM j.BwCostCenterID THEN 1 ELSE 0 END AS BIT) AS CostCenterDiffers,
    CAST(CASE WHEN j.KsRecordID IS NOT NULL AND j.BwServiceOrderID IS NOT NULL
                   AND j.KsManagerWorkerID IS DISTINCT FROM j.BwManagerWorkerID THEN 1 ELSE 0 END AS BIT) AS ManagerDiffers,
    CAST(CASE WHEN j.KsRecordID IS NOT NULL AND j.BwServiceOrderID IS NOT NULL
                   AND j.KsLocationID IS DISTINCT FROM j.BwLocationID THEN 1 ELSE 0 END AS BIT) AS OfficeDiffers,
    CAST(CASE WHEN j.KsRecordID IS NOT NULL AND j.BwWorkerID IS NOT NULL
                   AND j.KsStoredBwWorkerID IS DISTINCT FROM j.BwWorkerID THEN 1 ELSE 0 END AS BIT) AS LinkDiffers
INTO dw.CwReconciliationSnapshot
FROM (
    SELECT
        g.MonthEndDate,
        g.IdentityID, g.MatchStatus, g.MatchTier, g.PersonID, g.BwWorkerID, g.CwType, g.SupplierID,
        /* Bridgeway: what Keystone should hold */
        b.ServiceOrderID                                                 AS BwServiceOrderID,
        w.OriginalStartDate                                              AS BwContractStartDate,
        b.AssignmentEndDate                                              AS BwContractEndDate,
        CAST(CASE WHEN b.AssignmentEndDate >= g.MonthEndDate THEN 1 ELSE 0 END AS BIT) AS BwActive,
        CAST(CASE WHEN b.AssignmentEndDate >= g.MonthEndDate AND w.OriginalStartDate <= g.MonthEndDate
                  THEN 1 ELSE 0 END AS BIT)                              AS BwWorking,
        a.CostCenterCode                                                 AS BwCostCenterID,
        a.OfficeCode                                                     AS BwLocationID,
        e.WorkerID                                                       AS BwManagerWorkerID,
        /* Keystone: what it holds */
        k.KsRecordID,
        k.EffectiveStartDate                                             AS KsVersionStartDate,
        k.ChangeSource                                                   AS KsChangeSource,
        k.BwWorkerID                                                     AS KsStoredBwWorkerID,
        k.Status                                                         AS KsStatus,
        k.ContractStartDate                                              AS KsContractStartDate,
        k.ContractEndDate                                                AS KsContractEndDate,
        k.InactiveReason                                                 AS KsInactiveReason,
        CAST(CASE WHEN k.Status = 'Active' THEN 1 ELSE 0 END AS BIT)     AS KsActive,
        CAST(CASE WHEN k.Status = 'Active' AND k.ContractStartDate <= g.MonthEndDate
                  THEN 1 ELSE 0 END AS BIT)                              AS KsWorking,
        k.CostCenterID                                                   AS KsCostCenterID,
        k.LocationID                                                     AS KsLocationID,
        k.ManagerWorkerID                                                AS KsManagerWorkerID
    FROM (
        SELECT cal.MonthEndDate, i.*
        FROM dw.MonthEndCalendar AS cal
        CROSS JOIN dw.CwIdentityResolution AS i
        WHERE i.MatchStatus <> 'Never started'
    ) AS g
    LEFT JOIN #SentContract AS b
           ON b.BwWorkerID = g.BwWorkerID AND b.SentDate <= g.MonthEndDate
          AND b.NextSentFilled > g.MonthEndDate
    LEFT JOIN dw.BwContingentWorker AS w ON w.BwWorkerID = b.BwWorkerID
    LEFT JOIN #SentAny AS a
           ON a.BwWorkerID = g.BwWorkerID AND a.SentDate <= g.MonthEndDate
          AND a.NextSentFilled > g.MonthEndDate
    LEFT JOIN dw.DimWorker AS e ON e.WorkEmail = a.HiringManagerEmail
    LEFT JOIN dw.KsContingentWorker AS k
           ON k.PersonID = g.PersonID
          AND k.EffectiveStartDate <= g.MonthEndDate AND k.EffectiveEndDateFilled >= g.MonthEndDate
    WHERE b.BwWorkerID IS NOT NULL OR k.PersonID IS NOT NULL
) AS j
WHERE j.BwWorking = 1 OR j.KsWorking = 1;
CREATE CLUSTERED INDEX CIX_CwReconciliationSnapshot ON dw.CwReconciliationSnapshot (MonthEndDate, IdentityID);
DROP TABLE IF EXISTS #Sent;
DROP TABLE IF EXISTS #SentAny;
DROP TABLE IF EXISTS #SentContract;
GO

/* ------------------------------------------------------------------ the discrepancies
   Found from the two systems and the feed log alone; the answer key is never read here.
   For each field group that differs (contract, cost center, manager, office) the most recent
   recorded cause names it: a feed change not applied by the month-end (CW00 in transit, CW01
   late), a feed change that failed (CW02 extension, CW03 early end, CW12 attribute), or a hand
   edit in Keystone (CW05). Structural rules: CW06 link, CW07 second ID, CW08 never reached
   Keystone, CW09 Keystone only, CW10 over the cap, CW04 not closed, CW11 billed after the end.
   Methodology: docs/projects/contingent-workforce/case_study_4.md */
DROP TABLE IF EXISTS #Events;
SELECT f.FeedEventID, f.BwWorkerID, f.EventType, f.SentDate, f.AppliedDate, f.Outcome, f.ErrorText,
       CASE WHEN f.EventType IN ('New Worker', 'Renewal', 'Extension', 'Early End') THEN 1 ELSE 0 END AS GContract,
       CASE WHEN f.EventType = 'New Worker' OR f.CostCenterCode IS DISTINCT FROM f.PrevCostCenterCode THEN 1 ELSE 0 END AS GCostCenter,
       CASE WHEN f.EventType = 'New Worker' OR f.HiringManagerEmail IS DISTINCT FROM f.PrevManagerEmail THEN 1 ELSE 0 END AS GManager,
       CASE WHEN f.EventType = 'New Worker' OR f.OfficeCode IS DISTINCT FROM f.PrevOfficeCode THEN 1 ELSE 0 END AS GOffice,
       CASE WHEN f.Outcome = 'Failed' THEN
                 CASE f.EventType WHEN 'New Worker' THEN 'CW08' WHEN 'Early End' THEN 'CW03'
                                  WHEN 'Attribute Change' THEN 'CW12' ELSE 'CW02' END
            WHEN f.Outcome = 'Queued' THEN 'CW01'
            WHEN DATEDIFF(DAY, f.SentDate, f.AppliedDate) <= 2 THEN 'CW00' ELSE 'CW01' END AS Code
INTO #Events
FROM (
    SELECT fe.*, r.CostCenterCode, r.HiringManagerEmail, r.OfficeCode,
           LAG(r.CostCenterCode) OVER (PARTITION BY fe.BwWorkerID
               ORDER BY fe.SentDate, CASE WHEN fe.EventType = 'New Worker' THEN 0 ELSE 1 END, fe.RevisionID) AS PrevCostCenterCode,
           LAG(r.HiringManagerEmail) OVER (PARTITION BY fe.BwWorkerID
               ORDER BY fe.SentDate, CASE WHEN fe.EventType = 'New Worker' THEN 0 ELSE 1 END, fe.RevisionID) AS PrevManagerEmail,
           LAG(r.OfficeCode) OVER (PARTITION BY fe.BwWorkerID
               ORDER BY fe.SentDate, CASE WHEN fe.EventType = 'New Worker' THEN 0 ELSE 1 END, fe.RevisionID) AS PrevOfficeCode
    FROM dw.FeedBridgewayKeystoneEvent AS fe
    JOIN dw.BwServiceOrderRevision AS r ON r.RevisionID = fe.RevisionID
) AS f
WHERE f.Outcome IN ('Failed', 'Queued') OR f.AppliedDate > f.SentDate;

/* hand edits in Keystone: a Manager or HR Ops version that changed a field (first versions too:
   a hand edit on the day the feed created the record is merged into it) */
DROP TABLE IF EXISTS #Edits;
SELECT v.PersonID, v.EffectiveStartDate AS EditDate, v.ChangeSource,
       CASE WHEN v.CostCenterID IS DISTINCT FROM v.PrevCostCenterID THEN 1 ELSE 0 END       AS GCostCenter,
       CASE WHEN v.ManagerWorkerID IS DISTINCT FROM v.PrevManagerWorkerID THEN 1 ELSE 0 END AS GManager,
       CASE WHEN v.LocationID IS DISTINCT FROM v.PrevLocationID THEN 1 ELSE 0 END           AS GOffice
INTO #Edits
FROM (
    SELECT k.*,
           LAG(k.CostCenterID)    OVER (PARTITION BY k.PersonID ORDER BY k.EffectiveStartDate) AS PrevCostCenterID,
           LAG(k.ManagerWorkerID) OVER (PARTITION BY k.PersonID ORDER BY k.EffectiveStartDate) AS PrevManagerWorkerID,
           LAG(k.LocationID)      OVER (PARTITION BY k.PersonID ORDER BY k.EffectiveStartDate) AS PrevLocationID
    FROM dw.KsContingentWorker AS k
) AS v
WHERE v.ChangeSource IN ('Manager', 'HR Ops')
  AND COALESCE(v.InactiveReason, '') <> 'Converted to employee';

/* one row per differing field group */
DROP TABLE IF EXISTS #Diffs;
SELECT s.*, g.Grp
INTO #Diffs
FROM dw.CwReconciliationSnapshot AS s
CROSS JOIN (VALUES ('contract'), ('cost_center'), ('manager'), ('office')) AS g (Grp)
WHERE (g.Grp = 'contract' AND s.ContractDiffers = 1) OR (g.Grp = 'cost_center' AND s.CostCenterDiffers = 1)
   OR (g.Grp = 'manager' AND s.ManagerDiffers = 1)   OR (g.Grp = 'office' AND s.OfficeDiffers = 1);

/* the most recent recorded cause of each difference */
DROP TABLE IF EXISTS #Explained;
SELECT x.*
INTO #Explained
FROM (
    SELECT d.*, c.CauseDate, c.Code, c.FeedEventID, c.EventType, c.SentDate, c.AppliedDate, c.Outcome, c.ErrorText,
           ROW_NUMBER() OVER (PARTITION BY d.MonthEndDate, d.IdentityID, d.Grp
                              ORDER BY c.CauseDate DESC, c.Kind DESC, c.FeedEventID DESC) AS rn
    FROM #Diffs AS d
    LEFT JOIN (
        SELECT d.MonthEndDate, d.IdentityID, d.Grp, e.SentDate AS CauseDate, 1 AS Kind,
               e.Code, e.FeedEventID, e.EventType, e.SentDate, e.AppliedDate, e.Outcome, e.ErrorText
        FROM #Diffs AS d
        JOIN #Events AS e ON e.BwWorkerID = d.BwWorkerID AND e.SentDate <= d.MonthEndDate
        WHERE ((d.Grp = 'contract' AND e.GContract = 1) OR (d.Grp = 'cost_center' AND e.GCostCenter = 1)
               OR (d.Grp = 'manager' AND e.GManager = 1) OR (d.Grp = 'office' AND e.GOffice = 1))
          AND (e.Outcome = 'Failed' OR e.Outcome = 'Queued' OR e.AppliedDate > d.MonthEndDate)
        UNION ALL
        SELECT d.MonthEndDate, d.IdentityID, d.Grp, x.EditDate, 2, 'CW05', NULL, NULL, NULL, NULL, x.ChangeSource, NULL
        FROM #Diffs AS d
        JOIN #Edits AS x ON x.PersonID = d.PersonID AND x.EditDate <= d.MonthEndDate
        WHERE (d.Grp = 'cost_center' AND x.GCostCenter = 1) OR (d.Grp = 'manager' AND x.GManager = 1)
           OR (d.Grp = 'office' AND x.GOffice = 1)
    ) AS c ON c.MonthEndDate = d.MonthEndDate AND c.IdentityID = d.IdentityID AND c.Grp = d.Grp
) AS x
WHERE x.rn = 1;

DROP TABLE IF EXISTS #Lines;
/* field groups */
SELECT
    e.MonthEndDate, e.IdentityID, e.BwWorkerID, e.PersonID,
    CAST(COALESCE(e.Code, 'Unexplained') AS VARCHAR(12))                 AS DiscrepancyCode,
    CAST(CASE WHEN e.Outcome = 'Failed' AND e.ErrorText LIKE 'Worker not found%'
              THEN CASE WHEN EXISTS (SELECT 1 FROM dw.KsContingentWorker AS k
                                     WHERE k.PersonID = e.PersonID AND k.EffectiveStartDate <= e.SentDate)
                        THEN 'CW06' ELSE 'CW08' END
              ELSE COALESCE(e.Code, 'Unexplained') END AS VARCHAR(12))   AS RootCauseCode,
    CAST(e.Grp AS VARCHAR(12))                                           AS Grp,
    e.CauseDate                                                          AS SinceDate,
    e.BwServiceOrderID                                                   AS ServiceOrderID,
    e.FeedEventID,
    CAST(NULL AS VARCHAR(12))                                            AS TimesheetID,
    CAST(CONCAT(
        CASE e.Grp
            WHEN 'contract' THEN CONCAT('Bridgeway: ', CASE WHEN e.BwActive = 1 THEN 'active' ELSE 'ended' END,
                                        ', contract to ', COALESCE(CAST(e.BwContractEndDate AS VARCHAR(10)), '?'),
                                        '; Keystone: ', COALESCE(e.KsStatus, 'no record'),
                                        ', contract to ', COALESCE(CAST(e.KsContractEndDate AS VARCHAR(10)), '?'))
            WHEN 'cost_center' THEN CONCAT('Cost center: Bridgeway ', COALESCE(e.BwCostCenterID, '?'),
                                           ', Keystone ', COALESCE(e.KsCostCenterID, '?'))
            WHEN 'manager' THEN CONCAT('Manager: Bridgeway ', COALESCE(e.BwManagerWorkerID, '?'),
                                       ', Keystone ', COALESCE(e.KsManagerWorkerID, '?'))
            ELSE CONCAT('Office: Bridgeway ', COALESCE(e.BwLocationID, '?'), ', Keystone ', COALESCE(e.KsLocationID, '?'))
        END,
        CASE
            WHEN e.Code = 'CW05' THEN CONCAT('. Changed by hand in Keystone (', e.Outcome, ') on ', CAST(e.CauseDate AS VARCHAR(10)))
            WHEN e.Outcome = 'Failed' THEN CONCAT('. ', e.EventType, ' sent ', CAST(e.SentDate AS VARCHAR(10)), ' failed: ', e.ErrorText)
            WHEN e.Outcome = 'Queued' THEN CONCAT('. ', e.EventType, ' sent ', CAST(e.SentDate AS VARCHAR(10)), ', still queued')
            WHEN e.Code IS NOT NULL THEN CONCAT('. ', e.EventType, ' sent ', CAST(e.SentDate AS VARCHAR(10)),
                                                ', applied ', CAST(e.AppliedDate AS VARCHAR(10)))
            ELSE '. No recorded change explains it'
        END) AS VARCHAR(400))                                            AS Evidence
INTO #Lines
FROM #Explained AS e;

/* CW08 never reached Keystone: working in Bridgeway, no Keystone record */
INSERT INTO #Lines
SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID,
       COALESCE(p.Code, 'CW08'), COALESCE(p.Code, 'CW08'), 'record',
       COALESCE(p.SentDate, n.SentDate, s.BwContractStartDate), s.BwServiceOrderID,
       COALESCE(p.FeedEventID, n.FeedEventID), NULL,
       CONCAT('Working in Bridgeway since ', CAST(s.BwContractStartDate AS VARCHAR(10)), '; no Keystone record',
              CASE WHEN p.FeedEventID IS NOT NULL THEN CONCAT('. New Worker sent ', CAST(p.SentDate AS VARCHAR(10)), ', not applied yet')
                   WHEN n.FeedEventID IS NOT NULL THEN CONCAT('. New Worker sent ', CAST(n.SentDate AS VARCHAR(10)), ' failed: ', n.ErrorText)
                   ELSE '' END)
FROM dw.CwReconciliationSnapshot AS s
LEFT JOIN #Events AS p
       ON p.BwWorkerID = s.BwWorkerID AND p.EventType = 'New Worker' AND p.Code IN ('CW00', 'CW01')
      AND p.SentDate <= s.MonthEndDate AND (p.Outcome = 'Queued' OR p.AppliedDate > s.MonthEndDate)
LEFT JOIN #Events AS n
       ON n.BwWorkerID = s.BwWorkerID AND n.EventType = 'New Worker' AND n.Outcome = 'Failed'
WHERE s.BwWorking = 1 AND s.KsExists = 0;

/* CW09 Keystone-only contingent worker */
INSERT INTO #Lines
SELECT MonthEndDate, IdentityID, NULL, PersonID, 'CW09', 'CW09', 'record', KsContractStartDate, NULL, NULL, NULL,
       CONCAT('Active in Keystone since ', CAST(KsContractStartDate AS VARCHAR(10)),
              ' (written by ', KsChangeSource, '); no Bridgeway worker with this ID, or this name and start')
FROM dw.CwReconciliationSnapshot
WHERE MatchStatus = 'Keystone only' AND KsWorking = 1;

/* CW06 link ID missing or mistyped */
INSERT INTO #Lines
SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID, 'CW06', 'CW06', 'link',
       (SELECT MIN(k.EffectiveStartDate) FROM dw.KsContingentWorker AS k
        WHERE k.PersonID = s.PersonID AND k.BwWorkerID IS DISTINCT FROM s.BwWorkerID
          AND k.EffectiveStartDate <= s.MonthEndDate),
       s.BwServiceOrderID, NULL, NULL,
       CONCAT('Keystone stores ', CASE WHEN s.KsStoredBwWorkerID IS NULL THEN 'no Bridgeway ID'
                                       ELSE CONCAT('Bridgeway ID ', s.KsStoredBwWorkerID) END,
              '; matched to ', s.BwWorkerID, ' on name, supplier and start (',
              CASE s.MatchTier WHEN 2 THEN 'Medium' ELSE 'Low' END, ' confidence)')
FROM dw.CwReconciliationSnapshot AS s
WHERE s.MatchStatus = 'Matched' AND s.LinkDiffers = 1;

/* CW07 one person, two IDs: a new engagement the day after a same-name worker at the same
   supplier ended, on the same cost center */
INSERT INTO #Lines
SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID, 'CW07', 'CW07', 'identity',
       s.BwContractStartDate, s.BwServiceOrderID, NULL, NULL,
       CONCAT('Bridgeway ', s.BwWorkerID, ' started ', CAST(s.BwContractStartDate AS VARCHAR(10)),
              ' as a new engagement; ', p.BwWorkerID, ', same name and supplier, ended ', CAST(p.LastDay AS VARCHAR(10)))
FROM dw.CwReconciliationSnapshot AS s
JOIN dw.BwContingentWorker AS w ON w.BwWorkerID = s.BwWorkerID
JOIN (
    SELECT b.BwWorkerID, b.FirstName, b.LastName, b.SupplierID, r.AssignmentEndDate AS LastDay,
           r.CostCenterCode AS LastCostCenter,
           ROW_NUMBER() OVER (PARTITION BY b.BwWorkerID ORDER BY r.AssignmentEndDate DESC, r.ServiceOrderID DESC) AS rn
    FROM dw.BwContingentWorker AS b
    JOIN dw.BwServiceOrder AS o ON o.BwWorkerID = b.BwWorkerID
    JOIN dw.BwServiceOrderRevision AS r ON r.ServiceOrderID = o.ServiceOrderID AND r.IsCurrent = 1
    WHERE r.Status IN ('Approved', 'Closed')
) AS p
  ON p.rn = 1 AND p.FirstName = w.FirstName AND p.LastName = w.LastName AND p.SupplierID = w.SupplierID
 AND p.BwWorkerID <> w.BwWorkerID
 AND w.OriginalStartDate = DATEADD(DAY, 1, p.LastDay)
WHERE p.LastCostCenter = (SELECT TOP 1 r0.CostCenterCode
                          FROM dw.BwServiceOrder AS o0
                          JOIN dw.BwServiceOrderRevision AS r0
                            ON r0.ServiceOrderID = o0.ServiceOrderID AND r0.RevisionNo = 0
                          WHERE o0.BwWorkerID = w.BwWorkerID
                          ORDER BY r0.AssignmentStartDate);

/* CW10 over the 48-month cap */
INSERT INTO #Lines
SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID, 'CW10', 'CW10', 'engagement',
       DATEADD(MONTH, 48, s.BwContractStartDate), s.BwServiceOrderID, NULL, NULL,
       CONCAT(s.CwType, ' working since ', CAST(s.BwContractStartDate AS VARCHAR(10)), ': 48 months reached ',
              CAST(CAST(DATEADD(DAY, -1, DATEADD(MONTH, 48, s.BwContractStartDate)) AS DATE) AS VARCHAR(10)),
              '; contract now to ', CAST(s.BwContractEndDate AS VARCHAR(10)))
FROM dw.CwReconciliationSnapshot AS s
WHERE s.BwWorking = 1 AND s.CwType IN ('Contractor', 'Consultant')
  AND s.MonthEndDate >= DATEADD(MONTH, 48, s.BwContractStartDate);

/* CW04 ended but not closed in Bridgeway (not an order later extended: that was a late approval) */
INSERT INTO #Lines
SELECT cal.MonthEndDate, i.IdentityID, o.BwWorkerID, i.PersonID, 'CW04', 'CW04', 'order',
       DATEADD(DAY, 16, r.AssignmentEndDate), r.ServiceOrderID, NULL, NULL,
       CONCAT('Order ', r.ServiceOrderID, ': last day ', CAST(r.AssignmentEndDate AS VARCHAR(10)),
              ', still ', r.Status, ' on the month-end')
FROM dw.MonthEndCalendar AS cal
JOIN dw.BwServiceOrderRevision AS r
  ON r.EffectiveStartDate <= cal.MonthEndDate AND r.EffectiveEndDateFilled >= cal.MonthEndDate
 AND r.Status = 'Approved' AND DATEADD(DAY, 16, r.AssignmentEndDate) <= cal.MonthEndDate
JOIN dw.BwServiceOrder AS o ON o.ServiceOrderID = r.ServiceOrderID
LEFT JOIN dw.CwIdentityResolution AS i ON i.BwWorkerID = o.BwWorkerID
WHERE NOT EXISTS (SELECT 1 FROM dw.BwServiceOrderRevision AS later
                  WHERE later.ServiceOrderID = r.ServiceOrderID
                    AND later.EffectiveStartDate > cal.MonthEndDate
                    AND later.AssignmentEndDate > r.AssignmentEndDate);

/* CW11 billed after the assignment */
INSERT INTO #Lines
SELECT t.MonthEndDate, i.IdentityID, t.BwWorkerID, i.PersonID, 'CW11', 'CW11', 'timesheet',
       DATEFROMPARTS(YEAR(t.MonthEndDate), MONTH(t.MonthEndDate), 1), t.ServiceOrderID, NULL, t.TimesheetID,
       CONCAT('Timesheet ', t.TimesheetID, ' bills ', CAST(t.BilledUnits AS VARCHAR(20)), ' units for ',
              DATENAME(MONTH, t.MonthEndDate), ' ', YEAR(t.MonthEndDate),
              '; the assignment ended ', CAST(r.AssignmentEndDate AS VARCHAR(10)))
FROM dw.BwTimesheetMonth AS t
JOIN dw.BwServiceOrderRevision AS r
  ON r.ServiceOrderID = t.ServiceOrderID
 AND r.EffectiveStartDate <= t.MonthEndDate AND r.EffectiveEndDateFilled >= t.MonthEndDate
LEFT JOIN dw.CwIdentityResolution AS i ON i.BwWorkerID = t.BwWorkerID
WHERE DATEFROMPARTS(YEAR(t.MonthEndDate), MONTH(t.MonthEndDate), 1) > r.AssignmentEndDate;

/* one row per month-end, identity (or order / timesheet) and type: field groups merged.
   FeedEventID is that of the oldest cause; the fields are listed once each, in order.
   SQL Server allows two ordered STRING_AGGs in one SELECT only when they share an ordering
   (Msg 8711), so the field list is aggregated in its own derived table and joined back. */
DROP TABLE IF EXISTS #Ranked;
SELECT f.*,
       COALESCE(f.ServiceOrderID, '') AS OrderKey,
       COALESCE(f.TimesheetID, '')    AS SheetKey,
       ROW_NUMBER() OVER (PARTITION BY f.MonthEndDate, f.IdentityID, f.DiscrepancyCode, COALESCE(f.ServiceOrderID, ''),
                                       COALESCE(f.TimesheetID, ''), f.Field ORDER BY f.Grp) AS FieldRank,
       ROW_NUMBER() OVER (PARTITION BY f.MonthEndDate, f.IdentityID, f.DiscrepancyCode, COALESCE(f.ServiceOrderID, ''),
                                       COALESCE(f.TimesheetID, '')
                          ORDER BY CASE WHEN f.FeedEventID IS NULL OR f.SinceDate IS NULL THEN 1 ELSE 0 END,
                                   f.SinceDate, f.FeedEventID) AS CauseRank
INTO #Ranked
FROM (
    SELECT x.*,
           CASE x.Grp WHEN 'contract' THEN 'Status and contract dates' WHEN 'cost_center' THEN 'Cost center'
                      WHEN 'manager' THEN 'Manager' WHEN 'office' THEN 'Office' WHEN 'record' THEN 'Whole record'
                      WHEN 'link' THEN 'Bridgeway worker ID' WHEN 'identity' THEN 'Bridgeway worker ID; Keystone person'
                      WHEN 'engagement' THEN 'Engagement length' WHEN 'order' THEN 'Order status'
                      ELSE 'Timesheet' END AS Field
    FROM #Lines AS x
) AS f;

DROP TABLE IF EXISTS dw.CwDiscrepancy;
SELECT
    l.MonthEndDate,
    l.IdentityID,
    MIN(l.BwWorkerID)                                                    AS BwWorkerID,
    MIN(l.PersonID)                                                      AS PersonID,
    l.DiscrepancyCode,
    MIN(l.RootCauseCode)                                                 AS RootCauseCode,
    fa.FieldsAffected,
    MIN(l.SinceDate)                                                     AS SinceDate,
    DATEDIFF(DAY, MIN(l.SinceDate), l.MonthEndDate)                      AS AgeDays,
    MIN(l.ServiceOrderID)                                                AS ServiceOrderID,
    MAX(CASE WHEN l.CauseRank = 1 THEN l.FeedEventID END)                AS FeedEventID,
    MIN(l.TimesheetID)                                                   AS TimesheetID,
    STRING_AGG(l.Evidence, ' | ') WITHIN GROUP (ORDER BY l.Grp, l.Evidence) AS Evidence
INTO dw.CwDiscrepancy
FROM #Ranked AS l
JOIN (
    SELECT MonthEndDate, IdentityID, DiscrepancyCode, OrderKey, SheetKey,
           STRING_AGG(Field, '; ') WITHIN GROUP (ORDER BY Field) AS FieldsAffected
    FROM #Ranked
    WHERE FieldRank = 1
    GROUP BY MonthEndDate, IdentityID, DiscrepancyCode, OrderKey, SheetKey
) AS fa
  ON fa.MonthEndDate = l.MonthEndDate AND fa.IdentityID = l.IdentityID AND fa.DiscrepancyCode = l.DiscrepancyCode
 AND fa.OrderKey = l.OrderKey AND fa.SheetKey = l.SheetKey
GROUP BY l.MonthEndDate, l.IdentityID, l.DiscrepancyCode, l.OrderKey, l.SheetKey, fa.FieldsAffected;
CREATE CLUSTERED INDEX CIX_CwDiscrepancy ON dw.CwDiscrepancy (MonthEndDate, IdentityID);
DROP TABLE IF EXISTS #Events;
DROP TABLE IF EXISTS #Edits;
DROP TABLE IF EXISTS #Diffs;
DROP TABLE IF EXISTS #Explained;
DROP TABLE IF EXISTS #Lines;
DROP TABLE IF EXISTS #Ranked;
GO

/* -------------------------------------------------------------------- summary */
SELECT 'dw.BwContingentWorker' AS TableName, COUNT(*) AS RowsLoaded FROM dw.BwContingentWorker
UNION ALL SELECT 'dw.BwServiceOrderRevision', COUNT(*) FROM dw.BwServiceOrderRevision
UNION ALL SELECT 'dw.BwTimesheetMonth', COUNT(*) FROM dw.BwTimesheetMonth
UNION ALL SELECT 'dw.KsContingentWorker', COUNT(*) FROM dw.KsContingentWorker
UNION ALL SELECT 'dw.FeedBridgewayKeystoneEvent', COUNT(*) FROM dw.FeedBridgewayKeystoneEvent
UNION ALL SELECT 'dw.CwMonthEndSnapshot', COUNT(*) FROM dw.CwMonthEndSnapshot
UNION ALL SELECT 'dw.CwConversion', COUNT(*) FROM dw.CwConversion
UNION ALL SELECT 'dw.CwMovement', COUNT(*) FROM dw.CwMovement
UNION ALL SELECT 'dw.CwIdentityResolution', COUNT(*) FROM dw.CwIdentityResolution
UNION ALL SELECT 'dw.CwReconciliationSnapshot', COUNT(*) FROM dw.CwReconciliationSnapshot
UNION ALL SELECT 'dw.CwDiscrepancy', COUNT(*) FROM dw.CwDiscrepancy;
GO
