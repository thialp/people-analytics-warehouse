# Rail controls: build steps (Lens, Cost, Currency, Reset, Period, footnote, heights)

Data source for every calc and sheet: the walk (`ArcadiaHR`). Do the parts in order and test each one.
Group/View pickers are in [rail_group_picker_build.md](rail_group_picker_build.md).

---

## Part 0. Shapes (once)

1. Run `python docs/brand/build/make_rail_toggle_shapes.py 1D3150` (replace `1D3150` with your Group Field hex; it only colours the preview).
2. Copy the 12 new files `docs/brand/shapes/Arcadia/seg_lens_*`, `seg_cost_*`, `seg_currency_*` to `Documents/My Tableau Repository/Shapes/Arcadia`.
3. Tableau: on any sheet, Shape card > Reload Shapes.
4. Assign every shape by hand (Shape card > pick the value > click its file). Assign Palette does NOT match by name; it assigns in alphabetical order.

| Option | On/off files |
|---|---|
| Avg per FTE / Total payroll | `seg_lens_fte_*`, `seg_lens_amount_*` |
| Loaded / Base | `seg_cost_loaded_*`, `seg_cost_base_*` |
| Constant / Nominal | `seg_currency_constant_*`, `seg_currency_nominal_*` |

Look: on = white pill, navy text; off = light text. Capsule colour comes from Tableau shading (Part 1, step 6).

---

## Part 1. Lens toggle (repeat for Cost and Currency)

Same technique as Dashboard #1 (two data rows = two choices).

### 1.1 Calcs

```
// Lens Option
IF [step] = "Opening" THEN "fte"
ELSEIF [step] = "Closing" THEN "amount" END

// Lens State
IF ([Lens Option] = "fte") = [Is FTE] THEN "on" ELSE "off" END

// Lens Shape  (must equal the PNG file name without .png)
"seg_lens_" + [Lens Option] + "_" + [Lens State]
```

`p_Lens` stores `Per FTE` and `Total` (displayed Avg pay per FTE / Total payroll). Do not use `LOWER([p_Lens])`; use the existing `Is FTE` calc for the state.

### 1.2 Sheet `Lens Toggle`

| Step | Setting |
|---|---|
| 1 | Marks: **Shape** |
| 2 | Columns: `Lens Option` (Discrete). Sort: Manual, `fte` first |
| 3 | Filter `Lens Option`: exclude **Null** |
| 4 | Shape: `Lens Shape`. Click the Shape card, pick the palette Arcadia, assign each value by hand (Assign Palette does not match by name) |
| 5 | Size: max. Sheet fit: **Standard** (Entire View makes the shapes tiny in a 30 px cell); the dashboard item stays Entire View. Hide column header. Tooltip off |
| 6 | Format > Shading: Worksheet and Pane = Group Field blue. Lines None |
| 7 | Detail: `zzTrue`, `zzFalse` |

Dashboard item: 176 x 30, background Group Field blue, corner radius to match the Group Field, inner padding 0.

### 1.3 Actions

| Action | Type | Source | Target | Field | Clearing |
|---|---|---|---|---|---|
| Set lens | Change Parameter | Lens Toggle | `p_Lens` | `Lens Pick` (see note) | Keep current value |
| Deselect Lens Toggle | Filter | Lens Toggle | Lens Toggle (worksheet) | `zzTrue` > `zzFalse` | Show all values |

Note: the parameter wants `Per FTE` / `Total`. Make the field the action passes `Lens Pick` = `IF [step]="Opening" THEN "Per FTE" ELSEIF [step]="Closing" THEN "Total" END` and put it on Detail. Use `Lens Pick` as the field in the action; `Lens Option` stays for the shape. (Do not call it `Lens Value`: that name is already the measure on the cards.)

### 1.4 Remove the old `p_Lens` control from the top right of the dashboard. Heading text above the toggle: `SHOW PAY AS` (see Part 5).

### 1.5 Test

| Do | Expect |
|---|---|
| Click Total payroll | Cards switch to totals; pill moves; no blue box |
| Click Avg per FTE | Back |

---

## Part 2. Cost and Currency toggles

Same as Part 1 with:

