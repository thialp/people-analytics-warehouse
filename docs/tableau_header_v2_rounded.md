# Headcount & FTE Walk: rounded header, capsule toggle, info panel

Replaces sections 4 to 6 of `tableau_header_and_polish_steps.md` (the pills and the Methodology button). Needs Tableau Desktop 2026.2 (native **Corner Radius** in the Layout pane). Everything is rounded to the same 10 px radius as the KPI cards, so the page reads as one system.

Final header layout (1400 wide, floating, y 22 for all controls):

| Object | x | y | w | h | Look |
|---|---|---|---|---|---|
| Start Month | 840 | 22 | 146 | 32 | white, plain square (radius 0) |
| End Month | 996 | 22 | 146 | 32 | white, plain square (radius 0) |
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
| Start Month, End Month | `#FFFFFF` | none | 0 (plain; see the tooltip guide, Section 4) |
| Measure Toggle | `#243A57` | none | 16 |
| Info panel (section 4) | `#FBFBF8` | 1 px `#E4E3DD` | 10 |
| Header band (Blank) | `#13233A` | none | 0 (keep it square, it bleeds to the edges) |

Parameter dropdowns: this was tested and a rounded pill around them fights the control's own square border, so they stay plain squares (radius 0, Outer and Inner padding 0). The capsule toggle and info button keep their rounding.

## 4. Info button and definitions panel (replaces Methodology)

1. Add a **Vertical** container, floating: x 1004, y 84, w 340, h 340. Name it `Info Panel`. Background `#FBFBF8`, Border 1 px `#E4E3DD`, Corner Radius 10, Inner padding 16.
2. Drag a **Text** object into it. The final text (period rules, FTE and part-time, the toggle, turnover, internal moves) is in `tableau_final_polish_before_publish.md`, item 5. Make the panel **340 high**.
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
| Corners | Waterfall card and toggle capsule rounded like the KPI cards; dropdowns plain squares |
| Info | Click the "i": panel opens and the icon turns into an X; click again to close |
| Header | Subtitle fully visible, controls aligned on one row, right edge at 1344 |
