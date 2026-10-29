-- Release 6: the daily headcount counts people the same way as the month-end snapshot, so on every
-- month-end the two agree by department; it runs every day to the data-through date and no further;
-- and only days after the report date are open (not closed).
WITH snap AS (
    SELECT s.month_end_date, s.department_id, COUNT(*) AS employees
    FROM intermediate.int_worker_month_end_snapshot AS s
    WHERE NOT s.is_executive_officer
    GROUP BY ALL
),
snap_named AS (
    SELECT s.month_end_date, dep.department_name, s.employees
    FROM snap AS s JOIN staging.stg_department AS dep USING (department_id)
),
daily AS (
    SELECT as_of_date, department_name, employees FROM marts.mart_daily_headcount
),
cal AS (SELECT report_as_of_date, data_through_date FROM staging.stg_report_calendar)
SELECT 'month-end differs from the snapshot' AS problem,
       CAST(COALESCE(s.month_end_date, d.as_of_date) AS VARCHAR) || ' ' || COALESCE(s.department_name, d.department_name) AS detail
FROM snap_named AS s
FULL JOIN (SELECT * FROM daily WHERE as_of_date IN (SELECT month_end_date FROM intermediate.int_month_end_calendar)) AS d
  ON d.as_of_date = s.month_end_date AND d.department_name = s.department_name
WHERE s.employees IS DISTINCT FROM d.employees
UNION ALL
SELECT 'a day is missing', CAST(COUNT(DISTINCT as_of_date) AS VARCHAR)
FROM daily, cal
HAVING COUNT(DISTINCT as_of_date) <> DATEDIFF('day', (SELECT MIN(month_end_date) FROM intermediate.int_month_end_calendar), MAX(cal.data_through_date)) + 1
UNION ALL
SELECT 'runs past the data-through date', CAST(MAX(as_of_date) AS VARCHAR)
FROM daily HAVING MAX(as_of_date) > (SELECT data_through_date FROM cal)
UNION ALL
SELECT 'data-through date is before the report date', CAST(data_through_date AS VARCHAR)
FROM cal WHERE data_through_date < report_as_of_date
UNION ALL
SELECT 'is_closed disagrees with the report date', CAST(m.as_of_date AS VARCHAR)
FROM marts.mart_daily_headcount AS m, cal
WHERE m.is_closed <> (m.as_of_date <= cal.report_as_of_date)
