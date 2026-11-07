-- stg_gen_org_drift_truth
-- The answer key: every org design gap the generator seeded (a test fixture, never a
-- business source).
-- Source: gen_org_drift_truth (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_gen_org_drift_truth AS
SELECT
    NULLIF(drift_id, '')                                     AS drift_id,
    NULLIF(signal_code, '')                                  AS signal_code,
    NULLIF(cause, '')                                        AS cause,
    NULLIF(person_id, '')                                    AS person_id,
    NULLIF(matrix_org_id, '')                                AS matrix_org_id,
    NULLIF(assignment_id, '')                                AS assignment_id,
    NULLIF(job_record_ids, '')                               AS job_record_ids,
    NULLIF(original_values, '')                              AS original_values,
    NULLIF(seeded_value, '')                                 AS seeded_value,
    CAST(NULLIF(start_date, '') AS DATE)                     AS start_date,
    CAST(NULLIF(end_date, '') AS DATE)                       AS end_date,
    NULLIF(detail, '')                                       AS detail
FROM raw.gen_org_drift_truth;
