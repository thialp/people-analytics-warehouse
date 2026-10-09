# Headcount & FTE Walk: part-time on the FTE card, waterfall tooltip, plain dropdowns

Three jobs. Do them in this order, because the tooltip and the card both need the new column from Section 1.

## 1. Load the new data column (part-time workers)

Why: FTE is a decimal because a part-time worker counts as 1 in headcount but as 0.8 or 0.5 in FTE. To make that visible we need to know **how many** part-time workers there are, and the walk file had no such count. It now has one new column, `part_time_headcount`: workers under 1.0 FTE, filled on **Opening and Closing rows only** (every movement row is 0, because a move or an FTE change can flip a worker between full- and part-time, so a signed count of that would not mean anything on its own). A new test (23) ties it back to the worker-level table, month by month.

1. Download the new [`mart_headcount_fte_walk.csv`](../data/marts/mart_headcount_fte_walk.csv) (Download raw file) and replace your local copy of the same name in the same folder. The row count is still 292,696; only the last column is new.
2. In Tableau: **Data → (your data source) → Refresh Data Source** (or F5 on the Data Source tab). `Part Time Headcount` appears in the Data pane as a measure. Confirm it is a whole **Number (whole)**, and Default aggregation **Sum**.
3. Check: build `SUM(Part Time Headcount)` filtered to Closing, month 2026-06-30. Expected **924**. For 2025-07-31 Opening: **807**.

## 2. FTE card: decimal back, part-time count beside it

Replace three fields from the KPI cards guide and add four. Everything else on the card sheet stays as is.

```
// K Close PT
ZN(SUM(IF [In Range] AND [Movement Category] = "Closing" AND [Month End Date] = [End Month]
       THEN [Part Time Headcount] END))
```
```
// K FTE T   (FTE in tenths, so we can print one decimal with integer math)
INT(ROUND([K Close FTE] * 10, 0))
```
```
// K Gap T   (the part-time gap in tenths)
INT(ROUND([K Part Time Gap] * 10, 0))
```
```
// KPI 2 Value
IF NOT [K Valid] THEN "—" ELSE
  IF [K FTE T] >= 10000
  THEN STR(DIV([K FTE T], 10000)) + "," + RIGHT("00" + STR(DIV([K FTE T], 10) % 1000), 3)
  ELSE STR(DIV([K FTE T], 10)) END
  + "." + STR([K FTE T] % 10)
END
```
```
// KPI 2 Note
IF NOT [K Valid] THEN "" ELSE
  IF [K Close PT] >= 1000
  THEN STR(DIV(INT([K Close PT]), 1000)) + "," + RIGHT("00" + STR(INT([K Close PT]) % 1000), 3)
  ELSE STR(INT([K Close PT])) END
  + " part-time · " + STR(DIV([K Gap T], 10)) + "." + STR([K Gap T] % 10) + " below headcount"
END
```

(`K Part Time Gap` already exists: headcount minus FTE.) No change to the layers: `KPI 2 Value` and `KPI 2 Note` are already on the Label shelves.

Expected, FY26: **12,940.0** and **924 part-time · 261.0 below headcount**. The first line says the FTE total; the second says why it is lower than the 13,201 on the card next to it.

If the note runs past the card edge, use the short form `924 part-time · −261.0` (replace the last line of the note with `+ " part-time · −" + STR(DIV([K Gap T], 10)) + "." + STR([K Gap T] % 10)`).

**Caption under the waterfall: keep it in whole numbers.** The bars, the title and the caption all show FTE as whole numbers (12,282 + 2,328 − 1,319 − 317 − 34 = 12,940), so the waterfall card ties at a glance. The one-decimal figures live on the Closing FTE card and in the tooltip, where the part-time count explains them. The whole-number `WF FTE Open Str`, `WF FTE Close Str` and `WF FTE Chg Str` are in `tableau_final_polish_before_publish.md`, item 3.

## 3. Waterfall tooltip (dynamic)

What it should do: hover any bar and get a small card that says what the bar is, its size in the measure currently selected (Headcount or FTE), how big that is relative to where the period started, and, on the Opening and Closing bars, how many part-time workers sit behind the FTE gap. Every line is a calculated field, so it follows the Start Month, End Month and Measure controls.

Hover design (what you are building):

```
Hires                                          <- category name (bold)
2,354 workers                                  <- value, in the selected measure
18.8% of opening headcount · about 196 per month
```
and on the level bars:
```
Closing
13,201 workers
Active at the end of Jun 2026 · +5.5% vs opening
924 part-time (7.0%) · FTE is 261.0 below headcount
```
In FTE mode the same bars say "FTE" instead of "workers" and "opening FTE" instead of "opening headcount".

