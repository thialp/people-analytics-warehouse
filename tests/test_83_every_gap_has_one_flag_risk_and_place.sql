-- Dashboard #4's Sankey: every gap has exactly one flag, one risk and one place, the risk is the
-- flag's own, the place is one of the three with its label, only system feed gaps carry a timing
-- class (and every one does), and a contractor has a flag at most once per close.
-- The Sankey extension orders its first column by the sort (flag_label, alphabetical) and every
-- later column by first appearance in that order: so at every close the risks and the places must
-- first appear in alphabetical order, or the page would not read alphabetically in all three.
WITH rows_in_sankey_order AS (
    SELECT month_end_date, flag_label, risk, place_label,
           ROW_NUMBER() OVER (PARTITION BY month_end_date ORDER BY flag_label, risk, place_label) AS rn
    FROM (SELECT DISTINCT month_end_date, flag_label, risk, place_label FROM marts.mart_cw_gap_close)
),
first_risk AS (SELECT month_end_date, risk AS node, MIN(rn) AS first_rn FROM rows_in_sankey_order GROUP BY 1, 2),
first_place AS (SELECT month_end_date, place_label AS node, MIN(rn) AS first_rn FROM rows_in_sankey_order GROUP BY 1, 2)
SELECT 'more than one row for a gap' AS problem, month_end_date, gap_id, COUNT(*) AS n
FROM marts.mart_cw_gap_close GROUP BY month_end_date, gap_id HAVING COUNT(*) > 1
UNION ALL
SELECT 'risk or label is not the flag''s', g.month_end_date, g.gap_id, 1
FROM marts.mart_cw_gap_close AS g JOIN intermediate.int_cw_flag_type AS t USING (flag_code)
WHERE g.risk IS DISTINCT FROM t.risk OR g.risk_order IS DISTINCT FROM t.risk_order
   OR g.flag_label IS DISTINCT FROM t.flag_label
UNION ALL
SELECT 'unknown place or missing piece', month_end_date, gap_id, 1
FROM marts.mart_cw_gap_close
WHERE place NOT IN ('Bridgeway', 'Keystone', 'System feed') OR flag_code IS NULL OR risk IS NULL
   OR (place = 'System feed') <> (timing_class IS NOT NULL)
   OR place_label <> CASE place WHEN 'Bridgeway' THEN 'Bridgeway (vendor system)'
                                WHEN 'Keystone' THEN 'Keystone (HR system)'
                                ELSE 'System feed (integration)' END
UNION ALL
SELECT 'flag ranks are not 1..n', month_end_date, NULL, COUNT(DISTINCT flag_code)
FROM marts.mart_cw_gap_close GROUP BY month_end_date
HAVING MAX(flag_rank) <> COUNT(DISTINCT flag_code) OR COUNT(DISTINCT flag_rank) <> COUNT(DISTINCT flag_code)
UNION ALL
SELECT 'Sankey: ' || kind || ' not in alphabetical order', month_end_date, node, first_rn
FROM (SELECT 'risks' AS kind, *, LAG(node) OVER (PARTITION BY month_end_date ORDER BY first_rn) AS prev FROM first_risk
      UNION ALL
      SELECT 'places', *, LAG(node) OVER (PARTITION BY month_end_date ORDER BY first_rn) FROM first_place)
WHERE prev > node
