/*
  03d_build_dw_cw_reconciliation.sql
  Release 4: case study 4's reconciliation as Finance's month-end report meets it (Dashboard #4,
  Contingent Workforce Reconciliation). Runs after 03, 03b and 03c. The T-SQL twin of the DuckDB
  models added in release 4 (sql/01_staging stg_feed_event_delivery ... stg_ticket_category,
  sql/02_intermediate int_cw_close_run ... int_itsm_ticket_gap_link, sql/03_marts mart_cw_gap_close,
  mart_cw_gap_rate_close, mart_itsm_ticket_close); checked row for row against the DuckDB marts by
  sqlserver/check_tsql_in_duckdb.py, and on SQL Server by 15_validate_cw_reconciliation.sql.

    Times            FeedEventDelivery (sent and applied, GMT), KsContingentWorkerAudit
    Keystone jobs    KsCwJob (the PID each contingent job record holds), GenCwJobDefect (answer key)
    Load log         EtlLoadRun
    Helix            ItsmTicket, ItsmTicketEvent, ItsmTicketLink, RefTicketCategory
    derived          CwCloseRun         one row per month-end close: the run, each source's freshness
                     CwFlagType         the 9 flags, their risk and default place
                     CwLoadGap          gaps that exist only because a load failed
                     CwFlag             every gap at every close, with its cause and its place
                     ItsmTicketState    each ticket's state at each close's Helix read
                     ItsmTicketSubject  what each ticket is about, linked in tiers
                     ItsmTicketGapLink  the ticket working on each gap
                     CwGapClose, CwGapRateClose, ItsmTicketClose   the three marts (rpt views in 04c)

  Times are GMT, DATETIME2(0). Dates: EffectiveEndDate is inclusive and NULL while current;
  *Filled replaces NULL with 9999-12-31. Flags are BIT (0/1).
  Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ------------------------------------------------------------------ times */
DROP TABLE IF EXISTS dw.FeedEventDelivery;
SELECT
    CAST(feed_event_id AS VARCHAR(12))                     AS FeedEventID,
    CONVERT(DATETIME2(0), sent_at)                         AS SentAt,
    CONVERT(DATETIME2(0), NULLIF(applied_at, ''))          AS AppliedAt
INTO dw.FeedEventDelivery
FROM raw.feed_event_delivery;
CREATE CLUSTERED INDEX CIX_FeedEventDelivery ON dw.FeedEventDelivery (FeedEventID);
GO

DROP TABLE IF EXISTS dw.KsContingentWorkerAudit;
SELECT
    CAST(ks_record_id AS VARCHAR(12))                      AS KsRecordID,
    CONVERT(DATETIME2(0), changed_at)                      AS ChangedAt,
    CAST(changed_by   AS VARCHAR(24))                      AS ChangedBy
INTO dw.KsContingentWorkerAudit
FROM raw.ks_contingent_worker_audit;
GO

/* ------------------------------------------------------------------ Keystone job data */
DROP TABLE IF EXISTS dw.KsCwJob;
SELECT
    CAST(job_record_id AS VARCHAR(12))                     AS JobRecordID,
    CAST(person_id     AS VARCHAR(12))                     AS PersonID,
    CAST(empl_rcd AS INT)                                  AS EmplRcd,
    CAST(position_id   AS VARCHAR(12))                     AS PositionID,
    CONVERT(DATE, effective_start_date)                    AS EffectiveStartDate,
    CONVERT(DATE, NULLIF(effective_end_date, ''))          AS EffectiveEndDate,
    ISNULL(CONVERT(DATE, NULLIF(effective_end_date, '')), CONVERT(DATE, '9999-12-31')) AS EffectiveEndDateFilled,
    CAST(job_status    AS VARCHAR(12))                     AS JobStatus,
    CAST(action        AS VARCHAR(20))                     AS Action,
    CAST(change_source AS VARCHAR(10))                     AS ChangeSource,
    CAST(assignment_id AS VARCHAR(12))                     AS AssignmentID
INTO dw.KsCwJob
FROM raw.ks_cw_job;
CREATE CLUSTERED INDEX CIX_KsCwJob ON dw.KsCwJob (PersonID, EffectiveStartDate);
GO

DROP TABLE IF EXISTS dw.GenCwJobDefect;
SELECT
    CAST(defect_id   AS VARCHAR(10))                       AS DefectID,
    CAST(flag_code   AS VARCHAR(4))                        AS FlagCode,
    CAST(person_id   AS VARCHAR(12))                       AS PersonID,
    CAST(position_id AS VARCHAR(12))                       AS PositionID,
    CONVERT(DATE, start_date)                              AS StartDate,
    CONVERT(DATE, NULLIF(end_date, ''))                    AS EndDate,
    ISNULL(CONVERT(DATE, NULLIF(end_date, '')), CONVERT(DATE, '9999-12-31')) AS EndDateFilled,
    CAST(origin      AS VARCHAR(12))                       AS Origin,
    CAST(resolution  AS VARCHAR(20))                       AS Resolution,
    CAST(detail      AS VARCHAR(120))                      AS Detail
INTO dw.GenCwJobDefect
FROM raw.gen_cw_job_defect;
GO

/* ------------------------------------------------------------------ load log */
DROP TABLE IF EXISTS dw.EtlLoadRun;
SELECT
    CAST(run_id        AS VARCHAR(10))                     AS RunID,
    CAST(source_system AS VARCHAR(4))                      AS SourceSystem,
    CONVERT(DATETIME2(0), scheduled_at)                    AS ScheduledAt,
    CONVERT(DATETIME2(0), started_at)                      AS StartedAt,
    CONVERT(DATETIME2(0), finished_at)                     AS FinishedAt,
    CAST(status        AS VARCHAR(10))                     AS Status,
    CAST(NULLIF(rows_read, '') AS BIGINT)                  AS RowsRead,
    CAST(NULLIF(error_text, '') AS VARCHAR(100))           AS ErrorText
INTO dw.EtlLoadRun
FROM raw.etl_load_run;
GO

/* ------------------------------------------------------------------ Helix Service Desk */
DROP TABLE IF EXISTS dw.ItsmTicket;
SELECT
    CAST(ticket_number     AS VARCHAR(12))                 AS TicketNumber,
    CAST(title             AS VARCHAR(100))                AS Title,
    CAST(short_description AS VARCHAR(400))                AS ShortDescription,
    CAST(category_code     AS VARCHAR(10))                 AS CategoryCode,
    CAST(priority          AS VARCHAR(2))                  AS Priority,
    CAST(assignment_group  AS VARCHAR(20))                 AS AssignmentGroup,
    CONVERT(DATETIME2(0), opened_at)                       AS OpenedAt,
    CONVERT(DATETIME2(0), NULLIF(resolved_at, ''))         AS ResolvedAt,
    CONVERT(DATETIME2(0), NULLIF(closed_at, ''))           AS ClosedAt,
    CAST(NULLIF(close_code, '') AS VARCHAR(40))            AS CloseCode
INTO dw.ItsmTicket
FROM raw.itsm_ticket;
GO

DROP TABLE IF EXISTS dw.ItsmTicketEvent;
SELECT
    CAST(ticket_number AS VARCHAR(12))                     AS TicketNumber,
    ROW_NUMBER() OVER (PARTITION BY ticket_number ORDER BY CONVERT(DATETIME2(0), event_at)) AS EventSeq,
    CONVERT(DATETIME2(0), event_at)                        AS EventAt,
    CAST(NULLIF(from_state, '') AS VARCHAR(12))            AS FromState,
    CAST(to_state      AS VARCHAR(12))                     AS ToState,
    CAST(actor_group   AS VARCHAR(20))                     AS ActorGroup,
    CAST(note          AS VARCHAR(80))                     AS Note
INTO dw.ItsmTicketEvent
FROM raw.itsm_ticket_event;
CREATE CLUSTERED INDEX CIX_ItsmTicketEvent ON dw.ItsmTicketEvent (TicketNumber, EventSeq);
GO

DROP TABLE IF EXISTS dw.ItsmTicketLink;
SELECT
    CAST(ticket_number AS VARCHAR(12))                     AS TicketNumber,
    CAST(subject_type  AS VARCHAR(20))                     AS SubjectType,
    CAST(NULLIF(subject_id, '') AS VARCHAR(12))            AS SubjectID,
    CAST(NULLIF(secondary_id, '') AS VARCHAR(12))          AS SecondaryID,
    CAST(link_quality  AS VARCHAR(12))                     AS LinkQuality
INTO dw.ItsmTicketLink
FROM raw.itsm_ticket_link;
GO

