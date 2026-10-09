# Connecting the Marts to Tableau Public

Tableau Public doesn't have a GitHub connector. It reads local files (CSV, Excel), Google Sheets, OData and web data connectors. The simplest path is to download the two CSVs from this repo and connect to them as text files.

## 1. Download the data

For each file below, open it on GitHub and click the **Download raw file** button (the download arrow at the top right of the file view):

- [`data/marts/mart_workforce_cost_bridge.csv`](../../data/marts/mart_workforce_cost_bridge.csv), about 2 MB
- [`data/marts/mart_workforce_cost_snapshot.csv`](../../data/marts/mart_workforce_cost_snapshot.csv), about 30 MB. GitHub won't preview a file this size, but the download works.

Save both in one folder, for example `Documents/Tableau Public/arcadia/`.

## 2. Connect

1. Open **Tableau Public** (the free desktop app).
2. **Connect → To a File → Text file**, then pick `mart_workforce_cost_bridge.csv`.
3. On the Data Source page, check the types: `month_end_date` and `prior_month_end_date` should be **Date**, `fiscal_year` should be a **String** (it's a label, not a number to sum), and the dollar columns should be **Number (decimal)**.
4. Add `mart_workforce_cost_snapshot.csv` as a **second data source** (Data → New Data Source). Keep the two separate: they have different grains, and joining them would duplicate rows.

Tableau Public stores an extract of the data inside the published workbook, so viewers never need the CSVs.

## 3. Calculations

### Measure switches
Create two string parameters:

- **Currency View**: `Nominal`, `Constant`
- **Pay Basis**: `Base`, `Loaded`

```
// Selected Amount
CASE [Pay Basis] + "|" + [Currency View]
    WHEN "Base|Nominal"     THEN [Base Usd Nominal]
    WHEN "Base|Constant"    THEN [Base Usd Constant]
    WHEN "Loaded|Nominal"   THEN [Loaded Usd Nominal]
    WHEN "Loaded|Constant"  THEN [Loaded Usd Constant]
END
```

### Walking across any date range
Create two date parameters, **Start Month** and **End Month**, with allowable values taken from `month_end_date`. Opening comes from the first month, Closing from the last, and every other driver is summed in between:

```
// Walk Amount
IF [Month End Date] >= [Start Month] AND [Month End Date] <= [End Month] THEN
    CASE [Driver]
        WHEN "Opening Run-Rate" THEN IIF([Month End Date] = [Start Month], [Selected Amount], 0)
        WHEN "Closing Run-Rate" THEN IIF([Month End Date] = [End Month],   [Selected Amount], 0)
        ELSE [Selected Amount]
    END
END
```

This works because the SQL guarantees each month's closing equals the next month's opening (test 08).

### Waterfall
1. Put `Driver` on Columns, sorted by `Driver Order`, and filter out `Closing Run-Rate`.
2. Put `SUM([Walk Amount])` on Rows as a **Running Total** table calculation. Change the mark type to **Gantt Bar**.
3. Create `-SUM([Walk Amount])` and drag it to **Size**.
4. Turn on **Analysis → Totals → Show Row Grand Totals** and rename the total to *Closing Run-Rate*.
5. Color by `SUM([Walk Amount]) > 0` for increases and decreases.

Check the result: the grand total should equal the Closing Run-Rate line you filtered out.

### Small-group suppression
On any sheet that shows pay for small slices (country × grade, for example), hide pay where fewer than five people are in view:

```
// Pay (suppressed)
IF SUM([Headcount]) < 5 THEN NULL ELSE SUM([Selected Amount]) END
```

### Compa-ratio (snapshot data source)
```
// Compa-Ratio
SUM([Base Usd Constant]) / SUM([Range Mid Usd Constant])
```

### FX impact (snapshot data source)
```
// FX Impact
SUM([Loaded Usd Nominal]) - SUM([Loaded Usd Constant])
```

## 4. Suggested dashboard layout

| Layer | Content |
|---|---|
| **Executive** | KPI tiles (closing run-rate, change, % change, FX impact) and the company waterfall for the selected period |
| **Analytical** | Waterfall by function or department; driver trend by fiscal quarter; nominal vs constant trend |
| **Diagnostic** | Snapshot drill-down by country, grade and job family, with compa-ratio and suppression applied |
| **Methodology** | Definitions, the walk formula and a link back to this repo |

## 5. Updating the data

When the data changes in GitHub, download the CSVs again and save over the old files. In Tableau Public, right-click each data source and choose **Refresh**, then republish.

If you want a data source that refreshes without re-downloading, Google Sheets is the one live connection Tableau Public supports. Import the walk CSV into a Google Sheet and connect to that instead.