| Sheet | Option calc | State calc compares to | Shape calc | Values passed to parameter |
|---|---|---|---|---|
| Cost Toggle | `Opening` > `loaded`, `Closing` > `base` | `LOWER([p_Cost])` | `"seg_cost_" + [Cost Option] + "_" + [Cost State]` | `Cost Pick`: `Loaded` / `Base` |
| Currency Toggle | `Opening` > `constant`, `Closing` > `nominal` | `LOWER([p_Currency])` | `"seg_currency_" + ...` | `Currency Pick`: `Constant` / `Nominal` |

Check the exact strings your `p_Cost` and `p_Currency` hold (Data pane > right-click parameter > Edit) and use those in `Cost Pick` / `Currency Pick`.

---

## Part 3. Reset

### 3.1 Sheet `Reset`
Marks Square, Text = a calc `Reset Text` = `"Reset"`, left aligned like the Rail View, shading Group Field blue. Detail: the constants below, `zzTrue`, `zzFalse`.

| Calc | Formula |
|---|---|
| `Default From` | `DATE("2025-06-30")` |
| `Default To` | `DATE("2026-06-30")` |
| `Default View` | `"Company"` |
| `Default Group All` | `"Arcadia Systems"` |
| `Default Lens` | `"Per FTE"` |
| `Default Cost` | `"Loaded"` |
| `Default Currency` | `"Constant"` |
| `Default Span` | `"Fiscal year"` |

### 3.2 Actions (Change Parameter, source Reset, keep current value)

| Target | Field |
|---|---|
| `p_From` | `Default From` |
| `p_To` | `Default To` |
| `p_View` | `Default View` |
| `p_Group` | `Default Group All` |
| `p_Lens` | `Default Lens` |
| `p_Cost` | `Default Cost` |
| `p_Currency` | `Default Currency` |
| `p_Span` (Part 4) | `Default Span` |
| `p_GroupOpen` | `Close Panel` |
| `p_PeriodOpen` (Part 4) | `Close Panel` |

Plus a Deselect filter action for `Reset`.

---

## Part 4. Period picker (popover, same pattern as Group)

### 4.1 Parameters
| Name | Type | Values | Current |
|---|---|---|---|
| `p_Span` | String list | Fiscal year, Year to date, Quarter, Month | Fiscal year |
| `p_PeriodOpen` | Boolean | | False |

`p_From` and `p_To` must be Date parameters with Allowable values **All**. A list of quarter-end dates silently rejects the Month pairs' non-quarter-end dates: the Change Parameter action then updated one end of the pair and kept the other (Apr '25 gave Mar 31 2025 to the old To, which is a "Custom range" pair).

### 4.2 Calcs
```
// Pair Label
CASE [pair_type]
 WHEN "Year over Year" THEN LEFT(DATENAME('month',[from_month_end]),3) + " " + RIGHT(STR(YEAR([from_month_end])),2) + " → " + LEFT(DATENAME('month',[to_month_end]),3) + " " + RIGHT(STR(YEAR([to_month_end])),2)
 WHEN "Fiscal Year to Date" THEN LEFT([to_fiscal_period],4) + " first " + STR([months_between]) + " months"
 WHEN "Quarter over Quarter" THEN [to_fiscal_quarter]
 WHEN "Month over Month" THEN LEFT(DATENAME('month',[to_month_end]),3) + " '" + RIGHT(STR(YEAR([to_month_end])),2)
 ELSE "Custom range" END

// Span Type  (pair_type for each p_Span value)
CASE [p_Span]
 WHEN "Fiscal year" THEN "Year over Year"
 WHEN "Year to date" THEN "Fiscal Year to Date"
 WHEN "Quarter" THEN "Quarter over Quarter"
 WHEN "Month" THEN "Month over Month" END

// Period In Span
[pair_type] = [Span Type]
// Period Is Current
[from_month_end] = [p_From] AND [to_month_end] = [p_To]
// Period Key   (newest first)
-DATEDIFF('day', #2000-01-01#, [to_month_end])
// Pair Name   (Period Field and the Period Panel tooltip: adds the fiscal-year name to June to June pairs)
IF [pair_type] = "Year over Year" AND MONTH([from_month_end]) = 6
THEN LEFT([to_fiscal_period],4) + " · " + [Pair Label] ELSE [Pair Label] END
// Period Field Text
[Pair Name] + "  ▾"     (filter this sheet on Period Is Current = True)
// Toggle Period Panel   NOT [p_PeriodOpen]

// Grid position, 4 columns filled down (all three are table calcs, Specific Dimensions: Period Key, Pair Label)
// Period Rows   IF [p_Span] = "Month" THEN INT((SIZE() + 7) / 8) ELSE INT((SIZE() + 3) / 4) END
//               (Month: 48 pairs as 6 rows x 8 columns, ~57 px a column, so labels must stay short and must not wrap; the others keep 4 columns)
// Period Col    INT((INDEX() - 1) / [Period Rows])
// Period Row    (INDEX() - 1) % [Period Rows]
```
Year over Year holds 13 pairs: the fiscal years (June to June) plus the trailing 12 months ending at each quarter end. A label of just the calendar year made Dec 2025 and Sep 2025 both read "2025", which also merged them into one table-calc partition. Hence `Sep 24 → Sep 25` (opening to closing month-end) for every pair, June to June included, so the start of each comparison is visible (a bare `FY26` read like a column header, not a choice). The fiscal-year name stays in `Pair Name`: the rail field reads `FY26 · Jun 25 → Jun 26`. The other three spans already have unique labels. Result with 13 pairs: 4 rows by 4 columns, one fiscal year per column (FY26, Mar 25 → Mar 26, Dec 24 → Dec 25, Sep 24 → Sep 25 down column 0).

