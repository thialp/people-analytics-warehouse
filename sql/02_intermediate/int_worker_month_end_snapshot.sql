-- int_worker_month_end_snapshot
-- Grain: one row per active worker per month-end.
--
-- This is the "as-of" join that turns effective-dated history into point-in-time
-- snapshots: for each month-end, pick the job record and the compensation record
-- that were in effect on that date, then attach FX and fringe rates for that date.
--
-- Pay measures are ANNUALIZED RUN-RATES at the month-end, not monthly cost:
--   base   = annual base salary (full-time rate) x FTE
--   loaded = base x (1 + fringe rate)
-- Each is stated in USD two ways:
--   nominal  = converted at that month-end's actual FX rate
--   constant = converted at the fixed plan rate, so FX movements are removed
CREATE OR REPLACE TABLE intermediate.int_worker_month_end_snapshot AS
SELECT
    cal.month_end_date,
    cal.fiscal_year,
    w.worker_id,
    w.is_executive_officer,
    j.position_id,
    j.department_id,
    j.location_id,
    loc.country_code,
    j.job_profile_id,
    jp.job_family,
    j.grade,
    j.fte,
    comp.comp_record_id,
    comp.currency_code,
    comp.base_salary_annual_local,
    fx.usd_per_local_actual                                    AS fx_rate_actual,
    fx.usd_per_local_constant                                  AS fx_rate_constant,
    fr.fringe_rate,
    rng.range_mid                                              AS range_mid_local,

    -- annualized run-rate measures
    comp.base_salary_annual_local * j.fte * fx.usd_per_local_actual                         AS base_usd_nominal,
    comp.base_salary_annual_local * j.fte * fx.usd_per_local_constant                       AS base_usd_constant,
    comp.base_salary_annual_local * j.fte * fx.usd_per_local_actual   * (1 + fr.fringe_rate) AS loaded_usd_nominal,
    comp.base_salary_annual_local * j.fte * fx.usd_per_local_constant * (1 + fr.fringe_rate) AS loaded_usd_constant,
    rng.range_mid * j.fte * fx.usd_per_local_constant                                       AS range_mid_usd_constant

FROM intermediate.int_month_end_calendar AS cal

-- who was employed on the month-end (termination date is the last day worked)
JOIN staging.stg_worker AS w
  ON w.original_hire_date <= cal.month_end_date
 AND (w.termination_date IS NULL OR w.termination_date >= cal.month_end_date)

-- the job record in effect on the month-end
JOIN staging.stg_job_history AS j
  ON j.worker_id = w.worker_id
 AND cal.month_end_date BETWEEN j.effective_start_date AND j.effective_end_date_filled

-- the compensation record in effect on the month-end
LEFT JOIN staging.stg_compensation_history AS comp
  ON comp.worker_id = w.worker_id
 AND cal.month_end_date BETWEEN comp.effective_start_date AND comp.effective_end_date_filled

LEFT JOIN staging.stg_location    AS loc ON loc.location_id   = j.location_id
LEFT JOIN staging.stg_job_profile AS jp  ON jp.job_profile_id = j.job_profile_id
LEFT JOIN staging.stg_fx_rate     AS fx
  ON fx.currency_code = comp.currency_code
 AND fx.rate_date     = cal.month_end_date
LEFT JOIN staging.stg_fringe_rate AS fr
  ON fr.country_code = loc.country_code
 AND fr.fiscal_year  = cal.fiscal_year
LEFT JOIN staging.stg_salary_range AS rng
  ON rng.fiscal_year  = cal.fiscal_year
 AND rng.grade        = j.grade
 AND rng.country_code = loc.country_code;
