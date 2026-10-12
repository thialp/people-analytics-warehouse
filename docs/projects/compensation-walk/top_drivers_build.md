# Top drivers card: build guide (walk data source)

Question the card answers: **which drivers matter most, and why?** Four rows, ranked by size, each with its amount (teal adds, coral subtracts), a bar and a one-line reason with the real counts. It follows Period, View, Group, Lens, Cost and Currency, because every value is the same `Walk Row` the waterfall draws.

Design source: `design/build_sketch_svg.py` (`drivers()`), card at 930, 190, 440 x 314 (container `Card Drivers`).

## Why a LOD chain and not a rank table calculation

A Top N filter ranks before the other dimension filters, and a rank table calculation needs every dimension on the Marks card ticked in Compute Using (new ones split the partitions). The card keeps the four largest by comparing each driver with the fourth largest value, found with the same `{ MAX(...) }` chain the waterfall headline uses (`Driver 1 Size`, `Driver 2 Size`). It is a plain Boolean filter, so nothing depends on pill settings.

## Calculations (walk source `ArcadiaHR`)

```
// TD Key   (row level; the eight walk drivers, plus the org-view and currency ones; Opening and Closing give Null)
CASE [step]
  WHEN "Hires" THEN "Hires"
  WHEN "Exits" THEN "Exits"
  WHEN "Transfers In" THEN "Transfers in"
  WHEN "Transfers Out" THEN "Transfers out"
  WHEN "Promotions" THEN "Promotions & demotions"
  WHEN "Demotions" THEN "Promotions & demotions"
  WHEN "Tenure Increases" THEN "Tenure raises"
  WHEN "Market Adjustments" THEN "Market adjustments"
  WHEN "Relocation Adjustments" THEN "Relocation"
  WHEN "International Transfer Adjustments" THEN "Relocation"
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

`TD Why` (one line, 80 characters at most so it fits at 9 pt in a 408 px card; counts come from `worker_count`):

```
CASE [TD Key]
WHEN "Hires" THEN
    IF NOT [Is FTE] THEN [TD People Text] + " hires added pay to the payroll."
    ELSEIF [TD Total] < 0 THEN [TD People Text] + " people joined below the opening average, which pulled it down."
    ELSE [TD People Text] + " people joined above the opening average, which pushed it up." END
WHEN "Exits" THEN
    IF NOT [Is FTE] THEN [TD People Text] + " exits took pay off the payroll, offsetting hiring."
    ELSEIF [TD Total] >= 0 THEN [TD People Text] + " people left. They earned less than average, so the average rose."
    ELSE [TD People Text] + " people left. They earned more than average, so the average fell." END
WHEN "Promotions & demotions" THEN [TD People Text] + " people changed grade. Promotions add pay, demotions take a little back."
WHEN "Tenure raises" THEN [TD People Text] + " people stepped up on their hire anniversary."
WHEN "Market adjustments" THEN "Targeted pay corrections to the market for " + [TD People Text] + " people."
WHEN "Relocation" THEN "Pay reset to the destination office for " + [TD People Text] + " people who moved."
WHEN "FTE changes" THEN [TD People Text] + " people changed hours, which moved the FTE the pay is spread over."
WHEN "Fringe rates" THEN "Employer-cost rates changed for " + [TD People Text] + " people. Salaries did not move."
WHEN "Transfers in" THEN [TD People Text] + " people moved into this group at their current pay."
WHEN "Transfers out" THEN [TD People Text] + " people moved out of this group, taking their pay with them."
WHEN "Currency translation" THEN "Exchange rates changed the dollar value of pay for " + [TD People Text] + " people."
END
```

## Sheet `Top Drivers`

Built with the name-above-bar pattern ([map guide](tableau_office_moves_map_guide.md)). The name row carries two label lines: driver name plus signed amount (teal or coral), then the reason in 9 pt gray. Bars are the size (`MAX(TD Abs)`), always from zero, colored by `TD Direction`. No axis ever goes negative, so the name row cannot shift (the Region Bars issue).

## Expected values (Company, FY26)

| View | Rows, in order |
|---|---|
| Avg per FTE, Loaded, Constant | Tenure raises +$3,325, Hires −$3,270, Promotions & demotions +$632, Fringe rates +$279 |
| Total payroll | Hires +$411.3M, Exits −$331.8M, Tenure raises +$97.7M, Promotions & demotions +$18.6M |

These tie to the waterfall: raises +$3,378 = tenure +$3,325 and market +$53; hires and exits −$3,142 = hires −$3,270 and exits +$128 ([compensation_walk.md section 7](compensation_walk.md)).