DROP TABLE IF EXISTS dw.RefTicketCategory;
SELECT
    CAST(category_code  AS VARCHAR(10))                    AS CategoryCode,
    CAST(category_name  AS VARCHAR(60))                    AS CategoryName,
    CAST(subject_type   AS VARCHAR(20))                    AS SubjectType,
    CAST(default_group  AS VARCHAR(20))                    AS DefaultGroup,
    CAST(NULLIF(flag_code, '') AS VARCHAR(4))              AS FlagCode,
    CAST(NULLIF(risk, '') AS VARCHAR(32))                  AS Risk,
    CAST(priority       AS VARCHAR(2))                     AS Priority,
    CAST(title_template AS VARCHAR(60))                    AS TitleTemplate
INTO dw.RefTicketCategory
FROM raw.ref_ticket_category;
GO

/* ------------------------------------------------------------------ the month-end closes
   A close is the 00:00 GMT run on the 1st: Bridgeway at 00:00, Keystone after it (about 00:20),
   Helix at 00:00. A failed read leaves the source as of its last good load; Helix as of its last
   good read. */
DROP TABLE IF EXISTS dw.CwCloseRun;
SELECT
    c.MonthEndDate,
    c.PriorMonthEndDate,
    c.CloseRunAt,
    CAST(CASE WHEN c.MonthEndDate = MAX(c.MonthEndDate) OVER () THEN 1 ELSE 0 END AS BIT) AS IsLatestClose,
    bw.RunID                                                          AS BwRunID,
    bw.Status                                                         AS BwLoadStatus,
    bw.FinishedAt                                                     AS BwFinishedAt,
    ks.RunID                                                          AS KsRunID,
    ks.Status                                                         AS KsLoadStatus,
    ks.FinishedAt                                                     AS KsFinishedAt,
    hx.RunID                                                          AS HlxRunID,
    hx.Status                                                         AS HlxLoadStatus,
    CONVERT(DATE, DATEADD(DAY, -1, CONVERT(DATE, gb.ReadAt)))         AS BwDataAsOf,
    CONVERT(DATE, DATEADD(DAY, -1, CONVERT(DATE, gk.ReadAt)))         AS KsDataAsOf,
    gh.ReadAt                                                         AS HlxReadAt,
    CASE WHEN bw.Status = 'Failed' THEN bw.RunID WHEN ks.Status = 'Failed' THEN ks.RunID
         WHEN hx.Status = 'Failed' THEN hx.RunID END                  AS FailedRunID,
    CASE WHEN bw.Status = 'Failed' THEN CONCAT('Bridgeway load failed: the close used Bridgeway as of ',
              LEFT(DATENAME(MONTH, DATEADD(DAY, -1, CONVERT(DATE, gb.ReadAt))), 3), ' ', DAY(DATEADD(DAY, -1, CONVERT(DATE, gb.ReadAt))))
         WHEN ks.Status = 'Failed' THEN CONCAT('Keystone load failed: the close used Keystone as of ',
              LEFT(DATENAME(MONTH, DATEADD(DAY, -1, CONVERT(DATE, gk.ReadAt))), 3), ' ', DAY(DATEADD(DAY, -1, CONVERT(DATE, gk.ReadAt))))
         WHEN hx.Status = 'Failed' THEN CONCAT('Helix read failed: tickets are as of ',
              LEFT(DATENAME(MONTH, gh.ReadAt), 3), ' ', DAY(gh.ReadAt), ' ', FORMAT(gh.ReadAt, 'HH:mm'), ' GMT')
         WHEN bw.Status = 'Late' OR ks.Status = 'Late' THEN CONCAT('Loaded late, finished ',
              FORMAT(CASE WHEN bw.FinishedAt > ks.FinishedAt THEN bw.FinishedAt ELSE ks.FinishedAt END, 'HH:mm'),
              ' GMT; the data is complete')
         ELSE 'Loaded on time' END                                    AS LoadNote
INTO dw.CwCloseRun
FROM (SELECT MonthEndDate, PriorMonthEndDate, CONVERT(DATETIME2(0), DATEADD(DAY, 1, MonthEndDate)) AS CloseRunAt
      FROM dw.MonthEndCalendar) AS c
LEFT JOIN dw.EtlLoadRun AS bw ON bw.SourceSystem = 'BW' AND bw.ScheduledAt = c.CloseRunAt
LEFT JOIN dw.EtlLoadRun AS ks ON ks.SourceSystem = 'KS' AND ks.ScheduledAt = DATEADD(MINUTE, 20, c.CloseRunAt)
LEFT JOIN dw.EtlLoadRun AS hx ON hx.SourceSystem = 'HLX' AND hx.ScheduledAt = c.CloseRunAt
OUTER APPLY (SELECT MAX(r.ScheduledAt) AS ReadAt FROM dw.EtlLoadRun AS r
             WHERE r.SourceSystem = 'BW' AND r.Status <> 'Failed' AND r.ScheduledAt <= DATEADD(MINUTE, 20, c.CloseRunAt)
               AND r.ScheduledAt >= DATEADD(DAY, -10, c.CloseRunAt)) AS gb
OUTER APPLY (SELECT MAX(r.ScheduledAt) AS ReadAt FROM dw.EtlLoadRun AS r
             WHERE r.SourceSystem = 'KS' AND r.Status <> 'Failed' AND r.ScheduledAt <= DATEADD(MINUTE, 20, c.CloseRunAt)
               AND r.ScheduledAt >= DATEADD(DAY, -10, c.CloseRunAt)) AS gk
OUTER APPLY (SELECT MAX(r.ScheduledAt) AS ReadAt FROM dw.EtlLoadRun AS r
             WHERE r.SourceSystem = 'HLX' AND r.Status <> 'Failed' AND r.ScheduledAt <= DATEADD(MINUTE, 20, c.CloseRunAt)
               AND r.ScheduledAt >= DATEADD(DAY, -10, c.CloseRunAt)) AS gh;
GO

/* ------------------------------------------------------------------ the 9 flags
   Numbered and named so the Sankey reads alphabetically in all three columns (int_cw_flag_type). */
DROP TABLE IF EXISTS dw.CwFlagType;
SELECT CAST(t.FlagCode AS VARCHAR(4)) AS FlagCode, CAST(t.FlagName AS VARCHAR(60)) AS FlagName,
       CAST(CONCAT(RIGHT(CONCAT('0', SUBSTRING(t.FlagCode, 2, 2)), 2), ' ', t.FlagName) AS VARCHAR(64)) AS FlagLabel,
       CAST(t.Risk AS VARCHAR(32)) AS Risk, t.RiskOrder, CAST(t.DefaultPlace AS VARCHAR(12)) AS DefaultPlace,
       CAST(t.NextStep AS VARCHAR(100)) AS NextStep
INTO dw.CwFlagType
FROM (VALUES
    ('F01', 'One person, two IDs',                          'Active headcount mismatch',  1, 'Bridgeway',
     'Merge the two Bridgeway IDs'),
    ('F02', 'Bridgeway ID missing or different',            'Active headcount mismatch',  1, 'Keystone',
     'Align the Bridgeway ID stored in Keystone'),
    ('F03', 'In Bridgeway, not in Keystone',                'Active headcount mismatch',  1, 'Keystone',
     'Create the contractor in Keystone'),
    ('F04', 'Order open or billed after the end date',      'Billing after the end date', 2, 'Bridgeway',
     'Close the order in Bridgeway; request a credit for time billed after the end'),
    ('F05', 'Cost center differs',                          'Cost center mismatch',       3, 'Bridgeway',
     'Confirm the cost center with the manager; align the Bridgeway order or Keystone'),
    ('F06', 'PID still filled after the end date',          'PID mismatch',               4, 'Keystone',
     'End the job record and release the PID in Keystone'),
    ('F07', 'Two active PID records',                       'PID mismatch',               4, 'Keystone',
     'End the older job record in Keystone'),
    ('F08', 'Working in Bridgeway, ended in Keystone',      'Status mismatch',            5, 'Keystone',
     'Reactivate the contractor in Keystone'),
    ('F09', 'Active in Keystone, not working in Bridgeway', 'Status mismatch',            5, 'Keystone',
     'Confirm with the manager; inactivate in Keystone or raise a Bridgeway order')
) AS t(FlagCode, FlagName, Risk, RiskOrder, DefaultPlace, NextStep);
GO

/* ------------------------------------------------------------------ gaps a failed load creates
   A stale source is compared as it stood at its last good load; only differences the true data
   does not have are kept. */
DROP TABLE IF EXISTS #StaleRuns;
SELECT * INTO #StaleRuns FROM dw.CwCloseRun WHERE KsDataAsOf < MonthEndDate OR BwDataAsOf < MonthEndDate;

DROP TABLE IF EXISTS #KsChanged;
SELECT r.KsRunID, r.KsDataAsOf, s.*,
       o.KsRecordID AS OldRecordID, o.Status AS OldStatus, o.ContractEndDate AS OldEnd, o.CostCenterID AS OldCostCenterID
INTO #KsChanged
FROM #StaleRuns AS r
JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = r.MonthEndDate
LEFT JOIN dw.KsContingentWorker AS o
       ON o.PersonID = s.PersonID AND o.EffectiveStartDate <= r.KsDataAsOf AND o.EffectiveEndDateFilled >= r.KsDataAsOf
