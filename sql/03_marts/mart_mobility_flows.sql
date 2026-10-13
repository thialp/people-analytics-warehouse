-- mart_mobility_flows
-- Grain: one row per month-end per origin office per destination office.
--
-- Workers who changed office between two consecutive month-ends, as origin to
-- destination pairs, for a flow map. Each row carries both ends' coordinates so
-- Tableau can draw the line with MAKELINE(MAKEPOINT(from), MAKEPOINT(to))
-- without relating the location table twice.
--
-- Every office has coordinates (test 22), so has_coordinates is always true; the
-- column is kept so existing map calculations keep working.
CREATE OR REPLACE TABLE marts.mart_mobility_flows AS
WITH moves AS (
    SELECT month_end_date, prior_location_id AS from_location_id, current_location_id AS to_location_id
    FROM intermediate.int_worker_movement
    WHERE in_prior AND in_current AND prior_location_id <> current_location_id
)

SELECT
    mv.month_end_date,
    mv.from_location_id,
    f.city                                         AS from_city,
    f.region                                       AS from_region,
    f.latitude                                     AS from_latitude,
    f.longitude                                    AS from_longitude,
    mv.to_location_id,
    t.city                                         AS to_city,
    t.region                                       AS to_region,
    t.latitude                                     AS to_latitude,
    t.longitude                                    AS to_longitude,
    CASE WHEN f.country_code = t.country_code THEN 'Domestic' ELSE 'International' END AS flow_scope,
    f.latitude IS NOT NULL AND t.latitude IS NOT NULL AS has_coordinates,
    CAST(COUNT(*) AS INTEGER)                      AS workers
FROM moves AS mv
JOIN marts.mart_dim_location AS f ON f.location_id = mv.from_location_id
JOIN marts.mart_dim_location AS t ON t.location_id = mv.to_location_id
GROUP BY ALL
ORDER BY mv.month_end_date, mv.from_location_id, mv.to_location_id;
