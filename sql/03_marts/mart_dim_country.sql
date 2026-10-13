-- mart_dim_country
-- Grain: one row per country, with its region, currency and pay index.
CREATE OR REPLACE TABLE marts.mart_dim_country AS
SELECT country_code, country_name, region, currency_code, pay_index
FROM staging.stg_country
ORDER BY country_code;
