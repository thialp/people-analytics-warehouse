# Dashboard #3, Workforce Planning: from the Custom SQL to the first check sheets

Step by step in Tableau Desktop: connect to SQL Server, add the four data sources, and build four small check sheets that must show the numbers below before any dashboard design starts. Method and definitions: [workforce_planning.md](workforce_planning.md). Arcadia Systems is fictional and all data is synthetic.

## The four data sources (and why four)

| Data source name | Custom SQL file | Grain | Rows |
|---|---|---|---:|
| **Position Fill** | [`tableau/custom_sql_position_fill.sql`](../../../tableau/custom_sql_position_fill.sql) | one row per fill (external hire or internal move) | 30,575 |
| **Vacancy Pool** | [`tableau/custom_sql_vacancy_pool.sql`](../../../tableau/custom_sql_vacancy_pool.sql) | one row per empty seat per month-end | 62,055 |
| **Plan vs Actual** | [`tableau/custom_sql_plan_vs_actual.sql`](../../../tableau/custom_sql_plan_vs_actual.sql) | one row per plan version × cost center × quarter | 29,415 |
| **Seat Corridors** | [`tableau/custom_sql_seat_corridors.sql`](../../../tableau/custom_sql_seat_corridors.sql) | one row per quarter × from office × to office (backfills that changed office) | 821 |

