-- The workforce walk closes for Employees, for Contingent workers and for the Total, every
-- month: Opening + every movement = Closing. Conversions are the bridge between the two:
-- each month, the conversions out of Contingent equal the conversions into Employee, so the
-- Total is never moved by one; and every walk conversion is a person the warehouse can link
-- across the two systems (int_cw_conversion).
WITH by_type AS (
    SELECT month_end_date, worker_type,
           SUM(CASE WHEN movement_category = 'Closing' THEN -headcount ELSE headcount END) AS gap
    FROM marts.mart_headcount_fte_walk GROUP BY 1, 2
),
total AS (
    SELECT month_end_date,
           SUM(CASE WHEN movement_category = 'Closing' THEN -headcount ELSE headcount END) AS gap,
           SUM(headcount) FILTER (WHERE movement_category = 'Conversions')                  AS conversions_net,
           SUM(headcount) FILTER (WHERE movement_category = 'Conversions' AND worker_type = 'Employee') AS conv_in,
           -SUM(headcount) FILTER (WHERE movement_category = 'Conversions' AND worker_type = 'Contingent') AS conv_out
    FROM marts.mart_headcount_fte_walk GROUP BY 1
),
linked AS (
    SELECT month_end_date, COUNT(*) AS n FROM intermediate.int_cw_conversion WHERE is_walk_conversion GROUP BY 1
)
SELECT month_end_date, worker_type, 'does not close' AS problem FROM by_type WHERE gap <> 0
UNION ALL
SELECT month_end_date, 'Total', 'Total does not close' FROM total WHERE gap <> 0
UNION ALL
SELECT month_end_date, 'Total', 'conversions move the Total' FROM total WHERE COALESCE(conversions_net, 0) <> 0
UNION ALL
SELECT t.month_end_date, 'Total', 'conversions differ from the linked conversions'
FROM total AS t LEFT JOIN linked AS l USING (month_end_date)
WHERE COALESCE(t.conv_in, 0) <> COALESCE(l.n, 0) OR COALESCE(t.conv_out, 0) <> COALESCE(l.n, 0)
