# Seats to Fill: plan (Dashboard #5)

Case study 7 in the README for now (renumbered in the profile later) · Dashboard #5 · warehouse release 5. Arcadia Systems is fictional and all data is synthetic.

**Seats to Fill** · *FTE hiring forecast against plan*. Tableau Public title: "Seats to Fill: Hiring Forecast | Arcadia Systems"; the description starts with "Workforce forecasting:", and the tags are forecasting, workforce planning, survival analysis, Python, HR analytics.

**Page question:** *How many PIDs will we need to fill in the forward year, how many will still be vacant at each quarter-end, and can we trust the forecast?*

| Revision | Date | What changed |
|---|---|---|
| 1 | 2026-10-27 | Proposal agreed (sections 1 to 5). Phase 1 built: the report calendar, the forward budget, time-to-fill variation (section 6) |
| 2 | 2026-10-27 | Phase 2 built: the forecast package `forecast/`, eight marts, tests f01 to f05, CI step; method and backtest in [seats_to_fill_method.md](seats_to_fill_method.md). The demand of section 4 is refined there: net-new opens at the median ratio of every known quarter, and each draw has its own demand level and hiring speed |

## 1. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | **Employee PIDs only.** Contingent workers appear as one line: the forward budget's contingent total by function and the workers it buys at today's rates | Contingent workers come from department budgets and are forecast differently (reuse and the position audit, not requisitions). The FTE numbers carry the page |
| D2 | **A forward budget** for the year after the report date, dated May 15 before it, beside the historic budgets | Each year's fills are compared with the budget set before that year; the forecast is compared with the forward budget |
| D3 | **No hard-coded dates.** Every label comes from the report calendar (`ref_report_calendar`, `ref_report_quarter`); parameters store offsets (0 current year, +1 forward year), never years | Next year the as-of date moves to Jun 30, 2027 and every page shows FY28 without editing a calculation. The window keeps its length, so layouts never change |
| D4 | **Organisation: Function > Department**, with sub-function as a heading inside the department list (Sales, Client Services, Engineering, Infrastructure) | Only Commercial and Technology have real sub-functions; for the other six a sub-function list would repeat the function |
| D5 | **Location: Region > Country > Office** | 5 regions, 22 countries, 35 offices |
| D6 | **More time-to-fill variation** by function and graduate season, applied to approval dates only (section 6) | Hires never move, so Dashboards #1, #2 and #4 are unchanged |
| D7 | **Plan attainment in bands, not a hiring-speed scenario**: 0–25%, 25–50%, 50–75%, 75–100%, 100%+ of plan, like a sales quota | Hiring is seasonal and differs by country, so a flat speed slider is not a fair lever. Seasonality lives in the fill model |
| D8 | **Quarters and fiscal years only.** Fiscal year over fiscal year, a quarter against its own year's budget and the same quarter a year earlier, year to date as a sum of quarters. No months | Budgets are analysed quarterly and yearly; quarter grain keeps every mart small |
| D9 | The backtest follows the rail selection, using a mean and a variance per cell | Same scope as the rest of the page |
| D10 | Rules carried: executive officers (D-901) excluded; the unit is the PID and empty ones are "vacant"; neutral wording; muted palette, no blue with orange, no red-and-green; no arrow glyphs in text; tooltip command buttons off; Custom SQL, not CSV | Every Arcadia dashboard |

## 2. Cascading multi-select

The child lists store **exclusions**, so every child of a chosen parent starts ticked.

| Parameter | Holds | Meaning |
|---|---|---|
| `p_Functions` | `\|People\|` | Chosen functions; empty means all |
| `p_DeptOff` | `\|People>Talent Acquisition\|` | Departments unticked inside the chosen functions |
| `p_Regions` | `\|Asia Pacific\|` | Chosen regions; empty means all |
| `p_CountryOff` | `\|Asia Pacific>Japan\|` | Countries unticked |
| `p_OfficeOff` | `\|India>Pune\|` | Offices unticked |

