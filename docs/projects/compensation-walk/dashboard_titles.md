# Compensation Walk: titles that answer a question

Every card has one question it answers. The **headline states the answer** (dynamic, so it is true for every Period, View and Group); the line under it says how to read the card. A title that only names the chart ("Office moves", "Compensation Walk - FTE") makes the reader do the work, so none of those remain. The same idea as the Global Workforce Footprint prototype, where the header asks and each card answers.

FY26 values are Company, loaded cost, constant currency (30 Jun 2025 to 30 Jun 2026). Built and checked in Tableau on 2026-10-10 unless marked otherwise.

| Card | Question it answers | Headline (FY26, Pay per FTE lens) |
|---|---|---|
| Page header | Where did pay change, what drove it, over which dates? | **Compensation Walk** · "Where average pay per FTE changed at Arcadia Systems, what drove it, and how people move between offices · Jun 30, 2025 to Jun 30, 2026 · loaded cost, constant currency". A statement of what the page answers, not a question (the Global Workforce Footprint prototype does the same) |
| Waterfall | What moved it? | Headline "Average pay per FTE rose $1,153 (+1.1%)", then two 9 pt lines: "Jun 30, 2025 to Jun 30, 2026 · Pay per FTE = loaded cost ÷ FTE · axis not from zero" and "Biggest moves: raises +$3,378, hires and exits −$3,142" |
| Waterfall, Total payroll lens | The same, in dollars | "Total payroll rose $195.4M (+6.5%)"; "… · Total payroll = loaded cost of all workers · axis in $M, not from zero"; "Biggest moves: raises +$99.3M, hires and exits +$79.4M" |
| Office moves panel | Do people move inside or across borders? | "345 people changed office; 66% stayed inside one country" · subtitle "227 within one country · 118 across a border · dots mark where people arrived" |
| Top 5 busiest routes | Which routes carry the moves? | **Top 5 busiest routes** · "Bengaluru to Hyderabad leads, 28 people" / "People who changed office, by route" |
| Growth by region | Did every region grow, and from what base? | **Growth by region** · "Arcadia overall +5.6% (28,436 \| 30,015)" / "Region: opening \| closing headcount · bar: growth". Each name row carries `opening | closing` |
| Top drivers (next) | Which drivers matter most, and why? | to write with the card: the four biggest drivers, one reason each |
| Career moves (next) | How far do promotions climb? | e.g. "2,138 promotions and 114 demotions; only 16 reached Director and above" |

The two driver values in the waterfall's second line are the two largest by size (up or down). The numbers tie to the walk: raises = tenure 3,324.70 + market 53.35 = 3,378.05; hires and exits = −3,269.63 + 127.33 = −3,142.30; total lens raises 97.73M + 1.57M = 99.30M, hires and exits 411.26M − 331.82M = 79.44M ([compensation_walk.md §7](compensation_walk.md)).

## Calculations (walk data source)

**Lens test.** One Boolean, `Is FTE` = `[p_Lens] = "FTE"`, is used everywhere a calc depends on the lens (`Lens Value`, `D1 Text`, `D2 Text`, `Change Text`, `Waterfall Title`, `Waterfall Subtitle`, `Page Subtitle`, the axis calcs). The parameter's underlying Values stay `FTE` and `Amount`; Display As shows **Avg pay per FTE** and **Total payroll**. Calcs test the Value, never the Display As text. (On 2026-10-10 the titles read "Total payroll" while FTE was selected until every `[p_Lens] = "FTE"` was replaced by `[Is FTE]`.)

`In Pair` is the walk's existing Boolean (From, To, View and Group all match). The compact waterfall bars are `step_group`: Headcount = hires and exits (and transfers in org views), Career = promotions and demotions, Pay Rate = tenure and market raises, everything else = fringe and other; Opening and Closing are `Balance`.

```
// Lens Value   (row level; what the waterfall measures. Use your existing one if you have it.
//               When Cost and Currency become parameters, they join this calc)
IF [Is FTE] THEN [avg_loaded_usd_constant] ELSE [loaded_usd_constant] END

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
IF [Is FTE] THEN
    IF ABS([Driver 1 Value]) >= 999.5
    THEN STR(INT(INT(ROUND(ABS([Driver 1 Value]), 0)) / 1000)) + ","
         + RIGHT("00" + STR(INT(ROUND(ABS([Driver 1 Value]), 0)) % 1000), 3)
    ELSE STR(INT(ROUND(ABS([Driver 1 Value]), 0))) END
ELSE STR(ROUND(ABS([Driver 1 Value]) / 1000000, 1)) + "M" END

// Change Pct Text
IF [Walk Open] = 0 THEN "new group"
ELSE (IF [Walk Change] >= 0 THEN "+" ELSE "−" END) + STR(ROUND(ABS(100 * [Walk Change] / [Walk Open]), 1)) + "%" END

// Waterfall Title   (short, one line at 12 pt; the drivers moved to the subtitle)
(IF [Is FTE] THEN "Average pay per FTE " ELSE "Total payroll " END)
+ (IF [Walk Change] > 0 THEN "rose " ELSEIF [Walk Change] < 0 THEN "fell " ELSE "was flat " END)
+ [Change Text] + " (" + [Change Pct Text] + ")"
// Change Text carries no sign ("rose $195.4M", not "rose +$195.4M")

// Waterfall Subtitle   (two lines; the sheet needs about 54 px of height for title plus both lines)
[From Text] + " to " + [To Text] + " · "
+ IF [Is FTE] THEN "Pay per FTE = loaded cost ÷ FTE" ELSE "Total payroll = loaded cost of all workers" END
+ IF [Is FTE] THEN " · axis not from zero" ELSE " · axis in $M, not from zero" END
+ CHAR(10) + "Biggest moves: " + [Driver 1 Name] + " " + [D1 Text] + ", " + [Driver 2 Name] + " " + [D2 Text]

// Page Subtitle   (a statement of what the page answers, not a question)
"Where " + (IF [Is FTE] THEN "average pay per FTE" ELSE "total payroll" END) + " changed "
+ (IF [p_View] = "Company" THEN "at Arcadia Systems" ELSE "in " + [p_Group] END)
+ ", what drove it, and how people move between offices · "
+ [From Text] + " to " + [To Text] + " · loaded cost, constant currency"
```

