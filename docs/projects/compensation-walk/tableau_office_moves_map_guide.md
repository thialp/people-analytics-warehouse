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

// Top Route Movers   (people on the busiest route in the current selection)
{ MAX({ FIXED [Corridor] : SUM(IF [Move In Scope] THEN [workers] END) }) }

// Top Route
{ MAX(IF { FIXED [Corridor] : SUM(IF [Move In Scope] THEN [workers] END) } = [Top Route Movers]
      THEN [Corridor] END) }

// Moves Title   (map header; the busiest route moved to the Top 5 routes card, 2026-10-10)
IF [Movers] = 0 THEN "No one in this selection changed office in this period"
ELSEIF [Movers] = 1 THEN "One person changed office"
ELSE STR([Movers]) + " people changed office; "
     + STR(ROUND(100 * [Movers Within] / [Movers], 0)) + "% stayed inside one country" END
// Planned: add "1.2% of headcount" once the SQL carries opening headcount (345 / 28,436 = 1.2%)

// Routes Subtitle   (Top 5 routes card, two lines)
// ATTR() turns the two fixed (LOD) values into aggregates, so they can sit beside Movers
IF [Movers] = 0 THEN "" ELSE
ATTR([Top Route]) + " leads, " + STR(ATTR([Top Route Movers]))
+ IF ATTR([Top Route Movers]) = 1 THEN " person" ELSE " people" END
+ CHAR(10) + "People who changed office, by route" END

// Tooltip calcs for the routes card
// All Moves   (non-aggregate, whole selection)
{ SUM(IF [Move In Scope] THEN [workers] END) }
// Corridor Share
[Movers] / ATTR([All Moves])
// Office Pair   (same key for A to B and B to A)
IF [from_office] < [to_office] THEN [from_office] + " ↔ " + [to_office]
ELSE [to_office] + " ↔ " + [from_office] END
// Pair Movers
{ FIXED [Office Pair] : SUM(IF [Move In Scope] THEN [workers] END) }
// Opposite Movers
ATTR([Pair Movers]) - [Movers]

// Route Class   (aggregate; colors the lines: one-person border crossings are drawn lighter)
IF ATTR([flow_scope]) = "Domestic" THEN "Within one country"
ELSEIF [Movers] >= 2 THEN "Across a border"
ELSE "Across a border, one person" END

// Office Label   (layer 2; names the 5 offices that received the most people; compute using to_office)
IF RANK_UNIQUE([Movers]) <= 5 THEN ATTR([to_office]) + " " + STR([Movers]) END

// Moves Scope   (prefix for the subtitle; empty for the whole company)
IF [p_View] = "Company" THEN "" ELSE [p_Group] + ": " END

// (Top Region Movers and Top Region were for the retired Region Moves sheet; delete them)
```

`Movers`, `Movers Within` and `Movers Across` filter inside the calculation, not on the Filters shelf, so a selection with no moves shows 0 and the message instead of a blank sheet.

## 3. Sheet `Office Moves Map`

1. Double-click **Move Line**. A map appears with lines (Tableau adds *Latitude (generated)* and *Longitude (generated)*).
2. Drag **Move In Scope** to **Filters**, select **True**.
3. Marks (layer 1, `Move Line`): mark type **Automatic** (not Line: the Line type joins the marks into one connecting path and the sheet zigzags; Automatic draws each corridor as its own arc, curved along the shortest route over the globe). **Corridor** to **Detail**. **SUM(workers)** to **Size**. **Route Class** to **Color**: *Within one country* `#5B4FB3`, *Across a border* `#E4572E`, *Across a border, one person* `#F2A68C`. Color opacity 70%.
   - **Why three colors:** in FY26, 99 of the 143 routes carry a single person, and 87 of those cross a border. Drawing them in the pale coral from the brand ramp turns the long tail into background texture and leaves the real corridors (28, 25, 19 people) to stand out, without hiding anyone.
   - **Thin lines:** Size slider on the Marks card to the far left. If 28 people is not clearly thicker than 1, open the Size legend (**Analysis > Legends > Size**), **Edit Size**, and drag the upper handle until Bengaluru to Hyderabad is about 5 px.
4. Drag **Arrival Point** onto **Add a Marks Layer**. Layer 2: mark type **Circle**, **to_office** to **Detail**, **SUM(workers)** to **Size** (people who arrived at the office), color teal `#00938D`, opacity 85%, **Border** white. Size legend, **Edit Size**: smallest dot about 5 px, Pune (39 arrivals) about 24 px, so the dots read as how many people an office received. **Office Label** to **Label** (compute using `to_office`), 9 pt bold navy, tick no overlap, so only the 5 busiest offices are named.
5. Layer order on the Marks card: Arrival Point on top, Move Line below.
6. **Background that matches the card.** The Light style paints the ocean pure white (`#FFFFFF`) and the land `#F4F4F4`; the page is `#F3F3EF` and a card is `#FBFBF8`, so a Light map shows as a white box on the card. Fix it on the sheet: **Map > Map Layers**, untick **Base** (leaves a flat background), tick **Coastline** and **Country/Region Borders**; **Format > Shading > Worksheet: None**, so the card's fill shows through. If the outline-only look is too faint, fall back to Light with white cards (`make_kpi_cards_bg.py --fill FFFFFF` and white container fills).
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

