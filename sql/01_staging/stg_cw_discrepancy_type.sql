-- stg_cw_discrepancy_type
-- The catalogue of contingent workforce discrepancies (CW00 to CW12), named after what
-- happened in the systems, with what a Keystone-only manager sees, who can fix it and how
-- serious it is. The warehouse flags; the owning team fixes the source.
-- Source: generator/keystone_feed.py (warehouse metadata). Added in release 3.
CREATE OR REPLACE TABLE staging.stg_cw_discrepancy_type AS
SELECT
    discrepancy_code,
    discrepancy_name,
    what_happened,
    what_a_manager_sees,
    who_can_fix_it,
    severity
FROM raw.ref_cw_discrepancy_type;
