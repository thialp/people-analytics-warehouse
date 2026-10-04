# Methodology: Compensation Walk Drivers

This page explains how `mart_workforce_cost_bridge` turns two month-end snapshots into a reconciled set of drivers, with a worked example taken from the data.

## Definitions

| Term | Meaning |
|---|---|
| **Run-rate** | Annualized pay of everyone active on a month-end. It answers "what would a year cost at today's workforce and pay?" and is not monthly spend. |
| **Base** | Annual base salary (full-time rate) × FTE. |
| **Loaded** | Base × (1 + fringe rate). Fringe covers employer benefits, payroll taxes and social charges, which vary by country and fiscal year. |
| **Nominal** | Converted to USD at the actual rate on that month-end. |
| **Constant** | Converted to USD at one fixed rate set (FY26 Plan, taken from 2025-06-30) for every month, so currency movement is removed. |
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
2. Grade went up → **Promotions**. This includes any merit given in the same cycle.
3. Otherwise → **Merit & Adjustments** (merit cycle, market adjustments).

## Worked example

Worker `W108603`, Core Platform Engineering (`D-101`), Toronto, promoted from grade 3 to grade 4 in the March 2026 cycle. The values come from `int_worker_month_end_snapshot`.

| | 2026-02-28 (`0`) | 2026-03-31 (`1`) |
|---|---:|---:|
| Grade | 3 | 4 |
| Base salary, CAD | 121,400 | 135,800 |
| FTE | 1.0 | 1.0 |
| USD per CAD | 0.745395 | 0.767228 |
| Fringe rate (Canada, FY26) | 20.55% | 20.55% |
| **Loaded run-rate, USD nominal** | **109,086.84** | **125,600.52** |

Change to explain: **+16,513.67**

| Driver | Calculation | USD |
|---|---|---:|
| Promotions | (135,800 × 0.745395 − 121,400 × 0.745395) × 1.0 × 1.2055 | +12,939.46 |
| FTE Changes | 135,800 × 0.745395 × (1.0 − 1.0) × 1.2055 | 0.00 |
| Fringe Rate Changes | 135,800 × 0.745395 × 1.0 × (0.2055 − 0.2055) | 0.00 |
| FX Rate Changes | 135,800 × 1.0 × 1.2055 × (0.767228 − 0.745395) | +3,574.21 |
| **Total** | | **+16,513.67** ✓ |

In constant currency the same worker shows only the promotion effect, converted at the plan rate. The FX line belongs to the Canadian dollar, not to the promotion.

## What the walk does not do

- **It is not a payroll cost forecast.** Run-rate ignores when in the month someone joined or left. It is the right measure for "where will cost settle", not for "what did we spend".
- **Bonus, equity and allowances are out of scope.** Only base pay and fringe are modeled.
- **Rehires are treated as new workers.** The simulation does not rehire leavers.
