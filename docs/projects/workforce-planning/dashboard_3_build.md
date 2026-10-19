# Dashboard #3, Workforce Planning: build guide

The as-built guide for the third Arcadia dashboard, written step by step with the value every step must show. It follows Dashboards #1 and #2: the same 1400 × 850 page, the same rail, KPI band, card background and type ramp (Figma file `ecic7dYoG638uJPVjiQtgg`, Sizing & type page), and the same habits (titles state the finding, "drivers" not "steps", every control tested on a picked period). Method and definitions: [workforce_planning.md](workforce_planning.md). Arcadia Systems is fictional and all data is synthetic.

| Step | What | State |
|---|---|---|
| 1 | Headline question and the five KPI cards, with expected values | Agreed 2026-10-18 |
| 2 | Custom SQL, validated on SQL Server before Tableau | This guide, section 2 |
| 3 | Parameters, calculations and sheets, with the expected output of each | Next |
| 4 | Layout from the Figma replica, actions and the action audit | |
| 5 | Pre-publish checklist, screenshot, README and profile | |

## Decisions (2026-10-18)

| # | Decision | Why |
|---|---|---|
| D1 | **Executive officers excluded** (department `D-901`, the CEO and eight function heads), in every Dashboard #3 source | The same people on every Arcadia dashboard: FY26 year-end employees are **30,005** on #1, #2 and #3 |
| D2 | **Periods are quarter-end pairs inside one fiscal year**: FY, H1, H2, Q1 to Q4, for FY22 to FY26 | The plan is quarterly; there is no monthly plan to compare with |
| D3 | **A Version toggle** (Budget · RF1 · RF2 · RF3). A reforecast plans only the quarters still ahead (RF1 Q2–Q4, RF2 Q3–Q4, RF3 Q4), so plan **and** actual are counted over the quarters the version plans, and the subtitle names them | Plan and actual always cover the same dates |
| D4 | **No choice can lead to an empty page.** A Period, Version or Group option that has no plan for the other two current choices is drawn greyed out and does nothing when clicked. A View pick lands on that view's largest group | You asked for no blank state; see 2.2 |
| D5 | Card 4 is **net-new seats approved while a matching seat stood empty**; the vacancy pool is a chart | It is the finding unique to this case study |
| D6 | **Layout: the map runs the full content height** (668 × 630, as in the Footprint prototype), with three panels stacked beside it: plan vs actual, seat fills, vacancy pool | You chose the prototype layout |

## 1. The question and the five KPI cards

**Headline question:** *Did hiring follow the plan, and which seats did it fill?*

Page title **Workforce Planning**; dynamic subtitle (a statement, not a question): "Whether hiring followed the FY26 Budget at Arcadia Systems, which seats it filled, and which stand empty · Jun 30, 2025 to Jun 30, 2026".

FY26, Budget, Company (all from `custom_sql_wfp_summary.sql`, one row):

| # | Card title | Value | Note | Fields |
|---|---|---|---|---|
| 1 | Year-end employees | **30,005** | −332 vs plan 30,337 · cost $3,407.5M vs $3,446.5M | `actual_/planned_ending_headcount`, `actual_cost_usd_plan_fx`, `planned_cost_usd` |
| 2 | Net-new seats filled | **79.0%** | 2,181 of 2,762 planned | `actual_/planned_net_new` |
| 3 | Backfills | **92.8%** | 4,668 of 5,031 · median 42 days to fill | `actual_/planned_backfills`, `median_time_to_fill_days` |
| 4 | Net-new while a match stood empty | **628** | 28.8% of net-new · $55.4M starting base pay | `reuse_candidate_fills`, `net_new_fills`, `reuse_new_pay_usd_constant` |
| 5 | Contingent workers | **11,941** | −732 vs plan 12,673 · spend $1,238.7M vs $1,313.9M | `actual_/planned_cw_headcount`, `actual_cw_spend_usd_plan_fx`, `planned_cw_spend_usd` |

The same cards on other choices (use them to test the toggle and the period list):

