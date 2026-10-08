# KPI cards as map layers: the Headcount & FTE Walk card band

![Headcount and FTE Walk preview](images/headcount_walk_preview.png)

The five cards under the header (Closing headcount, Closing FTE, Hires, Voluntary turnover, Internal moves) are **one Tableau sheet**. Every title, number and note on it is text drawn as a map layer, positioned by calculated fields. A transparent card image sits underneath. The result:

- Five cards, 17 text pieces, one sheet, one query.
- Numbers, notes and colors update with the Start Month, End Month and any filter.
- The layout (card width, gaps, text positions) is controlled by 16 parameters, so you can restyle the band without redrawing anything.
- No images carry numbers, so nothing is stale and everything is searchable and accessible as a sheet.

**How it works in one paragraph.** A map sheet places marks by latitude and longitude, and Tableau can draw a text label on any mark. If we treat the sheet's pixels as a tiny flat map, a pixel position becomes a (latitude, longitude) pair, a label drawn at that point appears at that pixel, and a calculated field can compute the position from parameters. Each text piece is its own map layer (a Circle mark with 0% opacity, so only its label shows).

> **Tested?** The SQL, the numbers and the string formulas in this guide were checked against the warehouse (see Section 9). I could not run Tableau Public here, so the layer settings are written from how the technique works. Section 6 (calibration) is where you tune it on your screen; budget 15 minutes for it.

Download the companion workbook [`Arcadia_KPI_Cards_Config.xlsx`](Arcadia_KPI_Cards_Config.xlsx): every parameter, calculation, layer and dashboard setting in this guide as copy-ready tables, plus a validation tab with the FY26 numbers.

## 1. What you need first

- The Headcount & FTE Walk data source and the calculated fields from [that guide](tableau_headcount_walk_guide.md), Section 4: `In Range`, `Hires`, `Voluntary Leavers`, `Voluntary Turnover (annualized)`, `Hire Rate (annualized)`, `Internal Moves`, `Average Headcount`, `Months in Range`, and the parameters **Start Month** and **End Month**.
- The card background image [`brand/arcadia_kpi_cards_bg.png`](brand/arcadia_kpi_cards_bg.png): a transparent 1400 × 110 picture (drawn at 2×) holding five rounded off-white cards with a 1px `#E4E3DD` border.
- A new, empty worksheet named **KPI Cards**.

## 2. Layout in pixels

The dashboard is 1400 × 850. The header band is 0–76. The KPI sheet floats at **x = 0, y = 78, width 1400, height 110**, and the background image floats at the same position and size, **underneath** it. The whole dashboard uses a 56 px side gutter, so cards and charts line up.

