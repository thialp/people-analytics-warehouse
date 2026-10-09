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
              SELECT 'dw.DimWorker rows'                   AS check_name, (SELECT COUNT(*) FROM dw.DimWorker)               AS actual, 43569   AS expected
    UNION ALL SELECT 'dw.FactJobHistory rows',                            (SELECT COUNT(*) FROM dw.FactJobHistory),                    89240
    UNION ALL SELECT 'dw.FactCompensationHistory rows',                   (SELECT COUNT(*) FROM dw.FactCompensationHistory),           152939
    UNION ALL SELECT 'corrected pay records resolved',                    (SELECT COUNT(*) FROM dw.FactCompensationHistory WHERE WasCorrected = 1), 891
    UNION ALL SELECT 'dw.FactPerformanceReview rows',                     (SELECT COUNT(*) FROM dw.FactPerformanceReview),             131639
    UNION ALL SELECT 'dw.FactBonusPayout rows',                           (SELECT COUNT(*) FROM dw.FactBonusPayout),                   131639
    UNION ALL SELECT 'dw.MonthEndCalendar rows',                          (SELECT COUNT(*) FROM dw.MonthEndCalendar),                  49
    UNION ALL SELECT 'dw.WorkerMonthEndSnapshot rows',                    (SELECT COUNT(*) FROM dw.WorkerMonthEndSnapshot),            1347949
    UNION ALL SELECT 'dw.WorkerPayLedger rows',                           (SELECT COUNT(*) FROM dw.WorkerPayLedger),                   1347949
    UNION ALL SELECT 'dw.WorkerReportingChain rows',                      (SELECT COUNT(*) FROM dw.WorkerReportingChain),              918806
    UNION ALL SELECT 'org leaders at 2026-06-30',                         (SELECT COUNT(*) FROM rpt.vw_org_leader_summary WHERE month_end_date = '2026-06-30'), 44
) AS c;
GO

PRINT '2. Every snapshot row is fully valued (expected 0)';
SELECT COUNT(*) AS rows_missing_pay_fx_fringe_or_range
FROM dw.WorkerMonthEndSnapshot
WHERE BaseSalaryAnnualLocal IS NULL OR FxRateActual IS NULL OR FxRateConstant IS NULL
   OR FxRatePosting IS NULL OR FringeRate IS NULL OR RangeMidLocal IS NULL;
GO

PRINT '3. Everyone except the CEO reports to an employed manager (expected 0)';
SELECT COUNT(*) AS workers_without_a_valid_manager
FROM dw.WorkerMonthEndSnapshot AS s
LEFT JOIN dw.WorkerMonthEndSnapshot AS m
       ON m.MonthEndDate = s.MonthEndDate AND m.WorkerID = s.ManagerWorkerID
WHERE ISNULL(s.LeadsOrgUnitID, '') <> 'ORG-000' AND m.WorkerID IS NULL;
GO

PRINT '4. Control totals (executive officers excluded)';
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
    2022-06-30   25005   24733.20   2577787184.81   2613645368.50
    2026-06-30   30015   29395.70   3195503264.83   3195503264.83
  (Nominal equals constant on 2026-06-30: the constant rate set is that day's rates.)
*/
GO

PRINT '5. The pay ledger explains every change in every worker''s cost (expected 0)';
/* Between a worker's first month-end and any later one, the ledger's drivers must
   add up to the change in value on all four measures. */
WITH v AS (
    SELECT
        s.WorkerID, s.MonthEndDate,
        ROW_NUMBER() OVER (PARTITION BY s.WorkerID ORDER BY s.MonthEndDate) AS rn,
        s.BaseUsdNominal, s.BaseUsdConstant, s.LoadedUsdNominal, s.LoadedUsdConstant,
        l.CumPromotionBaseNominal + l.CumDemotionBaseNominal + l.CumTenureBaseNominal + l.CumMarketBaseNominal
          + l.CumRelocationBaseNominal + l.CumIntlTransferBaseNominal + l.CumFteBaseNominal + l.CumFxBaseNominal      AS ExplainedBN,
        l.CumPromotionBaseConstant + l.CumDemotionBaseConstant + l.CumTenureBaseConstant + l.CumMarketBaseConstant
          + l.CumRelocationBaseConstant + l.CumIntlTransferBaseConstant + l.CumFteBaseConstant                         AS ExplainedBC,
        l.CumPromotionLoadedNominal + l.CumDemotionLoadedNominal + l.CumTenureLoadedNominal + l.CumMarketLoadedNominal
          + l.CumRelocationLoadedNominal + l.CumIntlTransferLoadedNominal + l.CumFteLoadedNominal
          + l.CumFringeLoadedNominal + l.CumFxLoadedNominal                                                            AS ExplainedLN,
        l.CumPromotionLoadedConstant + l.CumDemotionLoadedConstant + l.CumTenureLoadedConstant + l.CumMarketLoadedConstant
          + l.CumRelocationLoadedConstant + l.CumIntlTransferLoadedConstant + l.CumFteLoadedConstant
          + l.CumFringeLoadedConstant                                                                                  AS ExplainedLC
    FROM dw.WorkerMonthEndSnapshot AS s
    JOIN dw.WorkerPayLedger AS l ON l.MonthEndDate = s.MonthEndDate AND l.WorkerID = s.WorkerID
)
SELECT COUNT(*) AS worker_months_not_explained
FROM v
JOIN v AS f ON f.WorkerID = v.WorkerID AND f.rn = 1
WHERE ABS((v.BaseUsdNominal    - f.BaseUsdNominal)    - v.ExplainedBN) > 0.005
   OR ABS((v.BaseUsdConstant   - f.BaseUsdConstant)   - v.ExplainedBC) > 0.005
   OR ABS((v.LoadedUsdNominal  - f.LoadedUsdNominal)  - v.ExplainedLN) > 0.005
   OR ABS((v.LoadedUsdConstant - f.LoadedUsdConstant) - v.ExplainedLC) > 0.005;
GO
