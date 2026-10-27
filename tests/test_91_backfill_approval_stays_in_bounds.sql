-- Time to fill (release 5): approval dates vary by function and graduate season, but a moved
-- approval stays realistic. Every filled requisition is approved on or before its fill; a
-- backfill is never approved more than two weeks before the person who left had their last day
-- (it can be approved during the notice period, not earlier); and a net-new PID never exists
-- before its office opened.
WITH bf AS (
    SELECT r.requisition_id, r.approved_date, a.end_date AS prior_last_day
    FROM staging.stg_requisition AS r
    JOIN staging.stg_position_assignment AS a
      ON a.position_id = r.position_id AND a.end_date < r.filled_date
    WHERE r.req_type = 'Backfill' AND r.status = 'Filled'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY r.requisition_id ORDER BY a.end_date DESC) = 1
)
SELECT 'approved after the fill' AS problem, requisition_id AS detail
FROM staging.stg_requisition WHERE status = 'Filled' AND approved_date > filled_date
UNION ALL
SELECT 'backfill approved over two weeks before the last day', requisition_id
FROM bf WHERE approved_date < prior_last_day - INTERVAL 14 DAY
UNION ALL
SELECT 'net-new PID before its office opened', r.requisition_id
FROM staging.stg_requisition AS r JOIN raw.dim_location AS l USING (location_id)
WHERE r.req_type = 'Net-new' AND r.approved_date < CAST(l.opened_date AS DATE)
