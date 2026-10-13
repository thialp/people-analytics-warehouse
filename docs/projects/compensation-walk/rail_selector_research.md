# Rail selectors: research on picking a group from a long list

Research for the Compensation Walk filter rail, written 2026-10-10 (night) for review on 2026-10-11. The question: how to pick one group (up to 35 values) in an elegant way, given that Tableau parameters cannot depend on each other and that a clicked mark stays highlighted. The company is fictional and all data is synthetic.

## The short answer

1. **The blue selection box has a known fix** that we did not use last night: the "auto-deselect" filter action (two calcs, `zzTrue` and `zzFalse`, and a filter action from the list sheet onto itself). Tableau re-draws the marks and the selection disappears. It is documented by InterWorks, phData and The Data School, and InterWorks uses it on a list sheet driven by parameter actions, which is our case. With it, the pill workaround is optional.
2. **For the Group list, the recommendation is a popover picker**: the rail shows one field ("Atlanta ▾"); clicking it opens a floating panel over the page with all groups of the current view in three columns (35 offices fit without scrolling), and picking one sets `p_Group` and closes the panel. Built from Dynamic Zone Visibility, a Boolean parameter and parameter actions; no extension.
3. **Tableau has added nothing native** for this in 2025.1 to 2026.2: no dependent (cascading) parameters, no "disable selection" for worksheets, no restyled dropdowns. The only "disable selection" setting found is on map layers. Multi-select and targeted parameter actions arrived in Tableau Next only, not in Desktop or Public.

## Group counts (from `data/marts/mart_compensation_walk.csv`)

| View | Groups | `group_parent` holds | Longest name |
|---|---|---|---|
| Company | 1 | (none) | |
| Function | 8 | Arcadia Systems | |
| Leader | 10 | Function | 18 |
| Department | 31 | Function (2 to 8 each) | 27 |
| Office | 35 | Country (22 countries, mostly 1 office each) | 13 |
| Country | 22 | Region (5) | 20 |

Office and Department are the hard cases. Grouping offices by country would give 22 one-line headings, so the panel lists them alphabetically; a region heading would need a new column (see option A, extra).

## Findings

### 1. Auto-deselect (removes the blue box)

Set-up as documented by InterWorks:

1. Calcs `zzTrue` = `TRUE` and `zzFalse` = `FALSE`.
2. Put both on Detail of the list sheet (`Rail View`, `Rail Group`, and any button sheet).
3. Dashboard > Actions > Add Action > **Filter**: source = the list sheet on this dashboard; target = **the same sheet**; Run on Select; Target Filters = Selected Fields, source `zzTrue` → target `zzFalse`; **Clearing the selection will: Show all values** (InterWorks warns that other clearing options can make the sheet disappear).
4. Keep the existing Change Parameter actions; they still fire on the click, then the filter action clears the selection.

phData and The Data School also add a Highlight action on `zzTrue` (hover); InterWorks does not need it. Try without first.

Why it works: the filter action re-generates the sheet's marks, and a re-generated mark is no longer selected (InterWorks' explanation). Not verified on our workbook yet; test 1 below.

### 2. Native parameter controls

- A list parameter shows as a single-value dropdown (compact list), radio buttons, slider or type-in. Only the control's fonts and shading can be formatted; the open dropdown list keeps Tableau's own look.
- "When workbook opens" lists refresh only at open (or a data refresh). They cannot follow another parameter, so one control cannot show only the groups of the chosen view.
- The help page does not say whether a calculated field can feed a dynamic list. Not needed for the options below.

### 3. Extensions

- Tableau's own **Data-Driven Parameters** extension (fills a parameter list from a sheet's field) was archived on 2025-08-23 and is "as-is".
- Tableau Public runs **sandboxed extensions only** (Infotopics, March 2026); the listed ones are chart types, not dropdowns or pickers.
- Not recommended: it adds a dependency a reviewer cannot see in the workbook, and Public support is uncertain.

### 4. Dynamic Zone Visibility (DZV)

- Drives visibility from a Boolean field or parameter that is single-valued and independent of the viz.
- The help page lists Desktop, Server and Cloud; DZV dashboards are common on Tableau Public. Our Expand / Collapse cards already use show-and-hide by parameter, so publishing will confirm it.

### 5. Community patterns for selectors

- **Selection panel with parameter actions** (datavis.blog): constant-1 bars on a 0 to 1 axis, color by "is selected", plus the deselect filter action. This is close to our pill build.
- **Cascading "parameters" with set actions** (Sons of Hierarchies): a stack of bars showing the current pick, each with a show/hide button that opens a list beneath it. This is the closest published example of a dropdown built from sheets.
- **Multi-value parameter lists** (InterWorks, 2024): radio-style circles as a column of a list sheet, the deselect action, and a reset button sheet.