Each file reads one reporting view (`rpt.vw_*`) and lists its columns, so field names are the warehouse names ([data dictionary](../../warehouse/data_dictionary.md#mart_position_fill)). All four were compared with the DuckDB marts row for row (`sqlserver/check_tsql_in_duckdb.py`).

**Do not join them in one data source.** They have different grains. Joining fills to the plan repeats every plan target on every fill row, and joining the pool repeats every seat every month. Keep four sources; parameters (and, later, relationships on cost center and quarter only where a sheet needs both) tie them together.

## 0. Before Tableau

Docker running, `arcadia-sql` up, and the warehouse built (your last `build_all` is current). Tableau **Desktop** (the free Tableau Public app cannot connect to SQL Server; publishing works as for Dashboard #2, with extracts). If Tableau shows a certificate error, copy `tableau/sqlserver_trust_local_certificate.tdc` to `~/Documents/My Tableau Repository/Datasources/` and restart Tableau.

## 1. Connect and add the four sources

1. **File > New.** On the Connect pane: **To a Server > Microsoft SQL Server.**
2. Server `localhost, 1433` · Database `ArcadiaHR` · Authentication *Use a specific username and password* · Username `sa` · Password: the container password (the 17-character one) · Require SSL unchecked > **Sign In**.
3. On the Data Source page, drag **New Custom SQL** onto the canvas. Paste the whole of `custom_sql_position_fill.sql` > **OK**.
4. Rename the source: double-click the name at the top left ("Custom SQL Query (ArcadiaHR)") and type **Position Fill**.
5. **Data > New Data Source** and repeat steps 1 to 4 for `custom_sql_vacancy_pool.sql` (**Vacancy Pool**), `custom_sql_plan_vs_actual.sql` (**Plan vs Actual**) and `custom_sql_seat_corridors.sql` (**Seat Corridors**). Tableau keeps the server sign-in, so each takes a few seconds.
6. **Fix the types once per source** (Data pane, right-click the field):
   - `Fiscal Year`, `Fiscal Quarter`, `Grade`, `Prior Grade`, `Chain Depth`, `Chain Length`, `Version Order`: **Convert to Dimension** (they are labels, not amounts). Leave them numeric so they sort correctly.
   - Booleans (`Reuse Candidate`, `Is Manager Seat`, `Was Frozen`, `Is Stale`, `Is Latest Version`, `Is Fiscal Year End`) arrive as True/False. Nothing to do.
   - Dollar fields: Default Properties > Number Format > Currency (Custom), 0 decimals.
7. Optional now, required before publishing: on each source, Data Source tab > Connection **Extract**. Live is fine while building and checking.

## 2. Sheet `CHK Fills FY26` (Position Fill)

**Question:** what did FY26 hiring fill?

Calculated fields (Analysis > Create Calculated Field), all in Position Fill:

```
// Fills            (one row per fill, so a distinct count of the key is the number of fills)
COUNTD([Fill Id])

// Reuse Candidates (net-new seats approved while a matching seat stood empty 90+ days)
COUNTD(IF [Reuse Candidate] THEN [Fill Id] END)

// Walk Gap         (must read 0.00: the four pay steps add up to the pay change)
SUM([Pay Change Usd Constant])
 - (SUM([Level Effect Usd Constant]) + SUM([Location Effect Usd Constant])
    + SUM([Market Effect Usd Constant]) + SUM([Positioning Effect Usd Constant]))
```

Build:

1. Drag `Fiscal Year` to **Filters** > select **2026** > OK.
2. `Seat Type` to **Rows**, then `Fill Type` to **Rows** (right of it).
3. `Fills` to **Text** (Marks card). Then `Reuse Candidates` onto the table (drop it on the numbers: Tableau switches to Measure Names / Measure Values).
4. **Analysis > Totals > Show Column Grand Totals** and **Add All Subtotals**.

Expected:

| Seat Type | Fill Type | Fills | Reuse Candidates |
|---|---|---:|---:|
| Backfill | External Hire | 3,531 | 0 |
| Backfill | Internal Move | 1,137 | 0 |
| Backfill total | | **4,668** | 0 |
| Net-new | External Hire | 1,704 | |
| Net-new | Internal Move | 477 | |
| Net-new total | | **2,181** | **628** |
| Grand total | | **6,849** | **628** |

Reuse candidates exist only on net-new fills (628 of 2,181 = 28.8%). Internal moves: 1,137 + 477 = **1,614** (24%).

Second block on the same sheet (duplicate the sheet, name it `CHK Backfills FY26`):

1. Filters: `Fiscal Year` = 2026 and `Seat Type` = Backfill.
2. Rows: `Prior Vacate Reason`. Text: `Fills`. Expected **Voluntary 2,612 · Internal Move Out 1,397 · Involuntary 659** (total 4,668).
3. Replace `Prior Vacate Reason` with `Level Change`. Expected **Same 3,916 · Down 567 · Up 185**.
4. Remove the row pill; put `Pay Change Usd Constant`, `Level Effect Usd Constant`, `Location Effect Usd Constant`, `Market Effect Usd Constant`, `Positioning Effect Usd Constant` (SUM) and `Walk Gap` on the table. Expected:

| Measure | FY26 backfills |
|---|---:|
| Pay change | −$7,004,254.10 |
| Level effect | −$6,788,600.86 |
| Location effect | −$671,912.38 |
| Market effect | +$2,211,643.30 |
| Positioning effect | −$1,755,384.16 |
| Walk Gap | **$0.00** |

5. Median days, same filters plus `Seat Decision` ≠ Immediate refill (Filters > Seat Decision > Exclude): `MEDIAN([Time To Fill Days])` **42**, `MEDIAN([Vacancy Days])` **54**.

## 3. Sheet `CHK Plan vs Actual FY26` (Plan vs Actual)

**Question:** did FY26 hiring follow the plan, by version?

Calculated fields, in Plan vs Actual:

```
// Planned Net-new         SUM([Planned Net New])
// Actual Net-new          SUM([Actual Net New])
// Net-new Attainment      SUM([Actual Net New]) / SUM([Planned Net New])
// Planned Backfills       SUM([Planned Backfills])
// Actual Backfills        SUM([Actual Backfills])

// Planned Year-end HC     (a level: read the fiscal year-end quarter only, never sum quarters)
SUM(IF [Quarter End Date] = MAKEDATE([Fiscal Year], 6, 30) THEN [Planned Ending Headcount] END)

// Actual Year-end HC
SUM(IF [Quarter End Date] = MAKEDATE([Fiscal Year], 6, 30) THEN [Actual Ending Headcount] END)

// Planned Year-end Cost / Actual Year-end Cost   (same pattern with [Planned Cost Usd] and
//   [Actual Cost Usd Plan Fx]: the actual cost at the version's own FX, so it compares with the plan)
```

Build:

1. Filters: `Fiscal Year` = 2026.
2. Rows: `Plan Version`. Sort it by `Version Order` (right-click the pill > Sort > Field > Version Order, Minimum, Ascending).
3. Put the calcs on the table (Measure Values), formatted `#,##0` and the attainment as a percentage.

Expected (each reforecast covers only the quarters still ahead, so its flows are smaller):

| Plan Version | Planned Net-new | Actual Net-new | Attainment | Planned Backfills | Actual Backfills | Planned Year-end HC | Actual Year-end HC |
|---|---:|---:|---:|---:|---:|---:|---:|
| FY26 Budget | 2,762 | 2,181 | 79.0% | 5,031 | 4,668 | 30,347 | 30,014 |
| FY26 RF1 | 1,845 | 1,532 | 83.0% | 3,772 | 3,639 | 30,229 | 30,014 |
| FY26 RF2 | 1,097 | 981 | 89.4% | 2,524 | 2,408 | 30,151 | 30,014 |
| FY26 RF3 | 549 | 510 | 92.9% | 1,202 | 1,207 | 30,095 | 30,014 |

Year-end cost, planned vs actual at the version's FX: Budget $3,380,139,551.15 vs $3,341,223,578.40; RF1 $3,396,460,209.24 vs $3,367,102,635.16; RF2 $3,393,655,798.51 vs $3,373,297,834.62; RF3 $3,401,481,434.59 vs $3,391,597,933.51. The actual differs by version because each version's actual is priced at that version's own FX date.

**The trap to see once:** remove `Plan Version` from Rows. Actual Net-new jumps to **5,204** (2,181 + 1,532 + 981 + 510): the same actuals summed four times. Every sheet on this source must keep one version (a `Plan Version` filter or a parameter), or `Is Latest Version` = True. Put `Plan Version` back.

## 4. Sheet `CHK Vacancy Pool Jun 2026` (Vacancy Pool)

**Question:** how many seats stood empty at year-end, and how many for 90 days or more?

```
// Seats          COUNTD([Position Id])
// Stale Seats    COUNTD(IF [Is Stale] THEN [Position Id] END)
```

1. Drag `Month End Date` to **Filters** > choose **Exact date** > 6/30/2026 > OK.
2. Rows: `Status`. Text: `Seats`, `Stale Seats`.

Expected: **Open 725 (77 stale) · Frozen 252 (136 stale)**.

The trap: remove the date filter and keep `Fiscal Year` = 2026 instead: Seats becomes 6,025, the seats that were empty at **any** month-end of the year. Counts of the pool are always at one month-end.

## 5. Sheet `CHK Corridors FY26 US` (Seat Corridors)

1. Filters: `Fiscal Year` = 2026; `From Country Code` = US; `To Country Code` = US.
2. Rows: `From City`, `To City`. Text: SUM(`Seats`). Sort by SUM(Seats) descending.

Expected top rows: **Austin → Chicago 19 · Austin → Atlanta 14 · San Francisco → Austin 14**, then three routes at 12 (Austin → New York, Austin → San Francisco, New York → Austin). Without the country filters the FY26 total is **467** seats: 410 moved to another office in the same country and 57 across a border (all leader seats refilled the same day by a successor based there).

## 6. When all four match

Save the workbook (`Arcadia Workforce Planning.twb`) and keep the four `CHK` sheets hidden in it, as Dashboard #1 keeps its CheckList: every later change can be checked against them. Next: the dashboard design (executive layer: hiring vs plan; analytical layer: backfill vs net-new, prior incumbent profile, pay walk; diagnostic layer: vacancy pool and reuse candidates; corridors map).

If a number differs, send me the sheet and the number. The warehouse values are fixed and checked (`08_validate_workforce_planning.sql` on SQL Server), so a difference is a filter, a type or a missing `Plan Version` filter.