WHERE r.KsDataAsOf < r.MonthEndDate AND s.KsVersionStartDate > r.KsDataAsOf;

DROP TABLE IF EXISTS #BwStale;
SELECT t.MonthEndDate, t.BwRunID, t.BwDataAsOf, t.BwWorkerID,
       (SELECT TOP 1 r.AssignmentEndDate
        FROM dw.FeedBridgewayKeystoneEvent AS f JOIN dw.BwServiceOrderRevision AS r ON r.RevisionID = f.RevisionID
        WHERE f.BwWorkerID = t.BwWorkerID AND f.SentDate <= t.BwDataAsOf AND f.EventType <> 'Attribute Change'
        ORDER BY f.SentDate DESC, CASE WHEN f.EventType = 'New Worker' THEN 1 ELSE 0 END DESC, f.RevisionID DESC) AS StaleEnd,
       (SELECT TOP 1 r.CostCenterCode
        FROM dw.FeedBridgewayKeystoneEvent AS f JOIN dw.BwServiceOrderRevision AS r ON r.RevisionID = f.RevisionID
        WHERE f.BwWorkerID = t.BwWorkerID AND f.SentDate <= t.BwDataAsOf
        ORDER BY f.SentDate DESC, CASE WHEN f.EventType = 'New Worker' THEN 1 ELSE 0 END DESC, f.RevisionID DESC) AS StaleCostCenterID
INTO #BwStale
FROM (SELECT DISTINCT r.MonthEndDate, r.BwRunID, r.BwDataAsOf, f.BwWorkerID
      FROM #StaleRuns AS r
      JOIN dw.FeedBridgewayKeystoneEvent AS f ON f.SentDate > r.BwDataAsOf AND f.AppliedDate <= r.MonthEndDate
      WHERE r.BwDataAsOf < r.MonthEndDate) AS t;

DROP TABLE IF EXISTS dw.CwLoadGap;
SELECT g.MonthEndDate, g.IdentityID, g.BwWorkerID, g.PersonID, CAST(g.FlagCode AS VARCHAR(4)) AS FlagCode,
       CAST(CASE WHEN g.RunID = r.KsRunID THEN 'Keystone stale' ELSE 'Bridgeway stale' END AS VARCHAR(16)) AS CauseDetail,
       CONVERT(DATE, DATEADD(DAY, 1, CASE WHEN g.RunID = r.KsRunID THEN r.KsDataAsOf ELSE r.BwDataAsOf END)) AS SinceDate,
       CASE WHEN g.RunID = r.KsRunID
            THEN CONCAT('Keystone load ', g.RunID, ' failed at the close; the warehouse still holds Keystone as of ',
                        CAST(r.KsDataAsOf AS VARCHAR(10)), ', before this record changed')
            ELSE CONCAT('Bridgeway load ', g.RunID, ' failed at the close; the warehouse still holds Bridgeway as of ',
                        CAST(r.BwDataAsOf AS VARCHAR(10)), ', before a change Keystone has already applied') END AS Evidence,
       g.KeystoneShows, g.BridgewayHas
INTO dw.CwLoadGap
FROM (
    SELECT MonthEndDate, IdentityID, BwWorkerID, PersonID, 'F03' AS FlagCode, KsRunID AS RunID,
           CONCAT('No record (created ', CAST(KsVersionStartDate AS VARCHAR(10)), ', after the last Keystone load)') AS KeystoneShows,
           CONCAT('Working since ', CAST(BwContractStartDate AS VARCHAR(10))) AS BridgewayHas
    FROM #KsChanged WHERE OldRecordID IS NULL AND BwWorking = 1 AND KsExists = 1
    UNION ALL
    SELECT MonthEndDate, IdentityID, BwWorkerID, PersonID,
           CASE WHEN BwActive = 1 THEN 'F08' ELSE 'F09' END, KsRunID,
           CONCAT(CASE WHEN OldStatus = 'Active' THEN 'Active' ELSE 'Inactive' END, ', contract to ',
                  CAST(OldEnd AS VARCHAR(10)), ' (as of ', CAST(KsDataAsOf AS VARCHAR(10)), ')'),
           CONCAT(CASE WHEN BwActive = 1 THEN 'Working, contract to ' ELSE 'Ended ' END, CAST(BwContractEndDate AS VARCHAR(10)))
    FROM #KsChanged
    WHERE OldRecordID IS NOT NULL AND BwServiceOrderID IS NOT NULL
      AND BwActive <> CASE WHEN OldStatus = 'Active' THEN 1 ELSE 0 END AND BwActive = KsActive
    UNION ALL
    SELECT k.MonthEndDate, k.IdentityID, k.BwWorkerID, k.PersonID,
           'F05', k.KsRunID,
           CONCAT('Cost center ', k.OldCostCenterID, ' (as of ', CAST(k.KsDataAsOf AS VARCHAR(10)), ')'),
           CONCAT('Cost center ', k.BwCostCenterID)
    FROM #KsChanged AS k
    WHERE k.OldRecordID IS NOT NULL AND k.BwServiceOrderID IS NOT NULL
      AND k.OldCostCenterID IS DISTINCT FROM k.BwCostCenterID
      AND k.KsCostCenterID IS NOT DISTINCT FROM k.BwCostCenterID
    UNION ALL
    SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID, 'F09', b.BwRunID,
           CONCAT('Active since ', CAST(s.KsContractStartDate AS VARCHAR(10))),
           CONCAT('No worker (sent after the last Bridgeway load, ', CAST(b.BwDataAsOf AS VARCHAR(10)), ')')
    FROM #BwStale AS b
    JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = b.MonthEndDate AND s.BwWorkerID = b.BwWorkerID
    WHERE b.StaleEnd IS NULL AND s.KsWorking = 1
    UNION ALL
    SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID,
           CASE WHEN b.StaleEnd >= s.MonthEndDate THEN 'F08' ELSE 'F09' END, b.BwRunID,
           CONCAT(CASE WHEN s.KsActive = 1 THEN 'Active' ELSE 'Inactive' END, ', contract to ', CAST(s.KsContractEndDate AS VARCHAR(10))),
           CONCAT(CASE WHEN b.StaleEnd >= s.MonthEndDate THEN 'Working, contract to ' ELSE 'Ended ' END,
                  CAST(b.StaleEnd AS VARCHAR(10)), ' (as sent by ', CAST(b.BwDataAsOf AS VARCHAR(10)), ')')
    FROM #BwStale AS b
    JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = b.MonthEndDate AND s.BwWorkerID = b.BwWorkerID
    WHERE b.StaleEnd IS NOT NULL AND s.KsRecordID IS NOT NULL
      AND CASE WHEN b.StaleEnd >= s.MonthEndDate THEN 1 ELSE 0 END <> s.KsActive AND s.BwActive = s.KsActive
    UNION ALL
    SELECT s.MonthEndDate, s.IdentityID, s.BwWorkerID, s.PersonID,
           'F05', b.BwRunID,
           CONCAT('Cost center ', s.KsCostCenterID),
           CONCAT('Cost center ', b.StaleCostCenterID, ' (as sent by ', CAST(b.BwDataAsOf AS VARCHAR(10)), ')')
    FROM #BwStale AS b
    JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = b.MonthEndDate AND s.BwWorkerID = b.BwWorkerID
    WHERE b.StaleCostCenterID IS NOT NULL AND s.KsRecordID IS NOT NULL
      AND b.StaleCostCenterID IS DISTINCT FROM s.KsCostCenterID
      AND s.BwCostCenterID IS NOT DISTINCT FROM s.KsCostCenterID
) AS g
JOIN dw.CwCloseRun AS r ON r.MonthEndDate = g.MonthEndDate;
DROP TABLE IF EXISTS #StaleRuns;
DROP TABLE IF EXISTS #KsChanged;
DROP TABLE IF EXISTS #BwStale;
GO

/* ------------------------------------------------------------------ every gap at every close
   The comparisons (int_cw_discrepancy as flags), conversions, Keystone job data against the PID
   ledger, and the load gaps; one row per close x contractor x flag; then the routing rule. */
DROP TABLE IF EXISTS #D;
SELECT d.*, s.BwActive, s.KsActive, s.BwWorking, s.BwCostCenterID, s.KsCostCenterID,
       s.BwContractStartDate, s.BwContractEndDate, s.KsContractEndDate, s.KsStatus, s.KsStoredBwWorkerID
INTO #D
FROM dw.CwDiscrepancy AS d
LEFT JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = d.MonthEndDate AND s.IdentityID = d.IdentityID;

