# Who Leads Where: build, check and publish

This page takes case study 7 from the warehouse to Tableau Public. A script writes the whole workbook: 80 worksheets, one 1400 × 850 dashboard in a light and a dark theme, and 168 actions. You give it a base workbook that holds only the connection, and you check its numbers against the tables below. Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.

Before this page: the release 7 tables are built on SQL Server and `18_validate_leadership_scope.sql` passes (`sql_server_release_7_run.md`).

## Contents

1. What you need
2. Make the base workbook
3. Install the shapes
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
| Python 3.9 or later (the builder uses only the standard library) | `python3 --version` |
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

The extract should hold 580,222 rows:

| row_type | Rows | Feeds |
|---|---:|---|
| Node | 10,518 | headline, KPIs, rail, picker, toggles, alignment totals, tree counts (leader × All / Employees / Contingent) |
| Tree | 255,219 | the tree: circles (`mark_type` Node) and 17-point link curves (`mark_type` Link). Dynamic: one tree for the whole company (63,091 rows). Static: three levels below every leader as the focus (192,128) |
| Day | 300,359 | "At work on": leader × worker type × the report date and the 30 days after it |
| Signal | 14,119 | the alignment panel: each person with a gap, once under every leader above them |
| R1 | 7 | role assignments still naming a former leader |

Only remake the base when the Custom SQL changes. A data refresh needs **Data › Refresh Extract** in the built workbook, nothing more.

## 3. Install the shapes

The toggles, buttons, dots and brand tiles are 52 PNG shapes, a light and a dark copy of each. The repository holds them in `tableau/builder/d7/shapes/`:

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

Expected: `wrote 52 shapes to …`.

## 4. Build the workbook

Close the workbook in Tableau first, so that Tableau does not save over the new file. Then:

```bash
cd ~/GitHub/people-analytics-warehouse
P=~/Documents/Claude/"Professional Portfolio"/tableau
D4_TWB="$P/4 Contingent Workforce Reconciliation/Arcadia CW Reconciliation.twb" \
D7_BRAND="$P/Shared/Brand/" \
python3 tableau/builder/d7/build_d7.py "$P/7 Who Leads Where/who_leads_where.twb" "$P/7 Who Leads Where/Who Leads Where.twb"
```

Expected: `calcs 200 sheets 80 zones 263 actions 168 (84 parameter)`.

The builder reads the shape file names from `tableau/builder/d7/shapes/`. Pass `D7_SHAPES=<folder>` to use another folder.

## 5. Open it in Tableau

Open `Who Leads Where.twb`. If Tableau asks to run the Custom SQL, answer **Yes**. The page opens on Isaac Holland (L1, Software Engineering), in the Dynamic tree, light theme.

If the workbook is already open, use **File › Revert to Saved**, then click **Revert**, instead of closing it. Never press **Save** between a build and a revert: Tableau would write its in-memory copy over the new build.

## 6. Check the numbers

Every value below comes from `python3 tableau/builder/d7/check_values.py`, computed from the marts the way the page reads them. `--verify` checks the closures:
- All = Employees + Contingent for every leader;
- people = directs + indirects;
- at work + off = people on every weekday;
- the ties to the other dashboards.

```bash
python3 tableau/builder/d7/check_values.py --verify
```

Expected: `3506 leaders, 300359 leader-days; problems: 0`.

To reach each leader, open the rail's **Organization** box: click Grace Ramsey in the L0 column, then the L1 or L2 name.

### Headline and KPIs (All)

