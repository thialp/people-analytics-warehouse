# Seats to Fill: spikes on Tableau Public (phase 4)

Four small tests, run before the page is designed in detail, so a limit of Tableau Public is found now and not in the middle of the build. They use one throw-away workbook, `D5 Spikes`, on the page's one Custom SQL data source. Each spike has a pass condition and a fallback chosen in advance. A failure is written down with its fallback; the design is never changed quietly. Arcadia Systems is fictional and all data is synthetic.

| Spike | Tests | Fallback |
|---|---|---|
| S1 | Cascading check-mark lists, Function > Department: children start ticked, a parent's un-tick cleans its children (`REGEXP_REPLACE`), the last ticked department is locked, an option with nothing behind it is dimmed | Changing a parent clears all child exclusions of that hierarchy (no regex) |
| S2 | The same for Region > Country > Office (two levels of clean-up) | As S1 |
| S3 | The likely range: P10, P50 and P90 across 100 draws, summed over any selection | `WINDOW_PERCENTILE` with `draw` on Detail |
| S4 | The survival curve as a table calculation, read at 30, 60 and 90 days | The curve computed per level band in SQL, scoped by function only |
| S5 | Published on Tableau Public: speed of a click, of a draw-range sheet, extract size | Fewer draws (50), or the mean-and-variance range |

## Setup (once)

**1. Refresh SQL Server's forecast tables.** This branch keeps a row for every draw (396,400 Draw rows), so the forecast tables changed. There is no need for the full `build_all`: three scripts reload them, in under a minute.

```bash
cd ~/GitHub/people-analytics-warehouse && git checkout main && git pull && git fetch --prune
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
for f in 02b_load_forecast 03e_build_dw_forecast 17_validate_seats_to_fill; do
  docker exec arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/$f.sql | grep -E "mart_pid_forecast_draws|returned|FAIL|Msg"
done
cp tableau/custom_sql_seats_to_fill.sql "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/5 Seats to Fill/"
```

Expected output, three lines and no `FAIL` or `Msg`:
- `raw.mart_pid_forecast_draws            396400 rows`
- `Built fc: mart_pid_fill_quarter, mart_fill_survival, mart_pid_forecast_draws, ...`
- `Seats to Fill Custom SQL returned 542701 rows in N seconds`

**2. Connect Tableau Desktop.** Connect > Microsoft SQL Server:
- server `localhost`, port `1433`, database `ArcadiaHR`;
- SQL Server Authentication, user `sa`, the password from `docker exec arcadia-sql printenv MSSQL_SA_PASSWORD`;
- Require SSL off.

**3. Add the Custom SQL.** Drag **New Custom SQL** onto the canvas and paste the whole of `tableau/custom_sql_seats_to_fill.sql`. Name the data source `Seats to Fill`. Choose **Extract**, then save as `D5 Spikes.twb` in `ArcadiaHR/5 Seats to Fill/`.

**Checkpoint 0.** On a sheet, put `row_type` on Rows and `Number of Records` (or `COUNT(row_type)`) on Text. Expected:

| row_type | Rows |
|---|---:|
| Backtest | 19,219 |
| CW budget | 48 |
| Draw | 396,400 |
| Quarter | 21,720 |
| Survival | 105,294 |
| Accuracy | 20 |
| Total | 542,701 |

**4. Data types.** Convert `quarter_offset`, `fy_offset`, `draw`, `period`, `origin_quarter_offset` and `horizon` to Dimension (they are keys, never summed).

## The parameters and calculations every spike uses

**Parameters.** Create five, all String, allowable values All, current value empty (delete the text so the box is blank):

| Parameter | Holds, when something is chosen |
|---|---|
| `p_Functions` | the chosen functions, `\|People\|Finance\|`; empty means every function |
| `p_DeptOff` | the departments **unticked** inside the chosen functions, `\|People>Talent Acquisition\|` |
| `p_Regions` | the chosen regions, `\|Asia Pacific\|`; empty means every region |
| `p_CountryOff` | the countries unticked, `\|Asia Pacific>Japan\|` |
| `p_OfficeOff` | the offices unticked, `\|Asia Pacific>India>Pune\|` |

The child strings store **exclusions**, so every child of a chosen parent starts ticked. Each key carries its parents (`Region>Country>Office`), so un-ticking a parent can strip its children with one regular expression.

