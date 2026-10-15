# Global Workforce Footprint: build guide, starting from the Compensation Walk workbook

> **Warehouse release 3:** part-time was removed (every employee is 1.0 FTE), so part-time counts and the FTE Changes step described here no longer exist in the data. This guide describes the dashboard as built on release 2; what changes is listed in [release 3 migration notes](../contingent-workforce/release_3_migration_notes.md).


Dashboard for case study 3. You copy the Compensation Walk workbook, point it at one new Custom SQL, keep the rail and the KPI cards, delete the pay pieces, and build three new cards: a larger, more efficient map, Top drivers of headcount change, and Growth by region / country / office. Arcadia Systems is fictional and all data is synthetic.

Everything below was checked against the warehouse: the new query was run in the DuckDB copy of the SQL Server build (`sqlserver/check_tsql_in_duckdb.py` translation) and ties out, and every expected value in this guide comes from that run. The SQL Server run on your Mac (Part 1) is still the final check.

**Files that come with this guide**

| File | Where it goes |
|---|---|
| `tableau/custom_sql_workforce_footprint.sql` | the new data source (Part 2) |
| `sqlserver/11_validate_workforce_footprint.sql` | SQL Server check (Part 1) |
| `docs/brand/build/make_footprint_toggle_shapes.py` and the 16 `seg_fp_*.png` shapes | rail toggles (Part 6) |

---

## Part 0. What changes and why (read once)

### 0.1 Your plan, with one correction

Your plan works: **Save As** the Compensation Walk, swap the data source, delete what the footprint does not use, and reuse the rail, the KPI cards and the card patterns. One correction: the new workbook uses **one** data source, not two.

- **Why one source.** A map's layers must all come from the same data source. The office bubbles need headcount by office, and the route lines need moves. In the Compensation Walk they came from two sources (walk, Office Moves), which is why the map could only show arrival dots and not headcount. The new query returns both, as two row types (`row_type` = `Office` or `Route`), so offices, routes and the radius ring are layers of one map.
- **Why Replace Data Source still works.** The new query keeps every column name the rail reads (`from_month_end`, `to_month_end`, `pair_type`, `view_name`, `group_name`, `step`, ...), and it has `Opening` and `Closing` steps, so the Period picker, View list, Group picker, toggles and Reset come across untouched. Replace Data Source maps fields by name (the lesson from release 2).

### 0.2 Decisions I made (change them if you disagree, before you build)

1. **Executive officers are excluded** (9 people), exactly like the walk, office moves and region walk. This keeps the Group lists identical to the Compensation Walk. FY26 is **28,438 → 30,005**; Dashboard #1, which keeps them, shows 28,447 → 30,014.
2. **Hires and exits compare two snapshots** (From and To), like the Compensation Walk. Someone hired and gone inside the period is in neither. FY26 shows **4,790 hires**; Dashboard #1 shows 5,235 because it sums month by month (445 people joined and left within the year: 354 voluntary, 91 involuntary). The Methodology line says so.
3. **Top drivers ranks by net effect on the group**, ties broken by how many people were involved. In and Out of the same kind are **one driver** (for example "Moves within a country"), so at company level a move shows as "600 moved, net 0" instead of a +600 and a −600 that cancel. This is how relocation gets onto the card even when it does not change the total.
4. **Growth by region / country / office is one sheet**, not three sheets with Dynamic Zone Visibility. A calculated dimension (`Geo Name`) swaps level with a parameter (`p_Geo`), so there is one sort, one format and one tooltip to maintain, and the swap is instant. You still get a three-option toggle in the card header. If you prefer three sheets with DZV, the calcs are the same; only `Geo Name` is replaced by `region`, `country_name`, `office_name`.
5. **Growth card bars show people added (net change)**, not growth %, and list the six largest changes. Growth % ranks tiny new offices first (Vancouver +345%); people added shows where the footprint actually grew. The percent stays in the label.
6. **Map colors use annualized growth in fixed bands**, so a month or a quarter is colored on the same scale as a year, and colors mean the same thing in every period (no Tableau 2025.2 color-range feature needed).
7. **No filled-country layer.** Country polygons include Alaska, Hawaii and northern Canada, and the map frames itself on its marks (Part 8), so a US polygon would stretch every frame to the Bering Sea. Coastline and borders only, as in the Compensation Walk.

### 0.3 Inventory: reuse, change, new, delete

| Piece in the Compensation Walk | Footprint | Part |
|---|---|---|
| Rail: logo, Period field and popover (`Period Field`, `Span List`, `Period Panel`, `Period Close`), View list (`Rail View`), Group picker (`Group Field`, `Group Panel`, `Panel Close`, `Group Heading`, `Group Heading 2`), dividers, footnote | **Reuse as is** | 6 |
| `Lens Toggle` (Avg per FTE / Total payroll) | **Change**: Headcount / FTE | 6.1 |
| `Cost Toggle` | **Change** into `Routes Toggle` (All / 3+ / 10+) | 6.2 |
| `Currency Toggle` | **Change** into `Radius Toggle` (500 km / 1,000 / 2,000) | 6.3 |
| `Reset` | **Change**: new defaults | 6.4 |
| `Info Button` + `Info Popover` | **Change**: text only | 6.5 |
| Page title and `Page Subtitle` | **Change** | 6.6 |
| KPI cards sheet (map sheet with text layers) + background image | **Reuse the sheet**, new value and note calcs, new typed titles | 7 |
| Waterfall sheets (`Waterfall Compact`, `Waterfall Expand`), their title/subtitle sheets, `Btn Expand ALL` / `Btn Collapse ALL` containers and their text and icon sheets | **Delete** | 4 |
| `Top Drivers` sheet | **Rebuild in place** (same name-above-bar pattern, new calcs) | 9 |
| `Office Moves Map` | **Delete**; new `Footprint Map` | 8 |
| `Office Moves Title`, `Office Moves SubTitle` | **Delete**; new `Map Title`, `Map Subtitle`, `Growth Legend`, `Map Key` | 8 |
| `Top Corridors` | **Delete** (busiest route moves into the drivers card and the map subtitle) | 4 |
| `Region Headcount` / `Region Bars` | **Rebuild in place** as `Geo Growth` (one sheet, three levels) | 10 |
| Office Moves data source | **Close** after its sheets are gone | 4 |
| Parameters `p_From`, `p_To`, `p_View`, `p_Group`, `p_Span`, `p_GroupOpen`, `p_PeriodOpen`, `p_InfoOpen`, the 16 `kpi_` parameters | **Reuse** | 5 |
| `p_Lens` | **Change** values | 5 |
| `p_Cost`, `p_Currency`, and any expand/panel parameter (`p_Expand`, `p_Panel`) | **Delete** | 4 |
| New parameters `p_Routes`, `p_RadiusKm`, `p_FocusOffice`, `p_MapFocus`, `p_Geo` | **New** | 5 |

---

## Part 1. SQL Server: add and check the query (Mac terminal)

Copy the two SQL files into the repo first (`tableau/custom_sql_workforce_footprint.sql`, `sqlserver/11_validate_workforce_footprint.sql`), then:

```bash
cd ~/GitHub/people-analytics-warehouse
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/11_validate_workforce_footprint.sql
```

Expected (the seconds will differ; the region walk and office moves run beside it so the ties can be checked):

```
Workforce footprint Custom SQL returned 666272 rows in N seconds
Region walk Custom SQL returned 26520 rows in N seconds
Office moves Custom SQL returned 89611 rows in N seconds
1. Shape
office rows 576679 576679 PASS · route rows 89593 89593 PASS · date pairs 88 88 PASS
views 6 6 PASS · groups 107 107 PASS · rows without a map point 0 PASS · rows without a group name 0 PASS
2. Closes and ties (every check expects 0)
offices whose headcount walk does not close 0 PASS · offices whose FTE walk does not close 0 PASS
views whose groups do not add up to the company 0 PASS · company pairs where routes differ from office moves in 0 PASS
region lines that differ from the region walk 0 PASS · route lines that differ from office moves 0 PASS
3. FY26, Company
opening headcount 28438 · hires 4790 · voluntary exits 2588 · involuntary exits 635
office moves (one country) 600 · cross-border moves 125 · closing headcount 30005
closing FTE x 10 293545 · offices with people 35 · route lines 155        (all PASS)
```

If any line fails, stop and send me the output.

**How the query is built** (so you can explain it in an interview): two derived tables joined by `UNION ALL`.

- **A. Office rows**: everyone present at the From or the To month-end, pre-aggregated (same population rule as the region walk), expanded into the six views with `CROSS APPLY (VALUES ...)`, then into the walk steps that apply. Each office closes: Opening + Hires − Voluntary Exits − Involuntary Exits + Transfers In − Transfers Out + Office Moves In − Office Moves Out + Cross-border Moves In − Cross-border Moves Out (+ FTE Changes for FTE) = Closing. `headcount` and `fte` are **signed**; `worker_count` is always the number of people.
- **B. Route rows**: people at both month-ends whose office differs, by origin and destination, with the same `group_side` (Both, From, To) as office moves. Identical to `custom_sql_office_moves.sql` without the reason column (check 2 proves it, row for row).
- **Which step a continuing person lands in**, per view: office changed → Office Moves Out at the old office and In at the new one (Cross-border when the countries differ); office the same but group changed → Transfers Out / In (only Function, Sub-function and Department can have these); FTE changed → FTE Changes at the closing office. Out and In carry the opening FTE, so the FTE walk closes too.

---

## Part 2. Copy the workbook and connect the new query

1. Open the Compensation Walk workbook. **File > Save As...** `Arcadia Workforce Footprint.twb` in a new folder. From here on, work only in the copy.
2. **Data > New Data Source > Microsoft SQL Server**: `localhost, 1433`, database `ArcadiaHR`, `sa`, Require SSL off (use the `.tdc` file if a certificate error appears), **Sign In**.
3. Drag **New Custom SQL** onto the canvas, paste the whole of `tableau/custom_sql_workforce_footprint.sql`, **OK**.
4. Rename the data source (top left of the Data Source tab) to **`Footprint`**.
5. In the data grid, check types (click the icon above a column to change it):

