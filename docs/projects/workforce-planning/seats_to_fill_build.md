# Dashboard #5, Seats to Fill: build guide

This guide builds the fifth Arcadia dashboard from an empty Tableau Desktop, in the order you would build it by hand: the data source, the parameters, the calculations, each sheet, the dashboard, the actions and the checks. Every formula is written to paste as it stands, and every expected value comes from [the check tables](seats_to_fill_check_tables.md), which are computed from the marts the way the page computes them. A step either matches or tells you exactly what differs.

The design is the approved prototype (Design canvas "Seats to Fill prototype", row "Option B, revised"); the method is [seats_to_fill_method.md](seats_to_fill_method.md); the decisions are [seats_to_fill_plan.md](seats_to_fill_plan.md). Four of the techniques used here were proven on Tableau Public first ([seats_to_fill_spikes.md](seats_to_fill_spikes.md)): the cascading lists, the clean-up of a parent's children with `REGEXP_REPLACE`, the range across 100 draws, and the survival curve as a table calculation.

Arcadia Systems is fictional; all data is synthetic.

| Step | What | State |
|---|---|---|
| 1 | Prototype, check tables, the Custom SQL with its chart scaffold | Done 2026-10-27 |
| 2 | This guide | Written 2026-10-27 |
| 3 | The build, written straight into the workbook in stages, each spot-checked in Desktop | Done 2026-10-27 (section 16: as built) |
| 4 | Publish, README, Figma, profile | Done 2026-10-27: [live on Tableau Public](https://public.tableau.com/app/profile/thialp/viz/SeatstoFillArcadiaSystems/Dashboard) |

## Contents

0. What you are building
1. Decisions
2. The data source
3. Parameters
4. Core calculations (row types, scope, period, the cascade, scope words, number text)
5. The forecast numbers
6. The KPI band (hero, three cards, hovers, the seat bridge)
7. The main chart (quarters, the fan, the budget step, fiscal-year chips, quarter labels)
8. How fast PIDs fill (the survival panel and its legend)
9. Can we trust it (the backtest panel)
10. The rail (capsules, Reset, the data line)
11. The popovers (Period, Organization, Location, Info)
12. Assembling the dashboard
13. Actions
14. Checks and click tests
15. Publishing
16. As built: what the workbook does differently from this guide, and why

---

## 0. What you are building

**The question on the page:** *how many PIDs will Arcadia fill in the forward year, how many will still be vacant at its end, and can the forecast be trusted?*

```
x 0      216 240                       692 704      920 932     1148 1160     1376 1400
y 0  ┌────────┬───────────────────────────────────────────────────────────────────────┐
     │  RAIL  │  Seats to Fill                                                        │ 22–70
     │  navy  │  FTE hiring forecast against plan · <scope> · FY27, Jul 2026 to Jun 2027 │
  86 │        │ ┌ HERO (navy) ──────────┐ ┌ KPI 1 ───┐ ┌ KPI 2 ───┐ ┌ KPI 3 ───┐       │
     │        │ │ PIDs filled in FY27   │ │ to fill  │ │ vacant   │ │ wait     │       │ 86–258
     │        │ │ quota bar             │ │          │ │ (bridge) │ │          │       │
 272 │        │ ┌ Main card ─────────────────────────┐  ━━ How fast PIDs fill ━━━━━━━   │ 272–548
     │        │ │ title 44                           │  survival curves, legend         │
     │        │ │ FY chips                           │                                   │
     │        │ │ quarters: line, fan, budget step   │  ━━ Can we trust it ━━━━━━━━━━   │ 562–812
     │        │ │ quarter labels · legend            │  backtest, legend                │
 812 │        │ └────────────────────────────────────┘                                   │
 826 │        │  footnote                                                             │
 850 └────────┴───────────────────────────────────────────────────────────────────────┘
```

| Where | What it answers | Nothing chosen, period FY27 |
|---|---|---|
| Title | What am I looking at? | **Seats to Fill** · "FTE hiring forecast against plan · all of Arcadia Systems · FY27, Jul 2026 to Jun 2027" |
| Hero (navy) | How many PIDs will we fill? | **6,891** likely 6,301 to 7,543 · "89% of the 7,709 the FY27 Budget plans · FY26 filled 6,849 (88%)" · quota bar: tick at 89%, bracket 82% to 98% |
| KPI 1 | How much work is there? | PIDs to fill in FY27 **7,672** · Likely 7,006 to 8,371 · 902 waiting today |
| KPI 2 | What is left at the end? | Vacant at the end of FY27 **781** · Likely 696 to 892 · 121 fewer than today. Hover: the seat bridge |
| KPI 3 | How fast do we fill? | Median wait to fill **43 days** · 92% filled within 90 days · PIDs approved in the last four quarters |
| Main card | Is the pace holding? | "Hiring holds near the FY26 pace: about 1,650 to 1,850 fills a quarter". 20 quarters filled, FY27 forecast with its fan, the budget as a step, a chip per fiscal year (82%, 87%, 68%, 84%, 88%, 89%) |
| Right top | Who waits longest? | Survival curves by level band; legend L1–L2 Associate 35 days · L3–L4 Senior 44 · L5–L6 Manager 57 · L7+ Director 88 |
| Right bottom | Can we trust it? | "The method held 7 of 8 past quarters" · 3.6% average error |

**How the numbers tie.** Every central number is the average of the 100 simulated futures, so they add up: the bridge in the vacant card's hover reads 902 + 4,391 + 1,552 + 828 = 7,672 to fill, minus 6,891 filled = 781 vacant; the functions add up to the company; the four quarters add up to the year's fills. The ranges (P10 to P90 across the futures) do not add up and are never summed.

**The palette.** Navy `#13233A` (rail, hero, titles, filled line), slate `#5A6170` (secondary text, budget), ink `#1F2329`, page `#F3F3EF`, cards `#FFFFFF` with a 1 px `#E4E3DD` border and 14 px corners. One accent, teal: dark `#0F6E56` (forecast line, accent text), mid `#5DCAA5`, light `#D3EEE4` (the fan), tint `#EEF7F3` (the forecast region). Attainment bands, light to strong: `#EEF0F3`, `#DDE2E9`, `#B9C3D1`, `#9FD6C3`, `#5DCAA5`. Level bands: L1–L2 navy `#13233A`, L3–L4 `#4A5D78`, L5–L6 `#8C9BB0`, L7+ sand `#B8A888`. No red and green pair, no blue and orange pair.

---

## 1. Decisions

| # | Decision | Why |
|---|---|---|
| B1 | **One data source**, `custom_sql_seats_to_fill.sql`, extracted; seven row types side by side, every calculation tests its row type | The rail's selection must reach every card; a parameter reaches every sheet of one source |
| B2 | **No context filters.** The scope, the period and the row type are tested inside each formula (`[Is Draw] AND [In Scope] AND [In Period]`) | A FIXED LOD runs before ordinary filters; with the conditions inside the formula there is no filter order to remember (Dashboard #4, D5) |
| B3 | **Central numbers are averages** (sum over the draws ÷ the number of draws); ranges are `PERCENTILE({ INCLUDE [draw] : … }, 0.1 / 0.9)` | Averages add up (plan D11); the percentile pattern passed spike S3 to the decimal |
| B4 | **The drawn charts stand on a scaffold**: the Custom SQL's 94 `Scaffold` rows carry positions only (quarter, series, path order); FIXED LODs give them their values | The main chart needs three layers (fan, lines, budget step) and the bridge and quota bar need fixed slots; a scaffold makes each a plain mark, as the Sankey on #4 |
| B5 | **LODs stay shallow.** Per-quarter values are one FIXED LOD over raw rows; only the range nests (a FIXED over an INCLUDE), and nothing builds on another LOD | Dashboard #4's lesson: nested LODs are nested subqueries (#4 build, 5.8) |
| B6 | **The cascade of spikes S1 and S2**: string parameters, children store exclusions, a parent's click cleans its children with `REGEXP_REPLACE`, the last ticked option is locked, an option with nothing behind it is dimmed | Passed on Tableau Public (plan section 8) |
| B7 | **A Period capsule**: the forward year or one of its quarters (`p_Period` 0 to 4). The KPI band and the hero follow it; the chart marks it; time to fill and the backtest do not change | Budgets are read by year and by quarter (plan D8); one capsule gives both without a second page |
| B8 | **Hovers are sentences**, written like a headline; the one exception is the vacant card, whose hover is the seat bridge (a sheet in the tooltip) | Approved prototype |
| B9 | **Native rounded corners** (Tableau 2026.1+) on the hero, the cards and the main card; the right panels have no card, only a 2 px navy rule above | Approved prototype; no background image to keep in step |
| B10 | **Every text that follows the data is a calculation**; numbers in sentences use the comma pattern (4.7) | Tableau has no number format inside a string |
| B11 | **Tooltip command buttons off on every sheet; every clickable sheet has a deselect** (`zzTrue` → `zzFalse`) | Nothing stays highlighted after a click |
| B12 | Rules carried: executive officers (D-901) excluded upstream; the unit is the PID and an empty one is "vacant"; neutral wording; no arrow glyphs in text | Every Arcadia dashboard |

---

## 2. The data source

### 2.1 What the Custom SQL returns

One `SELECT` of eight `UNION ALL` blocks, 542,795 rows, about two seconds on SQL Server. Every row carries `row_type`, `quarter_offset` (0 = the quarter ending on the report date, 1 to 4 the forward year) and the report calendar's labels.

| `row_type` | Rows | Grain | Feeds |
|---|---:|---|---|
| Quarter | 21,720 | quarter × department × office | History: filled, vacant at the end, the budget; the lists' "something behind this option" |
| Draw | 396,400 | forward quarter × department × office × draw | Every forecast number |
| Survival | 105,294 | approval quarter × department × office × level band × requisition type × ten-day period | Time to fill |
| Backtest | 19,219 | origin × target quarter × department × office | The backtest panel |
| Accuracy | 20 | origin × target quarter, company | The method's own check (not on the page) |
| CW budget | 48 | fiscal year × function | The contingent budget line (Info text) |
| Scaffold | 94 | chart positions, no numbers | The main chart (82), the bridge (7), the quota bar (5) |

The scaffold, row by row (`chart_part`, `chart_series`, `chart_point`, `chart_x`):

| Part | Series | Rows | `chart_point` (path order) | `chart_x` |
|---|---|---:|---|---|
| Line | Filled | 20, quarters −19 to 0 | q + 19 | q + 19.5 |
| Line | Forecast | 5, quarters 0 to 4 | q + 19 | q + 19.5 |
| Line | Budget | 48, quarters −19 to 4, two each | 2(q + 19) + side | q + 19 + side (side 0 or 1: the step's left and right ends) |
| Fan | Upper | 5, quarters 0 to 4 | q + 19 | q + 19.5 |
| Fan | Lower | 4, quarters 1 to 4 | 100 − (q + 19) | q + 19.5 |
| Bridge | Waiting, Backfills, Net-new, Immediate refills, To fill, Filled, Vacant | 7 | 1 to 7 | 1 to 7 |
| Quota | Band 1 to Band 5 | 5 | 1 to 5 | 1 to 5 |

Quarter q sits at x = q + 19.5: FY22 Q1 at 0.5, FY26 Q4 (q = 0) at 19.5, FY27 Q4 at 23.5. The fan's points, in path order, run along its top from Jun 30, 2026 to FY27 Q4 and back along its bottom, so they close into one polygon.

### 2.2 Connect and extract

1. **File > New.** Connect > To a Server > **Microsoft SQL Server**: server `localhost`, port `1433`, database `ArcadiaHR`, SQL Server Authentication, user `sa`, the password from `docker exec arcadia-sql printenv MSSQL_SA_PASSWORD`, **Require SSL** unchecked.
2. Drag **New Custom SQL** onto the canvas and paste `tableau/custom_sql_seats_to_fill.sql` in full. OK.
3. Rename the data source **Seats to Fill**.
4. **Extract**. Save as `Seats to Fill.twb` in `ArcadiaHR/5 Seats to Fill/`; the extract goes in `Data Source Hyper` beside it.

**Types** (right-click > Convert to Dimension): `quarter_offset`, `fy_offset`, `fiscal_quarter`, `draw`, `period`, `days_from`, `days_to`, `origin_quarter_offset`, `horizon`, `chart_point`. Keep `chart_x` a measure.

**Aliases on `level_band`** (right-click > Aliases): L1-L2 → **L1–L2 Associate**, L3-L4 → **L3–L4 Senior**, L5-L6 → **L5–L6 Manager**, L7+ → **L7+ Director**. Every legend, label and tooltip shows the alias.

**Checkpoint 2.** Sheet `CHK Rows`: `row_type` on Rows, `CNT(row_type)` on Text, grand total on. Expected **Quarter 21,720 · Draw 396,400 · Survival 105,294 · Backtest 19,219 · Accuracy 20 · CW budget 48 · Scaffold 94 · Total 542,795**. Keep it, hidden, until publishing.

---

## 3. Parameters

None is shown on the dashboard: the rail and the popovers set them.

| Name | Type | Allowable | Current value | What sets it |
|---|---|---|---|---|
| `p_Functions` | String | All | empty | Function list, Reset. Holds `\|People\|Finance\|`; empty means every function |
| `p_DeptOff` | String | All | empty | Department list, a function click, Reset. Holds the **unticked** departments, `\|People>Talent Acquisition\|` |
| `p_Regions` | String | All | empty | Region list, Reset. `\|Asia Pacific\|` |
| `p_CountryOff` | String | All | empty | Country list, a region click, Reset. `\|Asia Pacific>Japan\|` |
| `p_OfficeOff` | String | All | empty | Office list, a region or country click, Reset. `\|Asia Pacific>India>Pune\|` |
| `p_Period` | Integer | List: 0, 1, 2, 3, 4 | **0** | Period list, Reset. 0 = the forward year, 1 to 4 = its quarters |
| `p_PeriodOpen`, `p_OrgOpen`, `p_LocOpen`, `p_InfoOpen` | Boolean | True / False | False | The rail capsules, ✕, Reset (one popover open at a time) |

The child strings store exclusions, so every child of a chosen parent starts ticked; each key carries its parents, so un-ticking a parent strips its children with one regular expression.

---

## 4. Core calculations

All calculations live on **Seats to Fill**. Each formula starts with a `//` line naming it, so it pastes as written; create them in the order below.

### 4.1 Row types and helpers

```
// Is Quarter
[row_type] = "Quarter"

// Is Draw
[row_type] = "Draw"

// Is Survival
[row_type] = "Survival"

// Is Backtest
[row_type] = "Backtest"

// Is Scaffold
[row_type] = "Scaffold"

// zzTrue
TRUE

// zzFalse
FALSE

// Close Panel
FALSE

// Empty Text
""

// Zero Period
0

// Hover Cell
"."
```

### 4.2 Scope (spike-proven)

```
// Function In
[p_Functions] = "" OR CONTAINS([p_Functions], "|" + [function_name] + "|")

// Dept Key
[function_name] + ">" + [department_name]

// Dept In
[Function In] AND NOT CONTAINS([p_DeptOff], "|" + [Dept Key] + "|")

// Region In
[p_Regions] = "" OR CONTAINS([p_Regions], "|" + [region] + "|")

// Country Key
[region] + ">" + [country_name]

// Country In
[Region In] AND NOT CONTAINS([p_CountryOff], "|" + [Country Key] + "|")

// Office Key
[region] + ">" + [country_name] + ">" + [office_name]

// Office In
[Country In] AND NOT CONTAINS([p_OfficeOff], "|" + [Office Key] + "|")

// In Scope
CASE [row_type]
WHEN "Accuracy" THEN TRUE
WHEN "Scaffold" THEN TRUE
WHEN "CW budget" THEN [Function In]
ELSE [Dept In] AND [Office In] END

// Activity   (what "something is behind this option" means: history PIDs opened, filled or waiting)
IF [row_type] = "Quarter" AND [quarter_offset] <= 0
THEN ZN([filled]) + ZN([vacant_end]) + ZN([opened_backfill]) + ZN([opened_net_new]) + ZN([opened_immediate]) END
```

### 4.3 Period and calendar words

```
// Period Start
IF [p_Period] = 0 THEN 1 ELSE [p_Period] END

// Period End
IF [p_Period] = 0 THEN 4 ELSE [p_Period] END

// In Period
[quarter_offset] >= [Period Start] AND [quarter_offset] <= [Period End]

// Is Year
[p_Period] = 0

// Fwd FY
{ MIN([forward_fiscal_year_label]) }

// Cur FY
{ MIN([current_fiscal_year_label]) }

// As Of
{ MIN([report_as_of_label]) }

// Fwd Range Text
{ MIN([forward_period_label]) }

// Period Quarter Label
{ MIN(IF [Is Scaffold] AND [chart_series] = "Budget" AND [quarter_offset] = [Period Start] THEN [quarter_label] END) }

// Period Months
{ MIN(IF [Is Scaffold] AND [chart_series] = "Budget" AND [quarter_offset] = [Period Start] THEN [quarter_months_label] END) }

// Year Ago Label
{ MIN(IF [Is Scaffold] AND [chart_series] = "Budget" AND [quarter_offset] = [Period Start] - 4 THEN [quarter_label] END) }

// Period Label
IF [Is Year] THEN [Fwd FY] ELSE [Period Quarter Label] END

// Period Span Text
IF [Is Year] THEN [Fwd FY] + ", " + [Fwd Range Text] ELSE [Period Quarter Label] + ", " + [Period Months] END

// Compare Label
IF [Is Year] THEN [Cur FY] ELSE [Year Ago Label] END
```

Expected with `p_Period` 0: Period Label "FY27", Period Span Text "FY27, Jul 2026 to Jun 2027", Compare Label "FY26". With 2: "FY27 Q2", "FY27 Q2, Oct – Dec 26", "FY26 Q2". Nothing names a year: next June, when the report date moves to Jun 30, 2027, every label reads FY28 without an edit.

### 4.4 The cascade: Function > Department

From spike S1, with the dim tests wrapped in `ZN()` (an option with nothing behind it sums to NULL, not 0).

```
// Function Dim
ZN(SUM(IF [Office In] THEN [Activity] END)) = 0

// Function Toggle
IF CONTAINS([p_Functions], "|" + [function_name] + "|")
THEN (IF [p_Functions] = "|" + [function_name] + "|" THEN "" ELSE REPLACE([p_Functions], "|" + [function_name] + "|", "|") END)
ELSE (IF [p_Functions] = "" THEN "|" + [function_name] + "|" ELSE [p_Functions] + [function_name] + "|" END) END

// Function Pick
IF [Function Dim] THEN [p_Functions] ELSE MIN([Function Toggle]) END

// DeptOff Without Function
IF REGEXP_REPLACE([p_DeptOff], "\|" + [function_name] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_DeptOff], "\|" + [function_name] + ">[^|]*", "") END

// Function DeptOff Pick
IF [Function Dim] THEN [p_DeptOff] ELSE MIN([DeptOff Without Function]) END

// Function Tick
IF [Function Dim] THEN "dim" ELSEIF [p_Functions] <> "" AND MIN([Function In]) THEN "on" ELSE "off" END

// Dept Visible
[Function In]

// Dept Ticked
MIN([Dept In])

// Dept Scope
SUM(IF [Dept In] AND [Office In] THEN [Activity] END)

// Scope Total
MIN({ FIXED : SUM(IF [Dept In] AND [Office In] THEN [Activity] END) })

// Dept Locked
[Dept Ticked] AND ZN([Scope Total]) - ZN([Dept Scope]) = 0

// Dept Dim
ZN(SUM(IF [Office In] THEN [Activity] END)) = 0

// Dept Toggle
IF CONTAINS([p_DeptOff], "|" + [Dept Key] + "|")
THEN (IF [p_DeptOff] = "|" + [Dept Key] + "|" THEN "" ELSE REPLACE([p_DeptOff], "|" + [Dept Key] + "|", "|") END)
ELSE (IF [p_DeptOff] = "" THEN "|" + [Dept Key] + "|" ELSE [p_DeptOff] + [Dept Key] + "|" END) END

// Dept Pick
IF [Dept Locked] OR [Dept Dim] THEN [p_DeptOff] ELSE MIN([Dept Toggle]) END

// Dept Tick
IF [Dept Dim] THEN "dim" ELSEIF [Dept Locked] THEN "locked" ELSEIF [Dept Ticked] THEN "on" ELSE "off" END

// Sub Heading   (only Commercial and Technology have real sub-functions)
IF [sub_function] = [function_name] THEN "" ELSE [sub_function] END
```

### 4.5 The cascade: Region > Country > Office

```
// Region Dim
ZN(SUM(IF [Dept In] THEN [Activity] END)) = 0

// Region Toggle
IF CONTAINS([p_Regions], "|" + [region] + "|")
THEN (IF [p_Regions] = "|" + [region] + "|" THEN "" ELSE REPLACE([p_Regions], "|" + [region] + "|", "|") END)
ELSE (IF [p_Regions] = "" THEN "|" + [region] + "|" ELSE [p_Regions] + [region] + "|" END) END

// Region Pick
IF [Region Dim] THEN [p_Regions] ELSE MIN([Region Toggle]) END

// CountryOff Without Region
IF REGEXP_REPLACE([p_CountryOff], "\|" + [region] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_CountryOff], "\|" + [region] + ">[^|]*", "") END

// OfficeOff Without Region
IF REGEXP_REPLACE([p_OfficeOff], "\|" + [region] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_OfficeOff], "\|" + [region] + ">[^|]*", "") END

// Region CountryOff Pick
IF [Region Dim] THEN [p_CountryOff] ELSE MIN([CountryOff Without Region]) END

// Region OfficeOff Pick
IF [Region Dim] THEN [p_OfficeOff] ELSE MIN([OfficeOff Without Region]) END

// Region Tick
IF [Region Dim] THEN "dim" ELSEIF [p_Regions] <> "" AND MIN([Region In]) THEN "on" ELSE "off" END

// Country Visible
[Region In]

// Country Ticked
MIN([Country In])

// Country Scope
SUM(IF [Dept In] AND [Office In] THEN [Activity] END)

// Country Locked
[Country Ticked] AND ZN([Scope Total]) - ZN([Country Scope]) = 0

// Country Dim
ZN(SUM(IF [Dept In] THEN [Activity] END)) = 0

// Country Toggle
IF CONTAINS([p_CountryOff], "|" + [Country Key] + "|")
THEN (IF [p_CountryOff] = "|" + [Country Key] + "|" THEN "" ELSE REPLACE([p_CountryOff], "|" + [Country Key] + "|", "|") END)
ELSE (IF [p_CountryOff] = "" THEN "|" + [Country Key] + "|" ELSE [p_CountryOff] + [Country Key] + "|" END) END

// Country Pick
IF [Country Locked] OR [Country Dim] THEN [p_CountryOff] ELSE MIN([Country Toggle]) END

// OfficeOff Without Country
IF REGEXP_REPLACE([p_OfficeOff], "\|" + [Country Key] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_OfficeOff], "\|" + [Country Key] + ">[^|]*", "") END

// Country OfficeOff Pick
IF [Country Locked] OR [Country Dim] THEN [p_OfficeOff] ELSE MIN([OfficeOff Without Country]) END

// Country Tick
IF [Country Dim] THEN "dim" ELSEIF [Country Locked] THEN "locked" ELSEIF [Country Ticked] THEN "on" ELSE "off" END

// Office Visible
[Country In]

// Office Ticked
MIN([Office In])

// Office Scope
SUM(IF [Dept In] AND [Office In] THEN [Activity] END)

// Office Locked
[Office Ticked] AND ZN([Scope Total]) - ZN([Office Scope]) = 0

// Office Dim
ZN(SUM(IF [Dept In] THEN [Activity] END)) = 0

// Office Toggle
IF CONTAINS([p_OfficeOff], "|" + [Office Key] + "|")
THEN (IF [p_OfficeOff] = "|" + [Office Key] + "|" THEN "" ELSE REPLACE([p_OfficeOff], "|" + [Office Key] + "|", "|") END)
ELSE (IF [p_OfficeOff] = "" THEN "|" + [Office Key] + "|" ELSE [p_OfficeOff] + [Office Key] + "|" END) END

// Office Pick
IF [Office Locked] OR [Office Dim] THEN [p_OfficeOff] ELSE MIN([Office Toggle]) END

// Office Tick
IF [Office Dim] THEN "dim" ELSEIF [Office Locked] THEN "locked" ELSEIF [Office Ticked] THEN "on" ELSE "off" END
```

Walk-through of a clean-up, with `p_OfficeOff` = `|Asia Pacific>India>Pune|Europe>Poland>Krakow|`: a click on the region Asia Pacific leaves `|Europe>Poland>Krakow|`; a click on the country India (its key `Asia Pacific>India`) also leaves `|Europe>Poland>Krakow|`; with only Pune excluded, either click leaves `|`, which becomes empty.

### 4.6 Scope words (capsules and the subtitle)

Counts of what is in scope, as FIXED LODs over the history rows (one level deep):

```
// N Functions In
{ COUNTD(IF [Is Quarter] AND [Function In] THEN [function_name] END) }

// N Depts In
{ COUNTD(IF [Is Quarter] AND [Dept In] THEN [department_name] END) }

// N Depts Offered
{ COUNTD(IF [Is Quarter] AND [Function In] THEN [department_name] END) }

// N Regions In
{ COUNTD(IF [Is Quarter] AND [Region In] THEN [region] END) }

// N Countries In
{ COUNTD(IF [Is Quarter] AND [Country In] THEN [country_name] END) }

// N Offices In
{ COUNTD(IF [Is Quarter] AND [Office In] THEN [office_name] END) }

// N Offices Offered
{ COUNTD(IF [Is Quarter] AND [Region In] THEN [office_name] END) }

// One Function
{ MIN(IF [Is Quarter] AND [Function In] THEN [function_name] END) }

// One Region
{ MIN(IF [Is Quarter] AND [Region In] THEN [region] END) }
```

```
// Org Field Text
IF [p_Functions] = "" THEN "All functions"
ELSEIF [N Functions In] = 1 THEN [One Function]
ELSE STR([N Functions In]) + " functions" END

// Org Sub Text
IF [p_Functions] = "" AND [p_DeptOff] = "" THEN "8 functions · 31 departments"
ELSE STR([N Depts In]) + " of " + STR([N Depts Offered]) + " departments" END

// Loc Field Text
IF [p_Regions] = "" THEN "All locations"
ELSEIF [N Regions In] = 1 THEN [One Region]
ELSE STR([N Regions In]) + " regions" END

// Loc Sub Text
IF [p_Regions] = "" AND [p_CountryOff] = "" AND [p_OfficeOff] = "" THEN "5 regions · 35 offices"
ELSE STR([N Countries In]) + " countries · " + STR([N Offices In]) + " of " + STR([N Offices Offered]) + " offices" END

// Org Is All
[p_Functions] = "" AND [p_DeptOff] = ""

// Loc Is All
[p_Regions] = "" AND [p_CountryOff] = "" AND [p_OfficeOff] = ""

// Scope Text
IF [Org Is All] AND [Loc Is All] THEN "all of Arcadia Systems"
ELSE (IF [Org Is All] THEN "" ELSE [Org Field Text] + (IF [p_DeptOff] = "" THEN "" ELSE " (" + [Org Sub Text] + ")" END) END)
   + (IF NOT [Org Is All] AND NOT [Loc Is All] THEN " in " ELSE "" END)
   + (IF [Loc Is All] THEN "" ELSE [Loc Field Text] + (IF [p_CountryOff] = "" AND [p_OfficeOff] = "" THEN "" ELSE " (" + STR([N Offices In]) + " offices)" END) END)
END

// Page Subtitle
"FTE hiring forecast against plan · " + [Scope Text] + " · " + [Period Span Text]
```

The "8 functions · 31 departments" and "5 regions · 35 offices" in the all-case are written in: they describe the company, not the selection. Expected: People with Talent Acquisition unticked → Org Field Text "People", Org Sub Text "3 of 4 departments", Scope Text "People (3 of 4 departments)"; Asia Pacific without Pune → "Asia Pacific (8 offices)", Loc Sub Text "6 countries · 8 of 9 offices"; both → "People (3 of 4 departments) in Asia Pacific (8 offices)".

### 4.7 Numbers inside text

Tableau has no number format inside a string. The comma pattern rounds and inserts a comma; the page never shows a million.

```
// Comma Pattern (copy and rename the field for each number below)
IF ISNULL(x) THEN "–"
ELSEIF ROUND(x, 0) >= 1000 THEN STR(DIV(INT(ROUND(x, 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND(x, 0)) % 1000), 3)
ELSE STR(INT(ROUND(x, 0))) END
```

Each `… Str` field in sections 5 to 9 is this pattern with its number in place of `x`. Percentages use `STR(INT(ROUND(x * 100, 0))) + "%"`.

---

## 5. The forecast numbers

### 5.1 Row-level pieces (NULL on every other row, so a percentile across draws sees only draws)

```
// D Fills
IF [Is Draw] AND [In Scope] AND [In Period] THEN [filled] END

// D Opened Backfill
IF [Is Draw] AND [In Scope] AND [In Period] THEN [opened_backfill] END

// D Opened Net New
IF [Is Draw] AND [In Scope] AND [In Period] THEN [opened_net_new] END

// D Opened Immediate
IF [Is Draw] AND [In Scope] AND [In Period] THEN [opened_immediate] END

// D Waiting   (waiting as the period opens)
IF [Is Draw] AND [In Scope] AND [quarter_offset] = [Period Start] THEN [vacant_start] END

// D Vacant End
IF [Is Draw] AND [In Scope] AND [quarter_offset] = [Period End] THEN [vacant_end] END

// D To Fill
IF [Is Draw] AND [In Scope] THEN ZN([D Waiting]) + ZN([D Opened Backfill]) + ZN([D Opened Net New]) + ZN([D Opened Immediate]) END

// H Plan Row   (the budget for the period)
IF [Is Quarter] AND [In Scope] AND [In Period] THEN [planned_net_new] + [planned_backfills] END

// H Compare Fills   (the same span a year earlier)
IF [Is Quarter] AND [In Scope] AND [quarter_offset] >= [Period Start] - 4 AND [quarter_offset] <= [Period End] - 4 THEN [filled] END

// H Compare Plan
IF [Is Quarter] AND [In Scope] AND [quarter_offset] >= [Period Start] - 4 AND [quarter_offset] <= [Period End] - 4 THEN [planned_net_new] + [planned_backfills] END

// H Vacant Now
IF [Is Quarter] AND [In Scope] AND [quarter_offset] = 0 THEN [vacant_end] END
```

`D To Fill` is NULL outside the draws (not 0), so the draw-less rows form no group of their own in `INCLUDE [draw]`.

### 5.2 The KPI numbers (aggregates; for the KPI and hero sheets, which have no dimension in the view)

```
// Draws
MIN({ COUNTD([draw]) })

// F Fills
SUM([D Fills]) / [Draws]

// F Fills Lo
PERCENTILE({ INCLUDE [draw] : SUM([D Fills]) }, 0.1)

// F Fills Hi
PERCENTILE({ INCLUDE [draw] : SUM([D Fills]) }, 0.9)

// F To Fill
SUM([D To Fill]) / [Draws]

// F To Fill Lo
PERCENTILE({ INCLUDE [draw] : SUM([D To Fill]) }, 0.1)

// F To Fill Hi
PERCENTILE({ INCLUDE [draw] : SUM([D To Fill]) }, 0.9)

// F Vacant
SUM([D Vacant End]) / [Draws]

// F Vacant Lo
PERCENTILE({ INCLUDE [draw] : SUM([D Vacant End]) }, 0.1)

// F Vacant Hi
PERCENTILE({ INCLUDE [draw] : SUM([D Vacant End]) }, 0.9)

// F Waiting
SUM([D Waiting]) / [Draws]

// P Plan
SUM([H Plan Row])

// F Att
[F Fills] / [P Plan]

// F Att Lo
[F Fills Lo] / [P Plan]

// F Att Hi
[F Fills Hi] / [P Plan]

// H Fills Compare
SUM([H Compare Fills])

// H Att Compare
SUM([H Compare Fills]) / SUM([H Compare Plan])

// V Now
SUM([H Vacant Now])

// F Vacant Change
[F Vacant] - [F Waiting]
```

Formats (Default Properties > Number Format): every `F` count Number, 0 decimals, thousands separator; `F Att`, `F Att Lo`, `F Att Hi`, `H Att Compare` Percentage, 0 decimals.

**Expected**, nothing chosen: F Fills **6,891** (6,301 to 7,543) · F To Fill **7,672** (7,006 to 8,371) · F Vacant **781** (696 to 892) · F Waiting 902 · P Plan 7,709 · F Att 89% (82% to 98%) · H Fills Compare 6,849, H Att Compare 88% · F Vacant Change −121. Technology: 2,504 (2,265 to 2,766) · 2,827 · 323 · 87% of 2,866. Period FY27 Q2: 1,734 (1,574 to 1,931) · to fill 2,556 · vacant 823 · plan 2,055 · 84% · FY26 Q2 1,782 (86%) · waiting 812. All rows of the check tables, sections 1 and 7.

### 5.3 The same numbers as LODs (for sheets that have a dimension in the view)

The quota bar and the bridge draw on scaffold rows, where an ordinary aggregate would be computed per mark and come back empty. Their sheets read FIXED versions, each one level deep over raw rows (the percentile nests an INCLUDE, B5):

```
// L Draws
{ COUNTD([draw]) }

// L Fills
{ SUM([D Fills]) } / [L Draws]

// L Waiting
{ SUM([D Waiting]) } / [L Draws]

// L Backfill
{ SUM([D Opened Backfill]) } / [L Draws]

// L Net New
{ SUM([D Opened Net New]) } / [L Draws]

// L Immediate
{ SUM([D Opened Immediate]) } / [L Draws]

// L To Fill
[L Waiting] + [L Backfill] + [L Net New] + [L Immediate]

// L Vacant
[L To Fill] - [L Fills]

// L Plan
{ SUM([H Plan Row]) }

// L Att
[L Fills] / [L Plan]

// L Att Lo
{ PERCENTILE({ INCLUDE [draw] : SUM([D Fills]) }, 0.1) } / [L Plan]

// L Att Hi
{ PERCENTILE({ INCLUDE [draw] : SUM([D Fills]) }, 0.9) } / [L Plan]
```

`L Vacant` = `L To Fill` − `L Fills` holds exactly because the draws keep vacant at the end = waiting + opened − filled (test f01); it equals F Vacant (781.35 nothing chosen).

### 5.4 Attainment band and the words around the numbers

```
// F Band
IF [F Att] < 0.25 THEN "0–25%" ELSEIF [F Att] < 0.5 THEN "25–50%" ELSEIF [F Att] < 0.75 THEN "50–75%"
ELSEIF [F Att] < 1 THEN "75–100%" ELSE "100%+" END

// F Fills Str        Comma Pattern on [F Fills]
// F Fills Lo Str     Comma Pattern on [F Fills Lo]
// F Fills Hi Str     Comma Pattern on [F Fills Hi]
// F To Fill Str      … and Lo, Hi
// F Vacant Str       … and Lo, Hi
// F Waiting Str      Comma Pattern on [F Waiting]
// F Backfill Str     Comma Pattern on SUM([D Opened Backfill]) / [Draws]
// F Net New Str      Comma Pattern on SUM([D Opened Net New]) / [Draws]
// F Immediate Str    Comma Pattern on SUM([D Opened Immediate]) / [Draws]
// P Plan Str         Comma Pattern on [P Plan]
// H Fills Compare Str  Comma Pattern on [H Fills Compare]

// F Att Str
STR(INT(ROUND([F Att] * 100, 0))) + "%"

// F Att Lo Str / F Att Hi Str / H Att Compare Str     the same on their numbers

// Vacant Change Text
STR(ABS(INT(ROUND([F Vacant Change], 0)))) + (IF ROUND([F Vacant Change], 0) < 0 THEN " fewer" ELSEIF ROUND([F Vacant Change], 0) > 0 THEN " more" ELSE " the same" END)
+ (IF [Period Start] = 1 THEN " than today" ELSE " than as the quarter opens" END)

// Waiting Text
[F Waiting Str] + (IF [Period Start] = 1 THEN " waiting today" ELSE " waiting as the quarter opens" END)
```

Expected: "121 fewer than today"; Q2: "11 more than as the quarter opens", "812 waiting as the quarter opens".

---

## 6. The KPI band

### 6.1 The hero card (navy)

```
// Hero Kicker
"PIDs FILLED IN " + [Period Label] + ", FORECAST"

// Hero Line 3
[F Att Str] + " of the " + [P Plan Str] + " the " + [Fwd FY] + " Budget plans"
+ (IF [Is Year] THEN "" ELSE " for " + [Period Quarter Label] END)
+ " · " + [Compare Label] + " filled " + [H Fills Compare Str] + " (" + [H Att Compare Str] + ")"
```

Sheet **Hero Text**: Marks Text; Label, three lines, left aligned, vertical top:

| Line | Content | Font |
|---|---|---|
| 1 | `<Hero Kicker>` | Tableau Semibold 9, `#B9C3D1` |
| 2 | `<F Fills>` · three spaces · `likely <F Fills Lo> to <F Fills Hi>` | value Tableau Bold 36 white; the range Tableau Book 12 `#E4E9F0` |
| 3 | `<Hero Line 3>` | Tableau Book 10, `#E4E9F0` |

Worksheet shading None (the container is navy), tooltip off, Detail `zzTrue`, `zzFalse`.

**The quota bar.** Five bands behind, the forecast as a white tick, its range as a white bracket.

```
// Quota Row
[Is Scaffold] AND [chart_part] = "Quota"

// Quota From
([chart_point] - 1) * 25

// Quota Width
25

// Quota Att
[L Att] * 100

// Quota Lo
[L Att Lo] * 100

// Quota Hi
[L Att Hi] * 100
```

Sheet **Hero Quota**: Filter `Quota Row` = True. Columns `MIN(Quota From)`; axis Fixed **0 to 125**, tick marks Fixed, major every 25 from 0, format Number Custom `0"%"`, labels Tableau Book 8 `#8A97A8`, no title, no axis line. Marks **Gantt Bar**, Size `MIN(Quota Width)`, size slider so the bars touch; Color `chart_series`: Band 1 `#EEF0F3`, Band 2 `#DDE2E9`, Band 3 `#B9C3D1`, Band 4 `#9FD6C3`, Band 5 `#5DCAA5`; opacity 100%, no border. Rows nothing (one lane). Analytics:
- **Reference Band**, Entire Table, from `MIN(Quota Lo)` to `MIN(Quota Hi)`: fill none, line solid 1.5 px **white**, no label, no tooltip.
- **Reference Line**, Entire Table, `MIN(Quota Att)`: solid 3 px **white**, no label, no tooltip.

Shading None, grid lines None, tooltip off. The band labels 0% … 100% come from the axis; "100%+" is the last band. Expected: tick at 89.4, bracket 81.7 to 97.8 (nothing chosen); Technology 87.4 (79.0 to 96.5); People without Talent Acquisition 71.7, in the third band.

### 6.2 The three cards

```
// KPI 1 Title
"PIDs to fill in " + [Period Label]

// KPI 2 Title
"Vacant at the end of " + [Period Label]

// KPI 3 Title
MIN("Median wait to fill")
```

| Sheet | Line 1 (Book 10.5 `#5A6170`) | Line 2 (Bold 30 navy `#13233A`) | Line 3 (Medium 10.5 ink `#1F2329`) | Line 4 (Book 10 `#5A6170`) |
|---|---|---|---|---|
| **KPI 1** | `<KPI 1 Title>` | `<F To Fill>` | `Likely <F To Fill Lo> to <F To Fill Hi>` | `<Waiting Text>` |
| **KPI 2** | `<KPI 2 Title>` | `<F Vacant>` | `Likely <F Vacant Lo> to <F Vacant Hi>` | `<Vacant Change Text>` |
| **KPI 3** | `<KPI 3 Title>` | `<SV Median Days>` then ` days` | `<SV Within 90 Str> filled within 90 days` | `PIDs approved in the last four quarters` |

Lines 1 and 2 at the top, lines 3 and 4 at the bottom: put an empty line between them (the label's own blank line) and size the sheet so the card's 18 px top and bottom padding hold. All three: Marks Text, left aligned, Detail `zzTrue`, `zzFalse`, shading None.

`KPI 3` reads the survival rows with table calculations (section 8): Filter `Recent Cohort` = True; Detail `days_to`; every table calculation **Compute Using `days_to`**; plus the table-calculation filter `SV Is Last` = True, which keeps one mark (the last period) whose label carries the window results. Its tooltip is its own (no hover cover): see 6.3.

Expected, nothing chosen: KPI 1 "PIDs to fill in FY27 · 7,672 · Likely 7,006 to 8,371 · 902 waiting today"; KPI 2 "Vacant at the end of FY27 · 781 · Likely 696 to 892 · 121 fewer than today"; KPI 3 "43 days · 92% filled within 90 days". Technology: 2,827 · 323 (9 fewer) · 47 days, 90%.

### 6.3 Hover texts

Each sentence opens like a headline. `Subject` names the selection.

```
// Subject
IF [Org Is All] AND [Loc Is All] THEN "Arcadia" ELSE [Scope Text] END

// Hero Tip 1
[Subject] + " should fill about " + [F Fills Str] + " PIDs in " + [Period Label] + ", " + [F Att Str]
+ " of the " + [P Plan Str] + " the budget plans."

// Hero Tip 2
"In 8 of 10 simulated futures the total lands between " + [F Fills Lo Str] + " and " + [F Fills Hi Str]
+ ", " + [F Att Lo Str] + " to " + [F Att Hi Str] + " of plan."

// Hero Tip 3
[Compare Label] + " filled " + [H Fills Compare Str] + ", " + [H Att Compare Str] + " of its budget."

// KPI 1 Tip 1
[F To Fill Str] + " PIDs need filling in " + [Period Label] + ": the " + [F Waiting Str]
+ (IF [Period Start] = 1 THEN " waiting today" ELSE " waiting as the quarter opens" END)
+ ", and the PIDs expected to open during the " + (IF [Is Year] THEN "year." ELSE "quarter." END)

// KPI 1 Tip 2
"About " + [F Backfill Str] + " backfills for people who leave or move, " + [F Net New Str]
+ " net-new in the budget and " + [F Immediate Str] + " refilled the day they open."

// KPI 2 Tip 1
"Of the " + [F To Fill Str] + " PIDs to fill in " + [Period Label] + ", about " + [F Fills Str]
+ " should be filled; " + [F Vacant Str] + " would still be vacant at its end."

// KPI 3 Tip 1   (a table calculation, on the KPI 3 sheet itself)
"Half the PIDs approved in the last four quarters were filled within " + [SV Median Days Str] + "; "
+ [SV Within 90 Str] + " within 90 days, a quarter."
```

**Hover covers** (as on #4): sheets **Hover Hero**, **Hover KPI 1**, **Hover KPI 2**: Rows and Columns `Hover Cell` (headers hidden); Marks **Square**, size slider far right, opacity **0%**, no border; Detail `Hover Cell`, `zzTrue`, `zzFalse`; tooltip below. Command buttons off. Each floats over its card at the card's size.

| Sheet | Tooltip (Tableau Book 11 ink `#1F2329`; numbers in the sentences already) |
|---|---|
| Hover Hero | `<Hero Tip 1>` / `<Hero Tip 2>` Book 10 `#5A6170` / `<Hero Tip 3>` Book 10 `#5A6170` |
| Hover KPI 1 | `<KPI 1 Tip 1>` / `<KPI 1 Tip 2>` Book 10 `#5A6170` |
| Hover KPI 2 | `<KPI 2 Tip 1>` / the sheet **Bridge Tip** (Insert > Sheets; max width 420, max height 230, filter **none**) / `The seat bridge · averages of 100 simulated futures, so it adds up exactly` Book 9 `#5A6170` |
| KPI 3 (its own tooltip) | `<KPI 3 Tip 1>` / `Open PIDs count as still waiting, so recent quarters are not read as fast. The curves on the right show each level.` Book 10 `#5A6170` |

Expected hovers, nothing chosen: "Arcadia should fill about 6,891 PIDs in FY27, 89% of the 7,709 the budget plans." / "In 8 of 10 simulated futures the total lands between 6,301 and 7,543, 82% to 98% of plan." / "FY26 filled 6,849, 88% of its budget." · "7,672 PIDs need filling in FY27: the 902 waiting today, and the PIDs expected to open during the year." / "About 4,391 backfills for people who leave or move, 1,552 net-new in the budget and 828 refilled the day they open." · "Of the 7,672 PIDs to fill in FY27, about 6,891 should be filled; 781 would still be vacant at its end." · "Half the PIDs approved in the last four quarters were filled within 43 days; 92% within 90 days, a quarter."

### 6.4 The seat bridge (the vacant card's hover)

```
// Bridge Row
[Is Scaffold] AND [chart_part] = "Bridge"

// Bridge Size
CASE [chart_point] WHEN 1 THEN [L Waiting] WHEN 2 THEN [L Backfill] WHEN 3 THEN [L Net New]
WHEN 4 THEN [L Immediate] WHEN 5 THEN [L To Fill] WHEN 6 THEN [L Fills] WHEN 7 THEN [L Vacant] END

// Bridge Start
CASE [chart_point] WHEN 2 THEN [L Waiting] WHEN 3 THEN [L Waiting] + [L Backfill]
WHEN 4 THEN [L Waiting] + [L Backfill] + [L Net New] WHEN 6 THEN [L Vacant] ELSE 0 END

// Bridge Kind
CASE [chart_point] WHEN 1 THEN "waiting" WHEN 5 THEN "to fill" WHEN 6 THEN "filled" WHEN 7 THEN "vacant" ELSE "opens" END

// Bridge Label Plain
IF [chart_point] = 1 OR [chart_point] = 5 OR [chart_point] = 7 THEN [Bridge Size] END

// Bridge Label Plus
IF [chart_point] >= 2 AND [chart_point] <= 4 THEN [Bridge Size] END

// Bridge Label Minus
IF [chart_point] = 6 THEN [Bridge Size] END
```

Formats: `Bridge Label Plain` Number `#,##0`; `Bridge Label Plus` Custom `+#,##0`; `Bridge Label Minus` Custom `"−"#,##0` (a minus sign, not a hyphen). Aliases on `chart_series`: Waiting → "Waiting as it opens", To fill → "PIDs to fill", Filled → "Filled", Vacant → "Vacant at the end".

Sheet **Bridge Tip**: Filter `Bridge Row` = True. Columns `chart_point` (discrete, header hidden), then `chart_series` (discrete; header at the bottom, Book 9 `#5A6170`, wrap on). Rows `MIN(Bridge Start)`: Marks **Gantt Bar**, Size `MIN(Bridge Size)`; axis hidden, starting at 0. Color `Bridge Kind`: waiting navy `#13233A`, opens `#9FB0C6`, to fill teal `#0F6E56`, filled `#5DCAA5`, vacant slate `#5A6170`. Label `<MIN(Bridge Label Plain)><MIN(Bridge Label Plus)><MIN(Bridge Label Minus)>` Tableau Semibold 9 navy, alignment top, center. Shading None, every line None. Size on its own: 400 × 210.

Expected (check tables, section 2): 902 · +4,391 · +1,552 · +828 · 7,672 · −6,891 · 781. Technology 332 · +1,605 · +637 · +254 · 2,827 · −2,504 · 323. FY27 Q2: 812 · +1,121 · +418 · +206 (opened in Q2) · 2,556 · −1,734 · 823.

---

## 7. The main chart

### 7.1 The per-quarter values (one FIXED LOD per number, over raw rows)

```
// Q Filled
{ FIXED [quarter_offset] : SUM(IF [Is Quarter] AND [In Scope] THEN [filled] END) }

// Q Budget
{ FIXED [quarter_offset] : SUM(IF [Is Quarter] AND [In Scope] THEN [planned_net_new] + [planned_backfills] END) }

// Q Vacant
{ FIXED [quarter_offset] : SUM(IF [Is Quarter] AND [In Scope] THEN [vacant_end] END) }

// Q Forecast
{ FIXED [quarter_offset] : SUM(IF [Is Draw] AND [In Scope] THEN [filled] END) / COUNTD([draw]) }

// Q Forecast Vacant
{ FIXED [quarter_offset] : SUM(IF [Is Draw] AND [In Scope] THEN [vacant_end] END) / COUNTD([draw]) }

// Q P10
{ FIXED [quarter_offset] : PERCENTILE({ INCLUDE [draw] : SUM(IF [Is Draw] AND [In Scope] THEN [filled] END) }, 0.1) }

// Q P90
{ FIXED [quarter_offset] : PERCENTILE({ INCLUDE [draw] : SUM(IF [Is Draw] AND [In Scope] THEN [filled] END) }, 0.9) }
```

A history quarter has no draws, so `COUNTD([draw])` is 0 and the division returns NULL: the forecast exists only for quarters 1 to 4.

### 7.2 The marks

```
// Main Chart Row
[Is Scaffold] AND ([chart_part] = "Line" OR [chart_part] = "Fan")

// Line Y
CASE [chart_series]
WHEN "Filled" THEN [Q Filled]
WHEN "Forecast" THEN (IF [quarter_offset] = 0 THEN [Q Filled] ELSE [Q Forecast] END)
WHEN "Budget" THEN [Q Budget] END

// Fan Y
CASE [chart_series]
WHEN "Upper" THEN (IF [quarter_offset] = 0 THEN [Q Filled] ELSE [Q P90] END)
WHEN "Lower" THEN [Q P10] END

// End Label
IF [chart_series] = "Forecast" AND [quarter_offset] = 4 THEN [Q Forecast] END

// Period From
[Period Start] + 19

// Period To
[Period End] + 20
```

The forecast line and the fan start at the last filled quarter (Jun 30, 2026), so the history runs into the forecast without a gap. The budget rows sit at both ends of each quarter (`chart_x` q + 19 and q + 20), so one line through them, in path order, is a step.

Sheet **Main Chart**:
1. Filter `Main Chart Row` = True.
2. Columns `MIN(chart_x)`: axis Fixed **0 to 24**, hidden (no header).
3. Rows `MIN(Fan Y)`, then `MIN(Line Y)`; Dual Axis; Synchronize Axis. Left axis: shown, no title, Automatic range with **Include zero off**, labels Tableau Book 9 `#8C9BB0`, format Number `#,##0`; right axis hidden. Drag the left axis to **44 px** wide (the two helper sheets in 7.4 use the same width, so the quarters line up).
4. Marks `MIN(Fan Y)`: **Polygon**; Path `chart_point`; Detail `chart_part`; Color one color, teal light `#D3EEE4`, opacity 100%, no border. Tooltip: `Likely range: 8 in 10 simulated futures` Book 9.
5. Marks `MIN(Line Y)`: **Line**; Path `chart_point`; Detail `chart_series`; Color `chart_series`: Filled navy `#13233A`, Forecast teal `#0F6E56`, Budget slate `#5A6170`; Size `chart_series`: Filled and Forecast large, Budget small (two steps of the slider). If your Tableau offers a line pattern on the Path card, set Forecast and Budget **dashed**. Label `MIN(End Label)`, Tableau Bold 10 teal `#0F6E56`, alignment right, label only the marks that have one.
6. Analytics, on the Columns axis:
   - **Reference Band**, constant **20 to 24**, fill teal tint `#EEF7F3`, no line: the forecast year.
   - **Reference Band**, `MIN(Period From)` to `MIN(Period To)`, fill `#DDEFE7`, no line: the period chosen in the rail (the whole year when it is FY27).
   - **Reference Lines**, constants 4, 8, 12, 16: solid 1 px `#E4E3DD`, no label (the fiscal-year boundaries).
   - **Reference Line**, constant 20: dotted 1 px navy `#13233A`, label custom `Data ends · forecast starts` Tableau Semibold 8 navy, at the bottom.
7. Grid lines: rows solid 1 px `#ECEDEA`; columns none. Zero lines, axis rulers, borders None. Shading None (the card is white).
8. Tooltip (both cards): `<Line Tip 1>` Book 11 ink / `<Line Tip 2>` Book 10 `#5A6170` (7.5).

### 7.3 The title

```
// Year Forecast
{ SUM(IF [Is Draw] AND [In Scope] THEN [filled] END) } / [L Draws]

// Year Current
{ SUM(IF [Is Quarter] AND [In Scope] AND [fy_offset] = 0 THEN [filled] END) }

// Quarter Low
{ MIN([Q Forecast]) }

// Quarter High
{ MAX([Q Forecast]) }

// Pace Change
[Year Forecast] / [Year Current] - 1

// Main Title Text
(IF ABS([Pace Change]) <= 0.05 THEN "Hiring holds near the " + [Cur FY] + " pace"
 ELSEIF [Pace Change] > 0 THEN "Hiring picks up from " + [Cur FY]
 ELSE "Hiring slows from " + [Cur FY] END)
+ ": about " + [Quarter Low Str] + " to " + [Quarter High Str] + " fills a quarter"

// Main Subtitle
"PIDs filled each quarter, the " + [Fwd FY] + " forecast with the range that holds 8 in 10 simulated futures, and the budget"
```

`Quarter Low Str` and `Quarter High Str` are the comma pattern on `ROUND([Quarter Low], -1)` and `ROUND([Quarter High], -1)`. `Quarter Low` and `Quarter High` are the one place an LOD reads another (24 quarters, no measurable cost). Sheet **Main Title**: Text, `<Main Title Text>` Tableau Semibold 13 navy / `<Main Subtitle>` Book 10 `#5A6170`; Left, Top; Detail `zzTrue`, `zzFalse`; tooltip off.

Expected: "Hiring holds near the FY26 pace: about 1,650 to 1,850 fills a quarter"; Technology "about 600 to 650"; Asia Pacific "about 490 to 550" (check tables, section 4).

### 7.4 Fiscal-year chips and quarter labels

The chips sit in their own sheet above the chart, the quarter labels in one below, on the same 0 to 24 axis and the same 44 px left axis, so they line up with the quarters.

```
// FY Fills Hist
{ FIXED [fiscal_year_label] : SUM(IF [Is Quarter] AND [In Scope] AND [fy_offset] <= 0 THEN [filled] END) }

// FY Fills Fcst
{ FIXED [fiscal_year_label] : SUM(IF [Is Draw] AND [In Scope] THEN [filled] END) / COUNTD([draw]) }

// FY Plan
{ FIXED [fiscal_year_label] : SUM(IF [Is Quarter] AND [In Scope] THEN [planned_net_new] + [planned_backfills] END) }

// FY Att
IF MIN([fy_offset]) = 1 THEN MIN([FY Fills Fcst]) / MIN([FY Plan]) ELSE MIN([FY Fills Hist]) / MIN([FY Plan]) END

// FY Chip Shape
IF [FY Att] < 0.75 THEN "d5_chip_slate" ELSE "d5_chip_teal" END

// FY Label X
MIN([chart_x]) + 0.15

// FY Chip X
MAX([chart_x]) - 0.65

// Budget Row
[Is Scaffold] AND [chart_series] = "Budget"

// Quarter Tick Row
[Budget Row] AND [chart_point] % 2 = 0

// Quarter Tick Text
"Q" + STR([fiscal_quarter])

// Axis Pad
MIN(0)
```

Sheet **FY Chips**: Filter `Budget Row` = True. Columns `FY Label X` then `FY Chip X`; Dual Axis, Synchronize; both Fixed **0 to 24**, hidden. Rows `Axis Pad`: axis shown, **44 px wide**, no labels, no ticks, no title (a spacer). Detail `fiscal_year_label` on both cards.
- Card `FY Label X`: **Text**, `<fiscal_year_label>` Tableau Semibold 10 navy, left.
- Card `FY Chip X`: **Shape** `FY Chip Shape` (palette **Arcadia D5**: `d5_chip_teal.png`, `d5_chip_slate.png`, 56 × 18 pills), size so the pill is 56 px; Label `<FY Att>` (Percentage, 0 decimals) Tableau Semibold 9 navy, center, middle, on top of the pill.

Sheet **Quarter Axis**: Filter `Quarter Tick Row` = True. Columns `MIN(chart_x)`, Fixed 0 to 24, hidden; Rows `Axis Pad` as above (44 px spacer). Detail `quarter_offset`. Marks Text `<Quarter Tick Text>`, Book 9 `#8C9BB0`, center. (`MIN(chart_x)` of the left end plus the label centered on the half: put `MIN(chart_x) + 0.5` on Columns instead if your labels sit at the quarter's edge.)

Both: shading None, every line None, tooltip off. Expected chips (check tables, section 3): 82% · 87% · **68%** (slate) · 84% · 88% · 89%; People without Talent Acquisition 71% · 82% · 59% · 77% · 73% · 72% (four slate).

The legend under the chart is the image `d5_main_legend.png` (filled line, forecast, likely range, budget), 600 × 18.

### 7.5 The chart's hover

```
// Line Tip 1
IF [chart_series] = "Filled" THEN [quarter_label] + ", " + [quarter_months_label] + ": " + [Q Filled Str] + " PIDs filled, "
   + STR(INT(ROUND([Q Filled] / [Q Budget] * 100, 0))) + "% of the quarter's budget of " + [Q Budget Str] + "."
ELSEIF [chart_series] = "Forecast" AND [quarter_offset] > 0 THEN [quarter_label] + ", " + [quarter_months_label] + ": about "
   + [Q Forecast Str] + " fills forecast, likely " + [Q P10 Str] + " to " + [Q P90 Str] + "."
ELSEIF [chart_series] = "Budget" THEN [quarter_label] + " budget: " + [Q Budget Str] + " planned fills." END

// Line Tip 2
IF [chart_series] = "Filled" THEN [Q Vacant Str] + " PIDs vacant at the quarter end."
ELSEIF [chart_series] = "Forecast" AND [quarter_offset] > 0 THEN "The budget plans " + [Q Budget Str] + ". About "
   + [Q Forecast Vacant Str] + " PIDs would still be vacant at the quarter end." END
```

(`Q … Str` are the comma pattern on each `Q` value.) Expected: FY26 Q4 "FY26 Q4, Apr – Jun 26: 1,717 PIDs filled, 89% of the quarter's budget of 1,934." / "902 PIDs vacant at the quarter end."; FY27 Q1 "FY27 Q1, Jul – Sep 26: about 1,847 fills forecast, likely 1,748 to 1,965." / "The budget plans 1,852. About 812 PIDs would still be vacant at the quarter end."

---

## 8. How fast PIDs fill

From spike S4: Kaplan–Meier as a table calculation. The data stores PIDs at risk and fills per ten-day period, which add up over any selection; the curve is rebuilt from them.

```
// Recent Cohort
[Is Survival] AND [In Scope] AND [quarter_offset] >= -3

// SV At Risk
SUM(IF [Recent Cohort] THEN [at_risk] END)

// SV Filled
SUM(IF [Recent Cohort] THEN [sv_filled] END)

// SV Hazard
ZN([SV Filled]) / [SV At Risk]

// SV Filled Share
1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001))))

// SV Median Days
WINDOW_MAX(
  IF 1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001)))) >= 0.5
     AND 1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001))) - LN(MAX(1 - [SV Hazard], 0.0001))) < 0.5
  THEN MIN([days_from]) + 10 * (0.5 - (1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001))) - LN(MAX(1 - [SV Hazard], 0.0001)))))
       / ((1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001))))) - (1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001))) - LN(MAX(1 - [SV Hazard], 0.0001)))))
  END)

// SV Within 90
WINDOW_MAX(IF MIN([days_to]) = 89 THEN 1 - EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001)))) END)

// SV Is Last
LAST() = 0

// SV Median Days Str
IF ISNULL([SV Median Days]) THEN "over 200 days" ELSE STR(INT(ROUND([SV Median Days], 0))) + " days" END

// SV Within 90 Str
STR(INT(ROUND([SV Within 90] * 100, 0))) + "%"
```

Why one long formula. A period's share before it is the running sum without its own term (`RUNNING_SUM(…) − LN(…)`), so the crossing of 50% and its straight-line interpolation sit inside one calculation, under one Compute Using. Writing them as separate calculations would nest table calculations, each with its own addressing.

**Every table calculation on this page: Compute Using `days_to` only**, so `level_band` (when on the view) partitions.

Sheet **Survival**: Filter `Recent Cohort` = True. Columns `days_to` (dimension, **continuous**), axis Fixed **0 to 150**, hidden. Rows `SV Filled Share`, axis Fixed **0 to 1**, ticks at 0, 0.5, 1, format Percentage 0 decimals, labels Book 9 `#8C9BB0`, no title. Marks **Line**, Path > Line Type **Step**; Color `level_band` (L1–L2 Associate `#13233A`, L3–L4 Senior `#4A5D78`, L5–L6 Manager `#8C9BB0`, L7+ Director `#B8A888`); size two steps up. Reference lines on columns: constants 29, 59, 89, dotted 1 px `#D5DBE4`, labels custom `30 days`, `60 days`, `90 days` Book 8 `#5A6170` at the bottom. Grid lines rows `#ECEDEA`. Tooltip: `<level_band>: <SV Filled Share> of PIDs filled within <days_to> days.` (one more than `days_to`: write it as a calculation `MIN([days_to]) + 1` if you prefer exact words).

Sheet **Level Legend**: Filter `Recent Cohort` = True; the table-calculation filter `SV Is Last` = True. Columns `Legend Col`, Rows `Legend Row` (both discrete, headers hidden), Detail `level_band`, `days_to`. Marks Text: `━━  ` (Match Mark Color) then `<level_band>` Book 10 ink then `  ·  <SV Median Days Str>` Book 10 `#5A6170`; Color `level_band`. Left aligned.

```
// Legend Col
IF [level_band] = "L1-L2" OR [level_band] = "L5-L6" THEN 1 ELSE 2 END

// Legend Row
IF [level_band] = "L1-L2" OR [level_band] = "L3-L4" THEN 1 ELSE 2 END
```

Panel title (a dashboard text object, static): **How long PIDs wait, by level** Tableau Semibold 13 navy / "Share filled by days waited, PIDs approved in the last four quarters; each level's median wait beside its name" Book 10 `#5A6170`.

Expected (check tables, section 5): nothing chosen L1–L2 35 days · L3–L4 44 · L5–L6 57 · L7+ 88; all levels 43 days and 92.1% within 90 (KPI 3). At 30 / 60 / 90 days, all levels: 24.1% / 73.8% / 92.1%. Technology 47 days, 89.9%; People without Talent Acquisition: L7+ has no PIDs at risk and leaves the legend.

---

## 9. Can we trust it

```
// BT Row
[Is Backtest] AND [In Scope] AND [horizon] = 1

// BT Mean
SUM(IF [BT Row] THEN [filled_mean] END)

// BT Var
SUM(IF [BT Row] THEN [filled_var] END)

// BT CV
MIN(IF [BT Row] THEN [filled_shared_cv] END)

// BT SD
SQRT([BT Var] + POWER([BT CV] * [BT Mean], 2))

// BT Low
IF [BT Mean] - 1.2816 * [BT SD] < 0 THEN 0 ELSE [BT Mean] - 1.2816 * [BT SD] END

// BT High
[BT Mean] + 1.2816 * [BT SD]

// BT Span
[BT High] - [BT Low]

// BT Actual
SUM(IF [BT Row] THEN [actual_filled] END)

// BT In
IF [BT Actual] >= [BT Low] AND [BT Actual] <= [BT High] THEN "in range" ELSE "outside" END

// BT In Count
WINDOW_SUM(IF [BT Actual] >= [BT Low] AND [BT Actual] <= [BT High] THEN 1 ELSE 0 END)

// BT Error
WINDOW_AVG(ABS([BT Mean] - [BT Actual]) / [BT Actual])

// BT Title
"The method held " + STR([BT In Count]) + " of " + STR(SIZE()) + " past quarters"

// BT Subtitle
"Forecast range one quarter ahead, against what happened · " + STR(ROUND([BT Error] * 100, 1)) + "% average error"
```

Sheet **Backtest**: Filter `BT Row` = True. Columns `quarter_offset` (discrete, header hidden), then `quarter_label` (header at the bottom, Book 8 `#8C9BB0`). Rows `BT Low`, then `BT Actual`; Dual Axis, Synchronize; left axis shown, no title, Book 9 `#8C9BB0`, `#,##0`, include zero off; right hidden.
- Card `BT Low`: **Gantt Bar**, Size `BT Span`, color teal light `#D3EEE4`, width about 40%. Analytics: **Reference Line**, Per Cell, `BT Mean`, solid 2 px teal `#0F6E56`, no label.
- Card `BT Actual`: **Shape**, Shape `BT In`: in range → filled circle, outside → open circle (default palette); color navy; size small.
- Tooltip (both): `<quarter_label>, forecast one quarter ahead: <BT Low> to <BT High> fills; <BT Actual> filled, <BT In>.`

Sheet **Backtest Title**: Filter `BT Row` = True; Detail `quarter_offset`; table-calculation filter `SV Is Last`-style: create `BT Is Last` = `LAST() = 0` and filter True; Compute Using `quarter_offset` for every table calculation. Text `<BT Title>` Semibold 13 navy / `<BT Subtitle>` Book 10 `#5A6170`. Tooltip off.

The legend under it is the image `d5_backtest_legend.png` (forecast range, actual in range, outside).

Expected (check tables, section 6): nothing chosen "The method held 7 of 8 past quarters · 3.6% average error"; Technology 6 of 8, 4.7%; Asia Pacific 7 of 8, 3.0%; FY26 Q3 outside (1,506 to 1,638 against 1,672).

---

## 10. The rail

Same frame as #4: a 216 px navy `#13233A` container; controls are one-mark sheets whose Shape draws the control and whose label is the text (custom shapes from **Arcadia D4**: `d4_field_capsule.png` white, `d4_field_capsule_dark.png` dark, `d2_info_open.png`, `d2_info_close.png`, `d4_reset.png`). A sheet with only aggregates and constants on its shelves draws one mark.

```
// Period Field Text
[Period Label] + " forecast"

// Org Capsule Shape
IF [Org Is All] THEN "d4_field_capsule_dark" ELSE "d4_field_capsule" END

// Loc Capsule Shape
IF [Loc Is All] THEN "d4_field_capsule_dark" ELSE "d4_field_capsule" END

// Org Text Light       (on the white capsule)
IF NOT [Org Is All] THEN [Org Field Text] END

// Org Text Dark        (on the dark capsule)
IF [Org Is All] THEN [Org Field Text] END

// Loc Text Light / Loc Text Dark      the same with [Loc Is All] and [Loc Field Text]

// Toggle Period Panel
NOT [p_PeriodOpen]

// Toggle Org Panel
NOT [p_OrgOpen]

// Toggle Loc Panel
NOT [p_LocOpen]

// Toggle Info
NOT [p_InfoOpen]

// Info Shape
IF [p_InfoOpen] THEN "d2_info_close" ELSE "d2_info_open" END

// Rail Line 1
"Data to " + [As Of]

// Rail Line 2
"Forecast " + [Fwd Range Text]
```

| Sheet | Shape | Label | Detail | Tooltip |
|---|---|---|---|---|
| **Period Field** | `d4_field_capsule.png` (always white: the period is always a choice) | `<Period Field Text>` Semibold 9 navy, left | `Toggle Period Panel`, `Close Panel`, `zzTrue`, `zzFalse` | "Choose the period" |
| **Org Field** | `Org Capsule Shape` | `<Org Text Light>` Semibold 9 navy + `<Org Text Dark>` Medium 9 `#E4E9F0`, left | `Toggle Org Panel`, `Close Panel`, `zzTrue`, `zzFalse` | "Choose functions and departments" |
| **Loc Field** | `Loc Capsule Shape` | `<Loc Text Light>` + `<Loc Text Dark>` | `Toggle Loc Panel`, … | "Choose regions, countries and offices" |
| **Org Sub**, **Loc Sub** | none (Text) | `<Org Sub Text>` / `<Loc Sub Text>` Book 9 `#8A97A8` (white `#E4E9F0` when a selection is on: two runs as above) | `zzTrue`, `zzFalse` | off |
| **Reset** | `d4_reset.png` | none | `Empty Text`, `Zero Period`, `Close Panel`, `zzTrue`, `zzFalse` | "Reset to default view" |
| **Info Button** | `Info Shape` | none | `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse` | "How the forecast works" |
| **Rail As Of** | none (Text) | `<Rail Line 1>` Semibold 9 `#E4E9F0` / `<Rail Line 2>` Book 9 `#B9C3D1` / `<Draws>` simulated futures Book 9 `#B9C3D1` | `zzTrue`, `zzFalse` | off |

Sheet **Page Title**: Text, `Seats to Fill` Tableau Bold 18 navy / `<Page Subtitle>` Book 11 `#5A6170`; Left, Top; Detail `zzTrue`, `zzFalse`; tooltip off.

Expected: nothing chosen "All functions" (dark) "8 functions · 31 departments"; Technology "Technology" (white) "8 of 8 departments"; Asia Pacific "Asia Pacific" (white) "6 countries · 9 of 9 offices". Rail foot: "Data to Jun 30, 2026" / "Forecast Jul 2026 to Jun 2027" / "100 simulated futures".

---

## 11. The popovers

Each hangs from the rail's right edge (x 216): a navy `#13233A` vertical container, padding 0, no border, shown by its open flag; header 44 px (title Tableau Bold 12 white, ✕ at the right), line 9 px (`d2_popover_line_wide.png`), body, footer 28 px (Book 9 `#8FA0B8`). The ✕ sheets (**Period Close**, **Org Close**, **Loc Close**) are the #4 pattern: Text `✕` Book 12 `#B8C0CC`, Detail `zzFalse`, `zzTrue`, `Close Panel`, tooltip "Close".

The list sheets are the spikes' lists, restyled for the navy body: Marks **Shape** with the tick files `d4_tick_on.png` / `d4_tick_off.png` (Arcadia D4; the files carry the state, so no color on the shape), the name as the label in three runs so a dimmed or locked option reads differently:

```
// Function Shape     IF [Function Tick] = "on" THEN "d4_tick_on" ELSE "d4_tick_off" END
// Dept Shape         IF [Dept Tick] = "on" OR [Dept Tick] = "locked" THEN "d4_tick_on" ELSE "d4_tick_off" END
// Region Shape, Country Shape, Office Shape     the same on their Tick

// Function Name On     IF [Function Tick] <> "dim" THEN MIN([function_name]) END
// Function Name Dim    IF [Function Tick] = "dim" THEN MIN([function_name]) END
// Dept Name On         IF [Dept Tick] = "on" OR [Dept Tick] = "off" THEN MIN([department_name]) END
// Dept Name Locked     IF [Dept Tick] = "locked" THEN MIN([department_name]) END
// Dept Name Dim        IF [Dept Tick] = "dim" THEN MIN([department_name]) END
// … the same three for regions, countries, offices
```

Label runs: `  <… Name On>` Book 9.5 `#E4E9F0`, `<… Name Locked>` Book 9.5 `#8FA0B8`, `<… Name Dim>` Book 9.5 `#4F6178` (two leading spaces in the same run as the field). Every list: Filter `Is Quarter` = True (plus its Visible filter and the deselect); Detail its Pick fields, `zzTrue`, `zzFalse`; row headers on the left as group headings (Book 8.5 `#8FA0B8`); row banding none; tooltip off; Fit Entire View.

| Popover | x, y, w × h | Body |
|---|---|---|
| **Period Popover** | 216, 108, 360 × 260 | **Period List**: Filter `Is Scaffold` and `chart_series` = "Forecast" (five rows, quarters 0 to 4). Rows `quarter_offset` (header hidden). Shape `Period Shape` = `IF [quarter_offset] = [p_Period] THEN "d4_tick_on" ELSE "d4_tick_off" END`; label `<Period Option Text>` (below). Detail `quarter_offset`, `Close Panel`, `zzTrue`, `zzFalse`. Footer "Time to fill and the backtest do not change with the period." |
| **Org Popover** | 216, 188, 640 × 640 | Two columns: **Function List** 220 (Rows `function_name`, header hidden; Shape `Function Shape`; Detail `Function Pick`, `Function DeptOff Pick`) and **Dept List** 420 (Filter `Dept Visible` = True; Rows `function_name`, `Sub Heading` as headings, `department_name` header hidden; Shape `Dept Shape`; Detail `Dept Pick`). Footer "Choose functions; every department starts ticked. The last one ticked cannot be unticked; a greyed one has nothing in the chosen locations." |
| **Loc Popover** | 216, 268, 760 × 560 | Three columns: **Region List** 200 (Rows `region`), **Country List** 260 (Filter `Country Visible`; Rows `region` heading, `country_name`), **Office List** 300 (Filter `Office Visible`; Rows `country_name` heading, `office_name`). Footer "Choose regions; every country and office starts ticked." |
| **Info Popover** | 216, 24, 591 × 520 | Text (below) |

```
// Period Option Text
IF [quarter_offset] = 0 THEN [Fwd FY] + " · the whole year" ELSE [quarter_label] + " · " + [quarter_months_label] END
```

Period List expected: "FY27 · the whole year", "FY27 Q1 · Jul – Sep 26", … "FY27 Q4 · Apr – Jun 27". (Quarter 0's scaffold row stands in for the year: the forecast series starts there.)

**Info text** (lead-ins Tableau Semibold 10 white, body Book 10 `#B8C0CC`):

> **How the forecast works.** We learned how quickly each kind of PID gets filled and how often PIDs open, simulated the next fiscal year 100 times, and tested the same method on eight quarters that already happened.
>
> **The numbers.** Each number is the average of the 100 simulated futures, so they add up; a range holds 8 in 10 of them. Plan attainment is forecast fills over the fiscal year's Budget, set before the year.
>
> **Time to fill.** Kaplan–Meier over the PIDs approved in the last four quarters: open PIDs count as still waiting, so recent quarters are not read as fast.
>
> **Limits.** The near future is assumed to look like the recent past. A new office is forecast only from its own history. A company-wide event, such as a hiring freeze, is outside the range.
>
> **Contingent workers** are not forecast here: the FY27 Budget plans 13,097 at year end.
>
> **Data.** Arcadia Systems is fictional; all data is synthetic. Executive officers are excluded.

---

## 12. Assembling the dashboard

### 12.1 The page

New dashboard **Dashboard**, **Fixed 1400 × 850**, title off, shading **`#F3F3EF`**. Every item floating unless inside a container; show title off; padding 0 unless stated. Corner radius is under Layout > Background (Tableau 2026.1+).

### 12.2 Floating items, back to front

| # | Item | x | y | w | h | Format |
|---:|---|---:|---:|---:|---:|---|
| 1 | `Page Title` | 240 | 16 | 1136 | 56 | |
| 2 | Container `Hero` (vertical) | 240 | 86 | 452 | 172 | background navy `#13233A`, **corner radius 14**, inner padding 18 top, 22 sides |
| 3 | `Hero Text` | 262 | 100 | 408 | 104 | inside `Hero` |
| 4 | `Hero Quota` | 258 | 208 | 416 | 36 | inside `Hero` |
| 5–7 | Containers `KPI 1`, `KPI 2`, `KPI 3` | 704, 932, 1160 | 86 | 216 | 172 | white, border 1 px `#E4E3DD`, **radius 14**, inner padding 18 top and bottom, 20 sides; each holds its sheet |
| 8–10 | `Hover Hero`, `Hover KPI 1`, `Hover KPI 2` | 240, 704, 932 | 86 | 452, 216, 216 | 172 | over their cards |
| 11 | Container `Card: Main` (vertical) | 240 | 272 | 724 | 540 | white, border 1 px `#E4E3DD`, **radius 14**, inner padding 16 top, 14 sides: `Main Title` 696 × 50 · `FY Chips` 696 × 28 · `Main Chart` 696 × 380 · `Quarter Axis` 696 × 22 · image `d5_main_legend.png` 600 × 20 |
| 12 | Blank, navy `#13233A` | 988 | 272 | 388 | 2 | the rule above "How long PIDs wait" |
| 13 | Text: survival panel title (section 8) | 988 | 282 | 388 | 46 | |
| 14 | `Survival` | 984 | 330 | 392 | 170 | |
| 15 | `Level Legend` | 988 | 502 | 388 | 44 | |
| 16 | Blank, navy | 988 | 562 | 388 | 2 | |
| 17 | `Backtest Title` | 988 | 572 | 388 | 48 | |
| 18 | `Backtest` | 984 | 620 | 392 | 160 | |
| 19 | Image `d5_backtest_legend.png` | 988 | 786 | 388 | 18 | |
| 20 | Footnote text | 240 | 826 | 1136 | 16 | "Arcadia Systems is fictional; all data is synthetic. Executive officers excluded. Forecast = the average of 100 simulated futures; the range holds 8 in 10 of them (10th to 90th percentile)." Book 9 `#5A6170` |
| 21 | Container `Rail` (vertical) | 0 | 0 | 216 | 850 | navy, inner padding 8 left and right (12.3) |
| 22 | `Period Popover` | 216 | 108 | 360 | 260 | visibility `p_PeriodOpen` |
| 23 | `Org Popover` | 216 | 188 | 640 | 640 | visibility `p_OrgOpen` |
| 24 | `Loc Popover` | 216 | 268 | 760 | 560 | visibility `p_LocOpen` |
| 25 | `Info Popover` | 216 | 24 | 591 | 520 | visibility `p_InfoOpen` |

The rail sits in front of every page item; the popovers in front of everything.

### 12.3 Inside the rail (tiled, 200 wide, every item fixed height except the flexible blank)

| Item | h |
|---|---:|
| Blank | 24 |
| Container `Rail Top`: logo `arcadia_logo_horizontal_reverse.png` 200 × 40, Blank 12, `Info Button` row 28 (Blank 172 + 28 × 28) | 80 |
| Blank | 28 |
| Text PERIOD (Semibold 8 `#B8C4D6`) · Blank 6 · `Period Field` 32 · Blank 24 | 78 |
| Text ORGANIZATION · Blank 6 · `Org Field` 32 · `Org Sub` 18 · Blank 24 | 96 |
| Text LOCATION · Blank 6 · `Loc Field` 32 · `Loc Sub` 18 | 72 |
| Image `arcadia_rail_divider.png` | 24 |
| `Reset` | 32 |
| Blank (flexible) | rest |
| `Rail As Of` | 56 |
| Blank | 24 |

The popovers' tops line up with their headings: Period y 108, Organization y 188, Location y 268.

---

## 13. Actions

### 13.1 Change Parameter (run on Select; aggregation None; clearing the selection Keep current value; the source field on the source sheet's Detail)

| Name | Source sheet | Target | Field |
|---|---|---|---|
| Open period popover | Period Field | `p_PeriodOpen` | `Toggle Period Panel` |
| Period closes others | Period Field | `p_OrgOpen`, `p_LocOpen`, `p_InfoOpen` (three actions) | `Close Panel` |
| Set period | Period List | `p_Period` | `quarter_offset` |
| Close period popover on pick | Period List | `p_PeriodOpen` | `Close Panel` |
| Period popover on x | Period Close | `p_PeriodOpen` | `Close Panel` |
| Open org popover | Org Field | `p_OrgOpen` | `Toggle Org Panel` |
| Org closes others | Org Field | `p_PeriodOpen`, `p_LocOpen`, `p_InfoOpen` | `Close Panel` |
| Toggle function | Function List | `p_Functions` | `Function Pick` |
| Function cleans departments | Function List | `p_DeptOff` | `Function DeptOff Pick` |
| Toggle department | Dept List | `p_DeptOff` | `Dept Pick` |
| Org popover on x | Org Close | `p_OrgOpen` | `Close Panel` |
| Open loc popover | Loc Field | `p_LocOpen` | `Toggle Loc Panel` |
| Loc closes others | Loc Field | `p_PeriodOpen`, `p_OrgOpen`, `p_InfoOpen` | `Close Panel` |
| Toggle region | Region List | `p_Regions` | `Region Pick` |
| Region cleans countries | Region List | `p_CountryOff` | `Region CountryOff Pick` |
| Region cleans offices | Region List | `p_OfficeOff` | `Region OfficeOff Pick` |
| Toggle country | Country List | `p_CountryOff` | `Country Pick` |
| Country cleans offices | Country List | `p_OfficeOff` | `Country OfficeOff Pick` |
| Toggle office | Office List | `p_OfficeOff` | `Office Pick` |
| Loc popover on x | Loc Close | `p_LocOpen` | `Close Panel` |
| Reset functions, departments, regions, countries, offices | Reset | the five strings (five actions) | `Empty Text` |
| Reset period | Reset | `p_Period` | `Zero Period` |
| Reset closes popovers | Reset | the four open flags (four actions) | `Close Panel` |
| Open info | Info Button | `p_InfoOpen` | `Toggle Info` |
| Info closes others | Info Button | `p_PeriodOpen`, `p_OrgOpen`, `p_LocOpen` | `Close Panel` |

40 in all.

### 13.2 Deselect

One Filter action per clickable sheet: source and target the same sheet, run on Select, clearing **Show all values**, `zzTrue` → `zzFalse`. Sheets: Page Title, Hero Text, KPI 1, KPI 2, KPI 3, Hover Hero, Hover KPI 1, Hover KPI 2, Main Title, Backtest Title, Level Legend, Period Field, Org Field, Loc Field, Org Sub, Loc Sub, Reset, Info Button, Rail As Of, Period List, Function List, Dept List, Region List, Country List, Office List, Period Close, Org Close, Loc Close, and Hover KPI 3 as built (29). Not on `Main Chart`, `Survival` or `Backtest`: a selection there is useful.

---

## 14. Checks and click tests

### 14.1 Ties at every state

- The bridge: waiting + backfills + net-new + immediate = to fill (KPI 1); to fill − filled (hero) = vacant (KPI 2).
- The hero's fills for the year = the four quarters' forecast on the chart (averages add up): 1,847.3 + 1,733.7 + 1,662.5 + 1,647.7 = 6,891.2.
- KPI 3 = the survival panel's all-level reading; the backtest title's count = the filled dots.
- The rail capsule = the subtitle's scope words.

### 14.2 Values

Every number for six selections and the four quarters is in [the check tables](seats_to_fill_check_tables.md). Spot-check at least: nothing chosen; Technology; People without Talent Acquisition (attainment 72%, chips four slate, L7+ leaves the legend); Asia Pacific without Pune (the FY25 Q1 backtest range equals Asia Pacific's: Pune opened in Jul 2024); Legal & Compliance in Latin America (tiny: fills 9, backtest lows at 0); FY27 Q2.

### 14.3 Click tests (Presentation mode, then on Tableau Public)

| # | Do | Expect |
|---:|---|---|
| 1 | Nothing | The values of section 0 |
| 2 | Click every control, title, card and list row | Nothing stays highlighted |
| 3 | Open each popover in turn | One open at a time |
| 4 | Period > FY27 Q2 | Popover closes; capsule "FY27 Q2 forecast"; hero 1,734 (84% of 2,055; FY26 Q2 1,782, 86%); KPI 1 2,556, "812 waiting as the quarter opens"; KPI 2 823, "11 more than as the quarter opens"; Q2 shaded on the chart; survival and backtest unchanged |
| 5 | Organization > People, untick Talent Acquisition | Capsule "People" (white) "3 of 4 departments"; hero 181; subtitle "People (3 of 4 departments)" |
| 6 | People off | Every department back; `p_DeptOff` empty (the clean-up) |
| 7 | Legal & Compliance only, untick Legal | Compliance & Risk locked (grey name; a click changes nothing) |
| 8 | Location > Asia Pacific, untick Pune | Loc Sub "6 countries · 8 of 9 offices"; hero 1,861 |
| 9 | Finance, then Europe | Portugal and Lisbon dimmed; a click changes nothing |
| 10 | Hover the hero, KPI 1, KPI 3 | The sentences of 6.3 |
| 11 | Hover KPI 2 | The bridge, adding up |
| 12 | Hover a past quarter, a forecast quarter, a curve, a backtest dot | 7.5, 8, 9 |
| 13 | Reset | FY27, all functions, all locations, popovers closed |

---

## 15. Publishing

1. Reset; close every popover.
2. Hide all sheets; remove any stray legend or parameter control.
3. Save a lighter copy, `Seats to Fill (hide fields).twb`: Hide All Unused Fields; delete working sheets (`CHK Rows`). Keep the full original.
4. Extract on; refresh.
5. File > Save to Tableau Public As **Seats to Fill: Hiring Forecast | Arcadia Systems**. Description starting "Workforce forecasting:"; tags forecasting, workforce planning, survival analysis, Python, HR analytics. Show Viz on Profile on; Allow Workbook Download off; toolbar at the bottom.
6. On the web: the click tests of 14.3; the first load and a click timed; the screenshot (1400 × 850) for the repo.

**Assets to place before building** (in `My Tableau Repository/Shapes/Arcadia D5/` and the dashboard folder): `d5_chip_teal.png`, `d5_chip_slate.png` (shapes); `d5_main_legend.png`, `d5_backtest_legend.png` (images). The D4 shapes and rail images are reused as they are.

---

## 16. As built

The workbook was not built by hand from this guide: [`tableau/builder/d5/`](../../../tableau/builder/d5/) writes it into the saved base workbook (the Custom SQL and its extract, section 2.2), reading every formula from this guide's code blocks. Sections 0 to 15 stay the design; this section records where Tableau needed something different, found in the Desktop spot checks of 2026-10-27. The numbers did not change: every value in section 0 and the check tables reads the same on the page.

```
D4_TWB="…/4 Contingent Workforce Reconciliation/Contingent Workforce Reconciliation.twb" \
python3 tableau/builder/d5/build_d5.py base.twb "Seats to Fill.twb" 3      # Tableau closed first
```

### 16.1 Formulas

| Guide | As built | Why |
|---|---|---|
| Text calcs mix aggregates with row-level fields (`Hero Line 3`, the hover sentences, `Waiting Text`) | Row-level and parameter-only fields inside an aggregate formula are wrapped in `MIN()` | Tableau refuses to mix aggregate and non-aggregate arguments |
| `SV Median Days Str`, `KPI 3 Tip 1`, `BT Title`, `BT Subtitle` read other table calculations | Each repeats the inner table calculation in full | A table calculation read by another loses its Compute Using: the backtest read "1 of 8" and the medians were wrong until inlined. Every SV calc defaults to Compute Using `days_to`, every BT calc to `quarter_offset` |
| `Quota From`, `Quota Width`, `Quota Att/Lo/Hi` × 100 | Kept as fractions (0.25 a band, axis 0 to 1.25, Percentage format) | No custom `0"%"` format needed |
| `KPI 2 Title` "Vacant at the end of FY27 Q2" | "Vacant at the end of Q2" for a quarter | The card is 174 px wide; a label that does not fit becomes `####` |
| `Waiting Text`, `Vacant Change Text` "as the quarter opens" | "as Q2 opens" | Same width limit |
| `Hero Line 3` "… the FY27 Budget plans for FY27 Q2 · …" | "89% of the 7,709 in the FY27 Budget · FY26 filled 6,849 (88%)" | Same width limit; the kicker already names the quarter |
| KPI 3 line 4 "PIDs approved in the last four quarters" | "Approved in the past year"; line 3 "92% within 90 days" | Same width limit |
| `Line Tip 1` one sentence | `Line Tip Head` (Semibold navy) + `Line Tip Body` | Hovers are color-coded: counts navy, plan and likely figures teal |
| Backtest from `BT Low` … with a per-cell reference line | `QBT Mean/Var/CV/Actual` FIXED by `quarter_offset`, drawn on the scaffold rows (`BTS Row`): range and average are two Gantt marks of the same width, the actual is a shape | A reference line spans the whole column, wider than the bars; the values are the same formula |
| Added | `Tick X`, `Quarter Tick X`, `Chip Row`, `Year Under`, `Ref X4…20`, `Ref D29…89` (30/60/90), `Days Plus One`, `Close X`, `Tip Waiting Words`, `Tip Span Word`, the list `Shape`/`Name` fields, `Quota Band Text`, `Quota … Mark` | Helpers for the layout below |

### 16.2 Sheets and layout

- **KPI cards**: each card's text sheet sits in a white container (radius 14, padding 18/20); every card, KPI 3 included, has an invisible hover cover. `Hover KPI 3` carries `days_to` on Detail and the `SV Is Last` filter so its tooltip can read the survival numbers.
- **Hero quota bar**: the five bands are reference bands (they always fill the strip); the likely range is a translucent white band edged by two 1.5 px white lines; the forecast a 3 px white line. The strip is 44 px, with a hidden `Tick X` axis on Rows so it has height.
- **Main chart**: the forecast year (20 to 24) and the chosen period are reference bands built in the file; left axis 44 px, Include zero off; the FY chips sit centered over each year and the year names sit under each Q1 on the Quarter Axis sheet.
- **Survival**: step lines; the 30/60/90-day labels are the x-axis (ticks every 30), not reference-line labels, so they sit under the curves. Chart 158 px, legend 4 px lower.
- **Backtest**: columns fiscal year / Q1–Q4 (two rows of headers instead of "FY25 Q1"); dots are the shapes `d5_dot_in.png` (navy dot) and `d5_dot_out.png` (navy ring, no fill) in `Shapes/Arcadia D5`.
- **Lists**: every list is flat, one row per option, the tick on a hidden axis at the left, rows 18 px, fit width. Departments, countries and offices are sorted by their parent instead of grouped under it: a group of one row loses its label in Tableau (every single-office country showed a blank). Offices read "Country · Office".
- **Popovers**: x 216, joined to the rail, 12 px inner padding on the left; footers fixed at the bottom (30 px, one line); Period 360 × 190; Organization 640 × 700 at y 140; Location 640 × 720 at y 130; Info 591 × 420.
- **Rail**: capsules drawn at shape size 12 (the whole pill visible), Reset at 10.6.
- **Wording**: American spelling (Organization).
