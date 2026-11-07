-- Release 7 Canopy tree layout: every leader on the report date can be the focus in both modes;
-- every child leader sits once under its parent's focus at tier 1; every circle is on the canvas
-- (x 0 to 1); every link has 17 points and runs from its parent's circle to its own.
WITH leaders AS (
    SELECT l.leader_id, l.parent_leader_id
    FROM intermediate.int_org_leader AS l
    JOIN staging.stg_report_calendar AS rc ON l.month_end_date = rc.report_as_of_date
),
nodes AS (SELECT * FROM marts.mart_org_tree_layout WHERE mark_type = 'Node'),
links AS (SELECT * FROM marts.mart_org_tree_layout WHERE mark_type = 'Link')
SELECT 'leader is not a focus' AS problem, l.leader_id || ' ' || m.tree_mode AS id, '' AS detail
FROM leaders AS l CROSS JOIN (VALUES ('Dynamic'), ('Static')) AS m (tree_mode)
WHERE NOT EXISTS (SELECT 1 FROM nodes AS n WHERE n.tree_mode = m.tree_mode AND n.focus_leader_id = l.leader_id
                  AND n.tier = 0 AND n.node_id = l.leader_id)
UNION ALL
SELECT 'child leader not at tier 1 once', l.leader_id || ' ' || m.tree_mode, CAST(COUNT(n.node_id) AS VARCHAR)
FROM leaders AS l CROSS JOIN (VALUES ('Dynamic'), ('Static')) AS m (tree_mode)
LEFT JOIN nodes AS n ON n.tree_mode = m.tree_mode AND n.focus_leader_id = l.parent_leader_id
                    AND n.tier = 1 AND n.node_id = l.leader_id
WHERE l.parent_leader_id IS NOT NULL
GROUP BY l.leader_id, m.tree_mode HAVING COUNT(n.node_id) <> 1
UNION ALL
SELECT 'circle off the canvas', node_id || ' in ' || focus_leader_id || ' ' || tree_mode, CAST(x AS VARCHAR)
FROM nodes WHERE x < 0 OR x > 1
UNION ALL
SELECT 'link without 17 points', node_id || ' in ' || focus_leader_id || ' ' || tree_mode, CAST(COUNT(*) AS VARCHAR)
FROM links GROUP BY tree_mode, focus_leader_id, node_id HAVING COUNT(*) <> 17
UNION ALL
SELECT 'link does not join its circles', k.node_id || ' in ' || k.focus_leader_id || ' ' || k.tree_mode,
       CAST(k.point_index AS VARCHAR)
FROM links AS k
JOIN nodes AS e ON e.tree_mode = k.tree_mode AND e.focus_leader_id = k.focus_leader_id
               AND e.node_id = CASE WHEN k.point_index = 0 THEN k.parent_node_id ELSE k.node_id END
WHERE k.point_index IN (0, 16) AND (ABS(e.x - k.x) > 1e-5 OR ABS(e.y - k.y) > 1e-5)
