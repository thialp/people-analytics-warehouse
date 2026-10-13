-- Job level only changes through a promotion, demotion, leadership succession or
-- the reorganization. A promotion is exactly one level up and a demotion exactly
-- one level down (successions and the reorg may step a new leader up further).
WITH ordered AS (
    SELECT worker_id, effective_start_date, action_reason, grade,
           LAG(grade) OVER (PARTITION BY worker_id ORDER BY effective_start_date) AS prior_grade
    FROM staging.stg_job_history
)
SELECT worker_id, effective_start_date, action_reason, prior_grade, grade
FROM ordered
WHERE prior_grade IS NOT NULL
  AND ((action_reason = 'Promotion' AND grade <> prior_grade + 1)
    OR (action_reason = 'Demotion'  AND grade <> prior_grade - 1)
    OR (action_reason IN ('Succession', 'Reorganization') AND grade < prior_grade)
    OR (grade <> prior_grade AND action_reason NOT IN ('Promotion', 'Demotion', 'Succession', 'Reorganization')))
