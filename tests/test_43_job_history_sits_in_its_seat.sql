-- Release 6: position management is loaded at the report date and Core HR runs on to the data-through
-- date, so the two are compared as of the report date: what Core HR held on that day.
-- Every job record names the seat the worker holds: exactly one of the worker's
-- assignments covers the record's start date, and it is on the same position.
SELECT
    j.job_record_id,
    j.worker_id,
    j.effective_start_date,
    j.position_id,
    COUNT(a.assignment_id)                                     AS covering_assignments,
    STRING_AGG(a.position_id, ', ')                            AS assigned_positions
FROM staging.stg_job_history AS j
LEFT JOIN staging.stg_position_assignment AS a
  ON a.worker_id = j.worker_id
 AND j.effective_start_date BETWEEN a.start_date AND a.end_date_filled
WHERE j.effective_start_date <= (SELECT report_as_of_date FROM staging.stg_report_calendar)
GROUP BY ALL
HAVING COUNT(a.assignment_id) <> 1
    OR MAX(a.position_id) <> j.position_id
