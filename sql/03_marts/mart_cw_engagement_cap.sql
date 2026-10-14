-- mart_cw_engagement_cap
-- Grain: one row per Bridgeway worker who started (an engagement under one Bridgeway ID).
--
-- How long each engagement has run against the 48-month cap on Contractor and Consultant
-- engagements (BPO has none), as Bridgeway holds it on the extract date: the original start, the
-- last day of the latest order, months engaged, how many extensions and renewals it took, the
-- day the cap is reached and the months left before it. A renewal submitted as a new worker
-- (CW07) restarts the clock under the new ID: the cap applies to the person, which is why that
-- discrepancy matters.
CREATE OR REPLACE TABLE marts.mart_cw_engagement_cap AS
WITH extract AS (SELECT MAX(month_end_date) AS extract_date FROM intermediate.int_month_end_calendar),
orders AS (
    SELECT o.bw_worker_id,
           COUNT(*) FILTER (WHERE o.order_type = 'Renewal')                         AS renewals,
           MAX(r.assignment_end_date)                                               AS last_day
    FROM staging.stg_bw_service_order AS o
    JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = o.service_order_id AND r.is_current
    WHERE r.status IN ('Approved', 'Closed')
    GROUP BY 1
),
extensions AS (
    SELECT o.bw_worker_id, COUNT(*) AS extensions,
           COUNT(*) FILTER (WHERE r.revision_reason = 'Early end') AS early_ends
    FROM staging.stg_bw_service_order AS o
    JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = o.service_order_id
    WHERE r.revision_reason IN ('Extension', 'Early end')
    GROUP BY 1
)
SELECT
    w.bw_worker_id,
    i.identity_id,
    i.person_id,
    w.first_name || ' ' || w.last_name                                               AS worker_name,
    w.cw_type,
    s.supplier_name,
    w.original_start_date,
    o.last_day,
    o.last_day >= e.extract_date                                                      AS is_working_at_extract,
    CASE WHEN c.worker_id IS NOT NULL THEN 'Converted to employee'
         WHEN o.last_day >= e.extract_date THEN 'Working'
         WHEN COALESCE(x.early_ends, 0) > 0 THEN 'Ended early'
         ELSE 'Completed' END                                                         AS engagement_status,
    DATEDIFF('month', w.original_start_date, LEAST(o.last_day, e.extract_date) + 1)   AS months_engaged,
    COALESCE(x.extensions, 0) - COALESCE(x.early_ends, 0)                             AS extensions,
    o.renewals,
    CASE WHEN w.cw_type <> 'BPO' THEN CAST(w.original_start_date + INTERVAL 48 MONTH AS DATE) - 1 END AS cap_date,
    CASE WHEN w.cw_type <> 'BPO' AND o.last_day >= e.extract_date
         THEN DATEDIFF('month', e.extract_date, CAST(w.original_start_date + INTERVAL 48 MONTH AS DATE) - 1) END AS months_left_at_extract,
    w.cw_type <> 'BPO' AND o.last_day >= CAST(w.original_start_date + INTERVAL 48 MONTH AS DATE)          AS is_over_cap,
    CASE WHEN w.cw_type = 'BPO' THEN 'No cap'
         WHEN o.last_day >= CAST(w.original_start_date + INTERVAL 48 MONTH AS DATE) THEN 'Over the cap'
         WHEN o.last_day < e.extract_date THEN 'Ended within the cap'
         WHEN DATEDIFF('month', e.extract_date, CAST(w.original_start_date + INTERVAL 48 MONTH AS DATE) - 1) < 6 THEN 'Under 6 months left'
         WHEN DATEDIFF('month', e.extract_date, CAST(w.original_start_date + INTERVAL 48 MONTH AS DATE) - 1) < 12 THEN '6 to 12 months left'
         ELSE 'More than 12 months left' END                                          AS cap_band
FROM staging.stg_bw_contingent_worker AS w
CROSS JOIN extract AS e
JOIN orders AS o ON o.bw_worker_id = w.bw_worker_id
LEFT JOIN extensions AS x ON x.bw_worker_id = w.bw_worker_id
LEFT JOIN staging.stg_bw_supplier AS s ON s.supplier_id = w.supplier_id
LEFT JOIN intermediate.int_cw_identity_resolution AS i ON i.bw_worker_id = w.bw_worker_id
LEFT JOIN intermediate.int_cw_conversion AS c ON c.bw_worker_id = w.bw_worker_id
WHERE w.original_start_date IS NOT NULL
ORDER BY w.bw_worker_id;
