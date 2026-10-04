-- Constant currency means FX is held still, so the FX driver must be zero in
-- the constant-currency measures. Nominal and constant must also agree on the
-- plan-rate date, when actual and plan rates are the same.
SELECT month_end_date, department_id, driver, base_usd_constant, loaded_usd_constant,
       NULL AS loaded_usd_nominal
FROM marts.mart_workforce_cost_bridge
WHERE driver = 'FX Rate Changes'
  AND (base_usd_constant <> 0 OR loaded_usd_constant <> 0)

UNION ALL

SELECT month_end_date, department_id, 'Snapshot on plan-rate date', NULL, SUM(loaded_usd_constant),
       SUM(loaded_usd_nominal)
FROM marts.mart_workforce_cost_snapshot
WHERE month_end_date IN (SELECT rate_date FROM staging.stg_fx_rate      -- the date where every
                         GROUP BY rate_date                              -- currency's actual rate
                         HAVING BOOL_AND(usd_per_local_actual = usd_per_local_constant))  -- equals plan
GROUP BY month_end_date, department_id
HAVING ABS(SUM(loaded_usd_constant) - SUM(loaded_usd_nominal)) > 1
