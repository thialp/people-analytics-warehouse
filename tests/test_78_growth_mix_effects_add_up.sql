-- The growth-mix decomposition is exact and tied to the warehouse: for every date pair and
-- group, the six Shapley effects add up to closing minus opening cost (and so do the six
-- sequential effects, by construction), to within a dollar of rounding; the opening and closing
-- cost are the employees' loaded run-rate (executive officers excluded) plus the contingent
-- run-rate on those dates, from the two snapshots; and each group's opening and closing
-- headcount are those snapshots' counts.
WITH sums AS (
    SELECT from_month_end, to_month_end, view_name, group_name,
           SUM(shapley_effect_usd)    FILTER (WHERE factor_order BETWEEN 1 AND 6) AS shapley,
           SUM(sequential_effect_usd) FILTER (WHERE factor_order BETWEEN 1 AND 6) AS sequential,
           MAX(shapley_effect_usd)    FILTER (WHERE factor_order = 0)             AS opening,
           MAX(shapley_effect_usd)    FILTER (WHERE factor_order = 7)             AS closing,
           MAX(opening_headcount) AS opening_headcount, MAX(closing_headcount) AS closing_headcount
    FROM marts.mart_workforce_cost_growth_mix GROUP BY ALL
),
cost AS (
    SELECT month_end_date, SUM(nom) AS nom, COUNT(*) AS heads FROM (
        SELECT month_end_date, loaded_usd_nominal AS nom
        FROM intermediate.int_worker_month_end_snapshot WHERE NOT is_executive_officer
        UNION ALL
        SELECT month_end_date, run_rate_usd_nominal FROM intermediate.int_cw_month_end_snapshot
    ) GROUP BY 1
)
SELECT from_month_end, to_month_end, view_name, group_name, 'effects do not add up to the change' AS problem
FROM sums
WHERE ABS(shapley - (closing - opening)) > 1 OR ABS(sequential - (closing - opening)) > 1
UNION ALL
SELECT s.from_month_end, s.to_month_end, s.view_name, s.group_name, 'company cost or headcount differs from the snapshots'
FROM sums AS s
JOIN cost AS c0 ON c0.month_end_date = s.from_month_end
JOIN cost AS c1 ON c1.month_end_date = s.to_month_end
WHERE s.view_name = 'Company'
  AND (ABS(s.opening - c0.nom) > 1 OR ABS(s.closing - c1.nom) > 1
       OR s.opening_headcount <> c0.heads OR s.closing_headcount <> c1.heads)
UNION ALL
SELECT from_month_end, to_month_end, 'Function', NULL, 'functions do not add up to the company'
FROM sums
GROUP BY from_month_end, to_month_end
HAVING ABS(SUM(opening) FILTER (WHERE view_name = 'Function') - SUM(opening) FILTER (WHERE view_name = 'Company')) > 1
    OR ABS(SUM(closing) FILTER (WHERE view_name = 'Function') - SUM(closing) FILTER (WHERE view_name = 'Company')) > 1
