# Data Dictionary

All data is synthetic. Dates are ISO (`YYYY-MM-DD`). The fiscal year starts July 1 (FY2026 = 2025-07-01 to 2026-06-30).

## Raw tables (`data/raw/`)

Twenty tables in four groups: people and their history, the organization, the pay structure, and external reference data. The raw files call the 1–12 ladder **job level**; from staging onward it is called `grade`, the name the published marts and dashboards use.

### People and history

#### dim_worker
One row per worker ever employed (43,569).

| Column | Description |
|---|---|
| `worker_id` | Worker key, e.g. `W100001` |
| `first_name`, `last_name` | Fictional names, drawn from regional name pools |
| `original_hire_date` | First day of employment |
| `termination_date` | Last day worked; empty if still employed |
| `termination_type` | `Voluntary` or `Involuntary`; empty if still employed |
| `worker_type` | Always `Regular Employee` in this dataset |
| `is_executive_officer` | `True` for the CEO and the eight function heads, who are excluded from compensation reporting |

#### fact_job_history
Effective-dated job assignments (SCD Type 2). A new row starts whenever department, office, job, level, FTE, manager or leadership role changes.

| Column | Description |
|---|---|
| `job_record_id` | Record key |
| `worker_id` | → `dim_worker` |
| `effective_start_date` | First day the record applies |
| `effective_end_date` | Last day the record applies (inclusive); empty = current |
| `action_reason` | `Hire`, `Promotion`, `Demotion`, `Transfer`, `Reorganization`, `Succession`, `Location Change`, `FTE Change`, `Manager Change`, `Became People Manager`, `Returned to Individual Contributor`. When two changes land on the same day, one record carries the higher-ranked reason, in this order |
| `position_id` | Position held; a new position is assigned on transfer or reorganization |
| `department_id` | → `dim_department` |
| `location_id` | → `dim_location` |
| `job_profile_id` | → `dim_job_profile`: family + level, e.g. `SWE-L3`, `SWE-M5` (people-manager variant), `EXE-CEO` |
| `job_level` | 1 (Associate) to 12 (Chief Executive Officer); see `dim_job_level` |
| `fte` | 1.0, 0.8 or 0.5 |
| `manager_worker_id` | Direct manager (→ `dim_worker`). Empty only for the CEO, who reports to the board, and on pre-2022 history from before a worker's current manager joined |
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

- **Corrections.** 891 pay records have a second row with the same worker and effective date. The lower-id row holds a mistyped amount (some are off by a factor of 10). Staging keeps the latest row.
- **Conversion date.** Pay history was loaded into the warehouse on 2022-03-01. Workers hired before then have a `Conversion` row starting on that date and no earlier pay history.

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
| `opened_date` | Six offices opened during the window: Manila (2022-10), Guadalajara (2023-03), Lisbon (2023-09), Seoul (2024-03), Pune (2024-07) and Vancouver (2025-01) |

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
Pay ranges in local currency by fiscal year, level and country: `range_min` (85% of the level base), `range_mid` (the level base), `range_max` (135%). Ranges are held flat across the years.

### External reference data

#### ref_fx_rate_daily
Every ECB publication day from 2022-01-03 to 2026-09-14 for the 17 currencies: `currency_code`, `rate_date`, `usd_per_local`, `source`. Rates are the ECB euro reference rates crossed into USD (`USD per EUR ÷ currency per EUR`); the UAE dirham uses its USD peg (3.6725). Lookups on other days take the latest rate on or before the date.

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
| `is_estimate` | `True` for 2026 rows carried forward from 2025 because the OECD has not published 2026 yet |
| `method_note` | How the row was built |

#### ref_fringe_source
One row per country, year, component and source document: `country_code`, `year`, `component`, `source_id`, `source_title`, `source_url`. Test 28 checks that every non-zero component has at least one.

## Marts (`data/marts/`)

Pay measures in the two cost marts are **annualized run-rates at the month-end**, in USD. Executive officers are excluded.

| Measure | Definition |
|---|---|
| `base_usd_nominal` | Base salary × FTE, at the month-end's ECB rate |
| `base_usd_constant` | Base salary × FTE, at the constant rate set (2026-06-30) |
| `loaded_usd_nominal` | Base × (1 + fringe rate), month-end FX |
| `loaded_usd_constant` | Base × (1 + fringe rate), constant FX |

### mart_workforce_cost_bridge
Grain: **month-end × department × driver.** For each department and month, Opening + all drivers = Closing.

| Column | Description |
|---|---|
| `month_end_date` / `prior_month_end_date` | The month being explained, and the month-end it starts from |
| `fiscal_year`, `fiscal_quarter_label`, `fiscal_period` | Fiscal calendar, e.g. `FY26 Q2`, `FY26 P06` |
| `department_id`, `department_name`, `sub_function`, `function_name`, `cost_center` | Department the line is attributed to |
| `driver_order` | 1 to 13, for sorting a waterfall |
| `driver` | Opening Run-Rate, Hires, Terminations, Transfers In, Transfers Out, Promotions, Demotions, Tenure & Market Adjustments, International Mobility, FTE Changes, Fringe Rate Changes, FX Rate Changes, Closing Run-Rate |
| `driver_group` | Balance, Headcount Movement, Pay Rate, Workforce Mix, Fringe & FX |
| `worker_count` | Workers contributing to the line |
| `headcount` | Signed headcount change; for Opening and Closing, the headcount itself |
| `fte` | Signed FTE change; for Opening and Closing, the FTE itself |
| `base_usd_*`, `loaded_usd_*` | Signed dollar effect of the driver |

**Walking across several months:** take Opening from the first month, Closing from the last month, and sum every other driver across the months in between. Test 08 guarantees the months chain together.

