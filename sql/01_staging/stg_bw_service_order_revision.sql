-- stg_bw_service_order_revision
-- Service order revisions (SCD Type 2): every extension, rate change, early end or
-- attribute change is a new revision; exactly one is current per order. effective_end_date
-- is inclusive, NULL on the current revision (filled with 9999-12-31 for as-of joins).
-- Source system: Bridgeway VMS (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_bw_service_order_revision AS
SELECT
    revision_id,
    service_order_id,
    CAST(NULLIF(revision_no, '') AS INTEGER)                 AS revision_no,
    revision_reason,
    CAST(NULLIF(effective_start_date, '') AS DATE)           AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    CAST(NULLIF(is_current, '') AS BOOLEAN)                  AS is_current,
    status,
    CAST(NULLIF(assignment_start_date, '') AS DATE)          AS assignment_start_date,
    CAST(NULLIF(assignment_end_date, '') AS DATE)            AS assignment_end_date,
    CAST(NULLIF(closed_date, '') AS DATE)                    AS closed_date,
    role_family,
    seniority,
    job_title,
    NULLIF(cost_center_code, '')                             AS cost_center_code,
    NULLIF(hiring_manager_email, '')                         AS hiring_manager_email,
    NULLIF(office_code, '')                                  AS office_code,
    CAST(NULLIF(bill_rate, '') AS DECIMAL(18, 4))            AS bill_rate,
    rate_type,
    billing_currency,
    CAST(NULLIF(hours_per_week, '') AS DECIMAL(9, 2))        AS hours_per_week,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE),
             DATE '9999-12-31')                              AS effective_end_date_filled
FROM raw.bw_service_order_revision;
