-- Hires and terminations in the walk come from comparing snapshots. Recount
-- them straight from the worker master's hire and termination dates, and the
-- two must agree every month.
--   hire in month:        hired after the prior month-end, on or before this one,
--                         and still employed at this month-end
--   termination in month: employed at the prior month-end (termination date is
--                         the last day worked) and gone by this month-end
--                         (in-month hire-and-exits are excluded on both sides)
WITH walk AS (
    SELECT
        month_end_date,
        SUM(CASE WHEN movement_category = 'Hires'                    THEN headcount  ELSE 0 END) AS walk_hires,
        SUM(CASE WHEN movement_category = 'Voluntary Terminations'   THEN -headcount ELSE 0 END) AS walk_vol_terms,
        SUM(CASE WHEN movement_category = 'Involuntary Terminations' THEN -headcount ELSE 0 END) AS walk_invol_terms
    FROM marts.mart_headcount_fte_walk
    GROUP BY month_end_date
),
master AS (
    SELECT
        m.month_end_date,
        COUNT(*) FILTER (WHERE w.original_hire_date >  m.prior_month_end_date
                           AND w.original_hire_date <= m.month_end_date
                           AND (w.termination_date IS NULL OR w.termination_date >= m.month_end_date))  AS master_hires,
        COUNT(*) FILTER (WHERE w.original_hire_date <= m.prior_month_end_date
                           AND w.termination_date   >= m.prior_month_end_date
                           AND w.termination_date   <  m.month_end_date
                           AND w.termination_type   =  'Voluntary')                                     AS master_vol_terms,
        COUNT(*) FILTER (WHERE w.original_hire_date <= m.prior_month_end_date
                           AND w.termination_date   >= m.prior_month_end_date
                           AND w.termination_date   <  m.month_end_date
                           AND w.termination_type   =  'Involuntary')                                   AS master_invol_terms
    FROM marts.mart_dim_month AS m
    CROSS JOIN staging.stg_worker AS w
    GROUP BY m.month_end_date
)
SELECT walk.*, master.master_hires, master.master_vol_terms, master.master_invol_terms
FROM walk
JOIN master USING (month_end_date)
WHERE walk.walk_hires       <> master.master_hires
   OR walk.walk_vol_terms   <> master.master_vol_terms
   OR walk.walk_invol_terms <> master.master_invol_terms
