# Control totals

## Fiscal years

| FY | Opening HC | Hires | Voluntary | Involuntary | Moves in | Closing HC | Closing FTE | FY-end loaded $M (constant) |
|---|---|---|---|---|---|---|---|---|
| FY23 | 25,014 | 5,545 | 2,935 | 702 | 3,100 | 26,922 | 26,542.7 | 2,816.7 |
| FY24 | 26,922 | 3,508 | 2,262 | 980 | 3,388 | 27,188 | 26,730.7 | 2,897.3 |
| FY25 | 27,188 | 4,333 | 2,463 | 613 | 4,552 | 28,445 | 27,903.2 | 3,000.1 |
| FY26 | 28,445 | 5,168 | 2,843 | 746 | 3,623 | 30,024 | 29,404.7 | 3,195.5 |

## Row counts: raw

| Table | Rows |
|---|---|
| dim_country | 22 |
| dim_department | 32 |
| dim_job_level | 12 |
| dim_job_profile | 165 |
| dim_location | 35 |
| dim_org_unit | 44 |
| dim_worker | 43,569 |
| fact_bonus_payout | 131,639 |
| fact_compensation_history | 153,830 |
| fact_job_history | 89,240 |
| fact_performance_review | 131,639 |
| ref_fringe_rate | 110 |
| ref_fringe_source | 180 |
| ref_fx_rate_constant | 17 |
| ref_fx_rate_daily | 20,434 |
| ref_fx_rate_monthly | 833 |
| ref_job_level_base_salary | 264 |
| ref_performance_bonus | 3 |
| ref_salary_range | 1,320 |
| ref_tenure_increase | 7 |

## Row counts: marts

| Table | Rows |
|---|---|
| mart_compensation_walk | 271,219 |
| mart_dim_country | 22 |
| mart_dim_department | 32 |
| mart_dim_grade | 12 |
| mart_dim_job_family | 14 |
| mart_dim_location | 35 |
| mart_dim_month | 48 |
| mart_dim_org_unit | 44 |
| mart_fringe_rate | 110 |
| mart_headcount_fte_walk | 436,501 |
| mart_location_headcount | 1,581 |
| mart_mobility_flows | 1,117 |
| mart_office_moves | 260,464 |
| mart_org_leader_summary | 217 |
| mart_reporting_line | 137,593 |
| mart_workforce_cost_bridge | 13,835 |
| mart_workforce_cost_snapshot | 197,603 |
