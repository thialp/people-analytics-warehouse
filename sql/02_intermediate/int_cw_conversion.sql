-- int_cw_conversion
-- Grain: one row per contingent worker hired as an employee, as the warehouse can see it.
--
-- Keystone records a conversion on the contingent record (inactive_reason Converted to
-- employee, converted_to_worker_id = the new employee). The warehouse links it to Bridgeway
-- through the Bridgeway worker ID Keystone stored; a conversion whose link is blank or
-- mistyped (discrepancy CW06) cannot be tied to the Bridgeway engagement and is left out:
-- the employee then counts as an ordinary hire.
--
-- month_end_date is the month the conversion lands in the walks: the month-end on which the
-- worker is an employee and no longer a contingent worker. It is a conversion in the walk
-- only when the person was a contingent worker at the prior month-end and an employee at this
-- one (is_walk_conversion): then the walk books one out of Contingent and one into Employee
-- in the same month and the total does not move.
CREATE OR REPLACE TABLE intermediate.int_cw_conversion AS
WITH conv AS (
    SELECT k.person_id, k.bw_worker_id, k.converted_to_worker_id AS worker_id
    FROM staging.stg_ks_contingent_worker AS k
    WHERE k.inactive_reason = 'Converted to employee'
    QUALIFY ROW_NUMBER() OVER (PARTITION BY k.person_id ORDER BY k.effective_start_date) = 1
)
SELECT
    c.person_id,
    c.bw_worker_id,
    c.worker_id,
    w.original_hire_date                                                 AS hire_date,
    cal.month_end_date,
    cal.prior_month_end_date,
    (EXISTS (SELECT 1 FROM intermediate.int_cw_month_end_snapshot AS s
             WHERE s.bw_worker_id = c.bw_worker_id AND s.month_end_date = cal.prior_month_end_date)
     AND NOT EXISTS (SELECT 1 FROM intermediate.int_cw_month_end_snapshot AS s
                     WHERE s.bw_worker_id = c.bw_worker_id AND s.month_end_date = cal.month_end_date)
     AND EXISTS (SELECT 1 FROM intermediate.int_worker_month_end_snapshot AS e
                 WHERE e.worker_id = c.worker_id AND e.month_end_date = cal.month_end_date)
     AND NOT EXISTS (SELECT 1 FROM intermediate.int_worker_month_end_snapshot AS e
                     WHERE e.worker_id = c.worker_id AND e.month_end_date = cal.prior_month_end_date))
                                                                         AS is_walk_conversion
FROM conv AS c
JOIN staging.stg_bw_contingent_worker AS b ON b.bw_worker_id = c.bw_worker_id
JOIN staging.stg_worker AS w ON w.worker_id = c.worker_id
JOIN intermediate.int_month_end_calendar AS cal
  ON cal.month_end_date = LAST_DAY(w.original_hire_date);
