-- stg_raw_table_lineage
-- Which source system and module every raw table comes from (test 60).
-- Source: generator/source_systems.py (warehouse metadata). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_raw_table_lineage AS
SELECT
    table_name,
    system_code,
    module,
    grain,
    history_type,
    CAST(NULLIF(added_in_release, '') AS INTEGER)            AS added_in_release
FROM raw.ref_raw_table_lineage;
