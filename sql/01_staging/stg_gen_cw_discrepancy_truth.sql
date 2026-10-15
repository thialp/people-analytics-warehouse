-- stg_gen_cw_discrepancy_truth
-- The answer key: every discrepancy the generator seeded between Bridgeway and Keystone (and
-- Bridgeway's own hygiene problems), with its cause and the days it was true. A test
-- fixture, never a business source: the warehouse detects discrepancies from the two
-- systems alone, and this table only scores how much of what was seeded it finds.
-- Source: generator/keystone_feed.py (system GEN). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_gen_cw_discrepancy_truth AS
SELECT
    NULLIF(discrepancy_id, '')                               AS discrepancy_id,
    NULLIF(discrepancy_code, '')                             AS discrepancy_code,
    NULLIF(root_cause_code, '')                              AS root_cause_code,
    NULLIF(bw_worker_id, '')                                 AS bw_worker_id,
    NULLIF(person_id, '')                                    AS person_id,
    NULLIF(service_order_id, '')                             AS service_order_id,
    NULLIF(feed_event_id, '')                                AS feed_event_id,
    NULLIF(timesheet_id, '')                                 AS timesheet_id,
    NULLIF(fields_affected, '')                              AS fields_affected,
    CAST(NULLIF(start_date, '') AS DATE)                     AS start_date,
    CAST(NULLIF(end_date, '') AS DATE)                       AS end_date,
    NULLIF(resolution, '')                                   AS resolution,
    NULLIF(detail, '')                                       AS detail,
    COALESCE(CAST(NULLIF(end_date, '') AS DATE),
             DATE '9999-12-31')                              AS end_date_filled
FROM raw.gen_cw_discrepancy_truth;
