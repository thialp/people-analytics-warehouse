-- Keystone's contingent worker history is a clean effective-dated record, and every version
-- is explained: a Feed version by an event that was applied that very day, a System version
-- by Keystone inactivating the worker the day after the contract end it held, and HR Ops or
-- Manager versions by hand (no feed event). Statuses carry a reason only when inactive, and
-- contingent person IDs never collide with an employee's.
WITH k AS (
    SELECT k.*,
           LAG(k.effective_end_date) OVER w     AS prev_end,
           LEAD(k.effective_start_date) OVER w  AS next_start,
           SUM(CASE WHEN k.effective_end_date IS NULL THEN 1 ELSE 0 END)
               OVER (PARTITION BY k.person_id)  AS open_versions
    FROM staging.stg_ks_contingent_worker AS k
    WINDOW w AS (PARTITION BY k.person_id ORDER BY k.effective_start_date)
)
SELECT ks_record_id, 'gap or overlap with the previous version' AS problem
FROM k WHERE prev_end IS NOT NULL AND effective_start_date <> prev_end + INTERVAL 1 DAY
UNION ALL
SELECT ks_record_id, 'open-ended version that is not the last' FROM k WHERE effective_end_date IS NULL AND next_start IS NOT NULL
UNION ALL
SELECT MIN(ks_record_id), 'not exactly one current version' FROM k WHERE open_versions <> 1 GROUP BY person_id
UNION ALL
SELECT ks_record_id, 'version dated after the extract' FROM k WHERE effective_start_date > DATE '2026-06-30'
UNION ALL
SELECT k.ks_record_id, 'feed version without an event applied that day'
FROM k LEFT JOIN staging.stg_feed_bridgeway_keystone_event AS f USING (feed_event_id)
WHERE k.change_source = 'Feed'
  AND (f.feed_event_id IS NULL OR f.applied_date IS DISTINCT FROM k.effective_start_date)
UNION ALL
SELECT ks_record_id, 'feed event on a version written by hand or by Keystone'
FROM k WHERE change_source <> 'Feed' AND feed_event_id IS NOT NULL
UNION ALL
SELECT ks_record_id, 'Keystone inactivation not the day after the contract end'
FROM k
WHERE change_source = 'System'
  AND (status <> 'Inactive' OR effective_start_date <> contract_end_date + INTERVAL 1 DAY)
UNION ALL
SELECT ks_record_id, 'unknown change source' FROM k WHERE change_source NOT IN ('Feed', 'System', 'HR Ops', 'Manager')
UNION ALL
SELECT ks_record_id, 'inactive reason does not match the status'
FROM k WHERE (status = 'Inactive') <> (inactive_reason IS NOT NULL) OR status NOT IN ('Active', 'Inactive')
UNION ALL
SELECT DISTINCT k.person_id, 'contingent person ID used by an employee'
FROM k JOIN staging.stg_worker AS w ON w.worker_id = k.person_id
