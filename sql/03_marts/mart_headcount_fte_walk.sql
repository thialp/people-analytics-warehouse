-- mart_headcount_fte_walk
-- Grain: one row per month x worker type x slice x movement category x movement reason,
-- where a slice is department x country x job family x grade (contingent workers have no
-- job family or grade: theirs are empty).
--
-- Release 3: the walk covers the whole workforce. worker_type is Employee (Keystone HR) or
-- Contingent (Bridgeway VMS, as held at each month-end: int_cw_month_end_snapshot).
-- Contingent lines: Opening, Starts (New engagement / Returned after a lapse), Ends
-- (Completed / Ended early / Lapsed: approved late), Internal Moves (Transfer / Location
-- Change), Closing. A contingent worker hired as an employee is a Conversion: -1 for
-- Contingent and +1 for Employee in the same month and slice family, so the Total never moves;
-- such an employee is not in Hires. walk_step names each line the same way for both worker
-- types (Opening, Joined, Left, Moved out, Moved in, Converted, Closing), so a Total walk can
-- be drawn without mapping the two vocabularies. movement_order 7 (once FTE Changes) is
-- Conversions.
--
-- The headcount and FTE walk. For every slice and month:
--
--   Opening                      workers active at the prior month-end, in their prior slice
--   + Hires                      new workers, in their current slice
--   - Voluntary Terminations     leavers, in their prior slice
--   - Involuntary Terminations
--   - Internal Moves Out         workers who left this slice for another one
--   + Internal Moves In          workers who arrived from another slice
--   = Closing                    workers active at the month-end, in their current slice
--
-- Because a move is booked out of one slice and into another, the walk
-- reconciles at ANY roll-up of the slice: a promotion is a move between grades
-- that nets to zero for the department, and a transfer nets to zero for the
-- company.
--
-- Every employee is 1.0 FTE (release 3 removed part-time), so fte equals headcount
-- on every line; test 23 enforces it. The fte column stays so dashboards built on
-- it keep working. movement_order keeps its release 2 numbers (Closing is still 8;
-- 7 was FTE Changes and is no longer used), so sorts and calcs on it are unchanged.
--
-- The fact table carries codes only; names and hierarchies live in five small
-- dimension marts (mart_dim_*), which Tableau relates on matching field names.
-- That keeps the export small enough for GitHub and Tableau Public.
--
-- Headcount counts everyone, executive officers included. (They are excluded
-- only from the compensation marts, where pay is the sensitive part.) A contingent worker
-- counts 1.0 in the fte column, so fte = headcount on every line (test 23).
-- Sign convention: Opening and Closing are positive levels; movements carry
-- the sign of their effect.
CREATE OR REPLACE TABLE marts.mart_headcount_fte_walk AS
WITH m AS (
    SELECT mv.*, cv.worker_id IS NOT NULL AS is_conversion
    FROM intermediate.int_worker_movement AS mv
    LEFT JOIN intermediate.int_cw_conversion AS cv
           ON cv.worker_id = mv.worker_id AND cv.month_end_date = mv.month_end_date AND cv.is_walk_conversion
),

c AS (
    SELECT * FROM intermediate.int_cw_movement
),

job_families AS (
    SELECT DISTINCT job_family_code, job_family FROM staging.stg_job_profile
),