| Field | Type | Geographic role |
|---|---|---|
| `from_month_end`, `to_month_end`, `report_start_date`, `report_as_of_date`, `opened_date` | Date | |
| `latitude`, `longitude`, `to_latitude`, `to_longitude` | Number (decimal) | **None** (right-click > Geographic Role > None; MAKEPOINT does the mapping) |
| `headcount`, `worker_count`, `view_order`, `step_order`, `months_between` | Number (whole) | |
| `fte` | Number (decimal) | |
| `country_name`, `to_country`, `city` | String | **None** (no country polygons, decision 7) |

6. Go to a new sheet. Check: drag `headcount` to Text, filter `row_type` = Office, `step` = Closing, `view_name` = Company, `from_month_end` = 6/30/2025, `to_month_end` = 6/30/2026. Expected **30,005**. Delete the check sheet.

Do not extract yet (Part 13); working live while building is fine at this size, but if Desktop feels slow, **Data > Footprint > Extract Data > Extract** now and refresh at the end.

---

## Part 3. Replace the walk with the new source

1. **Data > Replace Data Source...** Current: the walk (`ArcadiaHR`). Replacement: **`Footprint`**. **OK**.
2. Every sheet that used the walk now uses `Footprint`. Fields that exist in both keep working; fields that exist only in the walk turn red in the calcs that used them. That is expected: most of those calcs are deleted in Part 4.
3. Fields **only in the walk** (red after the swap): `group_leader`, `movement_reason`, `base_usd_*`, `loaded_usd_*`, `avg_*`, `pct_*`. Nothing on the footprint uses them.
4. Fields **new in Footprint**: `row_type`, `group_side`, `location_id`, `office_name`, `city`, `country_name`, `region`, `site_type`, `opened_date`, `latitude`, `longitude`, `to_location_id`, `to_office`, `to_country`, `to_region`, `to_latitude`, `to_longitude`, `flow_scope_label`.
5. Replace Data Source does not remove the old source: **Data > ArcadiaHR > Close** now (nothing uses it any more; if Tableau says a sheet does, that sheet was not switched, so repeat step 1).
6. Leave the Office Moves source open for now. It goes in Part 4, after its sheets.

---

## Part 4. Delete what the footprint does not use (in this order)

Tableau will not delete a sheet that is on a dashboard, and an action whose source sheet is gone stays as a broken action, so the order matters.

### 4.1 Dashboard items

On the dashboard (`Summary`), select and remove (item dropdown > **Remove from Dashboard**, or the ✕ on the item):

- the waterfall card container and everything in it (`Waterfall Compact`, `Waterfall Expand`, title and subtitle sheets);
- `Btn Expand ALL` and `Btn Collapse ALL` (both containers with their text and icon sheets);
- the office moves panel container (`Panel: Office moves`) with everything in it (`Office Moves Map`, `Office Moves Title`, `Office Moves SubTitle`, `Top Corridors`, `Region Headcount`), and the floating panel toggle if it is there;
- in the rail: nothing yet (the toggles are edited in place in Part 6).

Keep `Top Drivers` and the `Card Drivers` container: they are rebuilt in place (Part 9). Keep the KPI cards sheet and its background image.

### 4.2 Actions

**Dashboard > Actions**. Delete every action whose source or target is one of the sheets above, and every action that targets `p_Cost`, `p_Currency`, `p_Expand` or `p_Panel` (they come back as Routes and Radius actions in Part 6, so **keep** "Set cost" and "Set currency" and their Deselect actions: you edit them there). Delete:

| Delete | Typical names |
|---|---|
| Expand / Collapse | `Expand`, `Collapse`, and their deselect actions |
| Panel toggle (if built) | `Set panel`, deselect |
| Highlight or filter actions from the waterfall or the routes | any with source `Waterfall *` or `Top Corridors` |

### 4.3 Sheets

Right-click each sheet tab > **Delete**: the waterfall sheets and their title/subtitle sheets, the Expand/Collapse text and icon sheets, `Office Moves Map`, `Office Moves Title`, `Office Moves SubTitle`, `Top Corridors`, and the retired items from the build-status cleanup list if they still exist (`Stat` sheets, `Region Moves`, `Moved People`, `Top Region Movers`, `Top Region`, `Axis Step`). **Duplicate** `Region Headcount` first if you want its formatting as a reference, then delete the original (Part 10 rebuilds it as `Geo Growth`).

### 4.4 Office Moves source

**Data > Office Moves > Close**. If Tableau says a sheet still uses it, that sheet was missed in 4.3.

### 4.5 Parameters

First empty the two pay toggles without deleting them (their dashboard items, headings and actions are reused in Part 6): open `Cost Toggle`, **Worksheet > Clear > Sheet**; same for `Currency Toggle`. Then right-click > **Delete**: `p_Cost`, `p_Currency`, `p_Expand`, `p_Panel` (whichever exist).

### 4.6 Calculated fields

In the data pane of `Footprint`, delete these (right-click > Delete; select several with Cmd-click). Some are still on the KPI cards and Top Drivers sheets; when Tableau asks whether to delete a field that is in use, answer **Yes** for the fields in this table (the pill leaves the sheet and the new one goes on in Parts 7 and 9). For a field that is not in this table, answer **No** and check where it is used.

| Group | Delete |
|---|---|
| Waterfall | `Lens Value`, `Walk Row`, `Run Pos`, `Axis Floor`, `Axis Unit`, `Waterfall Position`, `Waterfall Size`, `Waterfall Title`, `Waterfall Subtitle`, `Driver Name`, `Driver Value`, `Driver 1 Size`, `Driver 2 Size`, `Driver 1 Name`, `Driver 1 Value`, `Driver 2 Name`, `Driver 2 Value`, `D1 Text`, `D2 Text`, `Walk Open`, `Walk Close`, `Walk Change`, `Change Text`, `Change Pct Text`, `Expand Label`, any `WF *` calc |
| Top drivers (old) | every `TD *` calc (`TD Key`, `TD Total`, `TD Abs`, `TD Abs 1..4`, `TD Show`, `TD People`, `TD People Text`, `TD People Label`, `TD Value Text`, `TD Up Text`, `TD Down Text`, `TD Direction`, `TD Top Name`, `TD Top Text`, `TD Headline`, `TD Why`, `TD Group`, `TD Step Count`, `TD Subtitle`). They are recreated in Part 9 with new logic; deleting first avoids mixing old and new |
| Region card | `Open HC`, `Close HC`, `Growth %`, `Net Change`, `Share of Growth`, `Tot Open`, `Tot Close`, `Tot Open Text`, `Tot Close Text`, `Tot Growth Text`, `Region Subtitle`, `In Period` |
| Cost and currency | `Cost Option`, `Cost State`, `Cost Shape`, `Cost Pick`, `Currency Option`, `Currency State`, `Currency Shape`, `Currency Pick`, `Cost Text`, `Currency Text`, `Default Cost`, `Default Currency` |
| KPI cards | the old `KPI n Value` and `KPI n Note*` calcs and any `K *` helper that reads a pay field. Keep every `kpi_` layout calc (`kpi_lat *`, `kpi_lon *`, `kpi_pt *`, `kpi_Frame`) |

**Keep** (the rail and shared helpers): `In Pair`, `Is FTE`, `zzTrue`, `zzFalse`, `Close Panel`, `Group Field Text`, `Toggle Group Panel`, `Has Groups`, `Panel Title`, `Pick Rows`, `Pick Col`, `Pick Row`, `Group Is Current`, `Group In View`, `Group Label`, `Default Group`, the Period calcs (`Pair Label`, `Span Type`, `Period In Span`, `Period Is Current`, `Period Key`, `Pair Name`, `Period Field Text`, `Toggle Period Panel`, `Period Rows`, `Period Col`, `Period Row`, `Span Display`, `Span Label`, `Span Value`, `Span Order`), `Lens Option`, `Lens State`, `Lens Shape`, `Lens Pick`, `Toggle Info`, `Info Shape`, `Reset Text`, `Default From`, `Default To`, `Default View`, `Default Group All`, `Default Lens`, `Default Span`, `From Text`, `To Text`, `Page Subtitle`.

**Check after Part 4:** no red field anywhere (search the data pane for "!"), and the rail still works on the dashboard: open Period, pick FY25, pick View Office, pick Bengaluru. The KPI cards show errors or blanks at this point; that is fine until Part 7.

---

## Part 5. Parameters

### 5.1 Change `p_Lens`

Right-click `p_Lens` > Edit. Allowable values List:

| Value | Display As |
|---|---|
| `Headcount` | Headcount |
| `FTE` | FTE |

Current value **Headcount**. Then edit `Is FTE`:

```
// Is FTE
[p_Lens] = "FTE"
```

### 5.2 New parameters

| Name | Data type | Allowable values | Current value | Used by |
|---|---|---|---|---|
| `p_Routes` | Integer | List: 1 (Display As "All"), 3 ("3+"), 10 ("10+") | 3 | Map: hides routes with fewer people (1 = all) |
| `p_RadiusKm` | Integer | List: 500, 1000, 2000 | 1000 | Radius ring and "within" count |
| `p_FocusOffice` | String | All | London | Ring centre; set by clicking an office |
| `p_MapFocus` | String | List: World, Americas, Europe & Africa, Asia Pacific | World | Map framing |
| `p_Geo` | String | List: Region, Country, Office | Region | Growth card level |

`p_FocusOffice` uses **All** (not a list): a Change Parameter action can only set values the list allows, and a typed list would need updating whenever an office opens.

---

## Part 6. Rail: what changes

Shapes first:

1. Copy `docs/brand/build/make_footprint_toggle_shapes.py` into the repo and run `python3 docs/brand/build/make_footprint_toggle_shapes.py 1D3150 E4E3DD` (or use the 16 PNGs that came with this guide).
2. Copy the 16 `seg_fp_*.png` files to `Documents/My Tableau Repository/Shapes/Arcadia`.
3. In Tableau, on any sheet: Marks > Shape > **Reload Shapes**.

Look: identical to the Compensation Walk toggles (wash pill `#E4E3DD` with navy text when on, light text when off). Two-option cells are 88 x 30, three-option cells 58 x 30, so every capsule is 176 wide in the rail.

### 6.1 `Lens Toggle` (Headcount | FTE)

Edit the four calcs; the sheet, its actions and its dashboard item stay.

