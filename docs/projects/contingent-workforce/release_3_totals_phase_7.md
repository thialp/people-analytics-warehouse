# Control totals: release 3 after phase 7 (case study 4, 2026-10-14)

Employee and contingent totals are unchanged from [phase 6](release_3_totals_phase_6.md); the answer key changed slightly (a second ID counts from its first working day; a change that alters nothing marks nothing). New here: the discrepancies the warehouse finds on its own and their detection score. How: [case study 4](case_study_4.md). Rerun with `python pipeline/control_totals.py`.


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
| FY21 | 8,564 | 6,147 | 1,072 | 1,345 | 4,834 | 57.6 |
| FY22 | 9,288 | 6,646 | 1,128 | 1,514 | 5,292 | 740.0 |
| FY23 | 10,228 | 7,281 | 1,293 | 1,654 | 5,941 | 836.5 |
| FY24 | 9,910 | 7,020 | 1,191 | 1,699 | 4,970 | 894.7 |
| FY25 | 10,707 | 7,611 | 1,265 | 1,831 | 6,058 | 941.6 |
| FY26 | 11,941 | 8,443 | 1,508 | 1,990 | 6,907 | 1,087.9 |

## Keystone HR and the feed

Working on June 30 in each system (Bridgeway: the revision in effect that day; Keystone: active and past the contract start), feed events sent in the fiscal year, and workers with at least one seeded discrepancy open on June 30 (answer key, excluding changes in transit). FY21 feed counts are the whole year: the feed log covers every extracted worker's history.

| FY | Working in Bridgeway | Active in Keystone | Feed events | Applied late | Failed | Workers with an open discrepancy | % |
|---|---|---|---|---|---|---|---|
| FY21 | 8,564 | 8,532 | 11,870 | 744 | 156 | 281 | 3.3 |
| FY22 | 9,288 | 9,245 | 13,693 | 830 | 168 | 284 | 3.1 |
| FY23 | 10,228 | 10,170 | 14,958 | 897 | 208 | 320 | 3.1 |
| FY24 | 9,910 | 9,861 | 15,059 | 892 | 206 | 301 | 3.0 |
| FY25 | 10,707 | 10,644 | 16,397 | 960 | 222 | 325 | 3.0 |
| FY26 | 11,941 | 11,875 | 17,432 | 975 | 268 | 402 | 3.4 |

## Answer key

| Code | Discrepancy | Severity | Periods | Open at extract |
|---|---|---|---|---|
| CW00 | Change in transit | Expected | 21,136 | 0 |
| CW01 | Change arrived late | Data hygiene | 3,039 | 26 |
| CW02 | Extension never arrived | Access risk | 657 | 65 |
| CW03 | Early end never arrived | Access risk | 70 | 6 |
| CW04 | Ended but not closed in Bridgeway | Cost risk | 1,147 | 99 |
| CW05 | Changed in Keystone only | Cost risk | 2,148 | 219 |
| CW06 | Link ID missing or mistyped | Data hygiene | 213 | 49 |
| CW07 | One person, two IDs | Data hygiene | 54 | 26 |
| CW08 | Never reached Keystone | Access risk | 115 | 25 |
| CW09 | Keystone-only contingent worker | Access risk | 50 | 6 |
| CW10 | Over the duration cap | Compliance risk | 13 | 1 |
| CW11 | Billed after the assignment ended | Cost risk | 139 | 0 |
| CW12 | Attribute change never arrived | Data hygiene | 167 | 16 |

## Conversions to employee

Contingent workers hired as employees through a requisition, by the fiscal year of the hire, beside the contingent workers whose last Bridgeway day fell in the year and the external hires.

| FY | Conversions | CW exits | % of exits | External hires | % of hires |
|---|---|---|---|---|---|
| FY22 | 226 | 4,618 | 4.9 | 4,677 | 4.8 |
| FY23 | 226 | 5,038 | 4.5 | 5,539 | 4.1 |
| FY24 | 213 | 5,272 | 4.0 | 3,634 | 5.9 |
| FY25 | 244 | 5,283 | 4.6 | 4,376 | 5.6 |
| FY26 | 273 | 5,356 | 5.1 | 5,235 | 5.2 |

## Contingent line of the plan (Q4)

Contingent workers on June 30 in Bridgeway, against each plan version's Q4 line; spend is the planned annualized run-rate in USD at the version's FX.

