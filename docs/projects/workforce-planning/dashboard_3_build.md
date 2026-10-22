# Dashboard #3, Workforce Planning: build guide

The as-built guide for the third Arcadia dashboard, written step by step with the value every step must show. It follows Dashboards #1 and #2: the same 1400 × 850 page, the same rail, KPI band, card background and type ramp (Figma file `ecic7dYoG638uJPVjiQtgg`, Sizing & type page), and the same habits (titles state the finding, "drivers" not "steps", every control tested on a picked period). Method and definitions: [workforce_planning.md](workforce_planning.md). Arcadia Systems is fictional and all data is synthetic.

| Step | What | State |
|---|---|---|
| 1 | Headline question and the five KPI cards, with expected values | Agreed 2026-10-18 |
| 2 | Custom SQL, validated on SQL Server before Tableau | Done: 46 of 46 checks PASS on SQL Server (2026-10-18) |
| 3 | Parameters, calculations and sheets, with the expected output of each | Part A (sources, parameters, rail lists, KPI band): section 3. Part B (panels, map, check sheets): next |
| 4 | Layout from the Figma replica, actions and the action audit | |
| 5 | Pre-publish checklist, screenshot, README and profile | |

## Decisions (2026-10-18)

| # | Decision | Why |
|---|---|---|
| D1 | **Executive officers excluded** (department `D-901`, the CEO and eight function heads), in every Dashboard #3 source | The same people on every Arcadia dashboard: FY26 year-end employees are **30,005** on #1, #2 and #3 |
| D2 | **Periods are quarter-end pairs inside one fiscal year**: FY, H1, H2, Q1 to Q4, for FY22 to FY26 | The plan is quarterly; there is no monthly plan to compare with |
| D3 | **A Version toggle** (Budget · RF1 · RF2 · RF3). A reforecast plans only the quarters still ahead (RF1 Q2–Q4, RF2 Q3–Q4, RF3 Q4), so plan **and** actual are counted over the quarters the version plans, and the subtitle names them | Plan and actual always cover the same dates |
| D4 | **No choice can lead to an empty page.** A Period, Version or Group option that has no plan for the other two current choices is drawn greyed out and does nothing when clicked. A View pick lands on that view's largest group | You asked for no blank state; see 2.2 |
| D5 | Card 4 is **net-new seats approved while a matching seat stood empty**; the vacancy pool is a chart | It is the finding unique to this case study |
| D6 | **Layout: the map runs the full content height** (668 × 630, as in the Footprint prototype), with three panels stacked beside it: plan vs actual, seat fills, vacancy pool | You chose the prototype layout |

## 1. The question and the five KPI cards

**Headline question:** *Did hiring follow the plan, and which seats did it fill?*

Page title **Workforce Planning**; dynamic subtitle (a statement, not a question): "Whether hiring followed the FY26 Budget at Arcadia Systems, which seats it filled, and which stand empty · Jun 30, 2025 to Jun 30, 2026".

FY26, Budget, Company (all from `custom_sql_wfp_summary.sql`, one row):

| # | Card title | Value | Note | Fields |
|---|---|---|---|---|
| 1 | Year-end employees | **30,005** | −332 vs plan 30,337 · cost $3,407.5M vs $3,446.5M | `actual_/planned_ending_headcount`, `actual_cost_usd_plan_fx`, `planned_cost_usd` |
| 2 | Net-new seats filled | **79.0%** | 2,181 of 2,762 planned | `actual_/planned_net_new` |
| 3 | Backfills | **92.8%** | 4,668 of 5,031 · median 42 days to fill | `actual_/planned_backfills`, `median_time_to_fill_days` |
| 4 | Net-new while a match stood empty | **628** | 28.8% of net-new · $55.4M starting base pay | `reuse_candidate_fills`, `net_new_fills`, `reuse_new_pay_usd_constant` |
| 5 | Contingent workers | **11,941** | −732 vs plan 12,673 · spend $1,238.7M vs $1,313.9M | `actual_/planned_cw_headcount`, `actual_cw_spend_usd_plan_fx`, `planned_cw_spend_usd` |

The same cards on other choices (use them to test the toggle and the period list):

| Choice | Card 1 | Card 2 | Card 3 | Card 4 | Card 5 |
|---|---|---|---|---|---|
| FY26, RF1 (plans Q2–Q4) | 30,005 vs 30,219 | 83.0% (1,532 / 1,845) | 96.5% (3,639 / 3,772) | 453 | 11,941 vs 12,182 |
| FY26, RF2 (plans Q3–Q4) | 30,005 vs 30,142 | 89.4% (981 / 1,097) | 95.4% (2,408 / 2,524) | 300 | 11,941 vs 12,020 |
| FY26, RF3 (plans Q4) | 30,005 vs 30,086 | 92.9% (510 / 549) | 100.4% (1,207 / 1,202) | 165 | 11,941 vs 11,977 |
| FY26 Q3, Budget | 29,618 vs 30,046 | 83.8% (471 / 562) | 88.6% (1,201 / 1,356) | 135 | 11,277 vs 12,201 |
| FY26, Budget, Function Finance | 1,271 vs 1,308 | 68.0% (83 / 122) | 78.7% (181 / 230) | 13 | 370 vs 408 |
| FY26, Budget, Country India | 6,967 vs 7,056 | 74.4% (418 / 562) | 93.9% (1,047 / 1,115) | 191 | 4,883 vs 5,274 |
| FY24, Budget (the restructuring) | 27,208 vs 28,589 | 32.1% (910 / 2,833) | 91.2% (4,105 / 4,503) | 228 | 9,910 vs 10,746 |

