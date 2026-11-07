-- int_org_leader
-- Grain: one row per leader (everyone who leads people, plus the executive officers) per
-- month-end, with their level in the leadership view and their place in the tree
-- (release 7, case study 7).
--
--   L0  Executive Leadership: the CEO and the function heads (the executive officers)
--   L1  people managers who report to an executive officer
--   L2  people managers who report to an L1
--   Manager  every other people manager (the tree still opens their teams; the picker lists L0-L2)
--
-- path is the chain from the top, |W100001|W100002|..|me|, the string The Information Lab
-- org-chart technique filters on to keep a branch and its ancestors.
CREATE OR REPLACE TABLE intermediate.int_org_leader AS
WITH p AS (
    SELECT * FROM intermediate.int_person_month_end
    WHERE is_people_manager OR is_executive_officer
),
anc AS (
    SELECT c.month_end_date, c.descendant_id AS person_id,
           COUNT(*) FILTER (WHERE c.depth > 0)                                         AS depth_from_top,
           '|' || STRING_AGG(c.ancestor_id, '|' ORDER BY c.depth DESC) || '|'          AS path
    FROM intermediate.int_org_closure AS c
    JOIN p ON p.month_end_date = c.month_end_date AND p.person_id = c.descendant_id
    GROUP BY 1, 2
),
lvl AS (
    SELECT p.month_end_date, p.person_id,
           CASE WHEN p.is_executive_officer THEN 'L0'
                WHEN m.is_executive_officer THEN 'L1'
                WHEN m.is_people_manager AND mm.is_executive_officer AND NOT m.is_executive_officer THEN 'L2'
                ELSE 'Manager' END AS leader_level
    FROM p
    LEFT JOIN intermediate.int_person_month_end AS m
           ON m.month_end_date = p.month_end_date AND m.person_id = p.manager_worker_id
    LEFT JOIN intermediate.int_person_month_end AS mm
           ON mm.month_end_date = m.month_end_date AND mm.person_id = m.manager_worker_id
)
SELECT p.month_end_date, p.person_id AS leader_id, p.person_name AS leader_name, p.job_title, p.grade,
       l.leader_level, p.manager_worker_id AS parent_leader_id, a.depth_from_top, a.path,
       p.department_id, p.department_name, p.function_name, p.location_id, p.country_code, p.region,
       p.leads_org_unit_id, p.is_executive_officer
FROM p
JOIN lvl AS l ON l.month_end_date = p.month_end_date AND l.person_id = p.person_id
JOIN anc AS a ON a.month_end_date = p.month_end_date AND a.person_id = p.person_id;
