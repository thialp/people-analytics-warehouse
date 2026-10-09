-- The six views of the office moves must tell one story. For every date pair:
--   * the Company view counts each mover once (all 'Both');
--   * the Office view counts each mover once leaving an office ('From') and once joining one ('To');
--   * the Country view splits the same movers into inside one country ('Both') and across a
--     border ('From'/'To'), and 'Both' is exactly the Domestic scope;
--   * no flow starts and ends at the same office, and no row lacks a group name.
-- Returns one row per broken rule.
WITH pair AS (
    SELECT from_month_end, to_month_end,
           SUM(CASE WHEN view_name = 'Company' THEN workers ELSE 0 END)                          AS company,
           SUM(CASE WHEN view_name = 'Office'  AND group_side = 'To'   THEN workers ELSE 0 END)  AS office_in,
           SUM(CASE WHEN view_name = 'Office'  AND group_side = 'From' THEN workers ELSE 0 END)  AS office_out,
           SUM(CASE WHEN view_name = 'Country' AND group_side = 'Both' THEN workers ELSE 0 END)  AS country_both,
           SUM(CASE WHEN view_name = 'Country' AND group_side = 'To'   THEN workers ELSE 0 END)  AS country_in,
           SUM(CASE WHEN view_name = 'Country' AND group_side = 'From' THEN workers ELSE 0 END)  AS country_out,
           SUM(CASE WHEN view_name = 'Company' AND flow_scope = 'Domestic' THEN workers ELSE 0 END) AS company_domestic
    FROM marts.mart_office_moves
    GROUP BY ALL
)
SELECT from_month_end, to_month_end, 'views disagree' AS rule, company, office_in, office_out, country_both, country_in, country_out
FROM pair
WHERE company <> office_in OR company <> office_out
   OR company <> country_both + country_in OR country_in <> country_out
   OR country_both <> company_domestic
UNION ALL
SELECT from_month_end, to_month_end, 'same office or no name', workers, NULL, NULL, NULL, NULL, NULL
FROM marts.mart_office_moves
WHERE from_location_id = to_location_id OR group_name IS NULL
   OR (view_name = 'Office' AND group_side = 'Both')
   OR (group_side = 'Both' AND view_name = 'Country' AND flow_scope <> 'Domestic')
   OR (group_side <> 'Both' AND view_name = 'Country' AND flow_scope <> 'International')
