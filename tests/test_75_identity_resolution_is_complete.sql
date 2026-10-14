-- Identity resolution keeps everyone, once: every Bridgeway worker and every Keystone contingent
-- person appears in exactly one identity (matched or not), no identity is empty, a match has a
-- tier and a reason; every Keystone supplier spelling maps to exactly one Bridgeway supplier;
-- and a High match always rests on the stored ID.
WITH r AS (SELECT * FROM intermediate.int_cw_identity_resolution)
SELECT bw_worker_id AS id, 'Bridgeway worker missing or in two identities' AS problem
FROM (SELECT b.bw_worker_id, COUNT(r.identity_id) AS n
      FROM staging.stg_bw_contingent_worker AS b LEFT JOIN r USING (bw_worker_id) GROUP BY 1)
WHERE n <> 1
UNION ALL
SELECT person_id, 'Keystone person missing or in two identities'
FROM (SELECT k.person_id, COUNT(r.identity_id) AS n
      FROM (SELECT DISTINCT person_id FROM staging.stg_ks_contingent_worker) AS k LEFT JOIN r USING (person_id) GROUP BY 1)
WHERE n <> 1
UNION ALL
SELECT identity_id, 'empty identity' FROM r WHERE person_id IS NULL AND bw_worker_id IS NULL
UNION ALL
SELECT identity_id, 'match without tier or evidence, or tier without match'
FROM r WHERE (match_status = 'Matched') <> (match_tier IS NOT NULL) OR match_evidence IS NULL
UNION ALL
SELECT identity_id, 'High match not on the stored ID' FROM r WHERE match_tier = 1 AND stored_bw_worker_id <> bw_worker_id
UNION ALL
SELECT keystone_supplier_name, 'Keystone supplier spelling maps to no Bridgeway supplier'
FROM intermediate.int_cw_supplier_alias WHERE supplier_id IS NULL
UNION ALL
SELECT keystone_supplier_name, 'Keystone supplier spelling maps to two suppliers'
FROM intermediate.int_cw_supplier_alias GROUP BY keystone_supplier_name HAVING COUNT(*) > 1
