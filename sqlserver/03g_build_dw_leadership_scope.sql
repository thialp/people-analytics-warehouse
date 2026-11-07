/*
  03g_build_dw_leadership_scope.sql
  Release 7: Who Leads Where (case study 7), leadership scope and org design. Runs after 03, 03c
  and 03e (it reads dw.WorkerMonthEndSnapshot, dw.CwMonthEndSnapshot, dw.CwIdentityResolution,
  dw.KsContingentWorker and fc.report_calendar).

    typed raw     MatrixOrg, MatrixMembership, RoleAssignment, TimeOffRequest, LeaveOfAbsence,
                  BwTimeOff, RefJobFamilyHome, RefPublicHoliday, GenOrgDriftTruth, RefDayNumber
    derived       PersonMonthEnd       employees and contingent workers per month-end
                  OrgClosure           everyone below a person in the solid line, at any depth
                  OrgLeader            L0 / L1 / L2 / Manager, with the path from the top
                  AlignmentSignal      S1 S2 M1 M2 M3 per person per month-end
                  AssignmentSignal     R1: role assignments still naming a former leader
                  LeaderOrg            each leader's organization per month-end and worker type
                  TimeOffDay           one row per person per day off (time off or leave)
                  PersonAvailabilityDay  the report date and the 30 days after it
                  LeaderAvailability   at work / off per leader, worker type and day
                  OrgNode              the tree's nodes on the report date
                  OrgTreeLayout        the tree's coordinates (dynamic and static) for every leader
                  AlignmentDetail      person x signal on the report date, with the L0 / L1 / L2 above
                  OrgEntitlement       row-level security for Tableau Cloud

  The T-SQL twin of the release 7 models in sql/01_staging, sql/02_intermediate and sql/03_marts;
  checked row for row by sqlserver/check_tsql_in_duckdb.py, and on SQL Server by
  18_validate_leadership_scope.sql.

  The closure is built one level at a time (12 INSERTs, deepest Arcadia chain today: 8) instead of
  a recursive CTE: each level is one hash join, where a recursive CTE walks row by row through an
  index spool. 18_validate checks that no chain is cut at level 12.
  Weekdays are counted from Monday, Jan 1, 1900 (DATEDIFF(DAY, '1900-01-01', d) % 7: 0 = Monday,
  5 and 6 = the weekend), so the result never depends on the server's DATEFIRST setting.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ------------------------------------------------------------------ typed raw */
DROP TABLE IF EXISTS dw.MatrixOrg;
SELECT
    CAST(matrix_record_id AS VARCHAR(20))                         AS MatrixRecordID,
    CAST(matrix_org_id AS VARCHAR(20))                            AS MatrixOrgID,
    CAST(matrix_org_name AS VARCHAR(60))                          AS MatrixOrgName,
    CAST(matrix_type AS VARCHAR(20))                              AS MatrixType,
    CAST(NULLIF(region, '') AS VARCHAR(30))                       AS Region,
    CAST(NULLIF(parent_matrix_org_id, '') AS VARCHAR(20))         AS ParentMatrixOrgID,
    CAST(NULLIF(covers_country_codes, '') AS VARCHAR(100))        AS CoversCountryCodes,
    CONVERT(DATE, NULLIF(effective_start_date, ''))               AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))                 AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')), CONVERT(DATE, '9999-12-31')) AS EffectiveEndDateFilled,
    CAST(NULLIF(manager_worker_id, '') AS VARCHAR(20))            AS ManagerWorkerID,
    CAST(status AS VARCHAR(20))                                   AS Status,
    CONVERT(DATE, NULLIF(inactive_date, ''))                      AS InactiveDate,
    CONVERT(DATE, NULLIF(created_date, ''))                       AS CreatedDate
INTO dw.MatrixOrg
FROM raw.ks_matrix_org;

DROP TABLE IF EXISTS dw.MatrixMembership;
SELECT
    CAST(membership_id AS VARCHAR(20))                            AS MembershipID,
    CAST(person_id AS VARCHAR(20))                                AS PersonID,
    CAST(person_type AS VARCHAR(20))                              AS PersonType,
    CAST(matrix_org_id AS VARCHAR(20))                            AS MatrixOrgID,
    CONVERT(DATE, NULLIF(effective_start_date, ''))               AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))                 AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')), CONVERT(DATE, '9999-12-31')) AS EffectiveEndDateFilled,
    CAST(NULLIF(assigned_reason, '') AS VARCHAR(40))              AS AssignedReason
INTO dw.MatrixMembership
FROM raw.ks_matrix_membership;
CREATE CLUSTERED INDEX CIX_MatrixMembership ON dw.MatrixMembership (PersonID, EffectiveStartDate);

DROP TABLE IF EXISTS dw.RoleAssignment;
SELECT
    CAST(assignment_id AS VARCHAR(20))                            AS AssignmentID,
    CAST(role_name AS VARCHAR(60))                                AS RoleName,
    CAST(assignee_worker_id AS VARCHAR(20))                       AS AssigneeWorkerID,
    CAST(target_org_unit_id AS VARCHAR(20))                       AS TargetOrgUnitID,
    CAST(target_org_name AS VARCHAR(80))                          AS TargetOrgName,
    CAST(NULLIF(named_leader_worker_id, '') AS VARCHAR(20))       AS NamedLeaderWorkerID,
    CAST(assigned_via AS VARCHAR(20))                             AS AssignedVia,
    CAST(NULLIF(inherited_from_org_unit_id, '') AS VARCHAR(20))   AS InheritedFromOrgUnitID,
    CONVERT(DATE, NULLIF(effective_start_date, ''))               AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))                 AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')), CONVERT(DATE, '9999-12-31')) AS EffectiveEndDateFilled
INTO dw.RoleAssignment
FROM raw.ks_role_assignment;

DROP TABLE IF EXISTS dw.TimeOffRequest;
SELECT
    CAST(time_off_request_id AS VARCHAR(20))                      AS TimeOffRequestID,
    CAST(person_id AS VARCHAR(20))                                AS PersonID,
    CAST(person_type AS VARCHAR(20))                              AS PersonType,
    CAST(source_system AS VARCHAR(4))                             AS SourceSystem,
    CAST(NULLIF(bw_booking_id, '') AS VARCHAR(20))                AS BwBookingID,
    CAST(time_off_type AS VARCHAR(60))                            AS TimeOffType,
    CAST(request_type AS VARCHAR(30))                             AS RequestType,
    CONVERT(DATE, NULLIF(first_day, ''))                          AS FirstDay,
    CONVERT(DATE, NULLIF(last_day, ''))                           AS LastDay,
    CAST(NULLIF(units, '') AS FLOAT)                              AS Units,
    CAST(NULLIF(unit_of_time, '') AS VARCHAR(10))                 AS UnitOfTime,
    CAST(NULLIF(days_requested, '') AS FLOAT)                     AS DaysRequested,
    CAST(NULLIF(corrects_request_id, '') AS VARCHAR(20))          AS CorrectsRequestID,
    CAST(status AS VARCHAR(20))                                   AS Status,
    CONVERT(DATETIME2(0), NULLIF(created_at, ''))                 AS CreatedAt,
    CONVERT(DATETIME2(0), NULLIF(approved_at, ''))                AS ApprovedAt
INTO dw.TimeOffRequest
FROM raw.ks_time_off_request;

DROP TABLE IF EXISTS dw.LeaveOfAbsence;
SELECT
    CAST(leave_id AS VARCHAR(20))                                 AS LeaveID,
    CAST(worker_id AS VARCHAR(20))                                AS WorkerID,
    CAST(leave_type AS VARCHAR(40))                               AS LeaveType,
    CAST(status AS VARCHAR(20))                                   AS Status,
    CONVERT(DATE, NULLIF(initiated_date, ''))                     AS InitiatedDate,
    CONVERT(DATE, NULLIF(approved_date, ''))                      AS ApprovedDate,
    CONVERT(DATE, NULLIF(last_day_of_work, ''))                   AS LastDayOfWork,
    CONVERT(DATE, NULLIF(first_day_of_leave, ''))                 AS FirstDayOfLeave,
    CONVERT(DATE, NULLIF(estimated_last_day_of_leave, ''))        AS EstimatedLastDayOfLeave,
    CONVERT(DATE, NULLIF(actual_last_day_of_leave, ''))           AS ActualLastDayOfLeave,
    CONVERT(DATE, NULLIF(first_day_back_at_work, ''))             AS FirstDayBackAtWork,
    CAST(NULLIF(total_days_on_leave, '') AS INT)                  AS TotalDaysOnLeave,
    CAST(CASE LOWER(is_estimated) WHEN 'true' THEN 1 ELSE 0 END AS BIT) AS IsEstimated
