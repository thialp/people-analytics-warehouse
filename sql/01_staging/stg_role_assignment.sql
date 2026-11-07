-- stg_role_assignment
-- Keystone role assignments: HR and Finance partners on org units, Direct or Inherited.
-- The target name carries the leader the row was issued for.
-- Source: ks_role_assignment (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_role_assignment AS
SELECT
    NULLIF(assignment_id, '')                                AS assignment_id,
    NULLIF(role_name, '')                                    AS role_name,
    NULLIF(assignee_worker_id, '')                           AS assignee_worker_id,
    NULLIF(target_org_unit_id, '')                           AS target_org_unit_id,
    NULLIF(target_org_name, '')                              AS target_org_name,
    NULLIF(named_leader_worker_id, '')                       AS named_leader_worker_id,
    NULLIF(assigned_via, '')                                 AS assigned_via,
    NULLIF(inherited_from_org_unit_id, '')                   AS inherited_from_org_unit_id,
    CAST(NULLIF(effective_start_date, '') AS DATE)           AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE), DATE '9999-12-31') AS effective_end_date_filled
FROM raw.ks_role_assignment;
