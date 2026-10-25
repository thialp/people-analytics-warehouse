-- The release 4 times agree with the release 3 dates: every feed event has one delivery row, sent on
-- its sent_date, applied (when it was) on its applied_date and after it was sent; every Keystone
-- version was written on its effective start date. The load log has one run per source per
-- schedule, Keystone starts after Bridgeway finishes, and a failed run reads no rows.
SELECT 'feed delivery does not match the feed log' AS problem, f.feed_event_id AS id
FROM staging.stg_feed_bridgeway_keystone_event AS f
LEFT JOIN staging.stg_feed_event_delivery AS d USING (feed_event_id)
WHERE d.feed_event_id IS NULL OR CAST(d.sent_at AS DATE) <> f.sent_date
   OR CAST(d.applied_at AS DATE) IS DISTINCT FROM f.applied_date OR d.applied_at <= d.sent_at
UNION ALL
SELECT 'Keystone version written on another day', k.ks_record_id
FROM staging.stg_ks_contingent_worker AS k
LEFT JOIN staging.stg_ks_contingent_worker_audit AS a USING (ks_record_id)
WHERE a.ks_record_id IS NULL OR CAST(a.changed_at AS DATE) <> k.effective_start_date
UNION ALL
SELECT 'duplicate scheduled run', source_system || ' ' || CAST(scheduled_at AS VARCHAR)
FROM staging.stg_etl_load_run GROUP BY source_system, scheduled_at HAVING COUNT(*) > 1
UNION ALL
SELECT 'Keystone started before Bridgeway finished', k.run_id
FROM staging.stg_etl_load_run AS k
JOIN staging.stg_etl_load_run AS b
  ON b.source_system = 'BW' AND k.source_system = 'KS' AND CAST(b.scheduled_at AS DATE) = CAST(k.scheduled_at AS DATE)
WHERE k.started_at < b.finished_at
UNION ALL
SELECT 'failed run with rows, or a run without', run_id
FROM staging.stg_etl_load_run
WHERE (status = 'Failed') = (rows_read IS NOT NULL)
