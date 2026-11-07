-- mart_org_node
-- Grain: one row per leader x worker type (All, Employees, Contingent) on the report date: every node
-- of the Who Leads Where org tree, with what its tooltip shows (release 7, case study 7).
--
-- Every people manager and executive officer is a node. parent_leader_id and path drive the tree:
-- the dynamic tree keeps a node's branch and its ancestors (The Information Lab technique), the
-- static tree draws every node below the chosen leader. is_selectable marks L0, L1 and L2, the
-- leaders the rail lists; below L2 the tree still opens a manager's team.
CREATE OR REPLACE TABLE marts.mart_org_node AS
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar),
kids AS (
    SELECT month_end_date, parent_leader_id AS leader_id, COUNT(*) AS child_leaders
    FROM intermediate.int_org_leader GROUP BY 1, 2
),
today AS (
    SELECT leader_id, worker_type, at_work, off FROM marts.mart_leader_availability WHERE day_offset = 0
)
SELECT l.month_end_date                         AS as_of_date,
       l.leader_id, l.leader_name, l.job_title, l.grade, l.leader_level,
       l.leader_level IN ('L0', 'L1', 'L2')     AS is_selectable,
       l.parent_leader_id, pl.leader_name       AS parent_leader_name,
       l.depth_from_top, l.path,
       COALESCE(k.child_leaders, 0)             AS child_leaders,
       l.department_name, l.function_name, loc.office_name, loc.country_name, l.region,
       l.leads_org_unit_id, ou.org_unit_name    AS leads_org_unit_name,
       o.worker_type, o.people, o.directs, o.indirects, o.managers_below, o.layers_below, o.countries,
       o.median_span, o.managers_15_plus, o.managers_one_direct,
       o.gap_people, o.solid_line_gap_people, o.matrix_gap_people,
       o.s1_budgeted_elsewhere, o.s2_role_other_function, o.m1_country_leader_other_country,
       o.m2_not_one_country_matrix, o.m3_matrix_inactive_or_leaderless, o.assignments_naming_former_leader,
       t.at_work                                AS at_work_today,
       t.off                                    AS off_today
FROM intermediate.int_org_leader AS l
JOIN rc ON l.month_end_date = rc.report_as_of_date
JOIN intermediate.int_leader_org AS o ON o.month_end_date = l.month_end_date AND o.leader_id = l.leader_id
JOIN staging.stg_location AS loc ON loc.location_id = l.location_id
LEFT JOIN intermediate.int_org_leader AS pl ON pl.month_end_date = l.month_end_date AND pl.leader_id = l.parent_leader_id
LEFT JOIN kids AS k ON k.month_end_date = l.month_end_date AND k.leader_id = l.leader_id
LEFT JOIN staging.stg_org_unit AS ou ON ou.org_unit_id = l.leads_org_unit_id
LEFT JOIN today AS t ON t.leader_id = l.leader_id AND t.worker_type = o.worker_type
ORDER BY ALL;
