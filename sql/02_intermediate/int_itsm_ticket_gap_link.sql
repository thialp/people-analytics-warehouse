-- int_itsm_ticket_gap_link
-- Grain: one row per close x gap (int_cw_flag): the ticket working on it, if any.
--
-- A ticket belongs to a gap when it is about the same contractor (int_itsm_ticket_subject), it
-- was opened no more than 7 days before the gap began (not about an earlier episode), and its
-- category fits: the same risk, or a stuck-feed ticket for a gap waiting on the feed. A load gap
-- belongs to the ticket raised for the failed run. When several fit, the latest opened wins.
--   ticket_status   No ticket; Open; Fix pending next run (resolved, the gap still in the data);
--                   Closed, gap still open
CREATE OR REPLACE TABLE intermediate.int_itsm_ticket_gap_link AS
WITH g AS (
    SELECT f.month_end_date, f.gap_id, f.identity_id, f.risk, f.cause_code, f.since_date, r.failed_run_id
    FROM intermediate.int_cw_flag AS f
    JOIN intermediate.int_cw_close_run AS r USING (month_end_date)
),
cand AS (
    SELECT g.month_end_date, g.gap_id, s.ticket_number, st.state, st.is_open, st.opened_at
    FROM g
    JOIN intermediate.int_itsm_ticket_subject AS s
      ON (s.identity_id = g.identity_id
          AND (s.risk = g.risk OR (s.category_code = 'INT-FEED' AND g.cause_code IN ('CW00', 'CW01'))))
      OR (g.cause_code = 'LOAD' AND s.run_id = g.failed_run_id)
    JOIN intermediate.int_itsm_ticket_state AS st
      ON st.ticket_number = s.ticket_number AND st.month_end_date = g.month_end_date
    WHERE st.opened_at >= CAST(g.since_date AS TIMESTAMP) - INTERVAL 7 DAY OR g.cause_code = 'LOAD'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY g.month_end_date, g.gap_id ORDER BY st.opened_at DESC, s.ticket_number DESC) = 1
)
SELECT
    g.month_end_date,
    g.gap_id,
    c.ticket_number,
    c.state                                                                  AS ticket_state,
    CASE WHEN c.ticket_number IS NULL THEN 'No ticket'
         WHEN c.is_open THEN 'Open'
         WHEN c.state = 'Resolved' THEN 'Fix pending next run'
         ELSE 'Closed, gap still open' END                                   AS ticket_status,
    COALESCE(c.is_open OR c.state = 'Resolved', FALSE)                       AS has_ticket
FROM g
LEFT JOIN cand AS c USING (month_end_date, gap_id);
