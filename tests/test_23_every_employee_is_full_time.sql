-- Release 3 removed part-time: every employee is 1.0 FTE. Returns any job record below
-- 1.0 FTE, and any headcount walk line whose FTE differs from its headcount (which would
-- mean a part-time worker or an FTE movement slipped back in). Replaces release 2's
-- part-time control.
SELECT 'job record' AS source, CAST(job_record_id AS VARCHAR) AS id, fte, NULL AS headcount
FROM staging.stg_job_history
WHERE fte <> 1

UNION ALL

SELECT 'walk line', CAST(month_end_date AS VARCHAR) || ' ' || department_id || ' ' || movement_reason,
       fte, headcount
FROM marts.mart_headcount_fte_walk
WHERE fte <> headcount
