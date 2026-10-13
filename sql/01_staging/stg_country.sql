-- stg_country
-- 22 countries with region, currency and Arcadia's pay index (US = 1.00).
CREATE OR REPLACE TABLE staging.stg_country AS
SELECT
    country_code,
    country_name,
    region,
    currency_code,
    CAST(pay_index AS DECIMAL(5, 2)) AS pay_index
FROM raw.dim_country;
