-- mart_dim_country
-- Grain: one row per country, with its region.
CREATE OR REPLACE TABLE marts.mart_dim_country AS
SELECT DISTINCT country_code, country_name, region
FROM staging.stg_location
ORDER BY country_code;
