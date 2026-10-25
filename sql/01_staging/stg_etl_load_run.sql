-- stg_etl_load_run
-- The warehouse's own load log: every scheduled read of Bridgeway (00:00 GMT), Keystone (00:20,
-- after Bridgeway) and Helix (00:00 and 12:00), with its status. A failed run read nothing; the
-- warehouse kept that source's previous load.
-- Source system: Arcadia warehouse load log (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_etl_load_run AS
SELECT
    NULLIF(run_id, '')                                       AS run_id,
    NULLIF(source_system, '')                                AS source_system,
    CAST(NULLIF(scheduled_at, '') AS TIMESTAMP)              AS scheduled_at,
    CAST(NULLIF(started_at, '') AS TIMESTAMP)                AS started_at,
    CAST(NULLIF(finished_at, '') AS TIMESTAMP)               AS finished_at,
    NULLIF(status, '')                                       AS status,
    CAST(NULLIF(rows_read, '') AS BIGINT)                    AS rows_read,
    NULLIF(error_text, '')                                   AS error_text
FROM raw.etl_load_run;
