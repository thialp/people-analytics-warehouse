# Dashboard #6, Workforce Cost Bridge: build guide

This guide builds the sixth Arcadia dashboard from an empty Tableau Desktop, in the order you would build it by hand: the data source, the parameters, the calculations, each sheet, the dashboard, the popovers, the actions and the checks. Every formula pastes as it stands, and every expected value in section 13 is computed from the growth-mix mart the way the page computes it (`tableau/builder/d6/check_values.py`). A step either matches or shows exactly what differs.

Arcadia Systems is fictional; all data is synthetic.

| Step | What | State |
|---|---|---|
| 1 | Marts, Custom SQL, method, tests (test 78: the six effects add up to the change) | Done in release 3, unchanged through release 6 |
| 2 | This guide and its check values | Written 2026-10-29 |
| 3 | Three first-impression directions on a design canvas (A hero total, B headline ribbon, C answer card); **B chosen** 2026-10-29, C kept for #7 | Done |
| 4 | The build: `tableau/builder/d6` writes the workbook from this guide into the saved base workbook (2.2), then spot checks in Desktop | Build 1 checked; build 2 (template B) next |
| 5 | Publish, README, Figma values, profile, LinkedIn | After the build |

## Contents

0. What you are building
1. Decisions
2. The data source
3. Parameters
4. Core calculations (selection, labels, number text)
5. The selection's numbers
6. The headline and the factor ribbon
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

| Factor | On the page | Meaning |
|---|---|---|
| Volume | More people | More or fewer people |
| Workforce mix | Worker mix | The balance of employees and contingent workers |
| Location mix | Country mix | Which countries the people are in, within each worker type |
| Level mix | Grade mix | Which grades (or contingent types) the people are in, within type and country |
| Rate | Higher rates | What each person costs at constant exchange rates: pay and bill rates |
| Currency | Exchange rates | What exchange rates did to the reported cost |

**Template B, the headline ribbon.** The page's title *is* the answer, in one sentence with its numbers in plum. Under it a ribbon of the six factors, each with its value, a bar sized to the largest factor and one line of context. No boxes anywhere: the bridge, the order table and the five-year table are open panels under a 2 px plum rule, so the page reads like an editorial spread. It was chosen from three directions drawn with real numbers (A hero total, B headline ribbon, C answer card) because it is the boldest and gives each of the six factors its own KPI.

```
x 0      216 240                                                  948  988               1376 1400
y 0  ┌────────┬──────────────────────────────────────────────────────────────────────────┐
     │  RAIL  │ WORKFORCE COST BRIDGE (kicker)                                           │ 12–116
     │  navy  │ Workforce cost grew $402.9M to $4,648.1M, and 76% of it was more people  │
     │        │ Jun 30, 2025 to Jun 30, 2026 · +9.5% · all of Arcadia · 39,145 to …      │
 136 │        │ ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ │ plum rule
     │        │ More people │ Higher rates │ Grade mix │ Country mix │ Worker mix │ Exch. │ 140–240
     │        │ +$307.1M    │ +$139.8M     │ +$22.4M   │ −$9.3M      │ −$4.8M     │ −$52.2M│
     │        │ ▬▬▬▬▬▬▬▬    │ ▬▬▬▬         │ ▬         │ ▪           │ ▪          │ ▬▬    │
     │        │ 76% · +2,801│ 35% · pay …  │ toward …  │ toward …    │ toward …   │ +$455…│
 262 │        │ ━━ From $4,245.2M to $4,648.1M ━━━━━━━━━━━━━   ━━ A fixed order would … ━━│
     │        │ waterfall: Opening · six factors · Closing      Factor Shapley Fixed Bias │ 262–510
     │        │                                                 ━━ Rates rose every … ━━━│
     │        │                                                 FY × People Mix Rates Cur │ 520–812
 826 │        │ footnote                                                                 │
 850 └────────┴──────────────────────────────────────────────────────────────────────────┘
```

| Where | What it answers | Default view (FY26 vs FY25, all of Arcadia) |
|---|---|---|
| Headline | What happened, in one sentence? | "Workforce cost grew **$402.9M** to **$4,648.1M**, and **76%** of it was **more people**" |
| Subtitle | Which dates, which scope? | "**Jun 30, 2025** to **Jun 30, 2026** · +9.5% · all of Arcadia · 39,145 to 41,946 people · nominal USD" |
| Factor ribbon | How big is each factor? | More people **+$307.1M** (76% · +2,801 people) · Higher rates **+$139.8M** (35% · pay and bill rates) · Grade mix **+$22.4M** (toward higher grades) · Country mix **−$9.3M** (toward lower-cost countries) · Worker mix **−$4.8M** (toward cheaper worker types) · Exchange rates **−$52.2M** (+$455.2M without them) |
| Bridge | How does it add up? | "From **$4,245.2M** to **$4,648.1M**, one factor at a time": 4,245.2 · +307.1 · −4.8 · −9.3 · +22.4 · +139.8 · −52.2 · 4,648.1 |
| Order table | Why Shapley? | "A fixed order would overstate rates by **$5.5M**": Shapley, fixed order and bias per factor |
| Five fiscal years | Is this year different? | "Rates rose every year; currency swung both ways" · "In **FY24** headcount changed by only **−42**, yet cost rose **$93.5M**" |
| Rail | Which dates exactly? | Capsule "FY26 vs FY25 · year-end"; This **Jun 30, 2026** · Against **Jun 30, 2025** · Span 12 months, year-end to year-end |

