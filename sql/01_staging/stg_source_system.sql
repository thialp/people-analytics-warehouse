-- stg_source_system
-- The source systems behind the warehouse (generator/source_systems.py).
-- Source: generator/source_systems.py (warehouse metadata). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_source_system AS
SELECT
    system_code,
    system_name,
    system_type,
    record_of,
    used_by,
    extract
FROM raw.ref_source_system;
