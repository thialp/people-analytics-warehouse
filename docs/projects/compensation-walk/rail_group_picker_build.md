# Rail group picker: build steps

Step-by-step build for the Group selector in the Compensation Walk rail. Background and sources: [rail_selector_research.md](rail_selector_research.md). Data source for every calc and sheet: the walk (`ArcadiaHR`).

What you build:
- **Part 1:** the blue selection box disappears (`Rail View` first).
- **Part 2:** a rail field "Atlanta ▾" opens a panel listing every group of the current view in three columns. Clicking a group sets it and closes the panel.

Test each part before starting the next.

---

## Part 1. Remove the blue selection box

### 1.1 Two calcs

| Name | Formula |
|---|---|
| `zzTrue` | `TRUE` |
| `zzFalse` | `FALSE` |

### 1.2 Put them on `Rail View`

On the **All** Marks card, drag `zzTrue` and `zzFalse` to **Detail**.

### 1.3 Filter action

Dashboard > Actions > Add Action > **Filter**:

| Setting | Value |
|---|---|
| Name | `Deselect Rail View` |
| Source sheets | Summary: **Rail View** only |
| Run action on | Select |
| Target sheets | the **worksheet** `Rail View` itself, listed on its own in the Target Sheets box, NOT the `Summary (Rail View)` entry under the dashboard (InterWorks: "the sheet itself, not the dashboard instance") |
| Clearing the selection will | **Show all values** |
| Filter | Selected Fields: Source `zzTrue` → Target `zzFalse` |

### 1.4 Test

Click "Function" in the rail.

| Expected | If not |
|---|---|
| The view changes and **no blue box** stays on the row | Check that the target sheet is `Rail View` and the fields are True → False |
| The list stays visible | Clearing must be **Show all values**; the other two options can hide the sheet |

Once this works, the pill is optional. You can keep it, or go back to the plain list (white text for the current row, gray for the others, `●` marker).

---

## Part 2. Group picker

### 2.1 Parameter

| Name | Type | Current value |
|---|---|---|
| `p_GroupOpen` | Boolean | False |

### 2.2 Calcs

| Name | Formula | Note |
|---|---|---|
| `Group Field Text` | `[p_Group] + "  ▾"` | Text in the rail field |
| `Toggle Group Panel` | `NOT [p_GroupOpen]` | Opens or closes the panel |
| `Close Panel` | `FALSE` | Closes the panel |
| `Has Groups` | `[p_View] <> "Company"` | Hides the field under Company |
| `Panel Title` | see below | Panel heading |
| `Pick Rows` | `INT((SIZE() + 2) / 3)` | Rows per column, for 3 columns |
| `Pick Col` | `INT((INDEX() - 1) / [Pick Rows])` | Column 0, 1 or 2 |
| `Pick Row` | `(INDEX() - 1) % [Pick Rows]` | Row in that column |

```
// Panel Title
"Choose " +
CASE [p_View]
    WHEN "Function"   THEN "a function"
    WHEN "Leader"     THEN "a leader"
    WHEN "Department" THEN "a department"
    WHEN "Office"     THEN "an office"
    WHEN "Country"    THEN "a country"
    ELSE "a group"
END
```

`Group Is Current` (`[group_name] = [p_Group]`) and `Group In View` (`[view_name] = [p_View]`) already exist.

Sizes this gives:

| View | Groups | Rows per column |
|---|---|---|
| Office | 35 | 12 |
| Department | 31 | 11 |
| Country | 22 | 8 |
| Leader | 10 | 4 |
| Function | 8 | 3 |

### 2.3 Sheet `Group Field` (the rail field)

1. New sheet `Group Field`. Marks type **Text**.
2. Text: `Group Field Text`.
3. Detail: `Toggle Group Panel`, `zzTrue`, `zzFalse`.
4. Format:
   - Font 10 pt, white `#FFFFFF`, Alignment **Left**, Middle.
   - Format > Shading: Worksheet and Pane **None**.
   - Format > Lines: all **None**.
5. Tooltip: off (Tooltip > uncheck **Show tooltips**).

