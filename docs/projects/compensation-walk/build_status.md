# Compensation Walk dashboard: build status and next steps

Where the Tableau build stands, and what is still open. Updated 2026-10-09 (end of day). The company is fictional and all data is synthetic.

## Done

| Piece | State |
|---|---|
| Data | Walk Custom SQL and office-moves Custom SQL on SQL Server, both validated against the warehouse (`sqlserver/06`, `sqlserver/07`); 40 SQL tests pass |
| Summary page frame | 1400 x 850, filter rail 216, 30 px frame, 16 px gaps; every card edge on the KPI grid ([layout](design/README.md)) |
| KPI cards | Five cards follow the lens; background `docs/brand/arcadia_kpi_cards_bg_summary.png` (drawn by `docs/brand/build/make_kpi_cards_bg.py`); `kpi_GridLeft` 246, `kpi_CardW` 212, `kpi_GapX` 16 |
| Waterfall | Compact (6 bars) and expanded (13 bars) states with Expand / Collapse buttons; title states the result |
| Office moves panel | Map, Top 5 routes and Where they landed (region bars) built; follow the Period, View and Group parameters ([build guide](tableau_office_moves_map_guide.md)) |

## Open: polish on what exists

1. **Panel title.** The header shows the literal sheet name "Office Moves Title". Wire the `Moves Title` calculation (needs the `Top Route Movers` / `Top Route` calculations) or hide the sheet title.
2. **Panel subtitle.** The three `Stat` sheets are still used across the top (345 / 118 / 227, wrapping onto two lines, across before within). Replace them with the single `Office Moves SubTitle` sheet (colored runs: violet within one country, coral across a border) and delete the three Stat sheets.
3. **Region bars are not sorted by size** (they read alphabetically). Sort `to_region` descending by `SUM(Moved People)`.
4. **Chart titles** "Busiest routes" and "Where they landed" are not showing yet.
5. **Map framing.** After the resize to 484 x 224 the arcs run off both side edges. Re-frame the zoom so Vancouver (west) and Sydney (east) sit inside, and check the map fills its box.
6. **Routes in both directions** (option, not decided): count each pair of offices once, as the Figma prototype does. FY26 would read Bengaluru ↔ Hyderabad 53, Bengaluru ↔ Pune 22, Krakow ↔ Warsaw 17, Hyderabad ↔ Pune 16, Guadalajara ↔ Mexico City 16.
7. **Lens names.** `p_Lens` values `FTE` and `Amount` should display as **Pay per FTE** and **Total payroll** (Edit Parameter, Display As), and the dashboard title calculation should map them the same way (it still reads "Compensation Walk - FTE").
8. **Waterfall title**: add the driver ("led by ...") once the Top drivers calculations exist.

## Open: the rest of the dashboard (agreed order for the next session)

1. **Rail controls** (so the data can be explored): Period (`p_From`, `p_To`, valid pairs only) and quick picks (FY26, FY25, last 4 quarters, monthly); View by (six rows, `p_View`); Group list for `p_Group` (readers pick, they do not type); Lens, Cost, Currency toggles; Reset. Parameter actions, not filter actions, across the two data sources. Navigation tabs (Summary, Drivers, Diagnostics, Methodology) and the fictional-company footnote in the rail.
2. **Top drivers card** (empty): four ranked rows with a reason each.
3. **Career moves panel** (promotions, demotions, Director and above) with the same group keys as the walk, and the `p_Panel` toggle that swaps it with the office-moves panel. Needs a Custom SQL like `tableau/custom_sql_office_moves.sql`.
4. **Expand and collapse** for the other cards, using `step_group`.

## Open: housekeeping

- The sketch SVG and PNG files in `design/` still show the first layout (big stat numbers, 12 px gaps, 1104 wide panel). Regenerate with `build_sketch_svg.py` once the page is final.
- The Figma push is blocked by the plan's tool-call quota; the SVGs are the import path until it resets.
- Region bars show where people landed. Departures by region would need each move to appear twice (once per end): a data change, deferred.
- Dashboard #1 still needs republishing on Tableau Public with the refreshed data.
