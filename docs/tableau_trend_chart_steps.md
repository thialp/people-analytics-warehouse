# Headcount & FTE Walk: the trend chart (top right)

Top-right card (x 848, y 188, 496 × 300). It shows closing headcount (or FTE, following the toggle) for every month-end, with the period you are looking at shaded. It is an analysis, not a control: the period is chosen with the two dropdowns in the header.

## 1. Build the sheet `Trend`

1. New worksheet, named **Trend**.
2. **Filter** `Movement Category` → keep **Closing** only. No date filter: the chart shows all 48 months so the shaded period has context.
3. **Columns:** `Month End Date`, Exact Date, continuous (green pill).
4. **Rows:** `SUM(Selected Value)` (follows the Measure toggle). One pill is enough. If you built the second copy and the invisible circle layer for the picker idea, remove it: right-click the second pill on Rows → **Remove**, and the axis goes back to a single one.
5. Marks: type **Line**, color teal `#00938D`, width 2 px.
6. **Shading for the selected period.** Create:
   ```
   // Band Start   (the month-end before the start month: the walk opens there)
   DATEADD('day', -1, DATETRUNC('month', [Start Month]))
   ```
   Right-click the **horizontal date axis at the bottom** (not the vertical axis, which only offers numbers) → **Add Reference Line** → **Band** tab → Scope **Per Pane**. From → Value: `Band Start` (Minimum). To → Value: `End Month`. Fill: solid `#DDEFEB` (open the Fill menu → More Colors… and type the hex; the band has no opacity setting). Line **None**, label **None**. Do not use the line's teal for the band, or the line disappears.
7. **Label only the latest point:** on the line, Label → Show mark labels → *Marks to label* **Most Recent**, Tableau Semibold 9 pt navy `#13233A`, number format `#,##0`.
8. **Axes:**
   - Vertical: Edit Axis → untick **Include zero**, clear the title; number format Custom `#,##0,"k"` (11k, 12k, 13k); gridlines `#E4E3DD`.
   - Horizontal: clear the title; Edit Axis → Tick Marks → Major **Fixed**, origin 7/1/2022, interval 1 Year; Format → Dates → Custom `mmm yy` (Jul 22, Jul 23 …: the fiscal-year starts).
   - Axis fonts Tableau Book 8 pt slate `#5A6170`; no axis rulers.
9. **Title:**
   ```
   // Trend Title
   IF [Measure] = "Headcount" THEN "Closing headcount by month-end" ELSE "Closing FTE by month-end" END
   ```
   Drag it to **Detail**, Worksheet → Show Title, double-click the title, Insert `Trend Title` (Tableau Bold 12 pt navy). Second line (Tableau Book 9 pt slate): `Selected period shaded`.
10. **Tooltip** (the default lists every field; replace it): `<Month End Date>` in Tableau Semibold, a new line `<SUM(Selected Value)>`. Untick *Include command buttons*.
11. **Look:** Format → Shading: Worksheet and Pane `#FBFBF8`; no borders.
12. Optional annotation of the FY24 dip: right-click the lowest point → Annotate → Mark → `FY24 restructuring`, Tableau Book 8 pt slate, no border.

## 2. Place it on the dashboard

Float **Trend** at x **848**, y **188**, w **496**, h **300**. Background `#FBFBF8`, Border 1 px `#E4E3DD`, Corner Radius **10** on all four corners (same as the waterfall card).

## 3. Check (FY26: Start Jul 2025, End Jun 2026)

| Check | Expected |
|---|---|
| Latest label | 13,201 at the last point (Headcount) |
| Band | The last twelve months, ending at Jun 2026; it moves when you change the dropdowns |
| Toggle FTE | Title "Closing FTE by month-end"; last label 12,940 |
