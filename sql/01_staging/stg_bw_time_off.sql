-- stg_bw_time_off
-- Bridgeway time off bookings: contingent workers book time off in the vendor system;
-- Bridgeway is the source of truth for their days off.
-- Source: bw_time_off (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_bw_time_off AS
SELECT
    NULLIF(booking_id, '')                                   AS booking_id,
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    NULLIF(service_order_id, '')                             AS service_order_id,
    NULLIF(booking_type, '')                                 AS booking_type,
    CAST(NULLIF(first_day, '') AS DATE)                      AS first_day,
    CAST(NULLIF(last_day, '') AS DATE)                       AS last_day,
    CAST(NULLIF(working_days, '') AS INTEGER)                AS working_days,
    CAST(NULLIF(hours, '') AS DOUBLE)                        AS hours,
    NULLIF(status, '')                                       AS status,
    CAST(NULLIF(submitted_at, '') AS TIMESTAMP)              AS submitted_at,
    CAST(NULLIF(approved_at, '') AS TIMESTAMP)               AS approved_at
FROM raw.bw_time_off;
