-- stg_bw_service_order
-- One row per service order (accumulating snapshot). A renewal is a new order that names
-- the order it renews.
-- Source system: Bridgeway VMS (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_bw_service_order AS
SELECT
    service_order_id,
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    supplier_id,
    order_type,
    NULLIF(renews_service_order_id, '')                      AS renews_service_order_id,
    CAST(NULLIF(opened_date, '') AS DATE)                    AS opened_date,
    CAST(NULLIF(submitted_date, '') AS DATE)                 AS submitted_date,
    CAST(NULLIF(approved_date, '') AS DATE)                  AS approved_date,
    final_status
FROM raw.bw_service_order;
