# Dashboard #6, Workforce Cost Bridge: build guide

This guide builds the sixth Arcadia dashboard from an empty Tableau Desktop, in the order you would build it by hand: the data source, the parameters, the calculations, each sheet, the dashboard, the popovers, the actions and the checks. Every formula pastes as it stands, and every expected value in section 13 is computed from the growth-mix mart the way the page computes it (`tableau/builder/d6/check_values.py`). A step either matches or shows exactly what differs.

Arcadia Systems is fictional; all data is synthetic.

| Step | What | State |
|---|---|---|
| 1 | Marts, Custom SQL, method, tests (test 78: the six effects add up to the change) | Done in release 3, unchanged through release 6 |
| 2 | This guide and its check values | Written 2026-10-29 |
| 3 | The build: `tableau/builder/d6` writes the workbook from this guide into the saved base workbook (2.2), then spot checks in Desktop | Next |
| 4 | Publish, README, Figma values, profile, LinkedIn | After the build |

## Contents

0. What you are building
1. Decisions
2. The data source
3. Parameters
4. Core calculations (selection, labels, number text)
5. The selection's numbers
6. The KPI band
7. The bridge
8. The order of the steps (Shapley against one fixed order)
9. Five fiscal years
10. The rail
11. The popovers (Period, Organization, Info)
12. Assembling the dashboard
13. Checks and click tests
14. Publishing
15. As built (filled in after the build)

---

## 0. What you are building

**The question on the page (Finance):** *did workforce cost grow because of more people, a different mix of people, or higher rates and currency?*

**The answer:** total workforce cost (employees' loaded pay run-rate plus contingent workers' annualized bill run-rate, nominal USD) is split into six factors with Shapley values. Each factor gets its average effect over every order of the six steps, so no factor is favored by the order it is computed in, and the six effects add up to the change exactly.

| Factor | Meaning |
|---|---|
| Volume | More or fewer people |
| Workforce mix | The balance of employees and contingent workers |
| Location mix | Which countries the people are in, within each worker type |
| Level mix | Which grades (or contingent types) the people are in, within type and country |
| Rate | What each person costs at constant exchange rates: pay and bill rates |
| Currency | What exchange rates did to the reported cost |

```
x 0      216 240         456 470       686 700       916 930      1146 1160     1376 1400
y 0  ┌────────┬──────────────────────────────────────────────────────────────────────┐
     │  RAIL  │ Workforce Cost Bridge                                                │ 16–72
     │  navy  │ Why total workforce cost changed · <span> · <scope> · nominal USD …  │
  86 │        │ ┌ KPI 1 ──┐ ┌ KPI 2 ──┐ ┌ KPI 3 ──┐ ┌ KPI 4 ──┐ ┌ KPI 5 ──┐          │ 86–172
     │        │ │ total   │ │ volume  │ │ rates   │ │ mix     │ │ currency│          │
 186 │        │ ┌ Bridge card ─────────────────────────┐ ┌ Order of the steps ──────┐ │ 186–488
     │        │ │ title (the answer in words)          │ │ Shapley vs fixed order   │ │
     │        │ │ Opening · six factors · Closing      │ │ six factors, bias column │ │
     │        │ │ (Gantt waterfall, labels on top)     │ └──────────────────────────┘ │
     │        │ │                                      │ ┌ Five fiscal years ───────┐ │ 502–812
     │        │ │ note                                 │ │ FY × Volume Mix Rate Cur │ │
 812 │        │ └──────────────────────────────────────┘ └──────────────────────────┘ │
 826 │        │ footnote                                                             │
 850 └────────┴──────────────────────────────────────────────────────────────────────┘
```

| Where | What it answers | Default view (FY26 vs FY25, all of Arcadia) |
|---|---|---|
| Title | What am I looking at? | **Workforce Cost Bridge** · "Why total workforce cost changed · Jun 30, 2025 to Jun 30, 2026 · all of Arcadia · nominal USD · employees and contingent workers" |
| KPI 1 | How much did cost change? | Total cost, FY26 **$4,648.1M** · +$402.9M vs FY25 (+9.5%) |
| KPI 2 | How much was more people? | More people (volume) **+$307.1M** · 76% of the change · headcount +2,801 |
| KPI 3 | How much was rates? | Higher rates **+$139.8M** · pay and bill rates, constant FX |
| KPI 4 | How much was mix? | Mix of people **+$8.3M** · level +22.4 · location −9.3 · workforce −4.8 |
| KPI 5 | How much was currency? | Currency **−$52.2M** · +$455.2M before exchange rates |
| Bridge card | Why did it change? | "Cost grew $403M, and 76% of it was more people". Opening 4,245.2 · +307.1 · −4.8 · −9.3 · +22.4 · +139.8 · −52.2 · Closing 4,648.1 |
| Order of the steps | Why Shapley? | "A fixed order would move Rate by +$5.5M". Shapley and sequential bars per factor, the bias beside each |
| Five fiscal years | Is this year different? | "Rates rose every year; currency swung both ways". FY22 to FY26, Volume, Mix, Rate, Currency |

**The palette.** Navy `#13233A` (rail, titles, Shapley bars, level labels), slate `#5A6170` (secondary text), ink `#1F2329`, axis text `#8C9BB0`, grid `#ECEDEA`, page `#F3F3EF`, cards `#FFFFFF` with a 1 px `#E4E3DD` border and 14 px corners. Opening and closing bars: blue-gray `#8C9BB0`. A factor that adds cost: teal `#0F6E56` (bar and text). A factor that takes cost away: sand `#B8A888` (bar), dark sand `#7D6A45` (text, so it stays legible on white). Sequential bars: mist `#B9C3D1`. No red and green pair, no blue and orange pair.

---

## 1. Decisions

| # | Decision | Why |
|---|---|---|
| C1 | **One data source**, `custom_sql_workforce_cost_growth_mix.sql`, extracted (1,224 rows) | Every card reads the same 8 rows of one pair and group; one source keeps the parameters reaching every sheet |
| C2 | **The page is the Shapley bridge.** No layer from the monthly driver walk | The walk answers a different question (what happened month by month) and adds a 25-second second source. It can be its own page later |
| C3 | **Period: all 17 year-over-year pairs** (every fiscal quarter-end against the same date a year earlier), FY26 vs FY25 by default; the five-year table stays on fiscal years | Finance asks "Q3 against last Q3" as often as "the year against last year", and it costs nothing in the data |
| C4 | **Organization: all of Arcadia or one function, single choice** | Each function is its own Shapley bridge (its six effects add up to its own change), so functions cannot be added together |
| C5 | **No worker-type split** | The mart has no worker-type view, and inside one type the Workforce mix factor disappears, which a screenshot cannot explain |
| C6 | **Nominal USD only, no currency switch.** The Currency factor is the exchange-rate story; KPI 5 and its hover give the change without it | A switch that only hides one bar adds a control without adding an answer |
| C7 | **No Shapley / Sequential toggle**: the order-of-the-steps card shows both methods side by side, with the bias per factor | The comparison is the point; a toggle would hide it |
| C8 | **No hard-coded dates.** Every label comes from the data: the pair is an offset from the latest quarter-end (`p_Pair` 0 = latest), fiscal-year words come from `fiscal_year` and `fiscal_quarter_label` | Next year's refresh moves everything one year forward without editing a calculation |
| C9 | **Selections are tested inside each formula** (`[In Selection] AND [factor_order] = 5`), not with context filters; the bridge, the bias bars and the lists filter on a row-level boolean only | A FIXED LOD runs before ordinary filters; with the test inside the formula there is no filter order to remember |
| C10 | **The axis floor is a FIXED LOD**, 95% of the lower of opening and closing, rounded down to a round number (`$4.0B` by default), shown as a reference line labeled "Axis starts at …" | The factors are 0.1% to 7% of the total; from zero they would be invisible. Across all 153 pair-and-group views the path never dips below 96% of the lower end, so the floor always sits under every bar |
| C11 | **Every text that follows the data is a calculation**; money in sentences uses the money pattern (4.4) | Tableau has no number format inside a string |
| C12 | **Hovers are sentences, color-coded**: adds in teal, takes away in dark sand, levels and counts in navy. Tooltip command buttons off on every sheet; every clickable sheet has a deselect (`zzTrue` → `zzFalse`) | Rich tooltips carry the detail; nothing stays highlighted after a click |
| C13 | Rules carried: executive officers excluded upstream; neutral wording ("takes away", "lowered", never "wrong"); American spelling; integer font sizes; no arrow glyphs in text | Every Arcadia dashboard |

---

## 2. The data source

### 2.1 What the Custom SQL returns

One `SELECT` from the reporting view `rpt.vw_workforce_cost_growth_mix`, **1,224 rows**: 17 pairs × 9 groups × 8 factor rows.

| Column | Meaning |
|---|---|
| `from_month_end`, `to_month_end` | The two quarter-ends compared, a year apart (date) |
| `fiscal_year`, `fiscal_quarter_label` | Of `to_month_end`: 2026 and "FY26 Q4" for Jun 30, 2026 |
| `pair_type` | "Year over year" on every row |
| `view_order`, `view_name`, `group_name` | 1 Company "Arcadia Systems"; 2 Function, one of the 8 functions |
| `factor_order`, `factor`, `factor_meaning` | 0 Opening cost, 1 Volume, 2 Workforce mix, 3 Location mix, 4 Level mix, 5 Rate, 6 Currency, 7 Closing cost |
| `shapley_effect_usd` | The Shapley effect (USD); on rows 0 and 7 the opening and closing cost |
| `sequential_effect_usd` | The effect when the factors move one at a time in the order above |
| `order_bias_usd` | Sequential minus Shapley: what the choice of order alone would have moved |
| `opening_headcount`, `closing_headcount` | People in the group on each date (employees and contingent workers), repeated on every row of the pair |

Opening + the six Shapley effects = Closing, to the cent of each stored value (the largest residual over all 153 views is 2 cents, from rounding eight stored values).

