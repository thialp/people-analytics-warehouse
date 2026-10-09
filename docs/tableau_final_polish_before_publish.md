# Executive Summary: final polish before publishing

Five fixes, found by reading the finished dashboard (FY26, Jul 2025 to Jun 2026). Do them in this order; each is a few minutes.

## 1. Turnover by Function: the title says "All"

**Why:** the sheet still has Tableau's default title, `<Measure Names>`, which prints "All" when two measures share a bar. The `TO Title` field is on the sheet but was never put into the title, and the second line is too long, so it wraps.

On the **Turnover by Function** sheet: Worksheet → Show Title, double-click the title, delete everything and build two lines:

- Line 1 (Tableau Bold 12 pt, navy `#13233A`): Insert → `TO Title`. It reads "Commercial has the highest turnover in FY26".
- Line 2, one line only (Tableau Book 9 pt):
  `Involuntary` in dark coral `#B8401F`, then ` + ` in slate `#5A6170`, then `Voluntary` in coral `#E4572E`, then ` leavers ÷ average headcount, annualized` in slate.

The order is Involuntary first because that is the order of the colors in the bar (dark segment on the left, light on the right). The "groups under 20 people are hidden" note moves to the info panel (item 5) and stays in the tooltip.

If line 1 prints "Multiple values" instead of the sentence, `TO Title` is being split by a mark. Right-click `TO Title` on Detail → Compute Using → **Function Name**, and check that `TO Top Function` is also set to Function Name.

## 2. The three card titles should look like one family

| Card | Line 1 | Line 2 |
|---|---|---|
| Waterfall | `WF Title`, Tableau Bold 12 pt navy `#13233A` | `Opening + hires − leavers ± internal moves = closing · axis starts at zero`, Tableau Book 9 pt slate `#5A6170` |
| Trend | `Trend Title`, Tableau Bold 12 pt navy `#13233A` | `Selected period shaded` (this line is missing today), Tableau Book 9 pt slate |
| Turnover | `TO Title`, Tableau Bold 12 pt navy `#13233A` | see item 1 |

Check that the navy is exactly `#13233A` on all three; the waterfall title currently reads darker than the trend title. Left-align every title and keep the same 12 px inner padding on the left.

## 3. Waterfall caption: wording, and whole-number FTE

Two problems in the caption under the waterfall:

1. It said "filter to a department", but this dashboard has no department filter. The new wording replaces the sentence.
2. In FTE mode it showed "FTE 12,281.7 → 12,940.0" while the Opening bar reads 12,282. Everything on the waterfall card is a whole number (12,282 + 2,328 − 1,319 − 317 − 34 = 12,940, which ties exactly), so the caption should be too. The one-decimal figures stay on the Closing FTE card and in the tooltip, where the part-time count explains them.

Replace `WF Caption`:
```
// WF Caption
IF NOT [K Valid] THEN "" ELSE
[WF Moves Str] + " internal moves (" + [WF Promos Str] + " promotions, " + [WF Other Str] +
" other) move people between teams, so they net to zero at company level. FTE " +
[WF FTE Open Str] + " → " + [WF FTE Close Str] + ", including " + [WF FTE Chg Str] + " from schedule changes."
END
```
and put the three FTE helpers back to whole numbers (replace the formulas; every branch is wrapped in `STR`):
```
// WF FTE Open Str
IF INT(ROUND([WF FTE Open], 0)) >= 1000
THEN STR(DIV(INT(ROUND([WF FTE Open], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([WF FTE Open], 0)) % 1000), 3)
ELSE STR(INT(ROUND([WF FTE Open], 0))) END
```
```
// WF FTE Close Str
IF INT(ROUND([WF FTE Close], 0)) >= 1000
THEN STR(DIV(INT(ROUND([WF FTE Close], 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND([WF FTE Close], 0)) % 1000), 3)
ELSE STR(INT(ROUND([WF FTE Close], 0))) END
```
```
// WF FTE Chg Str
IF [WF FTE Chg] < 0 THEN "−" ELSE "+" END + STR(INT(ROUND(ABS([WF FTE Chg]), 0)))
```
Expected caption: *"1,615 internal moves (1,038 promotions, 577 other) move people between teams, so they net to zero at company level. FTE 12,282 → 12,940, including −34 from schedule changes."*