### 3.1 Calculated fields

Reuse the fields you already have (`WF Open`, `WF Close`, `WF FTE Open`, `WF FTE Close`, `In Range`, `Walk Value`, `Start Month`, `End Month`, `Measure`). The waterfall's marks are split by Movement Category, so the company-level numbers use the existing FIXED fields, and the per-bar numbers use a plain aggregate on the bar's own rows.

```
// TT Unit
IF [Measure] = "Headcount" THEN "workers" ELSE "FTE" END
```
```
// TT Noun
IF [Measure] = "Headcount" THEN "headcount" ELSE "FTE" END
```
```
// TT Open Ref   (the opening level in the selected measure)
IF [Measure] = "Headcount" THEN [WF Open] ELSE [WF FTE Open] END
```
```
// TT Close Ref
IF [Measure] = "Headcount" THEN [WF Close] ELSE [WF FTE Close] END
```
```
// TT Months   (how many months are in the range)
{ FIXED : COUNTD(IF [In Range] THEN [Month End Date] END) }
```
```
// TT Open Month   (the month-end before the range starts, e.g. "Jun 2025")
LEFT(DATENAME('month', DATEADD('month', -1, [Start Month])), 3) + " " +
STR(YEAR(DATEADD('month', -1, [Start Month])))
```
```
// TT Close Month   (e.g. "Jun 2026")
LEFT(DATENAME('month', [End Month]), 3) + " " + STR(YEAR([End Month]))
```
```
// TT Share Str   (this bar as a share of the opening level, one decimal)
// MAX() turns the fixed opening level into an aggregate, so it can sit beside SUM([Walk Value])
IF MAX([TT Open Ref]) = 0 THEN "" ELSE
  STR(DIV(INT(ROUND(ABS(SUM([Walk Value])) / MAX([TT Open Ref]) * 1000, 0)), 10)) + "." +
  STR(INT(ROUND(ABS(SUM([Walk Value])) / MAX([TT Open Ref]) * 1000, 0)) % 10) + "%"
END
```
```
// TT Net Str   (closing vs opening, signed; MAX() keeps it an aggregate like the other branches of TT Context)
IF MAX([TT Open Ref]) = 0 THEN "" ELSE
  IF MAX([TT Close Ref]) >= MAX([TT Open Ref]) THEN "+" ELSE "−" END +
  STR(DIV(INT(ROUND(ABS(MAX([TT Close Ref]) - MAX([TT Open Ref])) / MAX([TT Open Ref]) * 1000, 0)), 10)) + "." +
  STR(INT(ROUND(ABS(MAX([TT Close Ref]) - MAX([TT Open Ref])) / MAX([TT Open Ref]) * 1000, 0)) % 10) + "%"
END
```
```
// TT Context   (one plain-English line per bar)
CASE ATTR([Movement Category])
WHEN "Opening" THEN "Active at the end of " + [TT Open Month]
WHEN "Closing" THEN "Active at the end of " + [TT Close Month] + " · " + [TT Net Str] + " vs opening"
WHEN "FTE Changes" THEN "Schedule changes for workers who stayed. Headcount does not move."
ELSE [TT Share Str] + " of opening " + [TT Noun] + " · about " +
     STR(INT(ROUND(ABS(SUM([Walk Value])) / MAX([TT Months]), 0))) + " per month"
END
```

Part-time line (levels only; the movement bars get a people-to-FTE bridge in [the alignment guide](tableau_measure_alignment_steps.md), which replaces `TT Part Time`). Two helpers read the bar's own level rows:
```
// TT Level HC
SUM(IF [In Range] AND (([Movement Category] = "Opening" AND [Month End Date] = [Start Month])
                    OR ([Movement Category] = "Closing" AND [Month End Date] = [End Month]))
    THEN [Headcount] END)
```
```
// TT Level FTE
SUM(IF [In Range] AND (([Movement Category] = "Opening" AND [Month End Date] = [Start Month])
                    OR ([Movement Category] = "Closing" AND [Month End Date] = [End Month]))
    THEN [Fte] END)
```
```
// TT Level PT
ZN(SUM(IF [In Range] AND (([Movement Category] = "Opening" AND [Month End Date] = [Start Month])
                       OR ([Movement Category] = "Closing" AND [Month End Date] = [End Month]))
       THEN [Part Time Headcount] END))
```
```
// TT Part Time
IF (ATTR([Movement Category]) = "Opening" OR ATTR([Movement Category]) = "Closing") AND [TT Level HC] > 0 THEN
  IF [TT Level PT] >= 1000
  THEN STR(DIV(INT([TT Level PT]), 1000)) + "," + RIGHT("00" + STR(INT([TT Level PT]) % 1000), 3)
  ELSE STR(INT([TT Level PT])) END
  + " part-time (" +
  STR(DIV(INT(ROUND([TT Level PT] / [TT Level HC] * 1000, 0)), 10)) + "." +
  STR(INT(ROUND([TT Level PT] / [TT Level HC] * 1000, 0)) % 10) + "%) · FTE is " +
  STR(DIV(INT(ROUND(([TT Level HC] - [TT Level FTE]) * 10, 0)), 10)) + "." +
  STR(INT(ROUND(([TT Level HC] - [TT Level FTE]) * 10, 0)) % 10) + " below headcount"
ELSE "" END
```
(An empty string shows as a blank line, so movement bars simply have no part-time line.)

