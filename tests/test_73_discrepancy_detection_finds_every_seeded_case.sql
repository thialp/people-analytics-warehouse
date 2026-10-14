-- The warehouse's discrepancy rules find every discrepancy the generator seeded: on every
-- month-end, for every type, recall is 100%. A rule never reads the answer key, so this is a real
-- test of the rules. The only false flags allowed are One person, two IDs (CW07) between two
-- different people who share a name, supplier and cost center and started a day apart: the
-- systems cannot tell them from a real duplicate, and the work list says so. Any other false flag,
-- and any difference the rules cannot explain, fails the build.
SELECT month_end_date, discrepancy_code, 'seeded discrepancy missed' AS problem, missed AS n
FROM marts.mart_cw_detection_score WHERE missed > 0
UNION ALL
SELECT month_end_date, discrepancy_code, 'false flag', false_flags
FROM marts.mart_cw_detection_score WHERE false_flags > 0 AND discrepancy_code <> 'CW07'
UNION ALL
SELECT month_end_date, discrepancy_code, 'difference no recorded change explains', COUNT(*)
FROM intermediate.int_cw_discrepancy WHERE discrepancy_code = 'Unexplained' GROUP BY 1, 2
