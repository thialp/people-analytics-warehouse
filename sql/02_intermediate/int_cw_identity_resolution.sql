-- int_cw_identity_resolution
-- Grain: one row per identity: a Keystone contingent person matched to a Bridgeway worker, or
-- either one alone. Every Bridgeway worker and every Keystone contingent person appears exactly
-- once (test 75): unmatched records are kept, never dropped.
--
-- Keystone stores the Bridgeway worker ID it received on the feed, and that is the main key.
-- But it can be blank (a load that dropped it), mistyped (a record created by hand), or point at
-- nobody. So the matching runs in tiers, each on what the earlier tiers left:
--
--   Tier 1  High     Keystone's current stored ID is the Bridgeway worker, and the last names agree
--   Tier 2  Medium   same first and last name, same supplier (int_cw_supplier_alias), and the
--                    contract starts within 7 days of each other
--   Tier 3  Low      same first and last name, contract starts within 30 days
--
-- In tiers 2 and 3 a pair is kept only when each is the other's closest candidate, so one
-- Bridgeway worker is never given to two Keystone people. match_evidence says, in a sentence,
-- what the match rests on.
--
-- A Bridgeway worker who never started (withdrawn or rejected before day one) is listed as such:
-- Keystone is not expected to have them.
CREATE OR REPLACE TABLE intermediate.int_cw_identity_resolution AS
WITH ks AS (    -- each Keystone contingent person as Keystone holds them now
    SELECT k.person_id, k.first_name, k.last_name, k.bw_worker_id AS stored_bw_worker_id,
           k.supplier_name, a.supplier_id, k.cw_type,
           MIN(k.contract_start_date) OVER (PARTITION BY k.person_id) AS contract_start_date
    FROM staging.stg_ks_contingent_worker AS k
    LEFT JOIN intermediate.int_cw_supplier_alias AS a ON a.keystone_supplier_name = k.supplier_name
    QUALIFY k.effective_end_date IS NULL
),
bw AS (
    SELECT bw_worker_id, first_name, last_name, supplier_id, cw_type, original_start_date
    FROM staging.stg_bw_contingent_worker
),
tier1 AS (
    SELECT ks.person_id, bw.bw_worker_id, 1 AS match_tier
    FROM ks JOIN bw ON bw.bw_worker_id = ks.stored_bw_worker_id AND bw.last_name = ks.last_name
    QUALIFY ROW_NUMBER() OVER (PARTITION BY bw.bw_worker_id ORDER BY ks.person_id) = 1
),
cand2 AS (
    SELECT ks.person_id, bw.bw_worker_id, ABS(ks.contract_start_date - bw.original_start_date) AS gap
    FROM ks JOIN bw
      ON bw.first_name = ks.first_name AND bw.last_name = ks.last_name AND bw.supplier_id = ks.supplier_id
     AND ABS(ks.contract_start_date - bw.original_start_date) <= 7
    WHERE ks.person_id NOT IN (SELECT person_id FROM tier1)
      AND bw.bw_worker_id NOT IN (SELECT bw_worker_id FROM tier1)
),
tier2 AS (
    SELECT person_id, bw_worker_id, 2 AS match_tier FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY gap, bw_worker_id) AS r_p,
                  ROW_NUMBER() OVER (PARTITION BY bw_worker_id ORDER BY gap, person_id) AS r_b
        FROM cand2) WHERE r_p = 1 AND r_b = 1
),
cand3 AS (
    SELECT ks.person_id, bw.bw_worker_id, ABS(ks.contract_start_date - bw.original_start_date) AS gap
    FROM ks JOIN bw
      ON bw.first_name = ks.first_name AND bw.last_name = ks.last_name
     AND ABS(ks.contract_start_date - bw.original_start_date) <= 30
    WHERE ks.person_id NOT IN (SELECT person_id FROM tier1 UNION ALL SELECT person_id FROM tier2)
      AND bw.bw_worker_id NOT IN (SELECT bw_worker_id FROM tier1 UNION ALL SELECT bw_worker_id FROM tier2)
),
tier3 AS (
    SELECT person_id, bw_worker_id, 3 AS match_tier FROM (
        SELECT *, ROW_NUMBER() OVER (PARTITION BY person_id ORDER BY gap, bw_worker_id) AS r_p,
                  ROW_NUMBER() OVER (PARTITION BY bw_worker_id ORDER BY gap, person_id) AS r_b
        FROM cand3) WHERE r_p = 1 AND r_b = 1
),
matched AS (
    SELECT * FROM tier1 UNION ALL SELECT * FROM tier2 UNION ALL SELECT * FROM tier3
),
identities AS (
    SELECT person_id, bw_worker_id, match_tier FROM matched
    UNION ALL
    SELECT person_id, NULL, NULL FROM ks WHERE person_id NOT IN (SELECT person_id FROM matched)
    UNION ALL
    SELECT NULL, bw_worker_id, NULL FROM bw WHERE bw_worker_id NOT IN (SELECT bw_worker_id FROM matched)
)
SELECT
    'ID' || LPAD(CAST(ROW_NUMBER() OVER (ORDER BY COALESCE(i.bw_worker_id, 'ZZ'), i.person_id) AS VARCHAR), 6, '0') AS identity_id,
    i.person_id,
    i.bw_worker_id,
    CASE WHEN i.person_id IS NOT NULL AND i.bw_worker_id IS NOT NULL THEN 'Matched'
         WHEN i.person_id IS NOT NULL THEN 'Keystone only'
         WHEN bw.original_start_date IS NULL THEN 'Never started'
         ELSE 'Bridgeway only' END                                        AS match_status,
    i.match_tier,
    CASE i.match_tier WHEN 1 THEN 'High' WHEN 2 THEN 'Medium' WHEN 3 THEN 'Low' END AS match_confidence,
    CASE
        WHEN i.match_tier = 1 THEN 'Keystone stores Bridgeway ID ' || i.bw_worker_id || ' and the last names agree'
        WHEN i.match_tier IN (2, 3) THEN
            'Same name (' || ks.first_name || ' ' || ks.last_name || ')'
            || CASE WHEN i.match_tier = 2 THEN ', same supplier' ELSE '' END
            || ', starts ' || CAST(ABS(ks.contract_start_date - bw.original_start_date) AS VARCHAR) || ' days apart; Keystone stores '
            || COALESCE('Bridgeway ID ' || ks.stored_bw_worker_id, 'no Bridgeway ID')
        WHEN i.bw_worker_id IS NULL THEN 'No Bridgeway worker with this name, supplier and start'
            || COALESCE('; Keystone stores ' || ks.stored_bw_worker_id || ', which is nobody''s', '')
        WHEN bw.original_start_date IS NULL THEN 'Withdrawn or rejected before day one: Keystone is not expected to have them'
        ELSE 'No Keystone person with this ID, or this name and start'
    END                                                                   AS match_evidence,
    ks.stored_bw_worker_id,
    COALESCE(bw.first_name, ks.first_name)                                AS first_name,
    COALESCE(bw.last_name, ks.last_name)                                  AS last_name,
    COALESCE(bw.cw_type, ks.cw_type)                                      AS cw_type,
    COALESCE(bw.supplier_id, ks.supplier_id)                              AS supplier_id,
    bw.original_start_date                                                AS bridgeway_start_date,
    ks.contract_start_date                                                AS keystone_start_date
FROM identities AS i
LEFT JOIN ks ON ks.person_id = i.person_id
LEFT JOIN bw ON bw.bw_worker_id = i.bw_worker_id;
