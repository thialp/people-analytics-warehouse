-- Plan versus actual carries the contingent workforce exactly: for every plan version and
-- quarter, the actual contingent headcount summed over cost centers is the number Bridgeway
-- counted on the quarter-end (int_cw_month_end_snapshot), and the actual spend run-rate at
-- constant FX is theirs to the dollar; no contingent worker falls outside a plan line. At the
-- plan's FX the spend uses the same rate date as the planned spend, so a version's actual can
-- differ from the constant figure only by currency.
WITH snap AS (
    SELECT month_end_date AS quarter_end_date, COUNT(*) AS cw, SUM(run_rate_usd_constant) AS usd_constant
    FROM intermediate.int_cw_month_end_snapshot
    WHERE month_end_date IN (SELECT DISTINCT quarter_end_date FROM marts.mart_plan_vs_actual)
    GROUP BY 1
),
mart AS (
    SELECT plan_version, quarter_end_date,
           SUM(actual_cw_headcount) AS cw, SUM(actual_cw_spend_usd_constant) AS usd_constant,
           SUM(actual_cw_spend_usd_plan_fx) AS usd_plan_fx
    FROM marts.mart_plan_vs_actual GROUP BY 1, 2
)
SELECT m.plan_version, m.quarter_end_date, 'contingent headcount differs from the snapshot' AS problem
FROM mart AS m JOIN snap AS s USING (quarter_end_date) WHERE m.cw <> s.cw
UNION ALL
SELECT m.plan_version, m.quarter_end_date, 'contingent spend at constant FX differs from the snapshot'
FROM mart AS m JOIN snap AS s USING (quarter_end_date) WHERE ABS(m.usd_constant - s.usd_constant) > 1
UNION ALL
SELECT plan_version, quarter_end_date, 'contingent workers with no spend at plan FX, or the reverse'
FROM marts.mart_plan_vs_actual
WHERE (actual_cw_headcount = 0) <> (actual_cw_spend_usd_plan_fx = 0)
