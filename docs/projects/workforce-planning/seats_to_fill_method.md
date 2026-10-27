# Seats to Fill: the forecast method

How Dashboard #5 forecasts the PIDs Arcadia will need to fill in the forward year, and why the numbers can be trusted. Code: [`forecast/`](../../../forecast/). Plan and decisions: [seats_to_fill_plan.md](seats_to_fill_plan.md). Arcadia Systems is fictional and all data is synthetic.

**In one sentence:** we learned how quickly each kind of PID gets filled and how often PIDs open, simulated the forward year 100 times, and checked the same method against eight quarters that already happened.

**Scope:** employee PIDs. Contingent workers appear only as their budget line by function. Executive officers (D-901) are excluded.

## 1. What is forecast

For each department × office and each quarter of the forward year (FY27 at the Jun 30, 2026 report date):

| Measure | Meaning |
|---|---|
| Vacant at the start | Employee requisitions approved and still waiting (902 on Jun 30, 2026) |
| Opened | New PIDs approved in the quarter: backfills, net-new, immediate refills |
| Filled | PIDs filled in the quarter, immediate refills included |
| Vacant at the end | Still waiting at the quarter-end |

Every simulated future adds up: vacant at the end = vacant at the start + opened − filled (test f01).

The plan figures below are allocated to offices; see section 3.

**FY27, all of Arcadia, median and 80% range of the draws:**

| | P10 | Median | P90 |
|---|---:|---:|---:|
| PIDs to fill in the year (waiting on Jul 1 + opened) | 7,006 | 7,612 | 8,371 |
| PIDs filled | 6,301 | 6,838 | 7,543 |
| Vacant on Jun 30, 2027 | 696 | 772 | 892 |

Planned fills (FY27 Budget, net-new plus backfills) total 7,709, so the median forecast reaches 89% of plan, in the 75–100% band. FY26 reached 88% (6,849 of 7,793).

## 2. The three parts

### 2.1 Time to fill: a discrete-time survival model (`fill_model.py`)

For a requisition that has waited *k* ten-day periods, the model gives the chance it is filled in the next one. It is a logistic regression on requisition-periods. The 10-day period puts 30, 60 and 90 days on a period boundary.

The terms of the regression:

| Term | Levels | What the fit shows |
|---|---|---|
| Waiting-time baseline | 12 bins | The shape of the wait: almost no fills in the first ten days, a peak around day 60 |
| Level band | L1–L2, L3–L4, L5–L6, L7+ | Senior PIDs are slower: L5–L6 log-odds −1.2 against L1–L2 |
| Function | 8 | Technology −0.29 and Legal & Compliance −0.23 (slower); Operations +0.37 (faster) |
| Country | 22 | Small effects |
| Net-new or backfill | 2 | About the same |
| Graduate season | L1–L2 only, country × calendar month | Each country's season: the US in Aug–Sep, Brazil in Nov–Dec, India in Jul, Japan in Mar–Apr. The fit reads the period's middle day, so a season shows a month before the fills land |

**Why a survival model.** Requisitions still open on the forecast date have not finished waiting. Averaging only the filled ones makes recent quarters look fast; dropping the open ones makes them look slow. Here an open requisition counts as "not filled yet" for every period it was observed and then leaves the data (it is censored).

Requisitions filled the day they were approved (successions, teams handed over) never stand vacant. They are counted as immediate refills and kept out of the model.

**The fit.** Newton–Raphson (iteratively reweighted least squares) on binomial counts, with a ridge penalty of 2 on every term except the baseline, written in numpy. At the report date it uses 27,201 requisitions and 143,307 requisition-periods. Coefficients are rounded to six decimals before simulating, so runs reproduce byte for byte.

### 2.2 Demand (`simulate.py`, `Demand`)

| Source | Expected new PIDs per department × office × quarter |
|---|---|
| Backfills | Employees × the backfill rate per head of the function and country over the last eight quarters × the fiscal quarter's seasonal index |
| Net-new | The forward budget's net-new for the cost center × net-new PIDs opened per planned net-new fill. That ratio is the median over every known quarter, so the FY24 restructuring year does not drag it down; each function keeps its share of what it opened against its share of the plan. The cost center is split across its offices by their recent net-new share |
| Immediate refills | Their pace over the last four quarters |

Level bands for new PIDs are drawn from each cell's recent mix.

### 2.3 Simulation (`simulate.py`, `run`)

Each of 100 draws is one possible future:

1. **Demand level.** The draw takes its own demand level for backfills and net-new, as a lognormal shock. Its size comes from how much past quarters varied beyond chance: the median absolute deviation of the net-new ratios, and the spread of backfill openings around the rate.
2. **Hiring speed.** The draw takes its own hiring speed, a shift in the model's log-odds. Its size is the quarter-to-quarter spread of the 60-day fill share.
3. **New PIDs.** It draws Poisson counts of new PIDs, with random approval days inside the quarter.
4. **Filling.** It follows every waiting PID period by period: each period is a random draw against its fill chance.

