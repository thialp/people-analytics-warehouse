# Dashboard #4 spikes (phase 7): Tableau Public

Six small tests, run before any page is built, so a limit of the Sankey extension or of Tableau Public is found now and not in the middle of the build. One throw-away workbook, `D4 Spikes`, on the dashboard's one Custom SQL data source. Each spike has a pass condition and a fallback chosen in advance ([release 4 plan](release_4_plan.md), phase 7). A failure is written down with its fallback; the story is never changed quietly.

Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic.

## Setup (once)

Same route as Dashboards #1 to #3: Tableau Desktop on the local SQL Server, one Custom SQL data source, published as an extract (Tableau Public cannot reach a local SQL Server).

1. SQL Server must be up with the revision 3 warehouse built (`git pull`, then `build_all.sql`: 15 should say PASS on all 35 checks).
2. Tableau Desktop, **Connect > Microsoft SQL Server**: server `localhost`, port `1433`, database `ArcadiaHR`, SQL Server Authentication, user `sa`, the password from `docker exec arcadia-sql printenv MSSQL_SA_PASSWORD`.
3. Drag **New Custom SQL** onto the canvas and paste the whole of `tableau/custom_sql_cw_reconciliation_dashboard.sql`. **Extract** it (65,435 rows; it ran in 1 second on SQL Server).
4. Three row types share the source, so every sheet filters `row_type` first:
   - `Gap`: the Sankey, the gap list (`gaps` = 1)
   - `Ticket`: the ticket card (`tickets` = 1, one dot at `dot_x`, `dot_y`)
   - `Population`: the gap rate (not needed for the spikes)
5. Add `is_latest_close` = 1 as a filter too (Current, 30 Jun 2026).
6. Save the workbook as `D4 Spikes` (local `.twbx`; S6 publishes it).

The CSV `data/marts/mart_cw_reconciliation_dashboard.csv` holds the same columns and rows, and is only a fallback if the SQL Server connection misbehaves; the build uses the Custom SQL.

Expected on Current: 407 Gap rows (flags 01 to 09: 28, 49, 25, 100, 69, 48, 22, 54, 12), 361 Ticket rows.

If the S1 workbook already exists, refresh its extract (Data > CW Reconciliation > Extract > Refresh) and replace the old pills: `flag_rank_label` becomes `flag_label`, `place_key` becomes `place_label`, and the `risk_rank_label` and `flag_sort_key` calculations are no longer needed.

## S1. Sankey: node order (done 2026-10-25)

**Result.** The first column follows its pill sort; columns 2 and 3 ignore their sort and place each node in the order it first appears when the rows are read in the first column's order. Without a measure on Link every row counts 1, so `SUM(gaps)` is required. This was reproduced in code from four screenshots, percentages included, and led to revision 3 of the plan: the data is now built so all three columns read alphabetically at every close (test 83).

**Re-check on the revision 3 data** (a minute):

1. Levels, left to right: `flag_label`, `risk`, `place_label`. Link: `SUM(gaps)`. Sort `flag_label` Alphabetic, Ascending (the default).
2. Expected, top to bottom:
   - Flags: 01 One person, two IDs ... 09 Active in Keystone, not working in Bridgeway
   - Risks: Active headcount mismatch (102), Billing after the end date (100), Cost center mismatch (69), PID mismatch (70), Status mismatch (66)
   - Places: Bridgeway (vendor system) 194, Keystone (HR system) 151, System feed (integration) 62
3. Flag 09 (12 gaps) is still drawn with its label.

## S2. Sankey: a click drives a filter or set action

1. Second sheet: a plain list of gaps (`contractor_name`, `flag_name`, `place`, `days_open`), same filters.
2. Dashboard with both. Add the action: **Dashboard > Actions > Add Action > Filter**, source the Sankey sheet, target the list, run on **Select**, fields `flag_label`, `risk`, `place_label`.
3. Click a flag, then a risk, then a place.

**Pass:** the list narrows to that flag, risk or place each time; clicking empty space clears it. Record whether the click carries one field or all three (a click on a place should not need the flag).

**Fallback:** the KPI cards and the ticket card's rows drive the gap list instead (no click on the Sankey).

## S3. Sankey: colours and tooltip

The extension (version 2.0, December 2025) sets colours per node, per level, in **Format Extension > Edit Colors**. A ribbon takes the colour of the node it leaves.

