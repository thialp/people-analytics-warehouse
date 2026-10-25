-- Every ID a ticket carries points at something that exists: a Bridgeway worker, a Keystone person
-- (with the Bridgeway worker it belongs to, when both are given), or a load run that failed. A
-- ticket linked in the ID tier resolves to a contractor identity.
SELECT 'unknown Bridgeway worker' AS problem, l.ticket_number, l.subject_id AS id
FROM staging.stg_itsm_ticket_link AS l
WHERE l.subject_type = 'Contingent worker' AND l.subject_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM staging.stg_bw_contingent_worker AS w WHERE w.bw_worker_id = l.subject_id)
UNION ALL
SELECT 'unknown Keystone person', l.ticket_number, l.secondary_id
FROM staging.stg_itsm_ticket_link AS l
WHERE l.secondary_id IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM staging.stg_ks_contingent_worker AS k WHERE k.person_id = l.secondary_id)
UNION ALL
SELECT 'load ticket for a run that did not fail', l.ticket_number, l.subject_id
FROM staging.stg_itsm_ticket_link AS l
WHERE l.subject_type = 'Data load'
  AND NOT EXISTS (SELECT 1 FROM staging.stg_etl_load_run AS r WHERE r.run_id = l.subject_id AND r.status = 'Failed')
UNION ALL
SELECT 'ID link that resolves to no identity', s.ticket_number, s.link_quality
FROM intermediate.int_itsm_ticket_subject AS s
WHERE s.link_quality = 'ID field' AND s.subject_type = 'Contingent worker' AND s.identity_id IS NULL
