-- No job record starts before the hire date or runs past the termination date.
SELECT j.worker_id, j.job_record_id, j.effective_start_date, j.effective_end_date,
       w.original_hire_date, w.termination_date
FROM staging.stg_job_history AS j
JOIN staging.stg_worker AS w ON w.worker_id = j.worker_id
WHERE j.effective_start_date < w.original_hire_date
   OR (w.termination_date IS NOT NULL
       AND (j.effective_end_date IS NULL OR j.effective_end_date > w.termination_date))
