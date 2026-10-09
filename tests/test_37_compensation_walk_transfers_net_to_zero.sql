-- Transfers move people between groups at their opening value, so across all the
-- groups of a view they cancel: for every date pair and view, Transfers In + Transfers
-- Out = 0 in headcount, FTE and dollars. And no transfer ever appears in the Company
-- view, or without a reason.
SELECT from_month_end, to_month_end, view_name,
       SUM(headcount) AS hc, SUM(fte) AS fte, SUM(base_usd_nominal) AS bn, SUM(loaded_usd_constant) AS lc
FROM marts.mart_compensation_walk
WHERE step IN ('Transfers In', 'Transfers Out')
GROUP BY ALL
HAVING SUM(headcount) <> 0 OR SUM(fte) <> 0
    OR ABS(SUM(base_usd_nominal)) > 0.01 * COUNT(*) OR ABS(SUM(loaded_usd_constant)) > 0.01 * COUNT(*)
UNION ALL
SELECT from_month_end, to_month_end, view_name, NULL, NULL, NULL, NULL
FROM marts.mart_compensation_walk
WHERE step IN ('Transfers In', 'Transfers Out') AND (view_name = 'Company' OR movement_reason IS NULL)
