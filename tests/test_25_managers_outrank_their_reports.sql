-- Reporting lines follow the org rules at every month-end:
--   * a people manager or director reports to someone at a HIGHER level
--   * an individual contributor reports to someone at the same level or higher
--   * apart from org leaders, people report to a manager in their own department, except on the
--     job records release 7 seeded on purpose (a person who kept their old manager after the
--     reorganization or a transfer); the answer key lists every one (test 93)
SELECT s.month_end_date, s.worker_id, s.grade, s.is_people_manager, s.department_id,
       m.worker_id AS manager_id, m.grade AS manager_grade, m.department_id AS manager_department_id
FROM intermediate.int_worker_month_end_snapshot AS s
JOIN intermediate.int_worker_month_end_snapshot AS m
  ON m.month_end_date = s.month_end_date AND m.worker_id = s.manager_worker_id
WHERE ((s.is_people_manager OR s.grade >= 7) AND m.grade <= s.grade)
   OR (NOT s.is_people_manager AND s.grade < 7 AND m.grade < s.grade)
   OR (s.leads_org_unit_id IS NULL AND m.department_id <> s.department_id
       AND NOT EXISTS (
           SELECT 1
           FROM staging.stg_job_history AS j
           JOIN staging.stg_gen_org_drift_truth AS t
             ON t.signal_code = 'S1' AND list_contains(string_split(t.job_record_ids, ';'), j.job_record_id)
           WHERE j.worker_id = s.worker_id
             AND s.month_end_date BETWEEN j.effective_start_date AND j.effective_end_date_filled))
