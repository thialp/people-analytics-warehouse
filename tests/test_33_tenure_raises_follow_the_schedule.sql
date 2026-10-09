-- Tenure raises land on the hire anniversary and never exceed the schedule's raise
-- for the years completed (they can be smaller when pay reaches the top of range).
WITH comp AS (
    SELECT worker_id, effective_start_date, action_reason, base_salary_annual_local,
           LAG(base_salary_annual_local) OVER (PARTITION BY worker_id ORDER BY effective_start_date) AS prior_salary
    FROM staging.stg_compensation_history
)
SELECT c.worker_id, c.effective_start_date, c.prior_salary, c.base_salary_annual_local, t.increase_pct
FROM comp AS c
JOIN staging.stg_worker AS w USING (worker_id)
LEFT JOIN staging.stg_tenure_increase AS t
       ON YEAR(c.effective_start_date) - YEAR(w.original_hire_date) BETWEEN t.tenure_year_from AND t.tenure_year_to
WHERE c.action_reason = 'Tenure Increase'
  AND (MONTH(c.effective_start_date) <> MONTH(w.original_hire_date)
       OR (DAY(c.effective_start_date) <> DAY(w.original_hire_date)
           AND NOT (MONTH(w.original_hire_date) = 2 AND DAY(w.original_hire_date) = 29))
       OR c.base_salary_annual_local <= c.prior_salary
       OR c.base_salary_annual_local > c.prior_salary * (1 + t.increase_pct) + 50)
