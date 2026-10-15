-- Contractor and Consultant engagements stop at 48 months from the worker's original start;
-- BPO has no cap. A few are extended past the cap anyway (the breaches the contingent
-- workforce case study flags), but never by more than six months: anything longer means the
-- extension rule in the simulation is broken. Measured on the latest assignment end Bridgeway
-- holds for each worker.
WITH e AS (
    SELECT w.bw_worker_id, w.cw_type, w.original_start_date,
           MAX(r.assignment_end_date) AS last_end
    FROM staging.stg_bw_contingent_worker AS w
    JOIN staging.stg_bw_service_order AS o ON o.bw_worker_id = w.bw_worker_id
    JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = o.service_order_id AND r.is_current
    WHERE r.status IN ('Approved', 'Closed')
    GROUP BY ALL
)
SELECT bw_worker_id, cw_type, original_start_date, last_end
FROM e
WHERE cw_type <> 'BPO'
  AND last_end > original_start_date + INTERVAL 54 MONTH
