-- stg_bw_contingent_worker
-- Workers as Bridgeway knows them. Bridgeway never stores the Keystone person ID; the
-- link lives on the Keystone side (stg_ks_contingent_worker.bw_worker_id).
-- Source system: Bridgeway VMS (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_bw_contingent_worker AS
SELECT
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    first_name,
    last_name,
    email,
    supplier_id,
    cw_type,
    CAST(NULLIF(original_start_date, '') AS DATE)            AS original_start_date,
    CAST(NULLIF(created_date, '') AS DATE)                   AS created_date
FROM raw.bw_contingent_worker;
