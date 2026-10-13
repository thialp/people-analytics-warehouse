-- stg_tenure_increase
-- Raise on each hire anniversary by completed years of service (base pay only).
CREATE OR REPLACE TABLE staging.stg_tenure_increase AS
SELECT
    CAST(tenure_year_from AS INTEGER) AS tenure_year_from,
    CAST(tenure_year_to AS INTEGER)   AS tenure_year_to,
    CAST(increase_pct AS DOUBLE)      AS increase_pct
FROM raw.ref_tenure_increase;