| Choice | Card 1 | Card 2 | Card 3 | Card 4 | Card 5 |
|---|---|---|---|---|---|
| FY26, RF1 (plans Q2–Q4) | 30,005 vs 30,219 | 83.0% (1,532 / 1,845) | 96.5% (3,639 / 3,772) | 453 | 11,941 vs 12,182 |
| FY26, RF2 (plans Q3–Q4) | 30,005 vs 30,142 | 89.4% (981 / 1,097) | 95.4% (2,408 / 2,524) | 300 | 11,941 vs 12,020 |
| FY26, RF3 (plans Q4) | 30,005 vs 30,086 | 92.9% (510 / 549) | 100.4% (1,207 / 1,202) | 165 | 11,941 vs 11,977 |
| FY26 Q3, Budget | 29,618 vs 30,046 | 83.8% (471 / 562) | 88.6% (1,201 / 1,356) | 135 | 11,277 vs 12,201 |
| FY26, Budget, Function Finance | 1,271 vs 1,308 | 68.0% (83 / 122) | 78.7% (181 / 230) | 13 | 370 vs 408 |
| FY26, Budget, Country India | 6,967 vs 7,056 | 74.4% (418 / 562) | 93.9% (1,047 / 1,115) | 191 | 4,883 vs 5,274 |
| FY24, Budget (the restructuring) | 27,208 vs 28,589 | 32.1% (910 / 2,833) | 91.2% (4,105 / 4,503) | 228 | 9,910 vs 10,746 |

**Main panel headline** (FY26, Budget): "FY26: hiring filled 79% of planned net-new seats and 93% of backfills; employees closed 332 below plan". By quarter, net-new actual / planned: Q1 649 / 832, Q2 551 / 744, Q3 471 / 562, Q4 510 / 624.

Why FY24 Budget planned net-new reads 2,833 here and 2,834 in [workforce_planning.md](workforce_planning.md) section 9: one planned net-new seat sat in the Office of the CEO, which D1 removes.

## 2. Custom SQL, validated on SQL Server

### 2.1 The five data sources

