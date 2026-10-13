-- Office moves are the location side of the compensation walk's transfers. For every date
-- pair and every office or country: the people who joined the group (group_side 'To') equal
-- the walk's Transfers In headcount, and the people who left (group_side 'From') equal
-- Transfers Out. Returns every group where the two marts disagree.
WITH moves AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN group_side = 'To'   THEN workers ELSE 0 END) AS moves_in,
           SUM(CASE WHEN group_side = 'From' THEN workers ELSE 0 END) AS moves_out
    FROM marts.mart_office_moves
    WHERE view_name IN ('Office', 'Country')
    GROUP BY ALL
),
walk AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN step = 'Transfers In'  THEN headcount ELSE 0 END)  AS walk_in,
           SUM(CASE WHEN step = 'Transfers Out' THEN -headcount ELSE 0 END) AS walk_out
    FROM marts.mart_compensation_walk
    WHERE view_name IN ('Office', 'Country') AND step IN ('Transfers In', 'Transfers Out')
    GROUP BY ALL
)
SELECT COALESCE(m.from_month_end, w.from_month_end) AS from_month_end,
       COALESCE(m.to_month_end, w.to_month_end)     AS to_month_end,
       COALESCE(m.view_name, w.view_name)           AS view_name,
       COALESCE(m.group_id, w.group_id)             AS group_id,
       COALESCE(m.moves_in, 0) AS moves_in, COALESCE(w.walk_in, 0) AS walk_in,
       COALESCE(m.moves_out, 0) AS moves_out, COALESCE(w.walk_out, 0) AS walk_out
FROM moves AS m
FULL OUTER JOIN walk AS w USING (from_month_end, to_month_end, view_name, group_id)
WHERE COALESCE(m.moves_in, 0)  <> COALESCE(w.walk_in, 0)
   OR COALESCE(m.moves_out, 0) <> COALESCE(w.walk_out, 0)
