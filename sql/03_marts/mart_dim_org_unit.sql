-- mart_dim_org_unit
-- Grain: one row per org unit (company, function, sub-function, department), with
-- its parent, so Tableau can draw the org design as a tree.
CREATE OR REPLACE TABLE marts.mart_dim_org_unit AS
SELECT org_unit_id, org_unit_name, org_unit_type, parent_org_unit_id, function_name,
       leader_title, leader_grade
FROM staging.stg_org_unit
ORDER BY CASE org_unit_type WHEN 'Company' THEN 1 WHEN 'Function' THEN 2
                            WHEN 'Sub-function' THEN 3 ELSE 4 END, org_unit_id;
