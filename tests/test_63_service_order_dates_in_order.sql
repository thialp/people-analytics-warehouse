-- A service order's dates happen in order: opened <= submitted <= approved, and a new
-- engagement starts after it was approved (a renewal may be approved late, after its first
-- day: that is a real Bridgeway pattern, not an error). On every revision the assignment
-- ends on or after it starts. Workers that never started (withdrawn or rejected) are exempt
-- from the last two rules.
SELECT o.service_order_id, 'opened, submitted and approved out of order' AS problem
FROM staging.stg_bw_service_order AS o
WHERE o.submitted_date < o.opened_date OR o.approved_date < o.submitted_date
UNION ALL
SELECT o.service_order_id, 'new engagement starts before approval'
FROM staging.stg_bw_service_order AS o
JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = o.service_order_id AND r.revision_no = 0
WHERE o.order_type = 'New engagement' AND o.approved_date IS NOT NULL AND r.assignment_start_date <= o.approved_date
UNION ALL
SELECT r.service_order_id, 'assignment ends before it starts'
FROM staging.stg_bw_service_order_revision AS r
WHERE r.status NOT IN ('Withdrawn', 'Rejected') AND r.assignment_end_date < r.assignment_start_date
