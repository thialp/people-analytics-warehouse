# Compensation Walk dashboard: build status and next steps

Where the Tableau build stands, and what is still open. Updated 2026-10-12 (night): **Dashboard #2 is published** (see the Published section). The company is fictional and all data is synthetic.

## Published (2026-10-12)

- **Live:** https://public.tableau.com/app/profile/thialp/viz/ArcadiaCompensationWalk/Dashboard (profile: https://public.tableau.com/app/profile/thialp). Extracts of both data sources (271,219 and 260,464 rows). Steps, description text and decisions: [publish_tableau_public.md](publish_tableau_public.md).
- **Done in this stretch:** the rail (period, view, group, lens, cost, currency, reset, info panel and footnote), the Top drivers card (individual steps only), the Expand/Collapse buttons (text plus icon sheets in one container), amber Growth by Region, page subtitle with "Data as of".
- **Still to do on the published page:** the interaction checks listed in the publishing notes (rail, popovers, Expand/Collapse, Reset, hover). Anything that differs from Desktop goes below.

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

## Parked data items: done in warehouse release 2 (workbook steps still to do)

All the parked data changes were made in the SQL on branch `warehouse-release-2` (phases 2 and 7 of [the release plan](../workforce-planning/release_2_plan.md)). The workbook still has the old Custom SQL text and names. Click-by-click steps for the release 2 workbook session (phase 8), with the check table for every number: [release_2_republish.md](../workforce-planning/release_2_republish.md) and [expected_values.md](expected_values.md).

| Item | Data (done) | Workbook (to do) |
|---|---|---|
| Report As Of Date | `report_start_date` (30 Jun 2022) and `report_as_of_date` (30 Jun 2026) on every row of the walk, office moves, region walk and career moves, computed from the calendar | Page subtitle and Period popover note from the fields ("Data covers Jun 30, 2022 to Jun 30, 2026"); `Default To` = as-of date, `Default From` = one year earlier; Methodology line |
| More history, every FY with four options | History from Jun 30, 2021; the grid ends pairs after Jun 30, 2022 (lead-in year), so FY23 has all four year-over-year options | Paste the new walk and office-moves Custom SQL; the FY23 column of the Period popover fills in |
| Drop the Custom Range pairs | Grid holds the four offered types only: 88 pairs (was 184); walk 115,544 rows; SQL Server run 47 s on the Mac | Remove any `Custom Range` handling in calcs (`Pair Name` ELSE branch can stay) |
| Leader → Sub-function | `view_name = 'Sub-function'` in all four queries; the function-name fallback is kept so the view still covers the whole company (test 38) | `p_View` value, `p_GroupLeader` → `p_GroupSubfunction`, the `Selected Group` and `Panel Title` CASEs, delete the alias on `view_name`; tooltip: "no sub-function: shown at function level" |
| Region per group | New query [region walk](region_walk_and_career_moves.md): headcount walk by region for every group | Third data source; Growth by Region reads it with the same parameters, so it follows View and Group |
| `open_headcount` | Column on office moves = the group's Opening headcount (test 59) | Map title "725 people changed office (2.5% of headcount)" |
| Relocation 216 vs 227 | Checked (FY26 now 583 vs 600): 575 changed pay zone, 23 moved inside one pay zone (no pay change), 2 moved twice. Step renamed **Same-Country Transfer Adjustments** | Alias, Top drivers reason text and tooltip ("600 moved, 583 had a pay change"); Methodology line |
| Departures by region | Region walk: `exits + transfers_out + region_moves_out` | Optional second bar or tooltip on Growth by Region |
| Career moves panel | New query [career moves](region_walk_and_career_moves.md): promotions and demotions by grade, keyed like the walk; ties to the walk (test 58). FY26: 1,850 promotions (1,824 people), 148 demotions, 16 into Director and above | Build the panel and the `p_Panel` toggle (see "the rest of the dashboard" below) |

## Open: the rest of the dashboard (agreed order for the next session)

1. **Rail controls** (done 2026-10-12; build in [rail_controls_build.md](rail_controls_build.md)): Period (`p_From`, `p_To`, valid pairs only) and quick picks (FY26, FY25, last 4 quarters, monthly); View by (six rows, `p_View`); Group list for `p_Group` (readers pick, they do not type); Lens (now with Display As names), Cost, Currency toggles; Reset. Parameter actions, not filter actions, across the two data sources. The `p_Lens` control moves from the top right into the rail with a readable title ("Show pay as"). Navigation tabs (Summary, Drivers, Diagnostics, Methodology) and the fictional-company footnote in the rail.
2. **Top drivers card** (done 2026-10-12): four ranked rows with a reason each; build in [top_drivers_build.md](top_drivers_build.md). The calcs `TD Top Name`, `TD Top Text` and `TD Direction` may now be unused; delete them in the cleanup if so.
3. **Career moves panel** (promotions, demotions, Director and above) with the same group keys as the walk, and the `p_Panel` toggle that swaps it with the office-moves panel. Needs a Custom SQL like `tableau/custom_sql_office_moves.sql`.
4. **Expand and collapse** for the other cards, using `step_group`.

## Open: housekeeping

- The sketch SVG and PNG files in `design/` still show the first layout (big stat numbers, 12 px gaps, 1104 wide panel). Regenerate with `build_sketch_svg.py` once the page is final.
- The Figma push is blocked by the plan's tool-call quota; the SVGs are the import path until it resets.
- Dashboard #1 still needs republishing on Tableau Public with the refreshed data. (Dashboard #2 is published.)
- Open the PR for `office-moves-map-layout`, Squash and merge, and edit the message so no Co-Authored-By trailers remain (the first five commits on the branch have them against the working agreement).

## Decided 2026-10-12 (evening): small details after the Top drivers card
- **Expand / Collapse look like buttons**: the text label ("Expand · 11 steps", "Collapse · 4 groups") sits next to a small navy two-arrow icon sheet (`btn_expand_icon.png` / `btn_collapse_icon.png`). Each pair is a horizontal container (`Btn Expand ALL` / `Btn Collapse ALL`) with identical dimensions so nothing jumps when toggling. Both the text sheet and the icon sheet carry the parameter action.
- **Waterfall subtitle** drops "axis not from zero" / "axis in $M, not from zero" (the axis labels already show it); it now fits on one line in every Cost and View.
- **Top drivers subtitle** drops "teal adds, coral subtracts": "Largest of the N steps behind the waterfall".
- **Alias on `step` (Expand waterfall)**: International Transfer Adjustments -> "Cross-border move" (fallback "Intl. transfer"). Calcs compare the underlying values, so aliases do not break them.
- **Period popover note (until the SQL has `report_as_of_date`)**: second line under "Select a period", 9 pt `#8FA0B8`: "Fiscal year runs July to June · Data through Jun 30, 2026". Replace by the SQL date when the column exists (see the Report As Of Date item above).
- **Growth by region color**: amber `#D98E04` (user's pick). The slate version made the dashboard look flat, and teal/coral already mean up/down in the waterfall and "across a border" in the routes, so amber stays neutral on direction. Direction is carried by the bar side and the +/- label.
