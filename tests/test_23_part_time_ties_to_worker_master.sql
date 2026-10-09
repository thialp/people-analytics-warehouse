-- part_time_headcount (workers below 1.0 FTE) must tie to the worker-level movement
-- table at both ends of every month, and each month's Opening must equal the
-- previous month's Closing. Returns a row for every month that breaks either rule.
WITH walk AS (
    SELECT
        month_end_date,
        SUM(part_time_headcount) FILTER (WHERE movement_category = 'Opening') AS walk_open,
        SUM(part_time_headcount) FILTER (WHERE movement_category = 'Closing') AS walk_close
    FROM marts.mart_headcount_fte_walk
    GROUP BY month_end_date
),
workers AS (
    SELECT
        month_end_date,
        COUNT(*) FILTER (WHERE in_prior   AND prior_fte   < 1) AS src_open,
        COUNT(*) FILTER (WHERE in_current AND current_fte < 1) AS src_close
    FROM intermediate.int_worker_movement
    GROUP BY month_end_date
)
SELECT w.month_end_date, w.walk_open, w.walk_close, s.src_open, s.src_close
FROM walk AS w
JOIN workers AS s USING (month_end_date)
LEFT JOIN walk AS prev
       ON prev.month_end_date = (w.month_end_date - INTERVAL 1 MONTH)
          OR prev.month_end_date = LAST_DAY(w.month_end_date - INTERVAL 1 MONTH)
WHERE w.walk_open  <> s.src_open
   OR w.walk_close <> s.src_close
   OR (prev.month_end_date IS NOT NULL AND prev.walk_close <> w.walk_open)
