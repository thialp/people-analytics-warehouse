-- stg_function_hub
-- The offices each function means its people to sit in: its hubs (training, senior managers, support).
-- Source: ref_function_hub (see generator/org_design.py, FUNCTION_HUBS). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_function_hub AS
SELECT
    NULLIF(function_name, '')                                AS function_name,
    NULLIF(location_id, '')                                  AS location_id,
    NULLIF(hub_name, '')                                     AS hub_name
FROM raw.ref_function_hub;
