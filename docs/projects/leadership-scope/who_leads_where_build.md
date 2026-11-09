# Who Leads Where: build, check and publish

This page takes case study 7 from the warehouse to Tableau Public. A script writes the whole workbook: 92 worksheets, one 1400 × 850 dashboard in a light and a dark theme, and 180 actions. You give it a base workbook that holds only the connection, and you check its numbers against the tables below. Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.

Before this page: the release 7 tables are built on SQL Server and `18_validate_leadership_scope.sql` passes (`sql_server_release_7_run.md`).

## Contents

1. What you need
2. Make the base workbook
3. Install the shapes and the card pictures
4. Build the workbook
5. Open it in Tableau
6. Check the numbers
7. Click tests
8. Publish to Tableau Public
9. How the workbook works
10. When something goes wrong

---

## 1. What you need

| Item | Where |
|---|---|
| The repository, on the release branch | `~/GitHub/people-analytics-warehouse` |
| Python 3.9 or later (the builder uses only the standard library; the picture scripts need Pillow) | `python3 --version` |
| Tableau Desktop 2026.2 or later | |
| SQL Server running with `ArcadiaHR` built (release 7) | `docker start arcadia-sql` |
| Dashboard #4's workbook. It supplies the document-format manifest that Tableau needs for parameter actions and rounded corners | `…/tableau/4 Contingent Workforce Reconciliation/Arcadia CW Reconciliation.twb` |
| The Arcadia logos, light and dark | `…/tableau/Shared/Brand/arcadia_logo_horizontal.png` and `arcadia_logo_horizontal_reverse.png` |

In this page `…` stands for `~/Documents/Claude/Professional Portfolio`.

## 2. Make the base workbook

The builder writes everything except the connection. Tableau makes the connection, once:

1. Open Tableau Desktop. Go to **Connect › To a Server › Microsoft SQL Server** and enter:
   - server `localhost`;
   - database `ArcadiaHR`;
   - **Use a specific username and password**, user `sa`, and the password from `docker exec arcadia-sql printenv MSSQL_SA_PASSWORD`.

   Tick **Trust Server Certificate** if Tableau offers it.
2. Drag **New Custom SQL** to the canvas. Paste the whole of `tableau/custom_sql_who_leads_where.sql`, then click **OK**.
3. Switch the connection to **Extract**. Go to **Sheet 1** and save the extract next to the workbook.
4. Save as `…/tableau/7 Who Leads Where/who_leads_where.twb` and close Tableau.

The extract should hold 707,236 rows:

| row_type | Rows | Feeds |
|---|---:|---|
| Node | 10,518 | headline, KPIs, rail, picker, toggles, alignment totals, tree counts (leader × All / Employees / Contingent) |
| Tree | 255,219 | the tree: circles (`mark_type` Node) and 17-point link curves (`mark_type` Link). Dynamic: one tree for the whole company (63,091 rows). Static: three levels below every leader as the focus (192,128) |
| Day | 300,359 | "At work": leader × worker type × the report date and the 30 days after it |
| Signal | 14,119 | the alignment panel: each person with a gap, once under every leader above them |
| R1 | 7 | role assignments still naming a former leader |
| Pulse | 127,014 | the Team pulse: leader × worker type × the 13 month-ends to the report date (people, gaps, people in their function's hubs), plus the week's dip day, its public holiday and the lightest team |

Only remake the base when the Custom SQL changes. A data refresh needs **Data › Refresh Extract** in the built workbook, nothing more.

## 3. Install the shapes and the card pictures

**Shapes.** The toggles, buttons, dots and brand tiles are 52 PNG shapes, a light and a dark copy of each. The repository holds them in `tableau/builder/d7/shapes/`:

```bash
mkdir -p ~/Documents/"My Tableau Repository"/Shapes/"Arcadia D7"
cp ~/GitHub/people-analytics-warehouse/tableau/builder/d7/shapes/*.png ~/Documents/"My Tableau Repository"/Shapes/"Arcadia D7"/
ls ~/Documents/"My Tableau Repository"/Shapes/"Arcadia D7" | wc -l
```

Expected: `52`. Restart Tableau if it was open, because it reads the shapes folder at startup.

To redraw them (to change a color, for example), run the script below. It needs Pillow (`pip3 install pillow`) and the Inter font:

```bash
D7_FONTS=~/Library/Fonts python3 tableau/builder/d7/make_shapes_d7.py ~/Documents/"My Tableau Repository"/Shapes/"Arcadia D7"
```

Expected: `wrote 52 shapes to …`. The Workforce and Tree counts toggles have no track of their own: the dashboard container draws one smooth track behind them, so the segments never show a seam.

**Card pictures.** The five KPI cards and the six Team pulse tiles are pictures under two map sheets (section 9). Draw them, light and dark, into the workbook's `Images` folder:

```bash
python3 tableau/builder/d7/make_cards_d7.py ~/Documents/Claude/"Professional Portfolio"/tableau/"7 Who Leads Where"/Images
```

Expected: `wrote 4 pictures to …` (`d7_kpi_cards_l.png`, `d7_kpi_cards_d.png`, `d7_pulse_tiles_l.png`, `d7_pulse_tiles_d.png`).

## 4. Build the workbook

Close the workbook in Tableau first, so that Tableau does not save over the new file. Then:

```bash
cd ~/GitHub/people-analytics-warehouse
P=~/Documents/Claude/"Professional Portfolio"/tableau
D4_TWB="$P/4 Contingent Workforce Reconciliation/Arcadia CW Reconciliation.twb" \
D7_BRAND="$P/Shared/Brand/" \
D7_IMAGES="$P/7 Who Leads Where/Images/" \
python3 tableau/builder/d7/build_d7.py "$P/7 Who Leads Where/who_leads_where.twb" "$P/7 Who Leads Where/Who Leads Where.twb"
```

Expected: `calcs 422 sheets 92 zones 29 actions 180 (84 parameter)`. "zones" counts the floating items: each card is one container with its items tiled inside.

The builder reads the shape file names from `tableau/builder/d7/shapes/`. Pass `D7_SHAPES=<folder>` to use another folder. `D7_CALIB=1` adds a magenta dot on each KPI card's left edge, to check the map alignment (section 9); never publish a calibration build.

## 5. Open it in Tableau

Open `Who Leads Where.twb`. If Tableau asks to run the Custom SQL, answer **Yes**. The page opens on Grace Ramsey (CEO), in the Dynamic tree, All, Everyone, today, light theme, with no popover open.

To reload after a build, use **File › Close** and choose **Don't Save**, then open the workbook again. Never press **Save** between a build and a reload: Tableau would write its in-memory copy over the new build.

## 6. Check the numbers

Every value in the first four tables comes from `python3 tableau/builder/d7/check_values.py`, computed from the marts the way the page reads them. `--verify` checks the closures:
- All = Employees + Contingent for every leader;
- people = directs + indirects (executive officers excluded);
- at work + off = people on every weekday;
- the ties to the other dashboards.

```bash
python3 tableau/builder/d7/check_values.py --verify
```

Expected: `3506 leaders, 300359 leader-days; problems: 0`.

To reach each leader, click the rail's **Organization** box and pick the name in the picker (Marcus Carter › Isaac Holland; Marcus Carter › Maria Barnes; Isaac Holland › Daniela Guerra).

### Headline and KPIs (All)

| Leader | Headline | People led | At work today | Layers below | Median span | Alignment gaps |
|---|---|---:|---:|---:|---:|---:|
| Grace Ramsey (CEO) | Grace Ramsey leads 41,934 people. 2,057 (4.9%) show an alignment gap. | 41,934 (8 directs · 41,934 indirect) | 37,972 (3,962 off) | 8 | 10 (666 lead 15+ · 7 lead one) | 2,057 (1,206 solid · 876 matrix) |
| Isaac Holland (L1) | Isaac Holland leads 13,248 people. 866 (6.5%) show an alignment gap. | 13,248 (12 directs · 13,236 indirect) | 12,004 (1,244 off) | 6 | 12 (317 lead 15+ · 0 lead one) | 866 (693 solid · 183 matrix) |
| Maria Barnes (L1) | Maria Barnes leads 5,884 people. 168 (2.9%) show an alignment gap. | 5,884 (4 directs · 5,880 indirect) | 5,351 (533 off) | 5 | 14 (176 lead 15+ · 0 lead one) | 168 (22 solid · 146 matrix) |
| Daniela Guerra (L2) | Daniela Guerra leads 2,905 people. 254 (8.7%) show an alignment gap. | 2,905 (13 directs · 2,892 indirect) | 2,642 (263 off) | 5 | 13 (75 lead 15+ · 0 lead one) | 254 (215 solid · 44 matrix) |

The CEO's 8 directs are the function heads. They are executive officers: they lead, but stay out of every people count, as on Dashboards #1 to #6, so her 41,934 people are all indirect. Solid and matrix can add to more than the total, because one person can carry both kinds of gap. The headline names no countries: the page reads location as function hubs (the Team pulse's In the hub tile).

