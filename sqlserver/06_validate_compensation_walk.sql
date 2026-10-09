/*
  06_validate_compensation_walk.sql
  Runs the Tableau Custom SQL for the compensation walk, exactly as Tableau would
  (the file is included as-is with sqlcmd's :r), times it, and checks the result.
  Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/06_validate_compensation_walk.sql

  Every "expected" value comes from the DuckDB pipeline (data/marts/mart_compensation_walk.csv).
  The row count depends on the GRID markers in the Custom SQL: 271,219 rows for the
  default grid (quarter-end pairs plus month over month, 184 pairs).
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #walk;
SELECT *
INTO #walk
FROM (
:r /repo/tableau/custom_sql_compensation_walk.sql
) AS w;
PRINT CONCAT('Custom SQL returned ', (SELECT COUNT(*) FROM #walk), ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Shape';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'rows'       AS check_name, (SELECT COUNT(*) FROM #walk) AS actual, 271219 AS expected
    UNION ALL SELECT 'date pairs', (SELECT COUNT(*) FROM (SELECT DISTINCT from_month_end, to_month_end FROM #walk) AS p), 184
    UNION ALL SELECT 'views',      (SELECT COUNT(DISTINCT view_name) FROM #walk), 6
) AS c;
GO

PRINT '2. Groups whose walk does not close: Opening + steps <> Closing (expected 0)';
SELECT COUNT(*) AS groups_not_closing
FROM (
    SELECT from_month_end, to_month_end, view_name, group_id, COUNT(*) AS lines,
           SUM(CASE WHEN step = 'Closing' THEN -headcount           ELSE headcount           END) AS d_hc,
           SUM(CASE WHEN step = 'Closing' THEN -fte                 ELSE fte                 END) AS d_fte,
           SUM(CASE WHEN step = 'Closing' THEN -base_usd_nominal    ELSE base_usd_nominal    END) AS d_bn,
           SUM(CASE WHEN step = 'Closing' THEN -base_usd_constant   ELSE base_usd_constant   END) AS d_bc,
           SUM(CASE WHEN step = 'Closing' THEN -loaded_usd_nominal  ELSE loaded_usd_nominal  END) AS d_ln,
           SUM(CASE WHEN step = 'Closing' THEN -loaded_usd_constant ELSE loaded_usd_constant END) AS d_lc,
           SUM(CASE WHEN step = 'Closing' THEN -avg_loaded_usd_constant ELSE avg_loaded_usd_constant END) AS d_avg
    FROM #walk
    GROUP BY from_month_end, to_month_end, view_name, group_id
) AS g
WHERE d_hc <> 0 OR d_fte <> 0
   OR ABS(d_bn) > 0.005 * lines OR ABS(d_bc) > 0.005 * lines
   OR ABS(d_ln) > 0.005 * lines OR ABS(d_lc) > 0.005 * lines
   OR ABS(d_avg) > 0.0001 * lines;
GO

PRINT '3. Company, 30 Jun 2022 to 30 Jun 2026';
SELECT step, headcount, loaded_usd_nominal, loaded_usd_constant
FROM #walk
WHERE view_name = 'Company' AND from_month_end = '2022-06-30' AND to_month_end = '2026-06-30'
  AND step IN ('Opening', 'Closing');
/*
  Expected:
    Opening   25005   2577787184.61   2613645368.19
    Closing   30015   3195503264.60   3195503264.60
  (The cost snapshot control totals in 05 read .81 / .50 / .83: they add up values
   already rounded to the cent per group. The walk sums people first, then rounds.)
*/
GO

PRINT '4. FY26 company walk, loaded cost at constant FX (30 Jun 2025 to 30 Jun 2026)';
SELECT step_order, step, SUM(worker_count) AS people, SUM(headcount) AS headcount,
       SUM(loaded_usd_constant) AS loaded_usd_constant, SUM(avg_loaded_usd_constant) AS avg_per_fte
FROM #walk
WHERE view_name = 'Company' AND from_month_end = '2025-06-30' AND to_month_end = '2026-06-30'
GROUP BY step_order, step
ORDER BY step_order;
/*
  Expected:
     1  Opening                             28436   28436   3000123793.56   107553.68
     2  Hires                                4766    4766    411260583.95    -3269.63
     3  Exits                                3187   -3187   -331824382.85      127.33
     6  Promotions                           1899       0     19146841.89      651.35
     7  Demotions                              95       0      -580262.30      -19.74
     8  Tenure Increases                    24218       0     97731983.15     3324.70
     9  Market Adjustments                    307       0      1568126.87       53.35
    10  Relocation Adjustments                216       0       -87552.47       -2.98
    11  International Transfer Adjustments    118       0       602450.19       20.49
    12  FTE Changes                           377       0    -10639037.56      -11.04
    13  Fringe Rate Changes                 10892       0      8200720.18      278.98
    14  FX Translation                      17211       0            0.00        0.00
    15  Closing                             30015   30015   3195503264.60   108706.49
*/
GO

DROP TABLE IF EXISTS #walk;
GO
