-- stg_ks_contingent_worker_audit
-- When each Keystone contingent version was written (GMT) and by whom: the feed, Keystone's
-- nightly job, a manager, or HR Operations.
-- Source system: Keystone HR (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_ks_contingent_worker_audit AS
SELECT
    NULLIF(ks_record_id, '')                                 AS ks_record_id,
    CAST(NULLIF(changed_at, '') AS TIMESTAMP)                AS changed_at,
    NULLIF(changed_by, '')                                   AS changed_by
FROM raw.ks_contingent_worker_audit;