### 2.2 Connect and extract

1. **File > New.** Connect > To a Server > **Microsoft SQL Server**: server `localhost`, port `1433`, database `ArcadiaHR`, SQL Server Authentication, user `sa`, the password from `docker exec arcadia-sql printenv MSSQL_SA_PASSWORD`, **Require SSL** unchecked.
2. Drag **New Custom SQL** onto the canvas and paste `tableau/custom_sql_workforce_cost_growth_mix.sql` in full. OK.
3. Rename the data source **Workforce Cost Bridge**.
4. **Extract**. Save as `Workforce Cost Bridge base.twb` in `~/Documents/Tableau/Tableau Public/ArcadiaHR/6 Workforce Cost Bridge/`; the extract goes in `Data Source Hyper` beside it. Close Tableau. This is the base workbook the builder writes into.

**Types** (right-click > Convert to Dimension): `factor_order`, `fiscal_year`, `view_order`. Keep `opening_headcount` and `closing_headcount` measures. `from_month_end` and `to_month_end` stay dates.

**Checkpoint 2.** Sheet `CHK Rows`: `group_name` on Rows, `CNT(factor)` on Text, grand total on. Expected **136 per group, 9 groups, total 1,224**. Keep it, hidden, until publishing.

---

## 3. Parameters

None is shown on the dashboard: the rail and the popovers set them.

| Name | Type | Allowable | Current value | What sets it |
|---|---|---|---|---|
| `p_Pair` | Integer | Range 0 to 16, step 1 | **0** | Period list, Reset. 0 = the latest quarter-end against a year earlier, 1 = the quarter-end before, … 16 |
| `p_Group` | String | All | **Arcadia Systems** | Organization list, Reset. The company or one function |
| `p_PeriodOpen`, `p_OrgOpen`, `p_InfoOpen` | Boolean | True / False | False | The rail capsules, the ✕, Reset (one popover open at a time) |

---

## 4. Core calculations

All calculations live on **Workforce Cost Bridge**. Each formula starts with a `//` line naming it; create them in the order below. A row-level or LOD field used inside an aggregate formula is wrapped in `MIN()`, as written.

### 4.1 Helpers

```
// zzTrue
TRUE

// zzFalse
FALSE

// Close Panel
FALSE

// Zero Pair
0

// Hover Cell
"."
```

### 4.2 The selection

```
// Latest To
{ MAX([to_month_end]) }

// Pair Offset
DATEDIFF('quarter', [to_month_end], [Latest To])

// Is Year Pair
[Pair Offset] % 4 = 0

// In Pair
[Pair Offset] = [p_Pair]

// In Group
[group_name] = [p_Group]

// In Selection
[In Pair] AND [In Group]

// Is Factor
[factor_order] >= 1 AND [factor_order] <= 6

// Company Name
{ MIN(IF [view_name] = "Company" THEN [group_name] END) }

// Is Company
[p_Group] = [Company Name]

// Effect M
[shapley_effect_usd] / 1000000

// Seq M
[sequential_effect_usd] / 1000000

// Bias M
[order_bias_usd] / 1000000
```

Convert `Pair Offset` to a **Dimension** (discrete). Expected: Jun 30, 2026 rows → 0, Mar 31, 2026 → 1, Jun 30, 2022 → 16.

### 4.3 Calendar and scope words

```
// Year Word
"FY" + RIGHT(STR([fiscal_year]), 2)

// Prior Year Word
"FY" + RIGHT(STR([fiscal_year] - 1), 2)

// Quarter Suffix
IF RIGHT([fiscal_quarter_label], 2) = "Q4" THEN "" ELSE " " + RIGHT([fiscal_quarter_label], 2) END

// Row To Label
[Year Word] + [Quarter Suffix]

// Row From Label
[Prior Year Word] + [Quarter Suffix]

// Row To Date
LEFT(DATENAME('month', [to_month_end]), 3) + " " + STR(DAY([to_month_end])) + ", " + STR(YEAR([to_month_end]))

// Row From Date
LEFT(DATENAME('month', [from_month_end]), 3) + " " + STR(DAY([from_month_end])) + ", " + STR(YEAR([from_month_end]))

// To Label
{ MIN(IF [In Pair] THEN [Row To Label] END) }

// From Label
{ MIN(IF [In Pair] THEN [Row From Label] END) }

// To Date Text
{ MIN(IF [In Pair] THEN [Row To Date] END) }

// From Date Text
{ MIN(IF [In Pair] THEN [Row From Date] END) }

// As Of Text
{ MIN(IF [Pair Offset] = 0 THEN [Row To Date] END) }

// Pair Label
[To Label] + " vs " + [From Label]

// Span Text
[From Date Text] + " to " + [To Date Text]

// Org Field Text
IF [Is Company] THEN "All of Arcadia" ELSE [p_Group] END

// Scope Words
IF [Is Company] THEN "all of Arcadia" ELSE [p_Group] END

// Page Subtitle
"Why total workforce cost changed · " + [Span Text] + " · " + [Scope Words] + " · nominal USD · employees and contingent workers"
```

Expected with `p_Pair` 0: Pair Label "FY26 vs FY25", Span Text "Jun 30, 2025 to Jun 30, 2026". With 1: "FY26 Q3 vs FY25 Q3", "Mar 31, 2025 to Mar 31, 2026". With 8: "FY24 vs FY23". A pair ending on the fiscal year's last quarter reads as the fiscal year; any other reads with its quarter.

### 4.4 Numbers inside text

Tableau has no number format inside a string. Four patterns; each `… Txt`, `… Num` or `… Str` field below is one of them with its number in place of `x`.

```
// M1 Pattern (one decimal and a comma, no sign: 4,648.1)
IF ISNULL(x) THEN "–" ELSE
(IF INT(ROUND(ABS(x), 1)) >= 1000
 THEN STR(DIV(INT(ROUND(ABS(x), 1)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND(ABS(x), 1)) % 1000), 3)
 ELSE STR(INT(ROUND(ABS(x), 1))) END)
+ "." + STR(INT(ROUND((ROUND(ABS(x), 1) - INT(ROUND(ABS(x), 1))) * 10, 0)))
END

// Sign Pattern ("+" or the minus sign U+2212, never a hyphen)
IF ROUND(x, 1) >= 0 THEN "+" ELSE "−" END

// Comma Pattern (whole number with a comma)
IF ISNULL(x) THEN "–"
ELSEIF ROUND(ABS(x), 0) >= 1000 THEN STR(DIV(INT(ROUND(ABS(x), 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND(ABS(x), 0)) % 1000), 3)
ELSE STR(INT(ROUND(ABS(x), 0))) END

// Pct1 Pattern (one decimal, no sign: 9.5)
STR(INT(ROUND(ABS(x) * 100, 1))) + "." + STR(INT(ROUND((ROUND(ABS(x) * 100, 1) - INT(ROUND(ABS(x) * 100, 1))) * 10, 0)))
```

**Inside a formula,** `<M1 on x>`, `<Sign on x>`, `<Comma on x>` and `<Pct1 on x>` stand for the pattern with `x` replaced by the expression given (the builder pastes it in; by hand, paste the pattern and replace each `x`).

The three forms money takes on the page:

| Form | Built as | Example |
|---|---|---|
| Money | `"$" + M1 + "M"` | $4,648.1M |
| Signed money | `Sign + "$" + M1 + "M"` | +$307.1M, −$52.2M |
| Signed number | `Sign + M1` | +22.4, −9.3 |

---

## 5. The selection's numbers

Aggregates for one-mark sheets (the KPI cards, titles, hovers): no dimension in the view, the selection tested inside.

```
// S Opening
SUM(IF [In Selection] AND [factor_order] = 0 THEN [Effect M] END)

// S Closing
SUM(IF [In Selection] AND [factor_order] = 7 THEN [Effect M] END)

// S Volume
SUM(IF [In Selection] AND [factor_order] = 1 THEN [Effect M] END)

// S Workforce
SUM(IF [In Selection] AND [factor_order] = 2 THEN [Effect M] END)

// S Location
SUM(IF [In Selection] AND [factor_order] = 3 THEN [Effect M] END)

// S Level
SUM(IF [In Selection] AND [factor_order] = 4 THEN [Effect M] END)

// S Rate
SUM(IF [In Selection] AND [factor_order] = 5 THEN [Effect M] END)

// S Currency
SUM(IF [In Selection] AND [factor_order] = 6 THEN [Effect M] END)

// S Change
[S Closing] - [S Opening]

// S Change Pct
[S Change] / [S Opening]

// S Mix
[S Workforce] + [S Location] + [S Level]

// S Constant Change
[S Change] - [S Currency]

// S HC Open
MIN(IF [In Selection] THEN [opening_headcount] END)

// S HC Close
MIN(IF [In Selection] THEN [closing_headcount] END)

// S HC Change
[S HC Close] - [S HC Open]

// S Vol Share
[S Volume] / [S Change]

// S Bias Volume
SUM(IF [In Selection] AND [factor_order] = 1 THEN [Bias M] END)

// S Bias Workforce
SUM(IF [In Selection] AND [factor_order] = 2 THEN [Bias M] END)

// S Bias Location
SUM(IF [In Selection] AND [factor_order] = 3 THEN [Bias M] END)

// S Bias Level
SUM(IF [In Selection] AND [factor_order] = 4 THEN [Bias M] END)

// S Bias Rate
SUM(IF [In Selection] AND [factor_order] = 5 THEN [Bias M] END)

// S Bias Currency
SUM(IF [In Selection] AND [factor_order] = 6 THEN [Bias M] END)
```

Text fields (the pattern of 4.4 on each number):

