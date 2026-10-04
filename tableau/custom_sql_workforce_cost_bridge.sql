/*
  Tableau Custom SQL: Workforce Cost Bridge (SQL Server)
  ---------------------------------------------------------------------------
  Paste this whole query into Tableau: Data Source page > New Custom SQL.
  Returns one row per month-end x department x driver, with the same columns as
  data/marts/mart_workforce_cost_bridge.csv.

  Written for Tableau's Custom SQL rules, which wrap the query in a subquery:
    - a single SELECT: no CTEs (WITH), temp tables or variables
    - no ORDER BY
    - block comments only: a "--" comment on the last line would comment out
      the closing bracket Tableau adds after the query

  Because CTEs are off the table, the logic is layered with derived tables and
  CROSS APPLY:
    1. worker pairs   each worker's prior and current month-end state side by
                      side (FULL OUTER JOIN of two snapshot slices)
    2. measures       CROSS APPLY computes values and the rate decomposition once
    3. driver lines   CROSS APPLY (VALUES ...) unpivots each worker into the 12
                      walk lines; include_line keeps only the ones that apply
    4. aggregate      sum to month x department x driver

  For each department and month: Opening + all drivers = Closing.
  Methodology: docs/methodology.md
*/
SELECT
    w.month_end_date,
    cal.PriorMonthEndDate                                                         AS prior_month_end_date,
    cal.FiscalYear                                                                AS fiscal_year,
    cal.FiscalQuarterLabel                                                        AS fiscal_quarter_label,
    cal.FiscalPeriod                                                              AS fiscal_period,
    v.department_id,
    d.DepartmentName                                                              AS department_name,
    d.SubFunction                                                                 AS sub_function,
    d.FunctionName                                                                AS function_name,
    d.CostCenter                                                                  AS cost_center,
    v.driver_order,
    v.driver,
    v.driver_group,
    COUNT(DISTINCT w.worker_id)                                                   AS worker_count,
    SUM(v.headcount)                                                              AS headcount,
    CAST(ROUND(SUM(CAST(v.fte      AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2))     AS fte,
    CAST(ROUND(SUM(CAST(v.base_nom AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2))     AS base_usd_nominal,
    CAST(ROUND(SUM(CAST(v.base_con AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2))     AS base_usd_constant,
    CAST(ROUND(SUM(CAST(v.load_nom AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2))     AS loaded_usd_nominal,
    CAST(ROUND(SUM(CAST(v.load_con AS DECIMAL(19, 4))), 2) AS DECIMAL(19, 2))     AS loaded_usd_constant
FROM (
    /* 1. worker pairs: prior month-end state (p) beside current month-end state (c) */
    SELECT
        COALESCE(c.MonthEndDate, p.WalkMonthEndDate)               AS month_end_date,
        COALESCE(c.WorkerID, p.WorkerID)                           AS worker_id,
        CASE
            WHEN p.WorkerID IS NULL                THEN 'Hire'
            WHEN c.WorkerID IS NULL                THEN 'Termination'
            WHEN p.DepartmentID <> c.DepartmentID  THEN 'Transfer'
            ELSE 'Stayer'
        END                                                        AS movement_type,
        p.DepartmentID                                             AS dept_p,
        c.DepartmentID                                             AS dept_c,
        p.CountryCode                                              AS country_p,
        c.CountryCode                                              AS country_c,
        p.Grade                                                    AS grade_p,
        c.Grade                                                    AS grade_c,
        CAST(p.FTE AS FLOAT)                                       AS f0,
        CAST(c.FTE AS FLOAT)                                       AS f1,
        CAST(p.BaseSalaryAnnualLocal AS FLOAT)                     AS b0,
        CAST(c.BaseSalaryAnnualLocal AS FLOAT)                     AS b1,
        p.FxRateActual                                             AS x0,
        c.FxRateActual                                             AS x1,
        p.FxRateConstant                                           AS k0,
        c.FxRateConstant                                           AS k1,
        p.FringeRate                                               AS r0,
        c.FringeRate                                               AS r1,
        fx_cp.UsdPerLocalActual                                    AS x1p  /* current currency at prior month-end rate */
    FROM (
        SELECT cal_p.MonthEndDate AS WalkMonthEndDate, s.*
        FROM dw.WorkerMonthEndSnapshot AS s
        JOIN dw.MonthEndCalendar AS cal_p ON cal_p.PriorMonthEndDate = s.MonthEndDate
        WHERE s.IsExecutiveOfficer = 0
    ) AS p
    FULL OUTER JOIN (
        SELECT cal_c.PriorMonthEndDate, s.*
        FROM dw.WorkerMonthEndSnapshot AS s
        JOIN dw.MonthEndCalendar AS cal_c ON cal_c.MonthEndDate = s.MonthEndDate
        WHERE s.IsExecutiveOfficer = 0
          AND cal_c.PriorMonthEndDate IS NOT NULL
    ) AS c
      ON c.MonthEndDate = p.WalkMonthEndDate
     AND c.WorkerID     = p.WorkerID
    LEFT JOIN dw.RefFxRate AS fx_cp
      ON fx_cp.CurrencyCode = c.CurrencyCode
     AND fx_cp.RateDate     = c.PriorMonthEndDate
) AS w

/* 2. measures: values at each end and the rate decomposition, computed once */
CROSS APPLY (
    SELECT
        w.b0 * w.f0 * w.x0                               AS base_nom_0,
        w.b0 * w.f0 * w.k0                               AS base_con_0,
        w.b0 * w.f0 * w.x0 * (1 + w.r0)                  AS load_nom_0,
        w.b0 * w.f0 * w.k0 * (1 + w.r0)                  AS load_con_0,
        w.b1 * w.f1 * w.x1                               AS base_nom_1,
        w.b1 * w.f1 * w.k1                               AS base_con_1,
        w.b1 * w.f1 * w.x1 * (1 + w.r1)                  AS load_nom_1,
        w.b1 * w.f1 * w.k1 * (1 + w.r1)                  AS load_con_1,
        (w.b1 * w.x1p - w.b0 * w.x0) * w.f0              AS pay_base_nom,
        (w.b1 * w.k1  - w.b0 * w.k0) * w.f0              AS pay_base_con,
        (w.b1 * w.x1p - w.b0 * w.x0) * w.f0 * (1 + w.r0) AS pay_load_nom,
        (w.b1 * w.k1  - w.b0 * w.k0) * w.f0 * (1 + w.r0) AS pay_load_con,
        w.b1 * w.x1p * (w.f1 - w.f0)                     AS fte_base_nom,
        w.b1 * w.k1  * (w.f1 - w.f0)                     AS fte_base_con,
        w.b1 * w.x1p * (w.f1 - w.f0) * (1 + w.r0)        AS fte_load_nom,
        w.b1 * w.k1  * (w.f1 - w.f0) * (1 + w.r0)        AS fte_load_con,
        w.b1 * w.x1p * w.f1 * (w.r1 - w.r0)              AS fringe_load_nom,
        w.b1 * w.k1  * w.f1 * (w.r1 - w.r0)              AS fringe_load_con,
        w.b1 * w.f1 * (w.x1 - w.x1p)                     AS fx_base_nom,
        w.b1 * w.f1 * (1 + w.r1) * (w.x1 - w.x1p)        AS fx_load_nom,
        CASE WHEN w.movement_type IN ('Stayer', 'Transfer') THEN 1 ELSE 0 END AS is_continuing,
        CASE
            WHEN w.country_c <> w.country_p THEN 'International Mobility'
            WHEN w.grade_c   >  w.grade_p   THEN 'Promotions'
            ELSE 'Merit & Adjustments'
        END                                              AS pay_driver
) AS m

/* 3. driver lines: one candidate row per walk line; include_line keeps the ones that apply */
CROSS APPLY (VALUES
    (1,  'Opening Run-Rate',       'Balance',            w.dept_p,
         CASE WHEN w.movement_type <> 'Hire' THEN 1 ELSE 0 END,
         1,  w.f0,  m.base_nom_0,  m.base_con_0,  m.load_nom_0,  m.load_con_0),
    (2,  'Hires',                  'Headcount Movement', w.dept_c,
         CASE WHEN w.movement_type = 'Hire' THEN 1 ELSE 0 END,
         1,  w.f1,  m.base_nom_1,  m.base_con_1,  m.load_nom_1,  m.load_con_1),
    (3,  'Terminations',           'Headcount Movement', w.dept_p,
         CASE WHEN w.movement_type = 'Termination' THEN 1 ELSE 0 END,
         -1, -w.f0, -m.base_nom_0, -m.base_con_0, -m.load_nom_0, -m.load_con_0),
    (4,  'Transfers In',           'Headcount Movement', w.dept_c,
         CASE WHEN w.movement_type = 'Transfer' THEN 1 ELSE 0 END,
         1,  w.f0,  m.base_nom_0,  m.base_con_0,  m.load_nom_0,  m.load_con_0),
    (5,  'Transfers Out',          'Headcount Movement', w.dept_p,
         CASE WHEN w.movement_type = 'Transfer' THEN 1 ELSE 0 END,
         -1, -w.f0, -m.base_nom_0, -m.base_con_0, -m.load_nom_0, -m.load_con_0),
    (6,  'Promotions',             'Pay Rate',           w.dept_c,
         CASE WHEN m.is_continuing = 1 AND m.pay_driver = 'Promotions'
                   AND (m.pay_base_nom <> 0 OR m.pay_base_con <> 0) THEN 1 ELSE 0 END,
         0,  0,     m.pay_base_nom, m.pay_base_con, m.pay_load_nom, m.pay_load_con),
    (7,  'Merit & Adjustments',    'Pay Rate',           w.dept_c,
         CASE WHEN m.is_continuing = 1 AND m.pay_driver = 'Merit & Adjustments'
                   AND (m.pay_base_nom <> 0 OR m.pay_base_con <> 0) THEN 1 ELSE 0 END,
         0,  0,     m.pay_base_nom, m.pay_base_con, m.pay_load_nom, m.pay_load_con),
    (8,  'International Mobility', 'Pay Rate',           w.dept_c,   /* includes fringe re-levelling for the move */
         CASE WHEN m.is_continuing = 1 AND m.pay_driver = 'International Mobility' THEN 1 ELSE 0 END,
         0,  0,     m.pay_base_nom, m.pay_base_con,
                    m.pay_load_nom + m.fringe_load_nom, m.pay_load_con + m.fringe_load_con),
    (9,  'FTE Changes',            'Workforce Mix',      w.dept_c,
         CASE WHEN m.is_continuing = 1 AND w.f1 <> w.f0 THEN 1 ELSE 0 END,
         0,  w.f1 - w.f0, m.fte_base_nom, m.fte_base_con, m.fte_load_nom, m.fte_load_con),
    (10, 'Fringe Rate Changes',    'Fringe & FX',        w.dept_c,
         CASE WHEN m.is_continuing = 1 AND m.pay_driver <> 'International Mobility'
                   AND w.r1 <> w.r0 THEN 1 ELSE 0 END,
         0,  0,     0,             0,             m.fringe_load_nom, m.fringe_load_con),
    (11, 'FX Rate Changes',        'Fringe & FX',        w.dept_c,
         CASE WHEN m.is_continuing = 1 AND w.x1 <> w.x1p THEN 1 ELSE 0 END,
         0,  0,     m.fx_base_nom, 0,             m.fx_load_nom,     0),
    (12, 'Closing Run-Rate',       'Balance',            w.dept_c,
         CASE WHEN w.movement_type <> 'Termination' THEN 1 ELSE 0 END,
         1,  w.f1,  m.base_nom_1,  m.base_con_1,  m.load_nom_1,  m.load_con_1)
) AS v (driver_order, driver, driver_group, department_id, include_line,
        headcount, fte, base_nom, base_con, load_nom, load_con)

JOIN dw.MonthEndCalendar AS cal ON cal.MonthEndDate = w.month_end_date
LEFT JOIN dw.DimDepartment AS d  ON d.DepartmentID  = v.department_id
WHERE v.include_line = 1
GROUP BY
    w.month_end_date, cal.PriorMonthEndDate, cal.FiscalYear, cal.FiscalQuarterLabel, cal.FiscalPeriod,
    v.department_id, d.DepartmentName, d.SubFunction, d.FunctionName, d.CostCenter,
    v.driver_order, v.driver, v.driver_group
