/*
  03f_build_dw_cost_growth_mix.sql
  Release 6.1: dw.WorkforceCostGrowthMix, the year-over-year growth mix behind Dashboard #6 (Workforce
  Cost Bridge), in its own file so it can be rebuilt alone. Runs after 03 and 03c (it reads
  dw.WorkerMonthEndSnapshot and dw.CwMonthEndSnapshot). Moved out of 03c in release 6.1, which also
  adds the employee and contingent headcounts at both dates.
  The T-SQL twin of sql/03_marts/mart_workforce_cost_growth_mix.sql; checked row for row by
  sqlserver/check_tsql_in_duckdb.py, and on SQL Server by 12_validate_contingent_workforce.sql.
  Arcadia Systems is fictional; all data is synthetic.
*/
SET NOCOUNT ON;
USE ArcadiaHR;
GO

/* ------------------------------------------------------------------ growth mix (precomputed)
   Total workforce cost on a date = employees' loaded pay run-rate (executive officers excluded)
   + contingent workers' bill run-rate, nominal USD. With segments k = worker type t x country c
   x level l, C = N x SUM_k a_t x b_c|t x g_l|t,c x r_k x f_k (volume, workforce mix, location
   mix, level mix, rate, currency). Each factor's Shapley effect averages its contribution over
   every order of the six: SUM over S without i of |S|! (5 - |S|)! / 6! x [v(S + i) - v(S)].
   The weights |S|! (5 - |S|)! for |S| = 0..5 are 120, 24, 12, 12, 24, 120; the 64 subsets are
   six 0/1 bits cross-joined. Methodology: docs/projects/workforce-cost-bridge/methodology.md
   Precomputed here and read by rpt.vw_workforce_cost_growth_mix, like PlanVsActual: as a view
   it recomputed 64 subsets over every worker on every query (over 18 minutes under emulation).
   The population is first counted per month-end and segment (#GmPopulation), then joined to
   each pair's two dates on equality (a join on "date IN (from, to)" cannot be a hash join). */
DROP TABLE IF EXISTS #GmPopulation;
SELECT p.MonthEndDate, p.FunctionName, p.WorkerType, p.CountryCode, p.Lvl,
       COUNT(*) AS n, SUM(p.Nom) AS Nom, SUM(p.Con) AS Con
INTO #GmPopulation
FROM (
    SELECT s.MonthEndDate, d.FunctionName, 'Employee' AS WorkerType, s.CountryCode,
           CAST(s.Grade AS VARCHAR(12)) AS Lvl, s.LoadedUsdNominal AS Nom, s.LoadedUsdConstant AS Con
    FROM dw.WorkerMonthEndSnapshot AS s
    JOIN dw.DimDepartment AS d ON d.DepartmentID = s.DepartmentID
    JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
    WHERE s.IsExecutiveOfficer = 0 AND cal.FiscalMonth IN (3, 6, 9, 12)
    UNION ALL
    SELECT s.MonthEndDate, d.FunctionName, 'Contingent', s.CountryCode, s.CwType,
           s.RunRateUsdNominal, s.RunRateUsdConstant
    FROM dw.CwMonthEndSnapshot AS s
    JOIN dw.DimDepartment AS d ON d.DepartmentID = s.DepartmentID
    JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = s.MonthEndDate
    WHERE cal.FiscalMonth IN (3, 6, 9, 12)
) AS p
GROUP BY p.MonthEndDate, p.FunctionName, p.WorkerType, p.CountryCode, p.Lvl;