| Field | Form | Number |
|---|---|---|
| `S Opening Txt` | Money | `[S Opening]` |
| `S Closing Txt` | Money | `[S Closing]` |
| `S Change Txt` | Signed money | `[S Change]` |
| `S Volume Txt` | Signed money | `[S Volume]` |
| `S Rate Txt` | Signed money | `[S Rate]` |
| `S Mix Txt` | Signed money | `[S Mix]` |
| `S Currency Txt` | Signed money | `[S Currency]` |
| `S Constant Txt` | Signed money | `[S Constant Change]` |
| `S Currency Abs Txt` | Money | `[S Currency]` |
| `S Workforce Num`, `S Location Num`, `S Level Num` | Signed number | `[S Workforce]`, `[S Location]`, `[S Level]` |
| `S HC Open Str`, `S HC Close Str` | Comma | `[S HC Open]`, `[S HC Close]` |
| `S HC Change Str` | Sign + Comma (sign on `[S HC Change]`, whole number) | `[S HC Change]` |
| `S Change Pct Str` | Sign + Pct1 + "%" | `[S Change Pct]` |
| `S Vol Share Str` | `STR(INT(ROUND(x * 100, 0))) + "%"` | `[S Vol Share]` |

`S HC Change Str` uses `IF x >= 0 THEN "+" ELSE "−" END` for its sign (a count has no decimals to round).

**Expected, default view:** S Opening 4,245.2 · S Closing 4,648.1 · S Change +402.9 (+9.5%) · Volume +307.1 · Workforce −4.8 · Location −9.3 · Level +22.4 · Rate +139.8 · Currency −52.2 · S Mix +8.3 · S Constant Change +455.2 · headcount 39,145 to 41,946 (+2,801) · S Vol Share 76%.

### 5.1 The largest factor (for the bridge title)

```
// Max Abs Effect
MAX(MAX(MAX(ABS([S Volume]), ABS([S Workforce])), MAX(ABS([S Location]), ABS([S Level]))), MAX(ABS([S Rate]), ABS([S Currency])))

// Driver Order
IF ABS([S Volume]) = [Max Abs Effect] THEN 1
ELSEIF ABS([S Workforce]) = [Max Abs Effect] THEN 2
ELSEIF ABS([S Location]) = [Max Abs Effect] THEN 3
ELSEIF ABS([S Level]) = [Max Abs Effect] THEN 4
ELSEIF ABS([S Rate]) = [Max Abs Effect] THEN 5
ELSE 6 END

// Driver Effect
CASE [Driver Order] WHEN 1 THEN [S Volume] WHEN 2 THEN [S Workforce] WHEN 3 THEN [S Location]
WHEN 4 THEN [S Level] WHEN 5 THEN [S Rate] ELSE [S Currency] END

// Driver Words
CASE [Driver Order]
WHEN 1 THEN (IF [Driver Effect] >= 0 THEN "more people" ELSE "fewer people" END)
WHEN 2 THEN "the employee and contingent mix"
WHEN 3 THEN "the country mix"
WHEN 4 THEN "the grade mix"
WHEN 5 THEN (IF [Driver Effect] >= 0 THEN "higher rates" ELSE "lower rates" END)
ELSE "exchange rates" END

// Driver Share
[Driver Effect] / [S Change]
```

```
// Driver Txt
<Sign on [Driver Effect]> + "$" + <M1 on [Driver Effect]> + "M"

// Change Words
IF ROUND(ABS([S Change]), 1) < 10 THEN "$" + <M1 on [S Change]> + "M" ELSE "$" + <Comma on [S Change]> + "M" END
```

`Change Words` is the change rounded for a headline: $403M, or $4.6M for a change under $10M.

---

## 6. The KPI band

Five white cards, 216 × 86 each, at y 86: x **240, 470, 700, 930, 1160** (14 px gaps). Each card is a container (white `#FFFFFF`, border 1 px `#E4E3DD`, **corner radius 14**, inner padding 12 top and bottom, 14 sides) holding one text sheet, with an invisible hover cover over it (6.2).

```
// K1 Title
"Total cost, " + [To Label]

// K1 Line
[S Change Txt] + " vs " + MIN([From Label]) + " (" + [S Change Pct Str] + ")"

// K2 Title
IF [S Volume] >= 0 THEN "More people (volume)" ELSE "Fewer people (volume)" END

// HC Words
"headcount " + [S HC Change Str]

// K2 Line
IF [S Vol Share] >= 0 AND [S Vol Share] <= 1 THEN [S Vol Share Str] + " of the change · " + [HC Words] ELSE [HC Words] END

// K3 Title
IF [S Rate] >= 0 THEN "Higher rates" ELSE "Lower rates" END

// K3 Line
MIN("pay and bill rates, constant FX")

// K4 Title
MIN("Mix of people")

// K4 Line
"level " + [S Level Num] + " · location " + [S Location Num] + " · workforce " + [S Workforce Num]

// K5 Title
MIN("Currency")

// K5 Line
[S Constant Txt] + " before exchange rates"
```

A volume share outside 0 to 100% (volume larger than the whole change, or the opposite sign) is not a share; the line then shows only the headcount change.

Every KPI sheet: Marks **Text**, left aligned, vertical top; Detail `zzTrue`, `zzFalse`; worksheet shading None; tooltip off (the hover cover carries it). Three lines:

| Sheet | Line 1 (Tableau Book 10, slate `#5A6170`) | Line 2 (Tableau Bold 22, navy `#13233A`) | Line 3 (Tableau Book 9, slate `#5A6170`) |
|---|---|---|---|
| **KPI 1** | `<K1 Title>` | `<S Closing Txt>` | `<K1 Line>` |
| **KPI 2** | `<K2 Title>` | `<S Volume Txt>` | `<K2 Line>` |
| **KPI 3** | `<K3 Title>` | `<S Rate Txt>` | `<K3 Line>` |
| **KPI 4** | `<K4 Title>` | `<S Mix Txt>` | `<K4 Line>` |
| **KPI 5** | `<K5 Title>` | `<S Currency Txt>` | `<K5 Line>` |

Expected, default: KPI 1 "Total cost, FY26 · $4,648.1M · +$402.9M vs FY25 (+9.5%)"; KPI 2 "More people (volume) · +$307.1M · 76% of the change · headcount +2,801"; KPI 3 "Higher rates · +$139.8M · pay and bill rates, constant FX"; KPI 4 "Mix of people · +$8.3M · level +22.4 · location −9.3 · workforce −4.8"; KPI 5 "Currency · −$52.2M · +$455.2M before exchange rates".

### 6.1 Hover sentences

```
// K1 Tip 1
"Total workforce cost was " + [S Closing Txt] + " on " + MIN([To Date Text]) + ", against " + [S Opening Txt]
+ " on " + MIN([From Date Text]) + "."

// K1 Tip 2
"Employees' loaded pay run-rate plus contingent workers' annualized bill run-rate. Headcount "
+ [S HC Open Str] + " to " + [S HC Close Str] + " (" + [S HC Change Str] + ")."

// K2 Tip 1
"Volume " + [S Volume Txt] + (IF [S Vol Share] >= 0 AND [S Vol Share] <= 1 THEN ", " + [S Vol Share Str] + " of the change." ELSE "." END)

// K2 Tip 2
"What the change in headcount alone did to cost, with mix, rates and currency at their average over every order of the steps."

// K3 Tip 1
"Rates " + [S Rate Txt] + ": what each person costs moved, at constant exchange rates."

// K3 Tip 2
"Pay raises for employees and bill-rate changes for contingent workers. Promotions to a higher grade count under level mix."

// K4 Tip 1
"Mix " + [S Mix Txt] + " in all: level " + [S Level Num] + ", location " + [S Location Num] + ", workforce " + [S Workforce Num] + "."

// K4 Tip 2
"A positive mix effect means the workforce moved toward costlier grades, countries or worker types; a negative one, toward less costly ones."

// K5 Tip 1
"Exchange rates " + (IF [S Currency] >= 0 THEN "raised" ELSE "lowered" END) + " the reported cost by " + [S Currency Abs Txt] + "."

// K5 Tip 2
"Without the Currency effect the change would be " + [S Constant Txt] + "."
```

Expected, default: "Total workforce cost was $4,648.1M on Jun 30, 2026, against $4,245.2M on Jun 30, 2025." / "… Headcount 39,145 to 41,946 (+2,801)." · "Volume +$307.1M, 76% of the change." · "Rates +$139.8M: …" · "Mix +$8.3M in all: level +22.4, location −9.3, workforce −4.8." · "Exchange rates lowered the reported cost by $52.2M." / "Without the Currency effect the change would be +$455.2M."

### 6.2 Hover covers

Sheets **Hover K1** to **Hover K5**: Rows and Columns `Hover Cell` (headers hidden); Marks **Square**, size slider far right, opacity **0%**, no border; Detail `Hover Cell`, `zzTrue`, `zzFalse`. Command buttons off. Each floats over its card at the card's size (216 × 86).

| Sheet | Tooltip, line 1 (Tableau Book 11, ink `#1F2329`) | Line 2 (Tableau Book 10, slate `#5A6170`) |
|---|---|---|
| Hover K1 | `<K1 Tip 1>` | `<K1 Tip 2>` |
| Hover K2 | `<K2 Tip 1>` | `<K2 Tip 2>` |
| Hover K3 | `<K3 Tip 1>` | `<K3 Tip 2>` |
| Hover K4 | `<K4 Tip 1>` | `<K4 Tip 2>` |
| Hover K5 | `<K5 Tip 1>` | `<K5 Tip 2>` |

---

## 7. The bridge

### 7.1 The title

```
// Bridge Title
"Cost " + (IF [S Change] >= 0 THEN "grew " ELSE "fell " END) + [Change Words]
+ (IF [Driver Share] >= 0.5 AND [Driver Share] <= 1
   THEN ", and " + STR(INT(ROUND([Driver Share] * 100, 0))) + "% of it was " + [Driver Words]
   ELSE "; the largest effect was " + [Driver Words] + " (" + [Driver Txt] + ")" END)

// Bridge Subtitle
"Shapley split of the change, " + MIN([Span Text]) + ", $M nominal · each factor's average effect over every order of the steps"
```

