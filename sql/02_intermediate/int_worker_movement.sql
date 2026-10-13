-- int_worker_movement
-- Grain: one row per worker per month, for every worker active at the prior
-- month-end, at the current month-end, or at both.
--
-- It compares each worker's state at two consecutive month-end snapshots and
-- classifies what happened in between. A "slice" is the combination of
-- department, country, job family and grade: the attributes a headcount walk is
-- usually cut by. Any change of slice is an internal move.
--
--   active at prior only            -> Termination (voluntary or involuntary)
--   active at current only          -> Hire
--   active at both, slice changed   -> Internal Move (out of the old slice, into the new)
--   active at both, FTE changed     -> FTE Change (FTE only, no headcount effect)
--
-- When several slice attributes change in the same month, ONE reason is
-- recorded, in this order of precedence:
--   department changed  -> Reorganization (if a reorg action is on file that month), else Transfer
--   country changed     -> Location Change
--   grade went up/down  -> Promotion / Demotion
--   job family changed  -> Job Change
--
-- Office (location_id) is carried for the location marts but is not part of
-- the slice: a move between two offices in the same country is a relocation in
-- mart_location_headcount, not an internal move in the headcount walk.
--
-- Workers hired and terminated inside the same month appear in neither
-- snapshot, so a month-end walk never sees them. They are counted separately in
-- int_worker_in_month_hire_and_exit rather than silently lost.
CREATE OR REPLACE TABLE intermediate.int_worker_movement AS
WITH month_pairs AS (
    SELECT month_end_date, prior_month_end_date
    FROM intermediate.int_month_end_calendar
    WHERE prior_month_end_date IS NOT NULL
),

snap AS (
    SELECT month_end_date, worker_id, department_id, location_id, country_code, job_family, grade, fte
    FROM intermediate.int_worker_month_end_snapshot
),

-- everyone active at either end of each month
population AS (
    SELECT mp.month_end_date, mp.prior_month_end_date, s.worker_id
    FROM month_pairs AS mp
    JOIN snap AS s ON s.month_end_date = mp.prior_month_end_date
    UNION
    SELECT mp.month_end_date, mp.prior_month_end_date, s.worker_id
    FROM month_pairs AS mp
    JOIN snap AS s ON s.month_end_date = mp.month_end_date
),

-- job actions that took effect during the month, used to label department moves
actions AS (
    SELECT
        mp.month_end_date,
        j.worker_id,
        BOOL_OR(j.action_reason = 'Reorganization') AS had_reorganization
    FROM month_pairs AS mp
    JOIN staging.stg_job_history AS j
      ON j.effective_start_date >  mp.prior_month_end_date
     AND j.effective_start_date <= mp.month_end_date
    GROUP BY ALL
),

compared AS (
    SELECT
        p.month_end_date,
        p.prior_month_end_date,
        p.worker_id,
        w.is_executive_officer,
        pri.worker_id IS NOT NULL AS in_prior,
        cur.worker_id IS NOT NULL AS in_current,
        pri.department_id AS prior_department_id, cur.department_id AS current_department_id,
        pri.location_id   AS prior_location_id,   cur.location_id   AS current_location_id,
        pri.country_code  AS prior_country_code,  cur.country_code  AS current_country_code,
        pri.job_family    AS prior_job_family,    cur.job_family    AS current_job_family,
        pri.grade         AS prior_grade,         cur.grade         AS current_grade,
        pri.fte           AS prior_fte,           cur.fte           AS current_fte,
        w.termination_type,
        COALESCE(a.had_reorganization, FALSE) AS had_reorganization
    FROM population AS p
    JOIN staging.stg_worker AS w ON w.worker_id = p.worker_id
    LEFT JOIN snap AS pri ON pri.month_end_date = p.prior_month_end_date AND pri.worker_id = p.worker_id
    LEFT JOIN snap AS cur ON cur.month_end_date = p.month_end_date       AND cur.worker_id = p.worker_id
    LEFT JOIN actions AS a ON a.month_end_date  = p.month_end_date       AND a.worker_id   = p.worker_id
)

SELECT
    *,
    CASE
        WHEN in_current AND NOT in_prior THEN 'Hire'
        WHEN in_prior AND NOT in_current THEN 'Termination'
        WHEN prior_department_id <> current_department_id
          OR prior_country_code  <> current_country_code
          OR prior_job_family    <> current_job_family
          OR prior_grade         <> current_grade      THEN 'Internal Move'
        ELSE 'No Change'
    END AS movement_type,
    CASE
        WHEN in_current AND NOT in_prior THEN 'New Hire'
        WHEN in_prior AND NOT in_current THEN COALESCE(termination_type, 'Unknown')
        WHEN prior_department_id <> current_department_id
            THEN CASE WHEN had_reorganization THEN 'Reorganization' ELSE 'Transfer' END
        WHEN prior_country_code <> current_country_code THEN 'Location Change'
        WHEN current_grade > prior_grade                 THEN 'Promotion'
        WHEN current_grade < prior_grade                 THEN 'Demotion'
        WHEN prior_job_family <> current_job_family      THEN 'Job Change'
    END AS movement_reason,
    in_prior AND in_current AND prior_fte <> current_fte AS fte_changed
FROM compared;

