-- stg_raw_column
-- Column contract of every release 3 raw table (test 61).
-- Source: generator/source_systems.py (warehouse metadata). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_raw_column AS
SELECT
    table_name,
    CAST(NULLIF(column_order, '') AS INTEGER)                AS column_order,
    column_name,
    data_type,
    description
FROM raw.ref_raw_column;
