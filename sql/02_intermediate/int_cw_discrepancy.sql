-- int_cw_discrepancy
-- Grain: one row per month-end x identity (or service order, or timesheet) x discrepancy type.
--
-- The warehouse's own reconciliation: every discrepancy between Bridgeway and Keystone, and
-- Bridgeway's own hygiene problems, found from the two systems and the feed log alone. The
-- answer key (gen_cw_discrepancy_truth) is never read here; it only scores the result
-- (mart_cw_detection_score).
--
-- How a difference is explained. For each field group that differs on a month-end (contract
-- dates and status; cost center; manager; office), the rules collect the recorded causes that
-- could have produced it, and the most recent one names the discrepancy:
--
--   a feed change not yet applied on the month-end   CW00 Change in transit (applied within 2 days)
--                                                    CW01 Change arrived late (3 days or more, or still queued)
--   a feed change that failed                        CW02 Extension never arrived (an extension or renewal)
--                                                    CW03 Early end never arrived
--                                                    CW12 Attribute change never arrived
--   a hand edit in Keystone                          CW05 Changed in Keystone only
--
-- A change touches the fields its revision touched: contract changes (new worker, renewal,
-- extension, early end) the contract; a cost center change the cost center and the manager; a
-- manager change the manager; an office change the office. A failure that Keystone reported as
-- "worker not found" has a root cause: the record was never created (CW08) or its stored
-- Bridgeway ID is wrong (CW06). A difference with no recorded cause is flagged as
-- "Unexplained": nothing should land there.
--
-- Structural rules, on the identity or the order:
--   CW06 Link ID missing or mistyped    a matched person whose stored Bridgeway ID is not theirs
--   CW07 One person, two IDs            a Bridgeway worker who starts, as a new engagement, the day
--                                       after another worker with the same name and supplier ended,
--                                       on the same cost center (a renewal submitted as a new worker;
--                                       two different people with the same name rarely line up so)
--   CW08 Never reached Keystone         working in Bridgeway, no Keystone record (and no new-worker
--                                       change in transit)
--   CW09 Keystone-only                  working in Keystone, no Bridgeway worker
--   CW10 Over the duration cap          a Contractor or Consultant working 48 months after starting
--   CW04 Ended but not closed           the order's revision in effect is not Closed 16 days or more
--                                       after the last day (an order later extended was a late
--                                       approval, not a missing closure)
--   CW11 Billed after the assignment    time billed for a month that starts after the last day
--
-- Discrepancies between the systems count only on month-ends when either one shows the person
-- working (int_cw_reconciliation_snapshot); Bridgeway hygiene counts regardless.
CREATE OR REPLACE TABLE intermediate.int_cw_discrepancy AS
WITH snap AS (
    SELECT * FROM intermediate.int_cw_reconciliation_snapshot
),

extract AS (SELECT MAX(month_end_date) AS extract_date FROM intermediate.int_month_end_calendar),

-- feed changes, with the field groups each one touched: those whose value differs from the
-- change sent before it for the same worker (a new worker touches everything)
sent_seq AS (
    SELECT f.*, r.revision_reason, r.cost_center_code, r.hiring_manager_email, r.office_code,
           LAG(r.cost_center_code)     OVER w AS prev_cost_center_code,
           LAG(r.hiring_manager_email) OVER w AS prev_manager_email,
           LAG(r.office_code)          OVER w AS prev_office_code
    FROM staging.stg_feed_bridgeway_keystone_event AS f
    JOIN staging.stg_bw_service_order_revision AS r USING (revision_id)
    WINDOW w AS (PARTITION BY f.bw_worker_id ORDER BY f.sent_date, (f.event_type <> 'New Worker'), f.revision_id)
),
events AS (
    SELECT f.feed_event_id, f.bw_worker_id, f.event_type, f.sent_date, f.applied_date, f.outcome, f.error_text,
           f.revision_reason,
           f.event_type IN ('New Worker', 'Renewal', 'Extension', 'Early End')            AS g_contract,
           f.event_type = 'New Worker' OR f.cost_center_code     IS DISTINCT FROM f.prev_cost_center_code AS g_cost_center,
           f.event_type = 'New Worker' OR f.hiring_manager_email IS DISTINCT FROM f.prev_manager_email    AS g_manager,
           f.event_type = 'New Worker' OR f.office_code          IS DISTINCT FROM f.prev_office_code      AS g_office,
           CASE WHEN f.outcome = 'Failed' THEN
                CASE f.event_type WHEN 'New Worker' THEN 'CW08' WHEN 'Early End' THEN 'CW03'
                                  WHEN 'Attribute Change' THEN 'CW12' ELSE 'CW02' END
                WHEN f.outcome = 'Queued' THEN 'CW01'
                WHEN f.applied_date - f.sent_date <= 2 THEN 'CW00' ELSE 'CW01' END       AS code
    FROM sent_seq AS f
    WHERE f.outcome IN ('Failed', 'Queued') OR f.applied_date > f.sent_date
),

