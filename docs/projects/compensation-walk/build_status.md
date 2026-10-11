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

## Parked (back pocket, do later)

- **Relocation Adjustments 216 vs 227 within-country moves.** International lines up exactly (118 = 118): a border crossing always changes pay. The waterfall counts only moves with a pay-zone adjustment (`reloc_people > 0` in `custom_sql_compensation_walk.sql`); the map counts every office change. Most likely about 11 within-country movers changed office without a pay change; not yet checked. Plan: (1) write a check query splitting the 227 by whether a relocation pay event exists and see what the 11 share; (2) rename the step "Same-Country Transfer Adj." (SQL label, alias, tooltip); (3) show both numbers in the tooltip ("227 moved, 216 had a pay change"); (4) a line on the Methodology page. Data can change if needed: this is a demonstration dataset.
- **Departures by region** (each move would appear twice, once per end): a data change, deferred.

## Open: the rest of the dashboard (agreed order for the next session)

1. **Rail controls** (so the data can be explored): Period (`p_From`, `p_To`, valid pairs only) and quick picks (FY26, FY25, last 4 quarters, monthly); View by (six rows, `p_View`); Group list for `p_Group` (readers pick, they do not type); Lens (now with Display As names), Cost, Currency toggles; Reset. Parameter actions, not filter actions, across the two data sources. The `p_Lens` control moves from the top right into the rail with a readable title ("Show pay as"). Navigation tabs (Summary, Drivers, Diagnostics, Methodology) and the fictional-company footnote in the rail.
2. **Top drivers card** (empty): four ranked rows with a reason each.
3. **Career moves panel** (promotions, demotions, Director and above) with the same group keys as the walk, and the `p_Panel` toggle that swaps it with the office-moves panel. Needs a Custom SQL like `tableau/custom_sql_office_moves.sql`.
4. **Expand and collapse** for the other cards, using `step_group`.

## Open: housekeeping

- The sketch SVG and PNG files in `design/` still show the first layout (big stat numbers, 12 px gaps, 1104 wide panel). Regenerate with `build_sketch_svg.py` once the page is final.
- The Figma push is blocked by the plan's tool-call quota; the SVGs are the import path until it resets.
- Dashboard #1 still needs republishing on Tableau Public with the refreshed data.
- Open the PR for `office-moves-map-layout`, Squash and merge, and edit the message so no Co-Authored-By trailers remain (the first five commits on the branch have them against the working agreement).