`From Text` and `To Text` format the date parameters as "Jun 30, 2025" (they use only parameters, so they work in either data source; copy them into Office Moves if a sheet there needs them):

```
// From Text
LEFT(DATENAME('month', [p_From]), 3) + " " + STR(DAY([p_From])) + ", " + STR(YEAR([p_From]))
// To Text
LEFT(DATENAME('month', [p_To]), 3) + " " + STR(DAY([p_To])) + ", " + STR(YEAR([p_To]))
```

The walk source's period columns are `from_month_end` and `to_month_end` (not `from_date`). The page title becomes the static text **Compensation Walk**: the lens now lives in the subtitle and in the KPI card names.

## Office moves panel and the two bar cards

`Moves Title`, `Routes Subtitle`, the routes tooltip calcs and the colored-run subtitle are in the [map guide](tableau_office_moves_map_guide.md) (sections 2 and 4); the Growth by region calcs are in its `Region Headcount` section. The two bar cards share one title block: bold 11 pt navy line, then a two-line 9 pt gray subtitle (sheet titles with the calc inserted), so their bars start on the same line.

## Waterfall axis (true values, trimmed, both lenses)

The waterfall is a Gantt on a trimmed axis: a zero-based axis squashes steps that are 0.3% to 6% of the total. The axis is shown with light gridlines and **true** values, and re-fits itself when the lens changes or Expand opens. The three calcs (all in the walk source; `Waterfall Position` is a table calc, Compute Using `step`):

```
// Axis Unit   (depends only on the parameter)
IF [Is FTE] THEN 1 ELSE 1000000 END

// Waterfall Position   (true running total; before 2026-10-10 it also subtracted [Axis Floor], so ticks read $0M to $645M)
[Run Pos] / [Axis Unit]

// Waterfall Size   (negative on purpose: the Gantt bar is drawn back from the position; Opening and Closing start at the floor)
IF ATTR([step]) = "Opening" OR ATTR([step]) = "Closing"
THEN -(SUM([Walk Row]) - [Axis Floor]) / [Axis Unit]
ELSE -SUM([Walk Row]) / [Axis Unit] END
```

`Axis Floor` stays in dollars. Sheet settings, on `Waterfall Compact` and `Waterfall Expand`: Show Header on; Edit Axis, Range Automatic, **Include zero off**, title blank; Numbers Custom `$#,##0`; Major ticks Automatic, minor None; Format Lines, grid lines solid 0.5 px `#E4E3DD`, zero lines and axis ruler None; axis labels 9 pt gray. Delete the old reference line. Judge the tick density on the dashboard, not in the sheet editor (the editor is about 850 px tall, the compact card about 230 px).

What it shows: Avg pay per FTE ticks about $102,000 to $109,000 (Opening $107,554, Closing $108,706); Total payroll ticks about $2,800 to $3,450 in $M in Expand (Opening 3,000, Closing 3,195).

**Lessons recorded.**
- **Tableau number formats cannot be conditional.** `[>=1000000]$#,##0,,"M";$#,##0` is read as `positive;negative`, so every positive tick got the million format ("$0M" for 107,554). K or M by value is impossible on an axis. Scaling the data per lens (`Axis Unit`) and one plain format is the working answer. Bar labels can switch units because they are calculated strings.
- **A fixed tick interval cannot follow a parameter**, so leave Major ticks on Automatic.
- **`FLOOR` cannot take a table calculation**, and a floor, if needed, is already `Axis Floor`.
- A hidden floor offset in the position makes every axis label wrong; keep the position true and trim through the Level bars' size.

## Rules for any new title

1. It states a finding in a sentence, with the number in it.
2. It is dynamic: it must stay true when the reader changes Period, View, Group or Lens, and it has an empty-state sentence.
3. The subtitle says how to read the card (what is counted, what the colors mean), never "Everyone at Arcadia Systems".
4. A color explained in a subtitle needs no legend: color the words (violet within one country, coral across a border).
5. A page subtitle states what the page answers ("Where pay changed, what drove it, ..."); it is not a question.
6. Keep a title or subtitle to the number of lines its sheet can show: a third line is clipped, not wrapped. Give the sheet the height, or cut the line.
