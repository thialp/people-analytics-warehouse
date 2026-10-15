-- stg_bw_supplier
-- Bridgeway VMS suppliers, one row each.
-- Source system: Bridgeway VMS (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_bw_supplier AS
SELECT
    supplier_id,
    supplier_name,
    cw_types_offered,
    hq_country_code,
    CAST(NULLIF(onboarded_date, '') AS DATE)                 AS onboarded_date,
    CAST(NULLIF(is_active, '') AS BOOLEAN)                   AS is_active
FROM raw.bw_supplier;
