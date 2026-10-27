-- No look-ahead: every forecast (the forward one and each backtest origin) was fit only on
-- requisitions approved, and fills known, by its origin date; the forward forecast starts on the
-- report date and covers exactly the calendar's forward quarters, with every draw present.
WITH cal AS (SELECT * FROM staging.stg_report_calendar)
SELECT 'fit used data after its origin' AS problem, CAST(origin_date AS VARCHAR) AS detail
FROM forecast.mart_pid_forecast_run
WHERE latest_approval_used > origin_date OR latest_fill_used > origin_date
UNION ALL
SELECT 'forward run not on the report date', CAST(r.origin_date AS VARCHAR)
FROM forecast.mart_pid_forecast_run AS r, cal AS c
WHERE r.run_type = 'Forward' AND r.origin_date <> c.report_as_of_date
UNION ALL
SELECT 'forecast quarter is not a forward quarter', CAST(d.quarter_offset AS VARCHAR)
FROM (SELECT DISTINCT quarter_offset FROM forecast.mart_pid_forecast_draws) AS d
LEFT JOIN staging.stg_report_quarter AS q ON q.quarter_offset = d.quarter_offset AND q.is_forward
WHERE q.quarter_offset IS NULL
UNION ALL
SELECT 'draw count differs from the run', CAST(COUNT(DISTINCT d.draw) AS VARCHAR)
FROM forecast.mart_pid_forecast_draws AS d
HAVING COUNT(DISTINCT d.draw) <> (SELECT MAX(draws) FROM forecast.mart_pid_forecast_run WHERE run_type = 'Forward')
UNION ALL
SELECT 'backtest origin after the report date', CAST(origin_quarter_offset AS VARCHAR)
FROM forecast.mart_pid_forecast_accuracy WHERE origin_quarter_offset >= 0 OR quarter_offset > 0
