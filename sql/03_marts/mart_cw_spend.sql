-- mart_cw_spend
-- Grain: one row per month x cost center x supplier x contingent worker type x role family x
-- billing currency.
--
-- What the contingent workforce costs, two ways, side by side:
--
--   billed in the month   what suppliers invoiced (bw_timesheet_month): hours, units (hours, or
--                         months for BPO), the amount in billing currency, and in USD at the
--                         month-end ECB rate (nominal) and the constant rate set (constant)
--   working at month-end  the workers Bridgeway counted on the month-end and their annualized
--                         bill run-rate (hourly rate x contracted hours x 52, or monthly rate
--                         x 12): the basis of the plan's contingent line and of the cost bridge
--
-- Billed spend is lower than the run-rate pro rata because timesheets carry time off and
-- partial months. A month's billing is attributed to the cost center, supplier and role on the
-- service order revision in effect at the month-end (or on the order's last revision once it has
-- ended; on its first for work billed before a late approval), as Bridgeway held it then. Time billed after a worker's last day (discrepancy CW11)
-- is included: it was invoiced. billed_amount_local adds up to bw_timesheet_month to the cent
-- (test 71).
CREATE OR REPLACE TABLE marts.mart_cw_spend AS
WITH ts AS (
    SELECT t.*, o.supplier_id, w.cw_type
    FROM staging.stg_bw_timesheet_month AS t
    JOIN staging.stg_bw_service_order AS o ON o.service_order_id = t.service_order_id
    JOIN staging.stg_bw_contingent_worker AS w ON w.bw_worker_id = o.bw_worker_id
),

-- the revision that places each timesheet: the latest in effect by the month-end (the last one
-- once the order has ended); for work billed before the order was approved (a renewal approved
-- after its first day), the order's first revision
placed AS (
    SELECT ts.*, r.cost_center_code AS cost_center_id, r.role_family
    FROM ts
    JOIN staging.stg_bw_service_order_revision AS r ON r.service_order_id = ts.service_order_id
    QUALIFY ROW_NUMBER() OVER (
        PARTITION BY ts.timesheet_id
        ORDER BY CASE WHEN r.effective_start_date <= ts.month_end_date THEN 0 ELSE 1 END,
                 CASE WHEN r.effective_start_date <= ts.month_end_date THEN r.revision_no END DESC,
                 r.revision_no) = 1
),

billed AS (
    SELECT p.month_end_date, p.cost_center_id, p.supplier_id, p.cw_type, p.role_family,
           p.billing_currency,
           COUNT(DISTINCT p.bw_worker_id)                                        AS workers_billed,
           SUM(p.billed_hours)                                                   AS billed_hours,
           SUM(p.billed_units)                                                   AS billed_units,
           SUM(p.billed_amount_local)                                            AS billed_amount_local,
           SUM(CAST(p.billed_amount_local AS DECIMAL(38, 10)) * fx.usd_per_local_actual)   AS billed_usd_nominal,
           SUM(CAST(p.billed_amount_local AS DECIMAL(38, 10)) * fx.usd_per_local_constant) AS billed_usd_constant
    FROM placed AS p
    JOIN staging.stg_fx_rate AS fx ON fx.currency_code = p.billing_currency AND fx.rate_date = p.month_end_date
    GROUP BY ALL
),

working AS (
    SELECT month_end_date, cost_center_id, supplier_id, cw_type, role_family, billing_currency,
           COUNT(*)                                                              AS workers_at_month_end,
           SUM(CAST(run_rate_local AS DECIMAL(38, 10)))                          AS run_rate_local,
           SUM(CAST(run_rate_usd_nominal AS DECIMAL(38, 10)))                    AS run_rate_usd_nominal,
           SUM(CAST(run_rate_usd_constant AS DECIMAL(38, 10)))                   AS run_rate_usd_constant
    FROM intermediate.int_cw_month_end_snapshot
    GROUP BY ALL
)

SELECT
    k.month_end_date,
    cal.fiscal_year,
    cal.fiscal_quarter_label,
    k.cost_center_id,
    cc.department_id,
    cc.country_code,
    k.supplier_id,
    sp.supplier_name,
    k.cw_type,
    k.role_family,
    k.billing_currency,
    COALESCE(b.workers_billed, 0)                                                AS workers_billed,
    CAST(COALESCE(b.billed_hours, 0) AS DECIMAL(18, 2))                          AS billed_hours,
    CAST(COALESCE(b.billed_units, 0) AS DECIMAL(18, 4))                          AS billed_units,
    CAST(COALESCE(b.billed_amount_local, 0) AS DECIMAL(18, 2))                   AS billed_amount_local,
    CAST(ROUND(COALESCE(b.billed_usd_nominal, 0), 2) AS DECIMAL(18, 2))          AS billed_usd_nominal,
    CAST(ROUND(COALESCE(b.billed_usd_constant, 0), 2) AS DECIMAL(18, 2))         AS billed_usd_constant,
    COALESCE(w.workers_at_month_end, 0)                                          AS workers_at_month_end,
    CAST(ROUND(COALESCE(w.run_rate_local, 0), 2) AS DECIMAL(18, 2))              AS run_rate_local,
    CAST(ROUND(COALESCE(w.run_rate_usd_nominal, 0), 2) AS DECIMAL(18, 2))        AS run_rate_usd_nominal,
    CAST(ROUND(COALESCE(w.run_rate_usd_constant, 0), 2) AS DECIMAL(18, 2))       AS run_rate_usd_constant
FROM (
    SELECT month_end_date, cost_center_id, supplier_id, cw_type, role_family, billing_currency FROM billed
    UNION
    SELECT month_end_date, cost_center_id, supplier_id, cw_type, role_family, billing_currency FROM working
) AS k
LEFT JOIN billed  AS b USING (month_end_date, cost_center_id, supplier_id, cw_type, role_family, billing_currency)
LEFT JOIN working AS w USING (month_end_date, cost_center_id, supplier_id, cw_type, role_family, billing_currency)
JOIN intermediate.int_month_end_calendar AS cal ON cal.month_end_date = k.month_end_date
JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = k.cost_center_id
JOIN staging.stg_bw_supplier AS sp ON sp.supplier_id = k.supplier_id
ORDER BY k.month_end_date, k.cost_center_id, k.supplier_id, k.cw_type, k.role_family, k.billing_currency;
