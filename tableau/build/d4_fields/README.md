# Dashboard #4 fields, written into the workbook

Dashboard #4 has about 230 parameters and calculated fields (`docs/projects/contingent-workforce/dashboard_4_build.md`, sections 6 to 16). Typing them by hand takes hours and invites typos, so this folder writes them straight into the `.twb` XML.

| File | What it does |
|---|---|
| `spec.py` | Every parameter and calc, by caption, in build-doc order. Formulas refer to fields by caption (`[Gap Now]`, `[p_Close]`). Text patterns (comma, rate, toggle) are small functions, so a fix lands everywhere at once |
| `build.py` | Reads a workbook and writes a new one. It adds a `Parameters` data source; turns captions into Tableau's internal names (`[Calculation_…]`, `[Parameters].[Parameter …]`); adds the calcs to the `CW Reconciliation` data source; rewrites the spike calcs in place, keeping their internal names so the sheets keep their pills; and adds the new fields the Sankey sheet now depends on to that sheet's own field list. It stops if a reference does not resolve or a calc already exists |
| `check.py` | Checks every formula before Tableau sees it: balanced `()`, `{}`, `[]`; one `END` per `IF` or `CASE`; and no formula that mixes row-level and aggregate parts (Tableau's most common refusal) |

```bash
python3 tableau/build/d4_fields/check.py
python3 tableau/build/d4_fields/build.py "in.twb" "out.twb"
```

Run on 2026-10-25: 10 parameters, 211 new calcs, 21 spike calcs rewritten; `check.py` found no problems. Not included: the `kpi_` parameters and calcs, which are copied from Dashboard #2 (build doc, step 9).

Close Tableau before swapping in the new file. Tableau holds the workbook in memory and would overwrite the change on the next save.
