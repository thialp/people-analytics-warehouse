-- int_cw_flag
-- Grain: one row per month-end close x contractor x flag: a gap.
--
-- The reconciliation as Finance's report meets it. A gap is a comparison between the systems on
-- the close (int_cw_flag_type: F01 to F12), with the cause behind it (the CW codes of
-- int_cw_discrepancy, or JOB, CONV, LOAD below), and the place it is fixed.
--
-- Where the flags come from:
--   int_cw_discrepancy     the field differences and the structural rules, as comparisons:
--                          cost center (F01, F02: by function), contract status (F09 ended in
--                          Bridgeway and active in Keystone, F11 the reverse; a difference in
--                          dates alone, both active, is not a flag), order open after the end
--                          (F03), billed after the end (F04), two Bridgeway IDs (F05), the stored
--                          ID (F06), Keystone only (F10), missing in Keystone (F12). Manager,
--                          office and the 48-month cap are not flags: they do not move Finance's
--                          numbers.
--   conversions (CONV)     an F09 contractor who is now an employee: one person on two EMPLIDs,
--                          the contractor record and the employee one (F05, fixed in Keystone).
--                          The employee is found by name, hired within 31 days after the
--                          Bridgeway last day and still employed on the close.
--   Keystone job data (JOB) two active job records for one person (F07); one active record on a
--                          PID the PID ledger shows they are no longer in (F08).
--   a failed load (LOAD)   int_cw_load_gap: differences that exist only because a source is a
--                          stale. Gaps the stale source hides are dropped (a hand edit after the
--                          stale date when Keystone is stale; a change sent after it when
--                          Bridgeway is).
--
-- The routing rule (one CASE):
--   1. A feed change still waiting at the close (CW00, CW01) goes to Integration: "Clears on its
--      own" when it was sent within the 24 hours before the close run, "Alert data engineering"
--      when it has waited longer (the feed is stuck).
--   2. A gap that exists because a load failed goes to Integration, "Alert data engineering".
--   3. Otherwise by flag: F01 to F05 to Bridgeway (F05 to Keystone when it is a conversion),
--      F06 to F12 to Keystone.
-- is_counted: the gap counts against the 3% target unless it clears on its own by the next run.
CREATE OR REPLACE TABLE intermediate.int_cw_flag AS
WITH runs AS (SELECT * FROM intermediate.int_cw_close_run),
snap AS (SELECT * FROM intermediate.int_cw_reconciliation_snapshot),
cc AS (SELECT cost_center_id, department_id, function_name FROM staging.stg_cost_center),
idn AS (SELECT * FROM intermediate.int_cw_identity_resolution),
d AS (
    SELECT d.*, s.bw_active, s.ks_active, s.bw_working, s.bw_cost_center_id, s.ks_cost_center_id,
           s.bw_contract_start_date, s.bw_contract_end_date, s.ks_contract_end_date, s.ks_status,
           s.ks_stored_bw_worker_id
    FROM intermediate.int_cw_discrepancy AS d
    LEFT JOIN snap AS s USING (month_end_date, identity_id)
),

