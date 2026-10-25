-- int_cw_load_gap
-- Grain: one row per close x contractor x flag that exists only because a load failed.
--
-- When the close run's read of a source fails, the warehouse keeps that source's last good load:
-- the source is stale, as of an earlier day (int_cw_close_run: a day after one failed night, more
-- after an outage). Anything the source changed since then looks like a gap, although the two
-- systems agreed at the month-end. These are the gaps the routing rule sends to Integration with
-- "Alert data engineering":
--
--   Keystone stale   a contractor whose Keystone record changed after the stale date (the feed
--                    applied a change, or someone fixed it) is compared to Bridgeway as Keystone
--                    stood then: not created yet (F12), status (F09, F11), cost center (F01, F02)
--   Bridgeway stale  a worker Bridgeway sent a change for after the stale date that Keystone
--                    applied by the month-end: Keystone is compared to what Bridgeway had sent by
--                    then: a new worker (F10), status (F09, F11), cost center (F01, F02)
--
-- Only differences the true data does not have are kept: a real gap stays a real gap.
CREATE OR REPLACE TABLE intermediate.int_cw_load_gap AS
WITH runs AS (
    SELECT * FROM intermediate.int_cw_close_run
    WHERE ks_data_as_of < month_end_date OR bw_data_as_of < month_end_date
),
snap AS (SELECT * FROM intermediate.int_cw_reconciliation_snapshot),
cc AS (SELECT cost_center_id, function_name FROM staging.stg_cost_center),

-- Keystone a day stale ------------------------------------------------------------------------
ks_changed AS (
    SELECT r.month_end_date, r.ks_run_id, r.ks_data_as_of, s.*,
           o.ks_record_id AS old_record_id, o.status AS old_status, o.contract_end_date AS old_end,
           o.cost_center_id AS old_cost_center_id
    FROM runs AS r
    JOIN snap AS s ON s.month_end_date = r.month_end_date
    LEFT JOIN staging.stg_ks_contingent_worker AS o
      ON o.person_id = s.person_id AND o.effective_start_date <= r.ks_data_as_of
     AND o.effective_end_date_filled >= r.ks_data_as_of
    WHERE r.ks_data_as_of < r.month_end_date AND s.ks_version_start_date > r.ks_data_as_of
),
ks_gaps AS (
    SELECT month_end_date, identity_id, bw_worker_id, person_id, 'F12' AS flag_code, ks_run_id AS run_id,
           'No record (created ' || CAST(ks_version_start_date AS VARCHAR) || ', after the last Keystone load)' AS keystone_shows,
           'Working since ' || CAST(bw_contract_start_date AS VARCHAR) AS bridgeway_has
    FROM ks_changed WHERE old_record_id IS NULL AND bw_working AND ks_exists
    UNION ALL
    SELECT month_end_date, identity_id, bw_worker_id, person_id,
           CASE WHEN bw_active THEN 'F11' ELSE 'F09' END, ks_run_id,
           CASE WHEN old_status = 'Active' THEN 'Active' ELSE 'Inactive' END || ', contract to ' || CAST(old_end AS VARCHAR)
               || ' (as of ' || CAST(ks_data_as_of AS VARCHAR) || ')',
           CASE WHEN bw_active THEN 'Working, contract to ' ELSE 'Ended ' END || CAST(bw_contract_end_date AS VARCHAR)
    FROM ks_changed
    WHERE old_record_id IS NOT NULL AND bw_service_order_id IS NOT NULL
      AND bw_active <> (old_status = 'Active') AND bw_active = ks_active
    UNION ALL
    SELECT k.month_end_date, k.identity_id, k.bw_worker_id, k.person_id,
           CASE WHEN oc.function_name IS DISTINCT FROM bc.function_name THEN 'F01' ELSE 'F02' END, k.ks_run_id,
           'Cost center ' || k.old_cost_center_id || ' (as of ' || CAST(k.ks_data_as_of AS VARCHAR) || ')',
           'Cost center ' || k.bw_cost_center_id
    FROM ks_changed AS k
    LEFT JOIN cc AS oc ON oc.cost_center_id = k.old_cost_center_id
    LEFT JOIN cc AS bc ON bc.cost_center_id = k.bw_cost_center_id
    WHERE k.old_record_id IS NOT NULL AND k.bw_service_order_id IS NOT NULL
      AND k.old_cost_center_id IS DISTINCT FROM k.bw_cost_center_id
      AND k.ks_cost_center_id IS NOT DISTINCT FROM k.bw_cost_center_id
),