-- hand edits in Keystone: a Manager or HR Ops version that changed a field (not a conversion).
-- A record's first version counts too: a hand edit on the day the feed created the record is
-- merged into it (one version per day)
ks_versions AS (
    SELECT k.*,
           LAG(k.cost_center_id)    OVER w AS prev_cost_center_id,
           LAG(k.manager_worker_id) OVER w AS prev_manager_worker_id,
           LAG(k.location_id)       OVER w AS prev_location_id,
           LAG(k.ks_record_id)      OVER w AS prev_record_id
    FROM staging.stg_ks_contingent_worker AS k
    WINDOW w AS (PARTITION BY k.person_id ORDER BY k.effective_start_date)
),
edits AS (
    SELECT person_id, effective_start_date AS edit_date, change_source,
           cost_center_id    IS DISTINCT FROM prev_cost_center_id    AS g_cost_center,
           manager_worker_id IS DISTINCT FROM prev_manager_worker_id AS g_manager,
           location_id       IS DISTINCT FROM prev_location_id       AS g_office
    FROM ks_versions
    WHERE change_source IN ('Manager', 'HR Ops')
      AND COALESCE(inactive_reason, '') <> 'Converted to employee'
),

-- one row per differing field group
diffs AS (
    SELECT s.*, g.grp
    FROM snap AS s
    CROSS JOIN (VALUES ('contract'), ('cost_center'), ('manager'), ('office')) AS g(grp)
    WHERE (g.grp = 'contract' AND s.contract_differs) OR (g.grp = 'cost_center' AND s.cost_center_differs)
       OR (g.grp = 'manager' AND s.manager_differs)   OR (g.grp = 'office' AND s.office_differs)
),

-- every candidate cause of each difference, recorded on or before the month-end
causes AS (
    SELECT d.month_end_date, d.identity_id, d.grp, e.sent_date AS cause_date, 1 AS kind,
           e.code, e.feed_event_id, e.event_type, e.sent_date, e.applied_date, e.outcome, e.error_text
    FROM diffs AS d
    JOIN events AS e ON e.bw_worker_id = d.bw_worker_id AND e.sent_date <= d.month_end_date
    WHERE ((d.grp = 'contract' AND e.g_contract) OR (d.grp = 'cost_center' AND e.g_cost_center)
           OR (d.grp = 'manager' AND e.g_manager) OR (d.grp = 'office' AND e.g_office))
      AND (e.outcome = 'Failed' OR e.outcome = 'Queued' OR e.applied_date > d.month_end_date)
    UNION ALL
    SELECT d.month_end_date, d.identity_id, d.grp, x.edit_date, 2, 'CW05', NULL, NULL, NULL, NULL, x.change_source, NULL
    FROM diffs AS d
    JOIN edits AS x ON x.person_id = d.person_id AND x.edit_date <= d.month_end_date
    WHERE (d.grp = 'cost_center' AND x.g_cost_center) OR (d.grp = 'manager' AND x.g_manager)
       OR (d.grp = 'office' AND x.g_office)
),

explained AS (   -- the most recent cause per difference
    SELECT d.*, c.cause_date, c.code, c.feed_event_id, c.event_type, c.sent_date, c.applied_date, c.outcome, c.error_text
    FROM diffs AS d
    LEFT JOIN causes AS c USING (month_end_date, identity_id, grp)
    QUALIFY ROW_NUMBER() OVER (PARTITION BY d.month_end_date, d.identity_id, d.grp
                               ORDER BY c.cause_date DESC NULLS LAST, c.kind DESC, c.feed_event_id DESC) = 1
),