Why the `MAX(...)`: `TT Open Ref` and `TT Close Ref` come from FIXED fields, which Tableau treats as non-aggregate, while `SUM([Walk Value])` is an aggregate. Tableau refuses to mix the two in one expression ("Cannot mix aggregate and non-aggregate arguments"). Wrapping the fixed value in `MAX()` is harmless (it is a single constant) and makes both sides aggregates.

### 3.2 Put it on the sheet

1. On the **Waterfall** sheet drag these onto **Detail** on the Marks card: `TT Unit`, `TT Context`, `TT Part Time` (all three; Tableau lists the aggregates as `AGG(...)`, and `TT Unit` as a dimension). They make no extra marks because they are constant per bar.
2. Click **Tooltip** on the Marks card. Untick **Include command buttons**. Leave **Responsive – show tooltips instantly** on. Paste this and insert each field with the **Insert** menu:

   - Line 1 (Tableau Semibold 12, navy `#13233A`): `<ATTR(Movement Category)>`
   - Line 2 (Tableau Semibold 16, navy): `<SUM(Walk Value)> <TT Unit>`
   - Line 3 (Tableau Book 9, slate `#5A6170`): `<AGG(TT Context)>`
   - Line 4 (Tableau Book 9, slate): `<AGG(TT Part Time)>`

   `ATTR(Movement Category)` shows the aliases you set ("Voluntary leavers", "Involuntary leavers").
3. Number format for the value on line 2: right-click `Walk Value` → **Default Properties → Number Format → Custom** → `#,##0;−#,##0`. Leavers then read "−1,341 workers", hires "2,354 workers".
4. Walk Value in FTE mode shows whole numbers here, like the bar labels. That is deliberate: the one-decimal FTE lives on the card and in the Closing tooltip's part-time line.

### 3.3 Check (FY26, Measure = Headcount)

| Bar | Line 2 | Line 3 | Line 4 |
|---|---|---|---|
| Opening | 12,510 workers | Active at the end of Jun 2025 | 807 part-time (6.5%) · FTE is 228.3 below headcount |
| Hires | 2,354 workers | 18.8% of opening headcount · about 196 per month | (blank) |
| Voluntary leavers | −1,341 workers | 10.7% of opening headcount · about 112 per month | (blank) |
| Involuntary leavers | −322 workers | 2.6% of opening headcount · about 27 per month | (blank) |
| Closing | 13,201 workers | Active at the end of Jun 2026 · +5.5% vs opening | 924 part-time (7.0%) · FTE is 261.0 below headcount |

Switch Measure to FTE: the units become "FTE", and the Opening/Closing bars show 12,282 and 12,940 with the same part-time line.

Known limits: the "of opening" and "per month" figures use the company-wide FIXED fields, so they ignore a department filter on the sheet (the same limit the title and caption already have). The "FTE is X below headcount" line uses the bar's own rows, so it does follow filters.

## 4. Dropdowns: back to plain squares

The rounded pill around the dropdown boxes fights the control's own square border, so go simple and consistent:

1. Select **Start Month** → Layout pane → Corner Radius **0** on all four corners; Background **#FFFFFF**; Outer padding 0; Inner padding 0. Same for **End Month**.
2. Size stays 146 × 32 at x 840 and x 996, y 22.
3. Keep the Headcount | FTE capsule and the info button rounded: they are drawn shapes, so they read as buttons, while the two dropdowns read as inputs. That contrast is intended.
4. Also in this pass: the Info Panel text was cut off at the last line. Make the panel taller (h **300** instead of 252) and keep the same x and y.

Then check the whole header at 100% zoom, not in the Layout view.
