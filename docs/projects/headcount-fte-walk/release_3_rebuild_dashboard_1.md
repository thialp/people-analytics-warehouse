# Release 3 rebuild: Dashboard #1, Headcount & FTE Walk

Step-by-step rebuild of [arcadia_headcount_fte_walk](https://public.tableau.com/app/profile/thialp/viz/arcadia_headcount_fte_walk/ExecutiveSummary) on the release 3 data, so it works and reads like Dashboard #2 (Compensation Walk), keeps its own **top bar**, and shows **the same numbers** wherever the two dashboards show the same thing. Arcadia Systems is fictional and all data is synthetic.

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
| `fld_top.png` | 180 × 32 | #1 Period and Group fields (white capsule, same radius as the toggle) |
| `fld_rail.png` | 200 × 30 | #2 Period and Group fields (`#E4E3DD`, rounded like the toggles) |
| `seg_worker_employees_on/off`, `seg_worker_contingent_on/off`, `seg_worker_total_on/off` | 80 × 32 each | #1 Workforce toggle (capsule `#243A57`) |
| `btn_reset_top_label.png` | 184 × 32 | #1 Reset (outlined capsule: arrow + "Reset to default view") |
| `btn_reset_top.png` | 32 × 32 | Spare: arrow only, for a narrow header |
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
// Page Subtitle  [p_Group] + " · " + [Worker Words] + " · data as of " + "Jun 30, 2026"
// TT Open Day    LEFT(DATENAME('month',[p_From]),3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))
// TT Close Day   LEFT(DATENAME('month',[p_To]),3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))
```
`TT Open Day` and `TT Close Day` are used here, in 8.2 and in section 9; create them now (both on Headcount Walk) and skip them there.
(Optional later: read the as-of date from Region Walk's `report_as_of_date` with the blend, as #2 does.)

Text mark; Text: line 1 `Headcount & FTE Walk` Tableau Bold 18 white; line 2 `<Page Subtitle>` Tableau Book 8 `#C9D1DC` (Book 9 clips at 275 px wide: "data as of Jun 3…"). Detail `zzTrue`, `zzFalse`, `Title Tip`. Shading None. Dashboard item 285 × 58, Entire View. Line 2 stays on one line at this width; a long group name wraps to a second line.

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

Gaps are 12 px between controls and 16 px between the logo/title and the fields; the logo sits on the left edge of the page grid (x 30) and Info on the right edge (1370). The whole page uses a **30 px margin** so the banner and the body are the same width. **Corners and borders.** The capsules only look round if nothing square sits behind them. For `Period Field`, `Group Field`, `Workforce Toggle`, `Reset` and `Info Button`: Worksheet > Format > Shading > **Worksheet: None** (and Row/Column bands None), Format > Borders > all **None**; on the dashboard select the item > Layout pane > **Border: None**, **Background: None**. The toggle's dark capsule comes from the shape itself, so it needs no border or fill from Tableau. Info shares the Reset's thin translucent outline so the two read as one family.

Delete any parameter control (`p_InfoOpen`, `p_Worker`, `p_From`, `p_To`) and shape legend (`Info Shape`) left on the dashboard: they are helpers for the actions, not part of the page. The Page Title text is **white**.

---

## 7. Popovers

### 7.1 Period popover (copy of #2's)

Each popover opens directly under its own control (left edge aligned with the field, top at y 76, the bottom of the band); the Info panel is right-aligned to the page margin (x 990, right edge 1370).

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

The top bar has no room for #2's six-row view list, so the view list moves into the popover, laid out like the period popover (choice of kind on the left, options on the right).

1. Sheet `View List` (Region Walk): Marks **Text**. Rows: `view_name`, sorted by `view_order` (Field, Minimum). Text: `View Display`. Filter `View Offered` = True and `Period Is Current` = True. Detail: `view_name`, `Default Group`, `zzTrue`, `zzFalse`. Font Tableau Book 10 `#B8C0CC`; the current row Semibold white (Color: `ATTR([view_name] = [p_View])`, True white, False `#B8C0CC`). Headers hidden, shading None, tooltip off.
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

One per sheet: `Period Field`, `Group Field`, `Workforce Toggle`, `Reset`, `Info Button`, `Span List`, `Period Panel`, `View List`, `Group Panel`, each `Popover Close`, `Btn Expand Text`, `Btn Expand Icon`, `Btn Collapse Text`, `Btn Collapse Icon`, `Page Title`, `KPI cards`, `Waterfall Caption`, `Group Heading 2`. Add `zzTrue` and `zzFalse` to each sheet's Detail first. The charts (Waterfall, Trend, Turnover) keep normal selection: clicking a bar to highlight it is useful there.

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
```
// Expand Label     "Expand · " + STR([WF Driver Count]) + " drivers"
// Collapse Label   "Collapse · " + STR([WF Group Count]) + IIF([WF Group Count] = 1, " group", " groups")
```

Edit the existing waterfall calcs: in `Waterfall Position`, `Bar Type`, `Move Label`, `Level Label` and `TT Context`, replace `ATTR([Movement Category])` by `ATTR([WF Bar])`. Delete `Show Category`.

Sheet `Waterfall`:

1. Columns: replace `Movement Category` with `WF Bar`; sort **Field** `WF Order`, Minimum, Ascending.
2. `Waterfall Position`: Edit Table Calculation > Specific Dimensions > `WF Bar` only.
3. Filters: `WF Moves Hidden` = False (dimension filter), and a calc `WF Non Zero` = `SUM([Walk Value]) <> 0 OR ATTR([WF Bar]) = "Opening" OR ATTR([WF Bar]) = "Closing"` = True (drops the zero bars: Moved at Company, Converted in Total). A zero bar adds nothing to the running sum, so dropping it does not move the others.
4. Aliases on `WF Bar` (right-click > Aliases): Voluntary Terminations → `Voluntary leavers`, Involuntary Terminations → `Involuntary leavers`, Internal Moves In → `Moved in`, Internal Moves Out → `Moved out`, Conversions → `From contingent` (Employees) — in Contingent it reads "Conversions" (−270), which is clear on its own.
5. Axis: Include zero (headcount waterfalls start at zero; keep the published choice), ticks Automatic (a fixed 5,000 tick is wrong for a 543-person department), format `#,##0`. If the expanded chart shows too many labels, raise the axis font to Tableau Book 10 (Format > Scale) or hide the axis header: every bar has its value. Never set a fixed interval.
6. Title line 2 (Book 9 slate): `Opening + joined − left ± moves = closing · axis starts at zero`.

Expand / Collapse buttons: copy #2's construction (build_status.md, "Expand / Collapse look like buttons"): two horizontal containers `Btn Expand ALL` and `Btn Collapse ALL`, identical size **150 × 24**, each = a text sheet (`Expand Label` / `Collapse Label`, Semibold 9 navy) + an icon sheet (`btn_expand_icon` / `btn_collapse_icon`, 16 × 16). Calcs `Expand To` = TRUE and `Collapse To` = FALSE, on Detail with `zzTrue`, `zzFalse`; actions **Set expand** (`p_Expand` ← `Expand To`) from both Expand sheets and **Set collapse** (`p_Expand` ← `Collapse To`) from both Collapse sheets. Visibility, as on #2: `Btn Collapse ALL` > **Control visibility using value** = `p_Expand`; `Btn Expand ALL` > Control visibility using value = calc `Is Compact` (= `NOT [p_Expand]`). Both sit on the same spot at the waterfall card's top right (section 10).

### 8.2 KPI cards

#### 8.2a Wider cards (30 px margin)

The cards now span the full page grid (x 30 to 1370): five cards 255 wide with 16 gaps. Use the new background `docs/brand/arcadia_kpi_cards_bg_wide.png` (2800 × 220; generated with `make_kpi_cards_bg.py --left 30 --top 12 --card-w 255 --card-h 86 --gap 16 --radius 10`) as the background image item (0, 78, 1400 × 110). Set the KPI parameters: `kpi_GridLeft` 30, `kpi_CardW` 255, `kpi_GapX` 16 (others unchanged: GridTop 12, CardH 86, PadX 16). Tableau pads the map extent, so check that each title starts 16 px inside its card; if all five drift the same way nudge `kpi_FitX` by 0.01 (and `kpi_ShiftX` for a constant offset), as in the KPI guide, section 6.

Card set per toggle value. The map layers and 15 anchors stay as built; only the text calcs change.

| Card | Employees | Contingent | Total |
|---|---|---|---|
| 1 Title / value | Closing headcount · 30,005 | Closing contingent · 11,941 | Total workforce · 41,946 |
| 1 Note | **+5.5%** from 28,438 on Jun 30, 2025 | **+11.5%** from 10,707 | **+7.2%** from 39,145 |
| 2 Title / value | Joined · 5,235 | Started · 7,033 | Joined · 11,998 |
| 2 Note | 4,965 hires · 270 from contingent | 6,907 new · 126 returned | 4,965 hires · 7,033 starts |
| 3 Title / value | Voluntary turnover (annualized) · 10.1% | same (employees) | same (employees) |
| 3 Note | 2,942 left by choice · 726 involuntary | Employees; contingent ends: 5,529 | Employees; contingent ends: 5,529 |
| 4 Title / value | Internal moves · 3,633 | Internal moves · 336 | Internal moves · 3,969 |
| 4 Note | 2,015 promotions · 1,618 other moves | between teams | 2,015 promotions · 1,954 other |
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
// K Moves       ZN(SUM(IF [In Range] AND [Movement Category] = "Internal Moves In" THEN [Headcount] END))
```
```
// K CW Close    (contingent at close, whatever the toggle: card 5)
ZN(SUM(IF [In Period] AND [Officers Out] AND [In Group] AND [Worker Type] = "Contingent" AND [Is Closing Row] THEN [Headcount] END))
// K EE Close    same with [Worker Type] = "Employee"
// K All Close   [K CW Close] + [K EE Close]
// K CW Share    IF [K All Close] = 0 THEN 0 ELSE [K CW Close] / [K All Close] END
```

`KPI 2 Value`, `KPI 2 Note` and `KPI 5 ...` replace the old FTE card; `KPI 3 Title` becomes `"Voluntary turnover (annualized)"`, and cards 1 to 5 titles use `CASE [p_Worker]` per the table. `KPI 1 Note Rest` becomes `"from " + [K Open Str] + " on " + [TT Open Day]` where `TT Open Day` = `LEFT(DATENAME('month',[p_From]),3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))`.

Group view note: "Internal moves" in a group counts moves **into** its teams, from other teams inside or outside it (Commercial FY26: 948 in, 933 out). Card 4 note for a group: `"948 in · 933 out, including moves between its own teams"`.

### 8.3 Trend and Turnover

**Trend:** add `Trend Value` = `IF [Officers Out] AND [In Group] AND [Worker In Scope] AND [Movement Category] = "Closing" THEN [Headcount] END` and put `SUM([Trend Value])` on Rows instead of `SUM([Selected Value])`. Band: `Band Start` = `[p_From]` (EDIT: the band now starts on the opening month-end). Title calc `Trend Title` = `"Closing " + CASE [p_Worker] WHEN "Employees" THEN "headcount" WHEN "Contingent" THEN "contingent workers" ELSE "workforce" END + " by month-end"`. Remove the hard-coded "FY24 restructuring" annotation or keep it only for Company (it marks a company event).

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
Replace `Function Name` on Rows with `TO Dim`; `TO Top Function` → rename `TO Top`, `LOOKUP(ATTR([TO Dim]), FIRST())`, Compute Using `TO Dim`. Title: `[TO Top] + " has the highest turnover in " + [Period Name]` (see 8.5). Subtitle unchanged, plus "employees" when the toggle is not Employees: `Voluntary + Involuntary leavers ÷ average headcount, annualized · employees`.

### 8.4 Info popover (replaces the white Info Panel)

Container `Info Popover`, navy style (0.5), **x 990, y 76, w 380, h 470**, visibility `p_InfoOpen`, front. Header row: title "How to read this page" + ✕ (`Popover Close` for info). Body (one Text object, 10 pt):

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
`WF Period` → replace its formula with `[Period Name]`. `WF Title` for Employees stays the published sentence; for Contingent: `[Period Name] + ": " + starts + " starts, " + ends + " ends, net " + ...`; for Total: `[Period Name] + ": " + joined + " joined, " + left + " left, adding " + net + " people"`.

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
// TO Still Here  ZN([Region Walk].[RW Hires Still Here])
// TO Gap         [TO Joined] - [TO Still Here]
```
Tableau has no comma function, so each number gets a text calc (same pattern each time):

