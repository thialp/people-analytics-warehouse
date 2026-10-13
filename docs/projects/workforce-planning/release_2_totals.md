# Control totals

## Fiscal years

| FY | Opening HC | Hires | Voluntary | Involuntary | Moves in | Closing HC | Closing FTE | FY-end loaded $M (constant) |
|---|---|---|---|---|---|---|---|---|
| FY22 | 23,516 | 4,677 | 2,511 | 621 | 2,870 | 25,061 | 24,734.5 | 2,487.1 |
| FY23 | 25,061 | 5,538 | 2,943 | 715 | 3,069 | 26,941 | 26,510.1 | 2,727.3 |
| FY24 | 26,941 | 3,634 | 2,343 | 1,015 | 3,327 | 27,217 | 26,715.8 | 2,849.8 |
| FY25 | 27,217 | 4,376 | 2,532 | 614 | 4,432 | 28,447 | 27,861.7 | 3,066.1 |
| FY26 | 28,447 | 5,235 | 2,942 | 726 | 3,633 | 30,014 | 29,363.5 | 3,336.5 |

## Row counts: raw

| Table | Rows |
|---|---|
| dim_candidate | 188,982 |
| dim_cost_center | 630 |
| dim_country | 22 |
| dim_department | 32 |
| dim_job_level | 12 |
| dim_job_profile | 165 |
| dim_location | 35 |
| dim_org_unit | 44 |
| dim_position | 101,297 |
| dim_worker | 46,980 |
| fact_bonus_payout | 154,151 |
| fact_candidate_stage_event | 531,691 |
| fact_compensation_history | 186,191 |
| fact_job_history | 98,028 |
| fact_performance_review | 154,151 |
| fact_position_assignment | 54,094 |
| fact_requisition | 31,323 |
| fact_workforce_plan | 28,800 |
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
| mart_compensation_walk | 115,544 |
| mart_dim_country | 22 |
| mart_dim_department | 32 |
| mart_dim_grade | 12 |
| mart_dim_job_family | 14 |
| mart_dim_location | 35 |
| mart_dim_month | 60 |
| mart_dim_org_unit | 44 |
| mart_fringe_rate | 132 |
| mart_headcount_fte_walk | 521,029 |
| mart_location_headcount | 1,929 |
| mart_mobility_flows | 2,101 |
| mart_office_moves | 89,611 |
| mart_org_leader_summary | 260 |
| mart_plan_vs_actual | 28,800 |
| mart_position_fill | 30,575 |
| mart_reporting_line | 161,196 |
| mart_seat_corridors | 821 |
| mart_vacancy_pool | 62,055 |
| mart_workforce_cost_bridge | 17,022 |
| mart_workforce_cost_snapshot | 233,866 |
