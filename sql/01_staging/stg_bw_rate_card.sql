-- stg_bw_rate_card
-- Bridgeway rate card: target rate and band per fiscal year x country x CW type x role
-- family x seniority. BPO lines are monthly; everything else hourly.
-- Source system: Bridgeway VMS (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_bw_rate_card AS
SELECT
    rate_card_id,
    CAST(NULLIF(fiscal_year, '') AS INTEGER)                 AS fiscal_year,
    country_code,
    cw_type,
    role_family,
    seniority,
    rate_type,
    billing_currency,
    CAST(NULLIF(rate_low, '') AS DECIMAL(18, 4))             AS rate_low,
    CAST(NULLIF(rate_target, '') AS DECIMAL(18, 4))          AS rate_target,
    CAST(NULLIF(rate_high, '') AS DECIMAL(18, 4))            AS rate_high
FROM raw.bw_rate_card;
