-- int_cw_supplier_alias
-- Grain: one row per supplier name as Keystone holds it.
--
-- Keystone has no supplier table: the feed writes Bridgeway's exact supplier name, but people
-- type it their own way when they create a record by hand ("Quorlan Digital", "VANTRELL
-- TECHNICAL STAFFING INC"). Each spelling is mapped to a Bridgeway supplier on a normalized key:
-- the first four letters and digits of the name, lowercased, punctuation and spaces dropped.
-- The key is unique across Bridgeway's suppliers, and every Keystone spelling must map to
-- exactly one of them (test 75): a new spelling that does not is a failure to look at, not a
-- silent non-match.
CREATE OR REPLACE TABLE intermediate.int_cw_supplier_alias AS
WITH keyed AS (
    SELECT supplier_id, supplier_name,
           LEFT(REGEXP_REPLACE(LOWER(supplier_name), '[^a-z0-9]', '', 'g'), 4) AS supplier_key
    FROM staging.stg_bw_supplier
),
spellings AS (
    SELECT DISTINCT supplier_name AS keystone_supplier_name,
           LEFT(REGEXP_REPLACE(LOWER(supplier_name), '[^a-z0-9]', '', 'g'), 4) AS supplier_key
    FROM staging.stg_ks_contingent_worker
    WHERE supplier_name IS NOT NULL
)
SELECT s.keystone_supplier_name, s.supplier_key, k.supplier_id, k.supplier_name AS bridgeway_supplier_name,
       s.keystone_supplier_name = k.supplier_name AS is_exact
FROM spellings AS s
LEFT JOIN keyed AS k USING (supplier_key);
