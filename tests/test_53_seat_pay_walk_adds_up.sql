-- The seat pay walk adds up: for every backfill, level + location + market + positioning
-- equals the change from the prior incumbent's pay to the new incumbent's, to the cent.
-- A seat refilled at the same grade has no level effect; one refilled in the same office
-- has no location effect. Net-new seats have no walk.
SELECT fill_id, seat_type, level_change, location_change, pay_change_usd_constant,
       level_effect_usd_constant, location_effect_usd_constant, market_effect_usd_constant,
       positioning_effect_usd_constant
FROM marts.mart_position_fill
WHERE (seat_type = 'Backfill'
       AND (pay_change_usd_constant IS NULL
            OR ABS(pay_change_usd_constant - level_effect_usd_constant - location_effect_usd_constant
                   - market_effect_usd_constant - positioning_effect_usd_constant) > 0.005
            OR (level_change = 'Same' AND ABS(level_effect_usd_constant) > 0.005)
            OR (location_change = 'Same office' AND ABS(location_effect_usd_constant) > 0.005)))
   OR (seat_type = 'Net-new' AND (pay_change_usd_constant IS NOT NULL OR level_change IS NOT NULL))
