-- stg_matrix_membership
-- Keystone matrix membership: which country matrix each person (employee or contingent
-- worker) belongs to, and when.
-- Source: ks_matrix_membership (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_matrix_membership AS
SELECT
    NULLIF(membership_id, '')                                AS membership_id,
    NULLIF(person_id, '')                                    AS person_id,
    NULLIF(person_type, '')                                  AS person_type,
    NULLIF(matrix_org_id, '')                                AS matrix_org_id,
    CAST(NULLIF(effective_start_date, '') AS DATE)           AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    NULLIF(assigned_reason, '')                              AS assigned_reason,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE), DATE '9999-12-31') AS effective_end_date_filled
FROM raw.ks_matrix_membership;