-- 1. comparisons from the reconciliation ------------------------------------------------------
cost_center AS (
    SELECT d.month_end_date, d.identity_id, d.bw_worker_id, d.person_id,
           CASE WHEN bc.function_name IS DISTINCT FROM kc.function_name THEN 'F01' ELSE 'F02' END AS flag_code,
           d.discrepancy_code AS cause_code, d.root_cause_code, d.since_date, d.service_order_id, d.feed_event_id,
           NULL::VARCHAR AS position_id, d.evidence,
           'Cost center ' || d.ks_cost_center_id || ' (' || kd.department_name || ', ' || kc.function_name || ')' AS keystone_shows,
           'Cost center ' || d.bw_cost_center_id || ' (' || bd.department_name || ', ' || bc.function_name || ')' AS bridgeway_has
    FROM d
    LEFT JOIN cc AS bc ON bc.cost_center_id = d.bw_cost_center_id
    LEFT JOIN cc AS kc ON kc.cost_center_id = d.ks_cost_center_id
    LEFT JOIN staging.stg_department AS bd ON bd.department_id = bc.department_id
    LEFT JOIN staging.stg_department AS kd ON kd.department_id = kc.department_id
    WHERE d.discrepancy_code IN ('CW00', 'CW01', 'CW05', 'CW12') AND d.fields_affected LIKE '%Cost center%'
),
contract AS (
    SELECT d.month_end_date, d.identity_id, d.bw_worker_id, d.person_id,
           CASE WHEN d.bw_active THEN 'F11' ELSE 'F09' END AS flag_code,
           d.discrepancy_code AS cause_code, d.root_cause_code,
           CASE WHEN d.bw_active THEN d.since_date ELSE LEAST(d.since_date, d.bw_contract_end_date + 1) END AS since_date,
           d.service_order_id, d.feed_event_id, NULL::VARCHAR AS position_id, d.evidence,
           CASE WHEN d.ks_active THEN 'Active, contract to ' ELSE 'Inactive, contract to ' END
               || COALESCE(CAST(d.ks_contract_end_date AS VARCHAR), '?')                AS keystone_shows,
           CASE WHEN d.bw_active THEN 'Working, contract to ' ELSE 'Ended ' END
               || COALESCE(CAST(d.bw_contract_end_date AS VARCHAR), '?')                AS bridgeway_has
    FROM d
    WHERE d.discrepancy_code IN ('CW00', 'CW01', 'CW02', 'CW03') AND d.fields_affected LIKE '%Status%'
      AND d.bw_active IS DISTINCT FROM d.ks_active
),
structural AS (
    SELECT d.month_end_date, d.identity_id, d.bw_worker_id, d.person_id,
           CASE d.discrepancy_code WHEN 'CW04' THEN 'F03' WHEN 'CW11' THEN 'F04' WHEN 'CW07' THEN 'F05'
                WHEN 'CW06' THEN 'F06' WHEN 'CW09' THEN 'F10' ELSE 'F12' END AS flag_code,
           d.discrepancy_code, d.root_cause_code, d.since_date, d.service_order_id, d.feed_event_id, NULL, d.evidence,
           CASE d.discrepancy_code
                WHEN 'CW04' THEN 'Not held in Keystone'
                WHEN 'CW11' THEN 'Not held in Keystone'
                WHEN 'CW07' THEN 'Two people: ' || d.person_id || ' and an earlier record'
                WHEN 'CW06' THEN COALESCE('Stores Bridgeway ID ' || d.ks_stored_bw_worker_id, 'Stores no Bridgeway ID')
                WHEN 'CW09' THEN 'Active, no Bridgeway worker'
                ELSE 'No record' END,
           CASE d.discrepancy_code
                WHEN 'CW04' THEN 'Order ' || d.service_order_id || ' still open after the last day'
                WHEN 'CW11' THEN 'Time billed for a month after the last day'
                WHEN 'CW07' THEN 'Second Bridgeway ID ' || d.bw_worker_id || ' for the same person'
                WHEN 'CW06' THEN 'Worker ' || d.bw_worker_id
                WHEN 'CW09' THEN 'No worker'
                ELSE 'Working since ' || COALESCE(CAST(d.bw_contract_start_date AS VARCHAR), '?') END
    FROM d
    WHERE d.discrepancy_code IN ('CW04', 'CW11', 'CW07', 'CW06', 'CW09')
       OR (d.fields_affected = 'Whole record' AND d.discrepancy_code IN ('CW00', 'CW01', 'CW08'))
),

-- 2. a converted contractor still active as a contractor: one person, two EMPLIDs -------------
converted AS (
    SELECT c.month_end_date, c.identity_id, w.worker_id, w.original_hire_date
    FROM contract AS c
    JOIN idn AS i ON i.identity_id = c.identity_id
    JOIN snap AS s ON s.month_end_date = c.month_end_date AND s.identity_id = c.identity_id
    JOIN staging.stg_worker AS w
      ON w.first_name = i.first_name AND w.last_name = i.last_name
     AND w.original_hire_date BETWEEN s.bw_contract_end_date + 1 AND s.bw_contract_end_date + 31
     AND w.original_hire_date <= c.month_end_date
     AND (w.termination_date IS NULL OR w.termination_date > c.month_end_date)
    WHERE c.flag_code = 'F09'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY c.month_end_date, c.identity_id ORDER BY w.original_hire_date, w.worker_id) = 1
),
reconciliation AS (
    SELECT * FROM cost_center
    UNION ALL
    SELECT c.month_end_date, c.identity_id, c.bw_worker_id, c.person_id,
           CASE WHEN v.identity_id IS NOT NULL THEN 'F05' ELSE c.flag_code END,
           CASE WHEN v.identity_id IS NOT NULL THEN 'CONV' ELSE c.cause_code END,
           c.root_cause_code, c.since_date, c.service_order_id, c.feed_event_id, NULL,
           CASE WHEN v.identity_id IS NOT NULL
                THEN 'Hired as employee ' || v.worker_id || ' on ' || CAST(v.original_hire_date AS VARCHAR)
                     || '; the contractor record ' || c.person_id || ' is still active. ' || c.evidence
                ELSE c.evidence END,
           CASE WHEN v.identity_id IS NOT NULL THEN 'Two active EMPLIDs: ' || c.person_id || ' (contractor) and '
                     || v.worker_id || ' (employee)' ELSE c.keystone_shows END,
           CASE WHEN v.identity_id IS NOT NULL THEN 'Ended ' || CAST(s.bw_contract_end_date AS VARCHAR)
                     || ' (converted to employee)' ELSE c.bridgeway_has END
    FROM contract AS c
    LEFT JOIN converted AS v USING (month_end_date, identity_id)
    LEFT JOIN snap AS s USING (month_end_date, identity_id)
    UNION ALL
    SELECT * FROM structural
),

