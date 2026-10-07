-- Internal moves only relocate people between slices. Company-wide, every
-- month, moves in and moves out cancel exactly, in headcount and FTE, for
-- every reason (a transfer out of one department is a transfer into another).
SELECT
    month_end_date,
    movement_reason,
    SUM(headcount) AS net_headcount,
    SUM(fte)       AS net_fte
FROM marts.mart_headcount_fte_walk
WHERE movement_category IN ('Internal Moves In', 'Internal Moves Out')
GROUP BY month_end_date, movement_reason
HAVING SUM(headcount) <> 0
    OR SUM(fte) <> 0
