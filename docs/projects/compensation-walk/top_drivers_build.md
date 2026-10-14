# Top drivers card: build guide (walk data source)

> **Warehouse release 3:** part-time was removed (every employee is 1.0 FTE), so part-time counts and the FTE Changes step described here no longer exist in the data. This guide describes the dashboard as built on release 2; what changes is listed in [release 3 migration notes](../contingent-workforce/release_3_migration_notes.md).


Question the card answers: **which drivers matter most, and why?** Four rows, ranked by size, each with its amount (teal adds, coral subtracts), a bar and a one-line reason with the real counts. It follows Period, View, Group, Lens, Cost and Currency, because every value is the same `Walk Row` the waterfall draws.

Design source: `design/build_sketch_svg.py` (`drivers()`), card at 930, 190, 440 x 314 (container `Card Drivers`).

## Why a LOD chain and not a rank table calculation

A Top N filter ranks before the other dimension filters, and a rank table calculation needs every dimension on the Marks card ticked in Compute Using (new ones split the partitions). The card keeps the four largest by comparing each driver with the fourth largest value, found with the same `{ MAX(...) }` chain the waterfall headline uses (`Driver 1 Size`, `Driver 2 Size`). It is a plain Boolean filter, so nothing depends on pill settings.

## Calculations (walk source `ArcadiaHR`)

```
// TD Key   (row level; one row per individual step, never combined; names match the Expand axis aliases; Opening and Closing give Null)
CASE [step]
  WHEN "Hires" THEN "Hires"
  WHEN "Exits" THEN "Exits"
  WHEN "Transfers In" THEN "Transfers in"
  WHEN "Transfers Out" THEN "Transfers out"
  WHEN "Promotions" THEN "Promotions"
  WHEN "Demotions" THEN "Demotions"
  WHEN "Tenure Increases" THEN "Tenure raises"
  WHEN "Market Adjustments" THEN "Market adjustments"
  WHEN "Relocation Adjustments" THEN "Relocation"
  WHEN "International Transfer Adjustments" THEN "Cross-border move"
  WHEN "FTE Changes" THEN "FTE changes"
  WHEN "Fringe Rate Changes" THEN "Fringe rates"
  WHEN "FX Translation" THEN "Currency translation"
END

// TD Total   (one value per driver for the selected pair, view and group)
IF NOT ISNULL([TD Key]) THEN { FIXED [TD Key] : SUM(IF [In Pair] THEN [Walk Row] END) } END

// TD Abs
ABS([TD Total])

// TD Abs 1 .. 4   (largest, then each next largest)
{ MAX([TD Abs]) }
{ MAX(IF [TD Abs] < [TD Abs 1] THEN [TD Abs] END) }
{ MAX(IF [TD Abs] < [TD Abs 2] THEN [TD Abs] END) }
{ MAX(IF [TD Abs] < [TD Abs 3] THEN [TD Abs] END) }

// TD Show   (the filter: in the pair, not zero, among the four largest; fewer than four is fine)
[In Pair] AND [TD Abs] > 0 AND [TD Abs] >= IFNULL([TD Abs 4], 0)

// TD People
IF NOT ISNULL([TD Key]) THEN { FIXED [TD Key] : SUM(IF [In Pair] THEN [worker_count] END) } END

// TD People Text
IF [TD People] >= 1000
THEN STR(INT([TD People] / 1000)) + "," + RIGHT("00" + STR(INT([TD People]) % 1000), 3)
ELSE STR(INT([TD People])) END

// TD Value Text   (same pattern as D1 Text in dashboard_titles.md)
(IF [TD Total] < 0 THEN "−" ELSE "+" END) + "$" +
IF [Is FTE] THEN
    IF ABS([TD Total]) >= 999.5
    THEN STR(INT(INT(ROUND(ABS([TD Total]), 0)) / 1000)) + ","
         + RIGHT("00" + STR(INT(ROUND(ABS([TD Total]), 0)) % 1000), 3)
    ELSE STR(INT(ROUND(ABS([TD Total]), 0))) END
ELSE STR(ROUND(ABS([TD Total]) / 1000000, 1)) + "M" END

// TD Up Text / TD Down Text   (two fields so the label can color them differently)
IF [TD Total] >= 0 THEN [TD Value Text] ELSE "" END
IF [TD Total] < 0 THEN [TD Value Text] ELSE "" END

// TD Direction   (bar color)
IF [TD Total] >= 0 THEN "Adds" ELSE "Subtracts" END

// TD Top Name / TD Top Text / TD Headline   (card title)
{ MAX(IF [TD Abs] = [TD Abs 1] THEN [TD Key] END) }
{ MAX(IF [TD Abs] = [TD Abs 1] THEN [TD Value Text] END) }
IF ISNULL([TD Top Name]) THEN "No drivers in this selection"
ELSE [TD Top Name] + " moved pay the most, " + [TD Top Text] END
```

`TD People Label` (singular and plural, so a group of one reads "1 person"):

```
[TD People Text] + IF [TD People] = 1 THEN " person" ELSE " people" END
```