- A child shows only when its parent is chosen, or when nothing is chosen. It is ticked when its parent is in scope and it is not excluded.
- Toggling a parent also strips its children from the exclusion string (`REGEXP_REPLACE([p_DeptOff], "\|People>[^|]*", "")`), so re-ticking a parent brings its children back checked. Spike first; fallback: changing a parent clears all child exclusions of that hierarchy.
- **No blank view:** `Would Empty` = PIDs in scope minus this option's PIDs in scope = 0 locks an option that is the last thing holding the view up; an option with no PIDs under the other hierarchy's selection is dimmed.
- Sizes: Function 8, Department 31 plus 4 headings (3 columns × 12 slots), Region 5, Country 22 (2 × 12), Office 35 (3 × 12), 26 px slots. About 25 parameters and 45 parameter actions plus 18 deselects.
- Rail (216 px, navy): logo and ⓘ · PERIOD · ORGANISATION capsule ("People" / "3 of 4 departments") · LOCATION capsule · Reset · "Data to <as-of>" / "Forecast <forward period>". Each capsule opens a cascade popover with its levels as side-by-side columns. The page subtitle repeats the selection.

## 3. The page

| Where | What |
|---|---|
| KPI 1 | PIDs to fill in the forward year (median forecast, likely range) |
| KPI 2 | Forward year Q1: PIDs to fill · fills expected |
| KPI 3 | Vacant at the forward year's end (forecast) against today |
| KPI 4 | Plan attainment, forecast: share of the forward budget filled, in its band |
| KPI 5 | Median days to fill (last four quarters) · share filled within 30, 60, 90 days |
| Main card | Quarters: 20 of history and 4 forecast. Fills against the budget for each quarter, fiscal years as bands behind them, each year labelled with its attainment band; the forecast dashed with its likely range |
| Right top | How fast we fill: survival curve by level band, 30/60/90-day marks |
| Right middle | Where the forward year's demand comes from (exits, internal moves, plan net-new, open on the as-of date); the contingent budget by function in its hover |
| Right bottom | Can we trust it: the backtest, forecast range against what happened, eight quarters |

## 4. Method

One sentence: *we learned how quickly each kind of PID gets filled and how often people leave, simulated the forward year many times, and checked the same method against quarters that already happened.*

1. **Time to fill**: a discrete-time hazard model (logistic regression on requisition-weeks): the weekly chance a requisition is filled given its age, level band, function, region and the month (graduate seasons). Open requisitions are censored, so recent quarters are not read as slow; an open requisition aged 80 days gets its own remaining time.
2. **Backfill demand**: exit and internal-move rates per head (Poisson, by function, level band and region, with a quarter effect).
3. **Net-new demand**: the forward budget by quarter; PIDs open on the approval date.
4. **Simulation**: 100 draws per department × office × quarter, fixed seed: new vacancies arrive, each is filled by the hazard model, the rest carry over. Out: PIDs to fill, fills, vacant at quarter-end, per draw. Ranges are percentiles of the draws summed over the selection (percentiles do not add up, draws do). Fallback: mean and variance per cell.
5. **Backtest**: origins at eight past quarter-ends, each using only what was known then (data and the budget of that year), scored against what happened.

Survival curves under any selection: the mart stores PIDs at risk and fills per week of wait, which add up; Tableau rebuilds Kaplan–Meier with `EXP(RUNNING_SUM(LN(1 - fills / at risk)))`.

## 5. Phases

| # | Phase | Who | Status |
|---|---|---|---|
| 0 | Proposal | Both | **Done** 2026-10-27 |
| 1 | Generator: report calendar, forward budget, time-to-fill variation; tests 89 to 91 | Claude | **Built** (section 6) |
| 2 | Python models, marts, tests, CI step, methodology | Claude | **Built**: [seats_to_fill_method.md](seats_to_fill_method.md) |
| 3 | SQL Server twin, Custom SQL, validate script; run on the Mac | Claude, then Thiago | To do |
| 4 | Spikes on Tableau Public (cascade, draws, Kaplan–Meier table calc) | Claude writes, Thiago runs | To do |
| 5 | Check tables and a prototype with real numbers | Claude, Thiago approves | To do |
| 6 | Build guide, then the build in Tableau | Claude, Thiago | To do |
| 7 | Publish, README, Figma, profile | Both | To do |

