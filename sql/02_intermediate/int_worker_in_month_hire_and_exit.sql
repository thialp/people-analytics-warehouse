-- int_worker_in_month_hire_and_exit
-- Workers whose whole employment fell between two month-ends. A month-end
-- walk cannot show them, so they are listed here and reported as a data note.
CREATE OR REPLACE TABLE intermediate.int_worker_in_month_hire_and_exit AS
SELECT
    cal.month_end_date,
    w.worker_id,
    w.original_hire_date,
    w.termination_date,
    w.termination_type
FROM staging.stg_worker AS w
JOIN intermediate.int_month_end_calendar AS cal
  ON w.original_hire_date >  cal.prior_month_end_date
 AND w.termination_date   <  cal.month_end_date
WHERE cal.prior_month_end_date IS NOT NULL;
