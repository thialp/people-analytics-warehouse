-- mart_dim_month
-- Grain: one row per month-end in the walk (the first month-end has no prior
-- month, so it opens the history and is not walked).
-- Fiscal year starts July 1 (FY2026 = 2025-07-01 to 2026-06-30).
CREATE OR REPLACE TABLE marts.mart_dim_month AS
SELECT
    month_end_date,
    prior_month_end_date,
    fiscal_year,
    'FY' || RIGHT(CAST(fiscal_year AS VARCHAR), 2)  AS fiscal_year_label,
    fiscal_quarter_label,
    fiscal_period,
    fiscal_month,
    is_fiscal_year_end
FROM intermediate.int_month_end_calendar
WHERE prior_month_end_date IS NOT NULL
ORDER BY month_end_date;