Tableau sums the draws over any selection and then takes P10, P50 and P90 across them. Percentiles do not add up across a selection; draws do.

## 3. What counts as the plan

Each fiscal year's Budget, as approved before the year. Budgets are set by cost center (department × country). The page allocates them to offices by each office's share of the cost center's employees at the quarter's start, and says so in its info panel.

## 4. The backtest (`run_forecast.py`, `backtest`)

At each of the eight quarter-ends before the report date (Jun 30, 2024 to Mar 31, 2026), the whole method is refit on what was known that day. That means requisitions approved and fills known by then (test f02), and the latest plan version dated by then. It then forecasts the quarters that version covered and is compared with what happened.

**Next quarter, all of Arcadia:**

| Target quarter | P10 | Median | P90 | Actual | In range | Error |
|---|---:|---:|---:|---:|---|---:|
| FY25 Q1 | 1,276 | 1,436 | 1,568 | 1,475 | yes | −2.7% |
| FY25 Q2 | 1,288 | 1,435 | 1,598 | 1,466 | yes | −2.2% |
| FY25 Q3 | 1,271 | 1,404 | 1,559 | 1,466 | yes | −4.2% |
| FY25 Q4 | 1,374 | 1,492 | 1,595 | 1,445 | yes | +3.3% |
| FY26 Q1 | 1,527 | 1,651 | 1,801 | 1,678 | yes | −1.6% |
| FY26 Q2 | 1,501 | 1,663 | 1,769 | 1,782 | no | −6.7% |
| FY26 Q3 | 1,509 | 1,571 | 1,645 | 1,672 | no | −6.1% |
| FY26 Q4 | 1,584 | 1,656 | 1,736 | 1,717 | yes | −3.6% |

The 80% range holds the actual in 6 of 8 quarters; a calibrated 80% range should hold about 6.4. The median is off by 3.8% on average.

The two misses are both low, in FY26. Two and more quarters ahead, the method runs about 6% low on fills and about 10% low on vacancy, because backfills rose faster than their eight-quarter rate in FY26. More internal moves to fill growth leave more PIDs to backfill. The page shows this honestly instead of correcting it after the fact. Linking backfills to net-new growth (vacancy chains) is the natural next improvement.

Test f04 checks every run:
- the range holds the actual in at least half of the next-quarter forecasts;
- the range stays under 40% of the median;
- the median error stays under 10%.

## 5. Assumptions and limits

- **The near future looks like the recent past:** fill speeds from five years of history, backfill rates from eight quarters.
- **Headcount does not grow inside the year for the backfill rate.** The budget's growth enters through net-new.
- **No cancellations are simulated.** Only 12 requisitions were ever cancelled.
- **The synthetic history's budgets were drawn around what happened** (that is how the generator writes them). The backtest's net-new side is therefore a little favourable. The forward budget is a true projection.
- **A company-wide event**, such as a hiring freeze or a restructuring, is outside the range. It would be a scenario, not a forecast.

## 6. Tables (`forecast` schema in the warehouse, and `data/marts/`)

| Table | Grain | What it holds |
|---|---|---|
| `mart_pid_fill_quarter` | quarter × department × office (20 history quarters + the 4 forward) | Opened by type, filled by type, vacant at the end, employees at the start, the Budget allocated to the office |
| `mart_fill_survival` | approval quarter × department × office × level band × requisition type × ten-day period (to 210 days) | At risk and filled: Tableau rebuilds Kaplan–Meier under any selection with `EXP(RUNNING_SUM(LN(1 - filled / at_risk)))` |
| `mart_pid_forecast_draws` | forward quarter × department × office × draw (rows with all zeros dropped) | The six counts of section 1 |
| `mart_pid_forecast_backtest` | origin × target quarter × department × office | Mean and variance of the forecast fills and vacancy, and the actuals; the page sums means and variances over a selection (cells are treated as independent) |
| `mart_pid_forecast_accuracy` | origin × target quarter, company | P10, P50 and P90 against the actual, in range, error |
| `mart_pid_forecast_model` | coefficient | Every term of the time-to-fill model at the report date |
| `mart_pid_forecast_run` | run (forward and each backtest origin) | Origin, latest data used, requisitions fit, waiting at the origin, draws |
| `mart_cw_budget_function` | fiscal year × function | The contingent budget line: workers and annualized spend at year-end, spend per worker |

## 7. Run it

```bash
python pipeline/run_pipeline.py      # the warehouse
python forecast/run_forecast.py      # about 15 seconds: fit, simulate, backtest, write, test
```

Expected last line: `Done in ... All forecast tests passed.` CI runs both and checks that every mart reproduces exactly.
