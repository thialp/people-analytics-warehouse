-- Billed time sits inside the assignment as Bridgeway holds it on the extract date, is
-- priced at a rate the order actually carried, and adds up: amount = units x rate to the
-- cent, and no month bills more hours than its weekdays x 8.
WITH cur AS (
    SELECT service_order_id, assignment_start_date, assignment_end_date
    FROM staging.stg_bw_service_order_revision WHERE is_current
),
rates AS (
    SELECT DISTINCT service_order_id, bill_rate FROM staging.stg_bw_service_order_revision
)
SELECT t.timesheet_id, 'outside the assignment' AS problem
FROM staging.stg_bw_timesheet_month AS t JOIN cur USING (service_order_id)
WHERE t.month_end_date < cur.assignment_start_date
   OR DATE_TRUNC('month', t.month_end_date) > cur.assignment_end_date
UNION ALL
SELECT t.timesheet_id, 'rate the order never carried'
FROM staging.stg_bw_timesheet_month AS t LEFT JOIN rates AS r USING (service_order_id, bill_rate)
WHERE r.service_order_id IS NULL
UNION ALL
SELECT timesheet_id, 'amount is not units x rate'
FROM staging.stg_bw_timesheet_month
WHERE ABS(billed_amount_local - ROUND(billed_units * bill_rate, 2)) > 0.005
UNION ALL
SELECT timesheet_id, 'more hours than the month has working days'
FROM staging.stg_bw_timesheet_month
WHERE billed_hours > 8 * (SELECT COUNT(*) FROM generate_series(DATE_TRUNC('month', month_end_date), month_end_date, INTERVAL 1 DAY) AS g(d)
                          WHERE DAYOFWEEK(g.d) BETWEEN 1 AND 5)