-- 3. Keystone job data against the PID ledger ------------------------------------------------
jobs AS (
    SELECT r.month_end_date, j.person_id, j.position_id, j.empl_rcd, j.effective_start_date, j.job_record_id,
           EXISTS (SELECT 1 FROM staging.stg_cw_position_assignment AS a
                   WHERE a.worker_id = j.person_id AND a.position_id = j.position_id
                     AND a.start_date <= r.month_end_date AND a.end_date_filled >= r.month_end_date) AS in_ledger
    FROM runs AS r
    JOIN staging.stg_ks_cw_job AS j
      ON j.job_status = 'Active' AND j.effective_start_date <= r.month_end_date
     AND j.effective_end_date_filled >= r.month_end_date
),
job_person AS (
    SELECT month_end_date, person_id, COUNT(*) AS active_records,
           MIN(position_id) AS position_id, MAX(effective_start_date) AS second_since,
           STRING_AGG(position_id || ' (record ' || CAST(empl_rcd AS VARCHAR) || ')', ', ' ORDER BY empl_rcd) AS records,
           BOOL_OR(in_ledger) AS any_in_ledger,
           ARG_MAX(position_id, empl_rcd) FILTER (WHERE in_ledger) AS ledger_pid
    FROM jobs GROUP BY 1, 2
),
left_pid AS (    -- the day the person left the PID, by the ledger
    SELECT p.month_end_date, p.person_id, MAX(a.end_date) + 1 AS left_on
    FROM job_person AS p
    JOIN staging.stg_cw_position_assignment AS a
      ON a.worker_id = p.person_id AND a.position_id = p.position_id AND a.end_date < p.month_end_date
    WHERE p.active_records = 1 AND NOT p.any_in_ledger
    GROUP BY 1, 2
),
job_flags AS (
    SELECT p.month_end_date, i.identity_id, i.bw_worker_id, p.person_id,
           CASE WHEN p.active_records >= 2 THEN 'F07' ELSE 'F08' END,
           'JOB', 'JOB',
           CASE WHEN p.active_records >= 2 THEN p.second_since ELSE COALESCE(l.left_on, p.second_since) END,
           NULL, NULL, p.position_id,
           CASE WHEN p.active_records >= 2
                THEN 'Keystone job data holds ' || CAST(p.active_records AS VARCHAR) || ' active records: ' || p.records
                ELSE 'Keystone job record on ' || p.position_id || ' is still active'
                     || COALESCE('; the PID ledger shows the contractor left it on ' || CAST(l.left_on AS VARCHAR), '') END,
           CASE WHEN p.active_records >= 2 THEN CAST(p.active_records AS VARCHAR) || ' active records: ' || p.records
                ELSE 'Active in ' || p.position_id END,
           CASE WHEN p.active_records >= 2 THEN COALESCE('One assignment, on ' || p.ledger_pid, 'No current assignment')
                ELSE COALESCE('Left ' || p.position_id || ' on ' || CAST(l.left_on AS VARCHAR), 'Not in ' || p.position_id) END
    FROM job_person AS p
    LEFT JOIN left_pid AS l USING (month_end_date, person_id)
    LEFT JOIN idn AS i ON i.person_id = p.person_id
    WHERE p.active_records >= 2 OR NOT p.any_in_ledger
),

