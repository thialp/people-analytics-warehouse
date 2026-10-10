# Tableau build: Office moves map (Dashboard #2, Summary page, bottom panel)

Data source: Custom SQL `tableau/custom_sql_office_moves.sql` (field reference: [office_moves.md](office_moves.md)). Every sheet below filters with the same four values as the walk sheets: the date pair (`p_From`, `p_To`) and the view and group (`p_View`, `p_Group`), so nothing on the dashboard needs a workaround or an explanation.

## Check values (FY26: p_From 30 Jun 2025, p_To 30 Jun 2026)

| p_View / p_Group | People | Within one country | Across a border | Notes |
|---|---|---|---|---|
| Company / Arcadia Systems | 345 | 227 | 118 | 143 lines; busiest Bengaluru to Hyderabad (28), then Hyderabad to Bengaluru (25), Bengaluru to Pune (19) |
| Office / Bengaluru | 93 | 75 | 18 | 32 moved in, 61 moved out |
| Country / India | 136 | 91 | 45 | 91 inside India, 15 moved in from abroad, 30 moved out |
| Function / Technology | 147 | | | 131 inside the function, 10 left it, 6 joined it |

## 1. Connect

1. **Data > New Data Source > Microsoft SQL Server**, same server and database (`ArcadiaHR`) as the walk. Do not add it to the walk's data source: two Custom SQL tables there would need a relationship, and the parameters are shared across data sources anyway.
2. Drag **New Custom SQL** onto the canvas, paste the whole of `tableau/custom_sql_office_moves.sql`, **OK**. Rename the data source `Office Moves`.
3. Expected: about 260,000 rows; `from_month_end`, `to_month_end` are dates; the latitudes and longitudes are numbers (right-click each, **Geographic Role > None** if Tableau assigns one).

## 2. Calculated fields (data source Office Moves)

```
// Move In Scope
// The walk's In Pair, plus the people. Boolean.
[from_month_end] = [p_From] AND [to_month_end] = [p_To]
AND [view_name] = [p_View] AND [group_name] = [p_Group]

// Corridor
[from_office] + " to " + [to_office]

// Move Line
MAKELINE(MAKEPOINT(MIN([from_latitude]), MIN([from_longitude])),
         MAKEPOINT(MIN([to_latitude]),   MIN([to_longitude])))

// Arrival Point
MAKEPOINT(MIN([to_latitude]), MIN([to_longitude]))

// Movers
ZN(SUM(IF [Move In Scope] THEN [workers] END))

// Movers Within
ZN(SUM(IF [Move In Scope] AND [flow_scope] = "Domestic" THEN [workers] END))

// Movers Across
ZN(SUM(IF [Move In Scope] AND [flow_scope] = "International" THEN [workers] END))

// Moves Title
IF [Movers] = 0 THEN "No one in this selection changed office in this period"
ELSE STR([Movers]) + IF [Movers] = 1 THEN " person" ELSE " people" END + " changed office"
END

// Moves Subtitle
CASE [p_View]
WHEN "Company" THEN "Everyone at Arcadia Systems"
WHEN "Office"  THEN "Moves in or out of " + [p_Group]
WHEN "Country" THEN "Moves in or out of " + [p_Group] + ", and inside it"
ELSE "People in " + [p_Group]
END
```

`Movers`, `Movers Within` and `Movers Across` filter inside the calculation, not on the Filters shelf, so a selection with no moves shows 0 and the message instead of a blank sheet.

## 3. Sheet `Office Moves Map`

1. Double-click **Move Line**. A map appears with lines (Tableau adds *Latitude (generated)* and *Longitude (generated)*).
2. Drag **Move In Scope** to **Filters**, select **True**.
3. Marks (layer 1, `Move Line`): mark type **Automatic** (not Line: the Line type joins the marks into one connecting path and the sheet zigzags; Automatic draws each corridor as its own arc, curved along the shortest route over the globe). **Corridor** to **Detail**. **SUM(workers)** to **Size**. **flow_scope_label** to **Color**: *Within one country* `#5B4FB3`, *Across a border* `#E4572E`; opacity 60%. Size slider: small to medium, so Bengaluru to Hyderabad (28) is clearly thicker than a single move.
4. Drag **Arrival Point** onto **Add a Marks Layer**. Layer 2: mark type **Circle**, **to_office** to **Detail**, **SUM(workers)** to **Size**, color navy `#13233A`, opacity 80%, size small (people arriving).
5. Layer order on the Marks card: Arrival Point on top, Move Line below.
6. **Map > Background Maps > Light**. **Map > Map Layers**: washout 40%, keep only Base and Coastline.
7. **Map > Map Options**: untick *Show Map Search*, *Show View Toolbar*. Keep pan and zoom on so a reader can look closer.
8. Hide the headers and the Latitude/Longitude axes. Fit is greyed out on a map sheet; the framing is the saved zoom instead. Zoom out with the **−** control and pan until Vancouver (west) and Sydney (east) sit just inside the left and right edges. The 35 offices span about 2.4 wide to 1 tall in Mercator, so at 236 high the map is about 490 wide; that is why the map container in section 5 is 490, not wider. Long arcs bow north and may touch the top edge; that is expected.
9. Tooltip:
   ```
   <Corridor>
   <SUM(workers)> people · <flow_scope_label>
   Why: <move_reason>
   ```
   Add `move_reason` to **Detail** on layer 1 for the *Why* line. Each office pair has one reason, so lines do not split.
