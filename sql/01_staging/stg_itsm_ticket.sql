-- stg_itsm_ticket
-- Helix Service Desk tickets, as the last read holds them (GMT). The state at any earlier point
-- is rebuilt from stg_itsm_ticket_event.
-- Source system: Helix Service Desk (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_itsm_ticket AS
SELECT
    NULLIF(ticket_number, '')                                AS ticket_number,
    NULLIF(title, '')                                        AS title,
    NULLIF(short_description, '')                            AS short_description,
    NULLIF(category_code, '')                                AS category_code,
    NULLIF(priority, '')                                     AS priority,
    NULLIF(assignment_group, '')                             AS assignment_group,
    CAST(NULLIF(opened_at, '') AS TIMESTAMP)                 AS opened_at,
    CAST(NULLIF(resolved_at, '') AS TIMESTAMP)               AS resolved_at,
    CAST(NULLIF(closed_at, '') AS TIMESTAMP)                 AS closed_at,
    NULLIF(close_code, '')                                   AS close_code
FROM raw.itsm_ticket;
