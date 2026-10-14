-- The contingent side of the headcount walk is the Bridgeway month-end snapshot, moved: every
-- month the walk's contingent Opening equals the workers counted at the prior month-end and
-- its Closing those counted at this one; and the snapshot has one row per worker per month-end.
WITH walk AS (
    SELECT w.month_end_date, m.prior_month_end_date,
           SUM(w.headcount) FILTER (WHERE w.movement_category = 'Opening') AS opening,
           SUM(w.headcount) FILTER (WHERE w.movement_category = 'Closing') AS closing
    FROM marts.mart_headcount_fte_walk AS w
    JOIN marts.mart_dim_month AS m USING (month_end_date)
    WHERE w.worker_type = 'Contingent'
    GROUP BY ALL
),
snap AS (
    SELECT month_end_date, COUNT(*) AS n, COUNT(DISTINCT bw_worker_id) AS workers
    FROM intermediate.int_cw_month_end_snapshot GROUP BY 1
)
SELECT walk.month_end_date, 'walk does not tie to the snapshot' AS problem
FROM walk
LEFT JOIN snap AS cur ON cur.month_end_date = walk.month_end_date
LEFT JOIN snap AS pri ON pri.month_end_date = walk.prior_month_end_date
WHERE walk.closing IS DISTINCT FROM cur.n OR COALESCE(walk.opening, 0) IS DISTINCT FROM COALESCE(pri.n, 0)
UNION ALL
SELECT month_end_date, 'a worker twice on one month-end' FROM snap WHERE n <> workers