INTO dw.LeaveOfAbsence
FROM raw.ks_leave_of_absence;

DROP TABLE IF EXISTS dw.BwTimeOff;
SELECT
    CAST(booking_id AS VARCHAR(20))                               AS BookingID,
    CAST(bw_worker_id AS VARCHAR(20))                             AS BwWorkerID,
    CAST(service_order_id AS VARCHAR(20))                         AS ServiceOrderID,
    CAST(booking_type AS VARCHAR(30))                             AS BookingType,
    CONVERT(DATE, NULLIF(first_day, ''))                          AS FirstDay,
    CONVERT(DATE, NULLIF(last_day, ''))                           AS LastDay,
    CAST(NULLIF(working_days, '') AS INT)                         AS WorkingDays,
    CAST(NULLIF(hours, '') AS FLOAT)                              AS Hours,
    CAST(status AS VARCHAR(20))                                   AS Status,
    CONVERT(DATETIME2(0), NULLIF(submitted_at, ''))               AS SubmittedAt,
    CONVERT(DATETIME2(0), NULLIF(approved_at, ''))                AS ApprovedAt
INTO dw.BwTimeOff
FROM raw.bw_time_off;

DROP TABLE IF EXISTS dw.RefJobFamilyHome;
SELECT
    CAST(job_family_code AS VARCHAR(10))                          AS JobFamilyCode,
    CAST(home_function AS VARCHAR(60))                            AS HomeFunction,
    CAST(CASE LOWER(is_shared) WHEN 'true' THEN 1 ELSE 0 END AS BIT) AS IsShared
INTO dw.RefJobFamilyHome
FROM raw.ref_job_family_home;

DROP TABLE IF EXISTS dw.RefPublicHoliday;
SELECT
    CAST(country_code AS VARCHAR(3))                              AS CountryCode,
    CONVERT(DATE, holiday_date)                                   AS HolidayDate,
    CAST(holiday_name AS NVARCHAR(80))                            AS HolidayName,
    CAST(source AS VARCHAR(40))                                   AS Source
INTO dw.RefPublicHoliday
FROM raw.ref_public_holiday;

DROP TABLE IF EXISTS dw.GenOrgDriftTruth;
SELECT
    CAST(drift_id AS VARCHAR(20))                                 AS DriftID,
    CAST(signal_code AS VARCHAR(4))                               AS SignalCode,
    CAST(cause AS VARCHAR(40))                                    AS Cause,
    CAST(NULLIF(person_id, '') AS VARCHAR(20))                    AS PersonID,
    CAST(NULLIF(matrix_org_id, '') AS VARCHAR(20))                AS MatrixOrgID,
    CAST(NULLIF(assignment_id, '') AS VARCHAR(20))                AS AssignmentID,
    CAST(NULLIF(job_record_ids, '') AS VARCHAR(400))              AS JobRecordIDs,
    CAST(NULLIF(original_values, '') AS VARCHAR(400))             AS OriginalValues,
    CAST(NULLIF(seeded_value, '') AS VARCHAR(60))                 AS SeededValue,
    CONVERT(DATE, NULLIF(start_date, ''))                         AS StartDate,
    CONVERT(DATE, NULLIF(end_date, ''))                           AS EndDate,
    CAST(NULLIF(detail, '') AS VARCHAR(200))                      AS Detail
INTO dw.GenOrgDriftTruth
FROM raw.gen_org_drift_truth;

/* 0 to 9,999: one row per day offset, to spread a request or a leave over its days */
DROP TABLE IF EXISTS dw.RefDayNumber;
SELECT a.d + 10 * b.d + 100 * c.d + 1000 * e.d AS N
INTO dw.RefDayNumber
FROM (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) AS a (d)
CROSS JOIN (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) AS b (d)
CROSS JOIN (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) AS c (d)
CROSS JOIN (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9)) AS e (d);
GO

/* ------------------------------------------------------------------ PersonMonthEnd
   The 13 month-ends that end on the report date. Employees from the month-end snapshot,
   executive officers flagged (they lead, but stay out of every count). Contingent workers from
   Bridgeway (11,941 on the report date, as on Dashboards #1 and #4); their manager and
   department from the Keystone record in effect that day, else the Bridgeway hiring manager
   (matched on work email). Either way the manager must be an employee that month-end. */
DROP TABLE IF EXISTS #Months;
SELECT c.MonthEndDate, c.FiscalYear
INTO #Months
FROM dw.MonthEndCalendar AS c
CROSS JOIN fc.report_calendar AS rc
WHERE c.MonthEndDate <= rc.report_as_of_date
  AND c.MonthEndDate >= EOMONTH(DATEADD(MONTH, -12, rc.report_as_of_date));

DROP TABLE IF EXISTS #Emp;
SELECT s.MonthEndDate, s.FiscalYear, s.WorkerID AS PersonID,
       CAST('Employee' AS VARCHAR(12))                    AS WorkerType,
       CAST(NULL AS VARCHAR(20))                          AS BwWorkerID,
       CAST(CONCAT(w.FirstName, ' ', w.LastName) AS NVARCHAR(100)) AS PersonName,
       CAST(jp.JobTitle AS VARCHAR(100))                  AS JobTitle,
       s.DepartmentID, s.DepartmentID                     AS KeystoneDepartmentID,
       s.LocationID, s.LocationID                         AS KeystoneLocationID,
       s.JobProfileID, jp.JobFamilyCode, s.Grade, s.ManagerWorkerID,
       CAST('Keystone' AS VARCHAR(30))                    AS ManagerSource,
       s.IsPeopleManager, s.LeadsOrgUnitID, s.IsExecutiveOfficer,
       CAST(1 AS BIT)                                     AS HasKeystoneRecord
INTO #Emp
FROM dw.WorkerMonthEndSnapshot AS s
JOIN #Months AS m ON m.MonthEndDate = s.MonthEndDate
JOIN dw.DimWorker AS w ON w.WorkerID = s.WorkerID
LEFT JOIN dw.DimJobProfile AS jp ON jp.JobProfileID = s.JobProfileID;

DROP TABLE IF EXISTS #CwKs;
SELECT x.MonthEndDate, x.FiscalYear, x.BwWorkerID, x.BwDepartmentID, x.LocationID, x.RevisionID, x.KsPersonID,
       x.KsDepartmentID, x.KsLocationID, x.KsManagerWorkerID
INTO #CwKs
FROM (
    SELECT b.MonthEndDate, b.FiscalYear, b.BwWorkerID, b.DepartmentID AS BwDepartmentID, b.LocationID, b.RevisionID,
           ir.PersonID AS KsPersonID, k.DepartmentID AS KsDepartmentID, k.LocationID AS KsLocationID,
           k.ManagerWorkerID AS KsManagerWorkerID,
           ROW_NUMBER() OVER (PARTITION BY b.MonthEndDate, b.BwWorkerID
                              ORDER BY k.EffectiveStartDate DESC, k.KsRecordID DESC) AS rn
    FROM dw.CwMonthEndSnapshot AS b
    JOIN #Months AS m ON m.MonthEndDate = b.MonthEndDate
    LEFT JOIN dw.CwIdentityResolution AS ir ON ir.BwWorkerID = b.BwWorkerID AND ir.PersonID IS NOT NULL
    LEFT JOIN dw.KsContingentWorker AS k
           ON k.PersonID = ir.PersonID AND k.Status = 'Active'
          AND b.MonthEndDate BETWEEN k.EffectiveStartDate AND k.EffectiveEndDateFilled
) AS x
WHERE x.rn = 1;

