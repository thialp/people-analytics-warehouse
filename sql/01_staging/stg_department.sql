-- stg_department
-- Organization hierarchy: function > sub-function > department.
CREATE OR REPLACE TABLE staging.stg_department AS
SELECT
    department_id,
    department_name,
    sub_function,
    "function"                                  AS function_name,
    cost_center,
    CAST(effective_from_date AS DATE)           AS effective_from_date
FROM raw.dim_department;