```
// Lens Option
IF [step] = "Opening" THEN "headcount"
ELSEIF [step] = "Closing" THEN "fte" END

// Lens State
IF ([Lens Option] = "fte") = [Is FTE] THEN "on" ELSE "off" END

// Lens Shape   (must equal the PNG name without .png)
"seg_fp_lens_" + [Lens Option] + "_" + [Lens State]

// Lens Pick   (the value the action passes to p_Lens)
IF [step] = "Opening" THEN "Headcount" ELSEIF [step] = "Closing" THEN "FTE" END
```

On the sheet: Columns `Lens Option` sorted **Manual**, `headcount` first. Shape card: assign `seg_fp_lens_headcount_on/off` and `seg_fp_lens_fte_on/off` **by hand** (Assign Palette goes alphabetically, not by name). Action "Set lens" stays (source Lens Toggle, target `p_Lens`, field `Lens Pick`).

Heading text above it: `SHOW AS`.

**Test:** click FTE: KPI card 1 reads 29,354.5; click Headcount: 30,005.

### 6.2 `Cost Toggle` becomes `Routes Toggle` (All | 3+ | 10+)

Rename the sheet `Routes Toggle`. Remove the old `Cost *` pills from the shelves, then:

```
// Routes Option   (three rows from step_order: 1 Opening, 2 Hires, 3 Voluntary Exits)
CASE [step_order] WHEN 1 THEN "all" WHEN 2 THEN "3" WHEN 3 THEN "10" END

// Routes Pick   (integer, for p_Routes)
CASE [step_order] WHEN 1 THEN 1 WHEN 2 THEN 3 WHEN 3 THEN 10 END

// Routes State
IF [Routes Pick] = [p_Routes] THEN "on" ELSE "off" END

// Routes Shape
"seg_fp_routes_" + [Routes Option] + "_" + [Routes State]
```

Sheet: Marks **Shape**; Columns `Routes Option` (Discrete), sort by **Field** `step_order` Minimum, ascending; Filter `Routes Option` exclude Null; Shape `Routes Shape` (assign the six PNGs by hand); Detail `Routes Pick`, `zzTrue`, `zzFalse`; Size max; Fit Standard; header hidden; tooltip off; shading Group Field blue (same as Lens).

Why `step_order` 1 to 3 and not `step`: Opening, Hires and Voluntary Exits exist in almost every selection, and a toggle needs one mark per option whatever the filters. If a tiny group in a single month has no voluntary exit, the 10+ option would vanish; the toggle sheet therefore has **no** `In Pair` filter (it reads the whole table, where all three always exist).

Action: edit "Set cost": rename **Set routes**, source `Routes Toggle`, target parameter `p_Routes`, field `Routes Pick`, Keep current value. Its Deselect action stays (source and target `Routes Toggle`).

Heading: `ROUTES SHOWN`.

### 6.3 `Currency Toggle` becomes `Radius Toggle` (500 km | 1,000 | 2,000)

Same as 6.2:

```
// Radius Option
CASE [step_order] WHEN 1 THEN "500" WHEN 2 THEN "1000" WHEN 3 THEN "2000" END
// Radius Pick
CASE [step_order] WHEN 1 THEN 500 WHEN 2 THEN 1000 WHEN 3 THEN 2000 END
// Radius State
IF [Radius Pick] = [p_RadiusKm] THEN "on" ELSE "off" END
// Radius Shape
"seg_fp_radius_" + [Radius Option] + "_" + [Radius State]
```

Action "Set currency" becomes **Set radius** (target `p_RadiusKm`, field `Radius Pick`). Heading: `RADIUS AROUND OFFICE`.

### 6.4 `Reset`

Delete `Default Cost` and `Default Currency` from the sheet's Detail (already deleted as calcs in 4.6). Edit or add:

| Calc | Formula |
|---|---|
| `Default Lens` | `"Headcount"` |
| `Default Routes` | `3` |
| `Default Radius` | `1000` |
| `Default Focus Office` | `"London"` |
| `Default Map Focus` | `"World"` |
| `Default Geo` | `"Region"` |

`Default From` and `Default To` stay (`2025-06-30`, `2026-06-30`; or the as-of fields if you did release 2 step B1). Put the new calcs on `Reset`'s Detail and add Change Parameter actions (source Reset, Keep current value): `p_Routes` ← `Default Routes`, `p_RadiusKm` ← `Default Radius`, `p_FocusOffice` ← `Default Focus Office`, `p_MapFocus` ← `Default Map Focus`, `p_Geo` ← `Default Geo`. Delete the old Reset actions to `p_Cost` and `p_Currency` if any survived.

### 6.5 Info panel text (`Info Popover`)

Title: **How the footprint is counted**. Lines (terms bold white, text `#B8C0CC`, same fonts as before):

- **Headcount**: people active on the month-end, by the office they sit in. Executive officers are not included.
- **FTE**: the same people weighted by hours (a half-time person is 0.5).
- **Hires and exits**: compare the two dates. Someone who joined and left in between is in neither.
- **Office move**: same person, different office on the two dates. Moves inside one country and across a border are counted apart.
- **Transfers**: changed function, sub-function or department without changing office.
- **Growth colors**: growth annualized, so a quarter and a year use the same scale.

Move the `Info Button` into the `SHOW AS` heading row (same container trick as before).

### 6.6 Page title and subtitle

Page title text: **Global Workforce Footprint**.

```
// Page Subtitle
"Where " + (IF [p_View] = "Company" THEN "Arcadia's people are" ELSE "people in " + [p_Group] + " are")
+ ", where " + (IF [Is FTE] THEN "FTE" ELSE "headcount") + " grew, and how people move between offices · "
+ [From Text] + " to " + [To Text]
```

FY26, Company: "Where Arcadia's people are, where headcount grew, and how people move between offices · Jun 30, 2025 to Jun 30, 2026".

### 6.7 Rail spacing

Same system as `rail_controls_build.md` 5.4; the three pay sections are replaced one for one, so every y stays:

| Item | Height | Running y |
|---|---|---|
| ... logo, Period, View, Group Block as today | | 416 |
| Divider | 24 | 440 |
| SHOW AS (16) + 6 + Lens (30) | 52 | 492 |
| Blank | 24 | 516 |
| ROUTES SHOWN (16) + 6 + Routes (30) | 52 | 568 |
| Blank | 24 | 592 |
| RADIUS AROUND OFFICE (16) + 6 + Radius (30) | 52 | 644 |
| Divider | 24 | 668 |
| Reset | 30 | 698 |

Footnote stays: "Arcadia Systems is a fictional company. All data is synthetic."

**Test 6:** each toggle moves its pill and leaves no blue box; Reset brings back FY26, Company, Headcount, 3+, 1,000.

---

## Part 7. Shared calcs, then the KPI cards

### 7.1 Shared calcs (create once, data source Footprint)

```
// In Pair   (edit the existing one only if it differs; Boolean)
[from_month_end] = [p_From] AND [to_month_end] = [p_To]
AND [view_name] = [p_View] AND [group_name] = [p_Group]

// Office In Pair
[In Pair] AND [row_type] = "Office"

// Route In Pair
[In Pair] AND [row_type] = "Route"

// Walk Value   (row level; what every headcount card measures, following the lens)
IF [Is FTE] THEN [fte] ELSE [headcount] END
```

**The double-counting rule for this source:** every sum goes through `Office In Pair` or `Route In Pair`, never `In Pair` alone. Office rows and route rows describe the same people twice (once as headcount, once as moves), and every pair, view and group repeats people on purpose.

Totals and number-to-text helpers. Every `K` total is a **table-scoped LOD** (`{ ... }`): one value for the selection, usable on the KPI sheet and inside any title, even on a sheet that has a dimension (a plain `SUM` in a title splits by that dimension and shows `*`). Tableau has no FORMAT function, so text uses the same patterns as the Compensation Walk.

```
// K Open    { ZN(SUM(IF [Office In Pair] AND [step] = "Opening" THEN [Walk Value] END)) }
// K Close   { ZN(SUM(IF [Office In Pair] AND [step] = "Closing" THEN [Walk Value] END)) }
// K Open HC { ZN(SUM(IF [Office In Pair] AND [step] = "Opening" THEN [headcount] END)) }

// K Close T   (tenths, integer: lets the text show one decimal in FTE)
INT(ROUND([K Close] * 10, 0))
// K Open T
INT(ROUND([K Open] * 10, 0))

// K Pct T   (growth in tenths of a percent, absolute; rounding first prevents "−0.0%")
IF [K Open] = 0 THEN 0 ELSE INT(ROUND(ABS([K Close] / [K Open] - 1) * 1000, 0)) END
// K Pct Text
STR(DIV([K Pct T], 10)) + "." + STR([K Pct T] % 10) + "%"
// K Pct Sign   (empty when the rounded change is zero)
IF [K Pct T] = 0 THEN "" ELSEIF [K Close] > [K Open] THEN "+" ELSE "−" END
```

### 7.2 KPI card values and notes

The KPI cards sheet keeps its 17 layers and the `kpi_` parameters. Only the label fields change and the typed titles change.

**Card 1, Closing headcount** (title typed: `Closing headcount`; follows the lens, so make the title a field instead: `KPI 1 Title` = `IF [Is FTE] THEN "Closing FTE" ELSE "Closing headcount" END`)

```
// KPI 1 Value
(IF [K Close T] >= 10000
 THEN STR(DIV([K Close T], 10000)) + "," + RIGHT("00" + STR(DIV([K Close T], 10) % 1000), 3)
 ELSE STR(DIV([K Close T], 10)) END)
+ (IF [Is FTE] THEN "." + STR([K Close T] % 10) ELSE "" END)

// K Open Text   (same pattern on the opening)
(IF [K Open T] >= 10000
 THEN STR(DIV([K Open T], 10000)) + "," + RIGHT("00" + STR(DIV([K Open T], 10) % 1000), 3)
 ELSE STR(DIV([K Open T], 10)) END)
+ (IF [Is FTE] THEN "." + STR([K Open T] % 10) ELSE "" END)

// K Close Text   (same pattern on the closing; used by the Growth card subtitle)
(IF [K Close T] >= 10000
 THEN STR(DIV([K Close T], 10000)) + "," + RIGHT("00" + STR(DIV([K Close T], 10) % 1000), 3)
 ELSE STR(DIV([K Close T], 10)) END)
+ (IF [Is FTE] THEN "." + STR([K Close T] % 10) ELSE "" END)

// KPI 1 Note Up     (teal #006B66 layer)
IF [K Pct T] > 0 AND [K Close] > [K Open] THEN "+" + [K Pct Text] + " vs " + [K Open Text] + " at start" END
// KPI 1 Note Down   (coral #B8401F layer)
IF [K Pct T] > 0 AND [K Close] < [K Open] THEN "−" + [K Pct Text] + " vs " + [K Open Text] + " at start" END
// KPI 1 Note Flat   (slate #5A6170 layer)
IF [K Pct T] = 0 THEN "0.0% vs " + [K Open Text] + " at start" END
```