```
// TO Joined Text
IF [TO Joined] >= 1000 THEN STR(INT([TO Joined] / 1000)) + "," + RIGHT("00" + STR(INT([TO Joined]) % 1000), 3)
ELSE STR(INT([TO Joined])) END
// TO Still Here Text   (same, with [TO Still Here])
// TO Gap Text          (same, with [TO Gap])
// TT Close Day         LEFT(DATENAME('month',[p_To]),3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))
```
```
// Tie-out Text   (starts with "Note:"; one line; the same two numbers as Dashboard #2, seen from this page)
IF [p_Worker] <> "Employees" THEN "Note: the Compensation Walk covers employees only."
ELSEIF [p_View] = "Company" THEN
    "Note: the Compensation Walk counts only people still here on " + [TT Close Day] + ": " + [TO Still Here Text] +
    " of the " + [TO Joined Text] + " who joined (" + [TO Gap Text] + " left again)."
ELSE
    "Note: the Compensation Walk counts only people still here on " + [TT Close Day] + ": " + [TO Still Here Text] +
    " of the " + [TO Joined Text] + " who joined " + [p_Group] + "."
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
    "In the Compensation Walk's Hires: " + [TO Still Here Text] + ", the ones still there on " + [TT Close Day] + "." + CHAR(10) +
    "Not in that walk: " + [TO Gap Text] +
    (IF [p_View] = "Company"
     THEN ", who joined and left again before " + [TT Close Day] + "."
     ELSE ", who left Arcadia or moved to another team before " + [TT Close Day] + "." END)
END)
```
`Waterfall Caption`: `Tie-out Detail` on Detail; Worksheet > Tooltip: bold **Why the two dashboards count different hires**, `<AGG(Tie-out Detail)>`, then "The Compensation Walk compares two snapshots and prices people present on each date, so anyone who joined and left in between is in neither. This page counts every joiner and every leaver." (Book 9; no command buttons). FY26 Company: "5,235 people joined Arcadia between Jun 30, 2025 and Jun 30, 2026 … In the Compensation Walk's Hires: 4,790 … Not in that walk: 445, who joined and left again before Jun 30, 2026."