## 6. Phase 1: what changed in the data

**Report calendar.** `generator/report_calendar.py` writes `ref_report_calendar` (one row) and `ref_report_quarter` (24 quarters: FY22 to FY27) from `LAST_SNAPSHOT`. Test 89 ties them to the data.

**Forward budget.** `FY27 Budget`, dated 2026-05-15, four quarters for every cost center active in FY26: net-new from the same quarter of FY26 scaled from FY26's growth (5.5%) to the planned 5.0%, backfills by headcount, headcount grown from Jun 30, 2026, cost at the budget date's FX, with the budget's planning error. The contingent line projects each cost center's Jun 30, 2026 contingent headcount by 6% through the year. Own random streams, written after every historic version, so the FY22 to FY26 plan rows are byte-identical. It stays out of `mart_plan_vs_actual` (test 90).

**Time to fill.** `ttf_factor` in the generator: Technology and Legal & Compliance 15% slower, Operations 15% faster; levels 1 and 2 25% faster when the fill lands in their country's graduate season (Sep–Oct in North America and Europe, Dec–Jan in Brazil, South Africa and Australia, Jul–Aug in India, Singapore and Mexico, Jun–Jul in the Philippines, Apr in Japan, Feb–Mar in South Korea). Net-new PIDs are approved that much earlier or later before the hire; a filled external backfill has its approval moved, never more than 14 days before the person who left had their last day (test 91). Hire dates never move. Applicant draws still follow the simulated dates, so no applicant outside the moved requisitions changes.

| Raw table | Change |
|---|---|
| `fact_requisition` | Approval and opening dates of moved requisitions; 7 more net-new requisitions open at the extract (the slower functions are approved earlier) |
| `dim_position` | Net-new PIDs created on their new approval date; 7 more open at the extract |
| `fact_candidate_stage_event`, `dim_candidate` | Stage dates follow the new approval dates; only the open requisitions at the extract draw new applicants |
| `fact_workforce_plan` | + FY27 Budget rows |
| `ref_report_calendar`, `ref_report_quarter`, registry | New |
| Every other raw table | Byte-identical |

**What the variation looks like** (filled external requisitions, FY22 to FY26, approval to fill): median 37 days in Operations, 42 to 44 in Finance, Product, Commercial, People and Marketing, 47 in Legal & Compliance and 49 in Technology (filled within 90 days: 97% Operations, 89% Technology). Graduate levels in the US: median 27 to 28 days for fills in September and October, about 36 in other months.

**Checks.** All 91 data tests pass (tests 89 to 91 are new; test 76 now checks only quarters up to the report date). Every reporting view and Custom SQL matches its mart in `check_tsql_in_duckdb.py`; `16_validate_report_calendar.sql` is new (19 checks), and `08` and `14` carry the new expected values below. The generator reproduces the same files run to run.

**Effect on the published dashboards.** Dashboards #1, #2 and #4 are unchanged.

| Dashboard #3 number, FY26 · All organizations | Published (release 3.1) | Release 5 data |
|---|---:|---:|
| PIDs in total, Jun 30, 2026 | 51,163 | 51,170 |
| Vacant, new PIDs | 528 | 535 |
| Median days to fill a backfill | 42 | 43 |
| Net-new approved while a matching PID was vacant | 631 | 640 |
| Vacant, previously held | 8,689 | 8,689 |
| Fills (backfills, net-new) | 4,668 · 2,181 | unchanged | Dashboard #3 reads time to fill, reuse candidates and new-PID vacancy from the moved dates, so its median days to fill and new-PID counts move when it is next re-extracted. Its published extract stays as it is; recheck those numbers when the dashboards move to the Google Drive refresh.