| Leader | Headline | People led | At work today | Layers below | Median span | Alignment gaps |
|---|---|---:|---:|---:|---:|---:|
| Grace Ramsey (L0) | Grace Ramsey leads 41,934 people in 22 countries. 2,057 (4.9%) show an alignment gap. | 41,934 (0 directs · 41,934 indirect) | 37,972 (3,962 off) | 8 | 10 (666 lead 15+ · 7 lead one) | 2,057 (1,206 solid · 876 matrix) |
| Isaac Holland (L1) | Isaac Holland leads 13,248 people in 22 countries. 866 (6.5%) show an alignment gap. | 13,248 (12 directs · 13,236 indirect) | 12,004 (1,244 off) | 6 | 12 (317 lead 15+ · 0 lead one) | 866 (693 solid · 183 matrix) |
| Maria Barnes (L1) | Maria Barnes leads 5,884 people in 22 countries. 168 (2.9%) show an alignment gap. | 5,884 (4 directs · 5,880 indirect) | 5,351 (533 off) | 5 | 14 (176 lead 15+ · 0 lead one) | 168 (22 solid · 146 matrix) |
| Daniela Guerra (L2) | Daniela Guerra leads 2,905 people in 22 countries. 254 (8.7%) show an alignment gap. | 2,905 (13 directs · 2,892 indirect) | 2,642 (263 off) | 5 | 13 (75 lead 15+ · 0 lead one) | 254 (215 solid · 44 matrix) |

The CEO shows 0 directs because her direct reports, the eight function heads, are executive officers: they lead, but stay out of every count, as on Dashboards #1 to #6. Solid and matrix can add to more than the total, because one person can carry both kinds of gap.

### The worker toggle (people led / at work today / alignment gaps)

| Leader | All | Employees | Contingent |
|---|---|---|---|
| Grace Ramsey | 41,934 / 37,972 / 2,057 | 30,005 / 26,862 / 1,915 | 11,929 / 11,110 / 142 |
| Isaac Holland | 13,248 / 12,004 / 866 | 8,101 / 7,198 / 838 | 5,147 / 4,806 / 28 |
| Maria Barnes | 5,884 / 5,351 / 168 | 3,397 / 3,026 / 91 | 2,487 / 2,325 / 77 |
| Daniela Guerra | 2,905 / 2,642 / 254 | 1,851 / 1,655 / 245 | 1,054 / 987 / 9 |

30,005 employees is the number on every published dashboard. Contingent workers are 11,941 in Bridgeway; 12 of them have no manager employed on the report date, so they sit outside every tree, and the CEO leads 11,929.

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

Open the **At work on** box in the rail.

| Day | At work | Of | Off (time off, leave, holiday) | Left the team |
|---|---:|---:|---|---:|
| Tue, Jun 30 | 12,004 | 13,248 | 1,244 (1,174, 70, 0) | 0 |
| Wed, Jul 1 | 11,574 | 13,239 | 1,665 (1,154, 63, 448) | 9 |
| Fri, Jul 3 | 9,660 | 13,215 | 3,555 (995, 53, 2,507) | 33 |
| Thu, Jul 30 | 12,035 | 12,899 | 864 (798, 66, 0) | 349 |

Under the calendar: "The quietest weekday is Fri, Jul 3: 9,660 at work." Saturdays and Sundays read "Weekend".

## 7. Click tests

Run these in Tableau Desktop, then again on Tableau Public after publishing.

| # | Do | Expect |
|---:|---|---|
| 1 | Open the page | Isaac Holland, Dynamic tree: the chain from the CEO (Grace Ramsey) through Marcus Carter (L0) to him, the other leaders of each level small and unlabeled, and his five L2 leaders below him |
| 2 | Click Guerra in the tree | One click: her team grows out below her and the whole page moves to Daniela Guerra (headline, KPIs, rail, alignment panel). The window keeps four rows, so the CEO scrolls off the top |
| 3 | Click Joshi (her largest team member) | Wei Joshi (manager, 1,245 people): Holland, Guerra and Joshi down the middle, his nine leaders below; labels of a team larger than four alternate between two heights |
| 4 | Click Guerra, then Holland, higher up the chain | Back up one click at a time: everything below the clicked leader closes |
| 5 | **Static** | Three levels of leaders below the focus at once; small circles at the third level carry no labels; clicking a circle opens that leader |
| 6 | **Employees**, then **Contingent**, then **All** | Every number follows the worker toggle table above; the headline says "employees", "contingent workers", "people" |
| 7 | **At work** under Show | Tree counts change to the number at work on the chosen day; tooltips say "at work" |
| 8 | Open **At work on**, click Fri Jul 3 | The popover closes; AT WORK reads 9,660 for Isaac Holland; the calendar box reads Fri, Jul 3 |
| 9 | Pick a Saturday | AT WORK reads "Weekend" and the note says nobody is scheduled |
| 10 | Open **Organization**, click an L0, then an L1, then an L2 name | The L1 and L2 columns follow each click; the L2 click opens that leader and closes the popover; the teal dot marks the current path |
| 11 | The **expand** button at the tree's top right | The tree fills the page width; the alignment panel hides; the button now collapses it back |
| 12 | The **i** button in the alignment panel | The rules popover with the six signals and the partner to ask; ✕ closes it |
| 13 | **Dark** | Every element changes to the dark palette, with no light sheet left showing; **Light** brings it back |
| 14 | Open one popover, then another | Only one popover is open at a time |
| 15 | Hover a circle, a KPI, a signal, a calendar day | Detailed tooltips, with no `*` or `Null` anywhere |
| 16 | GitHub and LinkedIn tiles in the rail | Open github.com/thialp and the LinkedIn profile |
| 17 | Timing | In Desktop a click takes about 10 seconds: the 78 queries finish in about 2 seconds; the rest is Desktop laying out the 263 dashboard zones (the light and dark copies). Check the time again on Tableau Public |