field_lines AS (
    SELECT
        e.month_end_date, e.identity_id, e.bw_worker_id, e.person_id,
        COALESCE(e.code, 'Unexplained')                                     AS discrepancy_code,
        CASE WHEN e.outcome = 'Failed' AND e.error_text LIKE 'Worker not found%'
             THEN CASE WHEN EXISTS (SELECT 1 FROM staging.stg_ks_contingent_worker AS k
                                    WHERE k.person_id = e.person_id AND k.effective_start_date <= e.sent_date)
                       THEN 'CW06' ELSE 'CW08' END
             ELSE COALESCE(e.code, 'Unexplained') END                       AS root_cause_code,
        e.grp,
        e.cause_date                                                        AS since_date,
        e.bw_service_order_id                                               AS service_order_id,
        e.feed_event_id,
        NULL                                                                AS timesheet_id,
        CASE e.grp
            WHEN 'contract' THEN 'Bridgeway: ' || CASE WHEN e.bw_active THEN 'active' ELSE 'ended' END
                                 || ', contract to ' || COALESCE(CAST(e.bw_contract_end_date AS VARCHAR), '?')
                                 || '; Keystone: ' || COALESCE(e.ks_status, 'no record')
                                 || ', contract to ' || COALESCE(CAST(e.ks_contract_end_date AS VARCHAR), '?')
            WHEN 'cost_center' THEN 'Cost center: Bridgeway ' || COALESCE(e.bw_cost_center_id, '?')
                                    || ', Keystone ' || COALESCE(e.ks_cost_center_id, '?')
            WHEN 'manager' THEN 'Manager: Bridgeway ' || COALESCE(e.bw_manager_worker_id, '?')
                                || ', Keystone ' || COALESCE(e.ks_manager_worker_id, '?')
            ELSE 'Office: Bridgeway ' || COALESCE(e.bw_location_id, '?') || ', Keystone ' || COALESCE(e.ks_location_id, '?')
        END
        || CASE
            WHEN e.code = 'CW05' THEN '. Changed by hand in Keystone (' || e.outcome || ') on ' || CAST(e.cause_date AS VARCHAR)
            WHEN e.outcome = 'Failed' THEN '. ' || e.event_type || ' sent ' || CAST(e.sent_date AS VARCHAR) || ' failed: ' || e.error_text
            WHEN e.outcome = 'Queued' THEN '. ' || e.event_type || ' sent ' || CAST(e.sent_date AS VARCHAR) || ', still queued'
            WHEN e.code IS NOT NULL THEN '. ' || e.event_type || ' sent ' || CAST(e.sent_date AS VARCHAR)
                                         || ', applied ' || CAST(e.applied_date AS VARCHAR)
            ELSE '. No recorded change explains it'
        END                                                                 AS evidence
    FROM explained AS e
),

-- structural rules ------------------------------------------------------------------------
missing_record AS (    -- working in Bridgeway, no Keystone record
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id,
           COALESCE(p.code, 'CW08') AS discrepancy_code, COALESCE(p.code, 'CW08') AS root_cause_code,
           'record' AS grp, COALESCE(p.sent_date, n.sent_date, s.bw_contract_start_date) AS since_date,
           s.bw_service_order_id AS service_order_id, COALESCE(p.feed_event_id, n.feed_event_id) AS feed_event_id,
           NULL AS timesheet_id,
           'Working in Bridgeway since ' || CAST(s.bw_contract_start_date AS VARCHAR) || '; no Keystone record'
           || CASE WHEN p.feed_event_id IS NOT NULL THEN '. New Worker sent ' || CAST(p.sent_date AS VARCHAR) || ', not applied yet'
                   WHEN n.feed_event_id IS NOT NULL THEN '. New Worker sent ' || CAST(n.sent_date AS VARCHAR) || ' failed: ' || n.error_text
                   ELSE '' END AS evidence
    FROM snap AS s
    LEFT JOIN events AS p
           ON p.bw_worker_id = s.bw_worker_id AND p.event_type = 'New Worker' AND p.code IN ('CW00', 'CW01')
          AND p.sent_date <= s.month_end_date AND (p.outcome = 'Queued' OR p.applied_date > s.month_end_date)
    LEFT JOIN events AS n
           ON n.bw_worker_id = s.bw_worker_id AND n.event_type = 'New Worker' AND n.outcome = 'Failed'
    WHERE s.bw_working AND NOT s.ks_exists
),

