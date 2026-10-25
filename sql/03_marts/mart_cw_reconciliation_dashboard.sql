-- mart_cw_reconciliation_dashboard
-- Grain: one row per row_type x its own grain. Dashboard #4 in one data source (multi-select sets
-- work only inside one), the union of three marts and a scaffold, never summed across row types:
--
--   Gap         one per close x contractor x flag (mart_cw_gap_close): the Sankey, the gap list,
--               KPIs 3 to 5; gaps = 1
--   Population  one per close x cost center (mart_cw_gap_rate_close): the gap rate (KPI 2, the
--               timeline) and KPI 1; contractors_working is the denominator
--   Ticket      one per close x open ticket (mart_itsm_ticket_close): the ticket card; tickets = 1
--   Sankey      2,188 scaffold rows for the native Sankey (no close, no group), from the taxonomy:
--               sk_part Link (sk_level 1 flag to risk, 2 risk to place; sk_point 0 to 49 along the
--               two edges), Node (corners 0 to 3), Label, Header. Tableau positions every point
--               with FIXED LODs over the Gap rows.
--
-- flag_short: the short flag name every viewer sees (Gap and Sankey rows).
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
    NULL::INTEGER AS gaps_fixed_day_after, NULL::DOUBLE AS gap_rate_target, NULL::VARCHAR AS load_note,
    CASE flag_code WHEN 'F01' THEN 'One person, two IDs' WHEN 'F02' THEN 'Bridgeway ID mismatch' WHEN 'F03' THEN 'Not in Keystone' WHEN 'F04' THEN 'Billed after end date' WHEN 'F05' THEN 'Cost center differs' WHEN 'F06' THEN 'PID filled after end' WHEN 'F07' THEN 'Two active PID records' WHEN 'F08' THEN 'Ended in Keystone only' WHEN 'F09' THEN 'Active in Keystone only' END AS flag_short,
    NULL::VARCHAR AS sk_part, NULL::INTEGER AS sk_level, NULL::INTEGER AS sk_point
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
    gaps_open_prior_close, gaps_fixed_day_after, gap_rate_target, load_note,
    NULL, NULL, NULL, NULL
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
    NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
    NULL, NULL, NULL, NULL
FROM marts.mart_itsm_ticket_close
UNION ALL
SELECT
    'Sankey', NULL::DATE, NULL::VARCHAR, NULL::BOOLEAN, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, s.flag_code, s.flag_name, NULL::INTEGER, s.flag_label, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, s.risk, s.risk_order, s.place, s.place_order, s.place_label, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::BOOLEAN, NULL::DATE, NULL::INTEGER, NULL::VARCHAR, NULL::INTEGER, NULL::BOOLEAN, NULL::BOOLEAN, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::BOOLEAN, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::INTEGER, NULL::VARCHAR, NULL::INTEGER, NULL::DOUBLE, NULL::DOUBLE, 0, 0, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::INTEGER, NULL::DOUBLE, NULL::VARCHAR, CASE s.flag_code WHEN 'F01' THEN 'One person, two IDs' WHEN 'F02' THEN 'Bridgeway ID mismatch' WHEN 'F03' THEN 'Not in Keystone' WHEN 'F04' THEN 'Billed after end date' WHEN 'F05' THEN 'Cost center differs' WHEN 'F06' THEN 'PID filled after end' WHEN 'F07' THEN 'Two active PID records' WHEN 'F08' THEN 'Ended in Keystone only' WHEN 'F09' THEN 'Active in Keystone only' END, s.sk_part, s.sk_level, s.sk_point
FROM (SELECT 'Link' AS sk_part, l.*, n.sk_point FROM (SELECT CAST(1 AS INTEGER) AS sk_level, f.flag_code, f.flag_label, f.flag_name, f.risk, f.risk_order, p.place, p.place_order, p.place_label
           FROM (SELECT DISTINCT flag_code, flag_label, flag_name, risk, risk_order FROM marts.mart_cw_gap_close) AS f CROSS JOIN (SELECT DISTINCT place, place_order, place_label FROM marts.mart_cw_gap_close) AS p
         UNION ALL
         SELECT CAST(2 AS INTEGER), NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, r.risk, r.risk_order, p.place, p.place_order, p.place_label
           FROM (SELECT DISTINCT risk, risk_order FROM marts.mart_cw_gap_close) AS r CROSS JOIN (SELECT DISTINCT place, place_order, place_label FROM marts.mart_cw_gap_close) AS p) AS l
       CROSS JOIN (VALUES (0), (1), (2), (3), (4), (5), (6), (7), (8), (9), (10), (11), (12), (13), (14), (15), (16), (17), (18), (19), (20), (21), (22), (23), (24), (25), (26), (27), (28), (29), (30), (31), (32), (33), (34), (35), (36), (37), (38), (39), (40), (41), (42), (43), (44), (45), (46), (47), (48), (49)) AS n(sk_point)
     UNION ALL
     SELECT k.sk_part, d.*, k.sk_point FROM (SELECT CAST(1 AS INTEGER) AS sk_level, flag_code, flag_label, flag_name, risk, risk_order, NULL::VARCHAR AS place, NULL::INTEGER AS place_order, NULL::VARCHAR AS place_label FROM (SELECT DISTINCT flag_code, flag_label, flag_name, risk, risk_order FROM marts.mart_cw_gap_close) AS f
         UNION ALL SELECT CAST(2 AS INTEGER), NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, risk, risk_order, NULL::VARCHAR, NULL::INTEGER, NULL::VARCHAR FROM (SELECT DISTINCT risk, risk_order FROM marts.mart_cw_gap_close) AS r
         UNION ALL SELECT CAST(3 AS INTEGER), NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::INTEGER, place, place_order, place_label FROM (SELECT DISTINCT place, place_order, place_label FROM marts.mart_cw_gap_close) AS p) AS d
       CROSS JOIN (VALUES ('Node', 0), ('Node', 1), ('Node', 2), ('Node', 3), ('Label', 0)) AS k(sk_part, sk_point)
     UNION ALL
     SELECT 'Header', h.sk_level, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::VARCHAR, NULL::INTEGER, NULL::VARCHAR, NULL::INTEGER, NULL::VARCHAR, CAST(0 AS INTEGER)
       FROM (VALUES (1), (2), (3)) AS h(sk_level)) AS s
ORDER BY ALL;   -- the scaffold (DISTINCT, CROSS JOIN) has no natural order: sort so the CSV is the same on every run