**Calculations** (on `Seats to Fill`). Type the names exactly.

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
WHEN "CW budget" THEN [Function In]
ELSE [Dept In] AND [Office In] END

// Activity   (what "something is behind this option" means: history PIDs opened, filled or waiting)
IF [row_type] = "Quarter" AND [quarter_offset] <= 0
THEN ZN([filled]) + ZN([vacant_end]) + ZN([opened_backfill]) + ZN([opened_net_new]) + ZN([opened_immediate]) END

// zzTrue    TRUE
// zzFalse   FALSE
```

**Check sheet `S Check`** (Text marks, one row per line; keep it on every spike dashboard):

```
// Check FY Fills    SUM(IF [row_type] = "Quarter" AND [In Scope] AND [fy_offset] = 0 THEN [filled] END)
// Check Waiting     SUM(IF [row_type] = "Quarter" AND [In Scope] AND [quarter_offset] = 0 THEN [vacant_end] END)
// Check Strings     "Functions " + [p_Functions] + "  ·  DeptOff " + [p_DeptOff] + "  ·  Regions " + [p_Regions]
//                   + "  ·  CountryOff " + [p_CountryOff] + "  ·  OfficeOff " + [p_OfficeOff]
```

Expected with every parameter empty: FY fills **6,849**, waiting **902**.

## S1. Function > Department

### Calculations

```
// Function Dim   (the function has nothing in the chosen locations: clicking it does nothing)
SUM(IF [Office In] THEN [Activity] END) = 0

// Function Toggle   (row-level: add or remove this function)
IF CONTAINS([p_Functions], "|" + [function_name] + "|")
THEN (IF [p_Functions] = "|" + [function_name] + "|" THEN "" ELSE REPLACE([p_Functions], "|" + [function_name] + "|", "|") END)
ELSE (IF [p_Functions] = "" THEN "|" + [function_name] + "|" ELSE [p_Functions] + [function_name] + "|" END) END

// Function Pick
IF [Function Dim] THEN [p_Functions] ELSE MIN([Function Toggle]) END

// DeptOff Without Function   (row-level: the exclusions with this function's departments stripped)
IF REGEXP_REPLACE([p_DeptOff], "\|" + [function_name] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_DeptOff], "\|" + [function_name] + ">[^|]*", "") END

// Function DeptOff Pick
IF [Function Dim] THEN [p_DeptOff] ELSE MIN([DeptOff Without Function]) END

// Function Tick
IF [Function Dim] THEN "dim" ELSEIF [p_Functions] <> "" AND MIN([Function In]) THEN "on" ELSE "off" END
```

Walk-through of `DeptOff Without Function`, with `|People>Talent Acquisition|Finance>Tax|`:
- a click on People leaves `|Finance>Tax|`;
- a click on Finance leaves `|People>Talent Acquisition|`;
- with only `|People>Talent Acquisition|`, the result `|` becomes empty.

```
// Dept Visible   (row-level, a filter: only the chosen functions' departments are offered)
[Function In]

// Dept Ticked
MIN([Dept In])

// Dept Scope
SUM(IF [Dept In] AND [Office In] THEN [Activity] END)

// Scope Total
MIN({ FIXED : SUM(IF [Dept In] AND [Office In] THEN [Activity] END) })

// Dept Locked   (the last ticked department holding the view up: it cannot be unticked)
[Dept Ticked] AND ZN([Scope Total]) - ZN([Dept Scope]) = 0

// Dept Dim
SUM(IF [Office In] THEN [Activity] END) = 0

// Dept Toggle   (row-level)
IF CONTAINS([p_DeptOff], "|" + [Dept Key] + "|")
THEN (IF [p_DeptOff] = "|" + [Dept Key] + "|" THEN "" ELSE REPLACE([p_DeptOff], "|" + [Dept Key] + "|", "|") END)
ELSE (IF [p_DeptOff] = "" THEN "|" + [Dept Key] + "|" ELSE [p_DeptOff] + [Dept Key] + "|" END) END

// Dept Pick
IF [Dept Locked] OR [Dept Dim] THEN [p_DeptOff] ELSE MIN([Dept Toggle]) END

