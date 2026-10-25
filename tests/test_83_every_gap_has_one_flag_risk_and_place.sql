-- Dashboard #4's Sankey: every gap has exactly one flag, one risk and one place, the risk is the
-- flag's own, the place is one of the three, Integration gaps carry their shade and nothing else
-- does, and a contractor has a flag at most once per close.
SELECT 'more than one row for a gap' AS problem, month_end_date, gap_id, COUNT(*) AS n
FROM marts.mart_cw_gap_close GROUP BY month_end_date, gap_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'risk is not the flag''s', g.month_end_date, g.gap_id, 1
FROM marts.mart_cw_gap_close AS g JOIN intermediate.int_cw_flag_type AS t USING (flag_code)
WHERE g.risk IS DISTINCT FROM t.risk OR g.risk_order IS DISTINCT FROM t.risk_order
UNION ALL
SELECT 'unknown place or missing piece', month_end_date, gap_id, 1
FROM marts.mart_cw_gap_close
WHERE place NOT IN ('Bridgeway', 'Keystone', 'Integration') OR flag_code IS NULL OR risk IS NULL
   OR (place = 'Integration') <> (timing_class IS NOT NULL)
   OR place_key NOT IN ('Bridgeway', 'Keystone', 'Integration: clears on its own', 'Integration: alert data engineering')
UNION ALL
SELECT 'flag ranks are not 1..n', month_end_date, NULL, COUNT(DISTINCT flag_code)
FROM marts.mart_cw_gap_close GROUP BY month_end_date
HAVING MAX(flag_rank) <> COUNT(DISTINCT flag_code) OR COUNT(DISTINCT flag_rank) <> COUNT(DISTINCT flag_code)