**Card 2, Offices** (title typed: `Offices`)

```
// K Offices
{ COUNTD(IF [Office In Pair] AND [step] = "Closing" THEN [location_id] END) }
// K Countries
{ COUNTD(IF [Office In Pair] AND [step] = "Closing" THEN [country_name] END) }
// K Opened   (offices that opened inside the period and have people at its end)
{ COUNTD(IF [Office In Pair] AND [step] = "Closing"
         AND [opened_date] > [p_From] AND [opened_date] <= [p_To] THEN [location_id] END) }

// KPI 2 Value
STR([K Offices])
// KPI 2 Note   (short: the note line holds about 34 characters at 8 pt)
STR([K Countries]) + (IF [K Countries] = 1 THEN " country" ELSE " countries" END)
+ (IF [K Opened] > 0 THEN " · " + STR([K Opened]) + " opened" ELSE "" END)
```

**Card 3, Fastest-growing region** (title typed). A region needs at least 50 at the start (headcount or FTE), so a tiny base cannot win with a big percentage.

```
// Region Open    { FIXED [region] : SUM(IF [Office In Pair] AND [step] = "Opening" THEN [Walk Value] END) }
// Region Close   { FIXED [region] : SUM(IF [Office In Pair] AND [step] = "Closing" THEN [Walk Value] END) }
// Region Growth  (row level)
IF [Region Open] >= 50 THEN [Region Close] / [Region Open] - 1 END
// Top Region Growth
{ MAX([Region Growth]) }
// Top Region
{ MAX(IF [Region Growth] = [Top Region Growth] THEN [region] END) }
// Top Region Open / Top Region Close
{ MAX(IF [region] = [Top Region] THEN [Region Open] END) }
{ MAX(IF [region] = [Top Region] THEN [Region Close] END) }

// KPI 3 Value
IFNULL([Top Region], "—")
// KPI 3 Note   (whole numbers in both lenses: the note is about the base, not the decimals)
IF ISNULL([Top Region]) THEN "no region with 50+ at the start" ELSE
  (IF [Top Region Growth] >= 0 THEN "+" ELSE "−" END)
  + STR(DIV(INT(ROUND(ABS([Top Region Growth]) * 1000, 0)), 10)) + "."
  + STR(INT(ROUND(ABS([Top Region Growth]) * 1000, 0)) % 10) + "% · "
  + (IF [Top Region Open] >= 1000
     THEN STR(DIV(INT(ROUND([Top Region Open], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([Top Region Open], 0)) % 1000), 3)
     ELSE STR(INT(ROUND([Top Region Open], 0))) END)
  + " → "
  + (IF [Top Region Close] >= 1000
     THEN STR(DIV(INT(ROUND([Top Region Close], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([Top Region Close], 0)) % 1000), 3)
     ELSE STR(INT(ROUND([Top Region Close], 0))) END)
END
```

On the Label shelf Tableau shows LOD-based text fields as `ATTR(...)`; that is correct.

**Card 4, Largest country share** (title typed: `Largest country share`)

```
// Country Close      { FIXED [country_name] : SUM(IF [Office In Pair] AND [step] = "Closing" THEN [Walk Value] END) }
// Top Country Close  { MAX([Country Close]) }
// Top Country        { MAX(IF [Country Close] = [Top Country Close] THEN [country_name] END) }
// Top Country Offices
{ COUNTD(IF [Office In Pair] AND [step] = "Closing" AND [country_name] = [Top Country] THEN [location_id] END) }

// KPI 4 Value
IF [K Close] = 0 THEN "—" ELSE
  STR(DIV(INT(ROUND([Top Country Close] / [K Close] * 1000, 0)), 10)) + "."
  + STR(INT(ROUND([Top Country Close] / [K Close] * 1000, 0)) % 10) + "%"
END
// KPI 4 Note
[Top Country] + " · " + STR([Top Country Offices])
+ (IF [Top Country Offices] = 1 THEN " office" ELSE " offices" END)
```

No `ATTR()` is needed here because `K Close` is itself an LOD; if you ever mix one of these with a plain `SUM`, wrap the LOD in `ATTR()` (the Compensation Walk lesson).

**Card 5, Changed office** (title typed: `Changed office`; always people, whatever the lens: a move is a person)

```
// K Movers   { ZN(SUM(IF [Route In Pair] THEN [headcount] END)) }
// K Across   { ZN(SUM(IF [Route In Pair] AND [flow_scope_label] = "Across a border" THEN [headcount] END)) }

// KPI 5 Value
IF [K Movers] >= 1000
THEN STR(DIV(INT([K Movers]), 1000)) + "," + RIGHT("00" + STR(INT([K Movers]) % 1000), 3)
ELSE STR(INT([K Movers])) END
// KPI 5 Note
STR(INT([K Across])) + " cross-border · "
+ (IF [K Open HC] = 0 THEN "" ELSE
   STR(DIV(INT(ROUND([K Movers] / [K Open HC] * 1000, 0)), 10)) + "."
   + STR(INT(ROUND([K Movers] / [K Open HC] * 1000, 0)) % 10) + "% of people" END)
```

### 7.3 Put them on the layers

For each layer (Marks card tabs): drag the new field onto **Label** in place of the old one. Card 1 Title layer: replace the typed text with `KPI 1 Title`. Cards 2 to 5 Title layers: retype the text (Label > Text). Card 1 keeps three note layers (Up, Down, Flat); cards 2 to 5 use one note layer each (slate), so delete any extra Up/Down layers they had, or point them at an empty calc. Fonts and colors stay as in the configuration workbook.

### 7.4 Check (FY26)

| Card | Company, Headcount | Company, FTE | Country India | Office Bengaluru | Function Technology |
|---|---|---|---|---|---|
| 1 | 30,005 · +5.5% vs 28,438 at start | 29,354.5 · +5.4% vs 27,852.7 at start | 6,967 · +4.4% vs 6,672 | 3,493 · +2.3% vs 3,414 | 11,497 · +5.7% vs 10,877 |
| 2 | 35 · 22 countries | same | 3 · 1 country | 1 · 1 country | 35 · 22 countries |
| 3 | Latin America · +5.9% · 2,225 → 2,356 | | Asia Pacific · +4.4% · 6,672 → 6,967 | Asia Pacific · +2.3% | Latin America · +8.5% · 791 → 858 |
| 4 | 31.2% · United States · 6 offices | | 100.0% · India · 3 offices | 100.0% · India · 1 office | 29.4% · India · 3 offices |
| 5 | 725 · 125 cross-border · 2.5% of people | same | 210 · 55 cross-border · 3.1% of people | 150 · 19 cross-border · 4.4% of people | 336 · 53 cross-border · 3.1% of people |

FY25 (Jun 30, 2024 to Jun 30, 2025), Company: 28,438 · +4.5% vs 27,208; card 2 "35 · 22 countries · 2 opened" (Pune, Vancouver); card 3 Asia Pacific +6.5%; card 5 679, 111 across.

---

## Part 8. The map (`Footprint Map`): bigger, and doing more with less ink

### 8.1 What was inefficient in the Compensation Walk map, and the fix for each

| Problem in the Compensation Walk map | Fix here |
|---|---|
| Only moves were drawn; the map never showed where people **are** | Offices are the main layer: size = closing headcount (or FTE), color = growth band |
| One line per direction (A to B and B to A drawn twice) | Directions merged into one route per office pair (`Office Pair`): FY26 121 routes instead of 155 lines |
| 99 of 143 lines carried one person; the long tail filled the ocean | `p_Routes` hides routes under 3 people by default; the subtitle says how many people that leaves out, so nothing disappears silently (FY26: 30 routes drawn carrying 622 people, 103 people on smaller routes) |
| Dense clusters (Europe, India, US) unreadable at world zoom | `p_MapFocus` (World, Americas, Europe & Africa, Asia Pacific) reframes the map. Pan and zoom are switched off, so the frame is always deliberate |
| Fixed saved zoom: a filter could leave marks off-screen | The map frames itself on its marks (nothing pinned). An invisible 400 km halo around every office keeps a one-office selection from zooming to street level |
| Map was 520 x 224 | 636 x 530, the largest card on the page |
| No spatial question answered | Click an office: a ring of 500, 1,000 or 2,000 km and the title "Within 1,000 km of London: 7 offices, 4,240 people" |
| Every office labelled or none | Labels on the 6 largest offices in view plus the focus office |

### 8.2 Calcs (data source Footprint)

```
// Region In Focus   (row level, origin office)
CASE [p_MapFocus]
  WHEN "World"           THEN TRUE
  WHEN "Americas"        THEN [region] = "North America" OR [region] = "Latin America"
  WHEN "Europe & Africa" THEN [region] = "Europe" OR [region] = "Middle East & Africa"
  WHEN "Asia Pacific"    THEN [region] = "Asia Pacific"
END

// To Region In Focus   (same CASE on [to_region], for routes)
CASE [p_MapFocus]
  WHEN "World"           THEN TRUE
  WHEN "Americas"        THEN [to_region] = "North America" OR [to_region] = "Latin America"
  WHEN "Europe & Africa" THEN [to_region] = "Europe" OR [to_region] = "Middle East & Africa"
  WHEN "Asia Pacific"    THEN [to_region] = "Asia Pacific"
END

// Map Row   (the sheet filter: this pair, view and group, office or route)
[In Pair]
```

Offices:

```
// Office Shown   (row level: an office row of this selection, inside the map focus)
[Office In Pair] AND [Region In Focus]

// Office Point
IF [Office Shown] THEN MAKEPOINT([latitude], [longitude]) END

// Office Halo   (invisible; keeps a single office from zooming to street level)
IF [Office Shown] THEN BUFFER(MAKEPOINT([latitude], [longitude]), 400, "km") END

// Office Open    SUM(IF [Office Shown] AND [step] = "Opening" THEN [Walk Value] END)
// Office Close   SUM(IF [Office Shown] AND [step] = "Closing" THEN [Walk Value] END)
// Office Growth  (actual growth over the period)
IF ZN([Office Open]) = 0 THEN NULL ELSE [Office Close] / [Office Open] - 1 END
// Office Growth Annual   (same scale for a month, a quarter or a year)
IF ZN([Office Open]) = 0 THEN NULL
ELSE POWER([Office Close] / [Office Open], 12 / ATTR([months_between])) - 1 END

// Growth Band   (aggregate; the office color)
IF ZN([Office Open]) = 0 THEN "New office"
ELSEIF [Office Growth Annual] < 0 THEN "Shrinking"
ELSEIF [Office Growth Annual] < 0.03 THEN "0 to 3%"
ELSEIF [Office Growth Annual] < 0.06 THEN "3 to 6%"
ELSEIF [Office Growth Annual] < 0.10 THEN "6 to 10%"
ELSE "10% or more" END

// Office Label Rank   (table calc: compute using location_id)
RANK_UNIQUE([Office Close], 'desc')
// Office Label Name
IF [Office Label Rank] <= 6 OR ATTR([office_name]) = [p_FocusOffice] THEN ATTR([office_name]) END
// Office Label Value   (format the pill #,##0)
IF [Office Label Rank] <= 6 OR ATTR([office_name]) = [p_FocusOffice] THEN [Office Close] END
```

Routes:

```
// Office Pair   (row level; the same name for A to B and B to A)
IF [row_type] = "Route" THEN
  IF [office_name] < [to_office] THEN [office_name] + " ↔ " + [to_office]
  ELSE [to_office] + " ↔ " + [office_name] END
END

// Pair People   (people on the pair in the selection, both directions)
{ FIXED [Office Pair] : SUM(IF [Route In Pair] THEN [headcount] END) }

// Route Drawn   (row level)
[Route In Pair] AND [Pair People] >= [p_Routes] AND [Region In Focus] AND [To Region In Focus]

// Route Line
IF [Route Drawn] THEN MAKELINE(MAKEPOINT([latitude], [longitude]), MAKEPOINT([to_latitude], [to_longitude])) END

// Route People   (line width)
SUM(IF [Route Drawn] THEN [headcount] END)

// Routes Drawn    { COUNTD(IF [Route Drawn] THEN [Office Pair] END) }
// People Drawn    { ZN(SUM(IF [Route Drawn] THEN [headcount] END)) }
// People Not Drawn
{ SUM(IF [Route In Pair] AND [Region In Focus] AND [To Region In Focus] THEN [headcount] END) } - [People Drawn]
```

In a regional focus, a route is drawn only when both ends are in the region (a Bengaluru to London line would drag the frame back to the world).

**Why `Office Shown` and `Route Drawn` sit inside the size measures.** Each layer has one invisible null mark: on the office layer it holds the route rows and the offices outside the focus, on the route layer it holds the office rows and the hidden routes. That mark is not drawn, but its measures still enter the size scale. With a plain `SUM(headcount)` the route layer's null mark would carry about 30,000 and every real route would be drawn hairline thin. Putting the same condition in the measure makes the null mark's size empty.

Focus office and ring:

```
// Focus Lat      { FIXED : MAX(IF [office_name] = [p_FocusOffice] THEN [latitude]  END) }
// Focus Lon      { FIXED : MAX(IF [office_name] = [p_FocusOffice] THEN [longitude] END) }
// Focus Region   { FIXED : MAX(IF [office_name] = [p_FocusOffice] THEN [region] END) }
// Focus Point    MAKEPOINT([Focus Lat], [Focus Lon])

// Focus Shown   (the focus office has people in this selection and sits in the map focus)
{ MAX(IF [Office In Pair] AND [office_name] = [p_FocusOffice] THEN 1 ELSE 0 END) } = 1
AND CASE [p_MapFocus]
      WHEN "World" THEN TRUE
      WHEN "Americas" THEN [Focus Region] = "North America" OR [Focus Region] = "Latin America"
      WHEN "Europe & Africa" THEN [Focus Region] = "Europe" OR [Focus Region] = "Middle East & Africa"
      WHEN "Asia Pacific" THEN [Focus Region] = "Asia Pacific"
    END

// Radius Ring
IF [Focus Shown] THEN BUFFER([Focus Point], [p_RadiusKm], "km") END

// Km To Focus   (row level)
DISTANCE(MAKEPOINT([latitude], [longitude]), [Focus Point], "km")

// Radius People    { SUM(IF [Office In Pair] AND [step] = "Closing" AND [Km To Focus] <= [p_RadiusKm] THEN [Walk Value] END) }
// Radius Offices   { COUNTD(IF [Office In Pair] AND [step] = "Closing" AND [Km To Focus] <= [p_RadiusKm] THEN [location_id] END) }
```

Distances are great-circle from postal-code coordinates (the Methodology line says so).

### 8.3 Build the sheet, layer by layer

1. New sheet **`Footprint Map`**. Drag `Map Row` to **Filters**, select **True**.
2. Double-click **`Office Point`**. A map with dots appears (Tableau adds Latitude (generated), Longitude (generated)).
3. **Layer 1, offices** (the tab named `Office Point`):
   - Mark type **Circle**. `location_id` and `office_name` to **Detail**.
   - `Office Close` to **Size**. Size legend (Analysis > Legends > Size) > Edit Sizes: leave the range Automatic and drag the handles so the smallest office (FY26 Manila) is about 6 px and the largest (Bengaluru, 3,493) about 30 px.
   - `Growth Band` to **Color**. Colors (Edit Colors, assign each):
     | Band | Color |
     |---|---|
     | Shrinking | coral `#E4572E` |
     | 0 to 3% | `#CFE8E5` |
     | 3 to 6% | `#8CCBC5` |
     | 6 to 10% | `#2FA39C` |
     | 10% or more | `#006B66` |
     | New office | navy `#13233A` |
     Opacity 90%, Border white.
   - Label: `Office Label Name` and `Office Label Value` (compute both using `location_id`), text `<Office Label Name> <Office Label Value>`, 9 pt bold navy, number `#,##0`; Options: **Allow labels to overlap other marks** off.
   - `zzTrue`, `zzFalse` to Detail (for the deselect action).
