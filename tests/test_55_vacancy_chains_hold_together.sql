-- Vacancy chains hold together: a fill starts a chain exactly when no internal move
-- emptied its seat; otherwise it sits one step below the move that did, in the same
-- chain. Every seat left behind by an internal move is accounted for at the last
-- month-end: refilled later, or still Open, Frozen or Eliminated.
WITH last_me AS (SELECT MAX(month_end_date) AS d FROM intermediate.int_month_end_calendar),
links AS (
    SELECT c.fill_id, c.parent_fill_id, c.chain_id, c.chain_depth, f.prior_vacate_reason,
           p.chain_id AS parent_chain_id, p.chain_depth AS parent_depth
    FROM marts.mart_position_fill AS f
    JOIN intermediate.int_seat_vacancy_chain AS c USING (fill_id)
    LEFT JOIN intermediate.int_seat_vacancy_chain AS p ON p.fill_id = c.parent_fill_id
),
left_behind AS (   -- the seat each internal mover left, and what became of it
    SELECT f.fill_id, a.position_id, a.end_date,
           EXISTS (SELECT 1 FROM staging.stg_position_assignment AS b
                   WHERE b.position_id = a.position_id AND b.start_date > a.end_date)  AS refilled,
           (SELECT h.status FROM intermediate.int_position_history AS h, last_me
            WHERE h.position_id = a.position_id
              AND last_me.d BETWEEN h.effective_start_date AND h.effective_end_date_filled) AS status_now
    FROM marts.mart_position_fill AS f
    JOIN staging.stg_position_assignment AS a
      ON a.worker_id = f.worker_id AND a.end_date = f.fill_date - INTERVAL 1 DAY
    WHERE f.fill_type = 'Internal Move'
)
SELECT fill_id, 'chain link' AS problem
FROM links
WHERE (parent_fill_id IS NULL) <> (chain_depth = 1)
   OR (parent_fill_id IS NOT NULL AND (chain_id <> parent_chain_id OR chain_depth <> parent_depth + 1))
   OR (parent_fill_id IS NULL AND prior_vacate_reason = 'Internal Move Out')
UNION ALL
SELECT fill_id, 'seat left behind not accounted for'
FROM left_behind
WHERE NOT refilled AND status_now NOT IN ('Open', 'Frozen', 'Eliminated')