DROP TABLE IF EXISTS #Cw;
SELECT c.MonthEndDate, c.FiscalYear,
       ISNULL(c.KsPersonID, c.BwWorkerID)                 AS PersonID,
       CAST('Contingent' AS VARCHAR(12))                  AS WorkerType,
       c.BwWorkerID,
       CAST(CONCAT(bw.FirstName, ' ', bw.LastName) AS NVARCHAR(100)) AS PersonName,
       CAST(r.JobTitle AS VARCHAR(100))                   AS JobTitle,
       ISNULL(c.KsDepartmentID, c.BwDepartmentID)         AS DepartmentID,
       c.KsDepartmentID                                   AS KeystoneDepartmentID,
       c.LocationID,
       c.KsLocationID                                     AS KeystoneLocationID,
       CAST(NULL AS VARCHAR(20))                          AS JobProfileID,
       CAST(NULL AS VARCHAR(10))                          AS JobFamilyCode,
       CAST(NULL AS INT)                                  AS Grade,
       CASE WHEN ke.PersonID IS NOT NULL THEN c.KsManagerWorkerID
            WHEN be.PersonID IS NOT NULL THEN hm.WorkerID END AS ManagerWorkerID,
       CAST(CASE WHEN ke.PersonID IS NOT NULL THEN 'Keystone'
                 WHEN be.PersonID IS NOT NULL THEN 'Bridgeway hiring manager' END AS VARCHAR(30)) AS ManagerSource,
       CAST(0 AS BIT)                                     AS IsPeopleManager,
       CAST(NULL AS VARCHAR(20))                          AS LeadsOrgUnitID,
       CAST(0 AS BIT)                                     AS IsExecutiveOfficer,
       CAST(CASE WHEN c.KsDepartmentID IS NOT NULL THEN 1 ELSE 0 END AS BIT) AS HasKeystoneRecord
INTO #Cw
FROM #CwKs AS c
JOIN dw.BwServiceOrderRevision AS r ON r.RevisionID = c.RevisionID
JOIN dw.BwContingentWorker AS bw ON bw.BwWorkerID = c.BwWorkerID
LEFT JOIN dw.DimWorker AS hm ON hm.WorkEmail = r.HiringManagerEmail
LEFT JOIN #Emp AS ke ON ke.MonthEndDate = c.MonthEndDate AND ke.PersonID = c.KsManagerWorkerID
LEFT JOIN #Emp AS be ON be.MonthEndDate = c.MonthEndDate AND be.PersonID = hm.WorkerID;

DROP TABLE IF EXISTS dw.PersonMonthEnd;
SELECT p.MonthEndDate, p.FiscalYear, p.PersonID, p.WorkerType, p.BwWorkerID, p.PersonName, p.JobTitle,
       p.DepartmentID, p.KeystoneDepartmentID, p.LocationID, p.KeystoneLocationID, p.JobProfileID, p.JobFamilyCode,
       p.Grade, p.ManagerWorkerID, p.ManagerSource, p.IsPeopleManager, p.LeadsOrgUnitID, p.IsExecutiveOfficer,
       p.HasKeystoneRecord, loc.CountryCode, loc.Region, d.FunctionName, d.DepartmentName
