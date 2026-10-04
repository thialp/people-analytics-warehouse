-- stg_fx_rate
-- Month-end spot rates (actual) and the fixed plan rate used for constant-currency reporting,
-- side by side so every downstream join gets both with one lookup.
CREATE OR REPLACE TABLE staging.stg_fx_rate AS
SELECT
    m.currency_code,
    CAST(m.rate_date AS DATE)                         AS rate_date,
    CAST(m.usd_per_local AS DOUBLE)                   AS usd_per_local_actual,
    CAST(c.usd_per_local AS DOUBLE)                   AS usd_per_local_constant,
    c.rate_set                                        AS constant_rate_set
FROM raw.ref_fx_rate_monthly AS m
JOIN raw.ref_fx_rate_constant AS c
  ON c.currency_code = m.currency_code;
