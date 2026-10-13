-- The two marts must tell the same story: the walk's closing run-rate equals the
-- snapshot mart's total for the same month, company-wide.
WITH walk AS (
    SELECT month_end_date, SUM(headcount) AS headcount,
           SUM(loaded_usd_nominal) AS loaded_nominal, SUM(loaded_usd_constant) AS loaded_constant
    FROM marts.mart_workforce_cost_bridge
    WHERE driver = 'Closing Run-Rate'
    GROUP BY month_end_date
),
snapshot AS (
    SELECT month_end_date, SUM(headcount) AS headcount,
           SUM(loaded_usd_nominal) AS loaded_nominal, SUM(loaded_usd_constant) AS loaded_constant,
           COUNT(*) AS snapshot_rows
    FROM marts.mart_workforce_cost_snapshot
    GROUP BY month_end_date
)
SELECT w.month_end_date, w.headcount, s.headcount AS snapshot_headcount,
       w.loaded_nominal, s.loaded_nominal AS snapshot_loaded_nominal
FROM walk AS w
JOIN snapshot AS s ON s.month_end_date = w.month_end_date
WHERE w.headcount <> s.headcount
   OR ABS(w.loaded_nominal  - s.loaded_nominal)  > 0.01 * s.snapshot_rows
   OR ABS(w.loaded_constant - s.loaded_constant) > 0.01 * s.snapshot_rows