DROP TABLE IF EXISTS #Contract;
SELECT d.MonthEndDate, d.IdentityID, d.BwWorkerID, d.PersonID,
       CASE WHEN d.BwActive = 1 THEN 'F08' ELSE 'F09' END AS FlagCode,
       d.DiscrepancyCode AS CauseCode, d.RootCauseCode,
       CASE WHEN d.BwActive = 1 THEN d.SinceDate ELSE LEAST(d.SinceDate, CONVERT(DATE, DATEADD(DAY, 1, d.BwContractEndDate))) END AS SinceDate,
       d.ServiceOrderID, d.FeedEventID, d.Evidence,
       CONCAT(CASE WHEN d.KsActive = 1 THEN 'Active, contract to ' ELSE 'Inactive, contract to ' END,
              COALESCE(CAST(d.KsContractEndDate AS VARCHAR(10)), '?')) AS KeystoneShows,
       CONCAT(CASE WHEN d.BwActive = 1 THEN 'Working, contract to ' ELSE 'Ended ' END,
              COALESCE(CAST(d.BwContractEndDate AS VARCHAR(10)), '?')) AS BridgewayHas
INTO #Contract
FROM #D AS d
WHERE d.DiscrepancyCode IN ('CW00', 'CW01', 'CW02', 'CW03') AND d.FieldsAffected LIKE '%Status%'
  AND d.BwActive IS DISTINCT FROM d.KsActive;

DROP TABLE IF EXISTS #Converted;
SELECT MonthEndDate, IdentityID, WorkerID, OriginalHireDate
INTO #Converted
FROM (
    SELECT c.MonthEndDate, c.IdentityID, w.WorkerID, w.OriginalHireDate,
           ROW_NUMBER() OVER (PARTITION BY c.MonthEndDate, c.IdentityID ORDER BY w.OriginalHireDate, w.WorkerID) AS rn
    FROM #Contract AS c
    JOIN dw.CwIdentityResolution AS i ON i.IdentityID = c.IdentityID
    JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = c.MonthEndDate AND s.IdentityID = c.IdentityID
    JOIN dw.DimWorker AS w
      ON w.FirstName = i.FirstName AND w.LastName = i.LastName
     AND w.OriginalHireDate BETWEEN DATEADD(DAY, 1, s.BwContractEndDate) AND DATEADD(DAY, 31, s.BwContractEndDate)
     AND w.OriginalHireDate <= c.MonthEndDate
     AND (w.TerminationDate IS NULL OR w.TerminationDate > c.MonthEndDate)
    WHERE c.FlagCode = 'F09'
) AS x WHERE rn = 1;

DROP TABLE IF EXISTS #Jobs;
SELECT r.MonthEndDate, j.PersonID, j.PositionID, j.EmplRcd, j.EffectiveStartDate,
       CASE WHEN EXISTS (SELECT 1 FROM dw.FactContingentPositionAssignment AS a
                         WHERE a.WorkerID = j.PersonID AND a.PositionID = j.PositionID
                           AND a.StartDate <= r.MonthEndDate AND a.EndDateFilled >= r.MonthEndDate)
            THEN 1 ELSE 0 END AS InLedger
INTO #Jobs
FROM dw.CwCloseRun AS r
JOIN dw.KsCwJob AS j
  ON j.JobStatus = 'Active' AND j.EffectiveStartDate <= r.MonthEndDate AND j.EffectiveEndDateFilled >= r.MonthEndDate;

DROP TABLE IF EXISTS #JobPerson;
SELECT p.*, lp.LedgerPid
INTO #JobPerson
FROM (
    SELECT MonthEndDate, PersonID, COUNT(*) AS ActiveRecords, MIN(PositionID) AS PositionID,
           MAX(EffectiveStartDate) AS SecondSince,
           STRING_AGG(CONCAT(PositionID, ' (record ', EmplRcd, ')'), ', ') WITHIN GROUP (ORDER BY EmplRcd) AS Records,
           MAX(InLedger) AS AnyInLedger
    FROM #Jobs GROUP BY MonthEndDate, PersonID
) AS p
OUTER APPLY (SELECT TOP 1 j.PositionID AS LedgerPid FROM #Jobs AS j
             WHERE j.MonthEndDate = p.MonthEndDate AND j.PersonID = p.PersonID AND j.InLedger = 1
             ORDER BY j.EmplRcd DESC) AS lp;

DROP TABLE IF EXISTS #Gaps;
SELECT g.*
INTO #Gaps
FROM (
    /* cost center */
    SELECT d.MonthEndDate, d.IdentityID, d.BwWorkerID, d.PersonID,
           'F05' AS FlagCode,
           d.DiscrepancyCode AS CauseCode, d.RootCauseCode, d.SinceDate, d.ServiceOrderID, d.FeedEventID,
           CAST(NULL AS VARCHAR(12)) AS PositionID, d.Evidence,
           CONCAT('Cost center ', d.KsCostCenterID, ' (', kd.DepartmentName, ', ', kc.FunctionName, ')') AS KeystoneShows,
           CONCAT('Cost center ', d.BwCostCenterID, ' (', bd.DepartmentName, ', ', bc.FunctionName, ')') AS BridgewayHas
    FROM #D AS d
    LEFT JOIN dw.DimCostCenter AS bc ON bc.CostCenterID = d.BwCostCenterID
    LEFT JOIN dw.DimCostCenter AS kc ON kc.CostCenterID = d.KsCostCenterID
    LEFT JOIN dw.DimDepartment AS bd ON bd.DepartmentID = bc.DepartmentID
    LEFT JOIN dw.DimDepartment AS kd ON kd.DepartmentID = kc.DepartmentID
    WHERE d.DiscrepancyCode IN ('CW00', 'CW01', 'CW05', 'CW12') AND d.FieldsAffected LIKE '%Cost center%'
    UNION ALL
    /* contract status, a conversion relabelled */
    SELECT c.MonthEndDate, c.IdentityID, c.BwWorkerID, c.PersonID,
           CASE WHEN v.IdentityID IS NOT NULL THEN 'F01' ELSE c.FlagCode END,
           CASE WHEN v.IdentityID IS NOT NULL THEN 'CONV' ELSE c.CauseCode END,
           c.RootCauseCode, c.SinceDate, c.ServiceOrderID, c.FeedEventID, NULL,
           CASE WHEN v.IdentityID IS NOT NULL
                THEN CONCAT('Hired as employee ', v.WorkerID, ' on ', CAST(v.OriginalHireDate AS VARCHAR(10)),
                            '; the contractor record ', c.PersonID, ' is still active. ', c.Evidence)
                ELSE c.Evidence END,
           CASE WHEN v.IdentityID IS NOT NULL
                THEN CONCAT('Two active EMPLIDs: ', c.PersonID, ' (contractor) and ', v.WorkerID, ' (employee)')
                ELSE c.KeystoneShows END,
           CASE WHEN v.IdentityID IS NOT NULL
                THEN CONCAT('Ended ', CAST(s.BwContractEndDate AS VARCHAR(10)), ' (converted to employee)')
                ELSE c.BridgewayHas END
    FROM #Contract AS c
    LEFT JOIN #Converted AS v ON v.MonthEndDate = c.MonthEndDate AND v.IdentityID = c.IdentityID
    LEFT JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = c.MonthEndDate AND s.IdentityID = c.IdentityID
    UNION ALL
    /* structural */
    SELECT d.MonthEndDate, d.IdentityID, d.BwWorkerID, d.PersonID,
           CASE d.DiscrepancyCode WHEN 'CW04' THEN 'F04' WHEN 'CW11' THEN 'F04' WHEN 'CW07' THEN 'F01'
                WHEN 'CW06' THEN 'F02' WHEN 'CW09' THEN 'F09' ELSE 'F03' END,
           d.DiscrepancyCode, d.RootCauseCode, d.SinceDate, d.ServiceOrderID, d.FeedEventID, NULL, d.Evidence,
           CASE d.DiscrepancyCode
                WHEN 'CW04' THEN 'Not held in Keystone'
                WHEN 'CW11' THEN 'Not held in Keystone'
                WHEN 'CW07' THEN CONCAT('Two people: ', d.PersonID, ' and an earlier record')
                WHEN 'CW06' THEN CASE WHEN d.KsStoredBwWorkerID IS NULL THEN 'Stores no Bridgeway ID'
                                      ELSE CONCAT('Stores Bridgeway ID ', d.KsStoredBwWorkerID) END
                WHEN 'CW09' THEN 'Active, no Bridgeway worker'
                ELSE 'No record' END,
           CASE d.DiscrepancyCode
                WHEN 'CW04' THEN CONCAT('Order ', d.ServiceOrderID, ' still open after the last day')
                WHEN 'CW11' THEN 'Time billed for a month after the last day'
                WHEN 'CW07' THEN CONCAT('Second Bridgeway ID ', d.BwWorkerID, ' for the same person')
                WHEN 'CW06' THEN CONCAT('Worker ', d.BwWorkerID)
                WHEN 'CW09' THEN 'No worker'
                ELSE CONCAT('Working since ', COALESCE(CAST(d.BwContractStartDate AS VARCHAR(10)), '?')) END
    FROM #D AS d
    WHERE d.DiscrepancyCode IN ('CW04', 'CW11', 'CW07', 'CW06', 'CW09')
       OR (d.FieldsAffected = 'Whole record' AND d.DiscrepancyCode IN ('CW00', 'CW01', 'CW08'))
    UNION ALL
    /* Keystone job data against the PID ledger */
    SELECT p.MonthEndDate, i.IdentityID, i.BwWorkerID, p.PersonID,
           CASE WHEN p.ActiveRecords >= 2 THEN 'F07' ELSE 'F06' END, 'JOB', 'JOB',
           CASE WHEN p.ActiveRecords >= 2 THEN p.SecondSince ELSE COALESCE(l.LeftOn, p.SecondSince) END,
           NULL, NULL, p.PositionID,
           CASE WHEN p.ActiveRecords >= 2
                THEN CONCAT('Keystone job data holds ', p.ActiveRecords, ' active records: ', p.Records)
                ELSE CONCAT('Keystone job record on ', p.PositionID, ' is still active',
                            CASE WHEN l.LeftOn IS NOT NULL
                                 THEN CONCAT('; the PID ledger shows the contractor left it on ', CAST(l.LeftOn AS VARCHAR(10))) ELSE '' END) END,
           CASE WHEN p.ActiveRecords >= 2 THEN CONCAT(p.ActiveRecords, ' active records: ', p.Records)
                ELSE CONCAT('Active in ', p.PositionID) END,
           CASE WHEN p.ActiveRecords >= 2
                THEN CASE WHEN p.LedgerPid IS NULL THEN 'No current assignment' ELSE CONCAT('One assignment, on ', p.LedgerPid) END
                ELSE CASE WHEN l.LeftOn IS NULL THEN CONCAT('Not in ', p.PositionID)
                          ELSE CONCAT('Left ', p.PositionID, ' on ', CAST(l.LeftOn AS VARCHAR(10))) END END
    FROM #JobPerson AS p
    OUTER APPLY (SELECT CONVERT(DATE, DATEADD(DAY, 1, MAX(a.EndDate))) AS LeftOn
                 FROM dw.FactContingentPositionAssignment AS a
                 WHERE p.ActiveRecords = 1 AND p.AnyInLedger = 0
                   AND a.WorkerID = p.PersonID AND a.PositionID = p.PositionID AND a.EndDate < p.MonthEndDate) AS l
    LEFT JOIN dw.CwIdentityResolution AS i ON i.PersonID = p.PersonID
    WHERE p.ActiveRecords >= 2 OR p.AnyInLedger = 0
) AS g
JOIN dw.CwCloseRun AS r ON r.MonthEndDate = g.MonthEndDate
WHERE NOT (g.CauseCode = 'CW05' AND g.SinceDate > r.KsDataAsOf)
  AND NOT (g.CauseCode IN ('CW00', 'CW01') AND g.SinceDate > r.BwDataAsOf)
