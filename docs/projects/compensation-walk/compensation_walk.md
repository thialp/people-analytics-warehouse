# Compensation Walk: fields, rules and calculations

**Question it answers:** *between any two month-ends, why did compensation in this group move?*

| | |
|---|---|
| Tableau Custom SQL (SQL Server) | [`tableau/custom_sql_compensation_walk.sql`](../../../tableau/custom_sql_compensation_walk.sql) |
| Same result as a CSV (Tableau Public) | [`data/marts/mart_compensation_walk.csv`](../../../data/marts/mart_compensation_walk.csv), built by [`sql/03_marts/mart_compensation_walk.sql`](../../../sql/03_marts/mart_compensation_walk.sql) |
| Warehouse support table | `dw.WorkerPayLedger` / [`int_worker_pay_ledger`](../../../sql/02_intermediate/int_worker_pay_ledger.sql) |
| Grain | date pair × view × group × walk step × movement reason |
| Size (default grid) | 115,544 rows, 88 date pairs, 6 views, 107 groups |

The walk takes a group's compensation at the **From** month-end, explains every dollar of change, and lands on the **To** month-end exactly:

```
  Opening
+ Hires + Exits + Transfers In + Transfers Out                 who is in the group
+ Promotions + Demotions                                       career
+ Tenure Increases + Market Adjustments                        pay rate
+ Same-Country Transfer Adjustments + International Transfer Adjustments  location
+ Fringe Rate Changes + FX Translation                         statutory cost, currency
= Closing
```

It does this for headcount, FTE and four dollar measures (base or loaded cost, each at nominal or constant FX), both as **totals** and as **averages per FTE**. Every combination is computed in the data source, so the workbook only filters and sums. It needs no LOD expressions, no table calculations and no `AVG()`.

---

## 1. Why build it in the data source

A compensation walk sounds like a chart, but it is mostly a combinatorics problem:

* **Any two dates.** 61 month-ends give 1,830 possible From/To pairs. The walk for one pair cannot be built by adding up others, because someone hired in March and gone by May is in neither snapshot of a February-to-June walk.
* **Any group.** A transfer depends on the view. Moving office inside the same department is a transfer in the Office view and nothing at all in the Department view.
* **Averages don't add up.** The average-pay walk needs the group's opening average and closing FTE next to every line. In Tableau that means LOD expressions that have to agree with every filter on the sheet.
* **The driver of each dollar.** A promotion and an anniversary raise in the same month (817 worker-months in this data) are two different stories, and need to stay two numbers.

Done in Tableau, each of these is a calculated field that has to be right under every filter combination. Done once in SQL, they are columns that are right by construction, and they can be tested.

## 2. The three rules that make it close

### Rule 1: every line is priced on one side of the pair

| Step | Priced at | Assigned to the group at | Sign |
|---|---|---|---|
| Opening | opening value | From | + |
| Hires | closing value | To | + |
| Exits | opening value | From | − |
| Transfers Out | **opening** value | From | − |
| Transfers In | **opening** value | To | + |
| Pay drivers (Promotions … FX Translation) | amount of the change | To | ± |
| Closing | closing value | To | + |

A mover leaves the old group and enters the new one **at the same value**. When both groups are in scope, the two transfer lines cancel to the cent. Their pay change then shows up in the group they joined, under the driver that caused it.

**Worked example.** Maya earns $100,000 in Sales on 31 March. She transfers to Client Success in April with a $12,000 promotion, and gets a $3,000 tenure raise in May. On 30 June she earns $115,000.

| Group (Department view) | Line | Amount |
|---|---|---|
| Sales | Opening | +100,000 |
| Sales | Transfers Out | −100,000 |
| Client Success | Transfers In | +100,000 |
| Client Success | Promotions | +12,000 |
| Client Success | Tenure Increases | +3,000 |
| Client Success | Closing | +115,000 |

Sales closes at 100,000 − 100,000 = 0. Client Success closes at 100,000 + 12,000 + 3,000 = 115,000. At company level the transfer lines cancel, and Maya is +15,000 of pay drivers.

A common alternative prices *Transfers In* at the closing value. The walk still closes in headcount, but in dollars the promotion disappears into the transfer line. That design needs a residual or "comp change" plug to close at company level, and it cannot close inside a filtered group. Test 37 (and the mutation check in §9) proves this version cancels.

