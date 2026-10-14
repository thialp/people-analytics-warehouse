-- mart_location_headcount
-- Grain: one row per month-end per office location per worker type.
--
-- A headcount walk by office, one column per movement, for the map:
--
--   opening_headcount + hires - voluntary_terminations - involuntary_terminations
--     + contingent_starts - contingent_ends + conversions_in - conversions_out
--     + relocations_in - relocations_out = closing_headcount
--
-- Release 3: worker_type is Employee or Contingent (Bridgeway office, as held at each
-- month-end). Each worker type uses its own columns: employees hires and terminations,
-- contingent workers starts and ends; a contingent worker hired as an employee is a
-- conversion out of the Contingent row and into the Employee row (not an employee hire).
-- Filter on worker_type, or sum both for the whole workforce.
--
-- Movements are stored as positive counts here (the column name carries the
-- direction) because a wide table is what a map mark needs: one row per point.
-- A relocation is any change of office between two month-ends, including moves
-- between two offices in the same country, which the slice-level walk does not
-- see. Relocations net to zero across the company every month (test 21).
CREATE OR REPLACE TABLE marts.mart_location_headcount AS
WITH m AS (
    SELECT mv.*, cv.worker_id IS NOT NULL AS is_conversion
    FROM intermediate.int_worker_movement AS mv
    LEFT JOIN intermediate.int_cw_conversion AS cv
           ON cv.worker_id = mv.worker_id AND cv.month_end_date = mv.month_end_date AND cv.is_walk_conversion
),

c AS (
    SELECT * FROM intermediate.int_cw_movement
),

lines AS (
    --                                                         open hire vol invl strt end cvin cvot rin rout clos fte
    SELECT month_end_date, prior_location_id AS location_id, 'Employee' AS worker_type,
           1 AS opening, 0 AS hires, 0 AS vol, 0 AS invol, 0 AS starts, 0 AS ends, 0 AS conv_in, 0 AS conv_out,
           0 AS rel_in, 0 AS rel_out, 0 AS closing, 0.0 AS closing_fte
    FROM m WHERE in_prior
    UNION ALL
    SELECT month_end_date, current_location_id, 'Employee', 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    FROM m WHERE movement_type = 'Hire' AND NOT is_conversion
    UNION ALL
    SELECT month_end_date, current_location_id, 'Employee', 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0
    FROM m WHERE movement_type = 'Hire' AND is_conversion
    UNION ALL
    SELECT month_end_date, prior_location_id, 'Employee', 0, 0,
           CASE WHEN movement_reason = 'Voluntary' THEN 1 ELSE 0 END,
           CASE WHEN movement_reason = 'Voluntary' THEN 0 ELSE 1 END, 0, 0, 0, 0, 0, 0, 0, 0
    FROM m WHERE movement_type = 'Termination'
    UNION ALL
    SELECT month_end_date, current_location_id, 'Employee', 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0
    FROM m WHERE in_prior AND in_current AND prior_location_id <> current_location_id
    UNION ALL
    SELECT month_end_date, prior_location_id, 'Employee', 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0
    FROM m WHERE in_prior AND in_current AND prior_location_id <> current_location_id
    UNION ALL
    SELECT month_end_date, current_location_id, 'Employee', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, current_fte
    FROM m WHERE in_current

    UNION ALL
    SELECT month_end_date, prior_location_id, 'Contingent', 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0
    FROM c WHERE in_prior
    UNION ALL
    SELECT month_end_date, current_location_id, 'Contingent', 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0
    FROM c WHERE movement_type = 'Start'
    UNION ALL
    SELECT month_end_date, prior_location_id, 'Contingent', 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0
    FROM c WHERE movement_type = 'End'
    UNION ALL
    SELECT month_end_date, prior_location_id, 'Contingent', 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0
    FROM c WHERE movement_type = 'Conversion'
    UNION ALL
    SELECT month_end_date, current_location_id, 'Contingent', 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0
    FROM c WHERE in_prior AND in_current AND prior_location_id <> current_location_id
    UNION ALL
    SELECT month_end_date, prior_location_id, 'Contingent', 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0
    FROM c WHERE in_prior AND in_current AND prior_location_id <> current_location_id
    UNION ALL
    SELECT month_end_date, current_location_id, 'Contingent', 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1.0
    FROM c WHERE in_current
)

SELECT
    month_end_date,
    location_id,
    worker_type,
    CAST(SUM(opening)  AS INTEGER)                       AS opening_headcount,
    CAST(SUM(hires)    AS INTEGER)                       AS hires,
    CAST(SUM(vol)      AS INTEGER)                       AS voluntary_terminations,
    CAST(SUM(invol)    AS INTEGER)                       AS involuntary_terminations,
    CAST(SUM(starts)   AS INTEGER)                       AS contingent_starts,
    CAST(SUM(ends)     AS INTEGER)                       AS contingent_ends,
    CAST(SUM(conv_in)  AS INTEGER)                       AS conversions_in,
    CAST(SUM(conv_out) AS INTEGER)                       AS conversions_out,
    CAST(SUM(rel_in)   AS INTEGER)                       AS relocations_in,
    CAST(SUM(rel_out)  AS INTEGER)                       AS relocations_out,
    CAST(SUM(closing)  AS INTEGER)                       AS closing_headcount,
    ROUND(SUM(CAST(closing_fte AS DECIMAL(18, 4))), 2)   AS closing_fte
FROM lines
GROUP BY ALL
ORDER BY month_end_date, location_id, worker_type DESC;
