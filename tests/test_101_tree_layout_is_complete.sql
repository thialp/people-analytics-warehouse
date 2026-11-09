-- Release 7 Canopy tree layout.
-- Dynamic: one company tree; every leader on the report date is in it once, at its depth below the
--   CEO, with its parent one tier up; no two leaders who share a parent share a spot.
-- Static: every leader can be the focus; every child leader sits once under its parent's focus at
--   tier 1; every circle is on the 0 to 1 canvas.
-- Both: every link has 17 points and runs from its parent's circle to its own.
WITH leaders AS (
    SELECT l.leader_id, l.parent_leader_id
    FROM intermediate.int_org_leader AS l
    JOIN staging.stg_report_calendar AS rc ON l.month_end_date = rc.report_as_of_date
),
nodes AS (SELECT * FROM marts.mart_org_tree_layout WHERE mark_type = 'Node'),
links AS (SELECT * FROM marts.mart_org_tree_layout WHERE mark_type = 'Link'),
dyn AS (SELECT * FROM nodes WHERE tree_mode = 'Dynamic')
SELECT 'leader not in the company tree once' AS problem, l.leader_id AS id, CAST(COUNT(d.node_id) AS VARCHAR) AS detail
FROM leaders AS l LEFT JOIN dyn AS d ON d.node_id = l.leader_id
GROUP BY l.leader_id HAVING COUNT(d.node_id) <> 1
UNION ALL
SELECT 'company tree: parent not one tier up', d.node_id, CAST(d.tier AS VARCHAR)
FROM dyn AS d LEFT JOIN dyn AS p ON p.node_id = d.parent_node_id
WHERE (d.parent_node_id IS NULL AND d.tier <> 0) OR (d.parent_node_id IS NOT NULL AND (p.node_id IS NULL OR p.tier <> d.tier - 1))
UNION ALL
SELECT 'company tree: two leaders of one team on one spot', MIN(node_id), parent_node_id || ' at ' || CAST(x AS VARCHAR)
FROM dyn GROUP BY parent_node_id, x HAVING COUNT(*) > 1
UNION ALL
SELECT 'leader is not a static focus', l.leader_id, ''
FROM leaders AS l
WHERE NOT EXISTS (SELECT 1 FROM nodes AS n WHERE n.tree_mode = 'Static' AND n.focus_leader_id = l.leader_id
                  AND n.tier = 0 AND n.node_id = l.leader_id)
UNION ALL
SELECT 'child leader not at static tier 1 once', l.leader_id, CAST(COUNT(n.node_id) AS VARCHAR)
FROM leaders AS l
LEFT JOIN nodes AS n ON n.tree_mode = 'Static' AND n.focus_leader_id = l.parent_leader_id
                    AND n.tier = 1 AND n.node_id = l.leader_id
WHERE l.parent_leader_id IS NOT NULL
GROUP BY l.leader_id HAVING COUNT(n.node_id) <> 1
UNION ALL
SELECT 'static circle off the canvas', node_id || ' in ' || focus_leader_id, CAST(x AS VARCHAR)
FROM nodes WHERE tree_mode = 'Static' AND (x < 0 OR x > 1)
UNION ALL
SELECT 'link without 17 points', node_id || ' in ' || COALESCE(focus_leader_id, 'the company tree') || ' ' || tree_mode,
       CAST(COUNT(*) AS VARCHAR)
FROM links GROUP BY tree_mode, focus_leader_id, node_id HAVING COUNT(*) <> 17
UNION ALL
SELECT 'link does not join its circles', k.node_id || ' in ' || COALESCE(k.focus_leader_id, 'the company tree') || ' ' || k.tree_mode,
       CAST(k.point_index AS VARCHAR)
FROM links AS k
JOIN nodes AS e ON e.tree_mode = k.tree_mode AND e.focus_leader_id IS NOT DISTINCT FROM k.focus_leader_id
               AND e.node_id = CASE WHEN k.point_index = 0 THEN k.parent_node_id ELSE k.node_id END
WHERE k.point_index IN (0, 16) AND (ABS(e.x - k.x) > 1e-5 OR ABS(e.y - k.y) > 1e-5)
