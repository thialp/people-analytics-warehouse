-- Opening and Closing must equal an independent count of the month-end
-- snapshot, in headcount and FTE, for every month. Two marts built two ways
-- that agree are the evidence that neither one drops or double-counts people.
WITH walk AS (
    SELECT
        w.month_end_date,
        m.prior_month_end_date,
        SUM(CASE WHEN w.movement_category = 'Opening' THEN w.headcount END) AS opening_hc,
        SUM(CASE WHEN w.movement_category = 'Opening' THEN w.fte       END) AS opening_fte,
        SUM(CASE WHEN w.movement_category = 'Closing' THEN w.headcount END) AS closing_hc,
        SUM(CASE WHEN w.movement_category = 'Closing' THEN w.fte       END) AS closing_fte
    FROM marts.mart_headcount_fte_walk AS w
    JOIN marts.mart_dim_month AS m ON m.month_end_date = w.month_end_date
    GROUP BY ALL
),
snap AS (
    SELECT month_end_date, COUNT(*) AS hc, SUM(fte) AS fte
    FROM intermediate.int_worker_month_end_snapshot
    GROUP BY month_end_date
)
SELECT walk.*, cur.hc AS snapshot_closing_hc, pri.hc AS snapshot_opening_hc
FROM walk
LEFT JOIN snap AS cur ON cur.month_end_date = walk.month_end_date
LEFT JOIN snap AS pri ON pri.month_end_date = walk.prior_month_end_date
WHERE walk.closing_hc  IS DISTINCT FROM cur.hc
   OR walk.closing_fte IS DISTINCT FROM cur.fte
   OR walk.opening_hc  IS DISTINCT FROM pri.hc
   OR walk.opening_fte IS DISTINCT FROM pri.fte
