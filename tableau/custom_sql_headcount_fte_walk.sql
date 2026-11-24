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

  Live connections: the walk itself is built once per build into dw.HeadcountFteWalk
  (sqlserver/03h_build_dw_headcount_walk.sql), and this query reads it and adds the names.
  Computed here, the walk cost 9 to 40 seconds on every live query (Tableau Cloud and Pulse
  through Tableau Bridge); read from the table, about 0.3 seconds. Columns and rows are unchanged.

  grade and fiscal_year are returned as text, as the workbook typed them on the CSVs.
  Tableau rules: one SELECT, no CTEs, no ORDER BY, block comments only.
  Checked row for row against the DuckDB marts by sqlserver/check_tsql_in_duckdb.py, and on
  SQL Server by sqlserver/10_validate_headcount_fte_walk.sql.
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
FROM dw.HeadcountFteWalk AS w   /* built by sqlserver/03h_build_dw_headcount_walk.sql */
JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate  = w.MonthEndDate
JOIN dw.DimDepartment    AS d   ON d.DepartmentID    = w.DepartmentID
JOIN dw.DimCountry       AS co  ON co.CountryCode    = w.CountryCode
LEFT JOIN (SELECT DISTINCT JobFamilyCode, JobFamily FROM dw.DimJobProfile) AS jf
                                ON jf.JobFamilyCode  = w.JobFamilyCode
LEFT JOIN dw.DimJobLevel AS lv  ON lv.Grade          = w.Grade
