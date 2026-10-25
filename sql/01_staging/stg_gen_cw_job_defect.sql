-- stg_gen_cw_job_defect
-- The answer key for Keystone job data: every period a person holds two active job records (F07)
-- or one active record on a PID the ledger shows they left (F08). A test fixture, never a business
-- source: only test 82 reads it.
-- Source system: synthetic data generator (see generator/cw_operations.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_gen_cw_job_defect AS
SELECT
    NULLIF(defect_id, '')                                    AS defect_id,
    NULLIF(flag_code, '')                                    AS flag_code,
    NULLIF(person_id, '')                                    AS person_id,
    NULLIF(position_id, '')                                  AS position_id,
    CAST(NULLIF(start_date, '') AS DATE)                     AS start_date,
    CAST(NULLIF(end_date, '') AS DATE)                       AS end_date,
    COALESCE(CAST(NULLIF(end_date, '') AS DATE), DATE '9999-12-31') AS end_date_filled,
    NULLIF(origin, '')                                       AS origin,
    NULLIF(resolution, '')                                   AS resolution,
    NULLIF(detail, '')                                       AS detail
FROM raw.gen_cw_job_defect;
