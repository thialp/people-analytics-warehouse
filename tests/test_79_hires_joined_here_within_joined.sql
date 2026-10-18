-- The tie-out note on both dashboards ("hires count X of the Y who joined") compares one
-- population, so X can never exceed Y. Y is the Headcount & FTE Walk's joined (employee
-- hires plus conversions, each booked to the group on its hire month-end). X is the
-- compensation walk's Hires that joined THIS group and are still in it on the To date:
-- the region walk's hires - hires_joined_elsewhere. Hires booked to the group as at the
-- To date but hired into another group carry the reason 'Joined Elsewhere'.
--   1. X <= Y for every date pair and group of the five views both dashboards share
--   2. the walk's 'New Hire' people equal X, and its 'Joined Elsewhere' people equal the
--      region walk's hires_joined_elsewhere, in all six views
--   3. in the Company view nobody joins elsewhere
WITH pairs AS (
    SELECT DISTINCT from_month_end, to_month_end FROM marts.mart_region_walk
),
dept_map AS (
    SELECT d.department_id,
           CASE WHEN p.org_unit_type = 'Sub-function' THEN p.parent_org_unit_id ELSE p.org_unit_id END AS function_id,
           d.parent_org_unit_id AS leader_org_id
    FROM staging.stg_department AS d
    JOIN staging.stg_org_unit AS p ON p.org_unit_id = d.parent_org_unit_id
),
joined AS (
    SELECT p.from_month_end, p.to_month_end, v.view_name, v.group_id, SUM(h.headcount) AS joined
    FROM pairs AS p
    JOIN marts.mart_headcount_fte_walk AS h
      ON h.month_end_date > p.from_month_end AND h.month_end_date <= p.to_month_end
     AND h.worker_type = 'Employee' AND h.movement_category IN ('Hires', 'Conversions')
     AND h.department_id <> 'D-901'
    JOIN dept_map AS d ON d.department_id = h.department_id
    CROSS JOIN LATERAL (VALUES ('Company', 'ORG-000'), ('Function', d.function_id), ('Sub-function', d.leader_org_id),
                               ('Department', h.department_id), ('Country', h.country_code)) AS v(view_name, group_id)
    GROUP BY ALL
),
here AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(hires - hires_joined_elsewhere) AS joined_here, SUM(hires_joined_elsewhere) AS joined_elsewhere
    FROM marts.mart_region_walk
    GROUP BY ALL
),
walk AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN movement_reason = 'New Hire'         THEN worker_count ELSE 0 END) AS joined_here,
           SUM(CASE WHEN movement_reason = 'Joined Elsewhere' THEN worker_count ELSE 0 END) AS joined_elsewhere
    FROM marts.mart_compensation_walk
    WHERE step = 'Hires'
    GROUP BY ALL
)
SELECT 'still here exceeds joined' AS problem, h.from_month_end, h.to_month_end, h.view_name, h.group_id
FROM here AS h
LEFT JOIN joined AS j USING (from_month_end, to_month_end, view_name, group_id)
WHERE h.view_name <> 'Office' AND h.joined_here > COALESCE(j.joined, 0)
UNION ALL
SELECT 'walk hires reasons differ from the region walk', COALESCE(h.from_month_end, w.from_month_end),
       COALESCE(h.to_month_end, w.to_month_end), COALESCE(h.view_name, w.view_name), COALESCE(h.group_id, w.group_id)
FROM here AS h
FULL OUTER JOIN walk AS w USING (from_month_end, to_month_end, view_name, group_id)
WHERE COALESCE(h.joined_here, 0) <> COALESCE(w.joined_here, 0)
   OR COALESCE(h.joined_elsewhere, 0) <> COALESCE(w.joined_elsewhere, 0)
UNION ALL
SELECT 'company hires joined elsewhere', from_month_end, to_month_end, view_name, group_id
FROM here
WHERE view_name = 'Company' AND joined_elsewhere <> 0
