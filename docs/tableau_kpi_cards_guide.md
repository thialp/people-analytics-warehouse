# KPI cards as map layers: the Headcount & FTE Walk card band

![Headcount and FTE Walk preview](images/headcount_walk_preview.png)

The five cards under the header (Closing headcount, Closing FTE, Hires, Voluntary turnover, Internal moves) are **one Tableau sheet**. Every title, number and note on it is text drawn as a map layer, positioned by calculated fields. A transparent card image sits underneath. The result:

- Five cards, 15 text layers, one sheet, one query.
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
All three go on the **Label** shelf of the same layer (`kpi_pt Note 1`); only one is ever non-empty, so the color follows the sign. In the Edit Label window put them on one line with no spaces, `<KPI 1 Note Up><KPI 1 Note Down><KPI 1 Note Flat>`, then select each field and color it separately: Up teal `#006B66`, Down dark coral `#B8401F`, Flat slate `#5A6170`.

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

Titles are constant text, held in five one-line fields so they can sit on the Label shelf:

| Field | Formula |
|---|---|
| `KPI 1 Title` | `"Closing headcount"` |
| `KPI 2 Title` | `"Closing FTE"` |
| `KPI 3 Title` | `"Hires"` |
| `KPI 4 Title` | `"Voluntary turnover (annualized)"` |
| `KPI 5 Title` | `"Internal moves"` |

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

Two corner points. Tableau always zooms a map to fit the extent of its marks, so without them it would stretch the five text points to fill the sheet and the Fit and Shift parameters would have no effect. Two invisible points at the opposite corners of the sheet fix the extent. (Use points, not a `MAKELINE` frame: on a worksheet a line drew as a dot at its midpoint, so its ends did not count toward the extent.)

```
// kpi_Corner TL   (not Fit-scaled: the true corner of the sheet)
MAKEPOINT([kpi_SheetH] / 2 * [kpi_Scale], -[kpi_SheetW] / 2 * [kpi_Scale])
```
```
// kpi_Corner BR
MAKEPOINT(-[kpi_SheetH] / 2 * [kpi_Scale], [kpi_SheetW] / 2 * [kpi_Scale])
```

There is **no gate** on the points: every row produces the same point, so Tableau draws one mark per layer, and the label measures aggregate every row. The one rule: **no other dimension may be on a layer's Marks card**, or Tableau splits the layer into one mark per value.

## 5. Build the sheet

1. In **KPI Cards**, double-click `kpi_Corner TL`. Tableau creates a map. In the Marks card set the mark type to **Circle**, size to the smallest and **Color opacity to 0%**, so it is invisible. Then drag `kpi_Corner BR` onto the map, drop it on **Add a Marks Layer**, and give it the same settings.
2. **Size is set on the dashboard, not the sheet.** A worksheet cannot have a fixed size, so in the sheet editor the map fills your window and the text looks misplaced. The layout math assumes the sheet is exactly 1400 × 110, which you get when you float it on the dashboard (Section 7). Build the dashboard shell first (Fixed 1400 × 850, sheet floating at x 0, y 78, width 1400, height 110), then click the sheet there and use the **Go to Sheet** arrow to edit; judge positions on the dashboard only.
3. Hide everything map-like: **Map → Background Maps → None**; **Map → Map Options**: untick *Show Map Search*, *Show View Toolbar* and *Allow Pan/Zoom*. Set the sheet to **Entire View** and tooltips to none (**Worksheet → Tooltip**, untick *Show tooltips*).
4. Drag `kpi_pt Title 1` onto the map and drop it on **Add a Marks Layer**. Then in that layer's Marks card:
   - Mark type **Circle**, size at the **smallest**, Color opacity **0%**.
   - **Leave the rest of this Marks card empty.** The layer's only field is its anchor point (`kpi_pt …`); the words come from the Label slot below. Do not drag anything else (Movement Category, Department and so on) onto Color, Detail, Size or Tooltip: a dimension there splits the single mark into many and the label goes blank or repeats.
   - **Label → Text**: click **Label** on the Marks card, then the `…` button next to Text to open the Edit Label window.
     - *Title layers:* Tableau only lets you edit label text once a field is on the Label shelf (otherwise the Text box is grayed out), so each title is a one-line calculated field holding its words (Section 4.3). Drag `KPI n Title` onto **Label** and the words appear.
     - *Value and note layers:* drag the field (for example `KPI 1 Value`) onto **Label**; that is the live text. Use the `…` button only to set font and color.
     - Set the font, size and color in the same window.
   - In the Label pop-up: tick **Show mark labels** and **Allow labels to overlap other marks**; set **Alignment** (dropdown, default Automatic) to Horizontal **Right** and Vertical **Middle**. On a mark label this setting says where the text sits relative to the point: Automatic centers it on the point, Left puts it to the left of the point (the text *ends* there), and Right makes it *start* at the point, which is what we want.
5. Repeat for all 15 text layers. Fonts:

| Layer | Font |
|---|---|
| Titles | Tableau Semibold, 8 pt, slate `#5A6170` |
| Values | Tableau Bold, 20 pt, navy `#13233A` |
| Notes | Tableau Book, 8 pt, slate `#5A6170`; card 1's note is colored per field (Section 4.3) |

   Tableau Public embeds only Tableau's own fonts, so stay with these.
6. Hide the "null" indicator in the corner (right-click it → **Hide Indicator**).

## 6. Calibrate (about 5 minutes)

1. Make the dashboard (Section 7) with the background PNG underneath, and the sheet on top, then work from there.
2. With `kpi_FitX` and `kpi_FitY` at **1.1**, each title, value and note should start 16 px inside its card, and the three rows should sit about 19, 44 and 68 px below each card's top edge.
3. If the text is a little too wide or too narrow across the five cards, change `kpi_FitX` by 0.01 at a time; if the rows are too spread out or too tight vertically, change `kpi_FitY`. (To adjust live, right-click the parameter, choose **Show Parameter**, and edit it on the dashboard; remove the control afterwards.)
4. If everything is off by the same few pixels, change `kpi_ShiftX` / `kpi_ShiftY`, or the row offsets (`kpi_TitleDY`, `kpi_ValueDY`, `kpi_SubDY`).
5. If the text *ends* at its anchor instead of starting there, set Horizontal alignment to **Right** (Section 5).

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
| Fit and Shift parameters change nothing, and the text stretches across the whole sheet | The two corner layers are missing or not counted. Tableau re-fits the map to its marks each time, so the corners must be present (Section 4.4). |
| Text ends at its anchor instead of starting there | Alignment is Left; set Horizontal to Right. |
| Text clipped at the right of card 5 | The text is wider than the card; shorten the note or reduce the font. |
| Text looks misplaced in the sheet editor | Expected: a worksheet can't have a fixed size. Judge on the dashboard (Section 7). |
| Fonts look different on Tableau Public | Only Tableau's fonts are embedded; avoid others. |
