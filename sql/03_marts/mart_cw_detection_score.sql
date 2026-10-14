-- mart_cw_detection_score
-- Grain: one row per month-end x discrepancy type.
--
-- How well the warehouse's rules (int_cw_discrepancy) find what was seeded, scored against the
-- answer key (gen_cw_discrepancy_truth). On each month-end, a seeded discrepancy open that day is
-- INJECTED; it is DETECTED when the rules flag the same type on the same worker (the Bridgeway
-- worker, or the Keystone person for a Keystone-only worker) that month-end; a flag with no seeded
-- discrepancy behind it is a FALSE FLAG. Recall = detected / injected; precision = detected /
-- (detected + false flags). The rules never read the answer key: this is the only place it is
-- used, and it is what case study 6's methodology page shows. Test 73 holds recall at 100%.
CREATE OR REPLACE TABLE marts.mart_cw_detection_score AS
WITH me AS (
    SELECT month_end_date FROM intermediate.int_month_end_calendar
),
truth AS (
    SELECT DISTINCT me.month_end_date, t.discrepancy_code, COALESCE(t.bw_worker_id, t.person_id) AS who
    FROM me
    JOIN staging.stg_gen_cw_discrepancy_truth AS t
      ON t.start_date <= me.month_end_date AND t.end_date_filled >= me.month_end_date
),
flags AS (
    SELECT DISTINCT month_end_date, discrepancy_code,
           CASE WHEN discrepancy_code = 'CW09' THEN person_id ELSE bw_worker_id END AS who
    FROM intermediate.int_cw_discrepancy
),
scored AS (
    SELECT COALESCE(t.month_end_date, f.month_end_date) AS month_end_date,
           COALESCE(t.discrepancy_code, f.discrepancy_code) AS discrepancy_code,
           t.who IS NOT NULL AS injected, t.who IS NOT NULL AND f.who IS NOT NULL AS detected,
           t.who IS NULL AS false_flag
    FROM truth AS t
    FULL OUTER JOIN flags AS f USING (month_end_date, discrepancy_code, who)
)
SELECT
    s.month_end_date,
    cal.fiscal_year,
    s.discrepancy_code,
    ty.discrepancy_name,
    ty.severity,
    COUNT(*) FILTER (WHERE s.injected)                                   AS injected,
    COUNT(*) FILTER (WHERE s.detected)                                   AS detected,
    COUNT(*) FILTER (WHERE s.injected AND NOT s.detected)                AS missed,
    COUNT(*) FILTER (WHERE s.false_flag)                                 AS false_flags,
    ROUND(COUNT(*) FILTER (WHERE s.detected) / NULLIF(COUNT(*) FILTER (WHERE s.injected), 0), 4)  AS recall,
    ROUND(COUNT(*) FILTER (WHERE s.detected)
          / NULLIF(COUNT(*) FILTER (WHERE s.detected OR s.false_flag), 0), 4)                       AS precision
FROM scored AS s
JOIN intermediate.int_month_end_calendar AS cal USING (month_end_date)
LEFT JOIN staging.stg_cw_discrepancy_type AS ty ON ty.discrepancy_code = s.discrepancy_code
GROUP BY ALL
ORDER BY 1, 3;
