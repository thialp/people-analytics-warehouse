-- stg_ks_contingent_worker
-- The Keystone HR profile of each contingent worker (SCD Type 2). Written by the feed
-- from Bridgeway, or by hand in Keystone (HR Ops, managers). bw_worker_id is what
-- Keystone stored: it can be blank or mistyped, which identity resolution handles.
-- Source system: Keystone HR (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_ks_contingent_worker AS
SELECT
    NULLIF(ks_record_id, '')                                 AS ks_record_id,
    NULLIF(person_id, '')                                    AS person_id,
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    CAST(NULLIF(effective_start_date, '') AS DATE)           AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    NULLIF(change_source, '')                                AS change_source,
    NULLIF(feed_event_id, '')                                AS feed_event_id,
    NULLIF(first_name, '')                                   AS first_name,
    NULLIF(last_name, '')                                    AS last_name,
    NULLIF(cw_type, '')                                      AS cw_type,
    NULLIF(supplier_name, '')                                AS supplier_name,
    NULLIF(status, '')                                       AS status,
    CAST(NULLIF(contract_start_date, '') AS DATE)            AS contract_start_date,
    CAST(NULLIF(contract_end_date, '') AS DATE)              AS contract_end_date,
    NULLIF(inactive_reason, '')                              AS inactive_reason,
    NULLIF(department_id, '')                                AS department_id,
    NULLIF(cost_center_id, '')                               AS cost_center_id,
    NULLIF(location_id, '')                                  AS location_id,
    NULLIF(manager_worker_id, '')                            AS manager_worker_id,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE),
             DATE '9999-12-31')                              AS effective_end_date_filled
FROM raw.ks_contingent_worker;
