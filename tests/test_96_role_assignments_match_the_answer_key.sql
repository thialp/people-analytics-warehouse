-- Release 7 role assignments: dates in order, and on every month-end an assignment still names a
-- former leader (int_assignment_signal) exactly when the answer key seeded it (R1).
WITH m AS (SELECT DISTINCT month_end_date FROM intermediate.int_person_month_end),
key AS (
    SELECT m.month_end_date, t.assignment_id
    FROM staging.stg_gen_org_drift_truth AS t
    JOIN m ON m.month_end_date BETWEEN t.start_date AND COALESCE(t.end_date, DATE '9999-12-31')
    WHERE t.signal_code = 'R1'
)
SELECT 'dates out of order' AS problem, assignment_id, CAST(effective_start_date AS VARCHAR) AS detail
FROM staging.stg_role_assignment WHERE effective_end_date < effective_start_date
UNION ALL
SELECT 'found, not seeded', s.assignment_id, CAST(s.month_end_date AS VARCHAR)
FROM intermediate.int_assignment_signal AS s ANTI JOIN key AS k USING (month_end_date, assignment_id)
UNION ALL
SELECT 'seeded, not found', k.assignment_id, CAST(k.month_end_date AS VARCHAR)
FROM key AS k ANTI JOIN intermediate.int_assignment_signal AS s USING (month_end_date, assignment_id)
