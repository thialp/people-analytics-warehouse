# Data Dictionary

Arcadia Systems is fictional and all data is synthetic. History runs from 2021-06-30 to 2026-06-30 (61 month-ends; the dashboards show pairs ending after 2022-06-30, the first year being lead-in). Dates are ISO (`YYYY-MM-DD`). The fiscal year starts July 1 (FY2026 = 2025-07-01 to 2026-06-30).

## Raw tables (`data/raw/`)

Forty-nine tables in eight groups: people and their history, the organization, the pay structure, seats, requisitions and the plan, external reference data, the **contingent workforce** (release 3), the **lineage registry** (release 3) and the **reconciliation operations** (release 4). Every raw table comes from one source system: **Keystone HR**, **Bridgeway VMS**, the integration log between them, **Helix Service Desk**, the warehouse's load log, or public reference data; the map is in [source systems and lineage](source_systems.md) and in the raw table `ref_raw_table_lineage` (test 60). The raw files call the 1–12 ladder **job level**; from staging onward it is called `grade`, the name the published marts and dashboards use.

### People and history

#### dim_worker
One row per worker ever employed (46,980).

| Column | Description |
|---|---|
| `worker_id` | Worker key, e.g. `W100001` |
| `first_name`, `last_name` | Fictional names, drawn from regional name pools |
| `original_hire_date` | First day of employment |
| `termination_date` | Last day worked; empty if still employed |
| `termination_type` | `Voluntary` or `Involuntary`; empty if still employed |
| `worker_type` | Always `Regular Employee` in this dataset |
| `is_executive_officer` | `True` for the CEO and the eight function heads, who are excluded from compensation reporting |
| `work_email` | `first.last@arcadia-systems.example`, numbered on a clash in worker ID order (release 3). Bridgeway names a contingent worker's manager by email, so this is how the warehouse compares managers across the systems |

#### fact_job_history
Effective-dated job assignments (SCD Type 2). A new row starts whenever department, office, job, level, manager or leadership role changes.

| Column | Description |
|---|---|
| `job_record_id` | Record key |
| `worker_id` | → `dim_worker` |
| `effective_start_date` | First day the record applies |
| `effective_end_date` | Last day the record applies (inclusive); empty = current |
| `action_reason` | `Hire`, `Promotion`, `Demotion`, `Transfer`, `Reorganization`, `Succession`, `Location Change`, `Manager Change`, `Became People Manager`, `Returned to Individual Contributor`. When two changes land on the same day, one record carries the higher-ranked reason, in this order |
| `position_id` | The seat held (→ `dim_position`); it changes when the worker moves to another seat (transfer, reorganization, internal move). Test 43 checks every record names the seat the worker holds that day |
| `department_id` | → `dim_department` |
| `location_id` | → `dim_location` |
| `job_profile_id` | → `dim_job_profile`: family + level, e.g. `SWE-L3`, `SWE-M5` (people-manager variant), `EXE-CEO` |
| `job_level` | 1 (Associate) to 12 (Chief Executive Officer); see `dim_job_level` |
| `fte` | Always 1.0: every employee is full-time (release 3 removed part-time; test 23) |
| `manager_worker_id` | Direct manager (→ `dim_worker`). Empty only for the CEO, who reports to the board |
| `is_people_manager` | `True` if the worker has a team to lead |
| `leads_org_unit_id` | The org unit this worker leads (→ `dim_org_unit`): the company for the CEO, a function, sub-function or department for their heads; empty for everyone else |

Reporting rules, checked every month-end by tests 24 to 27: everyone except the CEO has an employed manager; a people manager reports to someone at a higher level and an individual contributor to someone at the same level or higher; apart from org leaders, people report within their own department; every chain ends at the CEO; every org unit has exactly one leader.

#### fact_compensation_history
Effective-dated base pay (SCD Type 2), stated as a **full-time annual rate in local currency**.

| Column | Description |
|---|---|
| `comp_record_id` | Record key; increases in entry order, so a correction always has a higher id than the row it replaces |
| `worker_id` | → `dim_worker` |
| `effective_start_date` / `effective_end_date` | As in job history. The start date is the posting date used for booked FX |
| `action_reason` | `Hire`, `Conversion`, `Tenure Increase`, `Promotion`, `Demotion`, `Market Adjustment`, `Relocation Adjustment`, `International Transfer` |
| `transaction_type` | `Original`, or `Correction` when the row replaces a mistyped row with the same effective date |
| `currency_code` | ISO currency of the pay |
| `base_salary_annual_local` | Annual base salary at 1.0 FTE |

**Source quirks to know about**

- **Corrections.** 1,128 pay records have a second row with the same worker and effective date. The lower-id row holds a mistyped amount (some are off by a factor of 10). Staging keeps the latest row.
- **Conversion date.** Pay history was loaded into the warehouse on 2021-03-01. Workers hired before then have a `Conversion` row starting on that date and no earlier pay history.

#### fact_performance_review
One rating per worker per fiscal year, given on June 30 to everyone employed that day who joined by March 31.

| Column | Description |
|---|---|
| `review_id` | Record key |
| `worker_id`, `fiscal_year`, `review_date` | Who, which year, and the review date (fiscal year-end) |
| `rating` | `Excellent`, `Good` or `Needs Improvement` |
| `bonus_pct` | Bonus as a share of base salary for that rating: 25%, 10% or 5% (→ `ref_performance_bonus`) |

#### fact_bonus_payout
The bonus earned on each review, in local currency.

| Column | Description |
|---|---|
| `bonus_id` | Record key |
| `worker_id`, `fiscal_year` | → `fact_performance_review` |
| `payout_date` | August 31 after the review |
| `currency_code`, `base_salary_annual_local`, `fte` | Pay at the review date |
| `proration_factor` | Months worked in the fiscal year ÷ 12 |
| `bonus_pct` | From the rating |
| `bonus_amount_local` | `base_salary_annual_local × fte × bonus_pct × proration_factor` |
| `payout_status` | `Paid`; `Forfeited` if the worker left before the payout date; `Scheduled` for FY2026, whose payout date is after the data window |

### Organization

#### dim_org_unit
The org design as a tree: the company, 8 functions, 4 sub-functions and 31 departments (44 units).

| Column | Description |
|---|---|
| `org_unit_id` | `ORG-000` (company), `ORG-TEC` (function), `ORG-TEC-ENG` (sub-function) or a department id |
| `org_unit_name`, `org_unit_type` | Name; `Company`, `Function`, `Sub-function` or `Department` |
| `parent_org_unit_id` | The unit above |
| `function` | Function the unit belongs to |
| `leader_title`, `leader_job_level` | The role that leads the unit and its level |

#### dim_department

| Column | Description |
|---|---|
| `department_id` | Department key |
| `department_name` | Department |
| `sub_function`, `function` | Its place in the org design |
| `parent_org_unit_id` | → `dim_org_unit`: the sub-function where the function has several, otherwise the function |
| `cost_center` | Finance cost center |
| `head_job_level` | Level the department head is expected to hold: 9 (VP) for departments of 1,000+, 8 for 300+, otherwise 7 |
| `effective_from_date` | Data & AI Platform (`D-108`) exists from the FY25 reorganization, 2024-11-01 |

#### dim_location
35 offices in 22 countries, every region covered.

| Column | Description |
|---|---|
| `location_id`, `office_name`, `site_type` | Office; Headquarters, Regional Hub, Engineering Center, Operations Center or Office |
| `street_address` | **Fictional** |
| `city`, `state_province`, `postal_code` | Real city and a real postal code for the business district. The UAE has no postal codes, so Dubai's is empty |
| `country_code`, `country_name`, `region`, `currency_code` | Country attributes |
| `latitude`, `longitude` | GeoNames centroid of the postal code (CC BY 4.0) |
| `geo_source` | Where the point comes from; names the two exceptions (Sao Paulo, Dubai) |
| `pay_zone_factor` | Pay differential within the country (San Francisco 1.15, New York 1.12, Seattle 1.10 ... Atlanta 0.95) |
| `opened_date` | Six offices opened during the history: Manila (2022-10), Guadalajara (2023-03), Lisbon (2023-09), Seoul (2024-03), Pune (2024-07) and Vancouver (2025-01) |

#### dim_country
22 countries: `country_code`, `country_name`, `region`, `currency_code` and `pay_index`, Arcadia's pay level for the same job relative to the US (US = 1.00, India = 0.27, Switzerland = 1.12).

### Pay structure

#### dim_job_level
The 12-level ladder: `job_level`, `level_code` (L1–L12), `level_name`, `career_track`, `us_base_salary_usd` (base for a new hire in a US pay-zone-1.00 office: L1 65,000 … L4 125,000 … L7 220,000 … L12 650,000), `range_min_pct` (0.85) and `range_max_pct` (1.35).

#### dim_job_profile
Job family × level (165 profiles): `job_profile_id`, `job_family_code`, `job_family`, `job_title`, `job_level`, `level_name`, `career_track`. Levels 5 and 6 have two profiles each: an individual contributor (`Staff …`, `Principal …`) and a people manager (`Manager, …`, `Senior Manager, …`).

#### ref_job_level_base_salary
Base salary for a new hire by level and country: `job_level`, `country_code`, `currency_code`, `base_salary_local`, `base_salary_usd_at_reference`, `fx_reference_date`. Set as US base × pay index, converted once at the ECB rates of 2022-06-30 and **fixed in local currency** from then on. Hires get this base × the office's pay zone × a small offer variation (±10%).

#### ref_tenure_increase
The raise on each hire anniversary by completed years of service: 1 year 5.0%, 2 years 6.0%, 3 years 5.0%, 4 years 4.5%, 5 years 4.0%, 6–10 years 3.0%, 11+ years 2.0%. Raises stop at the top of the range (135% of the level base).

#### ref_performance_bonus
`rating`, `bonus_pct` and `target_share`: Excellent 25% (20% of people), Good 10% (70%), Needs Improvement 5% (10%).

