-- stg_position
-- Effective-dated (SCD Type 2) seats. A position is a seat that outlives the people in
-- it: status Filled, Open (approved to hire), Frozen (hiring paused) or Eliminated, and
-- the seat's department, office, job and level. While a seat is filled it follows its
-- incumbent (a promotion re-levels the seat in place); when it is vacated it can be
-- re-levelled or relocated before it is refilled.
-- effective_end_date is inclusive; NULL means the record is still current.
CREATE OR REPLACE TABLE staging.stg_position AS
SELECT
    position_record_id,
    position_id,
    CAST(effective_start_date AS DATE)                       AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE),
             DATE '9999-12-31')                              AS effective_end_date_filled,
    change_reason,
    status,
    department_id,
    cost_center_id,
    location_id,
    job_profile_id,
    CAST(job_level AS INTEGER)                               AS grade,
    CAST(fte AS DECIMAL(4, 2))                               AS fte,
    CAST(created_date AS DATE)                               AS created_date,
    created_reason
FROM raw.dim_position;
