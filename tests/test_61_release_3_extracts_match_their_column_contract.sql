-- Column contract: every raw table added in release 3 (Bridgeway VMS, the Keystone contingent
-- worker profile, the integration log and the lineage registry itself) carries exactly the
-- columns documented in generator/source_systems.py, in the same order. Catches an extract
-- that gained, lost, renamed or reordered a column before any model reads it.
WITH documented AS (
    SELECT table_name, column_order, column_name FROM staging.stg_raw_column
),
loaded AS (
    SELECT table_name, ordinal_position AS column_order, column_name
    FROM information_schema.columns
    WHERE table_schema = 'raw'
      AND table_name IN (SELECT table_name FROM staging.stg_raw_table_lineage WHERE added_in_release = 3)
)
SELECT COALESCE(d.table_name, l.table_name) AS table_name,
       COALESCE(d.column_order, l.column_order) AS column_order,
       d.column_name AS documented, l.column_name AS loaded
FROM documented AS d
FULL OUTER JOIN loaded AS l USING (table_name, column_order)
WHERE d.column_name IS DISTINCT FROM l.column_name
