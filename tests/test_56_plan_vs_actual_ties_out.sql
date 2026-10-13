-- Plan vs actual ties to the rest of the warehouse: for every plan version and quarter,
-- the actual ending headcount across its cost centers equals the company headcount at
-- that quarter-end, and its actual hires and internal moves equal the seat fills in
-- that quarter.
WITH plan AS (
    SELECT plan_version, quarter_end_date, fiscal_year, fiscal_quarter,
           SUM(actual_ending_headcount) AS headcount,
           SUM(actual_net_new + actual_backfills) AS fills
    FROM marts.mart_plan_vs_actual
    GROUP BY ALL
),
people AS (
    SELECT month_end_date, COUNT(*) AS headcount FROM intermediate.int_worker_month_end_snapshot GROUP BY ALL
),
fills AS (
    SELECT c.fiscal_year, c.fiscal_quarter, COUNT(*) AS fills
    FROM marts.mart_position_fill AS f
    JOIN intermediate.int_month_end_calendar AS c ON c.month_end_date = LAST_DAY(f.fill_date)
    GROUP BY ALL
)
SELECT p.plan_version, p.quarter_end_date, p.headcount, pe.headcount AS company_headcount,
       p.fills, f.fills AS company_fills
FROM plan AS p
JOIN people AS pe ON pe.month_end_date = p.quarter_end_date
LEFT JOIN fills AS f ON f.fiscal_year = p.fiscal_year AND f.fiscal_quarter = p.fiscal_quarter
WHERE p.headcount <> pe.headcount
   OR p.fills <> COALESCE(f.fills, 0)
