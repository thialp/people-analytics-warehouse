/*
  03h_build_dw_headcount_walk.sql
  Builds dw.HeadcountFteWalk, the headcount and FTE walk, once per build. Runs after 03 and 03c
  (it reads dw.MonthEndCalendar, dw.WorkerMonthEndSnapshot, dw.DimWorker, dw.DimJobProfile,
  dw.FactJobHistory, dw.CwConversion and dw.CwMovement).

  Why a table: the walk compares every worker at both ends of every month (1.6M snapshot rows,
  read four times), checks job history for reorganizations, fans each worker-month into up to
  seven walk lines and groups them to 597,097 rows. Until now tableau/custom_sql_headcount_fte_walk.sql
  did all of that inside Tableau's query. With an extract it ran once per refresh; with a live
  connection (Tableau Cloud and Pulse through Tableau Bridge) it ran on every query, about 9 to
  40 seconds each, and a filter such as Closing only cannot skip any of the work. Built once here
  (about 25 seconds), the same question takes about 0.3 seconds.

  The logic is unchanged: the SELECT below is the Custom SQL's walk, moved here verbatim, the
  T-SQL twin of sql/03_marts/mart_headcount_fte_walk.sql. The Custom SQL now reads this table and
  joins the dimensions as before, so it returns the same 34 columns and 597,097 rows;
  10_validate_headcount_fte_walk.sql checks them.

  Grain: month-end x worker type x department x country x job family x grade x movement category x reason.
  Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DROP TABLE IF EXISTS dw.HeadcountFteWalk;
SELECT
    w.month_end_date      AS MonthEndDate,
    w.worker_type         AS WorkerType,
    w.department_id       AS DepartmentID,
    w.country_code        AS CountryCode,
    w.job_family_code     AS JobFamilyCode,
    w.grade               AS Grade,
    w.movement_order      AS MovementOrder,
    w.movement_category   AS MovementCategory,
    w.movement_reason     AS MovementReason,
    w.headcount           AS Headcount,
    w.fte                 AS FTE
INTO dw.HeadcountFteWalk
FROM (
    /* 3. one line per slice, month and movement */
    SELECT
        ln.month_end_date, ln.worker_type, ln.department_id, ln.country_code, ln.job_family_code, ln.grade,
        ln.movement_order, ln.movement_category, ln.movement_reason,
        SUM(ln.hc)                                                     AS headcount,
        CAST(SUM(CAST(ln.fte AS DECIMAL(18, 4))) AS DECIMAL(18, 2))    AS fte
    FROM (
        /* 2. each worker-month becomes the walk lines it feeds, in the prior (P) or current (C) slice */
        SELECT
            m.month_end_date,
            'Employee'                                                 AS worker_type,
            CASE WHEN v.side = 'P' THEN m.prior_department_id ELSE m.current_department_id END AS department_id,
            CASE WHEN v.side = 'P' THEN m.prior_country_code  ELSE m.current_country_code  END AS country_code,
            CASE WHEN v.side = 'P' THEN m.prior_family_code   ELSE m.current_family_code   END AS job_family_code,
            CASE WHEN v.side = 'P' THEN m.prior_grade         ELSE m.current_grade         END AS grade,
            v.movement_order, v.movement_category, v.movement_reason, v.hc, v.fte
        FROM (
            /* 1. every worker active at either end of each month, compared */
            SELECT
                c.month_end_date,
                c.prior_department_id, c.current_department_id,
                c.prior_country_code,  c.current_country_code,
                c.prior_family_code,   c.current_family_code,
                c.prior_grade,         c.current_grade,
                c.prior_fte,           c.current_fte,
                c.in_prior,            c.in_current,
                c.is_conversion,
                CASE
                    WHEN c.in_current = 1 AND c.in_prior = 0 THEN 'Hire'
                    WHEN c.in_prior = 1 AND c.in_current = 0 THEN 'Termination'
                    WHEN c.prior_department_id <> c.current_department_id
                      OR c.prior_country_code  <> c.current_country_code
                      OR c.prior_family_code   <> c.current_family_code
                      OR c.prior_grade         <> c.current_grade     THEN 'Internal Move'
                    ELSE 'No Change'
                END AS movement_type,
                CASE
                    WHEN c.in_current = 1 AND c.in_prior = 0 THEN 'New Hire'
                    WHEN c.in_prior = 1 AND c.in_current = 0 THEN COALESCE(c.termination_type, 'Unknown')
                    WHEN c.prior_department_id <> c.current_department_id
                        THEN CASE WHEN c.had_reorganization = 1 THEN 'Reorganization' ELSE 'Transfer' END
                    WHEN c.prior_country_code <> c.current_country_code THEN 'Location Change'
                    WHEN c.current_grade > c.prior_grade                 THEN 'Promotion'
                    WHEN c.current_grade < c.prior_grade                 THEN 'Demotion'
                    WHEN c.prior_family_code <> c.current_family_code    THEN 'Job Change'
                END AS movement_reason
            FROM (
                SELECT
                    p.month_end_date,
                    CASE WHEN pri.WorkerID IS NULL THEN 0 ELSE 1 END AS in_prior,
                    CASE WHEN cur.WorkerID IS NULL THEN 0 ELSE 1 END AS in_current,
                    pri.DepartmentID   AS prior_department_id,   cur.DepartmentID   AS current_department_id,
                    pri.CountryCode    AS prior_country_code,    cur.CountryCode    AS current_country_code,
                    pjp.JobFamilyCode  AS prior_family_code,     cjp.JobFamilyCode  AS current_family_code,
                    pri.Grade          AS prior_grade,           cur.Grade          AS current_grade,
                    pri.FTE            AS prior_fte,             cur.FTE            AS current_fte,
                    dw_w.TerminationType AS termination_type,
                    CASE WHEN cv.WorkerID IS NULL THEN 0 ELSE 1 END AS is_conversion,
                    CASE WHEN EXISTS (
                        SELECT 1 FROM dw.FactJobHistory AS j
                        WHERE j.WorkerID = p.worker_id
                          AND j.ActionReason = 'Reorganization'
                          AND j.EffectiveStartDate >  p.prior_month_end_date
                          AND j.EffectiveStartDate <= p.month_end_date
                    ) THEN 1 ELSE 0 END AS had_reorganization
                FROM (
                    SELECT cal1.MonthEndDate AS month_end_date, cal1.PriorMonthEndDate AS prior_month_end_date, s1.WorkerID AS worker_id
                    FROM dw.MonthEndCalendar AS cal1
                    JOIN dw.WorkerMonthEndSnapshot AS s1 ON s1.MonthEndDate = cal1.PriorMonthEndDate
                    UNION
                    SELECT cal2.MonthEndDate, cal2.PriorMonthEndDate, s2.WorkerID
                    FROM dw.MonthEndCalendar AS cal2
                    JOIN dw.WorkerMonthEndSnapshot AS s2 ON s2.MonthEndDate = cal2.MonthEndDate
                    WHERE cal2.PriorMonthEndDate IS NOT NULL
                ) AS p
                JOIN dw.DimWorker AS dw_w ON dw_w.WorkerID = p.worker_id
                LEFT JOIN dw.WorkerMonthEndSnapshot AS pri
                       ON pri.MonthEndDate = p.prior_month_end_date AND pri.WorkerID = p.worker_id
                LEFT JOIN dw.DimJobProfile AS pjp ON pjp.JobProfileID = pri.JobProfileID
                LEFT JOIN dw.WorkerMonthEndSnapshot AS cur
                       ON cur.MonthEndDate = p.month_end_date AND cur.WorkerID = p.worker_id
                LEFT JOIN dw.DimJobProfile AS cjp ON cjp.JobProfileID = cur.JobProfileID
                LEFT JOIN dw.CwConversion AS cv
                       ON cv.WorkerID = p.worker_id AND cv.MonthEndDate = p.month_end_date AND cv.IsWalkConversion = 1
            ) AS c
        ) AS m
        CROSS APPLY (VALUES
            (1, 'Opening', 'Opening', 1, m.prior_fte, 'P', m.in_prior),
            (2, 'Hires', m.movement_reason, 1, m.current_fte, 'C',
                CASE WHEN m.movement_type = 'Hire' AND m.is_conversion = 0 THEN 1 ELSE 0 END),
            (CASE WHEN m.movement_reason = 'Voluntary' THEN 3 ELSE 4 END,
                CASE WHEN m.movement_reason = 'Voluntary' THEN 'Voluntary Terminations' ELSE 'Involuntary Terminations' END,
                m.movement_reason, -1, -m.prior_fte, 'P',
                CASE WHEN m.movement_type = 'Termination' THEN 1 ELSE 0 END),
            (5, 'Internal Moves Out', m.movement_reason, -1, -m.prior_fte, 'P',
                CASE WHEN m.movement_type = 'Internal Move' THEN 1 ELSE 0 END),
            (6, 'Internal Moves In', m.movement_reason, 1, m.prior_fte, 'C',
                CASE WHEN m.movement_type = 'Internal Move' THEN 1 ELSE 0 END),
            (7, 'Conversions', 'Contingent to Employee', 1, m.current_fte, 'C',
                CASE WHEN m.movement_type = 'Hire' AND m.is_conversion = 1 THEN 1 ELSE 0 END),
            (8, 'Closing', 'Closing', 1, m.current_fte, 'C', m.in_current)
        ) AS v (movement_order, movement_category, movement_reason, hc, fte, side, keep_line)
        WHERE v.keep_line = 1

        UNION ALL
        /* 2b. contingent workers (Bridgeway, as held at each month-end): a slice is department x country */
        SELECT
            cm.MonthEndDate,
            'Contingent',
            CASE WHEN cv.side = 'P' THEN cm.PriorDepartmentID ELSE cm.CurrentDepartmentID END,
            CASE WHEN cv.side = 'P' THEN cm.PriorCountryCode  ELSE cm.CurrentCountryCode  END,
            NULL,
            NULL,
            cv.movement_order, cv.movement_category, cv.movement_reason, cv.hc, cv.fte
        FROM dw.CwMovement AS cm
        CROSS APPLY (VALUES
            (1, 'Opening', 'Opening', 1, 1.0, 'P', CAST(cm.InPrior AS INT)),
            (2, 'Starts', cm.MovementReason, 1, 1.0, 'C',
                CASE WHEN cm.MovementType = 'Start' THEN 1 ELSE 0 END),
            (3, 'Ends', cm.MovementReason, -1, -1.0, 'P',
                CASE WHEN cm.MovementType = 'End' THEN 1 ELSE 0 END),
            (5, 'Internal Moves Out', cm.MovementReason, -1, -1.0, 'P',
                CASE WHEN cm.MovementType = 'Internal Move' THEN 1 ELSE 0 END),
            (6, 'Internal Moves In', cm.MovementReason, 1, 1.0, 'C',
                CASE WHEN cm.MovementType = 'Internal Move' THEN 1 ELSE 0 END),
            (7, 'Conversions', cm.MovementReason, -1, -1.0, 'P',
                CASE WHEN cm.MovementType = 'Conversion' THEN 1 ELSE 0 END),
            (8, 'Closing', 'Closing', 1, 1.0, 'C', CAST(cm.InCurrent AS INT))
        ) AS cv (movement_order, movement_category, movement_reason, hc, fte, side, keep_line)
        WHERE cv.keep_line = 1
    ) AS ln
    GROUP BY ln.month_end_date, ln.worker_type, ln.department_id, ln.country_code, ln.job_family_code, ln.grade,
             ln.movement_order, ln.movement_category, ln.movement_reason
) AS w;

CREATE CLUSTERED INDEX CIX_HeadcountFteWalk ON dw.HeadcountFteWalk (MonthEndDate, MovementOrder);
GO
