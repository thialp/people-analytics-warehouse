-- The bonus plan is applied exactly:
--   * the bonus % is the plan's % for the rating (5% / 10% / 25%)
--   * amount = base x FTE x bonus % x proration, to the cent (half-cent rounding may differ)
--   * one review per worker per fiscal year, only for people employed on the review
--     date who joined at least three months before it (by March 31)
--   * Forfeited exactly when the worker left before the payout date
SELECT r.worker_id, r.fiscal_year, 'bonus % does not match the plan' AS issue
FROM staging.stg_performance_review AS r
JOIN staging.stg_performance_bonus AS p USING (rating)
WHERE r.bonus_pct <> p.bonus_pct
UNION ALL
SELECT worker_id, fiscal_year, 'bonus amount does not compute'
FROM staging.stg_bonus_payout
WHERE ABS(bonus_amount_local - ROUND(base_salary_annual_local * fte * bonus_pct * proration_factor, 2)) > 0.015
UNION ALL
SELECT worker_id, fiscal_year, 'more than one review in a year'
FROM staging.stg_performance_review GROUP BY ALL HAVING COUNT(*) > 1
UNION ALL
SELECT r.worker_id, r.fiscal_year, 'reviewed while not eligible'
FROM staging.stg_performance_review AS r
JOIN staging.stg_worker AS w USING (worker_id)
WHERE w.original_hire_date > MAKE_DATE(YEAR(r.review_date), 3, 31)
   OR (w.termination_date IS NOT NULL AND w.termination_date < r.review_date)
UNION ALL
SELECT b.worker_id, b.fiscal_year, 'payout status wrong'
FROM staging.stg_bonus_payout AS b
JOIN staging.stg_worker AS w USING (worker_id)
WHERE (b.payout_status = 'Forfeited') <> (w.termination_date IS NOT NULL AND w.termination_date < b.payout_date
                                          AND b.payout_status <> 'Scheduled')
