-- Forward budget (release 5): the year after the as-of date has exactly one plan version, its
-- Budget, approved on the date the calendar names (May 15 before the as-of date, so it was known
-- on the report date) and covering all four quarters for every cost center active in the last
-- fiscal year. No reforecast exists for it, and it never reaches the plan-vs-actual mart, which
-- compares plans with what happened.
WITH cal AS (SELECT * FROM staging.stg_report_calendar),
fwd AS (SELECT p.* FROM staging.stg_workforce_plan AS p, cal AS c WHERE p.fiscal_year = c.forward_fiscal_year),
last_fy AS (
    SELECT DISTINCT p.cost_center_id FROM staging.stg_workforce_plan AS p, cal AS c
    WHERE p.fiscal_year = c.current_fiscal_year AND p.version_type = 'Budget'
      AND (p.planned_ending_headcount > 0 OR p.planned_net_new > 0 OR p.planned_backfills > 0)
)
SELECT 'forward version other than its budget' AS problem, f.plan_version AS detail
FROM fwd AS f, cal AS c WHERE f.plan_version <> c.forward_budget_version OR f.version_type <> 'Budget'
UNION ALL
SELECT 'forward budget not dated on the calendar budget date', CAST(f.version_date AS VARCHAR)
FROM fwd AS f, cal AS c WHERE f.version_date <> c.forward_budget_date OR f.version_date > c.report_as_of_date
UNION ALL
SELECT 'cost center without four forward quarters', l.cost_center_id
FROM last_fy AS l LEFT JOIN fwd AS f USING (cost_center_id)
GROUP BY l.cost_center_id HAVING COUNT(DISTINCT f.fiscal_quarter) <> 4
UNION ALL
SELECT 'forward row reached the plan-vs-actual mart', CAST(m.fiscal_year AS VARCHAR)
FROM marts.mart_plan_vs_actual AS m, cal AS c WHERE m.fiscal_year >= c.forward_fiscal_year
UNION ALL
SELECT 'negative forward plan', f.cost_center_id
FROM fwd AS f WHERE f.planned_net_new < 0 OR f.planned_backfills < 0 OR f.planned_ending_headcount < 0
   OR f.planned_cw_headcount < 0 OR f.planned_cw_spend_usd < 0
