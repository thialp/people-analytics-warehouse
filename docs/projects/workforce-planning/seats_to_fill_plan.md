# Seats to Fill: plan (Dashboard #5)

Case study 5 in the README · Dashboard #5 · warehouse release 5. Arcadia Systems is fictional and all data is synthetic.

**Seats to Fill** · *FTE hiring forecast against plan*. Tableau Public title: "Seats to Fill: Hiring Forecast | Arcadia Systems"; the description starts with "Workforce forecasting:", and the tags are forecasting, workforce planning, survival analysis, Python, HR analytics.

**Page question:** *How many PIDs will we need to fill in the forward year, how many will still be vacant at each quarter-end, and can we trust the forecast?*

| Revision | Date | What changed |
|---|---|---|
| 1 | 2026-10-27 | Proposal agreed (sections 1 to 5). Phase 1 built: the report calendar, the forward budget, time-to-fill variation (section 6) |
| 3 | 2026-10-27 | Phase 3 built: the forecast tables on SQL Server (`02b`, `03e`, schema `fc`), the page's one Custom SQL `tableau/custom_sql_seats_to_fill.sql` (six row types, 542,701 rows), `17_validate_seats_to_fill.sql` (section 7) |
| 5 | 2026-10-27 | Phase 6 started: the build guide [seats_to_fill_build.md](seats_to_fill_build.md); the Custom SQL gains 94 `Scaffold` rows (chart positions for the main chart, the bridge and the quota bar; seven row types, 542,795 rows); a Period capsule (the forward year or one quarter, B7) |
| 4 | 2026-10-27 | Phases 4 and 5: spikes passed (section 8); prototype Option B approved and check tables written (section 9). Central numbers are now the **average** of the draws (D11), and the backtest range under a selection carries the draws' shared shock (D9) |
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
| D9 | The backtest follows the rail selection: per cell a mean and a variance, plus each quarter's **shared cv** (the company-wide shocks every draw applies to all cells), so the range is Σ mean ± 1.2816 × √(Σ variance + (shared cv × Σ mean)²) | Same scope as the rest of the page. Variances alone treat cells as independent and give ranges about a third as wide as the draws' (method, section 4) |
| D11 | **Central numbers are the average of the 100 draws**; ranges stay P10 to P90 | Averages add up: quarters to the year, functions to the company, and the seat bridge closes exactly (902 + 4,391 + 1,552 + 828 = 7,672; − 6,891 = 781). Medians leave gaps |
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

## 3. The page (approved prototype, Option B revised)

1400 × 850, the Arcadia rail on the left. Prototype: the Design canvas "Seats to Fill prototype", row "Option B, revised".

| Where | What | Hover |
|---|---|---|
| Hero card (navy, two columns wide) | PIDs filled in the forward year: average, likely range, attainment of the forward Budget and the current year for comparison; a quota bar with the five bands, the forecast as a tick and its range as a bracket | Text: one editorial sentence, then the range and the current year |
| KPI 1 | PIDs to fill in FY## (label from the calendar): average, range, waiting today | Text: what the PIDs to fill are made of |
| KPI 2 | Vacant at the forward year's end: average, range, change against today | **The seat bridge** (viz in tooltip): waiting + backfills + net-new + immediate refills = to fill; − filled = vacant |
| KPI 3 | Median wait to fill (last four quarters) and the share filled within 90 days | Text: median, 90 days, the senior levels |
| Main card | Quarters: 20 of history and 4 forecast; fills as a line, the forecast dashed with its fan (P10 to P90), the budget as a dashed step; fiscal years as bands with their attainment chip; a "data ends, forecast starts" marker. Title states the pace in words | Text per quarter: filled against budget, or the forecast with its range |
| Right, top (no card background, navy rule) | How fast PIDs fill: Kaplan–Meier by level band, 30/60/90-day marks; the legend names the levels (L1–L2 Associate, L3–L4 Senior, L5–L6 Manager, L7+ Director) | Text: the share at that day and the band's median |
| Right, bottom (no card background) | Can we trust it: the backtest, range against actual, eight quarters, in-range count and average error | Text: origin, range, actual |

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
| 3 | SQL Server twin, Custom SQL, validate script; run on the Mac | Claude, then Thiago | **Done**: Mac run passed (542,701 rows) |
| 4 | Spikes on Tableau Public (cascade, draws, Kaplan–Meier table calc) | Claude writes, Thiago runs | **Passed** 2026-10-27, no fallback needed (section 8) |
| 5 | Check tables and a prototype with real numbers | Claude, Thiago approves | **Done** 2026-10-27: Option B approved (section 9); [seats_to_fill_check_tables.md](seats_to_fill_check_tables.md) |
| 6 | Build guide, then the build in Tableau | Claude, Thiago | **Guide written** 2026-10-27; the build next, written into the workbook in stages |
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

## 7. Phase 3: SQL Server and the Custom SQL

The forecast runs in Python on the DuckDB warehouse; SQL Server receives its tables like any other source.

