-- A cost center is the department in one country: every seat record and requisition
-- carries the cost center of its department and its office's country, and that cost
-- center exists.
SELECT 'position' AS source, p.position_record_id AS id, p.cost_center_id, p.department_id, l.country_code
FROM staging.stg_position AS p
JOIN staging.stg_location AS l USING (location_id)
LEFT JOIN staging.stg_cost_center AS c ON c.cost_center_id = p.cost_center_id
WHERE c.cost_center_id IS NULL OR c.department_id <> p.department_id OR c.country_code <> l.country_code
UNION ALL
SELECT 'requisition', r.requisition_id, r.cost_center_id, r.department_id, l.country_code
FROM staging.stg_requisition AS r
JOIN staging.stg_location AS l USING (location_id)
LEFT JOIN staging.stg_cost_center AS c ON c.cost_center_id = r.cost_center_id
WHERE c.cost_center_id IS NULL OR c.department_id <> r.department_id OR c.country_code <> l.country_code
