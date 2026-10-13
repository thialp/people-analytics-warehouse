-- int_seat_vacancy_chain
-- Grain: one row per seat fill, placing it in its vacancy chain.
--
-- When someone moves internally into a seat, the seat they leave needs filling too:
-- one vacancy can set off a chain of moves. A fill's parent is the internal move that
-- emptied its seat (the prior incumbent moved out the day before and into another
-- seat). A fill with no parent starts a chain: its trigger is why that seat was empty
-- (a voluntary or involuntary exit, or a net-new seat). chain_depth counts the hops
-- from the first fill; chain_length is the longest chain from the same trigger.
CREATE OR REPLACE TABLE intermediate.int_seat_vacancy_chain AS
WITH RECURSIVE linked AS (
    SELECT
        f.fill_id,
        f.fill_type,
        f.seat_type,
        f.prior_vacate_reason,
        p.fill_id AS parent_fill_id
    FROM intermediate.int_seat_fill AS f
    LEFT JOIN intermediate.int_seat_fill AS p
      ON f.prior_vacate_reason = 'Internal Move Out'
     AND p.worker_id = f.prior_worker_id
     AND p.fill_date = f.prior_end_date + INTERVAL 1 DAY
),
chain AS (
    SELECT fill_id, fill_id AS chain_id, 1 AS chain_depth,
           CASE WHEN seat_type = 'Net-new' THEN 'Net-new seat'
                WHEN prior_vacate_reason = 'Internal Move Out' THEN 'Internal move before history'
                ELSE prior_vacate_reason || ' exit' END AS chain_trigger
    FROM linked
    WHERE parent_fill_id IS NULL
    UNION ALL
    SELECT l.fill_id, c.chain_id, c.chain_depth + 1, c.chain_trigger
    FROM linked AS l
    JOIN chain AS c ON l.parent_fill_id = c.fill_id
)
SELECT
    c.fill_id,
    l.parent_fill_id,
    c.chain_id,
    c.chain_depth,
    MAX(c.chain_depth) OVER (PARTITION BY c.chain_id) AS chain_length,
    c.chain_trigger
FROM chain AS c
JOIN linked AS l USING (fill_id);
