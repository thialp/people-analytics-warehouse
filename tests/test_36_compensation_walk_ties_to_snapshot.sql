-- Every group's Opening and Closing must equal the snapshot at those month-ends
-- (executive officers excluded), checked here for the Department and Office views,
-- which between them cover every worker.
WITH snap AS (
    SELECT month_end_date, department_id, location_id, COUNT(*) AS hc, SUM(fte) AS fte,
           SUM(base_usd_nominal) AS bn, SUM(loaded_usd_constant) AS lc
    FROM intermediate.int_worker_month_end_snapshot
    WHERE NOT is_executive_officer
    GROUP BY ALL
),
by_group AS (
    SELECT month_end_date, 'Department' AS view_name, department_id AS group_id,
           SUM(hc) AS hc, SUM(fte) AS fte, SUM(bn) AS bn, SUM(lc) AS lc FROM snap GROUP BY ALL
    UNION ALL
    SELECT month_end_date, 'Office', location_id, SUM(hc), SUM(fte), SUM(bn), SUM(lc) FROM snap GROUP BY ALL
),
walk AS (
    SELECT CASE step WHEN 'Opening' THEN from_month_end ELSE to_month_end END AS month_end_date,
           view_name, group_id, step, headcount, fte, base_usd_nominal, loaded_usd_constant
    FROM marts.mart_compensation_walk
    WHERE step IN ('Opening', 'Closing') AND view_name IN ('Department', 'Office')
)
SELECT w.*, g.hc, g.bn
FROM walk AS w
LEFT JOIN by_group AS g USING (month_end_date, view_name, group_id)
WHERE g.hc IS NULL OR w.headcount <> g.hc OR ABS(w.fte - g.fte) > 0.005
   OR ABS(w.base_usd_nominal - g.bn) > 0.01 OR ABS(w.loaded_usd_constant - g.lc) > 0.01
