# Dashboard #2 alignment plan: make Compensation Walk match Dashboard #1

Base = Dashboard #1 as published (`ArcadiaHeadcount`). Reference sections are in `docs/projects/headcount-fte-walk/release_3_rebuild_dashboard_1.md` (called **G1**) and `release_3_rebuild_dashboard_2.md` (**G2**). Work in order; each phase ends with a check you can see, and nothing is published until phase 9.

Principle: where #1 and #2 differ on purpose (a pay walk has a rail, a headcount walk has a header bar) the *components* still match: same fonts, colours, capsule shapes, hover sheets, tooltips, footnote wording, deselect rule.

## Phase 0. Shapes (Mac, 10 minutes, once)

Why: Tableau lists shapes in file-name order, white-on-transparent shapes look blank, and the folder only grows. New structure (see `docs/brand/shapes/README.md`): one palette per dashboard (`Arcadia D2`, `Arcadia D1`, `Arcadia Shared`), file names that say where they are used (`d2_lens_fte_on`), and a picture of every shape with its name (`docs/brand/shapes/index/d2.png`).

1. `cd ~/GitHub/people-analytics-warehouse && git checkout main && git pull`, then run the copy loop in `docs/brand/shapes/README.md`. Expected: the `ls` prints six `Arcadia*` folders.
2. Open `docs/brand/shapes/index/d2.png` and keep it beside Tableau.
3. Dashboard #1 keeps using the old `Arcadia` palette until it is republished; do not touch it.

## Phase 1. Rail controls (G2 5.1 to 5.4 and section 11)

For every sheet, pick the shape from palette **Arcadia D2** (or **Arcadia Shared**); the file name is the cheat sheet:

| Sheet | Shape file | Palette |
|---|---|---|
| Period Field, Group Field | `d2_field_capsule` | Arcadia D2 |
| Lens Toggle | `d2_lens_fte_on/off`, `d2_lens_payroll_on/off` | Arcadia D2 |
| Cost Toggle | `d2_cost_loaded_*`, `d2_cost_base_*` | Arcadia D2 |
| Currency Toggle | `d2_currency_constant_*`, `d2_currency_nominal_*` | Arcadia D2 |
| Reset | `d2_reset` | Arcadia D2 |
| Info Button | `d2_info_open`, `d2_info_close` | Arcadia D2 |
| Popover ✕ (Panel Close, Period Close) | `shared_close_light` | Arcadia Shared |
| Btn Expand / Btn Collapse icons | `shared_expand_icon`, `shared_collapse_icon` (until phase 5 replaces them) | Arcadia Shared |

The toggle shape on the Shape card is mapped by the on/off field, so re-pick the pairs in the **Edit Shape** dialog: select each data item on the left, then the file on the right.

**Group Field does not fit (the white capsule is narrower than the text; "ounting & Controllershi" is clipped).** The Period Field is right, so do not repair the Group Field, **copy the Period Field**:
1. Right-click the `Period Field` sheet tab > **Duplicate**. Rename the copy `Group Field`, after renaming or deleting the old `Group Field` (name taken).
2. Replace its fields with the group ones: Detail `Toggle Group Panel`, `Close Group Panel` (the group equivalents of the period parameters); Filter `Group Is Current`; Label `Group Field Text`; tooltip `Choose a group`.
3. Swap the sheet on the dashboard item and set the same fit and size as `Period Field` (item **200 × 32**, Fit **Entire View**, background None, padding 0).
4. Long names: the field is 200 px wide, about 24 characters at Semibold 10. Make the label calc cut long names and keep the full name in the tooltip:
```
// Group Field Text
IF LEN([p_Group]) > 24 THEN LEFT([p_Group], 23) + "…" ELSE [p_Group] END + "  ▾"
```
Tooltip: `<p_Group>` then "Choose a group". Check with Department > "Accounting & Controllership": it reads `Accounting & Controll…  ▾` fully inside the capsule.

Toggle containers: background `#243A57`, corner radius 15, padding 0, border none. ✕ and popovers: G2 5.2. Deselect audit: G2 5.4 (one `zzTrue`/`zzFalse` filter action per clickable and text sheet). **Check:** hover Period, Group, Reset, ⓘ and ✕ shows an outline only, no rings, no squares, no leftover highlight after a click.

## Phase 2. Page title and subtitle (G1 6.6 and 8.5)

