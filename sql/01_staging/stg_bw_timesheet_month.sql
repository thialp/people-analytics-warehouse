-- stg_bw_timesheet_month
-- Billed time per worker, service order and month. BPO orders bill monthly units.
-- Source system: Bridgeway VMS (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_bw_timesheet_month AS
SELECT
    timesheet_id,
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    service_order_id,
    CAST(NULLIF(month_end_date, '') AS DATE)                 AS month_end_date,
    CAST(NULLIF(billed_hours, '') AS DECIMAL(9, 2))          AS billed_hours,
    CAST(NULLIF(billed_units, '') AS DECIMAL(9, 2))          AS billed_units,
    CAST(NULLIF(bill_rate, '') AS DECIMAL(18, 4))            AS bill_rate,
    billing_currency,
    CAST(NULLIF(billed_amount_local, '') AS DECIMAL(18, 4))  AS billed_amount_local
FROM raw.bw_timesheet_month;
