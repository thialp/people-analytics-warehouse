-- Release 7 ties to the published numbers: on every month-end the people in the leadership view are
-- the employees of the month-end snapshot (executive officers excluded) and the contingent workers
-- Bridgeway counts; and the CEO leads all of them except people with no manager on file that day.
WITH ppl AS (
    SELECT month_end_date,
           COUNT(*) FILTER (WHERE worker_type = 'Employee')                                  AS employees,
           COUNT(*) FILTER (WHERE worker_type = 'Contingent')                                AS contingent,
           COUNT(*) FILTER (WHERE manager_worker_id IS NULL)                                 AS no_manager
    FROM intermediate.int_person_month_end WHERE NOT is_executive_officer GROUP BY 1
),
emp AS (SELECT month_end_date, COUNT(*) AS n FROM intermediate.int_worker_month_end_snapshot
        WHERE NOT is_executive_officer GROUP BY 1),
cw AS (SELECT month_end_date, COUNT(*) AS n FROM intermediate.int_cw_month_end_snapshot GROUP BY 1),
top AS (SELECT o.month_end_date, o.people FROM intermediate.int_leader_org AS o
        JOIN intermediate.int_person_month_end AS p ON p.month_end_date = o.month_end_date AND p.person_id = o.leader_id
        WHERE p.is_executive_officer AND p.manager_worker_id IS NULL AND o.worker_type = 'All')
SELECT ppl.month_end_date, ppl.employees, emp.n AS snapshot_employees, ppl.contingent, cw.n AS bridgeway_contingent,
       top.people AS ceo_people, ppl.no_manager
FROM ppl
JOIN emp USING (month_end_date)
JOIN cw USING (month_end_date)
JOIN top USING (month_end_date)
WHERE ppl.employees <> emp.n OR ppl.contingent <> cw.n
   OR top.people + ppl.no_manager <> ppl.employees + ppl.contingent