The first form is used when one factor explains half to all of the change; otherwise the title names the largest effect and its size, so it never reads "127% of it". Expected: default "Cost grew $403M, and 76% of it was more people"; FY24 vs FY23 "Cost grew $94M; the largest effect was higher rates (+$118.7M)"; FY25 Q1 vs FY24 Q1 "Cost grew $238M, and 53% of it was higher rates".

Sheet **Bridge Title**: Text, `<Bridge Title>` Tableau Semibold 14 navy `#13233A` / `<Bridge Subtitle>` Tableau Book 10 slate `#5A6170`; left, top; Detail `zzTrue`, `zzFalse`; tooltip off.

### 7.2 The axis floor

```
// Floor Raw
{ MIN(IF [In Selection] AND ([factor_order] = 0 OR [factor_order] = 7) THEN [Effect M] END) } * 0.95

// Floor Step
POWER(10, FLOOR(LOG([Floor Raw])) - 1)

// Axis Floor
FLOOR([Floor Raw] / [Floor Step]) * [Floor Step]

// Floor Text
IF [Axis Floor] >= 1000 THEN "$" + STR(INT([Axis Floor] / 1000)) + "." + STR(INT(ROUND([Axis Floor] / 100, 0)) % 10) + "B"
ELSE "$" + STR(INT([Axis Floor])) + "M" END
```

The floor is 95% of the lower of opening and closing, rounded down to two significant figures. Expected: default 4,000 ("$4.0B"); FY26 Q3 vs FY25 Q3 3,800; Technology 1,700 ("$1.7B"); People 170 ("$170M").

### 7.3 The marks

The sheet is filtered to the selection's 8 rows; the bars are a waterfall built with table calculations along `factor_order`.

```
// Step M
IF [factor_order] = 7 THEN 0 ELSE [Effect M] END

// Bar Top
RUNNING_SUM(SUM([Step M]))

// Bar Size
IF MIN([factor_order]) = 0 OR MIN([factor_order]) = 7 THEN -(RUNNING_SUM(SUM([Step M])) - MIN([Axis Floor]))
ELSE -SUM([Step M]) END

// Label Y
IF SUM([Step M]) < 0 THEN RUNNING_SUM(SUM([Step M])) - SUM([Step M]) ELSE RUNNING_SUM(SUM([Step M])) END

// Bar Kind
IF MIN([factor_order]) = 0 OR MIN([factor_order]) = 7 THEN "level"
ELSEIF ROUND(SUM([Effect M]), 1) >= 0 THEN "adds" ELSE "takes away" END

// Label Kind
IF MIN([factor_order]) = 0 OR MIN([factor_order]) = 7 THEN "level"
ELSEIF ROUND(SUM([Effect M]), 1) >= 0 THEN "adds" ELSE "takes away" END

// Bar Label
IF MIN([factor_order]) = 0 OR MIN([factor_order]) = 7 THEN <M1 on SUM([Effect M])>
ELSE <Sign on SUM([Effect M])> + <M1 on SUM([Effect M])> END

// Factor Head
CASE [factor_order] WHEN 0 THEN "Opening" WHEN 7 THEN "Closing" ELSE [factor] END

// Factor Sub
CASE [factor_order]
WHEN 0 THEN [From Label] WHEN 7 THEN [To Label]
WHEN 1 THEN "people" WHEN 2 THEN "employees, contingent" WHEN 3 THEN "countries"
WHEN 4 THEN "grades" WHEN 5 THEN "pay, bill rates" ELSE "exchange rates" END
```

How it closes: the running sum of Step M at row k is the cost after k factors have moved; the closing row adds 0, so its running sum is the closing cost. Each factor's Gantt bar hangs from that point by minus its effect, so it spans the previous level to the new one. The opening and closing bars hang down to the axis floor. `Label Y` is the top of each bar, so every label sits above its bar. Bar Kind and Label Kind are the same test twice, so the bars and the labels get separate color legends.

Sheet **Bridge**:
1. Filter `In Selection` = True.
2. Columns `factor_order` (discrete, header hidden), then `Factor Head` (header at the bottom, Tableau Semibold 9 ink `#1F2329`), then `Factor Sub` (header at the bottom, Tableau Book 8 slate `#5A6170`). Headers wrap; column width even.
3. Rows `Bar Top`, then `Label Y`; Dual Axis; Synchronize Axis. Every table calculation: **Compute Using Specific Dimensions `factor_order`, `Factor Head` and `Factor Sub`**, sorted by `factor_order`. (`Factor Head` and `Factor Sub` are on Columns only to label the bars; left out of the addressing, they would partition every column and restart the running sum.)
4. Left axis: no title, Automatic, **Include zero off**, labels Tableau Book 8 axis gray `#8C9BB0`, format Number Custom `$#,##0"M"`; right axis hidden.
5. Marks `Bar Top`: **Gantt Bar**; Size `Bar Size`; Color `Bar Kind`: level `#8C9BB0`, adds teal `#0F6E56`, takes away sand `#B8A888`; opacity 100%, no border; size slider at about 60% (the bars a little wider than their gaps).
6. Marks `Label Y`: **Text**; Text `Bar Label`; Color `Label Kind`: level navy `#13233A`, adds teal `#0F6E56`, takes away dark sand `#7D6A45`; Tableau Semibold 10; alignment center, **bottom** (the label sits on the point, above the bar).
7. Analytics: **Reference Line**, Entire Table, on the left axis, value `MIN(Axis Floor)`: solid 1 px `#D5DBE4`; label custom `Axis starts at <Floor Text>` (insert the field), Tableau Book 8 slate `#5A6170`, at the left, below the line. The reference line also holds the automatic axis down at the floor.
8. Grid lines: rows solid 1 px `#ECEDEA`; columns none. Zero line, axis rulers, borders and row/column dividers None. Shading None (the card is white).
9. Tooltip (both cards; command buttons off): see 7.4.

Expected bars, default (labels): Opening **4,245.2** · Volume **+307.1** · Workforce mix **−4.8** · Location mix **−9.3** · Level mix **+22.4** · Rate **+139.8** · Currency **−52.2** · Closing **4,648.1**. Running levels: 4,245.2 · 4,552.3 · 4,547.5 · 4,538.2 · 4,560.6 · 4,700.4 · 4,648.1 · 4,648.1. Axis starts at $4.0B. Under each bar: Opening / FY25, Volume / people, Workforce mix / employees, contingent, Location mix / countries, Level mix / grades, Rate / pay, bill rates, Currency / exchange rates, Closing / FY26.

### 7.4 The bridge's hover

```
// Tip Head
MIN([Factor Head]) + ", " + (IF MIN([factor_order]) = 0 THEN MIN([From Date Text]) ELSEIF MIN([factor_order]) = 7 THEN MIN([To Date Text]) ELSE MIN([Span Text]) END) + ":"

// Tip Value Level
IF [Bar Kind] = "level" THEN "$" + <M1 on SUM([Effect M])> + "M" END

// Tip Value Adds
IF [Bar Kind] = "adds" THEN "+$" + <M1 on SUM([Effect M])> + "M" END

// Tip Value Takes
IF [Bar Kind] = "takes away" THEN "−$" + <M1 on SUM([Effect M])> + "M" END

// Sel Change LOD
{ SUM(IF [In Selection] AND [factor_order] = 7 THEN [Effect M] END) - SUM(IF [In Selection] AND [factor_order] = 0 THEN [Effect M] END) }

// Tip Share
IF MIN([factor_order]) = 0 THEN <Comma on MIN([opening_headcount])> + " people"
ELSEIF MIN([factor_order]) = 7 THEN <Comma on MIN([closing_headcount])> + " people"
ELSEIF MIN([Sel Change LOD]) <> 0 THEN STR(INT(ROUND(SUM([Effect M]) / MIN([Sel Change LOD]) * 100, 0))) + "% of the change"
   + (IF MIN([factor_order]) = 1 THEN " · headcount " + <Comma on MIN([opening_headcount])> + " to " + <Comma on MIN([closing_headcount])> ELSE "" END)
END

// Tip Order
IF MIN([factor_order]) >= 1 AND MIN([factor_order]) <= 6
THEN "One fixed order of the steps would give " + <Sign on SUM([Seq M])> + "$" + <M1 on SUM([Seq M])> + "M, a bias of "
     + <Sign on SUM([Bias M])> + "$" + <M1 on SUM([Bias M])> + "M." END
```

On a bar, `S Change` would sum over that bar's one row and come back empty, so `Tip Share` reads the selection's change from the FIXED LOD `Sel Change LOD`.

Tooltip layout:
- Line 1: `<Tip Head>` Tableau Semibold 11 navy `#13233A`, a space, then `<Tip Value Level>` Tableau Bold 11 navy, `<Tip Value Adds>` Tableau Bold 11 teal `#0F6E56`, `<Tip Value Takes>` Tableau Bold 11 dark sand `#7D6A45` (only one is ever not empty).
- Line 2: `<ATTR(factor_meaning)>` Tableau Book 10 ink `#1F2329` (a dimension only on the tooltip must be ATTR, or the pill turns red and the sheet blanks).
- Line 3: `<Tip Share>` Tableau Book 10 slate `#5A6170`.
- Line 4: `<Tip Order>` Tableau Book 9 slate `#5A6170`.

Expected, default, the Rate bar: "Rate, Jun 30, 2025 to Jun 30, 2026: **+$139.8M**" / "What each person costs at constant exchange rates: pay and bill rates" / "35% of the change" / "One fixed order of the steps would give +$145.2M, a bias of +$5.5M." The Volume bar: "… 76% of the change · headcount 39,145 to 41,946". The Closing bar: "Closing, Jun 30, 2026: $4,648.1M" / "Total workforce cost at the later date" / "41,946 people".

### 7.5 The note under the chart

