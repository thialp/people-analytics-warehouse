-- Summed across offices, the location walk must match the company headcount
-- walk for opening, hires, both termination types and closing (headcount and
-- FTE), every month. Two marts cut two ways, one answer.
WITH loc AS (
    SELECT month_end_date,
           SUM(opening_headcount) AS opening, SUM(hires) AS hires,
           SUM(voluntary_terminations) AS vol, SUM(involuntary_terminations) AS invol,
           SUM(closing_headcount) AS closing, SUM(closing_fte) AS closing_fte
    FROM marts.mart_location_headcount
    GROUP BY 1
),
walk AS (
    SELECT month_end_date,
           SUM(headcount) FILTER (WHERE movement_category = 'Opening')                   AS opening,
           SUM(headcount) FILTER (WHERE movement_category = 'Hires')                     AS hires,
           -SUM(headcount) FILTER (WHERE movement_category = 'Voluntary Terminations')   AS vol,
           -SUM(headcount) FILTER (WHERE movement_category = 'Involuntary Terminations') AS invol,
           SUM(headcount) FILTER (WHERE movement_category = 'Closing')                   AS closing,
           SUM(fte)       FILTER (WHERE movement_category = 'Closing')                   AS closing_fte
    FROM marts.mart_headcount_fte_walk
    GROUP BY 1
)
SELECT *
FROM loc FULL OUTER JOIN walk USING (month_end_date)
WHERE loc.opening     IS DISTINCT FROM walk.opening
   OR loc.hires       IS DISTINCT FROM walk.hires
   OR loc.vol         IS DISTINCT FROM COALESCE(walk.vol, 0)
   OR loc.invol       IS DISTINCT FROM COALESCE(walk.invol, 0)
   OR loc.closing     IS DISTINCT FROM walk.closing
   OR loc.closing_fte IS DISTINCT FROM walk.closing_fte