## 4. KPI card 5 note: stray spacing

The card reads "1 ,038 promotions ·577 other moves"; it should read "1,038 promotions · 577 other moves". The formula in the guide produces the right text, so the `KPI 5 Note` field in your workbook has drifted (a space before the comma and a missing space after the dot). Open the field, select all, and paste:
```
// KPI 5 Note
IF NOT [K Valid] THEN "" ELSE
  IF [K Promotions] >= 1000
  THEN STR(DIV(INT([K Promotions]), 1000)) + "," + RIGHT("00" + STR(INT([K Promotions]) % 1000), 3)
  ELSE STR(INT([K Promotions])) END
  + " promotions · " +
  IF [K Other Moves] >= 1000
  THEN STR(DIV(INT([K Other Moves]), 1000)) + "," + RIGHT("00" + STR(INT([K Other Moves]) % 1000), 3)
  ELSE STR(INT([K Other Moves])) END
  + " other moves"
END
```
If it still shows a gap after the paste, the text is not wrong, it is the map label's character spacing: shorten the note to `1,038 promotions · 577 other` and it will fit without squeezing.

## 5. Info panel: replace the text

The panel still holds the first draft, written before the FTE decimals, the part-time count, the measure toggle, the period rules and the turnover chart. Open the `Info Panel` container, edit the text object and replace everything with this. Heading: Tableau Semibold 10 pt navy `#13233A`. Body: Tableau Book 9 pt slate `#5A6170`. Each bold lead-in is Tableau Semibold.

**How to read this page**

**Period.** The walk starts at the month-end before *From* and ends at the month-end of *To*. Choose *From* on or before *To*. Arcadia's fiscal year starts July 1.

**Headcount.** Workers with an active record at month-end.

**FTE.** Scheduled hours ÷ full-time hours. A part-time worker counts as a fraction, so FTE is lower than headcount; the Closing FTE card shows the gap and how many part-timers sit behind it.

**The walk.** Opening + hires − leavers ± internal moves = closing. It reconciles exactly to the month-end snapshot, in headcount and in FTE.

**Headcount | FTE toggle.** Switches the waterfall and the notes on the Hires and turnover cards. The two closing cards always show both measures. Turnover rates are always headcount-based.

**Internal moves.** Promotions and transfers move people between teams, so they net to zero at company level.

**Turnover.** Leavers ÷ average headcount, annualized. Groups under 20 people are not shown.

**Data.** Arcadia Systems is a fictional company and all data is synthetic.

Then resize the panel: Layout pane → height **340** (it was 300), keep x 1004, y 84, w 340. Close it once (click the "i") so the dashboard opens with the panel hidden.

## 6. Last check before you publish

| Check | Expected (From Jul 2025, To Jun 2026) |
|---|---|
| Turnover title | Commercial has the highest turnover in FY26, on one line, with a one-line subtitle |
| Waterfall caption | ends "FTE 12,282 → 12,940, including −34 from schedule changes." (same whole numbers as the bars) |
| KPI 5 note | 1,038 promotions · 577 other moves |
| Trend | subtitle "Selected period shaded" |
| Info panel | opens at the "i", new text fits without scrolling, closes again |
| Toggle to FTE | waterfall in FTE, Hires card note follows, turnover chart unchanged |
| Set From = To (one month) | one-month walk, no error; set From after To: cards show "—" and the title asks to pick a start month on or before the end month |

Then follow Part C of `tableau_turnover_and_tooltips_steps.md` (fixed 1400 × 850, hide helper sheets, publish) and send me the link.
