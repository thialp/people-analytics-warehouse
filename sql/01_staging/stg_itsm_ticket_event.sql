-- stg_itsm_ticket_event
-- Every state change of every ticket, in order (event_seq), GMT. A reassignment keeps the state
-- and changes the group.
-- Source system: Helix Service Desk (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_itsm_ticket_event AS
SELECT
    NULLIF(ticket_number, '')                                AS ticket_number,
    ROW_NUMBER() OVER (PARTITION BY ticket_number
                       ORDER BY CAST(event_at AS TIMESTAMP)) AS event_seq,
    CAST(NULLIF(event_at, '') AS TIMESTAMP)                  AS event_at,
    NULLIF(from_state, '')                                   AS from_state,
    NULLIF(to_state, '')                                     AS to_state,
    NULLIF(actor_group, '')                                  AS actor_group,
    NULLIF(note, '')                                         AS note
FROM raw.itsm_ticket_event;
