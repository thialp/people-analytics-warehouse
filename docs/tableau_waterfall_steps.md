# Headcount & FTE Walk: the waterfall sheet, step by step

Only the waterfall (a Gantt chart) with its dynamic title and caption. It assumes the fields from the main guide already exist: `Walk Value`, `Selected Value`, `In Range`, the parameters **Start Month**, **End Month**, **Measure**, and the KPI card field `K Valid`.

Fixed 1400 × 850 dashboard, waterfall card at **x 56, y 188, 780 × 624**.

## 1. Build the chart

The chart is a Gantt bar: each bar is a start position plus a length. The running total must be an aggregate calculation. (A *dimension* on Color splits the marks into groups and restarts the running total inside each group, which is the usual way this chart breaks.)

- Create three calculated fields:
```
// Waterfall Position
// Movement bars end at the running total; Opening and Closing sit on the total itself.
// Compute Using: Movement Category (sorted by Movement Order).
IF ATTR([Movement Category]) = "Closing"
    THEN SUM([Walk Value])
    ELSE RUNNING_SUM(SUM([Walk Value]))
END
```
```
// Waterfall Size
// Negative on purpose: a Gantt bar grows to the right of its start, so a negative size
// draws the bar backwards from the running total to where it began.
-SUM([Walk Value])
```
```
// Bar Type  (an aggregate, so it can go on Color without splitting the table calculation)
IF ATTR([Movement Category]) = "Opening" OR ATTR([Movement Category]) = "Closing" THEN "Level"
ELSEIF SUM([Walk Value]) >= 0 THEN "Increase"
ELSE "Decrease"
END
```
- Columns: `Movement Category`, sorted by `Movement Order` (right-click → Sort → Field → Movement Order, Minimum, Ascending). Keep **Closing** in the view: it is its own bar, so no filter and no grand total are needed.
- Rows: `Waterfall Position` → right-click → **Compute Using → Movement Category**.
- Mark type **Gantt Bar**. Drag `Waterfall Size` to **Size**, and `Bar Type` to **Color**.
- **Edit Colors:** Level warm gray `#8C8A84`, Increase teal `#00938D`, Decrease coral `#E4572E`.
- Right-click the axis → **Edit Axis** → tick **Include zero**. Bars start at zero so the size of each movement isn't exaggerated (Viz of the Day reviewers check this).
- **Dynamic title and caption.** The title states the finding and the caption explains what is *not* a bar (internal moves). Both are text built from calculated fields. The sheet's marks are split by `Movement Category`, so every number they use must be a **FIXED** calculation (a plain `SUM` would only see one category's rows). Create these fields:

```
// WF Open
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Opening" AND [Month End Date] = [Start Month] THEN [Headcount] END) })
```
```
// WF Close
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Closing" AND [Month End Date] = [End Month] THEN [Headcount] END) })
```
```
// WF Hires
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Hires" THEN [Headcount] END) })
```
```
// WF Leavers
ZN({ FIXED : -SUM(IF [In Range] AND ([Movement Category] = "Voluntary Terminations" OR [Movement Category] = "Involuntary Terminations") THEN [Headcount] END) })
```
```
// WF Moves
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Internal Moves In" THEN [Headcount] END) })
```
```
// WF Promos
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Internal Moves In" AND [Movement Reason] = "Promotion" THEN [Headcount] END) })
```
```
// WF FTE Open
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Opening" AND [Month End Date] = [Start Month] THEN [Fte] END) })
```
```
// WF FTE Close
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "Closing" AND [Month End Date] = [End Month] THEN [Fte] END) })
```
```
// WF FTE Chg
ZN({ FIXED : SUM(IF [In Range] AND [Movement Category] = "FTE Changes" THEN [Fte] END) })
```

Text helpers (the comma pattern from the KPI cards guide, Section 4.2; shown once, then the field list):
```
// WF Hires Str
IF [WF Hires] >= 1000
THEN STR(DIV(INT([WF Hires]), 1000)) + "," + RIGHT("00" + STR(INT([WF Hires]) % 1000), 3)
ELSE STR(INT([WF Hires])) END
```
Create the same pattern for `WF Leavers Str` (on `[WF Leavers]`), `WF Net Str` (on `ABS([WF Close] - [WF Open])`), `WF Moves Str` (`[WF Moves]`), `WF Promos Str` (`[WF Promos]`), `WF Other Str` (`[WF Moves] - [WF Promos]`), `WF FTE Open Str` (`ROUND([WF FTE Open], 0)`) and `WF FTE Close Str` (`ROUND([WF FTE Close], 0)`). Wrap the expression in `INT(...)` as above. Then:

```
// WF FTE Chg Str   (signed, whole number)
IF ROUND([WF FTE Chg], 0) < 0 THEN "−" ELSE "+" END +
STR(INT(ABS(ROUND([WF FTE Chg], 0))))
```
```
// WF Period   (a 12-month range reads as the fiscal year; Arcadia's year starts July 1)
IF DATEDIFF('month', [Start Month], [End Month]) = 11
THEN "FY" + RIGHT(STR(YEAR([End Month]) + IF MONTH([End Month]) >= 7 THEN 1 ELSE 0 END), 2)
ELSE LEFT(DATENAME('month', [Start Month]), 3) + " " + STR(YEAR([Start Month])) + " – " +
     LEFT(DATENAME('month', [End Month]), 3) + " " + STR(YEAR([End Month]))
END
```
```
// WF Title
IF NOT [K Valid] THEN "Choose a start month on or before the end month"
ELSE [WF Period] + ": " + [WF Hires Str] + " hires " +
     IF [WF Hires] >= [WF Leavers] THEN "outpaced " ELSE "fell short of " END +
     [WF Leavers Str] + " leavers, " +
     IF [WF Close] >= [WF Open] THEN "adding " ELSE "removing " END +
     [WF Net Str] + " people"
END
```
```
// WF Caption
IF NOT [K Valid] THEN "" ELSE
[WF Moves Str] + " internal moves (" + [WF Promos Str] + " promotions, " + [WF Other Str] +
" other) move people between teams, so they net to zero at company level. FTE " +
[WF FTE Open Str] + " → " + [WF FTE Close Str] + ", including " + [WF FTE Chg Str] + " from schedule changes."
END
```

- *Title:* on the waterfall sheet, drag `WF Title` to **Detail** (it has one value, so it does not split the marks), then **Worksheet → Show Title**, double-click the title, **Insert → `WF Title`**, and set Tableau Bold 12 pt navy. Add a second line of static text, Tableau Book 9 pt slate: `Opening + hires − leavers ± internal moves = closing · axis starts at zero`.
- *Caption:* create a new worksheet **Waterfall Caption**: drag `WF Caption` to **Label** on a Text mark (Tableau Book 8 pt slate, alignment left, wrap on), hide headers and title, Entire View. On the dashboard float it at the bottom of the waterfall card (see the layout table in the KPI guide) and set the waterfall sheet's bottom **inner padding** to 64 so the chart stops above it.
- For FY26 these read: *"FY26: 2,354 hires outpaced 1,663 leavers, adding 691 people"* and *"1,615 internal moves (1,038 promotions, 577 other) move people between teams, so they net to zero at company level. FTE 12,282 → 12,940, including −34 from schedule changes."*
- The title and caption use headcount even when Measure is FTE (the caption already shows the FTE change). They ignore filters on the waterfall sheet because of FIXED; a filter action on the dashboard will not change them.
- Hide the *Bar Type* legend (select it on the dashboard and delete it; the colors are explained by the labels), and add a filter so the **FTE Changes** bar only appears when Measure is FTE: create `Show Category` = `[Measure] = "FTE" OR [Movement Category] <> "FTE Changes"`, drag it to Filters and keep True.
- **Check:** the Closing bar's top equals the `Closing` KPI, and the last movement bar ends exactly where the Closing bar starts.
- At company level Internal Moves In and Out cancel (+1,615 and −1,615). Hide them with a filter on this sheet if you prefer a cleaner company view; they matter on department views.

## 2. Place it on the dashboard

1. Drag the **Waterfall** sheet to the dashboard, **Floating**, position **x 56, y 188**, size **780 × 624**.
2. Layout pane: Background `#FBFBF8`, Border 1px solid `#E4E3DD`. Inner padding: left 12, top 12, right 12, **bottom 64** (the chart stops above the caption).
3. Float the **Waterfall Caption** sheet at **x 68, y 756, 756 × 48**, background none, title hidden, above the waterfall sheet in the layout order.
4. Delete the *Bar Type* legend if it is on the dashboard.

## 3. Check

| Check | Expected (FY26, Start 2025-07-31, End 2026-06-30, Headcount) |
|---|---|
| Opening bar | 12,510 |
| Hires | +2,354 |
| Voluntary + Involuntary | −1,341 and −322 |
| Closing bar | 13,201, and the last movement bar ends exactly where it starts |
| Title | FY26: 2,354 hires outpaced 1,663 leavers, adding 691 people |
| Caption | 1,615 internal moves (1,038 promotions, 577 other) … FTE 12,282 → 12,940, including −34 from schedule changes. |
| Measure = FTE | Opening 12,282, FTE Changes bar appears at −34, Closing 12,940 |
| Start after End | Title reads "Choose a start month on or before the end month" |
