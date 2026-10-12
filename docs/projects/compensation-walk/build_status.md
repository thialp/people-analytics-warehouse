# Compensation Walk dashboard: build status and next steps

Where the Tableau build stands, and what is still open. Updated 2026-10-10 (end of day). The company is fictional and all data is synthetic.

## Done

| Piece | State |
|---|---|
| Data | Walk Custom SQL and office-moves Custom SQL on SQL Server, both validated against the warehouse (`sqlserver/06`, `sqlserver/07`); 40 SQL tests pass |
| Summary page frame | 1400 x 850, filter rail 216, 30 px frame, 16 px gaps; every card edge on the KPI grid ([layout](design/README.md)) |
| KPI cards | Five cards follow the lens; background `docs/brand/arcadia_kpi_cards_bg_summary.png` (drawn by `docs/brand/build/make_kpi_cards_bg.py`); `kpi_GridLeft` 246, `kpi_CardW` 212, `kpi_GapX` 16 |
| Lens | `Is FTE` Boolean drives every lens-dependent calc; `p_Lens` Display As is **Avg pay per FTE** / **Total payroll** (Values stay `FTE` / `Amount`); titles, subtitles and KPI cards follow it |
| Titles | Page subtitle is a statement, not a question; waterfall headline plus a two-line subtitle (period, lens meaning, axis note, biggest moves); map headline "345 people changed office; 66% stayed inside one country" ([dashboard_titles.md](dashboard_titles.md)) |
| Waterfall | Compact (6 bars) and expanded (13 bars) with Expand / Collapse; true-value trimmed axis with light gridlines that re-fits per lens (`Axis Unit`, true `Waterfall Position`); hover tooltips explain each step |
| Office moves panel | Map (thin three-class lines, teal arrival dots), **Top 5 busiest routes** (two-line subtitle, tooltip with share and both directions) and **Growth by region** (opening \| closing in the name row, bar = growth %, tooltip with net change and share of growth) built and following Period, View and Group where applicable ([build guide](tableau_office_moves_map_guide.md)) |

## Open: polish on what exists

1. **Apply and check the 16 px panel spacing** (map 520, routes 270, region 270, equal tops and bottoms, both bar cards with the same two-line title block). Specified in the map guide, section 5; not yet confirmed on the dashboard.
2. **Gray box behind the route counts** (reference-line label shading). Format the label with Shading None, or move `SUM(Movers)` onto the bar's Label and delete the reference line.
3. **Waterfall title block height.** The sheet needs about 54 px for the headline plus two lines, or the second subtitle line is clipped. Check Compact and Expand on the dashboard; also judge the tick density there (Automatic ticks depend on the card height).
4. **Axis format.** Total ticks read "$3,000" with no M (conditional formats do not exist in Tableau). Optional later: a small unit note from a calc.
5. **Region bars:** confirm the name row is not crowded at 9 pt; sort by growth descending.
6. **Map framing and background** (Base layer off, Worksheet shading None, all cards `#FBFBF8`); confirm the arcs stay inside both side edges.
7. **Share of headcount in the map title** ("1.2% of headcount"): needs `open_headcount` in `custom_sql_office_moves.sql` (345 / 28,436 = 1.2%). Not built; the title has no percentage until then.
8. **Delete the retired items:** the three `Stat` sheets, `Region Moves`, `Moved People`, `Top Region Movers`, `Top Region`, `Axis Step`, the opening-level reference line.
9. **Routes in both directions** (chart option; the tooltip already shows both directions): Bengaluru ↔ Hyderabad 53, Bengaluru ↔ Pune 22, Krakow ↔ Warsaw 17, Hyderabad ↔ Pune 16, Guadalajara ↔ Mexico City 16.
10. **Negative zero in the KPI band.** A tiny negative change shows "−0.0%" (and "−0%" in the waterfall title). Round the value in the calc before formatting so it reads 0.0%.

## Parked (back pocket, do later)