INTO dw.PersonMonthEnd
FROM (SELECT * FROM #Emp UNION ALL SELECT * FROM #Cw) AS p
JOIN dw.DimLocation AS loc ON loc.LocationID = p.LocationID
LEFT JOIN dw.DimDepartment AS d ON d.DepartmentID = p.DepartmentID;
CREATE CLUSTERED INDEX CIX_PersonMonthEnd ON dw.PersonMonthEnd (MonthEndDate, PersonID);
GO

/* ------------------------------------------------------------------ OrgClosure
   One row per month-end x ancestor x descendant, plus each person with themselves at depth 0.
   Built one level at a time: level n+1 = level n's ancestors' own managers. */
DROP TABLE IF EXISTS #Edge;
SELECT MonthEndDate, PersonID, ManagerWorkerID
INTO #Edge
FROM dw.PersonMonthEnd
WHERE ManagerWorkerID IS NOT NULL;
CREATE CLUSTERED INDEX CIX_Edge ON #Edge (MonthEndDate, PersonID);

DROP TABLE IF EXISTS dw.OrgClosure;
SELECT MonthEndDate, ManagerWorkerID AS AncestorID, PersonID AS DescendantID, 1 AS Depth
INTO dw.OrgClosure
FROM #Edge;

INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 2 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 1;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 3 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 2;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 4 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 3;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 5 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 4;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 6 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 5;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 7 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 6;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 8 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 7;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 9 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 8;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 10 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 9;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 11 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 10;
INSERT INTO dw.OrgClosure SELECT c.MonthEndDate, e.ManagerWorkerID, c.DescendantID, 12 FROM dw.OrgClosure AS c JOIN #Edge AS e ON e.MonthEndDate = c.MonthEndDate AND e.PersonID = c.AncestorID WHERE c.Depth = 11;
INSERT INTO dw.OrgClosure SELECT MonthEndDate, PersonID, PersonID, 0 FROM dw.PersonMonthEnd;
CREATE CLUSTERED INDEX CIX_OrgClosure ON dw.OrgClosure (MonthEndDate, AncestorID, DescendantID);
GO

/* ------------------------------------------------------------------ OrgLeader
   L0 Executive Leadership (the executive officers), L1 people managers who report to one, L2
   people managers who report to an L1, Manager every other people manager. Path is the chain
   from the top, |W100001|..|me|, the string the Information Lab org-chart technique filters on. */
DROP TABLE IF EXISTS #Lead;
SELECT * INTO #Lead FROM dw.PersonMonthEnd WHERE IsPeopleManager = 1 OR IsExecutiveOfficer = 1;

DROP TABLE IF EXISTS #Anc;
SELECT c.MonthEndDate, c.DescendantID AS PersonID,
       SUM(CASE WHEN c.Depth > 0 THEN 1 ELSE 0 END)                                AS DepthFromTop,
       CAST(CONCAT('|', STRING_AGG(c.AncestorID, '|') WITHIN GROUP (ORDER BY c.Depth DESC), '|') AS VARCHAR(400)) AS Path
INTO #Anc
FROM dw.OrgClosure AS c
JOIN #Lead AS p ON p.MonthEndDate = c.MonthEndDate AND p.PersonID = c.DescendantID
GROUP BY c.MonthEndDate, c.DescendantID;

DROP TABLE IF EXISTS dw.OrgLeader;
SELECT p.MonthEndDate, p.PersonID AS LeaderID, p.PersonName AS LeaderName, p.JobTitle, p.Grade,
       CAST(CASE WHEN p.IsExecutiveOfficer = 1 THEN 'L0'
                 WHEN m.IsExecutiveOfficer = 1 THEN 'L1'
                 WHEN m.IsPeopleManager = 1 AND mm.IsExecutiveOfficer = 1 THEN 'L2'
                 ELSE 'Manager' END AS VARCHAR(8))                      AS LeaderLevel,
       p.ManagerWorkerID AS ParentLeaderID, a.DepthFromTop, a.Path,
       p.DepartmentID, p.DepartmentName, p.FunctionName, p.LocationID, p.CountryCode, p.Region,
       p.LeadsOrgUnitID, p.IsExecutiveOfficer
INTO dw.OrgLeader
FROM #Lead AS p
JOIN #Anc AS a ON a.MonthEndDate = p.MonthEndDate AND a.PersonID = p.PersonID
LEFT JOIN dw.PersonMonthEnd AS m ON m.MonthEndDate = p.MonthEndDate AND m.PersonID = p.ManagerWorkerID
LEFT JOIN dw.PersonMonthEnd AS mm ON mm.MonthEndDate = m.MonthEndDate AND mm.PersonID = m.ManagerWorkerID;
CREATE CLUSTERED INDEX CIX_OrgLeader ON dw.OrgLeader (MonthEndDate, LeaderID);
GO

/* ------------------------------------------------------------------ AlignmentSignal
   A flag, never an error; executive officers left out; leading people in other regions is
   never a signal.
     S1 Budgeted in another org: the manager sits in another department (org-unit leaders exempt)
     S2 Role from another function: the job family's home function is not the department's
     M1 Country leader for another country: no country matrix covers the Keystone country
     M2 In two country matrices, or none
     M3 Matrix inactive or without a leader
   Matrix signals apply to people Keystone holds. */
DROP TABLE IF EXISTS #Kp;
SELECT p.MonthEndDate, p.PersonID, l.CountryCode AS KsCountryCode
INTO #Kp
FROM dw.PersonMonthEnd AS p
JOIN dw.DimLocation AS l ON l.LocationID = p.KeystoneLocationID
WHERE p.IsExecutiveOfficer = 0 AND p.HasKeystoneRecord = 1;

DROP TABLE IF EXISTS #Mem;
SELECT kp.MonthEndDate, kp.PersonID, kp.KsCountryCode, mm.MatrixOrgID, o.MatrixOrgName, o.Status, o.ManagerWorkerID,
       CASE WHEN CONCAT(';', o.CoversCountryCodes, ';') LIKE CONCAT('%;', kp.KsCountryCode, ';%') THEN 1 ELSE 0 END AS Covers
INTO #Mem
FROM #Kp AS kp
JOIN dw.MatrixMembership AS mm
  ON mm.PersonID = kp.PersonID AND kp.MonthEndDate BETWEEN mm.EffectiveStartDate AND mm.EffectiveEndDateFilled
JOIN dw.MatrixOrg AS o
  ON o.MatrixOrgID = mm.MatrixOrgID AND kp.MonthEndDate BETWEEN o.EffectiveStartDate AND o.EffectiveEndDateFilled;

DROP TABLE IF EXISTS #PerPerson;
SELECT kp.MonthEndDate, kp.PersonID, kp.KsCountryCode,
       COUNT(mem.MatrixOrgID)                                                    AS NMatrices,
       ISNULL(MAX(mem.Covers), 0)                                                AS AnyCovers,
       STRING_AGG(mem.MatrixOrgName, '; ') WITHIN GROUP (ORDER BY mem.MatrixOrgID) AS Matrices
INTO #PerPerson
FROM #Kp AS kp
LEFT JOIN #Mem AS mem ON mem.MonthEndDate = kp.MonthEndDate AND mem.PersonID = kp.PersonID
GROUP BY kp.MonthEndDate, kp.PersonID, kp.KsCountryCode;

DROP TABLE IF EXISTS dw.AlignmentSignal;
SELECT s.MonthEndDate, s.PersonID, CAST(s.SignalCode AS VARCHAR(4)) AS SignalCode,
       CAST(s.SignalDetail AS NVARCHAR(300)) AS SignalDetail,
       CAST(g.SignalName AS VARCHAR(60)) AS SignalName, CAST(g.SignalLine AS VARCHAR(20)) AS SignalLine
INTO dw.AlignmentSignal
FROM (
    SELECT p.MonthEndDate, p.PersonID, 'S1' AS SignalCode,
           CONCAT('Manager ', m.PersonName, ' sits in ', md.DepartmentName) AS SignalDetail
    FROM dw.PersonMonthEnd AS p
    JOIN dw.PersonMonthEnd AS m ON m.MonthEndDate = p.MonthEndDate AND m.PersonID = p.ManagerWorkerID
    JOIN dw.DimDepartment AS md ON md.DepartmentID = m.DepartmentID
    WHERE p.IsExecutiveOfficer = 0 AND p.LeadsOrgUnitID IS NULL
      AND p.KeystoneDepartmentID IS NOT NULL AND m.DepartmentID <> p.KeystoneDepartmentID
    UNION ALL
    SELECT p.MonthEndDate, p.PersonID, 'S2',
           CONCAT(jp.JobFamily, ' role, usually hired by ', h.HomeFunction)
    FROM dw.PersonMonthEnd AS p
    JOIN dw.RefJobFamilyHome AS h ON h.JobFamilyCode = p.JobFamilyCode
    JOIN dw.DimJobProfile AS jp ON jp.JobProfileID = p.JobProfileID
    WHERE p.IsExecutiveOfficer = 0 AND p.WorkerType = 'Employee' AND h.IsShared = 0
      AND p.FunctionName <> 'Executive' AND h.HomeFunction <> p.FunctionName
    UNION ALL
    SELECT MonthEndDate, PersonID, 'M1', CONCAT('Sits in ', KsCountryCode, '; matrix: ', Matrices)
    FROM #PerPerson WHERE NMatrices >= 1 AND AnyCovers = 0
    UNION ALL
    SELECT MonthEndDate, PersonID, 'M2',
           CASE WHEN NMatrices = 0 THEN 'No country matrix'
                ELSE CONCAT(NMatrices, ' country matrices: ', Matrices) END
    FROM #PerPerson WHERE NMatrices <> 1
    UNION ALL
    SELECT MonthEndDate, PersonID, 'M3',
           STRING_AGG(CONCAT(MatrixOrgName, CASE WHEN Status = 'Inactive' THEN ' has ended' ELSE ' has no leader' END), '; ')
               WITHIN GROUP (ORDER BY MatrixOrgID)
    FROM #Mem WHERE Status = 'Inactive' OR ManagerWorkerID IS NULL
    GROUP BY MonthEndDate, PersonID
) AS s
JOIN (VALUES ('S1', 'Budgeted in another org', 'Solid line'),
             ('S2', 'Role from another function', 'Solid line'),
             ('M1', 'Country leader for another country', 'Matrix line'),
             ('M2', 'In two country matrices, or none', 'Matrix line'),
             ('M3', 'Matrix inactive or without a leader', 'Matrix line'))
     AS g (SignalCode, SignalName, SignalLine) ON g.SignalCode = s.SignalCode;
CREATE CLUSTERED INDEX CIX_AlignmentSignal ON dw.AlignmentSignal (MonthEndDate, PersonID);

/* R1: a role assignment in effect that names someone other than the org unit's leader today */
DROP TABLE IF EXISTS dw.AssignmentSignal;
SELECT m.MonthEndDate, a.AssignmentID, a.RoleName, a.AssigneeWorkerID, a.TargetOrgUnitID, a.TargetOrgName,
       a.NamedLeaderWorkerID, a.AssignedVia, cl.PersonID AS CurrentLeaderID,
       CAST('R1' AS VARCHAR(4)) AS SignalCode, CAST('Still naming a former leader' AS VARCHAR(60)) AS SignalName,
       CAST('Role assignments' AS VARCHAR(20)) AS SignalLine
INTO dw.AssignmentSignal
FROM (SELECT DISTINCT MonthEndDate FROM dw.PersonMonthEnd) AS m
JOIN dw.RoleAssignment AS a ON m.MonthEndDate BETWEEN a.EffectiveStartDate AND a.EffectiveEndDateFilled
JOIN dw.PersonMonthEnd AS cl ON cl.MonthEndDate = m.MonthEndDate AND cl.LeadsOrgUnitID = a.TargetOrgUnitID
WHERE ISNULL(a.NamedLeaderWorkerID, '') <> cl.PersonID;
GO

/* ------------------------------------------------------------------ LeaderOrg
   Each leader's organization per month-end and worker type (All, Employees, Contingent):
   size, directs and indirects, layers, countries, spans, and the people with a signal. */
DROP TABLE IF EXISTS #Wt;
SELECT WorkerType INTO #Wt FROM (VALUES ('All'), ('Employees'), ('Contingent')) AS t (WorkerType);

DROP TABLE IF EXISTS #Flags;
SELECT MonthEndDate, PersonID,
       MAX(CASE WHEN SignalCode = 'S1' THEN 1 ELSE 0 END) AS S1, MAX(CASE WHEN SignalCode = 'S2' THEN 1 ELSE 0 END) AS S2,
       MAX(CASE WHEN SignalCode = 'M1' THEN 1 ELSE 0 END) AS M1, MAX(CASE WHEN SignalCode = 'M2' THEN 1 ELSE 0 END) AS M2,
       MAX(CASE WHEN SignalCode = 'M3' THEN 1 ELSE 0 END) AS M3
INTO #Flags
FROM dw.AlignmentSignal
GROUP BY MonthEndDate, PersonID;

DROP TABLE IF EXISTS #Below;
SELECT c.MonthEndDate, c.AncestorID AS LeaderID, c.Depth, d.PersonID, d.WorkerType AS PersonType,
       CAST(d.IsPeopleManager AS INT) AS IsPeopleManager, d.CountryCode,
       ISNULL(f.S1, 0) AS S1, ISNULL(f.S2, 0) AS S2, ISNULL(f.M1, 0) AS M1, ISNULL(f.M2, 0) AS M2, ISNULL(f.M3, 0) AS M3
INTO #Below
FROM dw.OrgClosure AS c
JOIN dw.OrgLeader AS l ON l.MonthEndDate = c.MonthEndDate AND l.LeaderID = c.AncestorID
JOIN dw.PersonMonthEnd AS d ON d.MonthEndDate = c.MonthEndDate AND d.PersonID = c.DescendantID
LEFT JOIN #Flags AS f ON f.MonthEndDate = c.MonthEndDate AND f.PersonID = c.DescendantID
WHERE c.Depth >= 1 AND d.IsExecutiveOfficer = 0;

DROP TABLE IF EXISTS #Size;
SELECT b.MonthEndDate, b.LeaderID, wt.WorkerType,
       COUNT(*)                                                                    AS People,
       SUM(CASE WHEN b.Depth = 1 THEN 1 ELSE 0 END)                                AS Directs,
       SUM(CASE WHEN b.Depth > 1 THEN 1 ELSE 0 END)                                AS Indirects,
       SUM(b.IsPeopleManager)                                                      AS ManagersBelow,
       MAX(b.Depth)                                                                AS LayersBelow,
       COUNT(DISTINCT b.CountryCode)                                               AS Countries,
       SUM(CASE WHEN b.S1 + b.S2 + b.M1 + b.M2 + b.M3 > 0 THEN 1 ELSE 0 END)       AS GapPeople,
       SUM(CASE WHEN b.S1 + b.S2 > 0 THEN 1 ELSE 0 END)                            AS SolidLineGapPeople,
       SUM(CASE WHEN b.M1 + b.M2 + b.M3 > 0 THEN 1 ELSE 0 END)                     AS MatrixGapPeople,
       SUM(b.S1) AS S1BudgetedElsewhere, SUM(b.S2) AS S2RoleOtherFunction, SUM(b.M1) AS M1CountryLeaderOtherCountry,
       SUM(b.M2) AS M2NotOneCountryMatrix, SUM(b.M3) AS M3MatrixInactiveOrLeaderless
INTO #Size
FROM #Below AS b
JOIN #Wt AS wt ON wt.WorkerType = 'All'
              OR (wt.WorkerType = 'Employees' AND b.PersonType = 'Employee')
              OR (wt.WorkerType = 'Contingent' AND b.PersonType = 'Contingent')
GROUP BY b.MonthEndDate, b.LeaderID, wt.WorkerType;

DROP TABLE IF EXISTS #DirectCount;
SELECT p.MonthEndDate, p.ManagerWorkerID AS ManagerID, wt.WorkerType, COUNT(*) AS Span
INTO #DirectCount
FROM dw.PersonMonthEnd AS p
JOIN #Wt AS wt ON wt.WorkerType = 'All'
              OR (wt.WorkerType = 'Employees' AND p.WorkerType = 'Employee')
              OR (wt.WorkerType = 'Contingent' AND p.WorkerType = 'Contingent')
WHERE p.ManagerWorkerID IS NOT NULL AND p.IsExecutiveOfficer = 0
GROUP BY p.MonthEndDate, p.ManagerWorkerID, wt.WorkerType;

DROP TABLE IF EXISTS #Spans;
SELECT x.MonthEndDate, x.LeaderID, x.WorkerType, MAX(x.MedianSpan) AS MedianSpan,
       AVG(CAST(x.Span AS FLOAT)) AS AverageSpan,
       SUM(CASE WHEN x.Span >= 15 THEN 1 ELSE 0 END) AS Managers15Plus,
       SUM(CASE WHEN x.Span = 1 THEN 1 ELSE 0 END) AS ManagersOneDirect
INTO #Spans
FROM (
    SELECT c.MonthEndDate, c.AncestorID AS LeaderID, dc.WorkerType, dc.Span,
           PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY dc.Span)
               OVER (PARTITION BY c.MonthEndDate, c.AncestorID, dc.WorkerType) AS MedianSpan
    FROM dw.OrgClosure AS c
    JOIN dw.OrgLeader AS l ON l.MonthEndDate = c.MonthEndDate AND l.LeaderID = c.AncestorID
    JOIN #DirectCount AS dc ON dc.MonthEndDate = c.MonthEndDate AND dc.ManagerID = c.DescendantID
) AS x
GROUP BY x.MonthEndDate, x.LeaderID, x.WorkerType;

