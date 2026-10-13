"""
Control totals for the warehouse, written as a Markdown table.

Run after pipeline/run_pipeline.py. It reads the DuckDB file and prints:
  * row counts of every raw table and every mart
  * per fiscal year: opening and closing headcount, hires, voluntary and involuntary
    terminations, internal moves, closing FTE and the fiscal-year-end loaded cost
    (USD, constant currency)

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
    sum(case when w.movement_category = 'Hires' then w.headcount end)                       as hires,
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

    for schema in ("raw", "marts"):
        names = [r[0] for r in con.sql(
            f"select table_name from information_schema.tables where table_schema = '{schema}' order by 1"
        ).fetchall()]
        counts = [(n, con.sql(f"select count(*) from {schema}.{n}").fetchone()[0]) for n in names]
        print(f"\n## Row counts: {schema}\n")
        print(table(counts, ["Table", "Rows"]))


if __name__ == "__main__":
    main()