UNION ALL
SELECT MonthEndDate, IdentityID, BwWorkerID, PersonID, FlagCode, 'LOAD', CauseDetail, SinceDate,
       NULL, NULL, NULL, Evidence, KeystoneShows, BridgewayHas
FROM dw.CwLoadGap;

DROP TABLE IF EXISTS dw.CwFlag;
SELECT
    g.MonthEndDate,
    CONCAT(g.FlagCode, '-', COALESCE(g.BwWorkerID, g.PersonID))                      AS GapID,
    COALESCE(g.IdentityID, i.IdentityID)                                               AS IdentityID,
    COALESCE(g.BwWorkerID, i.BwWorkerID)                                               AS BwWorkerID,
    COALESCE(g.PersonID, i.PersonID)                                                   AS PersonID,
    CAST(g.FlagCode AS VARCHAR(4))                                                     AS FlagCode,
    t.FlagName,
    t.FlagLabel,
    t.Risk,
    t.RiskOrder,
    CAST(g.CauseCode AS VARCHAR(12))                                                   AS CauseCode,
    CAST(g.RootCauseCode AS VARCHAR(16))                                               AS RootCauseCode,
    g.SinceDate,
    DATEDIFF(DAY, g.SinceDate, g.MonthEndDate)                                         AS DaysOpen,
    g.Items,
    g.ServiceOrderID,
    g.FeedEventID,
    fd.SentAt                                                                          AS FeedSentAt,
    g.PositionID,
    CAST(CASE WHEN g.CauseCode IN ('CW00', 'CW01', 'LOAD') THEN 'System feed'
              WHEN g.CauseCode IN ('CW02', 'CW08', 'CW12') AND g.RootCauseCode IS DISTINCT FROM 'CW06' THEN 'System feed'
              WHEN g.CauseCode IN ('CW02', 'CW08', 'CW12') THEN 'Keystone'
              WHEN g.FlagCode = 'F01' AND g.CauseCode = 'CONV' THEN 'Keystone'
              ELSE t.DefaultPlace END AS VARCHAR(12))                                  AS Place,
    CAST(CASE WHEN g.CauseCode IN ('CW00', 'CW01') AND fd.SentAt > DATEADD(HOUR, -24, r.CloseRunAt) THEN 'Clears on its own'
              WHEN g.CauseCode IN ('CW00', 'CW01') THEN 'Feed stuck'
              WHEN g.CauseCode IN ('CW02', 'CW08', 'CW12') AND g.RootCauseCode IS DISTINCT FROM 'CW06' THEN 'Feed event failed'
              WHEN g.CauseCode = 'LOAD' THEN 'Load failed' END AS VARCHAR(20))         AS TimingClass,
    g.KeystoneShows,
    g.BridgewayHas,
    CONCAT(g.Evidence,
           CASE WHEN g.CauseCode IN ('CW00', 'CW01') AND fd.SentAt IS NOT NULL
                THEN CONCAT('. Sent ', FORMAT(fd.SentAt, 'yyyy-MM-dd HH:mm'), ' GMT, ',
                            DATEDIFF(HOUR, fd.SentAt, r.CloseRunAt), ' hours before the close run')
                ELSE '' END)                                                           AS Evidence,
    CASE WHEN g.FlagCode = 'F01' AND g.CauseCode = 'CONV' THEN 'End the contractor record in Keystone; the person is now an employee'
         WHEN g.CauseCode IN ('CW00', 'CW01') AND fd.SentAt > DATEADD(HOUR, -24, r.CloseRunAt) THEN 'None: the change lands with the next feed batch'
         WHEN g.CauseCode IN ('CW00', 'CW01') THEN 'Data engineering: release the stuck feed change'
         WHEN g.CauseCode IN ('CW02', 'CW08', 'CW12') AND g.RootCauseCode IS DISTINCT FROM 'CW06'
              THEN 'Data engineering: replay the failed feed event, then check Keystone'
         WHEN g.CauseCode IN ('CW02', 'CW08', 'CW12') THEN 'Align the Bridgeway ID stored in Keystone, then replay the feed event'
         WHEN g.CauseCode = 'LOAD' THEN 'Data engineering: the next run reloads the source; check it cleared'
         ELSE t.NextStep END                                                           AS NextStep
INTO dw.CwFlag
FROM (
    SELECT x.*,
           COUNT(*) OVER (PARTITION BY x.MonthEndDate, COALESCE(x.IdentityID, x.BwWorkerID, x.PersonID), x.FlagCode) AS Items,
           ROW_NUMBER() OVER (PARTITION BY x.MonthEndDate, COALESCE(x.IdentityID, x.BwWorkerID, x.PersonID), x.FlagCode
                              ORDER BY x.SinceDate, x.ServiceOrderID, x.FeedEventID, x.Evidence) AS rn
    FROM #Gaps AS x
) AS g
JOIN dw.CwFlagType AS t ON t.FlagCode = g.FlagCode
JOIN dw.CwCloseRun AS r ON r.MonthEndDate = g.MonthEndDate
LEFT JOIN dw.FeedEventDelivery AS fd ON fd.FeedEventID = g.FeedEventID
LEFT JOIN dw.CwIdentityResolution AS i ON g.IdentityID IS NULL AND i.BwWorkerID = g.BwWorkerID
WHERE g.rn = 1;
CREATE CLUSTERED INDEX CIX_CwFlag ON dw.CwFlag (MonthEndDate, GapID);
DROP TABLE IF EXISTS #D;
DROP TABLE IF EXISTS #Contract;
DROP TABLE IF EXISTS #Converted;
DROP TABLE IF EXISTS #Jobs;
DROP TABLE IF EXISTS #JobPerson;
DROP TABLE IF EXISTS #Gaps;
GO

/* ------------------------------------------------------------------ tickets at each close
   A ticket's state at a read is its last event's state at or before the read. */
