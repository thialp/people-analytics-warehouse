# Headcount & FTE Walk: header dropdowns, final look

Back to two plain dropdowns (Start Month, End Month): the controls people already understand, styled to sit cleanly on the header band. The capsule toggle and the info button stay as they are.

## Layout (all floating, y 22)

| Object | x | y | w | h |
|---|---|---|---|---|
| Title text | 256 | 10 | **560** | 58 |
| Start Month | 840 | 22 | 146 | 32 |
| End Month | 996 | 22 | 146 | 32 |
| Measure Toggle (capsule) | 1152 | 22 | 150 | 32 |
| Info button | 1312 | 22 | 32 | 32 |

The title text is widened to 560 so the subtitle is not cut off; it ends at x 816, clear of the dropdowns. 10 px gaps between controls; right edge 1344, aligned with the cards.

## Style the two dropdowns

For each of **Start Month** and **End Month** (select the object on the dashboard, Layout pane):
1. **Corner Radius:** 0 on all four corners (they are 16 now).
2. **Background:** white `#FFFFFF`. **Border:** None.
3. **Outer padding** 0 on all sides; **Inner padding** 0.
4. Size and position from the table above.
5. Control title off (the dropdown's own arrow menu → untick **Show Title**); the label already says "From Nov 2024" / "To Aug 2025" via the display format.
6. Font: right-click the control → **Format** → Font: Tableau Semibold, 9 pt, navy `#13233A`. Tableau draws the arrow and thin border itself, which gives the plain square box you asked for.

Only the capsule (a drawn shape, rounded 16) and the info icon stay round, so inputs read as inputs and the buttons read as buttons.

## Subtitle

Edit the title text object. Line 2 (Tableau Book 9 pt, `#C9D1DC`):

`Why headcount moved over the period · reconciles to the month-end snapshot`

## If a reversed pair is chosen

Nothing breaks: the cards show "—" and the waterfall title reads "Choose a start month on or before the end month". Tableau cannot limit one dropdown by another, so this is the guard.

## Check

| Check | Expected |
|---|---|
| Header | Title and subtitle fully visible; two square white dropdowns, then the capsule, then the "i" button; right edge at 1344 |
| Dropdown text | "From Nov 2024" and "To Aug 2025" style, navy, no control title |
| Trend chart | Still in the top-right card, band follows the dropdowns |
