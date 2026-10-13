/*
  09_validate_region_walk_and_career_moves.sql
  Runs the two newer Tableau Custom SQL queries of the compensation walk dashboard
  inside SQL Server, exactly as Tableau would (each file is included unchanged with
  sqlcmd's :r), with the walk beside them, and checks that they tie to it.
  Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/09_validate_region_walk_and_career_moves.sql

  Every "expected" value comes from the DuckDB pipeline (data/marts/mart_region_walk.csv,
  mart_career_moves.csv). The walk takes about as long as in 06.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
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
DROP TABLE IF EXISTS #career;
SELECT *
INTO #career
FROM (
:r /repo/tableau/custom_sql_career_moves.sql
) AS c;
DECLARE @n INT = (SELECT COUNT(*) FROM #career);
PRINT CONCAT('Career moves Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #walk;
SELECT *
INTO #walk
FROM (
:r /repo/tableau/custom_sql_compensation_walk.sql
) AS w;
DECLARE @n INT = (SELECT COUNT(*) FROM #walk);
PRINT CONCAT('Compensation walk Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Shape';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'region walk rows'          AS check_name, (SELECT COUNT(*) FROM #regions) AS actual, 26520 AS expected
    UNION ALL SELECT 'region walk date pairs',   (SELECT COUNT(*) FROM (SELECT DISTINCT from_month_end, to_month_end FROM #regions) AS p), 88
    UNION ALL SELECT 'career moves rows',        (SELECT COUNT(*) FROM #career), 34532
    UNION ALL SELECT 'career moves date pairs',  (SELECT COUNT(*) FROM (SELECT DISTINCT from_month_end, to_month_end FROM #career) AS p), 88
    UNION ALL SELECT 'views (both)',             (SELECT COUNT(DISTINCT view_name) FROM #regions) + (SELECT COUNT(DISTINCT view_name) FROM #career), 12
) AS c;
GO

PRINT '2. Ties (every check expects 0)';
WITH r AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(opening_headcount) AS opening, SUM(hires) AS hires, SUM(exits) AS exits,
           SUM(transfers_in) AS transfers_in, SUM(transfers_out) AS transfers_out, SUM(closing_headcount) AS closing,
           SUM(region_moves_in) - SUM(region_moves_out) AS net_region_moves
    FROM #regions
    GROUP BY from_month_end, to_month_end, view_name, group_id
), w AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN step = 'Opening'       THEN headcount ELSE 0 END)  AS opening,
           SUM(CASE WHEN step = 'Hires'         THEN headcount ELSE 0 END)  AS hires,
           SUM(CASE WHEN step = 'Exits'         THEN -headcount ELSE 0 END) AS exits,
           SUM(CASE WHEN step = 'Transfers In'  THEN headcount ELSE 0 END)  AS transfers_in,
           SUM(CASE WHEN step = 'Transfers Out' THEN -headcount ELSE 0 END) AS transfers_out,
           SUM(CASE WHEN step = 'Closing'       THEN headcount ELSE 0 END)  AS closing
    FROM #walk
    GROUP BY from_month_end, to_month_end, view_name, group_id
)
SELECT check_name, failures, CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
    SELECT 'region walk rows that do not close' AS check_name, COUNT(*) AS failures
    FROM #regions
    WHERE opening_headcount + hires - exits + transfers_in - transfers_out + region_moves_in - region_moves_out
          <> closing_headcount
    UNION ALL
    SELECT 'groups whose region walk differs from the walk', COUNT(*)
    FROM r
    FULL OUTER JOIN w
      ON w.from_month_end = r.from_month_end AND w.to_month_end = r.to_month_end
     AND w.view_name = r.view_name AND w.group_id = r.group_id
    WHERE ISNULL(r.opening, -1) <> ISNULL(w.opening, -1) OR ISNULL(r.hires, -1) <> ISNULL(w.hires, -1)
       OR ISNULL(r.exits, -1) <> ISNULL(w.exits, -1) OR ISNULL(r.transfers_in, -1) <> ISNULL(w.transfers_in, -1)
       OR ISNULL(r.transfers_out, -1) <> ISNULL(w.transfers_out, -1) OR ISNULL(r.closing, -1) <> ISNULL(w.closing, -1)
       OR ISNULL(r.net_region_moves, 0) <> 0
    UNION ALL
    SELECT 'career groups with fewer moves than the walk''s people', COUNT(*)
    FROM (
        SELECT from_month_end, to_month_end, view_name, group_id, move_type, SUM(moves) AS moves
        FROM #career
        GROUP BY from_month_end, to_month_end, view_name, group_id, move_type
    ) AS c
    LEFT JOIN (
        SELECT from_month_end, to_month_end, view_name, group_id,
               CASE step WHEN 'Promotions' THEN 'Promotion' ELSE 'Demotion' END AS move_type,
               SUM(worker_count) AS people
        FROM #walk
        WHERE step IN ('Promotions', 'Demotions')
        GROUP BY from_month_end, to_month_end, view_name, group_id, step
    ) AS wp
      ON wp.from_month_end = c.from_month_end AND wp.to_month_end = c.to_month_end
     AND wp.view_name = c.view_name AND wp.group_id = c.group_id AND wp.move_type = c.move_type
    WHERE wp.people IS NULL OR c.moves < wp.people
) AS checks;
GO

PRINT '3. FY26 (30 Jun 2025 to 30 Jun 2026), company';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'promotions (moves)' AS check_name,
                     (SELECT SUM(moves) FROM #career WHERE view_name = 'Company' AND move_type = 'Promotion' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30') AS actual, 1850 AS expected
    UNION ALL SELECT 'demotions (moves)',
                     (SELECT SUM(moves) FROM #career WHERE view_name = 'Company' AND move_type = 'Demotion' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 148
    UNION ALL SELECT 'promotions into Director and above',
                     (SELECT SUM(moves) FROM #career WHERE view_name = 'Company' AND into_director = 1 AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 16
    UNION ALL SELECT 'North America opening',
                     (SELECT opening_headcount FROM #regions WHERE view_name = 'Company' AND region = 'North America' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 9909
    UNION ALL SELECT 'North America closing',
                     (SELECT closing_headcount FROM #regions WHERE view_name = 'Company' AND region = 'North America' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 10426
    UNION ALL SELECT 'Asia Pacific closing',
                     (SELECT closing_headcount FROM #regions WHERE view_name = 'Company' AND region = 'Asia Pacific' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 9005
    UNION ALL SELECT 'Technology, North America closing',
                     (SELECT closing_headcount FROM #regions WHERE view_name = 'Function' AND group_name = 'Technology' AND region = 'North America' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 3431
) AS c;
GO

DROP TABLE IF EXISTS #regions;
DROP TABLE IF EXISTS #career;
DROP TABLE IF EXISTS #walk;
GO
