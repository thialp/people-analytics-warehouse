-- int_worker_reporting_chain
-- Grain: one row per worker per month-end per manager above them (a "closure" table).
--
-- Walks each worker's reporting line up to the CEO with a recursive CTE, at every
-- month-end. hops = 1 is the direct manager, 2 the skip-level manager, and so on.
-- With this table, "everyone in Maria's organization" is a single equality join
-- (ancestor_worker_id = Maria) instead of a recursive query in the dashboard.
-- The recursion stops at 15 hops; test 26 checks that every chain ends at the CEO.
CREATE OR REPLACE TABLE intermediate.int_worker_reporting_chain AS
WITH RECURSIVE snap AS (
    SELECT month_end_date, worker_id, manager_worker_id
    FROM intermediate.int_worker_month_end_snapshot
),
chain AS (
    SELECT month_end_date, worker_id, manager_worker_id AS ancestor_worker_id, 1 AS hops
    FROM snap
    WHERE manager_worker_id IS NOT NULL
    UNION ALL
    SELECT c.month_end_date, c.worker_id, s.manager_worker_id, c.hops + 1
    FROM chain AS c
    JOIN snap AS s
      ON s.month_end_date = c.month_end_date
     AND s.worker_id      = c.ancestor_worker_id
    WHERE s.manager_worker_id IS NOT NULL
      AND c.hops < 15
)
SELECT month_end_date, worker_id, ancestor_worker_id, hops
FROM chain;
