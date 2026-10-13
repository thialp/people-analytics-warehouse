/*
  Tableau Custom SQL: Workforce Footprint (SQL Server)
  ===========================================================================
  Paste this whole query into Tableau: Data Source page > New Custom SQL,
  on the same SQL Server connection as the compensation walk (ArcadiaHR).
  ONE data source feeds the whole Footprint dashboard: the KPI cards, the map
  (offices and routes are two row types of the same table, so they can be two
  layers of one map), Top drivers, Growth by office / country / region, and
  the rail (period, view, group), whose fields keep the walk's names.

  WHAT IT ANSWERS
  For a pair of month-ends (From, To) and a group of people: where the group's
  people are (by office), how each office's headcount moved, and who moved
  between offices. Every office closes exactly, for headcount and FTE:

      Opening + Hires - Voluntary Exits - Involuntary Exits
              + Transfers In - Transfers Out
              + Office Moves In - Office Moves Out                 (same country)
              + Cross-border Moves In - Cross-border Moves Out
              + FTE Changes (FTE only)
      = Closing

  ROW TYPES
    row_type = 'Office'  one row per date pair x view x group x office x step.
                         headcount and fte are SIGNED (exits and "out" steps
                         are negative), so SUM over the steps of an office is
                         its change and Opening + steps = Closing.
    row_type = 'Route'   one row per date pair x view x group x side x
                         origin office x destination office: people present
                         at both month-ends whose office differs. headcount
                         is the number of people (positive); fte is NULL.
  Never sum the two row types together: filter row_type in every calc.

  WHO IS COUNTED
  Everyone active at a month-end except the 9 executive officers (CEO and
  function heads), as in every Compensation Walk source, so the rail's group
  lists are identical: FY26 28,438 -> 30,005 (Dashboard #1, which keeps them,
  shows 28,447 -> 30,014). Someone hired and gone between the two dates is in
  neither snapshot, so Hires and Exits are smaller than Dashboard #1's monthly
  sums (FY26: 4,790 hires here, 5,235 there; 445 joined and left in the year).
  Only From and To are compared: A -> B -> C is one move A -> C, A -> B -> A
  is no move.

  WHICH STEP A CONTINUING PERSON LANDS IN (decided per view, like the walk)
    office changed                  Office Moves Out at the old office (the
                                    group they were in), Office Moves In at
                                    the new office (the group they joined);
                                    Cross-border when the countries differ
    office same, group changed      Transfers Out / Transfers In (only the
                                    Function, Sub-function and Department
                                    views can have these)
    FTE changed                     FTE Changes at the closing office
  Out and In lines carry the OPENING FTE, so the FTE walk closes per office.
  In the Company view every move is out of one office and into another:
  Office Moves In = Office Moves Out, and they net to zero.

  ROUTE SIDES (group_side, same rule as custom_sql_office_moves.sql)
    Both   the mover was in the group at both ends: a move inside the group
    From   in the group at From and left it
    To     joined the group by To
  People who moved, for a group = SUM(headcount) of its Route rows.

  TABLEAU CUSTOM SQL RULES (Tableau wraps this query in a subquery)
    - one SELECT statement: no CTEs (WITH), temp tables or variables
    - no ORDER BY
    - block comments only

  THE GRID
  Same rule as the compensation walk, at the GRID markers (two places: the
  office part and the route part): the four offered period types, ending
  more than 12 months after the first month-end (88 pairs).
*/
SELECT
    t.from_date                                                                  AS from_month_end,
    t.to_date                                                                    AS to_month_end,
    (SELECT DATEADD(MONTH, 12, MIN(MonthEndDate)) FROM dw.MonthEndCalendar)      AS report_start_date,
    (SELECT MAX(MonthEndDate) FROM dw.MonthEndCalendar)                          AS report_as_of_date,
    cf.FiscalPeriod                                                              AS from_fiscal_period,
    ct.FiscalPeriod                                                              AS to_fiscal_period,
    cf.FiscalQuarterLabel                                                        AS from_fiscal_quarter,
    ct.FiscalQuarterLabel                                                        AS to_fiscal_quarter,
    DATEDIFF(MONTH, t.from_date, t.to_date)                                      AS months_between,
    CASE
        WHEN DATEDIFF(MONTH, t.from_date, t.to_date) = 1  THEN 'Month over Month'
        WHEN DATEDIFF(MONTH, t.from_date, t.to_date) = 3  THEN 'Quarter over Quarter'
        WHEN DATEDIFF(MONTH, t.from_date, t.to_date) = 12 THEN 'Year over Year'
        WHEN MONTH(t.from_date) = 6 AND t.to_date < DATEADD(MONTH, 12, t.from_date) THEN 'Fiscal Year to Date'
        ELSE 'Custom Range'
    END                                                                          AS pair_type,
    t.view_order,
    t.view_name,
    t.group_id,
    CASE t.view_name
        WHEN 'Office'  THEN lo.OfficeName
        WHEN 'Country' THEN co.CountryName
        ELSE ou.OrgUnitName
    END                                                                          AS group_name,
    CASE t.view_name
        WHEN 'Function'     THEN 'Arcadia Systems'
        WHEN 'Sub-function' THEN ou.FunctionName
        WHEN 'Department'   THEN ou.FunctionName
        WHEN 'Office'       THEN lo.CountryName
        WHEN 'Country'      THEN co.Region
    END                                                                          AS group_parent,
    t.row_type,
    t.step_order,
    t.step,
    t.step_group,
    t.group_side,
    t.loc                                                                        AS location_id,
    fl.OfficeName                                                                AS office_name,
    fl.City                                                                      AS city,
    fl.CountryName                                                               AS country_name,
    fl.Region                                                                    AS region,
    fl.SiteType                                                                  AS site_type,
    fl.OpenedDate                                                                AS opened_date,
    fl.Latitude                                                                  AS latitude,
    fl.Longitude                                                                 AS longitude,
    t.to_loc                                                                     AS to_location_id,
    tl.OfficeName                                                                AS to_office,
    tl.CountryName                                                               AS to_country,
    tl.Region                                                                    AS to_region,
    tl.Latitude                                                                  AS to_latitude,
    tl.Longitude                                                                 AS to_longitude,
    CASE WHEN t.row_type = 'Route' THEN
        CASE WHEN fl.CountryCode = tl.CountryCode THEN 'Within one country' ELSE 'Across a border' END
    END                                                                          AS flow_scope_label,
    CAST(t.headcount AS INT)                                                     AS headcount,
    CAST(ROUND(t.fte, 2) AS DECIMAL(19, 2))                                      AS fte,
    CAST(t.worker_count AS INT)                                                  AS worker_count
