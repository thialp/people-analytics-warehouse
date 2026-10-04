-- Every active worker in every month has pay, an FX rate (actual and constant),
-- a fringe rate and a salary range. A missing lookup would silently drop dollars.
SELECT month_end_date, worker_id, currency_code, country_code, grade,
       base_salary_annual_local, fx_rate_actual, fx_rate_constant, fringe_rate, range_mid_local
FROM intermediate.int_worker_month_end_snapshot
WHERE base_salary_annual_local IS NULL
   OR fx_rate_actual IS NULL
   OR fx_rate_constant IS NULL
   OR fringe_rate IS NULL
   OR range_mid_local IS NULL
