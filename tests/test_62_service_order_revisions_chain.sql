-- Bridgeway service order revisions are a clean effective-dated history: within an order the
-- revisions are numbered 0, 1, 2 ... without gaps, each starts the day after the previous one
-- ends (no gap, no overlap), only the last one is open-ended, and exactly one is current.
WITH r AS (
    SELECT service_order_id, revision_no, effective_start_date, effective_end_date, is_current,
           LAG(effective_end_date) OVER w AS prev_end,
           ROW_NUMBER() OVER w - 1           AS expected_no,
           COUNT(*) OVER (PARTITION BY service_order_id)                        AS revisions,
           SUM(CASE WHEN is_current THEN 1 ELSE 0 END) OVER (PARTITION BY service_order_id) AS current_count
    FROM staging.stg_bw_service_order_revision
    WINDOW w AS (PARTITION BY service_order_id ORDER BY revision_no)
)
SELECT service_order_id, revision_no, 'revision number skipped' AS problem FROM r WHERE revision_no <> expected_no
UNION ALL
SELECT service_order_id, revision_no, 'gap or overlap with the previous revision'
FROM r WHERE revision_no > 0 AND (prev_end IS NULL OR effective_start_date <> prev_end + INTERVAL 1 DAY)
UNION ALL
SELECT service_order_id, revision_no, 'ends before it starts' FROM r WHERE effective_end_date < effective_start_date
UNION ALL
SELECT service_order_id, revision_no, 'open-ended revision that is not the last'
FROM r WHERE effective_end_date IS NULL AND revision_no < revisions - 1
UNION ALL
SELECT service_order_id, revision_no, 'current flag on the wrong revision'
FROM r WHERE is_current <> (revision_no = revisions - 1)
UNION ALL
SELECT service_order_id, NULL, 'not exactly one current revision' FROM r WHERE current_count <> 1 GROUP BY service_order_id
