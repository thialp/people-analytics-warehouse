-- Lineage: every raw table the warehouse loads names exactly one source system (Keystone HR,
-- Bridgeway VMS, the integration log or public reference data), every lineage row points at
-- a table that exists, and every system it names is a known one. A new extract without
-- lineage, or lineage for a table that was dropped, fails the build.
WITH loaded AS (
    SELECT table_name FROM information_schema.tables WHERE table_schema = 'raw'
),
lineage AS (
    SELECT table_name, system_code, COUNT(*) OVER (PARTITION BY table_name) AS rows_for_table
    FROM staging.stg_raw_table_lineage
)
SELECT 'raw table without lineage' AS problem, l.table_name, NULL AS system_code
FROM loaded AS l LEFT JOIN lineage AS g USING (table_name)
WHERE g.table_name IS NULL

UNION ALL
SELECT 'lineage for a table that is not loaded', g.table_name, g.system_code
FROM lineage AS g LEFT JOIN loaded AS l USING (table_name)
WHERE l.table_name IS NULL

UNION ALL
SELECT 'table listed more than once', table_name, system_code
FROM lineage WHERE rows_for_table > 1

UNION ALL
SELECT 'unknown source system', g.table_name, g.system_code
FROM lineage AS g LEFT JOIN staging.stg_source_system AS s USING (system_code)
WHERE s.system_code IS NULL
