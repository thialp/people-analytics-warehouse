# Methodology: Compensation Walk Drivers

This page explains how `mart_workforce_cost_bridge` turns two month-end snapshots into a reconciled set of drivers, with a worked example taken from the data.

## Definitions

| Term | Meaning |
|---|---|
| **Run-rate** | Annualized pay of everyone active on a month-end. It answers "what would a year cost at today's workforce and pay?" and is not monthly spend. |
| **Base** | Annual base salary (full-time rate) × FTE. |
| **Loaded** | Base × (1 + fringe rate). Fringe covers employer social contributions, mandatory pension and severance funding, statutory extra pay (such as a 13th salary) and, in the US, employer health and retirement benefits. It varies by country and calendar year and comes from public sources ([organization and pay model](../../company/organization_and_pay_model.md#fringe-rates)). |
| **Nominal** | Converted to USD at the ECB reference rate on that month-end (the latest published rate on or before it). |
| **Constant** | Converted to USD at one fixed rate set (the latest rates in the data, 2026-06-30) for every month, so currency movement is removed. |
| **Posting** | Converted at the rate of the day the pay record took effect ("booked"). Carried in the snapshot as a third basis; the walk below uses month-end revaluation. |
| **Active** | Hired on or before the month-end and not terminated before it. The termination date is the last day worked. |
| **Executive officers** | Excluded from both marts. |

## Classifying each worker each month

Each month compares the prior month-end (`0`) with the current month-end (`1`). Every worker active at either point falls into exactly one group:

| Group | Rule | Walk lines |
|---|---|---|
| Hire | active at `1` only | **Hires** at current value, in current department |
| Termination | active at `0` only | **Terminations** at prior value, in prior department |
| Transfer | active at both, department changed | **Transfers Out** of the old department and **Transfers In** to the new one, both at *prior* value, plus rate drivers in the new department |
| Stayer | active at both, same department | Rate drivers only |

Valuing transfers at prior pay on both sides makes them cancel exactly for the company, which is checked by `test_10_transfers_net_to_zero`.

## Decomposing a continuing worker's change

| Symbol | Meaning |
|---|---|
| `B` | annual base salary in local currency |
| `F` | FTE |
| `X` | USD per unit of local currency (actual or constant) |
| `R` | fringe rate |
| `X1p` | the worker's **current** currency at the **prior** month-end rate |

```
pay    = (B1·X1p − B0·X0) · F0 · (1 + R0)
FTE    =  B1·X1p · (F1 − F0) · (1 + R0)
fringe =  B1·X1p · F1 · (R1 − R0)
FX     =  B1 · F1 · (1 + R1) · (X1 − X1p)
```

**Why the terms always add up.** Each term moves one factor from its prior value to its current value while holding the factors already moved at their new values. Adding them cancels every intermediate product, leaving `B1·F1·X1·(1+R1) − B0·F0·X0·(1+R0)`, which is exactly the change in value.

**Why `X1p` instead of `X0`.** When someone moves from the UK to Germany, `X0` is a GBP rate and `X1` is an EUR rate. Comparing them would treat a change of currency as an FX movement. Using the new currency at last month's rate puts the re-levelling of pay into **International Mobility** and leaves only real currency movement in **FX Rate Changes**.

**Order of the steps.** Sequential decompositions depend on the order the factors move. Here pay moves first, then FTE, fringe and FX. With monthly steps the cross-effects are small, and the order is fixed and documented so results never shift between runs. A symmetric (Shapley) split of the year-over-year change is built in release 3: see [Total workforce cost and the growth mix](#release-3-total-workforce-cost-and-the-growth-mix).

**Labelling the pay term:**

1. Country changed → **International Mobility**. The fringe change for the move is included here too, because it is a consequence of the move, not a fringe-policy change.
2. Job level went up → **Promotions**.
3. Job level went down → **Demotions**.
4. Otherwise → **Tenure & Market Adjustments**: anniversary (tenure) raises, market adjustments and the pay re-levelling of a move between two offices in the same country.

The label is set per worker per month. When a promotion and a tenure raise land in the same month (a July 1 promotion and a July 4 hire anniversary, say), the whole pay change is labelled Promotions. A walk built on pay records rather than month-ends can split the two.

## Worked example

Worker `W100335`, Site Reliability (`D-105`), Toronto, promoted from level 2 to level 3 in the July 2025 cycle (effective 2025-07-01). The values come from `int_worker_month_end_snapshot`.

| | 2025-06-30 (`0`) | 2025-07-31 (`1`) |
|---|---:|---:|
| Job level | 2 | 3 |
| Base salary, CAD | 98,600 | 108,200 |
| FTE | 1.0 | 1.0 |
| USD per CAD (ECB) | 0.731266 | 0.722692 |
| Fringe rate (Canada, 2025) | 9.65% | 9.65% |
| **Loaded run-rate, USD nominal** | **79,060.75** | **85,741.15** |

Change to explain: **+6,680.40**

| Driver | Calculation | USD |
|---|---|---:|
| Promotions | (108,200 × 0.731266 − 98,600 × 0.731266) × 1.0 × 1.0965 | +7,697.60 |
| FTE Changes | 108,200 × 0.731266 × (1.0 − 1.0) × 1.0965 | 0.00 |
| Fringe Rate Changes | 108,200 × 0.731266 × 1.0 × (0.0965 − 0.0965) | 0.00 |
| FX Rate Changes | 108,200 × 1.0 × 1.0965 × (0.722692 − 0.731266) | −1,017.20 |
| **Total** | | **+6,680.40** ✓ |

The promotion added more than the run-rate moved: the Canadian dollar weakened in July 2025 and took back about 13% of it. In constant currency the same worker shows only the promotion effect (+7,394.44 at the 2026-06-30 rate); the FX line belongs to the currency, not to the promotion.

## What the walk does not do

- **It is not a payroll cost forecast.** Run-rate ignores when in the month someone joined or left. It is the right measure for "where will cost settle", not for "what did we spend".
- **Bonus is not in the run-rate.** The performance bonus is a one-time payment, held in `fact_bonus_payout`; equity and allowances are not modeled.
- **Rehires are treated as new workers.** The simulation does not rehire leavers.

## Release 3: total workforce cost and the growth mix

### Contingent workers in the bridge

Since release 3 the bridge explains **total workforce cost**: employees' loaded pay run-rate plus contingent workers' annualized bill run-rate, with a `worker_type` column (Employee, Contingent). A contingent worker's run-rate is `R × X`, where `R` is the bill rate annualized in billing currency (hourly rate × contracted hours × 52, or monthly rate × 12) and `X` the month-end rate; there is no fringe, so the same value appears in the base and loaded measures. The contingent drivers sit next to their employee counterparts:

| driver_order | Driver | Contingent workers | Employees |
|---:|---|---|---|
| 2 | Contingent Starts / Hires | New engagements, at the current run-rate | Hires, except conversions |
| 3 | Contingent Ends / Terminations | Ended engagements (completed, early, or lapsed while an approval was late), at the prior run-rate | Terminations |
| 4, 5 | Transfers In / Out | A change of department, at the prior run-rate | Same |
| 8 | Contingent Rate Changes | `R1·X1p − R0·X0`: renegotiated extensions and repriced renewals | Tenure & Market Adjustments |
| 10 | Conversions | The prior run-rate leaves Contingent | The new employee's loaded pay arrives (not in Hires) |
| 12 | FX Rate Changes | `R1·(X1 − X1p)` | Same |

The conversions line shows the cost of swapping a contractor for an employee. In FY26, 270 conversions brought $19.7M of employee loaded pay and removed $32.7M of contingent run-rate: about $13M a year less run-rate. Part of the gap is the basis: the contingent run-rate assumes every contracted hour is billed, while billed spend carries time off.

### The growth mix (`mart_workforce_cost_growth_mix`)

The monthly bridge says *what happened*: hires, exits, raises. Finance asks a different question across a year: **was cost growth about more people, a different mix of people, or higher rates?** That needs the change split into structural factors. Total workforce cost on a date, over segments `k` = worker type `t` × country `c` × level `l` (the grade for employees; Contractor, Consultant or BPO for contingent workers), is a product of six factors:

```
C = N · Σ_k  a_t · b_c|t · g_l|t,c · r_k · f_k
```

| Factor | Symbol | Meaning |
|---|---|---|
| Volume | `N` | People |
| Workforce mix | `a_t` | Share of employees and of contingent workers |
| Location mix | `b_c\|t` | Share of each country within the worker type |
| Level mix | `g_l\|t,c` | Share of each grade (or contingent type) within type and country |
| Rate | `r_k` | Cost per head at the constant rate set: pay and bill rates |
| Currency | `f_k` | Nominal ÷ constant: what exchange rates did to the reported cost |

**Why Shapley.** Moving the factors one at a time from last year's value to this year's explains the change exactly, but the answer depends on the order: the first factor moved is valued at old levels of the others, the last at new levels, and the interaction terms land on whichever goes later. The Shapley value removes that bias by giving each factor its average contribution over every possible order:

```
effect_i = Σ over S not containing i of  |S|! · (6 − |S| − 1)! / 6!  · [ v(S ∪ {i}) − v(S) ]
```

where `v(S)` is the cost with the factors in `S` at this year's value and the rest at last year's. Six factors give 64 subsets per pair and group, computed in one SQL query (a 64-row subsets table cross-joined to the segments). The effects add up to the change exactly (test 78). The sequential split, in the order listed above, is kept beside it (`sequential_effect_usd`), and `order_bias_usd` is the difference: how much the choice of order alone would have moved each factor.

**A segment present on one date only** has a share of zero on the other; its rate and currency factor are taken from the date where it exists, so its arrival or departure is a mix effect, never a rate effect.

**What it shows (Company, $M nominal):**

| FY | Opening | Volume | Workforce mix | Location mix | Level mix | Rate | Currency | Closing |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| FY22 | 3,137.0 | +220.3 | −1.4 | −1.6 | −5.4 | +98.0 | −138.9 | 3,308.1 |
| FY23 | 3,308.1 | +277.1 | −1.6 | −13.2 | +5.2 | +112.1 | +36.2 | 3,723.9 |
| FY24 | 3,723.9 | −4.3 | +2.8 | −9.1 | +12.1 | +118.7 | −26.7 | 3,817.4 |
| FY25 | 3,817.4 | +214.1 | −2.6 | −23.6 | +21.8 | +131.8 | +86.4 | 4,245.2 |
| FY26 | 4,245.2 | +307.1 | −4.8 | −9.3 | +22.4 | +139.8 | −52.2 | 4,648.1 |

- **FY24 is the year the question matters.** Headcount was flat (volume −$4M), yet cost rose $93M: rates (+$119M) and a mix that moved toward higher grades (+$12M) in the restructuring year.
- **Location mix is negative every year.** Growth leans toward lower-cost countries, for employees and contractors alike.
- **Currency swings both ways**, by up to $139M (FY22), larger than every mix effect. That is why constant currency matters.
- **The order bias is real but small:** up to $6.8M on a single factor (FY22 currency). The sequential method overstates raises in four of the five years.

The mart covers every fiscal quarter-end against the same quarter a year earlier (17 pairs), for the Company and each Function.
