-- mart_dim_location
-- Grain: one row per office location, with map coordinates.
--
-- Coordinates are public city-centre points (WGS84, four decimals), which is
-- precise enough for a world map and avoids implying a street address.
-- "Remote - US" has no office, so it has no coordinates: the map shows it as a
-- separate figure rather than placing remote workers on an invented point.
CREATE OR REPLACE TABLE marts.mart_dim_location AS
WITH coordinates (location_id, latitude, longitude) AS (
    VALUES
        ('LOC-001',  30.2672,  -97.7431),   -- Austin
        ('LOC-002',  40.7128,  -74.0060),   -- New York
        ('LOC-003',  37.7749, -122.4194),   -- San Francisco
        ('LOC-004',  33.7490,  -84.3880),   -- Atlanta
        ('LOC-006',  43.6532,  -79.3832),   -- Toronto
        ('LOC-007', -23.5505,  -46.6333),   -- Sao Paulo
        ('LOC-008',  19.4326,  -99.1332),   -- Mexico City
        ('LOC-009',  51.5074,   -0.1278),   -- London
        ('LOC-010',  53.3498,   -6.2603),   -- Dublin
        ('LOC-011',  52.5200,   13.4050),   -- Berlin
        ('LOC-012',  48.8566,    2.3522),   -- Paris
        ('LOC-013',  52.2297,   21.0122),   -- Warsaw
        ('LOC-014',  50.0647,   19.9450),   -- Krakow
        ('LOC-015',  12.9716,   77.5946),   -- Bangalore
        ('LOC-016',  17.3850,   78.4867),   -- Hyderabad
        ('LOC-017',   1.3521,  103.8198),   -- Singapore
        ('LOC-018',  35.6762,  139.6503),   -- Tokyo
        ('LOC-019', -33.8688,  151.2093),   -- Sydney
        ('LOC-020',  25.2048,   55.2708),   -- Dubai
        ('LOC-021', -26.2041,   28.0473),   -- Johannesburg
        ('LOC-022', -33.9249,   18.4241)    -- Cape Town
)
SELECT
    l.location_id,
    l.city,
    l.country_code,
    l.country_name,
    l.region,
    l.site_type,
    CAST(c.latitude  AS DECIMAL(9, 4)) AS latitude,
    CAST(c.longitude AS DECIMAL(9, 4)) AS longitude
FROM staging.stg_location AS l
LEFT JOIN coordinates AS c USING (location_id)
ORDER BY l.location_id;
