-- int_person_month_end
-- Grain: one row per person in Arcadia's workforce per month-end, for the 13 month-ends that end on
-- the report date (release 7, case study 7). Employees and contingent workers together.
--
-- Employees come from the month-end snapshot (int_worker_month_end_snapshot), executive officers
-- included and flagged: they lead, but stay out of every count.
--
-- Contingent workers count from Bridgeway, the source of truth for who is a contingent worker
-- (int_cw_month_end_snapshot: 11,941 on Jun 30, 2026, the same number as Dashboards #1 and #4).
-- Where they sit is Bridgeway's office. Their place in the solid line comes from their Keystone
-- profile (matched through int_cw_identity_resolution): the manager and department on the
-- Keystone record in effect that day. When Keystone holds no active record for them, the manager
-- is the hiring manager on the Bridgeway order (matched on work email). Either way the manager
-- must be an employee on that month-end; otherwise the person is left without one.
--
-- person_id is the Keystone person ID (employees W1.., contingent W5..); a contingent worker
-- Keystone does not know is keyed by the Bridgeway worker ID.
CREATE OR REPLACE TABLE intermediate.int_person_month_end AS
WITH months AS (
    SELECT c.month_end_date, c.fiscal_year
    FROM intermediate.int_month_end_calendar AS c
    CROSS JOIN staging.stg_report_calendar AS rc
    WHERE c.month_end_date <= rc.report_as_of_date
      AND c.month_end_date >= last_day(rc.report_as_of_date - INTERVAL 12 MONTH)
),
emp AS (
    SELECT s.month_end_date, s.fiscal_year,
           s.worker_id                                   AS person_id,
           'Employee'                                    AS worker_type,
           CAST(NULL AS VARCHAR)                         AS bw_worker_id,
           w.worker_name                                 AS person_name,
           jp.job_title,
           s.department_id,
           s.department_id                               AS keystone_department_id,
           s.location_id,
           s.location_id                                 AS keystone_location_id,
           s.job_profile_id,
           jp.job_family_code,
           s.grade,
           s.manager_worker_id,
           'Keystone'                                    AS manager_source,
           s.is_people_manager,
           s.leads_org_unit_id,
           s.is_executive_officer,
           TRUE                                          AS has_keystone_record
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN months AS m ON m.month_end_date = s.month_end_date
    JOIN staging.stg_worker AS w ON w.worker_id = s.worker_id
    LEFT JOIN staging.stg_job_profile AS jp ON jp.job_profile_id = s.job_profile_id
),
cw AS (
    SELECT b.month_end_date, b.fiscal_year, b.bw_worker_id, b.department_id AS bw_department_id, b.location_id,
           b.revision_id, ir.person_id AS ks_person_id
    FROM intermediate.int_cw_month_end_snapshot AS b
    JOIN months AS m ON m.month_end_date = b.month_end_date
    LEFT JOIN intermediate.int_cw_identity_resolution AS ir
           ON ir.bw_worker_id = b.bw_worker_id AND ir.person_id IS NOT NULL
),
cw_ks AS (      -- the Keystone record in effect on the month-end (the latest, if two are active)
    SELECT cw.*, k.department_id AS ks_department_id, k.location_id AS ks_location_id,
           k.manager_worker_id AS ks_manager_worker_id
    FROM cw
    LEFT JOIN staging.stg_ks_contingent_worker AS k
           ON k.person_id = cw.ks_person_id AND k.status = 'Active'
          AND cw.month_end_date BETWEEN k.effective_start_date AND k.effective_end_date_filled
    QUALIFY ROW_NUMBER() OVER (PARTITION BY cw.month_end_date, cw.bw_worker_id
                               ORDER BY k.effective_start_date DESC NULLS LAST, k.ks_record_id DESC) = 1
),
cw_full AS (
    SELECT c.*, r.job_title, r.hiring_manager_email, hm.worker_id AS bw_manager_worker_id,
           bw.first_name || ' ' || bw.last_name AS person_name
    FROM cw_ks AS c
    JOIN staging.stg_bw_service_order_revision AS r ON r.revision_id = c.revision_id
    JOIN staging.stg_bw_contingent_worker AS bw ON bw.bw_worker_id = c.bw_worker_id
    LEFT JOIN staging.stg_worker AS hm ON hm.work_email = r.hiring_manager_email
),
cw_rows AS (
    SELECT c.month_end_date, c.fiscal_year,
           COALESCE(c.ks_person_id, c.bw_worker_id)      AS person_id,
           'Contingent'                                  AS worker_type,
           c.bw_worker_id,
           c.person_name,
           c.job_title,
           COALESCE(c.ks_department_id, c.bw_department_id) AS department_id,
           c.ks_department_id                            AS keystone_department_id,
           c.location_id,
           c.ks_location_id                              AS keystone_location_id,
           CAST(NULL AS VARCHAR)                         AS job_profile_id,
           CAST(NULL AS VARCHAR)                         AS job_family_code,
           CAST(NULL AS INTEGER)                         AS grade,
           CASE WHEN ke.person_id IS NOT NULL THEN c.ks_manager_worker_id
                WHEN be.person_id IS NOT NULL THEN c.bw_manager_worker_id END AS manager_worker_id,
           CASE WHEN ke.person_id IS NOT NULL THEN 'Keystone'
                WHEN be.person_id IS NOT NULL THEN 'Bridgeway hiring manager' END AS manager_source,
           FALSE                                         AS is_people_manager,
           CAST(NULL AS VARCHAR)                         AS leads_org_unit_id,
           FALSE                                         AS is_executive_officer,
           c.ks_department_id IS NOT NULL                AS has_keystone_record
    FROM cw_full AS c
    LEFT JOIN emp AS ke ON ke.month_end_date = c.month_end_date AND ke.person_id = c.ks_manager_worker_id
    LEFT JOIN emp AS be ON be.month_end_date = c.month_end_date AND be.person_id = c.bw_manager_worker_id
)
SELECT p.*, loc.country_code, loc.region, d.function_name, d.department_name
FROM (SELECT * FROM emp UNION ALL SELECT * FROM cw_rows) AS p
JOIN staging.stg_location AS loc ON loc.location_id = p.location_id
LEFT JOIN staging.stg_department AS d ON d.department_id = p.department_id;
