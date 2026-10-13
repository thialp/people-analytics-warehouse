-- A reuse candidate is a net-new seat approved while a seat it could have reused stood
-- vacant: the named seat was Open or Frozen on the approval date, in the same
-- department, job family and country, a grade within one, and vacant 90 days or more.
-- Only net-new seats are flagged, and the flag agrees with the count.
SELECT f.fill_id, f.seat_type, f.reuse_candidate, f.reuse_candidate_seats, f.reuse_candidate_position_id,
       h.status, h.status_since, f.requisition_approved_date
FROM marts.mart_position_fill AS f
LEFT JOIN intermediate.int_position_history AS h
  ON h.position_id = f.reuse_candidate_position_id
 AND f.requisition_approved_date BETWEEN h.effective_start_date AND h.effective_end_date_filled
LEFT JOIN staging.stg_job_profile AS jp ON jp.job_profile_id = f.job_profile_id
WHERE f.reuse_candidate <> (f.reuse_candidate_seats > 0)
   OR (f.reuse_candidate AND f.seat_type <> 'Net-new')
   OR (f.reuse_candidate AND (h.position_id IS NULL
                              OR h.status NOT IN ('Open', 'Frozen')
                              OR h.department_id <> f.department_id
                              OR h.job_family_code <> jp.job_family_code
                              OR h.country_code <> f.country_code
                              OR ABS(h.grade - f.grade) > 1
                              OR h.status_since > f.requisition_approved_date - INTERVAL 90 DAY
                              OR h.position_id = f.position_id))