-- Bridgeway a day stale -----------------------------------------------------------------------
sent AS (    -- every change sent, with what it says (as int_cw_reconciliation_snapshot reads it)
    SELECT f.bw_worker_id, f.sent_date, f.event_type, f.revision_id, r.assignment_end_date, r.cost_center_code
    FROM staging.stg_feed_bridgeway_keystone_event AS f
    JOIN staging.stg_bw_service_order_revision AS r USING (revision_id)
),
bw_touched AS (    -- workers Bridgeway sent a change for after the stale date, applied by the month-end
    SELECT DISTINCT r.month_end_date, r.bw_run_id, r.bw_data_as_of, f.bw_worker_id
    FROM runs AS r
    JOIN staging.stg_feed_bridgeway_keystone_event AS f
      ON f.sent_date > r.bw_data_as_of AND f.applied_date <= r.month_end_date
    WHERE r.bw_data_as_of < r.month_end_date
),
bw_stale AS (
    SELECT t.month_end_date, t.bw_run_id, t.bw_data_as_of, t.bw_worker_id,
           (SELECT ARG_MAX(s.assignment_end_date, (s.sent_date, s.event_type = 'New Worker', s.revision_id))
            FROM sent AS s WHERE s.bw_worker_id = t.bw_worker_id AND s.sent_date <= t.bw_data_as_of
              AND s.event_type <> 'Attribute Change')                                          AS stale_end,
           (SELECT ARG_MAX(s.cost_center_code, (s.sent_date, s.event_type = 'New Worker', s.revision_id))
            FROM sent AS s WHERE s.bw_worker_id = t.bw_worker_id AND s.sent_date <= t.bw_data_as_of) AS stale_cost_center_id
    FROM bw_touched AS t
),
bw_gaps AS (
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id, 'F10' AS flag_code, b.bw_run_id AS run_id,
           'Active since ' || CAST(s.ks_contract_start_date AS VARCHAR) AS keystone_shows,
           'No worker (sent after the last Bridgeway load, ' || CAST(b.bw_data_as_of AS VARCHAR) || ')' AS bridgeway_has
    FROM bw_stale AS b
    JOIN snap AS s ON s.month_end_date = b.month_end_date AND s.bw_worker_id = b.bw_worker_id
    WHERE b.stale_end IS NULL AND s.ks_working
    UNION ALL
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id,
           CASE WHEN b.stale_end >= s.month_end_date THEN 'F11' ELSE 'F09' END, b.bw_run_id,
           CASE WHEN s.ks_active THEN 'Active' ELSE 'Inactive' END || ', contract to ' || CAST(s.ks_contract_end_date AS VARCHAR),
           CASE WHEN b.stale_end >= s.month_end_date THEN 'Working, contract to ' ELSE 'Ended ' END
               || CAST(b.stale_end AS VARCHAR) || ' (as sent by ' || CAST(b.bw_data_as_of AS VARCHAR) || ')'
    FROM bw_stale AS b
    JOIN snap AS s ON s.month_end_date = b.month_end_date AND s.bw_worker_id = b.bw_worker_id
    WHERE b.stale_end IS NOT NULL AND s.ks_record_id IS NOT NULL
      AND (b.stale_end >= s.month_end_date) <> s.ks_active AND s.bw_active = s.ks_active
    UNION ALL
    SELECT s.month_end_date, s.identity_id, s.bw_worker_id, s.person_id,
           CASE WHEN oc.function_name IS DISTINCT FROM kc.function_name THEN 'F01' ELSE 'F02' END, b.bw_run_id,
           'Cost center ' || s.ks_cost_center_id,
           'Cost center ' || b.stale_cost_center_id || ' (as sent by ' || CAST(b.bw_data_as_of AS VARCHAR) || ')'
    FROM bw_stale AS b
    JOIN snap AS s ON s.month_end_date = b.month_end_date AND s.bw_worker_id = b.bw_worker_id
    LEFT JOIN cc AS oc ON oc.cost_center_id = b.stale_cost_center_id
    LEFT JOIN cc AS kc ON kc.cost_center_id = s.ks_cost_center_id
    WHERE b.stale_cost_center_id IS NOT NULL AND s.ks_record_id IS NOT NULL
      AND b.stale_cost_center_id IS DISTINCT FROM s.ks_cost_center_id
      AND s.bw_cost_center_id IS NOT DISTINCT FROM s.ks_cost_center_id
)

SELECT g.month_end_date, g.identity_id, g.bw_worker_id, g.person_id, g.flag_code,
       CASE WHEN g.run_id = r.ks_run_id THEN 'Keystone stale' ELSE 'Bridgeway stale' END AS cause_detail,
       CASE WHEN g.run_id = r.ks_run_id THEN r.ks_data_as_of ELSE r.bw_data_as_of END + 1  AS since_date,
       CASE WHEN g.run_id = r.ks_run_id
            THEN 'Keystone load ' || g.run_id || ' failed at the close; the warehouse still holds Keystone as of '
                 || CAST(r.ks_data_as_of AS VARCHAR) || ', before this record changed'
            ELSE 'Bridgeway load ' || g.run_id || ' failed at the close; the warehouse still holds Bridgeway as of '
                 || CAST(r.bw_data_as_of AS VARCHAR) || ', before a change Keystone has already applied' END AS evidence,
       g.keystone_shows,
       g.bridgeway_has
FROM (SELECT * FROM ks_gaps UNION ALL SELECT * FROM bw_gaps) AS g
JOIN intermediate.int_cw_close_run AS r USING (month_end_date);
