# Publishing the Compensation Walk to Tableau Public

Published 2026-10-12: [Compensation Walk](https://public.tableau.com/app/profile/thialp/viz/ArcadiaCompensationWalk/Dashboard) (profile: [thialp](https://public.tableau.com/app/profile/thialp)). Workbook `custom_sql_compensation_walk_20261011`, dashboard `Dashboard` (1400 x 850; republished 2026-10-17 with the aligned layout). The company is fictional and all data is synthetic.

## Why it is published as extracts

Tableau Public cannot reach a local SQL Server, so both data sources are **extracts** of the Custom SQL. The Data pane calls the walk `ArcadiaHR` and the office moves `Office Moves`.

| Data source | Rows in the extract | Custom SQL |
|---|---:|---|
| `ArcadiaHR` (the walk) | 271,219 | `tableau/custom_sql_compensation_walk.sql` |
| `Office Moves` | 260,464 | `tableau/custom_sql_office_moves.sql` |

Both are far under Tableau Public's 15-million-row limit. The extract is a snapshot: the SQL runs once, on the day you extract. The hyper files live in Tableau's own folder (`Documents/Tableau/Tableau Public/ArcadiaHR/Arcadia Compensation/Data Source Hyper/`); never commit `.hyper` files to the repository. The "Data as of Jun 30, 2026" text in the page subtitle and the Period popover note are static until the SQL has `report_as_of_date` (see [build_status.md](build_status.md)).

## Steps (free Tableau Public app, Mac)

1. Docker and the `arcadia-sql` container must be running (the extract refresh reads SQL Server).
2. On each data source, set Connection to **Extract**, use **Hide All Unused Fields**, and **Extract Data...** (Data Source tab or right-click the source in the Data pane). Check the row counts in **Extract > History**.
3. **Reset the dashboard first**: click "Reset to default view" on `Summary`, close all three popovers (`p_InfoOpen`, `p_PeriodOpen`, `p_GroupOpen` FALSE) and leave the waterfall in the Compact state. Tableau saves the parameter values as they are when you publish, and visitors land on them (the first test showed Brazil selected).
4. Hide the worksheets that are not on the dashboard (right-click the tab, Hide Sheet).
5. **File > Save to Tableau Public As...** (the Server menu is greyed out in the free app; Cmd+S also saves to Tableau Public). Name it `Arcadia Compensation Walk`. In the free app, saving and publishing are the same step, and the workbook is public.
6. On the web page, **Edit Details**: the description limit is **230 characters** (the form counts hashtags). The one used:
   `Why did average pay per FTE change? An interactive compensation walk for Arcadia Systems, a fictional company: drivers, office moves, regional growth. All data is synthetic. #PeopleAnalytics #WorkforceAnalytics #Compensation`
   External link: `https://github.com/thialp/people-analytics-warehouse`. Leave Inspiration blank.

## To republish after a data or design change

Refresh both extracts (**Extract > Refresh**, or Extract Data again), reset the dashboard (step 3), then **File > Save to Tableau Public As...** with the same name to replace the viz at the same URL. Check the page in the browser afterwards.

## Decisions made while finishing

- **Expand / Collapse button**: text sheet plus a navy two-arrow icon sheet side by side in one container (`Btn Expand ALL` / `Btn Collapse ALL`, identical size, so nothing jumps), with a soft border and corner radius on the container. The sheets themselves are transparent.
- **Hover outline on the button**: Tableau draws an outline on the mark under the cursor. There is no setting to turn it off. It is a normal "clickable" signal, so it stays. A one-sheet version (one invisible square mark with the label and arrow on it) would make the outline wrap the whole pill, but it was not tried.
- **Map credit ("© Mapbox © OpenStreetMap")** stays visible: attribution is a license requirement. To remove it legitimately, set the background map to None and use a public-domain Natural Earth image as a background image (on the polish list).
- **Selection/auto-deselect fields** (`zzTrue` / `zzFalse` on Detail) stay: they clear the selection after each click so a button can fire twice in a row.

## Checks to do on the published page (not yet done)

Rail buttons for Period, View, Cost, Currency and pay lens change the numbers; the Info, Period and Group popovers open and close; Expand and Collapse toggle; "Reset to default view" returns to FY26, Company, Avg per FTE, Loaded, Constant; hover on the map, routes and region bars; the page subtitle does not wrap for long group names. Anything that behaves differently from Desktop goes in [build_status.md](build_status.md).