4. **Layer 2, routes**: drag `Route Line` onto **Add a Marks Layer**. Mark type **Automatic** (never Line: Line joins the routes into one zigzag path). `Office Pair` to **Detail**. `Route People` to **Size** (both directions of the pair). `flow_scope_label` to **Color**: *Within one country* `#5B4FB3`, *Across a border* `#E4572E`; opacity 55%. Size legend > Edit Sizes: Bengaluru ↔ Hyderabad (101 people FY26) about 6 px, 3 people about 1 px. Layer dropdown > **Disable Selection**.
5. **Layer 3, ring**: drag `Radius Ring` onto Add a Marks Layer. Mark type **Map** (polygon). Color navy `#13233A`, opacity 8%, Border navy 1 px. **Disable Selection**.
6. **Layer 4, halo**: drag `Office Halo` onto Add a Marks Layer. `location_id` to Detail. Color any, **opacity 0%**, Border None. **Disable Selection**. It is invisible; it only sets the minimum frame.
7. **Layer order** (Marks card, drag the tabs): Office Point on top, then Route Line, Radius Ring, Office Halo at the bottom.
8. **Map > Background Maps > Light**. **Map > Map Layers**: untick **Base**, tick **Coastline** and **Country/Region Borders**, washout 0%. **Format > Shading > Worksheet: None** (the card's `#FBFBF8` shows through).
9. **Map > Map Options**: untick **Allow pan and zoom**, **Show Map Search**, **Show View Toolbar**. Units Metric.
10. Hide the null indicator at the bottom right (right-click > Hide Indicator): route rows have no Office Point and office rows have no Route Line, so each layer has one null mark, which is not drawn.
11. Do **not** zoom or pan the sheet. If you did, right-click the map > **Reset Zoom**. An unpinned map fits its marks every time the filters change, which is how `p_MapFocus` reframes it.
12. Tooltips:
    - Offices (layer 1):
      ```
      <office_name> · <ATTR(site_type)> · <ATTR(country_name)>
      <AGG(Office Open)> → <AGG(Office Close)> (<AGG(Office Growth)>, <AGG(Office Growth Annual)> a year)
      Hires <AGG(TT Hires)> · Exits <AGG(TT Exits)> · Moved in <AGG(TT In)> · Moved out <AGG(TT Out)>
      <AGG(TT Km)> km from <p_FocusOffice> · click to center the ring here
      ```
      with
      ```
      // TT Hires   SUM(IF [step] = "Hires" THEN [worker_count] END)
      // TT Exits   SUM(IF [step] = "Voluntary Exits" OR [step] = "Involuntary Exits" THEN [worker_count] END)
      // TT In      SUM(IF RIGHT([step], 3) = " In"  THEN [worker_count] END)
      // TT Out     SUM(IF RIGHT([step], 4) = " Out" THEN [worker_count] END)
      // TT Km      ROUND(MIN([Km To Focus]), 0)
      ```
      (number formats: growth `+0.0%;−0.0%`, counts `#,##0`.) Put each field on the layer's Detail before inserting it.
    - Routes (layer 2): `<Office Pair>` / `<AGG(Route People)> people, both directions · <flow_scope_label>`.

### 8.4 Map title, subtitle and legend (three text sheets)

```
// Map Title   (the finding of the ring; a plain sentence when the focus office is not on the map)
IF NOT [Focus Shown] THEN
  "Offices sized by " + (IF [Is FTE] THEN "FTE" ELSE "headcount") + ", colored by growth"
ELSEIF [Radius People] = 0 THEN "No one in this selection within " + [Radius Text] + " of " + [p_FocusOffice]
ELSE "Within " + [Radius Text] + " of " + [p_FocusOffice] + ": "
     + STR([Radius Offices]) + (IF [Radius Offices] = 1 THEN " office, " ELSE " offices, ")
     + [Radius People Text] + (IF [Is FTE] THEN " FTE" ELSE " people") END

// Radius Text
IF [p_RadiusKm] >= 1000 THEN STR(DIV([p_RadiusKm], 1000)) + ",000 km" ELSE STR([p_RadiusKm]) + " km" END

// Radius People Text   (comma pattern, whole numbers)
IF [Radius People] >= 1000
THEN STR(DIV(INT(ROUND([Radius People], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([Radius People], 0)) % 1000), 3)
ELSE STR(INT(ROUND([Radius People], 0))) END

// Map Subtitle   (one line, about 100 characters at most; the size and color key is in the legend row)
STR([Routes Drawn]) + (IF [Routes Drawn] = 1 THEN " route" ELSE " routes")
+ (IF [p_Routes] > 1 THEN " with " + STR([p_Routes]) + "+ people" ELSE "") + " between offices: "
// Map Subtitle Hidden
IF [People Not Drawn] > 0 THEN " · " + STR([People Not Drawn]) + " people on smaller routes not drawn" ELSE "" END
```

All the fields these read are LODs, so the text sheets need no filter and no `ATTR()`.

| Sheet | Text | Format |
|---|---|---|
| `Map Title` | `<Map Title>` (drag it to Text; Tableau shows `ATTR(Map Title)`) | 12 pt bold navy |
| `Map Subtitle` | `<Map Subtitle>` then typed **within one country** (violet `#5B4FB3`), typed ` / `, typed **across a border** (coral `#E4572E`), then `<Map Subtitle Hidden>` | 9 pt slate; one text mark in runs, like the Compensation Walk subtitle |
| `Map Key` | typed "Size: " + `<Lens Word>` + "  ·  ◯ " + `<Radius Text>` + " around " + `<p_FocusOffice>` + "  ·  click an office to move the ring" | 8 pt slate (`Lens Word` = `IF [Is FTE] THEN "FTE" ELSE "headcount" END`) |
| `Growth Legend` | six colored dots with the band names (below) | 8 pt |

Each text sheet: no dimension, title hidden, Fit Entire View, sheet background None.

`Growth Legend` replaces Tableau's color legend so the key matches the card style:

```
// Band Option   (six rows from step_order; the names must match Growth Band exactly)
CASE [step_order] WHEN 1 THEN "Shrinking" WHEN 2 THEN "0 to 3%" WHEN 3 THEN "3 to 6%"
                  WHEN 4 THEN "6 to 10%" WHEN 5 THEN "10% or more" WHEN 6 THEN "New office" END
// Band Text   "●  " + [Band Option]
```

Sheet: Marks **Text**; Columns `Band Option` (sort by `step_order` Minimum); filter exclude Null; Text `Band Text`; Color `Band Option` with the six band colors of 8.3 step 3 (assign by hand); header hidden; tooltip off; no `In Pair` filter (steps 1 to 6 exist in the whole table). Title typed in front: "Growth a year" as a text object, or leave it out.

### 8.5 Map focus toggle (`Map Focus Toggle`, a text toggle in the card)

```
// Focus Option   CASE [step_order] WHEN 1 THEN "World" WHEN 2 THEN "Americas" WHEN 3 THEN "Europe & Africa" WHEN 4 THEN "Asia Pacific" END
// Focus Is Current   [Focus Option] = [p_MapFocus]
```

Sheet: Marks **Text**; Columns `Focus Option` (sort by `step_order` Minimum); filter `Focus Option` exclude Null; Text `Focus Option`; Color `Focus Is Current` (True navy `#13233A`, False `#8A93A3`); Detail `zzTrue`, `zzFalse`; font 9 pt, bold; header hidden; tooltip off; shading None. (Step order 4 is Involuntary Exits, present in the whole table; no `In Pair` filter on this sheet.)

Action **Set map focus**: Change Parameter, source `Map Focus Toggle`, target `p_MapFocus`, field `Focus Option`, Keep current value. Plus **Deselect Map Focus Toggle** (filter, itself, `zzTrue` → `zzFalse`, Show all values).

### 8.6 Check (FY26, Company, Headcount, 3+, 1,000 km, London)

| Do | Expect |
|---|---|
| World | 35 offices; 30 routes; thickest Bengaluru ↔ Hyderabad (101); title "Within 1,000 km of London: 7 offices, 4,240 people"; subtitle "30 routes with 3+ people between offices: within one country / across a border · 103 people on smaller routes not drawn"; labels Bengaluru 3,493, Austin HQ 3,215, Hyderabad 2,996, London 1,527, New York 1,483, San Francisco 1,346 |
| Bands | 10% or more: Pune, Guadalajara, Manila, Vancouver, Stockholm, Lisbon, Seoul. 0 to 3%: Hyderabad, Bengaluru, Zurich, Mexico City, New York, Berlin. No shrinking office |
| Americas | 11 offices; 17 routes (357 people), 12 people not drawn |
| Europe & Africa | 15 offices; 3 routes: Krakow ↔ Warsaw 47, Cape Town ↔ Johannesburg 19, Berlin ↔ Munich 13; ring around London: Paris 341 km, Amsterdam 352, Dublin 464, Zurich 775, Munich 915, Berlin 927 inside |
| Asia Pacific | 9 offices; 4 routes (164 people); no ring (London not in focus); title falls back to "Offices sized by headcount, colored by growth" |
| Click Bengaluru (World, 1,000 km) | ring over south India: Bengaluru, Hyderabad 486 km, Pune 728 km; "Within 1,000 km of Bengaluru: 3 offices, 6,967 people" |
| Click Austin HQ, Radius 2,000 | "Within 2,000 km of Austin HQ: 5 offices, 6,499 people" (Guadalajara, Mexico City, Atlanta, Chicago) |
| Routes All | 121 routes; nothing "not drawn" |
| View Office, Bengaluru | one office plus routes to Hyderabad (101), Pune (30), Warsaw (3); the map zooms in (halo keeps it from street level) |

---

## Part 9. Top drivers card (rebuild `Top Drivers`)

Question the card answers: **what changed the headcount in this selection, in order, and where?** New people (hires), people leaving (voluntary, involuntary), people moving inside the company (transfers between groups, moves within a country, moves across a border), and in the FTE lens hours changes.

### 9.1 Calcs

```
// TD Key   (row level; In and Out of one kind are ONE driver)
CASE [step]
  WHEN "Hires"                  THEN "Hires"
  WHEN "Voluntary Exits"        THEN "Voluntary exits"
  WHEN "Involuntary Exits"      THEN "Involuntary exits"
  WHEN "Transfers In"           THEN "Transfers"
  WHEN "Transfers Out"          THEN "Transfers"
  WHEN "Office Moves In"        THEN "Moves within a country"
  WHEN "Office Moves Out"       THEN "Moves within a country"
  WHEN "Cross-border Moves In"  THEN "Moves across a border"
  WHEN "Cross-border Moves Out" THEN "Moves across a border"
  WHEN "FTE Changes"            THEN IF [Is FTE] THEN "FTE changes" END
END

// TD Group   (eyebrow)
CASE [TD Key]
  WHEN "Hires" THEN "NEW TO ARCADIA"
  WHEN "Voluntary exits" THEN "LEFT ARCADIA"
  WHEN "Involuntary exits" THEN "LEFT ARCADIA"
  WHEN "Transfers" THEN "INTERNAL · OTHER TEAMS"
  WHEN "Moves within a country" THEN "RELOCATION"
  WHEN "Moves across a border" THEN "RELOCATION"
  WHEN "FTE changes" THEN "HOURS"
END

// TD Total   (net effect on the group, in the lens)
IF NOT ISNULL([TD Key]) THEN { FIXED [TD Key] : SUM(IF [Office In Pair] THEN [Walk Value] END) } END
// TD Gross   (people involved; tie-break only)
IF NOT ISNULL([TD Key]) THEN { FIXED [TD Key] : SUM(IF [Office In Pair] THEN [worker_count] END) } END
// TD In / TD Out   (people, for transfers and moves)
IF NOT ISNULL([TD Key]) THEN { FIXED [TD Key] : SUM(IF [Office In Pair] AND RIGHT([step], 3) = " In"  THEN [worker_count] END) } END
IF NOT ISNULL([TD Key]) THEN { FIXED [TD Key] : SUM(IF [Office In Pair] AND RIGHT([step], 4) = " Out" THEN [worker_count] END) } END

// TD Size   (rank key: net effect, then people involved; the people part is below 0.1 so it never beats a real difference)
ABS([TD Total]) + [TD Gross] / 1000000

// TD Size 1 .. 4   (same LOD chain as the Compensation Walk card)
{ MAX([TD Size]) }
{ MAX(IF [TD Size] < [TD Size 1] THEN [TD Size] END) }
{ MAX(IF [TD Size] < [TD Size 2] THEN [TD Size] END) }
{ MAX(IF [TD Size] < [TD Size 3] THEN [TD Size] END) }

// TD Show   (the filter)
[Office In Pair] AND NOT ISNULL([TD Key]) AND [TD Gross] > 0 AND [TD Size] >= IFNULL([TD Size 4], 0)
```

Where it happened (offices for hires and exits, routes for moves):

```
// TD Office People   (people per driver per office; arrivals for moves)
IF NOT ISNULL([TD Key]) THEN
{ FIXED [TD Key], [location_id] : SUM(IF [Office In Pair] AND RIGHT([step], 4) <> " Out" THEN [worker_count] END) } END
// TD Office Max    { FIXED [TD Key] : MAX([TD Office People]) }
// TD Office Name   { FIXED [TD Key] : MAX(IF [TD Office People] = [TD Office Max] THEN [office_name] END) }

// Top Within People   { MAX(IF [flow_scope_label] = "Within one country" THEN [Pair People] END) }
// Top Within Pair     { MAX(IF [flow_scope_label] = "Within one country" AND [Pair People] = [Top Within People] THEN [Office Pair] END) }
// Top Across People   { MAX(IF [flow_scope_label] = "Across a border" THEN [Pair People] END) }
// Top Across Pair     { MAX(IF [flow_scope_label] = "Across a border" AND [Pair People] = [Top Across People] THEN [Office Pair] END) }
```

When two routes tie, `MAX` shows the alphabetically last name; that is acceptable for a one-line reason.

Text:

```
// TD Abs T   INT(ROUND(ABS([TD Total]) * 10, 0))
// TD Abs Text
(IF [TD Abs T] >= 10000
 THEN STR(DIV([TD Abs T], 10000)) + "," + RIGHT("00" + STR(DIV([TD Abs T], 10) % 1000), 3)
 ELSE STR(DIV([TD Abs T], 10)) END)
+ (IF [Is FTE] THEN "." + STR([TD Abs T] % 10) ELSE "" END)
// TD Up Text     IF [TD Abs T] > 0 AND [TD Total] > 0 THEN "+" + [TD Abs Text] ELSE "" END   (teal #006B66)
// TD Down Text   IF [TD Abs T] > 0 AND [TD Total] < 0 THEN "−" + [TD Abs Text] ELSE "" END   (coral #B8401F)
// TD Zero Text   IF [TD Abs T] = 0 THEN "net 0" ELSE "" END                                    (slate #5A6170)

// TD People Text   (comma pattern on TD Gross for hires and exits)
IF [TD Gross] >= 1000
THEN STR(DIV(INT([TD Gross]), 1000)) + "," + RIGHT("00" + STR(INT([TD Gross]) % 1000), 3)
ELSE STR(INT([TD Gross])) END

// TD Where   (empty in the Office view: the office is the group)
IF [p_View] = "Office" THEN "." ELSE
  (IF [TD Key] = "Hires" THEN "; most in " ELSE "; most from " END)
  + [TD Office Name] + " (" + STR([TD Office Max]) + ")."
END

// TD Why   (one line, at most about 65 characters)
CASE [TD Key]
WHEN "Hires"             THEN [TD People Text] + " people joined" + [TD Where]
WHEN "Voluntary exits"   THEN [TD People Text] + " people resigned" + [TD Where]
WHEN "Involuntary exits" THEN [TD People Text] + " people were let go" + [TD Where]
WHEN "Transfers"         THEN STR([TD In]) + " joined from other teams, " + STR([TD Out]) + " left, same office."
WHEN "Moves within a country" THEN
    (IF [TD In] = [TD Out] THEN STR([TD In]) + " moved, net 0" ELSE STR([TD In]) + " arrived, " + STR([TD Out]) + " left" END)
    + " · busiest " + [Top Within Pair] + ", " + STR([Top Within People])
WHEN "Moves across a border" THEN
    (IF [TD In] = [TD Out] THEN STR([TD In]) + " moved, net 0" ELSE STR([TD In]) + " arrived, " + STR([TD Out]) + " left" END)
    + " · busiest " + [Top Across Pair] + ", " + STR([Top Across People])
WHEN "FTE changes" THEN STR([TD Gross]) + " people changed hours."
END
```

Title and subtitle:

```
// TD Top Name   { MAX(IF [TD Size] = [TD Size 1] THEN [TD Key] END) }
// TD Top Value  { MAX(IF [TD Size] = [TD Size 1] THEN [TD Total] END) }
// TD Top N   INT(ROUND(ABS([TD Top Value]), 0))
// TD Headline
IF ISNULL([TD Top Name]) THEN "No movement in this selection"
ELSE [TD Top Name] + " moved " + (IF [Is FTE] THEN "FTE" ELSE "headcount") + " the most, "
     + (IF [TD Top Value] >= 0 THEN "+" ELSE "−" END)
     + (IF [TD Top N] >= 1000
        THEN STR(DIV([TD Top N], 1000)) + "," + RIGHT("00" + STR([TD Top N] % 1000), 3)
        ELSE STR([TD Top N]) END) END
// TD Driver Count   { COUNTD(IF [Office In Pair] THEN [TD Key] END) }
// TD Subtitle
"Largest of the " + STR([TD Driver Count]) + " drivers, ranked by net effect · moves count both ways"
```

### 9.2 Sheet

Same name-above-bar pattern as the Compensation Walk card (dual axis with `AVG(0)`, names pinned: `AVG(0)` axis unsynchronized and fixed 0 to 1). Changes from the old sheet:

1. Rows: `TD Key`, then `Measure Names` (dummy row above the bar, as before).
2. Filter `TD Show` = True (replaces the old one).
3. Name row label (on the `AGG(AVG(0))` tab), three lines: `<TD Group>` 8 pt gray; `<TD Key>  <TD Up Text><TD Down Text><TD Zero Text>` 10 pt navy with the three value fields colored teal, coral, slate; `<TD Why>` 9 pt gray.
4. Sort `TD Key` descending by `TD Size` (Field, Maximum).
5. No bars (decided for the Compensation Walk card on 2026-10-12): set the `<value>` tab's size to zero or drop it, so the card is a ranked list.
6. Title: line 1 `<TD Headline>` 12 pt bold navy; line 2 `<TD Subtitle>` 9 pt gray (drag both to Detail first; they show as `ATTR(...)`).
7. Tooltip off, or the driver with `TD In` and `TD Out`.

### 9.3 Check (FY26, rows in order)

| Selection | Rows |
|---|---|
| Company, Headcount | Hires +4,790 "4,790 people joined; most in Austin HQ (488)." · Voluntary exits −2,588 "most from Bengaluru (310)" · Involuntary exits −635 "most from Austin HQ (85)" · Moves within a country net 0 "600 moved, net 0 · busiest Bengaluru ↔ Hyderabad, 101" |
| Company, FTE | Hires +4,738.5 · Voluntary exits −2,534.0 · Involuntary exits −621.1 · FTE changes −81.6 "350 people changed hours." |
| Country India | Hires +1,038 (most in Bengaluru, 464) · Voluntary exits −613 (Bengaluru, 310) · Involuntary exits −131 (Hyderabad, 66) · Moves across a border +1 "28 arrived, 27 left · busiest Hyderabad ↔ New York, 5" |
| Office Bengaluru | Hires +464 · Voluntary exits −310 · Involuntary exits −55 · Moves within a country −23 "54 arrived, 77 left · busiest Bengaluru ↔ Hyderabad, 101" |
| Function Technology | Hires +1,821 (most in Hyderabad, 213) · Voluntary exits −935 (Bengaluru, 144) · Involuntary exits −232 (Hyderabad, 30) · Transfers −22 "44 joined from other teams, 66 left, same office." |

Headline FY26 Company: "Hires moved headcount the most, +4,790". Subtitle: "Largest of the 5 drivers, ranked by net effect · moves count both ways" (Company has no transfers: hires, two exits, two kinds of move).

---

## Part 10. Growth by region / country / office (`Geo Growth`)

### 10.1 Calcs

```
// Geo Name   (row level; the level follows p_Geo)
CASE [p_Geo] WHEN "Region" THEN [region] WHEN "Country" THEN [country_name] ELSE [office_name] END

// Geo Open    SUM(IF [Office In Pair] AND [step] = "Opening" THEN [Walk Value] END)
// Geo Close   SUM(IF [Office In Pair] AND [step] = "Closing" THEN [Walk Value] END)
// Geo Net     ZN([Geo Close]) - ZN([Geo Open])
// Geo Growth  IF ZN([Geo Open]) = 0 THEN NULL ELSE [Geo Close] / [Geo Open] - 1 END

// Geo Top   (table calc filter; compute using Geo Name only; leave Measure Names unticked)
RANK_UNIQUE(ABS([Geo Net]) + ZN([Geo Close]) / 1000000000, 'desc') <= 6

// Geo Net Text   (bar-end label, whole numbers in both lenses)
(IF [Geo Net] > 0 THEN "+" ELSEIF [Geo Net] < 0 THEN "−" ELSE "" END)
+ STR(INT(ROUND(ABS([Geo Net]), 0)))
+ (IF ISNULL([Geo Growth]) THEN " · new" ELSE
   " · " + (IF [Geo Growth] >= 0 THEN "+" ELSE "−" END)
   + STR(DIV(INT(ROUND(ABS([Geo Growth]) * 1000, 0)), 10)) + "." + STR(INT(ROUND(ABS([Geo Growth]) * 1000, 0)) % 10) + "%" END)

// Geo Count   { COUNTD(IF [Office In Pair] AND [step] = "Closing" THEN [Geo Name] END) }
// Geo Title   "Growth by " + LOWER([p_Geo])
// Geo Subtitle   (two lines; every field is an LOD, so it shows one value above the bars)
(IF [p_View] = "Company" THEN "Arcadia" ELSE [p_Group] END) + " overall "
+ [K Pct Sign] + [K Pct Text]
+ " (" + [K Open Text] + " | " + [K Close Text] + ")"
+ CHAR(10)
+ (IF [Geo Count] > 6 THEN "6 largest changes of " + STR([Geo Count]) ELSE "Every " + LOWER([p_Geo]) END)
+ " · opening | closing · bar: people added"
```

In the FTE lens the opening and closing in the subtitle keep one decimal (the `K` helpers); the bars and their labels are whole numbers.

### 10.2 Sheet

Start from your duplicate of `Region Headcount` (or a new sheet); same name-above-bar pattern with `<name>` = `Geo Name`, `<value>` = `Geo Net`.

1. Rows `Geo Name`, `Measure Names`; Columns `Geo Net`, `AVG(0)` (dual axis, **not** synchronized; `AVG(0)` axis fixed 0 to 1, as in the Region Bars fix, because a shrinking office makes `Geo Net` negative).
2. Filter **`Geo Top`** = True; Edit Table Calculation: Specific Dimensions, tick `Geo Name` only.
3. Name row label: `<Geo Name>   <Geo Open> | <Geo Close>` (name 9 pt navy, numbers 9 pt gray, format `#,##0` on the pills; in FTE `#,##0.0`).
4. `Geo Net` tab: bar color amber `#D98E04` (your pick for Growth by region), size about 40%; Label `<AGG(Geo Net Text)>` at the bar end, 9 pt bold navy.
5. Sort `Geo Name` descending by `Geo Net`.
6. Title: line 1 `<Geo Title>` 11 pt bold navy (on the left, leave room for the toggle), lines 2 and 3 `<Geo Subtitle>` 9 pt gray (drag both to Detail first; Tableau shows them as `ATTR(...)`).
7. Tooltip:
   ```
   <Geo Name>
   Opening <AGG(Geo Open)> · Closing <AGG(Geo Close)>
   Net change <AGG(Geo Net)> (<AGG(Geo Growth)>)
   ```

### 10.3 Level toggle (`Geo Toggle`)

Same as the map focus toggle (8.5): `Geo Option` = `CASE [step_order] WHEN 1 THEN "Region" WHEN 2 THEN "Country" WHEN 3 THEN "Office" END`; `Geo Is Current` = `[Geo Option] = [p_Geo]`; Text marks, navy / gray, 9 pt bold. Actions: **Set geo level** (Change Parameter `p_Geo` ← `Geo Option`) and **Deselect Geo Toggle**.

### 10.4 Check (FY26, Headcount)

| Selection | Rows, in order (net · growth) |
|---|---|
| Company, Region | North America 9,909 \| 10,426 +517 · +5.2%; Asia Pacific 8,524 \| 9,005 +481 · +5.6%; Europe 6,665 \| 7,043 +378 · +5.7%; Latin America 2,225 \| 2,356 +131 · +5.9%; Middle East & Africa 1,115 \| 1,175 +60 · +5.4%. Subtitle "Arcadia overall +5.5% (28,438 \| 30,005)" / "Every region · ..." |
| Company, Country | United States +369 · +4.1%; India +295 · +4.4%; Canada +148 · +16.2%; Poland +88 · +4.9%; Mexico +83 · +7.6%; United Kingdom +71 · +4.9%. "6 largest changes of 22" |
| Company, Office | Pune +158 · +49.4%; Austin HQ +103 · +3.3%; Vancouver +100 · +344.8%; Bengaluru +79 · +2.3%; Guadalajara +74 · +52.5%; San Francisco +72 · +5.7%. "6 largest changes of 35" |
| Country India, Office | Pune +158 · +49.4%; Bengaluru +79 · +2.3%; Hyderabad +58 · +2.0%. "Every office" |
| Function Technology, Office | Pune +77 · +44.0%; Vancouver +55 · +423.1%; Toronto +34 · +8.3%; Austin HQ +31 · +3.2%; Sao Paulo +30 · +7.8%; Guadalajara +27 · +47.4% |

The office view makes the story plain: the two big Indian centers barely grew (+2%); growth went to the new or young offices (Pune, Vancouver, Guadalajara).

---

## Part 11. Dashboard layout (Summary, 1400 x 850)

Same spacing system as the Compensation Walk: 30 px frame, 16 px gaps, 16 px padding inside every card, every card `#FBFBF8` with a 1 px `#E4E3DD` border, card edges on the KPI grid (cards at x 246, 474, 702, 930, 1158, each 212 wide).

| Card | x | y | w | h | Spans |
|---|---:|---:|---:|---:|---|
| KPI cards x5 | 246 + 228 n | 88 | 212 | 86 | unchanged |
| Map | 246 | 190 | 668 | 630 | KPI cards 1 to 3, down to the bottom frame (820) |
| Top drivers | 930 | 190 | 440 | 307 | KPI cards 4 and 5 |
| Growth | 930 | 513 | 440 | 307 | KPI cards 4 and 5 (190 + 307 + 16 = 513; 513 + 307 = 820) |

Why the map is tall rather than wide: the regional frames are taller than wide (Europe & Africa runs from Stockholm to Cape Town; Asia Pacific from Seoul to Melbourne), and the world frame fits 636 px wide. A 1124 x 300 strip, the Compensation Walk shape, wastes most of its width on any regional focus.

```
Card: Map                     floating, x 246, y 190, w 668, h 630, background #FBFBF8, border 1 px #E4E3DD, padding 16
|-- Map header                vertical, w 636, h 44
|     |-- Map Title           h 24
|     `-- Map Subtitle        h 20
|-- Footprint Map             w 636, h 530
`-- Map Legend row            horizontal, w 636, h 24
      |-- Growth Legend       w 400
      `-- Map Key             w 236
Map Focus Toggle              floating, x 614, y 258, w 276, h 24, background #FBFBF8 (inside the map's top right)

Card: Drivers                 floating, x 930, y 190, w 440, h 307, padding 16
`-- Top Drivers               w 408, h 275 (title block inside the sheet)

Card: Growth                  floating, x 930, y 513, w 440, h 307, padding 16
`-- Geo Growth                w 408, h 275
Geo Toggle                    floating, x 1174, y 529, w 180, h 22 (top right of the card, beside the title)
```

44 + 530 + 24 = 598 = 630 − 2 x 16. Remove any color or size legend Tableau adds. Bring the two floating toggles to the front, then the popovers (Group, Period, Info) to the very front.

Map credit (© Mapbox © OpenStreetMap) must stay visible: it is a license requirement.

---

## Part 12. Actions (complete list for the Footprint)

All Run on **Select**; Change Parameter actions use **Keep current value**; Deselect actions are filter actions from the sheet onto **the worksheet itself**, `zzTrue` → `zzFalse`, **Show all values**.

| # | Name | Type | Source | Target | Field | State |
|---|---|---|---|---|---|---|
| 1 | Open period panel | Parameter | Period Field | `p_PeriodOpen` | `Toggle Period Panel` | reused |
| 2 | Close group panel when period opens | Parameter | Period Field | `p_GroupOpen` | `Close Panel` | reused |
| 3 | Set span | Parameter | Span List | `p_Span` | `Span Value` | reused |
| 4 | Set From / Set To | Parameter | Period Panel | `p_From` / `p_To` | `from_month_end` / `to_month_end` | reused |
| 5 | Close on pick / Close on x | Parameter | Period Panel / Period Close | `p_PeriodOpen` | `Close Panel` | reused |
| 6 | Set view, Set group from view, Close panels on view change | Parameter | Rail View | `p_View`, `p_Group`, `p_GroupOpen`, `p_PeriodOpen`, `p_InfoOpen` | as before | reused |
| 7 | Open group panel, Set group, Close panel on pick / on ✕ | Parameter | Group Field / Group Panel / Panel Close | `p_GroupOpen`, `p_Group` | as before | reused |
| 8 | Set lens | Parameter | Lens Toggle | `p_Lens` | `Lens Pick` | reused (values changed) |
| 9 | Set routes | Parameter | Routes Toggle | `p_Routes` | `Routes Pick` | edited from Set cost |
| 10 | Set radius | Parameter | Radius Toggle | `p_RadiusKm` | `Radius Pick` | edited from Set currency |
| 11 | Reset (one per parameter) | Parameter | Reset | `p_From`, `p_To`, `p_View`, `p_Group`, `p_Lens`, `p_Span`, `p_Routes`, `p_RadiusKm`, `p_FocusOffice`, `p_MapFocus`, `p_Geo`, `p_GroupOpen`, `p_PeriodOpen`, `p_InfoOpen` | the Default calcs, `Close Panel` | edited |
| 12 | Open info, and the info closers | Parameter | Info Button and others | `p_InfoOpen`, ... | as before | reused |
| 13 | **Focus office** | Parameter | Footprint Map | `p_FocusOffice` | `office_name` | **new** |
| 14 | **Set map focus** | Parameter | Map Focus Toggle | `p_MapFocus` | `Focus Option` | **new** |
| 15 | **Set geo level** | Parameter | Geo Toggle | `p_Geo` | `Geo Option` | **new** |
| 16 | Deselect (one each) | Filter | Rail View, Group Field, Group Panel, Panel Close, Period Field, Span List, Period Panel, Period Close, Lens Toggle, Routes Toggle, Radius Toggle, Reset, Info Button, **Footprint Map**, **Map Focus Toggle**, **Geo Toggle** | the same sheet | `zzTrue` → `zzFalse` | three new |

Action 13: only the office layer is selectable (8.3 step 4 to 6), so a click always lands on an office. If the deselect on the map clears the selection before the parameter fires, set action 13 first in the list; if the ring does not move, delete action 16 for the map (a selected office then stays outlined, which is acceptable on a map).

---

## Part 13. Final checks, extract, publish

### 13.1 Interaction tests

| # | Do | Expect |
|---|---|---|
| 1 | Open the workbook (FY26, Company, Headcount, 3+, 1,000, London, World, Region) | Every check table above matches |
| 2 | Switch to FTE | KPI 1 29,354.5; drivers show FTE changes −81.6 fourth; map sizes change slightly; Growth shows FTE |
| 3 | Period: Quarter, FY26 Q4 | Company 29,618 → 30,005; Hires +1,317, Voluntary −742, Involuntary −188; 213 changed office (34 across a border); colors still on the same annual scale |
| 4 | View Country, India | Map shows three Indian offices and routes; KPIs 6,967 / 3 offices / Asia Pacific / 100.0% India / 210 |
| 5 | View Office, Bengaluru | One bubble, routes to Hyderabad, Pune, Warsaw; drivers include "54 arrived, 77 left" |
| 6 | Each map focus | Map reframes; offices and routes outside the focus disappear; the subtitle counts change |
| 7 | Click Bengaluru, then Radius 2,000 | Ring moves and grows; title updates |
| 8 | Growth toggle Region / Country / Office | The card swaps level without moving |
| 9 | Reset | Everything back to test 1 |
| 10 | A Month pair, then a small department | No blank sheet, no error; empty-state texts read naturally |

### 13.2 Extract and save

1. **Data > Footprint > Extract Data...** > All rows > **Extract**. Save the `.hyper` next to the workbook. About 666,000 rows.
2. **Data > Footprint > Extract > Refresh** if you edited the SQL afterwards.

### 13.3 Publish

1. Reset the dashboard (test 9), Summary dashboard active.
2. **File > Save to Tableau Public As...** → **Arcadia Global Workforce Footprint**.
3. Description (under 230 characters): "Where Arcadia's people are, where headcount grew and how people move between offices. One Custom SQL feeds offices, routes and radius as map layers. Fictional company, synthetic data. github.com/thialp/people-analytics-warehouse".
4. Add the URL to the README's case study 3 section and to `portfolio_handoff.md`.

### 13.4 Methodology line (Methodology page or info panel)

> Headcount by office at two month-ends for Arcadia Systems, a fictional company with synthetic data; executive officers excluded. Hires and exits compare the two dates, so people who joined and left in between are not counted (FY26: 4,790 hires here, 5,235 in the month-by-month Headcount & FTE Walk). An office move is the same person in a different office on the two dates. Routes combine both directions and hide pairs below the chosen number of people; the subtitle reports what is hidden. Distances are great-circle from postal-code coordinates. Every office closes: opening + hires − exits + transfers ± moves = closing; offices add up to the company; routes add up to the moves.
