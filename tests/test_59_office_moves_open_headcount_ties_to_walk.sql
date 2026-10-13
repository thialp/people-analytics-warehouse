-- The share of a group that moved office needs the group's size: open_headcount on every
-- office-moves row equals the compensation walk's Opening headcount for the same date
-- pair, view and group.
SELECT DISTINCT m.from_month_end, m.to_month_end, m.view_name, m.group_id, m.open_headcount, w.headcount
FROM marts.mart_office_moves AS m
LEFT JOIN marts.mart_compensation_walk AS w
  ON w.from_month_end = m.from_month_end AND w.to_month_end = m.to_month_end
 AND w.view_name = m.view_name AND w.group_id = m.group_id AND w.step = 'Opening'
WHERE m.open_headcount IS DISTINCT FROM w.headcount
