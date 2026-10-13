-- The walk can be chained across any date range only if each month's Closing
-- equals the next month's Opening, slice by slice.
WITH closing AS (
    SELECT w.month_end_date, w.department_id, w.country_code, w.job_family_code, w.grade,
           SUM(w.headcount) AS hc, SUM(w.fte) AS fte
    FROM marts.mart_headcount_fte_walk AS w
    WHERE w.movement_category = 'Closing'
    GROUP BY ALL
),
opening AS (
    SELECT m.prior_month_end_date AS month_end_date, w.department_id, w.country_code, w.job_family_code, w.grade,
           SUM(w.headcount) AS hc, SUM(w.fte) AS fte
    FROM marts.mart_headcount_fte_walk AS w
    JOIN marts.mart_dim_month AS m ON m.month_end_date = w.month_end_date
    WHERE w.movement_category = 'Opening'
    GROUP BY ALL
)
SELECT
    COALESCE(c.month_end_date, o.month_end_date) AS month_end_date,
    COALESCE(c.department_id, o.department_id)   AS department_id,
    c.hc AS closing_hc, o.hc AS next_opening_hc,
    c.fte AS closing_fte, o.fte AS next_opening_fte
FROM closing AS c
FULL OUTER JOIN opening AS o
  ON  o.month_end_date  = c.month_end_date
 AND o.department_id    = c.department_id
 AND o.country_code     = c.country_code
 AND o.job_family_code  = c.job_family_code
 AND o.grade            = c.grade
-- the last month has no next month to open, and the month before the first
-- walked month has no closing line (it is test 15's job to check that opening)
WHERE COALESCE(c.month_end_date, o.month_end_date) <  (SELECT MAX(month_end_date) FROM marts.mart_dim_month)
  AND COALESCE(c.month_end_date, o.month_end_date) >= (SELECT MIN(month_end_date) FROM marts.mart_dim_month)
  AND (c.hc IS DISTINCT FROM o.hc OR c.fte IS DISTINCT FROM o.fte)
