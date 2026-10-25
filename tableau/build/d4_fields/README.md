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

## The native Sankey (build doc section 9N)

| File | What it does |
|---|---|
| `spec_sankey.py` | The 3 parameters and 142 `Sk` calcs of the native Sankey: node counts, scale, node tops, ribbon offsets, the curve, labels, tooltips and click picks. Every position is a FIXED LOD of the selection, evaluated on the Custom SQL's `Sankey` scaffold rows |
| `build_sankey.py` | Writes the new Custom SQL (with `flag_short` and the scaffold) into both copies in the workbook, registers the four new columns, and adds the `Sk` fields. Existing fields are only read, so the extension Sankey (version A) is unchanged |
| `verify_sankey.py` | Runs the `Sk` formulas on the DuckDB mart (FIXED LODs as window aggregates) and draws the result as SVG, so the geometry is checked before Tableau opens |
| `patch_levels.py` | Version A only: took the counts out of the extension's level fields so its colours persist |

```bash
python3 tableau/build/d4_fields/check.py
python3 tableau/build/d4_fields/verify_sankey.py 2026-06-30 "" > sankey.svg
python3 tableau/build/d4_fields/build_sankey.py "in.twb" "out.twb"
```

Run on 2026-10-25: 142 `Sk` calcs and 3 parameters; `check.py` 374 formulas, no problems; `verify_sankey.py` matches the design at Jun 2026, Dec 2024 and Jun 2026 with Marketing.
