-- mart_cw_reconciliation
-- Grain: one row per month-end x function x supplier x discrepancy type.
--
-- The trend: how many contingent workers carry each kind of discrepancy, how many are new this
-- month and how old the rest are, beside the population each system shows (working in Bridgeway,
-- working in Keystone), so a share can be taken at any roll-up. Two row types, never summed
-- together (filter row_type in every calculation):
--
--   row_type 'Population'    one per month-end x function x supplier: cw_working_bridgeway,
--                            cw_working_keystone, workers_with_any_discrepancy
--   row_type 'Discrepancy'   one per month-end x function x supplier x type: workers_affected,
--                            new_this_month, and the age bands
CREATE OR REPLACE TABLE marts.mart_cw_reconciliation AS
WITH disc AS (
    SELECT x.month_end_date, x.discrepancy_code, x.identity_id, x.since_date, x.age_days,
           COALESCE(sp.supplier_name, 'Unknown')                    AS supplier_name,
           COALESCE(dep.function_name, 'Unknown')                   AS function_name
    FROM intermediate.int_cw_discrepancy AS x
    LEFT JOIN intermediate.int_cw_identity_resolution AS i ON i.identity_id = x.identity_id
    LEFT JOIN staging.stg_bw_supplier AS sp ON sp.supplier_id = i.supplier_id
    LEFT JOIN intermediate.int_cw_reconciliation_snapshot AS r
           ON r.month_end_date = x.month_end_date AND r.identity_id = x.identity_id
    LEFT JOIN (SELECT service_order_id, ARG_MAX(cost_center_code, revision_no) AS cost_center_id
               FROM staging.stg_bw_service_order_revision GROUP BY 1) AS oc ON oc.service_order_id = x.service_order_id
    LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = COALESCE(r.bw_cost_center_id, r.ks_cost_center_id, oc.cost_center_id)
    LEFT JOIN staging.stg_department AS dep ON dep.department_id = cc.department_id
),
flagged AS (    -- workers with at least one discrepancy that is more than a change in transit
    SELECT DISTINCT month_end_date, identity_id FROM intermediate.int_cw_discrepancy WHERE discrepancy_code <> 'CW00'
),
pop AS (
    SELECT r.month_end_date,
           COALESCE(dep.function_name, 'Unknown')                   AS function_name,
           COALESCE(sp.supplier_name, 'Unknown')                    AS supplier_name,
           COUNT(*) FILTER (WHERE r.bw_working)                     AS cw_working_bridgeway,
           COUNT(*) FILTER (WHERE r.ks_working)                     AS cw_working_keystone,
           COUNT(DISTINCT f.identity_id)                            AS workers_with_any_discrepancy
    FROM intermediate.int_cw_reconciliation_snapshot AS r
    LEFT JOIN flagged AS f ON f.month_end_date = r.month_end_date AND f.identity_id = r.identity_id
    LEFT JOIN staging.stg_bw_supplier AS sp ON sp.supplier_id = r.supplier_id
    LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = COALESCE(r.bw_cost_center_id, r.ks_cost_center_id)
    LEFT JOIN staging.stg_department AS dep ON dep.department_id = cc.department_id
    GROUP BY ALL
)
SELECT p.month_end_date, cal.fiscal_year, cal.fiscal_quarter_label, 'Population' AS row_type,
       p.function_name, p.supplier_name, NULL AS discrepancy_code, NULL AS discrepancy_name, NULL AS severity,
       NULL AS who_can_fix_it,
       p.cw_working_bridgeway, p.cw_working_keystone, p.workers_with_any_discrepancy,
       NULL AS workers_affected, NULL AS new_this_month, NULL AS aged_0_7, NULL AS aged_8_30, NULL AS aged_31_90,
       NULL AS aged_over_90
FROM pop AS p JOIN intermediate.int_month_end_calendar AS cal USING (month_end_date)
UNION ALL
SELECT x.month_end_date, cal.fiscal_year, cal.fiscal_quarter_label, 'Discrepancy',
       x.function_name, x.supplier_name, x.discrepancy_code, t.discrepancy_name, t.severity, t.who_can_fix_it,
       NULL, NULL, NULL,
       COUNT(DISTINCT x.identity_id),
       COUNT(DISTINCT x.identity_id) FILTER (WHERE x.since_date > cal.month_end_date - INTERVAL 1 MONTH),
       COUNT(DISTINCT x.identity_id) FILTER (WHERE x.age_days <= 7),
       COUNT(DISTINCT x.identity_id) FILTER (WHERE x.age_days BETWEEN 8 AND 30),
       COUNT(DISTINCT x.identity_id) FILTER (WHERE x.age_days BETWEEN 31 AND 90),
       COUNT(DISTINCT x.identity_id) FILTER (WHERE x.age_days > 90)
FROM disc AS x
JOIN intermediate.int_month_end_calendar AS cal USING (month_end_date)
JOIN staging.stg_cw_discrepancy_type AS t ON t.discrepancy_code = x.discrepancy_code
GROUP BY x.month_end_date, cal.fiscal_year, cal.fiscal_quarter_label, x.function_name, x.supplier_name,
         x.discrepancy_code, t.discrepancy_name, t.severity, t.who_can_fix_it
ORDER BY 1, 4 DESC, 5, 6, 7;
