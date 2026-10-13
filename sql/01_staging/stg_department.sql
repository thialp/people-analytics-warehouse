-- stg_department
-- Organization: function > sub-function > department, with each department's parent
-- org unit (a sub-function where the function has several, otherwise the function).
CREATE OR REPLACE TABLE staging.stg_department AS
SELECT
    department_id,
    department_name,
    sub_function,
    "function"                                  AS function_name,
    parent_org_unit_id,
    cost_center,
    CAST(head_job_level AS INTEGER)             AS head_grade,
    CAST(effective_from_date AS DATE)           AS effective_from_date
FROM raw.dim_department;
