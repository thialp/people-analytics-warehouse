-- The backtest's department x office rows (the ones the page sums for any selection) add up to the
-- company: their actuals equal the company actual for every origin and quarter, and no mean or
-- variance is negative.
WITH c AS (
    SELECT origin_quarter_offset, quarter_offset, SUM(actual_filled) AS actual_filled,
           SUM(filled_mean) AS filled_mean
    FROM forecast.mart_pid_forecast_backtest GROUP BY ALL
)
SELECT a.origin_quarter_offset, a.quarter_offset, 'cells do not add to the company actual' AS problem
FROM forecast.mart_pid_forecast_accuracy AS a JOIN c USING (origin_quarter_offset, quarter_offset)
WHERE c.actual_filled <> a.actual_filled
UNION ALL
SELECT a.origin_quarter_offset, a.quarter_offset, 'variance or mean negative'
FROM forecast.mart_pid_forecast_backtest AS a
WHERE a.filled_var < 0 OR a.vacant_end_var < 0 OR a.filled_mean < 0 OR a.vacant_end_mean < 0
