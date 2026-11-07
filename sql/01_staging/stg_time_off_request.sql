-- stg_time_off_request
-- Keystone time off requests: employees, and contingent workers as Bridgeway sent them.
-- Corrections carry negative units and point at the request they reduce.
-- Source: ks_time_off_request (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_time_off_request AS
SELECT
    NULLIF(time_off_request_id, '')                          AS time_off_request_id,
    NULLIF(person_id, '')                                    AS person_id,
    NULLIF(person_type, '')                                  AS person_type,
    NULLIF(source_system, '')                                AS source_system,
    NULLIF(bw_booking_id, '')                                AS bw_booking_id,
    NULLIF(time_off_type, '')                                AS time_off_type,
    NULLIF(request_type, '')                                 AS request_type,
    CAST(NULLIF(first_day, '') AS DATE)                      AS first_day,
    CAST(NULLIF(last_day, '') AS DATE)                       AS last_day,
    CAST(NULLIF(units, '') AS DOUBLE)                        AS units,
    NULLIF(unit_of_time, '')                                 AS unit_of_time,
    CAST(NULLIF(days_requested, '') AS DOUBLE)               AS days_requested,
    NULLIF(corrects_request_id, '')                          AS corrects_request_id,
    NULLIF(status, '')                                       AS status,
    CAST(NULLIF(created_at, '') AS TIMESTAMP)                AS created_at,
    CAST(NULLIF(approved_at, '') AS TIMESTAMP)               AS approved_at
FROM raw.ks_time_off_request;
