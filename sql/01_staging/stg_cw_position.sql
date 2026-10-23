-- stg_cw_position
-- Effective-dated (SCD Type 2) contingent PIDs, from Keystone's PID table (release 3.1).
-- A contingent PID is created, or a vacant one reused, when a request for a contingent worker
-- is approved; it is Filled while Bridgeway holds the assignment, then Open (vacant) until the
-- next contingent worker in the same role takes it or the position audit closes it
-- (Eliminated). It has no job profile or grade: the role is the contingent type and role family.
-- effective_end_date is inclusive; NULL means the record is still current.
CREATE OR REPLACE TABLE staging.stg_cw_position AS
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
    cw_type,
    cw_role_family,
    CAST(created_date AS DATE)                               AS created_date,
    created_reason
FROM raw.dim_position
WHERE worker_type = 'Contingent';
