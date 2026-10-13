-- mart_career_moves
-- Grain: one row per date pair x view x group x move type x grade before x grade after.
--
-- The DuckDB twin of tableau/custom_sql_career_moves.sql. The Career moves panel of the
-- compensation walk: promotions and demotions between two month-ends, by the grade a
-- person left and the grade they reached, keyed like the walk so the same filters drive
-- it. A move is a change of grade in the job history; a person promoted twice in the
-- period is two moves (moves) and one person (workers, per row).
--
-- Same population as the walk's Promotions and Demotions steps: people present at both
-- month-ends (executive officers excluded), placed in the group they are in at the To
-- date. The walk counts them from pay records, this mart from grade changes; the number
-- of people promoted (or demoted) agrees in every group (test 58).
-- director_and_above: the move is at Director (grade 7) or above on either side;
-- into_director: a promotion that crosses into Director and above.
CREATE OR REPLACE TABLE marts.mart_career_moves AS
WITH grid AS (
    -- === GRID === same rule as mart_compensation_walk (88 pairs)
    SELECT f.month_end_date AS from_date, t.month_end_date AS to_date
    FROM intermediate.int_month_end_calendar AS f
    JOIN intermediate.int_month_end_calendar AS t ON t.month_end_date > f.month_end_date
    WHERE t.month_end_date > (SELECT MIN(month_end_date) FROM intermediate.int_month_end_calendar) + INTERVAL 12 MONTH
      AND (   t.prior_month_end_date = f.month_end_date
           OR (    MONTH(f.month_end_date) IN (3, 6, 9, 12) AND MONTH(t.month_end_date) IN (3, 6, 9, 12)
               AND (   date_diff('month', f.month_end_date, t.month_end_date) IN (3, 12)
                    OR (MONTH(f.month_end_date) = 6 AND date_diff('month', f.month_end_date, t.month_end_date) < 12))))
),

-- every change of grade: a job record whose grade differs from the record before it
grade_change AS (
    SELECT worker_id, move_date, from_grade, to_grade
    FROM (
        SELECT worker_id, effective_start_date AS move_date, grade AS to_grade,
               LAG(grade) OVER (PARTITION BY worker_id ORDER BY effective_start_date) AS from_grade
        FROM staging.stg_job_history
    ) AS j
    WHERE from_grade IS NOT NULL AND from_grade <> to_grade
),

move AS (
    SELECT g.from_date, g.to_date, gc.worker_id, gc.from_grade, gc.to_grade,
           CASE WHEN gc.to_grade > gc.from_grade THEN 'Promotion' ELSE 'Demotion' END AS move_type,
           c.department_id AS c_dept, c.location_id AS c_loc, c.country_code AS c_country
    FROM grid AS g
    JOIN grade_change AS gc ON gc.move_date > g.from_date AND gc.move_date <= g.to_date
    JOIN intermediate.int_worker_month_end_snapshot AS o
      ON o.month_end_date = g.from_date AND o.worker_id = gc.worker_id AND NOT o.is_executive_officer
    JOIN intermediate.int_worker_month_end_snapshot AS c
      ON c.month_end_date = g.to_date AND c.worker_id = gc.worker_id
),

dept_map AS (
    SELECT d.department_id,
           CASE WHEN p.org_unit_type = 'Sub-function' THEN p.parent_org_unit_id ELSE p.org_unit_id END AS function_id,
           d.parent_org_unit_id AS leader_org_id
    FROM staging.stg_department AS d
    JOIN staging.stg_org_unit AS p ON p.org_unit_id = d.parent_org_unit_id
),

by_group AS (
    SELECT m.from_date, m.to_date, v.view_order, v.view_name,
           CASE v.view_order WHEN 1 THEN 'ORG-000' WHEN 2 THEN cd.function_id WHEN 3 THEN cd.leader_org_id
                             WHEN 4 THEN m.c_dept WHEN 5 THEN m.c_loc WHEN 6 THEN m.c_country END AS group_id,
           m.move_type, m.from_grade, m.to_grade,
           COUNT(*) AS moves, COUNT(DISTINCT m.worker_id) AS workers
    FROM move AS m
    LEFT JOIN dept_map AS cd ON cd.department_id = m.c_dept
    CROSS JOIN (VALUES (1, 'Company'), (2, 'Function'), (3, 'Sub-function'),
                       (4, 'Department'), (5, 'Office'), (6, 'Country')) AS v(view_order, view_name)
    GROUP BY ALL
)

SELECT
    t.from_date                                                         AS from_month_end,
    t.to_date                                                           AS to_month_end,
    (SELECT CAST(MIN(month_end_date) + INTERVAL 12 MONTH AS DATE) FROM intermediate.int_month_end_calendar) AS report_start_date,
    (SELECT MAX(month_end_date) FROM intermediate.int_month_end_calendar)                                  AS report_as_of_date,
    cf.fiscal_period                                                    AS from_fiscal_period,
    ct.fiscal_period                                                    AS to_fiscal_period,
    date_diff('month', t.from_date, t.to_date)                          AS months_between,
    t.view_order,
    t.view_name,
    t.group_id,
    CASE t.view_name
        WHEN 'Office'  THEN lo.office_name
        WHEN 'Country' THEN co.country_name
        ELSE ou.org_unit_name
    END                                                                 AS group_name,
    t.move_type,
    t.from_grade,
    fg.grade_level                                                      AS from_grade_level,
    t.to_grade,
    tg.grade_level                                                      AS to_grade_level,
    GREATEST(t.from_grade, t.to_grade) >= 7                             AS director_and_above,
    t.from_grade < 7 AND t.to_grade >= 7                                AS into_director,
    CAST(t.moves AS INTEGER)                                            AS moves,
    CAST(t.workers AS INTEGER)                                          AS workers
FROM by_group AS t
JOIN intermediate.int_month_end_calendar AS cf ON cf.month_end_date = t.from_date
JOIN intermediate.int_month_end_calendar AS ct ON ct.month_end_date = t.to_date
JOIN staging.stg_job_level AS fg ON fg.grade = t.from_grade
JOIN staging.stg_job_level AS tg ON tg.grade = t.to_grade
LEFT JOIN staging.stg_org_unit AS ou ON ou.org_unit_id = t.group_id
LEFT JOIN staging.stg_location AS lo ON t.view_name = 'Office'  AND lo.location_id  = t.group_id
LEFT JOIN staging.stg_country  AS co ON t.view_name = 'Country' AND co.country_code = t.group_id
ORDER BY t.from_date, t.to_date, t.view_order, t.group_id, t.move_type, t.from_grade, t.to_grade;