FROM (
    /* A. OFFICE rows: date pair x view x group x office x step */
    SELECT
        pg.from_date, pg.to_date, v.view_order, v.view_name, sd.group_id,
        CAST('Office' AS VARCHAR(6))  AS row_type,
        sd.step_order, sd.step, sd.step_group,
        CAST(NULL AS VARCHAR(4))      AS group_side,
        sd.loc,
        CAST(NULL AS VARCHAR(15))     AS to_loc,
        SUM(sd.hc)                    AS headcount,
        SUM(sd.fte)                   AS fte,
        SUM(sd.n)                     AS worker_count
    FROM (
        /* A1. everyone present at the From or the To month-end, pre-aggregated */
        SELECT
            g.from_date, g.to_date,
            CASE WHEN o.WorkerID IS NULL THEN 'Hire' WHEN c.WorkerID IS NULL THEN 'Exit' ELSE 'Continuing' END AS worker_class,
            CASE WHEN c.WorkerID IS NULL AND w.TerminationType = 'Voluntary' THEN 'Voluntary' ELSE 'Involuntary' END AS exit_type,
            o.DepartmentID AS o_dept, o.LocationID AS o_loc, o.CountryCode AS o_cty,
            c.DepartmentID AS c_dept, c.LocationID AS c_loc, c.CountryCode AS c_cty,
            COUNT(*)                                                   AS n,
            SUM(CAST(o.FTE AS DECIMAL(19, 4)))                         AS o_fte,
            SUM(CAST(c.FTE AS DECIMAL(19, 4)))                         AS c_fte,
            SUM(CASE WHEN o.FTE <> c.FTE THEN 1 ELSE 0 END)            AS fte_n
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
        WHERE o.WorkerID IS NOT NULL OR c.WorkerID IS NOT NULL
        GROUP BY g.from_date, g.to_date,
                 CASE WHEN o.WorkerID IS NULL THEN 'Hire' WHEN c.WorkerID IS NULL THEN 'Exit' ELSE 'Continuing' END,
                 CASE WHEN c.WorkerID IS NULL AND w.TerminationType = 'Voluntary' THEN 'Voluntary' ELSE 'Involuntary' END,
                 o.DepartmentID, o.LocationID, o.CountryCode, c.DepartmentID, c.LocationID, c.CountryCode
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
    /* A2. the six views: the group a person is in at each end of the pair */
    CROSS APPLY (VALUES
        (1, 'Company',      CAST('ORG-000' AS VARCHAR(15)),      CAST('ORG-000' AS VARCHAR(15))),
        (2, 'Function',     CAST(od.FunctionID AS VARCHAR(15)),  CAST(cd.FunctionID AS VARCHAR(15))),
        (3, 'Sub-function', CAST(od.LeaderOrgID AS VARCHAR(15)), CAST(cd.LeaderOrgID AS VARCHAR(15))),
        (4, 'Department',   CAST(pg.o_dept AS VARCHAR(15)),      CAST(pg.c_dept AS VARCHAR(15))),
        (5, 'Office',       CAST(pg.o_loc AS VARCHAR(15)),       CAST(pg.c_loc AS VARCHAR(15))),
        (6, 'Country',      CAST(pg.o_cty AS VARCHAR(15)),       CAST(pg.c_cty AS VARCHAR(15)))
    ) AS v (view_order, view_name, open_key, close_key)
    /* A3. the walk lines: each pre-aggregated row becomes the steps that apply */
    CROSS APPLY (VALUES
        ( 1, 'Opening',                'Balance',         v.open_key,  pg.o_loc,  pg.n,  pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class <> 'Hire' THEN 1 ELSE 0 END),
        ( 2, 'Hires',                  'Hires & exits',   v.close_key, pg.c_loc,  pg.n,  pg.c_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Hire' THEN 1 ELSE 0 END),
        ( 3, 'Voluntary Exits',        'Hires & exits',   v.open_key,  pg.o_loc, -pg.n, -pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Exit' AND pg.exit_type = 'Voluntary' THEN 1 ELSE 0 END),
        ( 4, 'Involuntary Exits',      'Hires & exits',   v.open_key,  pg.o_loc, -pg.n, -pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Exit' AND pg.exit_type = 'Involuntary' THEN 1 ELSE 0 END),
        ( 5, 'Transfers In',           'Transfers',       v.close_key, pg.c_loc,  pg.n,  pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.o_loc = pg.c_loc AND v.open_key <> v.close_key THEN 1 ELSE 0 END),
        ( 6, 'Transfers Out',          'Transfers',       v.open_key,  pg.o_loc, -pg.n, -pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.o_loc = pg.c_loc AND v.open_key <> v.close_key THEN 1 ELSE 0 END),
        ( 7, 'Office Moves In',        'Office moves',    v.close_key, pg.c_loc,  pg.n,  pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.o_loc <> pg.c_loc AND pg.o_cty = pg.c_cty THEN 1 ELSE 0 END),
        ( 8, 'Office Moves Out',       'Office moves',    v.open_key,  pg.o_loc, -pg.n, -pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.o_loc <> pg.c_loc AND pg.o_cty = pg.c_cty THEN 1 ELSE 0 END),
        ( 9, 'Cross-border Moves In',  'Office moves',    v.close_key, pg.c_loc,  pg.n,  pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.o_cty <> pg.c_cty THEN 1 ELSE 0 END),
        (10, 'Cross-border Moves Out', 'Office moves',    v.open_key,  pg.o_loc, -pg.n, -pg.o_fte,            pg.n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.o_cty <> pg.c_cty THEN 1 ELSE 0 END),
        (11, 'FTE Changes',            'FTE',             v.close_key, pg.c_loc,  0,     pg.c_fte - pg.o_fte, pg.fte_n,
            CASE WHEN pg.worker_class = 'Continuing' AND pg.fte_n > 0 THEN 1 ELSE 0 END),
        (12, 'Closing',                'Balance',         v.close_key, pg.c_loc,  pg.n,  pg.c_fte,            pg.n,
            CASE WHEN pg.worker_class <> 'Exit' THEN 1 ELSE 0 END)
    ) AS sd (step_order, step, step_group, group_id, loc, hc, fte, n, include_line)
    WHERE sd.include_line = 1
    GROUP BY pg.from_date, pg.to_date, v.view_order, v.view_name, sd.group_id,
             sd.step_order, sd.step, sd.step_group, sd.loc

    UNION ALL

    /* B. ROUTE rows: date pair x view x group x side x origin office x destination office */
    SELECT
        mv.from_date, mv.to_date, v.view_order, v.view_name, sd.group_id,
        CAST('Route' AS VARCHAR(6))   AS row_type,
        0                             AS step_order,
        CAST('Route' AS VARCHAR(25))  AS step,
        CAST('Route' AS VARCHAR(15))  AS step_group,
        sd.group_side,
        mv.o_loc,
        mv.c_loc,
        SUM(mv.n)                     AS headcount,
        CAST(NULL AS DECIMAL(19, 4))  AS fte,
        SUM(mv.n)                     AS worker_count
    FROM (
        /* B1. movers: present at both month-ends, office differs, pre-aggregated */
        SELECT
            g.from_date, g.to_date,
            o.DepartmentID AS o_dept, o.LocationID AS o_loc, o.CountryCode AS o_cty,
            c.DepartmentID AS c_dept, c.LocationID AS c_loc, c.CountryCode AS c_cty,
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
        JOIN dw.WorkerMonthEndSnapshot AS o ON o.MonthEndDate = g.from_date AND o.IsExecutiveOfficer = 0
        JOIN dw.WorkerMonthEndSnapshot AS c ON c.MonthEndDate = g.to_date AND c.WorkerID = o.WorkerID
        WHERE o.LocationID <> c.LocationID
        GROUP BY g.from_date, g.to_date, o.DepartmentID, o.LocationID, o.CountryCode,
                 c.DepartmentID, c.LocationID, c.CountryCode
    ) AS mv
    LEFT JOIN (
        SELECT d.DepartmentID,
               CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
               d.ParentOrgUnitID AS LeaderOrgID
        FROM dw.DimDepartment AS d
        JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
    ) AS od ON od.DepartmentID = mv.o_dept
    LEFT JOIN (
        SELECT d.DepartmentID,
               CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
               d.ParentOrgUnitID AS LeaderOrgID
        FROM dw.DimDepartment AS d
        JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
    ) AS cd ON cd.DepartmentID = mv.c_dept
    CROSS APPLY (VALUES
        (1, 'Company',      CAST('ORG-000' AS VARCHAR(15)),      CAST('ORG-000' AS VARCHAR(15))),
        (2, 'Function',     CAST(od.FunctionID AS VARCHAR(15)),  CAST(cd.FunctionID AS VARCHAR(15))),
        (3, 'Sub-function', CAST(od.LeaderOrgID AS VARCHAR(15)), CAST(cd.LeaderOrgID AS VARCHAR(15))),
        (4, 'Department',   CAST(mv.o_dept AS VARCHAR(15)),      CAST(mv.c_dept AS VARCHAR(15))),
        (5, 'Office',       CAST(mv.o_loc AS VARCHAR(15)),       CAST(mv.c_loc AS VARCHAR(15))),
        (6, 'Country',      CAST(mv.o_cty AS VARCHAR(15)),       CAST(mv.c_cty AS VARCHAR(15)))
    ) AS v (view_order, view_name, open_key, close_key)
    CROSS APPLY (VALUES
        (CAST('Both' AS VARCHAR(4)), v.open_key,  CASE WHEN v.open_key =  v.close_key THEN 1 ELSE 0 END),
        (CAST('From' AS VARCHAR(4)), v.open_key,  CASE WHEN v.open_key <> v.close_key THEN 1 ELSE 0 END),
        (CAST('To'   AS VARCHAR(4)), v.close_key, CASE WHEN v.open_key <> v.close_key THEN 1 ELSE 0 END)
    ) AS sd (group_side, group_id, include_line)
    WHERE sd.include_line = 1
    GROUP BY mv.from_date, mv.to_date, v.view_order, v.view_name, sd.group_id, sd.group_side, mv.o_loc, mv.c_loc
) AS t
JOIN dw.MonthEndCalendar AS cf ON cf.MonthEndDate = t.from_date
JOIN dw.MonthEndCalendar AS ct ON ct.MonthEndDate = t.to_date
JOIN dw.DimLocation      AS fl ON fl.LocationID   = t.loc
LEFT JOIN dw.DimLocation AS tl ON tl.LocationID   = t.to_loc
LEFT JOIN dw.DimOrgUnit  AS ou ON ou.OrgUnitID    = t.group_id
LEFT JOIN dw.DimLocation AS lo ON t.view_name = 'Office'  AND lo.LocationID  = t.group_id
LEFT JOIN dw.DimCountry  AS co ON t.view_name = 'Country' AND co.CountryCode = t.group_id
