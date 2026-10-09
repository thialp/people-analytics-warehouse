/*
  07_validate_office_moves.sql
  Runs the Tableau Custom SQL for office moves, exactly as Tableau would (the file is
  included as-is with sqlcmd's :r), times it, and checks the result. It also runs the
  compensation walk Custom SQL so the moves can be tied to the walk's transfers.
  Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/07_validate_office_moves.sql

  Every "expected" value comes from the DuckDB pipeline (marts.mart_office_moves and
  data/marts/mart_compensation_walk.csv). The row count depends on the GRID markers in
  the Custom SQL: 260,464 rows for the default grid (184 date pairs).
*/
SET NOCOUNT ON;
USE ArcadiaHR;
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
              SELECT 'rows'       AS check_name, (SELECT COUNT(*) FROM #moves) AS actual, 260464 AS expected
    UNION ALL SELECT 'date pairs', (SELECT COUNT(*) FROM (SELECT DISTINCT from_month_end, to_month_end FROM #moves) AS p), 184
    UNION ALL SELECT 'views',      (SELECT COUNT(DISTINCT view_name) FROM #moves), 6
    UNION ALL SELECT 'rows without a group name', (SELECT COUNT(*) FROM #moves WHERE group_name IS NULL), 0
    UNION ALL SELECT 'flows from an office to itself', (SELECT COUNT(*) FROM #moves WHERE from_location_id = to_location_id), 0
) AS c;
GO

PRINT '2. FY26 (30 Jun 2025 to 30 Jun 2026): people who changed office';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'Company, all moves' AS check_name,
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30') AS actual, 345 AS expected
    UNION ALL SELECT 'Company, within one country',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Company' AND flow_scope = 'Domestic' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 227
    UNION ALL SELECT 'Company, across a border',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Company' AND flow_scope = 'International' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 118
    UNION ALL SELECT 'Office view, joined an office (To)',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Office' AND group_side = 'To' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 345
    UNION ALL SELECT 'Office view, left an office (From)',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Office' AND group_side = 'From' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 345
    UNION ALL SELECT 'Country view, inside one country (Both)',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Country' AND group_side = 'Both' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 227
    UNION ALL SELECT 'Country view, across a border (To)',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Country' AND group_side = 'To' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'), 118
    UNION ALL SELECT 'Company, 30 Jun 2022 to 30 Jun 2026',
                     (SELECT SUM(workers) FROM #moves WHERE view_name = 'Company' AND from_month_end = '2022-06-30' AND to_month_end = '2026-06-30'), 789
) AS c;
GO

PRINT '3. Office and Country groups whose moves differ from the walk''s Transfers In / Out (expected 0)';
WITH m AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN group_side = 'To'   THEN workers ELSE 0 END) AS moves_in,
           SUM(CASE WHEN group_side = 'From' THEN workers ELSE 0 END) AS moves_out
    FROM #moves
    WHERE view_name IN ('Office', 'Country')
    GROUP BY from_month_end, to_month_end, view_name, group_id
), w AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN step = 'Transfers In'  THEN headcount ELSE 0 END)  AS walk_in,
           SUM(CASE WHEN step = 'Transfers Out' THEN -headcount ELSE 0 END) AS walk_out
    FROM #walk
    WHERE view_name IN ('Office', 'Country') AND step IN ('Transfers In', 'Transfers Out')
    GROUP BY from_month_end, to_month_end, view_name, group_id
)
SELECT COUNT(*) AS groups_not_tying
FROM m
FULL OUTER JOIN w
  ON w.from_month_end = m.from_month_end AND w.to_month_end = m.to_month_end
 AND w.view_name = m.view_name AND w.group_id = m.group_id
WHERE ISNULL(m.moves_in, 0)  <> ISNULL(w.walk_in, 0)
   OR ISNULL(m.moves_out, 0) <> ISNULL(w.walk_out, 0);
GO

PRINT '4. Dates, groups and names match the walk, so one set of dashboard filters drives both (expected 0)';
SELECT COUNT(*) AS move_groups_missing_from_walk
FROM (SELECT DISTINCT from_month_end, to_month_end, view_name, group_id, group_name FROM #moves) AS m
WHERE NOT EXISTS (
    SELECT 1 FROM #walk AS w
    WHERE w.from_month_end = m.from_month_end AND w.to_month_end = m.to_month_end
      AND w.view_name = m.view_name AND w.group_id = m.group_id AND w.group_name = m.group_name
);
GO

DROP TABLE IF EXISTS #moves;
DROP TABLE IF EXISTS #walk;
GO
