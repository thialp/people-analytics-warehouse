-- int_assignment_signal
-- Grain: one row per active role assignment x month-end whose target name carries a leader who no
-- longer leads that org unit (release 7, case study 7: "Still naming a former leader").
--
-- A role assignment (HR partner, Finance partner) is issued for an org unit and its name carries
-- the unit's leader at the time. After a leadership change it should be re-issued; when it is
-- not, it keeps naming the former leader. The signal sits with the unit's current leader.
CREATE OR REPLACE TABLE intermediate.int_assignment_signal AS
WITH months AS (SELECT DISTINCT month_end_date FROM intermediate.int_person_month_end),
cur_leader AS (
    SELECT month_end_date, leads_org_unit_id AS org_unit_id, person_id AS leader_id
    FROM intermediate.int_person_month_end
    WHERE leads_org_unit_id IS NOT NULL
)
SELECT m.month_end_date, a.assignment_id, a.role_name, a.assignee_worker_id, a.target_org_unit_id,
       a.target_org_name, a.named_leader_worker_id, a.assigned_via, cl.leader_id AS current_leader_id,
       'R1' AS signal_code, 'Still naming a former leader' AS signal_name, 'Role assignments' AS signal_line
FROM months AS m
JOIN staging.stg_role_assignment AS a
  ON m.month_end_date BETWEEN a.effective_start_date AND a.effective_end_date_filled
JOIN cur_leader AS cl ON cl.month_end_date = m.month_end_date AND cl.org_unit_id = a.target_org_unit_id
WHERE a.named_leader_worker_id IS DISTINCT FROM cl.leader_id;
