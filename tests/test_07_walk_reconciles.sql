-- The core control: for every department and month,
--   Opening + all drivers = Closing
-- for headcount, FTE and all four pay measures. Tolerance covers cent rounding only.
WITH totals AS (
    SELECT
        month_end_date,
        department_id,
        SUM(CASE WHEN driver = 'Opening Run-Rate' THEN headcount ELSE 0 END)           AS hc_open,
        SUM(CASE WHEN driver NOT IN ('Opening Run-Rate', 'Closing Run-Rate')
                 THEN headcount ELSE 0 END)                                            AS hc_moves,
        SUM(CASE WHEN driver = 'Closing Run-Rate' THEN headcount ELSE 0 END)           AS hc_close,
        SUM(CASE WHEN driver = 'Closing Run-Rate' THEN -fte ELSE fte END)              AS fte_gap,
        SUM(CASE WHEN driver = 'Closing Run-Rate' THEN -base_usd_nominal    ELSE base_usd_nominal    END) AS base_nom_gap,
        SUM(CASE WHEN driver = 'Closing Run-Rate' THEN -base_usd_constant   ELSE base_usd_constant   END) AS base_con_gap,
        SUM(CASE WHEN driver = 'Closing Run-Rate' THEN -loaded_usd_nominal  ELSE loaded_usd_nominal  END) AS load_nom_gap,
        SUM(CASE WHEN driver = 'Closing Run-Rate' THEN -loaded_usd_constant ELSE loaded_usd_constant END) AS load_con_gap,
        COUNT(*)                                                                       AS driver_rows
    FROM marts.mart_workforce_cost_bridge
    GROUP BY month_end_date, department_id
)
SELECT *
FROM totals
WHERE hc_open + hc_moves <> hc_close
   OR ABS(fte_gap)      > 0.01
   OR ABS(base_nom_gap) > 0.01 * driver_rows
   OR ABS(base_con_gap) > 0.01 * driver_rows
   OR ABS(load_nom_gap) > 0.01 * driver_rows
   OR ABS(load_con_gap) > 0.01 * driver_rows