#### ref_salary_range
Pay ranges in local currency by fiscal year (FY21–FY26), level and country: `range_min`, `range_mid`, `range_max` (85%, 100% and 135% of the midpoint) and `structure_increase_pct`. **Ranges move every July 1** by Arcadia's structure increase (2.5% to 4.0% a year, plus a country adjustment: India +4 points; Brazil, South Africa, Poland and the Philippines +2; Mexico +1.5; Japan and Switzerland −1.5), anchored on the FY23 level bases and rounded to 100 local units. Hire pay, the promotion floor and the tenure and market caps use the range in force. `structure_increase_pct` is empty in FY21, the first year. Test 52 checks each year moves by its increase.

### Seats, requisitions and plan

The position (seat) layer of case study 3. How it is simulated and used: [Workforce Planning](../projects/workforce-planning/workforce_planning.md).

#### dim_position
PID (seat) history (SCD Type 2): a new record whenever a PID changes status, grade, office or department. Release 3.1 adds the contingent workers' PIDs: every contractor holds a PID in Keystone, like an employee. 222,161 records: 99,689 for 33,650 employee PIDs and 122,472 for 31,264 contingent PIDs (`P800001` onward).

| Column | Description |
|---|---|
| `position_record_id`, `position_id` | Record key (`PS…`) and seat key (`P…`) |
| `effective_start_date`, `effective_end_date` | Inclusive; empty = current. Records chain with no gaps (test 41) |
| `change_reason` | `Initial`, `Net-new`, `Filled`, `Vacated`, `Re-levelled with incumbent` (promotion or demotion in place), `Re-levelled for backfill`, `Relocated with incumbent`, `Relocated for backfill`, `Job change with incumbent`, `Reorganization`, `Frozen`, `Unfrozen`, `Requisition cancelled`, `Eliminated` |
| `status` | `Filled`, `Open`, `Frozen` or `Eliminated`. Filled exactly when someone holds the seat (test 44) |
| `department_id`, `cost_center_id`, `location_id`, `job_profile_id`, `job_level`, `fte` | The seat as it stands in that record |
| `created_date`, `created_reason` | When the seat was created and why: `Initial` (held at the start of history), `Net-new` (growth), `Team split` (a new manager seat when a team passes nine). A PID is created when its requisition (or contingent request) is approved, not when it is filled, so new PIDs wait vacant for their first hire |
| `worker_type` | `Employee` or `Contingent` (release 3.1). Staging splits them: `stg_position` keeps employees, `stg_cw_position` contingent |
| `cw_type`, `cw_role_family` | Contingent PIDs only: the worker type and role the PID is for; with department, office and cost center, the key on which a vacant contingent PID is reused. Contingent PIDs have no job profile or level |

Contingent PIDs (`generator/cw_positions.py`): created, or a vacant one reused (45% when one with the same key is waiting), on the service order's approval date; `Filled` for the days Bridgeway holds the assignment, so filled contingent PIDs equal the contingent headcount (test 81); `Open` after it ends, until reused, or closed (`Eliminated`, reason `Closed by position audit`) by the January and July position audit, which closes 30% of those vacant 180 days or more. A worker returning after a lapse goes back to their own PID.

#### fact_position_assignment
Who held which PID: 98,389 assignments, 54,094 employee and 44,295 contingent. A seat never has two incumbents at once (test 42).

| Column | Description |
|---|---|
| `assignment_id` | Assignment key; it is also the `fill_id` of the fill that started it |
| `position_id`, `worker_id` | The seat and the person |
| `start_date`, `end_date` | Inclusive; empty while the person is in the seat |
| `fill_type` | `Initial` (in the seat when history starts), `External Hire`, `Internal Move` or `Contingent Assignment` (`PC…` keys) |
| `requisition_id` | The requisition the fill closed; empty for `Initial`; the Bridgeway service order for a contingent assignment |
| `vacate_reason` | `Voluntary`, `Involuntary` (the person left the company that day) or `Internal Move Out` (they start in another seat the next day); for contractors `Contract ended`, `Ended early` or `Converted to employee`; empty while in the seat (test 47) |
| `worker_type`, `bw_worker_id` | `Employee` or `Contingent`; a contractor's `worker_id` is their Keystone person ID (`W5…`), with the Bridgeway worker ID beside it |

