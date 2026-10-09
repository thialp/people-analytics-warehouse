-- Reporting lines follow the org rules at every month-end:
--   * a people manager or director reports to someone at a HIGHER level
--   * an individual contributor reports to someone at the same level or higher
--   * apart from org leaders, people report to a manager in their own department
SELECT s.month_end_date, s.worker_id, s.grade, s.is_people_manager, s.department_id,
       m.worker_id AS manager_id, m.grade AS manager_grade, m.department_id AS manager_department_id
FROM intermediate.int_worker_month_end_snapshot AS s
JOIN intermediate.int_worker_month_end_snapshot AS m
  ON m.month_end_date = s.month_end_date AND m.worker_id = s.manager_worker_id
WHERE ((s.is_people_manager OR s.grade >= 7) AND m.grade <= s.grade)
   OR (NOT s.is_people_manager AND s.grade < 7 AND m.grade < s.grade)
   OR (s.leads_org_unit_id IS NULL AND m.department_id <> s.department_id)
