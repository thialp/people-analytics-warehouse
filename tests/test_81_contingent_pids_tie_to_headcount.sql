-- Every contingent worker holds a PID in Keystone (release 3.1). Returns the rows that break:
--   1. filled contingent PIDs equal the contingent headcount (int_cw_month_end_snapshot) on every
--      month-end, by department and country: the PID view and the people view agree
--   2. a contingent PID never has two holders at once, and its history has no gaps or overlaps
--   3. a contingent PID is Filled exactly when someone holds it
--   4. a PID created for a request is created on or before the worker's first day
WITH pid AS (
    SELECT month_end_date, department_id, country_code, COUNT(*) AS n
    FROM intermediate.int_cw_position_snapshot WHERE status = 'Filled' GROUP BY ALL
),
hc AS (
    SELECT month_end_date, department_id, country_code, COUNT(*) AS n
    FROM intermediate.int_cw_month_end_snapshot GROUP BY ALL
),
checks AS (
    SELECT 'filled contingent PIDs differ from the contingent headcount' AS rule, COUNT(*) AS n
    FROM pid FULL JOIN hc USING (month_end_date, department_id, country_code)
    WHERE COALESCE(pid.n, 0) <> COALESCE(hc.n, 0)
    UNION ALL
    SELECT 'two holders at once', COUNT(*)
    FROM staging.stg_cw_position_assignment AS a
    JOIN staging.stg_cw_position_assignment AS b
      ON a.position_id = b.position_id AND a.assignment_id < b.assignment_id
     AND a.start_date <= b.end_date_filled AND b.start_date <= a.end_date_filled
    UNION ALL
    SELECT 'PID history has a gap or an overlap', COUNT(*)
    FROM (SELECT effective_start_date,
                 LAG(effective_end_date_filled) OVER (PARTITION BY position_id ORDER BY effective_start_date) AS prev_end
          FROM staging.stg_cw_position) AS h
    WHERE prev_end IS NOT NULL AND effective_start_date <> prev_end + INTERVAL 1 DAY
    UNION ALL
    SELECT 'status does not match the holder', COUNT(*)
    FROM intermediate.int_cw_position_snapshot
    WHERE (status = 'Filled') <> (incumbent_bw_worker_id IS NOT NULL)
    UNION ALL
    SELECT 'PID created after the worker started', COUNT(*)
    FROM staging.stg_cw_position_assignment AS a
    JOIN (SELECT DISTINCT position_id, created_date FROM staging.stg_cw_position) AS p USING (position_id)
    WHERE p.created_date > a.start_date
)
SELECT rule, n FROM checks WHERE n <> 0
