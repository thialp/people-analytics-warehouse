-- mart_cw_gap_close
-- Grain: one row per month-end close x contractor x flag: every gap Finance's report would carry
-- at that close (Jun 2021 to Jun 2026; the latest close is also Current). Dashboard #4's Sankey,
-- gap list and KPIs read it through tableau/custom_sql_cw_reconciliation_dashboard.sql.
--
--   flag, risk, place     the comparison (F01 to F09, flag_label "01 ..." in a fixed order), the
--                         risk it creates (five, alphabetical) and where it is aligned (Bridgeway,
--                         Keystone, System feed: alphabetical; place_label says what each one is).
--                         The Sankey reads flag_label, risk and place_label: all three sort
--                         alphabetically at every close (int_cw_flag_type explains why)
--   flag_rank             rank of the flag by gaps at this close (1 = most), and at the prior close
--                         and 12 closes earlier, so the page can say what moved
--   is_counted            counts against the 3% target (everything but "Clears on its own")
--   was_open_prior_close  the same gap episode was open at the prior close: the same contractor had
--                         the same flag then, and this episode began on or before it (a flag that
--                         cleared and came back between closes is a new episode, not carryover)
--   fixed_day_after_close a change landed on the 1st and the gap is gone at the next close: it
--                         missed the close by a day
--   groups                function, department and country of the cost center Bridgeway bills
--                         (Keystone's when Bridgeway has none), one per contractor per close
--   ticket                the Helix ticket working on it (int_itsm_ticket_gap_link)
-- Executive officers' department (D-901) is excluded, as on every Arcadia dashboard.
CREATE OR REPLACE TABLE marts.mart_cw_gap_close AS
WITH f AS (
    SELECT f.*, COALESCE(f.identity_id, f.bw_worker_id, f.person_id) AS contractor_key
    FROM intermediate.int_cw_flag AS f
),
snap AS (SELECT * FROM intermediate.int_cw_reconciliation_snapshot),
order_cc AS (
    SELECT service_order_id, ARG_MAX(cost_center_code, revision_no) AS cost_center_id
    FROM staging.stg_bw_service_order_revision GROUP BY 1
),
ks_last AS (    -- Keystone's cost center for the person on the close, or their last one before it
    SELECT r.month_end_date, k.person_id, ARG_MAX(k.cost_center_id, k.effective_start_date) AS cost_center_id
    FROM intermediate.int_cw_close_run AS r
    JOIN staging.stg_ks_contingent_worker AS k ON k.effective_start_date <= r.month_end_date
    WHERE k.person_id IN (SELECT person_id FROM f)
    GROUP BY 1, 2
),
placed AS (
    SELECT f.*, COALESCE(s.bw_cost_center_id, oc.cost_center_id, s.ks_cost_center_id, kl.cost_center_id) AS row_cost_center_id
    FROM f
    LEFT JOIN snap AS s ON s.month_end_date = f.month_end_date AND s.identity_id = f.identity_id
    LEFT JOIN order_cc AS oc ON oc.service_order_id = f.service_order_id
    LEFT JOIN ks_last AS kl ON kl.month_end_date = f.month_end_date AND kl.person_id = f.person_id
),
grouped AS (    -- one group per contractor per close: Bridgeway's cost center wins
    SELECT p.*,
           FIRST_VALUE(p.row_cost_center_id IGNORE NULLS) OVER (
               PARTITION BY p.month_end_date, p.contractor_key
               ORDER BY (s.bw_cost_center_id IS NULL), p.flag_code
               ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING)                AS cost_center_id
    FROM placed AS p
    LEFT JOIN snap AS s ON s.month_end_date = p.month_end_date AND s.identity_id = p.identity_id
),
scoped AS (
    SELECT g.*, cc.department_id, cc.country_code, dep.department_name, dep.function_name, co.country_name
    FROM grouped AS g
    LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = g.cost_center_id
    LEFT JOIN staging.stg_department AS dep ON dep.department_id = cc.department_id
    LEFT JOIN staging.stg_country AS co ON co.country_code = cc.country_code
    WHERE COALESCE(cc.department_id, '') <> 'D-901'
),
counts AS (
    SELECT month_end_date, flag_code, COUNT(*) AS flag_count,
           ROW_NUMBER() OVER (PARTITION BY month_end_date ORDER BY COUNT(*) DESC, flag_code) AS flag_rank
    FROM scoped GROUP BY 1, 2
),
cal AS (
    SELECT month_end_date, prior_month_end_date,
           LAG(month_end_date, 12) OVER (ORDER BY month_end_date) AS year_ago_month_end_date
    FROM intermediate.int_month_end_calendar
),
causes AS (
    SELECT discrepancy_code AS cause_code, discrepancy_name AS cause_name FROM staging.stg_cw_discrepancy_type
    UNION ALL SELECT 'JOB', 'Keystone job data out of step with the PID ledger'
    UNION ALL SELECT 'CONV', 'Converted to employee; contractor record still active'
    UNION ALL SELECT 'LOAD', 'Source load failed at the close'
),
next_day AS (    -- something changed for the contractor on the 1st after the close
    SELECT DISTINCT s.month_end_date, s.gap_id
    FROM scoped AS s
    WHERE EXISTS (SELECT 1 FROM staging.stg_ks_contingent_worker AS k
                  WHERE k.person_id = s.person_id AND k.effective_start_date = s.month_end_date + 1)
       OR EXISTS (SELECT 1 FROM staging.stg_feed_bridgeway_keystone_event AS e
                  WHERE e.bw_worker_id = s.bw_worker_id AND e.applied_date = s.month_end_date + 1)
       OR EXISTS (SELECT 1 FROM staging.stg_ks_cw_job AS j
                  WHERE j.person_id = s.person_id AND j.effective_start_date = s.month_end_date + 1)
       OR EXISTS (SELECT 1 FROM staging.stg_bw_service_order_revision AS r
                  WHERE r.service_order_id = s.service_order_id AND r.effective_start_date = s.month_end_date + 1)
)
SELECT
    s.month_end_date,
    STRFTIME(s.month_end_date, '%b %Y')                                              AS close_label,
    r.is_latest_close,
    s.gap_id,
    s.contractor_key,
    s.bw_worker_id,
    s.person_id,
    i.first_name || ' ' || i.last_name                                               AS contractor_name,
    i.cw_type,
    sup.supplier_name,
    s.flag_code,
    s.flag_name,
    s.flag_label,
    c.flag_count,
    c.flag_rank,
    cp.flag_count                                                                     AS flag_count_prior_close,
    cp.flag_rank                                                                      AS flag_rank_prior_close,
    cy.flag_count                                                                     AS flag_count_year_ago,
    cy.flag_rank                                                                      AS flag_rank_year_ago,
    s.risk,
    s.risk_order,
    s.place,
    CASE s.place WHEN 'Bridgeway' THEN 1 WHEN 'Keystone' THEN 2 ELSE 3 END           AS place_order,
    CASE s.place WHEN 'Bridgeway' THEN 'Bridgeway (vendor system)'
                 WHEN 'Keystone' THEN 'Keystone (HR system)'
                 ELSE 'System feed (integration)' END                                 AS place_label,
    s.cause_code,
    cz.cause_name,
    s.root_cause_code,
    s.timing_class,
    COALESCE(s.timing_class, '') <> 'Clears on its own'                              AS is_counted,
    s.since_date,
    s.days_open,
    CASE WHEN s.days_open <= 30 THEN '0 to 30 days' WHEN s.days_open <= 90 THEN '31 to 90 days'
         ELSE 'Over 90 days' END                                                      AS open_band,
    s.days_open > 90                                                                  AS is_over_90_days,
    CASE WHEN s.flag_code IN ('F06', 'F09') THEN s.month_end_date - s.since_date END AS days_since_end,
    (EXISTS (SELECT 1 FROM scoped AS p WHERE p.month_end_date = cl.prior_month_end_date AND p.gap_id = s.gap_id)
     AND s.since_date <= cl.prior_month_end_date)                                     AS was_open_prior_close,
    (nd.gap_id IS NOT NULL
     AND NOT EXISTS (SELECT 1 FROM scoped AS n
                     WHERE n.month_end_date = LAST_DAY(s.month_end_date + 1) AND n.gap_id = s.gap_id))
                                                                                      AS fixed_day_after_close,
    s.items,
    s.service_order_id,
    s.feed_event_id,
    s.position_id,
    s.cost_center_id,
    s.department_id,
    s.department_name,
    s.function_name,
    s.country_code,
    s.country_name,
    s.keystone_shows,
    s.bridgeway_has,
    s.evidence,
    s.next_step,
    l.ticket_number,
    tk.title                                                                          AS ticket_title,
    l.ticket_state,
    l.ticket_status,
    l.has_ticket
FROM scoped AS s
JOIN intermediate.int_cw_close_run AS r USING (month_end_date)
JOIN cal AS cl USING (month_end_date)
JOIN counts AS c USING (month_end_date, flag_code)
LEFT JOIN counts AS cp ON cp.month_end_date = cl.prior_month_end_date AND cp.flag_code = s.flag_code
LEFT JOIN counts AS cy ON cy.month_end_date = cl.year_ago_month_end_date AND cy.flag_code = s.flag_code
LEFT JOIN causes AS cz ON cz.cause_code = s.cause_code
LEFT JOIN next_day AS nd ON nd.month_end_date = s.month_end_date AND nd.gap_id = s.gap_id
LEFT JOIN intermediate.int_cw_identity_resolution AS i ON i.identity_id = s.identity_id
LEFT JOIN staging.stg_bw_supplier AS sup ON sup.supplier_id = i.supplier_id
LEFT JOIN intermediate.int_itsm_ticket_gap_link AS l ON l.month_end_date = s.month_end_date AND l.gap_id = s.gap_id
LEFT JOIN staging.stg_itsm_ticket AS tk ON tk.ticket_number = l.ticket_number
ORDER BY month_end_date, risk_order, place_order, days_open DESC, gap_id;