| FY | Actual CW | Budget | RF1 | RF2 | RF3 | Budget spend $M | RF3 spend $M |
|---|---|---|---|---|---|---|---|
| FY22 | 9,288 | 9,742 | 9,515 | 9,466 | 9,303 | 901.6 | 837.2 |
| FY23 | 10,228 | 10,210 | 10,596 | 10,317 | 10,253 | 964.2 | 963.3 |
| FY24 | 9,910 | 10,746 | 10,166 | 10,148 | 9,926 | 1,042.8 | 948.4 |
| FY25 | 10,707 | 11,312 | 10,730 | 10,790 | 10,816 | 1,134.4 | 1,066.5 |
| FY26 | 11,941 | 12,673 | 12,182 | 12,020 | 11,977 | 1,313.9 | 1,250.5 |

## Workforce walk by worker type

Closing headcount on June 30, contingent starts and ends in the year, and conversions (into Employee and out of Contingent: they must match).

| FY | Employees | Contingent | Contingent starts | Contingent ends | Conversions in | Conversions out |
|---|---|---|---|---|---|---|
| FY22 | 25,061 | 9,288 | 5,376 | 4,427 | 225 | 225 |
| FY23 | 26,941 | 10,228 | 6,029 | 4,864 | 225 | 225 |
| FY24 | 27,217 | 9,910 | 5,076 | 5,181 | 213 | 213 |
| FY25 | 28,447 | 10,707 | 6,144 | 5,106 | 241 | 241 |
| FY26 | 30,014 | 11,941 | 7,033 | 5,529 | 270 | 270 |

## Total workforce cost growth mix (Company, year over year to June 30, $M nominal)

| FY | Factor | Shapley | Sequential | Order bias |
|---|---|---|---|---|
| FY22 | Opening cost | 3,137.0 | 3,137.0 | 0.0 |
| FY22 | Volume | 220.3 | 221.9 | 1.6 |
| FY22 | Workforce mix | -1.4 | -1.7 | -0.3 |
| FY22 | Location mix | -1.6 | -1.4 | 0.2 |
| FY22 | Level mix | -5.4 | -5.3 | 0.1 |
| FY22 | Rate | 98.0 | 103.2 | 5.2 |
| FY22 | Currency | -138.9 | -145.7 | -6.8 |
| FY22 | Closing cost | 3,308.1 | 3,308.1 | 0.0 |
| FY23 | Opening cost | 3,308.1 | 3,308.1 | 0.0 |
| FY23 | Volume | 277.1 | 271.7 | -5.5 |
| FY23 | Workforce mix | -1.6 | -1.8 | -0.2 |
| FY23 | Location mix | -13.2 | -13.6 | -0.4 |
| FY23 | Level mix | 5.2 | 5.9 | 0.6 |
| FY23 | Rate | 112.1 | 115.3 | 3.2 |
| FY23 | Currency | 36.2 | 38.3 | 2.2 |
| FY23 | Closing cost | 3,723.9 | 3,723.9 | 0.0 |
| FY24 | Opening cost | 3,723.9 | 3,723.9 | 0.0 |
| FY24 | Volume | -4.3 | -4.2 | 0.1 |
| FY24 | Workforce mix | 2.8 | 2.6 | -0.2 |
| FY24 | Location mix | -9.1 | -9.2 | -0.1 |
| FY24 | Level mix | 12.1 | 13.3 | 1.2 |
| FY24 | Rate | 118.7 | 118.3 | -0.4 |
| FY24 | Currency | -26.7 | -27.3 | -0.6 |
| FY24 | Closing cost | 3,817.4 | 3,817.4 | 0.0 |
| FY25 | Opening cost | 3,817.4 | 3,817.4 | 0.0 |
| FY25 | Volume | 214.1 | 208.5 | -5.6 |
| FY25 | Workforce mix | -2.6 | -2.5 | 0.1 |
| FY25 | Location mix | -23.6 | -24.5 | -0.9 |
| FY25 | Level mix | 21.8 | 22.2 | 0.4 |
| FY25 | Rate | 131.8 | 133.7 | 1.9 |
| FY25 | Currency | 86.4 | 90.5 | 4.1 |
| FY25 | Closing cost | 4,245.2 | 4,245.2 | 0.0 |
| FY26 | Opening cost | 4,245.2 | 4,245.2 | 0.0 |
| FY26 | Volume | 307.1 | 303.8 | -3.3 |
| FY26 | Workforce mix | -4.8 | -5.3 | -0.5 |
| FY26 | Location mix | -9.3 | -9.1 | 0.1 |
| FY26 | Level mix | 22.4 | 23.5 | 1.1 |
| FY26 | Rate | 139.8 | 145.2 | 5.5 |
| FY26 | Currency | -52.2 | -55.2 | -2.9 |
| FY26 | Closing cost | 4,648.1 | 4,648.1 | 0.0 |

## Case study 4: discrepancies found by the warehouse

Open on the extract date (the work list), and the rules scored against the answer key over every month-end (detected = flagged on the same worker and month-end; false flag = nothing seeded behind it).