// Dept Tick
IF [Dept Dim] THEN "dim" ELSEIF [Dept Locked] THEN "locked" ELSEIF [Dept Ticked] THEN "on" ELSE "off" END
```

### Sheets

**`S1 Functions`:**
- Filter `row_type` = Quarter.
- Rows `function_name`.
- Marks Shape; Shape `Function Tick` from Arcadia D4: on → `d4_tick_on`, off and dim → `d4_tick_off`.
- Color `Function Tick`: on navy `#13233A`, off `#8C9BB0`, dim `#D5DBE4`.
- Label `function_name`.
- Detail: `Function Pick`, `Function DeptOff Pick`, `zzTrue`, `zzFalse`.
- Tooltip off.

**`S1 Departments`:**
- Filters `row_type` = Quarter and `Dept Visible` = True.
- Rows `function_name`, then `department_name`.
- Shape `Dept Tick`: on and locked → `d4_tick_on`, off and dim → `d4_tick_off`.
- Color `Dept Tick`: on navy `#13233A`, locked slate `#5A6170`, off `#8C9BB0`, dim `#D5DBE4`.
- Label `department_name`.
- Detail: `Dept Pick`, `zzTrue`, `zzFalse`.
- Tooltip off.

### Dashboard `S1` and its actions

Put `S1 Functions`, `S1 Departments` and `S Check` on one dashboard. Every Change Parameter action: Run on **Select**, aggregation None, clearing the selection **Keep current value**.

| Name | Source sheet | Target parameter | Source field |
|---|---|---|---|
| Toggle function | S1 Functions | `p_Functions` | `Function Pick` |
| Function cleans departments | S1 Functions | `p_DeptOff` | `Function DeptOff Pick` |
| Toggle department | S1 Departments | `p_DeptOff` | `Dept Pick` |

Plus a deselect on each list: Filter action, source and target the same sheet, `zzTrue` → `zzFalse`, clearing **Show all values**.

### Tests (Presentation mode, then on the web in S5)

| # | Do | Expect |
|---:|---|---|
| 1 | Nothing chosen | 8 functions off; 31 departments listed, all ticked; FY fills 6,849, waiting 902 |
| 2 | Click People | People on; only HR Business Partners, People Analytics, Talent Acquisition, Total Rewards listed, all ticked; `p_Functions` = `\|People\|` |
| 3 | Untick Talent Acquisition | `p_DeptOff` = `\|People>Talent Acquisition\|`; FY fills **175**, waiting **21** |
| 4 | Click People again (off) | No function chosen, all 31 departments back; `p_DeptOff` empty (the regex cleaned it) |
| 5 | Click People again (on) | All four People departments ticked again |
| 6 | Click Legal & Compliance (People still on) | Six departments listed; untick Legal: Compliance & Risk stays |
| 7 | Click People off, so only Legal & Compliance is chosen, with Legal unticked | Compliance & Risk shows **locked** (slate); clicking it changes nothing |

**Pass:**
- every click changes the lists and the check in well under a second;
- the clean-up in test 4 works (the action with `REGEXP_REPLACE` fires on the same click as the toggle);
- a parameter action takes an aggregated source field (`Function Pick`, `Dept Pick`);
- test 7's lock holds.

**Fallback:** if `REGEXP_REPLACE` or the two-actions-on-one-click fails, `Function DeptOff Pick` becomes `""` (a function change clears every department exclusion). If an aggregated field cannot drive a parameter action, the lock and dim become visual only, and the check sheet says "nothing to show" instead of a blank view.

## S2. Region > Country > Office

The same pattern one level deeper. Every key carries its parents, so un-ticking a region strips its countries and its offices, and un-ticking a country strips its offices.

