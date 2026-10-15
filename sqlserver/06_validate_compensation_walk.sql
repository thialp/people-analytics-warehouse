/*
  06_validate_compensation_walk.sql
  Runs the Tableau Custom SQL for the compensation walk, exactly as Tableau would
  (the file is included as-is with sqlcmd's :r), times it, and checks the result.
  Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/06_validate_compensation_walk.sql

  Every "expected" value comes from the DuckDB pipeline (data/marts/mart_compensation_walk.csv).
  The row count depends on the GRID markers in the Custom SQL: 115,544 rows for the
  default grid (the four offered period types, ending after the first year of history:
  88 pairs).
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
DECLARE @n INT = (SELECT COUNT(*) FROM #walk);
PRINT CONCAT('Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Shape';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'rows'       AS check_name, (SELECT COUNT(*) FROM #walk) AS actual, 108918 AS expected
    UNION ALL SELECT 'date pairs', (SELECT COUNT(*) FROM (SELECT DISTINCT from_month_end, to_month_end FROM #walk) AS p), 88
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

PRINT '3. Company, FY23 (30 Jun 2022 to 30 Jun 2023)';
SELECT step, headcount, loaded_usd_nominal, loaded_usd_constant
FROM #walk
WHERE view_name = 'Company' AND from_month_end = '2022-06-30' AND to_month_end = '2023-06-30'
  AND step IN ('Opening', 'Closing');
/*
  Expected:
    Opening   25052   2482526955.47   2519944448.29
    Closing   26932   2761818121.64   2771129945.16
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
     1  Opening                             28438   28438   3129964045.86   110062.73
     2  Hires                                4790    4790    491177210.36    -1200.58
     3  Exits                                3223   -3223   -348616593.73      203.82
     6  Promotions                           1824       0     21649191.69      721.52
     7  Demotions                             148       0      -804811.47      -26.82
     8  Tenure Increases                    25189       0    108071152.36     3601.77
     9  Market Adjustments                    287       0      1555253.85       51.83
    10  Same-Country Transfer Adjustments     583       0       193227.69        6.44
    11  International Transfer Adjustments    125       0     -1220144.21      -40.66
    13  Fringe Rate Changes                 11312       0      8514217.27      283.76
    14  FX Translation                      17038       0            0.00        0.00
    15  Closing                             30005   30005   3410482749.65   113663.81
  (Step 12, FTE Changes, no longer exists: every employee is 1.0 FTE since release 3.)
*/
GO

DROP TABLE IF EXISTS #walk;
GO
