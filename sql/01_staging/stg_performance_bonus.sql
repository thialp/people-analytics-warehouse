-- stg_performance_bonus
-- Bonus as a share of base salary for each annual rating, and the target rating mix.
CREATE OR REPLACE TABLE staging.stg_performance_bonus AS
SELECT
    rating,
    CAST(bonus_pct AS DOUBLE)    AS bonus_pct,
    CAST(target_share AS DOUBLE) AS target_share
FROM raw.ref_performance_bonus;
