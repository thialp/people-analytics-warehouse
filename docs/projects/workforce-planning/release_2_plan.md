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
| 3. Positions, requisitions, seat decisions | Done 2026-10-12 | Raw `dim_position` (101,297 records), `fact_position_assignment` (54,094), `fact_requisition` (31,323); staging models and `int_position_snapshot` (seat × month-end, 1.7M rows); tests 41–48 pass, and each was checked against a deliberately broken copy of the data. Fills FY22–FY26: about 24% of backfills are internal moves; external hires are 60–85% backfills (FY24, the restructuring year, 86%). Closing headcount within 21 of phase 2 every year. Cost: FY26 $3,359.4M vs $3,215.9M in phase 2 (+4.5%), because backfills hire at the leaver's level (average grade 3.62 → 3.71 over five years); see section 11 |
| 4. Range increases, cost centers, plan versions, candidates | Done 2026-10-12 | **Salary ranges move every July 1** (decided 2026-10-12): Arcadia pay policy, 2.5% to 4.0% a year plus a country adjustment (India +4 pp; Brazil, South Africa, Poland, Philippines +2; Mexico +1.5; Japan, Switzerland −1.5), anchored on the FY23 level bases; hire pay, the promotion floor and the tenure and market caps use the range in force. People and seats are identical to phase 3 (ranges change amounts, not decisions); cost FY22 $2,487.1M to FY26 $3,336.5M. **Cost centers**: `dim_cost_center`, department × country (`CC-1010-US`), 630; on every seat record and requisition. **Plan**: `fact_workforce_plan`, 28,800 rows, Budget plus RF1–RF3 per fiscal year (FY22–FY26), each reforecast covering the quarters still ahead; written around the actuals with an error that shrinks per version; budgets plan about 1.3× the net-new hires that happen (FY24 3.1×: set before the restructuring), backfills about 1.1×. **Candidates**: `dim_candidate` (188,982 applicants) and `fact_candidate_stage_event` (531,691 stages), split so source and internal flag are not repeated on every stage; about 7 applicants per real search; 16% accepted, 71% rejected, 11% withdrawn, 2% declined an offer. Tests 49–52 pass and catch deliberate breaks |
| 5. Marts for Dashboard #3 | Done 2026-10-12 | Intermediate `int_position_history` (seat records with status runs, country, pay zone, family), `int_seat_fill` (30,575 fills: prior incumbent, seat decision, level and location change, pay walk, reuse check), `int_seat_vacancy_chain`. Marts `mart_position_fill` (30,575), `mart_vacancy_pool` (62,055 seat-months), `mart_plan_vs_actual` (28,800), `mart_seat_corridors` (821), exported as CSVs. Pay walk adds up on every backfill (largest residual 3×10⁻¹¹ USD). **Reuse threshold set to 90 days** (at 30 days half of net-new seats matched a seat still being recruited for; at 90 days 25%, four in five of them frozen seats). Tests 53–56 pass and catch deliberate breaks. FY26 values in [headline_values.md](headline_values.md) |
| 6. SQL Server twin | Done 2026-10-12; first Mac run: 06 and 07 all PASS on SQL Server, `build_all` stopped in 03b (a primary-key column left nullable, fixed; the checker now tests that rule), rerun pending | `sqlserver/03b_build_dw_workforce_planning.sql` (seat layer: 7 typed tables, seat history, seat month-end snapshot, seat fills with pay walk and reuse check, vacancy chains, plan vs actual), 4 views in `04` with the marts' column names, `08_validate_workforce_planning.sql`; `05`, `06`, `07` expected values refreshed (06/07 now check FY23 instead of 2022→2026, a pair the new grid no longer has); `02` regenerated. SQL Server could not run here (container registries blocked), so `sqlserver/check_tsql_in_duckdb.py` translates the T-SQL to DuckDB with sqlglot and compares: all 7 reporting views and both Custom SQL files (walk: FY26 slice) match the DuckDB marts row for row; 05 and 08 all PASS. Found and fixed on the way: the existing org leader view returned a blank manager name for the CEO instead of NULL; cost center names use a plain hyphen (BULK INSERT reads the server code page). Run guide for the Mac: [sql_server_release_2_run.md](sql_server_release_2_run.md) |
| 7. Part A query changes and part B career moves | Next | |

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
| `dim_position` | position × effective-dated version | SCD2 | `position_record_id`, `position_id`, `effective_start_date`, `effective_end_date` (inclusive, NULL = current, as in job history), `status` (filled / open / frozen / eliminated), `job_profile_id`, `job_level`, `job_family`, `department_id`, `cost_center_id`, `location_id`, `pay_zone`, `fte`, `created_date`, `created_reason` (initial / net-new / split / reorg), `change_reason` (fill, vacate, re-level, relocate, freeze, unfreeze, eliminate, reclass on promotion) |
| `fact_position_assignment` | position × worker × effective dates | effective-dated | `assignment_id`, `position_id`, `worker_id`, `start_date`, `end_date` (inclusive), `fill_type` (Initial / External Hire / Internal Move), `requisition_id`, `vacate_reason` (Voluntary / Involuntary / Internal Move Out / NULL while in the seat) |
| `fact_requisition` | requisition | accumulating snapshot | `requisition_id`, `position_id`, `req_type` (Backfill / Net-new), `opened_date`, `approved_date`, `target_start_date`, `filled_date`, `cancelled_date`, `status`, the seat's `department_id`, `location_id`, `job_profile_id`, `job_level` when opened, `hiring_manager_id`, `filled_by_worker_id`, `fill_source` (External / Internal) |
| `dim_candidate` | applicant × requisition | Type 1 | `candidate_id`, `requisition_id`, `is_internal`, `candidate_source`, `worker_id` (the hire only), `final_status` |
| `fact_candidate_stage_event` | candidate × stage | transaction | `candidate_event_id`, `candidate_id`, `stage` (Applied → Screen → Interview → Offer → Accepted / Declined / Rejected / Withdrawn), `stage_order`, `stage_date` |
| `fact_workforce_plan` | cost center × fiscal quarter × plan version | versioned, never overwritten | `plan_version` (`FY26 Budget`, `FY26 RF1` …), `version_type`, `version_date`, `fiscal_year`, `fiscal_quarter`, `quarter_end_date`, `cost_center_id`, `planned_ending_headcount`, `planned_ending_fte`, `planned_net_new`, `planned_backfills`, `planned_cost_usd` (quarter-end loaded run-rate at the version date's FX), `plan_fx_rate_date` |
| ~~`ref_pay_zone`~~ | not needed | | offices already carry `pay_zone_factor` |
| `ref_salary_range` (changed) | fiscal year × level × country | dated | now moves every year; new `structure_increase_pct` |

### Derived (intermediate)

| Table | Grain | Purpose |
|---|---|---|
| `int_position_history` | seat record | Seat SCD2 with status run start (`status_since`), country, currency, pay zone, job family, manager seat flag. Built in phase 5; the snapshot and fills read it. |
| `int_position_snapshot` | position × month-end | Status, incumbent, level, office, cost center at each month-end. Feeds the vacancy pool and the plan-vs-actual comparison. |
| `int_seat_fill` | one row per fill (external or internal) | The core of Dashboard #3 (section 6). Named `int_seat_*` so it builds after `int_position_history` (models run in file-name order). |
| `int_seat_vacancy_chain` | fill | `parent_fill_id`, `chain_id`, `chain_depth`, `chain_length`, `chain_trigger` (Voluntary exit, Involuntary exit, Net-new seat). |

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
| `reuse_candidate` | Net-new only: when approved, a seat matching rule D5 had been open or frozen for 90 days or more (decided in phase 5; the threshold is one line in `int_seat_fill.sql` and test 54) |
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

Built in phase 3: test 41 (plan item 1), 42 (3), 43 (every job record sits in its seat, new), 44 (seat status matches its incumbent), 45 (12), 46 (5), 47 (6, extended to every seat exit), 48 (8). Built in phase 4: test 49 (plan item 9, plus reforecasts dated after the quarter they follow), 50 (candidates tie to requisitions), 51 (cost center = department × country), 52 (ranges move by the structure increase). Built in phase 5: test 53 (plan item 10, plus no level effect at the same grade and no location effect in the same office), 54 (11), 55 (7, plus chain links), 56 (plan vs actual ties to headcount and fills). Still to build: plan item 13 (phase 7); item 4 is true by construction of the snapshot and is replaced by 44.

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
- **Reuse threshold:** 90 days (phase 5). Change it in `int_seat_fill.sql` and test 54 together.
- **Pay zones:** settled. Offices already carry a pay-zone factor (`dim_location.pay_zone_factor`), so no new reference table is needed.
- **Market effect in the seat pay walk:** settled in phase 4: ranges move every July 1, so the market step is real.
- **The plan is written around the actuals (simulation shortcut):** the generator draws each version from what happened, with an error that shrinks per reforecast, instead of letting the plan drive hiring. Honest to say so in the case study; the version mechanics, variance and attainment are what the dashboard shows.
- **Grade creep from backfills (phase 3):** a backfill hires at the leaver's level, while net-new hires follow the junior-leaning hire mix, so the average grade drifts from 3.62 to 3.71 over five years and FY26 loaded cost is 4.5% above phase 2. Kept as is: it is a real effect and feeds case study 5 ("hiring shifted toward higher grades"). Lever if it should be smaller: `SEAT_DECISION` re-level share and `RELEVEL_DOWN_SHARE` in `generator/reference_data.py`.
- **Not built in phase 3:** short overlaps (two incumbents for up to 30 days, flagged) and rehires. Seats never overlap today (test 42).
- **Hires on Jul 1, 2026:** team splits at the last month-end hire a few managers the day after history ends (existing behaviour, 3 in this build); they are outside every snapshot.
- **2021 fringe rates:** carried back from 2022 and flagged. A researched 2021 set (OECD Taxing Wages 2022 edition, BLS ECEC March 2021) can replace them later.
- **Data size:** candidate volume per requisition is kept moderate so the repo and the Tableau Public extracts stay small. Expected rows are measured in phase 4.
