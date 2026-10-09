-- Every unit in the org design (company, function, sub-function, department) has
-- exactly one leader at every month-end. Data & AI Platform exists from the FY25
-- reorganization (2024-11-01).
WITH units AS (
    SELECT cal.month_end_date, ou.org_unit_id
    FROM intermediate.int_month_end_calendar AS cal
    CROSS JOIN staging.stg_org_unit AS ou
    LEFT JOIN staging.stg_department AS d ON d.department_id = ou.org_unit_id
    WHERE d.effective_from_date IS NULL OR d.effective_from_date <= cal.month_end_date
),
leaders AS (
    SELECT month_end_date, leads_org_unit_id AS org_unit_id, COUNT(*) AS n
    FROM intermediate.int_worker_month_end_snapshot
    WHERE leads_org_unit_id IS NOT NULL
    GROUP BY ALL
)
SELECT u.month_end_date, u.org_unit_id, COALESCE(l.n, 0) AS leaders
FROM units AS u
LEFT JOIN leaders AS l USING (month_end_date, org_unit_id)
WHERE COALESCE(l.n, 0) <> 1
