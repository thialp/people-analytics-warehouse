-- On every month-end a seat is Filled exactly when someone holds it, and an Open seat
-- has an open requisition.
SELECT month_end_date, position_id, status, incumbent_worker_id, open_requisition_id
FROM intermediate.int_position_snapshot
WHERE (status = 'Filled') <> (incumbent_worker_id IS NOT NULL)
   OR (status = 'Open' AND open_requisition_id IS NULL AND month_end_date <> status_since)