Sheet **Bridge Note**: Text, one mark; `Axis starts at <MIN(Floor Text)> so the factors are visible.` Tableau Book 9 slate `#5A6170`, then ` Teal adds cost, sand takes it away; the six effects add up to the change exactly.` Tableau Book 9 slate. Detail `zzTrue`, `zzFalse`; tooltip off.

---

## 8. The order of the steps

Shapley against one fixed order (the sequential split in the order Volume, Workforce mix, Location mix, Level mix, Rate, Currency). The bars show how close the two are; the bias column shows what the order alone would have moved.

```
// Bias Max Abs
MAX(MAX(MAX(ABS([S Bias Volume]), ABS([S Bias Workforce])), MAX(ABS([S Bias Location]), ABS([S Bias Level]))), MAX(ABS([S Bias Rate]), ABS([S Bias Currency])))

// Bias Driver
IF ABS([S Bias Volume]) = [Bias Max Abs] THEN "Volume"
ELSEIF ABS([S Bias Workforce]) = [Bias Max Abs] THEN "Workforce mix"
ELSEIF ABS([S Bias Location]) = [Bias Max Abs] THEN "Location mix"
ELSEIF ABS([S Bias Level]) = [Bias Max Abs] THEN "Level mix"
ELSEIF ABS([S Bias Rate]) = [Bias Max Abs] THEN "Rate"
ELSE "Currency" END

// Bias Driver Value
CASE [Bias Driver] WHEN "Volume" THEN [S Bias Volume] WHEN "Workforce mix" THEN [S Bias Workforce]
WHEN "Location mix" THEN [S Bias Location] WHEN "Level mix" THEN [S Bias Level]
WHEN "Rate" THEN [S Bias Rate] ELSE [S Bias Currency] END

// Bias Subtitle
"A fixed order would move " + [Bias Driver] + " by " + <Sign on [Bias Driver Value]> + "$" + <M1 on [Bias Driver Value]> + "M; Shapley averages every order"

// Bias Text
<Sign on SUM([Bias M])> + <M1 on SUM([Bias M])>

// Bias Notable
IF ABS(SUM([Bias M])) >= 1 THEN "notable" ELSE "small" END
```

Sheet **Bias Title**: Text, `The order of the steps changes the answer` Tableau Semibold 14 navy `#13233A` / `<Bias Subtitle>` Tableau Book 10 slate `#5A6170` / legend line: `■` Tableau Book 10 navy `#13233A`, ` Shapley (every order)   ` Tableau Book 9 slate, `■` Tableau Book 10 mist `#B9C3D1`, ` One fixed order   ` Tableau Book 9 slate, `Bias = fixed order − Shapley, $M` Tableau Book 9 slate. Left, top; Detail `zzTrue`, `zzFalse`; tooltip off.

Sheet **Bias Bars**:
1. Filters `In Selection` = True and `Is Factor` = True.
2. Rows `factor_order` (header hidden), `Factor Head` (header shown at the left, Tableau Book 10 ink `#1F2329`, left aligned), `Measure Names` (header hidden).
3. Columns `Measure Values` with two measures only: `SUM(Effect M)` renamed **Shapley**, `SUM(Seq M)` renamed **One fixed order**.
4. Marks **Bar**; Color `Measure Names`: Shapley navy `#13233A`, One fixed order mist `#B9C3D1`; size about 70% of the row.
5. Label the values: Tableau Book 8 slate `#5A6170`, at the bar end, format Number Custom `+#,##0.0;"−"#,##0.0`.
6. Axis hidden; zero line solid 1 px `#D5DBE4`; grid none; row dividers none; shading None.
7. Tooltip: `<Factor Head>` Tableau Semibold 10 navy / `Shapley <SUM(Effect M)> · one fixed order <SUM(Seq M)> · bias <Bias Text>` Tableau Book 10 slate (the numbers formatted as in 5).

Sheet **Bias Column**: same filters; Rows `factor_order` (header hidden); Marks **Text**, `<Bias Text>`; Color `Bias Notable`: notable navy `#13233A`, small axis gray `#8C9BB0`; Tableau Semibold 10, right aligned, middle. Shading None, no lines, tooltip off, Detail `zzTrue`, `zzFalse`. It floats beside Bias Bars at the same height, so its six rows line up with the six factor pairs.

Expected, default:

| Factor | Shapley | One fixed order | Bias |
|---|---:|---:|---:|
| Volume | +307.1 | +303.8 | −3.3 |
| Workforce mix | −4.8 | −5.3 | −0.5 |
| Location mix | −9.3 | −9.1 | +0.1 |
| Level mix | +22.4 | +23.5 | +1.1 |
| Rate | +139.8 | +145.2 | **+5.5** |
| Currency | −52.2 | −55.2 | −2.9 |

Subtitle "A fixed order would move Rate by +$5.5M; Shapley averages every order". Notable (navy): Volume, Level mix, Rate, Currency.

---

## 9. Five fiscal years

The selected group's five fiscal years, each against the year before: the pairs at offsets 0, 4, 8, 12 and 16.

```
// Table Column
CASE [factor_order] WHEN 1 THEN "Volume" WHEN 2 THEN "Mix" WHEN 3 THEN "Mix" WHEN 4 THEN "Mix"
WHEN 5 THEN "Rate" WHEN 6 THEN "Currency" END

// Table Col Order
CASE [factor_order] WHEN 1 THEN 1 WHEN 2 THEN 2 WHEN 3 THEN 2 WHEN 4 THEN 2 WHEN 5 THEN 3 WHEN 6 THEN 4 END

// Year Row
[In Group] AND [Is Year Pair] AND [Is Factor]

// Cell Text
<Sign on SUM([Effect M])> + <M1 on SUM([Effect M])>

// Cell Kind
IF ROUND(SUM([Effect M]), 1) >= 0 THEN "adds" ELSE "takes away" END

// Y Years
{ COUNTD(IF [In Group] AND [Is Year Pair] THEN [fiscal_year] END) }

// Y Rate Up
{ SUM(IF [In Group] AND [Is Year Pair] AND [factor_order] = 5 AND [Effect M] > 0 THEN 1 END) }

// Y Cur Min
{ MIN(IF [In Group] AND [Is Year Pair] AND [factor_order] = 6 THEN [Effect M] END) }

// Y Cur Max
{ MAX(IF [In Group] AND [Is Year Pair] AND [factor_order] = 6 THEN [Effect M] END) }

// Year Title
(IF ZN([Y Rate Up]) = [Y Years] THEN "Rates rose every year"
 ELSEIF ZN([Y Rate Up]) = 0 THEN "Rates fell every year"
 ELSE "Rates rose in " + STR(ZN([Y Rate Up])) + " of " + STR([Y Years]) + " years" END)
+ "; currency " + (IF [Y Cur Min] < 0 AND [Y Cur Max] > 0 THEN "swung both ways"
 ELSEIF [Y Cur Max] < 0 THEN "lowered cost every year" ELSE "raised cost every year" END)

// Year Subtitle
(IF [Is Company] THEN "All of Arcadia" ELSE [p_Group] END) + ", $M nominal, each fiscal year against the year before"

// Year Row Label
[Row To Label]

// FY End Words
{ MIN(IF [Pair Offset] = 0 THEN LEFT(DATENAME('month', [to_month_end]), 3) + " " + STR(DAY([to_month_end])) END) }

// Year Note
"Mix = workforce + location + level mix. Each row: " + [FY End Words] + " against the " + [FY End Words] + " a year before."
```

Sheet **Year Title**: Text, `<MIN(Year Title)>` Tableau Semibold 14 navy `#13233A` (wraps to two lines) / `<MIN(Year Subtitle)>` Tableau Book 10 slate `#5A6170`. Left, top; Detail `zzTrue`, `zzFalse`; tooltip off.

Sheet **Year Table**:
1. Filter `Year Row` = True.
2. Rows `Year Row Label` (sorted by `fiscal_year` ascending; header at the left, Tableau Semibold 10 navy `#13233A`, header title "FY").
3. Columns `Table Col Order` (header hidden), `Table Column` (header at the top, Tableau Semibold 9 slate `#5A6170`).
4. Marks **Text**, `<Cell Text>`; Color `Cell Kind`: adds teal `#0F6E56`, takes away dark sand `#7D6A45`; Tableau Book 10; alignment left, middle.
5. Header band: Format > Shading > Header, `#F3F3EF` (the column titles sit on a light band); rows white, no banding; row dividers solid 1 px `#ECEDEA` between rows; no column dividers.
6. Tooltip: `<Year Row Label> · <Table Column>: <Cell Text>` Tableau Book 10 ink `#1F2329`. Both fields are already in the view, so nothing goes on the Tooltip shelf (a Rows field is never repeated there).

Sheet **Year Note**: Text, `<MIN(Year Note)>` Tableau Book 9 slate `#5A6170`; Detail `zzTrue`, `zzFalse`; tooltip off.

Expected, all of Arcadia (title "Rates rose every year; currency swung both ways"; note "Mix = workforce + location + level mix. Each row: Jun 30 against the Jun 30 a year before."):

| FY | Volume | Mix | Rate | Currency |
|---|---:|---:|---:|---:|
| FY22 | +220.3 | −8.4 | +98.0 | −138.9 |
| FY23 | +277.1 | −9.5 | +112.1 | +36.2 |
| FY24 | −4.3 | +5.8 | +118.7 | −26.7 |
| FY25 | +214.1 | −4.5 | +131.8 | +86.4 |
| FY26 | +307.1 | +8.3 | +139.8 | −52.2 |

Mix is the sum of the three unrounded mix effects, rounded once: FY23 reads −9.5 and FY25 −4.5, not the −9.6 and −4.4 that adding three rounded numbers gives.

---

## 10. The rail

