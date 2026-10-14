# Control totals: release 3 after phase 3 (Bridgeway VMS simulation, 2026-10-14)

Employee totals are identical to [phase 1](release_3_totals_phase_1.md): the contingent workforce simulation runs on its own random stream after the employee simulation. New here is the contingent workforce table, read from Bridgeway as held on the extract date (30 June 2026). How it was built: [Bridgeway simulation](bridgeway_simulation.md). Rerun with `python pipeline/control_totals.py`.


## Fiscal years

| FY | Opening HC | Hires | Voluntary | Involuntary | Moves in | Closing HC | Closing FTE | FY-end loaded $M (constant) |
|---|---|---|---|---|---|---|---|---|
| FY22 | 23,516 | 4,677 | 2,511 | 621 | 2,870 | 25,061 | 25,061.0 | 2,519.9 |
| FY23 | 25,061 | 5,538 | 2,943 | 715 | 3,069 | 26,941 | 26,941.0 | 2,771.1 |
| FY24 | 26,941 | 3,634 | 2,343 | 1,015 | 3,327 | 27,217 | 27,217.0 | 2,902.5 |
| FY25 | 27,217 | 4,376 | 2,532 | 614 | 4,432 | 28,447 | 28,447.0 | 3,130.0 |
| FY26 | 28,447 | 5,235 | 2,942 | 726 | 3,633 | 30,014 | 30,014.0 | 3,410.5 |

## Contingent workforce (Bridgeway VMS)

Active on June 30 (the fiscal year-end), engagements started in the year, and billed spend at month-end FX. FY21 is one month (June 2021): timesheets start with the warehouse history.

| FY | Active CW | Contractor | Consultant | BPO | Engagements started | Billed spend $M |
|---|---|---|---|---|---|---|
| FY21 | 8,564 | 6,147 | 1,072 | 1,345 | 4,826 | 57.6 |
| FY22 | 9,288 | 6,646 | 1,128 | 1,514 | 5,280 | 739.9 |
| FY23 | 10,228 | 7,281 | 1,293 | 1,654 | 5,935 | 836.4 |
| FY24 | 9,910 | 7,020 | 1,191 | 1,699 | 4,966 | 894.7 |
| FY25 | 10,707 | 7,611 | 1,265 | 1,831 | 6,047 | 941.5 |
| FY26 | 11,941 | 8,443 | 1,508 | 1,990 | 6,902 | 1,087.9 |

## Row counts: raw

| Table | Rows |
|---|---|
| bw_contingent_worker | 43,423 |
| bw_rate_card | 23,408 |
| bw_service_order | 58,276 |
| bw_service_order_revision | 160,611 |
| bw_supplier | 23 |
| bw_timesheet_month | 632,365 |
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
| feed_bridgeway_keystone_event | 0 |
| ks_contingent_worker | 0 |
| ref_fringe_rate | 132 |
| ref_fringe_source | 215 |
| ref_fx_rate_constant | 17 |
| ref_fx_rate_daily | 24,820 |
| ref_fx_rate_monthly | 1,037 |
| ref_job_level_base_salary | 264 |
| ref_performance_bonus | 3 |
| ref_raw_column | 108 |
| ref_raw_table_lineage | 38 |
| ref_salary_range | 1,584 |
| ref_source_system | 5 |
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
