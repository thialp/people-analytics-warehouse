-- Contingent workers get no raises: within a service order the bill rate changes only on a
-- 'Rate change' revision (a renegotiated extension). A renewal reprices on a new order, so a
-- new rate there is revision 0 of that order. Billing currency and rate type never change
-- inside an order.
WITH r AS (
    SELECT service_order_id, revision_no, revision_reason, bill_rate, billing_currency, rate_type,
           LAG(bill_rate)        OVER w AS prev_rate,
           LAG(billing_currency) OVER w AS prev_currency,
           LAG(rate_type)        OVER w AS prev_type
    FROM staging.stg_bw_service_order_revision
    WHERE status NOT IN ('Withdrawn', 'Rejected')
    WINDOW w AS (PARTITION BY service_order_id ORDER BY revision_no)
)
SELECT service_order_id, revision_no, revision_reason, prev_rate, bill_rate
FROM r
WHERE revision_no > 0
  AND ((bill_rate IS DISTINCT FROM prev_rate AND revision_reason <> 'Rate change')
       OR billing_currency IS DISTINCT FROM prev_currency
       OR rate_type IS DISTINCT FROM prev_type)
