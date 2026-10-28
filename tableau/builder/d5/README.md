# Seats to Fill workbook builder

Writes `Seats to Fill.twb` (Dashboard #5) from the base workbook Tableau saves right after the Custom SQL is connected and extracted (build guide 2.2). Every calculation is read from the code blocks of [the build guide](../../../docs/projects/workforce-planning/seats_to_fill_build.md); section 16 of the guide lists what the workbook does differently and why.

| File | What it does |
|---|---|
| `twb.py` | A small .twb writer: names each calculation, infers its level (constant, row, aggregate, table calculation) and type, wraps row-level references inside aggregates in `MIN()`, and writes worksheets |
| `parse_guide.py` | Reads the `// Name` + formula blocks from the guide |
| `d5_calcs.py` | The guide's calculations plus the ones it describes in prose (comma-pattern strings, list shapes, the backtest on scaffold rows) |
| `model_d5.py` | Raw columns from the extract metadata, parameters, roles, aliases |
| `build_d5.py` | The sheets, color and shape maps, the dashboard, the popovers and their visibility, 69 actions |

```
D4_TWB="…/Contingent Workforce Reconciliation.twb" python3 build_d5.py base.twb "Seats to Fill.twb" 3
```

Stage 1 writes the KPI band, 2 adds the main chart, survival and backtest, 3 is the published workbook. Close the workbook in Tableau first. Dashboard #4's workbook supplies the document-format manifest Tableau needs for parameter actions and rounded corners.