DROP TABLE IF EXISTS dw.ItsmTicketState;
SELECT
    s.MonthEndDate,
    s.TicketNumber,
    s.State,
    CAST(CASE WHEN s.State IN ('New', 'In progress', 'Pending', 'Reopened') THEN 1 ELSE 0 END AS BIT) AS IsOpen,
    s.CurrentGroup,
    CAST(CASE s.CurrentGroup WHEN 'Vendor Management' THEN 'Bridgeway' WHEN 'HR Operations' THEN 'Keystone'
              ELSE 'System feed' END AS VARCHAR(12))                         AS Place,
    s.OpenedAt,
    s.LastResolvedAt,
    s.ClosedAt,
    s.TimesReopened,
    s.TimesReassigned,
    DATEDIFF(DAY, s.OpenedAt, s.HlxReadAt)                                   AS AgeDays,
    CAST(CASE WHEN DATEDIFF(DAY, s.OpenedAt, s.HlxReadAt) <= 5 THEN '0 to 5 days'
              WHEN DATEDIFF(DAY, s.OpenedAt, s.HlxReadAt) <= 30 THEN '6 to 30 days'
              ELSE 'Over 30 days' END AS VARCHAR(14))                        AS AgeBand,
    s.HlxReadAt
INTO dw.ItsmTicketState
FROM (
    SELECT r.MonthEndDate, r.HlxReadAt, e.TicketNumber,
           MIN(e.EventAt)                                                    AS OpenedAt,
           MAX(CASE WHEN e.EventSeq = l.LastSeq THEN e.ToState END)           AS State,
           MAX(CASE WHEN e.EventSeq = l.LastGroupSeq THEN e.ActorGroup END)   AS CurrentGroup,
           MAX(CASE WHEN e.ToState = 'Resolved' THEN e.EventAt END)           AS LastResolvedAt,
           MAX(CASE WHEN e.ToState = 'Closed' THEN e.EventAt END)             AS ClosedAt,
           SUM(CASE WHEN e.ToState = 'Reopened' THEN 1 ELSE 0 END)            AS TimesReopened,
           SUM(CASE WHEN e.Note LIKE 'Reassigned%' THEN 1 ELSE 0 END)         AS TimesReassigned
    FROM dw.CwCloseRun AS r
    JOIN dw.ItsmTicketEvent AS e ON e.EventAt <= r.HlxReadAt
    JOIN (SELECT r2.MonthEndDate, e2.TicketNumber, MAX(e2.EventSeq) AS LastSeq,
                 MAX(CASE WHEN e2.ActorGroup <> 'Helix' THEN e2.EventSeq END) AS LastGroupSeq
          FROM dw.CwCloseRun AS r2 JOIN dw.ItsmTicketEvent AS e2 ON e2.EventAt <= r2.HlxReadAt
          GROUP BY r2.MonthEndDate, e2.TicketNumber) AS l
      ON l.MonthEndDate = r.MonthEndDate AND l.TicketNumber = e.TicketNumber
    GROUP BY r.MonthEndDate, r.HlxReadAt, e.TicketNumber
) AS s
WHERE s.State <> 'Closed' OR s.ClosedAt > DATEADD(DAY, -120, s.HlxReadAt);
GO

/* what each ticket is about: the ID fields, else exactly one identity named in the description that
   either system showed working at a month-end in the two months before the ticket was opened */
DROP TABLE IF EXISTS dw.ItsmTicketSubject;
SELECT
    t.TicketNumber, t.Title, t.ShortDescription, t.CategoryCode, t.CategoryName, t.FlagCode, t.Risk,
    t.Priority, t.OpenedAt, t.SubjectType, t.LinkQuality,
    CASE WHEN t.SubjectType = 'Data load' THEN t.SubjectID END                     AS RunID,
    COALESCE(ib.IdentityID, ip.IdentityID, CASE WHEN nm.n = 1 THEN nm.IdentityID END) AS IdentityID,
    CAST(CASE WHEN t.SubjectType = 'Data load' THEN 'Load run'
              WHEN COALESCE(ib.IdentityID, ip.IdentityID) IS NOT NULL THEN 'ID'
              WHEN nm.n = 1 THEN 'Name'
              WHEN nm.n > 1 THEN 'Ambiguous'
              ELSE 'None' END AS VARCHAR(10))                                      AS LinkTier
INTO dw.ItsmTicketSubject
FROM (
    SELECT t.TicketNumber, t.Title, t.ShortDescription, t.CategoryCode, t.Priority, t.OpenedAt,
           c.FlagCode, c.Risk, c.CategoryName, l.SubjectType, l.SubjectID, l.SecondaryID, l.LinkQuality,
           CASE WHEN l.LinkQuality = 'Name in text' AND t.ShortDescription LIKE 'Contractor %:%'
                THEN SUBSTRING(t.ShortDescription, 12, CHARINDEX(':', t.ShortDescription) - 12) END AS Named
    FROM dw.ItsmTicket AS t
    JOIN dw.RefTicketCategory AS c ON c.CategoryCode = t.CategoryCode
    LEFT JOIN dw.ItsmTicketLink AS l ON l.TicketNumber = t.TicketNumber
) AS t
LEFT JOIN dw.CwIdentityResolution AS ib
       ON t.SubjectType = 'Contingent worker' AND ib.BwWorkerID = t.SubjectID
LEFT JOIN dw.CwIdentityResolution AS ip
       ON t.SubjectType = 'Contingent worker' AND t.SubjectID IS NULL AND ip.PersonID = t.SecondaryID
OUTER APPLY (SELECT MIN(i.IdentityID) AS IdentityID, COUNT(*) AS n
             FROM dw.CwIdentityResolution AS i
             WHERE CONCAT(i.FirstName, ' ', i.LastName) = t.Named
               AND EXISTS (SELECT 1 FROM dw.CwReconciliationSnapshot AS s
                           WHERE s.IdentityID = i.IdentityID
                             AND s.MonthEndDate >= DATEADD(DAY, -62, CONVERT(DATE, t.OpenedAt))
                             AND s.MonthEndDate <= EOMONTH(CONVERT(DATE, t.OpenedAt)))) AS nm;
GO

/* the ticket working on each gap: same contractor, opened no more than 7 days before the gap
   began, the same risk (or a stuck-feed ticket for a gap waiting on the feed); the latest wins */
DROP TABLE IF EXISTS dw.ItsmTicketGapLink;
SELECT
    g.MonthEndDate,
    g.GapID,
    c.TicketNumber,
    c.State                                                                  AS TicketState,
    CAST(CASE WHEN c.TicketNumber IS NULL THEN 'No ticket'
              WHEN c.IsOpen = 1 THEN 'Open'
              WHEN c.State = 'Resolved' THEN 'Fix pending next run'
              ELSE 'Closed, gap still open' END AS VARCHAR(24))              AS TicketStatus,
    CAST(CASE WHEN c.IsOpen = 1 OR c.State = 'Resolved' THEN 1 ELSE 0 END AS BIT) AS HasTicket
INTO dw.ItsmTicketGapLink
FROM (SELECT f.MonthEndDate, f.GapID, f.IdentityID, f.Risk, f.CauseCode, f.SinceDate, r.FailedRunID
      FROM dw.CwFlag AS f JOIN dw.CwCloseRun AS r ON r.MonthEndDate = f.MonthEndDate) AS g
OUTER APPLY (
    SELECT TOP 1 s.TicketNumber, st.State, st.IsOpen
    FROM dw.ItsmTicketSubject AS s
    JOIN dw.ItsmTicketState AS st ON st.TicketNumber = s.TicketNumber AND st.MonthEndDate = g.MonthEndDate
    WHERE ((s.IdentityID = g.IdentityID
            AND (s.Risk = g.Risk OR (s.CategoryCode = 'INT-FEED' AND g.CauseCode IN ('CW00', 'CW01'))))
           OR (g.CauseCode = 'LOAD' AND s.RunID = g.FailedRunID))
      AND (st.OpenedAt >= DATEADD(DAY, -7, CONVERT(DATETIME2(0), g.SinceDate)) OR g.CauseCode = 'LOAD')
    ORDER BY st.OpenedAt DESC, s.TicketNumber DESC
) AS c;
GO

/* ------------------------------------------------------------------ the marts (views in 04c) */
/* mart_cw_gap_close: every gap at every close, placed in one group per contractor, ranked */
DROP TABLE IF EXISTS #Placed;
SELECT f.*, COALESCE(f.IdentityID, f.BwWorkerID, f.PersonID) AS ContractorKey,
       COALESCE(s.BwCostCenterID, oc.CostCenterID, s.KsCostCenterID, kl.CostCenterID) AS RowCostCenterID,
       CASE WHEN s.BwCostCenterID IS NULL THEN 1 ELSE 0 END AS NoBridgewayCc
INTO #Placed
FROM dw.CwFlag AS f
LEFT JOIN dw.CwReconciliationSnapshot AS s ON s.MonthEndDate = f.MonthEndDate AND s.IdentityID = f.IdentityID
LEFT JOIN (SELECT ServiceOrderID, CostCenterCode AS CostCenterID,
                  ROW_NUMBER() OVER (PARTITION BY ServiceOrderID ORDER BY RevisionNo DESC) AS rn
           FROM dw.BwServiceOrderRevision) AS oc ON oc.ServiceOrderID = f.ServiceOrderID AND oc.rn = 1
