# Compensation Walk: titles that answer a question

Every card has one question it answers. The **headline states the answer** (dynamic, so it is true for every Period, View and Group); the line under it says how to read the card. A title that only names the chart ("Office moves", "Compensation Walk - FTE") makes the reader do the work, so none of those remain. The same idea as the Global Workforce Footprint prototype, where the header asks and each card answers.

FY26 values are Company, loaded cost, constant currency (30 Jun 2025 to 30 Jun 2026).

| Card | Question it answers | Headline (FY26, Pay per FTE lens) |
|---|---|---|
| Page header | Why did pay change, where, over which dates? | **Compensation Walk** · "Why did average pay per FTE change at Arcadia Systems between Jun 30, 2025 and Jun 30, 2026? Loaded cost, constant currency" |
| Waterfall | What moved it? | "Average pay per FTE rose $1,153 (+1.1%): raises +$3,378, hires and exits −$3,142" |
| Waterfall, Total payroll lens | The same, in dollars | "Total payroll rose $195.4M (+6.5%): raises +$99.3M, hires and exits +$79.4M" |
| Office moves panel | Do people move inside or across borders, and where? | "66% of moves stay inside one country; Bengaluru to Hyderabad is the busiest route (28 people)" · subtitle "345 people changed office · 227 within one country · 118 across a border" |
| Busiest routes | Which routes carry the moves? | **Busiest routes** · "People who moved, by route" |
| Where people landed | Which regions received them? | **Where people landed** · "Arrivals by region, split by within one country and across a border" |
| Top drivers (next) | Which drivers matter most, and why? | to write with the card: the four biggest drivers, one reason each |
| Career moves (next) | How far do promotions climb? | e.g. "2,138 promotions and 114 demotions; only 16 reached Director and above" |

The two driver values in the waterfall headline are the two largest by size (up or down). The numbers tie to the walk: raises = tenure 3,324.70 + market 53.35 = 3,378.05; hires and exits = −3,269.63 + 127.33 = −3,142.30; total lens raises 97.73M + 1.57M = 99.30M, hires and exits 411.26M − 331.82M = 79.44M ([compensation_walk.md §7](compensation_walk.md)).

## Calculations (walk data source)

`In Pair` is the walk's existing Boolean (From, To, View and Group all match). The compact waterfall bars are `step_group`: Headcount = hires and exits (and transfers in org views), Career = promotions and demotions, Pay Rate = tenure and market raises, everything else = fringe and other; Opening and Closing are `Balance`.

```
// Lens Value   (row level; what the waterfall measures. Use your existing one if you have it.
//               When Cost and Currency become parameters, they join this calc)
IF [p_Lens] = "FTE" THEN [avg_loaded_usd_constant] ELSE [loaded_usd_constant] END

// Driver Name   (row level; the compact bars)
CASE [step_group] WHEN "Headcount" THEN "hires and exits" WHEN "Career" THEN "promotions"
                  WHEN "Pay Rate" THEN "raises" ELSE "fringe and other" END

// Driver Value   (one value per bar, fixed so the view cannot change it)
{ FIXED [Driver Name] : SUM(IF [In Pair] AND [step_group] <> "Balance" THEN [Lens Value] END) }

// Driver 1 Size   (the largest bar, up or down)
{ MAX(ABS([Driver Value])) }

// Driver 2 Size   (the second largest)
{ MAX(IF ABS([Driver Value]) < [Driver 1 Size] THEN ABS([Driver Value]) END) }

// Driver 1 Name / Driver 1 Value / Driver 2 Name / Driver 2 Value
{ MAX(IF ABS([Driver Value]) = [Driver 1 Size] THEN [Driver Name]  END) }
{ MAX(IF ABS([Driver Value]) = [Driver 1 Size] THEN [Driver Value] END) }
{ MAX(IF ABS([Driver Value]) = [Driver 2 Size] THEN [Driver Name]  END) }
{ MAX(IF ABS([Driver Value]) = [Driver 2 Size] THEN [Driver Value] END) }

// Walk Open / Walk Close / Walk Change
{ SUM(IF [In Pair] AND [step] = "Opening" THEN [Lens Value] END) }
{ SUM(IF [In Pair] AND [step] = "Closing" THEN [Lens Value] END) }
[Walk Close] - [Walk Open]
```

Money as text, signed, with a thousands separator in the Per FTE lens and in millions in the Total lens (Tableau has no FORMAT function). Write `D1 Text` once, then copy it for `D2 Text` (replace `Driver 1 Value` by `Driver 2 Value`) and for `Change Text` (use `[Walk Change]` and drop the sign):

```
// D1 Text
(IF [Driver 1 Value] < 0 THEN "−" ELSE "+" END) + "$" +
IF [p_Lens] = "FTE" THEN
    IF ABS([Driver 1 Value]) >= 999.5
    THEN STR(INT(INT(ROUND(ABS([Driver 1 Value]), 0)) / 1000)) + ","
         + RIGHT("00" + STR(INT(ROUND(ABS([Driver 1 Value]), 0)) % 1000), 3)
    ELSE STR(INT(ROUND(ABS([Driver 1 Value]), 0))) END
ELSE STR(ROUND(ABS([Driver 1 Value]) / 1000000, 1)) + "M" END

// Change Pct Text
IF [Walk Open] = 0 THEN "new group"
ELSE (IF [Walk Change] >= 0 THEN "+" ELSE "−" END) + STR(ROUND(ABS(100 * [Walk Change] / [Walk Open]), 1)) + "%" END

// Waterfall Title
(IF [p_Lens] = "FTE" THEN "Average pay per FTE " ELSE "Total payroll " END)
+ (IF [Walk Change] > 0 THEN "rose " ELSEIF [Walk Change] < 0 THEN "fell " ELSE "was flat " END)
+ [Change Text] + " (" + [Change Pct Text] + "): "
+ [Driver 1 Name] + " " + [D1 Text] + ", " + [Driver 2 Name] + " " + [D2 Text]

// Page Subtitle
"Why did " + (IF [p_Lens] = "FTE" THEN "average pay per FTE" ELSE "total payroll" END) + " change "
+ (IF [p_View] = "Company" THEN "at Arcadia Systems" ELSE "in " + [p_Group] END)
+ " between " + [From Text] + " and " + [To Text] + "? Loaded cost, constant currency"
```

`From Text` and `To Text` format the date parameters as "Jun 30, 2025": `LEFT(DATENAME('month', [p_From]), 3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))`. Reuse the dashboard's current subtitle calculation if it already does this. The page title becomes the static text **Compensation Walk**: the lens now lives in the subtitle and in the KPI card names.

## Office moves panel

The `Moves Title`, `Moves Scope`, `Top Route` calculations and the colored-run subtitle are in the [map guide](tableau_office_moves_map_guide.md) (sections 2 and 4). The two chart labels are static sheet titles: bold 11 pt slate for the name, regular 9 pt gray for the line under it (the prototype's card style).

## Rules for any new title

1. It states a finding in a sentence, with the number in it.
2. It is dynamic: it must stay true when the reader changes Period, View, Group or Lens, and it has an empty-state sentence.
3. The subtitle says how to read the card (what is counted, what the colors mean), never "Everyone at Arcadia Systems".
4. A color explained in a subtitle needs no legend: color the words (violet within one country, coral across a border).
