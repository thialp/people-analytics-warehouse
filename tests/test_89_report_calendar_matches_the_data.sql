-- Report calendar (release 5): the as-of date is the last month-end the data covers, the
-- window holds five history years and the forward year (24 quarters, no gap), the offsets
-- count from the as-of date, and only the forward year's quarters are after it. If the data
-- and the calendar ever disagree, every label on every dashboard would be wrong.
WITH cal AS (SELECT * FROM staging.stg_report_calendar),
q AS (SELECT * FROM staging.stg_report_quarter)
SELECT 'not one calendar row' AS problem, CAST(COUNT(*) AS VARCHAR) AS detail
FROM cal HAVING COUNT(*) <> 1
UNION ALL
SELECT 'as-of is not the last month-end', CAST(c.report_as_of_date AS VARCHAR)
FROM cal AS c WHERE c.report_as_of_date <> (SELECT MAX(month_end_date) FROM intermediate.int_month_end_calendar)
UNION ALL
SELECT 'window is not 24 quarters', CAST(COUNT(*) AS VARCHAR) FROM q HAVING COUNT(*) <> 24
UNION ALL
SELECT 'quarter offsets do not run -19 to 4', CAST(MIN(quarter_offset) AS VARCHAR) || ' to ' || CAST(MAX(quarter_offset) AS VARCHAR)
FROM q HAVING MIN(quarter_offset) <> -19 OR MAX(quarter_offset) <> 4 OR COUNT(DISTINCT quarter_offset) <> 24
UNION ALL
SELECT 'quarter 0 does not end on the as-of date', q.quarter_label
FROM q, cal AS c WHERE q.quarter_offset = 0 AND q.quarter_end_date <> c.report_as_of_date
UNION ALL
SELECT 'fy_offset or is_forward disagrees with the calendar', q.quarter_label
FROM q, cal AS c
WHERE q.fy_offset <> q.fiscal_year - c.current_fiscal_year
   OR q.is_forward <> (q.quarter_end_date > c.report_as_of_date)
   OR q.is_forward <> (q.fiscal_year = c.forward_fiscal_year)
UNION ALL
SELECT 'quarters overlap or leave a gap', a.quarter_label
FROM q AS a JOIN q AS b ON b.quarter_offset = a.quarter_offset + 1
WHERE b.quarter_start_date <> a.quarter_end_date + INTERVAL 1 DAY
UNION ALL
SELECT 'history window does not start on the first quarter', CAST(c.history_start_date AS VARCHAR)
FROM cal AS c WHERE c.history_start_date <> (SELECT MIN(quarter_start_date) FROM q)
