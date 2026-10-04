/*
  05_validate.sql
  Control checks after the build. Every "expected" value below comes from the
  DuckDB pipeline in this repo, so SQL Server and the published CSVs must agree.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

PRINT '1. Row counts';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'dw.DimWorker rows'                   AS check_name, (SELECT COUNT(*) FROM dw.DimWorker)               AS actual, 19276  AS expected
    UNION ALL SELECT 'dw.FactJobHistory rows',                            (SELECT COUNT(*) FROM dw.FactJobHistory),                    26832
    UNION ALL SELECT 'dw.FactCompensationHistory rows',                   (SELECT COUNT(*) FROM dw.FactCompensationHistory),           64898
    UNION ALL SELECT 'corrected pay records resolved',                    (SELECT COUNT(*) FROM dw.FactCompensationHistory WHERE WasCorrected = 1), 362
    UNION ALL SELECT 'dw.MonthEndCalendar rows',                          (SELECT COUNT(*) FROM dw.MonthEndCalendar),                  49
    UNION ALL SELECT 'dw.WorkerMonthEndSnapshot rows',                    (SELECT COUNT(*) FROM dw.WorkerMonthEndSnapshot),            592823
) AS c;
GO

PRINT '2. Every snapshot row is fully valued (expected 0)';
SELECT COUNT(*) AS rows_missing_pay_fx_fringe_or_range
FROM dw.WorkerMonthEndSnapshot
WHERE BaseSalaryAnnualLocal IS NULL OR FxRateActual IS NULL OR FxRateConstant IS NULL
   OR FringeRate IS NULL OR RangeMidLocal IS NULL;
GO

PRINT '3. Control totals (executive officers excluded)';
SELECT
    month_end_date,
    SUM(headcount)                                   AS headcount,
    SUM(fte)                                         AS fte,
    SUM(loaded_usd_nominal)                          AS loaded_usd_nominal,
    SUM(loaded_usd_constant)                         AS loaded_usd_constant
FROM rpt.vw_workforce_cost_snapshot
WHERE month_end_date IN ('2022-06-30', '2026-06-30')
GROUP BY month_end_date
ORDER BY month_end_date;
/*
  Expected:
    2022-06-30   11000   10883.10   1126993109.33   1151151241.43
    2026-06-30   13189   12928.00   1566743212.90   1551634565.71
*/
GO
