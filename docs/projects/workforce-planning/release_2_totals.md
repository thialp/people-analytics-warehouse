# Control totals

## Fiscal years

| FY | Opening HC | Hires | Voluntary | Involuntary | Moves in | Closing HC | Closing FTE | FY-end loaded $M (constant) |
|---|---|---|---|---|---|---|---|---|
| FY22 | 23,516 | 4,694 | 2,553 | 613 | 2,895 | 25,044 | 24,716.7 | 2,643.0 |
| FY23 | 25,044 | 5,561 | 2,928 | 750 | 3,093 | 26,927 | 26,505.6 | 2,835.9 |
| FY24 | 26,927 | 3,607 | 2,326 | 1,010 | 3,308 | 27,198 | 26,704.0 | 2,912.8 |
| FY25 | 27,198 | 4,347 | 2,486 | 617 | 4,709 | 28,442 | 27,875.0 | 3,017.9 |
| FY26 | 28,442 | 5,244 | 2,887 | 764 | 3,618 | 30,035 | 29,390.3 | 3,215.9 |

## Row counts: raw

| Table | Rows |
|---|---|
| dim_country | 22 |
| dim_department | 32 |
| dim_job_level | 12 |
| dim_job_profile | 165 |
| dim_location | 35 |
| dim_org_unit | 44 |
| dim_worker | 46,982 |
| fact_bonus_payout | 154,118 |
| fact_compensation_history | 180,829 |
| fact_job_history | 98,597 |
| fact_performance_review | 154,118 |
| ref_fringe_rate | 132 |
| ref_fringe_source | 215 |
| ref_fx_rate_constant | 17 |
| ref_fx_rate_daily | 24,820 |
| ref_fx_rate_monthly | 1,037 |
| ref_job_level_base_salary | 264 |
| ref_performance_bonus | 3 |
| ref_salary_range | 1,584 |
| ref_tenure_increase | 7 |

## Row counts: marts

| Table | Rows |
|---|---|
| mart_compensation_walk | 114,977 |
| mart_dim_country | 22 |
| mart_dim_department | 32 |
| mart_dim_grade | 12 |
| mart_dim_job_family | 14 |
| mart_dim_location | 35 |
| mart_dim_month | 60 |
| mart_dim_org_unit | 44 |
| mart_fringe_rate | 132 |
| mart_headcount_fte_walk | 539,088 |
| mart_location_headcount | 1,929 |
| mart_mobility_flows | 1,454 |
| mart_office_moves | 53,826 |
| mart_org_leader_summary | 260 |
| mart_reporting_line | 161,162 |
| mart_workforce_cost_bridge | 17,119 |
| mart_workforce_cost_snapshot | 242,966 |