A 216 px navy `#13233A` container; controls are one-mark sheets whose Shape draws the control and whose label is the text. Shapes come from the palette **Arcadia D4** (`My Tableau Repository/Shapes/Arcadia D4/`); in that folder, sorted by name, they are: 1 `d2_info_close.png`, 2 `d2_info_open.png`, 3 `d4_field_capsule.png`, 4 `d4_field_capsule_dark.png`, 5 `d4_reset.png`, 10 `d4_tick_dim.png`, 11 `d4_tick_off.png`, 12 `d4_tick_on.png` (the numbers are each file's place in the picker; recount if your folder holds other files). A sheet with only aggregates and constants on its shelves draws one mark.

```
// Org Capsule Shape
IF [Is Company] THEN "d4_field_capsule_dark" ELSE "d4_field_capsule" END

// Org Text Light
IF NOT [Is Company] THEN [Org Field Text] END

// Org Text Dark
IF [Is Company] THEN [Org Field Text] END

// Org Sub Text
<Comma on [S HC Close]> + " people on " + MIN([To Date Text])

// Toggle Period Panel
NOT [p_PeriodOpen]

// Toggle Org Panel
NOT [p_OrgOpen]

// Toggle Info
NOT [p_InfoOpen]

// Info Shape
IF [p_InfoOpen] THEN "d2_info_close" ELSE "d2_info_open" END

// Default Group
MIN([Company Name])

// Rail Line 1
"Report date " + [As Of Text]
```

| Sheet | Shape | Label | Detail | Tooltip |
|---|---|---|---|---|
| **Period Field** | `d4_field_capsule.png` (always white: the period is always a choice) | `<Pair Label>` Tableau Semibold 9 navy `#13233A`, left | `Toggle Period Panel`, `Close Panel`, `zzTrue`, `zzFalse` | "Choose the two dates to compare" |
| **Period Sub** | none (Text) | `<Span Text>` Tableau Book 8 `#8A97A8` | `zzTrue`, `zzFalse` | off |
| **Org Field** | `Org Capsule Shape` | `<Org Text Light>` Tableau Semibold 9 navy `#13233A` + `<Org Text Dark>` Tableau Medium 9 `#E4E9F0`, left | `Toggle Org Panel`, `Close Panel`, `zzTrue`, `zzFalse` | "Choose all of Arcadia or one function" |
| **Org Sub** | none (Text) | `<Org Sub Text>` Tableau Book 8 `#8A97A8` | `zzTrue`, `zzFalse` | off |
| **Reset** | `d4_reset.png` | none | `Zero Pair`, `Default Group`, `Close Panel`, `zzTrue`, `zzFalse` | "Reset to default view" |
| **Info Button** | `Info Shape` | none | `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse` | "How the bridge works" |
| **Rail As Of** | none (Text) | `<Rail Line 1>` Tableau Semibold 9 `#E4E9F0` / `Nominal USD, ECB month-end rates` Tableau Book 9 `#B9C3D1` / `Employees and contingent workers` Tableau Book 9 `#B9C3D1` | `zzTrue`, `zzFalse` | off |

Capsules are drawn at shape size 12 (the whole pill shows), Reset at 10. Sheet **Page Title**: Text, `Workforce Cost Bridge` Tableau Bold 20 navy `#13233A` / `<Page Subtitle>` Tableau Book 11 slate `#5A6170`; left, top; Detail `zzTrue`, `zzFalse`; tooltip off.

Expected: default Period "FY26 vs FY25" / "Jun 30, 2025 to Jun 30, 2026"; Organization "All of Arcadia" (dark capsule) / "41,946 people on Jun 30, 2026"; Technology "Technology" (white capsule) / "19,157 people on Jun 30, 2026"; rail foot "Report date Jun 30, 2026".

---

## 11. The popovers

Each hangs from the rail's right edge (x 216): a navy `#13233A` vertical container, padding 0, no border, shown by its open flag (Layout > Control visibility using value). Inside: header 44 px (title Tableau Bold 12 white `#FFFFFF`, 12 px from the left; ✕ at the right), the line image `d2_popover_line_wide.png` 9 px, the body, a footer 30 px (Tableau Book 9 `#8FA0B8`, one line, 12 px from the left). The ✕ sheets (**Period Close**, **Org Close**, **Info Close**): Text `✕` Tableau Book 12 `#B8C0CC`, Detail `zzFalse`, `zzTrue`, `Close Panel`, tooltip "Close".

The list sheets: one row per option, Marks **Shape** with the tick files `d4_tick_on.png` (12) / `d4_tick_off.png` (11) from **Arcadia D4** (the files carry the state, so no color on the shape), the tick on a hidden axis at the left, **every tick at shape size 8 in every list** (a fixed size, never sized by the view, so ticks do not grow when a list is short), rows 22 px, fit width; row banding none; tooltip off.

```
// Pair Option Row
[In Group] AND [factor_order] = 0

// Pair Shape
IF MIN([Pair Offset]) = [p_Pair] THEN "d4_tick_on" ELSE "d4_tick_off" END

// Pair Option Name
MIN([Row To Label]) + " vs " + MIN([Row From Label])

// Pair Option Date
(IF RIGHT(MIN([fiscal_quarter_label]), 2) = "Q4" THEN "full year · " ELSE "" END)
+ LEFT(DATENAME('month', MIN([to_month_end])), 3) + " " + STR(DAY(MIN([to_month_end])))

// Group Option Row
[In Pair] AND [factor_order] = 0

// Group Shape
IF MIN([group_name]) = [p_Group] THEN "d4_tick_on" ELSE "d4_tick_off" END

// Group Option Name
IF MIN([view_name]) = "Company" THEN "All of Arcadia" ELSE MIN([group_name]) END

// Group Option People
<Comma on MIN([closing_headcount])> + " people"
```

| Popover | x, y, w × h | Body |
|---|---|---|
| **Period Popover** | 216, 132, 360 × 470 | Title "Compare". **Pair List**: Filter `Pair Option Row` = True (17 rows). Rows `Pair Offset` (header hidden, sorted ascending: the latest first). Shape `Pair Shape`; label `  <Pair Option Name>` Tableau Book 10 `#E4E9F0` then `   <Pair Option Date>` Tableau Book 9 `#8FA0B8`. Detail `Pair Offset`, `Close Panel`, `zzTrue`, `zzFalse`. Footer "Each choice compares a quarter-end with the same date a year before." |
| **Org Popover** | 216, 228, 360 × 300 | Title "Organization". **Group List**: Filter `Group Option Row` = True (9 rows). Rows `view_order`, `group_name` (headers hidden; the company first, then the functions A to Z). Shape `Group Shape`; label `  <Group Option Name>` Tableau Book 10 `#E4E9F0` then `   <Group Option People>` Tableau Book 9 `#8FA0B8`. Detail `group_name`, `Close Panel`, `zzTrue`, `zzFalse`. Footer "Each function is its own bridge: its effects add up to its own change." |
| **Info Popover** | 216, 24, 591 × 420 | Title "How the bridge works", then the text below |

Pair List expected: "FY26 vs FY25 · full year · Jun 30" (ticked by default), "FY26 Q3 vs FY25 Q3 · Mar 31", "FY26 Q2 vs FY25 Q2 · Dec 31", … "FY22 vs FY21 · full year · Jun 30". Group List: "All of Arcadia · 41,946 people", "Commercial · …", … "Technology · 19,157 people".

**Info text** (lead-ins Tableau Semibold 10 white `#FFFFFF`, body Tableau Book 10 `#B8C0CC`):

> **What is measured.** Total workforce cost on a date: employees' loaded pay run-rate (base pay × FTE × (1 + the country's fringe rate)) plus contingent workers' annualized bill run-rate, converted to USD at the ECB rate on that date. It is a run-rate, not spend: what a year would cost at that day's workforce and pay.
>
> **The six factors.** Cost is people × the mix of people × what each costs × currency. Volume is the number of people; workforce mix the balance of employees and contingent workers; location mix the countries; level mix the grades (or contingent types); rate the cost per head at constant exchange rates; currency what exchange rates did to the reported cost.
>
> **Why Shapley.** Moving the factors one at a time explains the change exactly, but the answer depends on the order: the factor moved first is valued at the old levels of the others. Shapley gives each factor its average effect over all 720 orders, so none is favored, and the six effects still add up to the change exactly. The card on the right shows how far one fixed order would drift.
>
> **Limits.** Bonus, equity and allowances are not in the run-rate. A grade or country that appears on one date only counts as mix, never as rate.
>
> **Data.** Arcadia Systems is fictional; all data is synthetic. Executive officers are excluded.

---

## 12. Assembling the dashboard

### 12.1 The page

New dashboard **Dashboard**, **Fixed 1400 × 850**, title off, shading **`#F3F3EF`**. Every item floating unless inside a container; show title off; padding 0 unless stated. Corner radius is under Layout > Background (Tableau 2026.1+).

### 12.2 Floating items, back to front

| # | Item | x | y | w | h | Format |
|---:|---|---:|---:|---:|---:|---|
| 1 | `Page Title` | 240 | 16 | 1136 | 56 | |
| 2–6 | Containers `KPI 1` … `KPI 5`, each holding its sheet | 240, 470, 700, 930, 1160 | 86 | 216 | 86 | white `#FFFFFF`, border 1 px `#E4E3DD`, **radius 14**, inner padding 12 top and bottom, 14 sides |
| 7–11 | `Hover K1` … `Hover K5` | 240, 470, 700, 930, 1160 | 86 | 216 | 86 | over their cards |
| 12 | Container `Card: Bridge` (vertical) | 240 | 186 | 724 | 626 | white, border 1 px `#E4E3DD`, **radius 14**, inner padding 16 top, 14 sides, 12 bottom: `Bridge Title` 696 × 50 · `Bridge` 696 × 512 · `Bridge Note` 696 × 36 |
| 13 | Container `Card: Order` (vertical) | 988 | 186 | 388 | 302 | white, border 1 px `#E4E3DD`, **radius 14**, inner padding 16 top, 14 sides, 12 bottom: `Bias Title` 360 × 74 · horizontal container 360 × 200 holding `Bias Bars` 304 × 200 and `Bias Column` 56 × 200 |
| 14 | Container `Card: Years` (vertical) | 988 | 502 | 388 | 310 | white, border 1 px `#E4E3DD`, **radius 14**, inner padding 16 top, 14 sides, 12 bottom: `Year Title` 360 × 58 · `Year Table` 360 × 204 · `Year Note` 360 × 20 |
| 15 | Footnote text | 240 | 826 | 1136 | 16 | "Arcadia Systems is fictional; all data is synthetic. Executive officers excluded. Effects are Shapley values: each factor's average effect over every order of the six steps, so they add up to the change." Tableau Book 9 slate `#5A6170` |
| 16 | Container `Rail` (vertical) | 0 | 0 | 216 | 850 | navy `#13233A`, inner padding 8 left and right (12.3) |
| 17 | `Period Popover` | 216 | 132 | 360 | 470 | visibility `p_PeriodOpen` |
| 18 | `Org Popover` | 216 | 228 | 360 | 300 | visibility `p_OrgOpen` |
| 19 | `Info Popover` | 216 | 24 | 591 | 420 | visibility `p_InfoOpen` |

