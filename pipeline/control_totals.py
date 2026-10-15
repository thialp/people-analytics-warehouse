"""
Control totals for the warehouse, written as a Markdown table.

Run after pipeline/run_pipeline.py. It reads the DuckDB file and prints:
  * row counts of every raw table and every mart
  * per fiscal year: opening and closing headcount, hires, voluntary and involuntary
    terminations, internal moves, closing FTE and the fiscal-year-end loaded cost
    (USD, constant currency)
  * per fiscal year, the contingent workforce as Bridgeway VMS holds it (release 3):
    active at the fiscal year-end by type, engagements started, and billed spend

Use it to freeze the numbers before a change to the generator and to compare after:

    python pipeline/control_totals.py > before.md
    ... change the generator, rebuild ...
    python pipeline/control_totals.py > after.md
    diff before.md after.md
"""

from __future__ import annotations

from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse" / "arcadia.duckdb"

FY_TOTALS = """
with walk as (
    select
        case when month(month_end_date) >= 7 then year(month_end_date) + 1
             else year(month_end_date) end           as fiscal_year,
        month_end_date,
        movement_category,
        headcount,
        fte
    from marts.mart_headcount_fte_walk
    where worker_type = 'Employee'      -- employees; contingent workers have their own tables
),
months as (
    select fiscal_year, min(month_end_date) as first_me, max(month_end_date) as last_me
    from walk group by fiscal_year
),
cost as (
    select fiscal_year, sum(loaded_usd_constant) as loaded_usd_constant
    from marts.mart_workforce_cost_snapshot
    where is_fiscal_year_end
    group by fiscal_year
)
select
    'FY' || right(cast(w.fiscal_year as varchar), 2)                                        as fy,
    sum(case when w.movement_category = 'Opening' and w.month_end_date = m.first_me
             then w.headcount end)                                                          as opening_hc,
    sum(case when w.movement_category in ('Hires', 'Conversions') then w.headcount end)    as hires,   -- conversions are employee hires too
    -sum(case when w.movement_category = 'Voluntary Terminations' then w.headcount end)     as voluntary,
    -sum(case when w.movement_category = 'Involuntary Terminations' then w.headcount end)   as involuntary,
    sum(case when w.movement_category = 'Internal Moves In' then w.headcount end)           as moves_in,
    sum(case when w.movement_category = 'Closing' and w.month_end_date = m.last_me
             then w.headcount end)                                                          as closing_hc,
    round(sum(case when w.movement_category = 'Closing' and w.month_end_date = m.last_me
             then w.fte end), 2)                                                            as closing_fte,
    round(max(c.loaded_usd_constant) / 1e6, 1)                                              as fy_end_loaded_usd_m
from walk w
join months m using (fiscal_year)
left join cost c using (fiscal_year)
group by w.fiscal_year
order by w.fiscal_year
"""


CW_TOTALS = """
with fy as (
    select distinct case when month(month_end_date) >= 7 then year(month_end_date) + 1
                         else year(month_end_date) end as fiscal_year
    from staging.stg_bw_timesheet_month
),
ends as (select fiscal_year, make_date(fiscal_year, 6, 30) as fy_end from fy),
cur as (   -- the revision in effect on each fiscal year-end, working that day
    select e.fiscal_year, w.cw_type, w.bw_worker_id
    from ends e
    join staging.stg_bw_service_order_revision r
      on r.effective_start_date <= e.fy_end and r.effective_end_date_filled >= e.fy_end
     and r.status in ('Approved', 'Closed')
     and r.assignment_start_date <= e.fy_end and r.assignment_end_date >= e.fy_end
    join staging.stg_bw_service_order o using (service_order_id)
    join staging.stg_bw_contingent_worker w on w.bw_worker_id = o.bw_worker_id
),
starts as (
    select case when month(original_start_date) >= 7 then year(original_start_date) + 1
                else year(original_start_date) end as fiscal_year, count(*) as started
    from staging.stg_bw_contingent_worker where original_start_date is not null group by 1
),
spend as (
    select case when month(t.month_end_date) >= 7 then year(t.month_end_date) + 1
                else year(t.month_end_date) end as fiscal_year,
           sum(t.billed_amount_local * fx.usd_per_local_actual) as usd
    from staging.stg_bw_timesheet_month t
    join staging.stg_fx_rate fx on fx.currency_code = t.billing_currency and fx.rate_date = t.month_end_date
    group by 1
)
select 'FY' || right(cast(e.fiscal_year as varchar), 2),
       count(distinct c.bw_worker_id),
       count(distinct case when c.cw_type = 'Contractor' then c.bw_worker_id end),
       count(distinct case when c.cw_type = 'Consultant' then c.bw_worker_id end),
       count(distinct case when c.cw_type = 'BPO' then c.bw_worker_id end),
       max(s.started),
       round(max(p.usd) / 1e6, 1)
from ends e
left join cur c using (fiscal_year)
left join starts s using (fiscal_year)
left join spend p using (fiscal_year)
group by e.fiscal_year
order by e.fiscal_year
"""

