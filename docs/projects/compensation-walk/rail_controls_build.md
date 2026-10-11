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
| 5 | Size: max. Fit: **Entire View**. Hide column header. Tooltip off |
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

### 4.2 Calcs
```
// Pair Label
CASE [pair_type]
 WHEN "Year over Year" THEN IF MONTH([from_month_end]) = 6 THEN LEFT([to_fiscal_period],4) ELSE STR(YEAR([to_month_end])) END
 WHEN "Fiscal Year to Date" THEN LEFT([to_fiscal_period],4) + " first " + STR([months_between]) + " months"
 WHEN "Quarter over Quarter" THEN [to_fiscal_quarter]
 WHEN "Month over Month" THEN LEFT(DATENAME('month',[to_month_end]),3) + " " + STR(YEAR([to_month_end]))
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
// Period Field Text
[Pair Label] + "  ▾"     (filter this sheet on Period Is Current = True)
// Toggle Period Panel   NOT [p_PeriodOpen]
```
Fiscal year caveat: Year over Year rows whose from-month is not June are calendar years; the label above shows the year only for those, and they sit in the same list. If you want fiscal only, add `MONTH([from_month_end]) = 6` to `Period In Span` when `p_Span` is Fiscal year.

### 4.3 Sheets
| Sheet | Build |
|---|---|
| `Period Field` | Text mark, `Period Field Text`; Detail `Toggle Period Panel`, `zzTrue`, `zzFalse`; filter `Period Is Current` = True; same look as Group Field |
| `Span List` | Square mark (like Rail View). Rows `pair_type` (filter out Custom Range), Text = `Span Label` (`CASE [pair_type] WHEN "Year over Year" THEN "Fiscal year" WHEN "Fiscal Year to Date" THEN "Year to date" WHEN "Quarter over Quarter" THEN "Quarter" WHEN "Month over Month" THEN "Month" END`), Detail `Span Value` (same text). Action sets `p_Span` from `Span Value` |
| `Period Panel` | Same as `Group Panel`: Columns `Pick Col`, Rows `Pick Row`, Text `Pair Label`, Detail `Period Key`, `from_month_end`, `to_month_end`, `Close Panel`, zz fields; filter `Period In Span` = True and `pair_type` not Custom; table calcs set to Specific Dimensions with `Period Key` first and every field ticked. Use `Pick Rows` = `INT((SIZE()+3)/4)` for 4 columns, or keep 3 |
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

## Part 5. Headings, footnote, heights

Headings are Text objects (9 pt, bold, `#8FA0B8`, uppercase): PERIOD, VIEW BY, `Group Heading` (existing), SHOW PAY AS, COST, CURRENCY.

Footnote: Text object "Arcadia Systems is fictional; all data is synthetic", 9 pt, white at about 60% (`#9AA5B5` on navy).

Rail stack, container padding 20, every item 176 wide:

| Item | Height |
|---|---|
| Blank | 24 |
| Logo | 40 |
| Blank | 24 |
| PERIOD | 18 |
| Blank | 6 |
| Period Field | 30 |
| Blank | 22 |
| VIEW BY | 18 |
| Blank | 6 |
| Rail View | 144 |
| Blank | 22 |
| Group Heading (DZV) | 18 |
| Blank | 6 |
| Group Field (DZV) | 30 |
| Blank | 22 |
| SHOW PAY AS | 18 |
| Blank | 4 |
| Lens | 30 |
| Blank | 14 |
| COST | 18 |
| Blank | 4 |
| Cost | 30 |
| Blank | 14 |
| CURRENCY | 18 |
| Blank | 4 |
| Currency | 30 |
| Blank | 22 |
| Reset | 30 |
| Flexible blank | rest |
| Footnote | 36 |
| Blank | 24 |

Popover y: field y minus 6. Re-check the Group and Period popover x (214) and front order after moving things.

---

## Test table
| # | Do | Expect |
|---|---|---|
| 1 | Click each toggle option | Cards update, pill moves, no blue box |
| 2 | Open Period, pick "Quarter", pick FY26 Q4 | Panel lists quarters newest first; picking closes it; field reads FY26 Q4 |
| 3 | Open Period, then Group | Period closes |
| 4 | Change several things, click Reset | Everything back to FY26, Company, Avg per FTE, Loaded, Constant |
| 5 | Switch to Company | Group Field and Group Heading disappear, controls below stay aligned |
