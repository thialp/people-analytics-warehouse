-- Company-wide, transfers only move people between departments: every month,
-- Transfers In and Transfers Out cancel out exactly in headcount and dollars.
SELECT
    month_end_date,
    SUM(headcount)           AS net_headcount,
    SUM(loaded_usd_nominal)  AS net_loaded_nominal,
    SUM(loaded_usd_constant) AS net_loaded_constant
FROM marts.mart_workforce_cost_bridge
WHERE driver IN ('Transfers In', 'Transfers Out')
GROUP BY month_end_date
HAVING SUM(headcount) <> 0
    OR ABS(SUM(loaded_usd_nominal))  > 1
    OR ABS(SUM(loaded_usd_constant)) > 1