1. Install the Arcadia palettes first (`docs/brand/Preferences.tps`, see `docs/brand/README.md`) and restart Tableau. Then **Edit Colors**, level by level, choosing the palette in *Select Color Palette*:
   - `flag_label`: *Arcadia 3 Categorical Light*, then **Assign To Level** (flags 01 to 09 take its nine colours in order)
   - `risk`: *Arcadia 6 Neutrals*, click each risk and pick steel `#8FA1B8`
   - `place_label`: *Arcadia 4 Systems*, **Assign To Level** (Bridgeway amber, Keystone violet, System feed teal)
   If the Arcadia palettes do not appear in the extension's list (they do under Tableau's own Edit Colors), record it: that decides whether the build colours the Sankey from a built-in palette.
2. Look for a setting that colours links by their **target** node. The ribbons from a risk to a place should take the place's colour; by default a ribbon takes the colour of the node it leaves (grey here). Record which it is.
3. Level width about 150 so the labels sit inside the nodes; node labels show the value and the percentage of total (version 2.0 option).
4. Tooltip: `flag_label`, `flag_rank`, `flag_rank_prior_close`, `flag_count_prior_close`, `SUM(gaps)`.

**Pass:** the Arcadia palettes are offered, the colours hold after a filter change (version 2.0 fixed colour persistence), risk-to-place ribbons can take the place's colour, flag 09's label is readable, and the tooltip shows the rank and the prior close. Send a screenshot of the Edit Colors panel too.

**Fallback:** risk-to-place ribbons stay grey; the place colour is on the place nodes only.

## S4. Set-action multi-select, on the web

1. On the Gap data: create sets from `function_name` (right-click the field > Create > Set, pick any, and name it `Function Set`).
2. A calculation for "something chosen":
   `Any Function Chosen` = `{ MAX(IF [Function Set] THEN 1 ELSE 0 END) } = 1`
   and the filter:
   `In Scope Function` = `NOT [Any Function Chosen] OR [Function Set]`
   (an empty set means All).
3. A sheet listing the 9 functions as capsules (text, or a bar), with a **Change Set Values** action: source that sheet, target `Function Set`, **Add to set** on select.
4. A second sheet: `SUM(gaps)` filtered by `In Scope Function` = True.
5. Publish this one sheet to Tableau Public (S6 does it with the full file) and test on the web: click two functions, click one again to remove it.

**Pass:** adding and removing a member each take well under a second, the selected capsule shows as ticked (colour or border), and an empty set shows all 407 gaps.
**Fallback:** native multi-value filters, styled to sit close to the capsules.

## S5. Ticket dots at 141 per cell

1. Filters: `row_type` = Ticket, `is_latest_close` = 1 (361 rows).
2. Scatter: `dot_x` on Columns, `dot_y` on Rows, both continuous (`dot_x` runs 0 to 3, `dot_y` 0.85 to 2.85); `ticket_number` on Detail so each row is a dot; panes or a 3 x 3 grid: `current_group` (Vendor Management, HR Operations, Data Engineering) by `age_band` (0 to 5 days, 6 to 30 days, Over 30 days).
3. Size the marks to the smallest circle that still shows (about 2.5 px). The densest cell holds 141 dots (at any close).

**Pass:** 141 dots in one cell are separate and readable, and hover lands on the right dot (tooltip shows its `ticket_number` and `age_days`).
**Fallback:** smaller cells, or a count per cell with the dots shown on hover.

## S6. Extract size and speed

1. Publish `D4 Spikes` to Tableau Public (Server > Tableau Public > Save to Tableau Public As...) as an extract, with S1 to S5 on separate sheets.
2. Open it on the web in a private window; time from opening to the Sankey drawn. Repeat once warm.

**Pass:** it publishes (all 65,435 rows; the CSV is about 26 MB, so the extract is of that order) and the page loads in under 5 seconds.
**Fallback:** drop the Gap rows of closes older than 25 months from the extract (the replay keeps two years).

## Send back

| Spike | Pass / fail | One line of what you saw |
|---|---|---|
| S1 | Done | re-check on revision 3: all three columns alphabetical, flag 09 visible? |
| S2 | | one click carries which fields? |
| S3 | | node colours set per level? risk-to-place ribbons by target? hold after a filter? flag 09 label fits? tooltip? |
| S4 | | add / remove speed, tick, empty set = All? |
| S5 | | readable at what size? hover correct? |
| S6 | | published? load seconds (cold, warm) |

Screenshots of S1/S3 (the Sankey) and S5 (the dense cell) help most. I record the results in the release plan and choose the fallbacks.
