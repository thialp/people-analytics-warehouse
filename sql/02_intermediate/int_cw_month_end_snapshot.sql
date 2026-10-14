-- int_cw_month_end_snapshot
-- Grain: one row per contingent worker (Bridgeway worker ID) per month-end on which they
-- were working, as Bridgeway held it that day.
--
-- Bridgeway is the source of truth for who is a contingent worker (release 3, decision D4):
-- a worker counts on a month-end when the service order revision in effect that day says
-- the assignment has started and not ended. "In effect that day" means the history is never
-- restated: an extension approved after the old end date counts from its approval, as it did
-- in the month-end report of the time. Attributes come from the same revision: the cost
-- center typed on the order gives the department and country, the office is the order's.
--
-- Spend is an ANNUALIZED RUN-RATE at the month-end, on the same basis as employee pay and
-- the plan's contingent line: hourly rate x contracted hours x 52, or monthly rate x 12,
-- in USD at the month-end ECB rate (nominal) and at the constant rate set (constant).
-- Billed spend (what timesheets actually invoice) is in mart_cw_spend.
CREATE OR REPLACE TABLE intermediate.int_cw_month_end_snapshot AS
SELECT
    cal.month_end_date,
    cal.fiscal_year,
    o.bw_worker_id,
    r.service_order_id,
    r.revision_id,
    w.cw_type,
    o.supplier_id,
    cc.department_id,
    cc.country_code,
    r.cost_center_code                                                   AS cost_center_id,
    r.office_code                                                        AS location_id,
    r.role_family,
    r.seniority,
    r.assignment_start_date,
    r.assignment_end_date,
    r.rate_type,
    r.bill_rate,
    r.billing_currency,
    r.hours_per_week,
    CASE WHEN r.rate_type = 'Monthly' THEN r.bill_rate * 12
         ELSE r.bill_rate * r.hours_per_week * 52 END                    AS run_rate_local,
    fx.usd_per_local_actual                                              AS fx_rate_actual,
    fx.usd_per_local_constant                                            AS fx_rate_constant,
    CAST(CASE WHEN r.rate_type = 'Monthly' THEN r.bill_rate * 12
              ELSE r.bill_rate * r.hours_per_week * 52 END AS DOUBLE)
        * fx.usd_per_local_actual                                        AS run_rate_usd_nominal,
    CAST(CASE WHEN r.rate_type = 'Monthly' THEN r.bill_rate * 12
              ELSE r.bill_rate * r.hours_per_week * 52 END AS DOUBLE)
        * fx.usd_per_local_constant                                      AS run_rate_usd_constant
FROM intermediate.int_month_end_calendar AS cal
JOIN staging.stg_bw_service_order_revision AS r
  ON r.effective_start_date <= cal.month_end_date
 AND r.effective_end_date_filled >= cal.month_end_date
 AND r.status IN ('Approved', 'Closed')
 AND r.assignment_start_date <= cal.month_end_date
 AND r.assignment_end_date >= cal.month_end_date
JOIN staging.stg_bw_service_order AS o ON o.service_order_id = r.service_order_id
JOIN staging.stg_bw_contingent_worker AS w ON w.bw_worker_id = o.bw_worker_id
JOIN staging.stg_cost_center AS cc ON cc.cost_center_id = r.cost_center_code
LEFT JOIN staging.stg_fx_rate AS fx
  ON fx.currency_code = r.billing_currency
 AND fx.rate_date = cal.month_end_date;
