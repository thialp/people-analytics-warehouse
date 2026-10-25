# Warehouse release 3: plan

**Arcadia Systems · people-analytics-warehouse** · drafted 2026-10-14. Arcadia Systems is fictional and all data is synthetic.

Release 3 adds Arcadia's **contingent workforce** and the **two source systems** behind it, removes **part-time**, and carries the change through every case study. It ends with a new **case study 4, Contingent Workforce**, about reconciling the two systems.

Like release 2, it is one generator release and one rebuild. Every number on Dashboards #1 and #2 changes again, so the check tables are rebuilt at the end, and Dashboard #3 is built on release 3 data rather than release 2.

## Progress

| Phase | State | Evidence |
|---|---|---|
| 0. Branch and baseline | Done 2026-10-14 | Branch `warehouse-release-3` from `main` (`8ac0f31`); regenerated raw files and marts match the committed ones; 59 tests pass; totals in [baseline_release_2.md](baseline_release_2.md) (FY26 closing 30,014 people, 29,363.5 FTE, $3,336.5M loaded constant) |
| 1. Remove part-time | Done 2026-10-14 | Every employee is 1.0 FTE. The generator keeps every random draw, so people, hires, exits, moves, seats and requisitions are identical to release 2; only the 1,899 FTE-change job and seat records are gone. FTE Changes removed from the headcount walk, compensation walk, cost bridge and footprint (DuckDB, Custom SQL); `part_time_headcount` dropped; test 23 now checks full-time. 59 tests pass; checker and all validation scripts PASS (06, 07, 09, 11 run locally too). FY26: 30,014 people = 30,014.0 FTE; loaded constant $3,410.5M (was $3,336.5M); pay per FTE $110,062.73 → $113,663.81. Totals: [release_3_totals_phase_1.md](release_3_totals_phase_1.md). Workbook impact: [release_3_migration_notes.md](release_3_migration_notes.md) |
| 2. Source systems and lineage | Done 2026-10-14 | `generator/source_systems.py`: five systems (Keystone HR, Bridgeway VMS, integration log, public reference data, warehouse metadata), the source of all 38 raw tables, and the column contract of the 11 release 3 tables, written as raw tables `ref_source_system`, `ref_raw_table_lineage`, `ref_raw_column`. The 8 contingent workforce tables land with headers only. 11 staging models; tests 60 (lineage) and 61 (column contract) pass and catch deliberate breaks; SQL Server raw load regenerated; checker PASS. Docs: [source systems and lineage](../../warehouse/source_systems.md), data dictionary section, README architecture. Existing raw files and marts unchanged |
| 3. Contingent worker simulation | Done 2026-10-14 | `generator/contingent_workforce.py` (own random stream, after the employee simulation: no employee file changes), parameters in `reference_data.py`. Burn-in from Jul 2013 so the Jun 2021 population has real ages; extract as of 2026-06-30; workers ended before Jul 2020 archived. 23 suppliers, 23,408 rate card lines, 43,423 workers, 58,276 service orders, 160,611 revisions, 632,365 timesheet rows. Active CW 8,564 (Jun 2021) → 11,941 (Jun 2026), 71% Contractor / 13% Consultant / 17% BPO, 64% Technology, 41% India; FY26 billed spend $1,087.9M (≈ a quarter of workforce cost). Tests 62–66 pass and catch deliberate breaks; control totals gain a contingent workforce table. [Bridgeway simulation](bridgeway_simulation.md), [totals](release_3_totals_phase_3.md) |
| 4. Feed and discrepancy injection | Done 2026-10-14 | `generator/keystone_feed.py` (own random stream: employee data and every mart unchanged). 106,357 feed events (1,410 failed, 6,345 late, 252 partly applied); 42,073 Keystone records, 140,681 versions (feed, Keystone inactivations, HR Ops, managers); Bridgeway hygiene seeded (late or missing closures, 139 timesheets after the last day, 62 renewals submitted as new workers). Answer key `gen_cw_discrepancy_truth`: 28,869 periods across 13 types (CW00 to CW12, catalogue `ref_cw_discrepancy_type`), built by replaying each Keystone record ideal vs real; zero unexplained days; about 3% of active CW carry an open discrepancy on any June 30; every worker active in one system but not the other on three test dates is explained by the key. Tests 67–69 (and 66 amended) pass and catch deliberate breaks. [Keystone and the feed](keystone_feed.md), [totals](release_3_totals_phase_4.md) |
| 5. Plan, conversions, spend | Done 2026-10-14 | **Conversions:** 1,182 contingent workers hired as employees into existing external hires (4.0–5.1% of contingent exits a year), same country and department, hire in the same month as the first day after the engagement and within 21 days, so a conversion never changes the total; Bridgeway's worker takes the employee's name, the applicant source is *Contingent conversion*, Keystone closes the record as *Converted to employee* with `converted_to_worker_id`, and a late feed change to a converted record is rejected. Employee data unchanged except 1,182 applicant sources. **Plan:** `planned_cw_headcount` and `planned_cw_spend_usd` (annualized run-rate at the version's FX) on every plan row, plus 615 contingent-only rows (zero employee measures; every employee total unchanged), own random stream. Phase 4 numbers shifted slightly with the new draws (docs refreshed). Tests 76–77 (and 68 extended) pass and catch deliberate breaks. [Conversions and the plan](conversions_and_plan.md), [totals](release_3_totals_phase_5.md) |
| 6. Marts: existing case studies | Done 2026-10-14 | Foundations: `int_cw_month_end_snapshot` (Bridgeway as held each month-end, never restated, run-rates at month-end and constant FX), `int_cw_movement`, `int_cw_conversion` (1,174 linked conversions, all in the same month on both sides). **Walk** (#1): `worker_type` and `walk_step`; contingent Starts, Ends (completed, early, *lapsed while an approval was late*: 85–116 a year), moves and Conversions (order 7), so employee Hires exclude conversions; Employees, Contingent and Total close every month. **Footprint**: office walk and flows by worker type, Bridgeway office. **Plan vs actual**: contingent headcount and run-rate at plan FX. **`mart_cw_spend`** (new): billed spend beside the month-end run-rate, tied to the timesheets to the cent. **Cost bridge**: worker type, contingent drivers, Conversions (driver 10). **`mart_workforce_cost_growth_mix`** (new): year-over-year total workforce cost split into volume, workforce mix, location mix, level mix, rate and currency by Shapley values, beside the sequential split and its order bias. The pipeline now orders models by what they read. Tests 70, 71, 72, 74, 78 (and 07–22 by worker type) pass and catch deliberate breaks. [Migration notes](release_3_migration_notes.md#phase-6-contingent-workers-in-the-marts-of-case-studies-15-2026-10-14), [growth mix](../workforce-cost-bridge/methodology.md#release-3-total-workforce-cost-and-the-growth-mix), [totals](release_3_totals_phase_6.md) |
| 7. Marts: case study 4 | Done 2026-10-14 | `dim_worker.work_email` (managers comparable across systems). Identity resolution in three tiers with confidence and evidence, a supplier alias map (59 spellings, 23 suppliers): every broken-link record matched to the right worker, every Keystone-only worker left unmatched. Side-by-side snapshot (what Keystone should hold = everything Bridgeway sent, applied the day it was sent) and rules for CW00–CW12 from the two systems and the feed log alone, with root cause, evidence, age, severity and owner. **Detection score: 28,530 seeded discrepancy-months, 100% found; 42 false flags, all explained name coincidences.** 416 of 11,941 contingent workers (3.5%) carry an open discrepancy on 30 June 2026. Marts `mart_cw_discrepancy_detail`, `mart_cw_reconciliation`, `mart_cw_engagement_cap`, `mart_cw_detection_score`. Tests 73, 75. [Case study 4](case_study_4.md), [totals](release_3_totals_phase_7.md) |
| 8. SQL Server twin and Custom SQL | Done 2026-10-14 (SQL Server on the Mac: all PASS) | `sqlserver/03c_build_dw_contingent.sql` (Bridgeway, Keystone and the feed typed into `dw`; contingent snapshot, conversions, movement, plan actuals; supplier alias, identity resolution, side-by-side snapshot, discrepancy rules), `04b_create_reporting_views_contingent.sql` (six views), `12_validate_contingent_workforce.sql` (51 checks); `DimWorker.WorkEmail`, the plan's contingent columns; Custom SQL for the walk (#1), the cost bridge and plan vs actual brought to worker types. `check_tsql_in_duckdb.py`: all 13 views and 10 Custom SQL results MATCH their marts row for row; the contingent intermediates match exactly, evidence text included; 05, 08, 10, 12 all PASS. [Run guide for the Mac](sql_server_release_3_run.md), [migration notes](release_3_migration_notes.md#phase-8-sql-server-twin-and-custom-sql-2026-10-14). **SQL Server run (Mac, 2026-10-14): 10 all 25 PASS (walk Custom SQL 597,097 rows in 14 s); 12 all 51 PASS (cost bridge Custom SQL 29,123 rows in 22 s).** Two SQL Server–only issues found and fixed on the way: Msg 8711 (two ordered `STRING_AGG`s in one SELECT; the checker now flags it) and a growth-mix view that ran 18+ minutes (now precomputed in `dw.WorkforceCostGrowthMix`) |
| 9. Expected values, docs | Done 2026-10-14 | Dashboard check tables (`expected_values.md`) regenerated by the pipeline since phase 6. README rewritten: a plain-language **executive summary** first (fictional company on real public data, Arcadia in numbers, the six questions, color-coded diagrams of the two systems and of a disagreement, FY26 findings), then the **technical deep dive** with release 3 throughout (contingent walk and bridge tables, the growth mix with Shapley vs sequential, case study 4, 40 raw tables, 78 tests, lessons). Six thin Custom SQL files for the new views (`tableau/custom_sql_cw_*.sql`, `custom_sql_workforce_cost_growth_mix.sql`), all MATCH their marts |
| 10. Tableau: Dashboards #1 and #2, then #3, then #6 | Not started | Includes the **Growth by Region fix** on Dashboard #2: the card ignores View and Group, so it shows the company while the KPI cards show the selected group; rebuild it on the region walk query ([migration notes](release_3_migration_notes.md#fix-carried-in-release-3-growth-by-region-follows-the-group-logged-2026-10-14)) |

---

## 1. Decisions (2026-10-14)

| # | Decision |
|---|---|
| D1 | **Part-time is removed.** Every employee is 1.0 FTE; employee headcount = employee FTE ≈ 30,000 at Jun 2026. |
| D2 | **Contingent workers (CW) are added:** about 12,000 active at Jun 2026, in three types: **Contractor, Consultant, BPO**. About two-thirds sit in Technology; the rest are spread across every function. Same history window as employees (Jun 2021 to Jun 2026). |
| D3 | **Two source systems.** **Keystone HR** is the HR system of record that managers and employees use. **Bridgeway VMS** is the vendor management system where suppliers submit vetted workers and service orders live. |
| D4 | **Bridgeway is the source of truth for CW.** A worker counts as active when their Bridgeway service order has started and has not ended. Keystone confirms, completes the profile (person ID, cost center, manager, office) and is where managers look. |
| D5 | **The feed is one-way:** Bridgeway → Keystone. Nothing typed in Keystone ever flows back. A Bridgeway change can reach Keystone late, partly, or not at all. **Bridgeway never stores the Keystone person ID**; Keystone stores the Bridgeway worker ID, and the warehouse joins the two on it. |
| D6 | **Employees are paid, CW are billed.** Employees keep salary, raises, bonus and tenure. CW carry a **bill rate** × **billed hours**: no raises, no bonus, no tenure increase. |
| D7 | **Bill rates change only at an extension or renewal** (a new service order revision). Some revisions renegotiate the rate up or down; nothing is automatic. |
| D8 | **Duration cap.** Contractor and Consultant: initial term up to 24 months, extensions up to 24 more, **48 months in total**. BPO: no cap, renewed yearly. A small number of breaches are seeded so the cap can be flagged. |
| D9 | **CW do not hold employee seats.** Positions, requisitions, applicants and the seat tests stay employee-only. CW arrive through service orders. |
| D10 | **Dashboards #1 and #2: worker-type split.** #1 walks Employees, CW and Total workforce. #2 stays employee pay per FTE; CW spend gets its own panel and feeds case study 6. |
| D11 | **The workforce plan carries a CW line** per cost center: planned CW headcount and CW spend, in every plan version. |
| D12 | **Case study 4 flags, it never fixes.** The warehouse cannot change either system; it classifies each discrepancy, explains it, and names who can fix it. |

## 2. Guardrails

1. **Employer anonymity.** CW reconciliation is a textbook enterprise problem, and case study 4 is designed from first principles with generic language (vendor system, service order, revision, feed, lag). It does not reproduce any real query's rule order, status codes, recon labels, flag names, toggles or validation layout. Discrepancy categories are named after **what happened in the systems**, not after anyone's internal vocabulary.
2. **Real data is used only for aggregate realism.** The hourly bill-rate benchmarks in section 6 are medians by country and worker type. No name, ID, supplier, cost center, code, title or row from any real file enters the generator, the repo or the docs.
3. **Same layering and conventions as release 2.** Raw CSV → `sql/01_staging` → `02_intermediate` → `03_marts`, T-SQL twin in `sqlserver/`, Custom SQL in `tableau/` (one SELECT, no CTEs, block comments only), per-domain random streams, every new table has a control that fails the build when it does not reconcile.
4. **Existing marts keep their column names** where they survive, so *Replace Data Source* still works. Dropped columns are listed in the migration notes.

---

## 3. Systems and lineage

```
 Supplier submits a vetted worker
            │
            ▼
 ┌─────────────────────────┐      one-way feed (can lag,      ┌─────────────────────────┐
 │  Bridgeway VMS          │  ──  fail or arrive partly)  ──▶ │  Keystone HR            │
 │  source of truth for CW │                                  │  system of record for   │
 │  workers, service       │      nothing flows back  ✕       │  employees; profile for │
 │  orders, revisions,     │  ◀────────────────────────────── │  CW (person ID, cost    │
 │  rates, timesheets      │                                  │  center, manager)       │
 └───────────┬─────────────┘                                  └───────────┬─────────────┘
             │ nightly extract                                            │ nightly extract
             ▼                                                            ▼
 ┌──────────────────────────────────────────────────────────────────────────────────────┐
 │  Arcadia warehouse: raw (bw_*, ks_*) → staging → identity resolution → snapshots     │
 │  → marts → Tableau. Employees + CW = total workforce; salary + bill spend = cost.    │
 └──────────────────────────────────────────────────────────────────────────────────────┘
```

Managers only see Keystone. When an extension is approved in Bridgeway but never reaches Keystone, the manager sees a worker "ending"; when a worker leaves early in Bridgeway but Keystone is never told, the manager still sees them active (and they may keep system access). Those are the stories case study 4 tells.

### Naming in the raw layer

- Existing raw tables (`dim_worker`, `fact_job_history`, `fact_compensation_history`, …) are **Keystone HR extracts**. Their names stay, to keep every release 2 model and test intact; the data dictionary gains a **Source system** line on each.
- New CW tables carry a **system prefix**: `bw_` for Bridgeway, `ks_` for the Keystone side of CW, `feed_` for the integration log. A reviewer sees at a glance which system a fact came from, which is the point of the case study.

---

## 4. Population targets

| | Jun 2021 | Jun 2026 | Notes |
|---|---:|---:|---|
| Employees (headcount = FTE) | ≈ 23,500 | ≈ 30,000 | Unchanged simulation, FTE forced to 1.0 |
| Contingent workers | ≈ 8,600 | ≈ 12,000 | Grows faster than employees, so the CW share of the workforce rises (≈ 27% → 29%) |
| Total workforce | ≈ 32,100 | ≈ 42,000 | |

CW mix at Jun 2026 (starting values, tunable in `generator/reference_data.py`):

| Dimension | Split |
|---|---|
| Type | Contractor 70% · Consultant 12% · BPO 18% |
| Function | Technology ≈ 65%; Operations and facilities carry most BPO; the rest spread across Finance, People, Marketing, Legal, Sales |
| Country | Weighted to Arcadia's lower-cost engineering and operations offices (India, Mexico, Philippines, Portugal and Central Europe where Arcadia has offices), then the US, then the rest. Only countries with an Arcadia office are used |
| Supplier | About 25 fictional suppliers; each offers one or two CW types; a handful of large suppliers carry most Contractors; BPO comes from a few facilities and security firms |
| Role family | Development, QA, Data, Analyst, Project / Delivery, Architecture, Design, Operations; BPO: Security, Facilities, Service Desk |
| Seniority | Junior · Mid · Senior · Lead |

Expected over five years: about 28,000–32,000 CW ever engaged and about 90,000 service order revisions.

---

## 5. Engagement lifecycle (Bridgeway)

1. **Request and submission.** A manager raises a need; a supplier submits a vetted worker; a **service order** is created (revision 0) with role, seniority, office, cost center, start, end, rate.
2. **Approval and start.** Approval takes days to weeks; some orders are withdrawn or rejected before start. Start is on or after approval.
3. **Revisions.** Every change is a new revision with its own effective dates, the current one flagged; **only one revision is current**, the others are history. Reasons: extension, rate change (only with an extension or renewal), cost center change, manager change, office change, early end.
4. **Extension.** Typical revisions extend 3–12 months. Contractor and Consultant engagements stop at 48 months total from the original start (D8). Some extensions renegotiate the rate (−5% to +8%).
5. **Renewal.** At a fiscal year turn, some engagements are renewed as a **new service order** under the same worker; a few are renewed under a **new Bridgeway worker ID** (the duplicate-person case in section 8).
6. **End.** Completed (reached the end date), ended early (by Arcadia or by the worker), **converted to employee** (fills an employee requisition, section 9), or replaced by another worker from the same supplier.
7. **Close.** The order should be closed on or after the end date. Some are not (section 8).

Start, end and duration distributions are tuned to look like a real large program: assignment length median about 16 months, engagement length (original start to end) mean about 2.2 years for Contractors, longer for BPO.

---

## 6. Rates, hours and spend

### Rate card

`bw_rate_card` (a Bridgeway table: rate cards are vendor-management configuration): fiscal year × country × CW type × role family × seniority → `rate_low`, `rate_target`, `rate_high`, `rate_type` (`Hourly`, or `Monthly` for BPO), `billing_currency`.

Anchors, hourly USD median for a mid-level Contractor in development (from aggregate benchmarks, rounded; everything else is derived with multipliers):

| Country | $/hr | | Country | $/hr |
|---|---:|---|---|---:|
| India | 31 | | Poland / Central Europe | 63 |
| Mexico | 53 | | Singapore | 64 |
| Philippines | 28 | | United States | 80 |
| Portugal | 50 | | United Kingdom | 93 |

Multipliers: seniority (Junior 0.75, Mid 1.00, Senior 1.30, Lead 1.55); type (Contractor 1.00, Consultant 1.35); role family (Architecture 1.25 … Analyst 0.90). BPO is billed **per month per worker** (an hourly equivalent is published for comparison). The card moves each July 1 by a market index per country, so a **renewal** can reprice while an untouched order keeps its rate (D7).

About 85% of orders bill in USD; the rest in local currency, valued with the ECB rates already in the warehouse.

### Hours and spend

- **Contracted hours:** 40 a week (BPO: one monthly unit).
- **Billed hours:** `bw_timesheet_month`, one row per worker per service order per month: working days × 8, less holidays and PTO noise, prorated in start and end months. **No hours after the end date**, except seeded anomalies.
- **Spend** = billed hours × rate (or the monthly fee), in billing currency, then USD at month-end FX and at the constant rate set.
- **Run-rate**, comparable with employee loaded cost: current rate × 2,080 hours (or monthly fee × 12). CW have **no fringe**; supplier margin is inside the bill rate.

Rough size check: ≈ 12,000 CW × ≈ $45/hr blended × 2,080 ≈ **$1.1B a year** against ≈ $3.3B employee loaded cost, so CW are about a quarter of workforce cost. The exact figure lands in phase 5.

---

## 7. New raw tables

> **Phase 2:** the column contract was settled and its source of truth is now [`generator/source_systems.py`](../../../generator/source_systems.py), enforced by test 61 and listed in the [data dictionary](../../warehouse/data_dictionary.md#contingent-workforce-release-3). Changes from this draft: the rate card is `bw_rate_card` (in Bridgeway); `bw_service_order` gains `supplier_id`, `order_type`, `renews_service_order_id`; `bw_timesheet_month` gains `billed_units` (months for BPO); `ks_contingent_worker` gains `ks_record_id`, `change_source`, `feed_event_id`, `inactive_reason`. The tables below are the original draft.

### Bridgeway VMS (`bw_`)

| Table | Grain | Key columns |
|---|---|---|
| `bw_supplier` | supplier | `supplier_id`, `supplier_name` (fictional), `cw_types_offered`, `hq_country_code`, `is_active` |
| `bw_contingent_worker` | worker in Bridgeway | `bw_worker_id` (`BW00012345`), `first_name`, `last_name`, `supplier_id`, `cw_type`, `original_start_date`, `email`. **No Keystone person ID** (D5) |
| `bw_service_order` | service order | `service_order_id`, `bw_worker_id`, `opened_date`, `submitted_date`, `approved_date`, `final_status` |
| `bw_service_order_revision` | order × revision (SCD2) | `revision_id`, `service_order_id`, `revision_no`, `revision_reason`, `effective_start_date`, `effective_end_date`, `is_current`, `status` (`Draft`, `Pending Approval`, `Approved`, `Active`, `Ended`, `Closed`, `Withdrawn`, `Rejected`), `assignment_start_date`, `assignment_end_date`, `closed_date`, `role_family`, `seniority`, `job_title`, `cost_center_code` (text, as typed), `hiring_manager_email`, `office_code`, `bill_rate`, `rate_type`, `billing_currency`, `hours_per_week` |
| `bw_timesheet_month` | worker × order × month | `bw_worker_id`, `service_order_id`, `month_end_date`, `billed_hours`, `billed_amount_local`, `billing_currency` |

### Keystone HR side of CW (`ks_`)

| Table | Grain | Key columns |
|---|---|---|
| `ks_contingent_worker` | person ID × effective-dated version (SCD2) | `person_id` (same `W…` key space as employees, so one ID per human in Keystone), `bw_worker_id` (stored from the feed; can be blank or mistyped), `first_name`, `last_name`, `cw_type`, `supplier_name` (text as fed), `status` (`Active`, `Inactive`), `contract_start_date`, `contract_end_date` (as Keystone knows it), `termination_date`, `department_id`, `cost_center_id`, `location_id`, `manager_worker_id` (an employee), `effective_start_date`, `effective_end_date`, `last_changed_by` (`Feed`, `HR Ops`, `Manager`) |

Keystone **auto-inactivates** a CW the day after the contract end date it holds, which is exactly what turns a missed extension into a false termination.

### Integration log (`feed_`)

| Table | Grain | Key columns |
|---|---|---|
| `feed_bridgeway_keystone_event` | one change sent | `feed_event_id`, `revision_id`, `bw_worker_id`, `event_type` (`New Worker`, `Extension`, `Early End`, `Rate Change`, `Attribute Change`, `Renewal`), `sent_date`, `applied_date`, `outcome` (`Applied`, `Applied Late`, `Partly Applied`, `Failed`), `error_text` |

Rates and hours never go to Keystone: managers in Keystone cannot see what a worker costs. That is part of why the warehouse matters.

### Truth table (generator only, not loaded as a source)

`gen_cw_discrepancy_truth`: every discrepancy the generator injected, with type, start and end dates. It is used by tests to **score the warehouse's detection** (how many injected cases it found, how many it flagged wrongly). It is clearly labelled a test fixture; Tableau never reads it.

> **Phase 4:** it is loaded as a raw table from its own lineage system, `GEN` (synthetic data generator), so lineage test 60 covers it and test 69 checks it. One row per cause and continuous period, with the root cause, the records involved, a resolution and a sentence of evidence. Dashboards show only the detection score derived from it, on the methodology page.

---

## 8. Discrepancies seeded in the data

Starting rates are tuned so that, on a typical month-end, about **3–5% of active CW** carry at least one open discrepancy: noticeable, not alarming, as in a healthy real program.

> **Phase 4:** built as **13 types, CW00 to CW12**: *Change in transit* (CW00) is split from *Change arrived late* so normal lag is never a problem; failed attribute changes are CW12; *rate outside the card band* is not seeded (the order scatter already produces it: a case study 4 finding, not an injected defect). Each type carries a severity and an owner in `ref_cw_discrepancy_type`; failures caused by a broken link or a missing record keep that **root cause**. The result lands at about 3%. Final catalogue, rates and volumes: [Keystone and the feed](keystone_feed.md#the-discrepancy-catalogue). The table below is the original draft.

| # | Discrepancy (named after what happened) | How it is seeded | What a Keystone-only manager sees | Who can fix it |
|---|---|---|---|---|
| 1 | **Change arrived late** | Most feed events apply 0–2 days after sending; ~6% take 3–15 days | Old end date, cost center or manager for a while | Self-clears; Integration team if over 7 days |
| 2 | **Extension never arrived** | ~1.5% of extensions fail | Keystone auto-inactivates the worker at the old end date while Bridgeway shows them active | Integration / HR Ops |
| 3 | **Early end never arrived** | ~2% of early ends fail | Worker still active in Keystone after leaving (access risk) | HR Ops |
| 4 | **Ended but never closed in Bridgeway** | ~3% of ended orders stay open past the end date | Nothing; Bridgeway hygiene | Vendor management / manager |
| 5 | **Changed in Keystone only** | Managers or HR Ops edit cost center, manager or office in Keystone; the next feed event may overwrite it | Keystone and Bridgeway disagree on attributes; cost charged to the Bridgeway cost center | Manager, in Bridgeway |
| 6 | **Link ID missing or mistyped** | ~1% of Keystone records with blank or transposed `bw_worker_id` | Nothing; breaks the join | HR Ops |
| 7 | **One person, two IDs** | ~0.5% of renewals create a new Bridgeway worker, and Keystone a second person ID | Same human twice | HR Ops + vendor management |
| 8 | **Never reached Keystone** | ~0.5% of new-worker events fail outright | Worker missing from the manager's team | Integration |
| 9 | **Keystone-only CW** | A few CW created by hand in Keystone with no Bridgeway order | A worker no supplier bills for | HR Ops |
| 10 | **Over the duration cap** | ~1% of Contractor and Consultant engagements extended past 48 months | Nothing | Vendor management / manager |
| 11 | **Billing anomaly** | Hours billed after the end date; rate outside the card band | Nothing (rates are not in Keystone) | Vendor management / Finance |

---

## 9. How release 3 ripples through case studies 1–3, 5 and 6

| Case study | Change |
|---|---|
| **1 Workforce Planning** (Dashboard #3) | `fact_workforce_plan` gains `planned_cw_headcount` and `planned_cw_spend_usd` per cost center × quarter × version. `mart_plan_vs_actual` gains the CW actuals. Seats, requisitions and applicants stay employee-only (D9), except **CW conversions**: ~4% of CW exits are a conversion that fills an employee requisition (`candidate_source` = `Contingent conversion`), so a backfill or net-new seat can be filled by someone who was already working at Arcadia. Dashboard #3 adds the employee / CW mix and plan vs actual for both. |
| **2 Headcount & FTE** (Dashboard #1) | `mart_headcount_fte_walk` gains `worker_type` (`Employee`, `Contingent`) in its grain. **FTE Changes** and `part_time_headcount` are removed. CW movements: **Starts**, **Ends** (completed, early), **Conversions** (out of Contingent, into Employee in the same month, so Total is unchanged by a conversion). Opening + movements = Closing for Employees, CW and Total (tests). The `fte` column stays for compatibility and equals headcount. |
| **3 Workforce Footprint** | CW appear on the office maps (Keystone office), split by worker type. *Built in phase 6 on the **Bridgeway** office instead, so every case study counts contingent workers from one source (D4); where Keystone's office differs it is discrepancy CW05, case study 4.* |
| **4 Compensation Walk** (Dashboard #2) | Stays employee-only. The **FTE Changes** step is removed. A separate **CW spend** panel: run-rate per CW and total CW spend, with its own walk (volume, rate, mix, FX). |
| **5 Workforce Cost Bridge / Finance Growth Mix** | Total workforce cost = employee loaded cost + CW spend. New drivers: **CW volume**, **CW rate**, **CW mix**, **employee / CW substitution** (conversions and CW replacing vacant seats). This is where the Shapley decomposition is built. |
| **6 Contingent Workforce** (new) | Section 10. |

---

## 10. Case study 4: Contingent Workforce

**Business question.** *Who is actually working for Arcadia through a supplier today, what does it cost, and where does the system managers use disagree with the system suppliers use?*

### Warehouse logic

| Model | Purpose |
|---|---|
| `int_cw_service_order_history` | Clean revision history: the revision in effect on any date, assignment dates, rate in force |
| `int_cw_identity_resolution` | Links Keystone person IDs to Bridgeway workers. Tier 1: stored `bw_worker_id` matches. Tier 2: name + supplier + start within 7 days. Tier 3: name + start within 30 days. Each link gets a **match confidence** (High, Medium, Low) and the evidence; unmatched records on either side are kept, never dropped |
| `int_cw_month_end_snapshot` | One row per resolved CW per month-end: Bridgeway status (the count, D4), Keystone status (the comparison), attributes from each system side by side, rate, run-rate |
| `int_cw_discrepancy` | Rule-based classification into the section 8 categories, with an **evidence sentence** naming the values compared, a **severity** (access risk, cost risk, data hygiene), an **owner**, and the **age** in days |
| `int_cw_engagement` | One row per engagement: original start, total months, extensions used, months left before the cap, conversion outcome |

### Marts

| Mart | Grain | Feeds |
|---|---|---|
| `mart_cw_active_snapshot` | month-end × cost center × office × supplier × type × role family | Active CW, run-rate spend, workforce mix with employees |
| `mart_cw_spend` | month × cost center × supplier × type | Billed hours, spend local, USD nominal and constant |
| `mart_cw_reconciliation` | month-end × discrepancy type × owner × function × supplier | Counts, age bands, trend: is the gap closing? |
| `mart_cw_discrepancy_detail` | worker × discrepancy × month-end (latest 13 month-ends) | The work list a manager or HR Ops can act on |
| `mart_cw_engagement_cap` | engagement | Time to cap, extensions remaining, breaches |
| `mart_cw_detection_score` | month-end × discrepancy type | Injected vs detected vs false flags (from the truth table): the validation story |

### Dashboard (outline; designed after the data is verified)

- **Executive:** active CW, CW share of workforce, CW spend run-rate, open discrepancies by severity, trend.
- **Analytical:** spend by supplier, type, function and country; rate vs card; engagements approaching the cap.
- **Diagnostic:** the discrepancy work list by owner, with evidence and age; identity matches by confidence.
- **Methodology:** the two systems, the one-way feed, the active rule, match tiers, and the detection score.

---

## 11. Removing part-time (phase 1)

- Generator: `fte` always 1.0; no `FTE Change` action; the hire mix draws no 0.8 or 0.5.
- Marts: the FTE Changes movement and driver lines are removed from the headcount walk, compensation walk and cost bridge; `part_time_headcount` is dropped; `fte` columns remain and equal headcount for employees.
- Tests: test 23 (part-time levels) is retired; walks still reconcile.
- Docs: data dictionary, README, case studies 1 and 2.
- Migration note for Dashboards #1 and #2: fields that disappear (`Part Time Headcount`, FTE Changes step) and calcs that reference them.

---

## 12. Tests (added to the 59 existing; numbers indicative)

Built in phase 2: **60** every raw table names exactly one source system, **61** every release 3 extract matches its column contract. The contingent workforce tests follow.

62. Revisions per service order chain with no gaps or overlaps; exactly one current revision per order.
63. Assignment start ≤ end; start on or after approval.
64. Contractor and Consultant engagement ≤ 48 months, except the seeded breaches (all of which are flagged).
65. A rate changes only on a revision whose reason is extension or renewal.
66. No billed hours after the assignment end, except the seeded billing anomalies (all flagged).
67. Every feed event refers to an existing revision of the worker's own order, of the matching type; applied date ≥ sent date; outcomes agree with the dates; first in, first out per worker. *(Built in phase 4.)*
68. Every Keystone CW version is explained by a feed event applied that day, a Keystone inactivation, or a hand edit; the history chains; person IDs never collide with employees. *(Built in phase 4.)*
69. The answer key is well formed: known types, references that exist, dates inside the extract. *(Built in phase 4; test 66 amended to accept only the after-end timesheets the key lists.)*
70. Active CW per month-end from the snapshot = active CW in the CW headcount walk.
71. CW spend in `mart_cw_spend` = billed hours × rate, to the cent, and ties to `bw_timesheet_month`.
72. Workforce walk: Opening + movements = Closing for Employees, CW and Total; a conversion nets to zero in Total.
73. Detection: every injected discrepancy open at a month-end is detected (recall 100% for rule-detectable types); false flags listed and explained.
74. Plan vs actual: actual CW headcount and spend tie to the CW snapshot and spend marts.
75. Identity resolution: every Bridgeway worker and every Keystone CW appears exactly once in the resolution output (matched or unmatched). *(Moved from 69 to phase 7, where the model is built.)*
76. The plan's contingent line is complete: every cost center with CW on a quarter end has a line in every version covering it; spend zero exactly when headcount is; each version within 20% of the actual. *(Built in phase 5.)*
77. Conversions agree across Keystone, recruiting and Bridgeway: closed on the hire date under the same name, the accepted external hire with source *Contingent conversion*, in the month after the last Bridgeway day. *(Built in phase 5; test 68 extended.)*
78. The growth-mix factors (Shapley and sequential) add up to the change in total workforce cost exactly and tie to both snapshots. *(Built in phase 6.)*

---

## 13. Run order

| Phase | Work | Checkpoint |
|---|---|---|
| 0 | Branch `warehouse-release-3`; record release 2 control totals | Regenerated files match; 59 tests pass |
| 1 | Remove part-time (section 11) | Walks reconcile; employee headcount unchanged, FTE = headcount |
| 2 | Source systems: names, raw table shells, lineage doc, data dictionary skeleton | Tests 60–61 |
| 3 | CW simulation: suppliers, workers, orders, revisions, rate card, timesheets (own random stream) | Tests 62–66; population and spend targets |
| 4 | Feed log and Keystone CW history; discrepancy injection; truth table | Tests 67–69 (identity resolution test moves to 75, phase 7) |
| 5 | CW plan line; conversions into employee requisitions | Tests 76–77 (test 74 needs the phase 6 marts); employee hires unchanged except conversions |
| 6 | Marts for case studies 1–3, 5 and 6 (worker type in the walk, CW spend panel, cost bridge drivers, footprint) | Tests 70–72, 74; existing tests pass |
| 7 | Marts for case study 4 | Tests 71, 73, 75 |
| 8 | SQL Server twin, Custom SQL files, DuckDB checker; Mac run | All PASS |
| 9 | Expected values for every dashboard; docs: data dictionary, case study 4, README, control totals | Check tables generated |
| 10 | Tableau: republish #1 and #2 on release 3, build #3, then design and build #6 | Check tables match |

## 14. Still open (none blocks phase 0)

- **Supplier count and names:** about 25 fictional names, generated to sound plausible and match no real firm.
- **Local-currency billing share:** 15% to start.
- **Holiday calendar for billed hours:** a flat country-level allowance first; a public holiday calendar later if useful.
- **Weekly snapshots:** case study 4 starts at month-end grain. A weekly view of the latest quarter can be added if the dashboard needs it, with an eye on Tableau Public extract size.
- **Size:** about 90,000 revisions and about 650,000 timesheet rows, measured in phase 3 against the GitHub 100 MB file limit (timesheets may ship compressed or as a mart-only export).