It shows one mark, for example `Atlanta  ▾`.

### 2.4 Sheet `Group Panel` (the list in the panel)

1. New sheet `Group Panel`. Marks type **Text**.
2. Columns: `Pick Col`. Right-click it and choose **Discrete**.
3. Rows: `Pick Row`. Right-click it and choose **Discrete**.
4. Text: `Group Label` (now just `[group_name]`).
5. Color: `Group Is Current`. True navy `#13233A`, False slate `#5A6170`.
6. Detail: `group_name`, `Close Panel`, `zzTrue`, `zzFalse`.
7. Filters: `Group In View` = True.
8. Table calc set-up (the important step). Right-click `Pick Col` > **Edit Table Calculation**.
   - At the top, the dropdown "Nested Calculations" lists `Pick Col` and `Pick Rows`. Set **both** the same way.
   - Choose **Specific Dimensions** and tick **every** field in the list.
   - Drag `group_name` to the **top** of the list.
   - "At the level": Deepest. "Sort order": **Specific Dimensions**.
   - Do the same for `Pick Row` and its nested `Pick Rows`.

   Why every field: an unticked dimension splits the list. `Group Is Current` would put the current group in its own column. With `group_name` on top, the order is alphabetical, and a click does not move anything (that was last night's bug).
9. Headers: right-click the `Pick Col` and `Pick Row` headers and uncheck **Show Header**.
10. Format:
    - Font 10 pt, Alignment **Left**, Middle.
    - Shading None, Lines None, Row Banding None.
11. Title: Worksheet > Show Title. Edit Title to `<Panel Title>` (Insert > Panel Title), 12 pt, bold, navy `#13233A`.
12. Tooltip: off, or `<group_name> · <group_parent>` if you want the parent shown.

Check on the sheet itself (set `p_View` to Office): three columns of 12, 12 and 11 offices, alphabetical down each column.

| If you see | Fix |
|---|---|
| Error "INT cannot be applied to table calculations" | Tell me; there is a version without INT |
| Everything in one column, or one row per column | Revisit step 8; a dimension is not ticked |
| Not alphabetical | `group_name` is not at the top in step 8 |

### 2.5 Sheet `Panel Close` (the ✕)

1. New sheet `Panel Close`. Marks type **Text**.
2. Text: type `✕` in the Text editor. Or make a calc `Close Text` = `"✕"` and put it on Text.
3. Detail: `Close Panel`, `zzTrue`, `zzFalse`.
4. Font 12 pt, slate `#5A6170`, Center. Shading None, Lines None. Tooltip off.

### 2.6 Dashboard actions

Dashboard > Actions. All are on the Summary dashboard, and all are **Run action on: Select**.

| # | Name | Type | Source sheet | Target | Field | Notes |
|---|---|---|---|---|---|---|
| 1 | Open group panel | Change Parameter | Group Field | `p_GroupOpen` | `Toggle Group Panel` | Aggregation None |
| 2 | Set group | Change Parameter | **Group Panel** | `p_Group` | `group_name` | Edit the existing action: change the source from Rail Group to Group Panel |
| 3 | Close panel on pick | Change Parameter | Group Panel | `p_GroupOpen` | `Close Panel` | |
| 4 | Close panel on ✕ | Change Parameter | Panel Close | `p_GroupOpen` | `Close Panel` | |
| 5 | Close panel on view change | Change Parameter | Rail View | `p_GroupOpen` | `Close Panel` | |
| 5b | Set group from view | Change Parameter | Rail View | `p_Group` | `Default Group` | Must exist: without it, changing the view keeps the old group (for example Atlanta under Department) and every card goes blank |
| 6 | Deselect Group Field | Filter | Group Field | Group Field | `zzTrue` → `zzFalse` | Show all values |
| 7 | Deselect Group Panel | Filter | Group Panel | Group Panel | `zzTrue` → `zzFalse` | Show all values |
| 8 | Deselect Panel Close | Filter | Panel Close | Panel Close | `zzTrue` → `zzFalse` | Show all values |

For actions 1, 3, 4, 5 and 5b: "When clearing the selection" = **Keep current value**.

For the three Deselect filter actions (6 to 8, and `Deselect Rail View` from Part 1), the target is the **worksheet itself** (`Group Field`, `Group Panel`, `Panel Close`, `Rail View`), not the `Summary (...)` entry under the dashboard.

### 2.7 Dashboard layout

**Rail field**

1. In the `Rail` container, delete the `Rail Group` sheet. Put `Group Field` where it was, under the GROUP label.
2. `Group Field` item:

| Setting | Value |
|---|---|
| Size | 176 x 30 (x 20, y 508 inside the rail) |
| Background | `#1D3150` |
| Border | solid, 1 px, `#5A6170` |
| Corner radius | 4 |
| Inner padding | 8 left and right, 0 top and bottom |
| Control visibility using value | `Has Groups` |

**Popover**

3. Drag a **Vertical** container onto the dashboard as **Floating**. Rename it `Group Popover`.

| Setting | Value |
|---|---|
| Position | x 228, y 420 |
| Size | 624 x 330 |
| Background | `#FBFBF8` |
| Border | solid, 1 px, `#E4E3DD` |
| Corner radius | 10 |
| Inner padding | 16 all sides |
| Control visibility using value | `p_GroupOpen` |

4. Drag `Group Panel` **into** `Group Popover` (tiled inside it). Fit: **Entire View**.
5. Drag `Panel Close` onto the dashboard as **Floating**:

| Setting | Value |
|---|---|
| Position | x 812, y 432 |
| Size | 28 x 28 |
| Control visibility using value | `p_GroupOpen` |

6. Order: the popover must sit in front of every card. Select `Group Popover`, open the item's dropdown, and choose **Floating Order > Bring to Front**. Do the same for `Panel Close`. In the Item hierarchy, the front-most items are listed first.

Size check for Office: 12 rows x 22 px = 264. Adding the title (about 28) and padding (32) gives about 324, inside the 330 panel.

### 2.8 Test

| # | Do | Expected |
|---|---|---|
| 1 | Set View = Office in the rail | The rail field reads "Amsterdam ▾" (or the default group); the panel is closed |
| 2 | Click the rail field | The panel opens: "Choose an office", 35 offices in 3 columns, Amsterdam navy |
| 3 | Click "Atlanta" | Dashboard filters to Atlanta, the panel closes, the field reads "Atlanta ▾", no blue box anywhere |
| 4 | Open the panel again | Atlanta navy, order still alphabetical |
| 5 | Click ✕ | Panel closes, nothing else changes |
| 6 | Open the panel, then click "Department" in View by | Panel closes; the field shows the first department |
| 7 | Click Company | The rail field disappears |

When all seven pass, publish a scratch copy to Tableau Public and repeat tests 2, 3 and 5 there.

---

## Fallback: one native dropdown per view

Use this only if Part 2 fails (the grid or the toggle).

1. Five parameters, each a String List:
   - `p_GroupFunction`, `p_GroupLeader`, `p_GroupDepartment`, `p_GroupOffice`, `p_GroupCountry`.
   - Values: Add values from `group_name`, then delete the names that belong to other views. Or use Paste from Clipboard with the list for that view.
2. Calc `Selected Group`:
   ```
   CASE [p_View]
       WHEN "Function"   THEN [p_GroupFunction]
       WHEN "Leader"     THEN [p_GroupLeader]
       WHEN "Department" THEN [p_GroupDepartment]
       WHEN "Office"     THEN [p_GroupOffice]
       WHEN "Country"    THEN [p_GroupCountry]
       ELSE "Arcadia Systems"
   END
   ```
3. In every calc that reads `p_Group`, replace it with `Selected Group`. This covers both data sources: the walk and Office Moves.
4. Five Boolean calcs for visibility, for example `Show Office Picker` = `[p_View] = "Office"`.
5. Show the five parameter controls stacked in the same rail spot. Each one is a single-value dropdown, with "Control visibility using value" set to its `Show … Picker` calc.