KS_TOTALS = """
with ends as (select make_date(y, 6, 30) as fy_end, y as fiscal_year from range(2021, 2027) t(y)),
bw as (    -- working in Bridgeway on the fiscal year-end, by the revision in effect that day
    select e.fiscal_year, o.bw_worker_id
    from ends e
    join staging.stg_bw_service_order_revision r
      on r.effective_start_date <= e.fy_end and r.effective_end_date_filled >= e.fy_end
     and r.status in ('Approved', 'Closed')
     and r.assignment_start_date <= e.fy_end and r.assignment_end_date >= e.fy_end
    join staging.stg_bw_service_order o using (service_order_id)
),
ks as (    -- active in Keystone and past the contract start
    select e.fiscal_year, k.person_id
    from ends e
    join staging.stg_ks_contingent_worker k
      on k.effective_start_date <= e.fy_end and k.effective_end_date_filled >= e.fy_end
     and k.status = 'Active' and k.contract_start_date <= e.fy_end
),
feed as (
    select case when month(sent_date) >= 7 then year(sent_date) + 1 else year(sent_date) end as fiscal_year,
           count(*) as sent,
           count(*) filter (where outcome = 'Failed') as failed,
           count(*) filter (where outcome = 'Applied Late') as late
    from staging.stg_feed_bridgeway_keystone_event group by 1
),
open_dq as (   -- seeded discrepancies open on the year-end (answer key), on workers working in Bridgeway
    select e.fiscal_year, count(distinct t.bw_worker_id) as workers
    from ends e
    join staging.stg_gen_cw_discrepancy_truth t
      on t.start_date <= e.fy_end and t.end_date_filled >= e.fy_end and t.discrepancy_code <> 'CW00'
    join bw b on b.fiscal_year = e.fiscal_year and b.bw_worker_id = t.bw_worker_id
    group by 1
)
select 'FY' || right(cast(e.fiscal_year as varchar), 2),
       (select count(distinct bw_worker_id) from bw where bw.fiscal_year = e.fiscal_year),
       (select count(distinct person_id) from ks where ks.fiscal_year = e.fiscal_year),
       f.sent, f.late, f.failed, d.workers,
       round(100.0 * d.workers / (select count(distinct bw_worker_id) from bw where bw.fiscal_year = e.fiscal_year), 1)
from ends e
left join feed f using (fiscal_year)
left join open_dq d using (fiscal_year)
order by e.fiscal_year
"""

DQ_TOTALS = """
select t.discrepancy_code, y.discrepancy_name, y.severity, count(*) as periods,
       count(*) filter (where t.end_date is null) as open_at_extract
from staging.stg_gen_cw_discrepancy_truth t
join staging.stg_cw_discrepancy_type y using (discrepancy_code)
group by all order by 1
"""

CONV_TOTALS = """
select 'FY' || right(cast(fy as varchar), 2), conversions, exits, round(100.0 * conversions / exits, 1),
       external_hires, round(100.0 * conversions / external_hires, 1)
from (
    select case when month(w.original_hire_date) >= 7 then year(w.original_hire_date) + 1 else year(w.original_hire_date) end as fy,
           count(*) as conversions
    from staging.stg_candidate c join staging.stg_worker w using (worker_id)
    where c.candidate_source = 'Contingent conversion' group by 1
) conv
join (
    select case when month(last_day) >= 7 then year(last_day) + 1 else year(last_day) end as fy, count(*) as exits
    from (select o.bw_worker_id, max(r.assignment_end_date) as last_day
          from staging.stg_bw_service_order_revision r join staging.stg_bw_service_order o using (service_order_id)
          where r.is_current and r.status in ('Approved', 'Closed') group by 1)
    where last_day < date '2026-06-30' group by 1
) ends using (fy)
join (
    select case when month(filled_date) >= 7 then year(filled_date) + 1 else year(filled_date) end as fy, count(*) as external_hires
    from staging.stg_requisition where fill_source = 'External' and status = 'Filled' group by 1
) hires using (fy)
order by fy
"""

