# Workforce Cost Bridge workbook builder

Writes the Workforce Cost Bridge workbook (Dashboard #6, [live on Tableau Public](https://public.tableau.com/app/profile/thialp/viz/WorkforceCostBridgeShapleyCostDecompositionArcadiaSystems/Dashboard)) from the base workbook Tableau saves right after the Custom SQL is connected and extracted (build guide 2.2). Every calculation is read from the code blocks of [the build guide](../../../docs/projects/workforce-cost-bridge/cost_bridge_build.md); section 15 of the guide records each review round and what changed.

| File | What it does |
|---|---|
| `twb.py` | The Dashboard #5 .twb writer, extended with caption parameters, date functions, grid and zero lines, row dividers and an x-axis per pane |
| `d6_calcs.py` | The guide's calculations, its number patterns (`<M1 on …>`, `<Sign on …>`, `<Comma on …>`, `<Pct1 on …>`) expanded in place, and the text fields it lists in a table |
| `model_d6.py` | Raw columns from the extract metadata, parameters, roles, the bridge's table-calculation order |
| `build_d6.py` | The sheets, the dashboard (rail, ribbon, bridge, order table, five years, three popovers), 53 actions: 23 parameter actions, 28 deselects, the GitHub and LinkedIn links |
| `check_values.py` | Every value the page shows, computed from `data/marts/mart_workforce_cost_growth_mix.csv` the way the page computes it (the guide's section 13). `--verify` checks that all 153 pair-and-group views close and that no bar dips below its axis floor |

```
python3 tableau/builder/d6/check_values.py --verify
D4_TWB="…/Contingent Workforce Reconciliation.twb" python3 tableau/builder/d6/build_d6.py base.twb "Workforce Cost Bridge.twb"
```

Expected: `153 pairs x groups; lowest path / min(opening, closing) = 0.9618; problems: 0`, then `calcs 212 sheets 32 actions 53 (23 parameter)`. Close the workbook in Tableau first. Dashboard #4's workbook supplies the document-format manifest Tableau needs for parameter actions and rounded corners. The base must carry the release 6.1 columns (`opening_employees` … `closing_contingent`); refresh its extract after the SQL Server run.
