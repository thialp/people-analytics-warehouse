# Who Leads Where workbook builder

Writes the Who Leads Where workbook (case study 7, Leadership Scope & Org Design) from the base workbook that Tableau saves right after the Custom SQL is connected and extracted. The base holds only the connection; the builder writes 422 calculations, 92 worksheets (light and dark), one 1400 × 850 dashboard of containers and 180 actions. [Live on Tableau Public](https://public.tableau.com/app/profile/thialp/viz/WhoLeadsWhereArcadiaSystems/WhoLeadsWhere). The [build guide](../../../docs/projects/leadership-scope/who_leads_where_build.md) covers the whole run, the check tables, the click tests and publishing.

| File | What it does |
|---|---|
| `d7_calcs.py` | Every calculation in plain names: the focus leader's FIXED reads, the KPIs and headline, the tree, the toggles, the picker, the calendar, the alignment panel, the Team pulse, and the context filters that keep each sheet to the rows it needs and return nothing while it is hidden |
| `build_d7.py` | The sheets, the dashboard zones and their Dynamic Zone Visibility, the parameter, deselect and link actions. Uses Dashboard #6's .twb writer (`../d6/twb.py`) |
| `make_shapes_d7.py` | Draws the 52 toggle, button, dot and brand shapes, light and dark |
| `make_cards_d7.py` | Draws the card pictures under the two map-layer sheets (the five KPI cards and the six Team pulse tiles), light and dark, at 2x; `images/` holds them |
| `shapes/` | The same 52 shapes, ready to copy into `My Tableau Repository/Shapes/Arcadia D7` |
| `check_values.py` | Every number the page shows for four check leaders, from the marts. `--verify` checks the closures and the ties |

```
python3 tableau/builder/d7/check_values.py --verify
D4_TWB="…/Arcadia CW Reconciliation.twb" D7_BRAND="…/Shared/Brand/" D7_IMAGES="…/7 Who Leads Where/Images/" python3 tableau/builder/d7/build_d7.py who_leads_where.twb "Who Leads Where.twb"
```

Expected: `3506 leaders, 300359 leader-days; problems: 0`, then `calcs 422 sheets 92 zones 29 actions 180 (84 parameter)`. Close the workbook in Tableau first. Dashboard #4's workbook supplies the document-format manifest Tableau needs for parameter actions and rounded corners.
