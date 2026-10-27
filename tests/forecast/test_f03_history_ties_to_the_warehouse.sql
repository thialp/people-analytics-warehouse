-- The forecast's history is the warehouse's: fills per fiscal year equal Dashboard #3's backfills plus
-- net-new fills (mart_wfp_summary, company, budget), and the survival inputs count every requisition
-- with a search that was filled within 210 days of approval, once.
WITH q AS (SELECT quarter_offset, fiscal_year FROM staging.stg_report_quarter),
hist AS (
    SELECT q.fiscal_year, SUM(h.filled) AS filled
    FROM forecast.mart_pid_fill_quarter AS h JOIN q USING (quarter_offset)
    WHERE h.quarter_offset <= 0 GROUP BY q.fiscal_year
),
wfp AS (
    SELECT fiscal_year, actual_backfills + actual_net_new AS filled
    FROM marts.mart_wfp_summary
    WHERE view_name = 'Company' AND pair_code = 'FY' AND version_type = 'Budget'
),
cal AS (SELECT * FROM staging.stg_report_calendar),
reqs AS (
    SELECT COUNT(*) AS n
    FROM staging.stg_requisition AS r, cal AS c
    WHERE r.department_id <> 'D-901' AND r.status = 'Filled' AND r.filled_date > r.approved_date
      AND r.approved_date >= c.history_start_date AND r.filled_date <= c.report_as_of_date
      AND DATE_DIFF('day', r.approved_date, r.filled_date) < 210
)
SELECT 'fiscal-year fills differ from Dashboard #3' AS problem, CAST(h.fiscal_year AS VARCHAR) AS detail
FROM hist AS h JOIN wfp AS w USING (fiscal_year)
WHERE h.filled <> w.filled
UNION ALL
SELECT 'survival fills differ from the requisitions', CAST((SELECT SUM(filled) FROM forecast.mart_fill_survival) AS VARCHAR)
FROM reqs WHERE (SELECT SUM(filled) FROM forecast.mart_fill_survival) <> reqs.n
UNION ALL
SELECT 'more at risk in a later period than an earlier one', s.department_id
FROM forecast.mart_fill_survival AS s
JOIN forecast.mart_fill_survival AS p
  ON p.cohort_quarter_offset = s.cohort_quarter_offset AND p.department_id = s.department_id
 AND p.location_id = s.location_id AND p.level_band = s.level_band AND p.req_type = s.req_type
 AND p.period = s.period - 1
WHERE s.at_risk > p.at_risk - p.filled
