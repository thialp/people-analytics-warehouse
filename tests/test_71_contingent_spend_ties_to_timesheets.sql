-- Contingent spend adds up: every month and billing currency, the spend mart's billed amount,
-- hours and units equal bw_timesheet_month to the cent; its USD amounts are the local amounts
-- at that month-end's rates; and its month-end workers and run-rate are the Bridgeway
-- snapshot's, so billed spend and the run-rate the plan and the cost bridge use share one
-- population.
WITH ts AS (
    SELECT month_end_date, billing_currency, SUM(billed_amount_local) AS amount,
           SUM(billed_hours) AS hours, SUM(billed_units) AS units
    FROM staging.stg_bw_timesheet_month GROUP BY 1, 2
),
mart AS (
    SELECT month_end_date, billing_currency, SUM(billed_amount_local) AS amount,
           SUM(billed_hours) AS hours, SUM(billed_units) AS units,
           SUM(billed_usd_nominal) AS usd_nominal, SUM(billed_usd_constant) AS usd_constant
    FROM marts.mart_cw_spend GROUP BY 1, 2
),
snap AS (
    SELECT month_end_date, COUNT(*) AS cw, SUM(run_rate_usd_constant) AS run_rate
    FROM intermediate.int_cw_month_end_snapshot GROUP BY 1
),
mart_snap AS (
    SELECT month_end_date, SUM(workers_at_month_end) AS cw, SUM(run_rate_usd_constant) AS run_rate
    FROM marts.mart_cw_spend GROUP BY 1
)
SELECT COALESCE(t.month_end_date, m.month_end_date) AS month_end_date,
       COALESCE(t.billing_currency, m.billing_currency) AS currency, 'billing differs from the timesheets' AS problem
FROM ts AS t FULL OUTER JOIN mart AS m USING (month_end_date, billing_currency)
WHERE t.amount IS DISTINCT FROM m.amount OR t.hours IS DISTINCT FROM m.hours
   OR ABS(COALESCE(t.units, 0) - COALESCE(m.units, 0)) > 0.0001
UNION ALL
SELECT m.month_end_date, m.billing_currency, 'USD is not local x the month-end rate'
FROM mart AS m JOIN staging.stg_fx_rate AS fx ON fx.currency_code = m.billing_currency AND fx.rate_date = m.month_end_date
WHERE ABS(m.usd_nominal - m.amount * fx.usd_per_local_actual) > 1
   OR ABS(m.usd_constant - m.amount * fx.usd_per_local_constant) > 1
UNION ALL
SELECT s.month_end_date, NULL, 'month-end workers or run-rate differ from the snapshot'
FROM snap AS s LEFT JOIN mart_snap AS m USING (month_end_date)
WHERE m.cw IS DISTINCT FROM s.cw OR ABS(m.run_rate - s.run_rate) > 1
