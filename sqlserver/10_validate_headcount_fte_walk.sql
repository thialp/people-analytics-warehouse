/*
  10_validate_headcount_fte_walk.sql
  Runs Dashboard #1's Tableau Custom SQL (tableau/custom_sql_headcount_fte_walk.sql) inside
  SQL Server, exactly as Tableau would (the file is included unchanged with sqlcmd's :r),
  and checks it against the DuckDB pipeline's CSVs, which the dashboard used before.
  Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/10_validate_headcount_fte_walk.sql

  Every "expected" value comes from data/marts/mart_headcount_fte_walk.csv and
  docs/projects/headcount-fte-walk/expected_values.md. Arcadia Systems is fictional and all
  data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #hc;
SELECT *
INTO #hc
FROM (
:r /repo/tableau/custom_sql_headcount_fte_walk.sql
) AS h;
DECLARE @n INT = (SELECT COUNT(*) FROM #hc);
PRINT CONCAT('Headcount & FTE walk Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Shape (the same rows as mart_headcount_fte_walk.csv, no row repeated by the dimension joins)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'rows'       AS check_name, (SELECT COUNT(*) FROM #hc) AS actual, 597097 AS expected
    UNION ALL SELECT 'distinct keys (month x worker type x slice x category x reason)',
                     (SELECT COUNT(*) FROM (SELECT DISTINCT month_end_date, worker_type, department_id, country_code,
                                                   job_family_code, grade, movement_category, movement_reason FROM #hc) AS k), 597097
    UNION ALL SELECT 'month-ends',  (SELECT COUNT(DISTINCT month_end_date) FROM #hc), 60
    UNION ALL SELECT 'worker types', (SELECT COUNT(DISTINCT worker_type) FROM #hc), 2
    UNION ALL SELECT 'functions',   (SELECT COUNT(DISTINCT function_name) FROM #hc), 9
    UNION ALL SELECT 'rows without a name from a dimension',
                     (SELECT COUNT(*) FROM #hc WHERE function_name IS NULL OR country_name IS NULL OR fiscal_year IS NULL
                                                  OR (worker_type = 'Employee' AND (job_family IS NULL OR grade_level IS NULL))), 0
    UNION ALL SELECT 'contingent rows with a job family or grade (they have none)',
                     (SELECT COUNT(*) FROM #hc WHERE worker_type = 'Contingent'
                                                 AND (job_family_code IS NOT NULL OR grade IS NOT NULL)), 0
) AS c;
GO

PRINT '2. Every slice and month closes: Opening + movements = Closing, in headcount and FTE (expected 0)';
SELECT 'slice-months that do not close' AS check_name, COUNT(*) AS failures,
       CASE WHEN COUNT(*) = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
    SELECT month_end_date, worker_type, department_id, country_code, job_family_code, grade,
           SUM(CASE WHEN movement_category = 'Closing' THEN 0 ELSE headcount END) AS hc_walk,
           SUM(CASE WHEN movement_category = 'Closing' THEN headcount ELSE 0 END) AS hc_close,
           SUM(CASE WHEN movement_category = 'Closing' THEN 0 ELSE fte END)       AS fte_walk,
           SUM(CASE WHEN movement_category = 'Closing' THEN fte ELSE 0 END)       AS fte_close
    FROM #hc
    GROUP BY month_end_date, worker_type, department_id, country_code, job_family_code, grade
) AS s
WHERE hc_walk <> hc_close OR ABS(fte_walk - fte_close) > 0.005;
GO

PRINT '3. FY26 (From Jul 2025, To Jun 2026), employees';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'opening (Jun 2025)' AS check_name,
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Opening' AND month_end_date = '2025-07-31') AS actual, 28447 AS expected
    UNION ALL SELECT 'hires (not counting conversions)',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Hires' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 4965
    UNION ALL SELECT 'conversions in',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Conversions' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 270
    UNION ALL SELECT 'voluntary leavers',
                     (SELECT -SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Voluntary Terminations' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 2942
    UNION ALL SELECT 'involuntary leavers',
                     (SELECT -SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Involuntary Terminations' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 726
    UNION ALL SELECT 'internal moves',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Internal Moves In' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 3633
    UNION ALL SELECT 'promotions',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Internal Moves In' AND movement_reason = 'Promotion' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 2015
    UNION ALL SELECT 'closing (Jun 2026)',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Closing' AND month_end_date = '2026-06-30'), 30014
    UNION ALL SELECT 'closing FTE x 10',
                     (SELECT CAST(ROUND(SUM(fte) * 10, 0) AS INT) FROM #hc WHERE worker_type = 'Employee' AND movement_category = 'Closing' AND month_end_date = '2026-06-30'), 300140
    UNION ALL SELECT 'lines where FTE differs from headcount (every employee is 1.0 FTE, a contingent worker counts 1.0)',
                     (SELECT COUNT(*) FROM #hc WHERE fte <> headcount), 0
) AS c;
GO

PRINT '4. FY26, contingent workers (Bridgeway, as held at each month-end)';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'opening (Jun 2025)' AS check_name,
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Contingent' AND movement_category = 'Opening' AND month_end_date = '2025-07-31') AS actual, 10707 AS expected
    UNION ALL SELECT 'starts',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Contingent' AND movement_category = 'Starts' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 7033
    UNION ALL SELECT 'ends',
                     (SELECT -SUM(headcount) FROM #hc WHERE worker_type = 'Contingent' AND movement_category = 'Ends' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 5529
    UNION ALL SELECT 'conversions out (= conversions into Employee)',
                     (SELECT -SUM(headcount) FROM #hc WHERE worker_type = 'Contingent' AND movement_category = 'Conversions' AND month_end_date BETWEEN '2025-07-31' AND '2026-06-30'), 270
    UNION ALL SELECT 'closing (Jun 2026)',
                     (SELECT SUM(headcount) FROM #hc WHERE worker_type = 'Contingent' AND movement_category = 'Closing' AND month_end_date = '2026-06-30'), 11941
    UNION ALL SELECT 'total workforce closing (Jun 2026)',
                     (SELECT SUM(headcount) FROM #hc WHERE movement_category = 'Closing' AND month_end_date = '2026-06-30'), 41955
    UNION ALL SELECT 'months where conversions do not net to zero across worker types',
                     (SELECT COUNT(*) FROM (SELECT month_end_date FROM #hc WHERE movement_category = 'Conversions'
                                            GROUP BY month_end_date HAVING SUM(headcount) <> 0) AS x), 0
) AS c;
GO

DROP TABLE IF EXISTS #hc;
GO
