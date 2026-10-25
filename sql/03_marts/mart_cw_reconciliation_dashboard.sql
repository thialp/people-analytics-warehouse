-- mart_cw_reconciliation_dashboard
-- Grain: one row per row_type x its own grain. Dashboard #4 in one data source (multi-select sets
-- work only inside one), the union of three marts, never summed across row types:
--
--   Gap         one per close x contractor x flag (mart_cw_gap_close): the Sankey, the gap list,
--               KPIs 3 to 5; gaps = 1
--   Population  one per close x cost center (mart_cw_gap_rate_close): the gap rate (KPI 2, the
--               timeline) and KPI 1; contractors_working is the denominator
--   Ticket      one per close x open ticket (mart_itsm_ticket_close): the ticket card; tickets = 1
--
-- Every row carries the close and the group (function, department, country of the cost center),
-- so one set per group filters every card. tableau/custom_sql_cw_reconciliation_dashboard.sql
-- builds the same rows on SQL Server from the three reporting views.
CREATE OR REPLACE TABLE marts.mart_cw_reconciliation_dashboard AS
SELECT
    'Gap' AS row_type, month_end_date, close_label, is_latest_close,
    cost_center_id, department_id, department_name, function_name, country_code, country_name,
    gap_id, contractor_key, bw_worker_id, person_id, contractor_name, supplier_name, cw_type,
    flag_code, flag_name, flag_rank, flag_label, flag_count, flag_rank_prior_close, flag_count_prior_close,
    flag_rank_year_ago, flag_count_year_ago, risk, risk_order, place, place_order, place_label,
    cause_code, cause_name, timing_class, is_counted, since_date, days_open, open_band, days_since_end,
    was_open_prior_close, fixed_day_after_close, keystone_shows, bridgeway_has, evidence, next_step,
    ticket_number, ticket_title, ticket_state, ticket_status, has_ticket,
    NULL::VARCHAR AS priority, NULL::VARCHAR AS category_name, NULL::VARCHAR AS current_group, NULL::VARCHAR AS link_tier,
    NULL::INTEGER AS age_days, NULL::VARCHAR AS age_band, NULL::INTEGER AS age_band_order,
    NULL::DOUBLE AS dot_x, NULL::DOUBLE AS dot_y,
    1 AS gaps, 0 AS tickets,
    NULL::INTEGER AS contractors_working, NULL::INTEGER AS contractors_working_keystone,
    NULL::INTEGER AS working_bridgeway_only, NULL::INTEGER AS working_keystone_only,
    NULL::INTEGER AS contractors_with_gap, NULL::INTEGER AS gaps_counted, NULL::INTEGER AS gaps_clear_on_own,
    NULL::INTEGER AS gaps_no_ticket, NULL::INTEGER AS gaps_over_90_days, NULL::INTEGER AS gaps_open_prior_close,
    NULL::INTEGER AS gaps_fixed_day_after, NULL::DOUBLE AS gap_rate_target, NULL::VARCHAR AS load_note
FROM marts.mart_cw_gap_close
UNION ALL
SELECT
    'Population', month_end_date, close_label, is_latest_close,
    cost_center_id, department_id, department_name, function_name, country_code, country_name,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    0, 0,
    contractors_working, contractors_working_keystone, working_bridgeway_only, working_keystone_only,
    contractors_with_gap, gaps_counted, gaps_clear_on_own, gaps_no_ticket, gaps_over_90_days,
    gaps_open_prior_close, gaps_fixed_day_after, gap_rate_target, load_note
FROM marts.mart_cw_gap_rate_close
UNION ALL
SELECT
    'Ticket', month_end_date, close_label, is_latest_close,
    cost_center_id, department_id, department_name, function_name, country_code, country_name,
    linked_gap_id, contractor_key, NULL, NULL, NULL, NULL, NULL,
    flag_code, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, risk, NULL, place, place_order, place_label,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    ticket_number, title, state, NULL, NULL,
    priority, category_name, current_group, link_tier, age_days, age_band, age_band_order, dot_x, dot_y,
    0, 1,
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL
FROM marts.mart_itsm_ticket_close;