### The worker toggle (people led / at work today / alignment gaps)

| Leader | All | Employees | Contingent |
|---|---|---|---|
| Grace Ramsey | 41,934 / 37,972 / 2,057 | 30,005 / 26,862 / 1,915 | 11,929 / 11,110 / 142 |
| Isaac Holland | 13,248 / 12,004 / 866 | 8,101 / 7,198 / 838 | 5,147 / 4,806 / 28 |
| Maria Barnes | 5,884 / 5,351 / 168 | 3,397 / 3,026 / 91 | 2,487 / 2,325 / 77 |
| Daniela Guerra | 2,905 / 2,642 / 254 | 1,851 / 1,655 / 245 | 1,054 / 987 / 9 |

30,005 employees is the number on every published dashboard, and the page footnote reads "Arcadia Systems is fictional; all data is synthetic. 41,934 people on Jun 30, 2026: 30,005 employees and 11,929 contingent workers." Contingent workers are 11,941 in Bridgeway; 12 of them have no manager employed on the report date, so they sit outside every tree.

### Org design alignment panel (All)

| Signal | Grace Ramsey | Isaac Holland | Maria Barnes | Daniela Guerra |
|---|---:|---:|---:|---:|
| Budgeted in another org | 258 | 112 | 22 | 10 |
| Role from another function | 958 | 584 | 3 | 205 |
| Country leader for another country | 42 | 14 | 2 | 3 |
| In two country matrices, or none | 19 | 1 | 4 | 0 |
| Matrix inactive or without a leader | 817 | 169 | 140 | 41 |
| Still naming a former leader (assignments) | 2 | 0 | 1 | 0 |

### Calendar, Isaac Holland (All)

Click the **Calendar** card in the rail.

| Day | At work | Of | Off (time off, leave, holiday) | Left the team |
|---|---:|---:|---|---:|
| Tue, Jun 30 | 12,004 | 13,248 | 1,244 (1,174, 70, 0) | 0 |
| Wed, Jul 1 | 11,574 | 13,239 | 1,665 (1,154, 63, 448) | 9 |
| Fri, Jul 3 | 9,660 | 13,215 | 3,555 (995, 53, 2,507) | 33 |
| Thu, Jul 30 | 12,035 | 12,899 | 864 (798, 66, 0) | 349 |

Under the calendar: "The quietest weekday is Fri, Jul 3: 9,660 at work." Saturdays and Sundays read "Weekend". The rail card shows the day and the number off: "Today · Tue, Jun 30" and "1,244 off".

### The rail's Organization box (All)

The CEO down to the leader on the page by name, then every level below them with its number of leaders. The subtitle counts the leader's directs.

