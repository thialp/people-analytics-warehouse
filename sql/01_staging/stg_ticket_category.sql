-- stg_ticket_category
-- Helix ticket categories: one per reconciliation flag (F01 to F12) and two for Integration (a
-- stuck feed change, a failed warehouse load).
-- Source system: Helix Service Desk (see generator/source_systems.py). Added in release 4.
CREATE OR REPLACE TABLE staging.stg_ticket_category AS
SELECT
    NULLIF(category_code, '')                                AS category_code,
    NULLIF(category_name, '')                                AS category_name,
    NULLIF(subject_type, '')                                 AS subject_type,
    NULLIF(default_group, '')                                AS default_group,
    NULLIF(flag_code, '')                                    AS flag_code,
    NULLIF(risk, '')                                         AS risk,
    NULLIF(priority, '')                                     AS priority,
    NULLIF(title_template, '')                               AS title_template
FROM raw.ref_ticket_category;
