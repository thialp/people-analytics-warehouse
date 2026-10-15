-- int_cw_movement
-- Grain: one row per contingent worker per month, for every Bridgeway worker working at the
-- prior month-end, at the current month-end, or at both (int_cw_month_end_snapshot).
--
-- The contingent counterpart of int_worker_movement. A contingent worker's slice is
-- department x country (contingent workers have no job family or grade):
--
--   working at current only          -> Start        New engagement, or Returned after a lapse
--   working at prior only            -> End          Completed, Ended early, Lapsed: approved late
--                                    -> Conversion   hired as an employee this month (int_cw_conversion)
--   working at both, slice changed   -> Internal Move  Transfer (department), Location Change (country)
--
-- End reasons, in this order:
--   Conversion                    Keystone closed the record as Converted to employee and the person is
--                                 an employee at this month-end: booked out of Contingent, into Employee
--   Lapsed: approved late         the worker is working again at a later month-end: the extension or
--                                 renewal was approved after the old end date, so the month-end report
--                                 of the time did not count them (history is never restated)
--   Ended early                   the order carries an Early end revision in effect by the month-end
--   Completed                     anything else: the assignment reached its end date
-- A Start is "Returned after a lapse" when the worker was counted at an earlier month-end.
--
-- Office is carried for the location marts but is not part of the slice, as for employees.
-- Run-rates on both sides feed the cost bridge.
CREATE OR REPLACE TABLE intermediate.int_cw_movement AS
WITH month_pairs AS (
    SELECT month_end_date, prior_month_end_date
    FROM intermediate.int_month_end_calendar
    WHERE prior_month_end_date IS NOT NULL
),

snap AS (
    SELECT * FROM intermediate.int_cw_month_end_snapshot
),

pairs AS (
    SELECT mp.month_end_date, mp.prior_month_end_date, s.bw_worker_id
    FROM month_pairs AS mp JOIN snap AS s ON s.month_end_date = mp.prior_month_end_date
    UNION
    SELECT mp.month_end_date, mp.prior_month_end_date, s.bw_worker_id
    FROM month_pairs AS mp JOIN snap AS s ON s.month_end_date = mp.month_end_date
),

span AS (   -- first and last month-end each worker is counted
    SELECT bw_worker_id, MIN(month_end_date) AS first_me, MAX(month_end_date) AS last_me
    FROM snap GROUP BY 1
),

compared AS (
    SELECT
        pr.month_end_date,
        pr.prior_month_end_date,
        pr.bw_worker_id,
        COALESCE(c.cw_type, p.cw_type)                 AS cw_type,
        p.bw_worker_id IS NOT NULL                     AS in_prior,
        c.bw_worker_id IS NOT NULL                     AS in_current,
        p.service_order_id                             AS prior_service_order_id,
        c.service_order_id                             AS current_service_order_id,
        p.department_id AS prior_department_id,        c.department_id AS current_department_id,
        p.country_code  AS prior_country_code,         c.country_code  AS current_country_code,
        p.cost_center_id AS prior_cost_center_id,      c.cost_center_id AS current_cost_center_id,
        p.location_id   AS prior_location_id,          c.location_id   AS current_location_id,
        p.supplier_id   AS prior_supplier_id,          c.supplier_id   AS current_supplier_id,
        p.billing_currency AS prior_currency,          c.billing_currency AS current_currency,
        p.run_rate_local AS prior_run_rate_local,      c.run_rate_local AS current_run_rate_local,
        p.fx_rate_actual AS prior_fx_rate_actual,      c.fx_rate_actual AS current_fx_rate_actual,
        p.fx_rate_constant AS prior_fx_rate_constant,  c.fx_rate_constant AS current_fx_rate_constant,
        p.run_rate_usd_nominal  AS prior_run_rate_usd_nominal,
        c.run_rate_usd_nominal  AS current_run_rate_usd_nominal,
        p.run_rate_usd_constant AS prior_run_rate_usd_constant,
        c.run_rate_usd_constant AS current_run_rate_usd_constant,
        sp.first_me,
        sp.last_me,
        cv.worker_id                                   AS converted_to_worker_id
    FROM pairs AS pr
    JOIN span AS sp ON sp.bw_worker_id = pr.bw_worker_id
    LEFT JOIN snap AS p ON p.bw_worker_id = pr.bw_worker_id AND p.month_end_date = pr.prior_month_end_date
    LEFT JOIN snap AS c ON c.bw_worker_id = pr.bw_worker_id AND c.month_end_date = pr.month_end_date
    LEFT JOIN intermediate.int_cw_conversion AS cv
           ON cv.bw_worker_id = pr.bw_worker_id AND cv.month_end_date = pr.month_end_date AND cv.is_walk_conversion
)

SELECT
    m.*,
    CASE
        WHEN m.in_current AND NOT m.in_prior                     THEN 'Start'
        WHEN m.in_prior AND NOT m.in_current
             AND m.converted_to_worker_id IS NOT NULL            THEN 'Conversion'
        WHEN m.in_prior AND NOT m.in_current                     THEN 'End'
        WHEN m.prior_department_id <> m.current_department_id
          OR m.prior_country_code  <> m.current_country_code     THEN 'Internal Move'
        ELSE 'No Change'
    END AS movement_type,
    CASE
        WHEN m.in_current AND NOT m.in_prior
            THEN CASE WHEN m.first_me < m.month_end_date THEN 'Returned after a lapse' ELSE 'New engagement' END
        WHEN m.in_prior AND NOT m.in_current AND m.converted_to_worker_id IS NOT NULL
            THEN 'Contingent to Employee'
        WHEN m.in_prior AND NOT m.in_current AND m.last_me > m.month_end_date
            THEN 'Lapsed: approved late'
        WHEN m.in_prior AND NOT m.in_current
            THEN CASE WHEN EXISTS (SELECT 1 FROM staging.stg_bw_service_order_revision AS r
                                   WHERE r.service_order_id = m.prior_service_order_id
                                     AND r.revision_reason = 'Early end'
                                     AND r.effective_start_date <= m.month_end_date)
                      THEN 'Ended early' ELSE 'Completed' END
        WHEN m.prior_department_id <> m.current_department_id THEN 'Transfer'
        WHEN m.prior_country_code  <> m.current_country_code  THEN 'Location Change'
    END AS movement_reason
FROM compared AS m;
