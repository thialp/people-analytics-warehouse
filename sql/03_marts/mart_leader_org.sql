-- mart_leader_org
-- Grain: one row per L0, L1 or L2 leader x worker type x month-end, for the 13 month-ends that end on
-- the report date (release 7, case study 7). The trend behind the KPI ribbon and the Tableau Cloud
-- Pulse metrics (people led, alignment gaps, median span) for each leader.
CREATE OR REPLACE TABLE marts.mart_leader_org AS
SELECT o.month_end_date, cal.fiscal_year, cal.fiscal_quarter_label,
       o.leader_id, l.leader_name, l.job_title, l.leader_level, l.function_name, l.department_name,
       o.worker_type, o.people, o.directs, o.indirects, o.managers_below, o.layers_below, o.countries,
       o.median_span, o.average_span, o.managers_15_plus, o.managers_one_direct,
       o.gap_people, o.solid_line_gap_people, o.matrix_gap_people,
       o.s1_budgeted_elsewhere, o.s2_role_other_function, o.m1_country_leader_other_country,
       o.m2_not_one_country_matrix, o.m3_matrix_inactive_or_leaderless, o.assignments_naming_former_leader,
       CASE WHEN o.people > 0 THEN o.gap_people * 1.0 / o.people END AS gap_rate
FROM intermediate.int_leader_org AS o
JOIN intermediate.int_org_leader AS l ON l.month_end_date = o.month_end_date AND l.leader_id = o.leader_id
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = o.month_end_date
WHERE l.leader_level IN ('L0', 'L1', 'L2');
