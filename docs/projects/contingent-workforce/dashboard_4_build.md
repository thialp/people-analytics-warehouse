# Dashboard #4, Contingent Workforce Reconciliation: build plan

The complete plan for the fourth Arcadia dashboard, from the data to the published page. It is the one document to work from: every parameter, calculation, sheet, container, action and check, in the order they are built. It reuses what already works on Dashboard #2 (Compensation Walk): the 216 px navy rail, the KPI band grid, the popover frame hanging from the rail, the image buttons and the deselect pattern. From Dashboard #3 it takes the fixed-slot popover rows, the KPI hovers and the card containers. Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic.

Companion documents: the release plan [release_4_plan.md](release_4_plan.md) (phases, decisions C1 to C14, lessons L1 to L13, the check tables in its section 7), the spike guide [spikes_guide.md](spikes_guide.md), the case study [case_study_4.md](case_study_4.md), and the Dashboard #2 and #3 build plans ([G2](../compensation-walk/release_3_rebuild_dashboard_2.md), [G3](../workforce-planning/release_3_rebuild_dashboard_3.md)). The design is the approved prototype canvas (boards *Current*, *Gap list*, *Dec 2024 replay*, *Sankey tooltips*).

| Revision | Date | What changed |
|---|---|---|
| 1 | 2026-10-25 | First full plan, steps 0 to 16. Spikes S1, S2 and S3 passed. Two findings added while writing it: the Sankey's place order breaks under a group filter (section 9.2, spike S7), and a Sankey click cannot show a hidden gap list (spike S2b). The page grid moves onto Dashboard #2's (cards from x 246, KPI band at y 88). **The build starts at step 5** (the dashboard shell, with the Sankey in its final tile) so the Sankey can be judged in place before anything else is built |
| 2 | 2026-10-25 | Steps 3 and 4 done by a generator (`tableau/build/d4_fields/`): every parameter and calc written into the workbook and checked. Small changes to make the formulas valid as written: `Has Prior` is an aggregate; `Main Subtitle` is an aggregate with `Top Flag Prior Rank` and `Clear Own Gaps`; one `Tick Shape` and one `List Row` per list; `p_Close` allows All, opening on `Latest Close` |
| 3 | 2026-10-25 | Status marks: 🟢 in the workbook, 🔴 still to add by hand (only the `kpi_` set, step 9). Folder `4 Contingent Workforce Reconciliation` (no leading zero) |
| 4 | 2026-10-25 | **Native Sankey (D15, section 9N).** The Custom SQL gains the Sankey scaffold (2,188 rows) and `flag_short`; 3 parameters and 142 `Sk` calcs written into the workbook and checked against the data (`verify_sankey.py`). Version A, the extension, kept as section 9 |
| 5 | 2026-10-25 | Flag labels left of the flag nodes, right-aligned, on their own 150 px sheet beside a 576 px Sankey (`Sk Flag Y`, `Sk Flag X`; `Sk Y Text`, `Sk W`, `Sk X3` changed). Thiago made the edits by hand in the open workbook; `spec_sankey.py` matches |

## Contents

0. Where we stand
1. The story
2. Decisions
3. Step 0: data (done)
4. Step 1: spikes
5. Step 2: workbook and data source
6. Step 3: parameters
7. Step 4: calculations
8. **Step 5: the dashboard shell and containers (build first)**
9. Step 6: the Sankey
10. Step 7: rail controls
11. Step 8: popovers
12. Step 9: KPI band and hovers
13. Step 10: gap list and the Overview · Gap list toggle
14. Step 11: timeline card
15. Step 12: ticket card
16. Step 13: title, subtitle, load note, footnote, info
17. Step 14: actions
18. Step 15: checks and click tests
19. Step 16: publish
20. Shapes and images to make

---

## 0. Where we stand

| Step | What | Who | Size | State |
|---:|---|---|---|---|
| 0 | Data: generator, warehouse, SQL Server, Custom SQL, check tables, prototype (release plan phases 1 to 6) | Claude, Thiago on the Mac | | **Done** (88 of 88 tests, 35 of 35 SQL Server checks, prototype approved) |
| 1 | Spikes S1 to S7 | Both | S | S1, S2, S3, S7 **passed** (S3 after the levels lost their counts, 9.3). S2b in 13.4; S4, S5, S6 in their sections |
| 2 | Workbook and data source | Thiago | S | Done in the spike workbook; step 2 makes it the real one |
| 3 | Parameters | Claude | S | **Written into the workbook** 2026-10-25 (10; `kpi_` in step 9) |
| 4 | Calculations | Claude | M | **Written into the workbook** 2026-10-25 (211 new; the 21 spike label and tooltip calcs rewritten in place) |
| **5** | **Dashboard shell: rail, KPI band, three cards, footnote, with placeholders; the Sankey in its tile (section 8)** | Thiago | S | **Next** |
| 6 | The Sankey, **native** (section 9N): extract refresh, the `Sankey Native` sheet, on the dashboard, actions. Version A, the extension (section 9), stays in the workbook | Thiago | M | **Next**: data and 142 fields written; the sheet is to build |
| 7 | Rail controls | Thiago | M | |
| 8 | Popovers: Point in time, Function, Department, Country, Info | Thiago | L | Needs S4 |
| 9 | KPI band and hovers | Thiago | M | |
| 10 | Gap list and the toggle | Thiago | M | Needs S2b |
| 11 | Timeline card | Thiago | S | |
| 12 | Ticket card | Thiago | M | Needs S5 |
| 13 | Title, subtitle, load note, footnote, info text | Thiago | S | |
| 14 | Actions (about 50) and the deselect audit | Thiago | M | |
| 15 | Checks and click tests | Both | M | |
| 16 | Publish, README, screenshot, profile | Both | S | Needs S6 |
| | Shapes and images (section 20) | Claude | S | Before step 7 |

S is an hour or less, M a session, L more than one session. One screenshot per step; I check it against the expected values written in the step.

---

## 1. The story

**Page question:** *Where do Bridgeway and Keystone disagree at the month-end close, what does each difference put at risk in Finance's report, and where is it aligned?*

| Where | Question | Current (Jun 2026 close), no group chosen |
|---|---|---|
| Header | Which close? | **Contingent Workforce Reconciliation** · "Where Bridgeway and Keystone disagree at the June 2026 close, and where each gap is aligned" |
| KPI 1 | How many contractors are working? | **11,941** contractors working in Bridgeway · Keystone shows 11,875 · net 66 |
| KPI 2 | How clean is the close? | **3.21%** gap rate · Known risk (target 3%) · 383 with a gap · May 3.41% |
| KPI 3 | Do the same problems come back? | **342** of 407 gaps still open from the May close · 84% |
| KPI 4 | Is anyone working on them? | **177** with no linked ticket · 43% of the gaps |
| KPI 5 | How old are they? | **277** of 407 gaps open over 90 days · oldest 3,235 days |
| Main card | What differs, what it puts at risk, where it is aligned | Sankey: 9 flags, 5 risks, 3 places, 407 gaps. Headline "Bridgeway holds 194 of 407 gaps. Largest flag: Order open or billed after the end date (100)" |
| Right top | Is the rate improving? | Gap rate at the last 13 closes, target line, the selected close marked |
| Right bottom | Who is working on it? | 361 open Helix tickets as dots, by the group working them (149 / 124 / 88) and age |
| Gap list (toggle) | Which contractors, exactly? | The 407 gaps, by where they are aligned, oldest first |

**How the numbers tie together.** Flags = risks = places = gap list rows = 407 (test 83). KPI 3, 4 and 5 count the gaps in the rate (`is_counted`), which equals the Sankey total whenever no gap "clears on its own" (0 in June; 1 in May, so May reads 417 in the KPIs and 418 on the Sankey, and the Sankey subtitle says so). KPI 2 counts contractors (383), never gaps. Open tickets by group add up to the card total (149 + 124 + 88 = 361).

---

## 2. Decisions

