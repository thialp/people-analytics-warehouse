-- stg_fx_rate_daily
-- Every ECB publication day (EUR crosses turned into USD per 1 unit of local
-- currency). Weekends and holidays have no row: lookups take the latest rate on or
-- before the date (ASOF join), the rule a payroll system applies.
CREATE OR REPLACE TABLE staging.stg_fx_rate_daily AS
SELECT
    currency_code,
    CAST(rate_date AS DATE)        AS rate_date,
    CAST(usd_per_local AS DOUBLE)  AS usd_per_local,
    source
FROM raw.ref_fx_rate_daily;
