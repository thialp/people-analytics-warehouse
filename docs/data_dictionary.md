# Data Dictionary

All data is synthetic. Dates are ISO (`YYYY-MM-DD`). The fiscal year starts July 1 (FY2026 = 2025-07-01 to 2026-06-30).

## Raw tables (`data/raw/`)

### dim_worker
One row per worker ever employed.

| Column | Description |
|---|---|
| `worker_id` | Worker key, e.g. `W100001` |
| `original_hire_date` | First day of employment |
| `termination_date` | Last day worked; empty if still employed |
| `termination_type` | `Voluntary` or `Involuntary`; empty if still employed |
| `worker_type` | Always `Regular Employee` in this dataset |
| `is_executive_officer` | `True` for the executive leadership team, who are excluded from compensation reporting |

### fact_job_history
Effective-dated job assignments (SCD Type 2). A new row starts whenever department, location, job, grade or FTE changes.

| Column | Description |
|---|---|
| `job_record_id` | Record key |
| `worker_id` | → `dim_worker` |
| `effective_start_date` | First day the record applies |
| `effective_end_date` | Last day the record applies (inclusive); empty = current |
| `action_reason` | `Hire`, `Promotion`, `Transfer`, `Reorganization`, `FTE Change`, `Location Change` |
| `position_id` | Position held; a new position is assigned on transfer |
| `department_id` | → `dim_department` |
| `location_id` | → `dim_location` |
| `job_profile_id` | → `dim_job_profile` (job family code + grade) |
| `grade` | 1 (Associate) to 9 (Vice President) |
| `fte` | 1.0, 0.8 or 0.5 |

### fact_compensation_history
Effective-dated base pay (SCD Type 2), stated as a **full-time annual rate in local currency**.

| Column | Description |
|---|---|
| `comp_record_id` | Record key; increases in entry order, so a correction always has a higher id than the row it replaces |
| `worker_id` | → `dim_worker` |
| `effective_start_date` / `effective_end_date` | As in job history |
| `action_reason` | `Hire`, `Conversion`, `Merit`, `Promotion`, `Market Adjustment`, `International Transfer` |
| `transaction_type` | `Original`, or `Correction` when the row replaces a mistyped row with the same effective date |
| `currency_code` | ISO currency of the pay |
| `base_salary_annual_local` | Annual base salary at 1.0 FTE |

**Source quirks to know about**

- **Corrections.** 362 pay records have a second row with the same worker and effective date. The lower-id row holds a mistyped amount (some are off by a factor of 10). Staging keeps the latest row.
- **Conversion date.** Pay history was loaded into the warehouse on 2022-03-01. Workers hired before then have a `Conversion` row starting on that date and no earlier pay history.

### dim_department

| Column | Description |
|---|---|
| `department_id` | Department key |
| `department_name` | Department |
| `sub_function` | Middle level of the org hierarchy |
| `function` | Top level of the org hierarchy |
| `cost_center` | Finance cost center |
| `effective_from_date` | When the department started; `D-108 Data & AI Platform` was created in the FY25 reorganization |

### dim_location

| Column | Description |
|---|---|
| `location_id` | Location key |
| `city` | Site city, or `Remote - US` |
| `country_code` / `country_name` | Country |
| `region` | North America, Latin America, Europe, Asia Pacific, Middle East & Africa |
| `currency_code` | Local pay currency |
| `site_type` | Headquarters, Regional Hub, Engineering Center, Office, Remote |

### dim_job_profile

| Column | Description |
|---|---|
| `job_profile_id` | Family code + grade, e.g. `SWE-4` |
| `job_family_code` / `job_family` | Job family |
| `job_title` | Title for that family and grade |
| `grade` / `grade_level` | Grade number and its label |
| `career_track` | Individual Contributor, Manager or Expert, Leadership |

### ref_fx_rate_monthly
Month-end exchange rates. `usd_per_local` is the number of US dollars per one unit of local currency (USD = 1). The rates are synthetic random walks; AED is pegged.

### ref_fx_rate_constant
One fixed rate per currency (`rate_set` = `FY26 Plan`, taken from the 2025-06-30 month-end), used for constant-currency reporting across all periods.

### ref_fringe_rate
Employer benefits, payroll taxes and social charges as a share of base pay, by `country_code` and `fiscal_year`.

### ref_salary_range
Pay range `range_min`, `range_mid`, `range_max` in local currency by `fiscal_year`, `grade` and `country_code`.

---

## Marts (`data/marts/`)

Pay measures in both marts are **annualized run-rates at the month-end**, in USD. Executive officers are excluded.

| Measure | Definition |
|---|---|
| `base_usd_nominal` | Base salary × FTE, at the month-end's actual FX rate |
| `base_usd_constant` | Base salary × FTE, at the FY26 plan rate |
| `loaded_usd_nominal` | Base × (1 + fringe rate), actual FX |
| `loaded_usd_constant` | Base × (1 + fringe rate), plan FX |

### mart_workforce_cost_bridge
Grain: **month-end × department × driver.** For each department and month, Opening + all drivers = Closing.

| Column | Description |
|---|---|
| `month_end_date` / `prior_month_end_date` | The month being explained, and the month-end it starts from |
| `fiscal_year`, `fiscal_quarter_label`, `fiscal_period` | Fiscal calendar, e.g. `FY26 Q2`, `FY26 P06` |
| `department_id`, `department_name`, `sub_function`, `function_name`, `cost_center` | Department the line is attributed to |
| `driver_order` | 1 to 12, for sorting a waterfall |
| `driver` | Opening Run-Rate, Hires, Terminations, Transfers In, Transfers Out, Promotions, Merit & Adjustments, International Mobility, FTE Changes, Fringe Rate Changes, FX Rate Changes, Closing Run-Rate |
| `driver_group` | Balance, Headcount Movement, Pay Rate, Workforce Mix, Fringe & FX |
| `worker_count` | Workers contributing to the line |
| `headcount` | Signed headcount change; for Opening and Closing, the headcount itself |
| `fte` | Signed FTE change; for Opening and Closing, the FTE itself |
| `base_usd_*`, `loaded_usd_*` | Signed dollar effect of the driver |

**Walking across several months:** take Opening from the first month, Closing from the last month, and sum every other driver across the months in between. Test 08 guarantees the months chain together.

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
| `range_mid_usd_constant` | Sum of range midpoints × FTE at plan FX. Compa-ratio = `SUM(base_usd_constant) / SUM(range_mid_usd_constant)` |
