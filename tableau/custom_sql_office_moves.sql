/*
  Tableau Custom SQL: Office Moves (SQL Server)
  ===========================================================================
  Paste this whole query into Tableau: Data Source page > New Custom SQL
  (a second query on the same SQL Server connection as the compensation walk).
  Same columns and numbers as the DuckDB mart marts.mart_office_moves.
  Field reference and worked examples: docs/projects/compensation-walk/office_moves.md

  WHAT IT ANSWERS
  For a pair of month-ends (From, To) and a group of people, which people
  changed office between the two dates, and from which office to which. It is
  built to sit beside the compensation walk on one dashboard: the date pair,
  the six views (Company, Function, Leader, Department, Office, Country) and the
  group names are the walk's, so the same parameters filter both queries and a
  map of office moves follows the dashboard filters like every other sheet.

  WHO IS A MOVER
  A worker present at BOTH month-ends whose office differs. Only From and To are
  compared, exactly as in the walk: A -> B -> C is one move A -> C, and
  A -> B -> A is no move. Executive officers are excluded, as in the walk.

  WHICH GROUP A MOVE BELONGS TO (group_side)
  The group the person is in at each end of the pair, by the walk's rule for
  that view:
    Both   same group at both ends: a move inside the group
    From   the person was in this group at the From date and left it
    To     the person joined this group by the To date
  Examples. Company view: every move is 'Both'. Office view: every move is a
  'From' row at the office it left and a 'To' row at the office it joined, so
  'To' = the walk's Transfers In and 'From' = Transfers Out. Country view: a
  move inside one country is 'Both'; a move across a border is 'From' for the
  old country and 'To' for the new one. Function / Leader / Department: a mover
  who also changed department appears once in each group they were in.
  The number of people moving inside a selected group is therefore
  SUM(workers) for that view and group, whatever the side; add the filter
  group_side to separate inbound from outbound.

  TABLEAU CUSTOM SQL RULES (Tableau wraps this query in a subquery)
    - one SELECT statement: no CTEs (WITH), temp tables or variables
    - no ORDER BY
    - block comments only: a "--" comment on the last line would comment out
      the bracket Tableau adds after the query
  Without CTEs the logic is layered as derived tables, read inside out:
    1. movers         one row per worker per date pair whose office changed
    2. pre-aggregate  movers with the same dates, departments, offices and
                      reason become one row: aggregate early ...
    3. expand         ... expand late: CROSS APPLY (VALUES) turns each row into
                      six views, then into the sides that apply
    4. aggregate      to date pair x view x group x side x office pair x reason

  THE GRID
  Same rule as the compensation walk, shown twice at the GRID markers: both
  month-ends are quarter ends (136 pairs), or the two are consecutive (48
  month-over-month pairs). Keep it identical to the walk's, or a pair on the
  dashboard will have a walk and no map.
*/
SELECT
    t.from_date                                                                  AS from_month_end,
    t.to_date                                                                    AS to_month_end,
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
    CASE t.view_name
        WHEN 'Function'   THEN 'Arcadia Systems'
        WHEN 'Leader'     THEN ou.FunctionName
        WHEN 'Department' THEN ou.FunctionName
        WHEN 'Office'     THEN lo.CountryName
        WHEN 'Country'    THEN co.Region
    END                                                                          AS group_parent,
    t.group_side,
    t.o_loc                                                                      AS from_location_id,
    fl.OfficeName                                                                AS from_office,
    fl.City                                                                      AS from_city,
    fl.CountryName                                                               AS from_country,
    fl.Region                                                                    AS from_region,
    fl.Latitude                                                                  AS from_latitude,
    fl.Longitude                                                                 AS from_longitude,
    t.c_loc                                                                      AS to_location_id,
    tl.OfficeName                                                                AS to_office,
    tl.City                                                                      AS to_city,
    tl.CountryName                                                               AS to_country,
    tl.Region                                                                    AS to_region,
    tl.Latitude                                                                  AS to_latitude,
    tl.Longitude                                                                 AS to_longitude,
    CASE WHEN fl.CountryCode = tl.CountryCode THEN 'Domestic' ELSE 'International' END          AS flow_scope,
    CASE WHEN fl.CountryCode = tl.CountryCode THEN 'Within one country' ELSE 'Across a border' END AS flow_scope_label,
    CASE WHEN fl.Region = tl.Region THEN 'Same region' ELSE 'Across regions' END                 AS region_scope,
    t.move_reason,
    CAST(t.workers AS INT)                                                       AS workers