CW_PLAN_TOTALS = """
with q4 as (select distinct fiscal_year, quarter_end_date from staging.stg_workforce_plan where fiscal_quarter = 4),
actual as (
    select q.fiscal_year, count(distinct o.bw_worker_id) as cw
    from q4 q
    join staging.stg_bw_service_order_revision r
      on r.effective_start_date <= q.quarter_end_date and r.effective_end_date_filled >= q.quarter_end_date
     and r.status in ('Approved', 'Closed')
     and r.assignment_start_date <= q.quarter_end_date and r.assignment_end_date >= q.quarter_end_date
    join staging.stg_bw_service_order o using (service_order_id)
    group by 1
)
select 'FY' || right(cast(p.fiscal_year as varchar), 2), a.cw,
       sum(p.planned_cw_headcount) filter (where p.version_type = 'Budget'),
       sum(p.planned_cw_headcount) filter (where p.version_type = 'RF1'),
       sum(p.planned_cw_headcount) filter (where p.version_type = 'RF2'),
       sum(p.planned_cw_headcount) filter (where p.version_type = 'RF3'),
       round(sum(p.planned_cw_spend_usd) filter (where p.version_type = 'Budget') / 1e6, 1),
       round(sum(p.planned_cw_spend_usd) filter (where p.version_type = 'RF3') / 1e6, 1)
from staging.stg_workforce_plan p join actual a using (fiscal_year)
where p.fiscal_quarter = 4
group by p.fiscal_year, a.cw order by p.fiscal_year
"""

GROWTH_MIX = """
select 'FY' || right(cast(fiscal_year as varchar), 2), factor,
       round(shapley_effect_usd / 1e6, 1), round(sequential_effect_usd / 1e6, 1), round(order_bias_usd / 1e6, 1)
from marts.mart_workforce_cost_growth_mix
where view_name = 'Company' and month(to_month_end) = 6
order by fiscal_year, factor_order
"""

WALK_BY_TYPE = """
select 'FY' || right(cast(case when month(month_end_date) >= 7 then year(month_end_date) + 1
                              else year(month_end_date) end as varchar), 2) as fy,
       sum(headcount) filter (where worker_type = 'Employee' and movement_category = 'Closing' and month(month_end_date) = 6),
       sum(headcount) filter (where worker_type = 'Contingent' and movement_category = 'Closing' and month(month_end_date) = 6),
       sum(headcount) filter (where worker_type = 'Contingent' and movement_category = 'Starts'),
       -sum(headcount) filter (where worker_type = 'Contingent' and movement_category = 'Ends'),
       sum(headcount) filter (where worker_type = 'Employee' and movement_category = 'Conversions'),
       -sum(headcount) filter (where worker_type = 'Contingent' and movement_category = 'Conversions')
from marts.mart_headcount_fte_walk
group by 1 order by 1
"""

DETECTION = """
select discrepancy_code, any_value(discrepancy_name), sum(injected), sum(detected), sum(false_flags),
       round(100.0 * sum(detected) / nullif(sum(injected), 0), 1)
from marts.mart_cw_detection_score group by 1 order by 1
"""

OPEN_NOW = """
select discrepancy_code, discrepancy_name, severity, count(*), cast(median(age_days) as integer)
from marts.mart_cw_discrepancy_detail
where month_end_date = (select max(month_end_date) from marts.mart_cw_discrepancy_detail)
group by all order by 4 desc
"""


def table(rows, headers) -> str:
    out = ["| " + " | ".join(headers) + " |", "|" + "---|" * len(headers)]
    for r in rows:
        out.append("| " + " | ".join(
            f"{v:,}" if isinstance(v, int) else f"{float(v):,.1f}" if isinstance(v, float) or hasattr(v, "as_tuple")
            else str(v) for v in r) + " |")
    return "\n".join(out)


