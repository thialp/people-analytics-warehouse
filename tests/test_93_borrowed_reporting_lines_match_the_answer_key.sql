-- Release 7: after the FY25 reorganization or a department transfer, some people kept reporting to
-- their old manager in another department. The generator replaced manager_worker_id on those job
-- records and nothing else. Every replaced record is in the answer key, carries the manager the key
-- names, and the key lists as many original managers as records (so the history can be put back).
-- Test 25 checks the replaced managers still outrank their reports.
WITH k AS (
    SELECT drift_id, seeded_value, UNNEST(string_split(job_record_ids, ';')) AS job_record_id
    FROM staging.stg_gen_org_drift_truth
    WHERE signal_code = 'S1'
)
SELECT k.drift_id, k.job_record_id, j.manager_worker_id AS found, k.seeded_value AS expected
FROM k
LEFT JOIN staging.stg_job_history AS j USING (job_record_id)
WHERE j.job_record_id IS NULL OR j.manager_worker_id IS DISTINCT FROM k.seeded_value
UNION ALL
SELECT drift_id, NULL, CAST(len(string_split(original_values, ';')) AS VARCHAR),
       CAST(len(string_split(job_record_ids, ';')) AS VARCHAR)
FROM staging.stg_gen_org_drift_truth
WHERE signal_code = 'S1' AND len(string_split(original_values, ';')) <> len(string_split(job_record_ids, ';'))
