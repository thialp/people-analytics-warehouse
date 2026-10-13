/*
  11_validate_workforce_footprint.sql
  Runs the Workforce Footprint Custom SQL inside SQL Server exactly as Tableau
  would (the file is included unchanged with sqlcmd's :r), with the region walk
  and office moves queries beside it, and checks that it closes and ties to them.
  Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/11_validate_workforce_footprint.sql

  Expected values were produced by running the same T-SQL in DuckDB
  (sqlserver/check_tsql_in_duckdb.py translation) on release 2 data.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #fp;
SELECT *
INTO #fp
FROM (
:r /repo/tableau/custom_sql_workforce_footprint.sql
) AS f;
DECLARE @n INT = (SELECT COUNT(*) FROM #fp);
PRINT CONCAT('Workforce footprint Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #regions;
SELECT *
INTO #regions
FROM (
:r /repo/tableau/custom_sql_region_walk.sql
) AS r;
DECLARE @n INT = (SELECT COUNT(*) FROM #regions);
PRINT CONCAT('Region walk Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #moves;
SELECT *
INTO #moves
FROM (
:r /repo/tableau/custom_sql_office_moves.sql
) AS m;
DECLARE @n INT = (SELECT COUNT(*) FROM #moves);
PRINT CONCAT('Office moves Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Shape';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'office rows'          AS check_name, (SELECT COUNT(*) FROM #fp WHERE row_type = 'Office') AS actual, 576679 AS expected
    UNION ALL SELECT 'route rows',          (SELECT COUNT(*) FROM #fp WHERE row_type = 'Route'), 89593
    UNION ALL SELECT 'date pairs',          (SELECT COUNT(*) FROM (SELECT DISTINCT from_month_end, to_month_end FROM #fp) AS p), 88
    UNION ALL SELECT 'views',               (SELECT COUNT(DISTINCT view_name) FROM #fp), 6
    UNION ALL SELECT 'groups',              (SELECT COUNT(*) FROM (SELECT DISTINCT view_name, group_name FROM #fp) AS g), 107
    UNION ALL SELECT 'rows without a map point',  (SELECT COUNT(*) FROM #fp WHERE latitude IS NULL OR longitude IS NULL), 0
    UNION ALL SELECT 'rows without a group name', (SELECT COUNT(*) FROM #fp WHERE group_name IS NULL), 0
) AS c;
GO

PRINT '2. Closes and ties (every check expects 0)';
SELECT check_name, actual, 0 AS expected,
       CASE WHEN actual = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
    SELECT 'offices whose headcount walk does not close' AS check_name, COUNT(*) AS actual
    FROM (
        SELECT from_month_end, to_month_end, view_name, group_id, location_id
        FROM #fp WHERE row_type = 'Office'
        GROUP BY from_month_end, to_month_end, view_name, group_id, location_id
        HAVING SUM(CASE WHEN step <> 'Closing' THEN headcount ELSE 0 END)
             <> SUM(CASE WHEN step =  'Closing' THEN headcount ELSE 0 END)
    ) AS x
    UNION ALL
    SELECT 'offices whose FTE walk does not close', COUNT(*)
    FROM (
        SELECT from_month_end, to_month_end, view_name, group_id, location_id
        FROM #fp WHERE row_type = 'Office'
        GROUP BY from_month_end, to_month_end, view_name, group_id, location_id
        HAVING ABS(SUM(CASE WHEN step <> 'Closing' THEN fte ELSE 0 END)
                 - SUM(CASE WHEN step =  'Closing' THEN fte ELSE 0 END)) > 0.05
    ) AS x
    UNION ALL
    SELECT 'views whose groups do not add up to the company', COUNT(*)
    FROM (
        SELECT a.from_month_end
        FROM (
            SELECT from_month_end, to_month_end, view_name,
                   SUM(CASE WHEN step = 'Opening' THEN headcount ELSE 0 END) AS o,
                   SUM(CASE WHEN step = 'Closing' THEN headcount ELSE 0 END) AS c
            FROM #fp WHERE row_type = 'Office'
            GROUP BY from_month_end, to_month_end, view_name
        ) AS a
        JOIN (
            SELECT from_month_end, to_month_end,
                   SUM(CASE WHEN step = 'Opening' THEN headcount ELSE 0 END) AS o,
                   SUM(CASE WHEN step = 'Closing' THEN headcount ELSE 0 END) AS c
            FROM #fp WHERE row_type = 'Office' AND view_name = 'Company'
            GROUP BY from_month_end, to_month_end
        ) AS b ON b.from_month_end = a.from_month_end AND b.to_month_end = a.to_month_end
        WHERE a.o <> b.o OR a.c <> b.c
    ) AS x
    UNION ALL
    SELECT 'company pairs where routes differ from office moves in', COUNT(*)
    FROM (
        SELECT from_month_end, to_month_end
        FROM #fp WHERE view_name = 'Company'
        GROUP BY from_month_end, to_month_end
        HAVING SUM(CASE WHEN row_type = 'Route' THEN headcount ELSE 0 END)
            <> SUM(CASE WHEN step IN ('Office Moves In', 'Cross-border Moves In') THEN headcount ELSE 0 END)
    ) AS x
    UNION ALL
    SELECT 'region lines that differ from the region walk', COUNT(*)
    FROM (
        SELECT r.from_month_end
        FROM (
            SELECT from_month_end, to_month_end, view_name, group_name, region,
                   SUM(opening_headcount) AS o, SUM(hires) AS h, SUM(exits) AS e, SUM(closing_headcount) AS c
            FROM #regions
            GROUP BY from_month_end, to_month_end, view_name, group_name, region
        ) AS r
        FULL JOIN (
            SELECT from_month_end, to_month_end, view_name, group_name, region,
                   SUM(CASE WHEN step = 'Opening' THEN headcount ELSE 0 END) AS o,
                   SUM(CASE WHEN step = 'Hires' THEN headcount ELSE 0 END) AS h,
                   -SUM(CASE WHEN step IN ('Voluntary Exits', 'Involuntary Exits') THEN headcount ELSE 0 END) AS e,
                   SUM(CASE WHEN step = 'Closing' THEN headcount ELSE 0 END) AS c
            FROM #fp WHERE row_type = 'Office'
            GROUP BY from_month_end, to_month_end, view_name, group_name, region
        ) AS f
          ON f.from_month_end = r.from_month_end AND f.to_month_end = r.to_month_end
         AND f.view_name = r.view_name AND f.group_name = r.group_name AND f.region = r.region
        WHERE r.region IS NULL OR f.region IS NULL OR r.o <> f.o OR r.h <> f.h OR r.e <> f.e OR r.c <> f.c
    ) AS x
    UNION ALL
    SELECT 'route lines that differ from office moves', COUNT(*)
    FROM (
        SELECT m.from_month_end
        FROM (
            SELECT from_month_end, to_month_end, view_name, group_name, group_side,
                   from_location_id, to_location_id, SUM(workers) AS n
            FROM #moves
            GROUP BY from_month_end, to_month_end, view_name, group_name, group_side, from_location_id, to_location_id
        ) AS m
        FULL JOIN (
            SELECT from_month_end, to_month_end, view_name, group_name, group_side,
                   location_id, to_location_id, SUM(headcount) AS n
            FROM #fp WHERE row_type = 'Route'
            GROUP BY from_month_end, to_month_end, view_name, group_name, group_side, location_id, to_location_id
        ) AS f
          ON f.from_month_end = m.from_month_end AND f.to_month_end = m.to_month_end
         AND f.view_name = m.view_name AND f.group_name = m.group_name AND f.group_side = m.group_side
         AND f.location_id = m.from_location_id AND f.to_location_id = m.to_location_id
        WHERE m.n IS NULL OR f.n IS NULL OR m.n <> f.n
    ) AS x
) AS c;
GO

PRINT '3. FY26, Company (Jun 30, 2025 to Jun 30, 2026)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'opening headcount' AS check_name, SUM(CASE WHEN step = 'Opening' THEN headcount ELSE 0 END) AS actual, 28438 AS expected FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'hires',                SUM(CASE WHEN step = 'Hires' THEN headcount ELSE 0 END), 4790 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'voluntary exits',      -SUM(CASE WHEN step = 'Voluntary Exits' THEN headcount ELSE 0 END), 2588 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'involuntary exits',    -SUM(CASE WHEN step = 'Involuntary Exits' THEN headcount ELSE 0 END), 635 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'office moves (one country)', SUM(CASE WHEN step = 'Office Moves In' THEN headcount ELSE 0 END), 600 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'cross-border moves',   SUM(CASE WHEN step = 'Cross-border Moves In' THEN headcount ELSE 0 END), 125 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'closing headcount',    SUM(CASE WHEN step = 'Closing' THEN headcount ELSE 0 END), 30005 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'closing FTE x 10',     CAST(ROUND(10 * SUM(CASE WHEN step = 'Closing' THEN fte ELSE 0 END), 0) AS INT), 293545 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'offices with people',  COUNT(DISTINCT CASE WHEN step = 'Closing' THEN location_id END), 35 FROM #fp WHERE row_type = 'Office' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
    UNION ALL SELECT 'route lines',          COUNT(*), 155 FROM #fp WHERE row_type = 'Route' AND view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
) AS c;
GO
