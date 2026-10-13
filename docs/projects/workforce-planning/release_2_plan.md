# Warehouse release 2: plan

**Arcadia Systems · people-analytics-warehouse** · drafted 2026-10-12. Arcadia Systems is fictional and all data is synthetic.

One SQL session that delivers three things in a single generator release and one rebuild:

- **A. The parked SQL items** from the Compensation Walk build.
- **B. The Career moves query** for Dashboard #2.
- **C. A new Workforce Planning domain** (positions, requisitions, candidates, plan) for **Dashboard #3**.

Every number on Dashboards #1 and #2 will change, because the history is extended and hires now come from requisitions. The expected-values tables are therefore rebuilt at the end, not patched.

## Progress

| Phase | State | Evidence |
|---|---|---|
| 0. Branch and baseline | Done 2026-10-12 | Branch `warehouse-release-2` from `main`; regenerated raw files and marts match the committed ones; 40 tests pass; totals in [baseline_release_1.md](baseline_release_1.md) (`python pipeline/control_totals.py`) |
| 1. Per-domain random streams | Done 2026-10-12 | `domain_stream()` in `generator/generate_data.py` (positions, recruiting, plan); zero raw files changed after regenerating |
| 2. History from Jun 2021 | Done 2026-10-12 | Start month-end Jun 30, 2021; 23,500 opening people with FY22 growth of 6.5% (25,044 at Jun 2022, old start 25,014); pay history from the Mar 2021 conversion; ECB extract from Jan 2021; 2021 fringe rates reuse each country's 2022 inputs, flagged `is_estimate`; 40 tests pass; totals in [release_2_totals.md](release_2_totals.md). Two part A items moved here from phase 7 because the walk CSV passed GitHub's 100 MB file limit: the grid keeps only the four offered period types (no Custom Range pairs) and the first year is lead-in (pairs end after Jun 30, 2022, computed from the calendar). 88 pairs; walk 114,977 rows (was 271,219), office moves 53,826 (was 260,464); build 46 s (was 80 s) |
| 3. Positions, requisitions, vacancy chains | Next | |

---

## 1. Decisions (2026-10-12)

| # | Decision |
|---|---|
| D1 | Dashboard #3 is **Workforce Planning**. |
| D2 | The Career moves query is part of this session. |
| D3 | The **position** is the thread. Each hire is tied to the seat it filled: net-new or backfill. A backfill links to the prior incumbent's exit type, level, office and pay. |
| D4 | **Internal fills are included.** A worker moving into a vacant seat vacates their own seat, which creates a backfill chain. |
| D5 | **Reuse match rule** for "could a vacant seat have been used instead of a net-new one": same department, same job family, level within ±1, **same country**, seat open or frozen. |
| D6 | **Cost center = department × country.** |
| D7 | **Pay zones may be added within a country** (for example US high-cost vs standard), so a California seat refilled in Austin shows a real location effect. |
| D8 | Seat relocation on backfill happens **within a country**; cross-border seat moves are rare. The dashboard filters by country to show office-to-office seat corridors. |

## 2. Principles

1. **One generator release.** Backfill, positions and plan all land together, so the check tables, extracts and republish happen once.
2. **One seeded random stream per domain:** positions, recruiting, plan. The worker simulation keeps its current stream and seed. A new domain never shifts the draws of an existing one.
3. **Same layering as today.** Raw CSV → `sql/01_staging` → `02_intermediate` → `03_marts`, with a T-SQL twin in `sqlserver/`. Tests are in `tests/`, and Tableau Custom SQL in `tableau/` uses one SELECT, no CTEs, block comments only.
4. **Existing marts keep their column names**, so *Replace Data Source* still works.
5. **Generic names.** Textbook grains and names (position, requisition, candidate, plan version).
6. **Every new table gets a control** that must reconcile exactly and fails the build when it doesn't.

## 3. Generator changes