### mart_compensation_walk
Grain: **date pair × view × group × walk step × movement reason.** For any two month-ends on the grid (every quarter-end to every later quarter-end, plus month over month: 184 pairs) and every group in six views (Company, Function, Leader, Department, Office, Country): Opening + Hires + Exits + Transfers In/Out + Promotions + Demotions + Tenure Increases + Market Adjustments + Relocation Adjustments + International Transfer Adjustments + FTE Changes + Fringe Rate Changes + FX Translation = Closing, in headcount, FTE and the four dollar measures, as totals (`base_usd_*`, `loaded_usd_*`), as an average walk per FTE (`avg_*`) and as a percent walk (`pct_*`). Filter to one `view_name` and one date pair. Same columns as the Tableau Custom SQL `tableau/custom_sql_compensation_walk.sql`.

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
Grain: **month-end × department × country × job family × grade × movement category × movement reason.** For every slice and month, Opening + every movement = Closing, in headcount and FTE (test 13). Codes only: names come from the five `mart_dim_*` files below, which Tableau relates on matching column names.

| Column | Description |
|---|---|
| `month_end_date` | The month being walked; → `mart_dim_month` |
| `department_id` | → `mart_dim_department` |
| `country_code` | → `mart_dim_country` |
| `job_family_code` | → `mart_dim_job_family` |
| `grade` | → `mart_dim_grade` |
| `movement_order` | 1 to 8, for sorting a waterfall |
| `movement_category` | Opening, Hires, Voluntary Terminations, Involuntary Terminations, Internal Moves Out, Internal Moves In, FTE Changes, Closing |
| `movement_reason` | New Hire · Voluntary · Involuntary · Transfer · Reorganization · Location Change · Promotion · Demotion · Job Change · FTE Increase · FTE Reduction · Opening · Closing |
| `headcount` | Signed headcount change; for Opening and Closing, the headcount itself |
| `fte` | Signed FTE change; for Opening and Closing, the FTE itself |
| `part_time_headcount` | Workers under 1.0 FTE. Filled on Opening and Closing rows only (the levels); every movement row carries 0, because a move or FTE change can flip a worker between full-time and part-time (test 23) |

Rules: headcount includes executive officers. A move is booked out of the old slice and into the new one at the worker's prior FTE, so moves net to zero at any roll-up that contains both slices; an FTE change in the same month is a separate FTE Changes line. When several slice attributes change in one month, one reason is recorded: department (Reorganization if a reorg action is on file, otherwise Transfer), then country, then grade, then job family.

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
Grain: **country × calendar year (2022–2026).** The fringe rate and its four components, `is_estimate`, `method_note` and `source_count`.

### mart_location_headcount
One row per month-end per office. Movements are positive counts; the column name carries the direction.

| Column | Definition |
|---|---|
| `opening_headcount` | Workers at this office at the prior month-end |
| `hires` | Workers who joined the company at this office |
| `voluntary_terminations`, `involuntary_terminations` | Workers who left the company from this office |
| `relocations_in`, `relocations_out` | Workers who changed office between the two month-ends, including within a country |
| `closing_headcount`, `closing_fte` | Workers at this office at the month-end, and their FTE |

`opening + hires − voluntary − involuntary + relocations_in − relocations_out = closing` for every row (test 19).

### mart_mobility_flows
One row per month-end per origin office per destination office: `from_location_id`, `from_city`, `from_region`, `from_latitude`, `from_longitude`, the same five for `to_`, `flow_scope` (`Domestic` or `International`), `has_coordinates` (always true now that every office has coordinates) and `workers`. Flows out of and into each office equal its relocations (test 22).

### mart_office_moves
One row per date pair × view × group × `group_side` × origin office × destination office × `move_reason`: the people who changed office between two month-ends on the compensation walk's grid, keyed like the walk (`view_name`, `group_id`, `group_name`, `group_parent`) so one set of filters drives both. Columns for the date pair, the group and its side (`Both`, `From`, `To`), both offices with city, country, region and coordinates, `flow_scope`, `flow_scope_label`, `region_scope`, `move_reason` and `workers`. Compared From vs To only, so a person who moved twice counts once. In the Office and Country views `To` equals the walk's Transfers In and `From` equals Transfers Out (test 39); the views agree with each other (test 40). The DuckDB twin of `tableau/custom_sql_office_moves.sql`; not exported to CSV. Field reference: [office_moves.md](../projects/compensation-walk/office_moves.md).

## Intermediate models used by the walk

### int_worker_movement
One row per worker per month for everyone active at the prior month-end, the current month-end or both: the worker's slice, office and FTE at each end, `movement_type` (Hire, Termination, Internal Move, No Change), `movement_reason` and `fte_changed`. Test 18 checks there is never a second row for the same worker and month.

### int_worker_in_month_hire_and_exit
Workers hired and terminated between the same two month-ends. A month-end walk cannot show them, so they are listed here instead of disappearing. The current data has none.

### int_compensation_history_usd
One row per pay record (after corrections), valued at the ECB rate of its posting date (an `ASOF` join to the latest rate on or before it) and at the constant rate.

### int_worker_month_end_snapshot
One row per active worker per month-end: job and pay in effect that day, manager and leadership role, FX (month-end, posting and constant), fringe by calendar year, range midpoint, and run-rates in all three FX bases.

### int_worker_reporting_chain
A closure table: one row per worker per manager above them per month-end, with `hops` (1 = direct manager). Built with a recursive CTE; about 9 million rows. "Everyone in Maria's organization" becomes an equality join instead of a recursive query.

### int_worker_reporting_line
One row per active worker per month-end: direct manager, skip-level manager, department head, function head, layers below the CEO, direct and total reports.
