-- int_itsm_ticket_state
-- Grain: one row per month-end close x ticket that exists at the close's Helix read.
--
-- A ticket's state at any moment is rebuilt from its events: the state of the last event at or
-- before the read (int_cw_close_run.hlx_read_at, 00:00 GMT on the 1st, or the read before when
-- that one failed). The group working it is the group of its last event that was not Helix's own
-- automatic close, so a misrouted ticket shows under the wrong place until it is reassigned.
-- Tickets closed more than 120 days before the read are left out.
--   is_open   New, In progress, Pending or Reopened
--   age       from opening to the read, in whole days, and the card's bands: 0 to 5 days,
--             6 to 30 days, over 30 days
CREATE OR REPLACE TABLE intermediate.int_itsm_ticket_state AS
WITH reads AS (
    SELECT month_end_date, hlx_read_at FROM intermediate.int_cw_close_run
),
upto AS (
    SELECT r.month_end_date, r.hlx_read_at, e.*
    FROM reads AS r
    JOIN staging.stg_itsm_ticket_event AS e ON e.event_at <= r.hlx_read_at
),
state AS (
    SELECT month_end_date, hlx_read_at, ticket_number,
           MIN(event_at)                                                  AS opened_at,
           ARG_MAX(to_state, event_seq)                                   AS state,
           ARG_MAX(actor_group, event_seq) FILTER (WHERE actor_group <> 'Helix') AS current_group,
           MAX(event_at) FILTER (WHERE to_state = 'Resolved')             AS last_resolved_at,
           MAX(event_at) FILTER (WHERE to_state = 'Closed')               AS closed_at,
           COUNT(*) FILTER (WHERE to_state = 'Reopened')                  AS times_reopened,
           COUNT(*) FILTER (WHERE note LIKE 'Reassigned%')                AS times_reassigned
    FROM upto
    GROUP BY 1, 2, 3
)
SELECT
    s.month_end_date,
    s.ticket_number,
    s.state,
    s.state IN ('New', 'In progress', 'Pending', 'Reopened')             AS is_open,
    s.current_group,
    CASE s.current_group WHEN 'Vendor Management' THEN 'Bridgeway' WHEN 'HR Operations' THEN 'Keystone'
                         ELSE 'System feed' END                          AS place,
    s.opened_at,
    s.last_resolved_at,
    s.closed_at,
    s.times_reopened,
    s.times_reassigned,
    DATE_DIFF('day', s.opened_at, s.hlx_read_at)                         AS age_days,
    CASE WHEN DATE_DIFF('day', s.opened_at, s.hlx_read_at) <= 5 THEN '0 to 5 days'
         WHEN DATE_DIFF('day', s.opened_at, s.hlx_read_at) <= 30 THEN '6 to 30 days'
         ELSE 'Over 30 days' END                                         AS age_band,
    s.hlx_read_at
FROM state AS s
WHERE s.state <> 'Closed' OR s.closed_at > s.hlx_read_at - INTERVAL 120 DAY;
