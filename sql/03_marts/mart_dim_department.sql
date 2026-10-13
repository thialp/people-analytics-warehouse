-- mart_dim_department
-- Grain: one row per department, with its sub-function, function, parent org unit,
-- cost center and the job level its head is expected to hold.
CREATE OR REPLACE TABLE marts.mart_dim_department AS
SELECT department_id, department_name, sub_function, function_name, parent_org_unit_id,
       cost_center, head_grade
FROM staging.stg_department
ORDER BY department_id;