| # | Decision | Why |
|---|---|---|
| D1 | One data source, the Custom SQL `custom_sql_cw_reconciliation_dashboard.sql`, extracted | The group filters work across every card only inside one source (release plan, phase 4) |
| D2 | Executive officers (`D-901`) excluded | Same people on every Arcadia dashboard; the Custom SQL already does it |
| D3 | **Page grid = Dashboard #2's.** Rail 0 to 216; cards from x 246 to 1370; KPI cards 212 × 86 at y 88, 16 apart; content cards from y 190 to 812; footnote y 822 | The same rail and band on #2 and #4, so the KPI band image and the `kpi_` values carry over |
| D4 | Main card 758 wide, right column 350 wide (cards are not on the KPI columns below the band) | The Sankey needs the width: on the KPI columns it would get 668 px (cards 1 to 3) |
| D5 | **Multi-select by parameter strings, not set actions.** `p_Functions` holds `|Commercial|Technology|`; a click toggles one name in or out; empty means All | A set action can add or remove, but it cannot toggle in one click. A string parameter can, and the pattern (parameter actions, deselect) is the one every Arcadia dashboard already uses. Spike S4 tests it on Tableau Public |
| D6 | **No context filters anywhere.** Every LOD tests the close and the scope inside its own formula | A FIXED runs before ordinary filters; putting the conditions inside the formula makes the counts right with no filter order to remember. Supersedes the context-filter note in the spike guide (S3) |
| D7 | **Sankey anchors** (section 9.2): three zero-weight rows keep Bridgeway, Keystone, System feed in that order under any group filter | Without them the place order breaks for 253 of 487 function × close combinations (the extension follows first appearance) |
| D8 | Flag numbers never shown: labels and tooltips use `flag_name`; `flag_label` only orders | Thiago, 2026-10-25: the number read like a rank |
| D9 | Sankey colours from Tableau's own palettes: flags Tableau 20, risks Miller Stone `#4F6980`, places Hue Circle (amber `#F89217`, violet `#7873C0`, teal `#21B087`); label colour Automatic | Spike S3; the extension lists only built-in palettes |
| D10 | Ranks and year-ago comparisons are company-wide; they show only when no group is chosen | `flag_rank` is computed for all of Arcadia; under a filter it would mislead |
| D11 | The KPI band is text drawn as map labels (Dashboards #1 to #3), left-aligned in each card | The prototype's cards read left to right (value, then unit) |
| D12 | Every text on the page is a calculation (L3); every empty state has words (L12): "No gaps in this selection", N/A for a zero denominator | Lessons from the published dashboards |
| D13 | No arrows or glyphs in viewer text; tooltip command buttons off on every sheet; every clickable or text sheet has a deselect action | Standing rules |
| D14 | Tickets with no linked contractor (95 of 361 at the June close) have no group, so they leave the ticket card when any group is chosen | They cannot be placed in a function or country; the info text says so |
| D15 | The Sankey on the page is native Tableau (polygons on a 2,188-row scaffold, FIXED LODs), not the viz extension | The extension draws labels only inside nodes and colours a link only by its source; native gives thin nodes, labels beside them and ribbons in the place colours. Version A stays in the workbook for reference (section 9). Short flag names (`flag_short`) everywhere a viewer reads a flag |

---

## 3. Step 0: data (done)

Release plan phases 1 to 6, all done (sections 3 to 8 of [release_4_plan.md](release_4_plan.md)): the generator writes the Keystone job data, feed times, load log and Helix tickets; the warehouse builds the flags, routing, ticket replay and four marts (88 of 88 tests); the SQL Server twin builds and validates them (`15_validate`, 35 of 35 PASS on the Mac, 2026-10-25); the Custom SQL returns 65,435 rows in about a second.

| Row type | Rows | Feeds | Count with |
|---|---:|---|---|
| Gap | 21,665 | Sankey, gap list, KPI 5's oldest gap | `gaps` (1 per row) |
| Population | 27,324 | KPIs 1 to 5, timeline | `contractors_working`, `contractors_with_gap`, `gaps_counted`, `gaps_open_prior_close`, `gaps_no_ticket`, `gaps_over_90_days` |
| Ticket | 16,446 | Ticket card; three of them anchor the Sankey (section 9.2) | `tickets` (1 per row), at `dot_x`, `dot_y` |

61 closes, Jun 30, 2021 to Jun 30, 2026. 8 functions, 31 departments, 22 countries.

**Before any Tableau step, on the Mac** (only if `main` moved since your last run):

```bash
cd ~/GitHub/people-analytics-warehouse
git checkout main && git pull && git log --oneline -1
D="$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/4 Contingent Workforce Reconciliation/Custom SQL"
cmp -s tableau/custom_sql_cw_reconciliation_dashboard.sql "$D/custom_sql_cw_reconciliation_dashboard.sql" && echo same || echo DIFF
```

Expected: the latest squash commit, then `same`. On `DIFF`, copy it: `cp tableau/custom_sql_cw_reconciliation_dashboard.sql "$D/"`. (The project folders are `1` to `6`, with no leading zero: the workbooks' extract paths use those names. Rename a folder only with Tableau closed, or the next save recreates the old one.)

---

## 4. Step 1: spikes

| # | Spike | State | Result or where it runs |
|---|---|---|---|
| S1 | Sankey order | **Passed** 2026-10-25 | The first column follows its sort; later columns follow first appearance. Led to the 9 / 5 / 3 taxonomy |
| S2 | Sankey click filters a sheet | **Passed** 2026-10-25 | A filter action from the Sankey filters a table on the same dashboard (screenshots: Bridgeway 194, Status mismatch 66, In Bridgeway, not in Keystone 25) |
| S3 | Colours, labels, tooltip | **Passed** 2026-10-25 | Colours per node from built-in palettes; label colour Automatic; the colour-coded tooltip renders in the extension |
| S2b | A Sankey click while the gap list is hidden | Section 13.4 | Can the Sankey run a **parameter** action (switch to the gap list)? If not, the filter waits for the toggle |
| S7 | Sankey order under a group filter, with anchors | **Passed** 2026-10-25 | Weight 0 works (no 0.001 needed). `|Marketing|` at Jun 2026: Bridgeway (3) above Keystone (3), although Marketing's first flag is aligned in Keystone; flags 1 · 2 · 1 · 2 match the data; System feed has no gaps, so no empty node |
| S4 | Multi-select by string parameter, on the web | Section 11.3 | A click toggles a name; the capsule and every card follow; quick on Tableau Public |
| S5 | Ticket dots at 141 per cell | Section 15 | Readable; hover finds the right dot |
| S6 | Extract size and load time | Section 19 | Publishes; the page loads in under 5 seconds |

---

## 5. Step 2: workbook and data source

You built the spikes in `Arcadia CW Reconciliation.twb`. Its data source, the Sankey sheet and the label and tooltip calcs are proven, so it becomes the real workbook; the test dashboard and the second Sankey go.

1. Close Tableau. Archive a copy of the spike state:

```bash
W="$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/4 Contingent Workforce Reconciliation"
ls "$W"/*.twb
mkdir -p "$W/_archive/2026-10-25"
cp "$W/Arcadia CW Reconciliation.twb" "$W/_archive/2026-10-25/Arcadia CW Reconciliation - spikes.twb"
ls "$W/_archive/2026-10-25"
```

   Expected: the workbook name, then `Arcadia CW Reconciliation - spikes.twb`. (If `ls` prints another folder or name, use it in the next lines.)
2. Open `Arcadia CW Reconciliation.twb`. Rename the data source **CW Reconciliation** (it may already be). Delete the sheet `Sankey 2`. Keep `Dashboard 1` until step 5 is done (it holds the S2 filter action as a reference), then delete it.
3. Data source checks (Data Source tab): Connection **Extract**; the Custom SQL is the file from step 0 (Edit Custom SQL: it starts with the comment block `custom_sql_cw_reconciliation_dashboard.sql`). If you change it, Extract > Refresh.
4. **Types.** `month_end_date` and `since_date` Date. `flag_rank`, `flag_rank_prior_close`, `flag_rank_year_ago`, `risk_order`, `place_order`, `age_band_order`: Convert to Dimension. `is_latest_close`, `is_counted`, `has_ticket`, `was_open_prior_close`, `fixed_day_after_close`: Boolean. Every count column stays a measure with number format `#,##0`.
5. File > Save.

**Checkpoint 2.** A sheet `CHK Rows`: `row_type` on Rows, `Number of Records` (or `CNT(row_type)`) on Text. Expected: **Gap 21,665 · Population 27,324 · Ticket 16,446**. Keep the sheet (hidden later), it is the first thing to look at if a number goes wrong.

---

## 6. Step 3: parameters

| | Name | Type | Allowable values | Current | Notes |
|---|---|---|---|---|---|
| 🟢 | `p_Close` | Date | **All** (the close grid and Reset set it, so no list is needed) | **Value when workbook opens: `Latest Close`** (7.1) | The close the page shows. Opens on the newest close after a refresh |
| 🟢 | `p_Functions` | String | All | empty | `|Commercial|Technology|`; empty = All functions |
| 🟢 | `p_Departments` | String | All | empty | Same pattern |
| 🟢 | `p_Countries` | String | All | empty | Same pattern |
| 🟢 | `p_ShowList` | Boolean | | False | False = Overview (Sankey), True = Gap list |
| 🟢 | `p_CloseOpen` | Boolean | | False | Popover open flags |
| 🟢 | `p_FunctionOpen` | Boolean | | False | |
| 🟢 | `p_DepartmentOpen` | Boolean | | False | |
| 🟢 | `p_CountryOpen` | Boolean | | False | |
| 🟢 | `p_InfoOpen` | Boolean | | False | |
| 🔴 | `kpi_` (16) | Float | | Dashboard #2's | Pasted with the KPI calcs in section 12 |

🟢 The ten `p_` parameters are in the workbook, and `p_Close` already opens on `Latest Close`. 🔴 The 16 `kpi_` parameters come with the KPI calcs in step 9 (12.1).

---

## 7. Step 4: calculations

All on **CW Reconciliation**. Field names are the SQL columns as Tableau shows them (`month_end_date`); calcs keep the names below.

**Status marks.** 🟢 already in the workbook (written by the generator, nothing to type). 🔴 still to add by hand. A 🟢 field still needs its sheet, shelf, format and action work in its step; only the typing is done.

**Written into the workbook, 2026-10-25.** The 10 parameters of section 6 and every calc in sections 7, 10, 11, 12.4, 13, 14, 15 and 16 (211 new, 21 spike calcs rewritten in place) were added to `Arcadia CW Reconciliation.twb` by [`tableau/build/d4_fields/`](../../../tableau/build/d4_fields/README.md), which also checks each formula for balanced brackets, IF and END, and mixed aggregate and row-level parts. Not included: the `kpi_` calcs and parameters (copied from Dashboard #2 in step 9). The formulas below are the source; the generator follows them.

### 7.1 Close and scope

```
// 🟢 Latest Close         { MAX([month_end_date]) }
// 🟢 First Close          { MIN([month_end_date]) }
// 🟢 Prior Close          DATEADD('day', -1, DATETRUNC('month', [p_Close]))
// 🟢 Year Ago Close       DATEADD('day', -1, DATEADD('month', -11, DATETRUNC('month', [p_Close])))
// 🟢 Is Selected Close    [month_end_date] = [p_Close]
// 🟢 Is Prior Close       [month_end_date] = [Prior Close]
// 🟢 Is Current           [p_Close] = [Latest Close]
// 🟢 Has Prior            [p_Close] > MIN([First Close])                                      (aggregate, so it sits with the K strings on the KPI cards)
// 🟢 Close Month          DATENAME('month', [p_Close])                                        "June"
// 🟢 Close Name           DATENAME('month', [p_Close]) + " " + STR(YEAR([p_Close]))          "June 2026"
// 🟢 Close Short          LEFT(DATENAME('month', [p_Close]), 3) + " " + STR(YEAR([p_Close])) "Jun 2026"
// 🟢 Prior Month          DATENAME('month', [Prior Close])                                    "May"
// 🟢 Prior Short          LEFT(DATENAME('month', [Prior Close]), 3)                           "May"

// 🟢 In Function          [p_Functions] = "" OR CONTAINS([p_Functions], "|" + [function_name] + "|")
// 🟢 In Department        [p_Departments] = "" OR CONTAINS([p_Departments], "|" + [department_name] + "|")
// 🟢 In Country           [p_Countries] = "" OR CONTAINS([p_Countries], "|" + [country_name] + "|")
// 🟢 In Scope             [In Function] AND [In Department] AND [In Country]
// 🟢 Scope Is All         [p_Functions] = "" AND [p_Departments] = "" AND [p_Countries] = ""

// 🟢 Is Gap               [row_type] = "Gap"
// 🟢 Is Pop               [row_type] = "Population"
// 🟢 Is Ticket            [row_type] = "Ticket"
// 🟢 Gap Now              [Is Gap] AND [Is Selected Close] AND [In Scope]
// 🟢 Pop Now              [Is Pop] AND [Is Selected Close] AND [In Scope]
// 🟢 Pop Prior            [Is Pop] AND [Is Prior Close] AND [In Scope]
// 🟢 Ticket Now           [Is Ticket] AND [Is Selected Close] AND [In Scope]

// 🟢 zzTrue               TRUE
// 🟢 zzFalse              FALSE
// 🟢 Close Panel          FALSE
```

A ticket with no linked contractor has no `function_name`, so `In Function` is False for it as soon as a function is chosen (D14).

### 7.2 Scope words (rail capsules, subtitle)

```
// 🟢 Function Count       IF [p_Functions] = "" THEN 0 ELSE LEN([p_Functions]) - LEN(REPLACE([p_Functions], "|", "")) - 1 END
// 🟢 Department Count     (same, on p_Departments)
// 🟢 Country Count        (same, on p_Countries)
// 🟢 Function Field Text  IF [Function Count] = 0 THEN "All"
//                      ELSEIF [Function Count] = 1 THEN MID([p_Functions], 2, LEN([p_Functions]) - 2)
//                      ELSE STR([Function Count]) + " selected" END
// 🟢 Department Field Text, Country Field Text   (same pattern; cut a single name over 20 letters: LEFT(name, 19) + "…")
// 🟢 Scope Text           (used in the subtitle; empty when nothing is chosen)
IF [Scope Is All] THEN ""
ELSE " · " + (IF [Function Count] = 0 THEN "" ELSEIF [Function Count] = 1 THEN [Function Field Text] ELSE STR([Function Count]) + " functions" END)
   + (IF [Department Count] = 0 THEN "" ELSE (IF [Function Count] > 0 THEN ", " ELSE "" END)
        + (IF [Department Count] = 1 THEN [Department Field Text] ELSE STR([Department Count]) + " departments" END) END)
   + (IF [Country Count] = 0 THEN "" ELSE (IF [Function Count] + [Department Count] > 0 THEN ", " ELSE "" END)
        + (IF [Country Count] = 1 THEN [Country Field Text] ELSE STR([Country Count]) + " countries" END) END)
END
```

Expected: nothing chosen "", Technology " · Technology", Commercial and Technology " · 2 functions", Technology and India " · Technology, India".

### 7.3 Toggles (multi-select, D5)

```
// 🟢 Function Toggle      (the new value of p_Functions when this function is clicked)
IF CONTAINS([p_Functions], "|" + [function_name] + "|")
THEN (IF [p_Functions] = "|" + [function_name] + "|" THEN "" ELSE REPLACE([p_Functions], "|" + [function_name] + "|", "|") END)
ELSE (IF [p_Functions] = "" THEN "|" + [function_name] + "|" ELSE [p_Functions] + [function_name] + "|" END) END
// 🟢 Department Toggle, Country Toggle   (same, on department_name / p_Departments and country_name / p_Countries)
// 🟢 Function Is On       CONTAINS([p_Functions], "|" + [function_name] + "|")
// 🟢 Department Is On, Country Is On     (same)
// 🟢 Dept In Functions    [p_Functions] = "" OR CONTAINS([p_Functions], "|" + [function_name] + "|")
// 🟢 Function State       IF [Function Is On] THEN "on" ELSE "off" END
// 🟢 Department State     IF [Department Is On] THEN "on" ELSEIF [Dept In Functions] THEN "off" ELSE "dim" END
// 🟢 Country State        IF [Country Is On] THEN "on" ELSE "off" END
// 🟢 Function Tick Shape    IF [Function Is On] THEN "d4_tick_on" ELSE "d4_tick_off" END     (values match the shape file names)
// 🟢 Department Tick Shape  IF [Department Is On] THEN "d4_tick_on" ELSEIF [Dept In Functions] THEN "d4_tick_off" ELSE "d4_tick_dim" END
// 🟢 Country Tick Shape     IF [Country Is On] THEN "d4_tick_on" ELSE "d4_tick_off" END
// 🟢 Empty Text           ""
// 🟢 Toggle Close Panel   NOT [p_CloseOpen]
// 🟢 Toggle Function Panel  NOT [p_FunctionOpen]      (Department, Country, Info the same)
// 🟢 Show Pick            (on the toggle sheet, one mark per option; see 10.2)
```

Walk-through: `|A|B|` and a click on B gives `|A|`; on A gives `|B|`; on C gives `|A|B|C|`; on the only member gives empty.

### 7.4 KPI numbers (Population rows; one formula per name)

```
// 🟢 K Working        SUM(IF [Pop Now] THEN [contractors_working] END)
// 🟢 K Keystone       SUM(IF [Pop Now] THEN [contractors_working_keystone] END)
// 🟢 K BW Only        SUM(IF [Pop Now] THEN [working_bridgeway_only] END)
// 🟢 K KS Only        SUM(IF [Pop Now] THEN [working_keystone_only] END)
// 🟢 K Net            [K Working] - [K Keystone]
// 🟢 K With Gap       SUM(IF [Pop Now] THEN [contractors_with_gap] END)
// 🟢 K Rate           IF ZN([K Working]) = 0 THEN NULL ELSE [K With Gap] / [K Working] END
// 🟢 K Rate Prior     IF ZN(SUM(IF [Pop Prior] THEN [contractors_working] END)) = 0 THEN NULL
//                  ELSE SUM(IF [Pop Prior] THEN [contractors_with_gap] END) / SUM(IF [Pop Prior] THEN [contractors_working] END) END
// 🟢 K Target         MIN(IF [Is Pop] THEN [gap_rate_target] END)
// 🟢 K Gaps           SUM(IF [Pop Now] THEN [gaps_counted] END)
// 🟢 K Clear Own      SUM(IF [Pop Now] THEN [gaps_clear_on_own] END)
// 🟢 K Carry          SUM(IF [Pop Now] THEN [gaps_open_prior_close] END)
// 🟢 K No Ticket      SUM(IF [Pop Now] THEN [gaps_no_ticket] END)
// 🟢 K Over 90        SUM(IF [Pop Now] THEN [gaps_over_90_days] END)
// 🟢 K Oldest         MAX(IF [Gap Now] AND [is_counted] THEN [days_open] END)
// 🟢 K Tickets        SUM(IF [Ticket Now] THEN [tickets] END)
```

Text twins use the comma and percent patterns from Dashboard #3 (G3 7.2), typed fresh:

```
// 🟢 Comma pattern, shown for K Working Str (copy for K Keystone, K With Gap, K Gaps, K Carry, K No Ticket, K Over 90, K Oldest, K BW Only, K KS Only)
IF ISNULL([K Working]) THEN "N/A"
ELSEIF [K Working] >= 1000 THEN STR(DIV(INT([K Working]), 1000)) + "," + RIGHT("00" + STR(INT([K Working]) % 1000), 3)
ELSE STR(INT([K Working])) END

// 🟢 Rate pattern, two decimals (K Rate Str; copy for K Rate Prior Str)
IF ISNULL([K Rate]) THEN "N/A" ELSE
STR(DIV(INT(ROUND([K Rate] * 10000, 0)), 100)) + "." + RIGHT("0" + STR(INT(ROUND([K Rate] * 10000, 0)) % 100), 2) + "%" END

// 🟢 Share pattern, no decimals (K Carry Pct Str: K Carry / K Gaps; K No Ticket Pct Str: K No Ticket / K Gaps)
IF ZN([K Gaps]) = 0 THEN "N/A" ELSE STR(INT(ROUND([K Carry] / [K Gaps] * 100, 0))) + "%" END

// 🟢 K Net Str        (IF [K Net] > 0 THEN "+" ELSEIF [K Net] < 0 THEN "−" ELSE "" END) + STR(ABS(INT([K Net])))
// 🟢 K Points Str     distance from the target in points, for the KPI 2 hover: "0.21 pts above" / "0.04 pts below" / "on"
IF ISNULL([K Rate]) THEN "" ELSE
  STR(DIV(INT(ROUND(ABS([K Rate] - [K Target]) * 10000, 0)), 100)) + "." + RIGHT("0" + STR(INT(ROUND(ABS([K Rate] - [K Target]) * 10000, 0)) % 100), 2)
  + IF ROUND([K Rate] - [K Target], 4) > 0 THEN " pts above" ELSEIF ROUND([K Rate] - [K Target], 4) < 0 THEN " pts below" ELSE " pts: on" END END
// 🟢 K Target Str     STR(INT(ROUND([K Target] * 100, 0))) + "%"
```

### 7.5 KPI card texts

| Card | `KPI n Title` | `KPI n Value` | `KPI n Unit` (same line, smaller) | `KPI n Note` |
|---|---|---|---|---|
| 1 | `"Working in Bridgeway"` | `[K Working Str]` | `"contractors"` | `"Keystone shows " + [K Keystone Str] + " · net " + [K Net Str]` |
| 2 | `"Gap rate at the close · target " + [K Target Str]` | `[K Rate Str]` | `KPI 2 Known` = `IF [K Rate] > [K Target] THEN "Known risk" END` (coral) and `KPI 2 Low` = `IF [K Rate] <= [K Target] THEN "Low risk" END` (teal) | `[K With Gap Str] + " with a gap · " + IF [Has Prior] THEN [Prior Short] + " " + [K Rate Prior Str] ELSE "first close in the data" END` |
| 3 | `IF [Has Prior] THEN "Still open from the " + [Prior Month] + " close" ELSE "Still open from the prior close" END` | `IF [Has Prior] THEN [K Carry Str] ELSE "N/A" END` | `"of " + [K Gaps Str] + " gaps"` | `IF [Has Prior] THEN [K Carry Pct Str] + " open since the " + [Prior Month] + " close" ELSE "No prior close in the data" END` |
| 4 | `"No linked ticket"` | `[K No Ticket Str]` (coral `#712B13`) | `[K No Ticket Pct Str] + " of the gaps"` | `"No Helix ticket linked to the gap"` |
| 5 | `"Open over 90 days"` | `[K Over 90 Str]` | `"of " + [K Gaps Str] + " gaps"` | `"Oldest gap " + [K Oldest Str] + " days"` |

🟢 Every text in this table is in the workbook: `KPI 1`–`5 Title`, `Value`, `Note`, `KPI 1`, `3`, `4`, `5 Unit`, `KPI 2 Known` and `KPI 2 Low`.

Hover texts (`KPI n Tip`, one tooltip per cover in section 12.4):

```
// 🟢 KPI 1 Tip   [K BW Only Str] + " working in Bridgeway but not active in Keystone, " + [K KS Only Str] + " the other way. Contractors, not gaps."
// 🟢 KPI 2 Tip   "Contractors with at least one gap in the rate, divided by contractors working in Bridgeway. " + [K Points Str]
//             + " a provisional " + [K Target Str] + " target. The target flags risk; it does not certify the report."
//             + IF ZN([K Clear Own]) > 0 THEN " " + STR([K Clear Own]) + " gaps clear on their own by the next run and are left out." ELSE "" END
// 🟢 KPI 3 Tip   "A gap open at the " + [Prior Month] + " close and still open now, as one continuous episode. A flag that cleared and came back is a new gap."
// 🟢 KPI 4 Tip   "No Helix ticket carries an ID that links it to the gap. A ticket may exist without one: 'no linked ticket' does not mean nobody is working on it."
// 🟢 KPI 5 Tip   "Days since the gap began, strictly over 90. Gap age, not ticket age: a gap can be older than its ticket."
```

### 7.6 Sankey (section 9 builds the sheet; D6, D7)

```
// 🟢 Sankey Gap Row       [Gap Now]
// 🟢 Sankey Gap           IIF([Sankey Gap Row], 1, 0)
// 🟢 Anchor Key           STR([month_end_date]) + "|" + [ticket_number]
// 🟢 Is Anchor            [Is Ticket] AND [Anchor Key] = { FIXED [place] : MIN(IF [Is Ticket] THEN [Anchor Key] END) }
// 🟢 Place Gaps           { FIXED [place] : SUM([Sankey Gap]) }
// 🟢 Sankey Anchor        [Is Anchor] AND [Place Gaps] > 0
// 🟢 Sankey Row           [Sankey Gap Row] OR [Sankey Anchor]
// 🟢 Sankey Weight        IF [Sankey Anchor] THEN 0 ELSE [Sankey Gap] END              (S7: 0.001 if the extension drops zero rows)

// 🟢 Flag Gaps            { FIXED [flag_label] : SUM([Sankey Gap]) }
// 🟢 Flag Text            [flag_name] + " (" + STR([Flag Gaps]) + ")"
// 🟢 First Flag           { FIXED : MIN(IF [Sankey Gap Row] THEN [flag_label] END) }
// 🟢 First Flag Text      { FIXED : MIN(IF [Sankey Gap Row] AND [flag_label] = [First Flag] THEN [Flag Text] END) }
// 🟢 First Flag Name      { FIXED : MIN(IF [Sankey Gap Row] AND [flag_label] = [First Flag] THEN [flag_name] END) }
// 🟢 What differs         IF [Sankey Anchor] THEN [First Flag Name] ELSE [flag_name] END        (no count: see 9.3)
// 🟢 Flag Sort            IF [Sankey Anchor] THEN [First Flag] ELSE [flag_label] END

// 🟢 Risk Gaps            { FIXED [risk] : SUM([Sankey Gap]) }
// 🟢 Risk Text            [risk] + " (" + STR([Risk Gaps]) + ")"
// 🟢 First Risk           { FIXED : MIN(IF [Sankey Gap Row] THEN [risk] END) }
// 🟢 First Risk Text      { FIXED : MIN(IF [Sankey Gap Row] AND [risk] = [First Risk] THEN [Risk Text] END) }
// 🟢 What it puts at risk IF [Sankey Anchor] THEN [First Risk] ELSE [risk] END                  (no count: see 9.3)

// 🟢 Where it is aligned  [place_label]                                                         (no count: see 9.3)
```

The three level names are the extension's column headers, so they are named as the prototype's headers. They replace `Flag Label (n)`, `Risk Label (n)` and `Place Label (n)` from the spikes (rename those to these names and edit the formulas, so nothing that uses them breaks).

### 7.7 Sankey tooltip (replaces the S3 table in the spike guide)

```
// 🟢 Tip Gaps            SUM([Sankey Gap])
// 🟢 Tip Share           SUM([Sankey Gap]) / MIN({ FIXED : SUM([Sankey Gap]) })                      (format: percentage, 0 decimals)
// 🟢 Tip Flags           COUNTD(IF [Sankey Gap Row] THEN [flag_label] END)
// 🟢 Tip Risks           COUNTD(IF [Sankey Gap Row] THEN [risk] END)
// 🟢 Tip Places          COUNTD(IF [Sankey Gap Row] THEN [place] END)
// 🟢 Tip Is Flag         [Tip Flags] = 1
// 🟢 Tip Title           IF [Tip Is Flag] THEN MIN(IF [Sankey Gap Row] THEN [flag_name] END)
//                     ELSEIF [Tip Risks] = 1 AND [Tip Places] = 1
//                       THEN MIN(IF [Sankey Gap Row] THEN [risk] END) + ", aligned in " + MIN(IF [Sankey Gap Row] THEN [place] END)
//                     ELSEIF [Tip Risks] = 1 THEN MIN(IF [Sankey Gap Row] THEN [risk] END)
//                     ELSE MIN(IF [Sankey Gap Row] THEN [place_label] END) END
// 🟢 Tip Ranked          [Tip Is Flag] AND MIN([Scope Is All])                                       (D10)
// 🟢 Tip Rank            IF [Tip Ranked] THEN "Rank " + STR(MIN([flag_rank])) + " of 9" END
// 🟢 Tip Rank Worse      IF [Tip Ranked] AND MIN([flag_rank]) < MIN([flag_rank_prior_close])
//                     THEN "up from " + STR(MIN([flag_rank_prior_close])) + " at the prior close (" + STR(MIN([flag_count_prior_close])) + ")" END
// 🟢 Tip Rank Better     (same with >, "down from")
// 🟢 Tip Rank Same       IF [Tip Ranked] AND MIN([flag_rank]) = MIN([flag_rank_prior_close])
//                     THEN "same rank as the prior close (" + STR(MIN([flag_count_prior_close])) + ")" END
// 🟢 Tip Year Ago        IF [Tip Ranked] AND NOT ISNULL(MIN([flag_rank_year_ago]))
//                     THEN "A year ago: " + STR(MIN([flag_count_year_ago])) + " gaps, rank " + STR(MIN([flag_rank_year_ago])) END
// 🟢 Tip Puts At Risk    IF [Tip Is Flag] THEN "Puts at risk: " + MIN(IF [Sankey Gap Row] THEN [risk] END) END
// 🟢 Tip Bridgeway       IF SUM(IF [Sankey Gap Row] AND [place] = "Bridgeway" THEN 1 END) > 0
//                     THEN "Bridgeway (vendor system) " + STR(SUM(IF [Sankey Gap Row] AND [place] = "Bridgeway" THEN 1 END)) END
// 🟢 Tip Keystone        (same for "Keystone", "Keystone (HR system) ")
// 🟢 Tip System Feed     (same for "System feed", "System feed (integration) ")
// 🟢 Tip From            IF NOT [Tip Is Flag] THEN "From " + STR([Tip Flags]) + " flags" END
// 🟢 Tip Feed Causes     IF [Tip Places] = 1 AND MIN(IF [Sankey Gap Row] THEN [place] END) = "System feed"
//                     THEN STR(SUM(IF [Sankey Gap Row] AND [timing_class] = "Feed event failed" THEN 1 ELSE 0 END)) + " failed feed events, "
//                        + STR(SUM(IF [Sankey Gap Row] AND [timing_class] = "Load failed" THEN 1 ELSE 0 END)) + " failed loads, "
//                        + STR(SUM(IF [Sankey Gap Row] AND [timing_class] = "Feed stuck" THEN 1 ELSE 0 END)) + " stuck" END
// 🟢 Tip No Ticket       IF SUM(IF [Sankey Gap Row] AND NOT [has_ticket] THEN 1 END) > 0
//                     THEN STR(SUM(IF [Sankey Gap Row] AND NOT [has_ticket] THEN 1 END)) + " with no ticket" END
// 🟢 Tip Over 90         IF SUM(IF [Sankey Gap Row] AND [days_open] > 90 THEN 1 END) > 0
//                     THEN STR(SUM(IF [Sankey Gap Row] AND [days_open] > 90 THEN 1 END)) + " open more than 90 days" END
// 🟢 Tip Next Step       IF [Tip Is Flag] THEN "Next step: " + MIN(IF [Sankey Gap Row] THEN [next_step] END)
//                     ELSEIF [Tip Places] = 1 AND MIN(IF [Sankey Gap Row] THEN [place] END) = "System feed" THEN "Worked by Data Engineering"
//                     ELSE "Next steps differ by gap: see the gap list" END
```

Every Tip calc counts only `Sankey Gap Row`, so the anchors (section 9.2) never change a tooltip.

### 7.8 Main card headline and subtitle

```
// 🟢 Total Gaps          { FIXED : SUM([Sankey Gap]) }
// 🟢 Top Place Gaps      { FIXED : MAX(IF [Sankey Gap Row] THEN [Place Gaps] END) }
// 🟢 Top Place           { FIXED : MIN(IF [Sankey Gap Row] AND [Place Gaps] = [Top Place Gaps] THEN [place] END) }
// 🟢 Top Flag Gaps       { FIXED : MAX(IF [Sankey Gap Row] THEN [Flag Gaps] END) }
// 🟢 Top Flag            { FIXED : MIN(IF [Sankey Gap Row] AND [Flag Gaps] = [Top Flag Gaps] THEN [flag_name] END) }
// 🟢 Top Flag Prior Rank { FIXED : MIN(IF [Sankey Gap Row] AND [flag_name] = [Top Flag] THEN [flag_rank_prior_close] END) }
// 🟢 Clear Own Gaps      { FIXED : SUM(IF [Sankey Gap Row] AND NOT [is_counted] THEN 1 ELSE 0 END) }
// 🟢 Move                ABS([flag_rank_year_ago] - [flag_rank])
// 🟢 Max Move            { FIXED : MAX(IF [Sankey Gap Row] THEN [Move] END) }
// 🟢 Mover               { FIXED : MIN(IF [Sankey Gap Row] AND [Move] = [Max Move] THEN [flag_label] END) }
// 🟢 Mover Text          { FIXED : MIN(IF [Sankey Gap Row] AND [flag_label] = [Mover] THEN
//                       [flag_name] + ": " + [Ordinal YA] + " a year ago (" + STR([flag_count_year_ago]) + "), "
//                       + [Ordinal Now] + " now (" + STR([Flag Gaps]) + ")" END) }
// 🟢 Ordinal Now         STR([flag_rank]) + CASE [flag_rank] WHEN 1 THEN "st" WHEN 2 THEN "nd" WHEN 3 THEN "rd" ELSE "th" END
// 🟢 Ordinal YA          (same on flag_rank_year_ago)
// 🟢 Comma helper        Total Gaps Str, Top Place Gaps Str, Top Flag Gaps Str: the comma pattern of 7.4

// 🟢 Main Title
IF ZN([Total Gaps]) = 0 THEN "No gaps in this selection"
ELSE [Top Place] + " holds " + [Top Place Gaps Str] + " of " + [Total Gaps Str] + " gaps. Largest flag: " + [Top Flag] + " (" + [Top Flag Gaps Str] + ")" END

// 🟢 Main Subtitle       (aggregate: every LOD inside MIN(), so it can use Has Prior)
(IF ZN(MIN([Total Gaps])) = 0 THEN "Choose another close or fewer groups"
ELSEIF NOT [Scope Is All] THEN "Ranks and year-ago comparisons cover all of Arcadia: choose All in the rail to see them"
ELSEIF NOT [Has Prior] THEN "First close in the data"
ELSE (IF MIN([Top Flag Prior Rank]) = 1 THEN "Same largest flag as " ELSE "New largest flag since " END) + [Prior Month] + ". "
   + (IF ZN(MIN([Max Move])) = 0 THEN "No flag changed rank since a year ago" ELSE MIN([Mover Text]) END)
END)
+ (IF MIN([Clear Own Gaps]) > 0 THEN " · " + STR(MIN([Clear Own Gaps])) + " clear on their own by the next run" ELSE "" END)
```

Expected: Current "Bridgeway holds 194 of 407 gaps. Largest flag: Order open or billed after the end date (100)" / "Same largest flag as May. One person, two IDs: 8th a year ago (24), 6th now (28)". May 2026 "…200 of 418…(99)" / "Same largest flag as April. PID still filled after the end date: 5th a year ago (33), 3rd now (51) · 1 clear on their own by the next run". Jun 2025 "…167 of 349…(85)" / "Same largest flag as May. No flag changed rank since a year ago · 3 clear on their own by the next run". Dec 2024 "…210 of 386…(126)" / "Same largest flag as November. One person, two IDs: 8th a year ago (18), 7th now (22)". Technology "Bridgeway holds 125 of 263 gaps. Largest flag: Order open or billed after the end date (73)".

### 7.9 Timeline, ticket card, gap list, rail and popovers

Written with their sheets: 14.1 (timeline), 15.1 (ticket card), 13.1 (gap list), 10 (rail), 11.1 to 11.4 (popovers), 16 (title and load note).

---

## 8. Step 5: the dashboard shell and containers (build first)

**Why first.** The Sankey is the page. This step puts every card on the page at its final size with placeholders, and drops the Sankey into its real tile, so step 6 (section 9) can tune the Sankey where it will live. Nothing here needs a calculation; the rail controls, KPI texts and the other cards replace their placeholders later, one by one (drag the sheet next to the placeholder inside the same container, then delete the placeholder).

**Before:** step 2 (the workbook). The `Sankey` sheet from the spikes as it is.

### 8.1 The page

1. New dashboard, name it **Contingent Workforce Reconciliation**.
2. Size: **Fixed size, 1400 × 850** (Dashboard pane > Size > Fixed size > Custom).
3. Format > Dashboard: Dashboard Shading **`#F3F3EF`**; Dashboard Title off.
4. Every item from here on: **Floating** (hold Shift while dragging, or set the Objects pane toggle to Floating), Show title off, inner and outer padding 0 unless stated. Type every x, y, w, h in the Layout pane.

### 8.2 The map of the page

```
x 0      216  246                                      1004 1020               1370 1400
y 0  ┌────────┬─────────────────────────────────────────────────────────────────────────┐
     │  RAIL  │  Contingent Workforce Reconciliation                         [load note]│ 14–74
     │ navy   │  Where Bridgeway and Keystone disagree at …                             │
  88 │        │ ┌card 1─┐ ┌card 2─┐ ┌card 3─┐ ┌card 4─┐ ┌card 5─┐                       │ KPI band 88–174
     │        │ └───────┘ └───────┘ └───────┘ └───────┘ └───────┘                       │
 190 │        │ ┌ Main card (Sankey · Gap list) ──────────┐ ┌ Timeline ────────┐         │ 190–480
     │        │ │ title 44                                │ │                  │         │
     │        │ │ Sankey 726 × 546                        │ └──────────────────┘         │
     │        │ │                                         │ ┌ Open tickets ────┐ 496     │
     │        │ │                                         │ │                  │         │
 812 │        │ └─────────────────────────────────────────┘ └──────────────────┘ 812     │
 822 │        │  footnote                                                               │
 850 └────────┴─────────────────────────────────────────────────────────────────────────┘
```

| # | Item | Type | x | y | w | h | Format |
|---:|---|---|---:|---:|---:|---:|---|
| 1 | `Rail` | Vertical container | 0 | 0 | 216 | 850 | Background navy `#13233A`, border None, inner padding **left 8, right 8**, top 0, bottom 0 (items are 200 wide) |
| 2 | Page title (placeholder) | Text | 246 | 14 | 760 | 60 | Line 1 `Contingent Workforce Reconciliation` Tableau Bold 18 navy `#13233A`; line 2 `Where Bridgeway and Keystone disagree at the June 2026 close, and where each gap is aligned` Tableau Book 10 slate `#5A6170`. Replaced by the `Page Title` sheet in section 16 |
| 3 | Load note (later) | | 1050 | 30 | 320 | 28 | Section 16; nothing now |
| 4 | KPI band image `arcadia_kpi_cards_bg_summary.png` | Image | 0 | 76 | 1400 | 110 | **Fit Image**, no border. The cards it draws sit at x 246, 474, 702, 930, 1158 and y 88, 212 × 86 (Dashboard #2's file, already in `Images and Buttons`) |
| 5 | `Card: Main` | Vertical container | 246 | 190 | 758 | 622 | Background `#FBFBF8`, border solid 1 px `#E4E3DD`, corner radius 10 (all four), inner padding **16** all sides |
| 6 | `Card: Timeline` | Vertical container | 1020 | 190 | 350 | 290 | Same card format |
| 7 | `Card: Tickets` | Vertical container | 1020 | 496 | 350 | 316 | Same card format |
| 8 | Footnote | Text | 246 | 822 | 1124 | 16 | `Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic. Executive officers excluded. Groups follow the cost center Bridgeway bills.` Tableau Book 9 slate `#5A6170` |

Rows: band 88 + 86 = 174, + 16 = 190; main and tickets end at 812 (190 + 622; 496 + 316); timeline 190 + 290 = 480, + 16 = 496. Columns: 246 + 758 = 1004, + 16 = 1020, + 350 = 1370 (30 px frame to 1400).

### 8.3 The rail (container 1, tiled items inside, top to bottom)

Every rail item is **tiled inside `Rail`**, 200 wide. Headings are Text objects: Tableau Bold 8, `#B8C4D6`, inner padding 0, height 16. Gaps are Blank objects of the exact height. Placeholders are Blanks with a background, so you see the capsules now.

| # | Item | Type | w × h | Running y (bottom) | Now | Later |
|---:|---|---|---|---:|---|---|
| R1 | Blank | Blank | 200 × 24 | 24 | | |
| R2 | `Rail Top` | Horizontal container | 200 × 40 | 64 | | |
| R2a | └ Logo `arcadia_logo_horizontal_reverse.png` | Image | 148 × 40 | | Fit Image | |
| R2b | └ Blank | Blank | 24 × 40 | | | |
| R2c | └ Info placeholder | Blank | 28 × 40 | | | `Info Button` sheet, inner padding top 12, bottom 12, left 12 (icon 16 × 16) |
| R3 | Blank | Blank | 200 × 28 | 92 | | |
| R4 | `POINT IN TIME` | Text | 200 × 16 | 108 | | |
| R5 | Blank | Blank | 200 × 6 | 114 | | |
| R6 | Close capsule placeholder | Blank, background **white** `#FFFFFF`, corner radius 16 | 200 × 32 | 146 | | `Close Field` sheet |
| R7 | Blank | Blank | 200 × 24 | 170 | | |
| R8 | `FUNCTION` | Text | 200 × 16 | 186 | | |
| R9 | Blank | Blank | 200 × 6 | 192 | | |
| R10 | Function capsule placeholder | Blank, background `#1B2D45`, border solid 1 px `#4A5B73`, radius 16 | 200 × 32 | 224 | | `Function Field` |
| R11 | Blank | Blank | 200 × 24 | 248 | | |
| R12 | `DEPARTMENT` | Text | 200 × 16 | 264 | | |
| R13 | Blank | Blank | 200 × 6 | 270 | | |
| R14 | Department capsule placeholder | as R10 | 200 × 32 | 302 | | `Department Field` |
| R15 | Blank | Blank | 200 × 24 | 326 | | |
| R16 | `COUNTRY` | Text | 200 × 16 | 342 | | |
| R17 | Blank | Blank | 200 × 6 | 348 | | |
| R18 | Country capsule placeholder | as R10 | 200 × 32 | 380 | | `Country Field` |
| R19 | Divider `arcadia_rail_divider.png` | Image | 200 × 24 | 404 | Fit Image | |
| R20 | `SHOW` | Text | 200 × 16 | 420 | | |
| R21 | Blank | Blank | 200 × 6 | 426 | | |
| R22 | Toggle placeholder | Blank, background `#1B2D45`, radius 16 | 200 × 32 | 458 | | `Show Toggle` |
| R23 | Divider | Image | 200 × 24 | 482 | | |
| R24 | Reset placeholder | Blank, border solid 1 px `#8A97A8`, radius 16 | 200 × 32 | 514 | | `Reset` |
| R25 | Blank (flexible) | Blank | 200 × rest | 790 | | |
| R26 | As-of placeholder | Text: `Data as of Jun 30, 2026` Tableau Semibold 9 `#E4E9F0`, line 2 `Refreshed daily at 00:00 GMT` Tableau Book 9 `#B9C3D1` | 200 × 36 | 826 | | `Rail As Of` sheet (follows the close) |
| R27 | Blank | Blank | 200 × 24 | 850 | | |

How to make it: drag a **Vertical** container onto the page as Floating, set item 1's position and format; then drag each item **into** it from the Objects pane in order, top to bottom (a grey bar shows where it lands). After each, select it and type its size. For R25 select the Blank and leave its height to fill (the container gives it what is left: 850 − 24 − 36 − 24 − 514 = 252). Popovers hang from the rail edge at x 216, level with the heading of their control: Point in time y 92, Function y 170, Department y 248, Country y 326, Info y 24 (section 11).

### 8.4 The cards (containers 5 to 7, tiled items inside)

| Container | Item | Type | w × h | Now | Later |
|---|---|---|---|---|---|
| `Card: Main` (inner 726 × 590) | Title placeholder | Text: `Bridgeway holds 194 of 407 gaps. Largest flag: Order open or billed after the end date (100)` Tableau Semibold 12 navy, line 2 `Same largest flag as May. One person, two IDs: 8th a year ago (24), 6th now (28)` Tableau Book 9 slate | 726 × 44 | | `Main Title` and `Gap List Title` sheets (9.6, 13.3) |
| | **`Sankey`** | Sheet | 726 × 546, outer padding **top 6** (drawn 726 × 540) | **the spike sheet** | the final sheet (section 9) |
| | Gap list | | | | `Gap List` sheet, same tile (section 13) |
| `Card: Timeline` (inner 318 × 258) | Title placeholder | Text: `Gap rate at each month-end close` Semibold 12 navy, line 2 `Contractors with a gap divided by contractors working in Bridgeway · last 13 closes` Book 9 slate | 318 × 56 | | `Timeline Title` |
| | Chart placeholder | Blank | 318 × 202 | | `Timeline` |
| `Card: Tickets` (inner 318 × 284) | Title placeholder | Text: `Open tickets by where they are aligned` Semibold 12 navy, line 2 `One dot per Helix ticket open at the close` Book 9 slate | 318 × 44 | | `Tickets Title` |
| | Body placeholder | Blank | 318 × 240 | | the ticket body (section 15) |

The `Sankey` sheet in its tile: Fit Entire View, background None (the card's `#FBFBF8` shows), Show title off. Dashboard `Dashboard 1` (the spike) can now be deleted.

### 8.5 Front to back

Layout pane > Item hierarchy, top of the list is in front: (later: the five popovers), `Rail`, (later: `KPI Hover 1`–`5`, `KPI Cards`), KPI band image, the three cards, page title, footnote. **The rail must be in front of `KPI Cards`** (section 12): that map sheet is 1400 wide, so without it the map would sit over the rail and steal the clicks on the Point in time and Function capsules.

### 8.6 Check (screenshot to me)

Presentation mode: the rail runs the full height with the logo, four headings and capsules, SHOW, Reset and the as-of text at the bottom; the five KPI card outlines line up with the title's left edge (x 246) and the right edge of the tickets card (x 1370); the main card, the timeline and the tickets cards end level at y 812; the Sankey fills its tile with nothing clipped; the footnote sits under the cards. Then section 9, in place.

---

## 9. Version A: the extension Sankey (kept in the workbook, not on the page; the page uses 9N)

**Before:** the parameters `p_Close`, `p_Functions`, `p_Departments`, `p_Countries` (section 6) and the calcs of 7.1, 7.6, 7.7 and 7.8. The rail controls are not needed yet: set a parameter by hand to test (right-click it > Show Parameter, then remove the control).

### 9.1 What step 6 changes on the spike sheet

| Shelf | Spike | Final |
|---|---|---|
| Filters | `is_latest_close` True, `row_type` Gap | **`Sankey Row` = True** only (it already carries the close, the scope and the anchors) |
| Levels | `Flag Label (n)`, `Risk Label (n)`, `Place Label (n)` | **`What differs`**, **`What it puts at risk`**, **`Where it is aligned`** (7.6) |
| Link | `SUM(gaps)` | **`SUM(Sankey Weight)`** |
| Sort of `What differs` | by its own text | right-click the pill > Sort > **Field `Flag Sort`, Minimum, Ascending** |
| Tooltip | the S3 calcs | the 7.7 calcs (same names; edit the formulas) |

### 9.2 Anchors keep the place order under a filter (spike S7)

**The finding.** The extension orders places by first appearance, reading rows in flag order. With every group, flag 01 reaches Bridgeway first. With one function, flag 01 may have only Keystone gaps (a conversion), and then Keystone comes first. Checked on the data with the rule that matched S1: the order breaks for **253 of 487 function × close combinations, 408 of 1,173 country × close, 656 of 1,722 department × close** (at the June close: Marketing, Finance, People, Commercial, Legal & Compliance, and six countries).

**The fix.** Three extra rows, one per place, with weight 0, whose flag and risk are the **first flag and first risk in the current selection**. They sort before every real row of that flag, so the first three appearances are always Bridgeway, Keystone, System feed. They need no change to the data: they are three existing Ticket rows (`Is Anchor`, one per place, the same three at every close and scope), relabelled by the 7.6 calcs. An anchor is used only if its place has gaps in the selection (`Sankey Anchor`), so an empty place never shows as a zero node.

**S7 passed 2026-10-25** (section 4). The test, for the record:

**Test (on the `Sankey` sheet, in its tile).**
1. Before the fix, confirm the finding: set `p_Functions` to `|Marketing|` (right-click the parameter > Show Parameter, type it). Expected with the spike filters: Keystone above Bridgeway. If it shows Bridgeway first, tell me (the rule would be different from S1).
2. Apply 9.1. Expected at `|Marketing|`: Bridgeway, Keystone, System feed, top to bottom; the node labels show only real gaps; nothing extra in the flag column.
3. If an anchor's link disappears and the order is still wrong, the extension drops zero rows: change `Sankey Weight` to `IF [Sankey Anchor] THEN 0.001 ELSE [Sankey Gap] END` and test again (0.001 of a gap is invisible; the labels use our own counts, so they still read whole numbers).
4. Set `p_Functions` back to empty.

**Fallback** if neither works: the places keep their colours, and a group filter may change their order. Recorded as a known limit in the info text.

### 9.3 Colours (S3, D9)

Format Extension > Edit Colors, per level and node (pick the palette, then the swatch; check the hex in the picker):

| Level | Nodes | Palette | Swatch |
|---|---|---|---|
| What differs | One person, two IDs · Bridgeway ID missing or different · In Bridgeway, not in Keystone · Order open or billed after the end date · Cost center differs · PID still filled after the end date · Two active PID records · Working in Bridgeway, ended in Keystone · Active in Keystone, not working in Bridgeway | Tableau 20 | light red · green · light orange · red · light pink · light green · light purple · yellow · light blue |
| What it puts at risk | all five | Miller Stone | 1st, slate `#4F6980` |
| Where it is aligned | Bridgeway (vendor system) · Keystone (HR system) · System feed (integration) | Hue Circle | 10th amber `#F89217` · 18th violet `#7873C0` · 4th teal `#21B087` |

**Persistence test: failed, fixed and passed on 2026-10-25.** Re-run after the fix at Jun 2026 with `|Marketing|`, Dec 2024 with `|Marketing|` and Dec 2024 with every group: the same colours in all three, places in the order Bridgeway, Keystone, System feed (System feed absent for Marketing, no empty node).

**What failed first, and why the levels lost their counts.** The extension saves each colour under the node's full text, so with the count in the text ("One person, two IDs (28)") the same flag at Dec 2024 ("(22)") or under `|Marketing|` ("Order open or billed after the end date (2)") is a new node with a default colour. The three level fields are therefore plain names (7.6): `What differs` = `flag_name`, `What it puts at risk` = `risk`, `Where it is aligned` = `place_label`, each with its anchor version. A node keeps its colour at every close and under every filter. `tableau/build/d4_fields/patch_levels.py` made the change in the workbook and carried the nine flag, five risk and three place colours already chosen over to the new names.

The count now comes from the extension's own value label (Format Extension, the level label setting; it shows the node size from `Sankey Weight`, anchors weigh 0). `Flag Text`, `Risk Text`, `First Flag Text` and `First Risk Text` no longer feed the levels; leave them, they are harmless.

### 9.4 Labels, sizes and the header

| Setting (Format Extension) | Value | Why |
|---|---|---|
| Label colour | **Automatic** | White on the slate risks, black on flags and places |
| Label font size | **9** (10 if flag 09 still fits) | One setting for every level; flag 09 (12 gaps) is about 14 px tall in a 540 px tile |
| Show percentage on nodes | **Off** | One line per label, so small nodes do not overlap; the share is in the tooltip |
| Node (level) width | start at **150**; record the value that keeps every label inside its node | Labels inside the nodes |
| Node padding | the smallest that still separates nodes | Gives the height back to the small flags |
| Link opacity | the default; risks-to-places in their place colour if the extension offers "colour links by target" (S3 question) | |
| Column headers | Show, if the extension shows the level names: they read "What differs", "What it puts at risk", "Where it is aligned" | The prototype's three headers come free |

**Tune in place** (that is the point of step 5): judge in Presentation mode, at the Current close and at Dec 2024. Record each value you settle on in a reply to me, and I write it into this table.

**Pass:** the three columns read in the prototype's order; every label is inside its node and readable, flag 09 included; the colours hold at Dec 2024 and with `|Marketing|`; hovering a flag, a risk and a place shows the three tooltips of the canvas board *Sankey tooltips*.

### 9.5 Tooltip

Layout and colours as in the spike guide (S3, item 5), with the 7.7 calcs: **Tip Title** navy `#13233A` Tableau Semibold 12 / **Tip Gaps** gaps, **Tip Share** of all gaps (Book 9 `#5A6170`, the numbers Semibold navy) / Tip Rank + Tip Rank Worse (coral `#B8401F`) + Tip Rank Better (teal `#0E7D5F`) + Tip Rank Same (gray `#5A6170`) on one line / Tip Year Ago / Tip Puts At Risk / "Aligned in:" Tip Bridgeway (`#B86400`), Tip Keystone (`#5650A0`), Tip System Feed (`#0E7D5F`) / Tip From / Tip Feed Causes / Tip No Ticket (coral) , Tip Over 90 / Tip Next Step (gray italic). Command buttons off.

Expected, Current, no group: hover flag "Bridgeway ID missing or different": "49 gaps, 12% of all gaps · Rank 4 of 9 up from 5 at the prior close (47) · A year ago: 40 gaps, rank 4 · Puts at risk: Active headcount mismatch · Aligned in: Keystone (HR system) 49 · 24 with no ticket, 39 open more than 90 days · Next step: Align the Bridgeway ID stored in Keystone" (your screenshot, 2026-10-25). With `|Technology|`: the same flag reads 31 gaps and shows no rank or year-ago lines.

### 9.6 Main card title sheet (`Main Title`)

Text mark, `Main Title` and `Main Subtitle` on Label: line 1 Tableau Semibold 12 navy, line 2 Tableau Book 9 slate `#5A6170`; alignment Left, Middle; Worksheet shading None; Fit Entire View; tooltip off; `zzTrue`, `zzFalse` on Detail (deselect, section 17). Replaces the title placeholder in `Card: Main` (726 × 44). Expected: 7.8.

---

## 9N. Step 6: the native Sankey (the one on the page)

**Why (D15).** The viz extension draws labels only inside the nodes and colours a link only by its source. In the 726 × 540 tile that gave wide nodes, spilt labels and a second link in one grey ([options board](img/sankey_options.png)). A native Sankey gives thin nodes, labels beside them, and every ribbon in the colour of the place that aligns it, the same amber, violet and teal as the ticket card. Version A (section 9, the extension on the `Sankey` sheet) stays in the workbook, unchanged, for reference; it is not on the page.

**What is already done (🟢).**
- **Data.** The Custom SQL has a fourth row type, `Sankey`: 2,188 scaffold rows built from the flag, risk and place taxonomy, with no close and no group. `sk_part` is `Link` (`sk_level` 1 runs flag to risk, 2 runs risk to place; `sk_point` 0 to 49 runs along the ribbon's two edges), `Node` (`sk_point` 0 to 3, the corners), `Label` or `Header`. Gap and Sankey rows also carry `flag_short`, the short name every viewer sees. The DuckDB mart has the same rows; `check_tsql_in_duckdb.py` matches them row for row (67,623), and `15_validate` checks the new counts.
- **Workbook.** `tableau/build/d4_fields/build_sankey.py` wrote the new Custom SQL (both copies), registered the four new columns, and added 3 parameters and 142 `Sk` calcs (`spec_sankey.py`). Existing fields are only read, never changed.
- **Proof.** `verify_sankey.py` runs the `Sk` formulas themselves on the mart (FIXED LODs as window aggregates) and draws the result. It matches the design at Jun 2026, Dec 2024 and Jun 2026 with Marketing ([check](img/native_sankey_check.png); flag codes stand in for the names, because the check skips text fields).

**How it works.** Every point is a FIXED LOD of the selection (`Sankey Gap` = `Gap Now`, so the close and the groups apply), evaluated on scaffold rows that carry the keys. No table calcs, so nothing depends on Compute Using.

| Piece | Fields |
|---|---|
| Node counts | `Sk F1`–`F9`, `Sk R1`–`R5`, `Sk P1`–`P3`: gaps per flag, risk and place in the selection (the taxonomy is fixed at 9 / 5 / 3) |
| Scale | `Sk Scale` = (height − `Sk Pad` × (nodes in the fullest column − 1)) / total gaps. Each column spreads its nodes over the full height (`Sk Gap F`, `R`, `P`), so a column with fewer nodes has wider gaps and the ribbons slant |
| Node tops | `Sk Y Flag`, `Sk Y Risk`, `Sk Y Place`: gaps before the node × scale + non-empty nodes before it × the column gap. Empty nodes take no space |
| Ribbons | Flag to risk, one band per flag × place (`Sk FP`), so each band already has its place colour. Risk to place, one per risk × place (`Sk RP`). Offsets in each node: `Sk FP Before`, `Sk RP Before`, `Sk PR Before` |
| Curve | `Sk T Along` runs 0 to 1 on the top edge and back on the bottom edge; `Sk Ease` = 3t² − 2t³ |
| Coordinates | `Sk X`, `Sk Y` for every part. `Sk Y Shape` (links and nodes) and `Sk Y Text` (labels and headers) split them over the two axes |

### 9N.1 Refresh the extract (SQL Server running in Docker)

1. Open the workbook. If Tableau warns that `flag_short` or `sk_…` columns are missing, the extract is older than the SQL. Continue.
2. Data > CW Reconciliation > Extract > Refresh.
3. Expected on `CHK Rows`: **Gap 21,665 · Population 27,324 · Sankey 2,188 · Ticket 16,446** (67,623). The other sheets do not change, because no existing field reads the new rows.

### 9N.2 Sheet `Sankey Native`

1. New worksheet `Sankey Native`. Right-click `sk_point` in the Data pane > Convert to Dimension.
2. Filters: `Sk Show` = True.
3. Columns: `Sk X` (AVG). Rows: `Sk Y Shape` (AVG), then `Sk Y Text` (AVG). Right-click the second pill > Dual Axis; right-click its axis > Synchronize Axis.
4. Axes: `Sk X` Fixed **0 to 576**. `Sk Y Shape` Fixed **0 to 540**, **Reversed** (check the right axis follows; set it the same if not). Then uncheck Show Header on all three. Right-click the null indicator, bottom right > Hide Indicator.
5. Marks card **AVG(Sk Y Shape)**: Polygon. Detail `Sk Mark`; Path `sk_point`; Color `Sk Colour` (table below), opacity **100%**, border None. On the `Sk Mark` pill: Sort > Field `Sk Draw`, Minimum, Ascending (wide ribbons first, thin ones on top, nodes last).
6. Marks card **AVG(Sk Y Text)**: Circle, size smallest, opacity **0%**. Detail `Sk Mark`. Label: `Sk Lbl Header`, `Sk Lbl Place`, `Sk Lbl Name`, `Sk Lbl Count`, `Sk Lbl Sub`, written as:
   ```
   <Sk Lbl Header><Sk Lbl Place><Sk Lbl Name> <Sk Lbl Count>
   <Sk Lbl Sub>
   ```
   Fonts: Header Tableau Book 8 `#6B7079`; Place Tableau Semibold 10 navy `#13233A`; Name Tableau Book 9 navy; Count Tableau Book 9 `#6B7079`; Sub Tableau Book 9 `#5A6170`. Alignment: horizontal **Right** (the text starts right of the point), vertical **Middle**. Options: **Allow labels to overlap other marks** on. Tooltip: off on this card.
7. Format: grid lines, zero lines and axis rulers None; borders None; worksheet shading None.

**Flag labels on their own sheet (revision 5).** The flag names sit left of the flag nodes, right-aligned, as in the prototype. Label alignment is one setting per Marks card, so they get their own sheet beside the Sankey, tiled, not floating over it, so the Sankey keeps its hovers and clicks. `Sk Y Text` carries the risk and place labels only; `Sk Flag Y` and `Sk Flag X` (144) carry the flags and "What differs".

**Sheet `Sankey Flag Labels`:** Filters `Sk Show` = True. Columns `Sk Flag X` (AVG), axis Fixed 0 to 150; Rows `Sk Flag Y` (AVG), axis Fixed 0 to 540, Reversed; headers and the null indicator hidden. Circle, smallest, opacity 0%; Detail `Sk Mark`; Label `<Sk Lbl Header><Sk Lbl Name> <Sk Lbl Count>` (names Book 9 navy, counts Book 9 `#6B7079`, header Book 8 `#6B7079`), alignment horizontal **Left** (the text ends at the point, 6 px before the nodes), vertical Middle, overlap allowed. Tooltip off; lines, borders and shading None. Optional: the three "Sankey picks" actions with this sheet as a second source.

| `Sk Colour` | Hex | What |
|---|---|---|
| Bridgeway ribbon | `#FBC37F` | Amber at 55% on white |
| Keystone ribbon | `#B5B2DC` | Violet at 55% |
| System feed ribbon | `#85D4BD` | Teal at 55% |
| Bridgeway | `#F89217` | Place node |
| Keystone | `#7873C0` | |
| System feed | `#21B087` | |
| Node | `#13233A` | Flag and risk nodes, navy |

**Tooltip** (the polygon card; command buttons off), one line each:
```
<Sk Tip Title>                                                   Tableau Semibold 12 navy
<Sk Tip Full>                                                    Book 9 #5A6170 italic (the flag's full wording)
<Sk Tip N> gaps, <Sk Tip Share> of all gaps                      Book 9 #5A6170; the numbers Semibold navy
<Sk Tip Rank> <Sk Tip Rank Worse><Sk Tip Rank Better><Sk Tip Rank Same>     worse coral #B8401F, better teal #0E7D5F, same #5A6170
<Sk Tip Year Ago>
<Sk Tip Puts At Risk>
<Sk Tip From>
<Sk Tip Aligned In> <Sk Tip Bridgeway>  <Sk Tip Keystone>  <Sk Tip System Feed>   #B86400, #5650A0, #0E7D5F
<Sk Tip Feed Causes>
<Sk Tip No Ticket>  <Sk Tip Over 90>                              no ticket coral
<Sk Tip Next Step>                                               #5A6170 italic
```
Ranks and year-ago lines show only with no group chosen (D10), as on version A.

### 9N.3 On the dashboard

1. In `Card: Main`, remove `Sankey` (the sheet stays in the workbook) and put a **horizontal container** in its place, 726 × 546: `Sankey Flag Labels` **150 × 546** and `Sankey Native` **576 × 546**, both with outer padding top 6 (drawn 540 high) and Fit **Entire View**. The two heights must match, or the labels drift from their nodes.
2. `Main Title` sheet: replace `Main Title` and `Main Subtitle` with **`Sk Main Title`** and **`Sk Main Subtitle`** (the same sentences, with short flag names).
3. Actions (Dashboard > Actions > Change Parameter, source `Sankey Native`, Run on **Select**, clearing **Set value to** empty):

| Name | Target | Field |
|---|---|---|
| Sankey picks a flag | `p_SkFlag` | `Sk Pick Flag` |
| Sankey picks a risk | `p_SkRisk` | `Sk Pick Risk` |
| Sankey picks a place | `p_SkPlace` | `Sk Pick Place` |
| Sankey opens the gap list | `p_ShowList` | `Show List On Click` (parameter actions work on a native sheet, so S2b holds) |

   A click on a flag-to-risk ribbon picks its flag and place; on a risk-to-place ribbon, its risk and place; on a node or its label, that node. The gap list filters on **`Sk Pick Match` = True** (with `Gap List Row`, 13.2), replacing the extension's filter action (13.4). **Reset** also sets `p_SkFlag`, `p_SkRisk` and `p_SkPlace` to `Empty Text` (section 17).
4. The gap list's WHAT DIFFERS column shows `flag_short`, so it uses the chart's names; `flag_name` stays in its tooltip.

### 9N.4 Expected

| State | Flags (01 to 09) | Risks | Places | Headline |
|---|---|---|---|---|
| Current (Jun 2026), all groups | 28 · 49 · 25 · 100 · 69 · 48 · 22 · 54 · 12 | 102 · 100 · 69 · 70 · 66 | Bridgeway 194 · Keystone 151 · System feed 62 | "Bridgeway holds 194 of 407 gaps. Largest flag: Billed after end date (100)" |
| Dec 2024 | 22 · 36 · 18 · 126 · 66 · 33 · 30 · 50 · 5 | 76 · 126 · 66 · 63 · 55 | 210 · 118 · 58 | "…210 of 386…(126)" |
| Jun 2026, `|Marketing|` | 02: 1 · 04: 2 · 05: 1 · 06: 2 (no others) | 1 · 2 · 1 · 2 (no Status) | Bridgeway 3 · Keystone 3 (no System feed) | "Bridgeway holds 3 of 6 gaps…" |

The places read Bridgeway, Keystone, System feed in every state, and the flags 01 to 09, by construction: no anchor rows are needed.

### 9N.5 Tune in place (constants are calcs; edit the number)

| Calc | Now | What it moves |
|---|---:|---|
| `Sk Pad` | 8 | Smallest gap between nodes in the fullest column |
| `Sk Node W` | 10 | Node width |
| `Sk X3` | 436 | Left edge of the place nodes on the 576 px sheet; the place labels use the 130 px to its right |
| `Sk Flag X` | 144 | Right end of the flag labels on their 150 px sheet |
| `Sk Top` | 26 | Room for the headers |
| `Sk Label DX` | 5 | Gap between a node and its label |
| `Sk Label DY` | 0 | Nudge if the one-line labels sit high (the template's empty second line can lift them) |
| Ribbon tints | 55% | The three ribbon colours in the table above |

Record the values you settle on here.

---

## 10. Step 7: rail controls

### 10.1 The control sheets

Shapes from section 20 (`Arcadia D4` palette). Every control: a worksheet whose single mark is a Shape drawing the control, its text as the mark's label, `zzTrue`, `zzFalse`, `Close Panel` on Detail, tooltip off (Close Field: `Choose the close`), Fit Entire View, Worksheet shading None. One mark: filter `Is Selected Close` = True **and** `Is Pop` = True and put `MIN(1)` nowhere (a Shape mark with only Detail fields that are constants is one mark; if Tableau draws several, add `Rail One` = `{ FIXED : MIN([cost_center_id]) } = [cost_center_id]` as a filter, True).

| Sheet | Shape | Label (font) | Detail | Opens |
|---|---|---|---|---|
| `Close Field` | `d4_field_capsule` (white, navy chevron), size slider far right | `Close Field Text` = `IF [Is Current] THEN "Current · " + [Close Short] ELSE [Close Short] + " close" END`, Tableau Semibold 9 navy `#13233A`, Center | `Toggle Close Panel`, `Close Panel`, `zzTrue`, `zzFalse` | Point in time popover |
| `Function Field` | `d4_field_capsule_dark` (`#1B2D45`, `#4A5B73` outline, light chevron) | `Function Field Text`, Tableau Medium 9 `#E4E9F0`, Left with inner padding 14 | `Toggle Function Panel`, `Close Panel`, `zzTrue`, `zzFalse` | Function popover |
| `Department Field` | dark capsule | `Department Field Text` | `Toggle Department Panel`, … | Department popover |
| `Country Field` | dark capsule | `Country Field Text` | `Toggle Country Panel`, … | Country popover |
| `Show Toggle` | `Show Shape` per option (10.2) | none (the words are in the shapes) | `Show Pick`, `Close Panel`, `zzTrue`, `zzFalse` | |
| `Reset` | `d4_reset` (outlined capsule with the words "Reset to default view") | none | `Default Close`, `Empty Text`, `zzFalse`, `Close Panel`, `zzTrue` | |
| `Info Button` | `Info Shape` = `IF [p_InfoOpen] THEN "d2_info_close" ELSE "d2_info_open" END` | none | `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse` | Info popover |
| `Rail As Of` | none (Text mark) | line 1 `IF [Is Current] THEN "Data as of " + <Day Text of p_Close> ELSE "Replaying the " + [Close Short] + " close" END` Tableau Semibold 9 `#E4E9F0`; line 2 `"The 00:00 GMT run on " + <Day Text of p_Close + 1 day>` Tableau Book 9 `#B9C3D1` | `zzTrue`, `zzFalse` | |

`Day Text` = `LEFT(DATENAME('month', x), 3) + " " + STR(DAY(x)) + ", " + STR(YEAR(x))`, written once for `[p_Close]` (`Close Day Text`) and once for `DATEADD('day', 1, [p_Close])` (`Run Day Text`). Expected: Current "Data as of Jun 30, 2026" / "The 00:00 GMT run on Jul 1, 2026"; Dec 2024 "Replaying the Dec 2024 close" / "The 00:00 GMT run on Jan 1, 2025".

🟢 In the workbook: `Close Field Text`, `Close Day Text`, `Run Day Text`, `Rail As Of Line 1` and `Rail As Of Line 2` (the two `Rail As Of` lines above), `Info Shape`, `Default Close`, `Rail One`, and the `Toggle … Panel` and `Toggle Info` fields (7.3).

`Default Close` = `[Latest Close]`. Reset targets: `p_Close` ← `Default Close`; `p_Functions`, `p_Departments`, `p_Countries` ← `Empty Text`; `p_ShowList` ← `zzFalse`; the five open flags ← `Close Panel`.

### 10.2 The Overview · Gap list toggle

Two marks, one per option. The data has no two-row list, so borrow two values of `place` on Gap rows (Bridgeway for Overview, Keystone for Gap list): any column with at least two values would do.

```
// 🟢 Toggle Option        IF [place] = "Bridgeway" THEN "Overview" ELSEIF [place] = "Keystone" THEN "Gap list" END
// 🟢 Toggle Row           [Is Gap] AND [month_end_date] = [Latest Close] AND NOT ISNULL([Toggle Option])
// 🟢 Show Pick            [Toggle Option] = "Gap list"                          (the new value of p_ShowList)
// 🟢 Show Shape           IF [Toggle Option] = "Overview" THEN (IF [p_ShowList] THEN "d4_show_overview_off" ELSE "d4_show_overview_on" END)
//                      ELSE (IF [p_ShowList] THEN "d4_show_gaplist_on" ELSE "d4_show_gaplist_off" END) END
```

Sheet: filter `Toggle Row` = True; Columns `Toggle Option` (sort Overview first: Manual), header hidden; Marks Shape on `Show Shape`, size far right; Detail `Show Pick`, `Close Panel`, `zzTrue`, `zzFalse`. Item 200 × 32 (two cells of 100 × 32). Expected: Overview white pill on load; a click on Gap list moves the pill and swaps the main card (section 13).

---

## 11. Step 8: popovers

### 11.0 One frame (Dashboard #2, section 14.3)

Every popover hangs from the rail edge: **x 216**, navy `#13233A`, corner radius **top-left 0, bottom-left 0, top-right 10, bottom-right 10**, padding 0, border None, **Control visibility using value** = its open flag, top level with its control's heading. Four bands: **header** 44 (title Tableau Bold 12 white, inner padding left 16, top 12; then `Clear` where there is one; then the ✕ sheet 44 × 44 with inner padding 14), **line** 9 (`d2_popover_line_wide.png`, Fit Image), **body**, **footer** 28 (Tableau Book 9 `#8FA0B8`, inner padding left 16, top 6). Rows sit on fixed slots (G3 9.0: continuous row position on odd numbers, fixed reversed axis 0 to 2 × slots, header hidden, Marks Text or Shape). Only one popover open at a time.

| Popover | Visibility | x | y | w | Body | h |
|---|---|---:|---:|---:|---|---:|
| `Close Popover` | `p_CloseOpen` | 216 | 92 | 624 | 8 + 6 × 32 + 8 = 208 | 289 |
| `Function Popover` | `p_FunctionOpen` | 216 | 170 | 312 | 8 + 8 × 26 + 8 = 224 | 305 |
| `Department Popover` | `p_DepartmentOpen` | 216 | 248 | 624 | 8 + 11 × 26 + 8 = 302 | 383 |
| `Country Popover` | `p_CountryOpen` | 216 | 326 | 624 | 8 + 8 × 26 + 8 = 224 | 305 |
| `Info Popover` | `p_InfoOpen` | 216 | 24 | 591 | 387 | 440 |

Bottoms: 381, 475, 631, 631, 464, all above the footnote.

### 11.1 Point in time (`Close Popover`)

A grid: years down (2026 on top), months across. 61 closes, Jun 2021 to Jun 2026.

```
// 🟢 Close Slot          2 * (2026 - YEAR([month_end_date])) + 1                (2026 = 1 … 2021 = 11)
// 🟢 Close Col           2 * MONTH([month_end_date]) - 1                        (Jan = 1 … Dec = 23)
// 🟢 Close Cell          LEFT(DATENAME('month', [month_end_date]), 3)
// 🟢 Close State         IF [month_end_date] = [p_Close] THEN "current" ELSE "on" END
// 🟢 Close Pick          [month_end_date]
// 🟢 Close Year Label    STR(YEAR([month_end_date]))
// 🟢 Close Grid Row      [Is Pop] AND { FIXED [month_end_date] : MIN([cost_center_id]) } = [cost_center_id]   (one row per close)
```

| Item | Type | w × h | Build |
|---|---|---|---|
| Header | Horizontal container | 624 × 44 | "Choose the close" text 580 × 44; `Close Close` (✕) 44 × 44 |
| Line | Image | 624 × 9 | |
| Body | Horizontal container | 624 × 208 | `Close Years` 72 × 208 (inner padding top 8, bottom 8, left 16): Rows `Close Slot` continuous, axis 0 to 12 reversed, Text `Close Year Label` Book 9 `#8FA0B8`. `Close Grid` 552 × 208 (padding top 8, bottom 8, right 16): Rows `Close Slot` (same axis), Columns `Close Col` continuous, axis 0 to 24, Text `Close Cell` Tableau Book 10, Color `Close State` current white `#FFFFFF` Semibold, on `#B8C0CC`; Detail `Close Pick` (exact date, discrete), `Close Panel`, `zzTrue`, `zzFalse`; tooltip off |
| Footer | Text | 624 × 28 | `Each close is the 00:00 GMT run on the 1st. Dec 2024 replays a Keystone outage; Sep 2023 a Bridgeway one.` |

Filter on both sheets: `Close Grid Row` = True. 2021 shows Jun to Dec; 2026 Jan to Jun. Expected: 61 cells; "Jun" in the 2026 row white.

### 11.2 Function (`Function Popover`)

```
// 🟢 Function Slot       (table calc) 2 * (INDEX() - 1) + 1     Compute Using function_name
// 🟢 Function List Row   [Is Pop] AND { FIXED [function_name] : MIN([cost_center_id]) } = [cost_center_id]   (one row per function; Department List Row and Country List Row the same)
// 🟢 Tick X              MIN(0.6)
```

Header: "Choose functions" 492 × 44, `Function Clear` 80 × 44 (Text mark "Clear all", Book 9 `#B8C0CC`, Detail `Empty Text`, `zzTrue`, `zzFalse`), ✕ 44 × 44 (w 312 total: use 188 + 80 + 44). Body `Function List` 312 × 224 (padding top 8, bottom 8, left 16): Rows `Function Slot` (continuous, axis 0 to 16, reversed); Columns `Tick X` (continuous, axis fixed 0 to 10, header hidden); Marks Shape `Function Tick Shape` (`d4_tick_on`, `d4_tick_off`), size small (12 px); Label `function_name` Right, Tableau Book 10, colour by `Function State` (on white `#FFFFFF`, off `#B8C0CC`), allow overlap; Detail `function_name`, `Function Toggle`, `zzTrue`, `zzFalse`; sort `function_name` ascending; filter `Function List Row` = True. Footer: `Choose one or more. None chosen means all functions.`

A click toggles the function and **keeps the popover open**, so several can be ticked in a row; ✕ or another control closes it.

### 11.3 Department and Country (`Department Popover`, `Country Popover`)

Three columns on fixed slots, as Dashboard #3's group panel (G3 9.2) with the D2 table calcs:

```
// 🟢 Pick Rows   INT((SIZE() + 2) / 3)          Pick Col   INT((INDEX() - 1) / [Pick Rows])
// 🟢 Pick Row    2 * ((INDEX() - 1) - [Pick Col] * [Pick Rows]) + 1
```

Columns `Pick Col` (discrete, header hidden), then `Tick X` (continuous 0 to 10, header hidden); Rows `Pick Row` continuous (axis 0 to 22 for departments, 0 to 16 for countries; reversed); Compute Using `department_name` (or `country_name`) on every nested calc. Shape `Department Tick Shape` or `Country Tick Shape` (the Department one adds `d4_tick_dim`); filter `Department List Row` or `Country List Row` = True, label the name Right, Book 9; Color by `Department State`: on white, off `#B8C0CC`, **dim `#56657E`** (outside the chosen functions: still clickable, D in the release plan's phase 8); Detail the name, its `Toggle`, `zzTrue`, `zzFalse`. Header "Choose departments" / "Choose countries" with `Clear all` and ✕; footer `Dim: outside the chosen functions. None chosen means all.` (country: `None chosen means all countries.`).

Expected: Department 31 names in 3 columns (11, 11, 9); Country 22 (8, 8, 6).

**Spike S4 runs here** on Tableau Public: tick Commercial and Technology; the capsule reads "2 selected"; KPI 2 reads 3.23%, the Sankey 280 gaps (Bridgeway 134, Keystone 100, System feed 46). Untick one: 3.20% and 263 (Technology). Each click under about a second. Fallback: native multi-value filters on the three fields, shown as dropdowns in the popovers.

### 11.4 Info (`Info Popover`)

Header "How to read this page" (591 × 44, no ✕: the ⓘ toggles it), line `d2_popover_line_info.png` 591 × 9, body Text 591 × 387, inner padding left 16, right 16, top 4. Lead-ins Tableau Semibold 10 white, body Tableau Book 10 `#B8C0CC`, one empty line between paragraphs:

> **The close.** Finance reports contractors from Keystone, Arcadia's HR system. Bridgeway, the vendor system, holds every contractor's order. At 00:00 GMT on the 1st, the close run reads both and compares them, contractor by contractor.
>
> **Gaps.** A gap is one difference for one contractor: Keystone shows one thing, Bridgeway another. Nine flags say what differs, five risks say what it puts at risk in the report, and three places say where it is aligned: Bridgeway (Vendor Management), Keystone (HR Operations) or the system feed between them (Data Engineering). The words say what differs, not which system is wrong.
>
> **Gap rate.** Contractors with at least one gap, divided by contractors working in Bridgeway. A change still in the feed that will land by the next run is left out. The 3% target is provisional: it flags risk, it does not certify the report.
>
> **Tickets.** Open Helix tickets at the close, by the group working them now. A ticket links to a gap through the contractor's ID; a name alone is not enough when two contractors share it, so some tickets link to no gap and, without a contractor, to no group.
>
> **What a flag proves.** "Active in Keystone, not working in Bridgeway" means Keystone still shows the contractor active after Bridgeway ended them, not that they used any access.
>
> **Data.** Arcadia Systems, Keystone, Bridgeway and Helix are fictional. All data is synthetic.

Check on Tableau Public that the last line is not cut (Dashboard #1 needed 29 px more online).

---

## 12. Step 9: KPI band and hovers

### 12.1 Copy the geometry from Dashboard #2

🔴 **Still to add by hand: the `kpi_` calcs and the 16 `kpi_` parameters**, by copy and paste from Dashboard #2 as below (the generator left them out on purpose, so #2's calibrated values come with them).

The grid is Dashboard #2's (D3), so copy, do not rebuild: in the Compensation Walk workbook select the `kpi_` calcs (`kpi_lat Title/Value/Sub`, `kpi_lon C1`–`C5`, `kpi_pt Title/Value/Note 1`–`5`, `kpi_Corner TL/BR`) in the Data pane, Ctrl+C; in this workbook select **CW Reconciliation**, Ctrl+V. Tableau brings the 16 `kpi_` parameters with #2's calibrated values (GridLeft 246, CardW 212, GapX 16). Then set **`kpi_PadX` 16** (left-aligned text, D11) if #2's is centred (106).

| Layer | Point | Label | Font, colour | Alignment |
|---|---|---|---|---|
| Title 1–5 | `kpi_pt Title n` | `KPI n Title` | Tableau Book 9 slate `#5A6170` | Left, Middle |
| Value 1–5 | `kpi_pt Value n` | `<KPI n Value>  <KPI n Unit>` (card 2: `<KPI 2 Value>  <KPI 2 Known><KPI 2 Low>`) | value Tableau Bold 20 navy `#13233A` (card 4 coral `#712B13`); unit Tableau Book 10 slate; Known risk Semibold 9 coral `#B8401F`, Low risk Semibold 9 teal `#0E7D5F` | Left, Middle |
| Note 1–5 | `kpi_pt Note n` | `KPI n Note` | Tableau Book 9 slate `#5A6170` | Left, Middle |

Build exactly as G3 10.2 steps 1 to 6 (corner layers, 15 text layers, circle at 0% opacity, map options off), with `Pop Now` doing what `Row Is Current` did there: no filter is needed because every K calc already tests `Pop Now`; put **`Is Selected Close` = True** on Filters to keep the sheet small. Dashboard: `KPI Cards` floating at x 0, y 76, 1400 × 110, behind the rail (8.5).

### 12.2 Expected

| | Card 1 | Card 2 | Card 3 | Card 4 | Card 5 |
|---|---|---|---|---|---|
| Current | 11,941 contractors · Keystone shows 11,875 · net +66 | 3.21% Known risk · 383 with a gap · May 3.41% | Still open from the May close: 342 of 407 gaps · 84% open since the May close | 177 · 43% of the gaps | 277 of 407 gaps · Oldest gap 3,235 days |
| May 2026 | 11,489 · 11,430 · +59 | 3.41% Known · 392 · Apr 3.51% | April: 358 of 417 · 86% | 192 · 46% | 287 of 417 · 3,205 |
| Jun 2025 | 10,707 · 10,644 · +63 | 3.05% Known · 327 · May 3.16% | May: 286 of 346 · 83% | 152 · 44% | 225 of 346 · 2,870 |
| Dec 2024 | 10,011 · 9,954 · +57 | 3.66% Known · 366 · Nov 3.53% | November: 324 of 386 · 84% | 199 · 52% | 253 of 386 · 2,689 |
| Jun 2021 (first) | 8,564 · 8,532 · +32 | 2.94% Low risk · 252 · first close in the data | prior close: N/A · No prior close in the data | 170 · 64% | 166 of 264 · 2,191 |
| Current, Technology | 7,660 · 7,608 · +52 | 3.20% Known · 245 · May 3.33% | 218 of 263 · 83% | 113 · 43% | 174 of 263 · 2,921 |
| Current, India | 4,883 · 4,861 · +22 | 3.36% Known · 164 | 148 of 173 · 86% | 75 · 43% | 120 of 173 · 2,556 |

### 12.3 Calibrate

As G3 10.2 "Calibrate", against Dashboard #2's grid: card 1's text starts 16 px inside x 246; title 17 px, value 44 px, note 71 px below y 88. #2's `kpi_FitX` and `kpi_ShiftX` should already be right; nudge only if the text drifts.

### 12.4 Hover covers

Five transparent sheets `KPI Hover 1`–`5` (G3 10.4): 🟢 `Hover Cell` = `"."` on Columns and Rows, headers hidden, Square at 0% opacity, size far right; filter `Is Selected Close` True and `Rail One` True (one mark); tooltip `<KPI n Title>` Semibold 10 navy / `<KPI n Tip>` Book 9 `#4A5A73`; Responsive; command buttons off. Floating at x 246, 474, 702, 930, 1158; y 88; 212 × 86; corner radius 5; above `KPI Cards`, behind the rail and popovers.

Expected (Current): card 1 "79 working in Bridgeway but not active in Keystone, 13 the other way. Contractors, not gaps." Card 2 "… 0.21 pts above a provisional 3% target. The target flags risk; it does not certify the report."

---

## 13. Step 10: gap list and the Overview · Gap list toggle

### 13.1 Calcs

```
// 🟢 Gap List Row        [Gap Now]
// 🟢 Aligned In          [place] + CHAR(10) + STR([Place Gaps]) + " gaps"      (name the calc exactly: WHERE ALIGNED)
// 🟢 Flag                [flag_name]                                            (name: WHAT DIFFERS)
// 🟢 Contractor          [contractor_name] + " · " + [bw_worker_id]            (name: CONTRACTOR)
// 🟢 Keystone Shows      [keystone_shows]                                       (name: KEYSTONE SHOWS)
// 🟢 Bridgeway Has       [bridgeway_has]                                        (name: BRIDGEWAY HAS)
// 🟢 Ticket              IFNULL([ticket_number], "No ticket")                  (name: TICKET)
// 🟢 Days Band           IF [days_open] > 90 THEN "over 90" ELSE "90 or less" END
// 🟢 Gap List Title      IF ZN([Total Gaps]) = 0 THEN "No gaps in this selection"
//                     ELSE [Total Gaps Str] + " gaps at the " + [Close Month] + " close, by where they are aligned" END
// 🟢 Gap List Subtitle   "Oldest first. Hover a row for the evidence, the next step and the ticket. Click a node in the Overview to narrow the list."
```

🟢 Created under their header names: `WHERE ALIGNED`, `WHAT DIFFERS`, `CONTRACTOR`, `KEYSTONE SHOWS`, `BRIDGEWAY HAS`, `TICKET`, and `DAYS OPEN` (13.2).

If the line break in `WHERE ALIGNED` does not show in a header, use `[place]` alone and put the count in the Gap List Title.

### 13.2 Sheet `Gap List`

- Filter `Gap List Row` = True.
- Rows, in order: `place_order` (discrete, header hidden), `WHERE ALIGNED`, `gap_id` (header hidden; sort by Field `days_open`, Maximum, Descending), `WHAT DIFFERS`, `CONTRACTOR`, `KEYSTONE SHOWS`, `BRIDGEWAY HAS`, `TICKET`.
- Marks Text: `SUM(days_open)` formatted `#,##0`, header "DAYS OPEN" (the measure's name on the column: rename via an alias calc `DAYS OPEN` = `[days_open]`); Color `Days Band`: over 90 coral `#B8401F`, 90 or less navy `#13233A`.
- Detail: `What differs`, `What it puts at risk`, `Where it is aligned` (the Sankey's filter action targets them), `zzTrue`, `zzFalse`.
- Header widths: WHERE ALIGNED 80, WHAT DIFFERS 160, CONTRACTOR 110, KEYSTONE SHOWS 130, BRIDGEWAY HAS 130, TICKET 70, DAYS OPEN 46 (total 726). Format > Alignment: wrap on; row height about 30 (two lines). Headers Tableau Book 9 `#2B2F36`; field labels Tableau Semibold 8 `#6B7079`; row dividers `#E4E3DD` thin; Worksheet shading None.
- Tooltip (command buttons off): `<contractor_name>` Semibold 10 navy / `<bw_worker_id> · <person_id> · <supplier_name>` / `<flag_name>` · puts at risk `<risk>` / Keystone shows: `<keystone_shows>` / Bridgeway has: `<bridgeway_has>` / Evidence: `<evidence>` / Open since `<since_date>` (`<days_open>` days) / Next step: `<next_step>` (gray italic) / Ticket: `<ticket_number>` `<ticket_title>` · `<ticket_status>`.
- Expected, Current: 407 rows; Bridgeway 194 (oldest 2,921 days, flag One person, two IDs), Keystone 151 (oldest 3,235), System feed 62 (oldest 2,831); 230 show an open ticket, 6 a ticket closed while the gap is still open, 171 read "No ticket" (KPI 4's 177 = 171 + 6).

### 13.3 The swap (dynamic zone visibility)

```
// 🟢 Show Overview       NOT [p_ShowList]
```

In `Card: Main`, add `Gap List Title` (726 × 44) and `Gap List` (726 × 546, outer padding top 6) below the Sankey pair. Control visibility: `Main Title` and `Sankey` by **`Show Overview`**; `Gap List Title` and `Gap List` by **`p_ShowList`**. The hidden pair collapses, so the visible pair takes the tile.

### 13.4 The Sankey click (S2 and S2b)

- **Filter action** `Sankey filters the gap list` (S2, passed): source `Sankey`, target `Gap List`, Run on Select, Selected Fields `What differs`, `What it puts at risk`, `Where it is aligned` (each to the same field), Clearing: **Show all values**.
- **S2b, test now:** Dashboard > Actions > Add Action > Change Parameter: source `Sankey`. If Tableau lists the Sankey as a source, set target `p_ShowList`, field 🟢 `Show List On Click` = `TRUE` (a calc), Run on Select: a click on a node then opens the gap list already filtered. If the Sankey is not offered as a source for parameter actions, keep the filter only: the list is filtered when the reader switches to it, and the Gap List Subtitle says so. Record which.

---

## 14. Step 11: timeline card

### 14.1 Calcs

```
// 🟢 Timeline Row        [Is Pop] AND [In Scope] AND DATEDIFF('month', [month_end_date], [p_Close]) >= 0
//                     AND DATEDIFF('month', [month_end_date], [p_Close]) <= 12
// 🟢 TL Rate             IF SUM([contractors_working]) = 0 THEN NULL ELSE SUM([contractors_with_gap]) / SUM([contractors_working]) END
// 🟢 TL Is Selected      MIN([month_end_date]) = [p_Close]          (aggregate, for Color and Size)
// 🟢 TL Label            IF [TL Is Selected] THEN [TL Rate Str] END  (🟢 TL Rate Str: the rate pattern of 7.4 on TL Rate)
// 🟢 TL Target           MIN([gap_rate_target])
// 🟢 Timeline Subtitle   "Contractors with a gap divided by contractors working in Bridgeway · last 13 closes" + [Scope Text]
```

### 14.2 Sheet `Timeline` (318 × 202)

- Filter `Timeline Row` = True.
- Columns `month_end_date` continuous, **Exact Date**; axis ticks every 3 months, format `mmm yy`, Book 8 `#6B7079`; no axis title.
- Rows `TL Rate`, then `TL Rate` again; Dual Axis, Synchronize. First: Line, navy `#13233A`, size 2. Second: Circle, Color `TL Is Selected` (True `#B8401F` when above target, else `#0E7D5F`: use the calc 🟢 `TL Dot` = `IF [TL Is Selected] THEN (IF [TL Rate] > [TL Target] THEN "selected above" ELSE "selected below" END) ELSE "other" END`; other white with a navy border), Size `TL Is Selected` (True large, False small), Label `TL Label` Semibold 10 in its colour.
- Y axis: Percentage, 1 decimal; not including zero; hide the second axis.
- Reference line on the first axis: Per Table, value `TL Target` (put it on Detail first), line dashed `#8C8A84`, label "Target 3%" (Custom: `Target <Value>`), Book 8.
- Grid lines `#E4E3DD`, zero line none; Worksheet shading None; tooltip: `<Close of the point>` "close: " `<TL Rate>` · `<SUM(contractors_with_gap)>` of `<SUM(contractors_working)>` contractors; command buttons off.
- `Timeline Title` (318 × 56): Text, line 1 "Gap rate at each month-end close" Semibold 12 navy, line 2 `Timeline Subtitle` Book 9 slate, wrap.

Expected, Current: Jun 25 3.05% · Jul 3.85% · Aug 3.79% · Sep 3.87% · Oct 3.89% · Nov 3.77% · Dec 3.81% · Jan 26 3.80% · Feb 3.65% · Mar 3.56% · Apr 3.51% · May 3.41% · **Jun 26 3.21%** (coral, labelled). Dec 2024: Dec 23 3.56% · Jan 24 3.57% · Feb 3.46% · Mar 3.35% · Apr 3.43% · May 3.28% · Jun 3.07% · Jul 3.88% · Aug 3.68% · Sep 3.77% · Oct 3.70% · Nov 3.53% · **Dec 24 3.66%**. Before Jun 2022 the line starts at Jun 2021 (fewer than 13 points). A13: the selected point equals KPI 2.

---

## 15. Step 12: ticket card

### 15.1 Calcs

```
// 🟢 Ticket Card Row     [Ticket Now]
// 🟢 Ticket Row Y        3.5 - [place_order]                         (Bridgeway 2.5, Keystone 1.5, System feed 0.5)
// 🟢 Band X              [age_band_order] - 0.5                     (0.5, 1.5, 2.5)
// 🟢 Place Open          { FIXED [place] : SUM(IF [Ticket Card Row] THEN [tickets] END) }
// 🟢 Band Open           { FIXED [age_band] : SUM(IF [Ticket Card Row] THEN [tickets] END) }
// 🟢 Place Sub           CASE [place] WHEN "Bridgeway" THEN "vendor system" WHEN "Keystone" THEN "HR system" ELSE "integration" END
// 🟢 Tickets Subtitle    "One dot per Helix ticket open at the close" + [Scope Text]
```

### 15.2 Sheets (body 318 × 240: a horizontal container with two vertical stacks)

| Sheet | Tile | Build |
|---|---|---|
| (Blank) | 96 × 28 | top-left corner |
| `Ticket Rows` | 96 × 212 | Filter `Ticket Card Row`. Rows `Ticket Row Y` (MIN, continuous, axis fixed 0 to 3, hidden). Marks Shape square, size small, Color `place` (Bridgeway `#F89217`, Keystone `#7873C0`, System feed `#21B087`); Label right: `<place>` Semibold 10 `#2B2F36` / `<Place Sub>` Book 9 `#5A6170` / `<Place Open>` open Semibold 9. Detail `place`. Tooltip off |
| `Ticket Bands` | 222 × 28 | Filter `Ticket Card Row`. Columns `Band X` (MIN, continuous, fixed 0 to 3, hidden). Text `<age_band>` Semibold 9 `#6B7079` / `<Band Open>` open Book 9. Detail `age_band` |
| `Ticket Dots` | 222 × 212 | Filter `Ticket Card Row`. Columns `dot_x` (AVG, continuous, fixed 0 to 3, hidden); Rows `dot_y` (AVG, fixed 0 to 3, hidden). Detail `ticket_number`, `month_end_date`. Marks Circle, size about 2.5 px, Color `place` (same three), no border. Reference lines at 1 and 2 on both axes, solid `#E4E3DD`. Tooltip: `<ticket_number>` Semibold 10 navy / `<title>` / `<current_group>` · `<age_days>` days open · `<state>` / Linked by `<link_tier>`; command buttons off |

Container: `Ticket Body` horizontal 318 × 240 = [vertical 96: Blank 28, Ticket Rows 212] + [vertical 222: Ticket Bands 28, Ticket Dots 212]. `Tickets Title` 318 × 44 above it.

**Spike S5 here:** the fullest cell holds 141 dots (Bridgeway, over 30 days, some closes). Readable at 2.5 px, and the hover finds the dot under the pointer. Fallback: dots 2 px, or a count per cell with the dots in the tooltip.

Expected, Current: 361 dots; Bridgeway 149, Keystone 124, System feed 88; 0 to 5 days 4, 6 to 30 days 54, over 30 days 303. Dec 2024: 294 (140 / 86 / 68; 9 / 30 / 255). With a group chosen, the dots keep their places (the grid is packed for the whole close), so a filtered cell is sparser, not repacked.

---

## 16. Step 13: title, subtitle, load note, footnote, info

```
// 🟢 Page Subtitle       "Where Bridgeway and Keystone " + (IF [Is Current] THEN "disagree" ELSE "disagreed" END)
//                     + " at the " + [Close Name] + " close, and where each gap is aligned" + [Scope Text]
// 🟢 Load Note           MIN(IF [Is Pop] AND [Is Selected Close] THEN [load_note] END)
// 🟢 Show Load Note      { FIXED : MAX(IF [Is Pop] AND [Is Selected Close] AND CONTAINS([load_note], "failed") THEN 1 ELSE 0 END) } = 1
```

- `Page Title` (246, 14, 760 × 60): Text, line 1 `Contingent Workforce Reconciliation` Tableau Bold 18 navy, line 2 `<Page Subtitle>` Tableau Book 10 slate. Tooltip off; deselect. Replaces the placeholder.
- `Load Note` sheet in a floating container at 1050, 30, 320 × 28: container background `#FAEEDA`, corner radius 14, **visibility `Show Load Note`**; text `<Load Note>` Tableau Semibold 9 `#633806`, Center. Expected: Dec 2024 "Keystone load failed: the close used Keystone as of Dec 28"; Sep 2023 the Bridgeway one; Mar 2026 the Helix one; hidden otherwise (late loads say the data is complete, so they stay off).
- Footnote: as placed in step 5 (final).
- Info text: section 11.4.

---

## 17. Step 14: actions

Parameter actions: Run on **Select**, Aggregation None, clearing **Keep current value**. Names exactly as below (one name per action makes the audit easy).

| # | Name | Source | Target | Field |
|---:|---|---|---|---|
| 1 | Open close popover | Close Field | `p_CloseOpen` | `Toggle Close Panel` |
| 2–5 | Close opens: function / department / country / info close | Close Field | `p_FunctionOpen`, `p_DepartmentOpen`, `p_CountryOpen`, `p_InfoOpen` | `Close Panel` |
| 6 | Set close | Close Grid | `p_Close` | `Close Pick` |
| 7 | Close popover on pick | Close Grid | `p_CloseOpen` | `Close Panel` |
| 8 | Close popover on ✕ | Close Close | `p_CloseOpen` | `Close Panel` |
| 9 | Open function popover | Function Field | `p_FunctionOpen` | `Toggle Function Panel` |
| 10–13 | Function opens: close / department / country / info close | Function Field | the four others | `Close Panel` |
| 14 | Toggle function | Function List | `p_Functions` | `Function Toggle` |
| 15 | Clear functions | Function Clear | `p_Functions` | `Empty Text` |
| 16 | Function popover on ✕ | Function Close | `p_FunctionOpen` | `Close Panel` |
| 17–24 | Department: open, four closes, toggle, clear, ✕ | Department Field / List / Clear / Close | as 9–16 | |
| 25–32 | Country: open, four closes, toggle, clear, ✕ | Country Field / List / Clear / Close | as 9–16 | |
| 33 | Set view | Show Toggle | `p_ShowList` | `Show Pick` |
| 34 | Show closes popovers | Show Toggle | the five open flags (five actions: 34a–e) | `Close Panel` |
| 35 | Reset close | Reset | `p_Close` | `Default Close` |
| 36–38 | Reset groups | Reset | `p_Functions`, `p_Departments`, `p_Countries` | `Empty Text` |
| 39 | Reset view | Reset | `p_ShowList` | `zzFalse` |
| 40 | Reset closes popovers | Reset | the five open flags (40a–e) | `Close Panel` |
| 41 | Open info | Info Button | `p_InfoOpen` | `Toggle Info` |
| 42 | Info opens, others close | Info Button | the four others (42a–d) | `Close Panel` |
| 43 | Sankey opens the gap list (S2b, if allowed) | Sankey | `p_ShowList` | `Show List On Click` |

Filter action: **Sankey filters the gap list** (13.4). Deselect (Filter, the sheet to itself, `zzTrue` to `zzFalse`, Show all values) on: `Page Title`, `Main Title`, `Gap List Title`, `Timeline Title`, `Tickets Title`, `Rail As Of`, `Close Field`, `Function Field`, `Department Field`, `Country Field`, `Show Toggle`, `Reset`, `Info Button`, `Close Grid`, `Close Close`, `Function List`, `Function Clear`, `Function Close` (and the Department and Country three), `KPI Cards`, `KPI Hover 1`–`5`, `Gap List`. Not on `Sankey`, `Timeline`, `Ticket Dots` (a highlight there is useful).

---

## 18. Step 15: checks and click tests

### 18.1 Check tables

Release plan section 7 (KPIs, Sankey places, risks and flags, the ticket card and the timeline at Current, May 2026, Jun 2025, Dec 2024), plus 12.2 here (KPIs with a group) and these Sankey totals with a group, Current:

| Selection | Gaps | Places B / K / S | Risks (A, B, C, P, S) | Flags 01–09 | Tickets B / K / S |
|---|---:|---|---|---|---|
| Technology | 263 | 125 / 93 / 45 | 58, 73, 44, 43, 45 | 10, 31, 17, 73, 44, 31, 12, 40, 5 | 72 / 55 / 41 |
| India | 173 | 91 / 63 / 19 | 30, 51, 34, 35, 23 | 6, 17, 7, 51, 34, 24, 11, 19, 4 | 49 / 40 / 17 |
| Commercial + Technology | 280 | 134 / 100 / 46 | 62, 77, 49, 45, 47 | 10, 34, 18, 77, 49, 33, 12, 40, 7 | 77 / 59 / 42 |
| Technology and India | 120 | 63 / 43 / 14 | 16, 40, 22, 24, 18 | 1, 12, 3, 40, 22, 17, 7, 16, 2 | 32 / 25 / 13 |

### 18.2 Ties on every state

Flags = risks = places = gap list rows (A2). KPI 2 = timeline's selected point (A13). Tickets by place add up to the card (A5). KPI 4 + linked = KPI gaps (A3).

### 18.3 Click tests (Presentation mode, then on Tableau Public)

| # | Do | Expect |
|---:|---|---|
| 1 | Hover every KPI card | Its tooltip; numbers equal the card |
| 2 | Click every control, title, KPI and the list rows | Nothing stays highlighted |
| 3 | Open each popover in turn | One open at a time; each hangs from the rail edge level with its heading |
| 4 | Point in time > 2024 > Dec | Popover closes; capsule "Dec 2024 close"; load note shows; system feed 58 with 6 failed loads in its tooltip; KPIs as 12.2 |
| 5 | Function > Technology, then Commercial | Capsule "Technology", then "2 selected"; every card follows; Sankey order still Bridgeway, Keystone, System feed |
| 6 | Department with Technology chosen | Non-Technology departments dim but clickable |
| 7 | Function > Marketing only | Sankey order kept (S7); tooltips show no ranks (D10) |
| 8 | Click a Sankey node, then Gap list | List filtered to that node; clearing the selection shows all |
| 9 | Hover a ticket dot | Ticket number and title |
| 10 | Reset | Current, all groups, Overview, popovers closed |

---

## 19. Step 16: publish

1. Reset; close popovers; hide every sheet; remove any parameter control shown for testing; delete stray legends; `CHK Rows` hidden.
2. I review the saved `.twb` before publishing (parameters, actions by name, no calc pointing at a missing field, extract on, no glyph or "wrong" in viewer text, command buttons off).
3. **Spike S6:** Save to Tableau Public As `arcadia_cw_reconciliation`; the page loads in under 5 seconds. Fallback: extract filter keeping the last 25 months of Gap rows.
4. Click tests on the web; the Info text not cut.
5. Repo: screenshot `docs/images/cw_reconciliation_dashboard.png`, README (case study 4: Tableau link and screenshot), the profile row, the release plan's tracker (phases 11 and 12), project docs, session handoff.

---

## 20. Shapes and images to make (Claude, before step 7)

Palette **Arcadia D4** (`docs/brand/shapes/by_dashboard/d4/`), drawn at 3x like Dashboard #2's:

| File | Size on the page | What |
|---|---|---|
| `d4_field_capsule` | 200 × 32 | White capsule, navy chevron 18 px from the right (Point in time) |
| `d4_field_capsule_dark` | 200 × 32 | `#1B2D45` capsule, `#4A5B73` outline, light chevron (Function, Department, Country) |
| `d4_show_overview_on/off`, `d4_show_gaplist_on/off` | 100 × 32 each | White pill with navy text when on; `#B9C3D1` text on the navy capsule when off |
| `d4_reset` | 200 × 32 | Outlined capsule, "Reset to default view" |
| `d4_tick_on`, `d4_tick_off`, `d4_tick_dim` | 12 × 12 | Filled teal `#5DCAA5` square with a white tick; outlined `#B8C0CC`; outlined `#56657E` |

Reused: `d2_info_open`, `d2_info_close`, `d2_popover_line_wide`, `d2_popover_line_info`, `shared_close_light`, `arcadia_rail_divider.png`, `arcadia_logo_horizontal_reverse.png`, `arcadia_kpi_cards_bg_summary.png`.
