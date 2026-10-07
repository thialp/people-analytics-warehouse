-- mart_headcount_fte_walk
-- Grain: one row per month x slice x movement category x movement reason,
-- where a slice is department x country x job family x grade.
--
-- The headcount and FTE walk. For every slice and month:
--
--   Opening                      workers active at the prior month-end, in their prior slice
--   + Hires                      new workers, in their current slice, at current FTE
--   - Voluntary Terminations     leavers, in their prior slice, at prior FTE
--   - Involuntary Terminations
--   - Internal Moves Out         workers who left this slice for another one, at prior FTE
--   + Internal Moves In          workers who arrived from another slice, at prior FTE
--   + FTE Changes                FTE change for workers who stayed (headcount effect is zero)
--   = Closing                    workers active at the month-end, in their current slice
--
-- Because a move is booked out of one slice and into another, the walk
-- reconciles at ANY roll-up of the slice: a promotion is a move between grades
-- that nets to zero for the department, and a transfer nets to zero for the
-- company. Movers are booked at their prior FTE; if their FTE also changed, the
-- difference appears as an FTE Change in their new slice. That keeps the move
-- itself FTE-neutral, so internal moves net to zero in FTE too.
--
-- The fact table carries codes only; names and hierarchies live in five small
-- dimension marts (mart_dim_*), which Tableau relates on matching field names.
-- That keeps the export small enough for GitHub and Tableau Public.
--
-- Headcount counts everyone, executive officers included. (They are excluded
-- only from the compensation marts, where pay is the sensitive part.)
-- Sign convention: Opening and Closing are positive levels; movements carry
-- the sign of their effect.
CREATE OR REPLACE TABLE marts.mart_headcount_fte_walk AS
WITH m AS (
    SELECT * FROM intermediate.int_worker_movement
),

lines AS (
    -- Opening
    SELECT month_end_date, prior_department_id AS department_id, prior_country_code AS country_code,
           prior_job_family AS job_family, prior_grade AS grade,
           1 AS movement_order, 'Opening' AS movement_category, 'Opening' AS movement_reason,
           1 AS headcount, prior_fte AS fte
    FROM m WHERE in_prior

    UNION ALL
    -- Hires
    SELECT month_end_date, current_department_id, current_country_code, current_job_family, current_grade,
           2, 'Hires', movement_reason, 1, current_fte
    FROM m WHERE movement_type = 'Hire'

    UNION ALL
    -- Terminations, split by type
    SELECT month_end_date, prior_department_id, prior_country_code, prior_job_family, prior_grade,
           CASE WHEN movement_reason = 'Voluntary' THEN 3 ELSE 4 END,
           CASE WHEN movement_reason = 'Voluntary' THEN 'Voluntary Terminations'
                ELSE 'Involuntary Terminations' END,
           movement_reason, -1, -prior_fte
    FROM m WHERE movement_type = 'Termination'

    UNION ALL
    -- Internal moves: out of the old slice ...
    SELECT month_end_date, prior_department_id, prior_country_code, prior_job_family, prior_grade,
           5, 'Internal Moves Out', movement_reason, -1, -prior_fte
    FROM m WHERE movement_type = 'Internal Move'

    UNION ALL
    -- ... and into the new one, at the same (prior) FTE
    SELECT month_end_date, current_department_id, current_country_code, current_job_family, current_grade,
           6, 'Internal Moves In', movement_reason, 1, prior_fte
    FROM m WHERE movement_type = 'Internal Move'

    UNION ALL
    -- FTE changes for everyone who stayed, booked in the current slice
    SELECT month_end_date, current_department_id, current_country_code, current_job_family, current_grade,
           7, 'FTE Changes',
           CASE WHEN current_fte > prior_fte THEN 'FTE Increase' ELSE 'FTE Reduction' END,
           0, current_fte - prior_fte
    FROM m WHERE fte_changed

    UNION ALL
    -- Closing
    SELECT month_end_date, current_department_id, current_country_code, current_job_family, current_grade,
           8, 'Closing', 'Closing', 1, current_fte
    FROM m WHERE in_current
),

job_families AS (
    SELECT DISTINCT job_family_code, job_family FROM staging.stg_job_profile
)

SELECT
    l.month_end_date,
    l.department_id,
    l.country_code,
    jf.job_family_code,
    l.grade,
    l.movement_order,
    l.movement_category,
    l.movement_reason,
    CAST(SUM(l.headcount) AS INTEGER)                        AS headcount,
    -- exact decimals so exports are identical from run to run
    ROUND(SUM(CAST(l.fte AS DECIMAL(18, 4))), 2)             AS fte
FROM lines AS l
JOIN job_families AS jf ON jf.job_family = l.job_family
GROUP BY ALL
ORDER BY l.month_end_date, l.department_id, l.country_code, jf.job_family_code, l.grade,
         l.movement_order, l.movement_reason;
