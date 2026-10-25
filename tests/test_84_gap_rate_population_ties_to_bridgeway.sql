-- The gap rate's denominator is the contractors working in Bridgeway on the close (11,941 on
-- Jun 30, 2026), its numerator the contractors with a counted gap in mart_cw_gap_close; the
-- gap counts tie too. No group can be double counted: the cells add up to the company.
WITH working AS (
    SELECT s.month_end_date, COUNT(*) AS n
    FROM intermediate.int_cw_reconciliation_snapshot AS s
    LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = s.bw_cost_center_id
    WHERE s.bw_working AND COALESCE(cc.department_id, '') <> 'D-901'
    GROUP BY 1
),
rate AS (
    SELECT month_end_date, SUM(contractors_working) AS working, SUM(contractors_with_gap) AS with_gap,
           SUM(gaps) AS gaps, SUM(gaps_no_ticket) AS no_ticket
    FROM marts.mart_cw_gap_rate_close GROUP BY 1
),
gap AS (
    SELECT month_end_date, COUNT(DISTINCT contractor_key) FILTER (WHERE is_counted) AS with_gap, COUNT(*) AS gaps,
           COUNT(*) FILTER (WHERE is_counted AND NOT has_ticket) AS no_ticket
    FROM marts.mart_cw_gap_close GROUP BY 1
)
SELECT r.month_end_date, w.n AS working_bridgeway, r.working, g.with_gap, r.with_gap AS rate_with_gap, g.gaps, r.gaps AS rate_gaps
FROM rate AS r
JOIN working AS w USING (month_end_date)
JOIN gap AS g USING (month_end_date)
WHERE r.working <> w.n OR r.with_gap <> g.with_gap OR r.gaps <> g.gaps OR r.no_ticket <> g.no_ticket
UNION ALL
SELECT DATE '2026-06-30', NULL, SUM(contractors_working), NULL, NULL, NULL, NULL
FROM marts.mart_cw_gap_rate_close WHERE month_end_date = DATE '2026-06-30'
HAVING SUM(contractors_working) <> 11941