| Change | What it does |
|---|---|
| History from **Jun 30, 2021** | The simulation starts one year earlier. The displayed window still starts after Jun 30, 2022 (rule in the pair grid). |
| Per-domain random streams | Refactor first and prove the output is unchanged before adding anything. |
| **Positions** | Every worker sits in a position from day one, CEO included. The initial incumbents of 2021 have no prior incumbent. |
| **Hires come from requisitions** | A hire event is the fill of a requisition on an open position. Growth targets now flow through the plan into net-new positions. |
| **Exit → vacancy decision** | Each exit and each internal move out triggers a decision on the seat (section 5). |
| **Promotions and demotions in place** | The position is reclassified one level with the same incumbent. This is a position SCD2 change and creates no vacancy. |
| **Transfers** | An internal move fills a vacant seat elsewhere and vacates the old one, which feeds the chain. |
| **Plan versions** | A budget before each July 1, then reforecasts RF1 to RF3 after each fiscal quarter. Built from the simulation's intent plus noise, so plan ≠ actual. |
| **Pay zones** | Add an office-level pay zone where the warehouse only has country level. Check first: the existing within-country relocation adjustment may already be zone-based. |
| **Frictions** | Late approvals, mid-year plan revisions, short overlaps (two incumbents for up to 30 days, flagged), net-new seats approved while matching vacancies sit open, and cancelled requisitions. |

## 4. New tables

### Raw / dimensional

| Table | Grain | History | Key columns |
|---|---|---|---|
| `dim_cost_center` | department × country | Type 1 | `cost_center_id`, `department_id`, `country_code`, `function_id` |
| `dim_position` | position × effective-dated version | SCD2 | `position_id`, `effective_from`, `effective_to` (exclusive, open = 9999-12-31), `status` (filled / open / frozen / eliminated), `job_profile_id`, `job_level`, `job_family`, `department_id`, `cost_center_id`, `location_id`, `pay_zone`, `fte`, `created_date`, `created_reason` (initial / net-new / split / reorg), `change_reason` (fill, vacate, re-level, relocate, freeze, unfreeze, eliminate, reclass on promotion) |
| `fact_position_assignment` | position × worker × effective dates | effective-dated | `position_id`, `worker_id`, `start_date`, `end_date`, `fill_type` (external hire / rehire / internal move / initial), `requisition_id`, `vacate_reason` (voluntary / involuntary / retirement / internal move out / still in seat), `overlap_flag` |
| `fact_requisition` | requisition | accumulating snapshot | `requisition_id`, `position_id`, `req_type` (backfill / net-new), `opened_date`, `approved_date`, `target_start_date`, `filled_date`, `cancelled_date`, `status`, `hiring_manager_id`, `filled_by_worker_id`, `fill_source` (external / internal) |
| `fact_candidate_stage_event` | candidate × requisition × stage | transaction | `candidate_id`, `requisition_id`, `stage` (applied → screen → interview → offer → accepted / declined / rejected / withdrawn), `stage_date`, `is_internal`, `worker_id` when internal |
| `fact_workforce_plan` | cost center × fiscal quarter × plan version | versioned, never overwritten | `plan_version` (FYnn Budget, RF1, RF2, RF3), `version_date`, `planned_ending_headcount`, `planned_ending_fte`, `planned_net_new`, `planned_backfills`, `planned_cost_usd` |
| `ref_pay_zone` (only if needed) | country × pay zone × fiscal year | dated | `zone_factor` applied to the level base salary and the salary range |

### Derived (intermediate)

| Table | Grain | Purpose |
|---|---|---|
| `int_position_snapshot` | position × month-end | Status, incumbent, level, office, cost center at each month-end. Feeds the vacancy pool and the plan-vs-actual comparison. |
| `int_position_fill` | one row per fill (external or internal) | The core of Dashboard #3 (section 6). |
| `int_vacancy_chain` | fill × chain | `chain_id`, `chain_depth`, `chain_root_event` (the exit or net-new seat that started it). |

### Marts

