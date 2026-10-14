-- int_cw_reconciliation_snapshot
-- Grain: one row per identity (int_cw_identity_resolution) per month-end on which either system
-- shows the person working.
--
-- The two systems side by side, as each held it on the month-end:
--
--   Bridgeway   what Keystone SHOULD hold: everything Bridgeway had sent by the month-end, applied
--               the day it was sent. The contract start is the worker's first day; the contract
--               end and the cost center, office and manager (the email resolved to the employee)
--               are those of the last change sent. That is the one definition under which a
--               difference is always a discrepancy: a change still in transit is one.
--   Keystone    the version of the contingent record in effect that day: status, contract dates,
--               cost center, office, manager, the Bridgeway ID it stores, who wrote the version
--
-- "Working" in Bridgeway's terms: the contract has started and not ended. Keystone counts a
-- worker active from the day the record is created to the day after the contract end it holds.
-- A difference only matters while either system shows the person working, so only those
-- month-ends are kept. The *_differs flags compare the two; the discrepancy rules
-- (int_cw_discrepancy) decide why they differ.
CREATE OR REPLACE TABLE intermediate.int_cw_reconciliation_snapshot AS
WITH cal AS (
    SELECT month_end_date FROM intermediate.int_month_end_calendar
),

emails AS (
    SELECT work_email, worker_id FROM staging.stg_worker
),

-- Everything Bridgeway sent, in the order Keystone should apply it: per worker and day, the last
-- change sent that day (new worker first, then by revision). What Keystone SHOULD hold on a
-- month-end is the state of the last change sent by then (attributes), and of the last contract
-- change (new worker, renewal, extension, early end) for the contract dates.
sent AS (
    SELECT f.bw_worker_id, f.sent_date, f.event_type, r.service_order_id, r.assignment_end_date,
           r.cost_center_code, r.office_code, r.hiring_manager_email,
           ROW_NUMBER() OVER (PARTITION BY f.bw_worker_id, f.sent_date
                              ORDER BY (f.event_type <> 'New Worker'), f.revision_id DESC) AS last_of_day,
           ROW_NUMBER() OVER (PARTITION BY f.bw_worker_id, f.sent_date, (f.event_type <> 'Attribute Change')
                              ORDER BY (f.event_type <> 'New Worker'), f.revision_id DESC) AS last_contract_of_day
    FROM staging.stg_feed_bridgeway_keystone_event AS f
    JOIN staging.stg_bw_service_order_revision AS r USING (revision_id)
),
sent_any AS (SELECT * FROM sent WHERE last_of_day = 1),
sent_contract AS (SELECT * FROM sent WHERE last_contract_of_day = 1 AND event_type <> 'Attribute Change'),

grid AS (
    SELECT cal.month_end_date, i.*
    FROM cal CROSS JOIN intermediate.int_cw_identity_resolution AS i
    WHERE i.match_status <> 'Never started'
),

bw AS (
    SELECT g.month_end_date, g.identity_id, c.service_order_id, c.assignment_end_date, w.original_start_date AS contract_start_date
    FROM grid AS g
    ASOF JOIN sent_contract AS c ON c.bw_worker_id = g.bw_worker_id AND c.sent_date <= g.month_end_date
    JOIN staging.stg_bw_contingent_worker AS w ON w.bw_worker_id = g.bw_worker_id
),

bw_attr AS (
    SELECT g.month_end_date, g.identity_id, a.cost_center_code, a.office_code, a.hiring_manager_email
    FROM grid AS g
    ASOF JOIN sent_any AS a ON a.bw_worker_id = g.bw_worker_id AND a.sent_date <= g.month_end_date
),

ks AS (
    SELECT cal.month_end_date, k.*
    FROM cal
    JOIN staging.stg_ks_contingent_worker AS k
      ON k.effective_start_date <= cal.month_end_date AND k.effective_end_date_filled >= cal.month_end_date
),

joined AS (
    SELECT
        i.month_end_date,
        i.identity_id, i.match_status, i.match_tier, i.person_id, i.bw_worker_id, i.cw_type, i.supplier_id,
        -- Bridgeway: what Keystone should hold
        b.service_order_id                                                   AS bw_service_order_id,
        b.contract_start_date                                                AS bw_contract_start_date,
        b.assignment_end_date                                                AS bw_contract_end_date,
        COALESCE(b.assignment_end_date >= i.month_end_date, FALSE)           AS bw_active,
        COALESCE(b.assignment_end_date >= i.month_end_date
                 AND b.contract_start_date <= i.month_end_date, FALSE)       AS bw_working,
        a.cost_center_code                                                   AS bw_cost_center_id,
        a.office_code                                                        AS bw_location_id,
        e.worker_id                                                          AS bw_manager_worker_id,
        -- Keystone: what it holds
        k.ks_record_id,
        k.effective_start_date                                               AS ks_version_start_date,
        k.change_source                                                      AS ks_change_source,
        k.bw_worker_id                                                       AS ks_stored_bw_worker_id,
        k.status                                                             AS ks_status,
        k.contract_start_date                                                AS ks_contract_start_date,
        k.contract_end_date                                                  AS ks_contract_end_date,
        k.inactive_reason                                                    AS ks_inactive_reason,
        COALESCE(k.status = 'Active', FALSE)                                 AS ks_active,
        COALESCE(k.status = 'Active' AND k.contract_start_date <= i.month_end_date, FALSE) AS ks_working,
        k.cost_center_id                                                     AS ks_cost_center_id,
        k.location_id                                                        AS ks_location_id,
        k.manager_worker_id                                                  AS ks_manager_worker_id
    FROM grid AS i
    LEFT JOIN bw      AS b ON b.identity_id = i.identity_id AND b.month_end_date = i.month_end_date
    LEFT JOIN bw_attr AS a ON a.identity_id = i.identity_id AND a.month_end_date = i.month_end_date
    LEFT JOIN emails  AS e ON e.work_email = a.hiring_manager_email
    LEFT JOIN ks      AS k ON k.person_id = i.person_id AND k.month_end_date = i.month_end_date
    WHERE b.identity_id IS NOT NULL OR k.person_id IS NOT NULL
)

SELECT
    j.*,
    j.ks_record_id IS NOT NULL                                               AS ks_exists,
    -- the differences, where both systems hold the person
    j.ks_record_id IS NOT NULL AND j.bw_service_order_id IS NOT NULL
        AND (j.ks_active <> j.bw_active
             OR j.ks_contract_end_date IS DISTINCT FROM j.bw_contract_end_date
             OR j.ks_contract_start_date IS DISTINCT FROM j.bw_contract_start_date)  AS contract_differs,
    j.ks_record_id IS NOT NULL AND j.bw_service_order_id IS NOT NULL
        AND j.ks_cost_center_id IS DISTINCT FROM j.bw_cost_center_id             AS cost_center_differs,
    j.ks_record_id IS NOT NULL AND j.bw_service_order_id IS NOT NULL
        AND j.ks_manager_worker_id IS DISTINCT FROM j.bw_manager_worker_id       AS manager_differs,
    j.ks_record_id IS NOT NULL AND j.bw_service_order_id IS NOT NULL
        AND j.ks_location_id IS DISTINCT FROM j.bw_location_id                   AS office_differs,
    j.ks_record_id IS NOT NULL AND j.bw_worker_id IS NOT NULL
        AND j.ks_stored_bw_worker_id IS DISTINCT FROM j.bw_worker_id              AS link_differs
FROM joined AS j
WHERE j.bw_working OR j.ks_working;
