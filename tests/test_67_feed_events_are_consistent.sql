-- The Bridgeway -> Keystone feed log is consistent with Bridgeway and with itself: every event
-- comes from a revision of one of the worker's own orders, of the type that revision implies,
-- sent on the revision's effective date; an applied event is applied on or after it was sent
-- and by the extract date; the outcome agrees with the dates (Applied within 2 days, Applied
-- Late after 3 or more, Failed and Queued not applied) and failures carry an error; and a
-- worker's events are applied first in, first out.
WITH f AS (
    SELECT f.*, r.revision_no, r.revision_reason, r.effective_start_date, o.order_type,
           o.bw_worker_id AS order_worker,
           LAG(f.applied_date) OVER (PARTITION BY f.bw_worker_id, f.applied_date IS NOT NULL
                                     ORDER BY f.sent_date, f.feed_event_id) AS prev_applied
    FROM staging.stg_feed_bridgeway_keystone_event AS f
    LEFT JOIN staging.stg_bw_service_order_revision AS r USING (revision_id)
    LEFT JOIN staging.stg_bw_service_order AS o ON o.service_order_id = r.service_order_id
)
SELECT feed_event_id, 'revision does not exist' AS problem FROM f WHERE revision_no IS NULL
UNION ALL
SELECT feed_event_id, 'revision belongs to another worker' FROM f WHERE order_worker <> bw_worker_id
UNION ALL
SELECT feed_event_id, 'event type does not match the revision'
FROM f
WHERE NOT (   (event_type IN ('New Worker', 'Renewal') AND revision_no = 0)
           OR (event_type = 'Extension' AND revision_reason = 'Extension')
           OR (event_type = 'Early End' AND revision_reason = 'Early end')
           OR (event_type = 'Attribute Change'
               AND revision_reason IN ('Cost center change', 'Manager change', 'Office change')))
UNION ALL
SELECT feed_event_id, 'not sent on the revision''s effective date' FROM f WHERE sent_date <> effective_start_date
UNION ALL
SELECT feed_event_id, 'applied before it was sent, or after the extract'
FROM f WHERE applied_date < sent_date OR applied_date > DATE '2026-06-30'
UNION ALL
SELECT feed_event_id, 'outcome does not match the dates'
FROM f
WHERE (outcome = 'Applied' AND NOT (applied_date - sent_date BETWEEN 0 AND 2))
   OR (outcome = 'Applied Late' AND NOT (applied_date - sent_date >= 3))
   OR (outcome = 'Partly Applied' AND (applied_date IS NULL OR event_type <> 'New Worker'))
   OR (outcome IN ('Failed', 'Queued') AND applied_date IS NOT NULL)
   OR outcome NOT IN ('Applied', 'Applied Late', 'Partly Applied', 'Failed', 'Queued')
UNION ALL
SELECT feed_event_id, 'error text missing, or on a clean load'
FROM f
WHERE (outcome IN ('Failed', 'Partly Applied')) <> (error_text IS NOT NULL)
UNION ALL
SELECT feed_event_id, 'applied ahead of an earlier event for the same worker'
FROM f WHERE applied_date < prev_applied
