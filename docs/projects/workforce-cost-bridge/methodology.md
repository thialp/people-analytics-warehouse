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

**Order of the steps.** Sequential decompositions depend on the order the factors move. Here pay moves first, then FTE, fringe and FX. With monthly steps the cross-effects are small, and the order is fixed and documented so results never shift between runs. A symmetric (Shapley) split is planned for the Finance Growth Mix case study.

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
