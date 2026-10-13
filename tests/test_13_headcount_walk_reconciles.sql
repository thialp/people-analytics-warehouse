-- Headcount and FTE walk, the core control: for every slice
-- (department x country x job family x grade) and every month,
--   Opening + Hires + Terminations + Internal Moves + FTE Changes = Closing
-- exactly, in headcount and in FTE.
WITH totals AS (
    SELECT
        month_end_date, department_id, country_code, job_family_code, grade,
        SUM(CASE WHEN movement_category = 'Closing' THEN -headcount ELSE headcount END) AS hc_gap,
        SUM(CASE WHEN movement_category = 'Closing' THEN -fte       ELSE fte       END) AS fte_gap
    FROM marts.mart_headcount_fte_walk
    GROUP BY ALL
)
SELECT *
FROM totals
WHERE hc_gap <> 0
   OR fte_gap <> 0
