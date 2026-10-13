-- mart_position_fill
-- Grain: one row per seat fill (external hire or internal move) between the first and
-- the last month-end. Dashboard #3 (Workforce Planning) reads it to answer: who did we
-- hire into which seat, was the seat new or vacated, and if vacated, who left it (and
-- why), where it was, at what level, and what the new incumbent costs against the last.
--
-- Fills are flows, so any period is the sum of its fills: filter on fill_date (or the
-- fiscal year and quarter) and add up. No date-pair grid is needed.
-- Pay fields are annual base salary rates in constant USD (backfills only); the four
-- effects add up exactly to pay_change_usd_constant (test 53).
-- Field reference: docs/projects/workforce-planning/
CREATE OR REPLACE TABLE marts.mart_position_fill AS
SELECT
    f.fill_id,
    f.fill_date,
    f.fill_fiscal_year                                       AS fiscal_year,
    cal.fiscal_quarter_label,
    cal.fiscal_period,
    f.fill_type,
    f.seat_type,
    f.seat_decision,
    f.was_frozen,
    f.requisition_id,
    f.requisition_opened_date,
    f.requisition_approved_date,
    f.time_to_fill_days,
    f.vacancy_days,
    f.position_id,
    f.seat_created_date,
    f.seat_created_reason,

    -- the new incumbent and the seat as filled
    f.worker_id,
    f.new_department_id                                      AS department_id,
    nd.department_name,
    nd.sub_function,
    nd.function_name,
    f.new_cost_center_id                                     AS cost_center_id,
    f.new_location_id                                        AS location_id,
    nl.office_name,
    nl.city,
    f.new_country_code                                       AS country_code,
    nl.country_name,
    nl.region,
    nl.latitude,
    nl.longitude,
    f.new_job_profile_id                                     AS job_profile_id,
    nj.job_title,
    nj.job_family,
    f.new_grade                                              AS grade,
    f.new_is_manager_seat                                    AS is_manager_seat,

    -- the prior incumbent and the seat as they left it (backfills)
    f.prior_worker_id,
    f.prior_end_date,
    f.prior_vacate_reason,
    f.prior_department_id,
    f.prior_location_id,
    pl.office_name                                           AS prior_office_name,
    pl.city                                                  AS prior_city,
    f.prior_country_code,
    pl.country_name                                          AS prior_country_name,
    pl.latitude                                              AS prior_latitude,
    pl.longitude                                             AS prior_longitude,
    f.prior_job_profile_id,
    pj.job_title                                             AS prior_job_title,
    f.prior_grade,
    f.prior_is_manager_seat,
    f.level_change,
    f.location_change,

    -- pay walk, prior incumbent -> new incumbent (constant USD, annual base rate)
    f.prior_pay_usd_constant,
    f.new_pay_usd_constant,
    f.pay_change_usd_constant,
    f.level_effect_usd_constant,
    f.location_effect_usd_constant,
    f.market_effect_usd_constant,
    f.positioning_effect_usd_constant,

    -- net-new seats approved while a matching seat stood vacant 90 days or more
    f.reuse_candidate,
    f.reuse_candidate_seats,
    f.reuse_candidate_position_id,
    f.reuse_candidate_vacant_since,

    -- vacancy chain
    c.chain_id,
    c.parent_fill_id,
    c.chain_depth,
    c.chain_length,
    c.chain_trigger
FROM intermediate.int_seat_fill AS f
JOIN intermediate.int_seat_vacancy_chain AS c USING (fill_id)
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = LAST_DAY(f.fill_date)
JOIN staging.stg_department   AS nd ON nd.department_id  = f.new_department_id
JOIN staging.stg_location     AS nl ON nl.location_id    = f.new_location_id
JOIN staging.stg_job_profile  AS nj ON nj.job_profile_id = f.new_job_profile_id
LEFT JOIN staging.stg_location    AS pl ON pl.location_id    = f.prior_location_id
LEFT JOIN staging.stg_job_profile AS pj ON pj.job_profile_id = f.prior_job_profile_id;