The rail sits in front of every page item; the popovers in front of everything.

### 12.3 Inside the rail (tiled, 200 wide, every item fixed height except the flexible blank)

| Item | h | y |
|---|---:|---:|
| Blank | 24 | 0 |
| Container `Rail Top`: logo `arcadia_logo_horizontal_reverse.png` 200 × 40, Blank 12, `Info Button` row 28 (Blank 172 + 28 × 28) | 80 | 24 |
| Blank | 28 | 104 |
| Text PERIOD (Tableau Semibold 8 `#B8C4D6`) 16 · Blank 6 · `Period Field` 32 · `Period Sub` 18 · Blank 24 | 96 | 132 |
| Text ORGANIZATION 16 · Blank 6 · `Org Field` 32 · `Org Sub` 18 · Blank 24 | 96 | 228 |
| Image `arcadia_rail_divider.png` | 24 | 324 |
| `Reset` | 32 | 348 |
| Blank (flexible) | rest | |
| `Rail As Of` | 56 | 770 |
| Blank | 24 | 826 |

The popovers' tops line up with their headings: Period y 132, Organization y 228.

### 12.4 Actions

**Change Parameter** (run on Select; aggregation None; clearing the selection Keep current value; the source field on the source sheet's Detail):

| Name | Source sheet | Target | Field |
|---|---|---|---|
| Open period popover | Period Field | `p_PeriodOpen` | `Toggle Period Panel` |
| Period closes others | Period Field | `p_OrgOpen`, `p_InfoOpen` (two actions) | `Close Panel` |
| Set pair | Pair List | `p_Pair` | `Pair Offset` |
| Close period popover on pick | Pair List | `p_PeriodOpen` | `Close Panel` |
| Period popover on x | Period Close | `p_PeriodOpen` | `Close Panel` |
| Open org popover | Org Field | `p_OrgOpen` | `Toggle Org Panel` |
| Org closes others | Org Field | `p_PeriodOpen`, `p_InfoOpen` (two actions) | `Close Panel` |
| Set group | Group List | `p_Group` | `group_name` |
| Close org popover on pick | Group List | `p_OrgOpen` | `Close Panel` |
| Org popover on x | Org Close | `p_OrgOpen` | `Close Panel` |
| Reset pair | Reset | `p_Pair` | `Zero Pair` |
| Reset group | Reset | `p_Group` | `Default Group` |
| Reset closes popovers | Reset | the three open flags (three actions) | `Close Panel` |
| Open info | Info Button | `p_InfoOpen` | `Toggle Info` |
| Info closes others | Info Button | `p_PeriodOpen`, `p_OrgOpen` (two actions) | `Close Panel` |
| Info popover on x | Info Close | `p_InfoOpen` | `Close Panel` |

21 in all.

**Deselect:** one Filter action per clickable sheet: source and target the same sheet, run on Select, clearing **Show all values**, `zzTrue` → `zzFalse`. Sheets: Page Title, KPI 1 to KPI 5, Hover K1 to Hover K5, Bridge Title, Bridge Note, Bias Title, Bias Column, Year Title, Year Note, Period Field, Period Sub, Org Field, Org Sub, Reset, Info Button, Rail As Of, Pair List, Group List, Period Close, Org Close, Info Close (29). Not on `Bridge`, `Bias Bars` or `Year Table`: a selection there is useful.

---

## 13. Checks and click tests

### 13.1 Ties at every state

- The bridge closes: Opening + the six labels = Closing (to 0.1 from rounding the labels).
- KPI 1's change = KPI 2 + KPI 3 + KPI 4 + KPI 5 (Volume + Rate + Mix + Currency).
- KPI 5's "before exchange rates" = KPI 1's change − KPI 5.
- The FY rows of the five-year table equal the bridge at `p_Pair` 0, 4, 8, 12, 16 (Mix = the three mix bars).
- The Shapley bars of the order card equal the bridge's factor labels.

### 13.2 Values

Computed by `python3 tableau/builder/d6/check_values.py`; `--verify` also confirms that all 153 views close and that no bar dips below its axis floor.

**All of Arcadia, every pair** ($M; the bars' labels):

| p_Pair | Pair | Span | Total cost | Change | Volume | Workforce mix | Location mix | Level mix | Rate | Currency | Axis floor |
|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | FY26 vs FY25 | Jun 30, 2025 to Jun 30, 2026 | $4,648.1M | +$402.9M (+9.5%) | +307.1 | −4.8 | −9.3 | +22.4 | +139.8 | −52.2 | $4.0B |
| 1 | FY26 Q3 vs FY25 Q3 | Mar 31, 2025 to Mar 31, 2026 | $4,517.4M | +$482.4M (+12.0%) | +276.2 | −3.8 | −6.7 | +24.6 | +135.0 | +57.2 | $3.8B |
| 2 | FY26 Q2 vs FY25 Q2 | Dec 31, 2024 to Dec 31, 2025 | $4,448.1M | +$539.9M (+13.8%) | +252.0 | −2.8 | −12.2 | +28.2 | +134.1 | +140.7 | $3.7B |
| 3 | FY26 Q1 vs FY25 Q1 | Sep 30, 2024 to Sep 30, 2025 | $4,342.0M | +$396.1M (+10.0%) | +236.6 | −2.8 | −13.6 | +23.3 | +135.5 | +17.1 | $3.7B |
| 4 | FY25 vs FY24 | Jun 30, 2024 to Jun 30, 2025 | $4,245.2M | +$427.8M (+11.2%) | +214.1 | −2.6 | −23.6 | +21.8 | +131.8 | +86.4 | $3.6B |
| 5 | FY25 Q3 vs FY24 Q3 | Mar 31, 2024 to Mar 31, 2025 | $4,034.9M | +$250.0M (+6.6%) | +153.9 | −1.0 | −24.2 | +14.7 | +133.0 | −26.4 | $3.5B |
| 6 | FY25 Q2 vs FY24 Q2 | Dec 31, 2023 to Dec 31, 2024 | $3,908.2M | +$110.8M (+2.9%) | +102.9 | +0.2 | −19.1 | +7.0 | +123.8 | −104.0 | $3.6B |
| 7 | FY25 Q1 vs FY24 Q1 | Sep 30, 2023 to Sep 30, 2024 | $3,946.0M | +$237.6M (+6.4%) | +49.1 | +1.5 | −16.0 | +9.2 | +125.6 | +68.2 | $3.5B |
| 8 | FY24 vs FY23 | Jun 30, 2023 to Jun 30, 2024 | $3,817.4M | +$93.5M (+2.5%) | −4.3 | +2.8 | −9.1 | +12.1 | +118.7 | −26.7 | $3.5B |
| 9 | FY24 Q3 vs FY23 Q3 | Mar 31, 2023 to Mar 31, 2024 | $3,785.0M | +$187.6M (+5.2%) | +68.7 | +1.6 | −13.7 | +12.0 | +111.7 | +7.3 | $3.4B |
| 10 | FY24 Q2 vs FY23 Q2 | Dec 31, 2022 to Dec 31, 2023 | $3,797.4M | +$304.5M (+8.7%) | +137.9 | +0.6 | −14.3 | +15.9 | +106.1 | +58.3 | $3.3B |
| 11 | FY24 Q1 vs FY23 Q1 | Sep 30, 2022 to Sep 30, 2023 | $3,708.4M | +$383.2M (+11.5%) | +201.2 | −0.4 | −19.8 | +13.1 | +106.1 | +82.9 | $3.1B |
| 12 | FY23 vs FY22 | Jun 30, 2022 to Jun 30, 2023 | $3,723.9M | +$415.8M (+12.6%) | +277.1 | −1.6 | −13.2 | +5.2 | +112.1 | +36.2 | $3.1B |
| 13 | FY23 Q3 vs FY22 Q3 | Mar 31, 2022 to Mar 31, 2023 | $3,597.3M | +$298.2M (+9.0%) | +262.9 | −1.5 | −12.3 | +3.3 | +113.6 | −67.8 | $3.1B |
| 14 | FY23 Q2 vs FY22 Q2 | Dec 31, 2021 to Dec 31, 2022 | $3,493.0M | +$261.7M (+8.1%) | +245.4 | −1.2 | −9.4 | +6.5 | +112.0 | −91.7 | $3.0B |
| 15 | FY23 Q1 vs FY22 Q1 | Sep 30, 2021 to Sep 30, 2022 | $3,325.2M | +$156.3M (+4.9%) | +229.3 | −0.9 | −4.9 | +5.1 | +105.6 | −177.9 | $3.0B |
| 16 | FY22 vs FY21 | Jun 30, 2021 to Jun 30, 2022 | $3,308.1M | +$171.1M (+5.5%) | +220.3 | −1.4 | −1.6 | −5.4 | +98.0 | −138.9 | $2.9B |

**Page texts, all of Arcadia, every pair:**

| p_Pair | Bridge title | KPI 2 title · line | KPI 5 line | Order-card subtitle (before "; Shapley averages every order") |
|---:|---|---|---|---|
| 0 | Cost grew $403M, and 76% of it was more people | More people (volume) · 76% of the change · headcount +2,801 | +$455.2M before exchange rates | A fixed order would move Rate by +$5.5M |
| 1 | Cost grew $482M, and 57% of it was more people | More people (volume) · 57% of the change · headcount +2,561 | +$425.2M before exchange rates | A fixed order would move Volume by −$6.6M |
| 2 | Cost grew $540M; the largest effect was more people (+$252.0M) | More people (volume) · 47% of the change · headcount +2,356 | +$399.2M before exchange rates | A fixed order would move Volume by −$8.6M |
| 3 | Cost grew $396M, and 60% of it was more people | More people (volume) · 60% of the change · headcount +2,194 | +$379.0M before exchange rates | A fixed order would move Volume by −$4.5M |
| 4 | Cost grew $428M, and 50% of it was more people | More people (volume) · 50% of the change · headcount +2,027 | +$341.4M before exchange rates | A fixed order would move Volume by −$5.6M |
| 5 | Cost grew $250M, and 62% of it was more people | More people (volume) · 62% of the change · headcount +1,480 | +$276.3M before exchange rates | A fixed order would move Rate by +$3.1M |
| 6 | Cost grew $111M; the largest effect was higher rates (+$123.8M) | More people (volume) · 93% of the change · headcount +997 | +$214.8M before exchange rates | A fixed order would move Currency by −$3.6M |
| 7 | Cost grew $238M, and 53% of it was higher rates | More people (volume) · 21% of the change · headcount +476 | +$169.3M before exchange rates | A fixed order would move Currency by +$1.7M |
| 8 | Cost grew $94M; the largest effect was higher rates (+$118.7M) | Fewer people (volume) · headcount −42 | +$120.2M before exchange rates | A fixed order would move Level mix by +$1.2M |
| 9 | Cost grew $188M, and 60% of it was higher rates | More people (volume) · 37% of the change · headcount +680 | +$180.3M before exchange rates | A fixed order would move Volume by −$1.1M |
| 10 | Cost grew $304M; the largest effect was more people (+$137.9M) | More people (volume) · 45% of the change · headcount +1,368 | +$246.1M before exchange rates | A fixed order would move Volume by −$3.1M |
| 11 | Cost grew $383M, and 53% of it was more people | More people (volume) · 53% of the change · headcount +2,051 | +$300.3M before exchange rates | A fixed order would move Volume by −$5.2M |
| 12 | Cost grew $416M, and 67% of it was more people | More people (volume) · 67% of the change · headcount +2,820 | +$379.7M before exchange rates | A fixed order would move Volume by −$5.5M |
| 13 | Cost grew $298M, and 88% of it was more people | More people (volume) · 88% of the change · headcount +2,657 | +$366.0M before exchange rates | A fixed order would move Rate by +$5.2M |
| 14 | Cost grew $262M, and 94% of it was more people | More people (volume) · 94% of the change · headcount +2,498 | +$353.4M before exchange rates | A fixed order would move Rate by +$6.0M |
| 15 | Cost grew $156M; the largest effect was more people (+$229.3M) | More people (volume) · headcount +2,371 | +$334.2M before exchange rates | A fixed order would move Currency by −$10.0M |
| 16 | Cost grew $171M; the largest effect was more people (+$220.3M) | More people (volume) · headcount +2,269 | +$310.0M before exchange rates | A fixed order would move Currency by −$6.8M |

**Each group, FY26 vs FY25 (`p_Pair` 0):**

| Group | Total cost | Change | Volume | Workforce mix | Location mix | Level mix | Rate | Currency | Axis floor | Bridge title |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| All of Arcadia | $4,648.1M | +$402.9M | +307.1 | −4.8 | −9.3 | +22.4 | +139.8 | −52.2 | $4.0B | Cost grew $403M, and 76% of it was more people |
| Commercial | $988.4M | +$64.3M | +44.8 | +0.0 | −5.3 | +5.2 | +29.7 | −10.2 | $870M | Cost grew $64M, and 70% of it was more people |
| Finance | $235.9M | +$24.9M | +18.9 | +1.9 | −1.8 | +1.7 | +6.3 | −2.1 | $200M | Cost grew $25M, and 76% of it was more people |
| Legal & Compliance | $148.8M | +$16.8M | +11.4 | +0.4 | +1.3 | +0.9 | +4.0 | −1.3 | $120M | Cost grew $17M, and 68% of it was more people |
| Marketing | $187.4M | +$16.5M | +13.6 | +0.8 | −3.0 | +0.5 | +6.4 | −1.7 | $160M | Cost grew $17M, and 82% of it was more people |
| Operations | $512.2M | +$44.7M | +37.5 | −3.1 | −0.7 | +2.1 | +15.3 | −6.4 | $440M | Cost grew $45M, and 84% of it was more people |
| People | $212.3M | +$27.4M | +18.6 | +0.6 | +0.5 | +1.5 | +8.1 | −1.9 | $170M | Cost grew $27M, and 68% of it was more people |
| Product | $346.8M | +$31.7M | +26.7 | −0.7 | −2.0 | +0.6 | +10.3 | −3.1 | $290M | Cost grew $32M, and 84% of it was more people |
| Technology | $2,016.3M | +$176.8M | +135.5 | +0.1 | +0.8 | +5.3 | +60.5 | −25.5 | $1.7B | Cost grew $177M, and 77% of it was more people |

The eight functions add up to the company's opening and closing cost, but their effects do not add up to the company's: each function's mix is measured inside the function.

**Technology, FY26 vs FY25:** KPIs "Total cost, FY26 · $2,016.3M · +$176.8M vs FY25 (+9.6%)" · "More people (volume) · +$135.5M · 77% of the change · headcount +1,301" · "Higher rates · +$60.5M" · "Mix of people · +$6.2M · level +5.3 · location +0.8 · workforce +0.1" · "Currency · −$25.5M · +$202.2M before exchange rates". Order card: Volume +135.5 / +134.0 / −1.5 · Workforce mix +0.1 / +0.0 / −0.1 · Location mix +0.8 / +1.0 / +0.2 · Level mix +5.3 / +5.6 / +0.3 · Rate +60.5 / +62.9 / **+2.4** · Currency −25.5 / −26.7 / −1.2; subtitle "A fixed order would move Rate by +$2.4M". Five-year table: FY22 +97.3 / −2.1 / +46.7 / −59.4 · FY23 +125.1 / −4.4 / +53.1 / +16.5 · FY24 +4.8 / −0.2 / +52.1 / −10.3 · FY25 +99.1 / +0.5 / +58.1 / +37.5 · FY26 +135.5 / +6.2 / +60.5 / −25.5.

**FY24 vs FY23, all of Arcadia (`p_Pair` 8), the year the question matters:** headcount 37,160 to 37,118, yet cost +$93.5M. KPIs "Fewer people (volume) · −$4.3M · headcount −42" · "Higher rates · +$118.7M" · "Mix of people · +$5.8M · level +12.1 · location −9.1 · workforce +2.8" · "Currency · −$26.7M · +$120.2M before exchange rates". Order card: the only year the fixed order understates Rate (bias −0.4).

### 13.3 Click tests (Presentation mode, then on Tableau Public)

| # | Do | Expect |
|---:|---|---|
| 1 | Nothing | The values of section 0 |
| 2 | Click every control, title, card and list row | Nothing stays highlighted |
| 3 | Open each popover in turn | One open at a time |
| 4 | Period > FY24 vs FY23 | Popover closes; capsule "FY24 vs FY23"; title "Cost grew $94M; the largest effect was higher rates (+$118.7M)"; KPI 2 "Fewer people (volume) · −$4.3M · headcount −42"; axis starts at $3.5B; the five-year table unchanged |
| 5 | Period > FY26 Q3 vs FY25 Q3 | KPI 1 "Total cost, FY26 Q3 · $4,517.4M · +$482.4M vs FY25 Q3 (+12.0%)"; Currency +$57.2M (teal); axis $3.8B |
| 6 | Organization > Technology | Capsule "Technology" (white) "19,157 people on Jun 30, 2026"; title "Cost grew $177M, and 77% of it was more people"; axis $1.7B; the order card and the five-year table follow |
| 7 | Organization > People | Axis starts at $170M; five-year table FY26 +18.6 / +2.6 / +8.1 / −1.9 |
| 8 | Hover each KPI card | The sentences of 6.1 |
| 9 | Hover the Rate bar, the Volume bar, the Closing bar | 7.4 |
| 10 | Info | The text of section 11; ✕ closes it |
| 11 | Reset | FY26 vs FY25, all of Arcadia, popovers closed |

---

## 14. Publishing

1. Reset; close every popover.
2. Hide all sheets; remove any stray legend or parameter control.
3. Save a lighter copy, `Workforce Cost Bridge (hide fields).twb`: Hide All Unused Fields; delete working sheets (`CHK Rows`). Keep the full original.
4. Extract on; refresh.
5. File > Save to Tableau Public As **Workforce Cost Bridge: Shapley Cost Decomposition | Arcadia Systems**. Description starting "Workforce cost analytics:"; tags workforce cost, Shapley decomposition, finance analytics, HR analytics, SQL. Show Viz on Profile on; Allow Workbook Download off; toolbar at the bottom.
6. On the web: the click tests of 13.3; the first load and a click timed; the screenshot (1400 × 850) for the repo.

**Assets to place before building:** the **Arcadia D4** shapes listed in section 10 (already in `My Tableau Repository/Shapes/Arcadia D4/` from Dashboards #4 and #5) and the images `arcadia_logo_horizontal_reverse.png`, `arcadia_rail_divider.png` and `d2_popover_line_wide.png` in the dashboard folder. No new shapes: the legends are text.

---

## 15. As built

Filled in after the build: where Tableau needed something different from this guide, and why. The numbers do not change.
