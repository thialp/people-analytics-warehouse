-- stg_leave_of_absence
-- Keystone leaves of absence, with the estimated and (once known) actual return.
-- Source: ks_leave_of_absence (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_leave_of_absence AS
SELECT
    NULLIF(leave_id, '')                                     AS leave_id,
    NULLIF(worker_id, '')                                    AS worker_id,
    NULLIF(leave_type, '')                                   AS leave_type,
    NULLIF(status, '')                                       AS status,
    CAST(NULLIF(initiated_date, '') AS DATE)                 AS initiated_date,
    CAST(NULLIF(approved_date, '') AS DATE)                  AS approved_date,
    CAST(NULLIF(last_day_of_work, '') AS DATE)               AS last_day_of_work,
    CAST(NULLIF(first_day_of_leave, '') AS DATE)             AS first_day_of_leave,
    CAST(NULLIF(estimated_last_day_of_leave, '') AS DATE)    AS estimated_last_day_of_leave,
    CAST(NULLIF(actual_last_day_of_leave, '') AS DATE)       AS actual_last_day_of_leave,
    CAST(NULLIF(first_day_back_at_work, '') AS DATE)         AS first_day_back_at_work,
    CAST(NULLIF(total_days_on_leave, '') AS INTEGER)         AS total_days_on_leave,
    CAST(NULLIF(is_estimated, '') AS BOOLEAN)                AS is_estimated
FROM raw.ks_leave_of_absence;
