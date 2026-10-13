-- stg_worker
-- One row per worker ever employed. Raw files land as text; types are set here.
CREATE OR REPLACE TABLE staging.stg_worker AS
SELECT
    worker_id,
    first_name,
    last_name,
    first_name || ' ' || last_name                  AS worker_name,
    CAST(original_hire_date AS DATE)                AS original_hire_date,
    CAST(NULLIF(termination_date, '') AS DATE)      AS termination_date,
    NULLIF(termination_type, '')                    AS termination_type,
    worker_type,
    CAST(is_executive_officer AS BOOLEAN)           AS is_executive_officer
FROM raw.dim_worker;
