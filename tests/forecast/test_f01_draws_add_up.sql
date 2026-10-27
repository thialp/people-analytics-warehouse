-- Every simulated future adds up: in each draw, department x office and quarter, PIDs vacant at the
-- end = vacant at the start + PIDs opened (backfills, net-new, immediate refills) - PIDs filled, and
-- a quarter starts where the one before it ended. The first quarter starts with exactly the
-- requisitions waiting on the report date, in every draw, and every department x office has a row
-- in every draw and quarter (zeros included), so percentiles across draws hold for any selection.
WITH d AS (SELECT * FROM forecast.mart_pid_forecast_draws),
grid AS (
    SELECT k.department_id, k.location_id, k.draw, q.quarter_offset
    FROM (SELECT DISTINCT department_id, location_id, draw FROM d) AS k
    CROSS JOIN (SELECT DISTINCT quarter_offset FROM d) AS q
),
full_ AS (
    SELECT g.department_id, g.location_id, g.draw, g.quarter_offset,
           COALESCE(d.vacant_start, 0) AS vacant_start, COALESCE(d.vacant_end, 0) AS vacant_end
    FROM grid AS g LEFT JOIN d USING (department_id, location_id, draw, quarter_offset)
),
start_pool AS (
    SELECT SUM(vacant_end) AS waiting FROM forecast.mart_pid_fill_quarter WHERE quarter_offset = 0
)
SELECT 'quarter does not add up' AS problem, department_id, location_id, draw, quarter_offset
FROM d
WHERE vacant_end <> vacant_start + opened_backfill + opened_net_new + opened_immediate - filled
UNION ALL
SELECT 'quarter does not start where the last ended', a.department_id, a.location_id, a.draw, a.quarter_offset
FROM full_ AS a JOIN full_ AS b
  ON b.department_id = a.department_id AND b.location_id = a.location_id AND b.draw = a.draw
 AND b.quarter_offset = a.quarter_offset - 1
WHERE a.vacant_start <> b.vacant_end
UNION ALL
SELECT 'first quarter does not start with the waiting requisitions', NULL, NULL, x.draw, 1
FROM (SELECT draw, SUM(vacant_start) AS s FROM d WHERE quarter_offset = 1 GROUP BY draw) AS x, start_pool AS p
WHERE x.s <> p.waiting
UNION ALL
SELECT 'a department x office misses a draw or a quarter', department_id, location_id, NULL, NULL
FROM forecast.mart_pid_forecast_draws
GROUP BY department_id, location_id
HAVING COUNT(*) <> (SELECT COUNT(DISTINCT draw) * COUNT(DISTINCT quarter_offset) FROM forecast.mart_pid_forecast_draws)
