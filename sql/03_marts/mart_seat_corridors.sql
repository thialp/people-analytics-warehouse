-- mart_seat_corridors
-- Grain: one row per fiscal quarter, office the seat was in when its incumbent left, and
-- office it was filled in, for backfills whose office changed.
-- The map layer for Dashboard #3: where seats migrate when they are refilled (a San
-- Francisco seat refilled in Austin), with the level change and the location effect on
-- pay. Same-office backfills are left out: they draw no line. Quarters add up, so any
-- period is the sum of its quarters.
CREATE OR REPLACE TABLE marts.mart_seat_corridors AS
SELECT
    f.fill_fiscal_year                                       AS fiscal_year,
    cal.fiscal_quarter_label,
    f.location_change,
    f.prior_location_id                                      AS from_location_id,
    fl.office_name                                           AS from_office_name,
    fl.city                                                  AS from_city,
    fl.country_code                                          AS from_country_code,
    fl.country_name                                          AS from_country_name,
    fl.latitude                                              AS from_latitude,
    fl.longitude                                             AS from_longitude,
    fl.pay_zone_factor                                       AS from_pay_zone,
    f.new_location_id                                        AS to_location_id,
    tl.office_name                                           AS to_office_name,
    tl.city                                                  AS to_city,
    tl.country_code                                          AS to_country_code,
    tl.country_name                                          AS to_country_name,
    tl.latitude                                              AS to_latitude,
    tl.longitude                                             AS to_longitude,
    tl.pay_zone_factor                                       AS to_pay_zone,
    COUNT(*)                                                 AS seats,
    SUM(CASE WHEN f.level_change = 'Down' THEN 1 ELSE 0 END) AS seats_levelled_down,
    SUM(CASE WHEN f.level_change = 'Up'   THEN 1 ELSE 0 END) AS seats_levelled_up,
    SUM(CASE WHEN f.seat_decision = 'Relocated' THEN 1 ELSE 0 END) AS seats_relocated_for_backfill,
    SUM(f.pay_change_usd_constant)                           AS pay_change_usd_constant,
    SUM(f.location_effect_usd_constant)                      AS location_effect_usd_constant
FROM intermediate.int_seat_fill AS f
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = LAST_DAY(f.fill_date)
JOIN staging.stg_location AS fl ON fl.location_id = f.prior_location_id
JOIN staging.stg_location AS tl ON tl.location_id = f.new_location_id
WHERE f.seat_type = 'Backfill'
  AND f.location_change <> 'Same office'
GROUP BY ALL;