#### fact_requisition
One row per requisition (31,614; the requisitions open at the extract and their PIDs, created the day they were approved, run six months past it at FY26's pace), an accumulating snapshot of its dates.

| Column | Description |
|---|---|
| `requisition_id`, `position_id` | Requisition and the seat it fills |
| `req_type` | `Backfill` (the seat had an incumbent) or `Net-new` |
| `opened_date`, `approved_date`, `target_start_date`, `filled_date`, `cancelled_date` | In order (test 48). Approval takes 0 to 14 days, and 8% are approved 30 to 75 days late; an approved requisition still open after 210 days is cancelled. Release 5: time to fill varies by function (Technology and Legal & Compliance 15% slower, Operations 15% faster) and graduate season (levels 1 and 2, 25% faster in their country's season); only approval dates move, never fills, and a backfill is never approved more than 14 days before the last day of the person who left (test 91) |
| `status` | `Filled`, `Open` or `Cancelled` |
| `department_id`, `cost_center_id`, `location_id`, `job_profile_id`, `job_level` | The seat when the requisition opened |
| `hiring_manager_id` | The seat's manager (→ `dim_worker`) |
| `filled_by_worker_id`, `fill_source` | Who filled it, `External` or `Internal` |

#### dim_candidate
One row per applicant per requisition (188,982): `candidate_id`, `requisition_id`, `is_internal`, `candidate_source` (Job board, Referral, Career site, Agency, Sourced, Internal, or Contingent conversion: a contingent worker hired when their engagement ended, release 3), `worker_id` (filled only for the person hired) and `final_status` (`Accepted`, `Rejected`, `Withdrawn`, `Declined`, or `In process` on a requisition still open). A filled requisition has exactly one accepted applicant, the person who filled the seat (test 50).

#### fact_candidate_stage_event
One row per applicant per stage reached (531,691): `candidate_event_id`, `candidate_id`, `stage` (`Applied`, `Screen`, `Interview`, `Offer`, then `Accepted`, `Declined`, `Rejected` or `Withdrawn`), `stage_order`, `stage_date`. Stages run in order between approval and the fill or cancellation. Source and internal flag sit on `dim_candidate`, not on every stage.

#### dim_cost_center
Department × country (630): `cost_center_id` (`CC-1010-US`), `cost_center_name` (`Core Platform Engineering - United States`), `department_id`, `department_cost_center` (the department's own code, `CC-1010`), `country_code`, `function`. Every seat record and requisition carries the cost center of its department and its office's country (test 51).

#### fact_workforce_plan
The workforce plan, one row per plan version × cost center × fiscal quarter (31,935: 29,415 for FY22 to FY26 and 2,520 for the forward budget). Versions are never overwritten (test 49). Since release 3 it carries a **contingent line** beside the employee plan; 615 rows exist only for that line (cost centers with contingent workers and no employee plan that year), with zeros on the employee side.

| Column | Description |
|---|---|
| `plan_version`, `version_type`, `version_date` | `FY26 Budget` (dated May 15 before the year), `FY26 RF1` (Oct 15), `RF2` (Jan 15), `RF3` (Apr 15). A reforecast covers only the quarters still ahead |
| `fiscal_year`, `fiscal_quarter`, `quarter_end_date` | The quarter planned |
| `cost_center_id` | → `dim_cost_center` |
| `planned_ending_headcount`, `planned_ending_fte` | Planned level at the quarter-end |
| `planned_net_new`, `planned_backfills` | Planned fills in the quarter |
| `planned_cost_usd`, `plan_fx_rate_date` | Planned quarter-end loaded run-rate, in USD at the FX of the version date |
| `planned_cw_headcount` | Planned contingent workers at the quarter-end (release 3) |
| `planned_cw_spend_usd` | Planned contingent spend: the annualized bill run-rate at the quarter-end (hourly rate × contracted hours × 52, or monthly rate × 12), in USD at the FX of the version date (release 3). Test 76 checks the line is complete |

The generator writes each version around what happened, with an error that shrinks from the budget to RF3; the FY24 budget predates the restructuring. The contingent line is looser (budgets run about 4% above the year-end contingent headcount) and has its own random stream, so no employee plan number moved when it was added. See [Workforce Planning, section 7](../projects/workforce-planning/workforce_planning.md#7-plan-versus-actual).

**The forward budget (release 5).** The year after the report date has one version, its Budget (`FY27 Budget`, dated 2026-05-15, before the report date): four quarters for each of the 630 cost centers active in FY26. Nothing after the report date is simulated, so it is a projection, not a plan written around what happened: net-new from the same quarter of FY26 scaled to the planned growth (`FORWARD_BUDGET_NET_GROWTH`, 5%), backfills by headcount, headcount grown from Jun 30, 2026, with the budget's planning error; the contingent line grows each cost center's Jun 30, 2026 contingent headcount by `FORWARD_BUDGET_CW_GROWTH` (6%). It is written on its own random streams after every historic version, so FY22 to FY26 are unchanged, and it never reaches `mart_plan_vs_actual`, which joins plans to quarters that happened (test 90).

### External reference data

#### ref_fx_rate_daily
Every ECB publication day from 2021-01-04 to 2026-09-14 for the 17 currencies: `currency_code`, `rate_date`, `usd_per_local`, `source`. Rates are the ECB euro reference rates crossed into USD (`USD per EUR ÷ currency per EUR`); the UAE dirham uses its USD peg (3.6725). Lookups on other days take the latest rate on or before the date.

#### ref_fx_rate_monthly
The rate in effect on each month-end (the latest ECB rate on or before it): `currency_code`, `rate_date`, `usd_per_local`.

#### ref_fx_rate_constant
One rate per currency for constant-currency reporting: `rate_set` (`Latest close (2026-06-30)`), `rate_date`, `currency_code`, `usd_per_local`.

#### ref_fringe_rate
Employer cost on top of base salary, by country and calendar year, built from public sources (method in [organization and pay model](../company/organization_and_pay_model.md#fringe-rates)).

| Column | Description |
|---|---|
| `country_code`, `year`, `effective_start_date`, `effective_end_date` | Rates change on January 1 |
| `social_contribution_rate` | Employer social security and payroll taxes |
| `retirement_severance_rate` | Mandatory pension, provident, severance or gratuity funding outside social security |
| `statutory_pay_rate` | Pay the law adds beyond 12 monthly salaries (13th salary, year-end bonus, vacation premium) |
| `employer_benefits_rate` | Employer health and retirement benefits; US only |
| `fringe_rate` | The sum of the four |
| `reference_salary_local` | Arcadia's L4 base in that country: the salary where contribution ceilings are tested |
| `is_estimate` | `True` for 2026 rows carried forward from 2025 where the OECD has not published 2026 yet, and for every 2021 row (history before the 2022 research reuses each country's 2022 inputs) |
| `method_note` | How the row was built |

#### ref_fringe_source
One row per country, year, component and source document: `country_code`, `year`, `component`, `source_id`, `source_title`, `source_url`. Test 28 checks that every non-zero component has at least one.

### Contingent workforce (release 3)

The contingent workforce comes from two systems. **Bridgeway VMS** (`bw_`) is the source of truth for who is a contingent worker, on which terms and at what rate; **Keystone HR** (`ks_`) holds the HR profile managers see; the **integration log** (`feed_`) records what travelled between them. How the systems relate, and what flows on the feed: [source systems and lineage](source_systems.md). How the program is simulated: [Bridgeway simulation](../projects/contingent-workforce/bridgeway_simulation.md).

**The extract.** Bridgeway is extracted as of **2026-06-30**, like the rest of the warehouse: no revision, approval or closure dated later is in it, but orders opened by then that start in July 2026 are (approved, or still pending approval). Workers whose last assignment ended before **2020-07-01** are archived in Bridgeway and not extracted.

> **Release 3 status:** Bridgeway (phase 3), Keystone, the feed and the answer key (phase 4) are filled. How Keystone and the feed are simulated, and the discrepancy catalogue: [Keystone and the feed](../projects/contingent-workforce/keystone_feed.md). Columns are the contract test 61 enforces.
>
> **Seeded on purpose.** The data carries the disagreements real programs have: between the two systems, and inside Bridgeway itself (orders closed late or never, time billed after the last day, a renewal submitted as a new worker). Every one is in the answer key, `gen_cw_discrepancy_truth`.

#### bw_supplier
Suppliers in Bridgeway VMS (23, all fictional). One stopped taking new orders in June 2022 (`is_active` false).

| Column | Type | Description |
|---|---|---|
| `supplier_id` | VARCHAR | Supplier key, e.g. SUP-014 |
| `supplier_name` | VARCHAR | Fictional supplier name |
| `cw_types_offered` | VARCHAR | CW types the supplier provides, semicolon separated: Contractor, Consultant, BPO |
| `hq_country_code` | VARCHAR | Country of the supplier's head office |
| `onboarded_date` | DATE | First day the supplier could take service orders |
| `is_active` | BOOLEAN | False once Arcadia stopped using the supplier |

#### bw_rate_card
Target bill rate and band per fiscal year (FY14 to FY27), country, CW type, role family and seniority, in USD. Moves every July 1 by a market index (3% a year, plus up to 2 points in India, Brazil, Mexico and the Philippines). An order keeps its rate until a renegotiated extension or a renewal.

| Column | Type | Description |
|---|---|---|
| `rate_card_id` | VARCHAR | Rate card line key |
| `fiscal_year` | INTEGER | Arcadia fiscal year the line applies to (July to June) |
| `country_code` | VARCHAR | Country where the work is done |
| `cw_type` | VARCHAR | Contractor, Consultant or BPO |
| `role_family` | VARCHAR | Development, QA, Data, Analyst, Project Delivery, Architecture, Design, Operations; BPO: Security, Facilities, Service Desk, Customer Support |
| `seniority` | VARCHAR | Junior, Mid, Senior or Lead |
| `rate_type` | VARCHAR | Hourly, or Monthly for BPO |
| `billing_currency` | VARCHAR | USD: the card is kept in USD; an order billing in local currency converts the target at the approval date's ECB rate |
| `rate_low` | DECIMAL | Bottom of the band |
| `rate_target` | DECIMAL | Target rate |
| `rate_high` | DECIMAL | Top of the band |

#### bw_contingent_worker
Workers as Bridgeway knows them. **No Keystone person ID**: the link is stored on the Keystone side. `original_start_date` is empty for a worker who was withdrawn or rejected before starting.

| Column | Type | Description |
|---|---|---|
| `bw_worker_id` | VARCHAR | Bridgeway worker key, e.g. BW00012345. Bridgeway never stores the Keystone person ID |
| `first_name` | VARCHAR | Fictional |
| `last_name` | VARCHAR | Fictional |
| `email` | VARCHAR | Work email issued for the engagement (fictional domain) |
| `supplier_id` | VARCHAR | → bw_supplier |
| `cw_type` | VARCHAR | Contractor, Consultant or BPO |
| `original_start_date` | DATE | First day of the first engagement under this Bridgeway ID |
| `created_date` | DATE | Day the supplier submitted the worker |

#### bw_service_order
One row per service order (accumulating snapshot). A renewal is a new order naming the one it renews. `final_status` is the status of the current revision on the extract date.

| Column | Type | Description |
|---|---|---|
| `service_order_id` | VARCHAR | Service order key, e.g. SO0012345 |
| `bw_worker_id` | VARCHAR | → bw_contingent_worker |
| `supplier_id` | VARCHAR | → bw_supplier |
| `order_type` | VARCHAR | New engagement, or Renewal of an earlier order for the same worker |
| `renews_service_order_id` | VARCHAR | The order this one renews; empty for a new engagement |
| `opened_date` | DATE | Manager raised the request |
| `submitted_date` | DATE | Supplier submitted the worker |
| `approved_date` | DATE | Order approved; empty if never approved |
| `final_status` | VARCHAR | Status of the current revision at the extract date |

#### bw_service_order_revision
Every change to an order is a new revision, effective-dated, one per day at most, with exactly one current per order (test 62). The rate changes only on a `Rate change` revision (test 65); an ended order gets a `Closure` revision with `status` = Closed a few days after its last day. Whether someone is working on a date comes from the assignment dates on the revision in effect that day.

| Column | Type | Description |
|---|---|---|
| `revision_id` | VARCHAR | Revision key |
| `service_order_id` | VARCHAR | → bw_service_order |
| `revision_no` | INTEGER | 0 for the original order, then 1, 2, ... |
| `revision_reason` | VARCHAR | Original or Renewal (revision 0), Extension, Rate change, Early end, Cost center change, Manager change, Office change, Closure |
| `effective_start_date` | DATE | First day the revision is in effect |
| `effective_end_date` | DATE | Last day in effect (inclusive); empty for the current revision |
| `is_current` | BOOLEAN | True on exactly one revision per order |
| `status` | VARCHAR | Pending Approval, Approved, Closed, Withdrawn, Rejected. Whether the worker is working on a date comes from the assignment dates, not the status |
| `assignment_start_date` | DATE | First working day of the assignment |
| `assignment_end_date` | DATE | Last working day of the assignment as this revision states it |
| `closed_date` | DATE | Day the order was closed in Bridgeway; empty while open |
| `role_family` | VARCHAR | See bw_rate_card |
| `seniority` | VARCHAR | Junior, Mid, Senior or Lead |
| `job_title` | VARCHAR | Title on the order |
| `cost_center_code` | VARCHAR | Cost center as typed on the order (text, not validated against Keystone) |
| `hiring_manager_email` | VARCHAR | Arcadia manager who owns the order |
| `office_code` | VARCHAR | Arcadia office where the work is done |
| `bill_rate` | DECIMAL | Rate in billing currency: per hour, or per month for BPO. Applies from the revision's effective date |
| `rate_type` | VARCHAR | Hourly or Monthly |
| `billing_currency` | VARCHAR | ISO currency code |
| `hours_per_week` | DECIMAL | Contracted hours; empty for monthly BPO orders |

#### bw_timesheet_month
Billed time per worker, order, month and rate, from June 2021 (the start of the warehouse history). Hourly orders bill weekdays × 8 less time off; BPO orders bill the share of the month worked. `billed_amount_local` = `billed_units × bill_rate`, to the cent (test 66). 139 timesheets bill a month after the worker's last day: seeded discrepancy CW11, each listed in the answer key.

| Column | Type | Description |
|---|---|---|
| `timesheet_id` | VARCHAR | Timesheet key: one per worker x service order x month x rate (a month whose rate changed has two) |
| `bw_worker_id` | VARCHAR | → bw_contingent_worker |
| `service_order_id` | VARCHAR | → bw_service_order |
| `month_end_date` | DATE | Month billed |
| `billed_hours` | DECIMAL | Approved hours; 0 for monthly BPO orders |
| `billed_units` | DECIMAL | Hours for hourly orders; months (1.0, or a fraction in start and end months) for BPO |
| `bill_rate` | DECIMAL | Rate applied |
| `billing_currency` | VARCHAR | ISO currency code |
| `billed_amount_local` | DECIMAL | billed_units x bill_rate |

#### ks_contingent_worker
The Keystone HR person record of each contingent worker, SCD Type 2, one version per day. Written by the feed from Bridgeway (`change_source` Feed), by Keystone itself when it inactivates a worker the day after the contract end it holds (System), and by hand (HR Ops, Manager). Contingent workers take person IDs from W500001, in the order Keystone created them; employees run from W100001, so the two never collide (test 68). The stored `bw_worker_id` is how the warehouse links Keystone to Bridgeway; it is blank or mistyped on a few records (discrepancy CW06), and a few records have no Bridgeway worker at all (CW09). When a contingent worker is hired as an employee, HR closes the record on the hire date as *Converted to employee*, naming the new employee in `converted_to_worker_id` (a new person, a new ID; test 77).

| Column | Type | Description |
|---|---|---|
| `ks_record_id` | VARCHAR | Record key |
| `person_id` | VARCHAR | Keystone person ID, the same W... key space as employees |
| `bw_worker_id` | VARCHAR | Bridgeway worker ID as Keystone stored it from the feed; blank when a load dropped it or a record was created by hand without one, mistyped when typed by hand |
| `effective_start_date` | DATE | First day the version applies |
| `effective_end_date` | DATE | Last day (inclusive); empty for the current version |
| `change_source` | VARCHAR | Feed, HR Ops, Manager, or System (Keystone inactivating the worker the day after the contract end date it holds) |
| `feed_event_id` | VARCHAR | → feed_bridgeway_keystone_event when change_source = Feed |
| `first_name` | VARCHAR | As Keystone holds it |
| `last_name` | VARCHAR | As Keystone holds it |
| `cw_type` | VARCHAR | Contractor, Consultant or BPO |
| `supplier_name` | VARCHAR | Free text: exact as fed, or as typed by hand; Keystone has no supplier table |
| `status` | VARCHAR | Active or Inactive |
| `contract_start_date` | DATE | First day of the engagement as Keystone knows it; renewals and extensions move the end, never the start |
| `contract_end_date` | DATE | As Keystone knows it; Keystone inactivates the worker the day after |
| `inactive_reason` | VARCHAR | Contract ended, Ended early, Manual, or Converted to employee; empty while active |
| `converted_to_worker_id` | VARCHAR | The employee the worker became (→ dim_worker) when inactive_reason is Converted to employee: a new person, a new ID |
| `department_id` | VARCHAR | → dim_department |
| `cost_center_id` | VARCHAR | → dim_cost_center |
| `location_id` | VARCHAR | → dim_location |
| `manager_worker_id` | VARCHAR | Arcadia employee the worker reports to (→ dim_worker) |

#### feed_bridgeway_keystone_event
Every change Bridgeway sent to Keystone: one event per revision Keystone cares about, with its outcome. Events for one worker are applied first in, first out, so a late event holds up the ones behind it (test 67). The payload is the revision itself (`revision_id`).

| Column | Type | Description |
|---|---|---|
| `feed_event_id` | VARCHAR | Event key |
| `revision_id` | VARCHAR | → bw_service_order_revision that caused the event |
| `bw_worker_id` | VARCHAR | → bw_contingent_worker |
| `event_type` | VARCHAR | New Worker, Renewal, Extension, Early End or Attribute Change. Rates and closures are not sent: Keystone holds neither |
| `sent_date` | DATE | Day Bridgeway sent the change: the revision's effective start |
| `applied_date` | DATE | Day Keystone applied it; empty if it failed or is still queued |
| `outcome` | VARCHAR | Applied (within 2 days), Applied Late (3 days or more), Partly Applied (created without the Bridgeway ID), Failed, or Queued on the extract date |
| `error_text` | VARCHAR | Integration message for failures and partial loads |

#### gen_cw_discrepancy_truth
**The answer key. A test fixture, not a business source** (system `GEN`). Every discrepancy the generator seeded, with its cause and the days it was true: one row per cause and continuous period. The warehouse detects discrepancies from Bridgeway, Keystone and the feed alone; this table only scores what it finds (case study 4). A Keystone-side discrepancy counts only on days when either system shows the worker working. How it is built: [Keystone and the feed](../projects/contingent-workforce/keystone_feed.md#the-answer-key).

| Column | Type | Description |
|---|---|---|
| `discrepancy_id` | VARCHAR | Answer key row |
| `discrepancy_code` | VARCHAR | → ref_cw_discrepancy_type: what the systems show |
| `root_cause_code` | VARCHAR | → ref_cw_discrepancy_type: why (differs when a broken link or a missing record made a later change fail) |
| `bw_worker_id` | VARCHAR | The Bridgeway worker it is about; empty for a Keystone-only worker |
| `person_id` | VARCHAR | The Keystone person involved; empty if Keystone has no record |
| `service_order_id` | VARCHAR | The order involved, when there is one |
| `feed_event_id` | VARCHAR | The feed event involved, when there is one |
| `timesheet_id` | VARCHAR | The timesheet involved (CW11) |
| `fields_affected` | VARCHAR | What disagrees, semicolon separated |
| `start_date` | DATE | First day it is true |
| `end_date` | DATE | Last day it is true; empty if still open on the extract date |
| `resolution` | VARCHAR | How it ended, or Open at extract |
| `detail` | VARCHAR | The facts behind it, in a sentence |

#### ref_cw_discrepancy_type
The 13 discrepancy types, CW00 to CW12, named after what happened in the systems (warehouse metadata).

| Column | Type | Description |
|---|---|---|
| `discrepancy_code` | VARCHAR | CW00 to CW12 |
| `discrepancy_name` | VARCHAR | Named after what happened in the systems |
| `what_happened` | VARCHAR | The event behind it |
| `what_a_manager_sees` | VARCHAR | What someone looking only at Keystone sees |
| `who_can_fix_it` | VARCHAR | The team that can correct the source; the warehouse only flags |
| `severity` | VARCHAR | Expected, Data hygiene, Cost risk, Access risk or Compliance risk |

### Report calendar (release 5)

Written by [`generator/report_calendar.py`](../../generator/report_calendar.py) from one setting, the report as-of date (`LAST_SNAPSHOT`). Dashboards read every date and fiscal-year label from these two tables and store offsets, not years, in their parameters, so moving the as-of date a year rolls every page forward without editing a calculation (test 89).

| Table | Grain | Columns |
|---|---|---|
| `ref_report_calendar` | one row | `report_as_of_date` (2026-06-30), `report_as_of_label` (Jun 30, 2026), `current_fiscal_year` and `_label` (FY26), `forward_fiscal_year` and `_label` (FY27), `history_first_fiscal_year` and `_label` (FY22), `history_start_date`, `forward_start_date`, `forward_end_date`, `forward_period_label` (Jul 2026 to Jun 2027), `forward_budget_version` (FY27 Budget), `forward_budget_date` |
| `ref_report_quarter` | fiscal quarter in the window (24: five history years and the forward year) | `fiscal_year`, `fiscal_year_label`, `fiscal_quarter`, `quarter_label` (FY27 Q1), `quarter_months_label` (Jul - Sep 26, ASCII), `quarter_start_date`, `quarter_end_date`, `fy_offset` (0 current, +1 forward), `quarter_offset` (0 = the quarter ending on the as-of date, -19 to 4), `is_forward` |

### Lineage registry (release 3)

Written by [`generator/source_systems.py`](../../generator/source_systems.py) with the data, so the warehouse documents and tests its own lineage.

| Table | Grain | Columns |
|---|---|---|
| `ref_source_system` | source system (6) | `system_code`, `system_name`, `system_type`, `record_of`, `used_by`, `extract` |
| `ref_raw_table_lineage` | raw table (40) | `table_name`, `system_code`, `module`, `grain`, `history_type`, `added_in_release` |
| `ref_raw_column` | release 3 raw table × column | `table_name`, `column_order`, `column_name`, `data_type`, `description` |

### Reconciliation operations (release 4)

Case study 4's month-end close view needs times, Keystone's job data, the warehouse's own load log and the tickets people raise. All new tables, each from its own random stream: no release 1 to 3 row changed. How they are used: [release 4 plan](../projects/contingent-workforce/release_4_plan.md).

#### feed_event_delivery
The hour each feed change was sent (the hourly batch that picked it up) and applied, GMT: one row per row of `feed_bridgeway_keystone_event`, on the same days (test 88).

| Column | Type | Description |
|---|---|---|
| `feed_event_id` | VARCHAR | → feed_bridgeway_keystone_event |
| `sent_at` | TIMESTAMP | GMT hour of the hourly batch that sent the change; on sent_date |
| `applied_at` | TIMESTAMP | GMT hour Keystone applied it, on applied_date; empty if it failed or is still queued |

#### ks_contingent_worker_audit
When each Keystone contingent version was written, GMT, and by whom: the feed at the hour it applied, Keystone's nightly job at 00:05, a manager in their office's working hours, or HR Operations (Bangalore).

| Column | Type | Description |
|---|---|---|
| `ks_record_id` | VARCHAR | → ks_contingent_worker |
| `changed_at` | TIMESTAMP | GMT time the version was written, on its effective start date |
| `changed_by` | VARCHAR | Integration, Keystone nightly job, Manager or HR Operations |

#### ks_cw_job
Keystone job data (SCD Type 2): which PID each contingent job record (EMPLID × record number) holds. It follows the PID ledger (`fact_position_assignment`), with two seeded imperfections fixed by HR Ops on the day they notice, never backdated: an old record left active on a return (two active PID records, F07) and a record ended late or never (PID still filled after the end date, F06).

| Column | Type | Description |
|---|---|---|
| `job_record_id` | VARCHAR | Row key |
| `person_id` | VARCHAR | EMPLID: the Keystone person (→ ks_contingent_worker) |
| `empl_rcd` | INTEGER | Job record number of the person: 0 for the first PID, 1 for the next, ... |
| `position_id` | VARCHAR | PID the job holds (→ dim_position) |
| `effective_start_date` | DATE | First day the row applies |
| `effective_end_date` | DATE | Last day (inclusive); empty for the current row |
| `job_status` | VARCHAR | Active or Terminated |
| `action` | VARCHAR | Assignment start, Return or Assignment end |
| `change_source` | VARCHAR | Feed, or HR Ops for an end entered by hand late |
| `assignment_id` | VARCHAR | → fact_position_assignment: the assignment the row was written for |

#### gen_cw_job_defect
**The answer key for Keystone job data. A test fixture, not a business source** (system `GEN`): every period a person holds two active job records or one record on a PID the ledger shows they left, computed by the generator from the rows themselves. Only test 82 reads it.

| Column | Type | Description |
|---|---|---|
| `defect_id` | VARCHAR | Answer key row |
| `flag_code` | VARCHAR | F07 two active PID records; F06 PID still filled after the end date |
| `person_id` | VARCHAR | EMPLID |
| `position_id` | VARCHAR | The PID involved (the lower one for F07) |
| `start_date` | DATE | First day it is true |
| `end_date` | DATE | Last day it is true; empty if still open on the extract date |
| `origin` | VARCHAR | Seeded (a job end entered late or never) or PID ledger (the ledger itself overlaps) |
| `resolution` | VARCHAR | Ended, or Open at extract |
| `detail` | VARCHAR | The facts behind it, in a sentence |

#### etl_load_run
The warehouse's own load log (system `ETL`): every scheduled read of Bridgeway (00:00 GMT), Keystone (about 00:20, after Bridgeway) and Helix (00:00 and 12:00), Jun 1, 2021 to Jul 1, 2026. A failed run reads nothing and the warehouse keeps that source's last good load. Three close runs had an outage on purpose: Bridgeway at the Sep 2023 close, Keystone at the Dec 2024 close (three nights), Helix at the Mar 2026 close.

| Column | Type | Description |
|---|---|---|
| `run_id` | VARCHAR | Run key |
| `source_system` | VARCHAR | BW, KS or HLX (→ ref_source_system) |
| `scheduled_at` | TIMESTAMP | GMT: Bridgeway 00:00, Keystone 00:20 (after Bridgeway), Helix 00:00 and 12:00 |
| `started_at` | TIMESTAMP | GMT |
| `finished_at` | TIMESTAMP | GMT |
| `status` | VARCHAR | Succeeded, Late (started more than an hour after schedule) or Failed (read nothing) |
| `rows_read` | INTEGER | Rows in the extract; empty when the run failed |
| `error_text` | VARCHAR | Why a run failed |

#### itsm_ticket
Helix Service Desk tickets (system `HLX`, fictional), as the last read holds them. Contingent worker tickets only so far; the design is generic. 2,967 tickets from January 2021.

| Column | Type | Description |
|---|---|---|
| `ticket_number` | VARCHAR | HLX-100001 upward, in the order tickets were opened |
| `title` | VARCHAR | Category title and the subject (ID, or name, or nothing) |
| `short_description` | VARCHAR | What the person who raised it wrote |
| `category_code` | VARCHAR | → ref_ticket_category |
| `priority` | VARCHAR | P1 to P4 |
| `assignment_group` | VARCHAR | Group working it now: Vendor Management, HR Operations or Data Engineering |
| `opened_at` | TIMESTAMP | GMT |
| `resolved_at` | TIMESTAMP | GMT of the current resolution; empty while open or after a reopen |
| `closed_at` | TIMESTAMP | GMT; Helix closes a resolved ticket after 3 days |
| `close_code` | VARCHAR | Fixed in source, No longer reproducible, Credit requested from supplier, Source fixed; next run reloads |

#### itsm_ticket_event
Every state change of every ticket. The state at any moment is the last event at or before it, which is how a close is replayed (test 85).

| Column | Type | Description |
|---|---|---|
| `ticket_number` | VARCHAR | → itsm_ticket |
| `event_at` | TIMESTAMP | GMT |
| `from_state` | VARCHAR | Empty for the opening event |
| `to_state` | VARCHAR | New, In progress, Pending, Resolved, Reopened or Closed (a reassignment keeps the state) |
| `actor_group` | VARCHAR | Group that made the change; Helix for automatic closes |
| `note` | VARCHAR | What happened |

#### itsm_ticket_link
What each ticket is about, as the person who raised it entered it: 7 in 10 carry the IDs, 2 in 10 only the name in the description, 1 in 10 nothing.

| Column | Type | Description |
|---|---|---|
| `ticket_number` | VARCHAR | → itsm_ticket |
| `subject_type` | VARCHAR | Contingent worker or Data load (later: Employee, Position) |
| `subject_id` | VARCHAR | Bridgeway worker ID, or the load run ID; empty when not entered |
| `secondary_id` | VARCHAR | Keystone EMPLID, when entered |
| `link_quality` | VARCHAR | ID field, Name in text (the name is in the description) or None |

#### ref_ticket_category
Helix ticket categories: one per reconciliation flag (F01 to F09) and two for the system feed.

| Column | Type | Description |
|---|---|---|
| `category_code` | VARCHAR | Category key |
| `category_name` | VARCHAR | Name |
| `subject_type` | VARCHAR | What a ticket of this category is about |
| `default_group` | VARCHAR | Group it is assigned to |
| `flag_code` | VARCHAR | The reconciliation flag it fixes, F01 to F09; empty for the system feed categories |
| `risk` | VARCHAR | The risk the flag creates |
| `priority` | VARCHAR | Default priority |
| `title_template` | VARCHAR | Ticket title before the subject |

## Marts (`data/marts/`)

Pay measures in the two cost marts are **annualized run-rates at the month-end**, in USD. Executive officers are excluded.

| Measure | Definition |
|---|---|
| `base_usd_nominal` | Base salary × FTE, at the month-end's ECB rate |
| `base_usd_constant` | Base salary × FTE, at the constant rate set (2026-06-30) |
| `loaded_usd_nominal` | Base × (1 + fringe rate), month-end FX |
| `loaded_usd_constant` | Base × (1 + fringe rate), constant FX |

### mart_workforce_cost_bridge
Grain: **month-end × department × worker type × driver.** For each department, worker type and month, Opening + all drivers = Closing. Since release 3 it explains total workforce cost: employees' loaded pay plus contingent workers' annualized bill run-rate (no fringe, so the same value in base and loaded). Contingent drivers and the Shapley growth mix: [methodology](../projects/workforce-cost-bridge/methodology.md#release-3-total-workforce-cost-and-the-growth-mix).

| Column | Description |
|---|---|
| `month_end_date` / `prior_month_end_date` | The month being explained, and the month-end it starts from |
| `fiscal_year`, `fiscal_quarter_label`, `fiscal_period` | Fiscal calendar, e.g. `FY26 Q2`, `FY26 P06` |
| `department_id`, `department_name`, `sub_function`, `function_name`, `cost_center` | Department the line is attributed to |
| `worker_type` | Employee or Contingent (release 3) |
| `driver_order` | 1 to 13, for sorting a waterfall; contingent drivers share their employee counterpart's number (2 Contingent Starts, 3 Contingent Ends, 8 Contingent Rate Changes); 10 is Conversions (once FTE Changes) |
| `driver` | Opening Run-Rate, Hires, Terminations, Transfers In, Transfers Out, Promotions, Demotions, Tenure & Market Adjustments, International Mobility, Conversions, Fringe Rate Changes, FX Rate Changes, Closing Run-Rate; for contingent workers Contingent Starts, Contingent Ends, Contingent Rate Changes. An employee hired from the contingent workforce is in Conversions, not Hires |
| `driver_group` | Balance, Headcount Movement, Pay Rate, Workforce Mix, Fringe & FX |
| `worker_count` | Workers contributing to the line |
| `headcount` | Signed headcount change; for Opening and Closing, the headcount itself |
| `fte` | Signed FTE change; for Opening and Closing, the FTE itself |
| `base_usd_*`, `loaded_usd_*` | Signed dollar effect of the driver |

**Walking across several months:** take Opening from the first month, Closing from the last month, and sum every other driver across the months in between. Test 08 guarantees the months chain together.

### mart_compensation_walk
Grain: **date pair × view × group × walk step × movement reason.** For any two month-ends on the grid (Month over Month, Quarter over Quarter, Year over Year and Fiscal Year to Date pairs ending after 2022-06-30: 88 pairs) and every group in six views (Company, Function, Sub-function, Department, Office, Country): Opening + Hires + Exits + Transfers In/Out + Promotions + Demotions + Tenure Increases + Market Adjustments + Same-Country Transfer Adjustments + International Transfer Adjustments + Fringe Rate Changes + FX Translation = Closing, in headcount, FTE and the four dollar measures, as totals (`base_usd_*`, `loaded_usd_*`), as an average walk per FTE (`avg_*`) and as a percent walk (`pct_*`). Filter to one `view_name` and one date pair. Every row also carries `report_start_date` and `report_as_of_date` (the data window). Same columns as the Tableau Custom SQL `tableau/custom_sql_compensation_walk.sql`.

Full field reference, rules and worked examples: [`compensation_walk.md`](../projects/compensation-walk/compensation_walk.md).

### mart_workforce_cost_snapshot
Grain: **month-end × department × country × grade × job family.**

| Column | Description |
|---|---|
| `month_end_date`, `fiscal_year`, `fiscal_quarter_label`, `fiscal_period`, `is_fiscal_year_end` | Fiscal calendar |
| `department_id`, `department_name`, `sub_function`, `function_name` | Organization |
| `country_code`, `country_name`, `region`, `currency_code` | Where the work happens and the pay currency |
| `grade`, `grade_level`, `career_track`, `job_family` | Job |
| `headcount`, `fte` | Workforce size |
| `base_usd_*`, `loaded_usd_*` | Run-rate pay |
| `range_mid_usd_constant` | Sum of range midpoints × FTE at constant FX. Compa-ratio = `SUM(base_usd_constant) / SUM(range_mid_usd_constant)` |

### mart_headcount_fte_walk
Grain: **month-end × worker type × department × country × job family × grade × movement category × movement reason.** For every worker type, slice and month, Opening + every movement = Closing, in headcount and FTE (test 13); Employees, Contingent and the Total each close every month, and a conversion never moves the Total (test 72). Codes only: names come from the five `mart_dim_*` files below, which Tableau relates on matching column names.

| Column | Description |
|---|---|
| `month_end_date` | The month being walked; → `mart_dim_month` |
| `worker_type` | Employee (Keystone HR) or Contingent (Bridgeway VMS, as held at each month-end; release 3) |
| `department_id` | → `mart_dim_department` |
| `country_code` | → `mart_dim_country` |
| `job_family_code` | → `mart_dim_job_family`; empty for contingent workers |
| `grade` | → `mart_dim_grade`; empty for contingent workers |
| `movement_order` | 1 to 8, for sorting a waterfall; 7 is Conversions (once FTE Changes) |
| `movement_category` | Opening, Hires, Voluntary Terminations, Involuntary Terminations, Internal Moves Out, Internal Moves In, Conversions, Closing; for contingent workers Opening, Starts, Ends, Internal Moves Out/In, Conversions, Closing |
| `movement_reason` | New Hire · Voluntary · Involuntary · Transfer · Reorganization · Location Change · Promotion · Demotion · Job Change · Contingent to Employee · Opening · Closing; contingent Starts: New engagement · Returned after a lapse; Ends: Completed · Ended early · Lapsed: approved late |
| `walk_step` | The same line in one vocabulary for both worker types: Opening, Joined, Left, Moved out, Moved in, Converted, Closing. Use it for a Total waterfall |
| `headcount` | Signed headcount change; for Opening and Closing, the headcount itself |
| `fte` | Signed FTE change; for Opening and Closing, the FTE itself |

Rules: headcount includes executive officers. A move is booked out of the old slice and into the new one at the worker's prior FTE, so moves net to zero at any roll-up that contains both slices. A contingent worker hired as an employee is booked −1 Contingent and +1 Employee as Conversions in the same month; the employee is not in Hires. A contingent worker counts 1.0 in `fte`. **Lapsed: approved late** is a contingent worker whose extension or renewal was approved after the old end date: the month-end report of the time did not count them, and the history is never restated, so they end one month and return (*Returned after a lapse*) the next. When several slice attributes change in one month, one reason is recorded: department (Reorganization if a reorg action is on file, otherwise Transfer), then country, then grade, then job family.

**Walking across several months:** take Opening from the first month, Closing from the last month, and sum every other line in between. Test 14 guarantees the months chain together.

### mart_dim_month
One row per walked month-end: `month_end_date`, `prior_month_end_date`, `fiscal_year`, `fiscal_year_label` (`FY26`), `fiscal_quarter_label`, `fiscal_period`, `fiscal_month`, `is_fiscal_year_end`.

### mart_dim_department
One row per department: `department_id`, `department_name`, `sub_function`, `function_name`, `parent_org_unit_id`, `cost_center`, `head_grade`.

### mart_dim_country
One row per country: `country_code`, `country_name`, `region`, `currency_code`, `pay_index`.

### mart_dim_job_family
One row per job family: `job_family_code`, `job_family`.

### mart_dim_grade
One row per job level: `grade` (1–12), `level_code` (L1–L12), `grade_level`, `career_track`, `us_base_salary_usd`.

### mart_dim_location
One row per office: `location_id`, `office_name`, `city`, `state_province`, `postal_code`, `street_address` (fictional), `country_code`, `country_name`, `region`, `site_type`, `latitude`, `longitude`, `geo_source`, `pay_zone_factor`, `opened_date`.

### mart_dim_org_unit
The org design as a tree, for drawing it: `org_unit_id`, `org_unit_name`, `org_unit_type`, `parent_org_unit_id`, `function_name`, `leader_title`, `leader_grade`.

### mart_org_leader_summary
Grain: **org leader × fiscal year-end (and the latest month-end).** The CEO, function heads, sub-function heads and department heads, with `worker_name`, `job_title`, `grade`, `department_id`, `office_name`, their manager (`manager_worker_id`, `manager_name`), `direct_reports`, `total_reports` (everyone below them) and `layers_from_ceo`. All names are fictional.

### mart_reporting_line
Grain: **worker × fiscal year-end.** `manager_worker_id`, `skip_level_manager_id` (the manager's manager), `department_head_id`, `function_head_id`, `function_org_unit_id`, `layers_from_ceo`, `direct_reports`, `total_reports`, plus `department_id`, `location_id`, `grade`, `job_profile_id`, `is_people_manager`. Every month-end is in `intermediate.int_worker_reporting_line`; the export keeps fiscal year-ends to stay small.

### mart_fringe_rate
Grain: **country × calendar year (2021–2026).** The fringe rate and its four components, `is_estimate`, `method_note` and `source_count`.

### mart_location_headcount
One row per month-end per office per worker type (Employee or Contingent; release 3). Movements are positive counts; the column name carries the direction. Filter on `worker_type`, or sum both for the whole workforce.

| Column | Definition |
|---|---|
| `opening_headcount` | Workers at this office at the prior month-end |
| `hires` | Workers who joined the company at this office |
| `voluntary_terminations`, `involuntary_terminations` | Workers who left the company from this office |
| `contingent_starts`, `contingent_ends` | Contingent rows: engagements starting and ending at this office |
| `conversions_in`, `conversions_out` | Contingent workers hired as employees: out of the Contingent row, into the Employee row |
| `relocations_in`, `relocations_out` | Workers who changed office between the two month-ends, including within a country |
| `closing_headcount`, `closing_fte` | Workers at this office at the month-end, and their FTE |

`opening + hires − voluntary − involuntary + contingent_starts − contingent_ends + conversions_in − conversions_out + relocations_in − relocations_out = closing` for every row (test 19).

### mart_mobility_flows
One row per month-end per worker type per origin office per destination office: `worker_type` (release 3), `from_location_id`, `from_city`, `from_region`, `from_latitude`, `from_longitude`, the same five for `to_`, `flow_scope` (`Domestic` or `International`), `has_coordinates` (always true now that every office has coordinates) and `workers`. Flows out of and into each office equal its relocations (test 22).

### mart_office_moves
One row per date pair × view × group × `group_side` × origin office × destination office × `move_reason`: the people who changed office between two month-ends on the compensation walk's grid, keyed like the walk (`view_name`, `group_id`, `group_name`, `group_parent`) so one set of filters drives both. Columns for the date pair (with `report_start_date`, `report_as_of_date`), the group and its side (`Both`, `From`, `To`), both offices with city, country, region and coordinates, `flow_scope`, `flow_scope_label`, `region_scope`, `move_reason`, `workers` and `open_headcount` (the group's headcount at the From date, equal to the walk's Opening; NULL for a group that did not exist yet, test 59). Compared From vs To only, so a person who moved twice counts once. In the Office and Country views `To` equals the walk's Transfers In and `From` equals Transfers Out (test 39); the views agree with each other (test 40). The DuckDB twin of `tableau/custom_sql_office_moves.sql`; not exported to CSV. Field reference: [office_moves.md](../projects/compensation-walk/office_moves.md).

### mart_region_walk
Grain: **date pair × view × group × region.** A headcount walk per region inside every group of the compensation walk, keyed the same way: `opening_headcount + hires − exits + transfers_in − transfers_out + region_moves_in − region_moves_out = closing_headcount` on every row. Transfers are moves into or out of the group; region moves are people who stayed in the group and changed region. Summed over regions it equals the walk's headcount lines (test 57). `hires_joined_elsewhere` counts the hires who joined another group of the view and moved in; the rest of `hires` are a subset of the Headcount & FTE Walk's joined for the group (test 79). The DuckDB twin of `tableau/custom_sql_region_walk.sql`. Field reference: [region walk and career moves](../projects/compensation-walk/region_walk_and_career_moves.md).

### mart_career_moves
Grain: **date pair × view × group × move type × from grade × to grade.** Promotions and demotions between two month-ends, from grade changes in the job history, for people present at both ends, in the group they belong to at the To date: `move_type`, `from_grade`, `from_grade_level`, `to_grade`, `to_grade_level`, `director_and_above` (grade 7 or above on either side), `into_director` (from grade 6 or below to 7 or above), `moves` and `workers`. The people promoted and demoted agree with the compensation walk, which counts them from pay records (test 58). The DuckDB twin of `tableau/custom_sql_career_moves.sql`.

### mart_position_fill
Grain: **seat fill** (external hire or internal move), 30,575 rows from FY22. The core table of case study 3 ([field guide](../projects/workforce-planning/workforce_planning.md)).

| Column | Description |
|---|---|
| `fill_id`, `fill_date`, `fiscal_year`, `fiscal_quarter_label`, `fiscal_period` | The fill |
| `fill_type` | `External Hire` or `Internal Move` |
| `seat_type` | `Net-new` (no earlier incumbent) or `Backfill` |
| `seat_decision` | Backfills only: `Backfill as is`, `Re-levelled`, `Relocated`, `Frozen, then reopened`, `Immediate refill` (a leader seat refilled the same day by a successor) |
| `was_frozen` | The seat was frozen at some point between exit and fill |
| `requisition_id`, `requisition_opened_date`, `requisition_approved_date` | The requisition |
| `time_to_fill_days`, `vacancy_days` | Approval to fill; prior incumbent's exit to fill |
| `position_id`, `seat_created_date`, `seat_created_reason` | The seat |
| `worker_id`; department, `sub_function`, `function_name`, `cost_center_id`, office, country, region and coordinates; `job_profile_id`, `job_title`, `job_family`, `grade`, `is_manager_seat` | The seat as filled, and who filled it |
| `prior_worker_id`, `prior_end_date`, `prior_vacate_reason`, `prior_department_id`, prior office, country and coordinates, `prior_job_profile_id`, `prior_job_title`, `prior_grade`, `prior_is_manager_seat` | Backfills: the previous incumbent and the seat as they left it |
| `level_change`, `location_change` | `Up` / `Same` / `Down`; `Same office` / `Other office, same country` / `Other country` |
| `prior_pay_usd_constant`, `new_pay_usd_constant`, `pay_change_usd_constant` | Annual base at exit and at fill, constant USD |
| `level_effect_usd_constant`, `location_effect_usd_constant`, `market_effect_usd_constant`, `positioning_effect_usd_constant` | The pay walk; adds up to `pay_change_usd_constant` to the cent (test 53) |
| `reuse_candidate`, `reuse_candidate_seats`, `reuse_candidate_position_id`, `reuse_candidate_vacant_since` | Net-new only: a seat in the same department, job family and country, a grade within one, stood Open or Frozen 90+ days on the approval date; the oldest is named (test 54) |
| `chain_id`, `parent_fill_id`, `chain_depth`, `chain_length`, `chain_trigger` | The vacancy chain the fill belongs to (test 55) |

### mart_vacancy_pool
Grain: **month-end × vacant PID** (Open or Frozen; 439,286 rows, employee and contingent; `worker_type`, `cw_type`, `cw_role_family` added in release 3.1, job and grade empty for contingent PIDs): `status`, `status_since`, `days_in_status`, `vacated_by`, `vacated_date`, `days_vacant`, `vacancy_age_band`, `is_stale` (vacant 90 days or more), the open requisition (`open_requisition_id`, `req_type`, `requisition_approved_date`), and the seat's organization, cost center, office, country, region, job and grade, `created_date`, `created_reason`. At 30 Jun 2026: employee 725 open and 252 frozen held before, plus 291 new; contingent 7,712 held before and 237 new. The CSV in `data/marts/` keeps quarter-ends only (149,615 rows), to stay under GitHub's 100 MB file limit; the warehouse table and `rpt.vw_vacancy_pool` keep every month-end.

### mart_plan_vs_actual
Grain: **plan version × cost center × fiscal quarter** (29,415 rows; the 615 contingent-only cost center rows are zero on every employee measure). The plan (`planned_*`) beside the actuals: `actual_ending_headcount`, `actual_ending_fte`, `actual_net_new`, `actual_net_new_reuse_candidates`, `actual_backfills`, `actual_external_hires`, `actual_internal_moves`, `actual_cost_usd_plan_fx` (comparable with `planned_cost_usd`) and `actual_cost_usd_constant`; plus `version_order`, `is_latest_version` and the cost center's department, function, country and region. For every version and quarter, the actual headcount sums to the company and the actual fills to the seat fills (test 56). Attainment = actual ÷ planned. Release 3 adds the contingent line: `planned_cw_headcount` beside `actual_cw_headcount` (Bridgeway on the quarter-end), and `planned_cw_spend_usd` beside `actual_cw_spend_usd_plan_fx` (annualized bill run-rate at the plan's FX) and `actual_cw_spend_usd_constant` (test 74).

### Case study 4 marts (release 3)

How they work and what they find: [case study 4](../projects/contingent-workforce/case_study_4.md).

| Mart | Grain | Columns |
|---|---|---|
| `mart_cw_discrepancy_detail` | month-end × discrepancy × worker, order or timesheet (latest 13 month-ends) | `discrepancy_code`, `discrepancy_name`, `severity`, `who_can_fix_it`, `root_cause_code`, `root_cause_name`, `identity_id`, `bw_worker_id`, `person_id`, `worker_name`, `cw_type`, `match_confidence`, `supplier_name`, `cost_center_id`, `department_id`, `department_name`, `function_name`, `country_code`, `manager_worker_id`, `fields_affected`, `since_date`, `age_days`, `age_band`, `service_order_id`, `feed_event_id`, `timesheet_id`, `evidence` |
| `mart_cw_reconciliation` | month-end × function × supplier (× discrepancy type) | `row_type` Population (`cw_working_bridgeway`, `cw_working_keystone`, `workers_with_any_discrepancy`) or Discrepancy (`discrepancy_code`, `discrepancy_name`, `severity`, `who_can_fix_it`, `workers_affected`, `new_this_month`, `aged_0_7`, `aged_8_30`, `aged_31_90`, `aged_over_90`); never sum the two row types together |
| `mart_cw_engagement_cap` | Bridgeway worker who started | `original_start_date`, `last_day`, `is_working_at_extract`, `engagement_status`, `months_engaged`, `extensions`, `renewals`, `cap_date`, `months_left_at_extract`, `is_over_cap`, `cap_band`, plus identity, name, type, supplier |
| `mart_cw_detection_score` | month-end × discrepancy type | `injected`, `detected`, `missed`, `false_flags`, `recall`, `precision`: the rules scored against the answer key (test 73) |

### Dashboard #4 marts (release 4)

The month-end close view of case study 4: [release 4 plan](../projects/contingent-workforce/release_4_plan.md). Executive officers (D-901) excluded. All 61 closes, Jun 2021 to Jun 2026; `is_latest_close` marks Current (Jun 30, 2026).

| Mart | Grain | Columns |
|---|---|---|
| `mart_cw_gap_close` | close × contractor × flag (21,665) | `gap_id`, `contractor_key`, `bw_worker_id`, `person_id`, `contractor_name`, `cw_type`, `supplier_name`; the flag (`flag_code`, `flag_name`, `flag_label` "01 ..." in a fixed order, `flag_rank`, `flag_count`, and rank and count at the prior close and 12 closes earlier); `risk`, `risk_order`; `place` (Bridgeway, Keystone, System feed), `place_order`, `place_label` (Bridgeway (vendor system), Keystone (HR system), System feed (integration)); flag, risk and place label sort alphabetically in the Sankey at every close (test 83); `cause_code`, `cause_name`, `root_cause_code`, `timing_class`, `is_counted`; `since_date`, `days_open`, `open_band`, `is_over_90_days`, `days_since_end`, `was_open_prior_close`, `fixed_day_after_close`, `items`; the order, feed event and PID involved; the group (`cost_center_id`, `department_id`, `department_name`, `function_name`, `country_code`, `country_name`: Bridgeway's billed cost center, Keystone's when Bridgeway has none); `keystone_shows`, `bridgeway_has`, `evidence`, `next_step`; the ticket (`ticket_number`, `ticket_title`, `ticket_state`, `ticket_status`, `has_ticket`) |
| `mart_cw_gap_rate_close` | close × cost center (27,324) | `contractors_working` (the gap rate's denominator: working in Bridgeway), `contractors_working_keystone`, `working_bridgeway_only`, `working_keystone_only`, `contractors_with_gap` (counted gaps), `contractors_with_any_gap`, `gaps`, `gaps_counted`, `gaps_clear_on_own`, `gaps_no_ticket`, `gaps_over_90_days`, `gaps_open_prior_close`, `gaps_fixed_day_after`, `gap_rate_target` (0.03), `load_note`, plus the group. Additive across any choice of function, department and country |
| `mart_itsm_ticket_close` | close × open Helix ticket (16,446) | `ticket_number`, `title`, `state`, `category_code`, `category_name`, `flag_code`, `risk`, `priority`, `place` (from the group working it), `place_order`, `place_label`, `current_group`, `opened_at`, `age_days`, `age_band` (0 to 5 days, 6 to 30 days, over 30 days), `age_band_order`, `times_reopened`, `times_reassigned`, `link_tier`, `contractor_key`, `linked_gap_id`, the group, `dot_seq`, `dot_x`, `dot_y` (the dot's place on the ticket card, packed 20 to a line, oldest first) |
| `mart_cw_reconciliation_dashboard` | row_type × its grain (65,435) | The three above in one union (`row_type` Gap, Population, Ticket; `gaps` and `tickets` count rows): Dashboard #4's one data source, the same rows as `tableau/custom_sql_cw_reconciliation_dashboard.sql` |

### mart_cw_spend
Grain: **month-end × cost center × supplier × contingent worker type × role family × billing currency** (release 3). What contingent workers cost, two ways side by side: **billed in the month** (`workers_billed`, `billed_hours`, `billed_units`, `billed_amount_local`, `billed_usd_nominal` at the month-end rate, `billed_usd_constant`) and **working at the month-end** (`workers_at_month_end`, `run_rate_local`, `run_rate_usd_nominal`, `run_rate_usd_constant`: hourly rate × contracted hours × 52, or monthly rate × 12). Also `fiscal_year`, `fiscal_quarter_label`, `department_id`, `country_code`, `supplier_name`. A month's billing is placed on the order revision in effect at the month-end. Billing ties to `bw_timesheet_month` to the cent and the month-end columns to the Bridgeway snapshot (test 71). Billed spend runs below the run-rate because timesheets carry time off and partial months.

### mart_workforce_cost_growth_mix
Grain: **date pair × view × group × factor** (release 3; 1,224 rows): each fiscal quarter-end against the same quarter-end a year earlier (17 pairs), for the Company and each Function. Splits the change in **total workforce cost** (employees' loaded pay plus contingent run-rate, nominal USD) into six factors: Volume, Workforce mix (employees vs contingent), Location mix, Level mix (grade, or contingent type), Rate (cost per head at constant FX) and Currency, with `factor_order` 0 (Opening cost) to 7 (Closing cost) for a waterfall. `shapley_effect_usd` is each factor's Shapley value (its average effect over every order of the six factors); `sequential_effect_usd` moves them one at a time in the listed order; `order_bias_usd` is the difference. Both add up to closing minus opening exactly (test 78). Also `fiscal_year`, `fiscal_quarter_label`, `pair_type`, `factor_meaning`, `opening_headcount`, `closing_headcount`. Method: [growth mix](../projects/workforce-cost-bridge/methodology.md#release-3-total-workforce-cost-and-the-growth-mix).

### mart_seat_corridors
Grain: **fiscal quarter × from office × to office** (821 rows): where backfilled seats moved, from the prior incumbent's office to the new incumbent's, with both offices' coordinates and pay zones, `location_change`, `seats`, `seats_levelled_down`, `seats_levelled_up`, `seats_relocated_for_backfill`, `pay_change_usd_constant`, `location_effect_usd_constant`. Draws the map lines in the Footprint pattern (`MAKELINE`).

### mart_pid_month_end
Grain: **month-end × worker type × PID kind × stale flag × department × country** (release 3.1): `pids`. PID kind is `Filled`, `Vacant previously held` or `Vacant new` (never filled); stale is vacant 90 days or more. The PID ledger behind Dashboard #3's KPIs. At 30 Jun 2026: 51,163 PIDs = 30,005 filled by employees + 11,941 by contractors + 8,689 vacant previously held + 528 vacant new.

### mart_cw_pid_fill
Grain: **contingent assignment** (release 3.1): `assignment_id`, `position_id`, `start_date`, `fiscal_year`, `fiscal_quarter`, `is_backfill` (the PID had a holder before), `department_id`, `country_name`.

### mart_wfp_summary
Grain: **fiscal year × period × plan version × view × group** (10,080 rows = 5 years × 7 periods × 4 versions × 72 groups). Feeds Dashboard #3's KPI band and rail. Periods (`pair_code` FY, H1, H2, Q1–Q4, with `pair_name` "FY26 · Jun 25 → Jun 26") compare quarter-ends inside one fiscal year. A reforecast plans only the quarters ahead of it, so `eff_first_quarter`..`eff_last_quarter` (`covered_label`, `eff_from_date`) is the part of the period it plans and every flow, plan and actual, is counted over those quarters; `is_covered` is false when it plans none of them. `has_plan` says whether the group has plan rows there (160 planned combinations of groups not yet open, such as Data & AI Platform before FY25); `is_view_default` marks each view's largest group. Flows: `planned_net_new`, `actual_net_new`, `planned_backfills`, `actual_backfills`, `actual_external_hires`, `actual_internal_moves`, `fills`, `backfill_fills`, `net_new_fills`, `internal_fills`, `reuse_candidate_fills`, `reuse_new_pay_usd_constant`, `backfill_pay_change_usd_constant`, `median_time_to_fill_days`, `median_vacancy_days` (backfills, immediate refills excluded). Levels at `to_date`: `planned_/actual_ending_headcount`, `planned_cost_usd`, `actual_cost_usd_plan_fx`, `planned_/actual_cw_headcount`, `planned_cw_spend_usd`, `actual_cw_spend_usd_plan_fx`. Executive officers (D-901) excluded. Release 3.1 adds the PID ledger at `to_date` (`pids_total`, `pids_filled_employee`, `pids_filled_contingent`, `vacant_previously_held`, `vacant_previously_held_contingent`, `vacant_previously_held_stale`, `vacant_new`, `vacant_new_contingent`, `vacant_new_stale`), backfill level and office changes (`level_down`, `level_up`, `level_and_office`, `moved_office`), contingent fills (`contingent_fills`, `contingent_backfill_fills`) and period labels (`span_name`, `span_order`, `period_short`, `period_months`, e.g. "FY26 Q3 · Jan – Mar 26"); `is_view_default` now marks each view's first group alphabetically. Test 80 checks that every choice has a row, filled PIDs equal the headcounts, filled + vacant = total, plan actuals equal the fills, groups add up to Company and Company ties to `mart_plan_vs_actual`.

### Forecast marts (release 5, Dashboard #5)

Written by [`forecast/run_forecast.py`](../../forecast/run_forecast.py) into the warehouse's `forecast` schema and `data/marts/`: `mart_pid_fill_quarter`, `mart_fill_survival`, `mart_pid_forecast_draws`, `mart_pid_forecast_backtest`, `mart_pid_forecast_accuracy`, `mart_pid_forecast_model`, `mart_pid_forecast_run`, `mart_cw_budget_function`. Grain, columns and method: [Seats to Fill: the forecast method](../projects/workforce-planning/seats_to_fill_method.md#6-tables-forecast-schema-in-the-warehouse-and-datamarts). Tests f01 to f05 in `tests/forecast/`.

## Intermediate models

### int_cw_supplier_alias
Every supplier spelling Keystone holds, mapped to a Bridgeway supplier on a normalized key (the first four letters and digits). Every spelling must map to exactly one (test 75).

### int_cw_identity_resolution
One row per identity: a Keystone contingent person matched to a Bridgeway worker, or either alone. Tier 1 (High): Keystone's stored Bridgeway ID and the same last name; tier 2 (Medium): same name, same supplier, starts within 7 days; tier 3 (Low): same name, starts within 30 days; mutual closest candidates only. `match_status` Matched, Keystone only, Bridgeway only or Never started; `match_evidence` says what the match rests on. Everyone appears exactly once (test 75).

### int_cw_reconciliation_snapshot
One row per identity per month-end on which either system shows the person working: what Keystone should hold (everything Bridgeway had sent by then, applied the day it was sent) beside what it holds, with `contract_differs`, `cost_center_differs`, `manager_differs`, `office_differs` and `link_differs`.

### int_cw_discrepancy
One row per month-end × identity (or order, or timesheet) × discrepancy type, found from the two systems and the feed log alone (never the answer key): `discrepancy_code`, `root_cause_code`, `fields_affected`, `since_date`, `age_days`, `evidence`, and the order, feed event or timesheet involved. Rules: [case study 4](../projects/contingent-workforce/case_study_4.md#3-why-they-differ-the-rules-int_cw_discrepancy).

### int_cw_close_run
One row per month-end close: the 00:00 GMT run on the 1st. Each source's run and status, how fresh each source was (`bw_data_as_of`, `ks_data_as_of`: the month-end, or earlier after a failed load; `hlx_read_at`), the failed run if any and the `load_note` the page shows.

### int_cw_flag_type
The 9 flags (F01 to F09): name, fixed label (`01 ...`), risk (five, alphabetical: Active headcount mismatch, Billing after the end date, Cost center mismatch, PID mismatch, Status mismatch), default place and next step. Numbered and named so the Sankey reads alphabetically in all three columns.

### int_cw_load_gap
Gaps that exist only because a load failed at the close: a stale source compared as it stood at its last good load, keeping only differences the true data does not have (cause `LOAD`).

### int_cw_flag
One row per close × contractor × flag: the comparisons from `int_cw_discrepancy` as flags, conversions still active as contractors (F01, cause `CONV`), Keystone job data against the PID ledger (F06, F07, cause `JOB`) and the load gaps, with the routing rule (`place` Bridgeway, Keystone or System feed; `timing_class` for the system feed: Clears on its own, Feed stuck, Feed event failed, Load failed), `keystone_shows`, `bridgeway_has`, `evidence` and `next_step`.

### int_itsm_ticket_state
One row per close × ticket existing at the close's Helix read: its state rebuilt from the events, the group working it, age and age band.

### int_itsm_ticket_subject
One row per ticket: the contractor it is about, linked in tiers (the IDs, else exactly one identity named in the description).

### int_itsm_ticket_gap_link
One row per close × gap: the ticket working on it (same contractor, opened no more than 7 days before the gap began, same risk or a stuck-feed ticket; latest wins) and `ticket_status` (No ticket, Open, Fix pending next run, Closed, gap still open).

### int_cw_month_end_snapshot
One row per contingent worker (Bridgeway worker ID) per month-end on which they were working, **as Bridgeway held it that day**: the service order revision in effect on the month-end says the assignment has started and not ended. History is never restated, so an extension approved after the old end date counts from its approval. Carries the order, type, supplier, cost center (and so department and country), office, role, seniority, rate and its annualized run-rate in billing currency and in USD (month-end and constant rates). Test 70.

### int_cw_movement
The contingent counterpart of `int_worker_movement`: one row per contingent worker per month, with the state at both month-ends and the classification (Start, End, Conversion, Internal Move, No Change) and reason.

### int_cw_conversion
One row per contingent worker hired as an employee that the warehouse can link: Keystone's *Converted to employee* record, through the Bridgeway worker ID Keystone stored, to the employee. `is_walk_conversion` marks those that were contingent at the prior month-end and employees at this one: all of them in this data (1,174). A conversion whose stored link is blank or mistyped (CW06) is an ordinary hire.

### int_worker_movement
One row per worker per month for everyone active at the prior month-end, the current month-end or both: the worker's slice, office and FTE at each end, `movement_type` (Hire, Termination, Internal Move, No Change), `movement_reason`. Test 18 checks there is never a second row for the same worker and month.

### int_worker_in_month_hire_and_exit
Workers hired and terminated between the same two month-ends. A month-end walk cannot show them, so they are listed here instead of disappearing. The current data has none.

### int_compensation_history_usd
One row per pay record (after corrections), valued at the ECB rate of its posting date (an `ASOF` join to the latest rate on or before it) and at the constant rate.

### int_worker_month_end_snapshot
One row per active worker per month-end: job and pay in effect that day, manager and leadership role, FX (month-end, posting and constant), fringe by calendar year, range midpoint, and run-rates in all three FX bases.

### int_worker_reporting_chain
A closure table: one row per worker per manager above them per month-end, with `hops` (1 = direct manager). Built with a recursive CTE; about 10.6 million rows. "Everyone in Maria's organization" becomes an equality join instead of a recursive query.

### int_month_end_calendar
One row per month-end (61, from 2021-06-30) with the prior month-end and the fiscal calendar.

### int_worker_pay_ledger
One row per worker per month-end: running totals of every pay event by reason, FTE change, fringe change and FX movement. Between any two month-ends a driver is `cum(To) − cum(From)`, so the compensation walk prices any date pair with two equality joins.

### int_position_history
Seat history (`dim_position`) with the start of each status run (`status_since`), the seat's country, currency and pay zone, job family and manager-seat flag.

### int_cw_position_snapshot
One row per contingent PID per month-end while it exists and is not closed: status, `status_since`, holder, department, cost center, office, country, worker type, role, created date. Filled contingent PIDs equal `int_cw_month_end_snapshot` by month, department and country (test 81).

### int_position_snapshot
One row per seat per month-end (1.7 million rows) for every seat that exists and is not eliminated: status, days in status, incumbent, open requisition. Filled seats equal the worker month-end snapshot, same people (test 45).

### int_seat_fill
One row per fill: prior incumbent, seat decision, level and location change, pay walk and reuse check. `mart_position_fill` adds names and the chain.

### int_seat_vacancy_chain
For each fill: `parent_fill_id` (the internal move that emptied its seat), `chain_id`, `chain_depth`, `chain_length` and `chain_trigger` (Voluntary exit, Involuntary exit or Net-new seat).

### int_worker_reporting_line
One row per active worker per month-end: direct manager, skip-level manager, department head, function head, layers below the CEO, direct and total reports.