OUTER APPLY (SELECT TOP 1 k.CostCenterID FROM dw.KsContingentWorker AS k
             WHERE k.PersonID = f.PersonID AND k.EffectiveStartDate <= f.MonthEndDate
             ORDER BY k.EffectiveStartDate DESC) AS kl;

DROP TABLE IF EXISTS #Scoped;
SELECT p.*, grp.CostCenterID, cc.DepartmentID, cc.CountryCode, dep.DepartmentName, dep.FunctionName, co.CountryName
INTO #Scoped
FROM #Placed AS p
OUTER APPLY (SELECT TOP 1 q.RowCostCenterID AS CostCenterID FROM #Placed AS q
             WHERE q.MonthEndDate = p.MonthEndDate AND q.ContractorKey = p.ContractorKey AND q.RowCostCenterID IS NOT NULL
             ORDER BY q.NoBridgewayCc, q.FlagCode) AS grp
LEFT JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = grp.CostCenterID
LEFT JOIN dw.DimDepartment AS dep ON dep.DepartmentID = cc.DepartmentID
LEFT JOIN dw.DimCountry AS co ON co.CountryCode = cc.CountryCode
WHERE COALESCE(cc.DepartmentID, '') <> 'D-901';
CREATE CLUSTERED INDEX CIX_Scoped ON #Scoped (MonthEndDate, GapID);

DROP TABLE IF EXISTS #Counts;
SELECT MonthEndDate, FlagCode, COUNT(*) AS FlagCount,
       ROW_NUMBER() OVER (PARTITION BY MonthEndDate ORDER BY COUNT(*) DESC, FlagCode) AS FlagRank
INTO #Counts
FROM #Scoped GROUP BY MonthEndDate, FlagCode;

