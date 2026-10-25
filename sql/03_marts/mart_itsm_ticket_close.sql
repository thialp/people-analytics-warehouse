-- mart_itsm_ticket_close
-- Grain: one row per month-end close x Helix ticket open at the close's read (New, In progress,
-- Pending, Reopened). Dashboard #6's ticket card: one dot per ticket by where it is fixed and how
-- long it has waited.
--
--   place        from the group working it at the read (a misrouted ticket sits in the wrong row
--                until it is reassigned)
--   groups       function, department and country of the contractor's gap at the close, else of
--                the contractor's cost center on the close; empty for tickets not linked to a
--                contractor (they show only when no group is chosen)
--   dot_x, dot_y the dot's position: the age band's column (0, 1, 2) and the place's row (2 Bridgeway
--                at the top, 1 Keystone, 0 Integration), packed inside the cell 20 to a line, oldest
--                first (dot_seq), so dots never overlap and a full cell reads as a count. Up to 160
--                per cell; the most at any close is 144
-- Executive officers' department (D-901) is excluded.
CREATE OR REPLACE TABLE marts.mart_itsm_ticket_close AS
WITH open_t AS (
    SELECT st.*, sb.title, sb.category_code, sb.category_name, sb.flag_code, sb.risk, sb.priority,
           sb.identity_id, sb.link_tier,
           ROW_NUMBER() OVER (PARTITION BY st.month_end_date, st.place, st.age_band
                              ORDER BY st.age_days DESC, st.ticket_number) AS dot_seq
    FROM intermediate.int_itsm_ticket_state AS st
    JOIN intermediate.int_itsm_ticket_subject AS sb USING (ticket_number)
    WHERE st.is_open
),
gap_group AS (
    SELECT month_end_date, contractor_key, MIN(cost_center_id) AS cost_center_id, MIN(gap_id) AS gap_id
    FROM marts.mart_cw_gap_close GROUP BY 1, 2
),
snap_group AS (
    SELECT month_end_date, identity_id, COALESCE(bw_cost_center_id, ks_cost_center_id) AS cost_center_id
    FROM intermediate.int_cw_reconciliation_snapshot
)
SELECT
    t.month_end_date,
    STRFTIME(t.month_end_date, '%b %Y')                                              AS close_label,
    r.is_latest_close,
    t.ticket_number,
    t.title,
    t.state,
    t.category_code,
    t.category_name,
    t.flag_code,
    t.risk,
    t.priority,
    t.place,
    CASE t.place WHEN 'Bridgeway' THEN 1 WHEN 'Keystone' THEN 2 ELSE 3 END           AS place_order,
    t.current_group,
    t.opened_at,
    t.age_days,
    t.age_band,
    CASE t.age_band WHEN '0 to 5 days' THEN 1 WHEN '6 to 30 days' THEN 2 ELSE 3 END  AS age_band_order,
    t.times_reopened,
    t.times_reassigned,
    t.link_tier,
    t.identity_id                                                                    AS contractor_key,
    gg.gap_id                                                                        AS linked_gap_id,
    COALESCE(gg.cost_center_id, sg.cost_center_id)                                   AS cost_center_id,
    cc.department_id,
    dep.department_name,
    dep.function_name,
    cc.country_code,
    co.country_name,
    t.dot_seq,
    (CASE t.age_band WHEN '0 to 5 days' THEN 0 WHEN '6 to 30 days' THEN 1 ELSE 2 END)
        + 0.05 + 0.9 * (((t.dot_seq - 1) % 20) + 0.5) / 20                             AS dot_x,
    (CASE t.place WHEN 'Bridgeway' THEN 2 WHEN 'Keystone' THEN 1 ELSE 0 END)
        + 0.9 - 0.8 * (FLOOR((t.dot_seq - 1) / 20) + 0.5) / 8                         AS dot_y
FROM open_t AS t
JOIN intermediate.int_cw_close_run AS r USING (month_end_date)
LEFT JOIN gap_group AS gg ON gg.month_end_date = t.month_end_date AND gg.contractor_key = t.identity_id
LEFT JOIN snap_group AS sg ON sg.month_end_date = t.month_end_date AND sg.identity_id = t.identity_id
LEFT JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = COALESCE(gg.cost_center_id, sg.cost_center_id)
LEFT JOIN staging.stg_department AS dep ON dep.department_id = cc.department_id
LEFT JOIN staging.stg_country AS co ON co.country_code = cc.country_code
WHERE COALESCE(cc.department_id, '') <> 'D-901'
ORDER BY t.month_end_date, place_order, t.age_days DESC, t.ticket_number;
