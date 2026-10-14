-- A contingent conversion is told consistently by every system that knows of it. Keystone's
-- contingent record closes as Converted to employee on the employee's hire date, under the
-- same name, and the employee was hired through a requisition with an applicant whose source
-- is Contingent conversion. Every such applicant has that Keystone record, unless Keystone
-- never had the contingent worker at all (the answer key's CW08). Where Keystone's link to
-- Bridgeway is intact, the hire falls in the calendar month of the first day after the worker's
-- last Bridgeway day, at most 21 days later: a conversion never changes the total workforce.
WITH conv AS (
    SELECT k.person_id, k.bw_worker_id, k.first_name, k.last_name, k.converted_to_worker_id AS worker_id,
           k.effective_start_date AS converted_on
    FROM staging.stg_ks_contingent_worker AS k
    WHERE k.inactive_reason = 'Converted to employee'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY k.person_id ORDER BY k.effective_start_date) = 1
),
cand AS (
    SELECT c.candidate_id, c.worker_id, c.final_status, c.is_internal, q.status AS req_status, q.filled_by_worker_id
    FROM staging.stg_candidate AS c JOIN staging.stg_requisition AS q USING (requisition_id)
    WHERE c.candidate_source = 'Contingent conversion'
),
last_day AS (   -- the worker's last day as Bridgeway holds it now
    SELECT o.bw_worker_id, MAX(r.assignment_end_date) AS last_day
    FROM staging.stg_bw_service_order_revision AS r JOIN staging.stg_bw_service_order AS o USING (service_order_id)
    WHERE r.is_current AND r.status IN ('Approved', 'Closed')
    GROUP BY 1
)
SELECT c.person_id AS id, 'not converted on the employee''s hire date, or under another name' AS problem
FROM conv AS c JOIN staging.stg_worker AS w USING (worker_id)
WHERE c.converted_on <> w.original_hire_date OR c.first_name <> w.first_name OR c.last_name <> w.last_name
UNION ALL
SELECT c.person_id, 'converted employee was not hired as a contingent conversion'
FROM conv AS c LEFT JOIN cand AS a USING (worker_id)
WHERE a.candidate_id IS NULL
UNION ALL
SELECT candidate_id, 'conversion applicant who was not the accepted external hire'
FROM cand
WHERE final_status <> 'Accepted' OR is_internal OR req_status <> 'Filled' OR filled_by_worker_id <> worker_id
UNION ALL
SELECT a.candidate_id, 'conversion applicant with no converted Keystone record'
FROM cand AS a
JOIN staging.stg_worker AS w USING (worker_id)
WHERE a.worker_id NOT IN (SELECT worker_id FROM conv)
  AND NOT EXISTS (SELECT 1 FROM staging.stg_bw_contingent_worker AS b
                  JOIN staging.stg_gen_cw_discrepancy_truth AS t
                    ON t.bw_worker_id = b.bw_worker_id AND t.discrepancy_code = 'CW08'
                  WHERE b.first_name = w.first_name AND b.last_name = w.last_name)
UNION ALL
SELECT c.person_id, 'hire not in the month after the last Bridgeway day, or more than 21 days later'
FROM conv AS c
JOIN staging.stg_bw_contingent_worker AS b
  ON b.bw_worker_id = c.bw_worker_id AND b.first_name = c.first_name AND b.last_name = c.last_name
JOIN last_day AS l ON l.bw_worker_id = b.bw_worker_id
WHERE c.converted_on <= l.last_day
   OR c.converted_on > l.last_day + INTERVAL 21 DAY
   OR DATE_TRUNC('month', c.converted_on) <> DATE_TRUNC('month', l.last_day + INTERVAL 1 DAY)
