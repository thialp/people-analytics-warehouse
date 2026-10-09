# Headcount & FTE Walk: rounded header, capsule toggle, info panel

Replaces sections 4 to 6 of `tableau_header_and_polish_steps.md` (the pills and the Methodology button). Needs Tableau Desktop 2026.2 (native **Corner Radius** in the Layout pane). Everything is rounded to the same 10 px radius as the KPI cards, so the page reads as one system.

Final header layout (1400 wide, floating, y 22 for all controls):

| Object | x | y | w | h | Look |
|---|---|---|---|---|---|
| Start Month | 840 | 22 | 146 | 32 | white, radius 16 |
| End Month | 996 | 22 | 146 | 32 | white, radius 16 |
| Measure Toggle (capsule) | 1152 | 22 | 150 | 32 | `#243A57`, radius 16, white sliding pill |
| Info button | 1312 | 22 | 32 | 32 | outlined "i" icon, no background |

Gaps are 10 px, and the right edge (1344) lines up with the cards below.

## 1. Shapes (already drawn for Arcadia)

Folder `docs/brand/shapes/Arcadia/` in the repo holds six transparent PNGs. They were drawn for this portfolio (script: `docs/brand/build/make_toggle_shapes.py`):

`seg_headcount_on`, `seg_headcount_off`, `seg_fte_on`, `seg_fte_off`, `info_open`, `info_close`.

Install:
1. Copy the whole **Arcadia** folder into `Documents/My Tableau Repository/Shapes/` (Mac) or `Documents\My Tableau Repository\Shapes\` (Windows).
2. In Tableau, on any Shape palette choose **Reload Shapes**.

Why baked-in text: a shape keeps its own colors, so the selected segment can be a white pill with navy text and the other one pale text on dark, which a plain Square mark with label cannot do.

## 2. Measure Toggle sheet, rebuilt

1. New calculated field:
   ```
   // Toggle Shape
   [Measure Option] + " " + [Option State]
   ```
   (gives `Headcount On`, `Headcount Off`, `FTE On`, `FTE Off`; `Measure Option` and `Option State` are the fields from the previous guide).
2. On the Measure Toggle sheet:
   - Keep the Null exclusion filter on `Measure Option`.
   - Columns: `Measure Option`. **Right-click it → Sort → Manual**: Headcount first, FTE second (this fixes the order you have now).
   - Marks type **Shape**. Remove Color and Label. Drag `Toggle Shape` onto **Shape**.
   - Click the Shape legend → **Select Shape Palette: Arcadia** → assign each member to its file (`Headcount On` → `seg_headcount_on`, and so on).
   - Size slider to the maximum so the pill fills its cell. Entire View.
   - Hide the column header, remove gridlines and borders, tooltips off.
   - Format → Shading → Worksheet and Pane: `#243A57`.
3. On the dashboard, select the floating sheet. In the Layout pane set Background `#243A57`, **Corner Radius 16 on all four corners**, position and size from the table above.
4. The Change Parameter action stays exactly as it was (Source field `Measure Option`, Target parameter `Measure`, Keep current value on clear).

Each cell is 75 × 32 px and the images are 300 × 128, so the aspect ratio matches and nothing is stretched.

## 3. Rounded cards and controls

Select the object, then Layout pane → **Corner Radius**.

| Object | Background | Border | Radius |
|---|---|---|---|
| Waterfall sheet (the card) | `#FBFBF8` | 1 px `#E4E3DD` | 10 |
| Trend and Turnover sheets (when built) | `#FBFBF8` | 1 px `#E4E3DD` | 10 |
| Start Month, End Month | `#FFFFFF` | none | 16 |
| Measure Toggle | `#243A57` | none | 16 |
| Info panel (section 4) | `#FBFBF8` | 1 px `#E4E3DD` | 10 |
| Header band (Blank) | `#13233A` | none | 0 (keep it square, it bleeds to the edges) |

Parameter dropdowns: set Outer padding 0 and Inner padding 2. If the inner box of the dropdown still shows square corners inside the pill, that is Tableau's own control border. Send me a screenshot and I will give you the fallback (a dark capsule behind both controls with white text).

## 4. Info button and definitions panel (replaces Methodology)

1. Add a **Vertical** container, floating: x 1004, y 84, w 340, h 252. Name it `Info Panel`. Background `#FBFBF8`, Border 1 px `#E4E3DD`, Corner Radius 10, Inner padding 16.
2. Drag a **Text** object into it and paste:

   **How to read this page** (Tableau Semibold 10 pt, navy `#13233A`)

   - **Headcount**: workers with an active record at month-end.
   - **FTE**: scheduled hours divided by full-time hours, so part-time workers count as a fraction.
   - **The walk**: opening + hires − leavers ± internal moves = closing. It reconciles exactly to the month-end snapshot.
   - **Internal moves**: cancel out at company level; filter to a department to see them.
   - **Voluntary turnover**: voluntary leavers ÷ average headcount, annualized. Shown only for groups of 20 or more people.
   - Fiscal year starts July 1. Arcadia Systems and all data are fictional (synthetic).

   Body text: Tableau Book 9 pt, slate `#5A6170`.
3. Select the container → its dropdown arrow → **Add Show/Hide Button**. Float the button at x 1312, y 22, 32 × 32.
4. Click the button → **Edit Button…**: Button style **Image**; for "when the item is hidden" choose `info_open.png`, for "when shown" choose `info_close.png` (files in `docs/brand/shapes/Arcadia/`). Tooltip: `Definitions`. Background none, border none.
5. Hide the panel once (click the button) so the dashboard opens clean. It floats above everything, so it covers part of the trend chart area only while open.

## 5. Header text fix

The subtitle is cut off ("every line reconci…"). Replace line 2 of the title with something shorter (still Tableau Book 9 pt, `#C9D1DC`):

`Why headcount moved over the period · reconciles to the month-end snapshot`

## 6. Check

| Check | Expected |
|---|---|
| Toggle | Headcount first. Selected side is a white pill with navy text; click FTE and the pill moves, the waterfall switches |
| Corners | Waterfall card, toggle capsule and dropdowns all visibly rounded; same feel as the KPI cards |
| Info | Click the "i": panel opens and the icon turns into an X; click again to close |
| Header | Subtitle fully visible, controls aligned on one row, right edge at 1344 |
