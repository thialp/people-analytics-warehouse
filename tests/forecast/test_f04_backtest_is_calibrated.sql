-- The likely range means what it says: across the backtest's next-quarter forecasts, the 80% range
-- (P10 to P90) holds the actual fills in at least half of the quarters and never in all of them by
-- being absurdly wide (the range stays under 40% of the median); the median is within 10% on average.
WITH b AS (SELECT * FROM forecast.mart_pid_forecast_accuracy WHERE horizon = 1)
SELECT 'range holds the actual in under half of the quarters' AS problem,
       CAST(SUM(CASE WHEN filled_in_range THEN 1 ELSE 0 END) AS VARCHAR) || ' of ' || CAST(COUNT(*) AS VARCHAR) AS detail
FROM b HAVING SUM(CASE WHEN filled_in_range THEN 1 ELSE 0 END) * 2 < COUNT(*)
UNION ALL
SELECT 'range too wide to be useful', CAST(ROUND(AVG((filled_p90 - filled_p10) / filled_p50), 3) AS VARCHAR)
FROM b HAVING AVG((filled_p90 - filled_p10) / filled_p50) >= 0.40
UNION ALL
SELECT 'median off by more than 10% on average', CAST(ROUND(AVG(ABS(filled_error_pct)), 2) AS VARCHAR)
FROM b HAVING AVG(ABS(filled_error_pct)) > 10
UNION ALL
SELECT 'fewer than eight backtest quarters', CAST(COUNT(*) AS VARCHAR) FROM b HAVING COUNT(*) < 8