### Rule 2: drivers come from a running ledger, so any pair is a subtraction

`dw.WorkerPayLedger` keeps, for every worker and month-end, a **running total** of every pay event, FTE change, fringe change and FX movement since their first month-end. Between any two month-ends:

```
driver amount (From → To)  =  cum_driver(To) − cum_driver(From)
```

That is two equality joins on the clustered key `(MonthEndDate, WorkerID)`, instead of a range scan of the pay history for each of the 88 pairs. This is the classic prefix-sum technique, and it is what makes an "any date to any date" grid affordable.

### Rule 3: transfers are decided per view

Every pre-aggregated row is expanded into six views. A row is a transfer in a view only when the person's group in **that view** differs between From and To. This removes the old "within-view transfers: include or exclude?" toggle, and the reconciliation problems it caused.

## 3. How one month is split in the ledger

For a worker present at both ends of a month, the change in each measure is applied in a fixed order. Each step is valued at the state the previous step left behind, so the steps add up exactly:

| Order | Driver | Base amount | Loaded amount |
|---|---|---|---|
| 1 | Pay events | each pay record that took effect in the month, minus the record it replaced, at the **prior** month-end FX rate and the prior FTE | × (1 + prior fringe rate) |
| 2 | FTE Changes (retired in release 3) | `new pay × prior-month FX × (FTE₁ − FTE₀)`, always 0 now that every employee is 1.0 FTE; no step line is written | × (1 + prior fringe rate) |
| 3 | Fringe Rate Changes | 0 | `new pay × prior-month FX × FTE₁ × (fringe₁ − fringe₀)` |
| 4 | FX Translation | `new pay × FTE₁ × (FX₁ − FX at prior month-end)` | × (1 + new fringe rate) |

At constant FX the same formulas use the fixed rate, so FX Translation is zero by definition. Pay events are split by the pay record's action reason:

| Ledger driver | Pay record action reason |
|---|---|
| Promotions | Promotion (including promotions to fill a leadership role) |
| Demotions | Demotion |
| Tenure Increases | Tenure Increase (anniversary raise) |
| Market Adjustments | Market Adjustment (off-cycle raise to keep pay competitive) |
| Same-Country Transfer Adjustments | Relocation Adjustment: a move to another office in the same country with a different pay zone (named Relocation Adjustments before release 2). A move between two offices in the same pay zone changes no pay, so it is not on this line: in FY26, 600 people changed office within a country and 583 had a pay adjustment (23 moved inside one pay zone; a few moved twice) |
| International Transfer Adjustments | International Transfer (pay reset on a move to another country and currency) |

Test 34 checks the identity for every worker and every month-end: the ledger's drivers add up to the change in value on all four measures. The largest gap across 27 million worker × date-pair combinations is $2 × 10⁻¹⁰.

## 4. Views and groups

| `view_order` | `view_name` | `group_id` | `group_name` | `group_parent` | `group_leader` | Groups |
|---|---|---|---|---|---|---|
| 1 | Company | `ORG-000` | Arcadia Systems | (none) | CEO | 1 |
| 2 | Function | function org unit (`ORG-TEC` …) | Technology … | Arcadia Systems | function head | 8 |
| 3 | Sub-function | the department's parent org unit: a sub-function (`ORG-TEC-ENG` …) or, where there is none, the function (so the view still contains the whole company; six of the ten groups are functions with no sub-function) | Engineering, Sales, Product … | function | SVP or function head | 10 |
| 4 | Department | department (`D-101` …) | Core Platform Engineering … | function | head of department | 31 |
| 5 | Office | office (`LOC-001` …) | Austin HQ … | country | (none) | 35 |
| 6 | Country | ISO country code | United States … | region | (none) | 22 |

* Org groups are keyed by **org unit**, not by the leader as a person. When a leader is replaced, their whole organization does not show up as "transferred". `group_leader` is whoever leads the unit on the **To** month-end.
* Executive officers (the CEO and the eight function heads) are excluded from the population, as in the other cost reporting. They still appear as `group_leader`.

## 5. The date-pair grid

The grid holds only the four period types the dashboard offers (release 2; it used to also hold 99 quarter-end to quarter-end "Custom Range" pairs that no control offered).