```
// Region Dim       SUM(IF [Dept In] THEN [Activity] END) = 0
// Region Toggle    as Function Toggle, with p_Regions and [region]
// Region Pick      IF [Region Dim] THEN [p_Regions] ELSE MIN([Region Toggle]) END
// CountryOff Without Region   (row-level)
IF REGEXP_REPLACE([p_CountryOff], "\|" + [region] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_CountryOff], "\|" + [region] + ">[^|]*", "") END
// OfficeOff Without Region    the same on p_OfficeOff (an office key starts with its region)
// Region CountryOff Pick      IF [Region Dim] THEN [p_CountryOff] ELSE MIN([CountryOff Without Region]) END
// Region OfficeOff Pick       IF [Region Dim] THEN [p_OfficeOff] ELSE MIN([OfficeOff Without Region]) END
// Region Tick      as Function Tick, with p_Regions, [Region In], [Region Dim]

// Country Visible  [Region In]
// Country Scope    SUM(IF [Dept In] AND [Office In] THEN [Activity] END)
// Country Locked   MIN([Country In]) AND ZN([Scope Total]) - ZN([Country Scope]) = 0
// Country Dim      SUM(IF [Dept In] THEN [Activity] END) = 0
// Country Toggle   as Dept Toggle, with p_CountryOff and [Country Key]
// Country Pick     IF [Country Locked] OR [Country Dim] THEN [p_CountryOff] ELSE MIN([Country Toggle]) END
// OfficeOff Without Country   (row-level: an office key is Region>Country>Office)
IF REGEXP_REPLACE([p_OfficeOff], "\|" + [Country Key] + ">[^|]*", "") = "|" THEN ""
ELSE REGEXP_REPLACE([p_OfficeOff], "\|" + [Country Key] + ">[^|]*", "") END
// Country OfficeOff Pick  IF [Country Locked] OR [Country Dim] THEN [p_OfficeOff] ELSE MIN([OfficeOff Without Country]) END
// Country Tick     as Dept Tick, with Country In / Locked / Dim

// Office Visible   [Country In]
// Office Scope, Office Locked, Office Dim, Office Toggle, Office Pick, Office Tick: as the department ones,
//                  with p_OfficeOff, [Office Key], [Office In]
```

**Sheets.**
- `S2 Regions`: Rows `region`.
- `S2 Countries`: Rows `region`, `country_name`; filter `Country Visible` = True.
- `S2 Offices`: Rows `country_name`, `office_name`; filter `Office Visible` = True.

All three: filter `row_type` = Quarter; shapes, colours and Detail as in S1.

**Actions:**

| Name | Source sheet | Target parameter | Source field |
|---|---|---|---|
| Toggle region | S2 Regions | `p_Regions` | `Region Pick` |
| Region cleans countries | S2 Regions | `p_CountryOff` | `Region CountryOff Pick` |
| Region cleans offices | S2 Regions | `p_OfficeOff` | `Region OfficeOff Pick` |
| Toggle country | S2 Countries | `p_CountryOff` | `Country Pick` |
| Country cleans offices | S2 Countries | `p_OfficeOff` | `Country OfficeOff Pick` |
| Toggle office | S2 Offices | `p_OfficeOff` | `Office Pick` |

Plus the three deselects. Put S1's lists on this dashboard too.

**Tests:**

