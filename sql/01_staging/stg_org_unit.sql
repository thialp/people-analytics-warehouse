-- stg_org_unit
-- The org design as a tree: company, functions, sub-functions, departments.
-- Who leads each unit on a given day comes from stg_job_history.leads_org_unit_id.
CREATE OR REPLACE TABLE staging.stg_org_unit AS
SELECT
    org_unit_id,
    org_unit_name,
    org_unit_type,
    NULLIF(parent_org_unit_id, '')       AS parent_org_unit_id,
    NULLIF("function", '')               AS function_name,
    leader_title,
    CAST(leader_job_level AS INTEGER)    AS leader_grade
FROM raw.dim_org_unit;