DROP TABLE IF EXISTS dw.CwGapClose;
SELECT
    s.MonthEndDate,
    CONCAT(LEFT(DATENAME(MONTH, s.MonthEndDate), 3), ' ', YEAR(s.MonthEndDate))     AS CloseLabel,
    r.IsLatestClose,
    s.GapID,
    s.ContractorKey,
    s.BwWorkerID,
    s.PersonID,
    CASE WHEN i.FirstName IS NOT NULL AND i.LastName IS NOT NULL THEN CONCAT(i.FirstName, ' ', i.LastName) END AS ContractorName,
    i.CwType,
    sup.SupplierName,
    s.FlagCode,
    s.FlagName,
    s.FlagLabel,
    c.FlagCount,
    c.FlagRank,
    cp.FlagCount                                                                       AS FlagCountPriorClose,
    cp.FlagRank                                                                        AS FlagRankPriorClose,
    cy.FlagCount                                                                       AS FlagCountYearAgo,
    cy.FlagRank                                                                        AS FlagRankYearAgo,
    s.Risk,
    s.RiskOrder,
    s.Place,
    CASE s.Place WHEN 'Bridgeway' THEN 1 WHEN 'Keystone' THEN 2 ELSE 3 END            AS PlaceOrder,
    CAST(CASE s.Place WHEN 'Bridgeway' THEN 'Bridgeway (vendor system)'
                      WHEN 'Keystone' THEN 'Keystone (HR system)'
                      ELSE 'System feed (integration)' END AS VARCHAR(28))           AS PlaceLabel,
    s.CauseCode,
    cz.CauseName,
    s.RootCauseCode,
    s.TimingClass,
    CAST(CASE WHEN COALESCE(s.TimingClass, '') <> 'Clears on its own' THEN 1 ELSE 0 END AS BIT) AS IsCounted,
    s.SinceDate,
    s.DaysOpen,
    CASE WHEN s.DaysOpen <= 30 THEN '0 to 30 days' WHEN s.DaysOpen <= 90 THEN '31 to 90 days'
         ELSE 'Over 90 days' END                                                       AS OpenBand,
    CAST(CASE WHEN s.DaysOpen > 90 THEN 1 ELSE 0 END AS BIT)                           AS IsOver90Days,
    CASE WHEN s.FlagCode IN ('F06', 'F09') THEN DATEDIFF(DAY, s.SinceDate, s.MonthEndDate) END AS DaysSinceEnd,
    CAST(CASE WHEN EXISTS (SELECT 1 FROM #Scoped AS p WHERE p.MonthEndDate = r.PriorMonthEndDate AND p.GapID = s.GapID)
                   AND s.SinceDate <= r.PriorMonthEndDate
              THEN 1 ELSE 0 END AS BIT)                                                AS WasOpenPriorClose,
    CAST(CASE WHEN (EXISTS (SELECT 1 FROM dw.KsContingentWorker AS k
                            WHERE k.PersonID = s.PersonID AND k.EffectiveStartDate = DATEADD(DAY, 1, s.MonthEndDate))
                    OR EXISTS (SELECT 1 FROM dw.FeedBridgewayKeystoneEvent AS e
                               WHERE e.BwWorkerID = s.BwWorkerID AND e.AppliedDate = DATEADD(DAY, 1, s.MonthEndDate))
                    OR EXISTS (SELECT 1 FROM dw.KsCwJob AS j
                               WHERE j.PersonID = s.PersonID AND j.EffectiveStartDate = DATEADD(DAY, 1, s.MonthEndDate))
                    OR EXISTS (SELECT 1 FROM dw.BwServiceOrderRevision AS rv
                               WHERE rv.ServiceOrderID = s.ServiceOrderID AND rv.EffectiveStartDate = DATEADD(DAY, 1, s.MonthEndDate)))
                   AND NOT EXISTS (SELECT 1 FROM #Scoped AS n
                                   WHERE n.MonthEndDate = EOMONTH(DATEADD(DAY, 1, s.MonthEndDate)) AND n.GapID = s.GapID)
              THEN 1 ELSE 0 END AS BIT)                                                AS FixedDayAfterClose,
    s.Items,
    s.ServiceOrderID,
    s.FeedEventID,
    s.PositionID,
    s.CostCenterID,
    s.DepartmentID,
    s.DepartmentName,
    s.FunctionName,
    s.CountryCode,
    s.CountryName,
    s.KeystoneShows,
    s.BridgewayHas,
    s.Evidence,
    s.NextStep,
    l.TicketNumber,
    tk.Title                                                                           AS TicketTitle,
    l.TicketState,
    l.TicketStatus,
    l.HasTicket
INTO dw.CwGapClose
FROM #Scoped AS s
JOIN dw.CwCloseRun AS r ON r.MonthEndDate = s.MonthEndDate
JOIN #Counts AS c ON c.MonthEndDate = s.MonthEndDate AND c.FlagCode = s.FlagCode
LEFT JOIN #Counts AS cp ON cp.MonthEndDate = r.PriorMonthEndDate AND cp.FlagCode = s.FlagCode
LEFT JOIN (SELECT MonthEndDate, LAG(MonthEndDate, 12) OVER (ORDER BY MonthEndDate) AS YearAgo
           FROM dw.MonthEndCalendar) AS ya ON ya.MonthEndDate = s.MonthEndDate
LEFT JOIN #Counts AS cy ON cy.MonthEndDate = ya.YearAgo AND cy.FlagCode = s.FlagCode
LEFT JOIN (SELECT DiscrepancyCode AS CauseCode, DiscrepancyName AS CauseName FROM dw.RefCwDiscrepancyType
           UNION ALL SELECT 'JOB', 'Keystone job data out of step with the PID ledger'
           UNION ALL SELECT 'CONV', 'Converted to employee; contractor record still active'
           UNION ALL SELECT 'LOAD', 'Source load failed at the close') AS cz ON cz.CauseCode = s.CauseCode
LEFT JOIN dw.CwIdentityResolution AS i ON i.IdentityID = s.IdentityID
LEFT JOIN dw.BwSupplier AS sup ON sup.SupplierID = i.SupplierID
LEFT JOIN dw.ItsmTicketGapLink AS l ON l.MonthEndDate = s.MonthEndDate AND l.GapID = s.GapID
LEFT JOIN dw.ItsmTicket AS tk ON tk.TicketNumber = l.TicketNumber;
CREATE CLUSTERED INDEX CIX_CwGapClose ON dw.CwGapClose (MonthEndDate, ContractorKey);
DROP TABLE IF EXISTS #Placed;
DROP TABLE IF EXISTS #Scoped;
DROP TABLE IF EXISTS #Counts;
GO

/* mart_cw_gap_rate_close: the gap rate's numerator and denominator per close x cost center */
DROP TABLE IF EXISTS dw.CwGapRateClose;
SELECT
    c.MonthEndDate,
    CONCAT(LEFT(DATENAME(MONTH, c.MonthEndDate), 3), ' ', YEAR(c.MonthEndDate))     AS CloseLabel,
    r.IsLatestClose,
    c.CostCenterID,
    cc.DepartmentID,
    dep.DepartmentName,
    dep.FunctionName,
    cc.CountryCode,
    co.CountryName,
    COALESCE(p.ContractorsWorking, 0)                                               AS ContractorsWorking,
    COALESCE(p.ContractorsWorkingKeystone, 0)                                       AS ContractorsWorkingKeystone,
    COALESCE(p.WorkingBridgewayOnly, 0)                                             AS WorkingBridgewayOnly,
    COALESCE(p.WorkingKeystoneOnly, 0)                                              AS WorkingKeystoneOnly,
    COALESCE(g.ContractorsWithGap, 0)                                               AS ContractorsWithGap,
    COALESCE(g.ContractorsWithAnyGap, 0)                                            AS ContractorsWithAnyGap,
    COALESCE(g.Gaps, 0)                                                             AS Gaps,
    COALESCE(g.GapsCounted, 0)                                                      AS GapsCounted,
    COALESCE(g.GapsClearOnOwn, 0)                                                   AS GapsClearOnOwn,
    COALESCE(g.GapsNoTicket, 0)                                                     AS GapsNoTicket,
    COALESCE(g.GapsOver90Days, 0)                                                   AS GapsOver90Days,
    COALESCE(g.GapsOpenPriorClose, 0)                                               AS GapsOpenPriorClose,
    COALESCE(g.GapsFixedDayAfter, 0)                                                AS GapsFixedDayAfter,
    CAST(0.03 AS DECIMAL(5, 2))                                                     AS GapRateTarget,
    r.LoadNote
INTO dw.CwGapRateClose
FROM (
    SELECT MonthEndDate, COALESCE(BwCostCenterID, KsCostCenterID) AS CostCenterID
    FROM dw.CwReconciliationSnapshot WHERE BwWorking = 1 OR KsWorking = 1
    UNION
    SELECT MonthEndDate, CostCenterID FROM dw.CwGapClose
) AS c
JOIN dw.CwCloseRun AS r ON r.MonthEndDate = c.MonthEndDate
LEFT JOIN (
    SELECT MonthEndDate, COALESCE(BwCostCenterID, KsCostCenterID) AS CostCenterID,
           SUM(CASE WHEN BwWorking = 1 THEN 1 ELSE 0 END)                    AS ContractorsWorking,
           SUM(CASE WHEN KsWorking = 1 THEN 1 ELSE 0 END)                    AS ContractorsWorkingKeystone,
           SUM(CASE WHEN BwWorking = 1 AND KsWorking = 0 THEN 1 ELSE 0 END)  AS WorkingBridgewayOnly,
           SUM(CASE WHEN KsWorking = 1 AND BwWorking = 0 THEN 1 ELSE 0 END)  AS WorkingKeystoneOnly
    FROM dw.CwReconciliationSnapshot WHERE BwWorking = 1 OR KsWorking = 1
    GROUP BY MonthEndDate, COALESCE(BwCostCenterID, KsCostCenterID)
) AS p ON p.MonthEndDate = c.MonthEndDate AND p.CostCenterID IS NOT DISTINCT FROM c.CostCenterID
LEFT JOIN (
    SELECT MonthEndDate, CostCenterID,
           COUNT(DISTINCT CASE WHEN IsCounted = 1 THEN ContractorKey END)    AS ContractorsWithGap,
           COUNT(DISTINCT ContractorKey)                                     AS ContractorsWithAnyGap,
           COUNT(*)                                                          AS Gaps,
           SUM(CASE WHEN IsCounted = 1 THEN 1 ELSE 0 END)                    AS GapsCounted,
           SUM(CASE WHEN IsCounted = 0 THEN 1 ELSE 0 END)                    AS GapsClearOnOwn,
           SUM(CASE WHEN IsCounted = 1 AND HasTicket = 0 THEN 1 ELSE 0 END)  AS GapsNoTicket,
           SUM(CASE WHEN IsCounted = 1 AND IsOver90Days = 1 THEN 1 ELSE 0 END) AS GapsOver90Days,
           SUM(CASE WHEN IsCounted = 1 AND WasOpenPriorClose = 1 THEN 1 ELSE 0 END) AS GapsOpenPriorClose,
           SUM(CASE WHEN FixedDayAfterClose = 1 THEN 1 ELSE 0 END)           AS GapsFixedDayAfter
    FROM dw.CwGapClose GROUP BY MonthEndDate, CostCenterID
) AS g ON g.MonthEndDate = c.MonthEndDate AND g.CostCenterID IS NOT DISTINCT FROM c.CostCenterID
LEFT JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = c.CostCenterID
LEFT JOIN dw.DimDepartment AS dep ON dep.DepartmentID = cc.DepartmentID
LEFT JOIN dw.DimCountry AS co ON co.CountryCode = cc.CountryCode
WHERE COALESCE(cc.DepartmentID, '') <> 'D-901';
GO

/* mart_itsm_ticket_close: every ticket open at each close, with its dot (packed 20 to a line, oldest first) */
DROP TABLE IF EXISTS dw.ItsmTicketClose;
SELECT
    t.MonthEndDate,
    CONCAT(LEFT(DATENAME(MONTH, t.MonthEndDate), 3), ' ', YEAR(t.MonthEndDate))     AS CloseLabel,
    r.IsLatestClose,
    t.TicketNumber,
    sb.Title,
    t.State,
    sb.CategoryCode,
    sb.CategoryName,
    sb.FlagCode,
    sb.Risk,
    sb.Priority,
    t.Place,
    CASE t.Place WHEN 'Bridgeway' THEN 1 WHEN 'Keystone' THEN 2 ELSE 3 END           AS PlaceOrder,
    CAST(CASE t.Place WHEN 'Bridgeway' THEN 'Bridgeway (vendor system)'
                      WHEN 'Keystone' THEN 'Keystone (HR system)'
                      ELSE 'System feed (integration)' END AS VARCHAR(28))           AS PlaceLabel,
    t.CurrentGroup,
    t.OpenedAt,
    t.AgeDays,
    t.AgeBand,
    CASE t.AgeBand WHEN '0 to 5 days' THEN 1 WHEN '6 to 30 days' THEN 2 ELSE 3 END  AS AgeBandOrder,
    t.TimesReopened,
    t.TimesReassigned,
    sb.LinkTier,
    sb.IdentityID                                                                    AS ContractorKey,
    gg.GapID                                                                         AS LinkedGapID,
    COALESCE(gg.CostCenterID, sg.CostCenterID)                                       AS CostCenterID,
    cc.DepartmentID,
    dep.DepartmentName,
    dep.FunctionName,
    cc.CountryCode,
    co.CountryName,
    t.DotSeq,
    (CASE t.AgeBand WHEN '0 to 5 days' THEN 0 WHEN '6 to 30 days' THEN 1 ELSE 2 END)
        + 0.05 + 0.9 * (((t.DotSeq - 1) % 20) + 0.5) / 20                              AS DotX,
    (CASE t.Place WHEN 'Bridgeway' THEN 2 WHEN 'Keystone' THEN 1 ELSE 0 END)
        + 0.9 - 0.8 * (FLOOR((t.DotSeq - 1) / 20) + 0.5) / 8                          AS DotY
INTO dw.ItsmTicketClose
FROM (SELECT st.*, ROW_NUMBER() OVER (PARTITION BY st.MonthEndDate, st.Place, st.AgeBand
                                      ORDER BY st.AgeDays DESC, st.TicketNumber) AS DotSeq
      FROM dw.ItsmTicketState AS st WHERE st.IsOpen = 1) AS t
JOIN dw.ItsmTicketSubject AS sb ON sb.TicketNumber = t.TicketNumber
JOIN dw.CwCloseRun AS r ON r.MonthEndDate = t.MonthEndDate
LEFT JOIN (SELECT MonthEndDate, ContractorKey, MIN(CostCenterID) AS CostCenterID, MIN(GapID) AS GapID
           FROM dw.CwGapClose GROUP BY MonthEndDate, ContractorKey) AS gg
       ON gg.MonthEndDate = t.MonthEndDate AND gg.ContractorKey = sb.IdentityID
LEFT JOIN (SELECT MonthEndDate, IdentityID, COALESCE(BwCostCenterID, KsCostCenterID) AS CostCenterID
           FROM dw.CwReconciliationSnapshot) AS sg
       ON sg.MonthEndDate = t.MonthEndDate AND sg.IdentityID = sb.IdentityID
LEFT JOIN dw.DimCostCenter AS cc ON cc.CostCenterID = COALESCE(gg.CostCenterID, sg.CostCenterID)
LEFT JOIN dw.DimDepartment AS dep ON dep.DepartmentID = cc.DepartmentID
LEFT JOIN dw.DimCountry AS co ON co.CountryCode = cc.CountryCode
WHERE t.IsOpen = 1 AND COALESCE(cc.DepartmentID, '') <> 'D-901';
GO
