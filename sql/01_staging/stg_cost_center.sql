-- stg_cost_center
-- Cost centers: one per department and country (CC-1010-US = department cost center
-- CC-1010, Core Platform Engineering, in the United States). Seats, requisitions and the
-- workforce plan are all kept by cost center, so a seat that moves to another country
-- changes cost center.
CREATE OR REPLACE TABLE staging.stg_cost_center AS
SELECT
    cost_center_id,
    cost_center_name,
    department_id,
    department_cost_center,
    country_code,
    "function"                                               AS function_name
FROM raw.dim_cost_center;
