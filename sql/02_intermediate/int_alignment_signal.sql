-- int_alignment_signal
-- Grain: one row per person x alignment signal x month-end (release 7, case study 7).
--
-- A leader's org design is the org units they lead and the job families their function hires;
-- the matrix line follows where people sit. A signal marks where a record departs from that
-- design. It is a flag, never an error: many have a good business reason. Executive officers
-- are left out, like everywhere else. Leading people in other regions is never a signal.
--
--   S1  Budgeted in another org        the manager sits in another department (a person who leads
--                                      an org unit is exempt: they report up across units by design)
--   S2  Role from another function     employees: the job family's home function is not the
--                                      department's function (shared families never show)
--   M1  Country leader for another     the person's country matrix does not cover the country
--       country                        Keystone has them in
--   M2  In two country matrices, or    not exactly one active country matrix
--       none
--   M3  Matrix inactive or without a   a membership in a matrix that has ended, or whose leader
--       leader                         seat is open that day
--
-- Matrix signals apply to people Keystone holds (every employee; a contingent worker with an
-- active Keystone record). A contingent worker Keystone does not know is case study 4's gap.
-- Role assignments naming a former leader are about assignments, not people:
-- see int_assignment_signal.
CREATE OR REPLACE TABLE intermediate.int_alignment_signal AS
WITH p AS (
    SELECT * FROM intermediate.int_person_month_end WHERE NOT is_executive_officer
),
s1 AS (
    SELECT p.month_end_date, p.person_id, 'S1' AS signal_code,
           'Manager ' || m.person_name || ' sits in ' || md.department_name AS signal_detail
    FROM p
    JOIN intermediate.int_person_month_end AS m
      ON m.month_end_date = p.month_end_date AND m.person_id = p.manager_worker_id
    JOIN staging.stg_department AS md ON md.department_id = m.department_id
    WHERE p.leads_org_unit_id IS NULL
      AND p.keystone_department_id IS NOT NULL
      AND m.department_id <> p.keystone_department_id
),
s2 AS (
    SELECT p.month_end_date, p.person_id, 'S2' AS signal_code,
           jp.job_family || ' role, usually hired by ' || h.home_function AS signal_detail
    FROM p
    JOIN staging.stg_job_family_home AS h ON h.job_family_code = p.job_family_code
    JOIN staging.stg_job_profile AS jp ON jp.job_profile_id = p.job_profile_id
    WHERE p.worker_type = 'Employee' AND NOT h.is_shared
      AND p.function_name NOT IN ('Executive') AND h.home_function <> p.function_name
),
kp AS (         -- people Keystone holds, and the country of the office Keystone has them in
    SELECT p.month_end_date, p.person_id, l.country_code AS ks_country_code
    FROM p
    JOIN staging.stg_location AS l ON l.location_id = p.keystone_location_id
    WHERE p.has_keystone_record
),
mem AS (
    SELECT kp.month_end_date, kp.person_id, kp.ks_country_code, mm.matrix_org_id,
           o.matrix_org_name, o.status, o.manager_worker_id,
           list_contains(string_split(o.covers_country_codes, ';'), kp.ks_country_code) AS covers
    FROM kp
    JOIN staging.stg_matrix_membership AS mm
      ON mm.person_id = kp.person_id
     AND kp.month_end_date BETWEEN mm.effective_start_date AND mm.effective_end_date_filled
    JOIN staging.stg_matrix_org AS o
      ON o.matrix_org_id = mm.matrix_org_id
     AND kp.month_end_date BETWEEN o.effective_start_date AND o.effective_end_date_filled
),
per_person AS (
    SELECT kp.month_end_date, kp.person_id, kp.ks_country_code,
           COUNT(mem.matrix_org_id)                                   AS n_matrices,
           COALESCE(BOOL_OR(mem.covers), FALSE)                       AS any_covers,
           STRING_AGG(mem.matrix_org_name, '; ' ORDER BY mem.matrix_org_id) AS matrices
    FROM kp
    LEFT JOIN mem ON mem.month_end_date = kp.month_end_date AND mem.person_id = kp.person_id
    GROUP BY 1, 2, 3
),
m1 AS (
    SELECT month_end_date, person_id, 'M1' AS signal_code,
           'Sits in ' || ks_country_code || '; matrix: ' || matrices AS signal_detail
    FROM per_person WHERE n_matrices >= 1 AND NOT any_covers
),
m2 AS (
    SELECT month_end_date, person_id, 'M2' AS signal_code,
           CASE WHEN n_matrices = 0 THEN 'No country matrix'
                ELSE n_matrices || ' country matrices: ' || matrices END AS signal_detail
    FROM per_person WHERE n_matrices <> 1
),
m3 AS (
    SELECT month_end_date, person_id, 'M3' AS signal_code,
           STRING_AGG(matrix_org_name || CASE WHEN status = 'Inactive' THEN ' has ended' ELSE ' has no leader' END,
                      '; ' ORDER BY matrix_org_id) AS signal_detail
    FROM mem WHERE status = 'Inactive' OR manager_worker_id IS NULL
    GROUP BY 1, 2
)
SELECT s.*, g.signal_name, g.signal_line
FROM (SELECT * FROM s1 UNION ALL SELECT * FROM s2 UNION ALL SELECT * FROM m1
      UNION ALL SELECT * FROM m2 UNION ALL SELECT * FROM m3) AS s
JOIN (VALUES ('S1', 'Budgeted in another org', 'Solid line'),
             ('S2', 'Role from another function', 'Solid line'),
             ('M1', 'Country leader for another country', 'Matrix line'),
             ('M2', 'In two country matrices, or none', 'Matrix line'),
             ('M3', 'Matrix inactive or without a leader', 'Matrix line'))
     AS g (signal_code, signal_name, signal_line) USING (signal_code);
