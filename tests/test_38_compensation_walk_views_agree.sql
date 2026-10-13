-- Every view is a different cut of the same people, so for each date pair the steps
-- other than transfers must add up to the same company totals in all six views, and
-- the constant-currency measures must carry no FX Translation.
WITH by_view AS (
    SELECT from_month_end, to_month_end, view_name, step,
           SUM(headcount) AS hc, SUM(fte) AS fte, SUM(base_usd_nominal) AS bn, SUM(loaded_usd_constant) AS lc
    FROM marts.mart_compensation_walk
    WHERE step NOT IN ('Transfers In', 'Transfers Out')
    GROUP BY ALL
),
company AS (SELECT * FROM by_view WHERE view_name = 'Company')
SELECT v.from_month_end, v.to_month_end, v.view_name, v.step
FROM by_view AS v
LEFT JOIN company AS c USING (from_month_end, to_month_end, step)
WHERE c.hc IS NULL OR v.hc <> c.hc OR v.fte <> c.fte
   OR ABS(v.bn - c.bn) > 0.5 OR ABS(v.lc - c.lc) > 0.5
UNION ALL
SELECT from_month_end, to_month_end, view_name, step
FROM marts.mart_compensation_walk
WHERE step = 'FX Translation' AND (base_usd_constant <> 0 OR loaded_usd_constant <> 0)