| Leader | Subtitle | Rows |
|---|---|---|
| Grace Ramsey | 8 directs · click to open any leader | CEO Grace Ramsey · EXEC 8 executives · L1 20 leaders · L2 189 · L3 557 · L4 1,115 · L5 1,149 · L6 467 |
| Marcus Carter | 2 directs · click to open any leader | CEO Grace Ramsey · EXEC Marcus Carter · L1 2 leaders · L2 8 · L3 62 · L4 367 · L5 602 · L6 298 |

### Team pulse (All, read from the page)

| Tile | Grace Ramsey | Marcus Carter |
|---|---|---|
| Team coverage · today | 91%, 37,972 of 41,934 at work, Above the 85% floor | 91%, 17,357 of 19,134 at work, Above the 85% floor |
| The week (Tue–Mon) | 91 · 87 · 88 · **67** · 89% | 91 · 87 · 89 · **73** · 90% |
| Insight | Plan for Friday: coverage dips to 67% for Independence Day (observed), US. Barnes's team is lightest, at 50%. | Plan for Friday: coverage dips to 73% … Barnes's team is lightest, at 73%. |
| Team growth | +2,791 +7.1% vs Jun 2025 | +1,301 +7.3% |
| Renewals ahead | 2,495 · contingent · 1,972 this week | 1,094 · 717 this week |
| Contingent mix | 28% +1.1 pts · 11,929 of 41,934 people | 40% +0.9 pts · 7,634 of 19,134 people |
| Alignment trend | −301 −13% (teal: fewer gaps is good) | −258 −20% |
| Coaching capacity | 81% · managers leading 2 to 14 people | 63% |
| In the hub | 47% −1 pts (gold) · in their function's hubs | 51% −0.9 pts |

Gold marks a change in the unfavorable direction, teal a favorable one; both are pastel.

## 7. Click tests

Run these in Tableau Desktop, then again on Tableau Public after publishing.

| # | Do | Expect |
|---:|---|---|
| 1 | Open the page | Grace Ramsey, Dynamic tree: her eight executives below her, Carter (Marcus) the largest |
| 2 | Click Carter (Marcus) in the tree | His team grows out below him and the whole page moves to Marcus Carter (headline, KPIs, rail, Team pulse) |
| 3 | Click Holland, then Ramsey higher up | Down one level, then back up: everything below the clicked leader closes |
| 4 | **Static** | Three levels of leaders below the focus at once; clicking a circle opens that leader |
| 5 | **Employees**, then **Contingent**, then **All** | Every number follows the worker toggle table; the headline says "employees", "contingent workers", "people" |
| 6 | **At work** under Tree counts | Tree counts change to the number at work on the chosen day |
| 7 | Click the **Calendar** card, then Fri Jul 3 | The popover closes; AT WORK reads 9,660 for Isaac Holland; the card reads Fri, Jul 3 |
| 8 | Click the **Organization** box | The picker opens across the page: CEO and executives, then L1 to L6. Pick Marcus Carter, Maria Barnes, Diego Pacheco: each click opens that leader, the next column lists their leaders ("L3 · UNDER DIEGO PACHECO"), and the picker closes when you pick a leader with no leaders below |
| 9 | The **expand** button at the tree's top right | The tree fills the page width; the Team pulse hides; the button collapses it back |
| 10 | The **i** button in the Team pulse | The alignment rules popover; ✕ closes it |
| 11 | **Dark** | Every element changes to the dark palette (circles with a soft ring); **Light** brings it back |
| 12 | Hover a KPI card's value, a circle, a calendar day, a coverage bar | Detailed tooltips, with no `*` or `Null` anywhere. A KPI card's tooltip shows on its middle band (the big number) |
| 13 | Click a KPI card, a tile, a toggle | Nothing stays selected: every sheet has a Deselect action |
| 14 | GitHub and LinkedIn tiles in the rail | Open github.com/thialp and the LinkedIn profile |
| 15 | Timing | In Desktop (Nov 9): open about 10 s, a tree click about 12 s, light/dark about 9.5 s. Check again on Tableau Public |