FROM (
    /* 4. aggregate to date pair x view x group x side x office pair x reason */
    SELECT
        ml.from_date, ml.to_date, ml.view_order, ml.view_name, ml.group_id, ml.group_side,
        ml.o_loc, ml.c_loc, ml.move_reason,
        SUM(ml.n) AS workers
    FROM (
        /* 3. expand late: six views, then the sides that apply */
        SELECT
            pg.from_date, pg.to_date, v.view_order, v.view_name, sd.group_id, sd.group_side,
            pg.o_loc, pg.c_loc, pg.move_reason, pg.n
        FROM (
            /* 2. pre-aggregate: one row per date pair x departments x offices x reason */
            SELECT mv.from_date, mv.to_date, mv.o_dept, mv.o_loc, mv.c_dept, mv.c_loc, mv.move_reason,
                   COUNT(*) AS n
            FROM (
                /* 1. movers: present at both month-ends, office differs */
                SELECT
                    g.from_date, g.to_date,
                    o.DepartmentID AS o_dept, o.LocationID AS o_loc,
                    c.DepartmentID AS c_dept, c.LocationID AS c_loc,
                    ISNULL(lc.LocationMoveReason, 'Other') AS move_reason
                FROM (
                    SELECT f.MonthEndDate AS from_date, t2.MonthEndDate AS to_date
                    FROM dw.MonthEndCalendar AS f
                    JOIN dw.MonthEndCalendar AS t2 ON t2.MonthEndDate > f.MonthEndDate
                    WHERE (MONTH(f.MonthEndDate) IN (3, 6, 9, 12) AND MONTH(t2.MonthEndDate) IN (3, 6, 9, 12))  /* === GRID === */
                       OR t2.PriorMonthEndDate = f.MonthEndDate                                                     /* === GRID === */
                ) AS g
                JOIN dw.WorkerMonthEndSnapshot AS o  ON o.MonthEndDate  = g.from_date AND o.IsExecutiveOfficer = 0
                JOIN dw.WorkerMonthEndSnapshot AS c  ON c.MonthEndDate  = g.to_date   AND c.WorkerID  = o.WorkerID
                JOIN dw.WorkerPayLedger        AS lc ON lc.MonthEndDate = g.to_date   AND lc.WorkerID = o.WorkerID
                WHERE o.LocationID <> c.LocationID
            ) AS mv
            GROUP BY mv.from_date, mv.to_date, mv.o_dept, mv.o_loc, mv.c_dept, mv.c_loc, mv.move_reason
        ) AS pg
        /* the function and leader organization each department rolls up to,
           and the country of each office, on both sides of the pair */
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
        LEFT JOIN dw.DimLocation AS ol ON ol.LocationID = pg.o_loc
        LEFT JOIN dw.DimLocation AS cl ON cl.LocationID = pg.c_loc
        /* the six views: the group a mover belongs to at each end of the pair */
        CROSS APPLY (VALUES
            (1, 'Company',    CAST('ORG-000' AS VARCHAR(15)),      CAST('ORG-000' AS VARCHAR(15))),
            (2, 'Function',   CAST(od.FunctionID AS VARCHAR(15)),  CAST(cd.FunctionID AS VARCHAR(15))),
            (3, 'Leader',     CAST(od.LeaderOrgID AS VARCHAR(15)), CAST(cd.LeaderOrgID AS VARCHAR(15))),
            (4, 'Department', CAST(pg.o_dept AS VARCHAR(15)),      CAST(pg.c_dept AS VARCHAR(15))),
            (5, 'Office',     CAST(pg.o_loc AS VARCHAR(15)),       CAST(pg.c_loc AS VARCHAR(15))),
            (6, 'Country',    CAST(ol.CountryCode AS VARCHAR(15)), CAST(cl.CountryCode AS VARCHAR(15)))
        ) AS v (view_order, view_name, open_key, close_key)
        /* the sides: one row when the group is the same at both ends, otherwise
           one row for the group the mover left and one for the group joined */
        CROSS APPLY (VALUES
            ('Both', v.open_key,  CASE WHEN v.open_key =  v.close_key THEN 1 ELSE 0 END),
            ('From', v.open_key,  CASE WHEN v.open_key <> v.close_key THEN 1 ELSE 0 END),
            ('To',   v.close_key, CASE WHEN v.open_key <> v.close_key THEN 1 ELSE 0 END)
        ) AS sd (group_side, group_id, include_line)
        WHERE sd.include_line = 1
    ) AS ml
    GROUP BY ml.from_date, ml.to_date, ml.view_order, ml.view_name, ml.group_id, ml.group_side,
             ml.o_loc, ml.c_loc, ml.move_reason
) AS t
JOIN dw.MonthEndCalendar AS cf ON cf.MonthEndDate = t.from_date
JOIN dw.MonthEndCalendar AS ct ON ct.MonthEndDate = t.to_date
JOIN dw.DimLocation      AS fl ON fl.LocationID   = t.o_loc
JOIN dw.DimLocation      AS tl ON tl.LocationID   = t.c_loc
LEFT JOIN dw.DimOrgUnit  AS ou ON ou.OrgUnitID    = t.group_id
LEFT JOIN dw.DimLocation AS lo ON t.view_name = 'Office'  AND lo.LocationID  = t.group_id
LEFT JOIN dw.DimCountry  AS co ON t.view_name = 'Country' AND co.CountryCode = t.group_id
