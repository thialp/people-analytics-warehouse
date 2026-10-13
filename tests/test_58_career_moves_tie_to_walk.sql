-- Two sources, one answer: the people promoted (and demoted) in each date pair and group,
-- counted from grade changes in the job history, equal the compensation walk's Promotions
-- (and Demotions) people, counted from pay records. The career moves mart has the same
-- number of moves per group as the grade changes.
WITH grid AS (SELECT DISTINCT from_month_end, to_month_end FROM marts.mart_compensation_walk),
grade_change AS (
    SELECT worker_id, move_date, CASE WHEN to_grade > from_grade THEN 'Promotion' ELSE 'Demotion' END AS move_type
    FROM (
        SELECT worker_id, effective_start_date AS move_date, grade AS to_grade,
               LAG(grade) OVER (PARTITION BY worker_id ORDER BY effective_start_date) AS from_grade
        FROM staging.stg_job_history
    ) AS j
    WHERE from_grade IS NOT NULL AND from_grade <> to_grade
),
moved AS (   -- company level: every pair, people present at both ends
    SELECT g.from_month_end, g.to_month_end, gc.move_type,
           COUNT(DISTINCT gc.worker_id) AS people, COUNT(*) AS moves
    FROM grid AS g
    JOIN grade_change AS gc ON gc.move_date > g.from_month_end AND gc.move_date <= g.to_month_end
    JOIN intermediate.int_worker_month_end_snapshot AS o
      ON o.month_end_date = g.from_month_end AND o.worker_id = gc.worker_id AND NOT o.is_executive_officer
    JOIN intermediate.int_worker_month_end_snapshot AS c
      ON c.month_end_date = g.to_month_end AND c.worker_id = gc.worker_id
    GROUP BY ALL
),
walk AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           CASE step WHEN 'Promotions' THEN 'Promotion' ELSE 'Demotion' END AS move_type,
           SUM(worker_count) AS people
    FROM marts.mart_compensation_walk
    WHERE step IN ('Promotions', 'Demotions')
    GROUP BY ALL
),
career AS (
    SELECT from_month_end, to_month_end, view_name, group_id, move_type, SUM(moves) AS moves, SUM(workers) AS workers
    FROM marts.mart_career_moves
    GROUP BY ALL
)
SELECT 'company people differ from the walk' AS problem, m.from_month_end, m.to_month_end, m.move_type,
       m.people AS from_grades, w.people AS from_pay
FROM moved AS m
LEFT JOIN walk AS w
  ON w.from_month_end = m.from_month_end AND w.to_month_end = m.to_month_end
 AND w.view_name = 'Company' AND w.move_type = m.move_type
WHERE m.people IS DISTINCT FROM w.people
UNION ALL
SELECT 'company moves differ from the mart', m.from_month_end, m.to_month_end, m.move_type, m.moves, c.moves
FROM moved AS m
LEFT JOIN career AS c
  ON c.from_month_end = m.from_month_end AND c.to_month_end = m.to_month_end
 AND c.view_name = 'Company' AND c.move_type = m.move_type
WHERE m.moves IS DISTINCT FROM c.moves
UNION ALL
SELECT 'a group has career moves but no walk line, or fewer moves than walk people', c.from_month_end, c.to_month_end,
       c.move_type, c.moves, w.people
FROM career AS c
LEFT JOIN walk AS w USING (from_month_end, to_month_end, view_name, group_id, move_type)
WHERE w.people IS NULL OR c.moves < w.people
UNION ALL
SELECT 'views do not add up to the company', c.from_month_end, c.to_month_end, c.move_type, SUM(c.moves), NULL
FROM career AS c
GROUP BY c.from_month_end, c.to_month_end, c.move_type, c.view_name
HAVING SUM(c.moves) <> (SELECT SUM(c2.moves) FROM career AS c2
                        WHERE c2.from_month_end = c.from_month_end AND c2.to_month_end = c.to_month_end
                          AND c2.move_type = c.move_type AND c2.view_name = 'Company')