The last column (FY23) holds only one option, and that is correct: the warehouse starts at the Jun 30, 2022 month-end, so a trailing 12 months ending Sep 22, Dec 22 or Mar 23 would need a start before the data. The earliest fiscal year is always partial in any history; backfilling would only move the gap to the new earliest year. The page subtitle states the data range.

```
// Span Display   (Label on Span List; the active span gets the same "›" marker as Rail View)
IF [Span Value] = [p_Span] THEN "› " + [Span Label] ELSE [Span Label] END
```
`Span Label` shows "Year over year" for the first option (it also holds the trailing-12-month pairs); `Span Value` still returns `Fiscal year`, the value stored in `p_Span`.

### 4.3 Sheets
| Sheet | Build |
|---|---|
| `Period Field` | Text mark, `Period Field Text`; Detail `Toggle Period Panel`, `zzTrue`, `zzFalse`; filter `Period Is Current` = True; same look as Group Field |
| `Span List` | Square mark (like Rail View). Rows `pair_type` (filter out Custom Range), Text = `Span Display` (`Span Label` is `CASE [pair_type] WHEN "Year over Year" THEN "Year over year" WHEN "Fiscal Year to Date" THEN "Year to date" WHEN "Quarter over Quarter" THEN "Quarter" WHEN "Month over Month" THEN "Month" END`), Detail `Span Value` (the old text, `Fiscal year`, so `p_Span` keeps its values). Sort `pair_type` by `Span Order` (1 to 4), no Color pill. Action sets `p_Span` from `Span Value` |
| `Period Panel` | Build from a new sheet (not a copy of `Group Panel`). Filter `Period In Span` = True. Detail `Period Key` first, then `Pair Label`; Text `Pair Label`; Columns `Period Col`, Rows `Period Row`; mark type Text. Every table calc (`Period Col`, `Period Row` and the nested `Period Rows`) is Specific Dimensions with `Period Key` and `Pair Label` ticked, Deepest. **Color uses `ATTR([Period Is Current])`, never the plain field**: a dimension on Color splits the table-calc partitions (the current pair lands in its own partition and sits on top of another cell). Then add `from_month_end`, `to_month_end`, `Close Panel`, `zzTrue`, `zzFalse` to Detail for the actions, ticking them in the table calcs as they arrive |
| `Period Close` | Copy of `Panel Close` |

Layout: popover `Period Popover` floating, same style as Group Popover, front, DZV `p_PeriodOpen`; `Span List` on the left (120 wide), `Period Panel` on the right.

