-- Months chain together: a department's closing run-rate for one month is its
-- opening run-rate for the next. This is what lets Tableau walk across any range
-- of months by summing monthly drivers.
WITH closing AS (
    SELECT department_id, month_end_date, headcount, loaded_usd_nominal, loaded_usd_constant
    FROM marts.mart_workforce_cost_bridge
    WHERE driver = 'Closing Run-Rate'
),
opening AS (
    SELECT department_id, prior_month_end_date AS month_end_date, headcount, loaded_usd_nominal, loaded_usd_constant
    FROM marts.mart_workforce_cost_bridge
    WHERE driver = 'Opening Run-Rate'
)
SELECT
    COALESCE(c.department_id, o.department_id)   AS department_id,
    COALESCE(c.month_end_date, o.month_end_date) AS month_end_date,
    c.headcount AS closing_headcount, o.headcount AS next_opening_headcount,
    c.loaded_usd_nominal AS closing_loaded_nominal, o.loaded_usd_nominal AS next_opening_loaded_nominal
FROM closing AS c
FULL OUTER JOIN opening AS o
  ON o.department_id = c.department_id
 AND o.month_end_date = c.month_end_date
WHERE COALESCE(c.month_end_date, o.month_end_date) < (SELECT MAX(month_end_date) FROM marts.mart_workforce_cost_bridge)
  AND COALESCE(c.month_end_date, o.month_end_date) > (SELECT MIN(prior_month_end_date) FROM marts.mart_workforce_cost_bridge)
  AND (COALESCE(c.headcount, 0) <> COALESCE(o.headcount, 0)
       OR ABS(COALESCE(c.loaded_usd_nominal, 0)  - COALESCE(o.loaded_usd_nominal, 0))  > 0.01
       OR ABS(COALESCE(c.loaded_usd_constant, 0) - COALESCE(o.loaded_usd_constant, 0)) > 0.01)