| Data source in Tableau | File (`tableau/`) | Rows | Feeds |
|---|---|---:|---|
| **WFP Summary** (new) | `custom_sql_wfp_summary.sql` | 10,080 | KPI band, page and panel headlines, Period / Version / View / Group lists |
| **Plan vs Actual** | `custom_sql_plan_vs_actual.sql` | 29,365 (was 29,415) | Plan vs actual panel (quarters, functions) |
| **Position Fill** | `custom_sql_position_fill.sql` | 30,575 | Map (offices and routes: each fill row carries the seat's new office and its prior office, so both layers come from one source), seat fills panel |
| **Vacancy Pool** | `custom_sql_vacancy_pool.sql` | 62,055 | Vacancy pool panel |
| **Seat Corridors** | `custom_sql_seat_corridors.sql` | 821 | The `CHK Corridors` sheet only |

What changed in the existing four: `WHERE v.department_id <> 'D-901'` (D1). Plan vs Actual loses its 50 executive-officer rows; the other three have none, and the filter states the rule. Seat Corridors has no department column and no officer rows.

**Why a summary source.** The five KPI cards are text drawn as map layers on **one** sheet (the technique from Dashboard #1), and map layers must share a data source. The summary holds every card's numbers at the grain of the rail's choices, so the band is one query of 10,080 rows. It is also what makes D4 possible: there is a row for every fiscal year × period × version × view × group, with `has_plan` telling the rail what to grey out.

### 2.2 How the summary keeps the page from going empty

| Column | Meaning | Used by |
|---|---|---|
| `is_covered` | The version plans at least one quarter of the period (RF2 + H1: no) | Version toggle, Period list |
| `has_plan` | Covered **and** the group has plan rows there (160 planned combinations are groups not yet open: Data & AI Platform before FY25; Portugal and South Korea before FY24; the Philippines in FY22) | Version toggle, Period list, Group list |
| `covered_label`, `eff_from_date` | Which quarters the numbers cover ("Q3–Q4", Dec 31, 2025) | Subtitles |
| `is_view_default` | Each view's largest group: Arcadia Systems, Technology, Engineering, Core Platform Engineering, United States. It has a plan in every period and version | The View list's action |

The rule in step 3: each list's clickable value is `IF [has_plan for the other two choices] THEN <this option> ELSE <the current value> END`, so a greyed option sets the parameter to what it already is (nothing happens) and its tooltip says why ("RF2 plans Q3–Q4 only. Choose Budget or RF1 for H1.").

### 2.3 Run it on the Mac

Nothing in the warehouse changed (the summary reads the existing `rpt` views), so there is no rebuild. Paste the commands one block at a time; no comments inside them (zsh would run them).

**1. Get the branch.**

```bash
cd ~/GitHub/people-analytics-warehouse
git fetch origin
git checkout dashboard-3-workforce-planning
git pull
```

Expected: `Switched to a new branch 'dashboard-3-workforce-planning'` and `branch 'dashboard-3-workforce-planning' set up to track 'origin/dashboard-3-workforce-planning'`, then `Already up to date.`

**2. Check the container is up.**

```bash
docker compose ps
```

Expected: `arcadia-sql` with status `Up ...` (and `(healthy)` if shown). If it is not listed: `docker compose up -d`, wait 20 seconds, run `docker compose ps` again.

**3. Run the validation script.**

```bash
export MSSQL_SA_PASSWORD="$(docker exec arcadia-sql printenv MSSQL_SA_PASSWORD)"
docker exec -it arcadia-sql /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "$MSSQL_SA_PASSWORD" -C -i /repo/sqlserver/14_validate_workforce_planning_dashboard.sql
```

Expected (seconds will differ; the summary takes the longest, about 10 to 30 seconds on the emulated Mac container):

```
Changed database context to 'ArcadiaHR'.
WFP summary Custom SQL returned 10080 rows in 18 seconds
Plan vs actual Custom SQL returned 29365 rows in 1 seconds
Position fill Custom SQL returned 30575 rows in 1 seconds
1. Shape: one row for every choice on the page
   11 rows, every result PASS (summary rows 10080, distinct keys 10080, fiscal years 5, groups 72,
   rows a version plans 7200, rows with a plan 7040, groups not yet open 160, view defaults without a
   plan 0, executive officers 0, plan vs actual rows 29365, position fill rows 30575)
2. Ties (every check expects 0)
   4 rows, every result PASS
3. KPI cards, FY26 (Jun 25 -> Jun 26), Company
   27 rows, every result PASS (the card values in section 1)
4. Period names (pair_name must read exactly as on the rail)
   4 rows, every result PASS (FY26 · Jun 25 → Jun 26, FY26 H1 · Jun 25 → Dec 25, FY26 Q3 · Dec 25 → Mar 26, Q3–Q4)
```

To see only failures, add `| grep -E "FAIL|Msg"` to the end of the command: **no output** means everything passed.

If section 4 shows `?` instead of `·` or `→`, the terminal is not UTF-8 but the data is fine (Tableau reads it correctly); the four checks still say PASS.

**4. Copy the files for Tableau** (the repo's `tableau/` folder is the source):

```bash
mkdir -p "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning"
cp tableau/custom_sql_wfp_summary.sql tableau/custom_sql_plan_vs_actual.sql tableau/custom_sql_position_fill.sql tableau/custom_sql_vacancy_pool.sql tableau/custom_sql_seat_corridors.sql "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning/"
ls "$HOME/Documents/Tableau/Tableau Public/ArcadiaHR/Custom SQL - Release 3/03 Workforce Planning/"
```

Expected: the five file names. (The handoff named this folder `01 Workforce Planning`; if yours has that name, use it in both commands.)

### 2.4 How it was checked before it reached you

| Check | Result |
|---|---|
| `python pipeline/run_pipeline.py` | 80 tests pass, including the new **test 80** (one row per choice, every group in every period, plan actuals = seat fills, groups add up to Company, Company = `mart_plan_vs_actual`, coverage follows the version, view defaults always planned, no executive officers). Run against a deliberately broken copy (a dropped row, a changed count): it caught both |
| `python sqlserver/check_tsql_in_duckdb.py` | The T-SQL summary equals the DuckDB mart `mart_wfp_summary` **row for row (10,080)**, medians and period names included; Plan vs Actual equals the mart without the officers (29,365); `14_validate`: 46 of 46 checks PASS; every other source and script unchanged and matching |
| Existing marts | Not one byte changed (the summary is a new mart beside them) |

Plan actuals equal the seat fills in **every** row of the summary (net-new, backfills, reuse candidates, external + internal), which is what lets card 4 (from fills) sit beside cards 2 and 3 (from the plan).
