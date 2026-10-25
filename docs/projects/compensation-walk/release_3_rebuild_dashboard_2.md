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
| Hires still here at the end | Tie-out note under the waterfall | Hires driver (4,790), Top drivers | **Identical** (same sentence in both). In a group view the note counts the hires who joined **this** group (Hires reason `New Hire`) and names the ones who joined elsewhere and moved in separately (section 8 item 9) |
| Leavers | Every leaver (3,668) | Exits from the opening team (3,223) | Different by definition, explained in both info panels |

**Why the hire counts differ, and why both are right.** Dashboard #1 counts **events** month by month: everyone who joined. Dashboard #2 compares **two snapshots**: pay can only be priced for someone present on a date, so a person hired in October who left in March is in neither snapshot. FY26, Company: 5,235 joined, 445 of them left again before Jun 30, 2026, so 4,790 were still here. The same 445 explain the leavers: 3,668 − 445 = 3,223 exits. For a group (a function, a country) the gap also includes people who joined and then changed team; and the Hires bar also holds people who joined **another** team and moved in (grouped where they are on the closing date), which the note counts separately so its two numbers are one population (section 8 item 9). Neither dashboard is changed to the other's definition: turnover needs every leaver, and a pay walk can only price people it can see. Instead **both show both numbers in one identical sentence** (Dashboard #1 guide section 9, Dashboard #2 guide section 7), so a reader never sees two unexplained hire counts.

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
| `fld_top.png` | 164 × 32 | #1 Period and Group fields (white capsule, same radius as the toggle) |
| `fld_rail.png` | 200 × 30 | #2 Period and Group fields (`#E4E3DD`, rounded like the toggles) |
| `seg_worker_employees_on/off`, `seg_worker_contingent_on/off`, `seg_worker_total_on/off` | 80 × 32 each | #1 Workforce toggle (capsule `#243A57`) |
| `btn_reset_top_label.png` | 150 × 32 | #1 Reset (outlined capsule: arrow + "Reset to default view") |
| `btn_reset_top.png` | 32 × 32 | Spare: arrow only, for a narrow header |
| `btn_reset_rail.png` | 188 × 30 | #2 Reset (outlined button, as published) |
| `btn_close.png` / `btn_close_light.png` | 16 × 16 | The ✕ on every popover (slate on white / mist on navy) |
| `info_open`, `info_close` (existing) | 32 × 32 | #1 info button |
| `rail_info_open`, `rail_info_close` (existing) | 16 × 16 | #2 info button |
| `btn_expand_icon`, `btn_collapse_icon` (existing) | 16 × 16 | Expand / Collapse on both |

