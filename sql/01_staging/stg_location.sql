-- stg_location
CREATE OR REPLACE TABLE staging.stg_location AS
SELECT location_id, city, country_code, country_name, region, currency_code, site_type
FROM raw.dim_location;
