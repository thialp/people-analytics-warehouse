/*
  Tableau Custom SQL: Region Walk (SQL Server)
  ===========================================================================
  Paste this whole query into Tableau: Data Source page > New Custom SQL
  (a third query on the same SQL Server connection as the compensation walk).
  Same columns and numbers as the DuckDB mart marts.mart_region_walk.

  WHAT IT ANSWERS
  For a pair of month-ends and a group in any of the walk's six views, how
  headcount moved in each region, as a walk that closes exactly per region:

      opening + hires - exits + transfers_in - transfers_out
              + region_moves_in - region_moves_out = closing

  transfers    people who joined or left the GROUP (the walk's Transfers In/Out)
  region moves people who stayed in the group but changed region (an office in
               another region): out of the old region, into the new one
  Departures by region = exits + transfers_out + region_moves_out.

  hires_joined_elsewhere  of the hires, those who joined another group of this
               view and moved in before the To date (the walk's Hires with
               reason 'Joined Elsewhere'). hires - hires_joined_elsewhere are
               the people who joined THIS group and are still in it: the
               "hires still here" of the tie-out note, never more than the
               Headcount & FTE Walk's joined for the group (test 79).

  Same population as the walk: executive officers excluded; a person is placed
  by their office at each end of the pair; someone hired and gone between the
  two dates is in neither snapshot. Summed over regions, a group's opening,
  hires, exits, transfers and closing equal the walk's headcount lines.

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
    t.region,
    CAST(t.opening       AS INT)                                                 AS opening_headcount,
    CAST(t.hires         AS INT)                                                 AS hires,
    CAST(t.hires_joined_elsewhere AS INT)                                        AS hires_joined_elsewhere,
    CAST(t.exits         AS INT)                                                 AS exits,
    CAST(t.transfers_in  AS INT)                                                 AS transfers_in,
    CAST(t.transfers_out AS INT)                                                 AS transfers_out,
    CAST(t.moves_in      AS INT)                                                 AS region_moves_in,
    CAST(t.moves_out     AS INT)                                                 AS region_moves_out,
    CAST(t.closing       AS INT)                                                 AS closing_headcount
FROM (
    /* 3. aggregate to date pair x view x group x region */
    SELECT
        pg.from_date, pg.to_date, v.view_order, v.view_name, sd.group_id, sd.region,
        SUM(sd.opening) AS opening, SUM(sd.hires) AS hires, SUM(sd.hires_elsewhere) AS hires_joined_elsewhere,
        SUM(sd.exits) AS exits,
        SUM(sd.transfers_in) AS transfers_in, SUM(sd.transfers_out) AS transfers_out,
        SUM(sd.moves_in) AS moves_in, SUM(sd.moves_out) AS moves_out, SUM(sd.closing) AS closing
    FROM (
        /* 1. everyone present at the From or the To month-end, pre-aggregated */
        SELECT
            g.from_date, g.to_date,
            CASE WHEN o.WorkerID IS NULL THEN 'Hire' WHEN c.WorkerID IS NULL THEN 'Exit' ELSE 'Continuing' END AS worker_class,
            o.DepartmentID AS o_dept, o.LocationID AS o_loc,
            c.DepartmentID AS c_dept, c.LocationID AS c_loc,
            /* hires: the group they joined (department and office on their hire month-end) */
            CASE WHEN o.WorkerID IS NULL THEN h.DepartmentID END AS h_dept,
            CASE WHEN o.WorkerID IS NULL THEN h.LocationID   END AS h_loc,
            COUNT(*) AS n
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
        JOIN dw.DimWorker AS w
          ON w.OriginalHireDate <= g.to_date
         AND (w.TerminationDate IS NULL OR w.TerminationDate >= g.from_date)
         AND w.IsExecutiveOfficer = 0
        LEFT JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = g.from_date AND o.WorkerID = w.WorkerID
        LEFT JOIN dw.WorkerMonthEndSnapshot AS c ON c.MonthEndDate = g.to_date   AND c.WorkerID = w.WorkerID
        LEFT JOIN dw.WorkerMonthEndSnapshot AS h
               ON h.MonthEndDate = EOMONTH(w.OriginalHireDate) AND h.WorkerID = w.WorkerID
        WHERE o.WorkerID IS NOT NULL OR c.WorkerID IS NOT NULL
        GROUP BY g.from_date, g.to_date,
                 CASE WHEN o.WorkerID IS NULL THEN 'Hire' WHEN c.WorkerID IS NULL THEN 'Exit' ELSE 'Continuing' END,
                 o.DepartmentID, o.LocationID, c.DepartmentID, c.LocationID,
                 CASE WHEN o.WorkerID IS NULL THEN h.DepartmentID END, CASE WHEN o.WorkerID IS NULL THEN h.LocationID END
    ) AS pg
    LEFT JOIN (
            SELECT d.DepartmentID,
                   CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
                   d.ParentOrgUnitID AS LeaderOrgID
            FROM dw.DimDepartment AS d
            JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
        ) AS od ON od.DepartmentID = pg.o_dept
    LEFT JOIN (
            SELECT d.DepartmentID,
                   CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
                   d.ParentOrgUnitID AS LeaderOrgID
            FROM dw.DimDepartment AS d
            JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
        ) AS cd ON cd.DepartmentID = pg.c_dept
    LEFT JOIN (
            SELECT d.DepartmentID,
                   CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
                   d.ParentOrgUnitID AS LeaderOrgID
            FROM dw.DimDepartment AS d
            JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
        ) AS hd ON hd.DepartmentID = pg.h_dept
    LEFT JOIN dw.DimLocation AS ol ON ol.LocationID = pg.o_loc
    LEFT JOIN dw.DimLocation AS cl ON cl.LocationID = pg.c_loc
    LEFT JOIN dw.DimLocation AS hl ON hl.LocationID = pg.h_loc
    /* 2. the six views, then two lines per row: the From side (group and region at
          the From date) and the To side */
    CROSS APPLY (VALUES
        (1, 'Company',      CAST('ORG-000' AS VARCHAR(15)),      CAST('ORG-000' AS VARCHAR(15)),      CAST('ORG-000' AS VARCHAR(15))),
        (2, 'Function',     CAST(od.FunctionID AS VARCHAR(15)),  CAST(cd.FunctionID AS VARCHAR(15)),  CAST(hd.FunctionID AS VARCHAR(15))),
        (3, 'Sub-function', CAST(od.LeaderOrgID AS VARCHAR(15)), CAST(cd.LeaderOrgID AS VARCHAR(15)), CAST(hd.LeaderOrgID AS VARCHAR(15))),
        (4, 'Department',   CAST(pg.o_dept AS VARCHAR(15)),      CAST(pg.c_dept AS VARCHAR(15)),      CAST(pg.h_dept AS VARCHAR(15))),
        (5, 'Office',       CAST(pg.o_loc AS VARCHAR(15)),       CAST(pg.c_loc AS VARCHAR(15)),       CAST(pg.h_loc AS VARCHAR(15))),
        (6, 'Country',      CAST(ol.CountryCode AS VARCHAR(15)), CAST(cl.CountryCode AS VARCHAR(15)), CAST(hl.CountryCode AS VARCHAR(15)))
    ) AS v (view_order, view_name, open_key, close_key, hire_key)
    CROSS APPLY (VALUES
        ('From', v.open_key, ol.Region,
            CASE WHEN pg.worker_class <> 'Hire' THEN pg.n ELSE 0 END, 0, 0,
            CASE WHEN pg.worker_class = 'Exit' THEN pg.n ELSE 0 END, 0,
            CASE WHEN pg.worker_class = 'Continuing' AND v.open_key <> v.close_key THEN pg.n ELSE 0 END, 0,
            CASE WHEN pg.worker_class = 'Continuing' AND v.open_key = v.close_key AND ol.Region <> cl.Region THEN pg.n ELSE 0 END, 0),
        ('To', v.close_key, cl.Region,
            0, CASE WHEN pg.worker_class = 'Hire' THEN pg.n ELSE 0 END,
            CASE WHEN pg.worker_class = 'Hire' AND v.hire_key <> v.close_key THEN pg.n ELSE 0 END,
            0, CASE WHEN pg.worker_class = 'Continuing' AND v.open_key <> v.close_key THEN pg.n ELSE 0 END,
            0, CASE WHEN pg.worker_class = 'Continuing' AND v.open_key = v.close_key AND ol.Region <> cl.Region THEN pg.n ELSE 0 END,
            0, CASE WHEN pg.worker_class <> 'Exit' THEN pg.n ELSE 0 END)
    ) AS sd (side, group_id, region, opening, hires, hires_elsewhere, exits, transfers_in, transfers_out, moves_in, moves_out, closing)
    WHERE (sd.side = 'From' AND pg.worker_class <> 'Hire') OR (sd.side = 'To' AND pg.worker_class <> 'Exit')
    GROUP BY pg.from_date, pg.to_date, v.view_order, v.view_name, sd.group_id, sd.region
    HAVING SUM(sd.opening) + SUM(sd.hires) + SUM(sd.exits) + SUM(sd.transfers_in) + SUM(sd.transfers_out)
         + SUM(sd.moves_in) + SUM(sd.moves_out) + SUM(sd.closing) > 0
) AS t
JOIN dw.MonthEndCalendar AS cf ON cf.MonthEndDate = t.from_date
JOIN dw.MonthEndCalendar AS ct ON ct.MonthEndDate = t.to_date
LEFT JOIN dw.DimOrgUnit  AS ou ON ou.OrgUnitID = t.group_id
LEFT JOIN dw.DimLocation AS lo ON t.view_name = 'Office'  AND lo.LocationID  = t.group_id
LEFT JOIN dw.DimCountry  AS co ON t.view_name = 'Country' AND co.CountryCode = t.group_id
