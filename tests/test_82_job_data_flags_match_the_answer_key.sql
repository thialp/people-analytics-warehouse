-- Keystone job data: on every close, the warehouse finds exactly the people the answer key says
-- hold two active job records (F07) or one active record on a PID the ledger shows they left
-- (F06), and no one else. The flags are built from Keystone and the PID ledger alone; the answer
-- key (gen_cw_job_defect, computed in Python by the generator) is read only here.
WITH truth AS (
    SELECT r.month_end_date, d.flag_code, d.person_id
    FROM intermediate.int_cw_close_run AS r
    JOIN staging.stg_gen_cw_job_defect AS d
      ON d.start_date <= r.month_end_date AND d.end_date_filled >= r.month_end_date
),
found AS (
    SELECT month_end_date, flag_code, person_id FROM intermediate.int_cw_flag WHERE cause_code = 'JOB'
)
SELECT 'seeded job defect missed' AS problem, t.* FROM truth AS t
WHERE NOT EXISTS (SELECT 1 FROM found AS f WHERE f.month_end_date = t.month_end_date
                  AND f.flag_code = t.flag_code AND f.person_id = t.person_id)
UNION ALL
SELECT 'job flag the answer key does not have', f.* FROM found AS f
WHERE NOT EXISTS (SELECT 1 FROM truth AS t WHERE t.month_end_date = f.month_end_date
                  AND t.flag_code = f.flag_code AND t.person_id = f.person_id)