lines AS (
    -- Employees ----------------------------------------------------------------------------
    -- Opening
    SELECT month_end_date, 'Employee' AS worker_type, prior_department_id AS department_id,
           prior_country_code AS country_code, prior_job_family AS job_family, prior_grade AS grade,
           1 AS movement_order, 'Opening' AS movement_category, 'Opening' AS movement_reason,
           1 AS headcount, prior_fte AS fte
    FROM m WHERE in_prior

    UNION ALL
    -- Hires (a contingent worker hired as an employee is a Conversion, below)
    SELECT month_end_date, 'Employee', current_department_id, current_country_code, current_job_family, current_grade,
           2, 'Hires', movement_reason, 1, current_fte
    FROM m WHERE movement_type = 'Hire' AND NOT is_conversion

    UNION ALL
    -- Terminations, split by type
    SELECT month_end_date, 'Employee', prior_department_id, prior_country_code, prior_job_family, prior_grade,
           CASE WHEN movement_reason = 'Voluntary' THEN 3 ELSE 4 END,
           CASE WHEN movement_reason = 'Voluntary' THEN 'Voluntary Terminations'
                ELSE 'Involuntary Terminations' END,
           movement_reason, -1, -prior_fte
    FROM m WHERE movement_type = 'Termination'

    UNION ALL
    -- Internal moves: out of the old slice ...
    SELECT month_end_date, 'Employee', prior_department_id, prior_country_code, prior_job_family, prior_grade,
           5, 'Internal Moves Out', movement_reason, -1, -prior_fte
    FROM m WHERE movement_type = 'Internal Move'

    UNION ALL
    -- ... and into the new one, at the same (prior) FTE
    SELECT month_end_date, 'Employee', current_department_id, current_country_code, current_job_family, current_grade,
           6, 'Internal Moves In', movement_reason, 1, prior_fte
    FROM m WHERE movement_type = 'Internal Move'

    UNION ALL
    -- Conversions in: contingent workers hired as employees
    SELECT month_end_date, 'Employee', current_department_id, current_country_code, current_job_family, current_grade,
           7, 'Conversions', 'Contingent to Employee', 1, current_fte
    FROM m WHERE movement_type = 'Hire' AND is_conversion

    UNION ALL
    -- Closing
    SELECT month_end_date, 'Employee', current_department_id, current_country_code, current_job_family, current_grade,
           8, 'Closing', 'Closing', 1, current_fte
    FROM m WHERE in_current

    -- Contingent workers --------------------------------------------------------------------
    UNION ALL
    SELECT month_end_date, 'Contingent', prior_department_id, prior_country_code, NULL, NULL,
           1, 'Opening', 'Opening', 1, 1.0
    FROM c WHERE in_prior

    UNION ALL
    SELECT month_end_date, 'Contingent', current_department_id, current_country_code, NULL, NULL,
           2, 'Starts', movement_reason, 1, 1.0
    FROM c WHERE movement_type = 'Start'

    UNION ALL
    SELECT month_end_date, 'Contingent', prior_department_id, prior_country_code, NULL, NULL,
           3, 'Ends', movement_reason, -1, -1.0
    FROM c WHERE movement_type = 'End'

    UNION ALL
    SELECT month_end_date, 'Contingent', prior_department_id, prior_country_code, NULL, NULL,
           5, 'Internal Moves Out', movement_reason, -1, -1.0
    FROM c WHERE movement_type = 'Internal Move'

    UNION ALL
    SELECT month_end_date, 'Contingent', current_department_id, current_country_code, NULL, NULL,
           6, 'Internal Moves In', movement_reason, 1, 1.0
    FROM c WHERE movement_type = 'Internal Move'

    UNION ALL
    -- Conversions out: hired as employees this month
    SELECT month_end_date, 'Contingent', prior_department_id, prior_country_code, NULL, NULL,
           7, 'Conversions', movement_reason, -1, -1.0
    FROM c WHERE movement_type = 'Conversion'

    UNION ALL
    SELECT month_end_date, 'Contingent', current_department_id, current_country_code, NULL, NULL,
           8, 'Closing', 'Closing', 1, 1.0
    FROM c WHERE in_current
)

SELECT
    l.month_end_date,
    l.worker_type,
    l.department_id,
    l.country_code,
    jf.job_family_code,
    l.grade,
    l.movement_order,
    l.movement_category,
    l.movement_reason,
    CASE l.movement_order
        WHEN 1 THEN 'Opening'   WHEN 2 THEN 'Joined'    WHEN 3 THEN 'Left'      WHEN 4 THEN 'Left'
        WHEN 5 THEN 'Moved out' WHEN 6 THEN 'Moved in'  WHEN 7 THEN 'Converted' WHEN 8 THEN 'Closing'
    END                                                      AS walk_step,
    CAST(SUM(l.headcount) AS INTEGER)                        AS headcount,
    -- exact decimals so exports are identical from run to run
    ROUND(SUM(CAST(l.fte AS DECIMAL(18, 4))), 2)             AS fte
FROM lines AS l
LEFT JOIN job_families AS jf ON jf.job_family = l.job_family
GROUP BY ALL
ORDER BY l.month_end_date, l.worker_type DESC, l.department_id, l.country_code, jf.job_family_code, l.grade,
         l.movement_order, l.movement_reason;
