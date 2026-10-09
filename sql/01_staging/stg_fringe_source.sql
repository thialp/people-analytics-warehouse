-- stg_fringe_source
-- One row per country, year, fringe component and source document.
CREATE OR REPLACE TABLE staging.stg_fringe_source AS
SELECT
    country_code,
    CAST("year" AS INTEGER) AS fringe_year,
    component,
    source_id,
    source_title,
    source_url
FROM raw.ref_fringe_source;
