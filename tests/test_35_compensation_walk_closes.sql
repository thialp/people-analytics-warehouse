-- The compensation walk must close for every date pair, view and group:
-- Opening + every step = Closing. Headcount and FTE exactly; dollars within half a
-- cent per published line (each line is rounded to the cent); the average walk within
-- a hundredth of a cent per line.
WITH g AS (
    SELECT
        from_month_end, to_month_end, view_name, group_id, COUNT(*) AS lines,
        SUM(CASE WHEN step = 'Closing' THEN -headcount           ELSE headcount           END) AS d_hc,
        SUM(CASE WHEN step = 'Closing' THEN -fte                 ELSE fte                 END) AS d_fte,
        SUM(CASE WHEN step = 'Closing' THEN -base_usd_nominal    ELSE base_usd_nominal    END) AS d_bn,
        SUM(CASE WHEN step = 'Closing' THEN -base_usd_constant   ELSE base_usd_constant   END) AS d_bc,
        SUM(CASE WHEN step = 'Closing' THEN -loaded_usd_nominal  ELSE loaded_usd_nominal  END) AS d_ln,
        SUM(CASE WHEN step = 'Closing' THEN -loaded_usd_constant ELSE loaded_usd_constant END) AS d_lc,
        SUM(CASE WHEN step = 'Closing' THEN -avg_base_usd_nominal    ELSE avg_base_usd_nominal    END) AS d_abn,
        SUM(CASE WHEN step = 'Closing' THEN -avg_base_usd_constant   ELSE avg_base_usd_constant   END) AS d_abc,
        SUM(CASE WHEN step = 'Closing' THEN -avg_loaded_usd_nominal  ELSE avg_loaded_usd_nominal  END) AS d_aln,
        SUM(CASE WHEN step = 'Closing' THEN -avg_loaded_usd_constant ELSE avg_loaded_usd_constant END) AS d_alc
    FROM marts.mart_compensation_walk
    GROUP BY ALL
)
SELECT * FROM g
WHERE d_hc <> 0 OR d_fte <> 0
   OR GREATEST(ABS(d_bn), ABS(d_bc), ABS(d_ln), ABS(d_lc))     > 0.005 * lines
   OR GREATEST(ABS(d_abn), ABS(d_abc), ABS(d_aln), ABS(d_alc)) > 0.0001 * lines