DROP TABLE IF EXISTS #Assign;
SELECT c.MonthEndDate, c.AncestorID AS LeaderID, COUNT(DISTINCT a.AssignmentID) AS AssignmentsNamingFormerLeader
INTO #Assign
FROM dw.OrgClosure AS c
JOIN dw.AssignmentSignal AS a ON a.MonthEndDate = c.MonthEndDate AND a.CurrentLeaderID = c.DescendantID
GROUP BY c.MonthEndDate, c.AncestorID;

DROP TABLE IF EXISTS dw.LeaderOrg;
SELECT l.MonthEndDate, l.LeaderID, l.LeaderLevel, wt.WorkerType,
       ISNULL(s.People, 0) AS People, ISNULL(s.Directs, 0) AS Directs, ISNULL(s.Indirects, 0) AS Indirects,
       ISNULL(s.ManagersBelow, 0) AS ManagersBelow, ISNULL(s.LayersBelow, 0) AS LayersBelow,
       ISNULL(s.Countries, 0) AS Countries, sp.MedianSpan, sp.AverageSpan,
       ISNULL(sp.Managers15Plus, 0) AS Managers15Plus, ISNULL(sp.ManagersOneDirect, 0) AS ManagersOneDirect,
       ISNULL(s.GapPeople, 0) AS GapPeople, ISNULL(s.SolidLineGapPeople, 0) AS SolidLineGapPeople,
       ISNULL(s.MatrixGapPeople, 0) AS MatrixGapPeople,
       ISNULL(s.S1BudgetedElsewhere, 0) AS S1BudgetedElsewhere, ISNULL(s.S2RoleOtherFunction, 0) AS S2RoleOtherFunction,
       ISNULL(s.M1CountryLeaderOtherCountry, 0) AS M1CountryLeaderOtherCountry,
       ISNULL(s.M2NotOneCountryMatrix, 0) AS M2NotOneCountryMatrix,
       ISNULL(s.M3MatrixInactiveOrLeaderless, 0) AS M3MatrixInactiveOrLeaderless,
       ISNULL(a.AssignmentsNamingFormerLeader, 0) AS AssignmentsNamingFormerLeader
INTO dw.LeaderOrg
FROM dw.OrgLeader AS l
CROSS JOIN #Wt AS wt
LEFT JOIN #Size AS s ON s.MonthEndDate = l.MonthEndDate AND s.LeaderID = l.LeaderID AND s.WorkerType = wt.WorkerType
LEFT JOIN #Spans AS sp ON sp.MonthEndDate = l.MonthEndDate AND sp.LeaderID = l.LeaderID AND sp.WorkerType = wt.WorkerType
LEFT JOIN #Assign AS a ON a.MonthEndDate = l.MonthEndDate AND a.LeaderID = l.LeaderID;
CREATE CLUSTERED INDEX CIX_LeaderOrg ON dw.LeaderOrg (MonthEndDate, LeaderID, WorkerType);
GO

/* ------------------------------------------------------------------ TimeOffDay
   One row per person per weekday off, from the start of the fiscal year to 60 days after the
   report date. Employees: approved absence requests of a full day or more, less the days a
   correction gave back; leaves of absence (the actual last day once known). Contingent workers:
   their Bridgeway bookings (Bridgeway is where they book; Keystone gets a copy). A day with both
   counts once, as leave. */
DROP TABLE IF EXISTS #Window;
SELECT DATEFROMPARTS(current_fiscal_year - 1, 7, 1) AS WindowStart, DATEADD(DAY, 60, report_as_of_date) AS WindowEnd
INTO #Window
FROM fc.report_calendar;

DROP TABLE IF EXISTS #Back;
SELECT DISTINCT r.PersonID, DATEADD(DAY, n.N, r.FirstDay) AS OffDate
INTO #Back
FROM dw.TimeOffRequest AS r
JOIN dw.RefDayNumber AS n ON n.N <= DATEDIFF(DAY, r.FirstDay, r.LastDay)
WHERE r.SourceSystem = 'KS' AND r.RequestType = 'Absence Correction';

