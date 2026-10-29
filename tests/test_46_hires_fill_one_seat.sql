-- Release 6: position management is loaded at the report date and Core HR runs on to the data-through
-- date, so the two are compared as of the report date: what Core HR held on that day.
-- Every worker's first seat starts on their hire date: as an Initial assignment for
-- people already employed when history starts, as an External Hire for everyone hired
-- later. No other assignment is an External Hire.
WITH first_month_end AS (
    SELECT MIN(month_end_date) AS d FROM intermediate.int_month_end_calendar
),
firsts AS (
    SELECT worker_id, start_date, fill_type,
           ROW_NUMBER() OVER (PARTITION BY worker_id ORDER BY start_date) AS n
    FROM staging.stg_position_assignment
)
SELECT w.worker_id, w.original_hire_date, f.start_date, f.fill_type, 'first seat' AS problem
FROM staging.stg_worker AS w
CROSS JOIN first_month_end AS m
LEFT JOIN firsts AS f ON f.worker_id = w.worker_id AND f.n = 1
WHERE w.original_hire_date <= (SELECT report_as_of_date FROM staging.stg_report_calendar)
  AND (f.start_date IS DISTINCT FROM w.original_hire_date
   OR f.fill_type <> CASE WHEN w.original_hire_date <= m.d THEN 'Initial' ELSE 'External Hire' END)
UNION ALL
SELECT worker_id, NULL, start_date, fill_type, 'external hire after the first seat'
FROM firsts
WHERE n > 1 AND fill_type = 'External Hire'
