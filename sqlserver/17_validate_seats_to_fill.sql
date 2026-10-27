/*
  17_validate_seats_to_fill.sql
  Release 5 (Dashboard #5, Seats to Fill): runs the page's Tableau Custom SQL inside SQL Server
  exactly as Tableau would (included unchanged with sqlcmd's :r) and checks it against the forecast
  the DuckDB warehouse wrote: rows by type, the history that ties to Dashboard #3, the forward
  plan, the forecast median, the backtest and the contingent line. Run it after build_all.sql:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/17_validate_seats_to_fill.sql

  Every expected value comes from the DuckDB forecast tables (forecast/run_forecast.py, release 5).
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

DECLARE @started DATETIME2 = SYSDATETIME();
DROP TABLE IF EXISTS #s5;
SELECT *
INTO #s5
FROM (
:r /repo/tableau/custom_sql_seats_to_fill.sql
) AS s;
DECLARE @n INT = (SELECT COUNT(*) FROM #s5);
PRINT CONCAT('Seats to Fill Custom SQL returned ', @n, ' rows in ',
             DATEDIFF(SECOND, @started, SYSDATETIME()), ' seconds');
GO

PRINT '1. Rows by type';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'all rows' AS check_name, (SELECT COUNT(*) FROM #s5) AS actual, 399560 AS expected
    UNION ALL SELECT 'Quarter rows',   (SELECT COUNT(*) FROM #s5 WHERE row_type = 'Quarter'), 21720
    UNION ALL SELECT 'Draw rows',      (SELECT COUNT(*) FROM #s5 WHERE row_type = 'Draw'), 253259
    UNION ALL SELECT 'Survival rows',  (SELECT COUNT(*) FROM #s5 WHERE row_type = 'Survival'), 105294
    UNION ALL SELECT 'Backtest rows',  (SELECT COUNT(*) FROM #s5 WHERE row_type = 'Backtest'), 19219
    UNION ALL SELECT 'Accuracy rows',  (SELECT COUNT(*) FROM #s5 WHERE row_type = 'Accuracy'), 20
    UNION ALL SELECT 'CW budget rows', (SELECT COUNT(*) FROM #s5 WHERE row_type = 'CW budget'), 48
    UNION ALL SELECT 'rows without a department (Accuracy and CW budget only)',
                     (SELECT COUNT(*) FROM #s5 WHERE department_id IS NULL), 68
    UNION ALL SELECT 'rows without the report date label', (SELECT COUNT(*) FROM #s5 WHERE report_as_of_label IS NULL), 0
) AS c;
GO

PRINT '2. History, plan and forecast';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'PIDs filled in the current fiscal year (Dashboard #3: 4,668 + 2,181)' AS check_name,
                     (SELECT SUM(filled) FROM #s5 WHERE row_type = 'Quarter' AND fy_offset = 0) AS actual, 6849 AS expected
    UNION ALL SELECT 'waiting on the report date',
                     (SELECT SUM(vacant_end) FROM #s5 WHERE row_type = 'Quarter' AND quarter_offset = 0), 902
    UNION ALL SELECT 'forward year planned fills (Budget, net-new + backfills)',
                     (SELECT CAST(ROUND(SUM(planned_net_new) + SUM(planned_backfills), 0) AS INT)
                      FROM #s5 WHERE row_type = 'Quarter' AND fy_offset = 1), 7709
    UNION ALL SELECT 'forward year fills, all draws',
                     (SELECT SUM(filled) FROM #s5 WHERE row_type = 'Draw'), 689114
    UNION ALL SELECT 'forward year fills, the median draw',
                     (SELECT MAX(m) FROM (SELECT PERCENTILE_DISC(0.5) WITHIN GROUP (ORDER BY f) OVER () AS m
                                          FROM (SELECT draw, SUM(filled) AS f FROM #s5 WHERE row_type = 'Draw' GROUP BY draw) AS d) AS p), 6838
    UNION ALL SELECT 'first forward quarter starts with the waiting PIDs in every draw',
                     (SELECT COUNT(*) FROM (SELECT draw FROM #s5 WHERE row_type = 'Draw' AND quarter_offset = 1
                                            GROUP BY draw HAVING SUM(vacant_start) <> 902) AS x), 0
    UNION ALL SELECT 'survival fills', (SELECT SUM(sv_filled) FROM #s5 WHERE row_type = 'Survival'), 26278
    UNION ALL SELECT 'backtest actual fills', (SELECT SUM(actual_filled) FROM #s5 WHERE row_type = 'Backtest'), 31711
    UNION ALL SELECT 'backtest next-quarter forecasts in range',
                     (SELECT SUM(CAST(filled_in_range AS INT)) FROM #s5 WHERE row_type = 'Accuracy' AND horizon = 1), 6
    UNION ALL SELECT 'forward contingent budget, workers at year-end',
                     (SELECT SUM(planned_cw_headcount) FROM #s5 WHERE row_type = 'CW budget' AND fy_offset = 1), 13097
) AS c;
GO
