-- int_worker_reporting_line
-- Grain: one row per active worker per month-end.
--
-- The reporting line in columns: direct manager, skip-level manager (the manager's
-- manager), the head of the worker's department and the function head they roll up
-- to, plus how many layers sit between them and the CEO (CEO = 0) and how many
-- people report to them directly and in total.
CREATE OR REPLACE TABLE intermediate.int_worker_reporting_line AS
WITH leaders AS (
    SELECT s.month_end_date, s.worker_id, s.leads_org_unit_id, ou.org_unit_type
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN staging.stg_org_unit AS ou ON ou.org_unit_id = s.leads_org_unit_id
),
up AS (                                   -- the worker themself (hops 0) plus every manager above
    SELECT month_end_date, worker_id, worker_id AS ancestor_worker_id, 0 AS hops
    FROM intermediate.int_worker_month_end_snapshot
    UNION ALL
    SELECT month_end_date, worker_id, ancestor_worker_id, hops
    FROM intermediate.int_worker_reporting_chain
),
rollup AS (
    SELECT
        u.month_end_date,
        u.worker_id,
        MAX(u.hops)                                                                AS layers_from_ceo,
        MAX(CASE WHEN u.hops = 1 THEN u.ancestor_worker_id END)                    AS manager_worker_id,
        MAX(CASE WHEN u.hops = 2 THEN u.ancestor_worker_id END)                    AS skip_level_manager_id,
        ARG_MIN(l.worker_id, u.hops) FILTER (WHERE l.org_unit_type = 'Department') AS department_head_id,
        ARG_MIN(l.worker_id, u.hops) FILTER (WHERE l.org_unit_type = 'Function')   AS function_head_id,
        ARG_MIN(l.leads_org_unit_id, u.hops) FILTER (WHERE l.org_unit_type = 'Function') AS function_org_unit_id
    FROM up AS u
    LEFT JOIN leaders AS l
      ON l.month_end_date = u.month_end_date
     AND l.worker_id      = u.ancestor_worker_id
    GROUP BY u.month_end_date, u.worker_id
),
spans AS (
    SELECT month_end_date, ancestor_worker_id AS worker_id,
           COUNT(*) FILTER (WHERE hops = 1) AS direct_reports,
           COUNT(*)                         AS total_reports
    FROM intermediate.int_worker_reporting_chain
    GROUP BY ALL
)
SELECT
    r.*,
    COALESCE(sp.direct_reports, 0) AS direct_reports,
    COALESCE(sp.total_reports, 0)  AS total_reports
FROM rollup AS r
LEFT JOIN spans AS sp USING (month_end_date, worker_id);
