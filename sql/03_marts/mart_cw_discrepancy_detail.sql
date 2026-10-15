-- mart_cw_discrepancy_detail
-- Grain: one row per month-end x discrepancy x worker (or order, or timesheet), for the latest
-- 13 month-ends: the work list. Who is affected, what disagrees, since when, why the warehouse
-- thinks so (evidence), how serious it is and who can fix it. The warehouse cannot change either
-- system; it flags, the owner fixes the source.
CREATE OR REPLACE TABLE marts.mart_cw_discrepancy_detail AS
WITH months AS (
    SELECT month_end_date FROM intermediate.int_month_end_calendar
    QUALIFY ROW_NUMBER() OVER (ORDER BY month_end_date DESC) <= 13
),
place AS (    -- where the person sits: Bridgeway's cost center, else Keystone's
    SELECT month_end_date, identity_id, COALESCE(bw_cost_center_id, ks_cost_center_id) AS cost_center_id,
           bw_manager_worker_id, ks_manager_worker_id
    FROM intermediate.int_cw_reconciliation_snapshot
),
order_cc AS (
    SELECT service_order_id, ARG_MAX(cost_center_code, revision_no) AS cost_center_id
    FROM staging.stg_bw_service_order_revision GROUP BY 1
)
SELECT
    d.month_end_date,
    d.discrepancy_code,
    t.discrepancy_name,
    t.severity,
    t.who_can_fix_it,
    d.root_cause_code,
    rt.discrepancy_name                                                    AS root_cause_name,
    d.identity_id,
    d.bw_worker_id,
    d.person_id,
    i.first_name || ' ' || i.last_name                                     AS worker_name,
    i.cw_type,
    i.match_confidence,
    s.supplier_name,
    COALESCE(p.cost_center_id, oc.cost_center_id)                          AS cost_center_id,
    cc.department_id,
    dep.department_name,
    dep.function_name,
    cc.country_code,
    COALESCE(p.bw_manager_worker_id, p.ks_manager_worker_id)              AS manager_worker_id,
    d.fields_affected,
    d.since_date,
    d.age_days,
    CASE WHEN d.age_days <= 7 THEN '0-7 days' WHEN d.age_days <= 30 THEN '8-30 days'
         WHEN d.age_days <= 90 THEN '31-90 days' ELSE 'Over 90 days' END   AS age_band,
    d.service_order_id,
    d.feed_event_id,
    d.timesheet_id,
    d.evidence
FROM intermediate.int_cw_discrepancy AS d
JOIN months USING (month_end_date)
JOIN staging.stg_cw_discrepancy_type AS t ON t.discrepancy_code = d.discrepancy_code
LEFT JOIN staging.stg_cw_discrepancy_type AS rt ON rt.discrepancy_code = d.root_cause_code
LEFT JOIN intermediate.int_cw_identity_resolution AS i ON i.identity_id = d.identity_id
LEFT JOIN staging.stg_bw_supplier AS s ON s.supplier_id = i.supplier_id
LEFT JOIN place AS p ON p.month_end_date = d.month_end_date AND p.identity_id = d.identity_id
LEFT JOIN order_cc AS oc ON oc.service_order_id = d.service_order_id
LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = COALESCE(p.cost_center_id, oc.cost_center_id)
LEFT JOIN staging.stg_department AS dep ON dep.department_id = cc.department_id
ORDER BY d.month_end_date DESC, t.severity, d.discrepancy_code, d.age_days DESC, d.identity_id;
