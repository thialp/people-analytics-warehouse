-- The answer key that scores discrepancy detection is itself sound: every row has a known
-- type, points at records that exist (Bridgeway worker, Keystone person, service order, feed
-- event, timesheet), runs forward in time inside the extract, and carries what its type
-- needs: a feed event for feed failures and delays, a timesheet billed after the last day for
-- CW11, no Bridgeway worker for a Keystone-only worker (CW09). Codes and causes agree.
WITH t AS (SELECT * FROM staging.stg_gen_cw_discrepancy_truth)
SELECT discrepancy_id, 'unknown discrepancy or root cause code' AS problem
FROM t
WHERE discrepancy_code NOT IN (SELECT discrepancy_code FROM staging.stg_cw_discrepancy_type)
   OR root_cause_code NOT IN (SELECT discrepancy_code FROM staging.stg_cw_discrepancy_type)
UNION ALL
SELECT discrepancy_id, 'Bridgeway worker does not exist'
FROM t WHERE bw_worker_id IS NOT NULL
  AND bw_worker_id NOT IN (SELECT bw_worker_id FROM staging.stg_bw_contingent_worker)
UNION ALL
SELECT discrepancy_id, 'Keystone person does not exist'
FROM t WHERE person_id IS NOT NULL
  AND person_id NOT IN (SELECT person_id FROM staging.stg_ks_contingent_worker)
UNION ALL
SELECT discrepancy_id, 'service order does not exist'
FROM t WHERE service_order_id IS NOT NULL
  AND service_order_id NOT IN (SELECT service_order_id FROM staging.stg_bw_service_order)
UNION ALL
SELECT discrepancy_id, 'feed event does not exist or is another worker''s'
FROM t LEFT JOIN staging.stg_feed_bridgeway_keystone_event AS f USING (feed_event_id)
WHERE t.feed_event_id IS NOT NULL AND (f.feed_event_id IS NULL OR f.bw_worker_id <> t.bw_worker_id)
UNION ALL
SELECT discrepancy_id, 'ends before it starts, or dated after the extract'
FROM t WHERE end_date < start_date OR start_date > DATE '2026-06-30' OR end_date > DATE '2026-06-30'
UNION ALL
SELECT discrepancy_id, 'open at extract but resolved, or resolved but open'
FROM t WHERE (end_date IS NULL) <> (resolution = 'Open at extract')
UNION ALL
SELECT discrepancy_id, 'feed delay or failure without its feed event'
FROM t WHERE discrepancy_code IN ('CW00', 'CW01', 'CW02', 'CW03', 'CW12') AND feed_event_id IS NULL
UNION ALL
SELECT t.discrepancy_id, 'CW11 timesheet is not after the assignment ended'
FROM t
LEFT JOIN staging.stg_bw_timesheet_month AS s USING (timesheet_id)
LEFT JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = s.service_order_id AND r.is_current
WHERE t.discrepancy_code = 'CW11'
  AND (s.timesheet_id IS NULL OR DATE_TRUNC('month', s.month_end_date) <= r.assignment_end_date)
UNION ALL
SELECT discrepancy_id, 'Keystone-only worker linked to Bridgeway, or without a person'
FROM t WHERE discrepancy_code = 'CW09' AND (bw_worker_id IS NOT NULL OR person_id IS NULL)
UNION ALL
SELECT discrepancy_id, 'root cause differs where it cannot'
FROM t WHERE root_cause_code <> discrepancy_code
  AND NOT (discrepancy_code IN ('CW02', 'CW03', 'CW12') AND root_cause_code IN ('CW06', 'CW08'))
