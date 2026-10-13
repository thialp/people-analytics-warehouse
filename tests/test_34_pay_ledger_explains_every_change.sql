-- The pay ledger must explain every change in every worker's cost: between a worker's
-- first month-end and any later one, the drivers add up to the change in value, on all
-- four measures. Any gap means a pay event, FTE, fringe or FX movement was missed.
WITH v AS (
    SELECT
        s.worker_id, s.month_end_date,
        s.base_usd_nominal, s.base_usd_constant, s.loaded_usd_nominal, s.loaded_usd_constant,
        l.cum_promotion_base_nominal + l.cum_demotion_base_nominal + l.cum_tenure_base_nominal
          + l.cum_market_base_nominal + l.cum_relocation_base_nominal + l.cum_intl_transfer_base_nominal
          + l.cum_fte_base_nominal + l.cum_fx_base_nominal                                     AS explained_bn,
        l.cum_promotion_base_constant + l.cum_demotion_base_constant + l.cum_tenure_base_constant
          + l.cum_market_base_constant + l.cum_relocation_base_constant + l.cum_intl_transfer_base_constant
          + l.cum_fte_base_constant                                                            AS explained_bc,
        l.cum_promotion_loaded_nominal + l.cum_demotion_loaded_nominal + l.cum_tenure_loaded_nominal
          + l.cum_market_loaded_nominal + l.cum_relocation_loaded_nominal + l.cum_intl_transfer_loaded_nominal
          + l.cum_fte_loaded_nominal + l.cum_fringe_loaded_nominal + l.cum_fx_loaded_nominal   AS explained_ln,
        l.cum_promotion_loaded_constant + l.cum_demotion_loaded_constant + l.cum_tenure_loaded_constant
          + l.cum_market_loaded_constant + l.cum_relocation_loaded_constant + l.cum_intl_transfer_loaded_constant
          + l.cum_fte_loaded_constant + l.cum_fringe_loaded_constant                           AS explained_lc
    FROM intermediate.int_worker_month_end_snapshot AS s
    JOIN intermediate.int_worker_pay_ledger AS l USING (month_end_date, worker_id)
),
first_month AS (
    SELECT * FROM v QUALIFY ROW_NUMBER() OVER (PARTITION BY worker_id ORDER BY month_end_date) = 1
)
SELECT v.worker_id, v.month_end_date
FROM v
JOIN first_month AS f USING (worker_id)
WHERE ABS((v.base_usd_nominal    - f.base_usd_nominal)    - (v.explained_bn - f.explained_bn)) > 0.005
   OR ABS((v.base_usd_constant   - f.base_usd_constant)   - (v.explained_bc - f.explained_bc)) > 0.005
   OR ABS((v.loaded_usd_nominal  - f.loaded_usd_nominal)  - (v.explained_ln - f.explained_ln)) > 0.005
   OR ABS((v.loaded_usd_constant - f.loaded_usd_constant) - (v.explained_lc - f.explained_lc)) > 0.005
UNION ALL
-- and the ledger has exactly one row per snapshot row
SELECT 'ledger rows <> snapshot rows', NULL
WHERE (SELECT COUNT(*) FROM intermediate.int_worker_pay_ledger)
   <> (SELECT COUNT(*) FROM intermediate.int_worker_month_end_snapshot)
