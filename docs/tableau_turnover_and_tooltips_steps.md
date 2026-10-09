# Headcount & FTE Walk: turnover by function, and the tooltips put together

Two jobs to finish the Executive Summary dashboard: the last worksheet (bottom right), and the waterfall tooltip, whose `TT …` fields exist but are not wired to the sheet yet.

## Part A. Turnover by function (bottom-right card: x 848, y 500, 496 × 312)

FY26 should show Commercial on top at 16.1% (13.0% voluntary + 3.1% involuntary), then Operations 12.6%, Corporate 12.5%, Product 12.0%, Technology 11.6%, Marketing 11.2%. Executive is hidden: only about 12 people, below the 20-person rule.

### A1. Fields

These reuse `Average Headcount`, `Voluntary Turnover (annualized)` and `Involuntary Turnover (annualized)` from the walk guide.
```
// Vol Rate Shown   (groups under 20 people are hidden, not shown as a wild rate)
IF [Average Headcount] < 20 THEN NULL ELSE [Voluntary Turnover (annualized)] END
```
```
// Invol Rate Shown
IF [Average Headcount] < 20 THEN NULL ELSE [Involuntary Turnover (annualized)] END
```
```
// Total Rate Shown
IF [Average Headcount] < 20 THEN NULL
ELSE [Voluntary Turnover (annualized)] + [Involuntary Turnover (annualized)] END
```
Format all three: Default Properties → Number Format → **Percentage, 1 decimal**.

