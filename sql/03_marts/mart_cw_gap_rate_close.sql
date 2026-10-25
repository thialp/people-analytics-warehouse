-- mart_cw_gap_rate_close
-- Grain: one row per month-end close x cost center (a department in a country), Jun 2021 to
-- Jun 2026: the gap rate's numerator and denominator, additive across any choice of function,
-- department and country.
--
--   contractors_working       working in Bridgeway on the close, by the cost center Bridgeway bills
--                             (the population; 11,941 on Jun 30, 2026)
--   contractors_working_keystone  active and started in Keystone (KPI 1's comparison), with the two
--                             one-sided counts behind the net difference
--   contractors_with_gap      contractors with at least one counted gap (not "Clears on its own"),
--                             by their group in mart_cw_gap_close; a contractor can have a gap
--                             without being in the population (Keystone only, ended in Bridgeway)
--   gap rate                  contractors_with_gap / contractors_working, against the 3% target
-- Executive officers' department (D-901) is excluded.
CREATE OR REPLACE TABLE marts.mart_cw_gap_rate_close AS
WITH pop AS (    -- grouped by Bridgeway's cost center (Keystone's for someone Bridgeway does not have working)
    SELECT month_end_date, COALESCE(bw_cost_center_id, ks_cost_center_id) AS cost_center_id,
           COUNT(*) FILTER (WHERE bw_working)                                      AS contractors_working,
           COUNT(*) FILTER (WHERE ks_working)                                      AS contractors_working_keystone,
           COUNT(*) FILTER (WHERE bw_working AND NOT ks_working)                   AS working_bridgeway_only,
           COUNT(*) FILTER (WHERE ks_working AND NOT bw_working)                   AS working_keystone_only
    FROM intermediate.int_cw_reconciliation_snapshot
    WHERE bw_working OR ks_working
    GROUP BY 1, 2
),
gaps AS (
    SELECT month_end_date, cost_center_id,
           COUNT(DISTINCT contractor_key) FILTER (WHERE is_counted)                  AS contractors_with_gap,
           COUNT(DISTINCT contractor_key)                                            AS contractors_with_any_gap,
           COUNT(*)                                                                  AS gaps,
           COUNT(*) FILTER (WHERE is_counted)                                        AS gaps_counted,
           COUNT(*) FILTER (WHERE NOT is_counted)                                    AS gaps_clear_on_own,
           COUNT(*) FILTER (WHERE is_counted AND NOT has_ticket)                     AS gaps_no_ticket,
           COUNT(*) FILTER (WHERE is_counted AND is_over_90_days)                    AS gaps_over_90_days,
           COUNT(*) FILTER (WHERE is_counted AND was_open_prior_close)               AS gaps_open_prior_close,
           COUNT(*) FILTER (WHERE fixed_day_after_close)                             AS gaps_fixed_day_after
    FROM marts.mart_cw_gap_close
    GROUP BY 1, 2
),
cells AS (
    SELECT month_end_date, cost_center_id FROM pop
    UNION SELECT month_end_date, cost_center_id FROM gaps
)
SELECT
    c.month_end_date,
    STRFTIME(c.month_end_date, '%b %Y')                                              AS close_label,
    r.is_latest_close,
    c.cost_center_id,
    cc.department_id,
    dep.department_name,
    dep.function_name,
    cc.country_code,
    co.country_name,
    COALESCE(p.contractors_working, 0)                                               AS contractors_working,
    COALESCE(p.contractors_working_keystone, 0)                                      AS contractors_working_keystone,
    COALESCE(p.working_bridgeway_only, 0)                                            AS working_bridgeway_only,
    COALESCE(p.working_keystone_only, 0)                                             AS working_keystone_only,
    COALESCE(g.contractors_with_gap, 0)                                              AS contractors_with_gap,
    COALESCE(g.contractors_with_any_gap, 0)                                          AS contractors_with_any_gap,
    COALESCE(g.gaps, 0)                                                              AS gaps,
    COALESCE(g.gaps_counted, 0)                                                      AS gaps_counted,
    COALESCE(g.gaps_clear_on_own, 0)                                                 AS gaps_clear_on_own,
    COALESCE(g.gaps_no_ticket, 0)                                                    AS gaps_no_ticket,
    COALESCE(g.gaps_over_90_days, 0)                                                 AS gaps_over_90_days,
    COALESCE(g.gaps_open_prior_close, 0)                                             AS gaps_open_prior_close,
    COALESCE(g.gaps_fixed_day_after, 0)                                              AS gaps_fixed_day_after,
    0.03                                                                             AS gap_rate_target,
    r.load_note
FROM cells AS c
JOIN intermediate.int_cw_close_run AS r USING (month_end_date)
LEFT JOIN pop AS p USING (month_end_date, cost_center_id)
LEFT JOIN gaps AS g USING (month_end_date, cost_center_id)
LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = c.cost_center_id
LEFT JOIN staging.stg_department AS dep ON dep.department_id = cc.department_id
LEFT JOIN staging.stg_country AS co ON co.country_code = cc.country_code
WHERE COALESCE(cc.department_id, '') <> 'D-901'
ORDER BY c.month_end_date, c.cost_center_id;
