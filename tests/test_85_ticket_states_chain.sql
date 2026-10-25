-- Helix: every ticket's history is one chain. It opens as New (no from_state), each change starts
-- from the state the last one ended in, nothing happens after Closed, and the ticket row agrees
-- with its history (opened at the first event, closed at the Closed event, resolved unless
-- reopened since). Every ticket has a category, a link row and at least one event.
WITH e AS (
    SELECT *, LAG(to_state) OVER (PARTITION BY ticket_number ORDER BY event_seq) AS prev_state
    FROM staging.stg_itsm_ticket_event
),
last AS (
    SELECT ticket_number, ARG_MAX(to_state, event_seq) AS state, MIN(event_at) AS first_at,
           MAX(event_at) FILTER (WHERE to_state = 'Closed') AS closed_at,
           ARG_MAX(event_at, event_seq) FILTER (WHERE to_state IN ('Resolved', 'Reopened')) AS last_res_at,
           ARG_MAX(to_state, event_seq) FILTER (WHERE to_state IN ('Resolved', 'Reopened')) AS last_res
    FROM e GROUP BY 1
)
SELECT 'chain broken' AS problem, ticket_number, CAST(event_seq AS VARCHAR) AS detail FROM e
WHERE (event_seq = 1 AND (from_state IS NOT NULL OR to_state <> 'New'))
   OR (event_seq > 1 AND from_state IS DISTINCT FROM prev_state)
   OR (event_seq > 1 AND prev_state = 'Closed')
UNION ALL
SELECT 'ticket row disagrees with its history', t.ticket_number, l.state
FROM staging.stg_itsm_ticket AS t JOIN last AS l USING (ticket_number)
WHERE t.opened_at <> DATE_TRUNC('minute', l.first_at)
   OR t.closed_at IS DISTINCT FROM DATE_TRUNC('minute', l.closed_at)
   OR (l.last_res = 'Resolved') <> (t.resolved_at IS NOT NULL)
UNION ALL
SELECT 'ticket without category, link or events', t.ticket_number, t.category_code
FROM staging.stg_itsm_ticket AS t
LEFT JOIN staging.stg_ticket_category AS c USING (category_code)
LEFT JOIN staging.stg_itsm_ticket_link AS l USING (ticket_number)
LEFT JOIN last USING (ticket_number)
WHERE c.category_code IS NULL OR l.ticket_number IS NULL OR last.ticket_number IS NULL
