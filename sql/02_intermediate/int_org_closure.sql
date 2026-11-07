-- int_org_closure
-- Grain: one row per month-end x ancestor x descendant: everyone below a person in the solid line,
-- at any depth, plus each person with themselves at depth 0 (release 7, case study 7).
--
-- This is the closure table that makes "who is in my organization" one join instead of a
-- recursive walk at query time: directs are depth 1, indirects depth 2 and below, layers are the
-- deepest depth. It is built once with a recursive CTE over the month-end reporting lines in
-- int_person_month_end (employees and contingent workers; a contingent worker is always a leaf).
-- Test 97 checks that every chain ends at the CEO and that directs + indirects = people under.
CREATE OR REPLACE TABLE intermediate.int_org_closure AS
WITH RECURSIVE edges AS (
    SELECT month_end_date, person_id, manager_worker_id
    FROM intermediate.int_person_month_end
    WHERE manager_worker_id IS NOT NULL
),
chain (month_end_date, ancestor_id, descendant_id, depth) AS (
    SELECT month_end_date, manager_worker_id, person_id, 1
    FROM edges
    UNION ALL
    SELECT c.month_end_date, e.manager_worker_id, c.descendant_id, c.depth + 1
    FROM chain AS c
    JOIN edges AS e ON e.month_end_date = c.month_end_date AND e.person_id = c.ancestor_id
    WHERE c.depth < 20
)
SELECT month_end_date, ancestor_id, descendant_id, depth FROM chain
UNION ALL
SELECT month_end_date, person_id, person_id, 0 FROM intermediate.int_person_month_end;
