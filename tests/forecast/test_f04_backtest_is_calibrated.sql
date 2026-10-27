-- The likely range means what it says: across the backtest's next-quarter forecasts, the 80% range
-- the page draws (the mean of the draws, plus and minus 1.2816 standard deviations) holds the actual
-- fills in at least half of the quarters and is not useful only by being absurdly wide (it stays
-- under 40% of the mean); the mean is within 10% of the actual on average. The draws' own P10 to P90
-- must pass the same bar.
WITH b AS (SELECT * FROM forecast.mart_pid_forecast_accuracy WHERE horizon = 1)
SELECT 'range holds the actual in under half of the quarters' AS problem,
       CAST(SUM(CASE WHEN filled_in_band THEN 1 ELSE 0 END) AS VARCHAR) || ' of ' || CAST(COUNT(*) AS VARCHAR) AS detail
FROM b HAVING SUM(CASE WHEN filled_in_band THEN 1 ELSE 0 END) * 2 < COUNT(*)
UNION ALL
SELECT 'P10 to P90 holds the actual in under half of the quarters',
       CAST(SUM(CASE WHEN filled_in_range THEN 1 ELSE 0 END) AS VARCHAR) || ' of ' || CAST(COUNT(*) AS VARCHAR)
FROM b HAVING SUM(CASE WHEN filled_in_range THEN 1 ELSE 0 END) * 2 < COUNT(*)
UNION ALL
SELECT 'range too wide to be useful', CAST(ROUND(AVG((filled_high - filled_low) / filled_mean), 3) AS VARCHAR)
FROM b HAVING AVG((filled_high - filled_low) / filled_mean) >= 0.40
UNION ALL
SELECT 'mean off by more than 10% on average', CAST(ROUND(AVG(ABS(filled_mean_error_pct)), 2) AS VARCHAR)
FROM b HAVING AVG(ABS(filled_mean_error_pct)) > 10
UNION ALL
SELECT 'fewer than eight backtest quarters', CAST(COUNT(*) AS VARCHAR) FROM b HAVING COUNT(*) < 8