| Mart | Grain | Feeds |
|---|---|---|
| `mart_position_fill` | fill | Hires by seat type, prior incumbent profile, level and location shift, pay walk |
| `mart_vacancy_pool` | month-end × cost center × job family × level | Open and frozen seats, vacancy age, reuse candidates |
| `mart_plan_vs_actual` | cost center × fiscal quarter × plan version | Planned vs actual net-new, backfills, ending headcount, cost |
| `mart_seat_corridors` | period pair × from office × to office | Map lines from the prior incumbent's office to the new hire's office (Footprint map pattern) |
| `mart_career_moves` (part B) | period pair × view × group × move type × level | Promotions, demotions, Director and above, keyed like the walk |

## 5. Seat rules in the simulation (starting values, tunable)

When a seat is vacated, by an exit or an internal move out:

| Outcome | Starting share | Notes |
|---|---:|---|
| Backfill as is | 60% | Same level, same office |
| Backfill re-levelled | 15% | Usually one level down (for example a manager seat refilled with an analyst); sometimes up |
| Backfill relocated within the country | 10% | Toward lower-cost offices or pay zones, for example California → Austin, Bengaluru → Hyderabad |
| Frozen | 10% | May be unfrozen later or eliminated |
| Eliminated | 5% | Concentrated in the FY24 restructuring and the FY25 reorg |

Fill source for an open seat: about 75% external and 25% internal. The internal share is higher for manager-and-above seats. Each internal fill vacates a seat, so it goes back through the table above.

Net-new seats are created from the plan's `planned_net_new`. Some are deliberately approved while a matching vacancy exists (rule D5), so the reuse flag has real cases.

## 6. `int_position_fill`: one row per fill

| Field | Definition |
|---|---|
| `fill_id`, `position_id`, `worker_id`, `fill_date`, `fill_type`, `requisition_id` | The hire or internal move |
| `seat_type` | `Net-new` when there is no prior assignment on the position; otherwise `Backfill` |
| `prior_worker_id`, `prior_end_date`, `prior_vacate_reason` | The previous incumbent's assignment on this position |
| `prior_level`, `new_level`, `level_change` | Position level when vacated vs when filled (up / same / down) |
| `prior_location_id`, `new_location_id`, `location_change` | Same office / other office in the same country / other country |
| `prior_pay_zone`, `new_pay_zone` | Zone at vacate and at fill |
| `vacancy_days` | `prior_end_date` → `fill_date` |
| `time_to_fill_days` | `opened_date` → `filled_date` |
| `chain_id`, `chain_depth` | From `int_vacancy_chain` |
| `reuse_candidate` | Net-new only: when approved, a seat matching rule D5 had been open or frozen for 30 days or more (default, tunable) |
| `reuse_candidate_position_id` | The matching seat (the oldest vacancy wins) |
| Pay fields | `prior_exit_pay`, `new_start_pay`, the pay walk below, all annualized base in constant USD |

### Pay walk from the prior incumbent to the new hire

Let `mid(level, zone, FY)` be the salary range midpoint.

| Step | Formula |
|---|---|
| Level effect | `mid(new level, old zone, exit FY) − mid(old level, old zone, exit FY)` |
| Location effect | `mid(new level, new zone, exit FY) − mid(new level, old zone, exit FY)` |
| Market effect | `mid(new level, new zone, hire FY) − mid(new level, new zone, exit FY)` |
| Positioning | `(new pay − mid(new level, new zone, hire FY)) − (prior pay − mid(old level, old zone, exit FY))` |

The four steps add up exactly to `new pay − prior pay` (tested). The order is level, then location, then market. A Shapley version that removes order bias can come later, when case study 5 is built.

## 7. Plan vs actual

`mart_plan_vs_actual`, per cost center × fiscal quarter × plan version:

- Planned vs actual **net-new**, **backfills** and **ending headcount and FTE**.
- **Net-new hired while reuse candidates existed:** count and cost.
- **Attainment** = actual ÷ planned. It can be compared against the budget or any reforecast, for a prior quarter or year.

Plan rows stay at quarter grain. Tableau relates them to the actuals, so yearly targets are never repeated across worker rows.

## 8. Tests (added to the 40 existing)

