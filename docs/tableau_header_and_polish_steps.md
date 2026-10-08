# Headcount & FTE Walk: header controls, waterfall polish, matching backgrounds

Three jobs on the dashboard you already have (1400 × 850, floating objects). Layout numbers come from the grid in the KPI cards guide.

## 1. Match the backgrounds

The page should be stone and every card off-white, so nothing looks "white on white".

1. **Dashboard → Format… → Dashboard shading** → `#F3F3EF`. (Your canvas currently shows pure white.)
2. **Each chart sheet** (Waterfall now, the others as you build them): on the sheet, **Format → Shading**:
   - Worksheet: `#FBFBF8`
   - Pane: `#FBFBF8`
   - Row Banding / Column Banding: none
   Also **Format → Borders**: Row Divider and Column Divider none.
3. **Waterfall Caption** sheet: Worksheet shading `#FBFBF8` too, so it blends into the card (you float it over the card's bottom padding).
4. **KPI cards** sheet: keep the background **None** (the card image sits underneath).
5. Waterfall card on the dashboard (select it → Layout pane): Background `#FBFBF8`, Border 1px `#E4E3DD`.

## 2. Cleaner waterfall axis and labels

Today the axis runs 0K to 16K in steps of 2K and the category names wrap. The prototype shows 0, 5k, 10k, 15k, signed labels and short names.

1. **Axis ticks.** Right-click the vertical axis → **Edit Axis** → *Tick Marks* tab → Major tick marks **Fixed**, tick every **5000**; tick Minor: None. Clear the axis title. **Format axis** → Numbers → Custom → `#,##0,"k"` (shows 5k, 10k, 15k). Keep **Include zero** on.
   - This fits the company view. If you later let a filter shrink the numbers (a single department, say), switch the tick interval back to **Automatic**.
2. **Short category names.** Right-click each header on the chart → **Edit Alias**:
   - Voluntary Terminations → `Voluntary leavers`
   - Involuntary Terminations → `Involuntary leavers`
   (Opening, Hires and Closing already read well.)
3. **Signed labels** (+2,354, −1,341; totals unsigned). Create two measures:
   ```
   // Move Label
   IF ATTR([Movement Category]) <> "Opening" AND ATTR([Movement Category]) <> "Closing"
   THEN SUM([Walk Value]) END
   ```
   ```
   // Level Label
   IF ATTR([Movement Category]) = "Opening" OR ATTR([Movement Category]) = "Closing"
   THEN SUM([Walk Value]) END
   ```
   Set the number format of `Move Label` to Custom `+#,##0;−#,##0;0` and `Level Label` to Custom `#,##0`. On the Marks card, **remove** the current label measure from Label, then drag both new fields onto **Label**. Open Label → Text and put them on one line: `<Move Label><Level Label>` (only one of the two has a value for any bar). Font Tableau Semibold 9 pt navy `#13233A`.
4. **Gridlines.** Format → Lines → Gridlines: light `#E4E3DD`, thin; Zero line: slightly darker `#8C8A84`. Axis rulers off.
5. Fonts: axis labels Tableau Book 8 pt slate `#5A6170`.

## 3. Header band: text

Edit the **Title** text object (x 256, y 10, 470 × 58): line 1 `Headcount & FTE Walk` (Tableau Bold 18 pt, white `#FFFFFF`); line 2 (Tableau Book 9 pt, `#C9D1DC`):

`How the workforce changed over the selected period, and why · every line reconciles to the month-end snapshot`

## 4. Header band: Start Month and End Month controls

1. On the Data pane right-click the parameter **Start Month** → **Properties…** → **Display format** → **Custom** → `"Start "mmm yyyy`. (If your version does not accept text in the format, use `mmm yyyy` and turn on the control's title instead.) Do the same for **End Month** with `"End "mmm yyyy`.
2. Right-click each parameter → **Show Parameter**. In the dashboard, click the control's dropdown arrow → **Single Value (Dropdown)** (compact) and untick **Show Title** (unless you used the title trick).
3. Make each control floating (the object's small menu → **Floating**) and set Layout pane values:

| Control | x | y | w | h |
|---|---|---|---|---|
| Start Month | 744 | 22 | 140 | 32 |
| End Month | 892 | 22 | 140 | 32 |

4. Layout pane: Background `#FFFFFF`, Outer padding 0. Format the control font Tableau Semibold 9 pt navy.
5. Put a start-before-end guard in the title: the `WF Title` field already says "Choose a start month on or before the end month" when `K Valid` is false.

## 5. Header band: Headcount / FTE pills (no images)

The selected state is driven by the **Measure** parameter itself, so there is no image per state.

1. Create these fields:
   ```
   // Measure Option
   IF [Movement Category] = "Opening" THEN "Headcount"
   ELSEIF [Movement Category] = "Closing" THEN "FTE"
   END
   ```
   ```
   // Option State
   IF [Measure Option] = [Measure] THEN "On" ELSE "Off" END
   ```
2. New worksheet **Measure Toggle**:
   - Filter `Measure Option` → exclude **Null**.
   - Columns: `Measure Option` (two cells side by side). Rows: nothing.
   - Marks: type **Square**, size at maximum so it fills each cell; `Option State` on **Color**: On = `#FFFFFF`, Off = `#243A57`; `Measure Option` on **Label** (alignment middle-center, Tableau Semibold 9 pt; leave the label color on **Automatic**, which gives dark text on white and white text on the dark pill).
   - Hide the column header (right-click → Show Header off), remove borders and gridlines, Worksheet shading `#13233A`, tooltips off, **Entire View**.
3. Float it at **x 1044, y 22, 150 × 32** above the header band.
4. **Dashboard → Actions → Add Action → Change Parameter**: Source sheet *Measure Toggle*, run on **Select**, Target parameter **Measure**, Source field `Measure Option`, aggregation None. Set *Clearing the selection will* **Keep current value**.

## 6. Header band: Methodology button

1. For now use a **Navigation** button (Objects → Navigation, floating): *Navigate to* the Methodology dashboard (create an empty dashboard named **Methodology** so the button has a target), title `Methodology`, button background `#243A57`, text white.
2. Float it at **x 1204, y 22, 140 × 32**.

## 7. Check (FY26)

| Check | Expected |
|---|---|
| Canvas | Stone `#F3F3EF`; cards off-white; no white box visible inside the waterfall card |
| Axis | 0, 5k, 10k, 15k; no axis title |
| Labels | 12,510 · +2,354 · −1,341 · −322 · 13,201 |
| Categories | Opening, Hires, Voluntary leavers, Involuntary leavers, Closing |
| Pills | Click FTE: the waterfall switches to FTE, the FTE pill turns white and Headcount turns dark, and the FTE Changes bar appears |
| Start/End | Setting Start after End makes the KPI values "—" and the title read "Choose a start month on or before the end month" |
