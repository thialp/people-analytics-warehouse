-- stg_ks_cw_job
-- Keystone job data for contingent workers (SCD Type 2): which PID each job record (EMPLID x
-- record number) holds, Active or Terminated. A person should hold one active record, on the
-- PID the PID ledger (stg_cw_position_assignment) shows them in; the reconciliation flags the
-- rest (F07 two active records, F06 still in a PID after leaving it).
-- Source system: Keystone HR (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_ks_cw_job AS
SELECT
    NULLIF(job_record_id, '')                                AS job_record_id,
    NULLIF(person_id, '')                                    AS person_id,
    CAST(NULLIF(empl_rcd, '') AS INTEGER)                    AS empl_rcd,
    NULLIF(position_id, '')                                  AS position_id,
    CAST(NULLIF(effective_start_date, '') AS DATE)           AS effective_start_date,
    CAST(NULLIF(effective_end_date, '') AS DATE)             AS effective_end_date,
    COALESCE(CAST(NULLIF(effective_end_date, '') AS DATE),
             DATE '9999-12-31')                              AS effective_end_date_filled,
    NULLIF(job_status, '')                                   AS job_status,
    NULLIF(action, '')                                       AS action,
    NULLIF(change_source, '')                                AS change_source,
    NULLIF(assignment_id, '')                                AS assignment_id
FROM raw.ks_cw_job;
