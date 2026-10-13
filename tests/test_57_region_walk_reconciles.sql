-- The region walk closes in every row (opening + hires - exits + transfers in - out +
-- region moves in - out = closing), and summed over regions it equals the compensation
-- walk's headcount lines for every date pair, view and group. Inside a group, region
-- moves in and out net to zero. The regions themselves are pinned down too: company
-- opening and closing by region equal the month-end snapshot by office region, and
-- every view (each splits the whole company) has the same region totals as the company.
WITH by_region AS (
    SELECT from_month_end, to_month_end, view_name, region,
           SUM(opening_headcount) AS opening, SUM(hires) AS hires, SUM(exits) AS exits,
           SUM(transfers_in - transfers_out + region_moves_in - region_moves_out) AS net_moves,
           SUM(closing_headcount) AS closing
    FROM marts.mart_region_walk
    GROUP BY ALL
),
snap AS (
    SELECT s.month_end_date, l.region, COUNT(*) AS headcount
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN staging.stg_location AS l USING (location_id)
    WHERE NOT s.is_executive_officer
    GROUP BY ALL
),
r AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(opening_headcount) AS opening, SUM(hires) AS hires, SUM(exits) AS exits,
           SUM(transfers_in) AS transfers_in, SUM(transfers_out) AS transfers_out,
           SUM(region_moves_in) AS moves_in, SUM(region_moves_out) AS moves_out,
           SUM(closing_headcount) AS closing
    FROM marts.mart_region_walk
    GROUP BY ALL
),
w AS (
    SELECT from_month_end, to_month_end, view_name, group_id,
           SUM(CASE WHEN step = 'Opening'       THEN headcount ELSE 0 END)  AS opening,
           SUM(CASE WHEN step = 'Hires'         THEN headcount ELSE 0 END)  AS hires,
           SUM(CASE WHEN step = 'Exits'         THEN -headcount ELSE 0 END) AS exits,
           SUM(CASE WHEN step = 'Transfers In'  THEN headcount ELSE 0 END)  AS transfers_in,
           SUM(CASE WHEN step = 'Transfers Out' THEN -headcount ELSE 0 END) AS transfers_out,
           SUM(CASE WHEN step = 'Closing'       THEN headcount ELSE 0 END)  AS closing
    FROM marts.mart_compensation_walk
    GROUP BY ALL
)
SELECT 'row does not close' AS problem, from_month_end, to_month_end, view_name, group_id, region
FROM marts.mart_region_walk
WHERE opening_headcount + hires - exits + transfers_in - transfers_out + region_moves_in - region_moves_out
      <> closing_headcount
UNION ALL
SELECT 'group differs from the walk', COALESCE(r.from_month_end, w.from_month_end), COALESCE(r.to_month_end, w.to_month_end),
       COALESCE(r.view_name, w.view_name), COALESCE(r.group_id, w.group_id), NULL
FROM r
FULL OUTER JOIN w USING (from_month_end, to_month_end, view_name, group_id)
WHERE r.opening IS DISTINCT FROM w.opening OR r.hires IS DISTINCT FROM w.hires OR r.exits IS DISTINCT FROM w.exits
   OR r.transfers_in IS DISTINCT FROM w.transfers_in OR r.transfers_out IS DISTINCT FROM w.transfers_out
   OR r.closing IS DISTINCT FROM w.closing OR r.moves_in <> r.moves_out
UNION ALL
SELECT 'company region differs from the snapshot', c.from_month_end, c.to_month_end, c.view_name, NULL, c.region
FROM by_region AS c
LEFT JOIN snap AS so ON so.month_end_date = c.from_month_end AND so.region = c.region
LEFT JOIN snap AS sc ON sc.month_end_date = c.to_month_end   AND sc.region = c.region
WHERE c.view_name = 'Company'
  AND (c.opening <> COALESCE(so.headcount, 0) OR c.closing <> COALESCE(sc.headcount, 0))
UNION ALL
SELECT 'view region totals differ from the company', v.from_month_end, v.to_month_end, v.view_name, NULL, v.region
FROM by_region AS v
LEFT JOIN by_region AS c
  ON c.from_month_end = v.from_month_end AND c.to_month_end = v.to_month_end
 AND c.region = v.region AND c.view_name = 'Company'
WHERE v.view_name <> 'Company'
  AND (v.opening IS DISTINCT FROM c.opening OR v.hires IS DISTINCT FROM c.hires OR v.exits IS DISTINCT FROM c.exits
       OR v.net_moves IS DISTINCT FROM c.net_moves OR v.closing IS DISTINCT FROM c.closing)
