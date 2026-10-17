# Arcadia shapes for Tableau

Tableau lists a shape palette in file-name order, shows white-on-transparent shapes as blank squares on its white palette, and every dashboard adds more files. So shapes are organised by dashboard and every file name says where it is used.

| Folder | Palette name in Tableau | Used by |
|---|---|---|
| `by_dashboard/shared` | `Arcadia Shared` | ⓘ and ✕ buttons, Summary \| By driver toggle, expand/collapse icons (both dashboards) |
| `by_dashboard/d1` | `Arcadia D1` | Dashboard #1 Headcount & FTE Walk |
| `by_dashboard/d2` | `Arcadia D2` | Dashboard #2 Compensation Walk |
| `by_dashboard/fp` | `Arcadia FP` | Global Workforce Footprint |
| `Arcadia` | `Arcadia` | Generator output and the palette Dashboard #1 was **published** with. Leave it alone until #1 is republished on the new names |
| `index/` | (not copied) | One picture per folder: every shape on the background it is drawn on, with its file name. Keep it open beside Tableau |

**Names:** `<scope>_<sheet>_<option>_<state>.png`, lower case. Examples: `d2_lens_fte_on`, `d2_lens_payroll_off`, `d2_field_capsule`, `d2_reset`, `shared_detail_summary_on`. The scope sorts the list, the sheet and option read like the dashboard, `on`/`off` is the toggle state. A new dashboard adds a scope (`d3_...`) and a folder; nothing else is renamed.

**`fld_top` vs `fld_rail`** (now `d1_field_capsule` / `d2_field_capsule`): the same white capsule; the top-bar one is 180 wide for the header and the rail one is 200 wide for the left rail. Only the width differs.

**Rebuild:** run the `make_*_shapes.py` generators, then `python3 docs/brand/build/organize_shapes.py`.

**Copy to Tableau (Mac):**
```
cd ~/GitHub/people-analytics-warehouse/docs/brand/shapes/by_dashboard
for s in shared:Arcadia\ Shared d1:Arcadia\ D1 d2:Arcadia\ D2 fp:Arcadia\ FP; do
  mkdir -p ~/Documents/My\ Tableau\ Repository/Shapes/"${s#*:}"
  cp ${s%%:*}/*.png ~/Documents/My\ Tableau\ Repository/Shapes/"${s#*:}"/
done
ls ~/Documents/My\ Tableau\ Repository/Shapes | grep Arcadia
```
Expected: `Arcadia`, `Arcadia Shapes`, `Arcadia D1`, `Arcadia D2`, `Arcadia FP`, `Arcadia Shared`.