For the title (the top function's name, taken from the first row of the sorted chart):
```
// TO Top Function   (table calculation: Compute Using Function Name)
LOOKUP(ATTR([Function Name]), FIRST())
```
```
// TO Title
IF ISNULL([TO Top Function]) THEN "Turnover by function"
ELSE [TO Top Function] + " has the highest turnover in " + [WF Period] END
```

### A2. Build the sheet `Turnover by Function`

1. **Rows:** `Function Name`.
2. **Columns:** drag `Vol Rate Shown` and `Invol Rate Shown` so they share one axis: drop the second on the first's axis (a double-bar cursor), which creates `Measure Values` with **Measure Names** on Color. Then **Filters**: `Measure Names` → keep only `Vol Rate Shown` and `Invol Rate Shown`.
   **Important:** Tableau also puts a second `Measure Names` pill on **Rows**, next to `Function Name`. Drag that pill off Rows (the Color one stays). If it stays, every function is split into one row per measure and the bars sit on top of each other. Without it, each function is one row and voluntary + involuntary sit end to end in the same bar (Analysis → Stack Marks → Automatic), so the bar length is the total.
3. **Marks (Measure Values layer):** type **Bar**. Color: Edit Colors → `Vol Rate Shown` coral `#E4572E`, `Invol Rate Shown` dark coral `#B8401F`. Size: slide to about two-thirds so the bars have gaps.
4. **Remove Executive:** drag `Total Rate Shown` to **Filters** → Special → **Non-null values**. (Do not drag it to the Marks card yet.)
5. **Sort:** right-click `Function Name` on Rows → Sort → By **Field**, descending, Field: `Total Rate Shown`, aggregation Sum.
6. **Total label at the end of each bar (the "hidden bar").** Drag `Total Rate Shown` to **Columns**, to the right of the existing pill (it becomes its own pill, not part of Measure Values). Right-click it → **Dual Axis**. Right-click the top axis → **Synchronize Axis**, then untick **Show Header** on it. On the Marks card for `AGG(Total Rate Shown)`:
   - Mark type **Text**. A text mark draws no bar at all, so nothing needs hiding, and it sits at x = total, which is exactly the end of the stacked bar.
   - If `Measure Names` is on this card's Color, drag it off, so the Total does not show in the legend.
   - Drag `Total Rate Shown` to **Label**: percentage, Tableau Semibold 9 pt navy `#13233A`. Label → Alignment → Horizontal **Right** (the text starts just past the bar end; if it lands on the wrong side, choose Left). If the label touches the bar, type two spaces before the field in Label → Text.
7. **Title:** drag `TO Title` to **Detail**; Worksheet → Show Title, double-click the title, Insert `TO Title` (Tableau Bold 12 pt navy). Add a second line: **Voluntary** (coral `#E4572E`, Tableau Semibold 9 pt) ` + ` **Involuntary** (dark coral `#B8401F`) ` leavers ÷ average headcount, annualized · groups under 20 people hidden` (slate `#5A6170`, Tableau Book 9 pt). Color each word by selecting it in the title editor.
8. **Clean look:** hide the bottom axis (right-click → untick Show Header), Format → Lines: grid, zero line, row/column dividers **None**. Function labels: Tableau Book 9 pt navy; the header of `Function Name` hidden ("Function Name" title off). Shading: Worksheet and Pane `#FBFBF8`.
9. **Tooltip** (Marks → Tooltip; untick *Include command buttons*). Put `Function Name`, `Total Rate Shown`, `Vol Rate Shown`, `Invol Rate Shown`, `Voluntary Leavers`, `Involuntary Leavers` and `Average Headcount` on **Detail** so they can be inserted, then:

   - Line 1 (Tableau Semibold 12, navy): `<Function Name>`
   - Line 2 (Tableau Semibold 16, navy): `<AGG(Total Rate Shown)>` then ` annualized turnover` (Tableau Book 9 pt, slate)
   - Line 3 (Tableau Book 9, slate): `Voluntary <AGG(Vol Rate Shown)> · <AGG(Voluntary Leavers)> leavers`
   - Line 4 (Tableau Book 9, slate): `Involuntary <AGG(Invol Rate Shown)> · <AGG(Involuntary Leavers)> leavers`
   - Line 5 (Tableau Book 9, slate): `Average headcount <AGG(Average Headcount)>`

   Set `Voluntary Leavers`, `Involuntary Leavers` and `Average Headcount` to Number (Custom) `#,##0`.

### A3. Place it

Drag **Turnover by Function** onto the dashboard, Floating: x **848**, y **500**, w **496**, h **312**. Background `#FBFBF8`, Border 1 px `#E4E3DD`, Corner Radius **10**.

### A4. Check (From Jul 2025 To Jun 2026)

| Check | Expected |
|---|---|
| Title | Commercial has the highest turnover in FY26 |
| Order and labels | Commercial 16.1%, Operations 12.6%, Corporate 12.5%, Product 12.0%, Technology 11.6%, Marketing 11.2% |
| Executive | Not shown (under 20 people) |
| Commercial tooltip | 16.1% · Voluntary 13.0% · 399 leavers · Involuntary 3.1% · 95 leavers · Average headcount 3,063 |
| Measure toggle | No change: turnover rates are headcount-based on purpose |

## Part B. Waterfall tooltip, assembled

You already created the `TT …` fields (from `tableau_tooltip_and_fte_steps.md` and `tableau_measure_alignment_steps.md`). They do nothing until they are on the sheet and in the tooltip text.

### B1. Field checklist (make sure each exists, using the latest versions)

| Field | Type | Note |
|---|---|---|
| `TT Unit`, `TT Noun` | text, constant | "workers"/"headcount" or "FTE" |
| `TT Open Ref`, `TT Close Ref` | number, from FIXED | the opening and closing level in the selected measure |
| `TT Months` | FIXED | months in range |
| `TT Open Month`, `TT Close Month` | text | "Jun 2025", "Jun 2026" |
| `TT Share Str`, `TT Net Str` | text | **the MAX() versions** from the fix |
| `TT Context` | text | one line per bar |
| `TT Level HC`, `TT Level FTE`, `TT Level PT` | aggregate | level rows at start/end month |
| `TT Bar T`, `TT Bar HC` | aggregate | this bar's FTE (tenths) and headcount |
| `TT Part Time` | text | the **replacement** version from the alignment guide (people-to-FTE bridge on movement bars) |

If a field shows a red squiggle, it is usually a missing `STR(...)` or a non-aggregate beside an aggregate: wrap fixed values in `MAX(...)`.

### B2. Put them on the Waterfall sheet

On the **Waterfall** sheet, drag these onto **Detail** on the Marks card: `TT Unit`, `TT Context`, `TT Part Time`, and **`Walk Value`** (it appears as `SUM(Walk Value)`; you need it on the sheet so it can be inserted into the tooltip). They add no extra marks because each has one value per bar.

Set the number format of `Walk Value`: Default Properties → Number Format → Custom `#,##0;−#,##0`.

### B3. Tooltip text

Marks → **Tooltip**. Untick *Include command buttons*; keep *Show tooltips instantly*. Build four lines with **Insert**:

- Line 1 (Tableau Semibold 12, navy `#13233A`): `<Movement Category>` (the aliases show: "Voluntary leavers", "Involuntary leavers")
- Line 2 (Tableau Semibold 16, navy): `<SUM(Walk Value)> <TT Unit>`
- Line 3 (Tableau Book 9, slate `#5A6170`): `<AGG(TT Context)>`
- Line 4 (Tableau Book 9, slate): `<AGG(TT Part Time)>`

### B4. Check (FY26)

| Bar (Headcount) | Line 2 | Line 3 | Line 4 |
|---|---|---|---|
| Opening | 12,510 workers | Active at the end of Jun 2025 | 807 part-time (6.5%) · FTE is 228.3 below headcount |
| Hires | 2,354 workers | 18.8% of opening headcount · about 196 per month | 2,354 people = 2,328.3 FTE (part-timers count as a fraction) |
| Voluntary leavers | −1,341 workers | 10.7% of opening headcount · about 112 per month | 1,341 people = 1,318.5 FTE |
| Involuntary leavers | −322 workers | 2.6% of opening headcount · about 27 per month | 322 people = 317.4 FTE |
| Closing | 13,201 workers | Active at the end of Jun 2026 · +5.5% vs opening | 924 part-time (7.0%) · FTE is 261.0 below headcount |

Toggle to FTE: units read "FTE", the FTE Changes bar says "Schedule changes for workers who stayed. Headcount does not move." and has no fourth line.

## Part C. Before you publish to Tableau Public

1. **Dashboard size:** Fixed, 1400 × 850 (Dashboard tab → Size).
2. **Data:** connect to the six CSVs (the new walk file with `part_time_headcount`), as in the walk guide; Tableau Public needs the data extracted, which it does on upload.
3. **Hidden sheets:** right-click each tab → Hide Sheet for the helper sheets (CheckList, Measure Toggle, Waterfall Caption, KPI cards, Trend, Turnover by Function) so only the dashboard shows. They keep working.
4. **Custom shapes** are saved inside the workbook, so the Headcount | FTE capsule works for viewers. Open the info panel once and close it so the dashboard opens clean.
5. **Check every control on the saved version:** Start/End dropdowns, Headcount | FTE, the info button, and the three tooltips (waterfall, trend, turnover).
6. **Title and description on Tableau Public:** "Headcount & FTE Walk · Arcadia Systems (fictional company, synthetic data)". Send me the link and I will update the README and the resume.
