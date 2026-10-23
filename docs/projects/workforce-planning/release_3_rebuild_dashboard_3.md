# Release 3 build plan: Dashboard #3, Workforce Planning (seats, not people)

This is the complete plan for the third Arcadia dashboard, from the data to the published page. It replaces the step-by-step build in [dashboard_3_build.md](dashboard_3_build.md), which stays only as history. It reuses what already works on Dashboard #1 (Headcount & FTE Walk): the top bar, popovers, KPI hovers, info panel, grid and type rules. From Dashboard #2 (Compensation Walk) it reuses the period grid, the map technique and the title rules. Arcadia Systems is fictional and all data is synthetic.

Companion guides, referred to as **G1** and **G2**: [Dashboard #1 rebuild](../headcount-fte-walk/release_3_rebuild_dashboard_1.md) and [Dashboard #2 rebuild](../compensation-walk/release_3_rebuild_dashboard_2.md). Method and definitions: [workforce_planning.md](workforce_planning.md).

![Design mock, default state](../../images/workforce_planning_mock.png)

*Design mock at the default state (FY26 · All organizations). Every number comes from the release 3 data. File: `docs/brand/build/d3_page_preview.html`.*

**Revision 2 (2026-10-23), after review:** the plan-version toggle is removed and the plan is the budget. The map is the main card again, now defined as seat movement (section 1). "Vacant" replaces open/frozen. Reset is the arrow icon. Card 5 is vacant seats.

## Contents

0. Seats vs people: the principle
1. The story
2. Decisions
3. Data
4. Shapes
5. Workbook and data sources
6. Parameters
7. Calculations
8. Top bar
9. Popovers
10. KPI band and hovers
11. The four cards
12. Dashboard layout
13. Actions (complete list)
14. Check tables
15. Click tests
16. Publish
17. Who does what, in what order

---

## 0. Seats vs people: the principle

Workforce planning has two ledgers, often called **seats vs butts**:

| | Seats (positions, PIDs) | People ("butts in seats") |
|---|---|---|
| What it is | A budgeted place for one person: department, cost center, office, job, grade | A worker, with a hire date, an exit date and moves in between |
| Who approves it | The plan (Finance) | Recruiting and the manager |
| Headcount | Filled seats | People at month-end |
| Changes when | A seat is created, re-graded, relocated, frozen or eliminated | A person is hired, moves, is promoted or leaves |

The two always agree on how many seats are filled (test 45: filled seats = month-end headcount, same people, every month). They disagree on *where things moved*. That is the point of this dashboard:

- **Every hire fills a seat.** It is either a **net-new seat**, created because the plan added growth, or a **vacant seat**: someone left (voluntarily, involuntarily, or by moving to another seat) and the seat is filled back. The second kind is a **backfill**.
- **A backfill can change the seat.** The seat can come back one grade lower or higher, or **in another office**.

  *Example:* someone in Austin resigns. The seat they held (PID P-…) stays vacant, then Recruiting fills it with a new hire in Chicago. The person did not move; **the seat moved from Austin to Chicago**.
- **Net-new seats have no "from".** They did not exist before, so they never appear on the map.

**How this differs from the Compensation Walk's map.** That map follows **people**: an employee changes office and their pay moves with them. This map follows **seats**: it compares where the person who left sat with where the person who refilled the seat sits. It is the same PID with a different occupant and a different office. On `Position Fill` that is `prior_office_name` (the office of the seat's previous holder) → `office_name` (the office of the new holder), for backfills only.

---

## 1. The story

**Page question:** *Where did hiring go: which seats were refilled, which were new, and what is still vacant?*

Read left to right, top to bottom:

| Where | Question | Default (FY26 · All organizations) |
|---|---|---|
| Header | Which dates? | **Workforce Planning** · "Opening Jun 30, 2025 → Closing Jun 30, 2026" (the same line as #1) |
| KPI 1 | How many people did we end with, against the plan? | **30,005** Employees · −332 vs plan 30,337 |
| KPI 2 | How many vacant seats did we fill back? | **4,668** Backfilled seats · 92.8% of plan · median 42 days to fill |
| KPI 3 | How many of them came back in another office? | **467** Backfills in a new office · 10.0% of backfills · 280 to lower pay |
| KPI 4 | How much growth did we add? | **2,181** Net-new seats · 79.0% of plan · 628 with a vacant match |
| KPI 5 | What is still vacant? | **977** Vacant seats · 213 vacant over 90 days |
| **Main card**, left, full height | Where did backfilled seats move? | "467 backfilled seats were refilled in a different office". The map (old office → new office), then the five busiest seat routes |
| Right, top | What else changed when a seat was refilled? | "1,208 of 4,668 backfills changed level or office". Same / one level down / one level up / moved office, with the pay change: new people earn $7.0M a year less than those who left |
| Right, middle | Where did the growth seats go? | "2,181 net-new seats filled, 79.0% of plan". Filled vs planned by function, one level below the selection; 628 approved while a matching seat was vacant |
| Right, bottom | How long have the vacant seats waited? | "977 seats are vacant; 213 for over 90 days". By time vacant on the closing date |

The KPI band follows the page: cards 1–3 sit over the map (people, backfills, backfills that moved) and cards 4–5 sit over the right column (net-new, vacant). The vacant card is a "where we stand today" closer. It can be dropped without breaking the story, but it opens the best discussion: *how many seats do we still need to fill, and are we approving new seats while old ones wait?*

**The plan is one number per card.** The budget approved before each fiscal year is "the plan". It appears only as "vs plan" or "% of plan" (KPIs 1, 2 and 4, and the net-new bars), so a screenshot reads without knowing about versions. The reforecasts stay in the warehouse and in the case study write-up.

---

## 2. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | Executive officers excluded (department `D-901`) | The same people on every Arcadia dashboard: 30,005 FY26 year-end employees on #1, #2 and #3 |
| D2 | Periods are quarter-end pairs inside one fiscal year: Fiscal year (5), Half year (10), Quarter (20) | The plan is quarterly and set per fiscal year. A pair that crosses fiscal years has no single plan |
| D3 | **No version choice. Plan = Budget**, filtered in the data source | Tableau Public visitors want the answer, not the reconciliation of four plans. The page reads from a screenshot |
| D4 | **No click leads to an empty page**: a period or group with no plan is drawn dim, and clicking it does nothing | Only groups not yet open are affected (Philippines FY22; Portugal and South Korea FY22–23; Data & AI Platform FY22–24) |
| D5 | A View pick lands on the view's **first group alphabetically**, as on #1 and #2 | Checked: Australia, Accounting & Controllership, Commercial and Client Services have a plan in every period |
| D6 | **"Vacant"** for a seat with no one in it; no open/frozen split anywhere on the page | Your wording; simpler. The 90-day threshold stays: vacant over 90 days is "stale" |
| D7 | Card 5 is **Vacant seats** | Agreed |
| D8 | The **map is the main card** (797 × 624, left), seat moves only, teal only | Section 0 |
| D9 | Reset is the **arrow icon** (`btn_reset_top`, now `d3_reset`), 32 × 32, next to ⓘ | Agreed |
| D10 | Colour: navy for the measure the title is about, slate `#8C9BB0` as comparator, light `#D5DBE4` for plan, teal `#00938D` only on the map card. Never blue with orange | The quiet look you liked |
| D11 | Card titles are **sheet titles from FIXED calcs** (one value per sheet), not separate title sheets | Fewer sheets and actions; a FIXED value never shows `*` |
| D12 | **A new workbook**; the first one is archived | Clean action list, no leftovers |

---

## 3. Data

### 3.1 Sources

| Data source | File (`tableau/`) | Rows | Data source filter | Feeds |
|---|---|---:|---|---|
| **WFP Summary** | `custom_sql_wfp_summary.sql` (**edited**, 3.2) | 10,080 → 2,520 | `version_type` = Budget | KPI band and hovers, header, Period and View pickers, Reset |
| **Plan vs Actual** | `custom_sql_plan_vs_actual.sql` (unchanged) | 29,365 → 11,740 | `version_type` = Budget | Net-new card |
| **Position Fill** | `custom_sql_position_fill.sql` (unchanged) | 30,575 | none | Main card (map, routes), backfill card |
| **Vacancy Pool** | `custom_sql_vacancy_pool.sql` (unchanged) | 62,055 | none | Vacant card |

The summary keeps its four versions in SQL (the case study uses them); the workbook filters to Budget once, at the source. Every sheet then sees one plan.

### 3.2 WFP Summary: new columns (same 10,080 rows)

| Column | Example | Used by |
|---|---|---|
| `span_name`, `span_order` | `Quarter`, 3 | Period popover, span list |
| `period_short` | `FY26 Q3` | Period grid, line 1 |
| `period_dates` | `Dec 25 → Mar 26` | Period grid, line 2 |
| `vacant_seats` | 977 | KPI 5 |
| `vacant_stale` | 213 (vacant over 90 days) | KPI 5 |
| `moved_seats` | 467 (backfills whose seat changed office in the period) | KPI 3 |
| `moved_lower_pay` | 280 (of those, to a lower pay range: `location_effect_usd_constant` < 0) | KPI 3 |
| `is_view_default` | **changed**: the view's first group alphabetically (D5) | View list |

The vacant columns are read on `to_date` from `rpt.vw_vacancy_pool`. The moved columns are counted over the period's quarters from `rpt.vw_position_fill`. Both are the same in every version row.

### 3.3 How it is checked (Claude, before you open Tableau)

| Check | Pass when |
|---|---|
| DuckDB mart `mart_wfp_summary` | `python pipeline/run_pipeline.py`: all tests pass. Test 80 is extended: vacant = vacancy pool on `to_date`; moved = position fill backfills with another office; defaults are alphabetical and always planned |
| T-SQL = DuckDB | `python sqlserver/check_tsql_in_duckdb.py`: the summary matches row for row |
| SQL Server on your Mac | `14_validate_workforce_planning_dashboard.sql` extended with the new columns: every line PASS |

The expected values in section 14 were computed from the base marts (fills, vacancy pool, plan vs actual) by an independent script, and they tie to the summary in every state.

### 3.4 On the Mac (after Claude pushes)

```bash
cd ~/GitHub/people-analytics-warehouse
git fetch origin
git checkout dashboard-3-rebuild
git pull
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/14_validate_workforce_planning_dashboard.sql | grep -E "FAIL|Msg|returned"
```

Expected: `WFP summary Custom SQL returned 10080 rows …`, `Plan vs actual Custom SQL returned 29365 rows …`, `Position fill Custom SQL returned 30575 rows …`, and no `FAIL` or `Msg` line.

```bash
D="$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning"
cp tableau/custom_sql_wfp_summary.sql tableau/custom_sql_plan_vs_actual.sql tableau/custom_sql_position_fill.sql tableau/custom_sql_vacancy_pool.sql "$D/"
ls "$D"
```

---

## 4. Shapes

Palette **Arcadia D3**: `d3_field_capsule` (the white capsule, 180 × 36, as on #1) and `d3_reset` (the arrow icon, 32 × 32). From **Arcadia Shared**: `shared_info_open`, `shared_info_close`, `shared_close_light`.

```bash
cd ~/GitHub/people-analytics-warehouse/docs/brand/shapes/by_dashboard
mkdir -p ~/Documents/My\ Tableau\ Repository/Shapes/Arcadia\ D3
cp d3/*.png ~/Documents/My\ Tableau\ Repository/Shapes/Arcadia\ D3/
ls ~/Documents/My\ Tableau\ Repository/Shapes/Arcadia\ D3
```

Expected: `d3_field_capsule.png  d3_reset.png`. In Tableau: Marks > Shape > More Shapes > **Reload Shapes**.

---

## 5. Workbook and data sources

1. Close Tableau. Move `Arcadia Workforce Planning.twb` to `_archive/2026-10-23/Arcadia Workforce Planning - first build.twb`.
2. **File > New**, save as `Arcadia Workforce Planning.twb` in the same folder.
3. Connect to SQL Server (`localhost, 1433`, `ArcadiaHR`, `sa`, Require SSL off). New Custom SQL with `custom_sql_wfp_summary.sql`. Rename it **WFP Summary**. Data > New Data Source for **Plan vs Actual**, **Position Fill** and **Vacancy Pool**.
4. **Data source filters** (Data Source tab, top right > Filters > Add): `version_type` = Budget on WFP Summary and on Plan vs Actual.
5. **Extract** all four.

**Checkpoint 1:** extract rows 2,520 · 11,740 · 30,575 · 62,055.

**Types.** Convert to Dimension on WFP Summary: `fiscal_year`, `pair_order`, `view_order`, `span_order`. On Plan vs Actual: `fiscal_year`, `fiscal_quarter`. Geographic role **None** on every latitude and longitude of Position Fill. Number format `#,##0` on the count measures.

**Paste what is proven** (Data pane > Copy, then right-click the target source > Paste):

| From | What | Into |
|---|---|---|
| Dashboard #1 workbook | the `kpi_` layout calcs (their 16 parameters come along) | WFP Summary |
| Dashboard #1 workbook | `zzTrue`, `zzFalse`, `Close Panel`, `Pick Rows`, `Pick Col`, `Pick Row` | WFP Summary |
| First #3 workbook (archived) | `K Close HC`, `K Plan HC`, `K HC Gap`, `K NN Done`, `K NN Plan`, `K NN Pct`, `K BF Done`, `K BF Plan`, `K BF Pct`, `K Days`, `K Reuse` and their `… Str` twins | WFP Summary |

Delete anything else that comes along (`K CW …`, `K Cost …`, `KPI 5 …`).

---

## 6. Parameters

| Name | Type | Allowable values | Current |
|---|---|---|---|
| `p_FY` | Integer | List 2022–2026 (display FY22 … FY26) | 2026 |
| `p_Period` | String | List FY, H1, H2, Q1, Q2, Q3, Q4 | FY |
| `p_Span` | String | List `Fiscal year`, `Half year`, `Quarter` | Fiscal year |
| `p_View` | String | List Company, Function, Sub-function, Department, Country | Company |
| `p_Group` | String | **All** | Arcadia Systems |
| `p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen` | Boolean | | False |

---

## 7. Calculations

### 7.1 WFP Summary: context and pickers

```
// Row Is Current     (one row: KPI band, header, Period Field, Group Field, Reset, Info)
[fiscal_year] = [p_FY] AND [pair_code] = [p_Period] AND [view_name] = [p_View] AND [group_name] = [p_Group]

// Period Grid Rows   [view_name] = [p_View] AND [group_name] = [p_Group] AND [span_name] = [p_Span]
// Span Rows          [fiscal_year] = [p_FY] AND [view_name] = [p_View] AND [group_name] = [p_Group]
// View Rows          [fiscal_year] = [p_FY] AND [pair_code] = [p_Period] AND [is_view_default]
// Group Grid Rows    [fiscal_year] = [p_FY] AND [pair_code] = [p_Period] AND [view_name] = [p_View] AND [view_name] <> "Company"

// Why Off            IF [has_plan] THEN "" ELSE [group_name] + " had no seats in the plan for " + [pair_name] + "." END

// FY Pick            IF [has_plan] THEN [fiscal_year] ELSE [p_FY] END          (dimension)
// Period Pick        IF [has_plan] THEN [pair_code] ELSE [p_Period] END
// Period Keep Open   NOT [has_plan]
// Cell Is Current    [fiscal_year] = [p_FY] AND [pair_code] = [p_Period]
// Cell State         IF [Cell Is Current] THEN "current" ELSEIF [has_plan] THEN "on" ELSE "off" END
// Cell Title         IF [Cell Is Current] THEN "› " + [period_short] ELSE [period_short] END
// Span Display       IF [span_name] = [p_Span] THEN "› " + [span_name] ELSE [span_name] END
// Toggle Period Panel   NOT [p_PeriodOpen]

// View Label         IF [view_name] = "Company" THEN "All organizations" ELSE [view_name] END
// View Display       IF [view_name] = [p_View] THEN "› " + [View Label] ELSE [View Label] END
// Keep Group Panel Open   [view_name] <> "Company"
// Group Pick         IF [has_plan] THEN [group_name] ELSE [p_Group] END
// Group Keep Open    NOT [has_plan]
// Group State        IF [group_name] = [p_Group] THEN "current" ELSEIF [has_plan] THEN "on" ELSE "off" END
// Panel Title        "Select " + CASE [p_View] WHEN "Function" THEN "a function" WHEN "Sub-function" THEN "a sub-function"
//                    WHEN "Department" THEN "a department" WHEN "Country" THEN "a country" ELSE "a view" END
// Group Field Text   IF [p_View] = "Company" THEN "All organizations"
//                    ELSEIF LEN([p_Group]) > 22 THEN LEFT([p_Group], 21) + "…" ELSE [p_Group] END
// Toggle Group Panel NOT [p_GroupOpen]
// Toggle Info        NOT [p_InfoOpen]
// Info Shape         IF [p_InfoOpen] THEN "shared_info_close" ELSE "shared_info_open" END
```

Reset defaults: `Default FY` = `2026`, `Default Period` = `"FY"`, `Default Span` = `"Fiscal year"`, `Default View` = `"Company"`, `Default Group` = `"Arcadia Systems"`.

Header (same text as #1's):

```
// From Day        LEFT(DATENAME('month', [from_date]), 3) + " " + STR(DAY([from_date])) + ", " + STR(YEAR([from_date]))
// To Day          the same pattern on [to_date]
// Page Subtitle   "Opening " + [From Day] + " → Closing " + [To Day]
// Title Tip
"Showing: " + (IF [p_View] = "Company" THEN "all of Arcadia" ELSE [view_name] + " · " + [group_name] END) + CHAR(10) +
"Every hire fills a seat: a vacant seat someone left (a backfill) or a new seat the plan added (net-new)." + CHAR(10) +
"The map follows seats, not people: where the person who left sat, and where the new person sits." + CHAR(10) +
"Plan = the budget approved before " + [fiscal_year_label] + ". Executive officers excluded."
```

### 7.2 WFP Summary: KPI numbers

Keep the pasted `K …` calcs (comma and percent patterns from the first guide, 3.5). Add:

```
// K Moved         SUM([moved_seats])
// K Moved Lower   SUM([moved_lower_pay])
// K Moved Pct     IF [K BF Done] = 0 THEN NULL ELSE [K Moved] / [K BF Done] END
// K Vacant        SUM([vacant_seats])
// K Stale         SUM([vacant_stale])
// K Reuse Pct     IF [K NN Done] = 0 THEN NULL ELSE [K Reuse] / [K NN Done] END
```

Add a `Str` twin for each count (plain comma pattern) and for `K Moved Pct` (percent pattern).

### 7.3 Period window (on Plan vs Actual, Position Fill and Vacancy Pool; parameters only, so the formula is the same in each)

```
// Period First Q   CASE [p_Period] WHEN "FY" THEN 1 WHEN "H1" THEN 1 WHEN "H2" THEN 3
//                  WHEN "Q1" THEN 1 WHEN "Q2" THEN 2 WHEN "Q3" THEN 3 ELSE 4 END
// Period Last Q    CASE [p_Period] WHEN "FY" THEN 4 WHEN "H1" THEN 2 WHEN "H2" THEN 4
//                  WHEN "Q1" THEN 1 WHEN "Q2" THEN 2 WHEN "Q3" THEN 3 ELSE 4 END
// Period To Date   DATEADD('day', -1, DATEADD('month', 3 * [Period Last Q], MAKEDATE([p_FY] - 1, 7, 1)))
// In Group
CASE [p_View]
    WHEN "Company"      THEN TRUE
    WHEN "Function"     THEN [function_name] = [p_Group]
    WHEN "Sub-function" THEN [sub_function] = [p_Group]
    WHEN "Department"   THEN [department_name] = [p_Group]
    WHEN "Country"      THEN [country_name] = [p_Group]
END
```

The group is always the seat's **current** department and country (where the new person sits). For a country view, a seat that moved from Bengaluru to Warsaw counts in Poland.

**Checkpoint 2** (scratch sheet `CHK`): filter `Row Is Current`, Text: `K Close HC`, `K Plan HC`, `K BF Done`, `K BF Plan`, `K Moved`, `K Moved Lower`, `K NN Done`, `K NN Plan`, `K Reuse`, `K Vacant`, `K Stale`. Default: **30,005 · 30,337 · 4,668 · 5,031 · 467 · 280 · 2,181 · 2,762 · 628 · 977 · 213**.

---

## 8. Top bar (G1 section 6; band 76 high, controls 32 high on y 30)

| Sheet | Build |
|---|---|
| `Page Title` | Filter `Row Is Current`. Line 1 `Workforce Planning` Tableau Bold 18 white; line 2 `<Page Subtitle>` Book 8 `#C9D1DC`. Detail `Title Tip`, `zzTrue`, `zzFalse`. Tooltip **How to read this page** + `<Title Tip>` + "Click ⓘ for the full definitions." |
| `Period Field` | Shape `d3_field_capsule`, size max; Label `<pair_name>  ▾` Semibold 9 navy, centre, allow overlap. Filter `Row Is Current`. Detail `Toggle Period Panel`, `Close Panel`, `span_name`, `zzTrue`, `zzFalse`. Tooltip `Choose the period` |
| `Group Field` | Same; Label `<Group Field Text>  ▾`; Detail `Toggle Group Panel`, `Close Panel`, `zzTrue`, `zzFalse`. Tooltip `<p_Group>` / `Choose who to look at` |
| `Reset` | Shape `d3_reset`, size max, filter `Row Is Current`. Detail the five `Default …`, `Close Panel`, `zzTrue`, `zzFalse`. Tooltip `Reset to default view` |
| `Info Button` | Shape `Info Shape` (assign the two shared files), filter `Row Is Current`. Detail `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse`. Tooltip `Click here for more information on how to read this page` |

Headings: dashboard Text objects, Bold 10 `#B8C4D6`: `SELECT PERIOD`, `SELECT VIEW`.

| Object | x | y | w | h |
|---|---:|---:|---:|---:|
| Header band (Blank `#13233A`) | 0 | 0 | 1400 | 76 |
| Logo | 30 | 14 | 177 | 48 |
| Page Title | 223 | 9 | 275 | 58 |
| SELECT PERIOD / Period Field | 506 | 12 / 30 | 180 | 14 / 32 |
| SELECT VIEW / Group Field | 698 | 12 / 30 | 180 | 14 / 32 |
| Reset | 1294 | 30 | 32 | 32 |
| Info Button | 1338 | 30 | 32 | 32 |

Every control: item background None, border None, padding 0 (G1 6.8).

---

## 9. Popovers (G1 0.5: navy `#13233A`, radius 10, inner padding 16, front, one open at a time)

![Popovers mock](../../images/workforce_planning_popovers_mock.png)

*Left: the period popover with Country · Portugal selected (FY22 and FY23 are dim: Portugal had no seats in the plan before FY24). Right: the view popover, showing a dim group the way it looks in FY22–FY24.*

### 9.1 Period popover

| Sheet | Build |
|---|---|
| `Span List` | Filter `Span Rows`. Rows `span_order`, `span_name` (hidden). Text `Span Display`, Book 10 `#B8C0CC` in the Label editor, no Color (G1 7.2). Detail `span_name`, `zzTrue`, `zzFalse`. 3 rows |
| `Period Panel` | Filter `Period Grid Rows`. Columns `fiscal_year` **descending**, Rows `pair_order` **descending**, headers hidden. Text: line 1 `<Cell Title>` Semibold 10, line 2 `<period_dates>` Book 9. Color `Cell State`: current `#FFFFFF`, on `#B8C0CC`, off `#56657E`. Detail `FY Pick`, `Period Pick`, `Period Keep Open`, `Why Off`, `zzTrue`, `zzFalse`. Tooltip `<Why Off>` only. A plain cross-tab with no table calcs, so Color as a dimension is safe |
| `Period Close` | Shape `shared_close_light` 16 × 16; Detail `Close Panel`, `zzTrue`, `zzFalse`; tooltip `Close` |

Container `Period Popover`: **x 506, y 76, w 708, h 254**, visibility `p_PeriodOpen`. Inside: a header row ("Select a period" Bold 12 white + `Period Close`); a note (Book 9 `#8FA0B8`: "Fiscal year runs July to June. Each option compares two quarter-ends."); then horizontal `Span List` (120) + `Period Panel` (540).

### 9.2 View popover

| Sheet | Build |
|---|---|
| `View List` | Filter `View Rows` (5 rows). Rows `view_order`, `view_name` (hidden). Text `View Display`, Book 10 `#B8C0CC`. Detail `view_name`, `group_name` (the view's default, the only row left by the filter), `Keep Group Panel Open`, `zzTrue`, `zzFalse` |
| `Group Panel` | Filter `Group Grid Rows`. Columns `Pick Col`, Rows `Pick Row` (both Discrete, hidden). Text `group_name` Book 10. Color `Group State` (white / `#B8C0CC` / `#56657E`). Detail **in this order**: `group_name`, `Group Pick`, `Group State`, `Group Keep Open`, `Why Off`, `zzTrue`, `zzFalse`. Every table calc (`Pick Col`, `Pick Row`, and `Pick Rows` inside them): Specific Dimensions, **all fields ticked, `group_name` at the top**. `group_name` goes first, not `Group Pick`: a dim group's `Group Pick` is the current group, so two marks would share it and break the alphabetical fill. Tooltip `<Why Off>` |
| `Group Heading` | `<Panel Title>` Bold 12 white, filter `Row Is Current` |
| `Group Close` | Copy of `Period Close` |

Container `Group Popover`: **x 610, y 76, w 760, h 330**, visibility `p_GroupOpen`. Header row (`Group Heading` + `Group Close`), then horizontal `View List` (140) + `Group Panel`.

### 9.3 Info popover

Container `Info Popover`: **x 960, y 76, w 410**, about 520 high, visibility `p_InfoOpen`. Header "How to read this page" + `Info Close`. Body Book 10 `#B8C0CC`, lead-ins Semibold 10 white:

> **Period.** Every option compares two quarter-ends inside one fiscal year, because the plan is quarterly. Arcadia's fiscal year runs July to June.
>
> **Who is counted.** Employees at quarter-end. The CEO and the eight function heads are left out on every Arcadia dashboard, so all three count the same people.
>
> **Seats, not people.** Every hire fills a seat. A net-new seat is growth the plan added. A backfill fills a vacant seat someone left, by resigning, being let go or moving to another seat. A promotion re-grades a seat with the same person in it, so it is not a fill.
>
> **The map.** One line per backfilled seat that changed office: from where the person who left sat, to where the new person sits. People's own office moves are on the Compensation Walk.
>
> **Vacant seats.** A seat with no one in it. Vacant over 90 days is stale. A net-new seat approved while a stale seat with the same department, job family and country (grade within one) was vacant counts as "with a vacant match".
>
> **Plan.** The budget approved before each fiscal year. Pay changes compare annual base pay in constant USD.
>
> **Data.** Arcadia Systems is a fictional company. All data is synthetic.

---

## 10. KPI band and hovers

### 10.1 Band (`KPI Cards`, WFP Summary)

Geometry as #1 (G1 8.2a): image `arcadia_kpi_cards_bg_wide.png` at 0, 78, 1400 × 110; `kpi_GridLeft` 30, `kpi_CardW` 255, `kpi_GapX` 16, `kpi_GridTop` 12, `kpi_CardH` 86. Filter `Row Is Current`. Centred text, as #1.

| Card | Title | Value | Note |
|---|---|---|---|
| 1 | `Employees` | `K Close HC Str` | `[K HC Gap Str] + " vs plan " + [K Plan HC Str]` |
| 2 | `Backfilled seats` | `K BF Done Str` | `[K BF Pct Str] + " of plan · median " + (IF ISNULL([K Days]) THEN "—" ELSE STR(INT(ROUND([K Days], 0))) END) + " days to fill"` |
| 3 | `Backfills in a new office` | `K Moved Str` | `[K Moved Pct Str] + " of backfills · " + [K Moved Lower Str] + " to lower pay"` |
| 4 | `Net-new seats` | `K NN Done Str` | `[K NN Pct Str] + " of plan · " + [K Reuse Str] + " with a vacant match"` |
| 5 | `Vacant seats` | `K Vacant Str` | `[K Stale Str] + " vacant over 90 days"` |

Every note is 45 characters or fewer, so each fits on one line at 255 wide.

### 10.2 Hovers (G1 8.2c)

`KPI Hover 1`–`5` on WFP Summary (`Hover Cell` = `"."` on Columns and Rows, Square at 0% opacity, filter `Row Is Current`), floating at **x 30, 301, 572, 843, 1114 · y 90 · 255 × 86**, corner radius 5, a deselect action each. Tooltip: `<KPI n Title>` Semibold 10 navy, `<KPI n Tip>` Book 9 `#4A5A73`.

```
// KPI 1 Tip
"People on the books on " + MIN([To Day]) + ": " + [K Close HC Str] + ". The plan expected " + [K Plan HC Str] + "."
+ CHAR(10) + "Headcount counts people; the rest of the page counts seats. Executive officers are not included."

// KPI 2 Tip
"A backfill fills a vacant seat someone left: they resigned, were let go, or moved to another seat."
+ CHAR(10) + [K BF Done Str] + " seats were filled back, against " + [K BF Plan Str] + " in the plan (" + [K BF Pct Str] + ")."
+ " Median days from approval to fill; leader seats filled the same day by a successor are left out of the median."

// KPI 3 Tip
"The same seat, a different office: the person who left sat in one office, the person who filled it sits in another."
+ CHAR(10) + [K Moved Str] + " of " + [K BF Done Str] + " backfills (" + [K Moved Pct Str] + "); " + [K Moved Lower Str] + " moved to an office with a lower pay range."

// KPI 4 Tip
"A net-new seat is growth the plan added. " + [K NN Done Str] + " were filled, against " + [K NN Plan Str] + " planned (" + [K NN Pct Str] + ")."
+ CHAR(10) + [K Reuse Str] + " were approved while a matching seat had been vacant for over 90 days (same department, job family and country, grade within one)."

// KPI 5 Tip
"Seats with no one in them on " + MIN([To Day]) + ": " + [K Vacant Str] + ". " + [K Stale Str] + " have been vacant for over 90 days."
```

---

## 11. The four cards

Card style: G1's type rule (title Semibold 12 navy, subtitle Book 9 slate `#5A6170`, labels Book 9), background `#FBFBF8`, corner radius 10. Titles and subtitles are FIXED calcs inserted in the sheet title (D11). On Position Fill:

```
// Fill Quarter       INT(RIGHT([fiscal_quarter_label], 1))
// In Period          [fiscal_year] = [p_FY] AND [Fill Quarter] >= [Period First Q] AND [Fill Quarter] <= [Period Last Q]
// Backfill In Scope  [In Period] AND [In Group] AND [seat_type] = "Backfill"
// Seat Moved         [Backfill In Scope] AND [location_change] <> "Same office"
```

### 11.1 Main card: where backfilled seats moved (Position Fill, two sheets in one card)

```
// Seat Route         [prior_office_name] + " → " + [office_name]
// Route Line         MAKELINE(MAKEPOINT(MIN([prior_latitude]), MIN([prior_longitude])), MAKEPOINT(MIN([latitude]), MIN([longitude])))
// New Office Point   MAKEPOINT(MIN([latitude]), MIN([longitude]))
// M Seats            { FIXED : SUM(IF [Seat Moved] THEN 1 END) }
// M Lower            { FIXED : SUM(IF [Seat Moved] AND [location_effect_usd_constant] < 0 THEN 1 END) }
// M Same Country     { FIXED : SUM(IF [Seat Moved] AND [location_change] = "Other office, same country" THEN 1 END) }
// M Border           { FIXED : SUM(IF [Seat Moved] AND [location_change] = "Other country" THEN 1 END) }
// M Title
IF ZN([M Seats]) = 0 THEN "No backfilled seat changed office in this period"
ELSEIF [M Seats] = 1 THEN "One backfilled seat was refilled in a different office"
ELSE <comma [M Seats]> + " backfilled seats were refilled in a different office" END
// M Subtitle
"Each line is one seat: from where the person who left sat, to where the new person sits"
+ IF ZN([M Seats]) = 0 THEN "" ELSE " · " + STR(ZN([M Lower])) + " moved to a lower-pay office" END
// R Subtitle         (routes sheet)
"Backfilled seats by old office → new office" + IF ZN([M Seats]) = 0 THEN "" ELSE
" · " + STR(ZN([M Same Country])) + " stayed in the same country, " + STR(ZN([M Border])) + " crossed a border" END
```

**Sheet `Seat Map`** (top of the card, 797 × 420): filter `Seat Moved` = True.
- Layer 1, `Route Line`: Automatic mark, `Seat Route` on Detail, teal `#00938D` at 50%, thinnest size, no Size field.
- Layer 2, `New Office Point`: Circle, `office_name` on Detail, `CNT(fill_id)` on Size (about 5 to 20 px), teal 85%, white border.
- Map Layers: Base off, Coastline and Country borders on; shading None; search and toolbar off; frame from Vancouver to Sydney (G2 map guide, step 6). Title `<M Title>` / `<M Subtitle>`.
- Tooltips. Route: `<Seat Route>` Semibold 10; `<CNT(fill_id)> seats: the person who left sat in <prior_office_name>, the new person sits in <office_name>`; `<AGG(Route Pay Words)>`, where `Route Pay Words` = `IF SUM([location_effect_usd_constant]) < 0 THEN "Lower pay range in the new office" ELSEIF SUM([location_effect_usd_constant]) > 0 THEN "Higher pay range in the new office" ELSE "Same pay range" END`. Dot: `<office_name>` Semibold 10; `<CNT(fill_id)> backfilled seats arrived from other offices`.

**Sheet `Seat Routes`** (bottom of the card, 797 × 190): filter `Seat Moved`. Rows `Seat Route`, Columns `CNT(fill_id)`, sorted descending. Filter `Route Rank` = `INDEX()` ≤ 5 (Compute Using `Seat Route`). Bars teal, label `<CNT(fill_id)> seats`. Row header Semibold 10 navy, width about 190. Title "Busiest seat routes" (Semibold 10) / `<R Subtitle>` (Book 9). Axis hidden, no grid lines. Tooltip as the map route.

Container `Card: Seat Moves`, **x 30, y 188, w 797, h 624**: vertical, background `#FBFBF8`, radius 10, padding 16, holding `Seat Map` (fixed 420) and `Seat Routes`.

Expected default: 467 · 280 lower · 101 routes into 30 offices. Biggest dots: Pune and Austin HQ (53 each), Hyderabad 43, Bengaluru 39, Chicago 34. Routes: Bengaluru → Hyderabad 37, Hyderabad → Bengaluru 32, Bengaluru → Pune 27, Hyderabad → Pune 26, Mexico City → Guadalajara 22. Subtitle "… 410 stayed in the same country, 57 crossed a border".

**What the routes say.** Most seat moves stay inside one country and favour lower-pay offices (the relocation rule in [workforce_planning.md](workforce_planning.md) section 3). The cross-border lines are leader seats filled the same day by a successor based elsewhere. Seats also move both ways (Bengaluru ↔ Hyderabad), because each refill goes where the hiring happened.

### 11.2 Right top: what changed when a seat was refilled (Position Fill)

```
// Change Kind    IF [location_change] <> "Same office" THEN "Moved to another office"
//                ELSEIF [level_change] = "Down" THEN "One level down"
//                ELSEIF [level_change] = "Up" THEN "One level up" ELSE "Same level, same office" END
// Change Order   CASE [Change Kind] WHEN "Same level, same office" THEN 1 WHEN "One level down" THEN 2 WHEN "One level up" THEN 3 ELSE 4 END
// Changed        [Change Kind] <> "Same level, same office"
// C Backfills    { FIXED : SUM(IF [Backfill In Scope] THEN 1 END) }
// C Changed      { FIXED : SUM(IF [Backfill In Scope] AND [Changed] THEN 1 END) }
// C Pay          { FIXED : SUM(IF [Backfill In Scope] THEN [pay_change_usd_constant] END) }
// Pay Words      (for an amount x: "$7.0M", "$412K", "$950")
IF ABS(x) >= 999950 THEN "$" + STR(ROUND(ABS(x) / 1000000, 1)) + "M"
ELSEIF ABS(x) >= 999.5 THEN "$" + STR(INT(ROUND(ABS(x) / 1000, 0))) + "K"
ELSE "$" + STR(INT(ROUND(ABS(x), 0))) END
// C Title
IF ZN([C Backfills]) = 0 THEN "No seat was backfilled in this period"
ELSE <comma ZN([C Changed])> + " of " + <comma [C Backfills]> + " backfills changed level or office" END
// C Subtitle
IF ZN([C Backfills]) = 0 THEN ""
ELSEIF ABS([C Pay]) < 500 THEN "New people earn about the same as those who left"
ELSE "New people earn " + <Pay Words on [C Pay]> + " a year " + IIF([C Pay] < 0, "less", "more") + " than those who left · label = pay change" END
// Row Pay Str    (IF SUM([pay_change_usd_constant]) < 0 THEN "−" ELSE "+" END) + <Pay Words on SUM([pay_change_usd_constant])>
```

Sheet `Backfill Changes`: filter `Backfill In Scope`. Rows `Change Kind` (by `Change Order`), Columns `CNT(fill_id)`, Color `Changed` (False `#8C9BB0`, True navy), Label `<CNT(fill_id)> · <AGG(Row Pay Str)>`. Item **x 843, y 188, w 526, h 196**. Tooltip: kind, count, pay, and one line of meaning ("Refilled one grade lower: a manager seat often comes back as an individual contributor").

Expected: 3,460 · +$0.7M; 556 · −$9.5M; 185 · +$3.0M; 467 · −$1.2M. The "Moved to another office" bar equals the map's 467 by construction.

### 11.3 Right middle: net-new seats against plan (Plan vs Actual)

```
// In Plan Period   [fiscal_year] = [p_FY] AND [fiscal_quarter] >= [Period First Q] AND [fiscal_quarter] <= [Period Last Q] AND [In Group]
// NN Dim           (one level below the selection, as #1's turnover card)
CASE [p_View]
    WHEN "Company"      THEN [function_name]
    WHEN "Function"     THEN IIF({ FIXED [function_name] : COUNTD([sub_function]) } > 1, [sub_function], [department_name])
    WHEN "Sub-function" THEN [department_name]
    WHEN "Department"   THEN [country_name]
    WHEN "Country"      THEN [function_name]
END
// N Done     { FIXED : SUM(IF [In Plan Period] THEN [actual_net_new] END) }
// N Plan     { FIXED : SUM(IF [In Plan Period] THEN [planned_net_new] END) }
// N Reuse    { FIXED : SUM(IF [In Plan Period] THEN [actual_net_new_reuse_candidates] END) }
// N Title
IF ZN([N Plan]) = 0 AND ZN([N Done]) = 0 THEN "No net-new seats in this period"
ELSEIF ZN([N Plan]) = 0 THEN <comma [N Done]> + " net-new seats filled; none were planned"
ELSE <comma [N Done]> + " net-new seats filled, " + <percent [N Done] / [N Plan]> + " of plan" END
// N Subtitle   "Filled vs planned by " + LOWER(<the NN Dim level name>) + " · " + STR(ZN([N Reuse])) + " approved while a matching seat was vacant"
// N Rank       RANK_UNIQUE(SUM([planned_net_new]) + SUM([actual_net_new]) / 1000)    (Compute Using NN Dim)
```

The level name for the subtitle: `CASE [p_View] WHEN "Company" THEN "function" WHEN "Function" THEN "sub-function or department" WHEN "Sub-function" THEN "department" WHEN "Department" THEN "country" ELSE "function" END`.

Sheet `Net-new by Group`: filter `In Plan Period` = True, `N Rank` ≤ 8, and `SUM(planned_net_new) + SUM(actual_net_new)` > 0. Rows `NN Dim` (sorted by planned, descending). Columns `SUM(planned_net_new)` (Bar `#D5DBE4`, size 60%) and `SUM(actual_net_new)` (Bar navy, size 30%), dual axis, synchronized, axis hidden. Label on the planned card: `<SUM(actual_net_new)> of <SUM(planned_net_new)>`. Item **x 843, y 400, w 526, h 196**. Fit Standard, rows about 16 px (the 8-row cap keeps the card the same height in every view). Tooltip: `<NN Dim>`; `<SUM(actual_net_new)> filled of <SUM(planned_net_new)> planned`; `<SUM(actual_net_new_reuse_candidates)> approved while a matching seat was vacant`.

Expected default: Technology 830 of 1,029 · Commercial 559 of 660 · Operations 320 of 444 · Product 156 of 182 · People 94 of 134 · Finance 83 of 122 · Marketing 69 of 99 · Legal & Compliance 70 of 92.

### 11.4 Right bottom: vacant seats (Vacancy Pool)

```
// In Vacant      [month_end_date] = [Period To Date] AND [In Group]
// Band           CASE [vacancy_age_band] WHEN "0-30 days" THEN "0–30 days" WHEN "31-90 days" THEN "31–90 days"
//                WHEN "91-180 days" THEN "91–180 days" ELSE "Over 180 days" END
// Band Order     CASE [vacancy_age_band] WHEN "0-30 days" THEN 1 WHEN "31-90 days" THEN 2 WHEN "91-180 days" THEN 3 ELSE 4 END
// V Seats        { FIXED : SUM(IF [In Vacant] THEN 1 END) }
// V Stale        { FIXED : SUM(IF [In Vacant] AND [is_stale] THEN 1 END) }
// V Title        IF ZN([V Seats]) = 0 THEN "No seat was vacant on " + <day of [Period To Date]>
//                ELSE <comma [V Seats]> + " seats are vacant; " + <comma ZN([V Stale])> + " for over 90 days" END
// V Subtitle     "Seats with no one in them on " + <day of [Period To Date]> + ", by how long they have been vacant"
```

Sheet `Vacant Seats`: filter `In Vacant`. Rows `Band` (by `Band Order`), Columns `CNT(position_id)`, Color `is_stale` (False `#8C9BB0`, True navy), label the count. Item **x 843, y 612, w 526, h 200**. Tooltip: `<Band>`: `<CNT(position_id)>` vacant seats.

Expected default: 396 · 368 · 126 · 87.

---

## 12. Dashboard layout (1400 × 850, all floating)

| # | Object | x | y | w | h |
|---|---|---:|---:|---:|---:|
| 1–8 | Top bar (section 8) | | | | |
| 9 | KPI background image | 0 | 78 | 1400 | 110 |
| 10 | KPI Cards | 0 | 78 | 1400 | 110 |
| 11–15 | KPI Hover 1–5 | 30 / 301 / 572 / 843 / 1114 | 90 | 255 | 86 |
| 16 | Card: Seat Moves (Seat Map + Seat Routes) | 30 | 188 | 797 | 624 |
| 17 | Backfill Changes | 843 | 188 | 526 | 196 |
| 18 | Net-new by Group | 843 | 400 | 526 | 196 |
| 19 | Vacant Seats | 843 | 612 | 526 | 200 |
| 20 | Footnote | 30 | 822 | 700 | 16 |
| 21 | Period, Group, Info popovers | 9.1–9.3 | | | |

Footnote: "Arcadia Systems is a fictional company. All data is synthetic and covers Jul 2021 to Jun 2026." Book 8 `#8C8A84`. Item order, bottom to top: background, KPI image, KPI Cards, cards, KPI hovers, band, controls, popovers.

---

## 13. Actions (complete list; build them on the dashboard after every sheet is placed)

### 13.1 Change Parameter (30): Run on Select, Aggregation None, Keep current value

| # | Name | Source | Target | Field |
|---:|---|---|---|---|
| 1 | Open period panel | Period Field | `p_PeriodOpen` | `Toggle Period Panel` |
| 2 | Open period on its span | Period Field | `p_Span` | `span_name` |
| 3 | Period opens, group closes | Period Field | `p_GroupOpen` | `Close Panel` |
| 4 | Period opens, info closes | Period Field | `p_InfoOpen` | `Close Panel` |
| 5 | Set span | Span List | `p_Span` | `span_name` |
| 6 | Set FY | Period Panel | `p_FY` | `FY Pick` |
| 7 | Set period | Period Panel | `p_Period` | `Period Pick` |
| 8 | Close period on pick | Period Panel | `p_PeriodOpen` | `Period Keep Open` |
| 9 | Close period on ✕ | Period Close | `p_PeriodOpen` | `Close Panel` |
| 10 | Open group panel | Group Field | `p_GroupOpen` | `Toggle Group Panel` |
| 11 | Group opens, period closes | Group Field | `p_PeriodOpen` | `Close Panel` |
| 12 | Group opens, info closes | Group Field | `p_InfoOpen` | `Close Panel` |
| 13 | Set view | View List | `p_View` | `view_name` |
| 14 | Set group from view | View List | `p_Group` | `group_name` |
| 15 | Keep group panel open | View List | `p_GroupOpen` | `Keep Group Panel Open` |
| 16 | Set group | Group Panel | `p_Group` | `Group Pick` |
| 17 | Close group on pick | Group Panel | `p_GroupOpen` | `Group Keep Open` |
| 18 | Close group on ✕ | Group Close | `p_GroupOpen` | `Close Panel` |
| 19–23 | Reset FY / period / span / view / group | Reset | `p_FY`, `p_Period`, `p_Span`, `p_View`, `p_Group` | the five `Default …` |
| 24–26 | Reset closes period / group / info | Reset | `p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen` | `Close Panel` |
| 27 | Open info | Info Button | `p_InfoOpen` | `Toggle Info` |
| 28–29 | Info opens, period / group closes | Info Button | `p_PeriodOpen`, `p_GroupOpen` | `Close Panel` |
| 30 | Close info on ✕ | Info Close | `p_InfoOpen` | `Close Panel` |

### 13.2 Deselect (19 Filter actions)

Source and target the same worksheet, Run on Select, Show all values, `zzTrue` → `zzFalse` (G1 7.4): `Page Title`, `Period Field`, `Group Field`, `Reset`, `Info Button`, `Span List`, `Period Panel`, `Period Close`, `View List`, `Group Panel`, `Group Heading`, `Group Close`, `Info Close`, `KPI Cards`, `KPI Hover 1`–`5`. The four cards keep normal selection.

**Total: 49 actions.** The final audit compares Dashboard > Actions with these two tables row by row.

---

## 14. Check tables (independent script on the base marts; ties to the summary in every state)

### 14.1 KPI band

| State | 1 Employees | 2 Backfilled seats | 3 In a new office | 4 Net-new seats | 5 Vacant |
|---|---|---|---|---|---|
| T1 FY26 · FY · All | 30,005 · −332 vs plan 30,337 | 4,668 · 92.8% · median 42 | 467 · 10.0% · 280 lower | 2,181 · 79.0% · 628 | 977 · 213 |
| T2 FY26 · Q3 · All | 29,618 · −428 vs plan 30,046 | 1,201 · 88.6% · median 43 | 102 · 8.5% · 59 | 471 · 83.8% · 135 | 1,189 · 219 |
| T3 FY26 · FY · Function Finance | 1,271 · −37 vs plan 1,308 | 181 · 78.7% · median 42 | 15 · 8.3% · 7 | 83 · 68.0% · 13 | 43 · 14 |
| T4 FY26 · FY · Country India | 6,967 · −89 vs plan 7,056 | 1,047 · 93.9% · median 44 | 135 · 12.9% · 99 | 418 · 74.4% · 191 | 228 · 58 |
| T5 FY24 · FY · All (restructuring) | 27,208 · −1,381 vs plan 28,589 | 4,105 · 91.2% · median 47 | 425 · 10.4% · 242 | 910 · 32.1% · 228 | 976 · 248 |
| T6 FY26 · H1 · Dept Accounting & Controllership | 547 · −3 vs plan 550 | 34 · 77.3% · median 42 | 4 · 11.8% · 2 | 18 · 60.0% · 5 | 24 · 5 |
| T7 FY26 · Q3 · Country Switzerland | 145 · +1 vs plan 144 | 3 · 60.0% · median 32 | 0 · 0.0% · 0 | 1 · **—** · 0 | 5 · 0 |

### 14.2 Cards

| State | Main card | Backfill changes | Net-new by group | Vacant by age |
|---|---|---|---|---|
| T1 | 467 · 101 routes · 30 offices · top Bengaluru → Hyderabad 37 · 410 / 57 | 3,460 +$0.7M · 556 −$9.5M · 185 +$3.0M · 467 −$1.2M; $7.0M less | Technology 830/1,029 … Legal & Compliance 70/92 | 396 · 368 · 126 · 87 |
| T2 | 102 · 48 routes · 24 offices · top Bengaluru → Pune 7 | 920 · 137 · 42 · 102; $1.8M less | Technology 188/217, Commercial 119/124, Operations 69/103 … | 506 · 465 · 157 · 61 |
| T3 | 15 · 11 routes · 9 offices · top Austin HQ → Chicago 3 | 145 · 17 · 4 · 15; $373K less | by **department**: Treasury & Tax 27/54, Accounting & Controllership 29/44, FP&A 27/24 | 11 · 18 · 7 · 7 |
| T4 | 135 · 14 routes · 3 offices · top Bengaluru → Hyderabad 37 | 744 · 134 · 34 · 135; **$816K more** | Technology 185/238, Operations 97/145, Commercial 78/99 … Legal & Compliance 8/5 | 88 · 82 · 35 · 23 |
| T5 | 425 · 84 routes · 30 offices · top Bengaluru → Hyderabad 56 | 3,015 · 504 · 161 · 425; $10.3M less | Technology 331/954 … every function near a third of plan | 401 · 332 · 192 · 51 |
| T7 | **No backfilled seat changed office in this period** | 3 same; about the same ($15K) | **1 net-new seat filled; none were planned** | 1 · 4 |

### 14.3 Dim options

| State | Must be dim | Tooltip |
|---|---|---|
| FY22 · Country | Philippines, Portugal, South Korea | Portugal had no seats in the plan for FY22 · Jun 21 → Jun 22. |
| FY24 · Department | Data & AI Platform | Data & AI Platform had no seats in the plan for FY24 · Jun 23 → Jun 24. |
| Country · Portugal | Period grid: every FY22 and FY23 cell | Portugal had no seats in the plan for FY23 Q2 · Sep 22 → Dec 22. (that cell) |

---

## 15. Click tests (Presentation mode)

| # | Do | Expect |
|---:|---|---|
| 1 | Hover every control and KPI card | Outline only, never a square; the tooltips of 8 and 10.2 |
| 2 | Click every control, the title and the KPI band | Nothing stays highlighted |
| 3 | Open Period, then View, then ⓘ | Only the last one open |
| 4 | Period > Quarter > FY26 Q3 | Closes; field "FY26 Q3 · Dec 25 → Mar 26"; page = T2 |
| 5 | View > Function | Stays open on Commercial; pick Finance: closes; page = T3 |
| 6 | View > All organizations | Closes at once |
| 7 | View > Country > Portugal, then Period | FY22 and FY23 cells dim; clicking one does nothing, the popover stays open |
| 8 | Hover a route and a dot on the map | Old office, new office, seats, pay range |
| 9 | Reset | FY26 · All organizations, popovers closed |

---

## 16. Publish

1. Reset, close popovers, hide all sheets. **File > Save to Tableau Public As** `arcadia_workforce_planning`, extracts only.
2. Check the live page against T1, T3, T4 and T7, and against section 15.
3. Screenshot (same crop as #1) to `docs/images/workforce_planning_dashboard.png`. Update the README, the Tableau Public profile and the portfolio site.
4. Claude: record the as-built values here, update `workforce_planning.md` (section 0's principle and the map definition), sync the project docs.

---

## 17. Who does what, in what order

| Phase | Who | What | Done when |
|---|---|---|---|
| 0 | Claude | This plan, shapes, mocks | You approve sections 0–2 and the mocks |
| 1 | Claude | SQL (3.2), test 80, T-SQL check, `14_validate`; branch `dashboard-3-rebuild` | All of 3.3 passes |
| 2 | You (Mac) | 3.4 and section 4 | No FAIL; 2 shapes installed |
| 3 | You (Tableau) | Sections 5–7 | Checkpoints 1 and 2 |
| 4 | You | Sections 8, 9 and the action table (13) for the controls | Click tests 3–7 and 9 |
| 5 | You | Section 10 | 14.1 for T1, T3, T7 |
| 6 | You | Section 11 | 14.2 for T1, T4, T7 |
| 7 | You | Section 12, info text, action audit, all of 15 | Everything passes |
| 8 | Both | Section 16 | Live on Tableau Public |

One screenshot per phase (the dashboard at T1 plus the state named in "Done when"). I check it against the tables and come back only with corrections.
