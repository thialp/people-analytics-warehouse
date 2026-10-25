-- stg_itsm_ticket_link
-- What each ticket is about, as the person who raised it entered it: the Bridgeway worker ID
-- and EMPLID in fields, only a name in the description, or nothing.
-- Source system: Helix Service Desk (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_itsm_ticket_link AS
SELECT
    NULLIF(ticket_number, '')                                AS ticket_number,
    NULLIF(subject_type, '')                                 AS subject_type,
    NULLIF(subject_id, '')                                   AS subject_id,
    NULLIF(secondary_id, '')                                 AS secondary_id,
    NULLIF(link_quality, '')                                 AS link_quality
FROM raw.itsm_ticket_link;