**Test the field pattern first** (Dashboard #1: section 6.1; Dashboard #2: section 5.1) before converting the others. If the label will not sit on the shape at full size, the fallback is the published pattern (Text mark, sheet shading as the box) plus the deselect action, which removes the selection highlight but not the hover square.

### 0.5 Popovers and the info panel: one style

> **Superseded for #2's popover frame by [section 14](#14-popover-carryback-from-dashboard-3-oct-24-2026)** (Oct 24): padding 0, header 44 with a line, radius square on the rail side, rows on fixed slots, browse first in the Group picker. Colours, fonts and the open rule below still apply.

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

Expected: the walk returns **110,498** rows and every check **PASS** (release 3 values; full expected output for `06`, `07`, `09` in `docs/projects/contingent-workforce/sql_server_release_3_run.md`). If the file name differs on your Mac, `ls sqlserver/0*validate*` lists them.

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
| `ArcadiaHR` (the walk) | `custom_sql_compensation_walk.sql` | 110,498 |
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

Check after applying it (Function Commercial, Loaded, Constant): 11 bars on the expanded waterfall, "Expand · 11 drivers", FX Translation absent; in Nominal it returns and the count reads 12. If the filter is missing you see one more bar than the label says.

**Axis density on the expanded sheet.** Tableau picks tick spacing from the axis font size and the chart height; the expanded chart is shorter, so with a small font it labels every $1,000. Raise the axis font (Format > Scale) to Tableau Book 10 first. If it is still crowded, hide the axis header and set Grid Lines to None: every bar carries its value. Do not set a fixed tick interval: it only fits one scale, and Total payroll is in millions.

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
| Group Heading, Group Heading 2 | Titles | off |
| Title (page title / subtitle) | Title | "How to read this page", section 8 item 8 |
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

3. Size and position are now set in [section 14.7](#147-dashboard) (x 216, y 64, 591 x 440, 44 px title header). Earlier note: height: the popover grows to about 380 × 430. Keep its top aligned with the SHOW PAY AS heading; if it now runs past the bottom of the rail area, move its top up to the SELECT VIEW heading.

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

Tableau has no `comma()` function, so each number gets its own text calc (the same comma pattern each time). Create these on **Region Walk**:

```
// TT To Day   (copy it from ArcadiaHR, or retype; it only uses p_To, so it works on any source.
//              Do NOT write [ArcadiaHR].[TT To Day] in a Region Walk calc: ArcadiaHR is not in this blend)
LEFT(DATENAME('month', [p_To]), 3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))

// RW Hires Still Here   SUM(IF [RW Is Current] THEN [hires] END)            (= the Hires driver's people)
// RW Hires Moved In     SUM(IF [RW Is Current] THEN [hires_joined_elsewhere] END)
//                       (hired into another group of this view, moved in before the closing date; 0 for Company)
// RW Hires Joined Here  [RW Hires Still Here] - [RW Hires Moved In]          (a subset of TO Joined: test 79)
// TO Joined             ZN([Headcount Walk].[HW Joined])
// TO Gap                [TO Joined] - [RW Hires Joined Here]                 (never negative)

// TO Joined Text
IF [TO Joined] >= 1000 THEN STR(INT([TO Joined] / 1000)) + "," + RIGHT("00" + STR(INT([TO Joined]) % 1000), 3)
ELSE STR(INT([TO Joined])) END
// TO Still Here Text   (same, with [RW Hires Still Here])
// TO Here Text         (same, with [RW Hires Joined Here])
// TO Gap Text          (same, with [TO Gap])
// TO Moved In Clause   (empty when nobody moved in; the count is below 1,000 in every group, so STR is enough)
IF [RW Hires Moved In] > 0 THEN ", plus " + STR([RW Hires Moved In]) + " who moved in" ELSE "" END

// Tie-out Text   (starts with "Note:"; says why Hires differs from "joined"; one line)
IF [p_View] = "Office" THEN
    "Note: pay is priced for people here on " + [TT To Day] + ": " + [TO Still Here Text] +
    " new to Arcadia at " + [p_Group] + ". Headcount & FTE Walk has no office view."
ELSEIF [p_View] = "Company" THEN
    "Note: pay is priced for people here on " + [TT To Day] + ", so hires count " + [TO Still Here Text] +
    " of the " + [TO Joined Text] + " who joined (" + [TO Gap Text] + " left again)."
ELSE
    "Note: Hires counts people here on " + [TT To Day] + ": " + [TO Here Text] +
    " of the " + [TO Joined Text] + " who joined " + [p_Group] + [TO Moved In Clause] + "."
END
```
Dashboard #1 uses the same helpers in its section 9, with the sentence seen from its side (it counts every hire; the Compensation Walk counts people still here).

Sheet: Text mark, Text `<Tie-out Text>`, Tableau Book 8, slate `#5A6170`, alignment Left and Middle, one line, Entire View, title hidden, shading None, tooltip: see below, `zzTrue` and `zzFalse` on Detail, deselect action (5.4). **Remove any from/to/view filters left from testing**: the calc already reads the parameters.

The note is written to fit **one line** (about 135 characters at 8 pt in 644 px; the longest group sentence, a department with a long name and four-digit counts, is 129). Wrapping text inside a floating item did not behave, so the sentence is short instead.

Placement on Summary (card x 246, y 190, 668 x 314, bottom 504). Reserve a thin strip with padding, not by resizing the sheet:

1. Item hierarchy > `Card Expanded` and `Card Compact` (they swap in the same slot): Layout > Inner Padding bottom **16 to 30**. The waterfall loses only 14 px (40 was too much: it squeezed the bars).
2. `Tie-out`: **Floating**, X **258**, Y **478**, Width **644**, Height **18**. In front of the card, background None, no border, padding 0, title hidden. It ends at y 496, 8 px above the card edge.

**Tooltip on the note (the numbers in plain English).** Calcs on Region Walk:

```
// TT From Day    LEFT(DATENAME('month', [p_From]), 3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))
// TO Who         IF [p_View] = "Company" THEN "Arcadia" ELSE [p_Group] END
// Tie-out Detail
(IF [p_View] = "Office" THEN
    "The Headcount & FTE Walk has no office view, so there is no joined count to compare with." + CHAR(10) +
    "In the Hires bar: " + [TO Still Here Text] + " people new to Arcadia who were at " + [p_Group] + " on " + [TT To Day] + "."
ELSE
    [TO Joined Text] + " people joined " + [TO Who] + " between " + [TT From Day] + " and " + [TT To Day] +
    " (Headcount & FTE Walk, counted month by month)." + CHAR(10) +
    "In the Hires bar: " + [TO Here Text] + ", the ones still there on " + [TT To Day] + "." + CHAR(10) +
    (IF [RW Hires Moved In] > 0
     THEN "Also in the bar: " + STR([RW Hires Moved In]) + " who joined another team and moved in before " + [TT To Day] +
          " (" + [TO Still Here Text] + " in all)." + CHAR(10)
     ELSE "" END) +
    "Not in the bar: " + [TO Gap Text] +
    (IF [p_View] = "Company"
     THEN ", who joined and left again before " + [TT To Day] + ". They are in neither snapshot, so there is no pay to price."
     ELSE ", who left Arcadia or moved to another team before " + [TT To Day] + ". They are not in this group's closing snapshot."
     END)
END)
```
`Tie-out` sheet: `Tie-out Detail` on Detail; Worksheet > Tooltip > Show tooltips (on hover, no command buttons). Tooltip text: bold line **Why Hires counts fewer people than joined**, then `<AGG(Tie-out Detail)>`, then: "Avg per FTE: a hire moves the average only by how far their pay is from the opening average. New hires usually start below it, so the bar is negative. Total payroll: a hire adds their full pay." and "The Headcount & FTE Walk counts every joiner and leaver month by month, so its hires and leavers include these people." FY26 Company reads: "5,235 people joined Arcadia between Jun 30, 2025 and Jun 30, 2026 ... In the Hires bar: 4,790 ... Not in the bar: 445, who joined and left again before Jun 30, 2026." FY26 Department Accounting & Controllership reads: "72 people joined Accounting & Controllership ... In the Hires bar: 68 ... Also in the bar: 5 who joined another team and moved in before Jun 30, 2026 (73 in all). Not in the bar: 4, who left Arcadia or moved to another team before Jun 30, 2026."

Check:

| Selection | Tie-out text |
|---|---|
| FY26, Company | Note: pay is priced for people here on Jun 30, 2026, so hires count 4,790 of the 5,235 who joined (445 left again). |
| FY26 Q4, Company | Note: pay is priced for people here on Jun 30, 2026, so hires count 1,317 of the 1,330 who joined (13 left again). |
| FY26, Function Commercial | Note: Hires counts people here on Jun 30, 2026: 1,305 of the 1,470 who joined Commercial, plus 4 who moved in. |
| FY26, Country India | Note: Hires counts people here on Jun 30, 2026: 1,033 of the 1,113 who joined India, plus 5 who moved in. |
| FY26, Department Accounting & Controllership | Note: Hires counts people here on Jun 30, 2026: 68 of the 72 who joined Accounting & Controllership, plus 5 who moved in. |

---

## 8. Details I caught on the published page

1. **Top 5 routes headline disagrees with the bars on a tie.** Commercial FY26 (published data): the headline says "Hyderabad to Bengaluru leads, 6 people", while the first bar is Bengaluru to Hyderabad (also 6). The bars break the tie alphabetically; the headline picks the other one. In the headline's route calc, change `MAX(IF ... THEN [route] END)` to **`MIN(...)`** so it picks the alphabetically first, the same as the bars. Better still when tied: `"Bengaluru to Hyderabad and back lead, 6 people each way"` (calc: if the top two have equal movers and are the same pair reversed).
2. **The page subtitle is cut off** with a long group name ("…Data as of Ju.." with Accounting & Controllership). Shorten the template so it fits 1,150 px at 9 pt with the longest department name: `"How pay per FTE moved in " + [p_Group] + " and why · " + period + " · " + [Cost Text] + ", " + [Currency Text] + " · data as of Jun 30, 2026"` (drops "and how people move between offices", which the map headline already says).
3. **"+$0" FX Translation bar** in Constant currency: removed by section 4.
4. **Negative zero** ("−0.0%", "−0%"): 0.6, in every percent text calc (KPI Change card, waterfall headline).
5. **Map headline share of headcount** (open since 2026-10-12, data ready since release 2): `open_headcount` on Office Moves = the group's opening. Headline: `"725 people changed office (2.5% of headcount); 83% stayed inside one country"`. Calc `Move Share` = `SUM(movers) / MIN([open_headcount])` (MIN because the column repeats on every row of the group).
6. **Same period words on both dashboards**: the Period field reads `FY26 · Jun 25 → Jun 26` here and will on Dashboard #1; the turnover title there uses "FY26". Keep `Pair Name` as the single source of period text.
7. **Hires & exits holds transfers in a group view** (Commercial: 77 in, 64 out). Its tooltip should say "hires, exits and transfers in and out of this group" when `p_View` is not Company.

8. **Page subtitle tooltip.** The default tooltip on the `Title` sheet printed raw field names ("Page Subtitle:", "p_Lens:") and repeated the subtitle. Replace it with "How to read this page": what is shown, the measure definition for the current Cost and Lens, the currency rule, the two-snapshot rule and the population. Calcs on ArcadiaHR (`TT From Day` plus one text calc `Title Tip`; `TT To Day` already exists):

```
// TT From Day
LEFT(DATENAME('month', [p_From]), 3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))
// Title Tip
"Showing: " + (IF [p_View] = "Company" THEN "all of Arcadia" ELSE [p_View] + " · " + [p_Group] END) + CHAR(10) +
(IF [Is FTE] THEN
    (IF [p_Cost] = "Loaded"
     THEN "Average pay per FTE = loaded cost ÷ FTE. Loaded cost is base pay plus employer fringe (benefits and payroll taxes)."
     ELSE "Average pay per FTE = base pay ÷ FTE. Base is pay only, with no employer fringe." END)
ELSE
    (IF [p_Cost] = "Loaded"
     THEN "Total payroll = total loaded cost: base pay plus employer fringe (benefits and payroll taxes)."
     ELSE "Total payroll = total base pay, with no employer fringe." END)
END) + CHAR(10) +
(IF [p_Currency] = "Constant"
 THEN "Constant currency: every month is converted at one fixed exchange rate, so currency moves do not count."
 ELSE "Nominal currency: each month is converted at that month's rate, so currency moves appear as FX Translation." END) + CHAR(10) +
"Compares two snapshots, " + [TT From Day] + " and " + [TT To Day] +
". Each person is priced at their pay on that date; people who joined and left in between are in neither." + CHAR(10) +
"Employees only, executive officers excluded; every employee counts as 1.0 FTE."
```
`Title` sheet: `Title Tip` on Detail (parameters only, adds no rows); Worksheet > Tooltip > Show tooltips (on hover, no command buttons): bold line **How to read this page**, then `<Title Tip>`, then "Click ⓘ in the left rail for the full definitions and limits." (Book 9, slate). Keep the deselect action (5.4); this replaces "off" for the page title sheet in that table. Dashboard #1 gets the same tooltip adapted to events (hires, leavers, movements) when it is rebuilt.

9. **SQL check, done 2026-10-18: "73 of the 72 who joined".** The note read "hires count 73 of the 72 who joined" for **FY26, Department Accounting & Controllership** (`D-502`). Run on the release 3 warehouse (SQL Server build translated to DuckDB):

   | Query | Population | Result |
   |---|---|---:|
   | (a) joined | first month-end in the snapshot between Jun 30, 2025 and Jun 30, 2026, department `D-502` on that month-end (Dashboard #1's Joined) | 72 |
   | (b) still here | not in the Jun 30, 2025 snapshot, in the Jun 30, 2026 snapshot, department `D-502` on Jun 30, 2026 (the Hires bar) | 73 |
   | (c) in one only | 4 joined A&C and left Arcadia (W142918, W143054, W143684, W146048); 5 joined another department (3 in FP&A, 1 in Product Engineering, 1 in Mobile & Web Engineering) and moved into A&C | 9 |

   (c) in full: W142918 (Sep 2025), W143054 (Oct 2025), W143684 (Nov 2025), W146048 (Apr 2026) joined A&C and were gone by Jun 30, 2026; W142677 (Sep 2025, `D-501`), W143776 (Nov 2025, `D-501`), W143958 (Dec 2025, `D-501`), W145500 (Mar 2026, `D-103`), W145594 (Mar 2026, `D-102`) joined elsewhere and moved into A&C. 72 − 4 + 5 = 73. Nobody joined A&C and moved out.

   **Cause:** the two numbers were different populations. Hires are grouped as at the closing date, because that is where their pay is priced, so in a group view they include people who joined another team and moved in; "joined" books each hire to the team they joined. Across all 88 periods, 73 period × group combinations showed still here > joined (Department 59, Sub-function 5, Country 5, Function 4, Company 0).

   **One population for both numbers: people who joined *this* group in the period.** Dashboard #1's joined already is that (it is a flow in a walk that must close, so it cannot be regrouped at the closing date). The Hires bar keeps its closing-date grouping (the pay walk closes on it); the walk now tags each hire with the group they joined: `movement_reason` on the Hires line is `New Hire` (joined this group, still in it) or `Joined Elsewhere` (joined another group of this view, moved in). The region walk carries the same split as `hires_joined_elsewhere`. The note compares `New Hire` people with joined and names the movers separately: "68 of the 72 who joined Accounting & Controllership, plus 5 who moved in" (68 + 5 = the bar's 73). After the change, still here > joined in **0** combinations; test 79 keeps it that way. Every line other than Hires is unchanged to the cent; the Hires bar keeps its people exactly and its dollars to within $0.01 (each reason is rounded to the cent separately). The walk has 1,580 more rows (110,498), the region walk the same 26,520 with one new column.

   Tableau: section 7.3 (calcs `RW Hires Moved In`, `RW Hires Joined Here`, `TO Here Text`, `TO Moved In Clause`; the group branch of `Tie-out Text`; the tooltip's "Also in the bar" line), and Dashboard #1 guide section 9. Refresh both extracts (Walk and Region Walk) after pasting the new Custom SQL. Optional: the Hires bar tooltip (7.1) can add a line from `SUM(IF [movement_reason] = "Joined Elsewhere" THEN [worker_count] END)`, e.g. "5 of them joined another team and moved in".

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
| Hires still here (Hires bar, tooltip) | 4,790 | 1,309 |
| In the tie-out: joined this group and still here · moved in | 4,790 · 0 | 1,305 · 4 |
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
| 3 | Function > Commercial | People 7,795 from 7,441; Growth by Region "Commercial +4.8% (7,441 \| 7,795)"; tie-out "1,305 of the 1,470 who joined Commercial, plus 4 who moved in"; Hires bar 1,309 people |
| 4 | Expand, Constant | "Expand · 11 drivers", no FX bar; Nominal: FX bar back, 12 |
| 5 | Hover the Hires bar (expanded) | "1,309 people still here on Jun 30, 2026" |
| 6 | Office > any office | Tie-out uses the office sentence |
| 7 | Open the period popover, then the group popover, then info | Only the last stays open |
| 8 | Reset | FY26, Company, Avg per FTE, Loaded, Constant, compact, popovers closed |
| 9 | Same selections on Dashboard #1 | Same opening, closing, still here, joined |

Publish: Reset, close popovers, Compact waterfall, hide all sheets, **File > Save to Tableau Public As...** `Arcadia Compensation Walk` (same name, same URL), extracts only. Check the published page with this table.

## 11. Align the rail with Dashboard #1 (white pill toggles, capsule fields)

The #1 look is now the base: a translucent navy capsule behind the toggle, a white pill for the selected option, white capsule fields, an outlined capsule Reset. The images keep their file names, so **nothing is re-assigned** in Tableau; only the images and the dashboard items change.

What changed in the PNGs (all regenerated from `docs/brand/build`, at 3x, alpha-only sharpening):

| Image | Before | Now |
|---|---|---|
| `seg_lens_*`, `seg_cost_*`, `seg_currency_*` (88 × 30 cell) | `#E4E3DD` pill, small corner radius, 10 px label | White pill, full capsule radius, navy label, 11 px (same as #1) |
| `fld_rail.png` | 200 × 30, `#E4E3DD` rectangle | 200 × 32, white capsule, box drawn 1 px low so the label sits optically centred |
| `btn_reset_rail.png` | outlined rectangle | outlined capsule, same 120-alpha line as #1 |

In Tableau (Mac), after `git pull` and copying `docs/brand/shapes/Arcadia/*.png` into `~/Documents/My Tableau Repository/Shapes/Arcadia/`:

1. Reopen the workbook and **Reload Shapes** (Shape card, any sheet). Confirm `Lens Toggle`, `Cost Toggle`, `Currency Toggle`, `Period Field`, `Group Field` and `Reset` show the new images.
2. For each of the three toggle items (`Lens Toggle`, `Cost Toggle`, `Currency Toggle`): Layout > **Background** `#243A57`, **corner radius 15**, padding 0, border none. Keep the current width and height (two cells, 30 tall). This capsule is what shows behind the unselected option, exactly as in #1.
3. `Period Field` and `Group Field` items: height **32** (was 30), move Y up by 1 so the box does not shift. Background stays None.
4. `Reset` item: no change (the capsule is in the image).
5. Check the three ✕ and Info shapes are still `rail_info_open/close` (they were regenerated, same names).
6. Hover: the hover outline is rectangular; if it shows square corners on a capsule, set the item corner radius to 15 on the toggles (as above) and 16 on the fields.

Check on the published page: selected option is a white pill with navy text, unselected is light slate on the capsule, text in the Period and Group fields has equal space above and below, Reset has a rounded outline.

---

## 14. Popover carryback from Dashboard #3 (Oct 24, 2026)

Dashboard #3 (Workforce Planning, published Oct 23) taught us two things about popovers, and Dashboard #1 got them in its section 14. This section carries both to #2. **Nothing else on the page changes**: the rail keeps its place, items and sizes, and the waterfall, KPI cards, drivers, Growth by Region, map, tie-out note and every number stay exactly as they are. Sources: [release_3_rebuild_dashboard_3.md](../workforce-planning/release_3_rebuild_dashboard_3.md) sections 7.1, 9.0 to 9.2 and 13; [Dashboard #1 section 14](../headcount-fte-walk/release_3_rebuild_dashboard_1.md); `dashboard_3_published.md` section 3. For popover layout and for how the view and group pickers behave, this section supersedes 0.5 (container padding and radius), 6 step 3 (info size) and the popover parts of `rail_group_picker_build.md` and `rail_controls_build.md`; each keeps its calcs and sheet names.

**Change A, organised popovers.** Every row sits on a fixed slot, so a short list starts at the top instead of spreading out. Each popover hangs from the rail edge with a header, a thin line, a body and a footer; a vertical divider separates the span list from the period grid.

**Change B, browse first, apply on a group click.** Clicking a view in the rail only browses (a new parameter, `p_ViewTab`) and opens the group popover on that view; the page does not move. Clicking a group applies the view and the group together and closes the popover. "All" (Company) has no groups, so it applies at once. Nothing defaults to the first country, function or office alphabetically any more.

**The #2 difference from #1 and #3.** #2 has no view list inside the popover: the rail's `Rail View` list *is* the view list (decision, Oct 24). So a rail view click sets `p_ViewTab` and opens the Group popover, the rail stays where it is, and the popover is a grid of groups only.

**Status (Oct 24, 2026): built, reviewed against 14.11 and published** at the same URL. All click tests passed. Corrections found while building are folded in below: `Rail View` must keep `Close Panel` on Detail, `WF Caption` is an unused leftover (not an R1 item), and the navy that was published (see R3).

**Next time you republish #2 (found while finishing #1, Oct 24):** (1) `d2_field_capsule` now has a drawn chevron (`make_d1_d2_chevrons.py`); apply it to `Period Field` and `Group Field`, delete the typed `▾` and keep one label run each, as in #1 section 14.14 item 1. (2) Open the Info popover on Tableau Public and check that the text is not cut off: #1's needed 29 px more height online than in Desktop. (3) `Info Button` and `Group Panel` have tooltip command buttons on, which shows a "Keep Only / Exclude" toolbar on hover online; untick **Include command buttons** on both.

### 14.1 What each picker does today, and what it will do

| Picker | Today (checked in your saved .twb, Oct 24) | After this section |
|---|---|---|
| **Period** (`Period Field`, `Span List`, `Period Panel`) | Already browse-then-apply: a span click sets `p_Span`, a cell click sets `p_From` and `p_To` and closes. Container x 214, y 85, 624 x 330, navy `#12213B`, padding 16. `Span List` rows are `pair_type` (discrete, Square marks); `Period Panel` rows are `Period Row`, an ordinal table calc, so a short grid floats in the middle. `Pair Label` uses an arrow glyph | Same behaviour. Rows on fixed slots (6 slots of 32 px), frame x 216, y 88, 624 x 289 with header, line, divider and footer. Arrow replaced (R1) |
| **View** (`Rail View`, in the rail) | **Applies on the first click.** A click on Function sets `p_View` = Function and `p_Group` = the first group alphabetically (`Default Group`, a FIXED MIN), so the page changes to Commercial before you have chosen; Office lands on the first office, Country on Argentina. The same click *closes* the Group popover (`Close panel on view change`), so you then open it from the Group field to pick the group you wanted | Browse first. A rail click on Function, Sub-function, Department, Office or Country sets `p_ViewTab` and opens the Group popover on that view; the page does not move. A click on All applies Company and Arcadia Systems at once and closes the popover. The `›` in the rail stays on the view in use |
| **Group** (`Group Field` in the rail, `Group Panel` in the popover) | `Group Field` opens the popover; `Group Panel` lists the groups of `p_View` (`Group In View`) and a click sets `p_Group` and closes. Container x 214, y 420, 624 x 330; marks Automatic, text Bold 12 with a Semibold 9 run | `Group Field` opens the popover on the view in use. `Group Panel` lists the groups of the tab being browsed (`Group Grid Rows`); a click sets `p_Group` and `p_View` together and closes. 12 slots of 26 px (Office has 35 offices, 3 columns of 12). Frame x 216, y 164, 624 x 409 |
| **Info** (`Info Button`, `Info Popover`) | One text object with the title "How pay is measured" inside the body; x 215, y 71, 591 x 440, padding 14 | Same text, same 591 x 440. 44 px header with the title and a ✕, a line, then the body |
| **Reset** | Resets `p_View` (`Default View`) and `p_Group` (`Default Group All`) | Also resets `p_ViewTab` (#3 action 23b) |

Why View applied on the first click: `Set view` and `Set group from view` both fire on a `Rail View` click, and `Default Group` is `{ FIXED [view_name] : MIN([group_name]) }`. Browsing needs a parameter that is *not* the one the page reads, which is exactly what `p_ViewTab` is.

Why the rail `›` stays on the view in use: the rail is always visible, so it must say what the page shows. While you browse, the popover title says which view you are looking at ("Select a department"). If you close the popover without picking, nothing changed and the rail is still right.

### 14.2 Refinements (all five approved, Oct 24)

| # | Refinement | Why | Cost |
|---|---|---|---|
| R1 | **Remove the arrow glyph** from `Pair Label` (Year over Year cells): " to " instead. (`WF Caption`, the FTE sentence, was in the first draft of this row. It is not used on any sheet, so nobody can see its arrow, and Tableau shows it red on its own: it mixes aggregated and row-level fields. It was deleted with the other unused red calcs; nothing to fix.) | Project rule: no arrow characters; an arrow at 9 pt is unreadable (same as #1 R1 and #3 D11) | 1 formula edit |
| R2 | **Fix a broken action**: `Close period panel when group opens` (Group Field) has **no source field** in the saved file, so it may not close the Period popover | Found in the .twb; one open at a time is the rule (0.5) | Pick `Close Panel` as its field |
| R3 | **One navy for the three popovers**: the file had `#13223A` (rail, Group, Info) and `#12213B` (Period). Published: all three popovers `#13243A`, the rail `#13223A`. The best match for a clean seam is the rail's own `#13223A` on the popovers; the 2-step difference in green is nearly invisible | The popovers touch the rail, so a difference can show as a faint line | Format only |
| R4 | **`Rail View` tooltip**: its tooltip still lists `Default Group`, `View Label`, `view_name` and a `<!Missing Field!>` (`Zero`) | Tooltips are off on every control; the missing field is a warning in waiting | Untick Show tooltips |
| R5 | **Info text style per 0.5**: lead-ins Tableau Semibold 10 white, body Tableau Book 10 `#B8C0CC` (today bold `#F5F5F5` and plain `#F5F5F5`) | Same as #1's info body | Format only |

Not changing (so you do not wonder): the typed `▾` in `Period Field` and `Group Field`; the rail order, sizes and dividers; the Group Block's visibility (`Has Groups`, it hides the Group field under All, which is still right because it reads `p_View`); the `kpi_` parameters; the unused sheet `Rail Group` and the unused parameters `Measure` and `p_Collapse` (they cost nothing; a tidy-up for another day).

**Known and left alone** (same as #1): `Group Panel` lists every group that ever existed in the view, so a group missing in the selected period is still clickable and gives an empty page. It predates this job.

### 14.3 The frame, in numbers

Page 1400 x 850; the rail is x 0 to 216, navy. All three popovers hang from the **rail edge** (x 216, flush), navy `#13233A`, **corner radius top-left 0, bottom-left 0, top-right 10, bottom-right 10** (square where they touch the rail), inner and outer padding 0, border None.

Four bands, top to bottom: **header** 44, **line** 9 (1 px line inset 16 each side), **body**, **footer** 28 (no footer on Info).

| Popover | x | y | w | Body | Total h | Top lines up with | Visibility |
|---|---:|---:|---:|---:|---:|---|---|
| `Period Popover` | 216 | 88 | 624 | **208** (8 + 6 x 32 + 8) | 44 + 9 + 208 + 28 = **289** | the SELECT PERIOD heading | `p_PeriodOpen` |
| `Group Popover` | 216 | 164 | 624 | **328** (8 + 12 x 26 + 8) | 44 + 9 + 328 + 28 = **409** | the SELECT VIEW heading | `p_GroupOpen` |
| `Info Popover` | 216 | 64 | 591 | **387** | 44 + 9 + 387 = **440** (same height as today) | the info button row | `p_InfoOpen` |

Bottoms: Period 377, Group 573, Info 504, all well above the footnote (y 822). Period and Group share x 216 to 840 (the same 624 width as today), so switching from one to the other does not jump sideways. The Group popover sits beside the rail view list, so the rail click and the popover it opens are side by side.

Why 6 period slots: Month is a grid of **6 rows by 8 columns** (`Period Rows` = ceil(48 / 8)); Fiscal year and Quarter are 4 by 4, Year to date 2 by 4. Why 12 group slots: `Pick Rows` = ceil(groups / 3), and Office has 35 offices, so 12 rows; Department 31 (11), Country 22 (8), Sub-function 10 (4), Function 8 (3).

**Fixed-slot rule** (same as #1 and #3): a row position goes on Rows as a **continuous** measure with a fixed, reversed axis and no header. Tableau rejects decimals such as 0.5 in the axis boxes, so every slot is **2 units wide with its centre on an odd number** (1, 3, 5 ...) and the axis runs from 0 to 2 x the number of slots.

| Sheet | Slots | Axis fixed start / end | Pane height | Pixels per slot |
|---|---:|---|---:|---:|
| `Span List`, `Period Panel` | 6 | 0 / 12 | 192 | 32 |
| `Group Panel` | 12 | 0 / 24 | 312 | 26 |

`Rail View` keeps its discrete rows: it always shows the same six views in a fixed 152 px block, so there is nothing to float.

### 14.4 Before Tableau (Mac)

The three images are made by `docs/brand/build/make_d3_popover_lines.py` (now with a `d2` mode) and are committed in `docs/brand/shapes/by_dashboard/d2/`. They are dashboard **Image** objects, not shapes, drawn at 2x so **Fit Image** keeps them crisp:

| File | Pixels | Item size | Where |
|---|---|---|---|
| `d2_popover_line_wide.png` | 1248 x 18 | 624 x 9 | Under the Period and Group headers |
| `d2_popover_line_info.png` | 1182 x 18 | 591 x 9 | Under the Info header |
| `d2_popover_divider_period.png` | 48 x 416 | 24 x 208 | Between `Span List` and `Period Panel` |

No group divider: the Group popover has no list on its left.

I have already copied the three files into `Arcadia Compensation/Images and Buttons/`. Check, and make a backup before you touch the workbook:

```bash
cd ~/Documents/Tableau/Tableau\ Public/ArcadiaHR/Arcadia\ Compensation
ls "Images and Buttons" | grep d2_popover
cp "Arcadia Compensation Walk.twb" "Arcadia Compensation Walk - before popovers.twb"
ls -1 *.twb
```

Expected: the three `d2_popover_*` names, then both `.twb` files.

### 14.5 Parameter and calcs

**Parameter.** Add one: `p_ViewTab`, String, List, values **Company, Function, Sub-function, Department, Office, Country** (the same six as `p_View`, spelled the same), current value **Company**. Easiest: right-click `p_View` in the Data pane > **Duplicate**, rename to `p_ViewTab`, check the list. It is the view the Group popover is *browsing*; `p_View` stays the view the page *uses*. Parameters go from 30 to **31**.

**Calcs (data source ArcadiaHR).** Edit four, create five. Spell the field names with the Data pane (`view_name`, `group_name` are the source's own).

*Edit in place (double-click the calc):*

```
// Group Is Current   (was: group only; six names exist in two views, see 14.9)
[group_name] = [p_Group] AND [view_name] = [p_View]
```
```
// Default Group   (was { FIXED [view_name] : MIN([group_name]) }, the alphabetical rule)
"Arcadia Systems"
```
```
// Pick Row   (odd slots 1, 3, 5 ... inside the column; Pick Col and Pick Rows stay as they are)
2 * ((INDEX() - 1) % [Pick Rows]) + 1
```
```
// Period Row   (odd slots; Period Col and Period Rows stay as they are)
2 * ((INDEX() - 1) % [Period Rows]) + 1
```

`Panel Title` stays on `p_View` on purpose: the rail heading above the Group field (`Group Heading`) reads it and must name the view in use. The popover gets its own title (`Tab Title`, below). `Default Group` is now used by no action; it stays (the unused `Rail Group` sheet reads it) but can no longer pick "the first one".

*Create (all row-level, no aggregation):*

```
// Tab Title          (the Group popover title: the view being browsed)
"Select " + CASE [p_ViewTab]
    WHEN "Function" THEN "a function" WHEN "Sub-function" THEN "a sub-function"
    WHEN "Department" THEN "a department" WHEN "Office" THEN "an office"
    WHEN "Country" THEN "a country" ELSE "a group" END
// Span Slot          (Span Order is 1 to 4: Year over Year, Year to date, Quarter, Month)
2 * [Span Order] - 1
// Span Is Current
[Span Value] = [p_Span]
// Group Grid Rows    (the groups of the view being browsed; All has no groups, so the grid is empty there)
[view_name] = [p_ViewTab] AND [view_name] <> "Company"
// View Apply         (a rail click on All applies at once; any other view only browses)
IF [view_name] = "Company" THEN "Company" ELSE [p_View] END
// Group Apply From View
IF [view_name] = "Company" THEN [group_name] ELSE [p_Group] END
// Keep Group Panel Open   (a rail click opens the popover, except on All)
[view_name] <> "Company"
```

That is seven new calcs. *Keep as they are, on purpose:* `Group In View` (`[view_name] = [p_View]`, still read by `Rail Group`), `View Label` (the rail `›` on `p_View`), `Has Groups`, `Group Field Text`, `Toggle Group Panel`.

*R1, arrows (one formula edit):*

```
// Pair Label   (only the Year over Year line changes: the arrow becomes " to ")
WHEN "Year over Year" THEN LEFT(DATENAME('month',[from_month_end]),3) + " " + RIGHT(STR(YEAR([from_month_end])),2) + " to " + LEFT(DATENAME('month',[to_month_end]),3) + " " + RIGHT(STR(YEAR([to_month_end])),2)
```

The FY26 cell then reads `Jun 25 to Jun 26` (Semibold 9, about 85 px in a 120 px column).

**Checkpoint P1 (any text table, ArcadiaHR):** `Span Slot` per `Span Value` = Fiscal year 1, Year to date 3, Quarter 5, Month 7. `Keep Group Panel Open` per `view_name` = False only for Company. `Default Group` = Arcadia Systems on every row.

### 14.6 Sheets

All sheets in this section: Fit **Entire View**, Format > Shading > Worksheet **None**, grid lines, zero lines, axis rulers and ticks **None**, row and column dividers **None**, Marks type **Text** (not Automatic or Square: Automatic sometimes picks Bar on a continuous pill and the label then sits at the bar's end).

**`Span List`**
1. Drag `Span Slot` to Rows (replace `pair_type`). Right-click the pill > **Measure > Minimum**, then right-click again > **Continuous**.
2. Right-click the axis > Edit Axis: Range **Fixed**, start **0**, end **12**; tick **Reversed**; close. Right-click the axis > untick **Show Header**.
3. Drag `pair_type` to **Detail** (it keeps its filter, which hides "Custom Range"). Marks type **Text** (it is Square today). Drag `Span Is Current` to **Color**: True white `#FFFFFF`, False `#B8C0CC`.
4. Text: `<Span Display>`, Tableau **Book 10**, alignment **Center**, **Middle**. (The `›` in `Span Display` marks the span in use.)
5. Detail keeps `Span Value`, `zzTrue`, `zzFalse`. Tooltip: untick Show tooltips.

**`Period Panel`**
1. Columns `Period Col` (Discrete, header hidden) as today. Rows: `Period Row` (now odd slots 1, 3, ... 11): right-click > **Continuous** (the pill turns green). Then right-click > **Edit Table Calculation** > **Specific Dimensions** with **every** Detail field ticked (`Period Key`, `Pair Label`, `from_month_end`, `to_month_end`, `Close Panel`, `zzTrue`, `zzFalse`). At the top of that dialog, **Nested calculation**: choose `Period Rows`, then `Period Col`, and set each to the same Specific Dimensions (one nested calc left on "Table (Across)" shifts the grid; this is the #3 lesson).
2. Axis: Fixed 0 to **12**, **Reversed**, header hidden. Format > Lines: all None.
3. Marks Text: `<Pair Label>` Tableau **Semibold 9**, **Center**, **Middle**. Color `Period Is Current` as today (True white `#FFFFFF`, False `#B8C0CC`). Tooltip `<Pair Name>` as today.
4. Keep the filters (`Action (zzFalse)`, `Period In Span` = True) and every Detail field.

**`Group Panel`**
1. Filters: remove `Group In View`; add `Group Grid Rows` = **True**. Keep `Action (zzFalse)`.
2. Columns `Pick Col` (Discrete, header hidden). Rows `Pick Row` (now odd slots 1, 3 ... 23): right-click > **Continuous**; axis Fixed 0 to **24**, **Reversed**, header hidden.
3. Detail: add **`view_name`** (needed by "Apply view on group pick"); remove **`Panel Title`** (it belongs to the heading). Keep `group_name`, `Close Panel`, `zzTrue`, `zzFalse`; Text `Group Label`; Tooltip `group_parent` as today.
4. Re-check **Edit Table Calculation** on `Pick Row`, `Pick Col` and the nested `Pick Rows`: Specific Dimensions with every Detail field ticked (`group_name`, `view_name`, `Close Panel`, `zzTrue`, `zzFalse`), `group_name` at the top.
5. Marks **Text** (Automatic today). Label `<Group Label>` only (delete the `·` run and the second field if they are still in the label): Tableau **Book 9** (today Bold 12), **Center**, **Middle**. Color `Group Is Current`: True white `#FFFFFF`, False `#B8C0CC`.
6. The sheet is empty while `p_ViewTab` = Company. That is correct. To test: right-click `p_ViewTab` > Show Parameter, set Office, look, set Company.

**`Group Heading 2`** (the popover title): Text `<Tab Title>` only (replace `Panel Title`; delete any typed run): Tableau **Bold 12**, white `#FFFFFF`, alignment **Left**, **Middle**. Tooltip off. Add `zzTrue`, `zzFalse` to Detail if missing.

**`Rail View`**: Detail: **add** `Group Apply From View`, `View Apply`, `Keep Group Panel Open`; **remove** `Default Group` only (no action reads it any more). **Keep `Close Panel` on Detail**: `Close on view change` and `Close info on view change` read it from `Rail View`, and without it they stop firing silently, so Period or Info stays open when you click a view. Keep `view_name`, `zzTrue`, `zzFalse`, Text `View Label`, rows, fonts and size exactly as today. Tooltip: untick Show tooltips (R4). Nothing visible changes in the rail.

**`Group Field`:** add `view_name` to **Detail** ("Open group on its view" reads it). Its filter `Group Is Current` now also checks the view, which still leaves exactly one mark.

**`Reset`:** no change. Its Detail already holds `Default View` (it will feed `p_ViewTab` too).

**Close sheets** (`Period Close`, `Panel Close`): unchanged; only their item size changes (14.7).

**Checkpoint P2 (sheets, before the dashboard):** `Span List` shows 4 rows on slots 1, 3, 5, 7; `Period Panel` at Fiscal year shows a 4 by 4 block starting at the top, at Month a 6 by 8 block. Set `p_ViewTab` to Function: `Group Panel` shows 8 names in 3 columns (3, 3, 2) from the top; Sub-function 10 (4, 4, 2); Department 31 (11, 11, 9); Office 35 (12, 12, 11); Country 22 (8, 8, 6). Set it back to Company. If a count is different, tell me before going on (the counts come from #1's lists plus Office).

### 14.7 Dashboard

Edit the three popover containers in place; do not delete and rebuild them, so every action keeps its source. Open one at a time: right-click `p_PeriodOpen` in the Data pane > **Show Parameter**, set True, work, then **Remove from Dashboard** the control and set the value back to False. Use the Layout pane's **Item hierarchy** (it lists hidden containers too). Type every x, y, w, h in the Layout pane.

**R3 first (a minute):** `Rail` container and the three popover containers: background `#13233A`, border None. The sheets inside the popovers: Format > Shading > Worksheet **None**, so the container's navy shows through.

**Period Popover** (vertical container, floating): x **216**, y **88**, w **624**, h **289**. Background `#13233A`, border **None** (it is Solid today), outer padding 0, **inner padding 0** (16 today), corner radius top-left 0, bottom-left 0, top-right 10, bottom-right 10.

| Item | Type | w | h | Format |
|---|---|---:|---:|---|
| `Period Popover Header` (the horizontal container, today 590 x 35) | Horizontal container | 624 | 44 | Background None, padding 0 |
| title (the text object, today 522 x 35) | Text | 580 | 44 | `Select a period`, Tableau Bold 12, white `#FFFFFF`; inner padding left 16, top 12; delete any second line |
| `Period Close` | Sheet | 44 | 44 | Inner padding 14 on all sides, outer 0 |
| header line | Image `d2_popover_line_wide.png` | 624 | 9 | **Fit Image**, no border, padding 0 |
| `Period Popover Panel` (today 590 x 261) | Horizontal container | 624 | 208 | Background None, padding 0 |
| `Span List` | Sheet | 120 | 208 | Inner padding top 8, bottom 8, left 0, right 0; outer 0 (4 today) |
| divider | Image `d2_popover_divider_period.png` | 24 | 208 | Fit Image, no border, padding 0 |
| `Period Panel` | Sheet | 480 | 208 | Inner padding top 8, bottom 8, left 0, right 0; outer 0 |
| footer | Text | 624 | 28 | `Fiscal year runs July to June. Each option compares two month-ends. Data through Jun 30, 2026.` Tableau Book 9, `#8FA0B8`; inner padding left 16, top 6 |

Steps: (1) set the container's position, size, padding and radius; (2) header container to h 44, then the title and the close sheet to the sizes above; (3) drag an **Image** object from the Objects pane into the container, between the header and the panel (a grey drop guide shows the spot), choose `d2_popover_line_wide.png`, Fit Image; (4) resize `Span List` and `Period Panel` and drag an Image between them for the divider; (5) drag a **Text** object below the panel for the footer. 120 + 24 + 480 = 624.

**Group Popover:** x **216**, y **164**, w **624**, h **409**. Same container format as the Period popover (border None, padding 0, the same radius).

| Item | Type | w | h | Format |
|---|---|---:|---:|---|
| header (horizontal container, today 590 x 35) | Horizontal container | 624 | 44 | Background None, padding 0 |
| `Group Heading 2` | Sheet | 580 | 44 | Inner padding left 16, others 0; outer 0 |
| `Panel Close` | Sheet | 44 | 44 | Inner padding 14 (today 68 x 35, outer 4) |
| header line | Image `d2_popover_line_wide.png` | 624 | 9 | Fit Image |
| `Group Panel` | Sheet | 624 | 328 | Inner padding top 8, bottom 8, left 16, right 16; outer 0 |
| footer | Text | 624 | 28 | `Pick a group to apply it. To change the view, click one in the rail.` Tableau Book 9, `#8FA0B8`; inner padding left 16, top 6 |

`Group Panel` sits directly in the vertical container under the header; drop the line image between them, then type its size. Three columns of 197 px each (624 minus 2 x 16, divided by 3) hold the longest office name at Book 9.

**Info Popover:** x **216**, y **64**, w **591**, h **440** (same size; position moves 1 px right and 7 px up so it hangs from the rail beside the info button). Container border None, padding 0 (14 today), same radius.

| Item | Type | w | h | Format |
|---|---|---:|---:|---|
| `Info Popover Header` (new) | Horizontal container | 591 | 44 | Background None, padding 0 |
| title | Text | 591 | 44 | `How pay is measured`, Tableau Bold 12, white; inner padding left 16, top 12 |
| header line | Image `d2_popover_line_info.png` | 591 | 9 | Fit Image |
| body (the existing text object) | Text | 591 | 387 | Delete the first line ("How pay is measured") and the blank line after it; inner padding left 16, right 16, top 4; outer 0. R5: lead-ins Tableau Semibold 10 white `#FFFFFF`, body Tableau Book 10 `#B8C0CC`; words exactly as section 6 |

The Info popover has no ✕ today (the info button toggles it, and it closes when another picker opens). That stays; the header is a title only, full width.

**Front-to-back order** (Item hierarchy, top of the list is in front): `Info Popover`, `Group Popover`, `Period Popover`, then everything else as it is. Remove every parameter control you showed for testing (`p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen`, `p_ViewTab`) and any colour legend Tableau added (adding `Span Is Current` to Color can drop one).

### 14.8 Actions (43 Change Parameter + 20 Deselect = 63; today 39 + 20 = 59)

Dashboard > Actions. Every Change Parameter action: **Run action on Select**, clearing the selection **Keep current value**, source = the dashboard and the single sheet named, aggregation as offered. Names in **bold** are new or renamed.

| # | Name | Source sheet | Target parameter | Source field | Status |
|---:|---|---|---|---|---|
| 1 | Open period panel | Period Field | `p_PeriodOpen` | `Toggle Period Panel` | keep |
| 2 | Close group panel when period opens | Period Field | `p_GroupOpen` | `Close Panel` | keep |
| 3 | Close info when period opens | Period Field | `p_InfoOpen` | `Close Panel` | keep |
| 4 | Set span | Span List | `p_Span` | `Span Value` | keep |
| 5 | Set From | Period Panel | `p_From` | `from_month_end` | keep |
| 6 | Set To | Period Panel | `p_To` | `to_month_end` | keep |
| 7 | Close on pick | Period Panel | `p_PeriodOpen` | `Close Panel` | keep |
| 8 | Close on ✕ | Period Close | `p_PeriodOpen` | `Close Panel` | keep |
| 9 | **Browse view** (#3 action 13) | Rail View | `p_ViewTab` | `view_name` | **edit `Set view`**: target `p_View` to `p_ViewTab`; rename |
| 10 | **Apply group for All** (#3 action 14) | Rail View | `p_Group` | `Group Apply From View` | **edit `Set group from view`**: field `Default Group` to `Group Apply From View`; rename |
| 11 | **Apply view for All** (#3 action 32) | Rail View | `p_View` | `View Apply` | **new** |
| 12 | **Rail view opens group popover** | Rail View | `p_GroupOpen` | `Keep Group Panel Open` | **edit `Close panel on view change`**: field `Close Panel` to `Keep Group Panel Open`; rename |
| 13 | Close on view change | Rail View | `p_PeriodOpen` | `Close Panel` | keep |
| 14 | Close info on view change | Rail View | `p_InfoOpen` | `Close Panel` | keep |
| 15 | Open group panel | Group Field | `p_GroupOpen` | `Toggle Group Panel` | keep |
| 16 | **Open group on its view** (#3 action 31) | Group Field | `p_ViewTab` | `view_name` | **new** |
| 17 | Close period panel when group opens | Group Field | `p_PeriodOpen` | `Close Panel` | **fix (R2)**: the source field is empty in the saved file; pick `Close Panel` |
| 18 | Close info when group opens | Group Field | `p_InfoOpen` | `Close Panel` | keep |
| 19 | Set group | Group Panel | `p_Group` | `group_name` | keep |
| 20 | **Apply view on group pick** (#3 action 33) | Group Panel | `p_View` | `view_name` | **new** |
| 21 | Close panel on pick | Group Panel | `p_GroupOpen` | `Close Panel` | keep |
| 22 | Close panel on X | Panel Close | `p_GroupOpen` | `Close Panel` | keep |
| 23 to 25 | Set lens / Set cost / Set currency | the three toggles | `p_Lens`, `p_Cost`, `p_Currency` | as saved | keep |
| 26 to 27 | Set detail compact / Set detail expand | the two detail toggles | `p_Expand` | `Detail Pick` | keep |
| 28 to 35 | Reset from / to / view / group / lens / cost / currency / span | Reset | as saved | the `Default ...` calcs | keep |
| 36 | **Reset view tab** (#3 action 23b) | Reset | `p_ViewTab` | `Default View` | **new** |
| 37 to 39 | Reset group panel / Reset period panel / Close info on reset | Reset | `p_GroupOpen`, `p_PeriodOpen`, `p_InfoOpen` | `Close Panel` | keep |
| 40 | Reset detail | Reset | `p_Expand` | as saved | keep |
| 41 | Open info | Info Button | `p_InfoOpen` | as saved | keep |
| 42 to 43 | Close period when info opens / Close group when info opens | Info Button | `p_PeriodOpen`, `p_GroupOpen` | `Close Panel` | keep |

That is **4 new** (11, 16, 20, 36), **3 edited** (9, 10, 12), **1 fixed** (17), the rest kept: 39 + 4 = **43**. The 20 Deselect actions already cover every clickable sheet here (`Rail View`, `Group Field`, `Group Panel`, `Panel Close`, `Period Field`, `Span List`, `Period Panel`, `Period Close`, `Reset`, `Info Button`); nothing new is needed.

**How a rail view click now runs** (six actions on one click): 9 sets the tab; 10 and 11 set `p_Group` and `p_View` to the values they already hold, except on All, where they set Arcadia Systems and Company; 12 opens the Group popover (True) except on All, where it closes it (False); 13 and 14 close Period and Info. So Function, Sub-function, Department, Office and Country only browse. **A Group Panel click** fires 19 (group), 20 (the view that group belongs to) and 21 (close), so view and group arrive together. Six names exist in two views (Finance, Legal & Compliance, Marketing, Operations, People, Product), which is why 20 reads `view_name` from the clicked mark and `Group Is Current` tests both.

### 14.9 Expected values

Page numbers do not change (section 9 stands). What is new is *when* they change and what the popovers show. FY26, Loaded, Constant, Avg per FTE.

| State | Expect |
|---|---|
| Open, nothing clicked | Company: pay per FTE $110,063 to $113,664 (+$3,601, +3.3%); people 28,438 to 30,005. Rail `›` on All; no Group field (All has no groups) |
| Click **Function** in the rail | Group popover opens beside the rail, title `Select a function`, 8 names (3, 3, 2) from the top, none white. **The page does not move**: still $110,063 to $113,664, rail `›` still on All |
| Click **Commercial** | Popover closes; rail `›` on Function; Group field shows `Commercial`; $116,724 to $120,604, people 7,441 to 7,795; Growth by Region `Commercial +4.8% (7,441 \| 7,795)` |
| Click the Group field | Opens on the Function tab with Commercial white |
| Click **Sub-function** in the rail | Title `Select a sub-function`, 10 names (4, 4, 2); page still Commercial. `Marketing`, `Finance` and the other shared names are **not** white here, because the view in use is Function |
| Click **Office** | 35 names (12, 12, 11), the grid fills the popover to its footer |
| Department, click Accounting & Controllership | People 543 to 560 (same as #1) |
| Country, click India | People 6,672 to 6,967 (same as #1) |
| Click **All** in the rail, from any state | Applies at once: Company numbers back, popover closed, Group field hidden |
| Reset | FY26, All, Avg per FTE, Loaded, Constant, compact; popovers closed; a rail click on Function then opens on Function with nothing white |
| Period popover | Fiscal year: 4 by 4 block from the top, level with "Year over year". Year to date: 2 by 4. Quarter: 4 by 4. Month: 6 by 8. Quarter, then FY26 Q4: closes, people 29,618 to 30,005 (same as #1) |

### 14.10 Click tests

| # | Do | Expect |
|---:|---|---|
| 1 | Open Period | Left edge flush with the rail, top level with SELECT PERIOD; title 16 px in; line 16 px short of each edge; footer note; right corners round, left corners square against the rail |
| 2 | Fiscal year, Year to date, Quarter, Month | Rows start at the top each time and never float to the middle; Month fills six rows |
| 3 | Open Period, then click a rail view | Period closes, Group opens on that view |
| 4 | Open Info, then Period, then the Group field | One open at a time each time (17 fixed) |
| 5 | Rail, click Function | Popover opens, **page does not change**, rail `›` stays on All |
| 6 | Click Commercial | Closes, page changes to 7,441 / 7,795 people, rail `›` on Function |
| 7 | Click the Group field | Opens on the Function tab with Commercial white |
| 8 | Marketing check: Function, Marketing; then Sub-function in the rail | Marketing not white on Sub-function |
| 9 | Office, Department, Country, All | Values per 14.9; no click lands on a default group |
| 10 | Open the Group popover, ✕ | Closes; page and rail unchanged |
| 11 | Click every control, the title, the KPI band, a rail view twice | No blue box or outline stays; the second click on a rail view reopens the popover |
| 12 | Reset | Everything back; a rail click on Function opens with nothing white |
| 13 | Info | 44 px header with the title, line, body unchanged in words; the info button closes it |

### 14.11 My review of the saved .twb (before you publish)

Save the workbook, tell me, and I read the file. I check these and report pass or fail for each:

| Check | Expect |
|---|---|
| Parameters | **31**: the 30 now plus `p_ViewTab` (String, list of 6, Company); none named "(copy)" except the existing `p_To`; `kpi_` values unchanged |
| Parameter actions | **43** with the targets and fields in 14.8; **20** deselects; every action has a source field (17 fixed) |
| Dangling references | No `Calculation_` id without a definition; no red calc; `Group Panel` filter is `Group Grid Rows` |
| Arrows | No arrow glyph (U+2192) in any calc, label or text object a viewer can see (`Pair Label` fixed) |
| Stray colour legend | No colour-legend zone on the dashboard |
| Dashboard zones | Popover positions and sizes as 14.3; padding 0; radius 0 on the rail side; image objects present with Fit Image; `Group Panel` inside its popover under the line; popovers in front |
| Navy | The three popovers share one colour and match the rail (published: popovers `#13243A`, rail `#13223A`); no `#12213B` left |
| Controls | No parameter control (`p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen`, `p_ViewTab`) on the page |
| Sheet specifics | `Span List`, `Period Panel`, `Group Panel`: Text marks, continuous slot pill, axis 0 to 12 or 0 to 24, reversed, header hidden; `Rail View` Detail has `Group Apply From View`, `View Apply`, `Keep Group Panel Open` and **`Close Panel`**, and no `Default Group`; `Group Heading 2` shows `Tab Title` |

### 14.12 Order of work, then publish and repo

1. Mac: backup (14.4).
2. Parameter and calcs (14.5), checkpoint P1.
3. Sheets (14.6), checkpoint P2.
4. Dashboard (14.7), one popover at a time; click tests 1 and 2 after Period, 13 after Info.
5. Actions (14.8), then click tests 3 to 12.
6. Save, send me the file for 14.11.
7. Publish: Reset, close popovers, compact waterfall, hide all sheets, **File > Save to Tableau Public As...** `Arcadia Compensation Walk` (same name keeps the URL). Check the published page with the 14.10 table and section 10.
8. Repo: new screenshot to `docs/images/` for the README row; the case-study README mentions the browse-first picker; this section's status line.

### 14.13 What this section does not touch

The data sources and Custom SQL; the waterfall, KPI cards, drivers, Growth by Region, map and tie-out; the rail's items, order and sizes; the Group Block's visibility rule; the toggles; the other `Reset` defaults (only `p_ViewTab` is added); Dashboard #1 (its own section 14); and any number on the page.