-- 4. everything, with what a failed load adds and hides --------------------------------------
all_gaps AS (
    SELECT g.* FROM (SELECT * FROM reconciliation UNION ALL SELECT * FROM job_flags) AS g
    JOIN runs AS r USING (month_end_date)
    WHERE NOT (g.cause_code = 'CW05' AND g.since_date > r.ks_data_as_of)
      AND NOT (g.cause_code IN ('CW00', 'CW01') AND g.since_date > r.bw_data_as_of)
    UNION ALL
    SELECT month_end_date, identity_id, bw_worker_id, person_id, flag_code, 'LOAD', cause_detail, since_date,
           NULL, NULL, NULL, evidence, keystone_shows, bridgeway_has
    FROM intermediate.int_cw_load_gap
),
one_per_contractor AS (    -- a worker with two open orders or two late timesheets is one gap
    SELECT g.*, COUNT(*) OVER w AS items
    FROM all_gaps AS g
    WINDOW w AS (PARTITION BY g.month_end_date, COALESCE(g.identity_id, g.bw_worker_id, g.person_id), g.flag_code)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY g.month_end_date, COALESCE(g.identity_id, g.bw_worker_id, g.person_id), g.flag_code
                               ORDER BY g.since_date, g.service_order_id, g.feed_event_id, g.evidence) = 1
)

SELECT
    g.month_end_date,
    g.flag_code || '-' || COALESCE(g.bw_worker_id, g.person_id)                       AS gap_id,
    COALESCE(g.identity_id, i.identity_id)                                             AS identity_id,
    COALESCE(g.bw_worker_id, i.bw_worker_id)                                           AS bw_worker_id,
    COALESCE(g.person_id, i.person_id)                                                 AS person_id,
    g.flag_code,
    t.flag_name,
    t.risk,
    t.risk_order,
    g.cause_code,
    g.root_cause_code,
    g.since_date,
    g.month_end_date - g.since_date                                                    AS days_open,
    g.items,
    g.service_order_id,
    g.feed_event_id,
    fd.sent_at                                                                         AS feed_sent_at,
    g.position_id,
    CASE WHEN g.cause_code IN ('CW00', 'CW01') THEN 'Integration'
         WHEN g.cause_code = 'LOAD' THEN 'Integration'
         WHEN g.flag_code = 'F05' AND g.cause_code = 'CONV' THEN 'Keystone'
         ELSE t.default_place END                                                      AS place,
    CASE WHEN g.cause_code IN ('CW00', 'CW01') AND fd.sent_at > r.close_run_at - INTERVAL 24 HOUR THEN 'Clears on its own'
         WHEN g.cause_code IN ('CW00', 'CW01') THEN 'Feed stuck'
         WHEN g.cause_code = 'LOAD' THEN 'Load failed' END                             AS timing_class,
    g.keystone_shows,
    g.bridgeway_has,
    g.evidence
        || CASE WHEN g.cause_code IN ('CW00', 'CW01') AND fd.sent_at IS NOT NULL
                THEN '. Sent ' || STRFTIME(fd.sent_at, '%Y-%m-%d %H:%M') || ' GMT, '
                     || CAST(DATE_DIFF('hour', fd.sent_at, r.close_run_at) AS VARCHAR) || ' hours before the close run'
                ELSE '' END                                                            AS evidence,
    CASE WHEN g.flag_code = 'F05' AND g.cause_code = 'CONV' THEN 'End the contractor record in Keystone; the person is now an employee'
         WHEN g.cause_code IN ('CW00', 'CW01') AND fd.sent_at > r.close_run_at - INTERVAL 24 HOUR THEN 'None: the change lands with the next feed batch'
         WHEN g.cause_code IN ('CW00', 'CW01') THEN 'Data engineering: release the stuck feed change'
         WHEN g.cause_code = 'LOAD' THEN 'Data engineering: the next run reloads the source; check it cleared'
         ELSE t.next_step END                                                          AS next_step
FROM one_per_contractor AS g
JOIN intermediate.int_cw_flag_type AS t USING (flag_code)
JOIN runs AS r USING (month_end_date)
LEFT JOIN staging.stg_feed_event_delivery AS fd ON fd.feed_event_id = g.feed_event_id
LEFT JOIN idn AS i ON g.identity_id IS NULL AND i.bw_worker_id = g.bw_worker_id;
