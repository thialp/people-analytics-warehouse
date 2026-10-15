# Release 3 rebuild: Dashboard #2, Compensation Walk

Step-by-step update of [ArcadiaCompensationWalk](https://public.tableau.com/app/profile/thialp/viz/ArcadiaCompensationWalk/Summary) on the release 3 data. Dashboard #2 is the reference design: it keeps its **side rail** exactly as it is, and the work here is the release 3 data, the details you captured, and the pieces that make it tie to Dashboard #1 number for number. Arcadia Systems is fictional and all data is synthetic.

Companion guide: [Dashboard #1 rebuild](../headcount-fte-walk/release_3_rebuild_dashboard_1.md). Section 0 is identical in both; you can import sheets, calcs and parameters from one workbook to the other wherever a step says so.

| Your note (Snagit) | Where it is fixed |
|---|---|
| "Calling drivers": Expand · 13 steps, "Largest of the 13 steps" | Section 4 |
| "Remove the dot" in the Group field | Sections 0.4 and 5.1 |
| "Remove highlighted" (Total payroll) | Sections 0.4 and 5.4 |
| "Keep that in all dashboards" (period popover) | Kept here; copied into #1 (its section 7.1) |
| "Same as dashboard #2" (info text box) | Section 6 here, #1 section 8.4, shared paragraphs in 0.5 |
| "Same numbers as #2" / "Align with dashboard #1" (Hires 1,058 people) | Section 7 and the explanation in 0.1 |
| "Numbers must match" (People card vs Growth by Region) | Section 3 |
| "Not selectable" (map title) | Section 5.4 |
| Info button tooltip | Section 6 |
| Details I caught | Section 8 |

## 0. Shared rules for both dashboards (identical in the #2 guide)

### 0.1 What must match, and what cannot

Checked in DuckDB on the release 3 warehouse: for **all 88 periods × every group of the five shared views (6,222 combinations)**, Dashboard #1's opening and closing equal Dashboard #2's to the person, once both exclude the executive officers and both use the same two month-end dates. Region Walk hires, exits and transfers equal Dashboard #2's walk lines in all 9,126 period × group combinations.

| Number | Dashboard #1 | Dashboard #2 | Rule |
|---|---|---|---|
| Opening, closing, net change, % change | KPI card 1, waterfall levels | People card, Growth by Region headline | **Identical** |
| Joined in the period | KPI card 2 (5,235 = 4,965 hires + 270 conversions) | Tie-out note under the waterfall | **Identical** (same sentence in both) |
| Hires still here at the end | Tie-out note under the waterfall | Hires driver (4,790), Top drivers | **Identical** (same sentence in both) |
| Leavers | Every leaver (3,668) | Exits from the opening team (3,223) | Different by definition, explained in both info panels |

**Why the hire counts differ, and why both are right.** Dashboard #1 counts **events** month by month: everyone who joined. Dashboard #2 compares **two snapshots**: pay can only be priced for someone present on a date, so a person hired in October who left in March is in neither snapshot. FY26, Company: 5,235 joined, 445 of them left again before Jun 30, 2026, so 4,790 were still here. The same 445 explain the leavers: 3,668 − 445 = 3,223 exits. For a group (a function, a country) the gap also includes people who joined and then changed team. Neither dashboard is changed to the other's definition: turnover needs every leaver, and a pay walk can only price people it can see. Instead **both show both numbers in one identical sentence** (Dashboard #1 guide section 9, Dashboard #2 guide section 7), so a reader never sees two unexplained hire counts.

### 0.2 Population

| Rule | Dashboard #1 | Dashboard #2 |
|---|---|---|
| Executive officers (CEO + 8 function heads, all in department `D-901` Office of the CEO) | **Excluded** (new: `Department Id <> "D-901"` inside `In Range`) | Excluded (in the SQL) |
| Worker type | Employees by default; Contingent and Total on the toggle | Employees only. When #1 shows Contingent or Total, the tie-out note says the Compensation Walk covers employees |
| Office view | Not offered (the headcount walk is by department × country, not office) | Offered |

### 0.3 One vocabulary

| Concept | Word on both dashboards | Not |
|---|---|---|
| The bars between Opening and Closing | **drivers** ("Expand · 4 drivers", "Largest of the 9 drivers behind the waterfall") | steps |
| The compact bars | **groups** ("Collapse · 2 groups") | |
| Two month-ends compared | **period** ("FY26 · Jun 25 → Jun 26") | range, window |
| People who arrived | **joined** (hires + conversions); expanded: Hires, Conversions | |
| People who left | **left**; expanded: Voluntary leavers, Involuntary leavers | terminations |
| Fictional-company line | "Arcadia Systems is a fictional company. All data is synthetic." | |

### 0.4 Buttons: images on worksheets, never a selectable text mark

Tableau runs a **parameter action only from a mark on a worksheet**. A dashboard Image object can open a URL and a Show/Hide button can toggle one container, but neither can set a parameter. So "image buttons" here means: **a worksheet whose single mark is a custom Shape that draws the button image**, with the action on that sheet. That fixes all three things you flagged:

| You saw | Cause | Fix used everywhere |
|---|---|---|
| Small square after "Commercial ▾" | The field is a **Text** mark. A text mark has no body, so Tableau draws its hover/selection indicator as a small square at the mark's anchor | Field = **Shape** mark drawing `fld_top.png` (#1) or `fld_rail.png` (#2), full size; the text is the mark's **label** laid on top. The hover indicator becomes the field's own outline |
| "Total payroll" shown highlighted after a click | The clicked mark stays **selected** (and the others fade) when the sheet has no deselect action, or the action points at the dashboard instead of the worksheet | Every clickable sheet has `zzTrue` and `zzFalse` on Detail and a **Filter action from the sheet to the same worksheet** (`zzTrue` → `zzFalse`, Clearing: Show all values) |
| A title could be selected | Titles drawn as **text sheets** have marks, so a click selects them | Same deselect action on **every** text sheet (titles, subtitles, captions, headings, KPI band); tooltips off |

Click flow after the fix: the click fires the parameter action, then the self filter action clears the selection in the same instant. On Tableau Public a brief flash can remain; nothing stays highlighted.

**Shape files (new, in the repo):** `docs/brand/build/make_button_shapes.py` writes these to `docs/brand/shapes/Arcadia/` (preview: `docs/brand/build/button_preview.png`). Install once: copy the PNGs into `Documents/My Tableau Repository/Shapes/Arcadia`, then on any sheet Marks > Shape > **Edit Shape... > Reload Shapes**. Assign shapes by hand (Assign Palette goes alphabetically, not by name).

| File | Size on the dashboard | Used for |
|---|---|---|
| `fld_top.png` | 180 × 32 | #1 Period and Group fields (white, square: inputs stay square) |
| `fld_rail.png` | 200 × 30 | #2 Period and Group fields (`#E4E3DD`, rounded like the toggles) |
| `seg_worker_employees_on/off`, `seg_worker_contingent_on/off`, `seg_worker_total_on/off` | 80 × 32 each | #1 Workforce toggle (capsule `#243A57`) |
| `btn_reset_top.png` | 32 × 32 | #1 Reset (white arrow on navy) |
| `btn_reset_rail.png` | 188 × 30 | #2 Reset (outlined button, as published) |
| `btn_close.png` / `btn_close_light.png` | 16 × 16 | The ✕ on every popover (slate on white / mist on navy) |
| `info_open`, `info_close` (existing) | 32 × 32 | #1 info button |
| `rail_info_open`, `rail_info_close` (existing) | 16 × 16 | #2 info button |
| `btn_expand_icon`, `btn_collapse_icon` (existing) | 16 × 16 | Expand / Collapse on both |

**Test the field pattern first** (Dashboard #1: section 6.1; Dashboard #2: section 5.1) before converting the others. If the label will not sit on the shape at full size, the fallback is the published pattern (Text mark, sheet shading as the box) plus the deselect action, which removes the selection highlight but not the hover square.

### 0.5 Popovers and the info panel: one style

| Item | Setting |
|---|---|
| Popover container | Floating vertical container, background navy `#13233A`, corner radius 10, inner padding 16, border none, **Control visibility using value** = its Boolean parameter, Bring to front |
| Title | Tableau Bold 12, white |
| Note under the title | Tableau Book 9, `#8FA0B8` |
| Body | Tableau Book 10, `#B8C0CC`; lead-in terms Tableau Semibold 10, white |
| Close | `Popover Close` sheet with `btn_close_light`, 16 × 16, top right |
| Open rule | Only one popover open at a time: each opener sets the others' parameters to `Close Panel` (= FALSE) |
| Info button tooltip | #1: "Click here for more information on how to read this page" · #2: "Click here for more information on how pay is measured" (sheet tooltip, Tableau Book 9) |

**Info panel text.** The first two and last paragraphs are word for word the same on both dashboards; the middle is each dashboard's own (full texts: Dashboard #1 guide section 8.4, Dashboard #2 guide section 6).

> **Period.** Every number compares two month-ends: the walk opens on the first and closes on the second. Arcadia's fiscal year runs July to June.
>
> **Who is counted.** Employees active at month-end. The CEO and the eight function heads are left out on both Arcadia dashboards, so both count the same people.
>
> *(dashboard-specific paragraphs)*
>
> **Data.** Arcadia Systems is a fictional company. All data is synthetic.

### 0.6 Small rules that apply everywhere

- **No negative zero.** Round before testing the sign: `IF ROUND([x], 3) = 0 THEN 0 ELSE [x] END` in every percent text calc, so "−0.0%" never shows.
- **Headlines are statements** with the number in them ("Average pay per FTE rose $3,601 (+3.3%)", "FY26: 4,965 hires outpaced 3,668 leavers, adding 1,567 people").
- **Period text** is `Pair Name` on both: "FY26 · Jun 25 → Jun 26".
- **Every control drives every sheet** (Period, View/Group and the Workforce toggle on #1; the rail on #2).

---

## 1. Before Tableau (Mac)

```bash
cd ~/GitHub/people-analytics-warehouse
git pull
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker compose up -d
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/06_validate_compensation_walk.sql
```

Expected: the walk returns **108,918** rows and every check **PASS** (release 3 values; full expected output for `06`, `07`, `09` in `docs/projects/contingent-workforce/sql_server_release_3_run.md`). If the file name differs on your Mac, `ls sqlserver/0*validate*` lists them.

Then:

1. Copy `tableau/custom_sql_compensation_walk.sql`, `custom_sql_office_moves.sql`, `custom_sql_region_walk.sql` and `custom_sql_headcount_fte_walk.sql` into `~/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/04 Compensation Walk/`.
2. Copy the 12 new PNGs from `arcadia_button_shapes.zip` (sent with this guide) into `~/Documents/My Tableau Repository/Shapes/Arcadia/`. Once they are in the repo, `python3 docs/brand/build/make_button_shapes.py` regenerates them (expected `wrote 12 files`).
3. Open the workbook, **File > Save As** `ArcadiaCompensationWalk_release1_backup`, close, reopen the original.

---

## 2. Data sources

### 2.1 Walk and Office Moves: edit in place

For each of the two sources: Data Source tab > right-click the Custom SQL table > **Edit Custom SQL Query** > select all > paste the release 3 file > OK > Extract > **Refresh**.

| Source | File | Rows after refresh |
|---|---|---:|
| `ArcadiaHR` (the walk) | `custom_sql_compensation_walk.sql` | 108,918 |
| `Office Moves` | `custom_sql_office_moves.sql` | 89,611 |

Nothing turns red: release 3 removed no column. What changes:

1. **FTE Changes is gone** (every employee is 1.0 FTE). Calcs that name it (`TD Key`, `TD Why`, the `step` alias) keep working; the branch is never reached. Delete the branch in each when convenient.
2. **If the release 2 workbook steps were never done** (the published page still says "13 steps" and shows release 1 numbers, so they were not): do them now from [release_2_republish.md](../workforce-planning/release_2_republish.md) part A. In short: `Leader` → `Sub-function` in the `p_View` list, `Panel Title`, `Selected Group` and the view alias; `Relocation Adjustments` → `Same-Country Transfer Adjustments` in `TD Key` (name "Same-country move"), `TD Why` and the `step` alias.
3. Check in a scratch sheet: FY26, Company, `step` = Opening: SUM(`headcount`) **28,438**; Closing **30,005**.

### 2.2 Region Walk

If the workbook does not have it yet: Data > New Data Source > Microsoft SQL Server (same connection) > New Custom SQL > paste `custom_sql_region_walk.sql` > rename **Region Walk** > Extract (Hide All Unused Fields first). **26,520** rows. If it exists: Edit Custom SQL Query > paste > Refresh.

### 2.3 Headcount Walk (for the tie-out note only)

1. Data > New Data Source > Microsoft SQL Server (same connection) > New Custom SQL > paste `custom_sql_headcount_fte_walk.sql` > rename **Headcount Walk**.
2. Extract with **filters** (Extract Data dialog > Filters > Add), so it stays small:
   - `worker_type` = Employee
   - `movement_category` in Hires, Conversions
   - `month_end_date` ≥ 7/31/2022 (the first month after the earliest period opening)
   - Hide All Unused Fields after the calcs below exist (or skip it; the filtered extract is small).
3. Calcs on **Headcount Walk** (its fields carry the CSV captions, `Month End Date` and so on):

```
// Link              "Arcadia"
// HW Group Name     (the Compensation Walk's group_name in each view; Office has no match here)
CASE [p_View]
    WHEN "Company"      THEN "Arcadia Systems"
    WHEN "Function"     THEN [Function Name]
    WHEN "Sub-function" THEN [Sub Function]
    WHEN "Department"   THEN [Department Name]
    WHEN "Country"      THEN [Country Name]
END
// HW In Selection
[Month End Date] > [p_From] AND [Month End Date] <= [p_To]
AND [Department Id] <> "D-901" AND [HW Group Name] = [p_Group]
// HW Joined         (= Dashboard #1's "Joined": hires + conversions from contingent)
SUM(IF [HW In Selection] THEN [Headcount] END)
```

4. On **Region Walk**: calc `Link` = `"Arcadia"`.
5. **Data > Edit Blend Relationships...**: Primary **Region Walk**, Secondary **Headcount Walk**, **Custom**: remove every proposed pair, add only `Link` ↔ `Link`.

`p_Group` holds the group **name** (as built: `Group Is Current` = `[group_name] = [p_Group]`), so the CASE above matches it directly. Checked: names agree in every view (Function, Sub-function, Department, Country) between the two queries.

---

## 3. Growth by Region follows the selection ("Numbers must match")

**What was wrong.** With Commercial selected, the People card said 7,092 (from 6,943) and Growth by Region said "Arcadia overall +5.6% (28,436 | 30,015)". The sheet was built on the walk's Country rows, which have no region-by-group breakdown, and the guide said not to filter it by group. The Region Walk has the breakdown, and per group its regions add up exactly to the walk's opening and closing (test 57).

**Rebuild the region sheet on Region Walk.** In your workbook the sheet is called `Region Bars` (older notes call it `Region Headcount`; same sheet). It is on `ArcadiaHR`, and two of its pills are table calculations (the small triangle on `Growth Bar` and on the `Top group_parent` filter), which do not carry over to another source. So build a new sheet from scratch, copy only the look, and swap it in. Nothing on the new sheet is a table calculation, and it needs no Top-N filter (a group has at most five regions).

### 3.1 Calcs (data source Region Walk, one calc per name)

```
// RW Is Current        (Boolean; this is the only place the selection enters)
[from_month_end] = [p_From] AND [to_month_end] = [p_To] AND [view_name] = [p_View] AND [group_name] = [p_Group]

// RW Open
SUM(IF [RW Is Current] THEN [opening_headcount] END)
// RW Close
SUM(IF [RW Is Current] THEN [closing_headcount] END)
// Region Growth
IF [RW Open] = 0 THEN NULL ELSE ([RW Close] - [RW Open]) / [RW Open] END
// RW Net Change
[RW Close] - [RW Open]

// RW Group Open        (the whole selection, all regions)
{ FIXED : SUM(IF [RW Is Current] THEN [opening_headcount] END) }
// RW Group Close
{ FIXED : SUM(IF [RW Is Current] THEN [closing_headcount] END) }
// RW Group Growth
IF [RW Group Open] = 0 THEN 0 ELSE ([RW Group Close] - [RW Group Open]) / [RW Group Open] END
// RW Share of Growth
IF ATTR([RW Group Close]) = ATTR([RW Group Open]) THEN NULL
ELSE [RW Net Change] / (ATTR([RW Group Close]) - ATTR([RW Group Open])) END
// (ATTR is needed: a FIXED value is not an aggregate, and RW Net Change is a SUM; without it Tableau says "Cannot mix aggregate and non-aggregate arguments")

// RW Open Text   (copy as RW Close Text, using [RW Group Close])
IF [RW Group Open] >= 1000
THEN STR(INT([RW Group Open] / 1000)) + "," + RIGHT("00" + STR(INT([RW Group Open]) % 1000), 3)
ELSE STR(INT([RW Group Open])) END

// RW Subtitle    (title line 1 + line 2)
(IF [p_View] = "Company" THEN "Arcadia Systems" ELSE [p_Group] END)
+ " " + (IF [RW Group Growth] >= 0 THEN "+" ELSE "−" END)
+ STR(ROUND(ABS(100 * [RW Group Growth]), 1)) + "% (" + [RW Open Text] + " | " + [RW Close Text] + ")"
+ CHAR(10) + "Region: opening | closing headcount · bar: growth"
```

Check before building the sheet: drag `region` to Rows and `RW Open`, `RW Close` to Text. Company, FY26 reads Latin America 2,225 / 2,356 ... North America 9,909 / 10,426; **Analysis > Totals > Show Row Grand Totals** gives 28,438 and 30,005. If a total is different, stop here: the problem is the calc or a parameter, not the shelves.

### 3.2 Shelves (new sheet `Region Headcount RW`, data source Region Walk)

1. **Filters:** drag `RW Is Current` to Filters, tick **True**, OK. (This removes the other 87 periods and the other groups; a region the group does not reach simply has no row.)
2. **Rows:** `region`. **Columns:** `Region Growth`. Marks type **Bar**. Right-click `region` on Rows > **Sort** > Sort by **Field**, Descending, Field `Region Growth`, Aggregation Sum. Expected: five bars, Latin America first for Company.
3. **The name row.** Double-click the empty space right of `Region Growth` on Columns, type `AVG(0)`, Enter. Right-click `AGG(AVG(0))` on Columns > **Dual Axis**. Do **not** synchronize the axes. Right-click the `AGG(AVG(0))` axis > **Edit Axis** > Fixed, Start 0, End 1 (so the names stay at the left edge even when a region shrinks).
4. On the **All** tab, drag **Measure Names** from Color to **Rows**, right of `region`. Each region now has two rows. If the name row is below the bar: right-click **Measure Names** on Rows > Sort > Manual, `AGG(AVG(0))` first.
5. **`AGG(AVG(0))` tab:** type **Gantt Bar**, Size to zero, Color opacity 0%. Drag `region`, `RW Open` and `RW Close` onto **Label**; edit the label to `<region>   <SUM(RW Open)> | <SUM(RW Close)>` (name Tableau Semibold 9 navy, numbers Book 9 gray, number format `#,##0`); Alignment **Left**, **Middle**; tick *Allow labels to overlap other marks*.
6. **`Region Growth` tab:** Color amber `#D98E04`, Size about 40%. Label shows `Region Growth` only, format `+0.0%;−0.0%`, Alignment right of the bar end. Detail: `RW Open`, `RW Close`, `RW Net Change`, `RW Share of Growth`, `RW Subtitle`. Tooltip:

```
<region>
Opening headcount: <SUM(RW Open)>
Closing headcount: <SUM(RW Close)>
Net change: <SUM(RW Net Change)> people (<AGG(Region Growth)>)
<AGG(RW Share of Growth)> of the selection's net growth
```
7. Hide headers (right-click `region`, **Measure Names** and both axes > untick Show Header). Format > Lines: Row Divider, Grid Lines, Zero Lines **None**. Sheet background None. Fit **Entire View**.
8. **Title:** double-click the title area: line 1 `Growth by Region` (11 pt bold navy), line 2 `<AGG(RW Subtitle)>` (9 pt gray). Easiest: on `Region Bars`, **Worksheet > Copy > Formatting**, then on the new sheet **Worksheet > Paste > Formatting**, then fix the fields. That brings the fonts, lines and sizes across; the pills you build yourself.
9. Subtitle line 1 reads **Arcadia Systems +5.5% (28,438 | 30,005)** for Company and **Commercial +4.8% (7,441 | 7,795)** for Function > Commercial.
10. On the dashboard: select the `Region Bars` item > its menu > **Swap Sheets** > `Region Headcount RW`. Position and size stay. Delete the old sheet, rename the new one `Region Bars`. When the docs are updated, remove the "do not add `p_View` or `p_Group` filters" note from the map guide, section 4.

Check (FY26):

| Selection | Headline | Regions (opening \| closing, growth) |
|---|---|---|
| Company | Arcadia Systems +5.5% (28,438 \| 30,005) | Latin America 2,225 \| 2,356 +5.9%; Europe 6,665 \| 7,043 +5.7%; Asia Pacific 8,524 \| 9,005 +5.6%; Middle East & Africa 1,115 \| 1,175 +5.4%; North America 9,909 \| 10,426 +5.2% |
| Function Commercial | Commercial +4.8% (7,441 \| 7,795) | Asia Pacific 1,951 \| 2,071 +6.2%; Europe 1,854 \| 1,957 +5.6%; North America 2,461 \| 2,553 +3.7%; Latin America 755 \| 781 +3.4%; Middle East & Africa 420 \| 433 +3.1% |

The headline numbers must equal the People card (opening, closing) for every selection. They come from two different queries that are tested to agree.

---

## 4. "Drivers", not steps

Three texts and one rule.

```
// TD Step Count   (EDIT: count drivers, and skip a driver that is zero by construction in the current Cost/Currency)
{ FIXED : COUNTD(
    IF [In Pair] AND [step_group] <> "Balance"
       AND NOT ([step] = "FX Translation" AND [p_Currency] = "Constant")
       AND NOT ([step] = "Fringe Rate Changes" AND [p_Cost] = "Base")
    THEN [step] END) }
```
Why the two exclusions: in **Constant** currency every month uses one rate, so FX Translation is exactly $0 (the expanded chart shows a "+$0" bar today); in **Base** cost there is no fringe, so Fringe Rate Changes is exactly $0. Counting them overstates the drivers and draws empty bars.

```
// Expand Label    "Expand · " + STR([TD Step Count]) + " drivers"
// TD Subtitle     "Largest of the " + STR([TD Step Count]) + " drivers behind the waterfall"
// Collapse label  "Collapse · " + STR(groups) + " groups"   (unchanged: 4 groups)
```

**Hide the zero driver bars on the expanded waterfall:** calc `Driver Is Zero` = `([step] = "FX Translation" AND [p_Currency] = "Constant") OR ([step] = "Fringe Rate Changes" AND [p_Cost] = "Base")`; on the expanded waterfall sheet, Filters > `Driver Is Zero` = False. Do not put it on the compact sheet (the groups already sum to zero there).

Optional, same vocabulary as #1: rename the compact group "Hires & exits" to **"Joined & left"** (alias on the group field) and the Top drivers eyebrow `HIRES & EXITS` to `JOINED & LEFT`. In a group view this group also holds transfers in and out, which "Joined & left" describes better. Keep "Hires" and "Exits" as the expanded driver names.

Check (FY26, Avg per FTE):

| Selection | Expand label | Top drivers subtitle |
|---|---|---|
| Company, Loaded, Constant | Expand · 9 drivers | Largest of the 9 drivers behind the waterfall |
| Company, Loaded, Nominal | Expand · 10 drivers | … 10 drivers … |
| Company, Base, Constant | Expand · 8 drivers | … 8 drivers … |
| Function Commercial, Loaded, Constant | Expand · 11 drivers | … 11 drivers … |

---

## 5. Image buttons and no highlight

### 5.1 Period Field and Group Field (the dot)

For each of `Period Field` and `Group Field`:

1. Marks type: **Text** → **Shape**. Click the Shape card > **More Shapes...** > palette `Arcadia` > `fld_rail`. Nothing goes on Shape (one mark, one image).
2. Move the existing text field (`Period Field Text` / `Group Field Text`, which already end in `  ▾`) from Text to **Label**. Label: Tableau Semibold 10, navy `#13233A`, Alignment **Center**, Middle; check **Allow labels to overlap other marks**. (Left alignment places a shape's label to the left of the mark, outside the image, so Center is the safe choice.)
3. Size slider at maximum. Fit **Standard**. Format > Shading: Worksheet and Pane **None** (the image is the box now; the old `#E4E3DD` shading would show around it). Lines None.
4. Tooltips: Period `Choose the period`; Group `Choose a group`. Tableau Book 9, no command buttons.
5. Dashboard item: background None (was `#E4E3DD`), padding 0, 200 × 30 as now.

Test: hover shows an outline around the field, no square; click opens the popover; the field never shows highlighted text. If the label will not sit on the image, keep the Text mark and the shading (as published) and confirm the deselect actions in 5.4: that clears the highlight; tell me what the hover still shows.

### 5.2 Reset and the popover ✕

- `Reset`: marks **Shape** = `btn_reset_rail` (the image has the arrow and "Reset to default view"); remove the text from Label; size max; tooltip `Reset to default view`. Item 188 × 30, centered in the rail as now.
- `Panel Close` and `Period Close`: marks **Shape** = `btn_close_light` (the popovers are navy), size max, tooltip `Close`. 16 × 16.

### 5.3 The three toggles

`Lens Toggle`, `Cost Toggle`, `Currency Toggle` are already image segments. The highlight you saw on "Total payroll" is the **selection** staying on the clicked mark. Check each has its deselect action (5.4) targeting the **worksheet**, not the `Summary (...)` entry, and that `zzTrue` and `zzFalse` are on its Detail.

### 5.4 Deselect audit (every clickable sheet and every text sheet)

Dashboard > Actions. For each sheet below there must be one **Filter** action: Source = the sheet, Run on **Select**, Target = **the same worksheet**, Clearing **Show all values**, Selected fields `zzTrue` → `zzFalse`. Add `zzTrue` and `zzFalse` to the sheet's Detail first, and turn its tooltip off unless the table gives one.

| Sheet | Kind | Tooltip |
|---|---|---|
| Period Field, Group Field | Field | 5.1 |
| Rail View | List | off |
| Span List, Period Panel, Group Panel | Popover lists | off |
| Panel Close, Period Close | ✕ | Close |
| Lens Toggle, Cost Toggle, Currency Toggle | Toggles | off |
| Reset | Button | Reset to default view |
| Info Button | Button | section 6 |
| Btn Expand (text and icon), Btn Collapse (text and icon) | Buttons | off |
| Group Heading, Group Heading 2, page title / subtitle sheet | Titles | off |
| **Map headline sheet** ("725 people changed office…") and its subtitle | Titles ("Not selectable") | off |
| Top Corridors title, Region Headcount title (if they are separate sheets) | Titles | off |
| KPI cards | Cards | off |
| Tie-out caption (section 7.3) | Caption | off |

Charts (waterfalls, map, routes, regions, Top Drivers) keep normal selection.

---

## 6. Info button and info popover

1. `Info Button` sheet: tooltip text **Click here for more information on how pay is measured** (Tableau Book 9). Uncheck Include command buttons. That is the only change to the button.
2. Popover style per 0.5 (it already is navy). Title "How pay is measured". Replace the body with the text below (the first two and last paragraphs are word for word the same as on Dashboard #1):

> **Period.** Every number compares two month-ends: the walk opens on the first and closes on the second. Arcadia's fiscal year runs July to June.
>
> **Who is counted.** Employees active at month-end. The CEO and the eight function heads are left out on both Arcadia dashboards, so both count the same people.
>
> **Avg per FTE · Total payroll.** Pay divided by FTE, or the pay of everyone.
>
> **Loaded · Base.** Base is annual salary. Loaded adds the employer's fringe rate (benefits and employer taxes): base × (1 + fringe rate).
>
> **Constant · Nominal.** Constant converts every month at one rate (Jun 30, 2026), so currency swings are removed. Nominal uses each month's own rate and adds an FX Translation driver.
>
> **Drivers.** Expand shows every driver between Opening and Closing; the compact chart groups them. A person hired and gone between the two dates is in neither snapshot, so Hires counts people still here at the end. Headcount & FTE Walk counts every hire; the note under the chart gives both numbers.
>
> **Data.** Arcadia Systems is a fictional company. All data is synthetic.

3. Height: the popover grows to about 380 × 430. Keep its top aligned with the SHOW PAY AS heading; if it now runs past the bottom of the rail area, move its top up to the SELECT VIEW heading.

---

## 7. Hires: aligned with Dashboard #1

The two dashboards count hires differently on purpose (0.1). What changes here is the **wording**, so the number says what it is, and **one note** that gives both numbers, identical to the note on Dashboard #1.

### 7.1 Waterfall tooltip, Hires bar (the "1,058 people" you circled)

On the expanded waterfall's tooltip, the Hires description and the people line become:

```
// TT To Day   LEFT(DATENAME('month', [p_To]), 3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))
// TT People Words   (the people line under the value)
IF ATTR([step]) = "Hires" THEN " people still here on " + [TT To Day]
ELSE " people" END
```
Tooltip people line: `<SUM(worker_count)><TT People Words>` → "1,309 people still here on Jun 30, 2026".

Hires description text (in the tooltip description calc, the `Hires` branch):
"People new to Arcadia who were in this group on the closing date, at their pay on that date. Someone hired and gone between the two dates is in neither snapshot."

### 7.2 Top drivers, Hires reason (`TD Why`, the Hires branch, Avg per FTE lens)

```
WHEN "Hires" THEN
    IF NOT [Is FTE] THEN "New hires still here (" + [TD People Label] + ") added pay."
    ELSEIF [TD Total] < 0 THEN [TD People Label] + " hired and still here, below the opening average."
    ELSE [TD People Label] + " hired and still here, above the opening average." END
```
Under 65 characters at 9 pt, as the card needs: "1,309 people hired and still here, below the opening average."

### 7.3 Tie-out note under the waterfall (the same sentence as Dashboard #1)

Sheet `Tie-out` on **Region Walk** (primary), Headcount Walk secondary (2.3). `Link` on Detail from Region Walk; check the link icon is active on `Link` only.

```
// RW Hires Still Here   SUM(IF [RW Is Current] THEN [hires] END)            (= the Hires driver's people)
// TO Joined             ZN([Headcount Walk].[HW Joined])
// TO Gap                [TO Joined] - [RW Hires Still Here]
// Tie-out Text
IF [p_View] = "Office" THEN
    comma([RW Hires Still Here]) + " people new to Arcadia were at " + [p_Group] + " on " + [TT To Day] +
    ". Headcount & FTE Walk has no office view."
ELSEIF [p_View] = "Company" THEN
    comma([TO Joined]) + " joined; " + comma([RW Hires Still Here]) + " were still here on " + [TT To Day] +
    ", the hires the Compensation Walk prices. The other " + comma([TO Gap]) + " left again before the end."
ELSE
    comma([TO Joined]) + " joined " + [p_Group] + "; " + comma([RW Hires Still Here]) +
    " people new to Arcadia were in it on " + [TT To Day] +
    " (the Compensation Walk's Hires). The rest left again or changed team."
END
```
`comma(x)` stands for the comma pattern (Dashboard #1 build book, 6.4): write it out each time. Copying is faster: the `Tie-out Text` formula is the same as Dashboard #1's (its section 9), with `RW Hires Still Here` / `TO Joined` on the swapped sources.

Sheet: Text mark, Text `<Tie-out Text>`, Tableau Book 8, slate `#5A6170`, left, one line, Entire View, shading None, tooltip off, deselect action (5.4). Dashboard: floating inside the waterfall card at its bottom (about x = card left + 12, y = card bottom − 22, width = card width − 24, height 18). Shrink the waterfall sheet's height by 18 so its axis labels stay clear.

Check:

| Selection | Tie-out text |
|---|---|
| FY26, Company | 5,235 joined; 4,790 were still here on Jun 30, 2026, the hires the Compensation Walk prices. The other 445 left again before the end. |
| FY26 Q4, Company | 1,330 joined; 1,317 were still here on Jun 30, 2026, … The other 13 left again before the end. |
| FY26, Function Commercial | 1,470 joined Commercial; 1,309 people new to Arcadia were in it on Jun 30, 2026 (the Compensation Walk's Hires). The rest left again or changed team. |
| FY26, Country India | 1,113 joined India; 1,038 people new to Arcadia were in it on Jun 30, 2026 … |

---

## 8. Details I caught on the published page

1. **Top 5 routes headline disagrees with the bars on a tie.** Commercial FY26 (published data): the headline says "Hyderabad to Bengaluru leads, 6 people", while the first bar is Bengaluru to Hyderabad (also 6). The bars break the tie alphabetically; the headline picks the other one. In the headline's route calc, change `MAX(IF ... THEN [route] END)` to **`MIN(...)`** so it picks the alphabetically first, the same as the bars. Better still when tied: `"Bengaluru to Hyderabad and back lead, 6 people each way"` (calc: if the top two have equal movers and are the same pair reversed).
2. **The page subtitle is cut off** with a long group name ("…Data as of Ju.." with Accounting & Controllership). Shorten the template so it fits 1,150 px at 9 pt with the longest department name: `"How pay per FTE moved in " + [p_Group] + " and why · " + period + " · " + [Cost Text] + ", " + [Currency Text] + " · data as of Jun 30, 2026"` (drops "and how people move between offices", which the map headline already says).
3. **"+$0" FX Translation bar** in Constant currency: removed by section 4.
4. **Negative zero** ("−0.0%", "−0%"): 0.6, in every percent text calc (KPI Change card, waterfall headline).
5. **Map headline share of headcount** (open since 2026-10-12, data ready since release 2): `open_headcount` on Office Moves = the group's opening. Headline: `"725 people changed office (2.5% of headcount); 83% stayed inside one country"`. Calc `Move Share` = `SUM(movers) / MIN([open_headcount])` (MIN because the column repeats on every row of the group).
6. **Same period words on both dashboards**: the Period field reads `FY26 · Jun 25 → Jun 26` here and will on Dashboard #1; the turnover title there uses "FY26". Keep `Pair Name` as the single source of period text.
7. **Hires & exits holds transfers in a group view** (Commercial: 77 in, 64 out). Its tooltip should say "hires, exits and transfers in and out of this group" when `p_View` is not Company.

---

## 9. Check table (release 3, run on DuckDB 2026-10-15)

FY26 (Jun 30, 2025 → Jun 30, 2026), Loaded, Constant. Company values are also in the generated [expected_values.md](expected_values.md).

| Item | Company | Function Commercial |
|---|---|---|
| Opening pay per FTE | $110,063 | $116,724 |
| Closing pay per FTE | $113,664 | $120,604 |
| Change | +$3,601 · +3.3% | +$3,880 · +3.3% |
| People | 30,005 from 28,438 (+1,567) | 7,795 from 7,441 (+354) |
| Total payroll | $3,130.0M → $3,410.5M | $868.5M → $940.1M |
| Compact: Hires & exits · Promotions · Raises · Fringe & other | −$997 · +$695 · +$3,654 · +$250 | −$1,020 · +$746 · +$3,926 · +$228 |
| Top drivers (per FTE) | Tenure raises +$3,602 (25,189) · Hires −$1,201 (4,790) · Promotions +$722 (1,824) · Fringe rates +$284 (11,312) | Tenure raises +$3,863 (6,478) · Hires −$1,466 (1,309) · Promotions +$771 (495) · Exits +$449 (968) |
| Hires still here (tooltip, tie-out) | 4,790 | 1,309 |
| Joined (from Headcount Walk) | 5,235 | 1,470 |
| Expand label | Expand · 9 drivers | Expand · 11 drivers |
| Growth by Region headline | Arcadia Systems +5.5% (28,438 \| 30,005) | Commercial +4.8% (7,441 \| 7,795) |
| Map headline | 725 people changed office (2.5% of headcount); 83% stayed inside one country | (check on the page) |

**Must equal Dashboard #1** (same selection): People opening and closing; Growth by Region headline; "still here" and "joined" in the tie-out.

---

## 10. Test and publish

| # | Do | Expect |
|---|---|---|
| 1 | Hover Period, Group, Reset, Info, ✕ | Outline or nothing, never a square; tooltips as in 5 and 6 |
| 2 | Click Total payroll, Base, Nominal, a View row, Expand, Collapse, the map headline, a KPI card | Nothing stays highlighted; titles cannot be selected |
| 3 | Function > Commercial | People 7,795 from 7,441; Growth by Region "Commercial +4.8% (7,441 \| 7,795)"; tie-out "1,470 joined Commercial; 1,309 …" |
| 4 | Expand, Constant | "Expand · 11 drivers", no FX bar; Nominal: FX bar back, 12 |
| 5 | Hover the Hires bar (expanded) | "1,309 people still here on Jun 30, 2026" |
| 6 | Office > any office | Tie-out uses the office sentence |
| 7 | Open the period popover, then the group popover, then info | Only the last stays open |
| 8 | Reset | FY26, Company, Avg per FTE, Loaded, Constant, compact, popovers closed |
| 9 | Same selections on Dashboard #1 | Same opening, closing, still here, joined |

Publish: Reset, close popovers, Compact waterfall, hide all sheets, **File > Save to Tableau Public As...** `Arcadia Compensation Walk` (same name, same URL), extracts only. Check the published page with this table.
