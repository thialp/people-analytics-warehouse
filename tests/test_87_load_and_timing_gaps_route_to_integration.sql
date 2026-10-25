-- The routing rule's Integration branch. A gap caused by a failed load exists only at a close whose
-- Bridgeway or Keystone load failed, and goes to Integration with "Alert data engineering". A gap
-- waiting on the feed goes to Integration: "Clears on its own" only when the change was sent in
-- the 24 hours before the close run, "Feed stuck" when it was sent earlier. Nothing else goes to
-- Integration, and every close whose load failed shows at least one load gap.
SELECT 'load gap at a close whose loads worked' AS problem, g.month_end_date, g.gap_id
FROM marts.mart_cw_gap_close AS g JOIN intermediate.int_cw_close_run AS r USING (month_end_date)
WHERE g.cause_code = 'LOAD' AND r.bw_data_as_of = r.month_end_date AND r.ks_data_as_of = r.month_end_date
UNION ALL
SELECT 'load gap not routed to Integration (alert)', month_end_date, gap_id
FROM marts.mart_cw_gap_close
WHERE cause_code = 'LOAD' AND place_key <> 'Integration: alert data engineering'
UNION ALL
SELECT 'feed gap with the wrong shade', g.month_end_date, g.gap_id
FROM marts.mart_cw_gap_close AS g JOIN intermediate.int_cw_close_run AS r USING (month_end_date)
JOIN staging.stg_feed_event_delivery AS d ON d.feed_event_id = g.feed_event_id
WHERE g.cause_code IN ('CW00', 'CW01')
  AND (g.timing_class = 'Clears on its own') <> (d.sent_at > r.close_run_at - INTERVAL 24 HOUR)
UNION ALL
SELECT 'Integration gap with no timing or load cause', month_end_date, gap_id
FROM marts.mart_cw_gap_close
WHERE place = 'Integration' AND cause_code NOT IN ('CW00', 'CW01', 'LOAD')
UNION ALL
SELECT 'failed close load with no load gap', r.month_end_date, NULL
FROM intermediate.int_cw_close_run AS r
WHERE (r.bw_data_as_of < r.month_end_date OR r.ks_data_as_of < r.month_end_date)
  AND NOT EXISTS (SELECT 1 FROM marts.mart_cw_gap_close AS g
                  WHERE g.month_end_date = r.month_end_date AND g.cause_code = 'LOAD')