## 8. Publish to Tableau Public

1. In Tableau Desktop, right-click the **Who Leads Where** dashboard tab and choose **Hide All Sheets**. The 80 worksheets stay in the workbook, but only the dashboard shows.
2. Make sure the page is on Isaac Holland, Dynamic, All, Everyone, today, Light, with no popover open. Tableau Public opens on the state you publish.
3. **File › Save to Tableau Public As…** and name it **Who Leads Where: Leadership Scope & Org Design (Arcadia Systems)**. Tableau packages the extract, the shapes and the logos with it.
4. On the Tableau Public page:
   - turn off **Show Sheets as Tabs**;
   - add a description: "Who leads whom, how many people, where they sit, and where the records depart from the org design. A synthetic enterprise (Arcadia Systems) with 41,934 people, employees and contingent workers. Built from a SQL Server warehouse; code on GitHub.";
   - link the repository (`https://github.com/thialp/people-analytics-warehouse`).
5. Run the click tests (section 7) on Tableau Public.
6. Record the live link in this page, the case study README and the portfolio site.

The extract (580,222 rows) is well inside Tableau Public's limits. Parameter actions, Dynamic Zone Visibility, custom shapes and context filters all work on Tableau Public.

Tableau Cloud with row-level security (each leader sees only their own branch) and Pulse metrics are phase 8 of the release plan.

## 9. How the workbook works

**One data source, five row types.** The Custom SQL stacks five shapes of data (section 2) into one table with a `row_type` column. The page reads the focus leader's numbers with FIXED expressions, for example:

```
{FIXED : MAX(IF [row_type] = "Node" AND [leader_id] = [p_Focus] AND [worker_type] = [p_Worker] THEN [people] END)}
```

so that any sheet can show them, with no blend and no filter.

**Context filters for speed.** A FIXED expression reads every row that reaches it. Without help, each of the page's 35 or so queries scanned all 646,673 rows (the extract before the company tree), and a click took 20 to 30 seconds. Each sheet now carries one context filter, which Tableau applies before any FIXED expression:

| Context | Rows kept | Sheets |
|---|---|---|
| Ctx Leaders | Node, Signal and R1 rows: about 12,600 | headline, KPIs 1, 3, 4, 5, rail, toggles, buttons, picker, alignment panel |
| Ctx Days | the focus leader's 31 Day rows for the chosen worker type | KPI 2, the At work box, the calendar and its summary |
| Ctx Tree | Dynamic: the company tree's rows whose manager is on the focus's path (`p_Path`), a few hundred of 63,091. Static: the focus's rows. Plus Node rows and one day's Day rows | the tree, normal and expanded |

The Count, Tree and Theme toggles draw their two segments from the focus leader's All and Employees Node rows (`Seg Mode`), so they live in the small Leaders context too.

**Two themes.** Every sheet exists twice: light, and dark with " (dark)" after its name. Dynamic Zone Visibility shows one set, driven by `p_Dark`, so colors never depend on a calculated color field.

**Navigation is parameters.** These parameters drive the page:

