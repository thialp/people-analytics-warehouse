-- mart_cw_pid_fill
-- Grain: one row per contingent assignment that starts in a PID (release 3.1): when, where, and
-- whether the PID was held before (a contingent backfill) or new. Feeds the Workforce Planning
-- summary's contingent fills, and its Custom SQL through rpt.vw_cw_pid_fill.
CREATE OR REPLACE TABLE marts.mart_cw_pid_fill AS
SELECT
    a.assignment_id,
    a.position_id,
    a.start_date,
    YEAR(a.start_date) + CASE WHEN MONTH(a.start_date) >= 7 THEN 1 ELSE 0 END  AS fiscal_year,
    ((MONTH(a.start_date) + 5) % 12) // 3 + 1                                  AS fiscal_quarter,
    a.is_backfill,
    p.department_id,
    l.country_name
FROM (SELECT x.*, LAG(x.assignment_id) OVER (PARTITION BY x.position_id ORDER BY x.start_date) IS NOT NULL AS is_backfill
      FROM staging.stg_cw_position_assignment AS x) AS a
JOIN staging.stg_cw_position AS p
  ON p.position_id = a.position_id AND a.start_date BETWEEN p.effective_start_date AND p.effective_end_date_filled
JOIN staging.stg_location AS l ON l.location_id = p.location_id
ORDER BY a.assignment_id;
