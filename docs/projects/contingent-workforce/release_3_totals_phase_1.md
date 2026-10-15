# Control totals: release 3 after phase 1 (part-time removed, 2026-10-14)

Same people as [the release 2 baseline](baseline_release_2.md): every headcount column is identical. FTE now equals headcount, and loaded cost rises because former part-timers cost a full salary. Rerun with `python pipeline/control_totals.py`.

## Fiscal years

| FY | Opening HC | Hires | Voluntary | Involuntary | Moves in | Closing HC | Closing FTE | FY-end loaded $M (constant) |
|---|---|---|---|---|---|---|---|---|
| FY22 | 23,516 | 4,677 | 2,511 | 621 | 2,870 | 25,061 | 25,061.0 | 2,519.9 |
| FY23 | 25,061 | 5,538 | 2,943 | 715 | 3,069 | 26,941 | 26,941.0 | 2,771.1 |
| FY24 | 26,941 | 3,634 | 2,343 | 1,015 | 3,327 | 27,217 | 27,217.0 | 2,902.5 |
| FY25 | 27,217 | 4,376 | 2,532 | 614 | 4,432 | 28,447 | 28,447.0 | 3,130.0 |
| FY26 | 28,447 | 5,235 | 2,942 | 726 | 3,633 | 30,014 | 30,014.0 | 3,410.5 |

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
| dim_position | 99,398 |
| dim_worker | 46,980 |
| fact_bonus_payout | 154,151 |
| fact_candidate_stage_event | 531,691 |
| fact_compensation_history | 186,191 |
| fact_job_history | 96,129 |
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
| mart_career_moves | 34,532 |
| mart_compensation_walk | 108,918 |
| mart_dim_country | 22 |
| mart_dim_department | 32 |
| mart_dim_grade | 12 |
| mart_dim_job_family | 14 |
| mart_dim_location | 35 |
| mart_dim_month | 60 |
| mart_dim_org_unit | 44 |
| mart_fringe_rate | 132 |
| mart_headcount_fte_walk | 519,173 |
| mart_location_headcount | 1,929 |
| mart_mobility_flows | 2,101 |
| mart_office_moves | 89,611 |
| mart_org_leader_summary | 260 |
| mart_plan_vs_actual | 28,800 |
| mart_position_fill | 30,575 |
| mart_region_walk | 26,520 |
| mart_reporting_line | 161,196 |
| mart_seat_corridors | 821 |
| mart_vacancy_pool | 62,055 |
| mart_workforce_cost_bridge | 15,999 |
| mart_workforce_cost_snapshot | 233,866 |
