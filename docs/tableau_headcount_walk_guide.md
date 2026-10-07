# Building the Headcount & FTE Walk Dashboard in Tableau Public

This guide builds the second dashboard, from [`mart_headcount_fte_walk`](../data/marts/mart_headcount_fte_walk.csv) and its five small dimension files. Plan on about two hours. Every step lists what you should see, so you can check as you go.

The finished workbook has four dashboards, one per audience:

| Dashboard | Reader | Answers |
|---|---|---|
| 1. Executive Summary | CHRO, CFO | How much did the workforce grow, and from what? |
| 2. Movement Drivers | HR business partners | Where are hires, leavers and internal moves concentrated? |
| 3. Diagnostics | Analysts | Which slices moved, and does every line reconcile? |
| 4. Methodology | Anyone | How the numbers are defined, and their limits |

![Static preview](images/headcount_walk_preview.png)

---

## 1. Download the data

From the repository, open each file below and click **Download raw file** (the arrow at the top right). Save all six in one folder, for example `Documents/Tableau Public/arcadia-headcount/`.

| File | Rows | What it is |
|---|---|---|
| [`mart_headcount_fte_walk.csv`](../data/marts/mart_headcount_fte_walk.csv) | 292,696 | The walk (fact table), codes only, about 15 MB |
| [`mart_dim_month.csv`](../data/marts/mart_dim_month.csv) | 48 | Month-ends with fiscal year, quarter, period |
| [`mart_dim_department.csv`](../data/marts/mart_dim_department.csv) | 32 | Department, sub-function, function, cost center |
| [`mart_dim_country.csv`](../data/marts/mart_dim_country.csv) | 15 | Country and region |
| [`mart_dim_job_family.csv`](../data/marts/mart_dim_job_family.csv) | 14 | Job family names |
| [`mart_dim_grade.csv`](../data/marts/mart_dim_grade.csv) | 9 | Grade level and career track |

Why six files and not one: names repeated on 292,696 rows would make a single file almost four times larger (57 MB). A star schema keeps the export small, and Tableau's relationships put it back together.

## 2. Connect and relate the tables

1. Open **Tableau Public**. **Connect → To a File → Text file** → `mart_headcount_fte_walk.csv`.
2. From the left panel, drag each `mart_dim_*` file onto the canvas next to the walk table. Tableau draws a "noodle" (a relationship) to the walk table each time.
3. Click each noodle and check the matching field. Tableau usually finds it on its own, because the column names match:

| Dimension file | Related on |
|---|---|
| `mart_dim_month` | `month_end_date` = `month_end_date` |
| `mart_dim_department` | `department_id` = `department_id` |
| `mart_dim_country` | `country_code` = `country_code` |
| `mart_dim_job_family` | `job_family_code` = `job_family_code` |
| `mart_dim_grade` | `grade` = `grade` |

