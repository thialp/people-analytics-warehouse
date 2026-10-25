# Dashboard #4 spikes (phase 7): Tableau Public

Six small tests, run before any page is built, so a limit of the Sankey extension or of Tableau Public is found now and not in the middle of the build. One throw-away workbook, `D4 Spikes`, on the dashboard's one data file. Each spike has a pass condition and a fallback chosen in advance ([release 4 plan](release_4_plan.md), phase 7). A failure is written down with its fallback; the story is never changed quietly.

Arcadia Systems, Keystone HR, Bridgeway VMS and Helix Service Desk are fictional; all data is synthetic.

## Setup (once)

1. Tableau Public Desktop, new workbook, **Text file**, choose `data/marts/mart_cw_reconciliation_dashboard.csv` (24.8 MB, 62,808 rows). Keep the connection as **Extract**.
2. Three row types share the file, so every sheet filters `row_type` first:
   - `Gap`: the Sankey, the gap list (`gaps` = 1)
   - `Ticket`: the ticket card (`tickets` = 1, one dot at `dot_x`, `dot_y`)
   - `Population`: the gap rate (not needed for the spikes)
3. Add `is_latest_close` = 1 as a filter too (Current, 30 Jun 2026).
4. Name the workbook `D4 Spikes` and save it as a local `.twbx` (not published yet, except S6).

Expected on Current: 379 Gap rows (flags F01 to F12: 54, 15, 99, 1, 28, 49, 10, 32, 6, 6, 54, 25), 330 Ticket rows.

## S1. Sankey: node order by a field

1. Add the Sankey extension to a sheet (Marks card or dashboard Extension object, **Sankey** from the Tableau Exchange; whichever your Tableau Public offers).
2. Filters: `row_type` = Gap, `is_latest_close` = 1.
3. Levels, left to right: `flag_rank_label`, `risk`, `place_key`. Value: `SUM(gaps)`.
4. Look at the left column.

**Pass:** the 12 flags run from "01 Order open after the end date" down to "12 Billed after the end date" (the number in the label is the rank at this close), and F04 with a single gap is still drawn as a visible ribbon.
Also record the risk column: do the six risks sit in the order `risk_order` gives (Wrong cost center, Paying after the end, Wrong headcount, Wrong PID, Access kept, Access lost) or alphabetically?

**Fallback:** the label sorts by rank by itself, so alphabetical order on it is the rank order. For risks, prefix `risk_order` into a label (`1 Wrong cost center`) the same way.

## S2. Sankey: a click drives a filter or set action

1. Second sheet: a plain list of gaps (`contractor_name`, `flag_name`, `place`, `days_open`), same filters.
2. Dashboard with both. Add the action: **Dashboard > Actions > Add Action > Filter**, source the Sankey sheet, target the list, run on **Select**, fields `flag_code`, `risk`, `place_key`.
3. Click a flag, then a risk, then a place.

**Pass:** the list narrows to that flag, risk or place each time; clicking empty space clears it. Record whether the click carries one field or all three (a click on a place should not need the flag).

**Fallback:** the KPI cards and the ticket card's rows drive the gap list instead (no click on the Sankey).

## S3. Sankey: colour by place across levels, tooltip

1. Colour the ribbons by `place_key` (3 values: Bridgeway, Keystone, Integration: alert data engineering).
2. Tooltip: `flag_rank_label`, `flag_rank_prior_close`, `flag_count_prior_close`, `SUM(gaps)`.

**Pass:** one colour per place on every level (a Bridgeway-bound gap is Bridgeway-coloured from flag to place), and the tooltip shows rank and prior-close count. The 2 Integration gaps (Current) stay visible beside 196 and 181.
Record: can two Integration shades (clears on its own; needs data engineering) be drawn, or only one colour per `place_key`?

**Fallback:** colour by level; the movement versus the prior close moves into the subtitle.

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

**Pass:** adding and removing a member each take well under a second, the selected capsule shows as ticked (colour or border), and an empty set shows all 379 gaps.
**Fallback:** native multi-value filters, styled to sit close to the capsules.

## S5. Ticket dots at 144 per cell

1. Filters: `row_type` = Ticket, `is_latest_close` = 1 (330 rows).
2. Scatter: `dot_x` on Columns, `dot_y` on Rows, both continuous (`dot_x` runs 0 to 3, `dot_y` 0.85 to 2.85); `ticket_number` on Detail so each row is a dot; panes or a 3 x 3 grid: `current_group` (Vendor Management, HR Operations, Data Engineering) by `age_band` (0 to 5 days, 6 to 30 days, Over 30 days).
3. Size the marks to the smallest circle that still shows (about 2.5 px). The densest cell holds 144 dots.

**Pass:** 144 dots in one cell are separate and readable, and hover lands on the right dot (tooltip shows its `ticket_number` and `age_days`).
**Fallback:** smaller cells, or a count per cell with the dots shown on hover.

## S6. Extract size and speed

1. Publish `D4 Spikes` to Tableau Public (File > Save to Tableau Public As...) with S1 to S5 on separate sheets.
2. Open it on the web in a private window; time from opening to the Sankey drawn. Repeat once warm.

**Pass:** it publishes (all 62,808 rows, 24.8 MB file) and the page loads in under 5 seconds.
**Fallback:** drop the Gap rows of closes older than 25 months from the extract (the replay keeps two years).

## Send back

| Spike | Pass / fail | One line of what you saw |
|---|---|---|
| S1 | | flag order, risk order, F04 visible? |
| S2 | | one click carries which fields? |
| S3 | | one colour per place? two Integration shades possible? tooltip? |
| S4 | | add / remove speed, tick, empty set = All? |
| S5 | | readable at what size? hover correct? |
| S6 | | published? load seconds (cold, warm) |

Screenshots of S1/S3 (the Sankey) and S5 (the dense cell) help most. I record the results in the release plan and choose the fallbacks.
