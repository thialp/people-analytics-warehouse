-- stg_requisition
-- One row per requisition (accumulating snapshot): opened, approved, then filled or
-- cancelled. req_type is Backfill when the seat had an incumbent before, Net-new when
-- it is filled for the first time. The department, office, job and level are the
-- seat's as it was when the requisition opened.
-- A seat refilled immediately (succession, a team handed to a new manager) gets a
-- requisition opened and approved on the day the seat was vacated.
CREATE OR REPLACE TABLE staging.stg_requisition AS
SELECT
    requisition_id,
    position_id,
    req_type,
    CAST(opened_date AS DATE)                                AS opened_date,
    CAST(approved_date AS DATE)                              AS approved_date,
    CAST(target_start_date AS DATE)                          AS target_start_date,
    CAST(NULLIF(filled_date, '') AS DATE)                    AS filled_date,
    CAST(NULLIF(cancelled_date, '') AS DATE)                 AS cancelled_date,
    status,
    department_id,
    cost_center_id,
    location_id,
    job_profile_id,
    CAST(job_level AS INTEGER)                               AS grade,
    NULLIF(hiring_manager_id, '')                            AS hiring_manager_id,
    NULLIF(filled_by_worker_id, '')                          AS filled_by_worker_id,
    NULLIF(fill_source, '')                                  AS fill_source
FROM raw.fact_requisition;
