# Arcadia Systems: brand and dashboard style

Arcadia Systems is the fictional company behind every dataset in this repository. This folder gives it one look, so the Tableau Public dashboards read as a single product, not as separate exercises.

![Arcadia Systems logo](arcadia_logo_horizontal.png)

## Logo

The mark is a capital **A** drawn as a peak, with a teal node where the crossbar would be: a point on a map, and a data point on a chart. The wordmark is set in Inter. Every file is drawn from code ([`build/logo.js`](build/logo.js)), with the letters converted to outlines so the SVGs look the same on any machine.

| File | Use it for |
|---|---|
| [`arcadia_logo_horizontal.svg`](arcadia_logo_horizontal.svg) / [`.png`](arcadia_logo_horizontal.png) | Dashboard headers on light backgrounds |
| [`arcadia_logo_horizontal_reverse.svg`](arcadia_logo_horizontal_reverse.svg) / [`.png`](arcadia_logo_horizontal_reverse.png) | Dashboard headers on the navy band (transparent background) |
| [`arcadia_logo_mark.svg`](arcadia_logo_mark.svg) / [`.png`](arcadia_logo_mark.png) | Small spaces: the corner of a dashboard, a favicon-sized tile |

In Tableau: drag an **Image** object into the header container, choose the PNG, tick **Fit image** and **Center image**. Keep at least the width of the teal dot as clear space around the logo.

The logo is original, so it is safe to publish; Tableau Public's Viz of the Day guidance asks authors not to use logos they don't own.

## Colors

**One source:** [`Preferences.tps`](Preferences.tps). Every Arcadia color lives there as a Tableau palette; pick colors from those palettes under **Edit Colors**, never with the eyedropper or a typed shade. The three published workbooks show why: picked by eye, the navy drifted into nine near-copies (`#13223A`, `#13243A`, `#122137`, `#14213A`, ...), the slate into two, the coral into three. The palettes are numbered so Tableau lists them together and in order.

![Arcadia palettes](arcadia_palettes.png)

| Palette | Use it for |
|---|---|
| **Arcadia 1 Categorical** | Roles that mean the same on every dashboard: teal growth and hires, coral decline and leavers, violet internal moves, amber one highlight (label it: under 3:1 on the page) |
| **Arcadia 2 Categorical Extended** | Identity for up to nine groups: the four roles, then blue, green, rose, sky, brown. More than nine: fold into "Other" |
| **Arcadia 3 Categorical Light** | Nine colors for large labelled fills with navy text (Sankey flags, treemaps), taken only from Tableau 10 and Tableau 20, so they can be picked inside viz extensions too. Always labelled |
| **Arcadia 4 Systems** | Bridgeway (vendor system) orange, Keystone (HR system) blue, the system feed teal: Tableau 10 colors, checked for color-blind separation as a set. Color follows the system on every dashboard; white text on Keystone |
| **Arcadia 5 Status** | On track, watch, at risk, no status. Always with a word |
| **Arcadia 6 Neutrals** | Dark to light: navy (brand ink, the rail, titles), navy 2 (controls on the rail), slate (borders on navy), text gray (subtitles, axis labels), steel, silver (dividers on navy), mist, warm gray (Opening and Closing totals), Tableau gray (the Sankey's middle column), hairline (gridlines), page (behind the cards), card (chart backgrounds), white |
| **Arcadia 7 Teal Sequential** | Magnitude on one hue (growth %, headcount on a map) |
| **Arcadia 8 Navy Sequential** | Magnitude that should stay quiet (counts, age bands) |
| **Arcadia 9 Coral-Teal Diverging** | Decline to growth, gray at zero |

Every categorical order was checked for color-blind separation (protanopia, deuteranopia, tritanopia) in this order against the card color, so keep the order. Regenerate the picture after any change: `python3 docs/brand/build/make_palette_sheet.py`.

**Viz extensions use Tableau's palettes only.** The Sankey extension (and Tableau's other viz extensions) lists Tableau's built-in palettes, never the ones in `Preferences.tps`. So the palettes an extension needs, 3 and 4, are made only of Tableau 10 and Tableau 20 colors: the same hex in both places, picked from the built-in palette inside the extension and from the Arcadia palette everywhere else.

