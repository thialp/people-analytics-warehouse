-- stg_location
-- 35 offices. Street addresses are fictional; postal codes are real and coordinates
-- are the GeoNames centroid of the postal code (exceptions noted in geo_source).
CREATE OR REPLACE TABLE staging.stg_location AS
SELECT
    location_id,
    office_name,
    site_type,
    street_address,
    city,
    state_province,
    NULLIF(postal_code, '')                 AS postal_code,
    country_code,
    country_name,
    region,
    currency_code,
    CAST(latitude AS DECIMAL(9, 4))         AS latitude,
    CAST(longitude AS DECIMAL(9, 4))        AS longitude,
    geo_source,
    CAST(pay_zone_factor AS DECIMAL(5, 2))  AS pay_zone_factor,
    CAST(opened_date AS DATE)               AS opened_date
FROM raw.dim_location;
