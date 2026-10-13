-- The flow map and the office walk must tell the same story: for every office
-- and month, workers flowing out (and in) equal its relocations out (and in).
-- Also guards the map: no self-loops, and every office has
-- coordinates.
WITH flows_out AS (
    SELECT month_end_date, from_location_id AS location_id, SUM(workers) AS n
    FROM marts.mart_mobility_flows GROUP BY ALL
),
flows_in AS (
    SELECT month_end_date, to_location_id AS location_id, SUM(workers) AS n
    FROM marts.mart_mobility_flows GROUP BY ALL
)
SELECT 'flow mismatch' AS issue, l.month_end_date, l.location_id
FROM marts.mart_location_headcount AS l
LEFT JOIN flows_out AS o USING (month_end_date, location_id)
LEFT JOIN flows_in  AS i USING (month_end_date, location_id)
WHERE l.relocations_out <> COALESCE(o.n, 0)
   OR l.relocations_in  <> COALESCE(i.n, 0)
UNION ALL
SELECT 'self loop', month_end_date, from_location_id
FROM marts.mart_mobility_flows WHERE from_location_id = to_location_id
UNION ALL
SELECT 'missing coordinates', NULL, location_id
FROM marts.mart_dim_location WHERE latitude IS NULL OR longitude IS NULL
