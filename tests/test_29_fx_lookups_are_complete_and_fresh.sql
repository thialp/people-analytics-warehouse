-- FX is real and complete: every pay record finds an ECB rate posted no more than 5
-- days before its posting date (weekends and holidays), every currency has
-- month-end rates for the whole window, and the constant rate set equals the actual
-- rate on its own date (2026-06-30).
SELECT comp_record_id AS id, currency_code, effective_start_date AS d, 'stale or missing posting rate' AS issue
FROM intermediate.int_compensation_history_usd
WHERE posting_fx_rate IS NULL OR effective_start_date - posting_fx_rate_date > 5
UNION ALL
SELECT NULL, cur.currency_code, cal.month_end_date, 'missing month-end rate'
FROM intermediate.int_month_end_calendar AS cal
CROSS JOIN (SELECT DISTINCT currency_code FROM staging.stg_country) AS cur
LEFT JOIN staging.stg_fx_rate AS fx ON fx.currency_code = cur.currency_code AND fx.rate_date = cal.month_end_date
WHERE fx.currency_code IS NULL
UNION ALL
SELECT NULL, currency_code, rate_date, 'constant rate differs from actual on its date'
FROM staging.stg_fx_rate
WHERE rate_date = DATE '2026-06-30' AND usd_per_local_actual <> usd_per_local_constant