`TD Why` (one line, about 65 characters at most: the card's plot is about 390 px wide at 9 pt, and longer lines are clipped; counts come from `worker_count`, which counts people, not events):

```
CASE [TD Key]
WHEN "Hires" THEN
    IF NOT [Is FTE] THEN "New hires (" + [TD People Label] + ") added pay to the payroll."
    ELSEIF [TD Total] < 0 THEN [TD People Label] + " joined below the opening average, pulling it down."
    ELSE [TD People Label] + " joined above the opening average, pushing it up." END
WHEN "Exits" THEN
    IF NOT [Is FTE] THEN "Exits (" + [TD People Label] + ") took pay off the payroll."
    ELSEIF [TD Total] >= 0 THEN [TD People Label] + " left, earning less than average, so the average rose."
    ELSE [TD People Label] + " left, earning more than average, so the average fell." END
WHEN "Promotions" THEN "Pay stepped up with the new grade for " + [TD People Label] + "."
WHEN "Demotions" THEN "Pay stepped down with the lower grade for " + [TD People Label] + "."
WHEN "Tenure raises" THEN [TD People Label] + " stepped up on their hire anniversary."
WHEN "Market adjustments" THEN "Targeted pay corrections to the market: " + [TD People Label] + "."
WHEN "Relocation" THEN "Pay reset to the new office inside a country: " + [TD People Label] + "."
WHEN "Cross-border move" THEN "Pay reset to the new country and currency: " + [TD People Label] + "."
WHEN "FTE changes" THEN [TD People Label] + " changed hours, shifting the FTE the pay is spread over."
WHEN "Fringe rates" THEN "Employer-cost rates changed for " + [TD People Label] + ", not salaries."
WHEN "Transfers in" THEN [TD People Label] + " moved into this group at their current pay."
WHEN "Transfers out" THEN [TD People Label] + " moved out of this group with their pay."
WHEN "Currency translation" THEN "Exchange rates changed the dollar value of pay for " + [TD People Label] + "."
END
```

## Sheet `Top Drivers`

Built with the name-above-bar pattern ([map guide](tableau_office_moves_map_guide.md)). The name row carries two label lines: driver name plus signed amount (teal or coral), then the reason in 9 pt gray. Bars are the size (`MAX(TD Abs)`), always from zero, colored by `TD Direction`. No bar goes negative. The two axes are **not synchronized**: the `AVG(0)` axis is fixed 0 to 1 (names pinned to the left edge) and the bar axis is automatic from zero. Synchronized, the shared axis stretched to about minus the maximum (zero in the middle of the card, bars squeezed into half the width).

## Expected values (Company, FY26)

Release 2 values (current data) are in the generated [expected_values.md](expected_values.md): Tenure raises +$3,605, Hires −$1,223, Promotions +$721, Fringe rates +$283 (Pay per FTE). The table below is the release 1 build check, kept for the record.

| View | Rows, in order |
|---|---|
| Avg per FTE, Loaded, Constant | Tenure raises +$3,325, Hires −$3,270, Promotions & demotions +$632, Fringe rates +$279 |
| Total payroll | Hires +$411.3M, Exits −$331.8M, Tenure raises +$97.7M, Promotions & demotions +$18.6M |

These tie to the waterfall: raises +$3,378 = tenure +$3,325 and market +$53; hires and exits −$3,142 = hires −$3,270 and exits +$128 ([compensation_walk.md section 7](compensation_walk.md)).

## Reading it next to the waterfall (decided 2026-10-12)

The card ranks the individual steps, the compact waterfall shows four groups (`step_group`), so "Tenure raises +$3,325" sits beside a "Raises +$3,378" bar. Decision: keep the card's numbers (they match the Expand view) and make the relationship readable without a methodology note. No bars on the card (the thin bar added nothing the numbers do not say).

1. **Eyebrow on every row**, small gray caps in the waterfall's own words:
```
// TD Group   (row level)
CASE [step_group]
  WHEN "Headcount" THEN "HIRES & EXITS"
  WHEN "Career" THEN "PROMOTIONS"
  WHEN "Pay Rate" THEN "RAISES"
  ELSE "FRINGE & OTHER"
END
```
   Label of the name row: line 1 `<TD Group>` (8 pt gray), line 2 `<TD Key>  <TD Up Text><TD Down Text>`, line 3 `<TD Why>`.
2. **Subtitle says what the card is.** Expand shows 13 bars in the Company view (Opening, Closing and 11 steps), so the count is distinct `step`:
```
// TD Step Count
{ FIXED : COUNTD(IF [In Pair] AND [step_group] <> "Balance" THEN [step] END) }
// TD Subtitle
"Largest of the " + STR([TD Step Count]) + " steps behind the waterfall · teal adds, coral subtracts"
```
3. **The waterfall admits it is a summary.** `Btn Expand` reads `"Expand · " + STR([TD Step Count]) + " steps"` (calc `Expand Label`), `Btn Collapse` reads "Collapse · 4 groups".

**Individual drivers only (decided 2026-10-12).** The card never combines steps: Promotions and Demotions are two rows, Relocation and Cross-border move are two rows. `TD Key` is one name per `step`, so the count in the subtitle and on the Expand button (distinct `step`) is exactly the number of candidates. The eyebrow (`TD Group`) is the only place a group appears.