1. Position SCD2: no gaps or overlaps per position; `effective_to` is exclusive.
2. Every active worker holds exactly one position on every day (overlaps only on seats where `overlap_flag` = 1, at most 30 days).
3. No position has two incumbents outside a flagged overlap.
4. Control every month-end: active positions = filled + open + frozen.
5. Every external hire event in `fact_job_history` has exactly one fill row with an external fill type, and the reverse.
6. Every internal fill has a matching vacate with reason `internal move out` on the same day.
7. Every chain ends in an external hire, a freeze, an elimination or an open seat at the as-of date.
8. Every filled requisition has exactly one fill and one accepted candidate.
9. Plan versions are never overwritten: (cost center, quarter, version) is unique, and versions are dated in order.
10. The pay walk steps add up to the pay change for every fill, to the cent.
11. A reuse candidate always satisfies rule D5 on the approval date.
12. Headcount from `int_position_snapshot` filled seats = headcount from the worker month-end snapshot, every month (the bridge between the two worlds).
13. The career moves mart ties to the walk's promotion and demotion counts.

## 9. Parked items (part A) and career moves (part B)

| Item | Where | Check |
|---|---|---|
| `report_as_of_date`, `report_start_date` | walk and office-moves Custom SQL, marts | Popover note, page subtitle, Default From/To |
| ~~Display window from Jul 2022~~ | done in phase 2 (lead-in rule in the grid of all four queries) | FY23 offers all four period options |
| ~~Drop the Custom Range pairs~~ | done in phase 2 | 88 pairs |
| `Leader` → `Sub-function` | both Custom SQLs, both marts, `build_sketch_svg.py`, picker docs; workbook parameter and calcs | Decide: list only real sub-functions, or keep the function-name fallback |
| Region per group | walk SQL | Growth by Region follows the group |
| `open_headcount` | office-moves SQL | "1.2% of headcount" in the map title |
| Relocation 216 vs 227 | check query first, then rename the step to "Same-Country Transfer Adj." | Tooltip shows both numbers |
| Departures by region | office-moves SQL | Each move appears once per end |
| **Career moves** (B) | new `tableau/custom_sql_career_moves.sql` + mart | Promotions, demotions, Director and above, same group keys; validated like 06 and 07 |

## 10. Run order

| Phase | Work | Checkpoint |
|---|---|---|
| 0 | New branch; save today's control totals for comparison | Regenerated files match; 40 tests pass |
| 1 | Split the random streams | Raw files unchanged |
| 2 | History from Jun 2021 | 40 tests pass; new totals recorded |
| 3 | Positions, assignments, hires through requisitions, vacancy decisions, chains | Tests 1–8, 12 |
| 4 | Pay zones, cost centers, plan versions, candidates | Tests 9–11 |
| 5 | DuckDB staging, intermediate, marts | All tests pass |
| 6 | SQL Server twin; `05_validate` extended; new `08_validate_workforce_planning.sql` | PASS |
| 7 | Part A query changes and part B career moves; `06`, `07`, new `09_validate_career_moves.sql` | PASS; marts match the Custom SQL row for row |
| 8 | New expected-values tables for Dashboards #1 and #2; refresh extracts; republish both | Check tables match |
| 9 | Docs: data dictionary, `docs/projects/workforce-planning/`, README case study 1 | — |

## 11. Still open

- **Sub-function fallback:** list only the real sub-functions, or keep the function names and say so in the tooltip.
- **Reuse threshold:** 30 days vacant by default; confirm when the first numbers exist.
- **Pay zones:** settled. Offices already carry a pay-zone factor (`dim_location.pay_zone_factor`), so no new reference table is needed.
- **Market effect in the seat pay walk:** salary ranges are the same in every fiscal year today, so the market step would always be zero. Decide in phase 4 whether ranges get an annual structure increase (this also moves the range cap on tenure raises).
- **2021 fringe rates:** carried back from 2022 and flagged. A researched 2021 set (OECD Taxing Wages 2022 edition, BLS ECEC March 2021) can replace them later.
- **Data size:** candidate volume per requisition is kept moderate so the repo and the Tableau Public extracts stay small. Expected rows are measured in phase 4.
