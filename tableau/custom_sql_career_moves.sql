/*
  Tableau Custom SQL: Career Moves (SQL Server)
  ===========================================================================
  Paste this whole query into Tableau: Data Source page > New Custom SQL
  (a query on the same SQL Server connection as the compensation walk).
  Same columns and numbers as the DuckDB mart marts.mart_career_moves.

  WHAT IT ANSWERS
  Promotions and demotions between two month-ends, by the grade a person left
  and the grade they reached, for any group of the walk's six views. A move is
  a change of grade in the job history; a person promoted twice in the period
  is two moves (moves) and one person (workers, per row).

  Same population as the walk's Promotions and Demotions steps: people present
  at both month-ends (executive officers excluded), placed in the group they are
  in at the To date. The walk counts them from pay records, this query from
  grade changes; the number of people promoted or demoted agrees in every group.
  director_and_above: the move is at Director (grade 7) or above on either side;
  into_director: a promotion that crosses into Director and above.

  TABLEAU CUSTOM SQL RULES (Tableau wraps this query in a subquery)
    - one SELECT statement: no CTEs (WITH), temp tables or variables
    - no ORDER BY
    - block comments only: a "--" comment on the last line would comment out
      the bracket Tableau adds after the query

  THE GRID
  Same rule as the compensation walk, at the GRID markers: the four offered
  period types, ending more than 12 months after the first month-end (88
  pairs). Keep it identical to the walk's, or a pair on the dashboard will
  have a walk and no rows here.
*/
SELECT
    t.from_date                                                                  AS from_month_end,
    t.to_date                                                                    AS to_month_end,
    (SELECT DATEADD(MONTH, 12, MIN(MonthEndDate)) FROM dw.MonthEndCalendar)          AS report_start_date,
    (SELECT MAX(MonthEndDate) FROM dw.MonthEndCalendar)                              AS report_as_of_date,
    cf.FiscalPeriod                                                              AS from_fiscal_period,
    ct.FiscalPeriod                                                              AS to_fiscal_period,
    DATEDIFF(MONTH, t.from_date, t.to_date)                                      AS months_between,
    t.view_order,
    t.view_name,
    t.group_id,
    CASE t.view_name
        WHEN 'Office'  THEN lo.OfficeName
        WHEN 'Country' THEN co.CountryName
        ELSE ou.OrgUnitName
    END                                                                          AS group_name,
    t.move_type,
    t.from_grade,
    fg.GradeLevel                                                                AS from_grade_level,
    t.to_grade,
    tg.GradeLevel                                                                AS to_grade_level,
    CAST(CASE WHEN t.from_grade >= 7 OR t.to_grade >= 7 THEN 1 ELSE 0 END AS BIT) AS director_and_above,
    CAST(CASE WHEN t.from_grade < 7 AND t.to_grade >= 7 THEN 1 ELSE 0 END AS BIT) AS into_director,
    CAST(t.moves AS INT)                                                         AS moves,
    CAST(t.workers AS INT)                                                       AS workers
FROM (
    /* 2. aggregate to date pair x view x group (at the To date) x move x grades */
    SELECT mv.from_date, mv.to_date, v.view_order, v.view_name, v.group_id,
           mv.move_type, mv.from_grade, mv.to_grade,
           COUNT(*) AS moves, COUNT(DISTINCT mv.WorkerID) AS workers
    FROM (
        /* 1. every change of grade between the two dates, for people present at both */
        SELECT g.from_date, g.to_date, gc.WorkerID, gc.from_grade, gc.to_grade,
               CASE WHEN gc.to_grade > gc.from_grade THEN 'Promotion' ELSE 'Demotion' END AS move_type,
               c.DepartmentID AS c_dept, c.LocationID AS c_loc, c.CountryCode AS c_country
        FROM (
                SELECT f.MonthEndDate AS from_date, t2.MonthEndDate AS to_date
                FROM dw.MonthEndCalendar AS f
                JOIN dw.MonthEndCalendar AS t2 ON t2.MonthEndDate > f.MonthEndDate
                WHERE t2.MonthEndDate > DATEADD(MONTH, 12, (SELECT MIN(MonthEndDate) FROM dw.MonthEndCalendar))   /* === GRID === first year is lead-in */
                  AND (   t2.PriorMonthEndDate = f.MonthEndDate                                                      /* === GRID === month */
                       OR (    MONTH(f.MonthEndDate) IN (3, 6, 9, 12) AND MONTH(t2.MonthEndDate) IN (3, 6, 9, 12)    /* === GRID === quarter-ends */
                           AND (   DATEDIFF(MONTH, f.MonthEndDate, t2.MonthEndDate) IN (3, 12)                         /* === GRID === quarter, year */
                                OR (MONTH(f.MonthEndDate) = 6 AND DATEDIFF(MONTH, f.MonthEndDate, t2.MonthEndDate) < 12))))  /* === GRID === year to date */
        ) AS g
        JOIN (
            SELECT j.WorkerID, j.EffectiveStartDate AS move_date, j.Grade AS to_grade,
                   LAG(j.Grade) OVER (PARTITION BY j.WorkerID ORDER BY j.EffectiveStartDate) AS from_grade
            FROM dw.FactJobHistory AS j
        ) AS gc
          ON gc.move_date > g.from_date AND gc.move_date <= g.to_date
         AND gc.from_grade IS NOT NULL AND gc.from_grade <> gc.to_grade
        JOIN dw.WorkerMonthEndSnapshot AS o
          ON o.MonthEndDate = g.from_date AND o.WorkerID = gc.WorkerID AND o.IsExecutiveOfficer = 0
        JOIN dw.WorkerMonthEndSnapshot AS c
          ON c.MonthEndDate = g.to_date AND c.WorkerID = gc.WorkerID
    ) AS mv
    LEFT JOIN (
            SELECT d.DepartmentID,
                   CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
                   d.ParentOrgUnitID AS LeaderOrgID
            FROM dw.DimDepartment AS d
            JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
        ) AS cd ON cd.DepartmentID = mv.c_dept
    CROSS APPLY (VALUES
        (1, 'Company',      CAST('ORG-000' AS VARCHAR(15))),
        (2, 'Function',     CAST(cd.FunctionID AS VARCHAR(15))),
        (3, 'Sub-function', CAST(cd.LeaderOrgID AS VARCHAR(15))),
        (4, 'Department',   CAST(mv.c_dept AS VARCHAR(15))),
        (5, 'Office',       CAST(mv.c_loc AS VARCHAR(15))),
        (6, 'Country',      CAST(mv.c_country AS VARCHAR(15)))
    ) AS v (view_order, view_name, group_id)
    GROUP BY mv.from_date, mv.to_date, v.view_order, v.view_name, v.group_id, mv.move_type, mv.from_grade, mv.to_grade
) AS t
JOIN dw.DimJobLevel AS fg ON fg.Grade = t.from_grade
JOIN dw.DimJobLevel AS tg ON tg.Grade = t.to_grade
JOIN dw.MonthEndCalendar AS cf ON cf.MonthEndDate = t.from_date
JOIN dw.MonthEndCalendar AS ct ON ct.MonthEndDate = t.to_date
LEFT JOIN dw.DimOrgUnit  AS ou ON ou.OrgUnitID = t.group_id
LEFT JOIN dw.DimLocation AS lo ON t.view_name = 'Office'  AND lo.LocationID  = t.group_id
LEFT JOIN dw.DimCountry  AS co ON t.view_name = 'Country' AND co.CountryCode = t.group_id
