-- stg_cw_position_assignment
-- Which contingent worker held which PID, and when (release 3.1). One row per span Bridgeway
-- holds the assignment (the rule of int_cw_month_end_snapshot, day by day), so filled
-- contingent PIDs equal the month-end contingent headcount (test 81).
--   worker_id      the worker's Keystone person ID (Bridgeway's ID converted to an Arcadia ID)
--   bw_worker_id   Bridgeway's worker ID
--   requisition_id the Bridgeway service order that started the span
--   vacate_reason  Contract ended, Ended early, Converted to employee; NULL while still working
CREATE OR REPLACE TABLE staging.stg_cw_position_assignment AS
SELECT
    assignment_id,
    position_id,
    NULLIF(worker_id, '')                                    AS worker_id,
    bw_worker_id,
    CAST(start_date AS DATE)                                 AS start_date,
    CAST(NULLIF(end_date, '') AS DATE)                       AS end_date,
    COALESCE(CAST(NULLIF(end_date, '') AS DATE),
             DATE '9999-12-31')                              AS end_date_filled,
    requisition_id                                           AS service_order_id,
    NULLIF(vacate_reason, '')                                AS vacate_reason
FROM raw.fact_position_assignment
WHERE worker_type = 'Contingent';
