-- mart_pid_month_end
-- Grain: month-end x worker type x PID kind x stale flag x department x country (release 3.1).
-- The PID ledger: every PID in Keystone on every month-end, employee and contingent, counted as
--   Filled                    someone holds it
--   Vacant previously held    someone held it and left (resigned, was let go, moved, ended)
--   Vacant new                created for a request and never filled yet
-- is_stale: vacant for 90 days or more. Filled employee PIDs equal the employee headcount
-- (test 45) and filled contingent PIDs the contingent headcount (test 81). Feeds the Workforce
-- Planning summary (mart_wfp_summary) and, through rpt.vw_pid_month_end, its Custom SQL.
CREATE OR REPLACE TABLE marts.mart_pid_month_end AS
WITH rows AS (
    SELECT s.month_end_date, 'Employee' AS worker_type, 'Filled' AS pid_kind, FALSE AS is_stale,
           s.department_id, l.country_name
    FROM intermediate.int_position_snapshot AS s
    JOIN staging.stg_location AS l ON l.location_id = s.location_id
    WHERE s.status = 'Filled'
    UNION ALL
    SELECT s.month_end_date, 'Contingent', 'Filled', FALSE, s.department_id, l.country_name
    FROM intermediate.int_cw_position_snapshot AS s
    JOIN staging.stg_location AS l ON l.location_id = s.location_id
    WHERE s.status = 'Filled'
    UNION ALL
    SELECT v.month_end_date, v.worker_type,
           CASE WHEN v.vacated_by = 'Never filled' THEN 'Vacant new' ELSE 'Vacant previously held' END,
           v.is_stale, v.department_id, v.country_name
    FROM marts.mart_vacancy_pool AS v
)
SELECT month_end_date, worker_type, pid_kind, is_stale, department_id, country_name, COUNT(*) AS pids
FROM rows
GROUP BY ALL
ORDER BY ALL;
