-- mart_dim_location
-- Grain: one row per office, with its map point and the date it opened.
--
-- Street addresses are fictional. Postal codes are real codes for each business
-- district, and latitude/longitude is the GeoNames centroid of the postal code
-- (geo_source names the two exceptions: Sao Paulo and Dubai, where the UAE has
-- no postal codes). Precise enough for a world map without implying a building.
CREATE OR REPLACE TABLE marts.mart_dim_location AS
SELECT
    location_id,
    office_name,
    city,
    state_province,
    postal_code,
    street_address,
    country_code,
    country_name,
    region,
    site_type,
    latitude,
    longitude,
    geo_source,
    pay_zone_factor,
    opened_date
FROM staging.stg_location
ORDER BY location_id;