### 4.4 Actions
| Name | Type | Source | Target | Field |
|---|---|---|---|---|
| Open period panel | Change Parameter | Period Field | `p_PeriodOpen` | `Toggle Period Panel` |
| Close group panel when period opens | Change Parameter | Period Field | `p_GroupOpen` | `Close Panel` |
| Close period panel when group opens | Change Parameter | Group Field | `p_PeriodOpen` | `Close Panel` |
| Set span | Change Parameter | Span List | `p_Span` | `Span Value` |
| Set From | Change Parameter | Period Panel | `p_From` | `from_month_end` |
| Set To | Change Parameter | Period Panel | `p_To` | `to_month_end` |
| Close on pick | Change Parameter | Period Panel | `p_PeriodOpen` | `Close Panel` |
| Close on x | Change Parameter | Period Close | `p_PeriodOpen` | `Close Panel` |
| Close on view change | Change Parameter | Rail View | `p_PeriodOpen` | `Close Panel` |
| Deselect Period Field / Span List / Period Panel / Period Close | Filter | each | itself | `zzTrue` > `zzFalse` |

Delete the old From/To controls and quick picks.

---

## Part 5. Look, spacing, wording, footnote

### 5.1 Colors (decided 2026-10-11)
| Part | Value |
|---|---|
| Selected toggle option (pill in the PNGs) | wash `#E4E3DD` with navy text. Regenerate: `python3 docs/brand/build/make_rail_toggle_shapes.py 1D3150 E4E3DD`, copy the PNGs, Reload Shapes |
| Group Field | background `#E4E3DD`, text navy `#13233A`, same radius as the toggles. On the `Group Field` sheet: font color navy, Shading = `#E4E3DD`; dashboard item background `#E4E3DD` |
| Capsule behind the toggles | Group Field blue (`#1D3150`-ish) |

### 5.2 Wording: headings read as actions (no dynamic text change except the Group heading)
| Heading | Text |
|---|---|
| Period | SELECT PERIOD |
| View | SELECT VIEW |
| Group | `Panel Title` becomes `"Select " + CASE ... "a function" ...` (shown in capitals by `Group Heading` in the rail). The Group popover title is a **duplicate sheet** (`Group Heading 2`) that reads the same `Panel Title`: one sheet cannot be placed twice with different styling, and the rail one has its own font and caps. The Period popover title is plain text: "Select a period" |
| Pay | SHOW PAY AS |
| Cost | SELECT COST |
| Currency | SELECT CURRENCY |

### 5.3 Group Block (stops the rail jumping when you choose All)
Vertical container `Group Block` in the Rail: `Group Heading` (16) + Blank (6) + `Group Field` (30) = 52. Item menu > **Fix Height**, 52, background None, padding 0. The Has Groups visibility stays on the heading and the field, so the 52 px is kept even when both are hidden.

### 5.4 Spacing system
Every control is a **section**: heading 16, gap 6, control. Sections are 24 apart. Nothing else in the rail uses another gap.

| Item | Height | Running y |
|---|---|---|
| Top Blank | 24 | 24 |
| Logo | 40 | 64 |
| Blank | 28 | 92 |
| SELECT PERIOD (16) + 6 + Period Field (30) | 52 | 144 |
| Blank | 24 | 168 |
| SELECT VIEW (16) + 6 + Rail View (150) | 172 | 340 |
| Blank | 24 | 364 |
| Group Block | 52 | 416 |
| Blank | 24 | 440 |
| SHOW PAY AS (16) + 6 + Lens (30) | 52 | 492 |
| Blank | 24 | 516 |
| SELECT COST (16) + 6 + Cost (30) | 52 | 568 |
| Blank | 24 | 592 |
| SELECT CURRENCY (16) + 6 + Currency (30) | 52 | 644 |
| Blank | 24 | 668 |
| Reset | 30 | 698 |
| Flexible Blank | rest | |
| Footnote | 36 | |
| Bottom Blank | 24 | 850 |

**Dividers instead of some Blanks (decided 2026-10-12).** `docs/brand/arcadia_rail_divider.png` (400 x 48, made by `docs/brand/build/make_rail_divider.py`) is a transparent image with a 1 px line (white at 14%). Drop it onto the dashboard as an **Image** item (Fit image, no link, no border), 200 x 24, in place of the 24 px Blank. It has the same height as the Blank it replaces, so nothing else moves. Use it in three places: after Group Block (before SHOW PAY AS), before Reset, and optionally after the logo. Between the other sections keep the plain 24 Blank, so the rail reads as three blocks: what you look at (period, view, group), how pay is measured (pay as, cost, currency), and Reset. A container border is not an option: Tableau borders go on all four sides, so one section per container would box every control.

