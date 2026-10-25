-- int_cw_close_run
-- Grain: one row per month-end close (Jun 2021 to Jun 2026).
--
-- A close is the warehouse run Finance's month-end report is built on: the 00:00 GMT run on the
-- 1st, which reads Bridgeway at 00:00, Keystone when Bridgeway is done (about 00:20) and Helix at
-- 00:00. Both HR systems are read as full effective-dated extracts, so a late run still sees the
-- month as it ended. A failed run reads nothing: the warehouse keeps that source's last good load,
-- so the close runs on the source as it stood then (a day stale after one failed night, more after
-- an outage), and the gaps that creates are routed to Integration (int_cw_load_gap). Helix is then
-- as of its last good read.
--
-- The latest close is also Current: the extract ends on Jun 30, 2026, a month-end.
CREATE OR REPLACE TABLE intermediate.int_cw_close_run AS
WITH cal AS (
    SELECT month_end_date, prior_month_end_date,
           CAST(month_end_date + 1 AS TIMESTAMP)                       AS close_run_at
    FROM intermediate.int_month_end_calendar
),
runs AS (
    SELECT c.month_end_date, r.*
    FROM cal AS c
    JOIN staging.stg_etl_load_run AS r
      ON r.scheduled_at IN (c.close_run_at, c.close_run_at + INTERVAL 20 MINUTE)
),
last_good AS (    -- each source's last read that worked, at or before the close run
    SELECT c.month_end_date, r.source_system, MAX(r.scheduled_at) AS read_at
    FROM cal AS c
    JOIN staging.stg_etl_load_run AS r
      ON r.status <> 'Failed' AND r.scheduled_at <= c.close_run_at + INTERVAL 20 MINUTE
     AND r.scheduled_at >= c.close_run_at - INTERVAL 10 DAY
    GROUP BY 1, 2
)
SELECT
    c.month_end_date,
    c.prior_month_end_date,
    c.close_run_at,
    c.month_end_date = MAX(c.month_end_date) OVER ()                  AS is_latest_close,
    bw.run_id                                                         AS bw_run_id,
    bw.status                                                         AS bw_load_status,
    bw.finished_at                                                    AS bw_finished_at,
    ks.run_id                                                         AS ks_run_id,
    ks.status                                                         AS ks_load_status,
    ks.finished_at                                                    AS ks_finished_at,
    hx.run_id                                                         AS hlx_run_id,
    hx.status                                                         AS hlx_load_status,
    CAST(gb.read_at AS DATE) - 1                                      AS bw_data_as_of,   -- a read at 00:00 holds the day before
    CAST(gk.read_at AS DATE) - 1                                      AS ks_data_as_of,
    gh.read_at                                                        AS hlx_read_at,
    CASE WHEN bw.status = 'Failed' THEN bw.run_id WHEN ks.status = 'Failed' THEN ks.run_id
         WHEN hx.status = 'Failed' THEN hx.run_id END                                  AS failed_run_id,
    CASE WHEN bw.status = 'Failed' THEN 'Bridgeway load failed: the close used Bridgeway as of '
              || STRFTIME(CAST(gb.read_at AS DATE) - 1, '%b %-d')
         WHEN ks.status = 'Failed' THEN 'Keystone load failed: the close used Keystone as of '
              || STRFTIME(CAST(gk.read_at AS DATE) - 1, '%b %-d')
         WHEN hx.status = 'Failed' THEN 'Helix read failed: tickets are as of '
              || STRFTIME(gh.read_at, '%b %-d %H:%M') || ' GMT'
         WHEN bw.status = 'Late' OR ks.status = 'Late' THEN 'Loaded late, finished '
              || STRFTIME(GREATEST(bw.finished_at, ks.finished_at), '%H:%M') || ' GMT; the data is complete'
         ELSE 'Loaded on time' END                                                     AS load_note
FROM cal AS c
LEFT JOIN runs AS bw ON bw.month_end_date = c.month_end_date AND bw.source_system = 'BW'
LEFT JOIN runs AS ks ON ks.month_end_date = c.month_end_date AND ks.source_system = 'KS'
LEFT JOIN runs AS hx ON hx.month_end_date = c.month_end_date AND hx.source_system = 'HLX'
LEFT JOIN last_good AS gb ON gb.month_end_date = c.month_end_date AND gb.source_system = 'BW'
LEFT JOIN last_good AS gk ON gk.month_end_date = c.month_end_date AND gk.source_system = 'KS'
LEFT JOIN last_good AS gh ON gh.month_end_date = c.month_end_date AND gh.source_system = 'HLX';
