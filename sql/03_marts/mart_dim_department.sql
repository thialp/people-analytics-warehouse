-- mart_dim_department
-- Grain: one row per department, with its sub-function, function and cost center.
CREATE OR REPLACE TABLE marts.mart_dim_department AS
SELECT department_id, department_name, sub_function, function_name, cost_center
FROM staging.stg_department
ORDER BY department_id;