**Dashboard #4, Contingent Workforce Reconciliation:** in the Sankey's Edit Colors (choose the palette, then the swatch; the number is its place in the palette's order, which runs down each column of swatches):

| Node | Color | In the extension |
|---|---|---|
| 01 One person, two IDs | `#FF9D9A` | Tableau 20, light red (12th) |
| 02 Bridgeway ID missing or different | `#59A14F` | Tableau 20, green (5th) |
| 03 In Bridgeway, not in Keystone | `#FFBE7D` | Tableau 20, light orange (4th) |
| 04 Order open or billed after the end date | `#E15759` | Tableau 20, red (11th) |
| 05 Cost center differs | `#FABFD2` | Tableau 20, light pink (16th) |
| 06 PID still filled after the end date | `#8CD17D` | Tableau 20, light green (6th) |
| 07 Two active PID records | `#D4A6C8` | Tableau 20, light purple (18th) |
| 08 Working in Bridgeway, ended in Keystone | `#F1CE63` | Tableau 20, yellow (8th) |
| 09 Active in Keystone, not working in Bridgeway | `#A0CBE8` | Tableau 20, light blue (2nd) |
| Every risk | `#BAB0AC` | Tableau 10, gray (10th) |
| Bridgeway (vendor system) | `#F28E2B` | Tableau 10, orange (2nd) |
| Keystone (HR system) | `#4E79A7` | Tableau 10, blue (1st) |
| System feed (integration) | `#76B7B2` | Tableau 10, teal (4th) |

The ticket card's rows use *Arcadia 4 Systems*, the same three colors.

### Install the palettes

1. Download [`Preferences.tps`](Preferences.tps) (or copy it from your clone of this repository).
2. Save it as `Documents/My Tableau Repository/Preferences.tps` for Tableau Desktop, and `Documents/My Tableau Public Repository/Preferences.tps` for Tableau Public. It replaces an older Arcadia file; if the file holds palettes of your own, copy only the `<color-palette>` blocks into it.
3. Restart Tableau. The nine palettes appear under **Edit Colors**, from *Arcadia 1 Categorical* to *Arcadia 9 Coral-Teal Diverging*.

Older workbooks keep their colors: a workbook stores the colors themselves, not the palette name.

### Save the look as a theme

Once the first dashboard is styled, use **Format → Workbook** to set fonts (Tableau's default sans is fine), then export the styling as a custom theme (Tableau 2025.1 and later) and apply it to every other workbook. All Arcadia dashboards then share fonts, sizes and colors without restyling by hand.

## Layout rules

These follow what Tableau Public's Viz of the Day team says it selects for: a clear key insight, color-blind-safe color, honest charts, new features used well, and downloadable workbooks.

1. **Lead with the answer.** The title states the finding ("Asia Pacific grew fastest in FY26"), not the topic ("Headcount by region"). The subtitle says how to read the chart.
2. **One navy header band** with the reverse logo on the left, the dashboard title, and the controls on the right. Same position on every dashboard.
3. **KPI band of five tiles** under the header: label, big number, one line of context with the change in teal or coral.
4. **Cards on a stone page.** Each chart sits on an off-white card with a 1px light-gray border and 12px gaps. No drop shadows, no gradients.
5. **Bars start at zero, waterfalls included.** A truncated axis makes a 5% change look like a doubling.
6. **Label directly, use few legends.** Label the bars and the few points that matter instead of numbering every mark.
7. **Color means the same thing everywhere.** Teal is always growth, coral always loss, violet always movement between groups.
8. **Every dashboard ends with a Methodology page** and allows the workbook to be downloaded.

The source for both dashboard previews is in [`build/`](build/); `bash docs/brand/build/build.sh` rebuilds the logos and the previews after `python pipeline/run_pipeline.py --no-export`.
