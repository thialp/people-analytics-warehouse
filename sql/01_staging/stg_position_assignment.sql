-- stg_position_assignment
-- Who sat in which seat, and when. One row per worker per seat held.
--   fill_type      Initial (in the seat when history starts), External Hire, Internal Move
--   vacate_reason  Voluntary, Involuntary (left the company), Internal Move Out (moved to
--                  another seat the next day), NULL while still in the seat
-- end_date is inclusive; NULL means the worker is still in the seat.
CREATE OR REPLACE TABLE staging.stg_position_assignment AS
SELECT
    assignment_id,
    position_id,
    worker_id,
    CAST(start_date AS DATE)                                 AS start_date,
    CAST(NULLIF(end_date, '') AS DATE)                       AS end_date,
    COALESCE(CAST(NULLIF(end_date, '') AS DATE),
             DATE '9999-12-31')                              AS end_date_filled,
    fill_type,
    NULLIF(requisition_id, '')                               AS requisition_id,
    NULLIF(vacate_reason, '')                                AS vacate_reason
FROM raw.fact_position_assignment;
