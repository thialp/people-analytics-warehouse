-- int_itsm_ticket_subject
-- Grain: one row per ticket: what it is about, resolved to a contractor identity in tiers, like
-- identity resolution itself.
--
--   ID      the Bridgeway worker ID in the subject field, or the EMPLID in the secondary field
--   Name    no ID, but the description names the contractor ("Contractor First Last: ...") and
--           exactly one identity with that name was working, in either system, at a month-end in
--           the two months before the ticket was opened (names repeat; the date window tells
--           people apart)
--   None    nothing to link on, or the name is shared by more than one identity (Ambiguous)
-- A load ticket is about a load run, not a contractor.
CREATE OR REPLACE TABLE intermediate.int_itsm_ticket_subject AS
WITH t AS (
    SELECT t.ticket_number, t.title, t.short_description, t.category_code, t.priority, t.opened_at,
           c.flag_code, c.risk, c.category_name, l.subject_type, l.subject_id, l.secondary_id, l.link_quality,
           CASE WHEN l.link_quality = 'Name in text' AND t.short_description LIKE 'Contractor %:%'
                THEN SUBSTRING(t.short_description, 12, STRPOS(t.short_description, ':') - 12) END AS named
    FROM staging.stg_itsm_ticket AS t
    JOIN staging.stg_ticket_category AS c USING (category_code)
    LEFT JOIN staging.stg_itsm_ticket_link AS l USING (ticket_number)
),
names AS (    -- the identities with the name that either system showed working around the opening day
    SELECT t.ticket_number, MIN(i.identity_id) AS identity_id, COUNT(*) AS n
    FROM t
    JOIN intermediate.int_cw_identity_resolution AS i ON i.first_name || ' ' || i.last_name = t.named
    WHERE EXISTS (SELECT 1 FROM intermediate.int_cw_reconciliation_snapshot AS s
                  WHERE s.identity_id = i.identity_id
                    AND s.month_end_date >= CAST(t.opened_at AS DATE) - 62
                    AND s.month_end_date <= LAST_DAY(CAST(t.opened_at AS DATE)))
    GROUP BY t.ticket_number
)
SELECT
    t.ticket_number, t.title, t.short_description, t.category_code, t.category_name, t.flag_code, t.risk,
    t.priority, t.opened_at, t.subject_type, t.link_quality,
    CASE WHEN t.subject_type = 'Data load' THEN t.subject_id END                         AS run_id,
    COALESCE(ib.identity_id, ip.identity_id, CASE WHEN nm.n = 1 THEN nm.identity_id END) AS identity_id,
    CASE WHEN t.subject_type = 'Data load' THEN 'Load run'
         WHEN COALESCE(ib.identity_id, ip.identity_id) IS NOT NULL THEN 'ID'
         WHEN nm.n = 1 THEN 'Name'
         WHEN nm.n > 1 THEN 'Ambiguous'
         ELSE 'None' END                                                                 AS link_tier
FROM t
LEFT JOIN intermediate.int_cw_identity_resolution AS ib
       ON t.subject_type = 'Contingent worker' AND ib.bw_worker_id = t.subject_id
LEFT JOIN intermediate.int_cw_identity_resolution AS ip
       ON t.subject_type = 'Contingent worker' AND t.subject_id IS NULL AND ip.person_id = t.secondary_id
LEFT JOIN names AS nm ON nm.ticket_number = t.ticket_number;