10. Legend: show the **flow_scope_label** color legend, title blank.

Expected, Company FY26: 143 lines; the thickest runs between Bengaluru and Hyderabad. Set p_View to Office and p_Group to Bengaluru: every line starts or ends at Bengaluru.

## 4. Title and stat sheets (each with no dimension on the view)

| Sheet | Text | Notes |
|---|---|---|
| `Office Moves Title` | `<Moves Title>` bold 14 pt navy | Panel title; shows the empty-state message |
| `Office Moves Subtitle` | `<Moves Subtitle>` 11 pt slate | |
| `Stat Total` | `<Movers>` 24 pt navy, then "People who changed office" 11 pt slate | |
| `Stat Within` | `<Movers Within>` 24 pt violet `#5B4FB3`, then "Within one country" | |
| `Stat Across` | `<Movers Across>` 24 pt coral `#E4572E`, then "Across a border" | |

Hide the titles, set the sheet background to none, **Fit: Entire View**. Expected Company FY26: 345, 227, 118.

### Sheet `Top Corridors`

The map is only 490 wide, so the room beside it holds a ranked list of the biggest routes. Data source Office Moves.

```
// Top Corridor  (Boolean table calculation, computed along Corridor)
RANK_UNIQUE([Movers]) <= 8 AND [Movers] > 0
```

1. **Corridor** to **Rows**, **Movers** to **Columns**.
2. Drag **Top Corridor** to **Filters**, select **True**. (A table-calculation filter runs last, so the eight are the top eight inside the current selection. A plain Top N filter would rank before **Move In Scope** applies.)
3. Sort **Corridor** descending by **Movers**.
4. **flow_scope_label** to **Color**, same colors as the map: *Within one country* `#5B4FB3`, *Across a border* `#E4572E`. A corridor is either one or the other, so each bar has one color.
5. Label the end of each bar with **Movers** (10 pt navy). Hide the Movers axis, gridlines, zero lines and borders; keep the Corridor labels (10 pt slate). Sheet background none.
6. Title shown, text "Biggest routes", 11 pt bold slate. **Fit: Entire View**.

Expected Company FY26: Bengaluru to Hyderabad 28, Hyderabad to Bengaluru 25, Bengaluru to Pune 19 at the top. With p_View Office and p_Group Bengaluru, every bar starts or ends at Bengaluru.

## 5. Place on the dashboard (Summary, 1400 x 850)

Items inside a layout container are tiled, not free-floating, so the panel is one floating container with the pieces nested in it. Sizes come from the design sketch (panel card 240, 512, 1104 x 306; the toggle floats at 1124, 524, 220 x 30).

```
Panel: Office moves                  floating, x 252, y 530, w 1080, h 280, no background
|-- Panel header                     vertical, w 1080, h 44
|     |-- Office Moves Title         h 24
|     `-- Office Moves Subtitle      h 20
`-- Panel body                       horizontal, w 1080, h 236
      |-- Office Moves Map           w 490, h 236
      |-- Top Corridors              w 290, h 236
      `-- Panel stats                vertical, w 300, h 236, outer padding left 20
            |-- Stat Total           h 62
            |-- Stat Within          h 62
            `-- Stat Across          h 62
```

Build it:

1. **Container.** From the dashboard Objects list, drag a **Vertical** container onto the dashboard with **Floating** selected. In the **Layout** pane set Position x 252, y 530, size 1080 x 280, Background None. Rename it `Panel: Office moves` (item menu, **Rename Dashboard Item**).
2. **Header.** Drag a second **Vertical** container into it, drop it at the top, size 1080 x 44. Drag `Office Moves Title` (h 24) and `Office Moves Subtitle` (h 20) into it.
3. **Body.** Drag a **Horizontal** container below the header, size 1080 x 236. Drag `Office Moves Map` into it and set its size to 490 x 236 (the offices' shape; a wider container only adds blank sides).
4. **Top corridors.** Drag `Top Corridors` into the body to the right of the map (290 x 236).
5. **Stats.** Drag a **Vertical** container to the right of that inside the body (300 x 236, outer padding left 20). Drag the three stat sheets into it, 62 high each.
6. In the Layout pane, set every container's **Background** to **None** and **Border** to **None**.
7. **Toggle.** Add it after the container as a floating item so it sits on top, at 1124, 524, 220 x 30. It stays outside the container, so it is still visible when the panel is hidden.

Titles are 500 wide, so the container's empty top right stays free for the toggle. Positions are within a couple of pixels of the sketch.

## 6. Check that it follows every filter

1. FY26, Company: 345 / 227 / 118, 143 lines.
2. p_View Office, p_Group Bengaluru: 93 people, lines only from or to Bengaluru; the subtitle reads "Moves in or out of Bengaluru".
3. p_View Country, p_Group India: 136, 91, 45.
4. p_View Function, p_Group Technology: 147.
5. Pick a month-over-month pair: counts shrink to a handful of lines; no blank sheet and no error.
6. A group with no moves in the period: the title shows the empty-state message, the stats show 0.
