-- Release 7 detection: on every month-end, every person-level gap the generator seeded (S1 borrowed
-- reporting line, M1 matrix for another country, M2 not one country matrix, M3 left in an ended
-- matrix) is found by int_alignment_signal for people Keystone holds, and every S1 (employees), M1
-- and M2 the warehouse finds was seeded. Contingent S1 and S2 are not seeded: they come from the data
-- as it is. M3 for a leaderless matrix is checked by test 95.
WITH m AS (SELECT DISTINCT month_end_date FROM intermediate.int_person_month_end),
seeded AS (
    SELECT DISTINCT m.month_end_date, t.signal_code, t.person_id
    FROM staging.stg_gen_org_drift_truth AS t
    JOIN m ON m.month_end_date BETWEEN t.start_date AND COALESCE(t.end_date, DATE '9999-12-31')
    JOIN intermediate.int_person_month_end AS p
      ON p.month_end_date = m.month_end_date AND p.person_id = t.person_id
     AND p.has_keystone_record AND NOT p.is_executive_officer
    WHERE t.person_id IS NOT NULL
),
found AS (
    SELECT s.month_end_date, s.signal_code, s.person_id
    FROM intermediate.int_alignment_signal AS s
    JOIN intermediate.int_person_month_end AS p USING (month_end_date, person_id)
    WHERE s.signal_code IN ('M1', 'M2') OR (s.signal_code = 'S1' AND p.worker_type = 'Employee')
)
SELECT 'seeded, not found' AS problem, sd.* FROM seeded AS sd
ANTI JOIN intermediate.int_alignment_signal AS s USING (month_end_date, signal_code, person_id)
UNION ALL
SELECT 'found, not seeded', f.* FROM found AS f
ANTI JOIN seeded AS sd USING (month_end_date, signal_code, person_id)
