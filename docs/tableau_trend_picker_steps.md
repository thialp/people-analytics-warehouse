# Headcount & FTE Walk: the trend chart that picks the period

Top-right card (x 848, y 188, 496 × 300). It shows closing headcount (or FTE, following the toggle) for every month-end, shades the period you are looking at, and **is the period picker**: drag across months and the start and end months, the KPI cards, the waterfall and its title all follow. A reversed range cannot be selected.

Order of work: build the sheet (Part 1), place it (Part 2), add the two actions (Part 3), then remove the two dropdowns (Part 4). Until Part 3 is done, nothing about the dropdowns changes, so the clean-up of the `From (pick)`, `To (pick)`, `Range Start` and `Range End` fields is just tidying and can be done any time.

## 1. Build the sheet `Trend`

1. New worksheet, named **Trend**.
2. **Filter** `Movement Category` → keep **Closing** only. (No date filter: the chart shows all 48 months so you can choose any period from it.)
3. **Columns:** `Month End Date`. Right-click the pill → **Exact Date**, then right-click again → **Continuous** (green pill). It must be Exact Date: your Start Month and End Month parameters hold month-end dates, and the action will pass exactly the dates on this axis. A month-truncated axis passes the 1st of the month and the parameter will not accept it.
4. **Rows:** `SUM(Selected Value)` (it follows the Measure toggle).
5. Marks card, line layer: type **Line**, color teal `#00938D`, line width 2 px.
6. **Picker layer.** Drag a second `SUM(Selected Value)` onto Rows next to the first, right-click it → **Dual Axis**, right-click the right axis → **Synchronize Axis**, then hide the right axis (untick Show Header). On the Marks card for the second field: type **Circle**, size about 60% of the slider, **Color opacity 0%**. These invisible circles are what you drag across; they are easier to hit than a thin line.
7. **Shading for the selected period.** Create:
   ```
   // Band Start   (the month-end before the start month: the walk opens there)
   DATEADD('day', -1, DATETRUNC('month', [Start Month]))
   ```
   Right-click the **horizontal date axis at the bottom** (the one with Nov 1, 24 and so on; **not** the vertical value axis, which only offers numbers) → **Add Reference Line** → **Band** tab → Scope **Per Pane**. From → Value: `Band Start` (Minimum). To → Value: `End Month` (the parameter). Both appear in the lists only on the date axis, because they are dates. If a band already exists on the vertical axis, right-click it and **Remove** it first. Fill: teal `#00938D` at 12% (Format → color with transparency), line **None**, label **None**. If Tableau does not list `Band Start`, choose the `Start Month` parameter instead (the band then begins at the start month's month-end, one month later; fine for a first version).
8. **Label only the latest point.** On the line layer: Label → Show mark labels → *Marks to label* **Most Recent**, font Tableau Semibold 9 pt navy `#13233A`, alignment right. Number format `#,##0`.
9. **Axes.**
   - Vertical axis: Edit Axis → untick **Include zero** (this is a line, not bars), clear the title; Format number Custom `#,##0.0,"k"`; gridlines light `#E4E3DD`.
   - Horizontal axis: clear the title; Edit Axis → Tick Marks → Major: **Fixed**, origin 7/1/2022, interval 1 Year; Format → Dates → Custom `mmm yy`. The ticks then read Jul 22, Jul 23, Jul 24, Jul 25, which are the fiscal-year starts.
   - Fonts: axis labels Tableau Book 8 pt slate `#5A6170`. Remove the axis rulers.
10. **Title.** Create:
    ```
    // Trend Title
    IF [Measure] = "Headcount" THEN "Closing headcount by month-end" ELSE "Closing FTE by month-end" END
    ```
    Drag it to **Detail** (constant, no extra marks), then Worksheet → Show Title, double-click it, Insert `Trend Title` (Tableau Bold 12 pt navy). Add a second line (Tableau Book 9 pt slate): `Drag across months to choose the period · selected period shaded`.
11. **Tooltip:** `<Month End Date>` (Tableau Semibold) and `<SUM(Selected Value)>`. Last line in slate: `Drag across months to set the period`. Untick *Include command buttons*.
12. **Look:** Format → Shading: Worksheet and Pane `#FBFBF8`; no borders, no gridline verticals.
13. Optional annotation of the FY24 dip: right-click the lowest point → Annotate → Mark → `FY24 restructuring`, Tableau Book 8 pt slate, no border.

## 2. Place it on the dashboard

Drag **Trend** onto the dashboard and make it **Floating**. Layout pane: x **848**, y **188**, w **496**, h **300**. Background `#FBFBF8`, Border 1 px `#E4E3DD`, Corner Radius **10** on all four corners (same as the waterfall card).

## 3. The two actions (this is the picker)

**Dashboard → Actions → Add Action → Change Parameter**, twice:

| | Action 1 | Action 2 |
|---|---|---|
| Name | Pick start | Pick end |
| Source sheet | Trend | Trend |
| Run action on | Select | Select |
| Target parameter | Start Month | End Month |
| Source field | Month End Date | Month End Date |
| Aggregation | **Minimum** | **Maximum** |
| Clearing the selection will | Keep current value | Keep current value |

Test: drag a box across Jul 2025 to Jun 2026 on the chart. Start becomes Jul 2025, End becomes Jun 2026, the band moves, the cards and waterfall recalculate. Click a single month: a one-month walk. If a drag does nothing, check that the pill is **Exact Date** and that the action source is the **Trend** sheet, not the dashboard.

If Tableau fades the line after a selection, that is its standard "unselected" look; the invisible circles carry the selection, so the visible line should stay bright. The shaded band is the real indicator of the period.

## 4. Remove the dropdowns

Select **Start Month** and **End Month** on the dashboard and delete them (the parameters stay in the workbook; only the controls go). Move the Headcount | FTE capsule and the info button right to close the gap, for example the capsule at x 1152 and the info button at x 1312 as before; there is room on the left for a short line of text: `Select months on the trend chart to change the period`, Tableau Book 9 pt, `#C9D1DC`, at x 840, y 30.

## 5. Optional: fiscal-year chips

A small sheet **FY Chips** gives one-click periods:
1. Columns: `Fiscal Year Label` (from the month dimension: FY23, FY24, FY25, FY26). Rows: nothing. Detail: `Month End Date` (Exact Date, so each chip holds its twelve months).
2. Marks: **Square**, small, colored by `Fiscal Year Label` in a single light gray with the label on **Text**; hide headers and gridlines; Entire View; Worksheet shading `#13233A`.
3. Add two more Change Parameter actions, same as Part 3 but with Source sheet **FY Chips** (Minimum to Start Month, Maximum to End Month).
4. Float it in the header at x 840, y 22, h 32 (about 240 wide) in place of the dropdowns.

Clicking FY26 passes all twelve months of FY26, so Minimum gives Jul 2025 and Maximum gives Jun 2026.

## 6. Check (FY26)

| Check | Expected |
|---|---|
| Latest label | 13,201 at the last point (Headcount) |
| Band | Covers the last twelve months, ending at Jun 2026 |
| Drag Jul 2025 to Jun 2026 | Cards: Closing 13,201, Hires 2,354; waterfall title "FY26: 2,354 hires outpaced 1,663 leavers, adding 691 people" |
| Click Aug 2025 only | Title "Aug 2025: …", one-month walk |
| Toggle FTE | Chart switches to FTE; title "Closing FTE by month-end"; last label 12,940 |
| Reversed range | Not possible with the chart as the only picker |