- Title `Compensation Walk`: Tableau Bold 18 navy `#13233A`. Subtitle Tableau Book 9, **slate `#5A6170`**, one line (today it wraps to two lines at 1400 wide; shorten, see below).
- The rail headings (SELECT PERIOD, SELECT VIEW...) use `#B8C4D6` like the #1 header secondary text; the subtitle and the headings must not drift apart.
- **Title calc.** Today the subtitle names only the selected group ("changed at Accounting & Controllership"). Make it name the level too, so the reader knows what kind of group it is, and shorten the rest to fit one line:
```
// Page Subtitle
"Where average pay per FTE changed " +
(IF [p_View] = "Company" THEN "at Arcadia Systems" ELSE "in " + [p_Group] + " (" + LOWER([p_View]) + ")" END) +
" · " + [TT Open Day] + " to " + [TT Close Day] + " · " + [Cost Words] + ", " + [Currency Words]
```
(Use #2's own name for the lens/cost words; keep "Data as of" in the footnote, as #1 does.) **Check:** Company reads "…at Arcadia Systems · Jun 30, 2025 to Jun 30, 2026 · loaded cost, constant currency"; Department selection reads "…in Accounting & Controllership (department) · …" on one line.
- Tell me if by "title not showing function" you meant a different text (for example the waterfall headline); I have not seen that calc and this is the one I could verify from your screenshot.
- Page Title tooltip: "How to read this page" with the `Title Tip` pattern of G1 6.6.

## Phase 3. KPI cards (G1 8.2a, 8.2c)

#2's five cards already have #1's look. Align: card geometry from the `kpi_` parameters (GridLeft 30, CardW 255, GapX 16); hover sheets `KPI Hover 1..5` with `zzTrue`/`zzFalse` Deselect actions (copy-paste the sheets from the #1 workbook, then re-point the fields); one tooltip per card in the same two-line pattern (what it is, how it is computed); card 4 "Change" gets the teal/coral colour rule of #1's card 1 note.

## Phase 4. Waterfall block (G1 8.1, 8.1b)

- Replace `Expand · 9 drivers` with the **Summary | By driver** toggle: `shared_detail_*` shapes, item 152 × 24 at the card's top-right corner, background `#ECEBE5`, radius 12, parameter `p_Expand` (G1 8.1). Delete the four Expand/Collapse sheets and calcs afterwards (G1 13 delete list).
- Caption under the waterfall: Book 8 slate, two lines, the same tie-out sentence (G2 7.3). Title Semibold 12 navy, subtitle Book 9 slate.
- Tooltips: same structure as #1's waterfall tooltips (heading, value, one explanatory line).

## Phase 5. Top drivers card (right of the waterfall)

Type rule from #1: heading Semibold 12 navy, one subtitle line Book 9 slate, driver names Semibold 10 navy, values teal `#00938D` / coral `#E4572E`, descriptions Book 9 slate. Section labels (RAISES, HIRES & EXITS...) Book 8 `#8C8A84` caps. Same corner radius and card fill `#FBFBF8` as the #1 cards.

## Phase 6. Office moves, routes, regions

Headline Semibold 12 navy with the number in it; subtitle Book 9 slate; bars use the brand colours (violet `#5B4FB3` routes, amber `#D98E04` regions). Growth by Region follows the selection (G2 3). Fixed row heights and Standard fit as the #1 Turnover card (G1 8.3b) so bars do not resize between views.

## Phase 7. Footnote, popovers, info panel

- Footnote: #1 puts one slate Book 8 line at the bottom of the page; #2 has it in the rail (`Rail Footnote`). Keep it in the rail but use the same words and colour (`#5A6170` on cream is wrong on navy: use `#B8C4D6` in the rail).
- Popovers: navy `#13233A`, radius 10, padding 16; ✕ = `shared_close_light` 16 × 16; one open at a time (G1 0.5).
- Info panel: first two and last paragraph word for word as #1 (G1 0.5); tooltip "Click here for more information on how pay is measured".

## Phase 8. Layout and cleanup

- Align every object to #1's grid (G1 section 10): cards left edge 30, charts' right edges equal the KPI cards' edges, 16 px gaps. Floating items only.
- Delete what will never be used (G1 13): calcs and sheets dependent on the old Expand/Collapse, the old `Measure`-style parameters, old shape assignments. Use Tableau's delete dialog as the detector.

## Phase 9. Check, publish

- Run the G2 section 9 check table (eight selections) and G2 5.4 deselect audit.
- Reset, close popovers, Summary view, hide all sheets, **File > Save to Tableau Public As...** `Arcadia Compensation Walk` (same name, same URL), extracts only.
- Compare the published page with the phase checks, then update the README image and profile (same crop as #1).

## What I will prepare next (tell me which phase you want first)

Each phase gets its own checked step list like G1 8.x: exact field names, formulas and expected screenshots. Suggested order: **1 → 2 → 4 → 3 → 5 → 6 → 7 → 8 → 9**, because phases 1 and 2 remove the visible bugs (rings, clipped group name, wrapped subtitle).