keystone_only AS (
    SELECT month_end_date, identity_id, NULL AS bw_worker_id, person_id, 'CW09', 'CW09', 'record',
           ks_contract_start_date, NULL, NULL, NULL,
           'Active in Keystone since ' || CAST(ks_contract_start_date AS VARCHAR)
           || ' (written by ' || ks_change_source || '); no Bridgeway worker with this ID, or this name and start'
    FROM snap WHERE match_status = 'Keystone only' AND ks_working
),

broken_link AS (
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id, 'CW06', 'CW06', 'link',
           (SELECT MIN(k.effective_start_date) FROM staging.stg_ks_contingent_worker AS k
            WHERE k.person_id = s.person_id AND k.bw_worker_id IS DISTINCT FROM s.bw_worker_id
              AND k.effective_start_date <= s.month_end_date),
           s.bw_service_order_id, NULL, NULL,
           'Keystone stores ' || COALESCE('Bridgeway ID ' || s.ks_stored_bw_worker_id, 'no Bridgeway ID')
           || '; matched to ' || s.bw_worker_id || ' on name, supplier and start (' ||
           CASE s.match_tier WHEN 2 THEN 'Medium' ELSE 'Low' END || ' confidence)'
    FROM snap AS s
    WHERE s.match_status = 'Matched' AND s.link_differs
),

second_id AS (
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id, 'CW07', 'CW07', 'identity',
           s.bw_contract_start_date, s.bw_service_order_id, NULL, NULL,
           'Bridgeway ' || s.bw_worker_id || ' started ' || CAST(s.bw_contract_start_date AS VARCHAR)
           || ' as a new engagement; ' || p.bw_worker_id || ', same name and supplier, ended ' || CAST(p.last_day AS VARCHAR)
    FROM snap AS s
    JOIN staging.stg_bw_contingent_worker AS w ON w.bw_worker_id = s.bw_worker_id
    JOIN (SELECT b.bw_worker_id, b.first_name, b.last_name, b.supplier_id, MAX(r.assignment_end_date) AS last_day,
                 ARG_MAX(r.cost_center_code, r.assignment_end_date) AS last_cost_center
          FROM staging.stg_bw_contingent_worker AS b
          JOIN staging.stg_bw_service_order AS o ON o.bw_worker_id = b.bw_worker_id
          JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = o.service_order_id AND r.is_current
          WHERE r.status IN ('Approved', 'Closed')
          GROUP BY ALL) AS p
      ON p.first_name = w.first_name AND p.last_name = w.last_name AND p.supplier_id = w.supplier_id
     AND p.bw_worker_id <> w.bw_worker_id
     AND w.original_start_date = p.last_day + 1
    WHERE p.last_cost_center = (SELECT r0.cost_center_code
                                FROM staging.stg_bw_service_order AS o0
                                JOIN staging.stg_bw_service_order_revision AS r0
                                  ON r0.service_order_id = o0.service_order_id AND r0.revision_no = 0
                                WHERE o0.bw_worker_id = w.bw_worker_id
                                ORDER BY r0.assignment_start_date LIMIT 1)
),

over_cap AS (
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id, 'CW10', 'CW10', 'engagement',
           CAST(s.bw_contract_start_date + INTERVAL 48 MONTH AS DATE), s.bw_service_order_id, NULL, NULL,
           s.cw_type || ' working since ' || CAST(s.bw_contract_start_date AS VARCHAR) || ': 48 months reached '
           || CAST(CAST(s.bw_contract_start_date + INTERVAL 48 MONTH AS DATE) - 1 AS VARCHAR)
           || '; contract now to ' || CAST(s.bw_contract_end_date AS VARCHAR)
    FROM snap AS s
    WHERE s.bw_working AND s.cw_type IN ('Contractor', 'Consultant')
      AND s.month_end_date >= s.bw_contract_start_date + INTERVAL 48 MONTH
),

