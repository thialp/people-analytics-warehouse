-- stg_feed_event_delivery
-- The hour each feed change was sent (the hourly batch that picked it up) and the hour Keystone
-- applied it, GMT. Same days as the feed log; empty applied_at when it failed or is still queued.
-- Source system: Bridgeway to Keystone integration log (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_feed_event_delivery AS
SELECT
    NULLIF(feed_event_id, '')                                AS feed_event_id,
    CAST(NULLIF(sent_at, '') AS TIMESTAMP)                   AS sent_at,
    CAST(NULLIF(applied_at, '') AS TIMESTAMP)                AS applied_at
FROM raw.feed_event_delivery;
