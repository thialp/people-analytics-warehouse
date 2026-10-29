# Workforce Cost Bridge workbook builder

Dashboard #6. The build guide is [`docs/projects/workforce-cost-bridge/cost_bridge_build.md`](../../../docs/projects/workforce-cost-bridge/cost_bridge_build.md).

| File | What it does |
|---|---|
| `check_values.py` | Every value the page shows, computed from `data/marts/mart_workforce_cost_growth_mix.csv` the way the page computes it: the tables of the guide's section 13. `--verify` checks that all 153 pair-and-group views close and that no bar dips below its axis floor |

```
python3 tableau/builder/d6/check_values.py --verify
python3 tableau/builder/d6/check_values.py
```

Expected first line: `153 pairs x groups; lowest path / min(opening, closing) = 0.9618; problems: 0`.

The workbook writer (as for Dashboard #5, reading every calculation from the guide's code blocks into the saved base workbook of the guide's section 2.2) is the next step.
