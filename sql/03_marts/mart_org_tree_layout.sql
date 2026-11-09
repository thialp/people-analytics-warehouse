-- mart_org_tree_layout
-- Grain: one row per tree mode x focus leader x mark (a circle, or one point of a link), on the
-- report date (release 7, case study 7: the Canopy tree).
--
-- Where every circle and link sits, so Tableau only plots x and y (y top to bottom: reverse the axis).
--   Dynamic  ONE tree for the whole company (focus_leader_id NULL): tier = depth below the CEO
--            (y = tier); each leader's child leaders one unit apart, biggest first, centered under
--            it (x = the parent's x + slot - (slots - 1) / 2). Nothing moves when the focus changes:
--            the page shows the chain from the CEO to the focus with each level's leaders and the
--            focus's own team, so Tableau can animate a click instead of redrawing the tree.
--            Only one team per level is ever shown, so teams of different parents never collide.
--   Static   for every leader as the focus, tiers 1 to 3 at once on a 0 to 1 canvas: tier 1 at the
--            centers of equal shares of the width, tier 2 fanned under its parent in a zigzag,
--            tier 3 as small dots under theirs
-- A link is the curve from the parent's circle to the child's: a cubic Bezier through (x1, y1),
-- (x1, ym), (x2, ym), (x2, y2), drawn as 17 points (point_index 0 to 16).
-- Sizes, colors and counts come from mart_org_node (join on node_id = leader_id).
CREATE OR REPLACE TABLE marts.mart_org_tree_layout AS
WITH RECURSIVE leaders AS (
    SELECT l.leader_id, l.parent_leader_id, l.leader_name, o.people
    FROM intermediate.int_org_leader AS l
    JOIN staging.stg_report_calendar AS rc ON l.month_end_date = rc.report_as_of_date
    JOIN intermediate.int_leader_org AS o
      ON o.month_end_date = l.month_end_date AND o.leader_id = l.leader_id AND o.worker_type = 'All'
),
sib AS (        -- each leader's place among the leaders who share its parent: biggest first
    SELECT leader_id, parent_leader_id,
           ROW_NUMBER() OVER (PARTITION BY parent_leader_id ORDER BY people DESC, leader_name, leader_id) - 1 AS slot,
           COUNT(*) OVER (PARTITION BY parent_leader_id) AS slots
    FROM leaders
    WHERE parent_leader_id IS NOT NULL
),
pos AS (       -- dynamic: the company tree, one level at a time from the CEO
    SELECT l.leader_id AS node_id, CAST(NULL AS VARCHAR) AS parent_node_id, 0 AS tier, 0 AS slot, 1 AS slots,
           0.0::DOUBLE AS x
    FROM leaders AS l WHERE l.parent_leader_id IS NULL
    UNION ALL
    SELECT s.leader_id, s.parent_leader_id, p.tier + 1, s.slot, s.slots, (p.x + (s.slot - (s.slots - 1) / 2.0))::DOUBLE
    FROM pos AS p JOIN sib AS s ON s.parent_leader_id = p.node_id
),
dyn AS (
    SELECT 'Dynamic' AS tree_mode, CAST(NULL AS VARCHAR) AS focus_leader_id, tier, node_id, parent_node_id,
           CAST(NULL AS VARCHAR) AS tier1_node_id, slot, slots, x, tier::DOUBLE AS y
    FROM pos
),
t0 AS (
    SELECT 'Static' AS tree_mode, l.leader_id AS focus_leader_id, 0 AS tier, l.leader_id AS node_id,
           CAST(NULL AS VARCHAR) AS parent_node_id, CAST(NULL AS VARCHAR) AS tier1_node_id,
           0 AS slot, 1 AS slots, 0.5::DOUBLE AS x, 0.0::DOUBLE AS y
    FROM leaders AS l
),
t1 AS (         -- static tier 1: the focus's child leaders, at the centers of equal shares of the width
    SELECT 'Static' AS tree_mode, s.parent_leader_id AS focus_leader_id, 1 AS tier, s.leader_id AS node_id,
           s.parent_leader_id AS parent_node_id, s.leader_id AS tier1_node_id, s.slot, s.slots,
           ((s.slot + 0.5) / s.slots)::DOUBLE AS x, 1.0::DOUBLE AS y
    FROM sib AS s
),
s2 AS (         -- static tier 2: fanned under the parent within its share of the width, zigzag in y
    SELECT p.tree_mode, p.focus_leader_id, 2 AS tier, s.leader_id AS node_id, s.parent_leader_id AS parent_node_id,
           s.parent_leader_id AS tier1_node_id, s.slot, s.slots,
           (p.x + (s.slot - (s.slots - 1) / 2.0) * LEAST(0.85 / p.slots / s.slots, 0.016))::DOUBLE AS x,
           (2 + 0.2 * (s.slot % 2))::DOUBLE AS y,
           p.slots AS parent_slots
    FROM t1 AS p
    JOIN sib AS s ON s.parent_leader_id = p.node_id
    WHERE p.tree_mode = 'Static'
),
s3 AS (         -- static tier 3: dots under their tier-2 parent
    SELECT p.tree_mode, p.focus_leader_id, 3 AS tier, s.leader_id AS node_id, s.parent_leader_id AS parent_node_id,
           p.tier1_node_id, s.slot, s.slots,
           (p.x + (s.slot - (s.slots - 1) / 2.0) * LEAST(0.85 / p.parent_slots / p.slots / s.slots, 0.007))::DOUBLE AS x,
           (3 + 0.1 * (s.slot % 2) + 0.06 * (p.slot % 2))::DOUBLE AS y
    FROM s2 AS p
    JOIN sib AS s ON s.parent_leader_id = p.node_id
),
nodes AS (
    SELECT * FROM dyn UNION ALL SELECT * FROM t0 UNION ALL SELECT * FROM t1
    UNION ALL SELECT tree_mode, focus_leader_id, tier, node_id, parent_node_id, tier1_node_id, slot, slots, x, y FROM s2
    UNION ALL SELECT * FROM s3
)
SELECT tree_mode, focus_leader_id, 'Node' AS mark_type, tier, node_id, parent_node_id, tier1_node_id, slot, slots,
       0 AS point_index, ROUND(x, 6) AS x, ROUND(y, 6) AS y
FROM nodes
UNION ALL
SELECT n.tree_mode, n.focus_leader_id, 'Link', n.tier, n.node_id, n.parent_node_id, n.tier1_node_id, n.slot, n.slots,
       k.i,
       ROUND(pow(1 - k.i / 16.0, 3) * p.x + 3 * pow(1 - k.i / 16.0, 2) * (k.i / 16.0) * p.x
             + 3 * (1 - k.i / 16.0) * pow(k.i / 16.0, 2) * n.x + pow(k.i / 16.0, 3) * n.x, 6),
       ROUND(pow(1 - k.i / 16.0, 3) * p.y + 3 * pow(1 - k.i / 16.0, 2) * (k.i / 16.0) * (p.y + n.y) / 2
             + 3 * (1 - k.i / 16.0) * pow(k.i / 16.0, 2) * (p.y + n.y) / 2 + pow(k.i / 16.0, 3) * n.y, 6)
FROM nodes AS n
JOIN nodes AS p ON p.tree_mode = n.tree_mode AND p.focus_leader_id IS NOT DISTINCT FROM n.focus_leader_id
                AND p.node_id = n.parent_node_id
CROSS JOIN range(0, 17) AS k (i)
WHERE n.tier >= 1
ORDER BY ALL;