DROP TABLE IF EXISTS #OffDay;
SELECT r.PersonID, CAST('Employee' AS VARCHAR(12)) AS WorkerType, DATEADD(DAY, n.N, r.FirstDay) AS OffDate,
       CAST('Time off' AS VARCHAR(20)) AS OffReason, r.TimeOffRequestID AS SourceID
INTO #OffDay
FROM dw.TimeOffRequest AS r
CROSS JOIN #Window AS w
JOIN dw.RefDayNumber AS n ON n.N <= DATEDIFF(DAY, r.FirstDay, r.LastDay)
WHERE r.SourceSystem = 'KS' AND r.RequestType = 'Absence Request' AND r.DaysRequested >= 1
  AND DATEDIFF(DAY, '1900-01-01', DATEADD(DAY, n.N, r.FirstDay)) % 7 < 5
  AND DATEADD(DAY, n.N, r.FirstDay) BETWEEN w.WindowStart AND w.WindowEnd
  AND NOT EXISTS (SELECT 1 FROM #Back AS b WHERE b.PersonID = r.PersonID AND b.OffDate = DATEADD(DAY, n.N, r.FirstDay));

INSERT INTO #OffDay
SELECT l.WorkerID, 'Employee', DATEADD(DAY, n.N, l.FirstDayOfLeave), 'Leave', l.LeaveID
FROM dw.LeaveOfAbsence AS l
CROSS JOIN #Window AS w
JOIN dw.RefDayNumber AS n ON n.N <= DATEDIFF(DAY, l.FirstDayOfLeave, ISNULL(l.ActualLastDayOfLeave, l.EstimatedLastDayOfLeave))
WHERE DATEDIFF(DAY, '1900-01-01', DATEADD(DAY, n.N, l.FirstDayOfLeave)) % 7 < 5
  AND DATEADD(DAY, n.N, l.FirstDayOfLeave) BETWEEN w.WindowStart AND w.WindowEnd;

INSERT INTO #OffDay
SELECT ISNULL(ir.PersonID, b.BwWorkerID), 'Contingent', DATEADD(DAY, n.N, b.FirstDay), 'Time off', b.BookingID
FROM dw.BwTimeOff AS b
CROSS JOIN #Window AS w
JOIN dw.RefDayNumber AS n ON n.N <= DATEDIFF(DAY, b.FirstDay, b.LastDay)
LEFT JOIN dw.CwIdentityResolution AS ir ON ir.BwWorkerID = b.BwWorkerID AND ir.PersonID IS NOT NULL
WHERE DATEDIFF(DAY, '1900-01-01', DATEADD(DAY, n.N, b.FirstDay)) % 7 < 5
  AND DATEADD(DAY, n.N, b.FirstDay) BETWEEN w.WindowStart AND w.WindowEnd;

DROP TABLE IF EXISTS dw.TimeOffDay;
SELECT PersonID, WorkerType, OffDate, OffReason, SourceID
INTO dw.TimeOffDay
FROM (
    SELECT o.*, ROW_NUMBER() OVER (PARTITION BY o.PersonID, o.OffDate
                                   ORDER BY CASE o.OffReason WHEN 'Leave' THEN 1 ELSE 2 END, o.SourceID) AS rn
    FROM #OffDay AS o
) AS x
WHERE x.rn = 1;
CREATE CLUSTERED INDEX CIX_TimeOffDay ON dw.TimeOffDay (PersonID, OffDate);
GO

/* ------------------------------------------------------------------ PersonAvailabilityDay
   Everyone in the workforce on the report date (executive officers excluded) x the report date
   and the 30 days after it, in the organization of the report date. First match wins:
   Not in the team (terminated, or the Bridgeway assignment ended), Weekend, Public holiday,
   Leave / Time off, At work. */
DROP TABLE IF EXISTS #Days;
SELECT DATEADD(DAY, n.N, rc.report_as_of_date) AS Day, n.N AS DayOffset
INTO #Days
FROM fc.report_calendar AS rc
JOIN dw.RefDayNumber AS n ON n.N <= 30;

DROP TABLE IF EXISTS #Ppl;
SELECT p.PersonID, p.WorkerType, p.CountryCode, w.TerminationDate, s.AssignmentEndDate
INTO #Ppl
FROM dw.PersonMonthEnd AS p
JOIN fc.report_calendar AS rc ON p.MonthEndDate = rc.report_as_of_date
LEFT JOIN dw.DimWorker AS w ON p.WorkerType = 'Employee' AND w.WorkerID = p.PersonID
LEFT JOIN dw.CwMonthEndSnapshot AS s
       ON p.WorkerType = 'Contingent' AND s.MonthEndDate = rc.report_as_of_date AND s.BwWorkerID = p.BwWorkerID
WHERE p.IsExecutiveOfficer = 0;

DROP TABLE IF EXISTS dw.PersonAvailabilityDay;
SELECT ppl.PersonID, ppl.WorkerType, d.Day, d.DayOffset,
       CAST(CASE WHEN (ppl.WorkerType = 'Employee' AND ppl.TerminationDate < d.Day)
                   OR (ppl.WorkerType = 'Contingent' AND ppl.AssignmentEndDate < d.Day) THEN 'Not in the team'
                 WHEN DATEDIFF(DAY, '1900-01-01', d.Day) % 7 >= 5 THEN 'Weekend'
                 WHEN h.HolidayDate IS NOT NULL THEN 'Public holiday'
                 WHEN t.OffReason IS NOT NULL THEN t.OffReason
                 ELSE 'At work' END AS VARCHAR(20)) AS DayStatus
INTO dw.PersonAvailabilityDay
FROM #Ppl AS ppl
CROSS JOIN #Days AS d
LEFT JOIN dw.RefPublicHoliday AS h ON h.CountryCode = ppl.CountryCode AND h.HolidayDate = d.Day
LEFT JOIN dw.TimeOffDay AS t ON t.PersonID = ppl.PersonID AND t.OffDate = d.Day;
CREATE CLUSTERED INDEX CIX_PersonAvailabilityDay ON dw.PersonAvailabilityDay (PersonID, Day);
GO

/* ------------------------------------------------------------------ LeaderAvailability
   The "At work on" calendar: per leader, worker type and day, the people still in the team, at
   work (weekdays only), off by reason, and the people of the report date who have left. */
DROP TABLE IF EXISTS dw.LeaderAvailability;
SELECT b.LeaderID, wt.WorkerType, b.Day, b.DayOffset,
       CAST(CASE WHEN DATEDIFF(DAY, '1900-01-01', b.Day) % 7 >= 5 THEN 1 ELSE 0 END AS BIT) AS IsWeekend,
       SUM(CASE WHEN b.DayStatus <> 'Not in the team' THEN 1 ELSE 0 END)               AS People,
       CASE WHEN DATEDIFF(DAY, '1900-01-01', b.Day) % 7 < 5
            THEN SUM(CASE WHEN b.DayStatus = 'At work' THEN 1 ELSE 0 END) END         AS AtWork,
       SUM(CASE WHEN b.DayStatus IN ('Time off', 'Leave', 'Public holiday') THEN 1 ELSE 0 END) AS Off,
       SUM(CASE WHEN b.DayStatus = 'Time off' THEN 1 ELSE 0 END)                       AS OffTimeOff,
       SUM(CASE WHEN b.DayStatus = 'Leave' THEN 1 ELSE 0 END)                          AS OffLeave,
       SUM(CASE WHEN b.DayStatus = 'Public holiday' THEN 1 ELSE 0 END)                 AS OffPublicHoliday,
       SUM(CASE WHEN b.DayStatus = 'Not in the team' THEN 1 ELSE 0 END)                AS LeftTeam
INTO dw.LeaderAvailability
FROM (
    SELECT c.AncestorID AS LeaderID, a.PersonID, a.WorkerType AS PersonType, a.Day, a.DayOffset, a.DayStatus
    FROM dw.OrgClosure AS c
    JOIN fc.report_calendar AS rc ON c.MonthEndDate = rc.report_as_of_date
    JOIN dw.OrgLeader AS l ON l.MonthEndDate = c.MonthEndDate AND l.LeaderID = c.AncestorID
    JOIN dw.PersonAvailabilityDay AS a ON a.PersonID = c.DescendantID
    WHERE c.Depth >= 1
) AS b
JOIN #Wt AS wt ON wt.WorkerType = 'All'
              OR (wt.WorkerType = 'Employees' AND b.PersonType = 'Employee')
              OR (wt.WorkerType = 'Contingent' AND b.PersonType = 'Contingent')
GROUP BY b.LeaderID, wt.WorkerType, b.Day, b.DayOffset;
CREATE CLUSTERED INDEX CIX_LeaderAvailability ON dw.LeaderAvailability (LeaderID, WorkerType, DayOffset);
GO

/* ------------------------------------------------------------------ OrgNode
   The tree's nodes on the report date: every leader x worker type, with what the circle, the
   KPIs and the tooltip show. */
DROP TABLE IF EXISTS dw.OrgNode;
SELECT l.MonthEndDate AS AsOfDate, l.LeaderID, l.LeaderName, l.JobTitle, l.Grade, l.LeaderLevel,
       CAST(CASE WHEN l.LeaderLevel IN ('L0', 'L1', 'L2') THEN 1 ELSE 0 END AS BIT) AS IsSelectable,
       l.ParentLeaderID, pl.LeaderName AS ParentLeaderName, l.DepthFromTop, l.Path,
       ISNULL(k.ChildLeaders, 0) AS ChildLeaders,
       l.DepartmentName, l.FunctionName, loc.OfficeName, loc.CountryName, l.Region,
       l.LeadsOrgUnitID, ou.OrgUnitName AS LeadsOrgUnitName,
       o.WorkerType, o.People, o.Directs, o.Indirects, o.ManagersBelow, o.LayersBelow, o.Countries,
       o.MedianSpan, o.Managers15Plus, o.ManagersOneDirect,
       o.GapPeople, o.SolidLineGapPeople, o.MatrixGapPeople,
       o.S1BudgetedElsewhere, o.S2RoleOtherFunction, o.M1CountryLeaderOtherCountry,
       o.M2NotOneCountryMatrix, o.M3MatrixInactiveOrLeaderless, o.AssignmentsNamingFormerLeader,
       t.AtWork AS AtWorkToday, t.Off AS OffToday
INTO dw.OrgNode
FROM dw.OrgLeader AS l
JOIN fc.report_calendar AS rc ON l.MonthEndDate = rc.report_as_of_date
JOIN dw.LeaderOrg AS o ON o.MonthEndDate = l.MonthEndDate AND o.LeaderID = l.LeaderID
JOIN dw.DimLocation AS loc ON loc.LocationID = l.LocationID
LEFT JOIN dw.OrgLeader AS pl ON pl.MonthEndDate = l.MonthEndDate AND pl.LeaderID = l.ParentLeaderID
LEFT JOIN (SELECT MonthEndDate, ParentLeaderID, COUNT(*) AS ChildLeaders FROM dw.OrgLeader
           GROUP BY MonthEndDate, ParentLeaderID) AS k
       ON k.MonthEndDate = l.MonthEndDate AND k.ParentLeaderID = l.LeaderID
LEFT JOIN dw.DimOrgUnit AS ou ON ou.OrgUnitID = l.LeadsOrgUnitID
LEFT JOIN dw.LeaderAvailability AS t ON t.LeaderID = l.LeaderID AND t.WorkerType = o.WorkerType AND t.DayOffset = 0;
GO

/* ------------------------------------------------------------------ OrgTreeLayout
   Where every circle and link sits, for every leader as the tree's focus, so Tableau only plots
   x and y. The canvas is x 0 to 1 (left to right) and y 0 to 3 (top to bottom: reverse the axis).

     Dynamic  tier 0 the focus; tier 1 the leaders who report to them, evenly spaced, biggest
              first; tier 2 the leaders under each tier-1 leader, centered under it (the page
              shows one tier-1 leader's row at a time: the open one, the biggest by default)
     Static   tiers 1 to 3 at once: tier 1 at the centers of equal shares of the width, tier 2
              fanned under its parent in a zigzag, tier 3 as small dots under theirs

   A link is the curve from the parent's circle to the child's: a cubic Bezier through
   (x1, y1), (x1, ym), (x2, ym), (x2, y2), drawn as 17 points (PointIndex 0 to 16). */
DROP TABLE IF EXISTS #TreeLeader;
SELECT l.LeaderID, l.ParentLeaderID, l.LeaderName, o.People
INTO #TreeLeader
FROM dw.OrgLeader AS l
JOIN fc.report_calendar AS rc ON l.MonthEndDate = rc.report_as_of_date
JOIN dw.LeaderOrg AS o ON o.MonthEndDate = l.MonthEndDate AND o.LeaderID = l.LeaderID AND o.WorkerType = 'All';

/* each leader's place among the leaders who share its parent: biggest first */
DROP TABLE IF EXISTS #Sib;
SELECT t.LeaderID, t.ParentLeaderID,
       ROW_NUMBER() OVER (PARTITION BY t.ParentLeaderID ORDER BY t.People DESC, t.LeaderName, t.LeaderID) - 1 AS Slot,
       COUNT(*) OVER (PARTITION BY t.ParentLeaderID) AS Slots
INTO #Sib
FROM #TreeLeader AS t
WHERE t.ParentLeaderID IS NOT NULL;

DROP TABLE IF EXISTS #TreeNode;
/* tier 0: the focus */
SELECT 'Dynamic' AS TreeMode, t.LeaderID AS FocusLeaderID, 0 AS Tier, t.LeaderID AS NodeID,
       CAST(NULL AS VARCHAR(20)) AS ParentNodeID, CAST(NULL AS VARCHAR(20)) AS Tier1NodeID,
       0 AS Slot, 1 AS Slots, CAST(0.5 AS FLOAT) AS X, CAST(0 AS FLOAT) AS Y
INTO #TreeNode
FROM #TreeLeader AS t
UNION ALL
SELECT 'Static', t.LeaderID, 0, t.LeaderID, NULL, NULL, 0, 1, 0.5, 0 FROM #TreeLeader AS t;

/* tier 1: the focus's child leaders. Dynamic: evenly spaced from 0.03 to 0.97. Static: each at the
   center of an equal share of the width, so the fan below it stays inside its share */
INSERT INTO #TreeNode
SELECT m.TreeMode, s.ParentLeaderID, 1, s.LeaderID, s.ParentLeaderID, s.LeaderID, s.Slot, s.Slots,
       CASE WHEN m.TreeMode = 'Static' THEN (s.Slot + 0.5) / s.Slots
            WHEN s.Slots = 1 THEN 0.5 ELSE 0.03 + 0.94 * s.Slot / (s.Slots - 1.0) END, 1
FROM #Sib AS s
CROSS JOIN (VALUES ('Dynamic'), ('Static')) AS m (TreeMode);

/* dynamic tier 2: centered under its tier-1 parent, 0.125 apart (closer when there are many),
   kept inside 0.03 to 0.97 */
INSERT INTO #TreeNode
SELECT 'Dynamic', p.FocusLeaderID, 2, s.LeaderID, s.ParentLeaderID, s.ParentLeaderID, s.Slot, s.Slots,
       z.X0 + s.Slot * z.Step, 2
FROM #TreeNode AS p
JOIN #Sib AS s ON s.ParentLeaderID = p.NodeID
CROSS APPLY (SELECT CASE WHEN s.Slots <= 1 THEN 0.125 WHEN 0.94 / (s.Slots - 1.0) < 0.125 THEN 0.94 / (s.Slots - 1.0)
                         ELSE 0.125 END AS Step) AS st
CROSS APPLY (SELECT st.Step AS Step,
                    CASE WHEN p.X - (s.Slots - 1) / 2.0 * st.Step < 0.03 THEN 0.03
                         WHEN p.X + (s.Slots - 1) / 2.0 * st.Step > 0.97 THEN 0.97 - (s.Slots - 1) * st.Step
                         ELSE p.X - (s.Slots - 1) / 2.0 * st.Step END AS X0) AS z
WHERE p.TreeMode = 'Dynamic' AND p.Tier = 1;

/* static tier 2: fanned under its parent within the parent's share of the width, zigzag in y */
INSERT INTO #TreeNode
SELECT 'Static', p.FocusLeaderID, 2, s.LeaderID, s.ParentLeaderID, s.ParentLeaderID, s.Slot, s.Slots,
       p.X + (s.Slot - (s.Slots - 1) / 2.0) * st.Step, 2 + 0.2 * (s.Slot % 2)
FROM #TreeNode AS p
JOIN #Sib AS s ON s.ParentLeaderID = p.NodeID
CROSS APPLY (SELECT CASE WHEN 0.85 / p.Slots / s.Slots < 0.016 THEN 0.85 / p.Slots / s.Slots ELSE 0.016 END AS Step) AS st
WHERE p.TreeMode = 'Static' AND p.Tier = 1;

/* static tier 3: dots under their tier-2 parent */
INSERT INTO #TreeNode
SELECT 'Static', p.FocusLeaderID, 3, s.LeaderID, s.ParentLeaderID, p.Tier1NodeID, s.Slot, s.Slots,
       p.X + (s.Slot - (s.Slots - 1) / 2.0) * st.Step, 3 + 0.1 * (s.Slot % 2) + 0.06 * (p.Slot % 2)
FROM #TreeNode AS p
JOIN #Sib AS s ON s.ParentLeaderID = p.NodeID
JOIN #TreeNode AS t1 ON t1.TreeMode = 'Static' AND t1.FocusLeaderID = p.FocusLeaderID AND t1.NodeID = p.Tier1NodeID AND t1.Tier = 1
CROSS APPLY (SELECT CASE WHEN 0.85 / t1.Slots / p.Slots / s.Slots < 0.007 THEN 0.85 / t1.Slots / p.Slots / s.Slots
                         ELSE 0.007 END AS Step) AS st
WHERE p.TreeMode = 'Static' AND p.Tier = 2;

DROP TABLE IF EXISTS dw.OrgTreeLayout;
/* the circles: one row each, PointIndex 0 */
SELECT CAST(n.TreeMode AS VARCHAR(8)) AS TreeMode, n.FocusLeaderID, CAST('Node' AS VARCHAR(4)) AS MarkType,
       n.Tier, n.NodeID, n.ParentNodeID, n.Tier1NodeID, n.Slot, n.Slots, 0 AS PointIndex,
       CAST(ROUND(n.X, 6) AS FLOAT) AS X, CAST(ROUND(n.Y, 6) AS FLOAT) AS Y
INTO dw.OrgTreeLayout
FROM #TreeNode AS n;

/* the links: 17 points along the curve from the parent to each node below tier 0 */
INSERT INTO dw.OrgTreeLayout
SELECT n.TreeMode, n.FocusLeaderID, 'Link', n.Tier, n.NodeID, n.ParentNodeID, n.Tier1NodeID, n.Slot, n.Slots, k.N,
       CAST(ROUND(POWER(1 - u.T, 3) * p.X + 3 * POWER(1 - u.T, 2) * u.T * p.X
                  + 3 * (1 - u.T) * POWER(u.T, 2) * n.X + POWER(u.T, 3) * n.X, 6) AS FLOAT),
       CAST(ROUND(POWER(1 - u.T, 3) * p.Y + 3 * POWER(1 - u.T, 2) * u.T * (p.Y + n.Y) / 2
                  + 3 * (1 - u.T) * POWER(u.T, 2) * (p.Y + n.Y) / 2 + POWER(u.T, 3) * n.Y, 6) AS FLOAT)
FROM #TreeNode AS n
JOIN #TreeNode AS p ON p.TreeMode = n.TreeMode AND p.FocusLeaderID = n.FocusLeaderID AND p.NodeID = n.ParentNodeID
JOIN dw.RefDayNumber AS k ON k.N <= 16
CROSS APPLY (SELECT CAST(k.N AS FLOAT) / 16 AS T) AS u
WHERE n.Tier >= 1;
CREATE CLUSTERED INDEX CIX_OrgTreeLayout ON dw.OrgTreeLayout (FocusLeaderID, TreeMode, MarkType, NodeID, PointIndex);
GO

/* ------------------------------------------------------------------ AlignmentDetail
   Person x signal on the report date, with the function head (the deepest L0), the L1 and the
   L2 above each person. */
DROP TABLE IF EXISTS #Above;
SELECT x.PersonID,
       MAX(CASE WHEN x.LeaderLevel = 'L0' AND x.L0Rank = 1 THEN x.LeaderID END) AS L0LeaderID,
       MAX(CASE WHEN x.LeaderLevel = 'L1' THEN x.LeaderID END)                  AS L1LeaderID,
       MAX(CASE WHEN x.LeaderLevel = 'L2' THEN x.LeaderID END)                  AS L2LeaderID
INTO #Above
FROM (
    SELECT c.DescendantID AS PersonID, l.LeaderID, l.LeaderLevel,
           ROW_NUMBER() OVER (PARTITION BY c.DescendantID, CASE WHEN l.LeaderLevel = 'L0' THEN 1 ELSE 0 END
                              ORDER BY l.DepthFromTop DESC) AS L0Rank
    FROM dw.OrgClosure AS c
    JOIN fc.report_calendar AS rc ON c.MonthEndDate = rc.report_as_of_date
    JOIN dw.OrgLeader AS l ON l.MonthEndDate = c.MonthEndDate AND l.LeaderID = c.AncestorID
    WHERE c.Depth >= 1
) AS x
GROUP BY x.PersonID;

DROP TABLE IF EXISTS dw.AlignmentDetail;
SELECT s.MonthEndDate AS AsOfDate, s.PersonID, p.PersonName, p.WorkerType, p.JobTitle, p.DepartmentName,
       p.FunctionName, loc.OfficeName, p.CountryCode, p.Region, p.ManagerWorkerID, m.PersonName AS ManagerName,
       m.DepartmentName AS ManagerDepartmentName, p.ManagerSource,
       s.SignalCode, s.SignalName, s.SignalLine, s.SignalDetail,
       a.L0LeaderID, a.L1LeaderID, a.L2LeaderID
INTO dw.AlignmentDetail
FROM dw.AlignmentSignal AS s
JOIN fc.report_calendar AS rc ON s.MonthEndDate = rc.report_as_of_date
JOIN dw.PersonMonthEnd AS p ON p.MonthEndDate = s.MonthEndDate AND p.PersonID = s.PersonID
JOIN dw.DimLocation AS loc ON loc.LocationID = p.LocationID
LEFT JOIN dw.PersonMonthEnd AS m ON m.MonthEndDate = p.MonthEndDate AND m.PersonID = p.ManagerWorkerID
LEFT JOIN #Above AS a ON a.PersonID = s.PersonID;
GO

/* ------------------------------------------------------------------ OrgEntitlement
   Row-level security for Tableau Cloud: each leader x the people they may see (themselves and
   everyone below them). A row is kept when USERNAME() matches ViewerEmail; People Analytics
   sees everyone through a group (ISMEMBEROF), not through rows here. */
DROP TABLE IF EXISTS dw.OrgEntitlement;
SELECT c.AncestorID AS ViewerLeaderID, w.WorkEmail AS ViewerEmail, l.LeaderLevel AS ViewerLeaderLevel,
       c.DescendantID AS PersonID, c.Depth
INTO dw.OrgEntitlement
FROM dw.OrgClosure AS c
JOIN fc.report_calendar AS rc ON c.MonthEndDate = rc.report_as_of_date
JOIN dw.OrgLeader AS l ON l.MonthEndDate = c.MonthEndDate AND l.LeaderID = c.AncestorID
JOIN dw.DimWorker AS w ON w.WorkerID = c.AncestorID;
GO

DECLARE @n INT = (SELECT COUNT(*) FROM dw.PersonMonthEnd);
PRINT CONCAT('dw.PersonMonthEnd                 ', @n);
DECLARE @c INT = (SELECT COUNT(*) FROM dw.OrgClosure);
PRINT CONCAT('dw.OrgClosure                     ', @c);
DECLARE @t INT = (SELECT COUNT(*) FROM dw.OrgTreeLayout);
PRINT CONCAT('dw.OrgTreeLayout                  ', @t);
DECLARE @a INT = (SELECT COUNT(*) FROM dw.LeaderAvailability);
PRINT CONCAT('dw.LeaderAvailability             ', @a);
GO