Caption layout: line 1 the existing moves sentence (`WF Caption`, edited: delete the "FTE ... schedule changes" half), line 2 `<Tie-out Text>`. Tableau Book 8 slate, left. Same position as today (over the waterfall's bottom padding).

| Selection | Tie-out text |
|---|---|
| FY26, Company | Note: the Compensation Walk counts only people still here on Jun 30, 2026: 4,790 of the 5,235 who joined (445 left again). |
| FY26 Q4 (Mar 31 → Jun 30, 2026), Company | Note: the Compensation Walk counts only people still here on Jun 30, 2026: 1,317 of the 1,330 who joined (13 left again). |
| FY26, Function Commercial | Note: the Compensation Walk counts only people still here on Jun 30, 2026: 1,309 of the 1,470 who joined Commercial. |

If the secondary number shows blank: the link is not active (click the link icon next to `Link` in the Region Walk pane) or a filter on the primary sheet removed `Link`.

---

## 10. Dashboard layout (1400 × 850, every object floating)

| # | Object | x | y | w | h | Note |
|---|---|---:|---:|---:|---:|---|
| 1–11 | Header (6.8) | | | | | |
| 12 | KPI background image | 0 | 78 | 1400 | 110 | new wide image (8.2a) |
| 13 | KPI cards | 0 | 78 | 1400 | 110 | geometry parameters per 8.2a |
| 14 | Waterfall | 30 | 188 | 806 | 624 | unchanged; bottom padding 64 |
| 15 | Btn Expand ALL / Btn Collapse ALL | 686 | 198 | 150 | 24 | Same spot; one visible at a time |
| 16 | Waterfall Caption | 42 | 750 | 782 | 56 | Two lines now |
| 17 | Trend | 852 | 188 | 518 | 300 | unchanged |
| 18 | Turnover | 852 | 500 | 518 | 312 | unchanged |
| 19 | Footnote (Text object) | 30 | 822 | 600 | 16 | "Arcadia Systems is a fictional company. All data is synthetic." Book 8 slate |
| 20 | Period / Group / Info popovers | 7.1, 7.2, 8.4 | | | | Front, hidden |

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
| Waterfall compact | Opening 28,438 · Joined +5,235 · Left −3,668 · Closing 30,005 · "Expand · 4 drivers" · "Collapse · 2 groups" |
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

**Cross-check with Dashboard #2 (must be identical):** FY26 Company 28,438 → 30,005; Commercial 7,441 → 7,795; Accounting & Controllership 543 → 560; India 6,672 → 6,967; Q4 29,618 → 30,005. Hires still here: Company 4,790, Commercial 1,309, Accounting & Controllership 73, India 1,038, Q4 1,317.

---

## 12. Test and publish

| # | Do | Expect |
|---|---|---|
| 1 | Hover every button and field | Outline or nothing; never a small square. Tooltips on Period, Group, Reset, Info |
| 2 | Click each toggle option, Expand, Collapse, a title, the KPI band | Nothing stays highlighted |
| 3 | Open Period, then Group, then Info | Only the last one is open |
| 4 | Period > Quarter > FY26 Q4 | Field "FY26 Q4", opening 29,618, closing 30,005 |
| 5 | View > Function > Commercial | Title "Commercial · employees · data as of Jun 30, 2026"; numbers per section 11; turnover by sub-function |
| 6 | Total | Card 1 41,946; waterfall Joined 11,998, Left 9,197; note "The Compensation Walk covers employees only." |
| 7 | Reset | FY26, Company, Employees, compact, all popovers closed |
| 8 | Same selections on Dashboard #2 | Same opening, closing and "still here" numbers |

Publish: reset the dashboard, hide all sheets, **File > Save to Tableau Public As...** `arcadia_headcount_fte_walk` (same name keeps the URL), extracts only. Check the page in the browser with the test table, Tableau Public row by row.