Use a Blank of the exact height for every gap, text objects at 16 high (9 pt, bold, `#8FA0B8`), and a heading's 6 px gap as a Blank of 6 (or text inner padding bottom 6). Rail View can be 150 (6 rows of 25) if 172 looks loose.

### 5.5 Subtitle and titles follow Cost and Currency
```
// Cost Text
IF [p_Cost] = "Loaded" THEN "loaded cost" ELSE "base pay" END
// Currency Text
IF [p_Currency] = "Constant" THEN "constant currency" ELSE "nominal currency" END
```
- `Page Subtitle`: end with `+ " · " + [Cost Text] + ", " + [Currency Text]` instead of `" · loaded cost, constant currency"`.
- `Waterfall Subtitle`: `"Pay per FTE = " + [Cost Text] + " ÷ FTE"` and `"Total payroll = " + [Cost Text] + " of all workers"`.

### 5.6 Info button and explanation panel
What the panel says (checked against the SQL, `compensation_walk.md` and `methodology.md`):
- **Loaded** = base pay plus the employer fringe rate (benefits and employer taxes), so loaded = base x (1 + fringe rate). Bonus and tenure pay are not in the base column; tenure increases and market adjustments show up in the walk as changes to base pay.
- **Base** = annualized base salary x FTE, with no fringe.
- **Constant** = every month converted at one fixed rate (30 June 2026), so currency swings are removed and the walk shows pay changes only.
- **Nominal** = each month at its own exchange rate, so the walk also has an "FX Translation" line.
- **Avg per FTE** = pay divided by FTE; **Total payroll** = pay of all workers.

Build:
1. Copy `rail_info_open.png` and `rail_info_close.png` (`docs/brand/shapes/Arcadia/`, 64 px, `#B8C0CC`) into `Documents/My Tableau Repository/Shapes/Arcadia`, then open the Shape palette (Marks card > Shape) and click Reload Shapes at the bottom of the Edit Shape dialog.
2. Parameter `p_InfoOpen`, Boolean, False. Calcs: `Toggle Info` = `NOT [p_InfoOpen]`; `Info Shape` = `IF [p_InfoOpen] THEN "rail_info_close" ELSE "rail_info_open" END` (values must match the file names). Reuse `Close Panel` (= FALSE) to close.
3. Sheet `Info Button`: Shape mark; `Info Shape` on Shape (assign the two values by hand); `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse` on Detail; filter `step` = Opening so there is one mark. Fit Standard; dashboard item Entire View, 16 x 16.
4. Layout: inside the `Show Pay As` container, a horizontal container 200 x 16: SHOW PAY AS text (flexible) on the left, `Info Button` (16 x 16) on the right.
5. Floating vertical container `Info Popover`: navy `#13233A`, about 380 x 250, same x as the other popovers (about 215), top aligned with the SHOW PAY AS heading. Title "How pay is measured", then the five definitions above, 10 to 11 pt, terms bold white, text `#B8C0CC`. Control visibility using value = `p_InfoOpen`. Bring to front.
6. Actions: `Open info` (Info Button, Select, Change Parameter, `p_InfoOpen` <- `Toggle Info`); `Deselect Info Button` (filter, zzTrue to zzFalse, the worksheet itself, Show all values); Info Button also sets `p_PeriodOpen` and `p_GroupOpen` <- `Close Panel`; Period Field and Group Field set `p_InfoOpen` <- `Close Panel` (add `Close Panel` to their Detail); Rail View and Reset also set `p_InfoOpen` <- `Close Panel`.

---

## Test table
| # | Do | Expect |
|---|---|---|
| 1 | Click each toggle option | Cards update, pill moves, no blue box |
| 2 | Open Period, pick "Quarter", pick FY26 Q4 | Panel lists quarters newest first; picking closes it; field reads FY26 Q4 |
| 3 | Open Period, then Group | Period closes |
| 4 | Change several things, click Reset | Everything back to FY26, Company, Avg per FTE, Loaded, Constant |
| 5 | Switch to Company | Group Field and Group Heading disappear, controls below stay aligned |
