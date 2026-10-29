-- stg_report_calendar
-- One row: the report as-of date and every label derived from it (release 5). Dashboards read
-- their dates and fiscal-year labels from here, so moving the as-of date a year rolls every
-- page forward without editing a calculation. Release 6 adds the data-through date: Keystone's Core HR
-- and Compensation run on past the report date to the latest nightly extract (mart_daily_headcount).
-- Source: generator/report_calendar.py.
CREATE OR REPLACE TABLE staging.stg_report_calendar AS
SELECT
    CAST(report_as_of_date AS DATE)                          AS report_as_of_date,
    report_as_of_label,
    CAST(data_through_date AS DATE)                          AS data_through_date,   -- release 6: Core HR's latest nightly extract
    data_through_label,
    CAST(current_fiscal_year AS INTEGER)                     AS current_fiscal_year,
    current_fiscal_year_label,
    CAST(forward_fiscal_year AS INTEGER)                     AS forward_fiscal_year,
    forward_fiscal_year_label,
    CAST(history_first_fiscal_year AS INTEGER)               AS history_first_fiscal_year,
    history_first_fiscal_year_label,
    CAST(history_start_date AS DATE)                         AS history_start_date,
    CAST(forward_start_date AS DATE)                         AS forward_start_date,
    CAST(forward_end_date AS DATE)                           AS forward_end_date,
    forward_period_label,
    forward_budget_version,
    CAST(forward_budget_date AS DATE)                        AS forward_budget_date
FROM raw.ref_report_calendar;
