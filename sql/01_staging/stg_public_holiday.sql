-- stg_public_holiday
-- National public holidays by country (python-holidays).
-- Source: ref_public_holiday (see generator/source_systems.py). Added in release 7.
CREATE OR REPLACE TABLE staging.stg_public_holiday AS
SELECT
    NULLIF(country_code, '')                                 AS country_code,
    CAST(NULLIF(holiday_date, '') AS DATE)                   AS holiday_date,
    NULLIF(holiday_name, '')                                 AS holiday_name,
    NULLIF(source, '')                                       AS source
FROM raw.ref_public_holiday;