## Options for the Group selector

### A. Popover picker (recommended)

How it looks:
- **Rail (y 508):** one field, 176 x 30. Slightly lighter navy (`#1D3150`), 1 px border `#5A6170`, white text "Atlanta", a ▾ at the right.
  - Under Company view it reads "Arcadia Systems" and is greyed (or hidden by DZV).
- **Click the field:** a light card (`#FBFBF8`, 1 px border `#E4E3DD`, radius 10) floats beside the rail, anchored next to the field.
  - Header: "Choose an office" and a ✕.
  - Body: all groups of the view in three columns, 20 px rows, 10 pt.
  - The current group is navy and bold with a teal ●; the others are slate.
- **Click a group:** the dashboard filters, and the panel closes.

Why this one:
- It answers the "long list" problem directly. Even Office (35 rows) fits in 12 rows x 3 columns, about 300 px tall, so nothing scrolls.
- The rail stays calm: one line per control, like a form.
- The same pattern can serve the Period picker later (columns: Fiscal year, Year to date, Quarter, Month). The rail then speaks one design language.
- Everything is native Tableau (DZV, parameter actions, table calcs), so it can be explained in an interview and seen in the workbook.

Build outline (to walk through together):

1. **Parameter `p_GroupOpen`** (Boolean, default False).
2. **Calcs**
   ```
   // Group Field Text      (rail field)
   [p_Group] + "  ▾"

   // Toggle Group Panel    (source field for the rail field's action)
   NOT [p_GroupOpen]

   // Close Panel           (source field for the panel's second action)
   FALSE

   // Group Is Current
   [group_name] = [p_Group]

   // Pick Rows             (table calc: rows per column, 3 columns)
   INT((SIZE() + 2) / 3)

   // Pick Col              (table calc, make Discrete)
   INT((INDEX() - 1) / [Pick Rows])

   // Pick Row              (table calc, make Discrete)
   (INDEX() - 1) - [Pick Col] * [Pick Rows]
   ```
   All three table calcs: Compute Using Specific Dimensions `group_name` only, sorted by `group_name` alphabetically (Edit Table Calculation > Sort order). This sort is set inside the table calc, not by a label. Last night's bug (Atlanta moved to the end) came from sorting by a label that changes when you click.
   - `INT()` on a table calc should work, but `FLOOR()` failed on the waterfall, so this is the first thing to test.
3. **Sheet `Group Field`:**
   - One text mark showing `Group Field Text`.
   - `Toggle Group Panel`, `zzTrue` and `zzFalse` on Detail.
   - Filter `In Pair` / `In Period` as on the other sheets, so it returns a single row.
4. **Sheet `Group Panel`:**
   - Columns `Pick Col` and Rows `Pick Row` (both discrete, headers hidden).
   - Text `Group Label`, color `Group Is Current`.
   - Detail `group_name`, `Close Panel`, `zzTrue` and `zzFalse`.
   - Filter `Group In View` = True.
   - Text alignment Left: in a table cell, left alignment works, unlike a text mark on an axis.
5. **Dashboard actions:**
   - Change Parameter: Group Field → `p_GroupOpen` ← `Toggle Group Panel`.
   - Change Parameter: Group Panel → `p_Group` ← `group_name` (exists as "Set group"; re-point it).
   - Change Parameter: Group Panel → `p_GroupOpen` ← `Close Panel`.
   - Filter (deselect), from each of the two sheets onto itself: `zzTrue` → `zzFalse`, Show all values.
   - Also close the panel when the view changes: Rail View → `p_GroupOpen` ← `Close Panel`, so a stale panel never shows.
6. **Layout:**
   - Floating vertical container `Group Popover` at about x 224, y 470, 624 x 300.
   - It holds the header (text "Choose a …" and a ✕ sheet that also sets `p_GroupOpen` ← `Close Panel`) and `Group Panel`.
   - Control visibility using value: `p_GroupOpen`.
   - Put it at the top of the floating order (last in the item hierarchy) so it covers the cards.

