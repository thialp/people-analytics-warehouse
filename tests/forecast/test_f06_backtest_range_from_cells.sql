-- The page rebuilds the backtest range for any selection from the department x office rows:
--   sum of means ± 1.2816 × sqrt(sum of variances + (shared cv × sum of means)²)
-- The shared cv carries the company-wide shocks every draw applies to all cells at once. Summed over
-- the whole company, that formula must give back the range of the company's own draws (within 1 PID,
-- the rounding of the stored means and variances), for fills and for vacancy, at every origin and quarter.
WITH c AS (
    SELECT origin_quarter_offset, quarter_offset,
           SUM(filled_mean) AS fm, SUM(filled_var) AS fv, MIN(filled_shared_cv) AS fc, MAX(filled_shared_cv) AS fc_max,
           SUM(vacant_end_mean) AS vm, SUM(vacant_end_var) AS vv, MIN(vacant_end_shared_cv) AS vc, MAX(vacant_end_shared_cv) AS vc_max
    FROM forecast.mart_pid_forecast_backtest GROUP BY ALL
), r AS (
    SELECT a.origin_quarter_offset, a.quarter_offset,
           fm - 1.2816 * SQRT(fv + POWER(fc * fm, 2)) AS f_low, fm + 1.2816 * SQRT(fv + POWER(fc * fm, 2)) AS f_high,
           vm - 1.2816 * SQRT(vv + POWER(vc * vm, 2)) AS v_low, vm + 1.2816 * SQRT(vv + POWER(vc * vm, 2)) AS v_high,
           fc, fc_max, vc, vc_max, a.filled_low, a.filled_high, a.vacant_end_low, a.vacant_end_high
    FROM forecast.mart_pid_forecast_accuracy AS a JOIN c USING (origin_quarter_offset, quarter_offset)
)
SELECT origin_quarter_offset, quarter_offset, 'shared cv differs between cells of one quarter' AS problem
FROM r WHERE fc <> fc_max OR vc <> vc_max
UNION ALL
SELECT origin_quarter_offset, quarter_offset, 'fills range from the cells misses the company draws'
FROM r WHERE ABS(f_low - filled_low) > 1 OR ABS(f_high - filled_high) > 1
UNION ALL
SELECT origin_quarter_offset, quarter_offset, 'vacancy range from the cells misses the company draws'
FROM r WHERE ABS(v_low - vacant_end_low) > 1 OR ABS(v_high - vacant_end_high) > 1
