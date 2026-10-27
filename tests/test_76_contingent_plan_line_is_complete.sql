-- The workforce plan's contingent line is complete and plausible: every cost center with
-- contingent workers on a quarter end (as Bridgeway held it that day) has a plan line in every
-- version covering that quarter; planned headcount and spend are never negative and spend is
-- zero exactly when headcount is; and each version's total stays within 20% of the quarter's
-- actual contingent headcount (a plan that far off would be a broken generator, not a bad plan).
-- Release 5: only quarters up to the report date have actuals; the forward budget is checked by test 90.
WITH qe AS (SELECT DISTINCT quarter_end_date FROM staging.stg_workforce_plan
            WHERE quarter_end_date <= (SELECT report_as_of_date FROM staging.stg_report_calendar)),
actual AS (
    SELECT q.quarter_end_date, r.cost_center_code AS cost_center_id, COUNT(DISTINCT o.bw_worker_id) AS cw
    FROM qe AS q
    JOIN staging.stg_bw_service_order_revision AS r
      ON r.effective_start_date <= q.quarter_end_date
     AND COALESCE(r.effective_end_date, DATE '9999-12-31') >= q.quarter_end_date
     AND r.status IN ('Approved', 'Closed')
     AND r.assignment_start_date <= q.quarter_end_date AND r.assignment_end_date >= q.quarter_end_date
    JOIN staging.stg_bw_service_order AS o USING (service_order_id)
    GROUP BY ALL
),
versions AS (SELECT DISTINCT plan_version, quarter_end_date FROM staging.stg_workforce_plan),
totals AS (
    SELECT p.plan_version, p.quarter_end_date, SUM(p.planned_cw_headcount) AS planned,
           (SELECT SUM(cw) FROM actual AS a WHERE a.quarter_end_date = p.quarter_end_date) AS actual
    FROM staging.stg_workforce_plan AS p WHERE p.quarter_end_date IN (SELECT quarter_end_date FROM qe) GROUP BY ALL
)
SELECT v.plan_version, a.cost_center_id, a.quarter_end_date, 'contingent workers but no plan line' AS problem
FROM actual AS a
JOIN versions AS v USING (quarter_end_date)
LEFT JOIN staging.stg_workforce_plan AS p
  ON p.plan_version = v.plan_version AND p.quarter_end_date = a.quarter_end_date AND p.cost_center_id = a.cost_center_id
WHERE p.plan_version IS NULL
UNION ALL
SELECT plan_version, cost_center_id, quarter_end_date, 'negative, or spend without headcount (or the reverse)'
FROM staging.stg_workforce_plan
WHERE planned_cw_headcount < 0 OR planned_cw_spend_usd < 0
   OR (planned_cw_headcount = 0) <> (planned_cw_spend_usd = 0)
UNION ALL
SELECT plan_version, NULL, quarter_end_date, 'version total more than 20% from the actual'
FROM totals WHERE ABS(planned - actual) > 0.20 * actual
