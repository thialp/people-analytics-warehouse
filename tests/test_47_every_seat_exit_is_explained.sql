-- Every time a worker leaves a seat it is explained: either they left the company that
-- day (the vacate reason is their termination type), or they moved out and started an
-- Internal Move into another seat the next day. Every Internal Move has that move-out.
WITH seq AS (
    SELECT a.*,
           LEAD(a.start_date) OVER (PARTITION BY a.worker_id ORDER BY a.start_date) AS next_start,
           LEAD(a.fill_type)  OVER (PARTITION BY a.worker_id ORDER BY a.start_date) AS next_fill_type,
           LAG(a.vacate_reason) OVER (PARTITION BY a.worker_id ORDER BY a.start_date) AS prev_vacate_reason
    FROM staging.stg_position_assignment AS a
)
SELECT s.assignment_id, s.worker_id, s.end_date, s.vacate_reason, w.termination_date, w.termination_type,
       s.next_start, s.next_fill_type
FROM seq AS s
JOIN staging.stg_worker AS w ON w.worker_id = s.worker_id
WHERE (s.end_date IS NULL) <> (s.vacate_reason IS NULL)
   OR (s.vacate_reason = 'Internal Move Out'
       AND (s.next_start IS DISTINCT FROM s.end_date + INTERVAL 1 DAY OR s.next_fill_type <> 'Internal Move'))
   OR (s.vacate_reason IN ('Voluntary', 'Involuntary')
       AND (s.end_date IS DISTINCT FROM w.termination_date OR s.vacate_reason <> w.termination_type
            OR s.next_start IS NOT NULL))
   OR (s.end_date IS NULL AND w.termination_date IS NOT NULL)
   OR (s.fill_type = 'Internal Move' AND s.prev_vacate_reason IS DISTINCT FROM 'Internal Move Out')