## 8. Publish to Tableau Public

**Published 2026-11-09:** [Who Leads Where on Tableau Public](https://public.tableau.com/app/profile/thialp/viz/WhoLeadsWhereArcadiaSystems/WhoLeadsWhere).

1. In Tableau Desktop, right-click the **Who Leads Where** dashboard tab and choose **Hide All Sheets**. The 92 worksheets stay in the workbook, but only the dashboard shows.
2. Make sure the page is on Grace Ramsey, Dynamic, All, Everyone, today, Light, with no popover open. Tableau Public opens on the state you publish.
3. **File › Save to Tableau Public As…** and name it **Who Leads Where | Leadership Scope & Org Design | Arcadia Systems**. Tableau packages the extract, the shapes, the logos and the card pictures with it.
4. On the Tableau Public page:
   - turn off **Show Sheets as Tabs**;
   - add a description: "Who leads whom, how many people, where they sit, and where the records depart from the org design, with a daily Team pulse. A synthetic enterprise (Arcadia Systems) with 41,934 people, employees and contingent workers. Built from a SQL Server warehouse; code on GitHub.";
   - link the repository (`https://github.com/thialp/people-analytics-warehouse`).
5. Run the click tests (section 7) on Tableau Public.
6. Record the live link in this page, the case study README and the portfolio site.

The extract (707,236 rows) is well inside Tableau Public's limits. Parameter actions, Dynamic Zone Visibility, custom shapes, map layers and context filters all work on Tableau Public.

Tableau Cloud with row-level security (each leader sees only their own branch) and Pulse metrics are phase 8 of the release plan. The Team pulse tiles map to Pulse metrics, and the coverage floor to a Pulse threshold.

## 9. How the workbook works

**One data source, six row types.** The Custom SQL stacks six shapes of data (section 2) into one table with a `row_type` column. The page reads the focus leader's numbers with FIXED expressions, for example:

```
{FIXED : MAX(IF [row_type] = "Node" AND [leader_id] = [Focus ID] AND [worker_type] = [p_Worker] THEN [people] END)}
```

so that any sheet can show them, with no blend and no filter.

**Navigation is one parameter per click.** `p_Path` holds the chain from the CEO to the leader on the page (`|W100001|W100002|W100010|`), and the leader is its last id: `Focus ID` = `REGEXP_EXTRACT([p_Path], "([^|]+)[|]$")`. A tree click or a picker click sets `p_Path` only. These parameters drive the page:

| Parameter | What it holds |
|---|---|
| `p_Path` | the path to the leader on the page (and so the leader) |
| `p_Tree` | Dynamic or Static |
| `p_Worker` | the worker type |
| `p_Count` | Everyone or At work |
| `p_Day` | the day |
| `p_Dark` | the theme |
| `p_Zoom` | whether the tree is expanded |
| `p_PickOpen`, `p_CalOpen`, `p_RulesOpen` | which popover is open |

`p_B0` and `p_B1` (the old three-column picker's browse state) are still in the workbook but unused. 84 parameter actions set the parameters. 92 deselect actions, one per sheet, clear each selection right after a click, so a second click on the same mark fires again and no mark stays highlighted. Opening one popover closes the others; the picker stays open while the picked leader has leaders below (`Pick Keep Open` = `[child_leaders] > 0`).

**Every card is a container.** Each card is one floating layout container with its items tiled inside: the rail, the header, the tree card (normal and expanded), the Team pulse card and the three popovers. Light and dark, normal and expanded, and the popovers switch on those 23 containers with Dynamic Zone Visibility. The two exceptions float on purpose: each card picture, and its map sheet laid exactly on top of it.

**The KPI cards and the Team pulse tiles are map layers.** Each set is one worksheet, `KPI Map` and `Tiles Map`, instead of 5 and 18 sheets. Every title, value and note is a map label on an invisible point:
- `MAKEPOINT(lat, lon)` with `lon = (x - W/2) × 0.01 × 1.1` and `lat = -(y - H/2) × 0.01 × 1.1`, where x and y are pixels on the sheet. A map puts a point exactly where its coordinates say, so the text lands on its card.
- Two corner points mark the frame. Tableau pads a fitted map by about 5% on each side, so the corners, at the sheet edges in plain degrees, land about 55 px in from the edges, and the 1.1 stretches the content to fill the sheet.
- **Every mark must stay inside the corners' frame.** If one mark falls outside it, Tableau refits the map to the marks instead, and every text drifts by a growing amount (about 1.5% across the KPI row, 13 px by card 5). That is why the KPI sheet starts 60 px left of the first card (under the rail) and why card 5's hover line stops at the frame.
- A label lands about 5 px right of its point, so the KPI labels are aimed 5 px left (`CAL` in `build_d7.py`). `D7_CALIB=1` draws a dot on each card's left edge to check the alignment.
- Each KPI card's tooltip lives on one invisible thick line across the card's middle (`KPI pt Hover Line n`). Tableau caps a line at about 30 px, so the tooltip shows on the card's middle band.
- The tiles' sparklines are line layers with a path (13 month-ends, or 31 days for Renewals ahead), scaled between the leader's own minimum and maximum. The percentage bars are thick lines drawn through all 13 month rows, so they never break.
- The card pictures are drawn at 2x by `make_cards_d7.py` and float at their exact size. A picture tiled inside a container was shrunk to about 91%.

**Context filters for speed.** A FIXED expression reads every row that reaches it, so each sheet carries one context filter, which Tableau applies before any FIXED expression:

| Context | Rows kept | Sheets |
|---|---|---|
| Ctx Leaders | Node, Signal and R1 rows: about 12,600 | headline, rail, toggles, buttons, picker, alignment panel |
| Ctx Days | the focus leader's 31 Day rows for the chosen worker type | the Calendar card, the calendar and its summary |
| Ctx Tree | Dynamic: the company tree's rows whose manager is on the path, a few hundred of 63,091. Static: the focus's rows | the tree, normal and expanded |
| Ctx Pulse | the focus leader's Node rows, Day rows and Pulse rows | the KPI map, the Team pulse hero and the tiles map |

The context also says when the sheet can be seen. Each sheet's context is `[Ctx …] AND` its theme (`NOT [p_Dark]` or `[p_Dark]`), its popover (`[p_PickOpen]`, …), or the narrow or expanded tree (`[p_Zoom]`). Tableau refreshes every sheet on every click, hidden ones included. A hidden sheet's context is then FALSE, a parameter-only test folded before the query, so it compiles and returns nothing.

**Performance, measured (Help › Settings and Performance › Performance Recording, Nov 9).** Every click refreshes every sheet, about 45 ms each on the main thread. Compiling the queries takes about 2 s; Hyper runs them in under 2 s.

| In Desktop | 136 sheets (before) | 92 sheets (now) |
|---|---:|---:|
| Sheets refreshed per click | 133 | 91 |
| Open | ~17 s | ~10 s |
| Tree click | ~16–18 s | ~12 s |
| Light / dark | ~14 s | ~9.5 s |

The next step, if the page needs it, is one set of sheets for both themes (theme colors from calculations instead of duplicate sheets), which halves the sheets again.

**The tree, Dynamic: one company tree that grows.** The idea comes from The Information Lab's org chart with dynamic drill-down. Every leader has one fixed place: `tier` is the depth below the CEO, and a leader's child leaders sit one unit apart, biggest first, centered under them. Nothing moves when the focus changes, so a click grows the tree out of the leader instead of drawing a new picture, and the workbook's animation (switched on in its `<style>`) shows the move. What shows:

- a circle whose manager is on the path: the chain from the CEO to the focus, every leader of each of those levels, and the focus's own team (`Parent On Path` = `CONTAINS([p_Path], "|" + [parent_node_id] + "|")`);
- four rows at most: two levels above the focus, the focus's row and the team (`[tier] >= [F Depth] - 2`);
- labels on the path and the team; the other leaders of each level small (35% size) and unlabeled, named on hover.

Clicking anyone higher up the chain closes everything below them. The axes are automatic without zero (`domain-expand='false'`), so the view pans and zooms to what is on the page.

**The tree, Static:** three levels of leaders below the focus at once, on a 0 to 1 canvas; clicking a circle opens that leader, clicking the focus goes up one.

**Drawing it.** The tree is a dual axis on the same x (`X Plot`):
- **Lines:** the link curves, 17 points per link, drawn on `Y Link`.
- **Pies:** the circles, drawn on `Y Node`. The circle size is the people led; the amber slice is the share with an alignment gap. In dark mode every circle has a soft ring.

Each pie is three wedges:
- the Node row: people without a gap;
- points 15 and 16 of the link into the circle, each carrying half the gap.

Tableau labels a wedge at its middle angle. Splitting the gap around 12 o'clock centers the big wedge, and with it the leader's name, at 6 o'clock, straight below the circle. Point 15 is plotted at the circle's center (`X Plot`): a few pixels off and Tableau would draw the two halves as a second pie on top.

**The Team pulse.** A leader's morning read, in the shape of Tableau Pulse: value, change and trend, one insight, never a negative note.
- **Team coverage (hero):** the share at work today against an 85% floor (a Pulse threshold), the next five weekdays as bars (today teal, a day under the floor gold), and the day to plan for, its holiday and the lightest team.
- **Team growth:** people led against the same month-end a year ago.
- **Renewals ahead:** contingent assignments ending in the next 30 days, and this week.
- **Contingent mix:** the contingent share and its change in a year.
- **Alignment trend:** the change in people with a gap in a year.
- **Coaching capacity:** managers leading 2 to 14 people.
- **In the hub:** the share in one of their function's hubs (`ref_function_hub`, e.g. Technology: Austin, Bengaluru, Hyderabad, Pune, Warsaw, Krakow).

**The code.** In `tableau/builder/d7/`:

| File | What it does |
|---|---|
| `d7_calcs.py` | every calculation |
| `build_d7.py` | sheets, map layers, dashboard containers, actions and visibility |
| `make_shapes_d7.py` | the 52 shapes |
| `make_cards_d7.py` | the 4 card pictures |
| `check_values.py` | the check tables in section 6 |

The .twb writer is Dashboard #6's (`tableau/builder/d6/twb.py`).

## 10. When something goes wrong

| What you see | Why | Fix |
|---|---|---|
| "element 'column' not allowed" on open | Calculations placed after a group in the data source | Rebuild with the current `build_d7.py`; it places them before `<extract>` |
| Red pills, and the KPIs or headline blank | A row-level field on the Tooltip shelf without ATTR | Rebuild; the builder wraps tooltip-only fields in ATTR |
| Shapes show as default circles and squares | Tableau did not find `Shapes/Arcadia D7` | Step 3, then restart Tableau |
| Logos or card pictures missing | `D7_BRAND` or `D7_IMAGES` did not point at the folder (with a trailing `/`) | Steps 3 and 4 |
| KPI or tile texts drift off their cards | A mark outside the corners' frame (a new layer near an edge, or a larger hover mark) | Keep every mark about 55 px inside the sheet edges; build with `D7_CALIB=1` and check the dots sit on the card edges |
| The build is overwritten after a reload | Tableau saved its own copy | Build again; close with Don't Save, never Save |
| Numbers differ from section 6 | The extract is older than the warehouse | **Data › Refresh Extract**, then compare again |
| "Msg 156 … near the keyword 'Off'" in SQL Server | `Off` is reserved in T-SQL | Pull the latest `main`; the column is bracketed as `[off]` |
