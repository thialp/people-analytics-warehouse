-- int_leader_org
-- Grain: one row per leader x month-end x worker type (All, Employees, Contingent): the size, shape
-- and alignment of everyone below the leader in the solid line (release 7, case study 7).
--
-- People are counted below the leader (depth 1 and deeper in int_org_closure), executive officers
-- excluded. Directs are depth 1, indirects the rest; layers below is the deepest depth.
-- Spans are the direct reports of every people manager in the organization, the leader included,
-- counted for the worker type of the row. Alignment gaps count people with at least one signal
-- (int_alignment_signal); assignments naming a former leader count the role assignments on the org
-- units led by the leader or anyone below them (they are about assignments, not people).
CREATE OR REPLACE TABLE intermediate.int_leader_org AS
WITH wt AS (
    SELECT * FROM (VALUES ('All'), ('Employees'), ('Contingent')) AS t (worker_type)
),
flags AS (
    SELECT month_end_date, person_id,
           BOOL_OR(signal_code = 'S1') AS s1, BOOL_OR(signal_code = 'S2') AS s2,
           BOOL_OR(signal_code = 'M1') AS m1, BOOL_OR(signal_code = 'M2') AS m2, BOOL_OR(signal_code = 'M3') AS m3
    FROM intermediate.int_alignment_signal
    GROUP BY 1, 2
),
below AS (
    SELECT c.month_end_date, c.ancestor_id AS leader_id, c.depth, d.person_id, d.worker_type AS person_type,
           d.is_people_manager, d.country_code,
           COALESCE(f.s1, FALSE) AS s1, COALESCE(f.s2, FALSE) AS s2, COALESCE(f.m1, FALSE) AS m1,
           COALESCE(f.m2, FALSE) AS m2, COALESCE(f.m3, FALSE) AS m3
    FROM intermediate.int_org_closure AS c
    JOIN intermediate.int_org_leader AS l ON l.month_end_date = c.month_end_date AND l.leader_id = c.ancestor_id
    JOIN intermediate.int_person_month_end AS d
      ON d.month_end_date = c.month_end_date AND d.person_id = c.descendant_id
    LEFT JOIN flags AS f ON f.month_end_date = c.month_end_date AND f.person_id = c.descendant_id
    WHERE c.depth >= 1 AND NOT d.is_executive_officer
),
size AS (
    SELECT b.month_end_date, b.leader_id, wt.worker_type,
           COUNT(*)                                                    AS people,
           COUNT(*) FILTER (WHERE b.depth = 1)                         AS directs,
           COUNT(*) FILTER (WHERE b.depth > 1)                         AS indirects,
           COUNT(*) FILTER (WHERE b.is_people_manager)                 AS managers_below,
           COALESCE(MAX(b.depth), 0)                                   AS layers_below,
           COUNT(DISTINCT b.country_code)                              AS countries,
           COUNT(*) FILTER (WHERE b.s1 OR b.s2 OR b.m1 OR b.m2 OR b.m3) AS gap_people,
           COUNT(*) FILTER (WHERE b.s1 OR b.s2)                        AS solid_line_gap_people,
           COUNT(*) FILTER (WHERE b.m1 OR b.m2 OR b.m3)                AS matrix_gap_people,
           COUNT(*) FILTER (WHERE b.s1)                                AS s1_budgeted_elsewhere,
           COUNT(*) FILTER (WHERE b.s2)                                AS s2_role_other_function,
           COUNT(*) FILTER (WHERE b.m1)                                AS m1_country_leader_other_country,
           COUNT(*) FILTER (WHERE b.m2)                                AS m2_not_one_country_matrix,
           COUNT(*) FILTER (WHERE b.m3)                                AS m3_matrix_inactive_or_leaderless
    FROM below AS b
    JOIN wt ON wt.worker_type = 'All'
            OR (wt.worker_type = 'Employees' AND b.person_type = 'Employee')
            OR (wt.worker_type = 'Contingent' AND b.person_type = 'Contingent')
    GROUP BY 1, 2, 3
),
direct_counts AS (      -- every manager's direct reports, by worker type
    SELECT p.month_end_date, p.manager_worker_id AS manager_id, wt.worker_type, COUNT(*) AS span
    FROM intermediate.int_person_month_end AS p
    JOIN wt ON wt.worker_type = 'All'
            OR (wt.worker_type = 'Employees' AND p.worker_type = 'Employee')
            OR (wt.worker_type = 'Contingent' AND p.worker_type = 'Contingent')
    WHERE p.manager_worker_id IS NOT NULL AND NOT p.is_executive_officer
    GROUP BY 1, 2, 3
),
spans AS (              -- the managers in each leader's organization, the leader included
    SELECT c.month_end_date, c.ancestor_id AS leader_id, dc.worker_type,
           MEDIAN(dc.span)                          AS median_span,
           AVG(dc.span)                             AS average_span,
           COUNT(*) FILTER (WHERE dc.span >= 15)    AS managers_15_plus,
           COUNT(*) FILTER (WHERE dc.span = 1)      AS managers_one_direct
    FROM intermediate.int_org_closure AS c
    JOIN intermediate.int_org_leader AS l ON l.month_end_date = c.month_end_date AND l.leader_id = c.ancestor_id
    JOIN direct_counts AS dc ON dc.month_end_date = c.month_end_date AND dc.manager_id = c.descendant_id
    GROUP BY 1, 2, 3
),
assign AS (
    SELECT c.month_end_date, c.ancestor_id AS leader_id, COUNT(DISTINCT a.assignment_id) AS assignments_naming_former_leader
    FROM intermediate.int_org_closure AS c
    JOIN intermediate.int_assignment_signal AS a
      ON a.month_end_date = c.month_end_date AND a.current_leader_id = c.descendant_id
    GROUP BY 1, 2
)
SELECT l.month_end_date, l.leader_id, l.leader_level, wt.worker_type,
       COALESCE(s.people, 0)                       AS people,
       COALESCE(s.directs, 0)                      AS directs,
       COALESCE(s.indirects, 0)                    AS indirects,
       COALESCE(s.managers_below, 0)               AS managers_below,
       COALESCE(s.layers_below, 0)                 AS layers_below,
       COALESCE(s.countries, 0)                    AS countries,
       sp.median_span, sp.average_span,
       COALESCE(sp.managers_15_plus, 0)            AS managers_15_plus,
       COALESCE(sp.managers_one_direct, 0)         AS managers_one_direct,
       COALESCE(s.gap_people, 0)                   AS gap_people,
       COALESCE(s.solid_line_gap_people, 0)        AS solid_line_gap_people,
       COALESCE(s.matrix_gap_people, 0)            AS matrix_gap_people,
       COALESCE(s.s1_budgeted_elsewhere, 0)        AS s1_budgeted_elsewhere,
       COALESCE(s.s2_role_other_function, 0)       AS s2_role_other_function,
       COALESCE(s.m1_country_leader_other_country, 0) AS m1_country_leader_other_country,
       COALESCE(s.m2_not_one_country_matrix, 0)    AS m2_not_one_country_matrix,
       COALESCE(s.m3_matrix_inactive_or_leaderless, 0) AS m3_matrix_inactive_or_leaderless,
       COALESCE(a.assignments_naming_former_leader, 0) AS assignments_naming_former_leader
FROM intermediate.int_org_leader AS l
CROSS JOIN wt
LEFT JOIN size AS s ON s.month_end_date = l.month_end_date AND s.leader_id = l.leader_id AND s.worker_type = wt.worker_type
LEFT JOIN spans AS sp ON sp.month_end_date = l.month_end_date AND sp.leader_id = l.leader_id AND sp.worker_type = wt.worker_type
LEFT JOIN assign AS a ON a.month_end_date = l.month_end_date AND a.leader_id = l.leader_id;
