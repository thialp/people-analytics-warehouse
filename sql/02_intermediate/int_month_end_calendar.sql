-- int_month_end_calendar
-- One row per month-end in the reporting window, with fiscal attributes.
-- The window is driven by the data: every month-end that has FX rates loaded.
-- Fiscal year starts July 1 (FY2026 = 2025-07-01 to 2026-06-30).
CREATE OR REPLACE TABLE intermediate.int_month_end_calendar AS
WITH month_ends AS (
    SELECT DISTINCT rate_date AS month_end_date
    FROM staging.stg_fx_rate
),
fiscal AS (
    SELECT
        month_end_date,
        LAG(month_end_date) OVER (ORDER BY month_end_date)               AS prior_month_end_date,
        CASE WHEN MONTH(month_end_date) >= 7
             THEN YEAR(month_end_date) + 1 ELSE YEAR(month_end_date) END AS fiscal_year,
        ((MONTH(month_end_date) + 5) % 12) + 1                           AS fiscal_month
    FROM month_ends
)
SELECT
    month_end_date,
    prior_month_end_date,
    fiscal_year,
    fiscal_month,
    CAST(CEIL(fiscal_month / 3.0) AS INTEGER)                            AS fiscal_quarter,
    'FY' || RIGHT(CAST(fiscal_year AS VARCHAR), 2)
        || ' P' || LPAD(CAST(fiscal_month AS VARCHAR), 2, '0')           AS fiscal_period,
    'FY' || RIGHT(CAST(fiscal_year AS VARCHAR), 2)
        || ' Q' || CAST(CEIL(fiscal_month / 3.0) AS INTEGER)             AS fiscal_quarter_label,
    fiscal_month = 12                                                    AS is_fiscal_year_end
FROM fiscal;