**Lead-in rule:** a pair must end more than 12 months after the first month-end in the warehouse. History starts at Jun 30, 2021, so every pair ends in FY23 or later, and FY23 has all four year-over-year options (the trailing 12 months ending Sep 22, Dec 22 and Mar 23 start in FY22). The rule is computed from the calendar, so it moves by itself if history is extended again.

`pair_type` labels each pair. It is evaluated in this order, and the first match wins:

| `pair_type` | Rule | Pairs |
|---|---|---|
| Month over Month | consecutive month-ends | 48 |
| Quarter over Quarter | quarter-ends 3 months apart | 16 |
| Year over Year | quarter-ends 12 months apart (fiscal years and trailing 12 months) | 16 |
| Fiscal Year to Date | From is a fiscal year-end (30 June), To a later quarter-end in the same fiscal year (Dec or Mar; Sep is already Quarter over Quarter) | 8 |
| **Grid** | | **88** |

Every month-end to every later one would be 1,830 pairs (61 month-ends): replace the conditions at the `=== GRID ===` markers to build it, at about 20× the rows and run time.

## 6. Field reference

### Keys and labels

| Field | Type | Meaning |
|---|---|---|
| `from_month_end` | date | Opening month-end of the pair |
| `to_month_end` | date | Closing month-end of the pair |
| `report_start_date`, `report_as_of_date` | date | The data window, the same on every row: the first month-end a pair can start after the lead-in year (30 Jun 2022) and the last month-end in the warehouse (30 Jun 2026). For the "Data covers ..." note and the default period; both move by themselves when history grows |
| `from_fiscal_period`, `to_fiscal_period` | text | e.g. `FY26 P12` (fiscal year starts 1 July) |
| `from_fiscal_quarter`, `to_fiscal_quarter` | text | e.g. `FY26 Q4` |
| `months_between` | integer | Months from From to To |
| `pair_type` | text | See §5 |
| `view_order`, `view_name` | integer, text | See §4. **Always filter to one view.** Each view contains the whole company once. |
| `group_id`, `group_name`, `group_parent`, `group_leader` | text | See §4 |
| `step_order`, `step` | integer, text | Walk step, 1 (Opening) to 15 (Closing). Sort `step` by `step_order`. |
| `step_group` | text | Balance, Headcount, Career, Pay Rate, Location, Workforce Rate, Statutory, Currency |
| `movement_reason` | text | Hires: `New Hire`. Exits: `Voluntary` / `Involuntary`. Transfers in org views: `Transfer` / `Reorganization`. Transfers in Office and Country: `Relocation` / `International Transfer`. Other steps: empty. |

### Measures

Every measure is a signed sum: aggregate with `SUM()` only. In the walk, Exits and Transfers Out are negative.

| Field | Meaning |
|---|---|
| `worker_count` | People behind the line, unsigned. Opening and Closing: people in the group. Flows: people moving. Pay drivers: people with at least one event of that kind (e.g. 1,824 people promoted in FY26). Divide a pay driver's dollars by it for the average raise per person affected. Not additive across steps. |
| `headcount` | Signed headcount. Opening + Hires + Exits + Transfers = Closing. Zero on pay drivers. |
| `fte` | Signed FTE. Equals headcount: every employee is 1.0 FTE since release 3. |
| `base_usd_nominal` | Annualized base pay (annual base × FTE) at each month-end's actual FX rate |
| `base_usd_constant` | Same at the constant rate set (30 June 2026), so currency movements are removed |
| `loaded_usd_nominal` | Base × (1 + employer fringe rate), nominal FX |
| `loaded_usd_constant` | Base × (1 + employer fringe rate), constant FX |
| `avg_base_usd_nominal` … `avg_loaded_usd_constant` | **Average walk per FTE** (§7). Opening and Closing hold the group's average. Every other step holds its contribution to the change in average. |
| `pct_base_usd_nominal` … `pct_loaded_usd_constant` | **Percent walk.** Each line as a share of the group's opening total (Opening = 1.0). Steps other than Opening and Closing add up to the growth rate. |

## 7. The average walk

The total walk adds dollars. The average walk explains how **average compensation per FTE** moved, which is a different question. New hires add dollars, for example, but usually pull the average down.

With *O* and *N₀* the group's opening dollars and FTE, *C* and *N₁* the closing ones, and each step *k* carrying dollars *Dₖ* and FTE *nₖ*:

```
C = O + Σ Dₖ        N₁ = N₀ + Σ nₖ        Ā₀ = O / N₀        Ā₁ = C / N₁

Ā₁ − Ā₀  =  Σ ( Dₖ − nₖ × Ā₀ ) / N₁            (exact)
```

So each step's contribution to the change in average is `(Dₖ − nₖ × Ā₀) / N₁`:

* **Pay drivers** move no FTE, so they contribute their dollars spread over closing FTE.
* **Hires, exits and transfers** contribute only to the extent they are paid differently from the opening average. Hiring below the average lowers it; losing below-average earners raises it.

`avg_*` holds Ā₀ on Opening, Ā₁ on Closing and the contribution on every other step. Steps 2 to 14 add up to Ā₁ − Ā₀ (test 35). In Tableau, a waterfall of `SUM([avg_loaded_usd_constant])` over steps 1 to 14 lands exactly on the Closing bar.

**Group with no opening population** (an office opened inside the window): Ā₀ is reported as 0, so every step contributes its full dollars and the steps still add up to Ā₁.

### Example: FY26, Arcadia, loaded cost at constant FX (30 Jun 2025 → 30 Jun 2026)

| Step | People | Total $ | Avg per FTE |
|---|---:|---:|---:|
| Opening | 28,438 | 3,129,964,046 | **110,062.73** |
| Hires | 4,790 | +491,177,210 | −1,200.58 |
| Exits | 3,223 | −348,616,594 | +203.82 |
| Promotions | 1,824 | +21,649,192 | +721.52 |
| Demotions | 148 | −804,811 | −26.82 |
| Tenure Increases | 25,189 | +108,071,152 | +3,601.77 |
| Market Adjustments | 287 | +1,555,254 | +51.83 |
| Same-Country Transfer Adjustments | 583 | +193,228 | +6.44 |
| International Transfer Adjustments | 125 | −1,220,144 | −40.66 |
| Fringe Rate Changes | 11,312 | +8,514,217 | +283.76 |
| FX Translation | 17,038 | 0 (constant FX) | 0 |
| Closing | 30,005 | 3,410,482,750 | **113,663.81** |

Total loaded cost grew 9.0%, mostly because of headcount: hires minus exits added $143M. The **average** grew $3,601 (3.3%). Tenure increases added $3,602 per FTE, promotions $722 and statutory fringe increases $284. New hires, paid below the average, took $1,201 back; less than before release 2, because salary ranges now move every July 1, so a new hire starts on this year's range while the people already here climbed last year's.

(Release 3 values: every employee is 1.0 FTE, so FTE equals headcount and the FTE Changes step is gone. Release 2 opened FY26 at an average of 110,084.39 with 353 people changing hours; release 1 at 107,553.68.)

## 8. Reconciling to the other dashboards

| Compared with | Difference | Why |
|---|---|---|
| Headcount & FTE Walk (FY26 opening 28,445, closing 30,024) | 9 fewer people at each end | Executive officers are excluded here, as in all cost reporting |
| Headcount & FTE Walk, hires (5,168) and exits (3,589) | 402 fewer of each here | That walk chains twelve monthly walks. A date-pair walk compares two snapshots, so the 402 people hired **and** gone within FY26 are in neither. To reproduce the chained figures, add up the Month over Month pairs. |
| Workforce Cost Bridge (monthly, by department) | None in any total. Month over Month pairs match the bridge to 2 cents | Only the driver split differs: the bridge assigns a whole month's pay change to one driver by grade change, while this walk splits it by pay event, so a same-month promotion and anniversary raise are two lines |
| Cost snapshot control totals (2022-06-30 loaded nominal 2,577,787,184.81) | 20 cents | The snapshot adds group totals that were each already rounded to the cent. This walk adds people first and rounds once (…184.61). |

**Rounding.** Every amount is converted to an exact decimal at the worker level, so all sums are exact and repeatable. Each published line is then rounded to the cent. Opening plus the steps can therefore differ from Closing by a few cents in a group (at most half a cent per line). Headcount and FTE close exactly.

## 9. Validation

