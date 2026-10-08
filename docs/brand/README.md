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

## Icons

64 line icons restyled from Heroicons (MIT), named for what they mean in a workforce report, with a ready-to-install Tableau shape pack: [`icons/`](icons/README.md).

## Colors

Every color has one job. The categorical order below passed a color-blindness check in this order (protanopia, deuteranopia, tritanopia), so keep it.

| Role | Color | Hex | Used for |
|---|---|---|---|
| Brand ink | Navy | `#13233A` | Header band, titles, the logo |
| Series 1 / growth | Teal | `#00938D` | Hires, increases, the sequential ramp's anchor |
| Series 2 / decline | Coral | `#E4572E` | Leavers, decreases |
| Series 3 / movement | Violet | `#5B4FB3` | Internal moves, relocation lines on the map |
| Accent | Amber | `#D98E04` | One highlighted mark at most. Always label it: it is under 3:1 contrast on the page |
| Totals | Warm gray | `#8C8A84` | Opening and Closing bars in a waterfall |
| Secondary text | Slate | `#5A6170` | Subtitles, axis labels, notes |
| Gridlines | Light gray | `#E4E3DD` | Hairlines only |
| Card | Off-white | `#FBFBF8` | Chart backgrounds |
| Page | Stone | `#F3F3EF` | Dashboard background behind the cards |

Ramps for magnitude and change:

| Ramp | Steps |
|---|---|
| Teal sequential | `#CDEDEA` `#9ED8D2` `#5FBFB7` `#2BA69E` `#00938D` `#007A75` `#00524F` |
| Coral to teal diverging | `#B8401F` `#E4572E` `#F2A68C` `#EFEEEA` `#8ACFC9` `#00938D` `#00615D` |

### Install the palettes in Tableau Public

1. Open [`Preferences.tps`](Preferences.tps) and click **Download raw file**.
2. Save it as `Documents/My Tableau Public Repository/Preferences.tps`. If a file with that name is already there, copy only the `<color-palette>` blocks into it.
3. Restart Tableau Public. The palettes appear under **Edit Colors** as *Arcadia Categorical*, *Arcadia Teal Sequential*, *Arcadia Coral-Teal Diverging* and *Arcadia Neutrals*.

Recent versions (2025.3 and later) also let you create custom palettes from inside Tableau; the file above is the same palettes, ready made.

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