DROP TABLE IF EXISTS dw.WorkforceCostGrowthMix;
WITH pairs AS (
    SELECT c.MonthEndDate AS ToMonthEnd, f.MonthEndDate AS FromMonthEnd, c.FiscalYear, c.FiscalQuarterLabel
    FROM dw.MonthEndCalendar AS c
    JOIN dw.MonthEndCalendar AS f ON f.MonthEndDate = EOMONTH(DATEADD(MONTH, -12, c.MonthEndDate))
    WHERE c.FiscalMonth IN (3, 6, 9, 12)
),
pair_dates AS (     /* each pair's two dates as rows: Side 0 = earlier, 1 = later */
    SELECT FromMonthEnd, ToMonthEnd, FromMonthEnd AS MonthEndDate, 0 AS Side FROM pairs
    UNION ALL
    SELECT FromMonthEnd, ToMonthEnd, ToMonthEnd, 1 FROM pairs
),
grouped AS (
    SELECT 1 AS ViewOrder, 'Company' AS ViewName, 'Arcadia Systems' AS GroupName, g.* FROM #GmPopulation AS g
    UNION ALL
    SELECT 2, 'Function', g.FunctionName, g.* FROM #GmPopulation AS g
),
seg AS (
    SELECT pd.FromMonthEnd, pd.ToMonthEnd, g.ViewOrder, g.ViewName, g.GroupName,
           g.WorkerType AS t, g.CountryCode AS c, g.Lvl AS l,
           SUM(CASE WHEN pd.Side = 0 THEN g.n ELSE 0 END)                 AS n0,
           SUM(CASE WHEN pd.Side = 1 THEN g.n ELSE 0 END)                 AS n1,
           ISNULL(SUM(CASE WHEN pd.Side = 0 THEN g.Nom END), 0)           AS nom0,
           ISNULL(SUM(CASE WHEN pd.Side = 1 THEN g.Nom END), 0)           AS nom1,
           ISNULL(SUM(CASE WHEN pd.Side = 0 THEN g.Con END), 0)           AS con0,
           ISNULL(SUM(CASE WHEN pd.Side = 1 THEN g.Con END), 0)           AS con1
    FROM pair_dates AS pd
    JOIN grouped AS g ON g.MonthEndDate = pd.MonthEndDate
    GROUP BY pd.FromMonthEnd, pd.ToMonthEnd, g.ViewOrder, g.ViewName, g.GroupName, g.WorkerType, g.CountryCode, g.Lvl
),
sized AS (
    SELECT s.*,
           SUM(n0) OVER (PARTITION BY FromMonthEnd, ToMonthEnd, ViewName, GroupName)       AS big_n0,
           SUM(n1) OVER (PARTITION BY FromMonthEnd, ToMonthEnd, ViewName, GroupName)       AS big_n1,
           SUM(n0) OVER (PARTITION BY FromMonthEnd, ToMonthEnd, ViewName, GroupName, t)    AS nt0,
           SUM(n1) OVER (PARTITION BY FromMonthEnd, ToMonthEnd, ViewName, GroupName, t)    AS nt1,
           SUM(n0) OVER (PARTITION BY FromMonthEnd, ToMonthEnd, ViewName, GroupName, t, c) AS ntc0,
           SUM(n1) OVER (PARTITION BY FromMonthEnd, ToMonthEnd, ViewName, GroupName, t, c) AS ntc1
    FROM seg AS s
),
factors AS (    /* the six factors at each date; where one is undefined on a date, the other date's stands in */
    SELECT FromMonthEnd, ToMonthEnd, ViewOrder, ViewName, GroupName, t, c, l, n0, n1,
           CAST(big_n0 AS FLOAT) AS v0, CAST(big_n1 AS FLOAT) AS v1,
           CAST(nt0 AS FLOAT) / big_n0 AS a0, CAST(nt1 AS FLOAT) / big_n1 AS a1,
           COALESCE(CAST(ntc0 AS FLOAT) / NULLIF(nt0, 0), CAST(ntc1 AS FLOAT) / NULLIF(nt1, 0)) AS b0,
           COALESCE(CAST(ntc1 AS FLOAT) / NULLIF(nt1, 0), CAST(ntc0 AS FLOAT) / NULLIF(nt0, 0)) AS b1,
           COALESCE(CAST(n0 AS FLOAT) / NULLIF(ntc0, 0), CAST(n1 AS FLOAT) / NULLIF(ntc1, 0))   AS g0,
           COALESCE(CAST(n1 AS FLOAT) / NULLIF(ntc1, 0), CAST(n0 AS FLOAT) / NULLIF(ntc0, 0))   AS g1,
           COALESCE(con0 / NULLIF(n0, 0), con1 / NULLIF(n1, 0))                                 AS r0,
           COALESCE(con1 / NULLIF(n1, 0), con0 / NULLIF(n0, 0))                                 AS r1,
           COALESCE(nom0 / NULLIF(con0, 0), nom1 / NULLIF(con1, 0))                             AS f0,
           COALESCE(nom1 / NULLIF(con1, 0), nom0 / NULLIF(con0, 0))                             AS f1
    FROM sized
),
subsets AS (    /* bits: 1 Volume, 2 Workforce mix, 4 Location mix, 8 Level mix, 16 Rate, 32 Currency */
    SELECT b1.x + 2 * b2.x + 4 * b3.x + 8 * b4.x + 16 * b5.x + 32 * b6.x AS bits,
           b1.x + b2.x + b3.x + b4.x + b5.x + b6.x                          AS size
    FROM (VALUES (0), (1)) AS b1 (x) CROSS JOIN (VALUES (0), (1)) AS b2 (x) CROSS JOIN (VALUES (0), (1)) AS b3 (x)
    CROSS JOIN (VALUES (0), (1)) AS b4 (x) CROSS JOIN (VALUES (0), (1)) AS b5 (x) CROSS JOIN (VALUES (0), (1)) AS b6 (x)
),
v AS (          /* the cost with the factors in S at their later value; products rounded to exact decimals */
    SELECT f.FromMonthEnd, f.ToMonthEnd, f.ViewOrder, f.ViewName, f.GroupName, s.bits, s.size,
           SUM(CAST(  (CASE WHEN s.bits & 1  > 0 THEN f.v1 ELSE f.v0 END)
                    * (CASE WHEN s.bits & 2  > 0 THEN f.a1 ELSE f.a0 END)
                    * (CASE WHEN s.bits & 4  > 0 THEN f.b1 ELSE f.b0 END)
                    * (CASE WHEN s.bits & 8  > 0 THEN f.g1 ELSE f.g0 END)
                    * (CASE WHEN s.bits & 16 > 0 THEN f.r1 ELSE f.r0 END)
                    * (CASE WHEN s.bits & 32 > 0 THEN f.f1 ELSE f.f0 END) AS DECIMAL(38, 6))) AS cost
    FROM factors AS f CROSS JOIN subsets AS s
    GROUP BY f.FromMonthEnd, f.ToMonthEnd, f.ViewOrder, f.ViewName, f.GroupName, s.bits, s.size
),
factor_list AS (
    SELECT * FROM (VALUES
        (1, 1,  'Volume',        'More or fewer people'),
        (2, 2,  'Workforce mix', 'The balance of employees and contingent workers'),
        (3, 4,  'Location mix',  'Which countries the people are in'),
        (4, 8,  'Level mix',     'Which grades (or contingent types) the people are in'),
        (5, 16, 'Rate',          'What each person costs at constant exchange rates: pay and bill rates'),
        (6, 32, 'Currency',      'What exchange rates did to the reported cost')
    ) AS x (FactorOrder, Bit, Factor, FactorMeaning)
),
effects AS (
    SELECT v.FromMonthEnd, v.ToMonthEnd, v.ViewOrder, v.ViewName, v.GroupName, fl.FactorOrder, fl.Factor, fl.FactorMeaning,
           SUM(CAST(v.cost * CASE WHEN v.bits & fl.Bit > 0
                                  THEN CASE v.size WHEN 1 THEN 120 WHEN 2 THEN 24 WHEN 3 THEN 12
                                                   WHEN 4 THEN 12 WHEN 5 THEN 24 ELSE 120 END
                                  ELSE -CASE v.size WHEN 0 THEN 120 WHEN 1 THEN 24 WHEN 2 THEN 12
                                                    WHEN 3 THEN 12 WHEN 4 THEN 24 ELSE 120 END END
                    AS DECIMAL(38, 6))) / 720                                           AS shapley,
           SUM(v.cost * CASE WHEN v.bits = 2 * fl.Bit - 1 THEN 1
                             WHEN v.bits = fl.Bit - 1     THEN -1 ELSE 0 END)            AS sequential
    FROM v CROSS JOIN factor_list AS fl
    GROUP BY v.FromMonthEnd, v.ToMonthEnd, v.ViewOrder, v.ViewName, v.GroupName, fl.FactorOrder, fl.Factor, fl.FactorMeaning
),
balances AS (
    SELECT FromMonthEnd, ToMonthEnd, ViewOrder, ViewName, GroupName,
           MAX(CASE WHEN bits = 0  THEN cost END) AS OpeningCost,
           MAX(CASE WHEN bits = 63 THEN cost END) AS ClosingCost
    FROM v GROUP BY FromMonthEnd, ToMonthEnd, ViewOrder, ViewName, GroupName
),
heads AS (
    SELECT FromMonthEnd, ToMonthEnd, ViewName, GroupName, SUM(n0) AS OpeningHeadcount, SUM(n1) AS ClosingHeadcount,
           SUM(CASE WHEN t = 'Employee' THEN n0 ELSE 0 END)   AS OpeningEmployees,
           SUM(CASE WHEN t = 'Employee' THEN n1 ELSE 0 END)   AS ClosingEmployees,
           SUM(CASE WHEN t = 'Contingent' THEN n0 ELSE 0 END) AS OpeningContingent,
           SUM(CASE WHEN t = 'Contingent' THEN n1 ELSE 0 END) AS ClosingContingent
    FROM factors GROUP BY FromMonthEnd, ToMonthEnd, ViewName, GroupName
),
lines AS (
    SELECT FromMonthEnd, ToMonthEnd, ViewOrder, ViewName, GroupName, 0 AS FactorOrder,
           'Opening cost' AS Factor, 'Total workforce cost at the earlier date' AS FactorMeaning,
           OpeningCost AS shapley, OpeningCost AS sequential
    FROM balances
    UNION ALL
    SELECT FromMonthEnd, ToMonthEnd, ViewOrder, ViewName, GroupName, FactorOrder, Factor, FactorMeaning, shapley, sequential
    FROM effects
    UNION ALL
    SELECT FromMonthEnd, ToMonthEnd, ViewOrder, ViewName, GroupName, 7,
           'Closing cost', 'Total workforce cost at the later date', ClosingCost, ClosingCost
    FROM balances
)
SELECT
    l.FromMonthEnd                                                       AS FromMonthEnd,
    l.ToMonthEnd                                                         AS ToMonthEnd,
    p.FiscalYear                                                         AS FiscalYear,
    p.FiscalQuarterLabel                                                 AS FiscalQuarterLabel,
    'Year over year'                                                     AS PairType,
    l.ViewOrder                                                          AS ViewOrder,
    l.ViewName                                                           AS ViewName,
    l.GroupName                                                          AS GroupName,
    l.FactorOrder                                                        AS FactorOrder,
    l.Factor                                                             AS Factor,
    l.FactorMeaning                                                      AS FactorMeaning,
    CAST(ROUND(l.shapley, 2) AS DECIMAL(18, 2))                          AS ShapleyEffectUsd,
    CAST(ROUND(l.sequential, 2) AS DECIMAL(18, 2))                       AS SequentialEffectUsd,
    CAST(ROUND(l.sequential - l.shapley, 2) AS DECIMAL(18, 2))           AS OrderBiasUsd,
    h.OpeningHeadcount                                                   AS OpeningHeadcount,
    h.ClosingHeadcount                                                   AS ClosingHeadcount,
    h.OpeningEmployees                                                   AS OpeningEmployees,
    h.ClosingEmployees                                                   AS ClosingEmployees,
    h.OpeningContingent                                                  AS OpeningContingent,
    h.ClosingContingent                                                  AS ClosingContingent
INTO dw.WorkforceCostGrowthMix
FROM lines AS l
JOIN pairs AS p ON p.ToMonthEnd = l.ToMonthEnd
JOIN heads AS h
  ON h.FromMonthEnd = l.FromMonthEnd AND h.ToMonthEnd = l.ToMonthEnd
 AND h.ViewName = l.ViewName AND h.GroupName = l.GroupName;
DROP TABLE IF EXISTS #GmPopulation;
GO

SELECT 'dw.WorkforceCostGrowthMix' AS TableName, COUNT(*) AS RowsLoaded FROM dw.WorkforceCostGrowthMix;
GO
