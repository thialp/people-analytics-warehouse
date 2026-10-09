-- stg_performance_review
-- One rating per worker per fiscal year, given on the fiscal year-end (June 30) to
-- everyone employed at least three months.
CREATE OR REPLACE TABLE staging.stg_performance_review AS
SELECT
    review_id,
    worker_id,
    CAST(fiscal_year AS INTEGER)   AS fiscal_year,
    CAST(review_date AS DATE)      AS review_date,
    rating,
    CAST(bonus_pct AS DOUBLE)      AS bonus_pct
FROM raw.fact_performance_review;