| Code | Discrepancy | Severity | Open | Median age (days) |
|---|---|---|---|---|
| CW05 | Changed in Keystone only | Cost risk | 219 | 107 |
| CW04 | Ended but not closed in Bridgeway | Cost risk | 99 | 111 |
| CW02 | Extension never arrived | Access risk | 65 | 85 |
| CW06 | Link ID missing or mistyped | Data hygiene | 49 | 309 |
| CW07 | One person, two IDs | Data hygiene | 27 | 729 |
| CW01 | Change arrived late | Data hygiene | 26 | 4 |
| CW08 | Never reached Keystone | Access risk | 25 | 462 |
| CW12 | Attribute change never arrived | Data hygiene | 16 | 110 |
| CW03 | Early end never arrived | Access risk | 6 | 120 |
| CW09 | Keystone-only contingent worker | Access risk | 6 | 162 |
| CW11 | Billed after the assignment ended | Cost risk | 1 | 29 |
| CW10 | Over the duration cap | Compliance risk | 1 | 69 |

| Code | Discrepancy | Injected | Detected | False flags | Recall % |
|---|---|---|---|---|---|
| CW00 | Change in transit | 861 | 861 | 0 | 100.0 |
| CW01 | Change arrived late | 967 | 967 | 0 | 100.0 |
| CW02 | Extension never arrived | 2,829 | 2,829 | 0 | 100.0 |
| CW03 | Early end never arrived | 229 | 229 | 0 | 100.0 |
| CW04 | Ended but not closed in Bridgeway | 6,592 | 6,592 | 0 | 100.0 |
| CW05 | Changed in Keystone only | 11,312 | 11,312 | 0 | 100.0 |
| CW06 | Link ID missing or mistyped | 1,942 | 1,942 | 0 | 100.0 |
| CW07 | One person, two IDs | 1,333 | 1,333 | 42 | 100.0 |
| CW08 | Never reached Keystone | 1,154 | 1,154 | 0 | 100.0 |
| CW09 | Keystone-only contingent worker | 234 | 234 | 0 | 100.0 |
| CW10 | Over the duration cap | 54 | 54 | 0 | 100.0 |
| CW11 | Billed after the assignment ended | 139 | 139 | 0 | 100.0 |
| CW12 | Attribute change never arrived | 884 | 884 | 0 | 100.0 |

## Row counts: raw

| Table | Rows |
|---|---|
| bw_contingent_worker | 43,484 |
| bw_rate_card | 23,408 |
| bw_service_order | 58,276 |
| bw_service_order_revision | 160,499 |
| bw_supplier | 23 |
| bw_timesheet_month | 632,504 |
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
| fact_workforce_plan | 29,415 |
| feed_bridgeway_keystone_event | 106,357 |
| gen_cw_discrepancy_truth | 28,948 |
| ks_contingent_worker | 141,791 |
| ref_cw_discrepancy_type | 13 |
| ref_fringe_rate | 132 |
| ref_fringe_source | 215 |
| ref_fx_rate_constant | 17 |
| ref_fx_rate_daily | 24,820 |
| ref_fx_rate_monthly | 1,037 |
| ref_job_level_base_salary | 264 |
| ref_performance_bonus | 3 |
| ref_raw_column | 128 |
| ref_raw_table_lineage | 40 |
| ref_salary_range | 1,584 |
| ref_source_system | 6 |
| ref_tenure_increase | 7 |

## Row counts: marts

| Table | Rows |
|---|---|
| mart_career_moves | 34,532 |
| mart_compensation_walk | 108,918 |
| mart_cw_detection_score | 761 |
| mart_cw_discrepancy_detail | 6,908 |
| mart_cw_engagement_cap | 42,116 |
| mart_cw_reconciliation | 18,072 |
| mart_cw_spend | 216,025 |
| mart_dim_country | 22 |
| mart_dim_department | 32 |
| mart_dim_grade | 12 |
| mart_dim_job_family | 14 |
| mart_dim_location | 35 |
| mart_dim_month | 60 |
| mart_dim_org_unit | 44 |
| mart_fringe_rate | 132 |
| mart_headcount_fte_walk | 597,097 |
| mart_location_headcount | 3,856 |
| mart_mobility_flows | 2,538 |
| mart_office_moves | 89,611 |
| mart_org_leader_summary | 260 |
| mart_plan_vs_actual | 29,415 |
| mart_position_fill | 30,575 |
| mart_region_walk | 26,520 |
| mart_reporting_line | 161,196 |
| mart_seat_corridors | 821 |
| mart_vacancy_pool | 62,055 |
| mart_workforce_cost_bridge | 29,123 |
| mart_workforce_cost_growth_mix | 1,224 |
| mart_workforce_cost_snapshot | 233,866 |
