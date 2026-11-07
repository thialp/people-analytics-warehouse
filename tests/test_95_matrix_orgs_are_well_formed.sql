-- Release 7 matrix orgs: a matrix's records never overlap; an active matrix whose leader seat is open
-- has an answer-key row for the vacancy (and the other way round); and on every month-end each
-- country is covered by exactly one active country matrix.
WITH r AS (
    SELECT *, LEAD(effective_start_date) OVER (PARTITION BY matrix_org_id ORDER BY effective_start_date) AS next_start
    FROM staging.stg_matrix_org
),
vac AS (SELECT matrix_org_id, effective_start_date FROM staging.stg_matrix_org
        WHERE status = 'Active' AND manager_worker_id IS NULL),
key AS (SELECT matrix_org_id, start_date FROM staging.stg_gen_org_drift_truth
        WHERE signal_code = 'M3' AND person_id IS NULL),
m AS (SELECT DISTINCT month_end_date FROM intermediate.int_person_month_end),
cover AS (
    SELECT m.month_end_date, UNNEST(string_split(o.covers_country_codes, ';')) AS country_code
    FROM m JOIN staging.stg_matrix_org AS o
      ON m.month_end_date BETWEEN o.effective_start_date AND o.effective_end_date_filled
    WHERE o.matrix_type = 'Country' AND o.status = 'Active'
)
SELECT 'records overlap' AS problem, matrix_org_id, CAST(effective_start_date AS VARCHAR) AS detail
FROM r WHERE next_start IS NOT NULL AND next_start <= effective_end_date_filled
UNION ALL
SELECT 'open seat without a key row', v.matrix_org_id, CAST(v.effective_start_date AS VARCHAR)
FROM vac AS v ANTI JOIN key AS k ON k.matrix_org_id = v.matrix_org_id AND k.start_date = v.effective_start_date
UNION ALL
SELECT 'key row without an open seat', k.matrix_org_id, CAST(k.start_date AS VARCHAR)
FROM key AS k ANTI JOIN vac AS v ON k.matrix_org_id = v.matrix_org_id AND k.start_date = v.effective_start_date
UNION ALL
SELECT 'country not covered exactly once', c.country_code, CAST(m.month_end_date AS VARCHAR)
FROM m CROSS JOIN staging.stg_country AS c
LEFT JOIN cover AS v ON v.month_end_date = m.month_end_date AND v.country_code = c.country_code
GROUP BY m.month_end_date, c.country_code
HAVING COUNT(v.country_code) <> 1