| # | Do | Expect |
|---:|---|---|
| 1 | Click Asia Pacific | 6 countries listed and ticked; 9 offices; FY fills **2,025**, waiting **280** |
| 2 | Untick the office Pune | `p_OfficeOff` = `\|Asia Pacific>India>Pune\|`; FY fills **1,825**, waiting **246** |
| 3 | Click Asia Pacific off | `p_OfficeOff` empty again (the region's offices were cleaned) |
| 4 | Click the function Finance (S1 list), then Europe | Portugal and its office Lisbon show **dim**: Finance has nothing there. Clicking Portugal changes nothing |
| 5 | Function Legal & Compliance, region Latin America | FY fills **7**, waiting **2** |

**Pass and fallback:** as S1.

## S3. The likely range across draws

```
// Draw Fills        IF [row_type] = "Draw" AND [In Scope] THEN [filled] END
// Draw Vacant End   IF [row_type] = "Draw" AND [In Scope] AND [quarter_offset] = 4 THEN [vacant_end] END
// Fills P10         PERCENTILE({ INCLUDE [draw] : SUM([Draw Fills]) }, 0.1)
// Fills P50         PERCENTILE({ INCLUDE [draw] : SUM([Draw Fills]) }, 0.5)
// Fills P90         PERCENTILE({ INCLUDE [draw] : SUM([Draw Fills]) }, 0.9)
// Vacant P10 / P50 / P90   the same with [Draw Vacant End]
```

`quarter_offset = 4` is the forward year's last quarter, whatever the year. `INCLUDE [draw]` sums each simulated future over the selection; the percentile is then taken across the 100 futures.

**Sheets.**
- `S3 Year`: Text marks with the six measures.
- `S3 Quarters`: `quarter_label` on Columns; filter `row_type` = Draw; Measure Values `Fills P10`, `Fills P50`, `Fills P90`.

Put both on the S2 dashboard so the lists drive them.

**Expected** (FY27 fills and vacant on Jun 30, 2027, P10 · P50 · P90):

| Selection | FY27 fills | Vacant at year end |
|---|---|---|
| Nothing chosen | 6,300.7 · 6,838.5 · 7,542.9 | 696.1 · 772.0 · 891.5 |
| Technology | 2,264.7 · 2,494.0 · 2,766.2 | 278.8 · 318.5 · 366.0 |
| People without Talent Acquisition | 159.9 · 179.0 · 203.1 | 14.9 · 20.0 · 28.1 |
| Asia Pacific | 1,875.9 · 2,033.0 · 2,250.0 | 202.8 · 229.0 · 263.1 |
| Asia Pacific without Pune | 1,716.0 · 1,846.5 · 2,024.7 | 181.9 · 211.0 · 240.3 |

Tableau's `PERCENTILE` interpolates the way these were computed, so the decimals should match. If they differ by a step, send the numbers.

**Pass:** the numbers match, and a list click redraws the range in about a second (Desktop) and a few seconds at most on the web (S5).

**Fallback:** `draw` on Detail of a hidden sheet and `WINDOW_PERCENTILE(SUM([Draw Fills]), 0.1)` computed along `draw`.

## S4. The survival curve

```
// Recent Cohort     [row_type] = "Survival" AND [quarter_offset] >= -3      (approved in the last four quarters)
// SV At Risk        SUM(IF [Recent Cohort] AND [In Scope] THEN [at_risk] END)
// SV Filled         SUM(IF [Recent Cohort] AND [In Scope] THEN [sv_filled] END)
// SV Hazard         ZN([SV Filled]) / [SV At Risk]
// SV Still Vacant   EXP(RUNNING_SUM(LN(MAX(1 - [SV Hazard], 0.0001))))
// SV Filled Share   1 - [SV Still Vacant]
```

**Sheet `S4 Curve`:**
- Filter `row_type` = Survival.
- Columns `days_to` (Dimension, Continuous).
- Rows `SV Filled Share`, a table calculation: Edit Table Calculation > Specific Dimensions, `days_to` only.
- Marks Line.
- Then add `level_band` to Color (`days_to` stays the only Specific Dimension, so each band gets its own curve).

Read the value at `days_to` 29, 59 and 89 (filled within 30, 60 and 90 days).

**Expected (all bands together, then by band):**

| Selection | 30 days | 60 days | 90 days |
|---|---:|---:|---:|
| Nothing chosen | 24.1% | 73.8% | 92.1% |
| Technology | 19.1% | 68.1% | 89.9% |
| People without Talent Acquisition | 25.9% | 76.2% | 96.5% |
| Asia Pacific without Pune | 22.7% | 72.0% | 91.5% |
| L1–L2 (nothing chosen) | 38.1% | 87.7% | 97.4% |
| L3–L4 | 21.7% | 74.6% | 94.0% |
| L5–L6 | 10.6% | 54.3% | 81.9% |
| L7+ | 0.0% | 27.3% | 54.5% |

**Pass:** the curve matches, follows every list click, and stays a smooth staircase under a small selection (Legal & Compliance in Latin America has very few requisitions; the curve may step, but it must draw).

**Fallback:** the curve per level band computed in SQL and filtered by function only.

## S5. On Tableau Public

1. Hide `S Check`'s parameter strings if you like.
2. Server > Tableau Public > **Save to Tableau Public As** `D5 Spikes`, as an extract.
3. Open it on the web in a private window and repeat:
   - S1 tests 2 to 4;
   - S2 tests 1 and 2;
   - one S3 and one S4 reading.

**Pass:**
- it publishes (543,000 rows; the CSVs behind it are about 20 MB);
- a list click updates in about 2 seconds or less;
- the page opens in under 5 seconds.

**Fallback:** 50 draws instead of 100 (`DRAWS` in `forecast/settings.py`), halving the Draw rows.

## Send back

| Spike | Pass / fail | One line of what you saw |
|---|---|---|
| S1 | | clean-up on the same click? aggregated pick field accepted? lock? |
| S2 | | two-level clean-up? dim on Portugal? |
| S3 | | numbers match? speed? |
| S4 | | curve values match? small selections draw? |
| S5 | | published? click and load seconds (cold, warm) |

A screenshot of the S2 dashboard with Asia Pacific chosen and Pune unticked helps most. I record the results in the plan and choose the fallbacks.
