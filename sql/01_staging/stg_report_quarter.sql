-- stg_report_quarter
-- One row per fiscal quarter in the report window: five years of history and the forward year
-- (release 5), with labels and offsets from the as-of date (fy_offset 0 = the current fiscal
-- year, +1 the forward year; quarter_offset 0 = the quarter ending on the as-of date).
-- Source: generator/report_calendar.py.
CREATE OR REPLACE TABLE staging.stg_report_quarter AS
SELECT
    CAST(fiscal_year AS INTEGER)                             AS fiscal_year,
    fiscal_year_label,
    CAST(fiscal_quarter AS INTEGER)                          AS fiscal_quarter,
    quarter_label,
    quarter_months_label,
    CAST(quarter_start_date AS DATE)                         AS quarter_start_date,
    CAST(quarter_end_date AS DATE)                           AS quarter_end_date,
    CAST(fy_offset AS INTEGER)                               AS fy_offset,
    CAST(quarter_offset AS INTEGER)                          AS quarter_offset,
    CAST(is_forward AS BOOLEAN)                              AS is_forward
FROM raw.ref_report_quarter;