| Parameter | What it holds |
|---|---|
| `p_Focus` | the leader |
| `p_Path` | the focus's path, the CEO down to the focus (`|W100001|W100002|W100010|`); set by the same click as `p_Focus` |
| `p_Tree` | Dynamic or Static |
| `p_Worker` | the worker type |
| `p_Count` | Everyone or At work |
| `p_Day` | the day |
| `p_B0`, `p_B1` | the picker's columns |
| `p_Dark` | the theme |
| `p_Zoom` | whether the tree is expanded |
| `p_PickOpen`, `p_CalOpen`, `p_RulesOpen` | which popover is open |

84 parameter actions set them. 80 deselect actions clear each selection right after a click, so a second click on the same mark fires again and no mark stays highlighted. Opening one popover closes the others.

**The tree, Dynamic: one company tree that grows.** The idea comes from The Information Lab's org chart with dynamic drill-down. Every leader has one fixed place: `tier` is the depth below the CEO, and a leader's child leaders sit one unit apart, biggest first, centered under them. Nothing moves when the focus changes, so a click grows the tree out of the leader instead of drawing a new picture, and the workbook's animation (switched on in its `<style>`) shows the move. What shows:

- a circle whose manager is on the focus's path: the chain from the CEO to the focus, every leader of each of those levels, and the focus's own team (`Parent On Path` = `CONTAINS([p_Path], "|" + [parent_node_id] + "|")`);
- four rows at most: two levels above the focus, the focus's row and the team (`[tier] >= [F Depth] - 2`);
- labels on the path and the team; the other leaders of each level small (35% size) and unlabeled, named on hover.

One click sets `p_Focus` and `p_Path` together (the clicked leader's id and path), so the tree, KPIs, rail and panel all follow. Clicking anyone higher up the chain closes everything below them. The axes are automatic without zero (`domain-expand='false'`), so the view pans and zooms to what is on the page. `p_Path` keeps the rule a plain row test: inside the context filter, a FIXED lookup of the path would run again inside each of the tree's FIXED reads.

**The tree, Static:** three levels of leaders below the focus at once, on a 0 to 1 canvas; clicking a circle opens that leader, clicking the focus goes up one.

**Drawing it.** The tree is a dual axis on the same x (`X Plot`):
- **Lines:** the link curves, 17 points per link, drawn on `Y Link`.
- **Pies:** the circles, drawn on `Y Node`. The circle size is the people led; the amber slice is the share with an alignment gap.

Each pie is three wedges:
- the Node row: people without a gap;
- points 15 and 16 of the link into the circle, each carrying half the gap.

Tableau labels a wedge at its middle angle. Splitting the gap around 12 o'clock centers the big wedge, and with it the leader's name, at 6 o'clock, straight below the circle. Point 15 is plotted at the circle's center (`X Plot`): a few pixels off and Tableau would draw the two halves as a second pie on top.

**The code.** In `tableau/builder/d7/`:

| File | What it does |
|---|---|
| `d7_calcs.py` | every calculation (200) |
| `build_d7.py` | sheets, dashboard zones, actions and visibility |
| `make_shapes_d7.py` | the shapes |
| `check_values.py` | the check tables in section 6 |

The .twb writer is Dashboard #6's (`tableau/builder/d6/twb.py`).

## 10. When something goes wrong

| What you see | Why | Fix |
|---|---|---|
| "element 'column' not allowed" on open | Calculations placed after a group in the data source | Rebuild with the current `build_d7.py`; it places them before `<extract>` |
| Red pills, and the KPIs or headline blank | A row-level field on the Tooltip shelf without ATTR | Rebuild; the builder wraps tooltip-only fields in ATTR |
| Shapes show as default circles and squares | Tableau did not find `Shapes/Arcadia D7` | Step 3, then restart Tableau |
| Logos missing | `D7_BRAND` did not point at the Brand folder (with a trailing `/`) | Step 4 |
| The build is overwritten after a revert | Tableau saved its own copy | Build again; use File › Revert to Saved, never Save |
| Numbers differ from section 6 | The extract is older than the warehouse | **Data › Refresh Extract**, then compare again |
| "Msg 156 … near the keyword 'Off'" in SQL Server | `Off` is reserved in T-SQL | Pull the latest `main`; the column is bracketed as `[off]` |