- **Relocation Adjustments 216 vs 227 within-country moves.** International lines up exactly (118 = 118): a border crossing always changes pay. The waterfall counts only moves with a pay-zone adjustment (`reloc_people > 0` in `custom_sql_compensation_walk.sql`); the map counts every office change. Most likely about 11 within-country movers changed office without a pay change; not yet checked. Plan: (1) write a check query splitting the 227 by whether a relocation pay event exists and see what the 11 share; (2) rename the step "Same-Country Transfer Adj." (SQL label, alias, tooltip); (3) show both numbers in the tooltip ("227 moved, 216 had a pay change"); (4) a line on the Methodology page. Data can change if needed: this is a demonstration dataset.
- **Report As Of Date in the SQL** (decided 2026-10-12). Add one column, `report_as_of_date`, to `custom_sql_compensation_walk.sql`: the latest month-end that exists in the warehouse (a static date, not a refresh timestamp; today 2026-06-30). Adding 2027 data to the warehouse moves it by itself. Uses: (1) the "Data through ..." line in the Period popover (a small sheet instead of a static text object); (2) a matching `report_start_date` (earliest month-end, today 2022-06-30) so the note reads "Data covers Jun 30, 2022 to Jun 30, 2026"; (3) `Default To` = the as-of date and `Default From` = one year earlier, so the dashboard opens on the latest fiscal year without editing the workbook; (4) a line on the Methodology page. Until then the popover note is static text.
- **More history so every fiscal year offered has all four period options** (decided 2026-10-12; numbers may change). Today the history starts at the Jun 30, 2022 month-end, so FY23 offers only Jun 22 → Jun 23: the trailing-12-month options ending Sep 22, Dec 22 and Mar 23 would start in 2021. Fix: start the generator one year earlier (month-ends from Jun 30, 2021; Sep 30, 2021 is the minimum) and keep the **displayed** window starting July 2022 by a rule in the pair grid (`to_month_end` after 2022-06-30). Every pair then still ends inside FY23 or later, FY23 gets its four options, and FY22 is never offered (so it is not the new partial year). Correction to an earlier note here: a backfill does not just move the gap, as long as the grid limits what is offered.
- **Drop the Custom Range pairs from the walk SQL** (found 2026-10-12). 99 of the 184 pairs are quarter-end to quarter-end ranges that no control offers. Removing them (keep the four offered types) removes about half the rows and run time; the Period popover can then never land on a pair with no label.
- **Rename the "Leader" view to "Sub-function"** (found 2026-10-12). The view is not a person: it groups departments by their parent org unit (a sub-function such as Engineering, Sales, Client Services, Infrastructure, or the function itself where there is none; 10 groups between Function (8) and Department (31)). It is keyed by org unit on purpose, so a reorg or a new leader does not look like a transfer (`compensation_walk.md` section 4), and the SQL already types those units 'Sub-function'. Until the SQL changes, the workbook shows the new name through an alias on `view_name` (underlying value stays `Leader`) and the `Panel Title` text. The SQL change touches: `view_name` / `'Leader'` in `tableau/custom_sql_compensation_walk.sql` (two places) and `tableau/custom_sql_office_moves.sql` (two), `sql/03_marts/mart_compensation_walk.sql` and `mart_office_moves.sql` (two each), `build_sketch_svg.py`, the picker docs, and in the workbook the `p_View` value, `p_GroupLeader` (rename to `p_GroupSubfunction`), the `Selected Group` and `Panel Title` CASEs; then delete the alias. Also decide the fallback: six of the ten groups repeat a function name (Finance, Marketing, People ...) because those functions have no sub-function, so "Finance" appears in both views. Option: list only the real sub-functions, or keep the fallback and say so in the tooltip. `group_leader` (the person who leads the unit on the To month-end) stays and could feed a "Led by" tooltip line.
- **Departures by region** (each move would appear twice, once per end): a data change, deferred.

## Open: the rest of the dashboard (agreed order for the next session)

1. **Rail controls** (so the data can be explored): Period (`p_From`, `p_To`, valid pairs only) and quick picks (FY26, FY25, last 4 quarters, monthly); View by (six rows, `p_View`); Group list for `p_Group` (readers pick, they do not type); Lens (now with Display As names), Cost, Currency toggles; Reset. Parameter actions, not filter actions, across the two data sources. The `p_Lens` control moves from the top right into the rail with a readable title ("Show pay as"). Navigation tabs (Summary, Drivers, Diagnostics, Methodology) and the fictional-company footnote in the rail.
2. **Top drivers card** (in progress 2026-10-12): four ranked rows with a reason each; build in [top_drivers_build.md](top_drivers_build.md).
3. **Career moves panel** (promotions, demotions, Director and above) with the same group keys as the walk, and the `p_Panel` toggle that swaps it with the office-moves panel. Needs a Custom SQL like `tableau/custom_sql_office_moves.sql`.
4. **Expand and collapse** for the other cards, using `step_group`.

## Open: housekeeping

- The sketch SVG and PNG files in `design/` still show the first layout (big stat numbers, 12 px gaps, 1104 wide panel). Regenerate with `build_sketch_svg.py` once the page is final.
- The Figma push is blocked by the plan's tool-call quota; the SVGs are the import path until it resets.
- Dashboard #1 still needs republishing on Tableau Public with the refreshed data.
- Open the PR for `office-moves-map-layout`, Squash and merge, and edit the message so no Co-Authored-By trailers remain (the first five commits on the branch have them against the working agreement).

## Decided 2026-10-12 (evening): small details after the Top drivers card
- **Expand / Collapse look like buttons**: the text label ("Expand · 11 steps", "Collapse · 4 groups") sits next to a small navy two-arrow icon sheet (`btn_expand_icon.png` / `btn_collapse_icon.png`). Each pair is a horizontal container (`Btn Expand ALL` / `Btn Collapse ALL`) with identical dimensions so nothing jumps when toggling. Both the text sheet and the icon sheet carry the parameter action.
- **Waterfall subtitle** drops "axis not from zero" / "axis in $M, not from zero" (the axis labels already show it); it now fits on one line in every Cost and View.
- **Top drivers subtitle** drops "teal adds, coral subtracts": "Largest of the N steps behind the waterfall".
- **Alias on `step` (Expand waterfall)**: International Transfer Adjustments -> "Cross-border move" (fallback "Intl. transfer"). Calcs compare the underlying values, so aliases do not break them.
- **Period popover note (until the SQL has `report_as_of_date`)**: second line under "Select a period", 9 pt `#8FA0B8`: "Fiscal year runs July to June · Data through Jun 30, 2026". Replace by the SQL date when the column exists (see the Report As Of Date item above).
- **Growth by region color**: amber `#D98E04` (user's pick). The slate version made the dashboard look flat, and teal/coral already mean up/down in the waterfall and "across a border" in the routes, so amber stays neutral on direction. Direction is carried by the bar side and the +/- label.
