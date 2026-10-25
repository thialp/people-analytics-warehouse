# Release 3 rebuild: Dashboard #1, Headcount & FTE Walk

Step-by-step rebuild of [arcadia_headcount_fte_walk](https://public.tableau.com/app/profile/thialp/viz/arcadia_headcount_fte_walk/Dashboard) on the release 3 data, so it works and reads like Dashboard #2 (Compensation Walk), keeps its own **top bar**, and shows **the same numbers** wherever the two dashboards show the same thing. Arcadia Systems is fictional and all data is synthetic.

Companion guide: [Dashboard #2 rebuild](../compensation-walk/release_3_rebuild_dashboard_2.md). Section 0 is identical in both; you can import sheets, calcs and parameters from one workbook to the other wherever a step says so.

| | Today (published) | After this rebuild |
|---|---|---|
| Data | Six CSVs, release 1 extract (13,201 closing) | One Custom SQL (`custom_sql_headcount_fte_walk.sql`, release 3, 597,097 rows) + the Region Walk (`custom_sql_region_walk.sql`, 26,520 rows) for the pickers and the Compensation Walk tie-out |
| Period | Two month dropdowns (From / To) | **Period button + popover**, the same 88 periods as Dashboard #2 (Fiscal year, Year to date, Quarter, Month) |
| Who | Company only | **View + group button + popover**: Company, Function, Sub-function, Department, Country (same names and lists as #2) |
| Measure | Headcount \| FTE toggle (now identical: every employee is 1.0 FTE) | **Employees \| Contingent \| Total** toggle |
| Buttons | Dropdowns, native Show/Hide info button | Image buttons on worksheets (no hover dot, no highlight), **Reset**, info button with a tooltip |
| Waterfall | Opening, Hires, Voluntary, Involuntary, Closing | Compact and **Expand / Collapse** like #2, counted in **drivers** |
| Population | Includes the 9 executive officers | **Excludes them, like #2**, so Opening, Closing and People match to the person |

## Where we are (updated Oct 17, 2026)

**Dashboard #1 is rebuilt and published:** [https://public.tableau.com/app/profile/thialp/viz/arcadia_headcount_fte_walk/Dashboard](https://public.tableau.com/app/profile/thialp/viz/arcadia_headcount_fte_walk/Dashboard). Sections 1 to 8 and 10 are done: top bar and popovers, waterfall (Summary | By driver), five KPI cards with hover tooltips, Trend and Turnover, layout aligned to the KPI grid. The published page was checked against section 11 for Employees, Contingent and Total (FY26 and FY25 Q3), Commercial and Finance; every figure ties to the cards, waterfall, trend and Dashboard #2.

**Popover carryback (Oct 24, 2026): built, reviewed against 14.11 and published** at the same URL. The popovers now have the two improvements proven on Dashboard #3: organised popovers (fixed row slots, one shared frame) and a Group popover that browses first and applies on a group click. All click tests passed. What changed from the plan while building is in [14.14](#1414-as-built-and-what-to-carry-forward); nothing else on the page changed.

**Open follow-ups (small):** (1) `Period Name` still prints "Jan 2025 – Mar 2025" for a quarter while the Period field says "FY25 Q3"; see 8.5 for the quarter branch. (2) Apply the same toggle, KPI hover tooltips and type rule to Dashboard #2. (3) Cleanup of leftover calcs, sheets and actions: see section 13.

## Checkpoints

Save the workbook and compare numbers at each checkpoint before going on. If a number is off, fix it there; later sections build on it.

| # | Where | You have | Check |
|---:|---|---|---|
| 1 | Sections 1 and 2.1 | Files in place, backup made, Headcount Walk on release 3 Custom SQL, old calcs deleted | 597,097 rows; scratch check 30,014, then 30,005 |
| 2 | Sections 2.2 and 2.3 | Region Walk source and the `Link` blend | 26,520 rows; blend shows the green link on `Link` only |
| 3 | Sections 3 to 5 | Parameters, core calcs, picker calcs | FY26 Company: 28,438 to 30,005 people |
| 4 | Sections 6 and 7 | Top bar, popovers, actions | Period, Group, Workforce and Reset change the page; no highlight on any click |
| 5 | Section 8 | Waterfall, KPI cards, trend, turnover, info popover | Every figure in section 11 |
| 6 | Sections 9 to 12 | Tie-out note, layout, test, publish | Section 11 table in full, then Tableau Public |

---

## 0. Shared rules for both dashboards (identical in the #2 guide)

### 0.1 What must match, and what cannot

Checked in DuckDB on the release 3 warehouse: for **all 88 periods × every group of the five shared views (6,222 combinations)**, Dashboard #1's opening and closing equal Dashboard #2's to the person, once both exclude the executive officers and both use the same two month-end dates. Region Walk hires, exits and transfers equal Dashboard #2's walk lines in all 9,126 period × group combinations.

| Number | Dashboard #1 | Dashboard #2 | Rule |
|---|---|---|---|
| Opening, closing, net change, % change | KPI card 1, waterfall levels | People card, Growth by Region headline | **Identical** |
| Joined in the period | KPI card 2 (5,235 = 4,965 hires + 270 conversions) | Tie-out note under the waterfall | **Identical** (same sentence in both) |
| Hires still here at the end | Tie-out note under the waterfall | Hires driver (4,790), Top drivers | **Identical** (same sentence in both). In a group view the note counts the hires who joined **this** group (Hires reason `New Hire`) and names the ones who joined elsewhere and moved in separately (Dashboard #2 guide section 8 item 9) |
| Leavers | Every leaver (3,668) | Exits from the opening team (3,223) | Different by definition, explained in both info panels |

**Why the hire counts differ, and why both are right.** Dashboard #1 counts **events** month by month: everyone who joined. Dashboard #2 compares **two snapshots**: pay can only be priced for someone present on a date, so a person hired in October who left in March is in neither snapshot. FY26, Company: 5,235 joined, 445 of them left again before Jun 30, 2026, so 4,790 were still here. The same 445 explain the leavers: 3,668 − 445 = 3,223 exits. For a group (a function, a country) the gap also includes people who joined and then changed team; and the Hires bar also holds people who joined **another** team and moved in (grouped where they are on the closing date), which the note counts separately so its two numbers are one population (Dashboard #2 guide section 8 item 9). Neither dashboard is changed to the other's definition: turnover needs every leaver, and a pay walk can only price people it can see. Instead **both show both numbers in one identical sentence** (Dashboard #1 guide section 9, Dashboard #2 guide section 7), so a reader never sees two unexplained hire counts.

### 0.2 Population

| Rule | Dashboard #1 | Dashboard #2 |
|---|---|---|
| Executive officers (CEO + 8 function heads, all in department `D-901` Office of the CEO) | **Excluded** (new: `Department Id <> "D-901"` inside `In Range`) | Excluded (in the SQL) |
| Worker type | Employees by default; Contingent and Total on the toggle | Employees only. When #1 shows Contingent or Total, the tie-out note says the Compensation Walk covers employees |
| Office view | Not offered (the headcount walk is by department × country, not office) | Offered |

### 0.3 One vocabulary

| Concept | Word on both dashboards | Not |
|---|---|---|
| The bars between Opening and Closing | **drivers** ("By driver", "Largest of the 9 drivers behind the waterfall") | steps |
| The compact bars | **groups** (the Summary view) | |
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
| A title could be selected | Titles drawn as **text sheets** have marks, so a click selects them | Same deselect action on **every** text sheet (titles, subtitles, captions, headings, KPI band); tooltips off on the sheets themselves; the KPI card tooltips come from the five `KPI Hover` sheets (8.2c) |

Click flow after the fix: the click fires the parameter action, then the self filter action clears the selection in the same instant. On Tableau Public a brief flash can remain; nothing stays highlighted.

**Shape files (new, in the repo):** `docs/brand/build/make_button_shapes.py` writes these to `docs/brand/shapes/Arcadia/` (preview: `docs/brand/build/button_preview.png`). Install once: copy the PNGs into `Documents/My Tableau Repository/Shapes/Arcadia`, then on any sheet Marks > Shape > **Edit Shape... > Reload Shapes**. Assign shapes by hand (Assign Palette goes alphabetically, not by name).

| File | Size on the dashboard | Used for |
|---|---|---|
| `fld_top.png` | 180 × 36 | #1 Period and Group fields (white capsule, 32 tall, drawn 2 px below the centre so the label sits optically centred) |
| `fld_rail.png` | 200 × 30 | #2 Period and Group fields (`#E4E3DD`, rounded like the toggles) |
| `seg_worker_employees_on/off`, `seg_worker_contingent_on/off`, `seg_worker_total_on/off` | 80 × 32 each | #1 Workforce toggle (capsule `#243A57`) |
| `btn_reset_top_label.png` | 184 × 32 | #1 Reset (outlined capsule: arrow + "Reset to default view") |
| `btn_reset_top.png` | 32 × 32 | Spare: arrow only, for a narrow header |
| `btn_reset_rail.png` | 188 × 30 | #2 Reset (outlined button, as published) |
| `btn_close.png` / `btn_close_light.png` | 16 × 16 | The ✕ on every popover (slate on white / mist on navy) |
| `info_open`, `info_close` (existing) | 32 × 32 | #1 info button |
| `rail_info_open`, `rail_info_close` (existing) | 16 × 16 | #2 info button |
| `btn_expand_icon`, `btn_collapse_icon` (existing) | 16 × 16 | Expand / Collapse on both |

**Image quality (rebuilt Oct 17, 2026).** Every generator now draws at 8x supersampling, shrinks once with LANCZOS and applies a light unsharp mask, and the delivered size is set in one place, `docs/brand/build/shape_quality.py` (`SHAPE_SCALE`, default **3**: an 80 × 32 cell is delivered 240 × 96, the 180 × 32 field 540 × 96). Dashboard sizes do not change. Why 3 and not "as big as possible": Tableau scales a shape to the mark size with a plain bilinear resample, so a source much larger than the screen size aliases (jagged edges, uneven letters). A test that mimics that resample, on the real header shapes, gave the lowest error at 3x across the screen sizes people use (1x to 3x device scale); 2x was best only on a 1x screen, 8x was worst. To try another size: `SHAPE_SCALE=2 python3 docs/brand/build/make_button_shapes.py` (also `make_toggle_shapes.py`, `make_detail_toggle_shapes.py`, `make_rail_toggle_shapes.py`, `make_rail_info_shapes.py`), then re-copy the PNGs. Outlines are drawn on whole pixels so thin lines stay sharp.

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

### 1.1 Warehouse and validation

```bash
cd ~/GitHub/people-analytics-warehouse
git pull
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker compose up -d
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/10_validate_headcount_fte_walk.sql
```

Expected: `Headcount & FTE walk Custom SQL returned 597097 rows in N seconds`, then every check **PASS** (full expected output: `docs/projects/contingent-workforce/sql_server_release_3_run.md`, step 4). The script reports FY26 opening **28,447** and closing **30,014**: it counts the 9 executive officers. The dashboard shows **28,438** and **30,005** after section 4 removes them, the same as Dashboard #2.

### 1.2 Files on the Mac

Everything lives under `~/Documents/Tableau/Tableau Public/ArcadiaHR/`:

```
Arcadia Headcount/
  Arcadia Headcount FTE Walk.twb                           <- the file you edit (Dashboard #1)
  Arcadia Headcount FTE Walk - release 2 backup.twb        <- the backup; never open it to edit
  Arcadia Headcount FTE Walk - published release 2.twbx    <- the packaged copy of what is on Tableau Public
  Data Source CSV/  Images and Buttons/  KPI Cards/        <- leave where they are (the workbooks read them by relative path)
  _archive/2026-10-15/                                     <- older dated versions
Arcadia Compensation/  Arcadia Cost Bridge/  Reference/  Custom SQL - Release 3/  SQL/  Figma/
```

1. Copy `tableau/custom_sql_headcount_fte_walk.sql` and `tableau/custom_sql_region_walk.sql` into `Custom SQL - Release 3/02 Headcount & FTE Walk/`.
2. Copy the 12 new PNGs from `arcadia_button_shapes.zip` (sent with this guide) into `~/Documents/My Tableau Repository/Shapes/Arcadia/`. Once they are in the repo, `python3 docs/brand/build/make_button_shapes.py` regenerates them (expected `wrote 12 files`).
3. The backup is the copy named `... - release 2 backup.twb`. If you ever need to redo it: close Tableau, copy `Arcadia Headcount FTE Walk.twb` in Finder to a new name, and open only the original. Every step below is on `Arcadia Headcount FTE Walk.twb`.

---

## 2. Data sources

### 2.1 The walk: release 3 Custom SQL (Checkpoint 1)

The workbook is still on the six CSVs (the data source is named `mart_headcount_fte_walk+`), so add the new source first and then replace the old one. Close every other workbook first.

1. **Add the new source.** Data > New Data Source > **Microsoft SQL Server**: the same connection as Dashboard #2 (server `localhost`, database `ArcadiaHR`, user `sa`, the trust-certificate setting from `tableau/sqlserver_trust_local_certificate.tdc`). Drag **New Custom SQL** to the canvas, paste the whole of `custom_sql_headcount_fte_walk.sql`, OK. Rename the source **Headcount Walk**. Paste from the clipboard (`cd ~/GitHub/people-analytics-warehouse && git pull && grep -c worker_type tableau/custom_sql_headcount_fte_walk.sql` must print 5 or more, then `pbcopy < tableau/custom_sql_headcount_fte_walk.sql`) so you are sure it is the release 3 query. If `worker_type` and `walk_step` are missing from the Data pane afterwards, the source still has the release 2 query: Data Source tab > right-click the Custom SQL table > Edit Custom SQL Query, select all, paste, OK, Extract > Refresh.
2. **Check types** on the Data Source tab: `Month End Date` and `Prior Month End Date` **Date**; `Grade` and `Fiscal Year` **String**; `Headcount` whole number, default aggregation Sum. Two new fields arrive: **Worker Type** (Employee, Contingent) and **Walk Step** (Opening, Joined, Left, Moved out, Moved in, Converted, Closing).
3. **Replace Data Source.** Data > **Replace Data Source...**: Current = `mart_headcount_fte_walk+`, Replacement = **Headcount Walk**, OK. Tableau moves every calc, parameter reference, alias and format to the new source and remaps fields by name.
4. **Replace References for the fields that stayed red.** Replace Data Source maps by name. If the new source shows its fields in snake_case (`headcount`, `fte`, `month_end_date`) while the old calcs point at `Headcount`, `Fte`, `Month End Date`, nothing remaps and the calcs that use them keep a red **!**. Do this **before** deleting anything. For each row: Data pane > right-click the **old red field** > **Replace References...** > pick the **new field** > OK.

   | Old red field | New field | Used by |
   |---|---|---|
   | Month End Date | `month_end_date` | `In Range`, every `K` and `WF` calc, the month lists, Trend |
   | Movement Category | `movement_category` | every measure calc, the waterfall columns, Trend filter |
   | Movement Order | `movement_order` | waterfall column sort |
   | Movement Reason | `movement_reason` | `K Promotions`, `WF Promos` |
   | Headcount | `headcount` | every headcount measure |
   | Fte | `fte` | every FTE measure |
   | Function Name | `function_name` | Turnover by function, `TO Top Function` |

   Do **not** replace `Part Time Headcount`: it has no release 3 field. After the seven replacements the `K`, `WF` and other calcs that are not in step 5's list lose their red **!**. If one stays red, hover it: Tableau names the missing field; replace that one the same way (the full old-to-new list is in [release_2_replace_references.md](../workforce-planning/release_2_replace_references.md) section 1.3).
5. **Delete the calcs that no longer apply.** **Part Time Headcount turns red** (the column is gone in release 3). Delete these calcs (Data pane, right-click > Delete; Tableau lists anything still using them): `K Close PT`, `K Part Time Gap`, `K Gap T`, `KPI 2 Note`, `TT Part Time`, `TT Level PT`, `Show Category`, `WF FTE Chg`, `WF FTE Chg Str`, `WF FTE Open`, `WF FTE Close`, `WF FTE Hires`, `WF FTE Leavers`, `WF FTE Open Str`, `WF FTE Close Str`, `WF FTE Hires Str`, `WF FTE Leavers Str`, `WF FTE Net Str`, `TT Bar T`, `K FTE T`. Their sheets get rebuilt below. If Tableau says a field is still in use, find it with the Data pane search and delete it.
6. **Month lists.** Parameters `Start Month` and `End Month` are replaced in section 3; leave them for now.
7. **Extract.** Data Source tab > Connection **Extract**, Hide All Unused Fields, Extract Data. Expected about **597,097** rows (a minute or two).
8. **Close the CSV source** only when no field shows a red **!** that you still need (right-click `mart_headcount_fte_walk+` > Close).
9. **Scratch check** (new sheet, delete after): filter `Movement Category` = Closing, `Month End Date` = 6/30/2026, `Worker Type` = Employee: SUM(Headcount) **30,014**. Add `Department Id` ≠ D-901: **30,005**. Put `Worker Type` on Rows to see both: Employee **30,005** (without D-901) and Contingent **11,941**.

**Checkpoint 1 passes when:** the extract has 597,097 rows, the types match step 2, the seven fields in step 4 are replaced with no red **!** left on the calcs you keep, no calc from step 5 remains, and the scratch check gives 30,014 and then 30,005. Save the workbook (Cmd+S).

### 2.2 The Region Walk (pickers + tie-out)

1. **Data > New Data Source > Microsoft SQL Server**, same connection (`localhost`, `ArcadiaHR`, `sa`, Require SSL off). Drag **New Custom SQL**, paste `custom_sql_region_walk.sql`, OK.
2. Rename the source **Region Walk**. Extract (Hide All Unused Fields first). Expected **26,520** rows.
3. Why this source in Dashboard #1: it holds the **same 88 periods** and the **same group names** as Dashboard #2, so the pickers offer exactly #2's choices; and its `Hires` is exactly #2's Hires line (checked for all 9,126 period × group combinations), which the tie-out note needs.

### 2.3 Blend link (for the tie-out note only)

1. In **Headcount Walk**: calc `Link` = `"Arcadia"`.
2. In **Region Walk**: calc `Link` = `"Arcadia"`.
3. **Data > Edit Blend Relationships...**: Primary `Headcount Walk`, Secondary `Region Walk`. Choose **Custom**, remove every pair Tableau proposes (for example `Region`, or the calc `Group Name` against `group_name`), and add only `Link` ↔ `Link`.

**Checkpoint 2 passes when:** `Region Walk` extracts 26,520 rows and the blend has only the `Link` pair. Save (Cmd+S).

---

## 3. Parameters

Rename where it says Rename (right-click > Rename): Tableau updates every calc that uses the parameter, and the meaning is kept or changed exactly as noted.

| Parameter | Action | Type | Allowable | Current | Note |
|---|---|---|---|---|---|
| `p_From` | **Rename** `Start Month` | Date | **All** | **6/30/2025** | Meaning changes: it is now the **opening month-end** (as on #2), not the first month. Section 4 edits the calcs that used it |
| `p_To` | **Rename** `End Month` | Date | **All** | 6/30/2026 | Same meaning (closing month-end) |
| `p_Worker` | **Rename** `Measure`, then Edit | String | List: `Employees`, `Contingent`, `Total` | Employees | Replaces Headcount / FTE |
| `p_Span` | New | String | List: `Fiscal year`, `Year to date`, `Quarter`, `Month` | Fiscal year | As #2 |
| `p_View` | New | String | List: `Company`, `Function`, `Sub-function`, `Department`, `Country` | Company | #2's list without Office |
| `p_Group` | New | String | All | `Arcadia Systems` | Stores the group **name**, as #2 |
| `p_Expand` | New | Boolean | | False | Compact / expanded waterfall |
| `p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen` | New | Boolean | | False | Popovers |

**After renaming `Measure` to `p_Worker`**, every calc that still tests `"Headcount"` or `"FTE"` silently takes the wrong branch (no red field warns you). Rewrite or delete them: `KPI 3 Title`, `KPI 3 Note`, `KPI 4 Note`, `K Hires Show`, `WF Title`, `Trend Title` (new formulas in section 8), and these four, which become constants: `TT Unit` = `"people"`, `TT Noun` = `"headcount"`, `TT Open Ref` = `[WF Open]`, `TT Close Ref` = `[WF Close]`; delete `Measure Option`, `Option State`, `Toggle Shape`, `K Hires FTE`, `K Leavers Vol FTE`, `K Hires FTE Str`, `K Vol FTE Str` with the old toggle sheet. Data pane search for `Measure` and `Fte` finds any left.

**Spell the values exactly.** `p_View` must hold `Company` and `p_Group` must hold `Arcadia Systems`, character for character: `Group Name` compares them as text, and one wrong letter makes `In Group` false for every row, so every sheet goes blank with no error. If a sheet is blank after section 4, put `In Period`, `Officers Out`, `In Group` and `Worker In Scope` on Rows with `SUM(Headcount)` on Text: the test that has no True row is the one to fix. Your fields are in snake_case on this source (`department_id`, `month_end_date`, `worker_type`): pick fields from the Data pane instead of typing the guide's spelling.

"All" for the dates matters (lesson from #2): a List silently rejects month-ends that are not on the list, and the action then changes only one end of the period.

**Faster:** in the #2 workbook select `p_Span`, `p_View`, `p_Group`, `p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen` in the Data pane > right-click > **Copy**; in #1, right-click the Data pane > **Paste**. Then edit `p_View` and remove `Office`. If Paste is greyed out, create them by hand from the table.

---

## 4. Core calculations (Headcount Walk source)

The scope goes **inside `In Range`**, not in filters: every KPI, waterfall, title and tooltip calc already starts with `IF [In Range]`, so they all inherit it at once, and FIXED calcs (which ignore normal filters) stay correct.

```
// Officers Out   (the 9 executive officers sit in D-901 Office of the CEO; Dashboard #2 leaves them out)
[Department Id] <> "D-901"
```
```
// Worker In Scope
CASE [p_Worker]
    WHEN "Employees"  THEN [Worker Type] = "Employee"
    WHEN "Contingent" THEN [Worker Type] = "Contingent"
    ELSE TRUE
END
```
```
// Group Name   (the same names as Dashboard #2's group_name in each view)
CASE [p_View]
    WHEN "Company"      THEN "Arcadia Systems"
    WHEN "Function"     THEN [Function Name]
    WHEN "Sub-function" THEN [Sub Function]
    WHEN "Department"   THEN [Department Name]
    WHEN "Country"      THEN [Country Name]
END
```
```
// In Group
[Group Name] = [p_Group]
```
```
// In Period   (months after the opening month-end, up to the closing month-end)
[Month End Date] > [p_From] AND [Month End Date] <= [p_To]
```
```
// In Range   (EDIT the existing calc: replace its whole formula)
[In Period] AND [Officers Out] AND [In Group] AND [Worker In Scope]
```
```
// Is Opening Row   (the walk's Opening line of the first month opens on p_From)
[Movement Category] = "Opening" AND [Prior Month End Date] = [p_From]
```
```
// Is Closing Row
[Movement Category] = "Closing" AND [Month End Date] = [p_To]
```
```
// Walk Value   (EDIT)
IF [In Range] THEN
    CASE [Movement Category]
        WHEN "Opening" THEN IIF([Is Opening Row], [Headcount], 0)
        WHEN "Closing" THEN IIF([Is Closing Row], [Headcount], 0)
        ELSE [Headcount]
    END
END
```
```
// Emp In Range   (turnover is always employees, whatever the toggle says)
[In Period] AND [Officers Out] AND [In Group] AND [Worker Type] = "Employee"
```
```
// Selected Value   DELETE (FTE equals headcount). Replace any use by [Headcount].
// K Valid          EDIT:  [p_From] < [p_To]      (always true: the picker only offers real periods)
```

**Edit these existing calcs**, replacing the old opening and closing tests:

| Calc | Old piece | New piece |
|---|---|---|
| `K Open HC`, `WF Open`, `TT Level HC` | `[Movement Category] = "Opening" AND [Month End Date] = [p_From]` (after the rename) | `[Is Opening Row]` |
| `K Close HC`, `WF Close`, `TT Level HC` | `[Movement Category] = "Closing" AND [Month End Date] = [p_To]` | `[Is Closing Row]` |
| `Average Headcount`, `Voluntary Leavers`, `Involuntary Leavers`, `Hire Rate (annualized)` and its parts | `[In Range]` | `[Emp In Range]` |
| `Months in Range` | `COUNTD(IF [In Range] THEN ...` | `COUNTD(IF [In Period] THEN [Month End Date] END)` |
| `TT Months` | `{ FIXED : COUNTD(IF [In Range] ...` | `{ FIXED : COUNTD(IF [In Period] THEN [Month End Date] END) }` |

**Scratch check** (Company, FY26, Employees): `SUM([Walk Value])` with `Movement Category` on Rows: Opening 28,438 · Hires 4,965 · Voluntary 2,942 (−) · Involuntary 726 (−) · Internal Moves Out 3,633 (−) · Internal Moves In 3,633 · Conversions 270 · Closing 30,005.

---

## 5. Pickers (Region Walk source)

### 5.1 Calcs on Region Walk

Named exactly as on #2's walk source, so the sheets and actions read the same.

```
// pair_type   (Region Walk has no pair_type column; same rule as the SQL's CASE)
IF [months_between] = 1 THEN "Month over Month"
ELSEIF [months_between] = 3 THEN "Quarter over Quarter"
ELSEIF [months_between] = 12 THEN "Year over Year"
ELSEIF MONTH([from_month_end]) = 6 THEN "Fiscal Year to Date"
ELSE "Custom Range" END
```
```
// to_fiscal_quarter   ("FY26 Q4")
LEFT([to_fiscal_period], 4) + " Q" + STR(INT((INT(RIGHT([to_fiscal_period], 2)) - 1) / 3) + 1)
```

Then copy these from [rail_controls_build.md](../compensation-walk/rail_controls_build.md) Part 4.2 **unchanged** (they reference the names above): `Pair Label`, `Span Type`, `Period In Span`, `Period Is Current`, `Period Key`, `Pair Name`, `Toggle Period Panel`, `Period Rows`, `Period Col`, `Period Row`, `Span Label`, `Span Value`, `Span Order`, `Span Display`, `Close Panel` (= FALSE), `zzTrue` (= TRUE), `zzFalse` (= FALSE). Copy from the #2 workbook (select > Copy > Paste on Region Walk) or type them.

Group calcs (from [rail_group_picker_build.md](../compensation-walk/rail_group_picker_build.md) 2.2, plus the view list):

```
// Group In View        [view_name] = [p_View]
// Group Is Current     [group_name] = [p_Group]
// Toggle Group Panel   NOT [p_GroupOpen]
// Pick Rows            INT((SIZE() + 2) / 3)
// Pick Col             INT((INDEX() - 1) / [Pick Rows])
// Pick Row             (INDEX() - 1) % [Pick Rows]
// View Offered         [view_name] <> "Office"
// View Display         IF [view_name] = [p_View] THEN "› " + [view_name] ELSE [view_name] END
// Default Group        { FIXED [view_name] : MIN([group_name]) }      (Company gives "Arcadia Systems")
// Panel Title
"Select " + CASE [p_View]
    WHEN "Function" THEN "a function" WHEN "Sub-function" THEN "a sub-function"
    WHEN "Department" THEN "a department" WHEN "Country" THEN "a country"
    ELSE "a view" END
// Period Field Text    [Pair Name]                    (the chevron is in the label, below)
// Group Field Text     IF [p_View] = "Company" THEN "All organizations" ELSE [p_Group] END   (display only; p_Group keeps the value "Arcadia Systems")
```

Note `group_name` and `view_name` here are Region Walk's own columns (`group_name`, `view_name`), not the Headcount Walk calc of the same caption.

### 5.2 The two tie-out calcs (Region Walk)

```
// RW Is Current
[from_month_end] = [p_From] AND [to_month_end] = [p_To] AND [view_name] = [p_View] AND [group_name] = [p_Group]
```
```
// RW Hires Still Here   (= Dashboard #2's Hires for the same period and group)
SUM(IF [RW Is Current] THEN [hires] END)
```
```
// RW Hires Moved In     (of those, hired into another group of this view and moved in; 0 for Company)
SUM(IF [RW Is Current] THEN [hires_joined_elsewhere] END)
```
```
// RW Hires Joined Here  (joined this group and still in it: never more than TO Joined, test 79)
[RW Hires Still Here] - [RW Hires Moved In]
```

---

## 6. Top bar (header), built like #2's rail controls

### 6.1 Period Field (test the image-field pattern here first)

Sheet `Period Field`, source **Region Walk**:

1. Marks: **Shape**. Click the Shape card > **More Shapes...** > palette `Arcadia` > click `fld_top`. Nothing goes on Shape: one mark, one image.
2. Label: `Period Field Text`. Label editor text: `<Period Field Text>  ▾` (two spaces, then ▾). Tableau Semibold 9, navy `#13233A`, Alignment **Center**, Middle. Check **Allow labels to overlap other marks**.
3. Size: drag the Size slider to the **maximum**. Fit: **Standard**.
4. Detail: `Toggle Period Panel`, `Close Panel`, `zzTrue`, `zzFalse`, `from_month_end`, `to_month_end`.
5. Filter: `Period Is Current` = True (one mark).
6. Format > Shading: Worksheet and Pane **None**. Format > Lines: all None. Hide headers.
7. Tooltip: `Choose the period` (Tableau Book 9), uncheck Include command buttons.
8. Dashboard item: floating, **Entire View**, background None, inner padding 0.

Test: the field shows `FY26 · Jun 25 → Jun 26  ▾` on a white capsule filling 180 × 32. Hover: a thin outline around the box, **no square**. If the shape will not fill the cell, set the item to Fit **Standard** on the dashboard and widen the sheet's cell (Format > Cell size > Taller/Wider); if it still will not, use the fallback in 0.4 and tell me what you see.

### 6.2 Group Field

Same as 6.1 with `Group Field Text`, Detail `Toggle Group Panel`, `Close Panel`, `zzTrue`, `zzFalse`; filter `Group Is Current` = True **and** `Group In View` = True. Tooltip `Choose who to look at`. When the view is Company it reads `All organizations  ▾` (a visitor who has never heard of Arcadia gets a clear label; the stored value stays `Arcadia Systems` so no calc changes) (it never disappears, so the bar never jumps).

### 6.3 Workforce Toggle (replaces Measure Toggle)

Source **Headcount Walk** (it has three rows to draw three buttons):

```
// Worker Option   (three data rows give the three buttons)
CASE [Walk Step] WHEN "Opening" THEN "employees" WHEN "Joined" THEN "contingent" WHEN "Left" THEN "total" END
// Worker Pick     CASE [Worker Option] WHEN "employees" THEN "Employees" WHEN "contingent" THEN "Contingent" WHEN "total" THEN "Total" END
// Worker State    IF [Worker Pick] = [p_Worker] THEN "on" ELSE "off" END
// Worker Shape    "seg_worker_" + [Worker Option] + "_" + [Worker State]
```

1. Duplicate the old `Measure Toggle` sheet, rename **Workforce Toggle**. Replace `Measure Option` on Columns with `Worker Option`; manual sort employees, contingent, total. Filter `Worker Option` excludes Null.
2. Shape: `Worker Shape`; assign the six values by hand to the six `seg_worker_*` files.
3. Detail: `Worker Pick`, `Close Panel`, `zzTrue`, `zzFalse`. Remove `Measure Option`.
4. Tooltip off (the three words are in the images).
5. Dashboard item 240 × 32, background `#243A57`, corner radius 16, padding 0.

### 6.4 Reset

Sheet `Reset`, source **Region Walk** (any one row):

| Calc | Formula |
|---|---|
| `Default From` | `#2025-06-30#` |
| `Default To` | `#2026-06-30#` |
| `Default Span` | `"Fiscal year"` |
| `Default View` | `"Company"` |
| `Default Group All` | `"Arcadia Systems"` |
| `Default Worker` | `"Employees"` |
| `Default Expand` | `FALSE` |

1. Marks **Shape** = `btn_reset_top_label` (the wide capsule with the words; not `btn_reset_rail`, which is #2's, and not `btn_reset_top`, the arrow-only spare); size max; filter `Period Is Current` = True and `view_name` = "Company" (one mark).
2. Detail: every `Default ...` calc, `Close Panel`, `zzTrue`, `zzFalse`.
3. Tooltip: `Reset to default view` (Semibold 9).
4. Shading None; item **184 × 32**.

### 6.5 Info Button

Sheet `Info Button`, source **Region Walk**:

```
// Info Shape    IF [p_InfoOpen] THEN "info_close" ELSE "info_open" END
// Toggle Info   NOT [p_InfoOpen]
```
Marks Shape = `Info Shape` (assign `info_open`, `info_close`), size max, one mark (same filters as Reset), Detail `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse`. Tooltip: **Click here for more information on how to read this page**. Item 32 × 32.

Delete the old native Show/Hide button and its `Info Panel` container after section 8.4 is built.

### 6.6 Page Title (a sheet, so the subtitle can follow the selection)

Source Headcount Walk.

```
// Worker Words   CASE [p_Worker] WHEN "Employees" THEN "employees" WHEN "Contingent" THEN "contingent workers" ELSE "employees and contingent workers" END
// TT Open Day    LEFT(DATENAME('month',[p_From]),3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))
// TT Close Day   LEFT(DATENAME('month',[p_To]),3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))
```
`TT Open Day` and `TT Close Day` are used here, in 8.2 and in section 9; create them now (both on Headcount Walk) and skip them there.

```
// Page Subtitle  the two dates the whole page compares (the period is no longer named in the header)
"Opening " + [TT Open Day] + " → Closing " + [TT Close Day]
```
The header carries the **dates**, not "data as of": every card, the waterfall and the charts use this period, so it belongs next to the Period field. "Data as of Jun 30, 2026" moves to the footnote (section 10, item 19). The group and the workforce type are already visible in the View field and the Workforce toggle, so the subtitle does not repeat them.
(Optional later: read the as-of date from Region Walk's `report_as_of_date` with the blend, as #2 does.)

Text mark; Text: line 1 `Headcount & FTE Walk` Tableau Bold 18 white; line 2 `<Page Subtitle>` Tableau Book 8 `#C9D1DC` (the longest text, "Opening Mar 31, 2024 → Closing Mar 31, 2025", fits at this width; anything longer, such as a "data as of" clause, clips). Detail `zzTrue`, `zzFalse`, `Title Tip`. Shading None. Dashboard item 285 × 58, Entire View. Two lines only (title 18 plus the dates line); a third line forces the title down to 14, which weakens the header.

**Tooltip "How to read this page"** (the default tooltip prints raw field names and repeats the subtitle; replace it). `TT Open Day` and `TT Close Day` are the two calcs just above:

```
// Title Tip
"Showing: " + (IF [p_View] = "Company" THEN "all of Arcadia" ELSE [p_View] + " · " + [p_Group] END) + " · " + [Worker Words] + CHAR(10) +
"Opening + joined − left ± moves = closing, reconciled to the month-end headcount." + CHAR(10) +
"Compares " + [TT Open Day] + " and " + [TT Close Day] + ". Every joiner and every leaver in between is counted, month by month." + CHAR(10) +
"Executive officers excluded." +
(IF [p_Worker] = "Employees" THEN "" ELSE CHAR(10) + "Contingent workers are contractors held in the vendor system; a conversion moves one person from Contingent to Employees, so Total does not change." END)
```
Worksheet > Tooltip: bold line **How to read this page** (Semibold 10 navy), `<Title Tip>`, then "Click ⓘ in the top bar for the full definitions." (Book 9 slate). Keep the deselect action (7.4).

### 6.7 Headings over the fields

Three dashboard **Text** objects (static text is not selectable), Tableau Bold 10, `#B8C4D6`, 180 × 14: `SELECT PERIOD`, `SELECT VIEW`, `SHOW`. Same words as #2's rail headings.

### 6.8 Header layout (1400 wide, band 76 high)

Every control is 32 high on the same baseline (y 30) and shaped as a capsule or circle, so the bar reads as one set.


| Object | x | y | w | h |
|---|---:|---:|---:|---:|
| Header band (Blank, `#13233A`) | 0 | 0 | 1400 | 76 |
| Logo | 30 | 14 | 177 | 48 |
| Page Title | 223 | 9 | 275 | 58 |
| SELECT PERIOD | 506 | 12 | 180 | 14 |
| Period Field | 506 | 30 | 180 | 32 |
| SELECT VIEW | 698 | 12 | 180 | 14 |
| Group Field | 698 | 30 | 180 | 32 |
| SHOW | 890 | 12 | 240 | 14 |
| Workforce Toggle | 890 | 30 | 240 | 32 |
| Reset | 1142 | 30 | 184 | 32 |
| Info Button | 1338 | 30 | 32 | 32 |

Gaps are 12 px between controls and 16 px between the logo/title and the fields; the logo sits on the left edge of the page grid (x 30) and Info on the right edge (1370). The whole page uses a **30 px margin** so the banner and the body are the same width. **Corners and borders.** The capsules only look round if nothing square sits behind them. For `Period Field`, `Group Field`, `Workforce Toggle`, `Reset` and `Info Button`: Worksheet > Format > Shading > **Worksheet: None** (and Row/Column bands None), Format > Borders > all **None**; on the dashboard select the item > Layout pane > **Border: None**, **Background: None**. For the toggle, the final look is: item **Background None** (it blends into the navy band) and an item **Border** in the same colour as the Reset outline (a thin light line, sample it with the colour picker from the Reset capsule), so the three options read as one control. `Info Button` x 1345 (it sits slightly right of the 1338 in the table, for breathing room beside Reset). Info shares the Reset's thin translucent outline so the two read as one family.

Delete any parameter control (`p_InfoOpen`, `p_Worker`, `p_From`, `p_To`) and shape legend (`Info Shape`) left on the dashboard: they are helpers for the actions, not part of the page. The Page Title text is **white**.

---

## 7. Popovers

### 7.1 Period popover (copy of #2's)

> **Layout superseded by [section 14](#14-popover-carryback-from-dashboard-3-oct-24-2026)** (Oct 24, 2026): the frame is now x 506, w 864, rows sit on fixed slots, and the sizes below no longer apply. The sheets, calcs and actions named here stay.

Each popover opens directly under its own control (left edge aligned with the field, top at y 76, the bottom of the band); the Info panel is right-aligned to the page margin (x 960, w 410, right edge 1370).

Sheets on **Region Walk**, built exactly as [rail_controls_build.md](../compensation-walk/rail_controls_build.md) Part 4.3: `Span List`, `Period Panel`, `Popover Close` (shape `btn_close_light`, Detail `Close Panel`, `zzTrue`, `zzFalse`, tooltip `Close`). Title text object "Select a period"; note line 9 pt `#8FA0B8`: "Fiscal year runs July to June. Each option compares two month-ends. Data through Jun 30, 2026."

Container `Period Popover`: floating, navy style of 0.5, **x 506, y 76, w 620, h 330** (left edge under the Period field), visibility `p_PeriodOpen`. Inside: header row (title + ✕), note, then a horizontal container with `Span List` (120 wide) and `Period Panel`.

Period actions (Dashboard > Actions, all Run on **Select**, Clearing **Keep current value**):

| Name | Source | Target parameter | Field |
|---|---|---|---|
| Open period panel | Period Field | `p_PeriodOpen` | `Toggle Period Panel` |
| Period opens, group closes | Period Field | `p_GroupOpen` | `Close Panel` |
| Period opens, info closes | Period Field | `p_InfoOpen` | `Close Panel` |
| Set span | Span List | `p_Span` | `Span Value` |
| Set From | Period Panel | `p_From` | `from_month_end` |
| Set To | Period Panel | `p_To` | `to_month_end` |
| Close on pick | Period Panel | `p_PeriodOpen` | `Close Panel` |
| Close period on ✕ | Popover Close (period) | `p_PeriodOpen` | `Close Panel` |

### 7.2 Group popover (new: the view list on the left, the groups on the right)

> **Layout and behaviour superseded by [section 14](#14-popover-carryback-from-dashboard-3-oct-24-2026).** A view click no longer applies the first group alphabetically: it only browses (`p_ViewTab`), and a group click applies view and group together. The text below describes the first build.

The top bar has no room for #2's six-row view list, so the view list moves into the popover, laid out like the period popover (choice of kind on the left, options on the right).

1. Sheet `View List` (Region Walk): Marks **Text**. Rows: `view_name`, sorted by `view_order` (Field, Minimum). Text: `View Display`. Filter `View Offered` = True and `Period Is Current` = True. Detail: `view_name`, `Default Group`, `zzTrue`, `zzFalse`. **No Color field**, like `Span List`: the current view is shown by the `›` that `View Label` puts in front of it. Set the look in the label, not in Format: Marks > **Text** > **...** (Edit Label) > Tableau Book 10, colour `#B8C0CC`; leave Format > Font at its defaults (a Format override beats the label and blocks the change). Why no Color: Tableau draws the hover outline in the mark's colour, so a grey or white Color field gives a bright outline on the navy popover, while no Color gives the default black, which disappears on navy (as on `Span List`). Headers hidden, shading None, tooltip off.
2. Sheet `Group Panel`: copy #2's ([rail_group_picker_build.md](../compensation-walk/rail_group_picker_build.md) 2.4) on Region Walk. Filters `Group In View` = True and `Period Is Current` = True. Detail `group_name`, `Close Panel`, `zzTrue`, `zzFalse`. Colors on navy: current white Semibold, others `#B8C0CC`.
3. Sheet `Group Heading 2`: Text `<Panel Title>`, Bold 12 white.
4. Container `Group Popover`: **x 610, y 76, w 760, h 330** (right edge 1370; wide enough for 3 columns of long department names), navy style, visibility `p_GroupOpen`. Header row (`Group Heading 2` + ✕ sheet), then a horizontal container: `View List` (140 wide) and `Group Panel`.

| Name | Source | Target | Field |
|---|---|---|---|
| Open group panel | Group Field | `p_GroupOpen` | `Toggle Group Panel` |
| Group opens, period closes | Group Field | `p_PeriodOpen` | `Close Panel` |
| Group opens, info closes | Group Field | `p_InfoOpen` | `Close Panel` |
| Set view | View List | `p_View` | `view_name` |
| Set group from view | View List | `p_Group` | `Default Group` |
| Keep panel open unless All | View List | `p_GroupOpen` | `Keep Group Panel Open` |
| Set group | Group Panel | `p_Group` | `group_name` |
| Close on group pick | Group Panel | `p_GroupOpen` | `Close Panel` |
| Close group on ✕ | Popover Close (group) | `p_GroupOpen` | `Close Panel` |

`Group Panel` filters on calc `Panel Shows Groups` = `[Group In View] AND [p_View] <> "Company"` (True) instead of `Group In View`, so with All selected the right-hand list is empty (it would only repeat "All organizations"); `Group Field` keeps `Group In View`.

Calc `Keep Group Panel Open` = `[view_name] <> "Company"` (add it to `View List` Detail): picking **All** applies at once and closes the popover (there is nothing else to choose); every other view keeps it open for the group pick.

Picking a view keeps the popover open and pre-selects the first group (alphabetical), so the cards are never blank; picking Company sets `Arcadia Systems`, which the lists show as **All organizations**: on `Group Panel` and `View List` right-click the `group_name` field (Region Walk) > **Aliases...** > `Arcadia Systems` = `All organizations` (close the popover with ✕ or pick again). 

### 7.3 Reset, toggle and info actions

| Name | Source | Target | Field |
|---|---|---|---|
| Set worker | Workforce Toggle | `p_Worker` | `Worker Pick` |
| Reset from / to / span / view / group / worker / expand | Reset | `p_From`, `p_To`, `p_Span`, `p_View`, `p_Group`, `p_Worker`, `p_Expand` | the `Default ...` calcs |
| Reset closes popovers (3 actions) | Reset | `p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen` | `Close Panel` |
| Open info | Info Button | `p_InfoOpen` | `Toggle Info` |
| Info opens, others close (2) | Info Button | `p_PeriodOpen`, `p_GroupOpen` | `Close Panel` |
| Close info on ✕ | Popover Close (info) | `p_InfoOpen` | `Close Panel` |

### 7.4 Deselect actions (the "no highlight" rule, every clickable sheet and every text sheet)

Dashboard > Actions > Add Action > **Filter**. Source = the sheet, Run on **Select**, Target = **the same worksheet** (pick the sheet under its own name, not under the dashboard), Clearing **Show all values**, Target filters **Selected fields**: `zzTrue` → `zzFalse`.

One per sheet: `Period Field`, `Group Field`, `Workforce Toggle`, `Reset`, `Info Button`, `Span List`, `Period Panel`, `View List`, `Group Panel`, each `Popover Close`, `Detail Toggle`, `Page Title`, `KPI cards`, `Waterfall Caption`, `Group Heading 2`. Add `zzTrue` and `zzFalse` to each sheet's Detail first. The charts (Waterfall, Trend, Turnover) keep normal selection: clicking a bar to highlight it is useful there.

---

## 8. Body

### 8.1 Waterfall: compact and expanded

```
// WF Bar   (the waterfall's column; replaces Movement Category on Columns)
IF [p_Expand] THEN [Movement Category]
ELSE
    CASE [Walk Step]
        WHEN "Converted" THEN
            IF [p_Worker] = "Total" THEN "Converted"
            ELSEIF [Worker Type] = "Employee" THEN "Joined"
            ELSE "Left" END
        WHEN "Moved in"  THEN "Moved (net)"
        WHEN "Moved out" THEN "Moved (net)"
        ELSE [Walk Step]
    END
END
```
Compact: Employees read Opening · **Joined** (hires + conversions from contingent) · **Left** · Moved (net, groups only) · Closing. Contingent: a conversion out is a **Left**. Total: a conversion is −1 contingent and +1 employee, so it nets to zero and disappears.

```
// WF Order
CASE [WF Bar]
    WHEN "Opening" THEN 1
    WHEN "Joined" THEN 2   WHEN "Hires" THEN 2   WHEN "Starts" THEN 3   WHEN "Conversions" THEN 4
    WHEN "Left" THEN 5     WHEN "Voluntary Terminations" THEN 5   WHEN "Involuntary Terminations" THEN 6   WHEN "Ends" THEN 7
    WHEN "Converted" THEN 8
    WHEN "Moved (net)" THEN 9   WHEN "Internal Moves In" THEN 9   WHEN "Internal Moves Out" THEN 10
    WHEN "Closing" THEN 11
END
```
```
// WF Moves Hidden   (at Company every move nets to zero, as #2 has no transfers at Company)
[p_View] = "Company" AND ([Walk Step] = "Moved in" OR [Walk Step] = "Moved out")
```
```
// WF Driver Total   (one value per expanded driver, for the Expand label)
{ FIXED [Movement Category] : SUM([Walk Value]) }
```
```
// WF Driver Count   (drivers the expanded waterfall shows: non-zero, not Opening/Closing, no moves at Company)
{ FIXED : COUNTD(
    IF [Movement Category] <> "Opening" AND [Movement Category] <> "Closing"
       AND NOT [WF Moves Hidden] AND [WF Driver Total] <> 0
    THEN [Movement Category] END) }
```
```
// WF Group Count   (bars the compact waterfall shows between Opening and Closing)
{ FIXED : COUNTD(
    IF [Walk Step] <> "Opening" AND [Walk Step] <> "Closing" AND NOT [WF Moves Hidden]
       AND NOT ([p_Worker] = "Total" AND [Walk Step] = "Converted")
       AND [Walk Value] <> 0
    THEN IIF([Walk Step] = "Moved in" OR [Walk Step] = "Moved out", "Moved",
             IIF([Walk Step] = "Converted", IIF([Worker Type] = "Employee", "Joined", "Left"), [Walk Step])) END) }
```

Edit the existing waterfall calcs: in `Waterfall Position`, `Bar Type`, `Move Label` and `Level Label`, replace `ATTR([Movement Category])` by `ATTR([WF Bar])`. Delete `Show Category`.

**Tooltip calcs: fix them from the bottom of the chain up.** `TT Context` reads `TT Net Str`, `TT Share Str` and `TT Noun`; those read `TT Open Ref` and `TT Close Ref`; and the two Refs still read the release 2 `WF FTE Open` / `WF FTE Close`, which is why they are red and why Tableau will not let you delete the FTE calcs yet. In this order:
1. `TT Unit` = `"people"` and `TT Noun` = `"headcount"` (constants: every employee is 1.0 FTE).
2. `TT Open Ref` = `[WF Open]` and `TT Close Ref` = `[WF Close]`. `TT Net Str`, `TT Share Str` and `TT Context` stop being red as soon as these two are saved.
3. `TT Context`, replacing the whole formula (the `FTE Changes` branch is gone, as that category no longer exists):
```
// TT Context
CASE ATTR([WF Bar])
WHEN "Opening" THEN "Active at the end of " + [TT Open Month]
WHEN "Closing" THEN "Active at the end of " + [TT Close Month] + " · " + [TT Net Str] + " vs opening"
ELSE [TT Share Str] + " of opening " + [TT Noun] + " · about " +
     STR(INT(ROUND(ABS(SUM([Walk Value])) / MAX([TT Months]), 0))) + " per month"
END
```
4. Check `TT Open Month` and `TT Close Month` read `[p_From]` and `[p_To]` (month and year of each), not the old `[Start Month]` / `[End Month]`.
5. Delete `TT Level PT`, `TT Part Time` and `TT Bar T` (Part Time and the FTE-in-tenths helper do not exist in release 3). Then the `WF FTE ...` calcs delete without a warning, except `WF FTE Open Str` and `WF FTE Close Str`, which `WF Caption` still uses until section 10.

Sheet `Waterfall`:

1. Columns: replace `Movement Category` with `WF Bar`; sort **Field** `WF Order`, Minimum, Ascending.
2. `Waterfall Position`: Edit Table Calculation > Specific Dimensions > `WF Bar` only.
3. Filters: `WF Moves Hidden` = False (dimension filter), and a calc `WF Non Zero` = `SUM([Walk Value]) <> 0 OR ATTR([WF Bar]) = "Opening" OR ATTR([WF Bar]) = "Closing"` = True (drops the zero bars: Moved at Company, Converted in Total). A zero bar adds nothing to the running sum, so dropping it does not move the others.
4. Aliases on `WF Bar` (right-click > Aliases): Voluntary Terminations → `Voluntary leavers`, Involuntary Terminations → `Involuntary leavers`, Internal Moves In → `Moved in`, Internal Moves Out → `Moved out`, Starts → `Contingent joined`, Ends → `Contingent left` ("Starts" and "Ends" read like Opening and Closing, but those two are snapshots of everyone on a date and these two are movements in the period), do **not** alias Conversions: the same bar is +270 in Employees (people from contingent) and −270 in Contingent (people who became employees), and an alias cannot change with the workforce type. It stays "Conversions".
5. Axis: Include zero (headcount waterfalls start at zero; keep the published choice), ticks Automatic (a fixed 5,000 tick is wrong for a 543-person department), format `#,##0`. If the expanded chart shows too many labels, raise the axis font to Tableau Book 10 (Format > Scale) or hide the axis header: every bar has its value. Never set a fixed interval.
6. Title line 2 (Book 9 slate): the dynamic `<WF Subtitle>` (calc below), inserted with Title > Insert > `WF Subtitle`; it changes with the Summary | By driver toggle.
7. Tooltip: `TT Unit`, `TT Context` and `Walk Value` must all sit on Detail or Tooltip (a pill that went red while editing is dropped silently; check the Marks card after the calcs turn green). Text: `<Movement Category>` Semibold 12 navy, `<SUM(Walk Value)> <TT Unit>` Semibold 16 navy, `<AGG(TT Context)>` Book 9 slate. The bar name in the tooltip is `WF Bar` in compact mode (Joined, Left, Moved (net)).
8. Axis format: Format > Axis > Numbers > Custom `#,##0` (not `#,##0,"k"`: a 849-person group would show a single "0k" tick).

**Tooltip that explains each bar** (replaces step 7's text; hover on any bar says what it is, how it is counted and the numbers). Calc on Headcount Walk (`TT Open Day`, `TT Close Day` from 8.2 and 9):
```
// TT What
CASE ATTR([WF Bar])
WHEN "Opening" THEN "Everyone active on " + [TT Open Day] + ". A snapshot of people on one date, not a movement."
WHEN "Closing" THEN "Everyone active on " + [TT Close Day] + ". Opening, plus everything that joined, minus everything that left, plus or minus internal moves."
WHEN "Hires" THEN "People new to Arcadia who started as employees during the period."
WHEN "Conversions" THEN IIF([p_Worker] = "Contingent",
    "Contingent workers who became Arcadia employees. They leave the contingent workforce here; the Employees view counts them as joined.",
    "Contingent workers who became employees during the period. They were already working at Arcadia, so they add to employees.")
WHEN "Starts" THEN "Contingent workers who began an assignment during the period."
WHEN "Ends" THEN "Contingent assignments that ended during the period."
WHEN "Voluntary Terminations" THEN "Employees who chose to leave Arcadia during the period."
WHEN "Involuntary Terminations" THEN "Employees whose employment Arcadia ended during the period."
WHEN "Internal Moves In" THEN "People who moved into this group from elsewhere in Arcadia (transfers and promotions)."
WHEN "Internal Moves Out" THEN "People who moved out of this group to elsewhere in Arcadia (transfers and promotions)."
WHEN "Joined" THEN CASE [p_Worker]
    WHEN "Employees" THEN "New hires plus contingent workers who became employees."
    WHEN "Contingent" THEN "Contingent workers who began an assignment."
    ELSE "New hires plus contingent workers who began an assignment." END
WHEN "Left" THEN CASE [p_Worker]
    WHEN "Employees" THEN "Employees who left, by choice or not."
    WHEN "Contingent" THEN "Contingent assignments that ended, plus workers who became employees."
    ELSE "Employees who left plus contingent assignments that ended." END
WHEN "Moved (net)" THEN "People moving in minus people moving out of this group. Across the whole company these cancel out."
WHEN "Converted" THEN "Contingent workers who became employees."
ELSE "" END
```
Tooltip text on the `Waterfall` sheet (Worksheet > Tooltip, on hover, no command buttons), with `TT What` added to Detail:
- `<WF Bar>` Semibold 12 navy
- `<SUM(Walk Value)> <TT Unit>` Semibold 16 navy
- `<AGG(TT Context)>` Book 9 slate (share of opening and per month)
- a blank line, then **What it is** (Semibold 9 navy) and `<AGG(TT What)>` Book 9 slate.

Summary | By driver toggle (replaces the Expand / Collapse buttons: both states are always visible, so a screenshot explains itself).

Calcs (Headcount Walk). The source rows come from `Walk Step`: "Opening" gives the Summary option, "Left" gives the By driver option (any two steps present in every view work):
```
// Detail Option   CASE [Walk Step] WHEN "Opening" THEN "summary" WHEN "Left" THEN "drivers" END
// Detail Pick     CASE [Detail Option] WHEN "summary" THEN FALSE WHEN "drivers" THEN TRUE END
// Detail State    IF [Detail Pick] = [p_Expand] THEN "on" ELSE "off" END
// Detail Shape    "seg_detail_" + [Detail Option] + "_" + [Detail State]
// WF Subtitle
IF [p_Expand] THEN "Opening + each driver = closing · all " + STR([WF Driver Count]) + " drivers shown · axis starts at zero"
ELSE "Opening + joined − left ± moves = closing · grouped view; By driver shows all " + STR([WF Driver Count]) + " drivers · axis starts at zero" END
```
Shapes: `seg_detail_summary_on/off.png` and `seg_detail_drivers_on/off.png` (generator `docs/brand/build/make_detail_toggle_shapes.py`), copied to `~/Documents/My Tableau Repository/Shapes/Arcadia`.

Tooltip calc (so a reader can hover to learn what a driver is):
```
// Detail Tip
CASE [Detail Option]
WHEN "summary" THEN "Summary" + CHAR(10) + "Groups the changes into Joined, Left and Moved (net), so the walk reads in one glance."
WHEN "drivers" THEN "By driver" + CHAR(10) + "A driver is one reason the headcount changed: hires, conversions, voluntary or involuntary leavers, internal moves. This view shows each of the " + STR([WF Driver Count]) + " drivers as its own bar."
END
```
On `Detail Toggle`: `Detail Tip` on Detail; Worksheet > Tooltip text `<Detail Tip>` (Book 9 navy; first line Semibold), no command buttons.

Sheet `Detail Toggle`, built like `Workforce Toggle` (6.3): `Detail Option` on Columns (manual sort: summary, drivers), filter out Null, mark type Shape, `Detail Shape` on Shape (assign the four files), `Detail Pick`, `zzTrue`, `zzFalse` on Detail, tooltip off, Entire View, shading and borders None.

Dashboard: floating item `Detail Toggle`, **x 663, y 205, w 152, h 24** (12 px inside the waterfall card's top-right corner at 827, the right edge of KPI card 3; y 205 centres it on the first title line), Background `#ECEBE5`, corner radius 12, padding 0, border none. Action **Set detail** (Change Parameter, Run on Select, Keep current value): source `Detail Toggle`, `p_Expand` ← `Detail Pick`; plus one Deselect filter action for `Detail Toggle` (7.4). Before leaving 8.1, make sure `p_Expand` is back to False (Reset sets it from `Default Expand`).

### 8.1b Waterfall caption (what is behind the bars)

The caption explains the bars on screen, with the same numbers, and changes with the Summary | By driver toggle, the workforce type and the view. Summary: it breaks Joined and Left into their parts. By driver: the bars already show the parts, so it says they add up to the net change. The tie-out line under it is section 9.

New number calcs on Headcount Walk (FIXED pattern like `WF Hires`; they follow the toggle through `In Range`):
```
// WF Vol         ZN({ FIXED : -SUM(IF [In Range] AND [Movement Category] = "Voluntary Terminations" THEN [Headcount] END) })
// WF Invol       ZN({ FIXED : -SUM(IF [In Range] AND [Movement Category] = "Involuntary Terminations" THEN [Headcount] END) })
// WF Starts      ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Starts" THEN [Headcount] END) })
// WF Ends        ZN({ FIXED : -SUM(IF [In Range] AND [Movement Category] = "Ends" THEN [Headcount] END) })
// WF Conv In     ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Conversions" AND [Worker Type] = "Employee" THEN [Headcount] END) })
// WF Conv Out    ZN({ FIXED : -SUM(IF [In Range] AND [Movement Category] = "Conversions" AND [Worker Type] = "Contingent" THEN [Headcount] END) })
// WF Moves In    ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Internal Moves In" THEN [Headcount] END) })
// WF Moves Out   ZN({ FIXED : -SUM(IF [In Range] AND [Movement Category] = "Internal Moves Out" THEN [Headcount] END) })
// WF Moves Net   [WF Moves In] - [WF Moves Out]
```
Text twins, the comma pattern (WF Vol Str shown; make the same for `WF Invol Str`, `WF Starts Str`, `WF Ends Str`, `WF Conv In Str`, `WF Conv Out Str`, `WF Moves In Str`, `WF Moves Out Str`, changing the field in all three places):
```
// WF Vol Str
IF [WF Vol] >= 1000 THEN STR(DIV(INT([WF Vol]), 1000)) + "," + RIGHT("00" + STR(INT([WF Vol]) % 1000), 3)
ELSE STR(INT([WF Vol])) END
```
Signed net moves and net change (the only two with a sign):
```
// WF Moves Net Str
IF [WF Moves Net] >= 0 THEN "+" ELSE "−" END +
IF ABS([WF Moves Net]) >= 1000 THEN STR(DIV(INT(ABS([WF Moves Net])), 1000)) + "," + RIGHT("00" + STR(INT(ABS([WF Moves Net])) % 1000), 3)
ELSE STR(INT(ABS([WF Moves Net]))) END
// WF Net Signed
IF [WF Close] >= [WF Open] THEN "+" ELSE "−" END + [WF Net Str]
```
Already existing and reused: `WF Hires Str`, `WF Joined Str`, `WF Left Str`, `WF Leavers Str`, `WF Net Str`.

```
// WF Moves Tail   (group views show the Moved (net) bar; at Company moves net to zero and there is no bar)
IF [p_View] = "Company" THEN " · internal moves net to zero and are not shown."
ELSE " · Moved (net) " + [WF Moves Net Str] + ": " + [WF Moves In Str] + " in, " + [WF Moves Out Str] + " out." END
```
```
// WF Caption
IF NOT [K Valid] THEN ""
ELSEIF [p_Expand] THEN
  IF [p_Worker] = "Employees" THEN
    IF [p_View] = "Company"
    THEN "Hires, conversions and leavers add up to the net change of " + [WF Net Signed] + " · internal moves net to zero and are not shown."
    ELSE "Hires, conversions, leavers and moves add up to the net change of " + [WF Net Signed] + "." END
  ELSEIF [p_Worker] = "Contingent" THEN
    "Contingent joined, contingent left and conversions add up to the net change of " + [WF Net Signed] + "."
  ELSE
    "Hires, contingent joined, leavers and contingent left add up to the net change of " + [WF Net Signed] + " · conversions net to zero."
  END
ELSE
  IF [p_Worker] = "Employees" THEN
    "Joined " + [WF Joined Str] + " = " + [WF Hires Str] + " hires + " + [WF Conv In Str] + " converted from contingent · Left " + [WF Left Str] +
    " = " + [WF Vol Str] + " voluntary + " + [WF Invol Str] + " involuntary" + [WF Moves Tail]
  ELSEIF [p_Worker] = "Contingent" THEN
    "Joined " + [WF Joined Str] + " contingent workers · Left " + [WF Left Str] + " = " + [WF Ends Str] + " assignments ended + " + [WF Conv Out Str] + " became employees."
  ELSE
    "Joined " + [WF Joined Str] + " = " + [WF Hires Str] + " hires + " + [WF Starts Str] + " contingent joined · Left " + [WF Left Str] +
    " = " + [WF Leavers Str] + " employees + " + [WF Ends Str] + " contingent left" + [WF Moves Tail]
  END
END
```
Expected, FY26, All organizations:

| Workforce | Summary | By driver |
|---|---|---|
| Employees | `Joined 5,235 = 4,965 hires + 270 converted from contingent · Left 3,668 = 2,942 voluntary + 726 involuntary · internal moves net to zero and are not shown.` | `Hires, conversions and leavers add up to the net change of +1,567 · internal moves net to zero and are not shown.` |
| Contingent | `Joined 7,033 contingent workers · Left 5,529 = ... assignments ended + 270 became employees.` | `Contingent joined, contingent left and conversions add up to the net change of +1,500.` |
| Total | `Joined 11,998 = 4,965 hires + 7,033 contingent joined · Left 9,197 = 3,668 employees + 5,529 contingent left · internal moves net to zero and are not shown.` | `Hires, contingent joined, leavers and contingent left add up to the net change of +2,801 · conversions net to zero.` |

Sheet `Waterfall Caption`: `WF Caption` on Text, Tableau Book 8 slate, left, **wrap on** (the Summary lines can need two lines; the item is 56 px tall and the tie-out line from section 9 is added later). Check each bar against the caption: every number in it is a bar or a sum of bars. Then delete `WF FTE Open Str` and `WF FTE Close Str`.

### 8.2 KPI cards

#### 8.2a Wider cards (30 px margin)

The cards now span the full page grid (x 30 to 1370): five cards 255 wide with 16 gaps. Use the new background `docs/brand/arcadia_kpi_cards_bg_wide.png` (2800 × 220; generated with `make_kpi_cards_bg.py --left 30 --top 12 --card-w 255 --card-h 86 --gap 16 --radius 10`) as the background image item (0, 78, 1400 × 110). Set the KPI parameters (calibrated on the real dashboard): `kpi_GridLeft` 30, `kpi_CardW` 255, `kpi_GapX` 16, `kpi_GridTop` 12, `kpi_CardH` 86, `kpi_SheetW` 1400, `kpi_SheetH` 110, **`kpi_FitX` 1.082**, **`kpi_ShiftX` −12**, **`kpi_PadX` 127.5** (half of CardW: the anchors sit at each card's centre). The text is **centred**: in all 15 mark layers of the `KPI cards` sheet (Title 1 to 5, Value 1 to 5, Note 1 to 5) open Label > Alignment and set Horizontal to Center. Expected anchor centres on the page: 157.5, 428.5, 699.5, 970.5, 1241.5. If the five cards drift the same way nudge `kpi_ShiftX`; if card 1 and card 5 drift in opposite directions nudge `kpi_FitX` by 0.005 (the map re-fits, so a change in FitX moves the text more than its size suggests), as in the KPI guide, section 6. Remove the parameter controls from the dashboard when done.

#### 8.2b Build the cards (rewrite the text calcs in place; no layer changes)

The map layers and anchors stay. Each card reads `KPI N Title`, `KPI N Value` and `KPI N Note`, so the slots are re-used: **KPI 2** = Joined (was Closing FTE), **KPI 3** = Voluntary turnover (was Hires), **KPI 4** = Internal moves (was Voluntary turnover), **KPI 5** = Workforce mix (was Internal moves). Card order on the page: Closing | Joined | Voluntary turnover | Internal moves | Workforce mix.

Number calcs (Headcount Walk). `K Vol Emp` and `K Invol Emp` ignore the Workforce toggle on purpose (turnover is an employee measure); the mix calcs ignore it so each card can show the other side of the split:
```
// K Joined      IF [p_Worker] = "Employees" THEN [WF Joined] + [WF Conv In] ELSE [WF Joined] END
// K Vol Emp     ZN(-SUM(IF [In Period] AND [Officers Out] AND [In Group] AND [Worker Type] = "Employee" AND [Movement Category] = "Voluntary Terminations" THEN [Headcount] END))
// K Invol Emp   same with "Involuntary Terminations"
// K CW Close    ZN(SUM(IF [In Period] AND [Officers Out] AND [In Group] AND [Worker Type] = "Contingent" AND [Is Closing Row] THEN [Headcount] END))
// K EE Close    same with [Worker Type] = "Employee"
// K All Close   [K CW Close] + [K EE Close]
// K CW Share    IF [K All Close] = 0 THEN 0 ELSE [K CW Close] / [K All Close] END
```
Text twins: the comma pattern on `K Joined`, `K Vol Emp`, `K Invol Emp`, `K CW Close`, `K EE Close`, `K All Close` (`K Joined Str`, `K Vol Emp Str`, ...), and the percent pattern on `K CW Share` (`K CW Share Str`) and on `1 - [K CW Share]` (`K EE Share Str`).

Card text:
```
// KPI 1 Title   CASE [p_Worker] WHEN "Employees" THEN "Closing headcount" WHEN "Contingent" THEN "Closing contingent" ELSE "Total workforce" END
// KPI 2 Title   "Joined"
// KPI 2 Value   IF NOT [K Valid] THEN "—" ELSE [K Joined Str] END
// KPI 2 Note
IF NOT [K Valid] THEN ""
ELSEIF [p_Worker] = "Employees" THEN [WF Hires Str] + " hires · " + [WF Conv In Str] + " from contingent"
ELSEIF [p_Worker] = "Contingent" THEN "contingent assignments that began"
ELSE [WF Hires Str] + " hires · " + [WF Starts Str] + " contingent joined" END
// KPI 3 Title   "Voluntary turnover (annualized)"
// KPI 3 Value   (the old KPI 4 Value formula, unchanged)
// KPI 3 Note
IF NOT [K Valid] THEN ""
ELSEIF [p_Worker] = "Employees" THEN [K Vol Emp Str] + " left by choice · " + [K Invol Emp Str] + " involuntary"
ELSE "Employees only · " + [K Vol Emp Str] + " left by choice" END
// KPI 4 Title   "Internal moves"
// KPI 4 Value   (the old KPI 5 Value formula, unchanged)
// KPI 4 Note
IF NOT [K Valid] THEN ""
ELSEIF [p_Worker] = "Contingent" THEN "between teams"
ELSEIF [p_View] <> "Company" THEN ATTR([WF Moves In Str]) + " in · " + ATTR([WF Moves Out Str]) + " out"
ELSE
  IF [K Promotions] >= 1000
  THEN STR(DIV(INT([K Promotions]), 1000)) + "," + RIGHT("00" + STR(INT([K Promotions]) % 1000), 3)
  ELSE STR(INT([K Promotions])) END
  + " promotions · " +
  IF [K Other Moves] >= 1000
  THEN STR(DIV(INT([K Other Moves]), 1000)) + "," + RIGHT("00" + STR(INT([K Other Moves]) % 1000), 3)
  ELSE STR(INT([K Other Moves])) END
  + " other moves"
END
// Why ATTR: [WF Moves In Str] is a FIXED calc (non-aggregate) and [K Promotions] is a SUM (aggregate); one IF cannot return both kinds, so the non-aggregate side is wrapped in ATTR(). Paste only the ELSE part of the old KPI 5 Note, not its own IF NOT [K Valid] line or its closing END.
// KPI 5 Title   CASE [p_Worker] WHEN "Employees" THEN "Contingent workforce" WHEN "Contingent" THEN "Employees" ELSE "Contingent share" END
// KPI 5 Value   IF NOT [K Valid] THEN "—" ELSE CASE [p_Worker] WHEN "Employees" THEN [K CW Close Str] WHEN "Contingent" THEN [K EE Close Str] ELSE [K CW Share Str] END END
// KPI 5 Note
IF NOT [K Valid] THEN ""
ELSE CASE [p_Worker]
  WHEN "Employees" THEN [K CW Share Str] + " of " + [K All Close Str] + " in total"
  WHEN "Contingent" THEN [K EE Share Str] + " of " + [K All Close Str] + " in total"
  ELSE [K CW Close Str] + " of " + [K All Close Str] END END
```
Delete afterwards: `KPI 2` FTE helpers (`K Close FTE`, `K FTE T`, `K Gap T`, `K Close PT`, `K Part Time Gap`), `KPI 3`'s old Hires formulas (`K Hires Show`), and any `... FTE` field. Check table: section 11.

Card set per toggle value. The map layers and 15 anchors stay as built; only the text calcs change.

| Card | Employees | Contingent | Total |
|---|---|---|---|
| 1 Title / value | Closing headcount · 30,005 | Closing contingent · 11,941 | Total workforce · 41,946 |
| 1 Note | **+5.5%** from 28,438 on Jun 30, 2025 | **+11.5%** from 10,707 | **+7.2%** from 39,145 |
| 2 Title / value | Joined · 5,235 | Started · 7,033 | Joined · 11,998 |
| 2 Note | 4,965 hires · 270 from contingent | 6,907 new · 126 returned | 4,965 hires · 7,033 starts |
| 3 Title / value | Voluntary turnover (annualized) · 10.1% | same (employees) | same (employees) |
| 3 Note | 2,942 left by choice · 726 involuntary | Employees; contingent ends: 5,529 | Employees; contingent ends: 5,529 |
| 4 Title / value | Hires per leaver · 1.35 | Joined per leaver · 1.21 | Joined per leaver · 1.30 |
| 4 Note | 4,965 hires ÷ 3,668 leavers | 7,033 joined ÷ 5,799 left | 11,998 joined ÷ 9,197 left |
| 5 Title / value | Contingent workforce · 11,941 | Employees · 30,005 | Contingent share · 28.5% |
| 5 Note | 28.5% of 41,946 in total | 71.5% of 41,946 in total | 11,941 of 41,946 |

Calcs (comma pattern and percent pattern from the build book, section 6.4):

```
// K Joined      (Employees: hires + conversions in; Contingent: starts; Total: hires + starts)
ZN(SUM(IF [In Range] AND ([Walk Step] = "Joined"
        OR ([p_Worker] = "Employees" AND [Movement Category] = "Conversions"))
    THEN [Headcount] END))
// K Hires       ZN(SUM(IF [In Range] AND [Movement Category] = "Hires" THEN [Headcount] END))
// K Conv In     ZN(SUM(IF [In Range] AND [Movement Category] = "Conversions" AND [Worker Type] = "Employee" THEN [Headcount] END))
// K Starts      ZN(SUM(IF [In Range] AND [Movement Category] = "Starts" THEN [Headcount] END))
// K Starts New  ZN(SUM(IF [In Range] AND [Movement Category] = "Starts" AND [Movement Reason] = "New engagement" THEN [Headcount] END))
// K Ends        ZN(-SUM(IF [In Period] AND [Officers Out] AND [In Group] AND [Movement Category] = "Ends" THEN [Headcount] END))
// K Leavers Inv ZN([Involuntary Leavers])
```
```
// K CW Close    (contingent at close, whatever the toggle: card 5)
ZN(SUM(IF [In Period] AND [Officers Out] AND [In Group] AND [Worker Type] = "Contingent" AND [Is Closing Row] THEN [Headcount] END))
// K EE Close    same with [Worker Type] = "Employee"
// K All Close   [K CW Close] + [K EE Close]
// K CW Share    IF [K All Close] = 0 THEN 0 ELSE [K CW Close] / [K All Close] END
```

`KPI 2 Value`, `KPI 2 Note` and `KPI 5 ...` replace the old FTE card; `KPI 3 Title` becomes `"Voluntary turnover (annualized)"`, and cards 1 to 5 titles use `CASE [p_Worker]` per the table. `KPI 1 Note Rest` becomes `"from " + [K Open Str] + " on " + [TT Open Day]` where `TT Open Day` = `LEFT(DATENAME('month',[p_From]),3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))`.

**KPI 4 = Hires per leaver.** Internal moves net to zero at Company and the page never explained them, so card 4 is now the waterfall title as one number. All pieces are FIXED helpers, so there is no aggregate/non-aggregate error.

```
// K HPL Num   IF [p_Worker] = "Employees" THEN [WF Hires] ELSE [WF Joined] END
// K HPL Den   IF [p_Worker] = "Employees" THEN [WF Leavers] ELSE [WF Left] END
// K HPL       IF [K HPL Den] = 0 THEN 0 ELSE [K HPL Num] / [K HPL Den] END
// K HPL N     INT(ROUND([K HPL] * 100, 0))
// K HPL Str   STR(DIV([K HPL N], 100)) + "." + RIGHT("0" + STR([K HPL N] % 100), 2)

// KPI 4 Title  CASE [p_Worker] WHEN "Employees" THEN "Hires per leaver" ELSE "Joined per leaver" END
// KPI 4 Value  IF NOT [K Valid] OR [K HPL Den] < 20 THEN "—" ELSE [K HPL Str] END
// KPI 4 Note
IF NOT [K Valid] THEN ""
ELSEIF [p_Worker] = "Employees" THEN [WF Hires Str] + " hires ÷ " + [WF Leavers Str] + " leavers"
ELSE [WF Joined Str] + " joined ÷ " + [WF Left Str] + " left" END
```

If `WF Leavers Str` or `WF Left Str` does not exist yet, build it with the comma pattern. Expected FY26: Employees 1.35, Contingent 1.21, Total 1.30. Afterwards delete `K Moves`, `K Promotions`, `K Other Moves`, `K Hires Show`.

**KPI 3 title.** "Annualized" is there so a month, a quarter and a year compare on one scale (a quarter's 2.25% is shown as 9.0%). Make the title follow the period: `KPI 3 Title` = `IF DATEDIFF('month',[p_From],[p_To]) >= 11 THEN "Voluntary turnover" ELSE "Voluntary turnover (annualized)" END` (adjust the 11 if your To is the last day of the month).

#### 8.2c KPI card tooltips

Every card gets a hover tooltip, so the five cards behave the same way. Cards 3 and 4 explain how the number is built; cards 1, 2 and 5 say plainly what is being counted and which selections it reflects. Tone: friendly and professional, one short paragraph per card.

**1. Calcs** (all built from fields that already exist; if a `... Str` twin is missing, create it with the comma pattern):

```
// KPI 1 Tip
CASE [p_Worker]
WHEN "Employees" THEN "Employees on the books at the close of " + [TT Close Day] + ": " + [K EE Close Str] + ", compared with " + [K Open Str] + " on " + [TT Open Day] + ". Executive officers are not included."
WHEN "Contingent" THEN "Contingent workers with an active assignment at the close of " + [TT Close Day] + ": " + [K CW Close Str] + ", compared with " + [K Open Str] + " on " + [TT Open Day] + "."
ELSE "Employees plus contingent workers at the close of " + [TT Close Day] + ": " + [K All Close Str] + ", compared with " + [K Open Str] + " on " + [TT Open Day] + "."
END + CHAR(10) + "Reflects the period, view and workforce you have selected."
```
```
// KPI 2 Tip
CASE [p_Worker]
WHEN "Employees" THEN "People who joined the company during the period: " + [K Joined Str] + ". That is " + [WF Hires Str] + " new hires plus " + [WF Conv In Str] + " contingent workers who became employees. Moves between teams are not counted here."
WHEN "Contingent" THEN "Contingent assignments that started during the period: " + [K Joined Str] + ". This includes new engagements and workers who returned."
ELSE "Everyone who started during the period: " + [K Joined Str] + ", made up of employee hires and contingent starts."
END + CHAR(10) + "Reflects the period, view and workforce you have selected."
```
```
// KPI 3 Tip
"Voluntary leavers divided by average headcount, expressed as a 12-month rate so that a month, a quarter and a year can be compared on the same scale."
+ CHAR(10) + IF DATEDIFF('month',[p_From],[p_To]) >= 11 THEN "This period spans a full year, so no scaling is needed. " ELSE "" END
+ [K Vol Emp Str] + " employees left by choice; the " + [K Invol Emp Str] + " involuntary exits are not included."
+ IF [p_Worker] <> "Employees" THEN CHAR(10) + "Employees only: contingent workers are not part of this rate." ELSE "" END
+ CHAR(10) + "Shown as a dash for groups with fewer than 20 people."
```
```
// KPI 4 Tip
CASE [p_Worker]
WHEN "Employees" THEN "New hires divided by leavers. Above 1.00 means more people came in than left; below 1.00 means the workforce shrank. " + [WF Hires Str] + " hires ÷ " + [WF Leavers Str] + " leavers (voluntary and involuntary). Contingent conversions and moves between teams are not counted."
ELSE "People who joined divided by people who left. Above 1.00 means more came in than left; below 1.00 means the workforce shrank. " + [WF Joined Str] + " joined ÷ " + [WF Left Str] + " left."
END
```
```
// KPI 5 Tip
CASE [p_Worker]
WHEN "Employees" THEN "Contingent workers (vendor-supplied, not on the payroll) with an active assignment at the close of " + [TT Close Day] + ": " + [K CW Close Str] + ", or " + [K CW Share Str] + " of the " + [K All Close Str] + " people working for the company."
WHEN "Contingent" THEN "Employees at the close of " + [TT Close Day] + ": " + [K EE Close Str] + ", out of " + [K All Close Str] + " people working for the company (employees plus contingent workers)."
ELSE "Contingent workers as a share of the whole workforce at the close of " + [TT Close Day] + ": " + [K CW Close Str] + " of " + [K All Close Str] + "."
END
```

**2. Why not on the map layers.** Tooltips set on the 15 layers of `KPI cards` never showed in Dashboard #1 or #2, whatever the circle size, opacity or tooltip text (a plain "TEST" did not show either). Leave those layers as they are (tooltips off) and put the hover on five small ordinary sheets laid over the cards.

**3. Build `KPI Hover N` (N = 1 to 5).**
1. Calc `Hover Cell` = `"."`.
2. New sheet `KPI Hover 1` on Headcount Walk. `Hover Cell` on Columns and on Rows (second copy); right-click each pill and untick Show Header.
3. Marks type **Square**; Size all the way right (the square fills the pane); Color opacity **0%**.
4. `KPI 1 Title` and `KPI 1 Tip` on **Tooltip** (Attribute). Tooltip text: line 1 `<ATTR(KPI 1 Title)>` (Semibold 10 navy), line 2 `<ATTR(KPI 1 Tip)>` (Book 9, `#4A5A73`). Show tooltips on, Include command buttons off.
5. `zzTrue` and `zzFalse` on **Detail**.
6. Format: Shading > Worksheet None, Borders None, Grid lines None, Fit Entire View, Show Title off.
7. Duplicate the sheet four times and swap the two fields for `KPI N Title` / `KPI N Tip` (and the tooltip text).

**4. Dashboard.** Each sheet is a **Floating** item, Show title off, Background None, Border None, **Corner Radius 5**, above `KPI cards` in the item list:

| Item | x | y | w | h |
|---|---|---|---|---|
| KPI Hover 1 | 30 | 90 | 255 | 86 |
| KPI Hover 2 | 301 | 90 | 255 | 86 |
| KPI Hover 3 | 572 | 90 | 255 | 86 |
| KPI Hover 4 | 843 | 90 | 255 | 86 |
| KPI Hover 5 | 1114 | 90 | 255 | 86 |

Add the deselect action for each hover sheet (7.4: Filter, source and target the same worksheet, Run on Select, Show all values, `zzTrue` → `zzFalse`), named `Deselect KPI Hover N`. Without it a click leaves a blue cover and a Keep Only / Exclude toolbar.

**5. Hover outline.** Tableau draws a rectangular hover outline around the mark. A corner radius on the item clips that rectangle and the corners look cut, so keep it small: **5** looks clean (10 clips the outline, 0 is a plain rectangle). (Colouring the mark like the card was considered to hide the outline; the corner radius is the fix that was used.)

**6. Check** in Presentation Mode: hover each card in Employees, Contingent and Total and read the sentence against the numbers on the card (Employees FY26: 30,005 versus 28,438; 5,235 = 4,965 + 270; 1.35 = 4,965 ÷ 3,668; 11,941 = 28.5% of 41,946). FY25 Q3 makes card 3 mention annualizing; FY26 says the period spans a full year. A click must not turn anything blue. Apply the same build to Dashboard #2.

### 8.3 Trend and Turnover

**8.3a Trend, step by step.** The Trend answers "where does the selected period sit in the history?". It follows Workforce and View. The subtitle carries the dates, both values and the change (the same +498 and +1.3% as the waterfall title and card 1); the chart carries only the line, the shaded band, two unlabelled dots on the band edges and one grey label at the start of the history. (A first version labelled both band edges, the change and the last point; in the 518 px card the labels collided with each other and with the line, so they were dropped.)

1. **Trend Value** (Headcount Walk). No `In Period` test, so the line covers the whole history; `Worker In Scope` and `In Group` make it follow the toggle and View.
```
IF [Officers Out] AND [In Group] AND [Worker In Scope] AND [Movement Category] = "Closing" THEN [Headcount] END
```
2. **Title and subtitle.** Use only `WF` fields here (non-aggregate); a `K` field is an aggregate and makes Tableau stop with "Cannot mix aggregate and non-aggregate arguments".
```
// Trend Title
"Closing " + CASE [p_Worker] WHEN "Employees" THEN "headcount" WHEN "Contingent" THEN "contingent workers" ELSE "workforce" END + " by month-end"
// Trend Open Str
IF [WF Open] >= 1000 THEN STR(DIV(INT([WF Open]), 1000)) + "," + RIGHT("00" + STR(INT([WF Open]) % 1000), 3) ELSE STR(INT([WF Open])) END
// Trend Close Str
IF [WF Close] >= 1000 THEN STR(DIV(INT([WF Close]), 1000)) + "," + RIGHT("00" + STR(INT([WF Close]) % 1000), 3) ELSE STR(INT([WF Close])) END
// Trend Pct
IF [WF Open] = 0 THEN 0 ELSE ([WF Close] - [WF Open]) / [WF Open] END
// Trend Chg Str
IF [WF Close] >= [WF Open] THEN "+" ELSE "−" END + [WF Net Str]
// Trend Pct Str
IF [WF Close] >= [WF Open] THEN "+" ELSE "−" END
+ STR(DIV(INT(ROUND(ABS([Trend Pct]) * 1000, 0)), 10)) + "." + STR(INT(ROUND(ABS([Trend Pct]) * 1000, 0)) % 10) + "%"
// Trend Subtitle
IF NOT [K Valid] THEN "" ELSE
[TT Open Day] + " → " + [TT Close Day] + " · " + [Trend Open Str] + " → " + [Trend Close Str]
+ " (" + [Trend Chg Str] + ", " + [Trend Pct Str] + ")" END
```
Put `Trend Title` and `Trend Subtitle` on Detail of the `Trend` sheet, then in the sheet title (Worksheet > Edit Title) Insert each: line 1 `Trend Title` (bold), line 2 `Trend Subtitle` (Book 9 slate). `Band Start` = `[p_From]`.

3. **Dots and the start label.**
```
// Trend Pt     (the four points that get a dot)
SUM(IF [month_end_date] = [p_From] OR [month_end_date] = [p_To]
       OR [month_end_date] = { FIXED : MIN([month_end_date]) }
       OR [month_end_date] = { FIXED : MAX([month_end_date]) } THEN [Trend Value] END)
// Pt Role      (a dimension: drives the dot colour)
IF [month_end_date] = [p_From] OR [month_end_date] = [p_To] THEN "Selected"
ELSEIF [month_end_date] = { FIXED : MIN([month_end_date]) } OR [month_end_date] = { FIXED : MAX([month_end_date]) } THEN "Edge"
ELSE "None" END
// Trend Lbl    (the only dot label: the first month of the history)
IF ATTR([month_end_date]) = ATTR({ FIXED : MIN([month_end_date]) }) THEN
    IF SUM([Trend Value]) >= 1000 THEN STR(DIV(INT(SUM([Trend Value])), 1000)) + "," + RIGHT("00" + STR(INT(SUM([Trend Value])) % 1000), 3)
    ELSE STR(INT(SUM([Trend Value]))) END
ELSE "" END
```
4. **Layout.** Columns `month_end_date`. Rows `SUM(Trend Value)` then `AGG(Trend Pt)`; right-click the second pill > **Dual Axis**, then **Synchronize Axis** and untick **Show Header** on the right axis. Range Automatic, Include zero off. Right-click the "nulls" badge > Hide Indicator.
   - `SUM(Trend Value)` card: line, teal, **no label**. Tooltip: line 1 `<month_end_date>` (Semibold 11 navy), line 2 `<SUM(Trend Value)>` (Book 10 navy); show tooltips, no command buttons. No table calcs: a month-over-month calc is split by `Pt Role` and shows the change versus the previous *labelled* point, so it was dropped.
   - `AGG(Trend Pt)` card: **Circle**, small; `Pt Role` on **Color on this card only** (a pill on the `All` card would colour and split the line); Edit Colors: `Selected` `#13233A`, `Edge` `#8C8A84`, `None` any; hide the legend. **Label**: `Trend Lbl` only, Book 9, Match Mark Color, Top Center. Tooltip off.

5. **Checks.** FY25 Q3, Total: subtitle `Dec 31, 2024 → Mar 31, 2025 · 37,836 → 38,334 (+498, +1.3%)` on one line, two navy dots on the band edges, grey `32,072` at the start, nothing touching the line. FY26: `Jun 30, 2025 → Jun 30, 2026 · …`. The last point on the line is the full-history end (Employees 30,005, Contingent 11,941, Total 41,946); the percentage matches card 1 in every workforce type. One teal line for all three workforce types: the title and subtitle carry the change (colour by workforce was considered and dropped, since the palette gives teal, coral and violet fixed meanings).

**Turnover:** the rows become **one level below the selection**, so the chart always says something about what you picked:

```
// TO Dim
CASE [p_View]
    WHEN "Company"      THEN [Function Name]
    WHEN "Function"     THEN IIF({ FIXED [Function Name] : COUNTD([Sub Function]) } > 1, [Sub Function], [Department Name])
    WHEN "Sub-function" THEN [Department Name]
    WHEN "Department"   THEN [Country Name]
    WHEN "Country"      THEN [Function Name]
END
```
Replace `Function Name` on Rows with `TO Dim`; `TO Top Function` becomes `TO Top` = `LOOKUP(ATTR([TO Dim]), FIRST())` (Compute Using `TO Dim`). Sort `TO Dim` descending by `Total Rate Shown`. `Vol Rate Shown`, `Invol Rate Shown` and `Total Rate Shown` already return NULL under 20 average headcount, so small groups never appear.

**Title and subtitle.** `TO Title` = `[TO Top] + " has the highest turnover, " + [Period Name]` (Semibold 12 navy). Subtitle (Book 9 slate `#5A6170`, except the words Voluntary and Involuntary in the two bar colours): `Voluntary + Involuntary leavers ÷ average headcount, annualized` followed by `<TO Suffix>`:

```
// TO Suffix
IF [p_Worker] = "Employees" THEN "" ELSE " · employees only" END
```

**Fixed bar size (the department view has up to 22 countries).** Cap the list at 10 rows and fix the row height, so a 2-bar chart and an 8-bar chart look alike:

1. `TO Rank` = `INDEX()`, on Filters, range 1 to 10, Compute Using `TO Dim`.
2. Fit **Standard** on the sheet and on the dashboard item (toolbar dropdown with the item selected; the dashboard setting wins). Format > Cell Size > Taller or Shorter until the rows are about 22 px apart (Mac has no numeric height). Marks > Size about 75%.
3. Row-label column: drag the edge to about 95 px, sized for the default view ("Legal & Compliance"). Longer labels end in "…" and the tooltip has the full name. A column left on auto moves the bars in every view.

**Tooltip** (no command buttons): `<ATTR(TO Dim)>` Semibold 12 navy; `<AGG(Total Rate Shown)>` Semibold 16 navy then ` annualized turnover` Book 9 slate; `Voluntary <AGG(Vol Rate Shown)> · <AGG(Voluntary Leavers)> leavers`; `Involuntary <AGG(Invol Rate Shown)> · <AGG(Involuntary Leavers)> leavers`; `Average headcount: <AGG(Average Headcount)>` (Book 9 slate). Use `TO Dim` in line 1, not `function_name`.

**Checks (FY26).** Company: Commercial 14.8%, Legal & Compliance 12.9%, Operations 11.9%, Technology 11.7%, Finance 11.7%, Product 11.6%, People 11.4%, Marketing 11.4%. Commercial: Sales 14.9%, Client Services 14.8%. Finance: Treasury & Tax 13.4%, FP&A 12.3%, Accounting & Controllership 10.3%.

**One type rule for the three cards.** Title Semibold 12 navy `#13233A`; subtitle Book 9 slate `#5A6170`; caption and footnote Book 8 slate.

### 8.4 Info popover (replaces the white Info Panel)

> **Frame updated in [section 14](#14-popover-carryback-from-dashboard-3-oct-24-2026)** (44 px header, line, body 518; same text and the same 410 x 571 box). The old hidden `Info Panel` is deleted there.

Container `Info Popover`, navy style (0.5), **x 960, y 76, w 410, h 571** (as built: 410 wide so the paragraphs wrap in fewer lines; right edge 1370 = page margin), visibility `p_InfoOpen`, front. Item hierarchy: `Info Popover` > `Info Popover Header` (title text + `Popover Close Info`, a duplicate of `Popover Close Group`) and `Info Popover Panel` (the body text). Header row: title "How to read this page" + ✕ (`Popover Close Info`; action `Close info on ✕` and `Deselect Popover Close Info` use it). Body (one Text object, 10 pt):

> **Period.** Every number compares two month-ends: the walk opens on the first and closes on the second. Arcadia's fiscal year runs July to June.
>
> **Who is counted.** Employees active at month-end. The CEO and the eight function heads are left out on both Arcadia dashboards, so both count the same people.
>
> **Employees, Contingent, Total.** Contingent workers are contractors held in the vendor system. A contingent worker hired as an employee is a conversion: one out of Contingent, one into Employees, so the Total does not move.
>
> **The walk.** Opening + joined − left ± moves = closing, reconciled to the month-end snapshot. Expand shows each driver; moves appear when a group is selected.
>
> **Joined and left.** This page counts every hire and every leaver. The Compensation Walk compares the two dates, so someone who joined and left in between is in neither snapshot: its Hires count only people still here at the end. The note under the waterfall gives both numbers.
>
> **Turnover.** Employee leavers ÷ average headcount, annualized. Groups under 20 people are not shown.
>
> **Data.** Arcadia Systems is a fictional company. All data is synthetic.

### 8.5 Titles

```
// Period Name   (Headcount Walk; the same words as #2's Pair Name for fiscal years)
IF DATEDIFF('month', [p_From], [p_To]) = 12 AND MONTH([p_From]) = 6
THEN "FY" + RIGHT(STR(YEAR([p_To])), 2)
ELSE LEFT(DATENAME('month', DATEADD('day', 1, [p_From])), 3) + " " + STR(YEAR(DATEADD('day', 1, [p_From]))) + " – " +
     LEFT(DATENAME('month', [p_To]), 3) + " " + STR(YEAR([p_To]))
END
```
`WF Period` → replace its formula with `[Period Name]` (create `Period Name` first).

**Why the title currently reads "+30005 FTE net".** The release 2 `WF Title` tests `[Measure] = "Headcount"`. After `Measure` became `p_Worker` that test is never true, so the title falls to its FTE branch, where `WF FTE Open` is 0 (it still looks for the old start month) and the net is the whole closing figure. Rewrite the calc as below; the FTE branch and the FTE helpers then go away.

Two new helpers (Headcount Walk), scoped by the toggle automatically because `In Range` already contains `Worker In Scope`:
```
// WF Joined   (Employees: hires · Contingent: starts · Total: both; a conversion nets to zero in Total)
ZN({ FIXED : SUM(IF [In Range] AND ([Movement Category] = "Hires" OR [Movement Category] = "Starts") THEN [Headcount] END) })
```
```
// WF Left     (leavers, ends; for Contingent a conversion to employee counts as a leaver, as the compact waterfall does)
ZN({ FIXED : -SUM(IF [In Range] AND ([Movement Category] = "Voluntary Terminations" OR [Movement Category] = "Involuntary Terminations"
                                      OR [Movement Category] = "Ends"
                                      OR ([p_Worker] = "Contingent" AND [Movement Category] = "Conversions")) THEN [Headcount] END) })
```
Their text twins, same comma pattern as `WF Hires Str` (create `WF Joined Str` on `[WF Joined]` and `WF Left Str` on `[WF Left]`):
```
// WF Joined Str
IF [WF Joined] >= 1000
THEN STR(DIV(INT([WF Joined]), 1000)) + "," + RIGHT("00" + STR(INT([WF Joined]) % 1000), 3)
ELSE STR(INT([WF Joined])) END
```
Then **edit** `WF Title` (replace the whole formula):
```
// WF Title
IF NOT [K Valid] THEN "Choose a start month on or before the end month"
ELSEIF [p_Worker] = "Employees" THEN
     [WF Period] + ": " + [WF Hires Str] + " hires " +
     IF [WF Hires] >= [WF Leavers] THEN "outpaced " ELSE "fell short of " END +
     [WF Leavers Str] + " leavers, " +
     IF [WF Close] >= [WF Open] THEN "adding " ELSE "removing " END + [WF Net Str] + IIF([WF Net Str] = "1", " person", " people")
ELSEIF [p_Worker] = "Contingent" THEN
     [WF Period] + ": " + [WF Joined Str] + " joined, " + [WF Left Str] + " left, " +
     IF [WF Close] >= [WF Open] THEN "adding " ELSE "removing " END + [WF Net Str] + IIF([WF Net Str] = "1", " contingent worker", " contingent workers")
ELSE
     [WF Period] + ": " + [WF Joined Str] + " joined, " + [WF Left Str] + " left, " +
     IF [WF Close] >= [WF Open] THEN "adding " ELSE "removing " END + [WF Net Str] + IIF([WF Net Str] = "1", " person", " people")
END
```
`WF Net Str` (`ABS([WF Close] - [WF Open])`) already follows the toggle. Check: Employees FY26 Company reads the first row of the table below; Total reads 11,998 joined, 9,197 left, adding 2,801 people.

| Selection | Waterfall title |
|---|---|
| FY26, Company, Employees | FY26: 4,965 hires outpaced 3,668 leavers, adding 1,567 people |
| FY26, Function Commercial, Employees | FY26: 1,458 hires outpaced 1,131 leavers, adding 354 people |
| FY26, Company, Total | FY26: 11,998 joined, 9,197 left, adding 2,801 people |

---

## 9. The tie-out note (same sentence as Dashboard #2)

Sheet `Waterfall Caption` (rebuild; primary **Headcount Walk**, secondary **Region Walk**). Put `Link` on Detail from the primary; check the blend link icon is orange on `Link` only.

```
// TO Joined      ZN(SUM(IF [In Range] AND [Worker Type] = "Employee" AND ([Movement Category] = "Hires" OR [Movement Category] = "Conversions") THEN [Headcount] END))
// TO Still Here  ZN([Region Walk].[RW Hires Still Here])      (the Compensation Walk's Hires bar)
// TO Here        ZN([Region Walk].[RW Hires Joined Here])     (the part of it that joined this group)
// TO Moved In    ZN([Region Walk].[RW Hires Moved In])
// TO Gap         [TO Joined] - [TO Here]                      (never negative)
```
Tableau has no comma function, so each number gets a text calc (same pattern each time):

```
// TO Joined Text
IF [TO Joined] >= 1000 THEN STR(INT([TO Joined] / 1000)) + "," + RIGHT("00" + STR(INT([TO Joined]) % 1000), 3)
ELSE STR(INT([TO Joined])) END
// TO Still Here Text   (same, with [TO Still Here])
// TO Here Text         (same, with [TO Here])
// TO Gap Text          (same, with [TO Gap])
// TO Moved In Clause   IF [TO Moved In] > 0 THEN ", plus " + STR([TO Moved In]) + " who moved in" ELSE "" END
// TT Close Day         LEFT(DATENAME('month',[p_To]),3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))
```
```
// Tie-out Text   (starts with "Note:"; one line; the same two numbers as Dashboard #2, seen from this page)
IF [p_Worker] <> "Employees" THEN "Note: the Compensation Walk covers employees only."
ELSEIF [p_View] = "Company" THEN
    "Note: the Compensation Walk counts only people still here on " + [TT Close Day] + ": " + [TO Still Here Text] +
    " of the " + [TO Joined Text] + " who joined (" + [TO Gap Text] + " left again)."
ELSE
    "Note: the Compensation Walk counts people here on " + [TT Close Day] + ": " + [TO Here Text] +
    " of the " + [TO Joined Text] + " who joined " + [p_Group] + [TO Moved In Clause] + "."
END
```

**Tooltip on the note** (the numbers in plain English; mirrors #2's). Extra calcs on Headcount Walk (`TT Open Day` from 8.2):

```
// TO Who   IF [p_View] = "Company" THEN "the whole company" ELSE [p_Group] END
// Tie-out Detail
(IF [p_Worker] <> "Employees" THEN
    "The Compensation Walk prices employees only, so there is nothing to compare for contingent workers."
ELSE
    [TO Joined Text] + " people joined " + [TO Who] + " between " + [TT Open Day] + " and " + [TT Close Day] +
    " (hires plus people converted from contingent, counted month by month)." + CHAR(10) +
    "In the Compensation Walk's Hires: " + [TO Here Text] + ", the ones still there on " + [TT Close Day] + "." + CHAR(10) +
    (IF [TO Moved In] > 0
     THEN "Also in its Hires: " + STR([TO Moved In]) + " who joined another team and moved in (" + [TO Still Here Text] + " in all)." + CHAR(10)
     ELSE "" END) +
    "Not in that walk: " + [TO Gap Text] +
    (IF [p_View] = "Company"
     THEN ", who joined and left again before " + [TT Close Day] + "."
     ELSE ", who left Arcadia or moved to another team before " + [TT Close Day] + "." END)
END)
```
`Waterfall Caption`: `Tie-out Detail` on Detail; Worksheet > Tooltip: bold **Why the two dashboards count different hires**, `<AGG(Tie-out Detail)>`, then "The Compensation Walk compares two snapshots and prices people present on each date, so anyone who joined and left in between is in neither. This page counts every joiner and every leaver." (Book 9; no command buttons). FY26 Company: "5,235 people joined Arcadia between Jun 30, 2025 and Jun 30, 2026 … In the Compensation Walk's Hires: 4,790 … Not in that walk: 445, who joined and left again before Jun 30, 2026."

Caption layout: line 1 `<WF Caption>` (built in 8.1b), line 2 `<Tie-out Text>`. Tableau Book 8 slate, left.

| Selection | Tie-out text |
|---|---|
| FY26, Company | Note: the Compensation Walk counts only people still here on Jun 30, 2026: 4,790 of the 5,235 who joined (445 left again). |
| FY26 Q4 (Mar 31 → Jun 30, 2026), Company | Note: the Compensation Walk counts only people still here on Jun 30, 2026: 1,317 of the 1,330 who joined (13 left again). |
| FY26, Function Commercial | Note: the Compensation Walk counts people here on Jun 30, 2026: 1,305 of the 1,470 who joined Commercial, plus 4 who moved in. |
| FY26, Department Accounting & Controllership | Note: the Compensation Walk counts people here on Jun 30, 2026: 68 of the 72 who joined Accounting & Controllership, plus 5 who moved in. |

If the secondary number shows blank: the link is not active (click the link icon next to `Link` in the Region Walk pane) or a filter on the primary sheet removed `Link`.

---

## 10. Dashboard layout (1400 × 850, every object floating)

| # | Object | x | y | w | h | Note |
|---|---|---:|---:|---:|---:|---|
| 1–11 | Header (6.8) | | | | | |
| 12 | KPI background image | 0 | 78 | 1400 | 110 | new wide image (8.2a) |
| 13 | KPI cards | 0 | 78 | 1400 | 110 | geometry parameters per 8.2a |
| 14 | Waterfall | 30 | 188 | 797 | 624 | right edge 827 = right edge of KPI card 3; bottom padding 64 |
| 15 | Detail Toggle (Summary \| By driver) | 663 | 205 | 152 | 24 | Background `#ECEBE5`, radius 12 |
| 16 | Waterfall Caption | 42 | 750 | 773 | 56 | Two lines now |
| 17 | Trend | 843 | 188 | 526 | 296 | left edge 843 = left edge of KPI card 4, right edge 1369 = KPI card 5; 16 px gap to Turnover; Inner Padding bottom 4 |
| 18 | Turnover | 843 | 500 | 526 | 312 | Bottom 812, level with the waterfall; Inner Padding bottom 4 |
| 19 | Footnote (Text object) | 30 | 822 | 600 | 16 | "Arcadia Systems is a fictional company. All data is synthetic and covers Jul 2021 to Jun 2026." Book 8 slate (width 600 is enough; widen to 700 if it clips) |
| 20 | Period / Group / Info popovers | section 14.3 | 506 / 506 / 960 | 76 | 864 / 864 / 410 | 289 / 383 / 571 | Front, hidden (Period and Group share one frame) |

Item order (Layout pane, bottom to top): background, cards, charts, buttons, header controls, popovers last.

---

## 11. Check table (release 3, run on DuckDB 2026-10-15)

Default state: FY26 (Jun 30, 2025 → Jun 30, 2026), Company, Employees, compact.

| Item | Value |
|---|---|
| Card 1 | 30,005 · +5.5% from 28,438 on Jun 30, 2025 |
| Card 2 | Joined 5,235 · 4,965 hires · 270 from contingent |
| Card 3 | 10.1% · 2,942 left by choice · 726 involuntary |
| Card 4 | 3,633 · 2,015 promotions · 1,618 other moves |
| Card 5 | 11,941 · 28.5% of 41,946 in total |
| Waterfall compact | Opening 28,438 · Joined +5,235 · Left −3,668 · Closing 30,005 · toggle Summary | By driver |
| Waterfall expanded | Hires +4,965 · From contingent +270 · Voluntary −2,942 · Involuntary −726 |
| Turnover by function | Commercial 14.8% (12.2 + 2.6), Legal & Compliance 12.9%, Operations 11.9%, Technology 11.7%, Finance 11.7%, Product 11.6%, People 11.4%, Marketing 11.4%; no Executive row |

| Selection | Opening | Joined (hires + conv.) | Voluntary | Involuntary | Moves in / out | Closing | Vol. turnover |
|---|---:|---:|---:|---:|---:|---:|---:|
| FY26 Company Employees | 28,438 | 5,235 (4,965 + 270) | 2,942 | 726 | — | 30,005 | 10.1% |
| FY26 Q4 Company Employees | 29,618 | 1,330 (1,255 + 75) | 751 | 192 | — | 30,005 | 10.1% |
| FY26 YTD 9 months (→ Mar 31, 2026) | 28,438 | 3,905 (3,710 + 195) | 2,191 | 534 | — | 29,618 | 10.1% |
| FY26 Function Commercial | 7,441 | 1,470 (1,458 + 12) | 930 | 201 | 948 / 933 | 7,795 | 12.2% |
| FY26 Department Accounting & Controllership | 543 | 72 (70 + 2) | 49 | 8 | 67 / 65 | 560 | 8.9% |
| FY26 Country India | 6,672 | 1,113 (983 + 130) | 672 | 149 | 801 / 798 | 6,967 | 9.8% |
| FY26 Company Contingent | 10,707 | 7,033 starts | 5,529 ends | — | — | 11,941 (after −270 converted) | — |
| FY26 Company Total | 39,145 | 11,998 | 8,471 + 726 | — | — | 41,946 | — |

Commercial turnover rows (one level below): Sales 14.9%, Client Services 14.8%. Title: "Sales has the highest turnover in FY26".

**Cross-check with Dashboard #2 (must be identical):** FY26 Company 28,438 → 30,005; Commercial 7,441 → 7,795; Accounting & Controllership 543 → 560; India 6,672 → 6,967; Q4 29,618 → 30,005. Hires still here (the Compensation Walk's Hires bar): Company 4,790, Commercial 1,309, Accounting & Controllership 73, India 1,038, Q4 1,317. In the tie-out, joined this group + moved in: Company 4,790 + 0, Commercial 1,305 + 4, Accounting & Controllership 68 + 5, India 1,033 + 5, Q4 1,317 + 0.

---

## 12. Test and publish

| # | Do | Expect |
|---|---|---|
| 1 | Hover every button and field | Outline or nothing; never a small square. Tooltips on Period, Group, Reset, Info |
| 2 | Click each toggle option, Expand, Collapse, a title, the KPI band | Nothing stays highlighted |
| 3 | Open Period, then Group, then Info | Only the last one is open |
| 4 | Period > Quarter > FY26 Q4 | Field "FY26 Q4", opening 29,618, closing 30,005 |
| 5 | View > Function > Commercial | Header subtitle shows the opening and closing dates of the period; numbers per section 11; turnover by sub-function |
| 6 | Total | Card 1 41,946; waterfall Joined 11,998, Left 9,197; note "The Compensation Walk covers employees only." |
| 7 | Reset | FY26, Company, Employees, compact, all popovers closed |
| 8 | Same selections on Dashboard #2 | Same opening, closing and "still here" numbers |

Publish: reset the dashboard, hide all sheets, **File > Save to Tableau Public As...** `arcadia_headcount_fte_walk` (same name keeps the URL), extracts only. Check the page in the browser with the test table, Tableau Public row by row.

## 13. Wrap-up: cleanup, decisions and lessons

**Cleanup rule (Tableau tells you what is live).** Right-click a calc > Delete. The dialog lists every field and sheet that depends on it. If it lists `KPI cards`, `Dashboard`, `Waterfall`, `Trend` or `Turnover by Function`, or a field you keep: **No**. If it lists nothing, only `CheckList`, or only other calcs on the delete list: **Yes**. This is more reliable than guessing from names: `K EE Share Str` (card 5) and `K Net Pct` / `K Net Pct Str` (the teal note on card 1) looked dead and are not; `Net Change %` is used only by the test sheet and goes.

**Delete:** the FTE and part-time calcs (`K Close PT`, `K Part Time Gap`, `K Gap T`, `K FTE T`, `K Close FTE`, `K Hires FTE`, `K Hires FTE Str`, `K Leavers Vol FTE`, `K Vol FTE Str`, `TT Level FTE`), the Expand/Collapse calcs and the four Expand/Collapse sheets, `Measure Option`, `Option State`, the old `Measure` parameter, `Net Change %`, and the orphan action `Set collapse` (no source sheet). Keep every `kpi_` parameter, `p_Expand` (the Summary | By driver toggle runs on it) and all `Deselect ...` actions. Region Walk has nothing to delete.

**Actions check.** `Close info on ✕` must have source `Popover Close Info`; `Close period on ✕` has source `Popover Close`. A wrong source sheet is the usual reason a ✕ does nothing.

**Design decisions worth knowing**

| Decision | Why |
|---|---|
| KPI tooltips are floating hover sheets | Tooltips do not fire on map-layer marks. Each hover sheet is transparent, sits over its card and carries the card's `KPI N Tip`; a `zzTrue`/`zzFalse` Deselect action stops the click highlight |
| Trend shows four labels on dots, not a line label | A line label collides with the line; dual axis with small bordered dots keeps the numbers readable; a reference line (`Trend Top`) adds headroom |
| Turnover is capped at 10 rows, Standard fit, fixed row height | The department view has 22 countries; Entire View made 2 bars huge and 8 bars thin. Fixed row height and a fixed label column keep every view alike |
| Title 12 semibold navy, subtitle 9 book slate, caption 8 book slate | One type rule across the three cards |
| Header secondary text `#B8C4D6`, footnote slate | The subtitle and the SELECT headings drifted apart before |
| KPI 3 title follows the period | "Voluntary turnover" for 12 months or more, "(annualized)" below that, so a quarter and a year compare on one scale |
| Hires per leaver replaces the old hires/FTE card | FTE equals headcount in release 3; the new ratio reads as a trend signal (1.35 FY26) |

---

## 14. Popover carryback from Dashboard #3 (Oct 24, 2026)

Dashboard #3 (Workforce Planning, published Oct 23) taught us two things about popovers. This section carries both back to #1. **Nothing else on the page changes**: the waterfall, KPI cards, trend, turnover, tie-out note, numbers and layout below y 76 stay exactly as they are. Sources: [release_3_rebuild_dashboard_3.md](../workforce-planning/release_3_rebuild_dashboard_3.md) sections 7.1, 9.0 to 9.2 and 13, and the lessons in `dashboard_3_published.md` section 3. This section supersedes 7.1, 7.2 and 8.4 for layout and for how the Group popover behaves; those sections keep the calcs and sheet names, and each now has a pointer here.

**Change A, organised popovers.** Every row sits on a fixed slot, so a short list starts at the top instead of spreading out; Period and Group share one frame; each popover hangs from the header band with a header, a thin line, a body and a footer; a vertical divider separates the list from the grid.

**Change B, browse first, apply on a group click.** Clicking a view only browses (a new parameter, `p_ViewTab`) and the page does not move. Clicking a group applies the view and the group together and closes the popover. "All organizations" has no groups, so it applies at once. Nothing defaults to the first country, function or office alphabetically any more.

**Status (Oct 24, 2026): built, reviewed and published.** Changes from the plan below are in 14.14: drawn-chevron capsule (the typed `▾` is gone), the Info button stays an "i", the Info popover is taller on Tableau Public, and a note on the Info tooltip toolbar.

### 14.1 What each picker does today, and what it will do

| Picker | Today (checked in your saved .twb, Oct 24) | After this section |
|---|---|---|
| **Period** (`Period Field`, `Span List`, `Period Panel`) | Already browse-then-apply: a span click only sets `p_Span`, a cell click sets `p_From` and `p_To` and closes. The container floats at x 506, w 620, h 330. Rows are spread by `Period Row`, an ordinal table calc, so a short grid sits wherever the pane puts it. Cell labels use an arrow glyph in `Pair Label` | Same behaviour. Rows on fixed slots (6 slots of 32 px), shared frame x 506 to 1370, header, line, divider and footer. Arrow glyph replaced (R1) |
| **Group** (`Group Field`, `View List`, `Group Panel`) | **Applies on the first click.** A click on Function sets `p_View` = Function and `p_Group` = the first group alphabetically (`Default Group`, a FIXED MIN), so the page changes to Commercial before you have chosen. Country sets Argentina, Department sets the first department, and so on. The popover then stays open for the real pick. Container x 610, w 760 | Browse first. View click sets `p_ViewTab` only. Group click sets `p_Group` and `p_View` together and closes. "All organizations" applies at once |
| **Info** (`Info`, hidden panel) | Works; header is 30 px high with no line. A second, older panel (`Info Panel`, hidden, with the From / To text) is still in the item list | Same text and size; 44 px header with a line. Old panel deleted (R3) |
| **Reset** | Resets `p_View` and `p_Group` (through `Default Group`) | Also resets `p_ViewTab` (action 23b) |

Why Group applied on the first click: `Set view` and `Set group from view` both fire on a View List click, and `Default Group` is `{ FIXED [view_name] : MIN([group_name]) }`. Browsing needs a parameter that is *not* the one the page reads, which is exactly what `p_ViewTab` is.

### 14.2 Refinements (all small; tell me any you do not want)

| # | Refinement | Why | Cost |
|---|---|---|---|
| R1 | **Remove the arrow glyph** from `Pair Label` (cells and capsule), `Page Subtitle` and `Trend Subtitle`: " to " or " · " instead of the arrow | Same rule as #3 (D11): an arrow at 9 pt is unreadable, and the project rule is no arrow characters | 3 formula edits (14.5) |
| R2 | **Add two missing closers**: `Period opens, info closes` and `Group opens, info closes` | Today Info closes the other two, but opening Period or Group while Info is open leaves both open (Info starts at x 960, inside the Period frame). #3 has all six pairs | 2 actions |
| R3 | **Delete the old hidden `Info Panel`** (the zone with the "walk starts at the month-end before From" text) | It is dead weight in the item list and its text is out of date | 1 delete |
| R4 | **One navy, `#13233A`**: the file has `#13223A` (header band, Info body), `#13203B` (Period Panel and Group Panel sheets) and `#12213B` (toggle); popovers should match the band exactly or you see a seam | Popovers hang from the band, so a one-digit difference shows as a line | Format only |
| R5 | `Group Heading 2` still holds a typed run `SELECT PERIOD`; make sure the label is only `<Panel Title>` | A typed run beats the field and would print the wrong heading | Check |

Not changing (so you do not wonder): the typed `▾` in `Period Field` and `Group Field` (this was done at the end of the job after all: see 14.14, item 1); the calibrated `kpi_FitX` 1.082 and `kpi_ShiftX` -12 (those are #1's own); `Set collapse` (leave it alone).

**Known and left alone.** `Group Panel` lists every group that ever existed (Department 31, Country 22 across all periods), while a single period has 30 to 31 departments and 19 to 22 countries. A group that did not exist in the selected period is still clickable and gives an empty page. This predates the job and needs a period filter on the picker source; flagged for later.

### 14.3 The frame, in numbers

Page 1400 x 850. All popovers hang from the header band (top y 76, flush), navy `#13233A`, **corner radius top-left 0, top-right 0, bottom-left 10, bottom-right 10**, inner and outer padding 0, border None.

Four bands, top to bottom: **header** 44, **line** 9 (1 px line inset 16 each side), **body**, **footer** 28 (no footer on Info).

| Popover | x | y | w | Body | Total h | Visibility |
|---|---:|---:|---:|---:|---:|---|
| `Period Popover` | 506 | 76 | 864 | **208** (8 + 6 x 32 + 8) | 44 + 9 + 208 + 28 = **289** | `p_PeriodOpen` |
| `Group Popover` | 506 | 76 | 864 | **302** (8 + 11 x 26 + 8) | 44 + 9 + 302 + 28 = **383** | `p_GroupOpen` |
| `Info Popover` | 960 | 76 | 410 | **518** | 44 + 9 + 518 = **571** (unchanged) | `p_InfoOpen` |

Period and Group share x 506 to 1370 (left edge under `SELECT PERIOD`, right edge under the info button), so switching from one to the other does not jump. Both were narrower before (Period 620, Group 760).

Why 6 period slots: the Month span has 48 periods in a grid of **6 rows by 8 columns** (`Period Rows` = ceil(48 / 8)); Fiscal year (16) and Quarter (16) are 4 by 4 and Year to date (8) is 2 by 4. Six rows of 32 px is the tallest any span needs, and the shorter spans simply start at the top.

**Fixed-slot rule** (same as #3): a row position goes on Rows as a **continuous** measure with a fixed, reversed axis and no header. Tableau rejects decimals such as 0.5 in the axis boxes, so every slot is **2 units wide with its centre on an odd number** (1, 3, 5 ...) and the axis runs from 0 to 2 x the number of slots.

| Sheet | Slots | Axis fixed start / end | Pane height | Pixels per unit |
|---|---:|---|---:|---:|
| `Span List`, `Period Panel` | 6 | 0 / 12 | 192 | 16 (slot = 32) |
| `View List`, `Group Panel` | 11 | 0 / 22 | 286 | 13 (slot = 26) |

### 14.4 Before Tableau (Mac)

The four images are made by `docs/brand/build/make_d3_popover_lines.py` (now with a `d1` mode) and are committed in `docs/brand/shapes/by_dashboard/d1/`. They are dashboard **Image** objects, not shapes, drawn at 2x so **Fit Image** keeps them crisp:

| File | Pixels | Item size | Where |
|---|---|---|---|
| `d1_popover_line_wide.png` | 1728 x 18 | 864 x 9 | Under the Period and Group headers |
| `d1_popover_line_info.png` | 820 x 18 | 410 x 9 | Under the Info header |
| `d1_popover_divider_period.png` | 48 x 416 | 24 x 208 | Between `Span List` and `Period Panel` |
| `d1_popover_divider_group.png` | 48 x 604 | 24 x 302 | Between `View List` and `Group Panel` |

I have already copied the four files into `Arcadia Headcount/Images and Buttons/`. Check, and make a backup before you touch the workbook:

```bash
cd ~/Documents/Tableau/Tableau\ Public/ArcadiaHR/Arcadia\ Headcount
ls "Images and Buttons" | grep d1_popover
cp "Arcadia Headcount FTE Walk.twb" "Arcadia Headcount FTE Walk - before popovers.twb"
ls -1 *.twb
```

Expected: the four `d1_popover_*` names, then both `.twb` files. (The same four files are in the repo, so a later `git pull` brings them too.)

### 14.5 Parameter and calcs

**Parameter.** Add one: `p_ViewTab`, String, List, values **Company, Function, Sub-function, Department, Country** (the same five as `p_View`, spelled the same), current value **Company**. Easiest: right-click `p_View` in the Data pane > **Duplicate**, rename to `p_ViewTab`, and check the list. It is the tab the Group popover is *browsing*; `p_View` stays the view the page *uses*. Parameters go from 26 to **27**.

**Calcs on Region Walk.** Edit the six that exist, create the new ones, delete the two that are replaced. Spell the field names with the Data pane (`view_name`, `group_name`, `view_order` are Region Walk's own).

*Edit in place (double-click the calc):*

```
// Group Is Current   (was: group only; six names exist in two views, see 14.9)
[group_name] = [p_Group] AND [view_name] = [p_View]
```
```
// Panel Title   (change p_View to p_ViewTab; the rest is as it is)
"Select " + CASE [p_ViewTab]
    WHEN "Function" THEN "a function" WHEN "Sub-function" THEN "a sub-function"
    WHEN "Department" THEN "a department" WHEN "Country" THEN "a country"
    ELSE "a view" END
```
```
// Default Group   (was { FIXED [view_name] : MIN([group_name]) }, the alphabetical rule)
"Arcadia Systems"
```
```
// View Label   (the text on View List: the chevron marks the tab being browsed, not the view in use; "All organizations" matches the Group field)
IF [view_name] = [p_ViewTab] THEN "› " ELSE "" END
+ IF [view_name] = "Company" THEN "All organizations" ELSE [View Name Display] END
```
```
// Pick Row   (odd slots 1, 3, 5 ... inside the column; Pick Col and Pick Rows stay as they are)
2 * ((INDEX() - 1) % [Pick Rows]) + 1
```
```
// Period Row   (odd slots; Period Col and Period Rows stay as they are)
2 * ((INDEX() - 1) % [Period Rows]) + 1
```

Why `Default Group` becomes a constant: it feeds `Reset` (a reset must land on Arcadia Systems, which it did only because Company's minimum happens to be that) and the old View List click. With the View List click gone, nothing may pick "the first one" any more, so the calc says what it means. If a calc named `Default Group All` also exists, point nothing at it and delete it.

*Create (all row-level, no aggregation):*

```
// Span Slot          (Span Order is 1 to 4: Fiscal year, Year to date, Quarter, Month)
2 * [Span Order] - 1
// Span Is Current
[Span Value] = [p_Span]
// View Slot          (Office, view_order 5, is not offered, so Country at 6 is pulled up to slot 9: no gap)
2 * (IF [view_order] > 5 THEN [view_order] - 1 ELSE [view_order] END) - 1
// View Is Current
[view_name] = [p_ViewTab]
// Group Grid Rows    (the groups of the tab being browsed; Company has no groups, so the grid is empty there)
[view_name] = [p_ViewTab] AND [view_name] <> "Company"
// View Apply         (a click on All organizations applies at once; any other view only browses)
IF [view_name] = "Company" THEN "Company" ELSE [p_View] END
// Group Apply From View
IF [view_name] = "Company" THEN [group_name] ELSE [p_Group] END
```

*Keep as they are, on purpose:* `Group In View` (`[view_name] = [p_View]`) and `Keep Group Panel Open` (`[view_name] <> "Company"`). `Group Field` still filters on `Group In View`, because the field must show the view *in use*, not the one being browsed.

*Delete:* `Panel Shows Groups` (replaced by `Group Grid Rows`). Right-click > Delete: the dialog should list only `Group Panel`; if it lists anything else, press No and tell me.

*R1, arrows (three formula edits):*

```
// Pair Label   (only the Year over Year line changes: the arrow between the two dates becomes " to ")
WHEN "Year over Year" THEN LEFT(DATENAME('month',[from_month_end]),3) + " " + RIGHT(STR(YEAR([from_month_end])),2) + " to " + LEFT(DATENAME('month',[to_month_end]),3) + " " + RIGHT(STR(YEAR([to_month_end])),2)
// Page Subtitle
"Opening " + [TT Open Day] + " · Closing " + [TT Close Day]
// Trend Subtitle   (both arrows become " to ")
IF NOT [K Valid] THEN "" ELSE
[TT Open Day] + " to " + [TT Close Day] + " · " + [Trend Open Str] + " to " + [Trend Close Str]
+ " (" + [Trend Chg Str] + ", " + [Trend Pct Str] + ")" END
```
The capsule then reads `FY26 · Jun 25 to Jun 26` (24 characters at Semibold 9, about 130 px of the 180-px capsule, clear of the chevron).

**Checkpoint P1 (CHK sheet or any text table, Region Walk):** `Span Slot` per `Span Value` = Fiscal year 1, Year to date 3, Quarter 5, Month 7. `View Slot` per `view_name` = Company 1, Function 3, Sub-function 5, Department 7, Country 9 (Office would be 9 too, but it is filtered out; if Office appears in a test table, ignore it). `Default Group` = Arcadia Systems on every row.

### 14.6 Sheets

All sheets in this section: Fit **Entire View**, Format > Shading > Worksheet **None**, grid lines, zero lines, axis rulers and ticks **None**, row and column dividers **None**, Marks type **Text** (not Automatic: Automatic sometimes picks Bar on a continuous pill and the label then sits at the bar's end).

**`Span List` (Region Walk)**
1. Drag `Span Slot` to Rows (replace `pair_type`). Right-click the pill > **Measure > Minimum**, then right-click again > **Continuous**.
2. Right-click the axis > Edit Axis: Range **Fixed**, start **0**, end **12**; tick **Reversed**; close. Right-click the axis > untick **Show Header**.
3. `pair_type` stays on **Detail** (and keeps its filter, which hides "Custom Range"). Drag `Span Is Current` to **Color**: True white `#FFFFFF`, False `#B8C0CC` (Edit Colors; if Tableau offers a palette, pick any and then set the two chips by hand).
4. Text: `<Span Display>`, Tableau Book 10, alignment **Center**, **Middle**. (The `›` in `Span Display` marks the span being browsed.)
5. Detail also keeps `Span Value`, `zzTrue`, `zzFalse`. Tooltip: untick Show tooltips.

**`Period Panel` (Region Walk)**
1. Columns `Period Col` (Discrete, header hidden) as today. Rows: `Period Row` (now odd slots 1, 3, ... 11): right-click the pill > **Continuous** (the pill turns green). The pill changes from discrete to continuous, so the table calc setup is kept: right-click > **Edit Table Calculation** and check **Specific Dimensions** with **every** field of Detail ticked (`Period Key`, `Pair Label`, `from_month_end`, `to_month_end`, `Close Panel`, `zzTrue`, `zzFalse`, and the colour and tooltip fields). Do the same in the nested calcs: click **Nested calculation** at the top of that dialog, choose `Period Rows`, `Period Col` in turn, and set each to the same Specific Dimensions (this is the lesson from #3: one nested calc left on "Table (Across)" shifts the grid).
2. Axis: Fixed 0 to **12**, **Reversed**, header hidden. Format > Lines: all None.
3. Marks Text: `<Pair Label>` Tableau **Semibold 9**, **Center**, **Middle**. Color `Period Is Current`: True white `#FFFFFF`, False `#B8C0CC`. Tooltip `<Pair Name>` as today.
4. Keep the filters (`Action (zzFalse)`, `Period In Span` = True) and every Detail field.

**`View List` (Region Walk)**
1. Rows: drag `View Slot` onto Rows, **Measure > Minimum**, **Continuous**; **remove** `View Label` from Rows and drag it to **Text**. Axis Fixed **0** to **22**, **Reversed**, header hidden.
2. Marks Text: `<View Label>` Tableau **Book 10**, **Center**, **Middle**. Color `View Is Current`: True white `#FFFFFF`, False `#B8C0CC`.
3. Detail: `view_name`, `Group Apply From View`, `View Apply`, `Keep Group Panel Open`, `zzTrue`, `zzFalse`. **Remove `Default Group` and `Close Panel`** (they are not used by the new actions). Filter `view_name` keeps Company, Function, Sub-function, Department, Country (no Office). Tooltip off.
4. Why `view_name` stays on Detail: it is the field the "Browse view" action reads, and the field that keeps one mark per view.

**`Group Panel` (Region Walk)**
1. Filters: remove `Panel Shows Groups`; add `Group Grid Rows` = **True**. Keep `Action (zzFalse)`.
2. Columns `Pick Col` (Discrete, header hidden). Rows `Pick Row` (now odd slots 1, 3 ... 21): right-click > **Continuous**; axis Fixed 0 to **22**, **Reversed**, header hidden. Re-check **Edit Table Calculation** on `Pick Row`, `Pick Col` and the nested `Pick Rows`: Specific Dimensions with every Detail field ticked, `group_name` at the top.
3. Marks **Text** (it is Automatic today): `<Group Label>` Tableau **Book 9** (it is Bold 12 in the saved file), **Center**, **Middle**. Color `Group Is Current`: True white `#FFFFFF`, False `#B8C0CC`.
4. Detail: `group_name`, `view_name` (new, needed by the "Apply view" action), `Group Label` stays on Text, `Close Panel`, `zzTrue`, `zzFalse`, `Panel Title` (remove it if present; it belongs to the heading sheet).
5. The sheet is empty while `p_ViewTab` = Company. That is correct. To test: right-click `p_ViewTab` > Show Parameter, set Function, look, set Company, then hide the control (Remove from dashboard when you add it to a dashboard; in the sheet it is free).

**`Group Heading 2`:** Text `<Panel Title>` only (delete the typed `SELECT PERIOD` run if it is still there, R5): Tableau **Bold 12**, white `#FFFFFF`, alignment **Left**, **Middle**. Tooltip off. Detail `zzTrue`, `zzFalse`.

**`Group Field`:** add `view_name` to **Detail** (action 31 needs it). Nothing else changes.

**`Reset`:** no change. Its Detail already holds `Default View` (it will feed `p_ViewTab` too), and `Default Group` is now the constant.

**Close sheets** (`Popover Close`, `Popover Close Group`, `Popover Close Info`): unchanged; they only need the new 44 x 44 item size (14.7).

**Checkpoint P2 (sheets, before the dashboard):** `Span List` shows 4 rows level with slots 1, 3, 5, 7; `Period Panel` at Fiscal year shows a 4 by 4 block starting at the top, at Month a 6 by 8 block; set `p_ViewTab` to Function: `Group Panel` shows 8 names in 3 columns (3, 3, 2) from the top; Department: 31 names (11, 11, 9); Country: 22 (8, 8, 6); Sub-function: 10 (4, 4, 2). Set it back to Company.

### 14.7 Dashboard

Edit the three existing popover containers in place; do not delete and rebuild them, so every action keeps its source. Open one at a time: right-click `p_PeriodOpen` in the Data pane > **Show Parameter**, set True, work, then **Remove from Dashboard** the control and set the value back to False. In the Layout pane use **Item hierarchy** (it lists hidden containers too).

**R4 first (a minute):** on the header band (blank object), the three popover containers and the three panel sheets: background `#13233A`, border None. Sheets get this through Format > Shading > Worksheet **None** where they sit on a navy container, so set the **container** navy and the sheets None.

**Period Popover** (vertical container, Floating): x **506**, y **76**, w **864**, h **289**.

| Item | Type | w | h | Format |
|---|---|---:|---:|---|
| `Period Popover` | Vertical container | 864 | 289 | Background `#13233A`, border None, radius bottom-left and bottom-right 10, top 0, padding 0 |
| `Period Popover Header` | Horizontal container | 864 | 44 | Background None, padding 0 |
| title | Text | 820 | 44 | `Select a period`, Tableau Bold 12, white `#FFFFFF`; inner padding left 16, top 12 |
| `Popover Close` | Sheet | 44 | 44 | Inner padding 14 on all sides |
| header line | Image `d1_popover_line_wide.png` | 864 | 9 | **Fit Image**, no border, padding 0 |
| `Period Popover Panel` | Horizontal container | 864 | 208 | Background None, padding 0 |
| `Span List` | Sheet | 160 | 208 | Inner padding top 8, bottom 8, left 0, right 0 |
| divider | Image `d1_popover_divider_period.png` | 24 | 208 | Fit Image, no border, padding 0 |
| `Period Panel` | Sheet | 680 | 208 | Inner padding top 8, bottom 8, left 0, right 0 |
| footer | Text | 864 | 28 | `Fiscal year runs July to June. Each option compares two month-ends. Data through Jun 30, 2026.` Tableau Book 9, `#8FA0B8`; inner padding left 16, top 6 |

The current header text object holds `SELECT PERIOD` and the note in one run; split it: the note moves to the footer (copy its text), and the header text becomes the title above. Steps: (1) set the container to the new size and position first; (2) set the header container to h 44 and the text and close sheet to the sizes above; (3) drag an **Image** object from the Objects pane into the container, between the header and the panel (a grey drop guide shows the spot), choose `d1_popover_line_wide.png`, Fit Image; (4) resize `Span List` and `Period Panel` and drag an Image between them for the divider; (5) drag a **Text** object below the panel for the footer. For every tiled item, type the w and h in the Layout pane.

**Group Popover:** x **506**, y **76**, w **864**, h **383**.

| Item | Type | w | h | Format |
|---|---|---:|---:|---|
| `Group Popover` | Vertical container | 864 | 383 | As the Period popover |
| `Group Popover Header` | Horizontal container | 864 | 44 | |
| `Group Heading 2` | Sheet | 820 | 44 | Inner padding left 16, others 0 |
| `Popover Close Group` | Sheet | 44 | 44 | Inner padding 14 |
| header line | Image `d1_popover_line_wide.png` | 864 | 9 | Fit Image |
| `Group Popover Panel` | Horizontal container | 864 | 302 | |
| `View List` | Sheet | 160 | 302 | Inner padding top 8, bottom 8 |
| divider | Image `d1_popover_divider_group.png` | 24 | 302 | Fit Image |
| `Group Panel` | Sheet | 680 | 302 | Inner padding top 8, bottom 8 |
| footer | Text | 864 | 28 | `Choose a view on the left, then a group on the right. All organizations applies at once.` Tableau Book 9, `#8FA0B8`; inner padding left 16, top 6 |

**Info Popover:** x **960**, y **76**, w **410**, h **571** (unchanged size).

| Item | Type | w | h | Format |
|---|---|---:|---:|---|
| `Info Popover Header` | Horizontal container | 410 | 44 | |
| title | Text | 366 | 44 | `How to read this page`, Tableau Bold 12, white; inner padding left 16, top 12 |
| `Popover Close Info` | Sheet | 44 | 44 | Inner padding 14 |
| header line | Image `d1_popover_line_info.png` | 410 | 9 | Fit Image |
| `Info Popover Panel` body | Text | 410 | 518 | Inner padding left 16, right 16, top 4. Lead-ins Tableau Semibold 10 white `#FFFFFF`, body Tableau Book 10 `#B8C0CC`; text exactly as 8.4 |

**R3:** Item hierarchy > the hidden **`Info Panel`** (the old one, 286 px wide, with the From / To text) > right-click > **Remove from Dashboard**.

**Front-to-back order** (Item hierarchy, top of the list is in front): `Info Popover`, `Group Popover`, `Period Popover`; then `KPI Hover 1` to `5`; then `KPI cards`; then the rest. A popover has to be in front of the hovers or a hover cover steals clicks from the open popover. Remove every parameter control you showed for testing (`p_PeriodOpen`, `p_GroupOpen`, `p_ViewTab`) and any colour legend Tableau added.

### 14.8 Actions (38 Change Parameter + 21 Deselect = 59; today 32 + 21 = 53)

Dashboard > Actions. Every Change Parameter action: **Run action on Select**, clearing the selection **Keep current value**, source = the dashboard and the single sheet named, aggregation as offered.

| # | Name | Source sheet | Target parameter | Source field | Status |
|---:|---|---|---|---|---|
| 1 | Open period panel | Period Field | `p_PeriodOpen` | `Toggle Period Panel` | keep |
| 2 | Period opens, group closes | Period Field | `p_GroupOpen` | `Close Panel` | keep |
| 3 | **Period opens, info closes** | Period Field | `p_InfoOpen` | `Close Panel` | **new (R2)** |
| 4 | Set span | Span List | `p_Span` | `Span Value` | keep |
| 5 | Set From | Period Panel | `p_From` | `from_month_end` | keep |
| 6 | Set To | Period Panel | `p_To` | `to_month_end` | keep |
| 7 | Close on pick | Period Panel | `p_PeriodOpen` | `Close Panel` | keep, rename `Close period on pick` |
| 8 | Close period on ✕ | Popover Close | `p_PeriodOpen` | `Close Panel` | keep |
| 9 | Open group panel | Group Field | `p_GroupOpen` | `Toggle Group Panel` | keep |
| 10 | Group opens, period closes | Group Field | `p_PeriodOpen` | `Close Panel` | keep |
| 11 | **Group opens, info closes** | Group Field | `p_InfoOpen` | `Close Panel` | **new (R2)** |
| 12 | **Open group on its view** (#3 action 31) | Group Field | `p_ViewTab` | `view_name` | **new** |
| 13 | **Browse view** (#3 action 13) | View List | `p_ViewTab` | `view_name` | **edit `Set view`**: change the target from `p_View` to `p_ViewTab`; rename |
| 14 | **Apply group for All organizations** (#3 action 14) | View List | `p_Group` | `Group Apply From View` | **edit `Set group from view`**: change the field from `Default Group`; rename |
| 15 | **Apply view for All organizations** (#3 action 32) | View List | `p_View` | `View Apply` | **new** |
| 16 | Keep group panel open | View List | `p_GroupOpen` | `Keep Group Panel Open` | keep, rename from `Keep panel open unless All` |
| 17 | Set group | Group Panel | `p_Group` | `group_name` | keep |
| 18 | **Apply view on group pick** (#3 action 33) | Group Panel | `p_View` | `view_name` | **new** |
| 19 | Close on group pick | Group Panel | `p_GroupOpen` | `Close Panel` | keep |
| 20 | Close group on ✕ | Popover Close Group | `p_GroupOpen` | `Close Panel` | keep |
| 21 | Set worker | Workforce Toggle | `p_Worker` | `Worker Pick` | keep |
| 22 | Set detail | Detail Toggle | `p_Expand` | `Detail Pick` | keep |
| 23 to 29 | Reset from / to / span / view / group / worker / expand | Reset | `p_From`, `p_To`, `p_Span`, `p_View`, `p_Group`, `p_Worker`, `p_Expand` | the `Default ...` calcs | keep |
| 30 | **Reset view tab** (#3 action 23b) | Reset | `p_ViewTab` | `Default View` | **new** |
| 31 to 33 | Reset closes popovers 1 to 3 | Reset | `p_PeriodOpen`, `p_GroupOpen`, `p_InfoOpen` | `Close Panel` | keep |
| 34 | Open info | Info | `p_InfoOpen` | `Toggle Info` | keep |
| 35 to 36 | Info opens, period closes / Info opens, group closes | Info | `p_PeriodOpen`, `p_GroupOpen` | `Close Panel` | keep, rename from `Info opens, others close 1 / 2` |
| 37 | Close info on ✕ | Popover Close Info | `p_InfoOpen` | `Close Panel` | keep |
| 38 | Set collapse | (as saved) | `p_Expand` | (as saved) | leave alone |

That is **6 new** (3, 11, 12, 15, 18, 30), **2 edited** (13, 14), the rest kept: 32 + 6 = **38**. The 21 Deselect actions already cover every sheet used here (`Span List`, `Period Panel`, `View List`, `Group Panel`, `Group Heading 2`, the three Close sheets, the fields); nothing new is needed.

**How a View List click now runs** (three actions fire on the one click): 13 sets the tab; 14 and 15 set `p_Group` and `p_View` to the values they already hold, except on All organizations, where they set Arcadia Systems and Company; 16 keeps the popover open (True) except on All organizations, where it closes (False). So Function, Sub-function, Department and Country only browse. **A Group Panel click** fires 17 (group), 18 (the view that group belongs to) and 19 (close), so view and group arrive together. Six names exist in two views (Finance, Legal & Compliance, Marketing, Operations, People, Product), which is why 18 reads `view_name` from the clicked mark.

### 14.9 Expected values

Page numbers do not change (section 11 stands). What is new is *when* they change and what the popovers show.

| State | Expect |
|---|---|
| Open, nothing clicked (FY26, All organizations) | Opening 28,438, closing 30,005. Capsule `FY26 · Jun 25 to Jun 26`; field `All organizations` |
| Group popover, View List | 5 items on slots 1, 3, 5, 7, 9: All organizations (› and white while browsing), Function, Sub-function, Department, Country. No gap, no Office |
| Click **Function** | List shows `›` on Function; grid shows 8 names (3, 3, 2). **The page does not move**: still 28,438 to 30,005, field still All organizations |
| Click **Commercial** | Popover closes; field `Commercial`; opening 7,441, closing 7,795; turnover by sub-function |
| Click Sub-function (popover reopened on the Function tab, Commercial applied) | 10 names (4, 4, 2). `Marketing`, `Finance` and the other four shared names are **not** white here, because the applied view is Function; each is white only on the tab of the view in use |
| Department | 31 names (11, 11, 9). Click Accounting & Controllership: 543 to 560 |
| Country | 22 names (8, 8, 6). Click India: 6,672 to 6,967 |
| Click **All organizations** from any tab | Applies at once, popover closes, page back to Company numbers |
| Reset | FY26, All organizations, Employees, compact; popovers closed; reopening the Group popover starts on the All organizations tab with an empty grid |
| Period popover | Fiscal year: 4 by 4 block from the top, level with "Fiscal year". Year to date: 2 by 4. Quarter: 4 by 4 (FY26 Q4 top-left). Month: 6 by 8. Click Quarter, then FY26 Q4: closes, opening 29,618, closing 30,005 |

### 14.10 Click tests

| # | Do | Expect |
|---:|---|---|
| 1 | Open Period | Left edge level with `SELECT PERIOD`, right edge under the info button; title 16 px in; line 16 px short of each edge; footer note; bottom corners round, top corners square against the band |
| 2 | Fiscal year, Year to date, Quarter, Month | Rows start at the top each time and never float to the middle; Month fills six rows |
| 3 | Open Group, then Period | Only Period is open (Group closed by action 2) |
| 4 | Open Period, then Info, then Group | One open at a time; with Info open, opening Period closes Info (R2) |
| 5 | Group, click Function | Tab changes, **page does not change**, popover stays open |
| 6 | Click Commercial | Closes, page changes to 7,441 / 7,795 |
| 7 | Reopen Group | Opens on the Function tab with Commercial white |
| 8 | Marketing check: Function, Marketing; reopen; Sub-function tab | Marketing not white on Sub-function |
| 9 | Department, Country, All organizations | Values per 14.9; no click lands on a default group |
| 10 | Click every control, the title, the KPI band | No blue box or outline stays |
| 11 | Reset | Everything back; reopen Group: All organizations tab, empty grid |
| 12 | Info | Header 44, line, body unchanged; ✕ closes |

### 14.11 My review of the saved .twb (before you publish)

Save the workbook, tell me, and I read the file. I check these and report pass or fail for each:

| Check | Expect |
|---|---|
| Parameters | **27**: the 26 now plus `p_ViewTab` (String, list of 5, Company); none named "(copy)"; `kpi_` values unchanged (FitX 1.082, ShiftX -12) |
| Parameter actions | **38** with the targets and fields in 14.8; **21** deselects; none with a missing source sheet except `Set collapse` |
| Dangling references | No calc points at a deleted field (`Panel Shows Groups`); no `Calculation_` id without a definition; no red calc |
| Arrows | No arrow glyph (U+2192) in any calc, label or text object a viewer can see |
| Stray colour legend | No colour-legend zone on the dashboard (adding `Span Is Current` and `View Is Current` to Color can drop one) |
| Dashboard zones | Popover positions and sizes as 14.3; image objects present with Fit Image; old `Info Panel` gone; popovers in front of the hovers |
| Navy | The band and the popovers use `#13233A` |
| Controls | No parameter control (`p_PeriodOpen`, `p_GroupOpen`, `p_ViewTab`) left on the page |
| Sheet specifics | `Span List`, `View List`, `Period Panel`, `Group Panel`: Text marks, continuous slot pill, axis 0 to 12 or 0 to 22, reversed, header hidden; `Group Panel` filter is `Group Grid Rows`; `View List` Detail has no `Default Group` |

### 14.12 Order of work, then publish and repo

1. Mac: backup (14.4).
2. Parameter and calcs (14.5), checkpoint P1.
3. Sheets (14.6), checkpoint P2.
4. Dashboard (14.7), one popover at a time; click test 1 and 2 after Period, 5 to 9 after Group, 12 after Info.
5. Actions (14.8).
6. Click tests 3, 4, 10, 11.
7. Save, send me the file for 14.11.
8. Publish: reset, close popovers, hide helper sheets, **File > Save to Tableau Public As...** `arcadia_headcount_fte_walk` (same name keeps the URL). Check the published page with the 14.10 table.
9. Repo: new screenshot to `docs/images/` for the README row; section 0 of the case-study README mentions the browse-first picker; this section's status line.

### 14.13 What this section does not touch

The data sources and Custom SQL; the waterfall, KPI cards, trend, turnover and tie-out; the header layout (6.8); the other `Reset` defaults (only `Default Group` changes, and `p_ViewTab` is added to the reset); Dashboard #2 (its rail is a different shape and gets its own pass, with one open decision on what a rail view click does); and any number on the page.

### 14.14 As built, and what to carry forward

Published Oct 24, 2026 at the same URL. These are the differences from the plan above, in the order they came up.

1. **Drawn-chevron capsule.** `d1_field_capsule` now has the chevron drawn into the image (generator `docs/brand/build/make_d1_d2_chevrons.py`; `d2_field_capsule` got the same). #1's capsule is 180 px wide (#3's is 200), so the chevron sits **12 px** from the right edge instead of 18, which leaves the label about 11 px of clearance. The labels are one run each, `<Period Field Text>` or `<Group Field Text>`, Tableau Semibold, navy, Center and Middle, with no typed `▾`, no trailing spaces and no stray glyph. Two calc changes keep the text short: `Group Field Text` cuts at 17 letters plus "…" (`IF [p_View] = "Company" THEN "All organizations" ELSEIF LEN([p_Group]) > 18 THEN LEFT([p_Group], 17) + "…" ELSE [p_Group] END`), and `Period Field Text` is `REPLACE([Pair Name], " to ", " – ")`, which saves about 8 px (the grid and subtitles keep "to"). Shape: `Arcadia D1 > d1_field_capsule`, Size slider all the way right.
2. **Info button is only an "i".** Taking the ✕ glyph off the button (it swapped on `Info Shape` while the popover was open) was a request after the first build: the popover's own ✕ (`Popover Close Info`, action 37) closes it. The `Info` sheet has no `Info Shape` on the Shape shelf and a single shape. Clicking the "i" while the popover is open still toggles it shut (`Toggle Info`), which is harmless.
3. **Info popover is taller on Tableau Public.** The text was cut off at the bottom online although it fit in Desktop (the web renders the Book 10 body slightly wider and wraps more). It was published at **x 960, y 76, w 408, h 600** instead of 410 x 571 (body 547 instead of 518). Rule for #2 and #3: after publishing, open the Info popover on the web and leave at least 15% spare height. If you republish from your local file, apply the same size there first, or the next publish brings back 571.
4. **Group footer.** A footer text object needs a **fixed height** to hold 28 px: left alone, Tableau sized it to 25 px with a 4 px outer margin. Set Outer padding 0, Inner padding left 16 and top 6, and the height 28 (the Period footer was already correct).
5. **One navy, typed.** The Tableau colour picker rounds: typing `#13243A` into the Info popover background saved as `#132539`, one unit off and invisible, with no border. The Header Band and the Period and Group popovers are `#13243A`; the published navy is therefore not the `#13233A` in R4 above (same as #2).
6. **`Info` tooltip toolbar (to fix on the next dashboard).** On Tableau Public, hovering the Info button shows the "Keep Only / Exclude" command toolbar. Cause, found in the saved .twb: the `Info` sheet's tooltip has command buttons on (`<customized-tooltip>`), while `Reset`, `Period Field`, `Group Field`, `Workforce Toggle` and `Detail Toggle` have them off (`show-buttons='false'`). Fix: `Info` sheet > Tooltip > untick **Include command buttons**. #2's `Info Button` and `Group Panel` have the same default. Not changed in this release.
7. **`View List` Detail.** `Default Group` and `Close Panel` were left on its Detail; nothing reads them there, so it is harmless, and 14.6 says to remove them.
8. **Counts as built.** 38 Change Parameter actions and 21 Deselect, 27 parameters; no arrows anywhere in calcs, labels or text.