not_closed AS (
    SELECT cal.month_end_date, i.identity_id, o.bw_worker_id, i.person_id, 'CW04', 'CW04', 'order',
           CAST(r.assignment_end_date + INTERVAL 16 DAY AS DATE), r.service_order_id, NULL, NULL,
           'Order ' || r.service_order_id || ': last day ' || CAST(r.assignment_end_date AS VARCHAR)
           || ', still ' || r.status || ' on the month-end'
    FROM intermediate.int_month_end_calendar AS cal
    JOIN staging.stg_bw_service_order_revision AS r
      ON r.effective_start_date <= cal.month_end_date AND r.effective_end_date_filled >= cal.month_end_date
     AND r.status = 'Approved' AND r.assignment_end_date + INTERVAL 16 DAY <= cal.month_end_date
    JOIN staging.stg_bw_service_order AS o ON o.service_order_id = r.service_order_id
    LEFT JOIN intermediate.int_cw_identity_resolution AS i ON i.bw_worker_id = o.bw_worker_id
    -- not an order that was later extended: that was a late approval, the worker came back on it
    WHERE NOT EXISTS (SELECT 1 FROM staging.stg_bw_service_order_revision AS later
                      WHERE later.service_order_id = r.service_order_id
                        AND later.effective_start_date > cal.month_end_date
                        AND later.assignment_end_date > r.assignment_end_date)
),

billed_after AS (
    SELECT t.month_end_date, i.identity_id, t.bw_worker_id, i.person_id, 'CW11', 'CW11', 'timesheet',
           CAST(DATE_TRUNC('month', t.month_end_date) AS DATE), t.service_order_id, NULL, t.timesheet_id,
           'Timesheet ' || t.timesheet_id || ' bills ' || CAST(t.billed_units AS VARCHAR) || ' units for '
           || STRFTIME(t.month_end_date, '%B %Y') || '; the assignment ended ' || CAST(r.assignment_end_date AS VARCHAR)
    FROM staging.stg_bw_timesheet_month AS t
    JOIN staging.stg_bw_service_order_revision AS r
      ON r.service_order_id = t.service_order_id
     AND r.effective_start_date <= t.month_end_date AND r.effective_end_date_filled >= t.month_end_date
    LEFT JOIN intermediate.int_cw_identity_resolution AS i ON i.bw_worker_id = t.bw_worker_id
    WHERE DATE_TRUNC('month', t.month_end_date) > r.assignment_end_date
),

all_lines AS (
    SELECT month_end_date, identity_id, bw_worker_id, person_id, discrepancy_code, root_cause_code, grp,
           since_date, service_order_id, feed_event_id, timesheet_id, evidence FROM field_lines
    UNION ALL SELECT * FROM missing_record
    UNION ALL SELECT * FROM keystone_only
    UNION ALL SELECT * FROM broken_link
    UNION ALL SELECT * FROM second_id
    UNION ALL SELECT * FROM over_cap
    UNION ALL SELECT * FROM not_closed
    UNION ALL SELECT * FROM billed_after
)

-- one row per month-end, identity (or order / timesheet) and type: field groups merged
SELECT
    month_end_date,
    identity_id,
    ANY_VALUE(bw_worker_id)                                                AS bw_worker_id,
    ANY_VALUE(person_id)                                                   AS person_id,
    discrepancy_code,
    MIN(root_cause_code)                                                   AS root_cause_code,
    ARRAY_TO_STRING(LIST_SORT(LIST(DISTINCT CASE grp WHEN 'contract' THEN 'Status and contract dates' WHEN 'cost_center' THEN 'Cost center'
                                 WHEN 'manager' THEN 'Manager' WHEN 'office' THEN 'Office' WHEN 'record' THEN 'Whole record'
                                 WHEN 'link' THEN 'Bridgeway worker ID' WHEN 'identity' THEN 'Bridgeway worker ID; Keystone person'
                                 WHEN 'engagement' THEN 'Engagement length' WHEN 'order' THEN 'Order status'
                                 ELSE 'Timesheet' END)), '; ')                AS fields_affected,
    MIN(since_date)                                                        AS since_date,
    month_end_date - MIN(since_date)                                       AS age_days,
    ANY_VALUE(service_order_id)                                            AS service_order_id,
    ANY_VALUE(feed_event_id)                                               AS feed_event_id,
    ANY_VALUE(timesheet_id)                                                AS timesheet_id,
    STRING_AGG(evidence, ' | ' ORDER BY grp)                               AS evidence
FROM all_lines
GROUP BY month_end_date, identity_id, discrepancy_code, COALESCE(service_order_id, ''), COALESCE(timesheet_id, '');
