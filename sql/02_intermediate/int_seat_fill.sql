-- int_seat_fill
-- Grain: one row per seat fill (an external hire or an internal move into a seat)
-- between the first and the last month-end.
--
-- For a backfill, the row sets the seat as it was when the prior incumbent left beside
-- the seat as it was filled: who left and why, how long the seat stood empty, whether
-- it was re-levelled, relocated or frozen in between, and a pay walk from the prior
-- incumbent's last pay to the new incumbent's first pay that adds up exactly:
--
--   new pay - prior pay = level effect + location effect + market effect + positioning
--
-- with mid(grade, office, FY) = the salary range midpoint for the grade in the office's
-- country and fiscal year, times the office's pay zone, in constant USD:
--   level effect     mid(new grade, prior office, exit FY) - mid(prior grade, prior office, exit FY)
--   location effect  mid(new grade, new office,   exit FY) - mid(new grade,   prior office, exit FY)
--   market effect    mid(new grade, new office,   fill FY) - mid(new grade,   new office,   exit FY)
--   positioning      (new pay - mid(new grade, new office, fill FY)) - (prior pay - mid(prior grade, prior office, exit FY))
-- Pay is the annual base salary rate (not x FTE), so a part-time incumbent compares
-- like for like. The order is level, then location, then market. Pays and the level,
-- location and market effects are rounded to the cent; positioning is what remains, so
-- the walk adds up exactly to the cent and the published CSV is the same on every run.
--
-- For a net-new seat, reuse_candidate says whether a seat it could have reused was
-- vacant when it was approved: same department, job family and country, a grade within
-- one, Open or Frozen for 90 days or more (a stale vacancy, not one still being recruited
-- for: at 90 days four in five matches are frozen seats). The oldest such seat is named.
CREATE OR REPLACE TABLE intermediate.int_seat_fill AS
WITH last_month_end AS (
    SELECT MIN(month_end_date) AS first_me, MAX(month_end_date) AS last_me FROM intermediate.int_month_end_calendar
),
seq AS (
    SELECT a.*,
           LAG(a.worker_id)     OVER w AS prior_worker_id,
           LAG(a.end_date)      OVER w AS prior_end_date,
           LAG(a.vacate_reason) OVER w AS prior_vacate_reason
    FROM staging.stg_position_assignment AS a
    WINDOW w AS (PARTITION BY a.position_id ORDER BY a.start_date)
),
fills AS (
    SELECT s.*
    FROM seq AS s, last_month_end AS m
    WHERE s.fill_type <> 'Initial'
      AND s.start_date > m.first_me AND s.start_date <= m.last_me
),
k AS (   -- constant-currency rate per currency
    SELECT DISTINCT currency_code, usd_per_local_constant AS usd FROM staging.stg_fx_rate
),
base AS (
    SELECT
        f.assignment_id                                                  AS fill_id,
        f.position_id,
        f.worker_id,
        f.start_date                                                     AS fill_date,
        CASE WHEN MONTH(f.start_date) >= 7 THEN YEAR(f.start_date) + 1 ELSE YEAR(f.start_date) END AS fill_fiscal_year,
        f.fill_type,
        f.requisition_id,
        CASE WHEN f.prior_worker_id IS NULL THEN 'Net-new' ELSE 'Backfill' END AS seat_type,
        r.opened_date                                                    AS requisition_opened_date,
        r.approved_date                                                  AS requisition_approved_date,
        DATE_DIFF('day', r.approved_date, f.start_date)                  AS time_to_fill_days,
        f.prior_worker_id,
        f.prior_end_date,
        f.prior_vacate_reason,
        CASE WHEN f.prior_end_date IS NULL THEN NULL
             WHEN MONTH(f.prior_end_date) >= 7 THEN YEAR(f.prior_end_date) + 1 ELSE YEAR(f.prior_end_date) END AS exit_fiscal_year,
        DATE_DIFF('day', f.prior_end_date, f.start_date) - 1             AS vacancy_days,
        -- the seat as the prior incumbent left it
        ps.department_id AS prior_department_id, ps.cost_center_id AS prior_cost_center_id,
        ps.location_id AS prior_location_id, ps.country_code AS prior_country_code,
        ps.currency_code AS prior_currency_code, ps.pay_zone_factor AS prior_pay_zone,
        ps.job_profile_id AS prior_job_profile_id, ps.job_family_code AS prior_job_family_code,
        ps.grade AS prior_grade, ps.is_manager_seat AS prior_is_manager_seat,
        -- the seat as it was filled
        ns.department_id AS new_department_id, ns.cost_center_id AS new_cost_center_id,
        ns.location_id AS new_location_id, ns.country_code AS new_country_code,
        ns.currency_code AS new_currency_code, ns.pay_zone_factor AS new_pay_zone,
        ns.job_profile_id AS new_job_profile_id, ns.job_family_code AS new_job_family_code,
        ns.grade AS new_grade, ns.is_manager_seat AS new_is_manager_seat,
        ns.created_date AS seat_created_date, ns.created_reason AS seat_created_reason,
        -- what happened to the seat while it was empty
        first_after.change_reason                                        AS first_change_after_vacate,
        EXISTS (SELECT 1 FROM intermediate.int_position_history AS h
                WHERE h.position_id = f.position_id AND h.status = 'Frozen'
                  AND h.effective_start_date > f.prior_end_date AND h.effective_start_date < f.start_date) AS was_frozen,
        -- pay
        pc.base_salary_annual_usd_constant                               AS prior_pay_usd_constant,
        nc.base_salary_annual_usd_constant                               AS new_pay_usd_constant
    FROM fills AS f
    JOIN staging.stg_requisition AS r ON r.requisition_id = f.requisition_id
    JOIN intermediate.int_position_history AS ns
      ON ns.position_id = f.position_id
     AND f.start_date BETWEEN ns.effective_start_date AND ns.effective_end_date_filled
    LEFT JOIN intermediate.int_position_history AS ps
      ON ps.position_id = f.position_id
     AND f.prior_end_date BETWEEN ps.effective_start_date AND ps.effective_end_date_filled
    LEFT JOIN intermediate.int_position_history AS first_after
      ON first_after.position_id = f.position_id
     AND first_after.effective_start_date = f.prior_end_date + INTERVAL 1 DAY
    LEFT JOIN intermediate.int_compensation_history_usd AS pc
      ON pc.worker_id = f.prior_worker_id
     AND f.prior_end_date BETWEEN pc.effective_start_date AND pc.effective_end_date_filled
    JOIN intermediate.int_compensation_history_usd AS nc
      ON nc.worker_id = f.worker_id
     AND f.start_date BETWEEN nc.effective_start_date AND nc.effective_end_date_filled
),
mids AS (
    SELECT
        b.*,
        r1.range_mid * b.prior_pay_zone * k1.usd AS mid_prior_grade_prior_office_exit,
        r2.range_mid * b.prior_pay_zone * k1.usd AS mid_new_grade_prior_office_exit,
        r3.range_mid * b.new_pay_zone   * k2.usd AS mid_new_grade_new_office_exit,
        r4.range_mid * b.new_pay_zone   * k2.usd AS mid_new_grade_new_office_fill
    FROM base AS b
    LEFT JOIN k AS k1 ON k1.currency_code = b.prior_currency_code
    LEFT JOIN k AS k2 ON k2.currency_code = b.new_currency_code
    LEFT JOIN staging.stg_salary_range AS r1
      ON r1.fiscal_year = b.exit_fiscal_year AND r1.grade = b.prior_grade AND r1.country_code = b.prior_country_code
    LEFT JOIN staging.stg_salary_range AS r2
      ON r2.fiscal_year = b.exit_fiscal_year AND r2.grade = b.new_grade AND r2.country_code = b.prior_country_code
    LEFT JOIN staging.stg_salary_range AS r3
      ON r3.fiscal_year = b.exit_fiscal_year AND r3.grade = b.new_grade AND r3.country_code = b.new_country_code
    LEFT JOIN staging.stg_salary_range AS r4
      ON r4.fiscal_year = b.fill_fiscal_year AND r4.grade = b.new_grade AND r4.country_code = b.new_country_code
),
reuse AS (   -- net-new seats approved while a seat they could have reused was vacant
    SELECT
        m.fill_id,
        COUNT(*)                                                         AS reuse_candidate_seats,
        ARG_MIN(h.position_id, h.status_since::VARCHAR || h.position_id)  AS reuse_candidate_position_id,
        MIN(h.status_since)                                              AS reuse_candidate_vacant_since
    FROM mids AS m
    JOIN intermediate.int_position_history AS h
      ON m.seat_type = 'Net-new'
     AND h.position_id <> m.position_id
     AND h.status IN ('Open', 'Frozen')
     AND m.requisition_approved_date BETWEEN h.effective_start_date AND h.effective_end_date_filled
     AND h.department_id   = m.new_department_id
     AND h.job_family_code = m.new_job_family_code
     AND h.country_code    = m.new_country_code
     AND ABS(h.grade - m.new_grade) <= 1
     AND h.status_since <= m.requisition_approved_date - INTERVAL 90 DAY   -- reuse threshold
    GROUP BY m.fill_id
)
SELECT
    m.* EXCLUDE (prior_currency_code, new_currency_code, prior_pay_usd_constant, new_pay_usd_constant,
                 mid_prior_grade_prior_office_exit, mid_new_grade_prior_office_exit,
                 mid_new_grade_new_office_exit, mid_new_grade_new_office_fill),
    CASE WHEN m.seat_type = 'Net-new' THEN NULL
         WHEN m.new_grade > m.prior_grade THEN 'Up'
         WHEN m.new_grade < m.prior_grade THEN 'Down'
         ELSE 'Same' END                                                 AS level_change,
    CASE WHEN m.seat_type = 'Net-new' THEN NULL
         WHEN m.new_location_id = m.prior_location_id THEN 'Same office'
         WHEN m.new_country_code = m.prior_country_code THEN 'Other office, same country'
         ELSE 'Other country' END                                        AS location_change,
    CASE WHEN m.seat_type = 'Net-new' THEN NULL
         WHEN m.first_change_after_vacate = 'Re-levelled for backfill' THEN 'Re-levelled'
         WHEN m.first_change_after_vacate = 'Relocated for backfill'   THEN 'Relocated'
         WHEN m.first_change_after_vacate = 'Frozen'                   THEN 'Frozen, then reopened'
         WHEN m.first_change_after_vacate = 'Vacated' AND m.vacancy_days <= 1
              AND m.requisition_opened_date = m.requisition_approved_date THEN 'Immediate refill'
         WHEN m.first_change_after_vacate = 'Vacated'                  THEN 'Backfill as is'
         ELSE 'Immediate refill' END                                     AS seat_decision,
    -- pay walk (backfills only), constant USD, exact to the cent
    w.prior_pay_usd_constant,
    w.new_pay_usd_constant,
    w.new_pay_usd_constant - w.prior_pay_usd_constant                    AS pay_change_usd_constant,
    w.level_effect_usd_constant,
    w.location_effect_usd_constant,
    w.market_effect_usd_constant,
    (w.new_pay_usd_constant - w.prior_pay_usd_constant) - w.level_effect_usd_constant
      - w.location_effect_usd_constant - w.market_effect_usd_constant    AS positioning_effect_usd_constant,
    COALESCE(u.reuse_candidate_seats, 0) > 0                             AS reuse_candidate,
    COALESCE(u.reuse_candidate_seats, 0)                                 AS reuse_candidate_seats,
    u.reuse_candidate_position_id,
    u.reuse_candidate_vacant_since
FROM mids AS m
CROSS JOIN LATERAL (
    SELECT
        CAST(ROUND(CAST(m.prior_pay_usd_constant AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS prior_pay_usd_constant,
        CAST(ROUND(CAST(m.new_pay_usd_constant   AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS new_pay_usd_constant,
        CAST(ROUND(CAST(m.mid_new_grade_prior_office_exit AS DECIMAL(38, 10))
                 - CAST(m.mid_prior_grade_prior_office_exit AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS level_effect_usd_constant,
        CAST(ROUND(CAST(m.mid_new_grade_new_office_exit AS DECIMAL(38, 10))
                 - CAST(m.mid_new_grade_prior_office_exit AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS location_effect_usd_constant,
        CAST(ROUND(CAST(m.mid_new_grade_new_office_fill AS DECIMAL(38, 10))
                 - CAST(m.mid_new_grade_new_office_exit AS DECIMAL(38, 10)), 2) AS DECIMAL(18, 2)) AS market_effect_usd_constant
) AS w
LEFT JOIN reuse AS u USING (fill_id);
