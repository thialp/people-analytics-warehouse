-- The applicant pipeline agrees with the requisitions: a Filled requisition has exactly
-- one Accepted candidate, who is the worker that filled the seat (internal when the
-- fill was internal); no other requisition has one. Each candidate's stages run in
-- order without gaps, between approval and the fill or cancellation, and the final
-- status is the last stage reached.
WITH accepted AS (
    SELECT requisition_id, COUNT(*) AS n, MIN(worker_id) AS worker_id, BOOL_AND(is_internal) AS is_internal
    FROM staging.stg_candidate
    WHERE final_status = 'Accepted'
    GROUP BY requisition_id
),
last_stage AS (
    SELECT candidate_id, MAX(stage_order) AS n_stages, COUNT(*) AS n_rows,
           ARG_MAX(stage, stage_order) AS last_stage
    FROM staging.stg_candidate_stage_event
    GROUP BY candidate_id
)
SELECT r.requisition_id AS id, r.status AS detail, 'accepted candidate' AS problem
FROM staging.stg_requisition AS r
LEFT JOIN accepted AS a USING (requisition_id)
WHERE (r.status = 'Filled' AND (a.n IS DISTINCT FROM 1 OR a.worker_id IS DISTINCT FROM r.filled_by_worker_id
                                OR a.is_internal <> (r.fill_source = 'Internal')))
   OR (r.status <> 'Filled' AND a.n IS NOT NULL)
UNION ALL
SELECT e.candidate_id, e.stage, 'stage order or date'
FROM staging.stg_candidate_stage_event AS e
JOIN staging.stg_candidate AS c USING (candidate_id)
JOIN staging.stg_requisition AS r USING (requisition_id)
WHERE e.stage_date < LEAST(r.approved_date, COALESCE(r.filled_date, r.approved_date))
   OR e.stage_date > COALESCE(r.filled_date, r.cancelled_date, (SELECT MAX(month_end_date) FROM intermediate.int_month_end_calendar))
   OR e.stage_date < (SELECT MAX(e2.stage_date) FROM staging.stg_candidate_stage_event AS e2
                      WHERE e2.candidate_id = e.candidate_id AND e2.stage_order < e.stage_order)
UNION ALL
SELECT c.candidate_id, c.final_status, 'final status'
FROM staging.stg_candidate AS c
JOIN last_stage AS l USING (candidate_id)
WHERE l.n_stages <> l.n_rows
   OR c.final_status <> CASE WHEN l.last_stage IN ('Accepted', 'Declined', 'Rejected', 'Withdrawn')
                             THEN l.last_stage ELSE 'In process' END