def main() -> None:
    con = duckdb.connect(str(DB_PATH), read_only=True)

    print("# Control totals\n")
    print("## Fiscal years\n")
    rows = con.sql(FY_TOTALS).fetchall()
    print(table(rows, ["FY", "Opening HC", "Hires", "Voluntary", "Involuntary", "Moves in",
                       "Closing HC", "Closing FTE", "FY-end loaded $M (constant)"]))

    print("\n## Contingent workforce (Bridgeway VMS)\n")
    print("Active on June 30 (the fiscal year-end), engagements started in the year, and billed spend at "
          "month-end FX. FY21 is one month (June 2021): timesheets start with the warehouse history.\n")
    print(table(con.sql(CW_TOTALS).fetchall(), ["FY", "Active CW", "Contractor", "Consultant", "BPO",
                                                "Engagements started", "Billed spend $M"]))

    print("\n## Keystone HR and the feed\n")
    print("Working on June 30 in each system (Bridgeway: the revision in effect that day; Keystone: active and past "
          "the contract start), feed events sent in the fiscal year, and workers with at least one seeded "
          "discrepancy open on June 30 (answer key, excluding changes in transit). FY21 feed counts are the "
          "whole year: the feed log covers every extracted worker's history.\n")
    print(table(con.sql(KS_TOTALS).fetchall(), ["FY", "Working in Bridgeway", "Active in Keystone", "Feed events",
                                                "Applied late", "Failed", "Workers with an open discrepancy", "%"]))
    print("\n## Answer key\n")
    print(table(con.sql(DQ_TOTALS).fetchall(), ["Code", "Discrepancy", "Severity", "Periods", "Open at extract"]))

    print("\n## Conversions to employee\n")
    print("Contingent workers hired as employees through a requisition, by the fiscal year of the hire, beside "
          "the contingent workers whose last Bridgeway day fell in the year and the external hires.\n")
    print(table(con.sql(CONV_TOTALS).fetchall(), ["FY", "Conversions", "CW exits", "% of exits",
                                                  "External hires", "% of hires"]))
    print("\n## Contingent line of the plan (Q4)\n")
    print("Contingent workers on June 30 in Bridgeway, against each plan version's Q4 line; spend is the planned "
          "annualized run-rate in USD at the version's FX.\n")
    print(table(con.sql(CW_PLAN_TOTALS).fetchall(), ["FY", "Actual CW", "Budget", "RF1", "RF2", "RF3",
                                                     "Budget spend $M", "RF3 spend $M"]))

    print("\n## Workforce walk by worker type\n")
    print("Closing headcount on June 30, contingent starts and ends in the year, and conversions (into Employee "
          "and out of Contingent: they must match).\n")
    print(table(con.sql(WALK_BY_TYPE).fetchall(), ["FY", "Employees", "Contingent", "Contingent starts",
                                                   "Contingent ends", "Conversions in", "Conversions out"]))
    print("\n## Total workforce cost growth mix (Company, year over year to June 30, $M nominal)\n")
    print(table(con.sql(GROWTH_MIX).fetchall(), ["FY", "Factor", "Shapley", "Sequential", "Order bias"]))

    print("\n## Case study 6: discrepancies found by the warehouse\n")
    print("Open on the extract date (the work list), and the rules scored against the answer key over every "
          "month-end (detected = flagged on the same worker and month-end; false flag = nothing seeded behind it).\n")
    print(table(con.sql(OPEN_NOW).fetchall(), ["Code", "Discrepancy", "Severity", "Open", "Median age (days)"]))
    print()
    print(table(con.sql(DETECTION).fetchall(), ["Code", "Discrepancy", "Injected", "Detected", "False flags", "Recall %"]))

    for schema in ("raw", "marts"):
        names = [r[0] for r in con.sql(
            f"select table_name from information_schema.tables where table_schema = '{schema}' order by 1"
        ).fetchall()]
        counts = [(n, con.sql(f"select count(*) from {schema}.{n}").fetchone()[0]) for n in names]
        print(f"\n## Row counts: {schema}\n")
        print(table(counts, ["Table", "Rows"]))


if __name__ == "__main__":
    main()