## 4. Title and subtitle sheets (each with no dimension on the view)

| Sheet | Text | Notes |
|---|---|---|
| `Office Moves Title` | `<Moves Title>` bold 12 pt navy | The story, and the empty-state message |
| `Office Moves SubTitle` | `<Moves Scope>` `<Movers>` " people changed office · " `<Movers Within>` " within one country · " `<Movers Across>` " across a border" · "dots mark where people arrived" | 9 pt. One text mark, formatted in runs: slate for scope, count and "people changed office"; **violet `#5B4FB3`** for the within-country run; **coral `#E4572E`** for the across-a-border run. The colored words are the key to the map, the routes and the region bars, so the panel needs no legend |

Hide the titles, set the sheet background to none, **Fit: Entire View**. Expected Company FY26 subtitle: "345 people changed office · 227 within one country · 118 across a border"; title: "345 people changed office; 66% stayed inside one country". The three `Stat` sheets are no longer used: delete them.

### Pattern: the name above each bar (used by `Top Corridors` and `Region Headcount`)

Tableau has no setting that puts a label above a bar, so the name is carried by a second, invisible mark in a row of its own. The recipe is the dual-axis `AVG(0)` trick ([Data School, Stanley Chan](https://thedataschool.co.uk/stanley-chan/add-a-label-above-every-horizontal-bar-in-tableau); same steps in [InterWorks](https://interworks.com/blog/2021/08/25/advance-with-assist-adding-field-names-above-bars-on-a-bar-chart/)). `<name>` is `Corridor` or `to_region`; `<value>` is the measure of that sheet.

1. `<name>` to **Rows**, `<value>` to **Columns**. Mark type **Bar**.
2. Double-click the empty space to the right of the `<value>` pill on Columns, type `AVG(0)` and press Enter. A second pill, `AGG(AVG(0))`, appears.
3. Right-click `AGG(AVG(0))` on Columns, **Dual Axis**. Then right-click the top axis, **Synchronize Axis**. The Marks card now has three tabs: **All**, `<value>`, `AGG(AVG(0))`.
4. On the **All** tab, **Measure Names** sits on Color. Drag it to **Rows**, to the right of `<name>`. (If it is not there, drag **Measure Names** from the bottom of the Dimensions list.) Each bar now has a second row.
5. The dummy row must be **above** the bar. If it is below: right-click the **Measure Names** pill, **Sort**, **Manual**, and move `AGG(AVG(0))` above `<value>`.
6. **`AGG(AVG(0))` tab:** mark type **Gantt Bar**, Size slider to the far left (zero), Color opacity 0%. Drag `<name>` from the Dimensions list in the data pane (not from Rows) onto **Label**. Click **Label**: Alignment horizontal **Left**, vertical **Middle**; font Tableau Book 10 pt slate `#5A6170`; **Options**: tick *Allow labels to overlap other marks*. If the text is centered on the zero line and half of it hangs off the left, Alignment is not set to Left.
7. Hide the headers: right-click `<name>` and **Measure Names** on Rows, untick **Show Header**; right-click each axis, untick **Show Header**.
8. **Format**, **Lines**: Row Divider, Grid Lines and Zero Lines all **None**. Sheet background none.
9. **`<value>` tab:** Size slider to about 40%, so a bar is about 10 px thick in a row about 20 px high.

With 5 names on a 224 px sheet, each name gets about 40 px: 20 for the name, 20 for the bar. Fit: **Entire View**.

### Sheet `Top Corridors` (top 5, name above the bar)

Five routes, one per region bar next door, so the two charts have the same number of rows. Data source Office Moves.

```
// Top Corridor  (Boolean table calculation, computed along Corridor)
RANK_UNIQUE([Movers]) <= 5 AND [Movers] > 0
```

1. Build the pattern above with `<name>` = **Corridor** and `<value>` = **Movers**.
2. Drag **Top Corridor** to **Filters**, select **True**. A table-calculation filter runs last, so the five are the top five inside the current selection (a plain Top N filter would rank before **Move In Scope** applies). Right-click the pill, **Edit Table Calculation**, **Compute using: Specific Dimensions**, tick `Corridor` and `flow_scope_label`; leave **Measure Names** unticked.
3. **Movers** tab: **flow_scope_label** to **Color**, same colors as the map: *Within one country* `#5B4FB3`, *Across a border* `#E4572E`. A corridor is either one or the other, so each bar has one color. **Movers** to **Label**, bar end, 10 pt bold navy.
4. Sort **Corridor** descending by **Movers** (right-click the header before hiding it, **Sort**).
5. Title shown: line 1 "Top 5 busiest routes" (11 pt bold navy), line 2 `<AGG(Routes Subtitle)>` (9 pt gray; drag `Routes Subtitle` to Detail first). FY26: "Bengaluru to Hyderabad leads, 28 people" / "People who changed office, by route".
6. Tooltip (put `Corridor Share`, `Pair Movers`, `Opposite Movers`, `flow_scope_label` on Detail):
   ```
   <ATTR(Corridor)>
   <ATTR(flow_scope_label)>
   People who moved: <SUM(Movers)> (<AGG(Corridor Share)> of all office moves)
   In the opposite direction: <AGG(Opposite Movers)> people
   Both directions: <ATTR(Pair Movers)> people
   ```
   FY26 Bengaluru to Hyderabad: 28 people, 8.1% of 345, 25 the other way, 53 both ways.
7. Count labels: the reference-line label gets a gray box behind it. Format it (right-click the label, Format) with Shading None, or put `SUM(Movers)` on the bar's Label and delete the reference line.

Expected Company FY26: Bengaluru to Hyderabad 28, Hyderabad to Bengaluru 25, Bengaluru to Pune 19, Hyderabad to Pune 13, Warsaw to Krakow 12. With p_View Office and p_Group Bengaluru, every route starts or ends at Bengaluru.

Option (the tooltip now shows both directions; the chart still counts one direction): count each pair of offices once, in both directions, as the Figma prototype does (`IF [from_office] < [to_office] THEN [from_office] + " ↔ " + [to_office] ELSE [to_office] + " ↔ " + [from_office] END`). FY26 would read Bengaluru ↔ Hyderabad 53, Bengaluru ↔ Pune 22, Krakow ↔ Warsaw 17, Hyderabad ↔ Pune 16, Guadalajara ↔ Mexico City 16.

### Sheet `Region Headcount` (replaces `Region Moves`, 2026-10-10)

The card compares **closing with opening headcount by region**, so it ties to the KPI cards (28,436 to 30,015). It uses the **walk** data source (`ArcadiaHR`, the Country-view rows; `group_parent` is the region), not Office Moves, and follows Period but ignores View and Group (always the company by region). `Region Moves` (arrivals by region, within or across a border) and its `Moved People` calc are retired. The old build is in git history (commit before 2026-10-10).

Calculations (walk source; the date columns are `from_month_end` and `to_month_end`):

```
// In Period
[from_month_end] = [p_From] AND [to_month_end] = [p_To]

// Open HC / Close HC
SUM(IF [view_name]="Country" AND [In Period] AND [step]="Opening" THEN [headcount] END)
SUM(IF [view_name]="Country" AND [In Period] AND [step]="Closing" THEN [headcount] END)

// Growth %
([Close HC] / [Open HC]) - 1
// Net Change
[Close HC] - [Open HC]
// Share of Growth
[Net Change] / (ATTR([Tot Close]) - ATTR([Tot Open]))

// Tot Open / Tot Close   (company totals)
{ FIXED : SUM(IF [view_name]="Country" AND [In Period] AND [step]="Opening" THEN [headcount] END) }
{ FIXED : SUM(IF [view_name]="Country" AND [In Period] AND [step]="Closing" THEN [headcount] END) }

// Tot Open Text   (copy for Tot Close Text)
IF ATTR([Tot Open]) >= 1000
THEN STR(INT(ATTR([Tot Open]) / 1000)) + "," + RIGHT("00" + STR(INT(ATTR([Tot Open])) % 1000), 3)
ELSE STR(INT(ATTR([Tot Open]))) END
// Tot Growth Text
(IF ATTR([Tot Close]) >= ATTR([Tot Open]) THEN "+" ELSE "−" END)
+ STR(ROUND(ABS(100 * (ATTR([Tot Close]) - ATTR([Tot Open])) / ATTR([Tot Open])), 1)) + "%"

// Region Subtitle   (two lines)
"Arcadia overall " + [Tot Growth Text] + " (" + [Tot Open Text] + " | " + [Tot Close Text] + ")"
+ CHAR(10) + "Region: opening | closing headcount · bar: growth"
```

Sheet: the name-above-bar pattern with `<name>` = `group_parent` and `<value>` = `Growth %`. Name row label `<group_parent>   <SUM(Open HC)> | <SUM(Close HC)>` (name 9 pt navy, the two numbers 9 pt gray; the pills carry the `#,##0` format). Bar end label only the percent, format `+0.0%;−0.0%`. Bars teal `#00938D`, sorted descending by `Growth %`. Title "Growth by region" (11 pt bold navy), line 2 `<AGG(Region Subtitle)>` (9 pt gray). The bars come out nearly the same length (5.0% to 6.1% in FY26): that is the finding, growth was broad-based, and a zero-based bar shows it honestly.

Tooltip (put `Open HC`, `Close HC`, `Net Change`, `Growth %`, `Share of Growth` on Detail):

```
<group_parent>
Opening headcount: <SUM(Open HC)>
Closing headcount: <SUM(Close HC)>
Net change: <SUM(Net Change)> people (<AGG(Growth %)>)
<AGG(Share of Growth)> of Arcadia's net growth
```

Check FY26: closing counts 10,187 / 9,803 / 6,638 / 2,287 / 1,100 add to 30,015; opening adds to 28,436; company +5.6%. Regions in the build: North America +5.7%, Asia Pacific +5.2%, Europe +6.0%, Latin America +5.0%, Middle East & Africa +6.1%; North America added the most people (+546).

Do not add `p_View` or `p_Group` filters to this sheet.

## 5. Place on the dashboard (Summary, 1400 x 850)

One spacing system: a **30 px frame** between the rail and the cards, between the cards and the right edge, and below the last card; **16 px** between cards, across and down; **16 px** padding inside every card. Every card edge lands on the KPI card grid (cards at x 246, 474, 702, 930, 1158, each 212 wide), so the rows line up. Full table: `design/README.md`.

| Card | x | y | w | h | Spans |
|---|---:|---:|---:|---:|---|
| KPI cards x5 | 246 + 228 n | 88 | 212 | 86 | |
| Waterfall | 246 | 190 | 668 | 314 | KPI cards 1 to 3 (right edge 914) |
| Top drivers | 930 | 190 | 440 | 314 | KPI cards 4 and 5 |
| Panel (map) | 246 | 520 | 1124 | 300 | KPI cards 1 to 5 (right edge 1370, bottom 820) |

**One card color.** Every card is filled `#FBFBF8` with a 1 px `#E4E3DD` border, KPI cards included. Until 2026-10-10 the waterfall, Top drivers and panel containers had no fill (page color `#F3F3EF`), the KPI cards were `#FBFBF8` and the Light map was `#FFFFFF`: three different whites. Set each container's Background to `#FBFBF8` (Layout pane) and every sheet inside it to background None.

Items inside a layout container are tiled, not free-floating, so the panel is one floating container with the pieces nested in it.

```
Panel: Office moves                  floating, x 246, y 520, w 1124, h 300, background card, padding 16
|-- Panel header                     vertical, w 1092, h 44
|     |-- Office Moves Title         h 24
|     `-- Office Moves SubTitle      h 20
`-- Panel body                       horizontal, w 1092, h 224
      |-- Office Moves Map           w 520, h 224
      |-- Top Corridors              w 270, h 224
      `-- Region Headcount           w 270, h 224
```

520 + 270 + 270 + 2 x 16 = 1092 = 1124 - 2 x 16. Gaps are 16 px, the same as the rest of the page (the first build had about 6 px between map and routes). Both bar sheets use the same title block (11 pt bold line plus a two-line 9 pt subtitle) so their bars start on the same line as the map's top edge; tops and bottoms all match.

Build it:

1. **Container.** Floating **Vertical** container, Layout pane position x 246, y 520, size 1124 x 300. Rename it `Panel: Office moves`. Background `#FBFBF8`, border 1 px `#E4E3DD`, inner padding 16 on all sides (this is the card, so no separate card object).
2. **Header.** A **Vertical** container at the top, 1092 x 44, holding `Office Moves Title` (h 24) and `Office Moves SubTitle` (h 20).
3. **Body.** A **Horizontal** container below it, 1092 x 224, holding `Office Moves Map` (520), `Top Corridors` (270) and `Region Headcount` (270). Remove the old stats container. Set the body and header containers' background and border to **None**.
4. **Toggle.** A floating item after the container, so it sits on top: x 1134, y 534, 220 x 30 (inside the card's top right; the title stays under 870 px wide).
5. Remove the color legend Tableau adds to the dashboard, if it came back.

## 6. Check that it follows every filter

1. FY26, Company: 345 / 227 / 118, 143 lines.
2. p_View Office, p_Group Bengaluru: 93 people, lines only from or to Bengaluru; the subtitle reads "Moves in or out of Bengaluru".
3. p_View Country, p_Group India: 136, 91, 45.
4. p_View Function, p_Group Technology: 147.
5. Pick a month-over-month pair: counts shrink to a handful of lines; no blank sheet and no error.
6. A group with no moves in the period: the title shows the empty-state message, the subtitle shows 0 and the two bar charts are empty.
