/*
  Tableau Custom SQL: Compensation Walk (SQL Server)
  ===========================================================================
  Paste this whole query into Tableau: Data Source page > New Custom SQL.
  Same columns and numbers as data/marts/mart_compensation_walk.csv.
  Field reference, rules and worked examples: docs/projects/compensation-walk/compensation_walk.md

  WHAT IT ANSWERS
  For a pair of month-ends (From, To) and a group of people, why compensation
  moved, as a walk that closes exactly:

      Opening
    + Hires + Exits + Transfers In + Transfers Out          (who is in the group)
    + Promotions + Demotions                                 (career)
    + Tenure Increases + Market Adjustments                  (pay rate)
    + Relocation Adjustments + International Transfer Adj.   (location)
    + FTE Changes + Fringe Rate Changes + FX Translation     (hours, statutory, currency)
    = Closing

  for headcount, FTE and four dollar measures (base / loaded x nominal /
  constant FX), in total and as an average per FTE. Every combination is
  pre-computed: each date pair on the grid, for every group of six views
  (Company, Function, Leader, Department, Office, Country). The workbook only
  filters and sums; it needs no LOD expression, table calculation or
  parameter-driven SQL.

  WHY THE WALK CLOSES IN EVERY GROUP, UNDER ANY FILTER
    1. Each line is priced on ONE side of the pair:
         Opening, Exits, Transfers Out      opening value, opening group
         Transfers In                       OPENING value, closing group
         Hires, Closing                     closing value, closing group
         every pay driver                   amount of change, closing group
       A mover leaves the old group and enters the new one at the same value,
       so the two transfer lines cancel exactly when both groups are in scope.
       Their pay change then lands in the group they joined, under the driver
       that caused it. Nothing is a plug and no residual line exists.
    2. Pay drivers come from dw.WorkerPayLedger, a running total per worker
       of every pay event, FTE change, fringe change and FX movement since
       their first month-end. Between any two month-ends a driver is
       cum(To) - cum(From): two equality joins, no range scan of the history.
       Two changes in one month (a promotion and an anniversary raise) stay
       two separate amounts.
    3. Transfers are decided PER VIEW. Moving office inside a department is a
       transfer in the Office view and not in the Department view, where the
       person simply stays and only their pay drivers show.

  TABLEAU CUSTOM SQL RULES (Tableau wraps this query in a subquery)
    - one SELECT statement: no CTEs (WITH), temp tables or variables
    - no ORDER BY
    - block comments only: a "--" comment on the last line would comment out
      the bracket Tableau adds after the query
  Without CTEs the logic is layered as derived tables, read inside out:
    1. worker pairs   one row per worker per date pair, everyone present at
                      either date, with the ledger difference for each driver
    2. pre-aggregate  workers with the same dates, groups and reasons become
                      one row (about 9 workers per row): aggregate early ...
    3. expand         ... expand late: CROSS APPLY (VALUES) turns each row into
                      six views, then into the walk steps that apply
    4. aggregate      to date pair x view x group x step x reason
    5. group totals   window SUMs put each group's opening and closing beside
                      every line, for the average walk and the percent walk

  THE GRID (the runtime lever)
  Pairs are taken from dw.MonthEndCalendar where both month-ends are quarter
  ends (136 pairs), or the two month-ends are consecutive (48 month-over-month
  pairs). The rule appears twice, at the two GRID markers; keep them identical.
  Deleting both conditions gives every month-end to every later month-end:
  1,176 pairs, about 8x the rows and run time.

  SCOPE
  Executive officers (the CEO and the function heads) are excluded, as in the
  other cost reporting. Pay is the annualized run-rate at each month-end
  (annual base x FTE); loaded adds the employer fringe rate. Someone hired and
  gone between the two dates is in neither snapshot, so not in the walk.
*/
SELECT
    t.from_date                                                                  AS from_month_end,
    t.to_date                                                                    AS to_month_end,
    cf.FiscalPeriod                                                              AS from_fiscal_period,
    ct.FiscalPeriod                                                              AS to_fiscal_period,
    cf.FiscalQuarterLabel                                                        AS from_fiscal_quarter,
    ct.FiscalQuarterLabel                                                        AS to_fiscal_quarter,
    DATEDIFF(MONTH, t.from_date, t.to_date)                                      AS months_between,
    CASE
        WHEN DATEDIFF(MONTH, t.from_date, t.to_date) = 1  THEN 'Month over Month'
        WHEN DATEDIFF(MONTH, t.from_date, t.to_date) = 3  THEN 'Quarter over Quarter'
        WHEN DATEDIFF(MONTH, t.from_date, t.to_date) = 12 THEN 'Year over Year'
        WHEN MONTH(t.from_date) = 6 AND t.to_date < DATEADD(MONTH, 12, t.from_date) THEN 'Fiscal Year to Date'
        ELSE 'Custom Range'
    END                                                                          AS pair_type,
    t.view_order,
    t.view_name,
    t.group_id,
    CASE t.view_name
        WHEN 'Office'  THEN lo.OfficeName
        WHEN 'Country' THEN co.CountryName
        ELSE ou.OrgUnitName
    END                                                                          AS group_name,
    CASE t.view_name
        WHEN 'Function'   THEN 'Arcadia Systems'
        WHEN 'Leader'     THEN ou.FunctionName
        WHEN 'Department' THEN ou.FunctionName
        WHEN 'Office'     THEN lo.CountryName
        WHEN 'Country'    THEN co.Region
    END                                                                          AS group_parent,
    lw.LeaderName                                                                AS group_leader,
    t.step_order,
    t.step,
    t.step_group,
    t.movement_reason,
    t.worker_count,
    t.headcount,
    CAST(ROUND(t.fte, 2)                 AS DECIMAL(19, 2))                      AS fte,
    CAST(ROUND(t.base_usd_nominal, 2)    AS DECIMAL(19, 2))                      AS base_usd_nominal,
    CAST(ROUND(t.base_usd_constant, 2)   AS DECIMAL(19, 2))                      AS base_usd_constant,
    CAST(ROUND(t.loaded_usd_nominal, 2)  AS DECIMAL(19, 2))                      AS loaded_usd_nominal,
    CAST(ROUND(t.loaded_usd_constant, 2) AS DECIMAL(19, 2))                      AS loaded_usd_constant,
    /* AVERAGE WALK, per FTE. Opening and Closing carry the group's average;
       every other step carries its contribution to the change in average:
           (step amount - step FTE x opening average) / closing FTE
       The steps add up exactly to closing average - opening average. */
    CAST(ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_bn  / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_bn / NULLIF(t.close_fte, 0)
        ELSE (t.base_usd_nominal - t.fte * ISNULL(t.open_bn / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4) AS DECIMAL(19, 4))                                                   AS avg_base_usd_nominal,
    CAST(ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_bc  / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_bc / NULLIF(t.close_fte, 0)
        ELSE (t.base_usd_constant - t.fte * ISNULL(t.open_bc / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4) AS DECIMAL(19, 4))                                                   AS avg_base_usd_constant,
    CAST(ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_ln  / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_ln / NULLIF(t.close_fte, 0)
        ELSE (t.loaded_usd_nominal - t.fte * ISNULL(t.open_ln / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4) AS DECIMAL(19, 4))                                                   AS avg_loaded_usd_nominal,
    CAST(ROUND(CASE t.step
        WHEN 'Opening' THEN t.open_lc  / NULLIF(t.open_fte, 0)
        WHEN 'Closing' THEN t.close_lc / NULLIF(t.close_fte, 0)
        ELSE (t.loaded_usd_constant - t.fte * ISNULL(t.open_lc / NULLIF(t.open_fte, 0), 0)) / NULLIF(t.close_fte, 0)
    END, 4) AS DECIMAL(19, 4))                                                   AS avg_loaded_usd_constant,
    /* PERCENT WALK: each line as a share of the group's opening total */
    CAST(ROUND(t.base_usd_nominal    / NULLIF(t.open_bn, 0), 6) AS DECIMAL(19, 6)) AS pct_base_usd_nominal,
    CAST(ROUND(t.base_usd_constant   / NULLIF(t.open_bc, 0), 6) AS DECIMAL(19, 6)) AS pct_base_usd_constant,
    CAST(ROUND(t.loaded_usd_nominal  / NULLIF(t.open_ln, 0), 6) AS DECIMAL(19, 6)) AS pct_loaded_usd_nominal,
    CAST(ROUND(t.loaded_usd_constant / NULLIF(t.open_lc, 0), 6) AS DECIMAL(19, 6)) AS pct_loaded_usd_constant
FROM (
    /* 5. group totals: each group's opening and closing beside every line */
    SELECT
        w.*,
        SUM(CASE WHEN w.step = 'Opening' THEN w.fte END)                 OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS open_fte,
        SUM(CASE WHEN w.step = 'Closing' THEN w.fte END)                 OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS close_fte,
        SUM(CASE WHEN w.step = 'Opening' THEN w.base_usd_nominal END)    OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS open_bn,
        SUM(CASE WHEN w.step = 'Opening' THEN w.base_usd_constant END)   OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS open_bc,
        SUM(CASE WHEN w.step = 'Opening' THEN w.loaded_usd_nominal END)  OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS open_ln,
        SUM(CASE WHEN w.step = 'Opening' THEN w.loaded_usd_constant END) OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS open_lc,
        SUM(CASE WHEN w.step = 'Closing' THEN w.base_usd_nominal END)    OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS close_bn,
        SUM(CASE WHEN w.step = 'Closing' THEN w.base_usd_constant END)   OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS close_bc,
        SUM(CASE WHEN w.step = 'Closing' THEN w.loaded_usd_nominal END)  OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS close_ln,
        SUM(CASE WHEN w.step = 'Closing' THEN w.loaded_usd_constant END) OVER (PARTITION BY w.from_date, w.to_date, w.view_name, w.group_id) AS close_lc
    FROM (
        /* 4. aggregate to date pair x view x group x step x reason */
        SELECT
            wl.from_date, wl.to_date, wl.view_order, wl.view_name, wl.group_id,
            wl.step_order, wl.step, wl.step_group, wl.movement_reason,
            SUM(wl.people)          AS worker_count,
            SUM(wl.hc)              AS headcount,
            SUM(wl.fte)             AS fte,
            SUM(wl.bn)              AS base_usd_nominal,
            SUM(wl.bc)              AS base_usd_constant,
            SUM(wl.ln)              AS loaded_usd_nominal,
            SUM(wl.lc)              AS loaded_usd_constant
        FROM (
            /* 3. expand late: six views, then the walk steps that apply */
            SELECT
                pg.from_date, pg.to_date, v.view_order, v.view_name,
                CASE WHEN st.side = 'open' THEN v.open_key ELSE v.close_key END                 AS group_id,
                st.step_order, st.step, st.step_group,
                CASE WHEN st.step_order IN (4, 5) THEN v.move_reason ELSE st.reason END          AS movement_reason,
                st.people, st.hc, st.fte, st.bn, st.bc, st.ln, st.lc
            FROM (
                /* 2. pre-aggregate: one row per date pair x opening and closing
                      department and office x worker class x reasons */
                SELECT
                    wp.from_date, wp.to_date, wp.worker_class, wp.exit_reason,
                    wp.o_dept, wp.o_loc, wp.c_dept, wp.c_loc, wp.org_move_reason, wp.location_move_reason,
                    COUNT(*)            AS n,
                    SUM(wp.f0)          AS f0,        SUM(wp.f1)          AS f1,
                    SUM(wp.bn0)         AS bn0,       SUM(wp.bc0)         AS bc0,
                    SUM(wp.ln0)         AS ln0,       SUM(wp.lc0)         AS lc0,
                    SUM(wp.bn1)         AS bn1,       SUM(wp.bc1)         AS bc1,
                    SUM(wp.ln1)         AS ln1,       SUM(wp.lc1)         AS lc1,
                    SUM(wp.promo_bn)    AS promo_bn,  SUM(wp.promo_bc)    AS promo_bc,  SUM(wp.promo_ln)  AS promo_ln,  SUM(wp.promo_lc)  AS promo_lc,
                    SUM(wp.demo_bn)     AS demo_bn,   SUM(wp.demo_bc)     AS demo_bc,   SUM(wp.demo_ln)   AS demo_ln,   SUM(wp.demo_lc)   AS demo_lc,
                    SUM(wp.tenure_bn)   AS tenure_bn, SUM(wp.tenure_bc)   AS tenure_bc, SUM(wp.tenure_ln) AS tenure_ln, SUM(wp.tenure_lc) AS tenure_lc,
                    SUM(wp.market_bn)   AS market_bn, SUM(wp.market_bc)   AS market_bc, SUM(wp.market_ln) AS market_ln, SUM(wp.market_lc) AS market_lc,
                    SUM(wp.reloc_bn)    AS reloc_bn,  SUM(wp.reloc_bc)    AS reloc_bc,  SUM(wp.reloc_ln)  AS reloc_ln,  SUM(wp.reloc_lc)  AS reloc_lc,
                    SUM(wp.intl_bn)     AS intl_bn,   SUM(wp.intl_bc)     AS intl_bc,   SUM(wp.intl_ln)   AS intl_ln,   SUM(wp.intl_lc)   AS intl_lc,
                    SUM(wp.fte_bn)      AS fte_bn,    SUM(wp.fte_bc)      AS fte_bc,    SUM(wp.fte_ln)    AS fte_ln,    SUM(wp.fte_lc)    AS fte_lc,
                    SUM(wp.fringe_ln)   AS fringe_ln, SUM(wp.fringe_lc)   AS fringe_lc,
                    SUM(wp.fx_bn)       AS fx_bn,     SUM(wp.fx_ln)       AS fx_ln,
                    /* people behind each pay driver: workers with at least one event of that kind */
                    SUM(CASE WHEN wp.promo_events  > 0 THEN 1 ELSE 0 END)                    AS promo_people,
                    SUM(CASE WHEN wp.demo_events   > 0 THEN 1 ELSE 0 END)                    AS demo_people,
                    SUM(CASE WHEN wp.tenure_events > 0 THEN 1 ELSE 0 END)                    AS tenure_people,
                    SUM(CASE WHEN wp.market_events > 0 THEN 1 ELSE 0 END)                    AS market_people,
                    SUM(CASE WHEN wp.reloc_events  > 0 THEN 1 ELSE 0 END)                    AS reloc_people,
                    SUM(CASE WHEN wp.intl_events   > 0 THEN 1 ELSE 0 END)                    AS intl_people,
                    SUM(CASE WHEN wp.fte_events    > 0 THEN 1 ELSE 0 END)                    AS fte_people,
                    SUM(CASE WHEN wp.fringe_lc <> 0 OR wp.fringe_ln <> 0 THEN 1 ELSE 0 END)  AS fringe_people,
                    SUM(CASE WHEN wp.fx_bn     <> 0 OR wp.fx_ln     <> 0 THEN 1 ELSE 0 END)  AS fx_people
                FROM (
                    /* 1. worker pairs: everyone present at the From or the To month-end */
                    SELECT
                        g.from_date, g.to_date,
                        CASE WHEN o.WorkerID IS NULL THEN 'Hire'
                             WHEN c.WorkerID IS NULL THEN 'Exit'
                             ELSE 'Continuing' END                                                AS worker_class,
                        CASE WHEN c.WorkerID IS NULL THEN w.TerminationType END                   AS exit_reason,
                        o.DepartmentID AS o_dept, o.LocationID AS o_loc,
                        c.DepartmentID AS c_dept, c.LocationID AS c_loc,
                        CASE WHEN o.DepartmentID <> c.DepartmentID THEN lc.OrgMoveReason END      AS org_move_reason,
                        CASE WHEN o.LocationID   <> c.LocationID   THEN lc.LocationMoveReason END AS location_move_reason,
                        /* every amount becomes an exact decimal here, so all later sums are exact */
                        CAST(o.FTE AS DECIMAL(38, 10)) AS f0, CAST(c.FTE AS DECIMAL(38, 10)) AS f1,
                        CAST(o.BaseUsdNominal    AS DECIMAL(38, 10)) AS bn0, CAST(o.BaseUsdConstant   AS DECIMAL(38, 10)) AS bc0,
                        CAST(o.LoadedUsdNominal  AS DECIMAL(38, 10)) AS ln0, CAST(o.LoadedUsdConstant AS DECIMAL(38, 10)) AS lc0,
                        CAST(c.BaseUsdNominal    AS DECIMAL(38, 10)) AS bn1, CAST(c.BaseUsdConstant   AS DECIMAL(38, 10)) AS bc1,
                        CAST(c.LoadedUsdNominal  AS DECIMAL(38, 10)) AS ln1, CAST(c.LoadedUsdConstant AS DECIMAL(38, 10)) AS lc1,
                        /* driver amounts between the two dates: ledger at To minus ledger at From */
                        CAST(lc.CumPromotionBaseNominal       - lo.CumPromotionBaseNominal AS DECIMAL(38, 10))       AS promo_bn,
                        CAST(lc.CumPromotionBaseConstant      - lo.CumPromotionBaseConstant AS DECIMAL(38, 10))      AS promo_bc,
                        CAST(lc.CumPromotionLoadedNominal     - lo.CumPromotionLoadedNominal AS DECIMAL(38, 10))     AS promo_ln,
                        CAST(lc.CumPromotionLoadedConstant    - lo.CumPromotionLoadedConstant AS DECIMAL(38, 10))    AS promo_lc,
                        CAST(lc.CumDemotionBaseNominal        - lo.CumDemotionBaseNominal AS DECIMAL(38, 10))        AS demo_bn,
                        CAST(lc.CumDemotionBaseConstant       - lo.CumDemotionBaseConstant AS DECIMAL(38, 10))       AS demo_bc,
                        CAST(lc.CumDemotionLoadedNominal      - lo.CumDemotionLoadedNominal AS DECIMAL(38, 10))      AS demo_ln,
                        CAST(lc.CumDemotionLoadedConstant     - lo.CumDemotionLoadedConstant AS DECIMAL(38, 10))     AS demo_lc,
                        CAST(lc.CumTenureBaseNominal          - lo.CumTenureBaseNominal AS DECIMAL(38, 10))          AS tenure_bn,
                        CAST(lc.CumTenureBaseConstant         - lo.CumTenureBaseConstant AS DECIMAL(38, 10))         AS tenure_bc,
                        CAST(lc.CumTenureLoadedNominal        - lo.CumTenureLoadedNominal AS DECIMAL(38, 10))        AS tenure_ln,
                        CAST(lc.CumTenureLoadedConstant       - lo.CumTenureLoadedConstant AS DECIMAL(38, 10))       AS tenure_lc,
                        CAST(lc.CumMarketBaseNominal          - lo.CumMarketBaseNominal AS DECIMAL(38, 10))          AS market_bn,
                        CAST(lc.CumMarketBaseConstant         - lo.CumMarketBaseConstant AS DECIMAL(38, 10))         AS market_bc,
                        CAST(lc.CumMarketLoadedNominal        - lo.CumMarketLoadedNominal AS DECIMAL(38, 10))        AS market_ln,
                        CAST(lc.CumMarketLoadedConstant       - lo.CumMarketLoadedConstant AS DECIMAL(38, 10))       AS market_lc,
                        CAST(lc.CumRelocationBaseNominal      - lo.CumRelocationBaseNominal AS DECIMAL(38, 10))      AS reloc_bn,
                        CAST(lc.CumRelocationBaseConstant     - lo.CumRelocationBaseConstant AS DECIMAL(38, 10))     AS reloc_bc,
                        CAST(lc.CumRelocationLoadedNominal    - lo.CumRelocationLoadedNominal AS DECIMAL(38, 10))    AS reloc_ln,
                        CAST(lc.CumRelocationLoadedConstant   - lo.CumRelocationLoadedConstant AS DECIMAL(38, 10))   AS reloc_lc,
                        CAST(lc.CumIntlTransferBaseNominal    - lo.CumIntlTransferBaseNominal AS DECIMAL(38, 10))    AS intl_bn,
                        CAST(lc.CumIntlTransferBaseConstant   - lo.CumIntlTransferBaseConstant AS DECIMAL(38, 10))   AS intl_bc,
                        CAST(lc.CumIntlTransferLoadedNominal  - lo.CumIntlTransferLoadedNominal AS DECIMAL(38, 10))  AS intl_ln,
                        CAST(lc.CumIntlTransferLoadedConstant - lo.CumIntlTransferLoadedConstant AS DECIMAL(38, 10)) AS intl_lc,
                        CAST(lc.CumFteBaseNominal             - lo.CumFteBaseNominal AS DECIMAL(38, 10))             AS fte_bn,
                        CAST(lc.CumFteBaseConstant            - lo.CumFteBaseConstant AS DECIMAL(38, 10))            AS fte_bc,
                        CAST(lc.CumFteLoadedNominal           - lo.CumFteLoadedNominal AS DECIMAL(38, 10))           AS fte_ln,
                        CAST(lc.CumFteLoadedConstant          - lo.CumFteLoadedConstant AS DECIMAL(38, 10))          AS fte_lc,
                        CAST(lc.CumFringeLoadedNominal        - lo.CumFringeLoadedNominal AS DECIMAL(38, 10))        AS fringe_ln,
                        CAST(lc.CumFringeLoadedConstant       - lo.CumFringeLoadedConstant AS DECIMAL(38, 10))       AS fringe_lc,
                        CAST(lc.CumFxBaseNominal              - lo.CumFxBaseNominal AS DECIMAL(38, 10))              AS fx_bn,
                        CAST(lc.CumFxLoadedNominal            - lo.CumFxLoadedNominal AS DECIMAL(38, 10))            AS fx_ln,
                        lc.CumPromotionEvents            - lo.CumPromotionEvents            AS promo_events,
                        lc.CumDemotionEvents             - lo.CumDemotionEvents             AS demo_events,
                        lc.CumTenureEvents               - lo.CumTenureEvents               AS tenure_events,
                        lc.CumMarketEvents               - lo.CumMarketEvents               AS market_events,
                        lc.CumRelocationEvents           - lo.CumRelocationEvents           AS reloc_events,
                        lc.CumIntlTransferEvents         - lo.CumIntlTransferEvents         AS intl_events,
                        lc.CumFteEvents                  - lo.CumFteEvents                  AS fte_events
                    FROM (
                        SELECT f.MonthEndDate AS from_date, t2.MonthEndDate AS to_date
                        FROM dw.MonthEndCalendar AS f
                        JOIN dw.MonthEndCalendar AS t2 ON t2.MonthEndDate > f.MonthEndDate
                        WHERE (MONTH(f.MonthEndDate) IN (3, 6, 9, 12) AND MONTH(t2.MonthEndDate) IN (3, 6, 9, 12))  /* === GRID === */
                           OR t2.PriorMonthEndDate = f.MonthEndDate                                                     /* === GRID === */
                    ) AS g
                    /* everyone employed at some point between the two dates; the WHERE
                       below keeps those present at the From or the To month-end */
                    JOIN dw.DimWorker AS w
                      ON w.OriginalHireDate <= g.to_date
                     AND (w.TerminationDate IS NULL OR w.TerminationDate >= g.from_date)
                     AND w.IsExecutiveOfficer = 0
                    LEFT JOIN dw.WorkerMonthEndSnapshot AS o  ON o.MonthEndDate  = g.from_date AND o.WorkerID  = w.WorkerID
                    LEFT JOIN dw.WorkerPayLedger        AS lo ON lo.MonthEndDate = g.from_date AND lo.WorkerID = w.WorkerID
                    LEFT JOIN dw.WorkerMonthEndSnapshot AS c  ON c.MonthEndDate  = g.to_date   AND c.WorkerID  = w.WorkerID
                    LEFT JOIN dw.WorkerPayLedger        AS lc ON lc.MonthEndDate = g.to_date   AND lc.WorkerID = w.WorkerID
                    WHERE o.WorkerID IS NOT NULL OR c.WorkerID IS NOT NULL
                ) AS wp
                GROUP BY wp.from_date, wp.to_date, wp.worker_class, wp.exit_reason,
                         wp.o_dept, wp.o_loc, wp.c_dept, wp.c_loc, wp.org_move_reason, wp.location_move_reason
            ) AS pg
            /* the function and leader organization each department rolls up to,
               and the country of each office, on both sides of the pair */
            LEFT JOIN (
                SELECT d.DepartmentID,
                       CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
                       d.ParentOrgUnitID AS LeaderOrgID
                FROM dw.DimDepartment AS d
                JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
            ) AS od ON od.DepartmentID = pg.o_dept
            LEFT JOIN (
                SELECT d.DepartmentID,
                       CASE WHEN p.OrgUnitType = 'Sub-function' THEN p.ParentOrgUnitID ELSE p.OrgUnitID END AS FunctionID,
                       d.ParentOrgUnitID AS LeaderOrgID
                FROM dw.DimDepartment AS d
                JOIN dw.DimOrgUnit AS p ON p.OrgUnitID = d.ParentOrgUnitID
            ) AS cd ON cd.DepartmentID = pg.c_dept
            LEFT JOIN dw.DimLocation AS ol ON ol.LocationID = pg.o_loc
            LEFT JOIN dw.DimLocation AS cl ON cl.LocationID = pg.c_loc
            /* the six views: the group a row belongs to at each end of the pair,
               and the reason to show when those two groups differ */
            CROSS APPLY (VALUES
                (1, 'Company',    CAST('ORG-000' AS VARCHAR(15)),   CAST('ORG-000' AS VARCHAR(15)),   CAST(NULL AS VARCHAR(30))),
                (2, 'Function',   CAST(od.FunctionID AS VARCHAR(15)),  CAST(cd.FunctionID AS VARCHAR(15)),  pg.org_move_reason),
                (3, 'Leader',     CAST(od.LeaderOrgID AS VARCHAR(15)), CAST(cd.LeaderOrgID AS VARCHAR(15)), pg.org_move_reason),
                (4, 'Department', CAST(pg.o_dept AS VARCHAR(15)),      CAST(pg.c_dept AS VARCHAR(15)),      pg.org_move_reason),
                (5, 'Office',     CAST(pg.o_loc AS VARCHAR(15)),       CAST(pg.c_loc AS VARCHAR(15)),       pg.location_move_reason),
                (6, 'Country',    CAST(ol.CountryCode AS VARCHAR(15)), CAST(cl.CountryCode AS VARCHAR(15)), pg.location_move_reason)
            ) AS v (view_order, view_name, open_key, close_key, move_reason)
            /* the walk steps: which side prices the line, whether it applies to this
               row, and its signed people, headcount, FTE and four dollar amounts */
            CROSS APPLY (VALUES
                (1,  'Opening',                            'Balance',        'open',  CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.worker_class <> 'Hire' THEN 1 ELSE 0 END,
                     pg.n,  pg.n,  pg.f0,  pg.bn0,  pg.bc0,  pg.ln0,  pg.lc0),
                (2,  'Hires',                              'Headcount',      'close', CAST('New Hire' AS VARCHAR(30)),
                     CASE WHEN pg.worker_class = 'Hire' THEN 1 ELSE 0 END,
                     pg.n,  pg.n,  pg.f1,  pg.bn1,  pg.bc1,  pg.ln1,  pg.lc1),
                (3,  'Exits',                              'Headcount',      'open',  CAST(pg.exit_reason AS VARCHAR(30)),
                     CASE WHEN pg.worker_class = 'Exit' THEN 1 ELSE 0 END,
                     pg.n, -pg.n, -pg.f0, -pg.bn0, -pg.bc0, -pg.ln0, -pg.lc0),
                (4,  'Transfers In',                       'Headcount',      'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.worker_class = 'Continuing' AND v.open_key <> v.close_key THEN 1 ELSE 0 END,
                     pg.n,  pg.n,  pg.f0,  pg.bn0,  pg.bc0,  pg.ln0,  pg.lc0),
                (5,  'Transfers Out',                      'Headcount',      'open',  CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.worker_class = 'Continuing' AND v.open_key <> v.close_key THEN 1 ELSE 0 END,
                     pg.n, -pg.n, -pg.f0, -pg.bn0, -pg.bc0, -pg.ln0, -pg.lc0),
                (6,  'Promotions',                         'Career',         'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.promo_people  > 0 THEN 1 ELSE 0 END,
                     pg.promo_people,  0, 0, pg.promo_bn,  pg.promo_bc,  pg.promo_ln,  pg.promo_lc),
                (7,  'Demotions',                          'Career',         'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.demo_people   > 0 THEN 1 ELSE 0 END,
                     pg.demo_people,   0, 0, pg.demo_bn,   pg.demo_bc,   pg.demo_ln,   pg.demo_lc),
                (8,  'Tenure Increases',                   'Pay Rate',       'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.tenure_people > 0 THEN 1 ELSE 0 END,
                     pg.tenure_people, 0, 0, pg.tenure_bn, pg.tenure_bc, pg.tenure_ln, pg.tenure_lc),
                (9,  'Market Adjustments',                 'Pay Rate',       'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.market_people > 0 THEN 1 ELSE 0 END,
                     pg.market_people, 0, 0, pg.market_bn, pg.market_bc, pg.market_ln, pg.market_lc),
                (10, 'Relocation Adjustments',             'Location',       'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.reloc_people  > 0 THEN 1 ELSE 0 END,
                     pg.reloc_people,  0, 0, pg.reloc_bn,  pg.reloc_bc,  pg.reloc_ln,  pg.reloc_lc),
                (11, 'International Transfer Adjustments', 'Location',       'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.intl_people   > 0 THEN 1 ELSE 0 END,
                     pg.intl_people,   0, 0, pg.intl_bn,   pg.intl_bc,   pg.intl_ln,   pg.intl_lc),
                (12, 'FTE Changes',                        'Workforce Rate', 'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.fte_people    > 0 THEN 1 ELSE 0 END,
                     pg.fte_people,    0, pg.f1 - pg.f0, pg.fte_bn, pg.fte_bc, pg.fte_ln, pg.fte_lc),
                (13, 'Fringe Rate Changes',                'Statutory',      'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.fringe_people > 0 THEN 1 ELSE 0 END,
                     pg.fringe_people, 0, 0, 0, 0, pg.fringe_ln, pg.fringe_lc),
                (14, 'FX Translation',                     'Currency',       'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.fx_people     > 0 THEN 1 ELSE 0 END,
                     pg.fx_people,     0, 0, pg.fx_bn, 0, pg.fx_ln, 0),
                (15, 'Closing',                            'Balance',        'close', CAST(NULL AS VARCHAR(30)),
                     CASE WHEN pg.worker_class <> 'Exit' THEN 1 ELSE 0 END,
                     pg.n,  pg.n,  pg.f1,  pg.bn1,  pg.bc1,  pg.ln1,  pg.lc1)
            ) AS st (step_order, step, step_group, side, reason, include_line, people, hc, fte, bn, bc, ln, lc)
            WHERE st.include_line = 1
        ) AS wl
        GROUP BY wl.from_date, wl.to_date, wl.view_order, wl.view_name, wl.group_id,
                 wl.step_order, wl.step, wl.step_group, wl.movement_reason
    ) AS w
) AS t
JOIN dw.MonthEndCalendar AS cf ON cf.MonthEndDate = t.from_date
JOIN dw.MonthEndCalendar AS ct ON ct.MonthEndDate = t.to_date
LEFT JOIN dw.DimOrgUnit  AS ou ON ou.OrgUnitID = t.group_id
LEFT JOIN dw.DimLocation AS lo ON t.view_name = 'Office'  AND lo.LocationID  = t.group_id
LEFT JOIN dw.DimCountry  AS co ON t.view_name = 'Country' AND co.CountryCode = t.group_id
LEFT JOIN (
    /* the leader of each org unit on each month-end (offices and countries have none) */
    SELECT s.MonthEndDate, s.LeadsOrgUnitID, CONCAT(lw0.FirstName, ' ', lw0.LastName) AS LeaderName
    FROM dw.WorkerMonthEndSnapshot AS s
    JOIN dw.DimWorker AS lw0 ON lw0.WorkerID = s.WorkerID
    WHERE s.LeadsOrgUnitID IS NOT NULL
) AS lw ON lw.MonthEndDate = t.to_date AND lw.LeadsOrgUnitID = t.group_id