| File | What it does |
|---|---|
| `sqlserver/make_load_forecast.py` | Generates the two scripts below from the forecast tables, so they stay in step |
| `sqlserver/02b_load_forecast.sql` | Lands the eight forecast CSVs from `data/marts/` into `raw` as text (BULK INSERT) |
| `sqlserver/03e_build_dw_forecast.sql` | Types them into schema `fc`, with `fc.report_calendar` and `fc.report_quarter` |
| `tableau/custom_sql_seats_to_fill.sql` | The page's one data source: six row types (Quarter 21,720 · Draw 396,400 · Survival 105,294 · Backtest 19,219 · Accuracy 20 · CW budget 48), department, office and calendar labels on every row; `quarter_months_label` carries the en dash ("Jul – Sep 26") |
| `sqlserver/17_validate_seats_to_fill.sql` | Runs the Custom SQL as Tableau does and checks 22 values: rows by type, FY26 fills 6,849, 902 waiting, the FY27 plan 7,709, the median draw 6,838, survival and backtest totals, 6 of 8 in the draws' P10 to P90 and 7 of 8 in the page's range, the FY26 Q4 range rebuilt from the backtest rows (1,573 to 1,739), 13,097 planned contractors |

`check_tsql_in_duckdb.py` builds `fc` from the CSVs, compares every row type of the Custom SQL with its forecast table (all six MATCH) and runs 17 (19 of 19 PASS).

**On the Mac, after the merge:**

```bash
cd ~/GitHub/people-analytics-warehouse && git checkout main && git pull && git fetch --prune
docker compose up -d && docker compose logs --since 1m -f build
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker exec arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/17_validate_seats_to_fill.sql | grep -E "returned|FAIL|Msg"
D="$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/5 Seats to Fill"
mkdir -p "$D" && cp tableau/custom_sql_seats_to_fill.sql "$D/" && ls "$D"
```

Expected: the build ends with `arcadia-build exited with code 0` and no `FAIL` or `Msg`; the validate prints only `Seats to Fill Custom SQL returned 542701 rows in N seconds`; the folder lists `custom_sql_seats_to_fill.sql`.

## 8. Phase 4: spike results

Run on 2026-10-27 in Tableau Desktop 2026.2.3, then on Tableau Public ([D5 Spikes](https://public.tableau.com/app/profile/thialp/viz/D5Spikes/Spikes)), with the guide's expected values: [seats_to_fill_spikes.md](seats_to_fill_spikes.md).

| Spike | Result | What was seen |
|---|---|---|
| S1 Function > Department | Pass | One click on a function updates `p_Functions` and cleans `p_DeptOff` (`REGEXP_REPLACE`) together. Aggregated pick fields drive parameter actions. People without Talent Acquisition: 175 · 21. The last ticked department locks; empty options dim |
| S2 Region > Country > Office | Pass | Two-level clean-up works. Asia Pacific 2,025 · 280; without Pune 1,825 · 246; Portugal dims under Finance; Legal & Compliance in Latin America 7 · 2 |
| S3 Range across draws | Pass | `PERCENTILE({INCLUDE [draw]: ...})` matches to the decimal: all 6,300.7 · 6,838.5 · 7,542.9; Asia Pacific without Pune 1,716.0 · 1,846.5 · 2,024.7 |
| S4 Survival curve | Pass | The table calculation matches by level band exactly (L1–L2 38.1 / 87.7 / 97.4 … L7+ 0.0 / 27.3 / 54.5) and follows every list click |
| S5 Tableau Public | Pass | Published as an extract (542,701 rows); the page and every click responded in normal time |

**Decisions carried into the build:**
- The cascade, the 100 draws and the Kaplan–Meier table calculation go into the page as designed. None of the fallbacks is needed.
- Every "dim" test is wrapped in `ZN()`: an option with nothing behind it sums to NULL, not 0, and would otherwise never dim. The spike guide is corrected.
- Tick shapes need a fixed size: with entire-view sizing they grow as the list shortens.
- The all-levels readings table drew no values without a partitioning dimension; the page reads the curve from one table calculation with a dimension on Rows, as the by-band table did.

## 9. Phase 5: the prototype and the check tables

**Prototype.** A Design canvas with four directions (A classic, B bento hero, C quota board, D editorial headline), researched against Viz of the Day and current dashboard practice: one clear finding, rounded cards (native in Tableau 2026.1), a size hierarchy, muted colour with one accent. **Option B was chosen and revised** (2026-10-27):
- the seat bridge card is removed; the bridge becomes the hover of the vacant card, and the two remaining right panels get the space;
- every other hover is text, written like D's headline;
- KPI 1 reads "PIDs to fill in FY27"; KPI 3 shows only the share within 90 days;
- the survival legend names the levels; the right panels lose their card background (D's navy rule).

Boards on the canvas: all of Arcadia, Technology selected, Asia Pacific selected, the vacant card's hover, and the hover text sheet.

**Check tables.** [seats_to_fill_check_tables.md](seats_to_fill_check_tables.md), generated by `forecast/check_tables.py` from the marts: the KPI band, the bridge, the fiscal-year chips, the main chart, time to fill and the backtest, for six selections (all; Technology; People without Talent Acquisition; Asia Pacific; Asia Pacific without Pune; Legal & Compliance in Latin America).

**Found while building the prototype:**
- **Averages, not medians** (D11), so the bridge reconciles.
- **The backtest range under a selection** (D9): summing cell variances gave ranges a third as wide as the draws' and 3 of 8 in range. Each backtest row now carries the shared cv; the page's range holds **7 of 8** for the company (3.6% average error), Technology 6 of 8, Asia Pacific 7 of 8. Test f06 ties the formula to the draws.
- **New offices:** Pune opened on Jul 1, 2024, so the first backtest has no forecast for it (Asia Pacific without Pune shows the same FY25 Q1 range as Asia Pacific). Written into the method's limits.
- **Small selections:** a range never goes below zero.
- **Small selections (levels):** L7+ has few PIDs under most selections (none for People without Talent Acquisition); the page shows the band only when it has PIDs at risk, and its hover says "few PIDs" under 20.