Extras, if wanted:
- **Search box:** a type-in string parameter `p_GroupSearch` in the panel header. Add a filter calc `CONTAINS(LOWER([group_name]), LOWER([p_GroupSearch]))`, which is True when the box is empty. Mainly useful if the lists grow; 35 items do not need it.
- **Region headings for Office:** add `group_region` to `custom_sql_compensation_walk.sql` (region of the office's country). Then the panel can use one column per region (5 columns, 2 to 13 offices each), like a mega-menu. This is a data change, so it is optional.
- **Parent context:** show `group_parent` in the tooltip ("Hyderabad · India", "Data Platform · Technology").

Risks to test:
- The deselect action and the parameter actions on the same click (InterWorks shows this combination working).
- DZV toggling from a parameter action that reads its own parameter.
- Whether the table-calc grid survives the view switch.
- The floating panel covering the waterfall on Tableau Public.

### B. One native dropdown per view, shown by DZV

- Five list parameters (`p_GroupFunction`, `p_GroupLeader`, `p_GroupDepartment`, `p_GroupOffice`, `p_GroupCountry`), each a single-value dropdown in the same rail spot. DZV shows only the one for the current view.
- A calc `Selected Group` (a CASE on `p_View`) replaces `p_Group` in every filter.
- **Pros:** native and accessible (keyboard, screen reader). Every view keeps its own last pick. Few moving parts.
- **Cons:**
  - The open list keeps Tableau's look (white, system font), so it reads less custom than the rest of the rail.
  - Five parameter lists to maintain (static lists, since the data does not change).
  - Every calc that reads `p_Group` changes.
  - Reset has to set five parameters.

### C. Keep the in-rail list, add the deselect action

- Return to the plain navy list (white and gray text, ● marker) with the deselect action, and give it more height or let it scroll.
- **Pros:** cheapest change.
- **Cons:** it does not solve "too many options in a small box", which was the complaint.

## Recommendation

- **View by:** keep the in-rail list (six options). Add the deselect action, then choose between the pill and the plain ● list with nothing stuck highlighted.
- **Group:** option A, the popover picker. Fall back to B if A's table-calc grid or the parameter-action toggle misbehaves on Public.
- **Period (stage 2):** reuse A's popover with four columns. Decide after A works.

## Tests for tomorrow, in order

1. Deselect action on `Rail View` (5 minutes). This settles whether the blue box can go everywhere.
2. `Group Panel` grid on its own sheet: `Pick Rows`, `Pick Col` and `Pick Row` with Office and Department, with alphabetical order kept after a click.
3. The `p_GroupOpen` toggle and DZV on the dashboard, with the panel closing on pick.
4. Publish a scratch copy to Tableau Public to confirm DZV, the floating panel and the actions work there.

## Sources

- [InterWorks: Tableau Hacks, Basic Apply, Reset and De-Highlight (2023)](https://interworks.com/blog/2023/09/26/tableau-hacks-basic-apply-reset-and-de-highlight)
- [InterWorks: Tableau Hacks, Multi-Value Parameters (2024)](https://interworks.com/blog/2024/02/21/tableau-hacks-multi-value-parameters/)
- [InterWorks: Tableau Hacks, Dynamic Parameters (2024)](https://interworks.com/blog/2024/02/26/tableau-hacks-dynamic-parameters/)
- [phData: Automatically Deselect Marks](https://www.phdata.io/blog/automatically-deselect-marks/)
- [The Data School: How to Automatically Deselect in Tableau](https://thedataschool.co.uk/stephen-moyse/how-to-automatically-deselect-in-tableau)
- [datavis.blog: Creating a selection panel with parameter actions](https://datavis.blog/2019/12/18/creating-a-selection-panel-with-parameter-actions/)
- [Sons of Hierarchies: Cascading "parameters" with set actions](https://sonsofhierarchies.com/2019/11/19/creating-cascading-parameters-in-tableau-with-set-actions/)
- [VizPainter: Dynamic parameters in Tableau](https://vizpainter.com/dynamic-parameters-in-tableau/)
- [Tableau Help: Create Parameters](https://help.tableau.com/current/pro/desktop/en-us/parameters_create.htm)
- [Tableau Help: Use Dynamic Zone Visibility](https://help.tableau.com/current/pro/desktop/en-us/dynamic_zone_visibility.htm)
- [Tableau Help: Filter Actions](https://help.tableau.com/current/pro/desktop/en-us/actions_filter.htm)
- [GitHub: tableau/extension-data-driven-parameters (archived)](https://github.com/tableau/extension-data-driven-parameters)
- [Infotopics: Trusted Extensions on Tableau Public (2026)](https://appsfortableau.infotopics.com/topic/releases/trusted-extensions-now-available-on-tableau-public/)
- [Flerlage Twins: New features in 2025.2 (map layer "disable selection")](https://www.flerlagetwins.com/2025/06/new-features-1.html)
- [Tableau: 2026.1 features](https://www.tableau.com/2026-1-features), [all releases](https://www.tableau.com/products/new-features), [2025 community-driven features](https://www.tableau.com/blog/tableau-community-driven-innovation-2025)
