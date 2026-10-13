-- int_position_history
-- Grain: one row per seat record (the SCD2 history in stg_position), with what the
-- seat-level models need beside it: how long the seat has been in its current status
-- (consecutive records with the same status form one run), the office's country and
-- pay zone, the job family, and whether it is a manager seat.
CREATE OR REPLACE TABLE intermediate.int_position_history AS
WITH flagged AS (
    SELECT p.*,
           LAG(p.status) OVER (PARTITION BY p.position_id ORDER BY p.effective_start_date) AS prev_status
    FROM staging.stg_position AS p
),
runs AS (
    SELECT *,
           SUM(CASE WHEN status = prev_status THEN 0 ELSE 1 END)
               OVER (PARTITION BY position_id ORDER BY effective_start_date) AS run_id
    FROM flagged
)
SELECT
    r.position_record_id,
    r.position_id,
    r.effective_start_date,
    r.effective_end_date,
    r.effective_end_date_filled,
    r.change_reason,
    r.status,
    MIN(r.effective_start_date) OVER (PARTITION BY r.position_id, r.run_id) AS status_since,
    r.department_id,
    r.cost_center_id,
    r.location_id,
    l.country_code,
    l.currency_code,
    l.pay_zone_factor,
    r.job_profile_id,
    jp.job_family_code,
    jp.job_family,
    r.grade,
    jp.career_track <> 'Individual Contributor'                            AS is_manager_seat,
    r.fte,
    r.created_date,
    r.created_reason
FROM runs AS r
JOIN staging.stg_location    AS l  ON l.location_id     = r.location_id
JOIN staging.stg_job_profile AS jp ON jp.job_profile_id = r.job_profile_id;
