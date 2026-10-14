-- Summed across offices, the location walk must match the headcount walk for opening,
-- joiners (employee hires, contingent starts), each kind of leaver, conversions and closing
-- (headcount and FTE), every month and worker type. Two marts cut two ways, one answer.
WITH loc AS (
    SELECT month_end_date, worker_type,
           SUM(opening_headcount) AS opening, SUM(hires) + SUM(contingent_starts) AS joined,
           SUM(voluntary_terminations) AS vol, SUM(involuntary_terminations) AS invol,
           SUM(contingent_ends) AS ends, SUM(conversions_in) - SUM(conversions_out) AS conversions,
           SUM(closing_headcount) AS closing, SUM(closing_fte) AS closing_fte
    FROM marts.mart_location_headcount
    GROUP BY 1, 2
),
walk AS (
    SELECT month_end_date, worker_type,
           SUM(headcount) FILTER (WHERE movement_category = 'Opening')                   AS opening,
           SUM(headcount) FILTER (WHERE movement_category IN ('Hires', 'Starts'))        AS joined,
           -SUM(headcount) FILTER (WHERE movement_category = 'Voluntary Terminations')   AS vol,
           -SUM(headcount) FILTER (WHERE movement_category = 'Involuntary Terminations') AS invol,
           -SUM(headcount) FILTER (WHERE movement_category = 'Ends')                     AS ends,
           SUM(headcount) FILTER (WHERE movement_category = 'Conversions')               AS conversions,
           SUM(headcount) FILTER (WHERE movement_category = 'Closing')                   AS closing,
           SUM(fte)       FILTER (WHERE movement_category = 'Closing')                   AS closing_fte
    FROM marts.mart_headcount_fte_walk
    GROUP BY 1, 2
)
SELECT *
FROM loc FULL OUTER JOIN walk USING (month_end_date, worker_type)
WHERE loc.opening     IS DISTINCT FROM walk.opening
   OR loc.joined      IS DISTINCT FROM COALESCE(walk.joined, 0)
   OR loc.vol         IS DISTINCT FROM COALESCE(walk.vol, 0)
   OR loc.invol       IS DISTINCT FROM COALESCE(walk.invol, 0)
   OR loc.ends        IS DISTINCT FROM COALESCE(walk.ends, 0)
   OR loc.conversions IS DISTINCT FROM COALESCE(walk.conversions, 0)
   OR loc.closing     IS DISTINCT FROM walk.closing
   OR loc.closing_fte IS DISTINCT FROM walk.closing_fte
