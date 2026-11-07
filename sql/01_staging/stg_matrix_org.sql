-- stg_matrix_org
-- Keystone matrix orgs (SCD Type 2): five region matrices and the country or cluster
-- matrices under them, each with a leader whose seat can be open; an ended matrix keeps an
-- open Inactive record.
-- Source: ks_matrix_org (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_matrix_org AS
SELECT
    NULLIF(matrix_record_id, '')                             AS matrix_record_id,
    NULLIF(matrix_org_id, '')                                AS matrix_org_id,
    NULLIF(matrix_org_name, '')                              AS matrix_org_name,
    NULLIF(matrix_type, '')                                  AS matrix_type,
    NULLIF(region, '')                                       AS region,
    NULLIF(parent_matrix_org_id, '')                         AS parent_matrix_org_id,
    NULLIF(covers_country_codes, '')                         AS covers_country_codes,
    CAST(NULLIF(effective_start_date, '') AS DATE)           AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    NULLIF(manager_worker_id, '')                            AS manager_worker_id,
    NULLIF(status, '')                                       AS status,
    CAST(NULLIF(inactive_date, '') AS DATE)                  AS inactive_date,
    CAST(NULLIF(created_date, '') AS DATE)                   AS created_date,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE), DATE '9999-12-31') AS effective_end_date_filled
FROM raw.ks_matrix_org;