**Main panel headline** (FY26, Budget): "FY26: hiring filled 79% of planned net-new seats and 93% of backfills; employees closed 332 below plan". By quarter, net-new actual / planned: Q1 649 / 832, Q2 551 / 744, Q3 471 / 562, Q4 510 / 624.

Why FY24 Budget planned net-new reads 2,833 here and 2,834 in [workforce_planning.md](workforce_planning.md) section 9: one planned net-new seat sat in the Office of the CEO, which D1 removes.

## 2. Custom SQL, validated on SQL Server

### 2.1 The five data sources

| Data source in Tableau | File (`tableau/`) | Rows | Feeds |
|---|---|---:|---|
| **WFP Summary** (new) | `custom_sql_wfp_summary.sql` | 10,080 | KPI band, page and panel headlines, Period / Version / View / Group lists |
| **Plan vs Actual** | `custom_sql_plan_vs_actual.sql` | 29,365 (was 29,415) | Plan vs actual panel (quarters, functions) |
| **Position Fill** | `custom_sql_position_fill.sql` | 30,575 | Map (offices and routes: each fill row carries the seat's new office and its prior office, so both layers come from one source), seat fills panel |
| **Vacancy Pool** | `custom_sql_vacancy_pool.sql` | 62,055 | Vacancy pool panel |
| **Seat Corridors** | `custom_sql_seat_corridors.sql` | 821 | The `CHK Corridors` sheet only |

What changed in the existing four: `WHERE v.department_id <> 'D-901'` (D1). Plan vs Actual loses its 50 executive-officer rows; the other three have none, and the filter states the rule. Seat Corridors has no department column and no officer rows.

**Why a summary source.** The five KPI cards are text drawn as map layers on **one** sheet (the technique from Dashboard #1), and map layers must share a data source. The summary holds every card's numbers at the grain of the rail's choices, so the band is one query of 10,080 rows. It is also what makes D4 possible: there is a row for every fiscal year × period × version × view × group, with `has_plan` telling the rail what to grey out.

### 2.2 How the summary keeps the page from going empty

| Column | Meaning | Used by |
|---|---|---|
| `is_covered` | The version plans at least one quarter of the period (RF2 + H1: no) | Version toggle, Period list |
| `has_plan` | Covered **and** the group has plan rows there (160 planned combinations are groups not yet open: Data & AI Platform before FY25; Portugal and South Korea before FY24; the Philippines in FY22) | Version toggle, Period list, Group list |
| `covered_label`, `eff_from_date` | Which quarters the numbers cover ("Q3–Q4", Dec 31, 2025) | Subtitles |
| `is_view_default` | Each view's largest group: Arcadia Systems, Technology, Engineering, Core Platform Engineering, United States. It has a plan in every period and version | The View list's action |

The rule in step 3: each list's clickable value is `IF [has_plan for the other two choices] THEN <this option> ELSE <the current value> END`, so a greyed option sets the parameter to what it already is (nothing happens) and its tooltip says why ("RF2 plans Q3–Q4 only. Choose Budget or RF1 for H1.").

### 2.3 Run it on the Mac

Nothing in the warehouse changed (the summary reads the existing `rpt` views), so there is no rebuild. Paste the commands one block at a time; no comments inside them (zsh would run them).

**1. Get the branch.**

```bash
cd ~/GitHub/people-analytics-warehouse
git fetch origin
git checkout dashboard-3-workforce-planning
git pull
```

Expected: `Switched to a new branch 'dashboard-3-workforce-planning'` and `branch 'dashboard-3-workforce-planning' set up to track 'origin/dashboard-3-workforce-planning'`, then `Already up to date.`

**2. Check the container is up.**

```bash
docker compose ps
```

Expected: `arcadia-sql` with status `Up ...` (and `(healthy)` if shown). If it is not listed: `docker compose up -d`, wait 20 seconds, run `docker compose ps` again.

**3. Run the validation script.**

```bash
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/14_validate_workforce_planning_dashboard.sql
```

Expected (seconds will differ; the summary takes the longest, about 10 to 30 seconds on the emulated Mac container):

```
Changed database context to 'ArcadiaHR'.
WFP summary Custom SQL returned 10080 rows in 18 seconds
Plan vs actual Custom SQL returned 29365 rows in 1 seconds
Position fill Custom SQL returned 30575 rows in 1 seconds
1. Shape: one row for every choice on the page
   11 rows, every result PASS (summary rows 10080, distinct keys 10080, fiscal years 5, groups 72,
   rows a version plans 7200, rows with a plan 7040, groups not yet open 160, view defaults without a
   plan 0, executive officers 0, plan vs actual rows 29365, position fill rows 30575)
2. Ties (every check expects 0)
   4 rows, every result PASS
3. KPI cards, FY26 (Jun 25 -> Jun 26), Company
   27 rows, every result PASS (the card values in section 1)
4. Period names (pair_name must read exactly as on the rail)
   4 rows, every result PASS (FY26 · Jun 25 → Jun 26, FY26 H1 · Jun 25 → Dec 25, FY26 Q3 · Dec 25 → Mar 26, Q3–Q4)
```

To see only failures, add `| grep -E "FAIL|Msg"` to the end of the command: **no output** means everything passed.

If section 4 shows `?` instead of `·` or `→`, the terminal is not UTF-8 but the data is fine (Tableau reads it correctly); the four checks still say PASS.

**4. Copy the files for Tableau** (the repo's `tableau/` folder is the source):

```bash
mkdir -p "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning"
cp tableau/custom_sql_wfp_summary.sql tableau/custom_sql_plan_vs_actual.sql tableau/custom_sql_position_fill.sql tableau/custom_sql_vacancy_pool.sql tableau/custom_sql_seat_corridors.sql "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning/"
ls "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning/"
```

Expected: the five file names. (The handoff named this folder `01 Workforce Planning`; if yours has that name, use it in both commands.)

### 2.4 How it was checked before it reached you

| Check | Result |
|---|---|
| `python pipeline/run_pipeline.py` | 80 tests pass, including the new **test 80** (one row per choice, every group in every period, plan actuals = seat fills, groups add up to Company, Company = `mart_plan_vs_actual`, coverage follows the version, view defaults always planned, no executive officers). Run against a deliberately broken copy (a dropped row, a changed count): it caught both |
| `python sqlserver/check_tsql_in_duckdb.py` | The T-SQL summary equals the DuckDB mart `mart_wfp_summary` **row for row (10,080)**, medians and period names included; Plan vs Actual equals the mart without the officers (29,365); `14_validate`: 46 of 46 checks PASS; every other source and script unchanged and matching |
| Existing marts | Not one byte changed (the summary is a new mart beside them) |

Plan actuals equal the seat fills in **every** row of the summary (net-new, backfills, reuse candidates, external + internal), which is what lets card 4 (from fills) sit beside cards 2 and 3 (from the plan).

### 2.5 What the Mac run found

The first run of `14_validate_workforce_planning_dashboard.sql` failed with Msg 130: SQL Server does not allow a subquery inside an aggregate, and the group list had `SUM(CASE … (SELECT MAX(quarter_end_date) …))`. DuckDB accepts it, so the translation check had passed it. The latest quarter-end now comes from a one-row joined table (commit `cd0a3ae`). Second run: **46 of 46 PASS** (10,080 / 29,365 / 30,575 rows; the summary takes 29 seconds, so it is an extract in Tableau). Lesson for the checker: it proves the logic, not every T-SQL restriction, so the SQL Server run stays the final gate.

## 3. Parameters, calculations and sheets (part A)

Part A builds the workbook shell, the parameters, the rail's lists (with the greying that stops an empty page) and the KPI band. Each step says what to see. Part B (plan vs actual panel, seat fills, vacancy pool, map, check sheets) follows once part A matches.

**Field names.** Tableau shows the SQL columns exactly as written, lowercase with underscores: `fiscal_year`, `has_plan`, `actual_cw_spend_usd_plan_fx`. The formulas below use those names, so they paste as they are. Fields you create (`K Close HC`, `Why Off`, `Row Is Current`) keep their capitalised names, and parameters start with `p_`.

### 3.0 The workbook and the five sources

1. **File > New**, then connect to SQL Server as in [tableau_first_sheets_guide.md](tableau_first_sheets_guide.md), section 1 (server `localhost, 1433`, database `ArcadiaHR`, user `sa`, Require SSL unchecked).
2. Drag **New Custom SQL** onto the canvas and paste `custom_sql_wfp_summary.sql` (from the folder you copied in 2.3). Rename the source **WFP Summary**.
3. **Data > New Data Source** for `custom_sql_plan_vs_actual.sql` (**Plan vs Actual**), `custom_sql_position_fill.sql` (**Position Fill**), `custom_sql_vacancy_pool.sql` (**Vacancy Pool**) and `custom_sql_seat_corridors.sql` (**Seat Corridors**).
4. **Extract all five** (Data Source tab > Connection: Extract > Edit > keep defaults). WFP Summary takes about 30 seconds live, and every click on the rail would wait that long. Save as `Arcadia Workforce Planning.twb`.

Expected: on the WFP Summary data source page, **10,080 rows** (View Data shows them); Plan vs Actual 29,365; Position Fill 30,575; Vacancy Pool 62,055; Seat Corridors 821.

**Types (WFP Summary).** Right-click each and choose **Convert to Dimension** (they arrive as measures, with the `#` icon): `fiscal_year`, `pair_order`, `version_order`, `view_order`, `quarters_in_pair`, `eff_first_quarter`, `eff_last_quarter`, `quarters_covered`. They are labels, not amounts. `has_plan`, `is_covered` and `is_view_default` arrive as True/False.

### 3.1 Parameters (all in the workbook, not shown on the dashboard)

| Name | Type | Allowable values | Current | Display as |
|---|---|---|---|---|
| `p_FY` | Integer | List: 2022 to 2026 | 2026 | FY22 … FY26 |
| `p_Period` | String | List: FY, H1, H2, Q1, Q2, Q3, Q4 | FY | Full year, H1, H2, Q1 … Q4 |
| `p_Version` | String | List: Budget, RF1, RF2, RF3 | Budget | same |
| `p_View` | String | List: Company, Function, Sub-function, Department, Country | Company | same |
| `p_Group` | String | **All** | Arcadia Systems | |
| `p_PeriodOpen` | Boolean | | False | |
| `p_GroupOpen` | Boolean | | False | |

`p_Group` must be **All** (not a list): its values change with the view, and a list would reject a group it does not hold (Dashboard #2 learned this with `p_From`/`p_To`). The page cannot reach a bad value anyway, because only options that have data can be clicked.

### 3.2 Calculations every list and card uses (WFP Summary)

```
// Pick Context FY       (the other four choices; the FY list shows only rows that match them)
[pair_code] = [p_Period] AND [version_type] = [p_Version]
AND [view_name] = [p_View] AND [group_name] = [p_Group]

// Pick Context Period
[fiscal_year] = [p_FY] AND [version_type] = [p_Version]
AND [view_name] = [p_View] AND [group_name] = [p_Group]

// Pick Context Version
[fiscal_year] = [p_FY] AND [pair_code] = [p_Period]
AND [view_name] = [p_View] AND [group_name] = [p_Group]

// Pick Context Group
[fiscal_year] = [p_FY] AND [pair_code] = [p_Period]
AND [version_type] = [p_Version] AND [view_name] = [p_View]

// Row Is Current        (all five: exactly one row of the summary; the KPI band and subtitle use it)
[fiscal_year] = [p_FY] AND [pair_code] = [p_Period] AND [version_type] = [p_Version]
AND [view_name] = [p_View] AND [group_name] = [p_Group]
```

What each list sheet shows is therefore the **row for every option of that list, with the other four choices held at their current values**. Because the summary has a row for every combination, that row's `has_plan` already says whether the option leads to data. No lookup, no LOD.

```
// Version Plans         (which quarters each version plans; used in the "why" tooltip)
CASE [version_type] WHEN "Budget" THEN "Q1–Q4" WHEN "RF1" THEN "Q2–Q4"
                    WHEN "RF2" THEN "Q3–Q4" ELSE "Q4" END

// Why Off               (tooltip text of a greyed option; empty when the option works)
IF [has_plan] THEN ""
ELSEIF NOT [is_covered]
THEN [version_type] + " plans " + [Version Plans] + " only, so it has nothing for " + [pair_name] + "."
ELSE [group_name] + " had no plan seats in " + [pair_name] + " (" + [version_type] + ")." END

// Option Color          (one calc per list; see 3.3 for the compared field)
// "off" greyed and unclickable · "current" the active choice · "on" a working choice
```

### 3.3 The rail lists (one sheet each)

All five follow Dashboard #2's `Rail View` pattern, with one difference. Dashboard #2's `Rail View` is a **Text** mark with no Color pill (white words on the dark rail; the active row is shown only by the "›" marker). Here a list must also show an option that cannot be chosen, so each sheet adds one Color pill, the `… State` calc, and nothing else changes:

- **Marks: Text** (Tableau Book, 9, Middle Left on the Text card). **Do not set a font color** there: a fixed font color overrides the Color shelf and the dimming never shows.
- **Format > Shading:** Worksheet and Pane = the dark blue of Dashboard #2's Rail View.
- **Color = the state calc:** **current** and **on** `#FFFFFF`, **off** `#6E7B93` (about 3 to 1 against the navy: clearly dimmer than white, still legible).
- Header hidden, Entire View, tooltip = `<Why Off>` only. Detail = the pick field, `Why Off`, `zzTrue`, `zzFalse`, `Close Panel`.
- Any pick field that returns a number (`FY Pick`) must be a **dimension** (Convert to Dimension); otherwise Detail shows `SUM(...)`.
- Copy `zzTrue`, `zzFalse` and `Close Panel` from Dashboard #2's workbook (Ctrl+C, then Ctrl+V on WFP Summary) so the deselect trick is identical.

| Sheet | Filter (True) | Rows | Text | Color | Pick (Detail; the action uses it) |
|---|---|---|---|---|---|
| `Rail FY` | `Pick Context FY` | `fiscal_year` | `FY Display` | `FY State` | `FY Pick` |
| `Rail Period` | `Pick Context Period` | `pair_order`, `pair_code` | `Period Display` | `Period State` | `Period Pick` |
| `Rail Version` | `Pick Context Version` | `version_order`, `version_type` | `Version Display` | `Version State` | `Version Pick` |
| `Rail View` | `Pick View Rows` (below) | `view_order`, `view_name` | `View Display` | `View State` | `View Pick` |
| `Rail Group` | `Pick Context Group` | `group_name` (sorted by `group_name`) | `Group Display` | `Group State` | `Group Pick` |

`Rail View` shows one row per view: the view's default group (always planned) in the current year, period and version. Its filter is one Boolean calc, `Pick View Rows` = `[fiscal_year] = [p_FY] AND [pair_code] = [p_Period] AND [version_type] = [p_Version] AND [is_view_default]`, set to True. Expected: 5 rows (Company, Function, Sub-function, Department, Country), all "on". Calcs (the first block is complete; the other lists change only the compared field):

```
// FY Display      [fiscal_year_label]  with the marker on the current one
IF [fiscal_year] = [p_FY] THEN "› " + [fiscal_year_label] ELSE [fiscal_year_label] END
// FY State
IF NOT [has_plan] THEN "off" ELSEIF [fiscal_year] = [p_FY] THEN "current" ELSE "on" END
// FY Pick         (a greyed option passes the current value, so a click changes nothing)
IF [has_plan] THEN [fiscal_year] ELSE [p_FY] END
```

```
// Period Label    (the text of the option; the dates are in the tooltip via Pair Name)
CASE [pair_code] WHEN "FY" THEN "Full year" ELSE [pair_code] END
// Period Display / Period State / Period Pick: as FY, comparing [pair_code] with [p_Period]
// Version Display / State / Pick: as FY, comparing [version_type] with [p_Version]; the text is [version_type]
// Group Display / State / Pick: as FY, comparing [group_name] with [p_Group]
// View Display / State: compare [view_name] with [p_View]; View State is never "off"
// View Pick       [view_name]
// View Default Group   (the group a View click lands on: the view's largest, always with a plan)
{ FIXED [view_name] : MAX(IF [is_view_default] THEN [group_name] END) }
```

Put `View Default Group` on `Rail View`'s Detail.

**Actions** need a dashboard (parameter and filter actions do not fire from a worksheet). Build a dashboard `TEST RAIL` with the five lists, `Reset` and the five parameter cards, and add the actions there (Dashboard > Actions > Add Action > Change Parameter; Run on **Select**; Aggregation **None**; clearing the selection **Keep current value**). **Keep `TEST RAIL`**: actions are tied to the dashboard they were built on, so in step 4 it is resized to 1400 × 850 and rearranged into the real dashboard instead of rebuilding the 19 actions. Tested on the Mac 2026-10-22: all rows below pass.

| Name | Source | Target | Field |
|---|---|---|---|
| Set FY | Rail FY | `p_FY` | `FY Pick` |
| Set Period | Rail Period | `p_Period` | `Period Pick` |
| Set Version | Rail Version | `p_Version` | `Version Pick` |
| Set View | Rail View | `p_View` | `View Pick` |
| Set Group on View | Rail View | `p_Group` | `View Default Group` |
| Set Group | Rail Group | `p_Group` | `Group Pick` |

Plus the deselect filter action (`zzTrue` > `zzFalse`, Show all values) on every one of the five sheets, as in Dashboard #2. The two View actions fire together, so the page never sees a view with a group from another view.

**Expected output.** Set the parameters by hand (right-click a parameter > Show Parameter, or edit the current value) to each state below, look at the five sheets and compare. "off" means gray and unclickable.

| # | State (FY · Period · Version · View · Group) | Rail FY | Rail Period | Rail Version | Rail Group |
|---|---|---|---|---|---|
| T1 | FY26 · Full year · Budget · Company · Arcadia Systems | 5 on | 7 on | 4 on | 1 row, on |
| T2 | FY26 · **H1** · Budget · Company | 5 on | 7 on | Budget, RF1 on; **RF2, RF3 off** | 1 |
| T3 | FY26 · Full year · **RF2** · Company | 5 on | FY, H2, Q3, Q4 on; **H1, Q1, Q2 off** | 4 on | 1 |
| T4 | **FY22** · Full year · Budget · **Country** · United States | 5 on | 7 on | 4 on | 22 rows: 19 on; **Philippines, Portugal, South Korea off** |
| T5 | **FY23** · H2 · **RF1** · **Department** · Core Platform Engineering | 5 on | **Q1 off**, six on | 4 on | 31 rows: 30 on; **Data & AI Platform off** |

Tooltip checks (hover the greyed option, read the whole tooltip):

| Hover | Must read |
|---|---|
| T2, RF2 | RF2 plans Q3–Q4 only, so it has nothing for FY26 H1 · Jun 25 → Dec 25. |
| T3, H1 | RF2 plans Q3–Q4 only, so it has nothing for FY26 H1 · Jun 25 → Dec 25. |
| T4, Portugal | Portugal had no plan seats in FY22 · Jun 21 → Jun 22 (Budget). |

(The label starts at the quarter-end before the first quarter of the fiscal year, so FY22 reads Jun 21 → Jun 22.)

Then click test (every click, then **Reset the parameters to T1**): in T1 click **FY24** on Rail FY → p_FY = 2024, the card values change in 3.5. Click **Country** on Rail View → p_View = Country and p_Group = United States in one click. In T4, click the greyed **Portugal**: nothing changes (p_Group still United States). Click **RF2** in T2: nothing changes. These four are the whole "no empty page" promise.

### 3.4 Reset

`Reset` is the Dashboard #2 sheet with new defaults and the same Change Parameter pattern ([rail_controls_build.md](../compensation-walk/rail_controls_build.md), Part 3):

| Calc | Formula | Target parameter |
|---|---|---|
| `Default FY` | `2026` | `p_FY` |
| `Default Period` | `"FY"` | `p_Period` |
| `Default Version` | `"Budget"` | `p_Version` |
| `Default View` | `"Company"` | `p_View` |
| `Default Group` | `"Arcadia Systems"` | `p_Group` |
| `Close Panel` | `FALSE` | `p_PeriodOpen`, `p_GroupOpen` |

Expected: from any state, one click returns to T1.

### 3.5 The KPI band (one sheet, on WFP Summary)

**Method.** Copy the geometry from Dashboard #2 instead of rebuilding it. In the Dashboard #2 workbook select the 16 `kpi_` parameters' dependent calcs (`kpi_lat Title/Value/Sub`, `kpi_lon C1`–`C5`, `kpi_pt Title/Value/Note 1`–`5`, `kpi_Corner TL/BR`) in the Data pane and press Ctrl+C; in this workbook select **WFP Summary** and press Ctrl+V. Tableau recreates the `kpi_` parameters they use. If any calc shows a red exclamation mark, create the 16 parameters from the Parameters tab of `Arcadia_KPI_Cards_Config.xlsx` (same names, same defaults) and the calcs resolve. The sheet size is the same, 1400 × 110, floated at x 0, y 78, so the geometry and calibration (`kpi_FitX/Y`) carry over unchanged.

**The numbers** (aggregates over the single row `Row Is Current` leaves; every `SUM` here is a sum of one value). Build the sheet `KPI Cards` and put **`Row Is Current` = True** on Filters first.

```
// K Close HC        SUM([actual_ending_headcount])
// K Plan HC         SUM([planned_ending_headcount])
// K HC Gap          [K Close HC] - [K Plan HC]
// K Cost Gap Pct    IF SUM([planned_cost_usd]) = 0 THEN NULL
//                   ELSE (SUM([actual_cost_usd_plan_fx]) - SUM([planned_cost_usd])) / SUM([planned_cost_usd]) END
// K NN Done         SUM([actual_net_new])
// K NN Plan         SUM([planned_net_new])
// K NN Pct          IF [K NN Plan] = 0 THEN NULL ELSE [K NN Done] / [K NN Plan] END
// K BF Done         SUM([actual_backfills])
// K BF Plan         SUM([planned_backfills])
// K BF Pct          IF [K BF Plan] = 0 THEN NULL ELSE [K BF Done] / [K BF Plan] END
// K Days            SUM([median_time_to_fill_days])      (NULL when nothing was filled)
// K Reuse           SUM([reuse_candidate_fills])
// K NN Fills        SUM([net_new_fills])
// K Reuse Pct       IF [K NN Fills] = 0 THEN NULL ELSE [K Reuse] / [K NN Fills] END
// K Reuse Pay       SUM([reuse_new_pay_usd_constant])
// K CW Done         SUM([actual_cw_headcount])
// K CW Plan         SUM([planned_cw_headcount])
// K CW Gap          [K CW Done] - [K CW Plan]
// K CW Spend Pct    IF SUM([planned_cw_spend_usd]) = 0 THEN NULL
//                   ELSE (SUM([actual_cw_spend_usd_plan_fx]) - SUM([planned_cw_spend_usd])) / SUM([planned_cw_spend_usd]) END
```

**Check before any text:** drag `K Close HC`, `K Plan HC`, `K NN Done`, `K NN Plan`, `K BF Done`, `K BF Plan`, `K Reuse`, `K CW Done`, `K CW Plan` onto Text of a plain text table. In T1 it must read **30,005 · 30,337 · 2,181 · 2,762 · 4,668 · 5,031 · 628 · 11,941 · 12,673** (these are the Section 1 numbers; the 46 SQL checks already prove them). Not 3,000,500 or any multiple: that means the `Row Is Current` filter is missing.

**Strings.** Same two patterns as Dashboard #2 (the comma pattern for counts, the percent pattern for rates), plus one for money. Tableau has no number-format function, so each is whole-number math: `DIV` is integer division, `%` is the remainder. Helpers first:

```
// K Cost T          cost in tenths of a million: 3,407,541,370 -> 34075
INT(ROUND(SUM([actual_cost_usd_plan_fx]) / 100000, 0))
// K Cost Plan T     INT(ROUND(SUM([planned_cost_usd]) / 100000, 0))
// K Reuse Pay T     INT(ROUND([K Reuse Pay] / 100000, 0))
// K CW Spend T      INT(ROUND(SUM([actual_cw_spend_usd_plan_fx]) / 100000, 0))
// K CW Spend Plan T INT(ROUND(SUM([planned_cw_spend_usd]) / 100000, 0))
```

```
// Money pattern, shown for K Cost T (copy it for the other four, replacing the field)
// K Cost Str        34075 -> "$3,407.5M"
"$" + IF DIV([K Cost T], 10) >= 1000
      THEN STR(DIV([K Cost T], 10000)) + "," + RIGHT("00" + STR(DIV([K Cost T], 10) % 1000), 3)
      ELSE STR(DIV([K Cost T], 10)) END
    + "." + STR([K Cost T] % 10) + "M"
```
Copies: `K Cost Plan Str` (from `K Cost Plan T`), `K Reuse Pay Str`, `K CW Spend Str`, `K CW Spend Plan Str`.

```
// Comma pattern, signed gap (K HC Gap Str; copy for K CW Gap Str with [K CW Gap])
(IF [K HC Gap] > 0 THEN "+" ELSEIF [K HC Gap] < 0 THEN "−" ELSE "" END)
+ IF ABS([K HC Gap]) >= 1000
  THEN STR(DIV(ABS([K HC Gap]), 1000)) + "," + RIGHT("00" + STR(ABS([K HC Gap]) % 1000), 3)
  ELSE STR(ABS([K HC Gap])) END

// Comma pattern, plain count (K Plan HC Str; copy for K CW Plan Str, K NN Plan Str, K NN Done Str, K BF Plan Str, K BF Done Str)
IF [K Plan HC] >= 1000
THEN STR(DIV([K Plan HC], 1000)) + "," + RIGHT("00" + STR([K Plan HC] % 1000), 3)
ELSE STR([K Plan HC]) END

// Percent pattern (K NN Pct Str; copy for K BF Pct Str and K Reuse Pct Str)
IF ISNULL([K NN Pct]) THEN "—"
ELSE STR(DIV(INT(ROUND([K NN Pct] * 1000, 0)), 10)) + "." + STR(INT(ROUND([K NN Pct] * 1000, 0)) % 10) + "%" END

// Signed percent for the cost and spend variance (K Cost Gap Str; copy for K CW Spend Gap Str with [K CW Spend Pct])
IF ISNULL([K Cost Gap Pct]) THEN "—" ELSE
  (IF INT(ROUND(ABS([K Cost Gap Pct]) * 1000, 0)) = 0 THEN ""
   ELSEIF [K Cost Gap Pct] > 0 THEN "+" ELSE "−" END)
  + STR(DIV(INT(ROUND(ABS([K Cost Gap Pct]) * 1000, 0)), 10)) + "."
  + STR(INT(ROUND(ABS([K Cost Gap Pct]) * 1000, 0)) % 10) + "%" END
```

The sign test uses the **rounded** number, so a −0.04% change reads "0.0%", never "−0.0%".

Cards (values, notes, titles; value and note are what the Label shelf holds):

| Card | `KPI n Title` | `KPI n Value` | `KPI n Note` |
|---|---|---|---|
| 1 | `IF [pair_code] = "FY" THEN "Year-end employees" ELSE "Employees at period end" END` (use `MIN([pair_code])`) | the comma pattern on `K Close HC` | `[K HC Gap Str] + " vs plan " + [K Plan HC Str] + " · cost " + [K Cost Str] + " vs " + [K Cost Plan Str]` |
| 2 | `"Net-new seats filled"` | `K NN Pct Str` | `[K NN Done Str] + " of " + [K NN Plan Str] + " planned"` |
| 3 | `"Backfills"` | `K BF Pct Str` | `[K BF Done Str] + " of " + [K BF Plan Str] + " · median " + IF ISNULL([K Days]) THEN "—" ELSE STR(INT(ROUND([K Days], 0))) END + " days to fill"` |
| 4 | `"Net-new while a match stood empty"` | the comma pattern on `K Reuse` | `[K Reuse Pct Str] + " of net-new · " + [K Reuse Pay Str] + " starting base pay"` |
| 5 | `"Contingent workers"` | the comma pattern on `K CW Done` | `[K CW Gap Str] + " vs plan " + [K CW Plan Str] + " · spend " + [K CW Spend Str] + " vs " + [K CW Spend Plan Str]` |

Cards 1 and 5 are the long notes agreed in step 1 (50 characters). At 9 pt Tableau Book a card note holds about 44 characters in 228 px, so those two may clip. Build the long note now and the short form beside it (`KPI 1 Note Short` = `[K HC Gap Str] + " vs plan " + [K Plan HC Str] + " · cost " + [K Cost Gap Str]`, and the same for card 5 with `K CW Spend Gap Str` and "spend"). Section 4 puts the sheet on the page at its real width and keeps whichever fits. A one-row check on Tableau Public happens in step 5 either way.

**Layers.** Build the 15 text layers and the two corner points exactly as in [tableau_kpi_cards_guide.md](../headcount-fte-walk/tableau_kpi_cards_guide.md), section 5 (circle at 0% opacity, nothing else on the layer's Marks card, Label Right/Middle, same fonts), pointing each layer's Label at the `KPI n Title`/`Value`/`Note` fields above. The sheet is calibrated on the dashboard, not here.

**Expected output**, T1 (FY26 · Full year · Budget · Company):

| Card | Title | Value | Note (long) | Note (short) |
|---|---|---|---|---|
| 1 | Year-end employees | 30,005 | −332 vs plan 30,337 · cost $3,407.5M vs $3,446.5M | −332 vs plan 30,337 · cost −1.1% |
| 2 | Net-new seats filled | 79.0% | 2,181 of 2,762 planned | |
| 3 | Backfills | 92.8% | 4,668 of 5,031 · median 42 days to fill | |
| 4 | Net-new while a match stood empty | 628 | 28.8% of net-new · $55.4M starting base pay | |
| 5 | Contingent workers | 11,941 | −732 vs plan 12,673 · spend $1,238.7M vs $1,313.9M | −732 vs plan 12,673 · spend −5.7% |

More states to test against the same sheet (values from Section 1; open the parameters and set them by hand):

| State | Card 1 value / note | Card 2 | Card 3 | Card 4 | Card 5 value / note |
|---|---|---|---|---|---|
| FY26 · RF1 | 30,005 · −214 vs plan 30,219 | 83.0% · 1,532 of 1,845 planned | 96.5% · 3,639 of 3,772 | 453 | 11,941 · −241 vs plan 12,182 |
| FY26 · RF3 | 30,005 · −81 vs plan 30,086 | 92.9% · 510 of 549 planned | **100.4%** · 1,207 of 1,202 | 165 | 11,941 · −36 vs plan 11,977 |
| FY26 · Q3 | "Employees at period end" 29,618 · −428 vs plan 30,046 | 83.8% · 471 of 562 | 88.6% · 1,201 of 1,356 | 135 | 11,277 · −924 vs plan 12,201 |
| FY26 · Function Finance | 1,271 · −37 vs plan 1,308 | 68.0% · 83 of 122 planned | 78.7% · 181 of 230 | 13 | 370 · −38 vs plan 408 |
| FY24 · Budget | 27,208 · −1,381 vs plan 28,589 | 32.1% · 910 of 2,833 planned | 91.2% · 4,105 of 4,503 | 228 | 9,910 · −836 vs plan 10,746 |

(The RF1 and RF3 gaps are the difference of the two numbers in Section 1; the 100.4% on RF3 backfills is correct: hiring filled 1,207 against a plan of 1,202. A percentage above 100 must print as `100.4%`, which is why the percent pattern uses `DIV` and not a fixed width.)

The empty-denominator states: 30 planned combinations have no planned net-new, 41 no planned backfills and 68 no median. Two reachable ones: **FY26 · Q3 · Budget · Country · Switzerland** has 0 planned net-new seats and 1 filled, so card 2 must read **"—"** with the note "1 of 0 planned"; **FY24 · Full year · Budget · Country · South Korea** has no backfill fills with a time to fill, so card 3's note must read "median — days to fill" (2 backfills planned, 0 filled). Neither may show an error or `NaN`.

### 3.6 The page title and subtitle

The title is the static text **Workforce Planning**. The subtitle is one calc on `KPI Cards`'s data source (put it in a text-only sheet `Page Subtitle`, filter `Row Is Current` = True, as Dashboard #2 does):

```
// From Text / To Text   (Eff From Date and To Date as "Jun 30, 2025")
LEFT(DATENAME('month', MIN([eff_from_date])), 3) + " " + STR(DAY(MIN([eff_from_date]))) + ", " + STR(YEAR(MIN([eff_from_date])))
LEFT(DATENAME('month', MIN([to_date])), 3) + " " + STR(DAY(MIN([to_date]))) + ", " + STR(YEAR(MIN([to_date])))

// Page Subtitle
"Whether hiring followed the " + MIN([fiscal_year_label]) + " " + MIN([version_type])
+ IF MIN([covered_label]) = "Q1–Q4" THEN "" ELSE ", covering " + MIN([covered_label]) END
+ IF MIN([view_name]) = "Company" THEN " at Arcadia Systems" ELSE " in " + MIN([group_name]) END
+ ", which seats it filled, and which stand empty · " + [From Text] + " to " + [To Text]
```

Expected: T1 reads **"Whether hiring followed the FY26 Budget at Arcadia Systems, which seats it filled, and which stand empty · Jun 30, 2025 to Jun 30, 2026"**. FY26 · RF2 · Function · Finance reads "Whether hiring followed the FY26 RF2, covering Q3–Q4 in Finance, which seats it filled, and which stand empty · Dec 31, 2025 to Jun 30, 2026".

### 3.7 When part A matches

Send me: the five rail sheets in states T2, T4 and T5 (a screenshot of each), and the KPI sheet text table (or the band on the page) in T1, RF3 and the Switzerland state. I measure the numbers against the tables above. Then part B: the plan vs actual panel, seat fills, vacancy pool, the map, and refreshing the `CHK` sheets with the release 3 numbers.
