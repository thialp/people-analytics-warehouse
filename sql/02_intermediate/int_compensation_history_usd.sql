-- int_compensation_history_usd
-- Grain: one row per compensation record (after corrections).
--
-- Each pay record is valued in USD at the FX rate of the day it was posted (its
-- effective date): the "booked" rate. The local amount never changes after posting,
-- so the booked USD value only moves when a new record is posted. ECB rates exist on
-- business days only; the ASOF join takes the latest rate on or before the posting date.
--
-- The constant-currency value uses one fixed rate set for every period (the latest
-- month-end rate in the data, 2026-06-30), so it moves only when pay moves.
CREATE OR REPLACE TABLE intermediate.int_compensation_history_usd AS
SELECT
    c.comp_record_id,
    c.worker_id,
    c.effective_start_date,
    c.effective_end_date,
    c.effective_end_date_filled,
    c.action_reason,
    c.currency_code,
    c.base_salary_annual_local,
    c.was_corrected,
    fx.rate_date                                             AS posting_fx_rate_date,
    fx.usd_per_local                                         AS posting_fx_rate,
    k.usd_per_local                                          AS constant_fx_rate,
    c.base_salary_annual_local * fx.usd_per_local            AS base_salary_annual_usd_posting,
    c.base_salary_annual_local * k.usd_per_local             AS base_salary_annual_usd_constant
FROM staging.stg_compensation_history AS c
ASOF LEFT JOIN staging.stg_fx_rate_daily AS fx
       ON fx.currency_code = c.currency_code
      AND fx.rate_date    <= c.effective_start_date
LEFT JOIN (SELECT DISTINCT currency_code, usd_per_local_constant AS usd_per_local FROM staging.stg_fx_rate) AS k
       ON k.currency_code = c.currency_code;
