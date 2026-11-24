/*
  custom_sql_pulse_headcount.sql
  Tableau Custom SQL for the Tableau Pulse metric Arcadia Headcount (Tableau Cloud, live through
  Tableau Bridge; SQL Server, database ArcadiaHR).

  Actuals and budget in one table, so the Pulse goal uses the same table and the same Month End Date
  as the metric (a goal on a related plan table with its own quarterly date makes Pulse drop the chart).

    actuals  the Headcount & FTE walk (dw.HeadcountFteWalk), every column as in
             custom_sql_headcount_fte_walk.sql; plan_headcount is NULL
    budget   the Budget version's planned ending headcount (rpt.vw_plan_vs_actual) per cost center
             (department x country) and worker type, phased to each month-end in a straight line from
             the prior quarter-end target, so the quarter-ends equal the plan exactly; written as Closing
             lines (movement_reason Budget) with headcount 0, so a metric on Closing keeps them and its
             totals do not move. Executive officers (D-901) are excluded, as in the plan everywhere.

  Checks: Jun 30, 2026 closing headcount 41,955 (41,946 without D-901), budget 43,010
  (30,337 employee + 12,673 contingent). Dashboard #1 does not use this query.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Arcadia Systems is fictional and all data is synthetic.
*/
SELECT
    w.MonthEndDate AS month_end_date,
    w.WorkerType AS worker_type,
    w.DepartmentID AS department_id,
    w.CountryCode AS country_code,
    w.JobFamilyCode AS job_family_code,
    CAST(w.Grade AS VARCHAR(2))                                        AS grade,
    w.MovementOrder AS movement_order,
    w.MovementCategory AS movement_category,
    w.MovementReason AS movement_reason,
    CASE w.MovementOrder
        WHEN 1 THEN 'Opening'   WHEN 2 THEN 'Joined'    WHEN 3 THEN 'Left'      WHEN 4 THEN 'Left'
        WHEN 5 THEN 'Moved out' WHEN 6 THEN 'Moved in'  WHEN 7 THEN 'Converted' WHEN 8 THEN 'Closing'
    END                                                                AS walk_step,
    w.Headcount AS headcount,
    w.FTE AS fte,
    w.PlanHeadcount AS plan_headcount,
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
    /* actuals: the walk, built by sqlserver/03h_build_dw_headcount_walk.sql */
    SELECT hw.MonthEndDate, hw.WorkerType, hw.DepartmentID, hw.CountryCode, hw.JobFamilyCode, hw.Grade,
           hw.MovementOrder, hw.MovementCategory, hw.MovementReason, hw.Headcount, hw.FTE,
           CAST(NULL AS DECIMAL(12, 2)) AS PlanHeadcount
    FROM dw.HeadcountFteWalk AS hw

    UNION ALL
    /* budget: the plan's ending headcount per cost center and worker type, phased to every month-end
       in a straight line from the prior quarter-end target to this quarter's (flat when there is no
       prior quarter); dated and labelled as Closing lines with no headcount */
    SELECT cal.MonthEndDate, wt.WorkerType, p.department_id, p.country_code, NULL, NULL,
           8, 'Closing', 'Budget', 0, 0,
           CAST(wt.PrevPlan + (wt.QuarterPlan - wt.PrevPlan)
                * DATEDIFF(MONTH, p.prior_quarter_end, cal.MonthEndDate) / 3.0 AS DECIMAL(12, 2))
    FROM (
        SELECT v.department_id, v.country_code, v.quarter_end_date,
               EOMONTH(DATEADD(MONTH, -3, v.quarter_end_date))                            AS prior_quarter_end,
               v.planned_ending_headcount                                                  AS plan_emp,
               v.planned_cw_headcount                                                      AS plan_cw,
               LAG(v.quarter_end_date)         OVER (PARTITION BY v.department_id, v.country_code ORDER BY v.quarter_end_date) AS prev_quarter_end,
               LAG(v.planned_ending_headcount) OVER (PARTITION BY v.department_id, v.country_code ORDER BY v.quarter_end_date) AS prev_emp,
               LAG(v.planned_cw_headcount)     OVER (PARTITION BY v.department_id, v.country_code ORDER BY v.quarter_end_date) AS prev_cw
        FROM rpt.vw_plan_vs_actual AS v
        WHERE v.version_type = 'Budget' AND v.department_id <> 'D-901'
    ) AS p
    JOIN dw.MonthEndCalendar AS cal
      ON cal.MonthEndDate > p.prior_quarter_end AND cal.MonthEndDate <= p.quarter_end_date
    CROSS APPLY (VALUES
        ('Employee',   p.plan_emp, CASE WHEN p.prev_quarter_end = p.prior_quarter_end THEN p.prev_emp ELSE p.plan_emp END),
        ('Contingent', p.plan_cw,  CASE WHEN p.prev_quarter_end = p.prior_quarter_end THEN p.prev_cw  ELSE p.plan_cw  END)
    ) AS wt (WorkerType, QuarterPlan, PrevPlan)
) AS w
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate  = w.MonthEndDate
JOIN dw.DimDepartment    AS d   ON d.DepartmentID    = w.DepartmentID
JOIN dw.DimCountry       AS co  ON co.CountryCode    = w.CountryCode
LEFT JOIN (SELECT DISTINCT JobFamilyCode, JobFamily FROM dw.DimJobProfile) AS jf
                                ON jf.JobFamilyCode  = w.JobFamilyCode
LEFT JOIN dw.DimJobLevel AS lv  ON lv.Grade          = w.Grade