| Item | Value (px) |
|---|---|
| Sheet size | 1400 × 110 |
| Left gutter (first card's left edge) | 56 |
| Card top inside the sheet | 12 |
| Card size | 244 × 86 |
| Gap between cards | 17 (card lefts at 56, 317, 578, 839, 1100) |
| Text inset from the card's left edge | 16 |
| Title / value / note baselines below the card top | 19 / 44 / 68 |

Why the 56 px gutter: Tableau pads the map's fitted extent by roughly 4.5% on each side, so text anchored in the outer 9% of the sheet drifts off. The first text anchor sits at 72 px, which stays inside.

## 3. Parameters

Create these 16 parameters (Float unless noted; none are shown on the dashboard). The prefix `kpi_` keeps them together in the Parameters list.

| Name | Default | What it does |
|---|---|---|
| `kpi_Scale` | 0.010986328125 | Degrees per pixel at zoom 7: 360 ÷ (256 × 2^7). Don't change it. |
| `kpi_SheetW` / `kpi_SheetH` | 1400 / 110 | The sheet's pixel size |
| `kpi_FitX` / `kpi_FitY` | 1.1 / 1.1 | Calibration factors (Section 6) |
| `kpi_ShiftX` / `kpi_ShiftY` | 0 / 0 | Nudge everything by pixels |
| `kpi_GridLeft` | 56 | Left edge of card 1 |
| `kpi_GridTop` | 12 | Top edge of the cards |
| `kpi_CardW` / `kpi_CardH` | 244 / 86 | Card size |
| `kpi_GapX` | 17 | Space between cards |
| `kpi_PadX` | 16 | Text inset from the card's left edge |
| `kpi_TitleDY` / `kpi_ValueDY` / `kpi_SubDY` | 19 / 44 / 68 | Text center below the card top |

## 4. Calculated fields

### 4.1 The numbers (prefix `K`)

These reuse your existing fields. Create them in order.

```
// K Valid  (a start after the end is meaningless)
[Start Month] <= [End Month]
```
```
// K Open HC
ZN(SUM(IF [In Range] AND [Movement Category] = "Opening" AND [Month End Date] = [Start Month]
       THEN [Headcount] END))
```
```
// K Close HC
ZN(SUM(IF [In Range] AND [Movement Category] = "Closing" AND [Month End Date] = [End Month]
       THEN [Headcount] END))
```
```
// K Close FTE
ZN(SUM(IF [In Range] AND [Movement Category] = "Closing" AND [Month End Date] = [End Month]
       THEN [Fte] END))
```
```
// K Net Pct
IF [K Open HC] = 0 THEN 0 ELSE ([K Close HC] - [K Open HC]) / [K Open HC] END
```
```
// K Hires
ZN([Hires])
```
```
// K Leavers Vol
ZN([Voluntary Leavers])
```
```
// K Moves
ZN([Internal Moves])
```
```
// K Promotions
ZN(SUM(IF [In Range] AND [Movement Category] = "Internal Moves In"
            AND [Movement Reason] = "Promotion" THEN [Headcount] END))
```
```
// K Other Moves
[K Moves] - [K Promotions]
```
```
// K Part Time Gap  (headcount minus FTE)
[K Close HC] - [K Close FTE]
```

Cards 1 and 2 always show **headcount** and **FTE** by name, so they ignore the Measure parameter; that parameter drives the waterfall.

### 4.2 Text helpers

Tableau has no number-format function for text, so we build the strings with whole-number math. `DIV` is integer division and `%` is the remainder.

```
// K Open Str   (12510 -> "12,510")
IF [K Open HC] >= 1000
THEN STR(DIV(INT([K Open HC]), 1000)) + "," + RIGHT("00" + STR(INT([K Open HC]) % 1000), 3)
ELSE STR(INT([K Open HC])) END
```
```
// K Net Pct Str   (0.055 -> "5.5%"; sign handled by the note)
STR(DIV(INT(ROUND(ABS([K Net Pct]) * 1000, 0)), 10)) + "." +
STR(INT(ROUND(ABS([K Net Pct]) * 1000, 0)) % 10) + "%"
```

Every other string repeats one of these two patterns: the **comma pattern** (for counts) and the **percent pattern** (for rates). Replace the field name in each.

### 4.3 What each card shows

| Card | Value field | Note field(s) |
|---|---|---|
| 1 Closing headcount | `KPI 1 Value` | `KPI 1 Note Up`, `Note Down`, `Note Flat` |
| 2 Closing FTE | `KPI 2 Value` | `KPI 2 Note` |
| 3 Hires | `KPI 3 Value` | `KPI 3 Note` |
| 4 Voluntary turnover (annualized) | `KPI 4 Value` | `KPI 4 Note` |
| 5 Internal moves | `KPI 5 Value` | `KPI 5 Note` |

```
// KPI 1 Value
IF NOT [K Valid] THEN "—"
ELSEIF [K Close HC] >= 1000
THEN STR(DIV(INT([K Close HC]), 1000)) + "," + RIGHT("00" + STR(INT([K Close HC]) % 1000), 3)
ELSE STR(INT([K Close HC])) END
```
```
// KPI 1 Note Up   (teal text)
IF [K Valid] AND [K Net Pct] > 0 THEN "+" + [K Net Pct Str] + " vs " + [K Open Str] + " at start" END
```
```
// KPI 1 Note Down   (dark coral text)
IF [K Valid] AND [K Net Pct] < 0 THEN "−" + [K Net Pct Str] + " vs " + [K Open Str] + " at start" END
```
```
// KPI 1 Note Flat   (slate text)
IF [K Valid] AND [K Net Pct] = 0 THEN [K Net Pct Str] + " vs " + [K Open Str] + " at start" END
```
The three notes sit on the same spot; only one is ever non-empty, so the color follows the sign without any color field.

```
// KPI 2 Value   (12,940.0: round to tenths, then split whole and tenth)
IF NOT [K Valid] THEN "—" ELSE
  IF DIV(INT(ROUND([K Close FTE] * 10, 0)), 10) >= 1000
  THEN STR(DIV(DIV(INT(ROUND([K Close FTE] * 10, 0)), 10), 1000)) + "," +
       RIGHT("00" + STR(DIV(INT(ROUND([K Close FTE] * 10, 0)), 10) % 1000), 3)
  ELSE STR(DIV(INT(ROUND([K Close FTE] * 10, 0)), 10)) END
  + "." + STR(INT(ROUND([K Close FTE] * 10, 0)) % 10)
END
```
```
// KPI 2 Note
IF NOT [K Valid] THEN "" ELSE
  IF INT(ROUND([K Part Time Gap], 0)) >= 1000
  THEN STR(DIV(INT(ROUND([K Part Time Gap], 0)), 1000)) + "," +
       RIGHT("00" + STR(INT(ROUND([K Part Time Gap], 0)) % 1000), 3)
  ELSE STR(INT(ROUND([K Part Time Gap], 0))) END
  + " below headcount (part-time)"
END
```
```
// KPI 3 Value   (the comma pattern on [K Hires])
IF NOT [K Valid] THEN "—"
ELSEIF [K Hires] >= 1000
THEN STR(DIV(INT([K Hires]), 1000)) + "," + RIGHT("00" + STR(INT([K Hires]) % 1000), 3)
ELSE STR(INT([K Hires])) END
```
```
// KPI 3 Note   (the percent pattern on the annualized hire rate)
IF NOT [K Valid] THEN "" ELSE
  STR(DIV(INT(ROUND(ZN([Hire Rate (annualized)]) * 1000, 0)), 10)) + "." +
  STR(INT(ROUND(ZN([Hire Rate (annualized)]) * 1000, 0)) % 10) + "% annualized hire rate"
END
```
```
// KPI 4 Value   (hidden for groups under 20 people, like Rate Shown)
IF NOT [K Valid] OR [Average Headcount] < 20 THEN "—" ELSE
  STR(DIV(INT(ROUND([Voluntary Turnover (annualized)] * 1000, 0)), 10)) + "." +
  STR(INT(ROUND([Voluntary Turnover (annualized)] * 1000, 0)) % 10) + "%"
END
```
```
// KPI 4 Note   (the comma pattern on [K Leavers Vol])
IF NOT [K Valid] THEN "" ELSE
  IF [K Leavers Vol] >= 1000
  THEN STR(DIV(INT([K Leavers Vol]), 1000)) + "," + RIGHT("00" + STR(INT([K Leavers Vol]) % 1000), 3)
  ELSE STR(INT([K Leavers Vol])) END
  + " leavers by choice"
END
```
```
// KPI 5 Value   (the comma pattern on [K Moves])
IF NOT [K Valid] THEN "—"
ELSEIF [K Moves] >= 1000
THEN STR(DIV(INT([K Moves]), 1000)) + "," + RIGHT("00" + STR(INT([K Moves]) % 1000), 3)
ELSE STR(INT([K Moves])) END
```
```
// KPI 5 Note
IF NOT [K Valid] THEN "" ELSE
  IF [K Promotions] >= 1000
  THEN STR(DIV(INT([K Promotions]), 1000)) + "," + RIGHT("00" + STR(INT([K Promotions]) % 1000), 3)
  ELSE STR(INT([K Promotions])) END
  + " promotions · " +
  IF [K Other Moves] >= 1000
  THEN STR(DIV(INT([K Other Moves]), 1000)) + "," + RIGHT("00" + STR(INT([K Other Moves]) % 1000), 3)
  ELSE STR(INT([K Other Moves])) END
  + " other moves"
END
```

The titles are not fields: type them directly into each title layer's label (Section 5).

### 4.4 Geometry

Pixel to degrees. With the origin at the sheet center, longitude is the x offset and latitude is the **negative** y offset (pixels grow downward, latitude grows upward):

> lon = (x − W/2) × scale × FitX  lat = −(y − H/2) × scale × FitY

`MAKEPOINT` takes **(latitude, longitude)**, in that order.

Three latitude fields (one per text row):

```
// kpi_lat Title
-([kpi_GridTop] + [kpi_TitleDY] + [kpi_ShiftY] - [kpi_SheetH] / 2) * [kpi_Scale] * [kpi_FitY]
```
```
// kpi_lat Value
-([kpi_GridTop] + [kpi_ValueDY] + [kpi_ShiftY] - [kpi_SheetH] / 2) * [kpi_Scale] * [kpi_FitY]
```
```
// kpi_lat Sub
-([kpi_GridTop] + [kpi_SubDY] + [kpi_ShiftY] - [kpi_SheetH] / 2) * [kpi_Scale] * [kpi_FitY]
```

Five longitude fields (`i` is 0 to 4; write the number out in each field):

```
// kpi_lon C1   (i = 0; C2 uses 1, C3 uses 2, C4 uses 3, C5 uses 4)
([kpi_GridLeft] + 0 * ([kpi_CardW] + [kpi_GapX]) + [kpi_PadX] + [kpi_ShiftX] - [kpi_SheetW] / 2)
  * [kpi_Scale] * [kpi_FitX]
```

Fifteen anchor points. Each card has three pieces of text (a title, a value and a note), and each piece sits at its own spot, so each gets its own point: 5 cards × 3 pieces = 15. Names run `kpi_pt Title 1` … `kpi_pt Title 5`, `kpi_pt Value 1` … `kpi_pt Value 5` and `kpi_pt Note 1` … `kpi_pt Note 5`:

```
// kpi_pt Title 1
MAKEPOINT([kpi_lat Title], [kpi_lon C1])
```
Title *n* uses `kpi_lat Title` and `kpi_lon Cn`; Value *n* uses `kpi_lat Value`; Note *n* uses `kpi_lat Sub` (the latitude of the note row).

Two helper lines:

```
// kpi_Frame   (not Fit-scaled: it marks the sheet's true extent; drawn at 0% opacity)
MAKELINE(MAKEPOINT([kpi_SheetH] / 2 * [kpi_Scale], -[kpi_SheetW] / 2 * [kpi_Scale]),
         MAKEPOINT(-[kpi_SheetH] / 2 * [kpi_Scale],  [kpi_SheetW] / 2 * [kpi_Scale]))
```
```
// kpi_Check   (card 1 bottom-left to card 5 top-left, Fit applied; used only to calibrate)
MAKELINE(
  MAKEPOINT(-([kpi_GridTop] + [kpi_CardH] - [kpi_SheetH] / 2) * [kpi_Scale] * [kpi_FitY],
            ([kpi_GridLeft] - [kpi_SheetW] / 2) * [kpi_Scale] * [kpi_FitX]),
  MAKEPOINT(-([kpi_GridTop] - [kpi_SheetH] / 2) * [kpi_Scale] * [kpi_FitY],
            ([kpi_GridLeft] + 4 * ([kpi_CardW] + [kpi_GapX]) - [kpi_SheetW] / 2) * [kpi_Scale] * [kpi_FitX]))
```

There is **no gate** on the points: every row produces the same point, so Tableau draws one mark per layer, and the label measures aggregate every row. The one rule: **no other dimension may be on a layer's Marks card**, or Tableau splits the layer into one mark per value.

## 5. Build the sheet

1. In **KPI Cards**, double-click `kpi_Frame`. Tableau creates a map. This is the bottom layer. In the Marks card set **Color opacity to 0%**, so it is invisible.
2. **Set the sheet size first.** The layout math assumes the sheet is exactly 1400 × 110. Open the **Entire View** dropdown in the toolbar, choose **Fixed Size → Custom**, and enter width 1400, height 110. Until you do, the sheet fills your screen and every text piece lands in the wrong place.
3. Hide everything map-like: **Map → Background Maps → None**; **Map → Map Options**: untick *Show Map Search*, *Show View Toolbar* and *Allow Pan/Zoom*. Set the sheet to **Entire View** and tooltips to none (**Worksheet → Tooltip**, untick *Show tooltips*).
4. Drag `kpi_pt Title 1` onto the map and drop it on **Add a Marks Layer**. Then in that layer's Marks card:
   - Mark type **Circle**, size at the **smallest**, Color opacity **0%**.
   - **Leave the rest of this Marks card empty.** The layer's only field is its anchor point (`kpi_pt …`); the words come from the Label slot below. Do not drag anything else (Movement Category, Department and so on) onto Color, Detail, Size or Tooltip: a dimension there splits the single mark into many and the label goes blank or repeats.
   - **Label → Text**: click **Label** on the Marks card, then the `…` button next to Text to open the Edit Label window.
     - *Title layers:* delete anything in the box and type the words as plain text (for example `Closing headcount`). Titles never change, so they are not fields.
     - *Value and note layers:* don't type. Click **Insert** in that window and pick the field (for example `KPI 1 Value`); the box then shows the field in angle brackets, and that is the live text.
     - Set the font, size and color in the same window.
   - In the Label pop-up: tick **Show mark labels** and **Allow labels to overlap other marks**; set **Alignment** (dropdown, default Automatic) to Horizontal **Left** and Vertical **Middle**. Automatic centers the text on its point instead of starting it there.
5. Repeat for all 17 layers (15 anchor points, plus the two extra notes for card 1's Down and Flat states, which reuse `kpi_pt Sub 1`). Fonts:

| Layer | Font |
|---|---|
| Titles | Tableau Semibold, 8 pt, slate `#5A6170` |
| Values | Tableau Bold, 20 pt, navy `#13233A` |
| Notes | Tableau Book, 8 pt, slate `#5A6170`; for `KPI 1 Note Up` use teal text `#006B66`, for `KPI 1 Note Down` dark coral `#B8401F` |

   Tableau Public embeds only Tableau's own fonts, so stay with these.
6. Last, add `kpi_Check` as the top layer: Mark type Line, color magenta, width 2 (you will delete it after calibration).
7. Hide the "null" indicator in the corner (right-click it → **Hide Indicator**).

## 6. Calibrate (about 15 minutes)

1. Make the dashboard (Section 7) with the background PNG underneath, and the sheet on top.
2. Look at the magenta check line: its two ends should land on the **bottom-left corner of card 1** and the **top-left corner of card 5**.
3. If the line is too short or too long horizontally, change `kpi_FitX`; vertically, `kpi_FitY`. Change both in steps of 0.01. They should end up close to 1.1 (Tableau pads the fit by about 4.5% on each side).
4. If the line is correct but a text piece looks off by a few pixels, change `kpi_ShiftX`/`kpi_ShiftY` or the text row offsets (`kpi_TitleDY`, `kpi_ValueDY`, `kpi_SubDY`).
5. If a title is centered on its anchor instead of starting there, set the label alignment to **Left** in that layer.
6. Delete the `kpi_Check` layer.

## 7. Put it on the dashboard

1. Dashboard size: **Fixed, 1400 × 850**.
2. Drag an **Image** object, set it to **Floating**, choose `docs/brand/arcadia_kpi_cards_bg.png`, position **x 0, y 78, w 1400, h 110**. In its settings, tick **Fit Image** and leave **Center Image** off.
3. Drag the **KPI Cards** sheet, also **Floating**, at the same position and size, and move it above the image in the layout tree. Set its background to **None** and hide its title.
4. Check that no other object overlaps this band, and that every other card on the page starts at the same left gutter, x = 56.

## 8. Header controls

The header buttons (Start, End, Headcount, FTE, Methodology) do **not** need an image per state. See the *Parameter action* entry in [the headcount guide, Section 6](tableau_headcount_walk_guide.md#6-dashboards-and-actions): one small sheet colors the selected option from the parameter itself, so the selected state follows automatically.

## 9. Check values (FY26)

Start Month 2025-07-31, End Month 2026-06-30:

| Card | Value | Note |
|---|---|---|
| 1 Closing headcount | 13,201 | +5.5% vs 12,510 at start |
| 2 Closing FTE | 12,940.0 | 261 below headcount (part-time) |
| 3 Hires | 2,354 | 18.3% annualized hire rate |
| 4 Voluntary turnover (annualized) | 10.4% | 1,341 leavers by choice |
| 5 Internal moves | 1,615 | 1,038 promotions · 577 other moves |

I ran the same text formulas in Python against the warehouse numbers and they reproduce this table exactly. Set Start Month after End Month: all five values should show "—".

## 10. If something looks wrong

| Symptom | Likely cause |
|---|---|
| A label is blank | A dimension is on that layer's Marks card, splitting the layer so the label sees a partial row set. Remove it. |
| Two copies of a label | Same cause. |
| The whole text block sits too low or too high | Adjust `kpi_ShiftY`, or the Fit values (Section 6). |
| Text clipped at the right of card 5 | The text is wider than the card; shorten the note or reduce the font. |
| Layout changes when the dashboard is not fixed size | Use a fixed 1400 × 850 size. |
| Fonts look different on Tableau Public | Only Tableau's fonts are embedded; avoid others. |