4. In the data grid, set types by clicking the icon above each column:
   - `month_end_date` and `prior_month_end_date`: **Date**
   - `grade`: **String** in both the walk and the grade file (it's a label, not a number to sum)
   - `fiscal_year`: **String**
   - `headcount`: **Number (whole)**, `fte`: **Number (decimal)**

**Check:** on a new sheet, drag `Movement Category` to Rows and `SUM(Headcount)` to Text. Opening and Closing are large positive numbers (each month's levels added up), the four movement categories are signed, and FTE Changes shows 0 headcount.

Relationships, not joins, are the right choice here: each dimension is one row per key, and Tableau only queries the tables a sheet actually uses.

## 3. Parameters

Create four parameters (right-click the Data pane → **Create Parameter**):

| Name | Type | Values | Default |
|---|---|---|---|
| **Start Month** | Date | List, **Add values from** `month_end_date` | 2025-07-31 |
| **End Month** | Date | List, **Add values from** `month_end_date` | 2026-06-30 |
| **Measure** | String | List: `Headcount`, `FTE` | Headcount |
| **Show Methodology** | Boolean | True / False | False |

Show the first three as controls on every dashboard (right-click → **Show Parameter**).

## 4. Calculated fields

Create these in order; later ones use earlier ones. Field names in brackets must match yours exactly.

### Core
```
// Selected Value
IF [Measure] = "Headcount" THEN [Headcount] ELSE [Fte] END
```
```
// In Range
[Month End Date] >= [Start Month] AND [Month End Date] <= [End Month]
```
```
// Walk Value
// Opening comes from the first month, Closing from the last, and every
// movement is summed across the months in between. This works because the
// SQL guarantees each month's Closing equals the next month's Opening (test 14).
IF [In Range] THEN
    CASE [Movement Category]
        WHEN "Opening" THEN IIF([Month End Date] = [Start Month], [Selected Value], 0)
        WHEN "Closing" THEN IIF([Month End Date] = [End Month],   [Selected Value], 0)
        ELSE [Selected Value]
    END
END
```

### KPIs
```
// Opening
SUM(IF [In Range] AND [Movement Category] = "Opening" AND [Month End Date] = [Start Month]
    THEN [Selected Value] END)
```
```
// Closing
SUM(IF [In Range] AND [Movement Category] = "Closing" AND [Month End Date] = [End Month]
    THEN [Selected Value] END)
```
```
// Net Change %
([Closing] - [Opening]) / [Opening]
```
```
// Months in Range
COUNTD(IF [In Range] THEN [Month End Date] END)
```
```
// Average Headcount
// Each month's average is (opening + closing) / 2; this averages those across the range.
SUM(IF [In Range] AND ([Movement Category] = "Opening" OR [Movement Category] = "Closing")
    THEN [Headcount] END) / 2 / [Months in Range]
```
```
// Hires
SUM(IF [In Range] AND [Movement Category] = "Hires" THEN [Headcount] END)
```
```
// Voluntary Leavers
-SUM(IF [In Range] AND [Movement Category] = "Voluntary Terminations" THEN [Headcount] END)
```
```
// Involuntary Leavers
-SUM(IF [In Range] AND [Movement Category] = "Involuntary Terminations" THEN [Headcount] END)
```
```
// Voluntary Turnover (annualized)
ZN([Voluntary Leavers]) / [Average Headcount] * 12 / [Months in Range]
```
```
// Involuntary Turnover (annualized)
ZN([Involuntary Leavers]) / [Average Headcount] * 12 / [Months in Range]
```
```
// Hire Rate (annualized)
ZN([Hires]) / [Average Headcount] * 12 / [Months in Range]
```
```
// Internal Moves
SUM(IF [In Range] AND [Movement Category] = "Internal Moves In" THEN [Headcount] END)
```

Format the three rate fields as **Percentage, 1 decimal**.

### Control (shown on the Diagnostics dashboard)
```
// Walk Gap
// Opening + every movement - Closing. Must be 0 for any slice and any range.
SUM([Walk Value]) - 2 * [Closing]
```
`SUM([Walk Value])` already includes Closing once, so subtracting twice leaves Opening + movements − Closing.

### Small-group rule
```
// Rate Shown
// Rates on fewer than 20 people swing wildly; hide them rather than mislead.
IF [Average Headcount] < 20 THEN NULL ELSE [Voluntary Turnover (annualized)] END
```

### Set for comparisons
Right-click `Department Name` → **Create → Set** → name it **Selected Departments**, pick any one department. Then:
```
// Selected vs Rest
IF [Selected Departments] THEN "Selected" ELSE "Rest of company" END
```

**Check against these FY26 values** (Start Month 2025-07-31, End Month 2026-06-30, Measure Headcount):

| Field | Expected |
|---|---|
| Opening | 12,510 |
| Hires | 2,354 |
| Voluntary Leavers | 1,341 |
| Involuntary Leavers | 322 |
| Internal Moves | 1,615 (1,038 promotions, 577 transfers) |
| Closing | 13,201 |
| Net Change % | 5.5% |
| Voluntary Turnover (annualized) | 10.4% |
| Walk Gap | 0 |

With Measure = FTE: Opening 12,281.7, Closing 12,940.0, FTE Changes −34.1.

If a number is off, the usual cause is a type (Step 2.4) or a filter left on a sheet.

## 5. Sheets

### Executive Summary
1. **KPI band.** One sheet per KPI (Closing, Net Change %, Hires, Voluntary Turnover, Internal Moves): put the field on **Text**, mark type **Text**, size the font large, and add a smaller line underneath with the comparison (for example `Opening` in the tooltip-style caption).
2. **Headcount waterfall.** This is the main exhibit.
   - Columns: `Movement Category`. Sort it by `Movement Order` (right-click → Sort → Field → Movement Order, Minimum, Ascending).
   - Filter out `Closing`.
   - Rows: `SUM([Walk Value])` → right-click → **Quick Table Calculation → Running Total**.
   - Mark type **Gantt Bar**. Create `-SUM([Walk Value])` and drag it to **Size**.
   - **Analysis → Totals → Show Row Grand Totals**, and rename the total *Closing*.
   - Color: create `SUM([Walk Value]) > 0` and drag it to Color; blue for increases, red for decreases, gray for the Opening and total bars.
   - **Check:** the grand total equals the `Closing` KPI.
   - At company level Internal Moves In and Out cancel (+1,615 and −1,615). Hide them with a filter on this sheet if you prefer a cleaner company view; they matter on department views.
3. **Headcount trend.** Columns: `Month End Date` (continuous month). Rows: `SUM(IF [Movement Category] = "Closing" THEN [Selected Value] END)`. Don't filter this to the range: show all history, and add a **reference band** from `Start Month` to `End Month` so the selected period stands out.

### Movement Drivers
4. **Turnover by function.** Rows: `Function Name`. Columns: `Voluntary Turnover (annualized)` and `Involuntary Turnover (annualized)` as a stacked bar (Measure Names on Color). Sort descending. Label the bar ends.
5. **Net change heatmap.** Rows: `Function Name`, Columns: `Fiscal Period`, Color: `SUM(IF [Movement Category] <> "Opening" AND [Movement Category] <> "Closing" THEN [Selected Value] END)`, diverging blue–red palette centered at 0. This shows where growth and shrinkage happened month by month.
6. **Internal moves by reason.** Rows: `Movement Reason`, filtered to `Internal Moves In`, bars by `Grade Level`. Promotions show as a move out of one grade and into the next, so a grade-level view of the walk explains career progression without any extra logic.

### Diagnostics
7. **Slice table.** Rows: `Function Name` → `Department Name` → `Country Name` → `Grade` (build a hierarchy: drag Department onto Function, and so on, so readers can drill with the + icons). Columns: `Measure Names` with Opening, Hires, Voluntary Leavers, Involuntary Leavers, Internal Moves, Closing, Walk Gap.
8. **Control tile.** A single Text sheet with `Walk Gap` and the caption "Opening + movements − Closing for every slice in view. 0 means the walk reconciles." This makes data quality visible instead of assumed.

## 6. Dashboards and actions

Use a fixed size of **1200 × 900** for each dashboard.

1. **Executive Summary**: title, KPI band across the top, waterfall (left two-thirds), trend (right third). Parameter controls in one row above the charts.
2. **Movement Drivers**: turnover by function (left), heatmap (right), internal moves (bottom).
3. **Diagnostics**: control tile top right, slice table filling the rest.
4. **Methodology**: a text object with the definitions from Section 7.

Actions (**Dashboard → Actions**):

- **Filter action:** on Movement Drivers, clicking a function in the turnover chart filters the heatmap and internal moves to that function. Clearing the selection shows all values.
- **Set action:** on Movement Drivers, selecting departments in the heatmap updates **Selected Departments**; add `Selected vs Rest` to the color of the turnover chart so a selection is compared against the rest of the company.
- **Parameter action:** make a small sheet listing `Headcount` and `FTE` (a calculated field `"Headcount"` and one `"FTE"`, or a two-row text sheet), and add a parameter action that sets **Measure** on click. Readers switch measures by clicking, not through a dropdown.
- **Dynamic zone visibility:** on the Executive Summary, add a container holding a short methodology note, and under **Layout → Control visibility using value** pick `Show Methodology`. A button sheet with a parameter action toggles it.
- **Navigation:** add **Navigation** buttons along the top of each dashboard so all four read as one product.

Tooltips: on the waterfall, use viz-in-tooltip to show the 12-month trend of the hovered category (**Insert → Sheets** in the tooltip editor).

## 7. Methodology text (paste into dashboard 4)

> **What this shows.** A monthly headcount and FTE walk for Arcadia Systems, a fictional company with synthetic data. For any slice (department, country, job family, grade) and any range of months: Opening + Hires − Terminations ± Internal Moves ± FTE Changes = Closing.
>
> **Definitions.** Headcount counts every worker active on the month-end, executive officers included; a part-time worker counts as one. FTE weights each worker by their scheduled fraction. A termination date is the last day worked. Internal moves are changes of department, country, job family or grade between two month-ends; when several change at once, one reason is recorded (department, then country, then grade, then job family). Movers are counted at their prior FTE; a same-month FTE change shows separately. Turnover rates are annualized: leavers ÷ average headcount × 12 ÷ months in range.
>
> **Controls.** Eighteen automated tests run on every build. Among them: every slice reconciles each month; each month's closing equals the next month's opening; opening and closing match an independent count of the month-end snapshot; internal moves net to zero company-wide; hires and leavers match the worker master's dates.
>
> **Limits.** Someone hired and terminated within one month never appears at a month-end, so a month-end walk can't show them (none occur in this dataset; the model counts them separately). Location changes within the same country don't change a slice, so they aren't moves at this grain.

## 8. Publish

1. **File → Save to Tableau Public As…** and name it **Arcadia Headcount & FTE Walk**.
2. When it opens in the browser, click **Edit Details** and paste a one-paragraph description plus the GitHub link: `https://github.com/thialp/people-analytics-warehouse`.
3. Under the workbook's settings, allow **Download** of the workbook so reviewers can open your calculated fields.
4. Copy the workbook URL and add it to the README (the "Dashboard" row and Section 9), or send it to me to update.

**Before you publish, check:** Walk Gap shows 0, the FY26 numbers in Section 4 match, and no sheet still carries a test filter.
