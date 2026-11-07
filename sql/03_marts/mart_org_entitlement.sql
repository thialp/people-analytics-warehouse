-- mart_org_entitlement
-- Grain: one row per leader x person they may see, on the report date: the leader themselves and
-- everyone below them in the solid line (release 7, case study 7).
--
-- This is the row-level security table for Tableau Cloud. A leader signs in with their work email;
-- the data source keeps a row when USERNAME() matches viewer_email for that person, so a leader sees
-- only their own branch. People Analytics sees everyone through a group (ISMEMBEROF), not through
-- rows here.
CREATE OR REPLACE TABLE marts.mart_org_entitlement AS
WITH rc AS (SELECT report_as_of_date FROM staging.stg_report_calendar)
SELECT c.ancestor_id AS viewer_leader_id, w.work_email AS viewer_email, l.leader_level AS viewer_leader_level,
       c.descendant_id AS person_id, c.depth
FROM intermediate.int_org_closure AS c
JOIN rc ON c.month_end_date = rc.report_as_of_date
JOIN intermediate.int_org_leader AS l ON l.month_end_date = c.month_end_date AND l.leader_id = c.ancestor_id
JOIN staging.stg_worker AS w ON w.worker_id = c.ancestor_id;