| Check | Where | What it proves |
|---|---|---|
| Test 34: pay ledger explains every change | `tests/` (DuckDB, CI) | Drivers add up to the change in value for every worker and month-end, on all four measures |
| Test 35: walk closes | `tests/` | Opening + steps = Closing for all 19,321 pair × view × group walks, totals and averages |
| Test 36: ties to snapshot | `tests/` | Opening and Closing equal the month-end snapshot for every department and office |
| Test 37: transfers net to zero | `tests/` | Within each view, Transfers In + Out = 0 in headcount, FTE and dollars, and every transfer has a reason |
| Test 38: views agree | `tests/` | All six views add up to the same company totals for every step, and constant FX has no FX line |
| Test 39: office moves tie to the walk | `tests/` | In the Office and Country views, people who joined a group equal the walk's Transfers In headcount and people who left equal Transfers Out, for every group and date pair ([office moves](office_moves.md)) |
| Test 40: office-move views agree | `tests/` | Company, Office and Country views count the same movers; moves inside one country are exactly the Domestic scope; no flow starts and ends at one office |
| Ledger rows and ledger identity | `sqlserver/05_validate.sql` | Same as test 34, on SQL Server |
| Custom SQL as Tableau runs it | `sqlserver/06_validate_compensation_walk.sql` | Runs the exact Tableau file (`:r` include), times it, and checks shape, closure and the FY26 example above |
| Office moves Custom SQL as Tableau runs it | `sqlserver/07_validate_office_moves.sql` | Runs both Custom SQL files, times them, checks shape and the FY26 example (345 movers), ties the moves to the walk's transfers, and checks every move group exists in the walk with the same name |
| SQL Server vs DuckDB | development check | The Custom SQL, transpiled to DuckDB, returns the same rows, labels and values as the CSV (zero differences across 10,455 rows). `dw.WorkerPayLedger` matches the DuckDB ledger on all 41 columns. |
| Against the Workforce Cost Bridge | development check | For every department and month, the Month over Month walk equals the bridge's Opening, Hires, Terminations, Transfers In and Out, total pay change and Closing, within 2 cents (1,460 department-months). Two independently written models agree. |
| Mutation checks | development check | Removing the FX line, or pricing Transfers In at closing value, fails test 35 in thousands of groups. Dropping tenure raises from the ledger fails test 34. |

## 10. Performance

| Stage | Rows (default grid) |
|---|---:|
| 1. Worker pairs | 4.4 million |
| 2. Pre-aggregated rows | about 0.5 million (aggregate early, about 9 workers per row) |
| 3. Expanded walk lines (six views × applicable steps) | about 12 million |
| 4–5. Published rows | 115,544 |

* DuckDB builds the mart in about 30 seconds on a laptop-class machine. The SQL Server timing is printed by `06_validate_compensation_walk.sql`.
* **Aggregate early, expand late.** Workers are collapsed to (date pair, departments, offices, reasons) *before* being multiplied into views and steps, which cuts the expansion about 9×.
* The ledger turns the date-range problem into two equality joins on the clustered primary key.
* Exact decimals cost about 2× CPU over floating point and buy byte-identical output on every run.

## 11. Using it in Tableau

* **Filters to set on every sheet:** one `view_name`, one `from_month_end`, one `to_month_end` (or a `pair_type` plus a To date). Then pick groups.
* **Total waterfall:** `step` on Columns sorted by `step_order`, and `SUM([loaded_usd_constant])` as a Gantt bar with a running sum. Closing is a total, so exclude it from the running sum, or draw it as its own bar.
* **Average waterfall:** same chart with `SUM([avg_loaded_usd_constant])`. It is valid for **one group at a time**, because the averages are computed per group. For several groups together, compute `SUM([loaded_usd_constant]) / SUM([fte])` on Opening and Closing instead.
* **Basis switch:** a parameter choosing among the four measures (base/loaded × nominal/constant) drives one calculated field. No other logic is needed.
* **Never use `AVG()`.** Every row is a group of people. Averages come from the `avg_*` fields or from `SUM($) / SUM(fte)`.

## 12. Limits and choices

* **Hired and gone inside the window:** not in a date-pair walk (see §8).
* **Inflation** is not a separate driver: the warehouse has no CPI data. Market Adjustments are the company's response to market pay movements. A CPI series could be added as a benchmark line, not as a walk step, because it is not a cause of any person's pay change.
* **Hires** are valued at their closing pay. Raises they received between joining and the To date are part of the Hires line, not of the pay drivers.
* **Movement reasons** use the latest department or office change before the To date. Someone who transferred and was later reorganized shows as Reorganization.
* **Bonus** is out of scope. The walk explains run-rate pay and its employer fringe; bonuses are one-time annual payouts with their own table.
