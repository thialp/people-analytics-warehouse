/*
  custom_sql_headcount_fte_walk.sql
  Tableau Custom SQL for Dashboard #1, Headcount & FTE Walk (SQL Server, database ArcadiaHR).

  Replaces the six CSVs the dashboard was built on (mart_headcount_fte_walk + mart_dim_month,
  mart_dim_department, mart_dim_country, mart_dim_job_family, mart_dim_grade) with one flat
  query. Every column keeps the CSV's name, so Tableau gives each field the same caption and
  Replace Data Source maps them one to one. The dimension columns are joined in on keys that
  are unique in their dimension, so no fact row is repeated: the query returns exactly the
  fact's rows and the same totals.

  Grain: month-end x worker type x department x country x job family x grade x movement
  category x reason. For every slice and month: Opening + Hires - Voluntary - Involuntary
  - Internal Moves Out + Internal Moves In + Conversions = Closing.

  Release 3: worker_type Employee (Keystone HR) or Contingent (Bridgeway VMS, as held at each
  month-end: dw.CwMovement). Contingent workers have no job family or grade (theirs are
  empty, so those two dimensions are LEFT JOINed); their lines are Opening, Starts, Ends,
  Internal Moves, Conversions and Closing. A contingent worker hired as an employee is a
  Conversion (movement_order 7): -1 for Contingent and +1 for Employee in the same month, so
  the total never moves, and that employee is not in Hires. walk_step names each line the same
  way for both worker types (Opening, Joined, Left, Moved out, Moved in, Converted, Closing).

  Rules (the same as sql/02_intermediate/int_worker_movement.sql, int_cw_movement.sql and
  sql/03_marts/mart_headcount_fte_walk.sql in the DuckDB pipeline):
    * an employee slice is department x country x job family x grade; a contingent worker's
      is department x country;
    * a worker in the prior month-end only is a termination (by termination type), in the
      current only a hire, in both with another slice an internal move, booked out of the
      old slice and into the new one;
    * one reason per move: department (Reorganization if a reorg job action took effect in
      the month, else Transfer), then country (Location Change), then grade (Promotion /
      Demotion), then job family (Job Change);
    * every employee is 1.0 FTE (release 3 removed part-time) and a contingent worker counts
      1.0, so fte = headcount on every line;
    * executive officers are counted (they are excluded only where pay is shown).

  grade and fiscal_year are returned as text, as the workbook typed them on the CSVs.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Checked row for row against the DuckDB marts by sqlserver/check_tsql_in_duckdb.py, and on
  SQL Server by sqlserver/10_validate_headcount_fte_walk.sql.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    w.month_end_date,
    w.worker_type,
    w.department_id,
    w.country_code,
    w.job_family_code,
    CAST(w.grade AS VARCHAR(2))                                        AS grade,
    w.movement_order,
    w.movement_category,
    w.movement_reason,
    CASE w.movement_order
        WHEN 1 THEN 'Opening'   WHEN 2 THEN 'Joined'    WHEN 3 THEN 'Left'      WHEN 4 THEN 'Left'
        WHEN 5 THEN 'Moved out' WHEN 6 THEN 'Moved in'  WHEN 7 THEN 'Converted' WHEN 8 THEN 'Closing'
    END                                                                AS walk_step,
    w.headcount,
    w.fte,
    /* mart_dim_month */
    cal.PriorMonthEndDate                                              AS prior_month_end_date,
    CAST(cal.FiscalYear AS VARCHAR(4))                                 AS fiscal_year,
    CONCAT('FY', RIGHT(CAST(cal.FiscalYear AS VARCHAR(4)), 2))         AS fiscal_year_label,
    cal.FiscalQuarterLabel                                             AS fiscal_quarter_label,
    cal.FiscalPeriod                                                   AS fiscal_period,
    cal.FiscalMonth                                                    AS fiscal_month,
    cal.IsFiscalYearEnd                                                AS is_fiscal_year_end,
    /* mart_dim_department */
    d.DepartmentName                                                   AS department_name,
    d.SubFunction                                                      AS sub_function,
    d.FunctionName                                                     AS function_name,
    d.ParentOrgUnitID                                                  AS parent_org_unit_id,
    d.CostCenter                                                       AS cost_center,
    d.HeadGrade                                                        AS head_grade,
    /* mart_dim_country */
    co.CountryName                                                     AS country_name,
    co.Region                                                          AS region,
    co.CurrencyCode                                                    AS currency_code,
    co.PayIndex                                                        AS pay_index,
    /* mart_dim_job_family */
    jf.JobFamily                                                       AS job_family,
    /* mart_dim_grade */
    lv.LevelCode                                                       AS level_code,
    lv.GradeLevel                                                      AS grade_level,
    lv.CareerTrack                                                     AS career_track,
    lv.UsBaseSalaryUsd                                                 AS us_base_salary_usd
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
) AS w
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate  = w.month_end_date
JOIN dw.DimDepartment    AS d   ON d.DepartmentID    = w.department_id
JOIN dw.DimCountry       AS co  ON co.CountryCode    = w.country_code
LEFT JOIN (SELECT DISTINCT JobFamilyCode, JobFamily FROM dw.DimJobProfile) AS jf
                                ON jf.JobFamilyCode  = w.job_family_code
LEFT JOIN dw.DimJobLevel AS lv  ON lv.Grade          = w.grade
