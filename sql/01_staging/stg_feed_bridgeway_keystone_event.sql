-- stg_feed_bridgeway_keystone_event
-- Every change Bridgeway sent to Keystone, when it was applied, or that it failed.
-- Source system: Bridgeway to Keystone integration log (see generator/source_systems.py). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_feed_bridgeway_keystone_event AS
SELECT
    NULLIF(feed_event_id, '')                                AS feed_event_id,
    NULLIF(revision_id, '')                                  AS revision_id,
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    NULLIF(event_type, '')                                   AS event_type,
    CAST(NULLIF(sent_date, '') AS DATE)                      AS sent_date,
    CAST(NULLIF(applied_date, '') AS DATE)                   AS applied_date,
    NULLIF(outcome, '')                                      AS outcome,
    NULLIF(error_text, '')                                   AS error_text
FROM raw.feed_bridgeway_keystone_event;
