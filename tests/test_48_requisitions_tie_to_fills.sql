-- Requisitions and seat fills agree: every fill after history starts has a requisition
-- on the same seat, a Filled requisition has exactly that one fill (same day, same
-- person, internal or external as the fill), and dates run in order.
WITH fills AS (
    SELECT a.requisition_id, COUNT(*) AS fills, MIN(a.position_id) AS position_id,
           MIN(a.start_date) AS start_date, MIN(a.worker_id) AS worker_id,
           MIN(CASE a.fill_type WHEN 'Internal Move' THEN 'Internal' ELSE 'External' END) AS source
    FROM staging.stg_position_assignment AS a
    WHERE a.requisition_id IS NOT NULL
    GROUP BY a.requisition_id
)
SELECT r.requisition_id, r.status, r.position_id, f.position_id AS filled_position, f.fills, 'requisition' AS problem
FROM staging.stg_requisition AS r
LEFT JOIN fills AS f ON f.requisition_id = r.requisition_id
WHERE (r.status = 'Filled' AND (f.fills IS DISTINCT FROM 1 OR f.position_id <> r.position_id
                                OR f.start_date <> r.filled_date OR f.worker_id <> r.filled_by_worker_id
                                OR f.source <> r.fill_source))
   OR (r.status <> 'Filled' AND f.fills IS NOT NULL)
   OR r.approved_date < r.opened_date
   OR r.filled_date < r.approved_date
   OR r.cancelled_date < r.approved_date
   OR (r.status = 'Cancelled') <> (r.cancelled_date IS NOT NULL)
UNION ALL
SELECT a.assignment_id, a.fill_type, a.position_id, NULL, NULL, 'fill without requisition'
FROM staging.stg_position_assignment AS a
WHERE a.fill_type <> 'Initial' AND a.requisition_id IS NULL
