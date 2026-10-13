-- stg_bonus_payout
-- The bonus earned on each review, in local currency, paid on August 31 to people
-- still employed (Forfeited if they left first; Scheduled when the payout date is
-- after the data window). Prorated by months worked in the fiscal year.
CREATE OR REPLACE TABLE staging.stg_bonus_payout AS
SELECT
    bonus_id,
    worker_id,
    CAST(fiscal_year AS INTEGER)                    AS fiscal_year,
    CAST(payout_date AS DATE)                       AS payout_date,
    currency_code,
    CAST(base_salary_annual_local AS DECIMAL(18, 2)) AS base_salary_annual_local,
    CAST(fte AS DECIMAL(4, 2))                      AS fte,
    CAST(proration_factor AS DECIMAL(6, 4))         AS proration_factor,
    CAST(bonus_pct AS DOUBLE)                       AS bonus_pct,
    CAST(bonus_amount_local AS DECIMAL(18, 2))      AS bonus_amount_local,
    payout_status
FROM raw.fact_bonus_payout;
