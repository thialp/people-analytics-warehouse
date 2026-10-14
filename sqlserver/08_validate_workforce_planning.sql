/*
  08_validate_workforce_planning.sql
  Control checks for the seat layer (03b_build_dw_workforce_planning.sql) and its
  reporting views. Runs at the end of build_all.sql, or on its own:

    sqlcmd -S localhost -U sa -P "<password>" -C -i /repo/sqlserver/08_validate_workforce_planning.sql

  Every "expected" value comes from the DuckDB pipeline in this repo
  (data/marts/mart_position_fill.csv, mart_vacancy_pool, mart_plan_vs_actual,
  mart_seat_corridors), so SQL Server and the published CSVs must agree.
  Money is compared to within 5 cents: pays and effects are exact to the cent in both
  builds, but a float converted to a decimal can land a cent apart.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

PRINT '1. Row counts';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'dw.DimCostCenter rows'          AS check_name, (SELECT COUNT(*) FROM dw.DimCostCenter)          AS actual, 630     AS expected
    UNION ALL SELECT 'dw.DimPosition rows',                          (SELECT COUNT(*) FROM dw.DimPosition),                      99398
    UNION ALL SELECT 'dw.FactPositionAssignment rows',               (SELECT COUNT(*) FROM dw.FactPositionAssignment),          54094
    UNION ALL SELECT 'dw.FactRequisition rows',                      (SELECT COUNT(*) FROM dw.FactRequisition),                 31323
    UNION ALL SELECT 'dw.FactWorkforcePlan rows',                    (SELECT COUNT(*) FROM dw.FactWorkforcePlan),               29415
    UNION ALL SELECT 'dw.DimCandidate rows',                         (SELECT COUNT(*) FROM dw.DimCandidate),                    188982
    UNION ALL SELECT 'dw.FactCandidateStageEvent rows',              (SELECT COUNT(*) FROM dw.FactCandidateStageEvent),         531691
    UNION ALL SELECT 'dw.PositionMonthEndSnapshot rows',             (SELECT COUNT(*) FROM dw.PositionMonthEndSnapshot),        1701742
    UNION ALL SELECT 'rpt.vw_position_fill rows',                    (SELECT COUNT(*) FROM rpt.vw_position_fill),               30575
    UNION ALL SELECT 'rpt.vw_vacancy_pool rows',                     (SELECT COUNT(*) FROM rpt.vw_vacancy_pool),                62055
    UNION ALL SELECT 'rpt.vw_plan_vs_actual rows',                   (SELECT COUNT(*) FROM rpt.vw_plan_vs_actual),              29415
    UNION ALL SELECT 'rpt.vw_seat_corridors rows',                   (SELECT COUNT(*) FROM rpt.vw_seat_corridors),              821
) AS c;
GO

PRINT '2. Seat integrity (every check expects 0)';
SELECT check_name, failures, CASE WHEN failures = 0 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
    SELECT 'seats with two incumbents at once' AS check_name, COUNT(*) AS failures
    FROM (
        SELECT PositionID, EndDate,
               LEAD(StartDate) OVER (PARTITION BY PositionID ORDER BY StartDate, AssignmentID) AS NextStart
        FROM dw.FactPositionAssignment
    ) AS a
    WHERE NextStart IS NOT NULL AND (EndDate IS NULL OR NextStart <= EndDate)
    UNION ALL
    SELECT 'month-ends where filled seats differ from headcount', COUNT(*)
    FROM (
        SELECT c.MonthEndDate,
               (SELECT COUNT(*) FROM dw.PositionMonthEndSnapshot AS s
                 WHERE s.MonthEndDate = c.MonthEndDate AND s.Status = 'Filled') AS FilledSeats,
               (SELECT COUNT(*) FROM dw.WorkerMonthEndSnapshot AS w
                 WHERE w.MonthEndDate = c.MonthEndDate)                         AS People
        FROM dw.MonthEndCalendar AS c
    ) AS m
    WHERE FilledSeats <> People
    UNION ALL
    SELECT 'fills without a requisition', COUNT(*)
    FROM dw.FactPositionAssignment
    WHERE FillType <> 'Initial' AND RequisitionID IS NULL
    UNION ALL
    SELECT 'backfills whose pay walk does not add up', COUNT(*)
    FROM dw.SeatFill
    WHERE SeatType = 'Backfill'
      AND ABS(PayChangeUsdConstant - LevelEffectUsdConstant - LocationEffectUsdConstant
              - MarketEffectUsdConstant - PositioningEffectUsdConstant) > 0.005
    UNION ALL
    SELECT 'plan quarters whose actual headcount differs from the company', COUNT(*)
    FROM (
        SELECT p.PlanVersion, p.QuarterEndDate, SUM(p.ActualEndingHeadcount) AS Headcount,
               (SELECT COUNT(*) FROM dw.WorkerMonthEndSnapshot AS w WHERE w.MonthEndDate = p.QuarterEndDate) AS People
        FROM dw.PlanVsActual AS p
        GROUP BY p.PlanVersion, p.QuarterEndDate
    ) AS q
    WHERE Headcount <> People
) AS c;
GO

PRINT '3. FY26 seat fills (fiscal_year = 2026)';
SELECT check_name, actual, expected,
       CASE WHEN ABS(actual - expected) <= 0.05 THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'fills'                        AS check_name, CAST((SELECT COUNT(*) FROM rpt.vw_position_fill WHERE fiscal_year = 2026) AS DECIMAL(18, 2)) AS actual, CAST(6849 AS DECIMAL(18, 2)) AS expected
    UNION ALL SELECT 'backfills',                    (SELECT COUNT(*) FROM rpt.vw_position_fill WHERE fiscal_year = 2026 AND seat_type = 'Backfill'), 4668
    UNION ALL SELECT 'net-new seats',                (SELECT COUNT(*) FROM rpt.vw_position_fill WHERE fiscal_year = 2026 AND seat_type = 'Net-new'), 2181
    UNION ALL SELECT 'internal moves',               (SELECT COUNT(*) FROM rpt.vw_position_fill WHERE fiscal_year = 2026 AND fill_type = 'Internal Move'), 1614
    UNION ALL SELECT 'reuse candidates (net-new)',   (SELECT COUNT(*) FROM rpt.vw_position_fill WHERE fiscal_year = 2026 AND reuse_candidate = 1), 628
    UNION ALL SELECT 'vacancy chains',               (SELECT COUNT(DISTINCT chain_id) FROM rpt.vw_position_fill WHERE fiscal_year = 2026), 5681
    UNION ALL SELECT 'pay change, $',                (SELECT CAST(SUM(pay_change_usd_constant) AS DECIMAL(18, 2)) FROM rpt.vw_position_fill WHERE fiscal_year = 2026), -7004254.10
    UNION ALL SELECT 'level effect, $',              (SELECT CAST(SUM(level_effect_usd_constant) AS DECIMAL(18, 2)) FROM rpt.vw_position_fill WHERE fiscal_year = 2026), -6788600.86
    UNION ALL SELECT 'location effect, $',           (SELECT CAST(SUM(location_effect_usd_constant) AS DECIMAL(18, 2)) FROM rpt.vw_position_fill WHERE fiscal_year = 2026), -671912.38
    UNION ALL SELECT 'market effect, $',             (SELECT CAST(SUM(market_effect_usd_constant) AS DECIMAL(18, 2)) FROM rpt.vw_position_fill WHERE fiscal_year = 2026), 2211643.30
    UNION ALL SELECT 'positioning effect, $',        (SELECT CAST(SUM(positioning_effect_usd_constant) AS DECIMAL(18, 2)) FROM rpt.vw_position_fill WHERE fiscal_year = 2026), -1755384.16
    UNION ALL SELECT 'US seat corridors (seats)',    (SELECT SUM(seats) FROM rpt.vw_seat_corridors WHERE fiscal_year = 2026 AND from_country_code = 'US' AND to_country_code = 'US'), 175
) AS c;
GO

PRINT '4. Vacancy pool at 30 Jun 2026';
SELECT check_name, actual, expected,
       CASE WHEN actual = expected THEN 'PASS' ELSE 'FAIL' END AS result
FROM (
              SELECT 'open seats' AS check_name, (SELECT COUNT(*) FROM rpt.vw_vacancy_pool WHERE month_end_date = '2026-06-30' AND status = 'Open') AS actual, 725 AS expected
    UNION ALL SELECT 'open seats vacant 90+ days',   (SELECT COUNT(*) FROM rpt.vw_vacancy_pool WHERE month_end_date = '2026-06-30' AND status = 'Open' AND is_stale = 1), 77
    UNION ALL SELECT 'frozen seats',                 (SELECT COUNT(*) FROM rpt.vw_vacancy_pool WHERE month_end_date = '2026-06-30' AND status = 'Frozen'), 252
    UNION ALL SELECT 'frozen seats vacant 90+ days', (SELECT COUNT(*) FROM rpt.vw_vacancy_pool WHERE month_end_date = '2026-06-30' AND status = 'Frozen' AND is_stale = 1), 136
) AS c;
GO

PRINT '5. FY26 plan vs actual, company (each reforecast covers only the quarters still ahead)';
SELECT plan_version,
       SUM(planned_net_new)   AS planned_net_new,   SUM(actual_net_new)   AS actual_net_new,
       SUM(planned_backfills) AS planned_backfills, SUM(actual_backfills) AS actual_backfills,
       SUM(CASE WHEN fiscal_quarter = 4 THEN planned_ending_headcount END) AS planned_jun_headcount,
       SUM(CASE WHEN fiscal_quarter = 4 THEN actual_ending_headcount END)  AS actual_jun_headcount,
       CAST(SUM(CASE WHEN fiscal_quarter = 4 THEN planned_cost_usd END) AS DECIMAL(18, 2))        AS planned_jun_cost_usd,
       CAST(SUM(CASE WHEN fiscal_quarter = 4 THEN actual_cost_usd_plan_fx END) AS DECIMAL(18, 2)) AS actual_jun_cost_usd_plan_fx
FROM rpt.vw_plan_vs_actual
WHERE fiscal_year = 2026
GROUP BY plan_version
ORDER BY plan_version;
/*
  Expected:
    FY26 Budget   2762   2181   5031   4668   30347   30014   3380139551.15   3341223578.40
    FY26 RF1      1845   1532   3772   3639   30229   30014   3396460209.24   3367102635.16
    FY26 RF2      1097    981   2524   2408   30151   30014   3393655798.51   3373297834.62
    FY26 RF3       549    510   1202   1207   30095   30014   3401481434.59   3391597933.51
*/
GO