**The palette.** Rail navy `#13233A` (the Arcadia rail, the same on every dashboard). Page `#F6F4F1` (warm paper). Ink `#1F2329`, slate `#5A6170`, axis text `#8C9BB0`. **Plum `#5B3A63`**: this dashboard's accent: the kicker, the rules, every number that adds cost and the headline's numbers. **Sand `#C2A878`** for bars that take cost away, **dark sand `#8A6A35`** for their text (legible on the paper). Opening and closing bars `#9AA5B4`. Light rules and dividers `#E0DCD6`, grid `#E7E3DD`, ribbon bar track `#ECE8E2`, small bias bars `#D5DBE4`. No red and green pair, no blue and orange pair.

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
| C12 | **Hovers are sentences, color-coded**: adds in plum, takes away in dark sand, dates, levels and counts in navy. Tooltip command buttons off on every sheet; every clickable sheet has a deselect (`zzTrue` → `zzFalse`) | Rich tooltips carry the detail; nothing stays highlighted after a click |
| C14 | **Template B, the headline ribbon** (chosen 2026-10-29 from three directions drawn with real numbers; C, the answer card, is kept for #7): the title states the answer with its numbers in plum, six factor cells replace the five KPI cards, every panel is open (no white cards) | The first impression must answer the question from a screenshot; the six factors are the page's KPIs; open panels give #6 its own look beside #5's cards |
| C15 | **Plum and sand**, on warm paper `#F6F4F1` | Professional but different from #1 to #5 (navy and teal); plum adds, sand takes away, never red with green |
| C16 | **Dates spelled out** (the How-To #2 lesson): the capsule says year-end or quarter-end, the rail lists This, Against and Span, and the subtitle names both dates in bold | A visitor must know exactly which two days are compared without opening the picker |
| C17 | **Numbers in sentences are colored and bold**: plum for what adds cost, dark sand for what takes it away, navy for dates and counts; in titles, subtitles and every hover | The eye finds the numbers first |
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

// Pair Is Year
{ MIN(IF [In Pair] THEN (IF RIGHT([fiscal_quarter_label], 2) = "Q4" THEN 1 ELSE 0 END) END) } = 1

// Pair Kind
IF [Pair Is Year] THEN " · year-end" ELSE " · quarter-end" END

// Period Field Text
[Pair Label] + [Pair Kind]

// Span Line 1
"12 months"

// Span Line 2
IF [Pair Is Year] THEN "year-end to year-end" ELSE "quarter-end to quarter-end" END
```

Expected with `p_Pair` 0: Pair Label "FY26 vs FY25", Period Field Text "FY26 vs FY25 · year-end", Span Text "Jun 30, 2025 to Jun 30, 2026", Span Line 1 and 2 "12 months" / "year-end to year-end". With 1: "FY26 Q3 vs FY25 Q3 · quarter-end", "Mar 31, 2025 to Mar 31, 2026". With 8: "FY24 vs FY23". A pair ending on the fiscal year's last quarter reads as the fiscal year; any other reads with its quarter.

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
| `S Change Abs Txt` | Money (no sign) | `[S Change]` |
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

### 5.1 The largest factor (for the headline)

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

## 6. The headline and the factor ribbon

### 6.1 The headline

```
// Head Verb
IF [S Change] >= 0 THEN "Workforce cost grew " ELSE "Workforce cost fell " END

// Head Share Form
[Driver Share] >= 0.5 AND [Driver Share] <= 1

// Head Mid
IF [Head Share Form] THEN ", and " ELSE "; the largest effect was " END

// Head Pct
IF [Head Share Form] THEN STR(INT(ROUND([Driver Share] * 100, 0))) + "%" ELSE "" END

// Head Of
IF [Head Share Form] THEN " of it was " ELSE "" END

// Head Driver
[Driver Words] + (IF [Head Share Form] THEN "" ELSE " (" + [Driver Txt] + ")" END)
```

The share form is used when one factor explains half to all of the change; otherwise the headline names the largest effect and its size, so it never reads "127% of it".

Sheet **Page Title**: Text, one mark; left, top; Detail `zzTrue`, `zzFalse`; tooltip off. Three lines:

| Line | Runs |
|---|---|
| 1 | `WORKFORCE COST BRIDGE` Tableau Semibold 10 plum `#5B3A63` |
| 2 | `<Head Verb>` Tableau Bold 20 ink `#1F2329` · `<S Change Abs Txt>` Bold 20 plum `#5B3A63` · ` to ` Bold 20 ink · `<S Closing Txt>` Bold 20 plum · `<Head Mid>` Bold 20 ink · `<Head Pct>` Bold 20 plum · `<Head Of>` Bold 20 ink · `<Head Driver>` Bold 20 plum (20, not 22: the longest headline, "…; the largest effect was higher rates (+$118.7M)", then stays on one line) |
| 3 | `<ATTR(From Date Text)>` Tableau Semibold 11 navy `#13233A` · ` to ` Book 11 slate `#5A6170` · `<ATTR(To Date Text)>` Semibold 11 navy · ` · <S Change Pct Str> · <ATTR(Scope Words)> · <S HC Open Str> to <S HC Close Str> people · nominal USD` Book 11 slate |

Expected: "Workforce cost grew **$402.9M** to **$4,648.1M**, and **76%** of it was **more people**" / "**Jun 30, 2025** to **Jun 30, 2026** · +9.5% · all of Arcadia · 39,145 to 41,946 people · nominal USD". FY24 vs FY23: "Workforce cost grew $93.5M to $3,817.4M; the largest effect was higher rates (+$118.7M)".

### 6.2 The factor ribbon

Six cells, one per factor, in the order a reader weighs them: people, rates, grades, countries, worker mix, exchange rates. Three sheets share the same six columns, stacked: **Ribbon Top** (name and value), **Ribbon Bars** (the bar), **Ribbon Note** (one line of context).

```
// Ribbon Order
CASE [factor_order] WHEN 1 THEN 1 WHEN 5 THEN 2 WHEN 4 THEN 3 WHEN 3 THEN 4 WHEN 2 THEN 5 WHEN 6 THEN 6 END

// Rib Name
CASE MIN([factor_order])
WHEN 1 THEN (IF SUM([Effect M]) >= 0 THEN "More people" ELSE "Fewer people" END)
WHEN 5 THEN (IF SUM([Effect M]) >= 0 THEN "Higher rates" ELSE "Lower rates" END)
WHEN 4 THEN "Grade mix" WHEN 3 THEN "Country mix" WHEN 2 THEN "Worker mix" ELSE "Exchange rates" END

// Rib Value
<Sign on SUM([Effect M])> + "$" + <M1 on SUM([Effect M])> + "M"

// Rib Share
SUM([Effect M]) / MIN([Sel Change LOD])

// Rib Share Ok
[Rib Share] >= 0 AND [Rib Share] <= 1

// Rib HC Change
MIN([closing_headcount]) - MIN([opening_headcount])

// Rib HC Txt
(IF [Rib HC Change] >= 0 THEN "+" ELSE "−" END) + <Comma on [Rib HC Change]> + " people"

// Rib Without FX
MIN([Sel Change LOD]) - SUM([Effect M])

// Rib Note
CASE MIN([factor_order])
WHEN 1 THEN (IF [Rib Share Ok] THEN STR(INT(ROUND([Rib Share] * 100, 0))) + "% · " ELSE "" END) + [Rib HC Txt]
WHEN 5 THEN (IF [Rib Share Ok] THEN STR(INT(ROUND([Rib Share] * 100, 0))) + "% · " ELSE "" END) + "pay and bill rates"
WHEN 4 THEN (IF SUM([Effect M]) >= 0 THEN "toward higher grades" ELSE "toward lower grades" END)
WHEN 3 THEN (IF SUM([Effect M]) >= 0 THEN "toward higher-cost countries" ELSE "toward lower-cost countries" END)
WHEN 2 THEN (IF SUM([Effect M]) >= 0 THEN "toward costlier worker types" ELSE "toward cheaper worker types" END)
ELSE <Sign on [Rib Without FX]> + "$" + <M1 on [Rib Without FX]> + "M without them" END

// Rib Bar Kind
IF ROUND(SUM([Effect M]), 1) >= 0 THEN "adds" ELSE "takes away" END

// Rib Max
{ MAX(IF [In Selection] AND [Is Factor] THEN ABS([Effect M]) END) }

// Rib Bar Size
ABS(SUM([Effect M])) / MIN([Rib Max])

// Rib Zero
MIN(0.0)

// Rib Val Adds
IF [Cell Kind] = "adds" THEN [Rib Value] END

// Rib Val Takes
IF [Cell Kind] = "takes away" THEN [Rib Value] END

// Rib Share Txt
IF [Rib Share Ok] THEN STR(INT(ROUND([Rib Share] * 100, 0))) + "% of the change" ELSE "" END

// Rib Tip Extra
CASE MIN([factor_order])
WHEN 1 THEN "Headcount " + <Comma on MIN([opening_headcount])> + " to " + <Comma on MIN([closing_headcount])> + ", with mix, rates and currency at their average over every order of the steps."
WHEN 5 THEN "Raises and bill-rate changes at constant exchange rates; promotions to a higher grade count under grade mix."
WHEN 6 THEN "Without the Currency effect the change would be " + <Sign on [Rib Without FX]> + "$" + <M1 on [Rib Without FX]> + "M."
ELSE "" END
```

`Cell Kind` (section 9) colors every factor number on the page: adds plum, takes away dark sand. `Rib Max` is the largest factor in the selection, so the largest bar always fills its cell.

All three sheets: Filters `In Selection` = True and `Is Factor` = True; Columns `Ribbon Order` (discrete, header hidden); Fit Entire View; shading None; every line None; Detail `zzTrue`, `zzFalse`.

- **Ribbon Top**: Marks **Text**; Color `Cell Kind` (adds plum `#5B3A63`, takes away dark sand `#8A6A35`); left, top. Line 1 `  <Rib Name>` Tableau Book 10 slate `#5A6170`; line 2 `  <Rib Value>` Tableau Bold 24, no font color (the mark color carries plum or sand). The two leading spaces keep the text off the cell divider.
- **Ribbon Bars**: Columns `Ribbon Order` then `Rib Zero` (continuous, axis Fixed **−0.07 to 1.07**, hidden: the margin insets each bar and its track from the cell edges, so the six tracks read as six bars, not one strip). Marks **Gantt Bar** (size slider at its second step: a 5 px bar), Size `Rib Bar Size`, Color `Rib Bar Kind` (the same test as `Cell Kind`, its own field so its colors can differ: adds plum `#5B3A63`, takes away light sand `#C2A878`), size slider so the bar is 6 px tall. Analytics: **Reference Band**, per pane, constant 0 to 1, fill `#ECE8E2` (the track), no line.
- **Ribbon Note**: Marks **Text**, `  <Rib Note>` Tableau Book 9 slate `#5A6170`, left, top.
- **Tooltip** (Ribbon Top and Ribbon Bars, command buttons off): line 1 `<Rib Name>: ` Tableau Semibold 11 navy `#13233A`, `<Rib Val Adds>` Tableau Bold 11 plum `#5B3A63`, `<Rib Val Takes>` Tableau Bold 11 dark sand `#8A6A35`; line 2 `<Rib Share Txt>` Tableau Semibold 10 navy; line 3 `<ATTR(factor_meaning)>` Tableau Book 10 ink `#1F2329`; line 4 `<Rib Tip Extra>` Tableau Book 9 slate `#5A6170`.

Lines between the cells are five 1 px blanks `#E0DCD6` on the dashboard (12.2), at the cell edges, from the plum rule to the bottom rule.

Expected, default: More people **+$307.1M** · 76% · +2,801 people | Higher rates **+$139.8M** · 35% · pay and bill rates | Grade mix **+$22.4M** · toward higher grades | Country mix **−$9.3M** · toward lower-cost countries | Worker mix **−$4.8M** · toward cheaper worker types | Exchange rates **−$52.2M** · +$455.2M without them. Bars: 100%, 46%, 7%, 3%, 2%, 17% of a cell. Hover on More people: "More people: **+$307.1M**" / "**76% of the change**" / "More or fewer people" / "Headcount 39,145 to 41,946, with mix, rates and currency at their average over every order of the steps."

---

## 7. The bridge

### 7.1 The title

The headline (6.1) already states the answer, so the bridge's title says what the chart shows.

Sheet **Bridge Title**: Text, one mark; left, top; Detail `zzTrue`, `zzFalse`; tooltip off. Line 1: `From ` Tableau Bold 14 navy `#13233A` · `<S Opening Txt>` Bold 14 slate `#5A6170` · ` to ` Bold 14 navy · `<S Closing Txt>` Bold 14 plum `#5B3A63` · `, one factor at a time` Bold 14 navy. Line 2: `Each factor's average effect over every order of the six steps, $M; the axis starts at ` Tableau Book 10 slate `#5A6170` · `<ATTR(Floor Text)>` Semibold 10 navy · ` so the factors are visible` Book 10 slate.

Expected: "From **$4,245.2M** to **$4,648.1M**, one factor at a time" / "… the axis starts at **$4.0B** so the factors are visible".

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
(IF SUM([Step M]) < 0 THEN RUNNING_SUM(SUM([Step M])) - SUM([Step M]) ELSE RUNNING_SUM(SUM([Step M])) END)
+ 0.035 * (WINDOW_MAX(RUNNING_SUM(SUM([Step M]))) - MIN([Axis Floor]))

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

How it closes: the running sum of Step M at row k is the cost after k factors have moved; the closing row adds 0, so its running sum is the closing cost. Each factor's Gantt bar hangs from that point by minus its effect, so it spans the previous level to the new one. The opening and closing bars hang down to the axis floor. `Label Y` is the top of each bar plus 3.5% of the chart's height, so every label sits clear above its bar (build 1 put the label's middle on the bar's top edge). Bar Kind and Label Kind are the same test twice, so the bars and the labels get separate color legends.

Sheet **Bridge**:
1. Filter `In Selection` = True.
2. Columns `factor_order` (discrete, header hidden), then `Factor Head` (header at the bottom, Tableau Semibold 9 ink `#1F2329`), then `Factor Sub` (header at the bottom, Tableau Book 8 slate `#5A6170`). Headers wrap; column width even.
3. Rows `Bar Top`, then `Label Y`; Dual Axis; Synchronize Axis. Every table calculation: **Compute Using Specific Dimensions `factor_order`, `Factor Head` and `Factor Sub`**, sorted by `factor_order`. (`Factor Head` and `Factor Sub` are on Columns only to label the bars; left out of the addressing, they would partition every column and restart the running sum.)
4. Left axis: no title, Automatic, **Include zero off**, labels Tableau Book 8 axis gray `#8C9BB0`, format Number Custom `$#,##0"M"`; right axis hidden.
5. Marks `Bar Top`: **Gantt Bar**; Size `Bar Size`; Color `Bar Kind`: level `#9AA5B4`, adds plum `#5B3A63`, takes away sand `#C2A878`; opacity 100%, no border; size slider at about 60% (the bars a little wider than their gaps).
6. Marks `Label Y`: **Text**; Text `Bar Label`; Color `Label Kind`: level navy `#13233A`, adds plum `#5B3A63`, takes away dark sand `#8A6A35`; Tableau Bold 10; alignment center, middle.
7. Analytics: **Reference Line**, Entire Table, on the left axis, value `MIN(Axis Floor)`: solid 1 px `#D5DBE4`; label custom `Axis starts at <Floor Text>` (insert the field), Tableau Book 8 slate `#5A6170`, at the left, below the line. The reference line also holds the automatic axis down at the floor.
8. Grid lines: rows solid 1 px `#E7E3DD`; columns none. Zero line, axis rulers, borders and row/column dividers None. Shading None (the panel is open on the page's paper).
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
- Line 1: `<Tip Head>` Tableau Semibold 11 navy `#13233A`, a space, then `<Tip Value Level>` Tableau Bold 11 navy, `<Tip Value Adds>` Tableau Bold 11 plum `#5B3A63`, `<Tip Value Takes>` Tableau Bold 11 dark sand `#8A6A35` (only one is ever not empty).
- Line 2: `<ATTR(factor_meaning)>` Tableau Book 10 ink `#1F2329` (a dimension only on the tooltip must be ATTR, or the pill turns red and the sheet blanks).
- Line 3: `<Tip Share>` Tableau Semibold 10 navy `#13233A`.
- Line 4: `<Tip Order>` Tableau Book 9 slate `#5A6170`.

Expected, default, the Rate bar: "Rate, Jun 30, 2025 to Jun 30, 2026: **+$139.8M**" / "What each person costs at constant exchange rates: pay and bill rates" / "35% of the change" / "One fixed order of the steps would give +$145.2M, a bias of +$5.5M." The Volume bar: "… 76% of the change · headcount 39,145 to 41,946". The Closing bar: "Closing, Jun 30, 2026: $4,648.1M" / "Total workforce cost at the later date" / "41,946 people".

### 7.5 The note under the chart

A dashboard text object under the chart (static): `Plum adds cost` Tableau Semibold 9 plum `#5B3A63` · `, ` · `sand takes it away` Semibold 9 dark sand `#8A6A35` · `; the six effects add up to the change exactly.` Tableau Book 9 slate `#5A6170`.

---

## 8. The order of the steps

Shapley against one fixed order (the sequential split: Volume, Workforce mix, Location mix, Level mix, Rate, Currency). A table, one row per factor: the two values side by side and the bias (fixed order minus Shapley) as a small diverging bar on its own scale. Build 1's paired bars put a $5M difference beside $300M bars, where it could not be seen.

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

// Bias Driver Effect
CASE [Bias Driver] WHEN "Volume" THEN [S Volume] WHEN "Workforce mix" THEN [S Workforce]
WHEN "Location mix" THEN [S Location] WHEN "Level mix" THEN [S Level]
WHEN "Rate" THEN [S Rate] ELSE [S Currency] END

// Bias Word
CASE [Bias Driver] WHEN "Volume" THEN "volume" WHEN "Workforce mix" THEN "the worker mix" WHEN "Location mix" THEN "the country mix"
WHEN "Level mix" THEN "the grade mix" WHEN "Rate" THEN "rates" ELSE "currency" END

// Bias Lead
"A fixed order would " + (IF [Bias Driver Value] * [Bias Driver Effect] >= 0 THEN "overstate " ELSE "understate " END) + [Bias Word] + " by "

// Bias Amount
"$" + <M1 on [Bias Driver Value]> + "M"

// Bias Text
<Sign on SUM([Bias M])> + <M1 on SUM([Bias M])>

// Bias Kind
IF ABS(SUM([Bias M])) < 1 THEN "small" ELSEIF SUM([Bias M]) >= 0 THEN "adds" ELSE "takes away" END

// Bias Label Kind
IF ABS(SUM([Bias M])) < 1 THEN "small" ELSEIF SUM([Bias M]) >= 0 THEN "adds" ELSE "takes away" END

// Bias Shap Txt
<Sign on SUM([Effect M])> + <M1 on SUM([Effect M])>

// Bias Seq Txt
<Sign on SUM([Seq M])> + <M1 on SUM([Seq M])>

// Bias Axis
{ MAX(IF [In Selection] AND [Is Factor] THEN ABS([Bias M]) END) } * 1.15

// Bias Axis Neg
-[Bias Axis]
```

"Overstate" when the fixed order moves the factor further in its own direction (a bias with the same sign as the effect), "understate" otherwise. `Bias Axis` keeps the diverging bars symmetric and leaves room for their labels.

Sheet **Bias Title**: Text, one mark; left, top; Detail `zzTrue`, `zzFalse`; tooltip off; 80 px tall, so a title that wraps to two lines keeps its subtitle. Line 1: `<Bias Lead>` Tableau Bold 14 navy `#13233A` · `<Bias Amount>` Bold 14 plum `#5B3A63`. Line 2: `Shapley vs one fixed order (volume first, currency last), $M` Tableau Book 10 slate `#5A6170`.

Four sheets side by side make the table; each: Filters `In Selection` = True and `Is Factor` = True; Rows `factor_order` (discrete, header hidden); Fit Entire View; shading None; row dividers solid 1 px `#E7E3DD`; Detail `zzTrue`, `zzFalse`; tooltip off unless stated. Same height and top, so the six rows line up.

| Sheet | Width | Mark | Content |
|---|---:|---|---|
| **Bias Names** | 104 | Text | `<Factor Head>` Tableau Book 10 ink `#1F2329`, left |
| **Bias Shapley** | 64 | Text | `<Bias Shap Txt>` Tableau Semibold 10 navy `#13233A`, right |
| **Bias Seq** | 72 | Text | `<Bias Seq Txt>` Tableau Book 10 slate `#5A6170`, right |
| **Bias Num** | 48 | Text | `<Bias Text>` Tableau Semibold 10, right; Color `Bias Kind` labels: adds plum `#5B3A63`, takes away dark sand `#8A6A35`, small axis gray `#8C9BB0` (the field **Bias Label Kind**, the same test as `Bias Kind`) |
| **Bias Bars** | 96 | Bar | Columns `SUM(Bias M)`, axis hidden; Color `Bias Kind`: adds plum `#5B3A63`, takes away sand `#C2A878`, small `#D5DBE4`; size 50%; no label (the number sits in its own column, so a short bar never hides it); zero line solid 1 px `#D5DBE4`; two reference lines at `MIN(Bias Axis)` and `MIN(Bias Axis Neg)` with no line (they only hold the axis symmetric). Tooltip: `<Factor Head>` Semibold 10 navy / `Shapley ` Book 10 ink, `<Bias Shap Txt>` Semibold 10 navy, ` · one fixed order ` Book 10 ink, `<Bias Seq Txt>` Semibold 10 slate, ` · bias ` Book 10 ink, `<Bias Text>` Bold 10 plum |

Column headers are four dashboard text objects above the table: `Factor` (left), `Shapley`, `Fixed order`, `Bias` (right aligned over the number column), Tableau Book 9 axis gray `#8C9BB0`.

Expected, default: title "A fixed order would overstate rates by **$5.5M**".

| Factor | Shapley | Fixed order | Bias |
|---|---:|---:|---:|
| Volume | +307.1 | +303.8 | −3.3 (sand) |
| Workforce mix | −4.8 | −5.3 | −0.5 (small) |
| Location mix | −9.3 | −9.1 | +0.1 (small) |
| Level mix | +22.4 | +23.5 | +1.1 (plum) |
| Rate | +139.8 | +145.2 | **+5.5** (plum) |
| Currency | −52.2 | −55.2 | −2.9 (sand) |

---

## 9. Five fiscal years

The selected group's five fiscal years, each against the year before: the pairs at offsets 0, 4, 8, 12 and 16.

```
// Table Column
CASE [factor_order] WHEN 1 THEN "People" WHEN 2 THEN "Mix" WHEN 3 THEN "Mix" WHEN 4 THEN "Mix"
WHEN 5 THEN "Rates" WHEN 6 THEN "Currency" END

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

// Row HC Change
[closing_headcount] - [opening_headcount]

// Y HC Min
{ MIN(IF [In Group] AND [Is Year Pair] THEN ABS([Row HC Change]) END) }

// Is Quiet Year
[In Group] AND [Is Year Pair] AND ABS([Row HC Change]) = [Y HC Min]

// Quiet Flag
IF [Is Quiet Year] THEN 1 ELSE 0 END

// Quiet FY
{ MIN(IF [Is Quiet Year] THEN [Row To Label] END) }

// Quiet HC
{ MIN(IF [Is Quiet Year] THEN [Row HC Change] END) }

// Quiet Change
{ SUM(IF [Is Quiet Year] AND [factor_order] = 7 THEN [Effect M] END) - SUM(IF [Is Quiet Year] AND [factor_order] = 0 THEN [Effect M] END) }

// Quiet HC Txt
(IF [Quiet HC] >= 0 THEN "+" ELSE "−" END) + <Comma on [Quiet HC]>

// Quiet Verb
IF [Quiet Change] >= 0 THEN ", yet cost rose " ELSE ", and cost fell " END

// Quiet Change Txt
"$" + <M1 on [Quiet Change]> + "M"

// Cell Text Hi
IF MIN([Quiet Flag]) = 1 THEN [Cell Text] END

// Cell Text Lo
IF MIN([Quiet Flag]) = 0 THEN [Cell Text] END

// Year Row Label
[Row To Label]

// FY End Words
{ MIN(IF [Pair Offset] = 0 THEN LEFT(DATENAME('month', [to_month_end]), 3) + " " + STR(DAY([to_month_end])) END) }

// Year Note
"Mix = worker + country + grade · each " + [FY End Words] + " vs the one before · bold: quietest"
```

The quiet year is the one whose headcount changed least: the year where volume explains least and the other factors carry the change. Its row is bold in the table and named in the subtitle.

Sheet **Year Title**: Text, one mark; left, top; Detail `zzTrue`, `zzFalse`; tooltip off. Line 1: `<ATTR(Year Title)>` Tableau Bold 14 navy `#13233A`. Line 2: `In ` Tableau Book 10 slate `#5A6170` · `<ATTR(Quiet FY)>` Semibold 10 navy · ` headcount changed by only ` Book 10 slate · `<ATTR(Quiet HC Txt)>` Semibold 10 navy · `<ATTR(Quiet Verb)>` Book 10 slate · `<ATTR(Quiet Change Txt)>` Bold 10 plum `#5B3A63`.

Sheet **Year Table**:
1. Filter `Year Row` = True.
2. Rows `Year Row Label` (sorted by `fiscal_year` ascending; header at the left, Tableau Semibold 10 navy `#13233A`, header title "FY").
3. Columns `Table Col Order` (header hidden), `Table Column` (header at the top, Tableau Semibold 9 slate `#5A6170`).
4. Marks **Text**, `<Cell Text Hi>` Tableau Bold 10 then `<Cell Text Lo>` Tableau Book 10 (only one is ever not empty); Color `Cell Kind`: adds plum `#5B3A63`, takes away dark sand `#8A6A35`; alignment right, middle.
5. No shading (open on the paper); column titles Tableau Semibold 9 slate `#5A6170`; row dividers solid 1 px `#E7E3DD`; no column dividers.
6. Tooltip: `<Year Row Label> · <Table Column>: <Cell Text>` Tableau Book 10 ink `#1F2329`. Both fields are already in the view, so nothing goes on the Tooltip shelf (a Rows field is never repeated there).

Sheet **Year Note**: Text, `<MIN(Year Note)>` Tableau Book 9 slate `#5A6170`; Detail `zzTrue`, `zzFalse`; tooltip off.

Expected, all of Arcadia (title "Rates rose every year; currency swung both ways"; subtitle "In **FY24** headcount changed by only **−42**, yet cost rose **$93.5M**"; FY24 bold):

| FY | People | Mix | Rates | Currency |
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

The dates list under the Period capsule (the How-To #2 lesson: a visitor reads exactly which two days are compared). Two columns, one row per item, so keys and values always line up: three static text keys at x 12, 60 wide, `This`, `Against`, `Span` (Tableau Book 9 `#8FA0B8`), and beside each, at x 76, its own one-mark sheet:

| Sheet | Label | h |
|---|---|---:|
| **Date This** | `<ATTR(To Date Text)>` Tableau Semibold 9 white `#FFFFFF` | 18 |
| **Date Against** | `<ATTR(From Date Text)>` Tableau Semibold 9 white | 18 |
| **Date Span** | `<ATTR(Span Line 1)>` / `<ATTR(Span Line 2)>` Tableau Book 9 `#B9C3D1` (two lines: the span never truncates) | 32 |

Each: Detail `zzTrue`, `zzFalse`; tooltip off.

| Sheet | Shape | Label | Detail | Tooltip |
|---|---|---|---|---|
| **Period Field** | `d4_field_capsule.png` (always white: the period is always a choice) | `<Period Field Text>` Tableau Semibold 9 navy `#13233A`, left | `Toggle Period Panel`, `Close Panel`, `zzTrue`, `zzFalse` | "Choose the two dates to compare" |
| **Org Field** | `Org Capsule Shape` | `<Org Text Light>` Tableau Semibold 9 navy `#13233A` + `<Org Text Dark>` Tableau Medium 9 `#E4E9F0`, left | `Toggle Org Panel`, `Close Panel`, `zzTrue`, `zzFalse` | "Choose all of Arcadia or one function" |
| **Org Sub** | none (Text) | `<Org Sub Text>` Tableau Book 8 `#8A97A8` | `zzTrue`, `zzFalse` | off |
| **Reset** | `d4_reset.png` | none | `Zero Pair`, `Default Group`, `Close Panel`, `zzTrue`, `zzFalse` | "Reset to default view" |
| **Info Button** | `Info Shape` | none | `Toggle Info`, `Close Panel`, `zzTrue`, `zzFalse` | "How the bridge works" |
| **Rail As Of** | none (Text) | `<Rail Line 1>` Tableau Semibold 9 `#E4E9F0` / `USD at month-end ECB rates` Tableau Book 9 `#B9C3D1` / `Employees and contingent workers` Tableau Book 9 `#B9C3D1` | `zzTrue`, `zzFalse` | off |

Capsules are drawn at shape size 12 (the whole pill shows), Reset at 10. The rail's first heading reads **COMPARE**.

Expected: default Period "FY26 vs FY25 · year-end"; This Jun 30, 2026 · Against Jun 30, 2025 · Span 12 months / year-end to year-end; Organization "All of Arcadia" (dark capsule) / "41,946 people on Jun 30, 2026"; Technology "Technology" (white capsule) / "19,157 people on Jun 30, 2026"; rail foot "Report date Jun 30, 2026".

---

## 11. The popovers

Each hangs from the rail's right edge (x 216): a navy `#13233A` vertical container, padding 0, no border, shown by its open flag (Layout > Control visibility using value). Inside: header 44 px (title Tableau Bold 12 white `#FFFFFF`, 12 px from the left; ✕ at the right), the line image `d2_popover_line_wide.png` 9 px, the body, a footer 30 px (Tableau Book 9 `#8FA0B8`, one line, 12 px from the left). The ✕ sheets (**Period Close**, **Org Close**, **Info Close**): Text `✕` Tableau Book 12 `#B8C0CC`, Detail `zzFalse`, `zzTrue`, `Close Panel`, tooltip "Close".

The list sheets: one row per option, Marks **Shape** with the tick files `d4_tick_on.png` (12) / `d4_tick_off.png` (11) from **Arcadia D4** (the files carry the state, so no color on the shape), the tick on a hidden axis at the left, **every tick at shape size 1.8 in every list** (a fixed size, never sized by the view, so ticks do not grow when a list is short; build 1's size 8 drew stacked, oversized ticks), rows 22 px, fit width; row banding none; tooltip off.

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

// Group Key
STR([view_order]) + " " + [group_name]

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
| **Org Popover** | 216, 228, 360 × 300 | Title "Organization". **Group List**: Filter `Group Option Row` = True (9 rows). Rows `Group Key` (header hidden; the company first, then the functions A to Z; one row field, because build 1's two row fields drew the rows on top of each other). Shape `Group Shape`; label `  <Group Option Name>` Tableau Book 10 `#E4E9F0` then `   <Group Option People>` Tableau Book 9 `#8FA0B8`. Detail `group_name`, `Close Panel`, `zzTrue`, `zzFalse`. Footer "Each function is its own bridge: its effects add up to its own change." |
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

New dashboard **Dashboard**, **Fixed 1400 × 850**, title off, shading **`#F6F4F1`** (warm paper). Every item floating; show title off; padding 0 unless stated. No cards: every panel sits on the paper under a rule.

### 12.2 Floating items, back to front

| # | Item | x | y | w | h | Format |
|---:|---|---:|---:|---:|---:|---|
| 1 | `Page Title` | 240 | 12 | 1136 | 116 | |
| 2 | Blank, plum `#5B3A63` | 240 | 136 | 1136 | 2 | the ribbon's top rule |
| 3 | `Ribbon Top` | 240 | 146 | 1136 | 70 | |
| 4 | `Ribbon Bars` | 240 | 222 | 1136 | 10 | |
| 5 | `Ribbon Note` | 240 | 236 | 1136 | 22 | |
| 6 | Blank `#E0DCD6` | 240 | 266 | 1136 | 1 | the ribbon's bottom rule |
| 7–11 | Blanks `#E0DCD6`, the cell dividers | 429, 619, 808, 997, 1187 | 148 | 1 | 112 | |
| 12 | Blank, plum | 240 | 280 | 708 | 2 | |
| 13 | `Bridge Title` | 240 | 290 | 708 | 54 | |
| 14 | `Bridge` | 240 | 348 | 708 | 438 | |
| 15 | Text: the bridge's note (7.5) | 240 | 792 | 708 | 18 | |
| 16 | Blank, plum | 988 | 280 | 388 | 2 | |
| 17 | `Bias Title` | 988 | 290 | 388 | 78 | |
| 18 | Four text objects: the order table's headers | 988, 1092, 1156, 1228 | 372 | 104, 64, 72, 48 | 16 | Tableau Book 9 `#8C9BB0`; Factor left, the others right |
| 19 | `Bias Names`, `Bias Shapley`, `Bias Seq`, `Bias Num`, `Bias Bars` | 988, 1092, 1156, 1228, 1280 | 390 | 104, 64, 72, 48, 96 | 144 | |
| 20 | Blank, plum | 988 | 548 | 388 | 2 | |
| 21 | `Year Title` | 988 | 558 | 388 | 74 | |
| 22 | `Year Table` | 988 | 634 | 388 | 170 | |
| 23 | `Year Note` | 988 | 806 | 388 | 16 | |
| 24 | Footnote text | 240 | 828 | 1136 | 16 | "Arcadia Systems is fictional; all data is synthetic. Executive officers excluded. Effects are Shapley values: each factor's average effect over every order of the six steps, so they add up to the change." Tableau Book 9 slate `#5A6170` |
| 25 | Blank, navy `#13233A` (the rail) | 0 | 0 | 216 | 850 | |
| 26 | Rail items (12.3) | | | | | |
| 27 | `Period Popover` | 216 | 152 | 360 | 470 | visibility `p_PeriodOpen` |
| 28 | `Org Popover` | 216 | 318 | 360 | 300 | visibility `p_OrgOpen` |
| 29 | `Info Popover` | 216 | 24 | 591 | 420 | visibility `p_InfoOpen` |

The ribbon's cells are 1136 ÷ 6 = 189.3 px; the dividers sit on their edges.

### 12.3 The rail (floating over the navy blank)

Room to breathe, as on How-To #2: 12 px side margins, a clear gap between each block, larger rail text (capsules 11 pt, the date list 10 pt), the date list in two columns.

| Item | x | y | w | h |
|---|---:|---:|---:|---:|
| Logo `arcadia_logo_horizontal_reverse.png` | 12 | 24 | 156 | 40 |
| `Info Button` | 178 | 30 | 28 | 28 |
| Text COMPARE (Tableau Semibold 9 `#B8C4D6`) | 12 | 96 | 192 | 16 |
| `Period Field` (label Tableau Semibold 11) | 12 | 116 | 192 | 34 |
| Key `This` · `Date This` | 12 · 66 | 164 | 52 · 146 | 20 |
| Key `Against` · `Date Against` | 12 · 66 | 184 | 52 · 146 | 20 |
| Key `Span` · `Date Span` | 12 · 66 | 204 | 52 · 146 | 34 |
| Text ORGANIZATION | 12 | 262 | 192 | 16 |
| `Org Field` (label Tableau Semibold or Medium 11) | 12 | 282 | 192 | 34 |
| `Org Sub` | 12 | 322 | 192 | 18 |
| Image `arcadia_rail_divider.png` | 12 | 356 | 192 | 24 |
| `Reset` | 12 | 392 | 192 | 32 |
| `Rail As Of` | 12 | 752 | 192 | 70 |

Keys Tableau Book 10 `#8FA0B8`; `Date This` and `Date Against` Tableau Semibold 10 white; `Date Span` Tableau Book 9 `#B9C3D1`. `Rail As Of`: `<Rail Line 1>` Semibold 9 `#E4E9F0` / `USD at month-end ECB rates` / `Employees and contingent workers` Book 9 `#B9C3D1` (each line fits 192 px, so nothing wraps). The popovers open just under their capsules: Period at y 152, Organization at y 318.

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

**Deselect:** one Filter action per clickable sheet: source and target the same sheet, run on Select, clearing **Show all values**, `zzTrue` → `zzFalse`. Every sheet except `Bridge`, `Bias Bars` and `Year Table` (a selection there is useful).

---

## 13. Checks and click tests

### 13.1 Ties at every state

- The bridge closes: Opening + the six labels = Closing (to 0.1 from rounding the labels).
- The six ribbon values add up to the headline's change.
- The exchange-rates cell's "without them" = the headline's change − its value.
- The FY rows of the five-year table equal the bridge at `p_Pair` 0, 4, 8, 12, 16 (Mix = the three mix bars).
- The order table's Shapley column equals the bridge's factor labels.

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

| p_Pair | Headline | Order-card title | People note | Exchange-rates note |
|---:|---|---|---|---|
| 0 | Workforce cost grew $402.9M to $4,648.1M, and 76% of it was more people | A fixed order would overstate rates by $5.5M | More people · 76% · +2,801 people | +$455.2M without them |
| 1 | Workforce cost grew $482.4M to $4,517.4M, and 57% of it was more people | A fixed order would understate volume by $6.6M | More people · 57% · +2,561 people | +$425.2M without them |
| 2 | Workforce cost grew $539.9M to $4,448.1M; the largest effect was more people (+$252.0M) | A fixed order would understate volume by $8.6M | More people · 47% · +2,356 people | +$399.2M without them |
| 3 | Workforce cost grew $396.1M to $4,342.0M, and 60% of it was more people | A fixed order would understate volume by $4.5M | More people · 60% · +2,194 people | +$379.0M without them |
| 4 | Workforce cost grew $427.8M to $4,245.2M, and 50% of it was more people | A fixed order would understate volume by $5.6M | More people · 50% · +2,027 people | +$341.4M without them |
| 5 | Workforce cost grew $250.0M to $4,034.9M, and 62% of it was more people | A fixed order would overstate rates by $3.1M | More people · 62% · +1,480 people | +$276.3M without them |
| 6 | Workforce cost grew $110.8M to $3,908.2M; the largest effect was higher rates (+$123.8M) | A fixed order would overstate currency by $3.6M | More people · 93% · +997 people | +$214.8M without them |
| 7 | Workforce cost grew $237.6M to $3,946.0M, and 53% of it was higher rates | A fixed order would overstate currency by $1.7M | More people · 21% · +476 people | +$169.3M without them |
| 8 | Workforce cost grew $93.5M to $3,817.4M; the largest effect was higher rates (+$118.7M) | A fixed order would overstate the grade mix by $1.2M | Fewer people · −42 people | +$120.2M without them |
| 9 | Workforce cost grew $187.6M to $3,785.0M, and 60% of it was higher rates | A fixed order would understate volume by $1.1M | More people · 37% · +680 people | +$180.3M without them |
| 10 | Workforce cost grew $304.5M to $3,797.4M; the largest effect was more people (+$137.9M) | A fixed order would understate volume by $3.1M | More people · 45% · +1,368 people | +$246.1M without them |
| 11 | Workforce cost grew $383.2M to $3,708.4M, and 53% of it was more people | A fixed order would understate volume by $5.2M | More people · 53% · +2,051 people | +$300.3M without them |
| 12 | Workforce cost grew $415.8M to $3,723.9M, and 67% of it was more people | A fixed order would understate volume by $5.5M | More people · 67% · +2,820 people | +$379.7M without them |
| 13 | Workforce cost grew $298.2M to $3,597.3M, and 88% of it was more people | A fixed order would overstate rates by $5.2M | More people · 88% · +2,657 people | +$366.0M without them |
| 14 | Workforce cost grew $261.7M to $3,493.0M, and 94% of it was more people | A fixed order would overstate rates by $6.0M | More people · 94% · +2,498 people | +$353.4M without them |
| 15 | Workforce cost grew $156.3M to $3,325.2M; the largest effect was more people (+$229.3M) | A fixed order would overstate currency by $10.0M | More people · +2,371 people | +$334.2M without them |
| 16 | Workforce cost grew $171.1M to $3,308.1M; the largest effect was more people (+$220.3M) | A fixed order would overstate currency by $6.8M | More people · +2,269 people | +$310.0M without them |

**Each group, FY26 vs FY25 (`p_Pair` 0):**

| Group | Total cost | Change | Volume | Workforce mix | Location mix | Level mix | Rate | Currency | Axis floor | Headline |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|
| All of Arcadia | $4,648.1M | +$402.9M | +307.1 | −4.8 | −9.3 | +22.4 | +139.8 | −52.2 | $4.0B | Workforce cost grew $402.9M to $4,648.1M, and 76% of it was more people |
| Commercial | $988.4M | +$64.3M | +44.8 | +0.0 | −5.3 | +5.2 | +29.7 | −10.2 | $870M | Workforce cost grew $64.3M to $988.4M, and 70% of it was more people |
| Finance | $235.9M | +$24.9M | +18.9 | +1.9 | −1.8 | +1.7 | +6.3 | −2.1 | $200M | Workforce cost grew $24.9M to $235.9M, and 76% of it was more people |
| Legal & Compliance | $148.8M | +$16.8M | +11.4 | +0.4 | +1.3 | +0.9 | +4.0 | −1.3 | $120M | Workforce cost grew $16.8M to $148.8M, and 68% of it was more people |
| Marketing | $187.4M | +$16.5M | +13.6 | +0.8 | −3.0 | +0.5 | +6.4 | −1.7 | $160M | Workforce cost grew $16.5M to $187.4M, and 82% of it was more people |
| Operations | $512.2M | +$44.7M | +37.5 | −3.1 | −0.7 | +2.1 | +15.3 | −6.4 | $440M | Workforce cost grew $44.7M to $512.2M, and 84% of it was more people |
| People | $212.3M | +$27.4M | +18.6 | +0.6 | +0.5 | +1.5 | +8.1 | −1.9 | $170M | Workforce cost grew $27.4M to $212.3M, and 68% of it was more people |
| Product | $346.8M | +$31.7M | +26.7 | −0.7 | −2.0 | +0.6 | +10.3 | −3.1 | $290M | Workforce cost grew $31.7M to $346.8M, and 84% of it was more people |
| Technology | $2,016.3M | +$176.8M | +135.5 | +0.1 | +0.8 | +5.3 | +60.5 | −25.5 | $1.7B | Workforce cost grew $176.8M to $2,016.3M, and 77% of it was more people |

The eight functions add up to the company's opening and closing cost, but their effects do not add up to the company's: each function's mix is measured inside the function.

**The factor ribbon, all of Arcadia, FY26 vs FY25:**

Headline: Workforce cost grew $402.9M to $4,648.1M, and 76% of it was more people  
Subtitle: Jun 30, 2025 to Jun 30, 2026 · +9.5% · all of Arcadia · 39,145 to 41,946 people · nominal USD

| Cell | Name | Value | Note |
|---:|---|---:|---|
| 1 | More people | +$307.1M | 76% · +2,801 people |
| 2 | Higher rates | +$139.8M | 35% · pay and bill rates |
| 3 | Grade mix | +$22.4M | toward higher grades |
| 4 | Country mix | −$9.3M | toward lower-cost countries |
| 5 | Worker mix | −$4.8M | toward cheaper worker types |
| 6 | Exchange rates | −$52.2M | +$455.2M without them |

**Technology, p_Pair 0:** Workforce cost grew $176.8M to $2,016.3M, and 77% of it was more people · More people +$135.5M (77% · +1,301 people) · Higher rates +$60.5M (34% · pay and bill rates) · Grade mix +$5.3M (toward higher grades) · Country mix +$0.8M (toward higher-cost countries) · Worker mix +$0.1M (toward costlier worker types) · Exchange rates −$25.5M (+$202.2M without them)

**Arcadia Systems, p_Pair 8:** Workforce cost grew $93.5M to $3,817.4M; the largest effect was higher rates (+$118.7M) · Fewer people −$4.3M (−42 people) · Higher rates +$118.7M (pay and bill rates) · Grade mix +$12.1M (toward higher grades) · Country mix −$9.1M (toward lower-cost countries) · Worker mix +$2.8M (toward costlier worker types) · Exchange rates −$26.7M (+$120.2M without them)

**Technology, FY26 vs FY25:** order table Volume +135.5 / +134.0 / −1.5 · Workforce mix +0.1 / +0.0 / −0.1 · Location mix +0.8 / +1.0 / +0.2 · Level mix +5.3 / +5.6 / +0.3 · Rate +60.5 / +62.9 / **+2.4** · Currency −25.5 / −26.7 / −1.2; title "A fixed order would overstate rates by $2.4M". Five-year table FY22 +97.3 / −2.1 / +46.7 / −59.4 · FY23 +125.1 / −4.4 / +53.1 / +16.5 · FY24 +4.8 / −0.2 / +52.1 / −10.3 · FY25 +99.1 / +0.5 / +58.1 / +37.5 · FY26 +135.5 / +6.2 / +60.5 / −25.5; subtitle "In FY24 headcount changed by only +50, yet cost rose $46.4M".

### 13.3 Click tests (Presentation mode, then on Tableau Public)

| # | Do | Expect |
|---:|---|---|
| 1 | Nothing | The values of section 0 |
| 2 | Click every control, title, card and list row | Nothing stays highlighted |
| 3 | Open each popover in turn | One open at a time |
| 4 | Period > FY24 vs FY23 | Popover closes; capsule "FY24 vs FY23 · year-end"; This Jun 30, 2024, Against Jun 30, 2023; headline "Workforce cost grew $93.5M to $3,817.4M; the largest effect was higher rates (+$118.7M)"; ribbon "Fewer people −$4.3M · −42 people"; axis starts at $3.5B; the five-year table unchanged |
| 5 | Period > FY26 Q3 vs FY25 Q3 | Capsule "FY26 Q3 vs FY25 Q3 · quarter-end"; Span "12 months, quarter-end to quarter-end"; headline "… grew $482.4M to $4,517.4M, and 57% of it was more people"; Exchange rates +$57.2M in plum; axis $3.8B |
| 6 | Organization > Technology | Capsule "Technology" (white) "19,157 people on Jun 30, 2026"; headline "Workforce cost grew $176.8M to $2,016.3M, and 77% of it was more people"; axis $1.7B; the order table and the five-year table follow |
| 7 | Organization > People | Axis starts at $170M; five-year table FY26 +18.6 / +2.6 / +8.1 / −1.9; subtitle "In FY24 headcount changed by only +51, yet cost rose $10.4M" |
| 8 | Hover each ribbon cell | The tooltips of 6.2, numbers in plum or sand |
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

The workbook is written by `tableau/builder/d6/` from this guide's code blocks into the saved base workbook (2.2):

```
D4_TWB=".../4 Contingent Workforce Reconciliation/Arcadia CW Reconciliation.twb" \
python3 tableau/builder/d6/build_d6.py "Workforce Cost Bridge base.twb" "Workforce Cost Bridge (build N).twb"
```

**Build 1 (2026-10-29), the first layout (five KPI cards, white cards).** Every number matched section 13 in Desktop, the waterfall closed and every period and function pick changed every card. What it taught, carried into this guide:

| Seen in build 1 | Changed |
|---|---|
| The first impression did not tell the story: the title was a page name, the KPI cards were five equal boxes | Template B (C14): the headline is the answer, the six factors are the KPIs |
| Text sheets showed ".." (page subtitle, KPI line 3, rail foot) | Every text sheet is sized for its lines plus padding (12.2) |
| Value labels sat across the bar tops | `Label Y` lifts each label by 3.5% of the chart's height |
| The Shapley and fixed-order bars could not show a $5M difference beside $300M | The order card is a table with a diverging bias bar (8) |
| Popover ticks drew oversized and stacked | Ticks at shape size 1.8 |
| Organization list rows overlapped | One row field, `Group Key` |
| The period was only "FY26 vs FY25" | Dates spelled out (C16) |

---

**Build 2 (2026-10-29), template B.** Every value matched section 13 (default, FY24 vs FY23, Technology); the ribbon hovers, the quiet-year bold row and the order table worked. Sizing, carried into this guide:

| Seen in build 2 | Changed |
|---|---|
| The ribbon's six tracks ran edge to edge as one strip and the text touched the dividers: crowded beside the prototype | Bars inset (axis −0.07 to 1.07), 5 px bars, two leading spaces on the ribbon text, a taller ribbon (12.2) |
| The rail was tight; the keys `This`, `Against`, `Span` sat in one text box and drifted from their dates; the span truncated | A two-column date list, one sheet per row, the span on two lines; more space between rail blocks (12.3) |
| A two-line headline (FY24 vs FY23) pushed the subtitle out | Headline at Bold 20 |
| The order table's title wrapped and lost its subtitle; the five-year title lost its subtitle; the note truncated | Taller title sheets (80 and 76), a shorter subtitle and note |
| Bias bars too short for their labels | `Bias Axis` at 1.45× the largest bias |
| "toward the less costly worker type" truncated | "toward cheaper worker types" |

**Build 3 (2026-10-29).** Right, but the changes were too small to see; Span still truncated, the bias labels still sat on their bars. Build 4 takes the sizes from the prototype instead of nudging: rail capsules 11 pt and the date list 10 pt with a wider value column and Span as "12 months" / "year-end to year-end"; ribbon values Bold 24 in a taller band; the bias number in its own column beside a label-free bar; shorter notes ("toward cheaper worker types", the year note, the rail foot).
