"""Export the numbers the Headcount & FTE Walk preview draws into build/headcount_data.json."""
import json
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[3]
con = duckdb.connect(str(ROOT / "warehouse" / "arcadia.duckdb"), read_only=True)
FY = con.execute("SELECT MAX(fiscal_year) FROM marts.mart_dim_month").fetchone()[0]


def rows(sql, params=()):
    cur = con.execute(sql, params)
    cols = [d[0] for d in cur.description]
    return [{k: (float(v) if v is not None and not isinstance(v, (int, float, str, bool)) else v)
             for k, v in zip(cols, r)} for r in cur.fetchall()]


WALK = """
    WITH w AS (
        SELECT w.*, m.fiscal_month
        FROM marts.mart_headcount_fte_walk AS w
        JOIN marts.mart_dim_month AS m USING (month_end_date)
        WHERE m.fiscal_year = ?
    )
    SELECT
        SUM(headcount) FILTER (WHERE movement_category = 'Opening' AND fiscal_month = 1)  AS opening,
        SUM(fte)       FILTER (WHERE movement_category = 'Opening' AND fiscal_month = 1)  AS opening_fte,
        SUM(headcount) FILTER (WHERE movement_category = 'Hires')                         AS hires,
        -SUM(headcount) FILTER (WHERE movement_category = 'Voluntary Terminations')       AS voluntary,
        -SUM(headcount) FILTER (WHERE movement_category = 'Involuntary Terminations')     AS involuntary,
        SUM(headcount) FILTER (WHERE movement_category = 'Internal Moves In')             AS moves,
        SUM(headcount) FILTER (WHERE movement_category = 'Internal Moves In' AND movement_reason = 'Promotion') AS promotions,
        SUM(headcount) FILTER (WHERE movement_category = 'Internal Moves In' AND movement_reason = 'Transfer')  AS transfers,
        SUM(fte)       FILTER (WHERE movement_category = 'FTE Changes')                   AS fte_changes,
        SUM(headcount) FILTER (WHERE movement_category = 'Closing' AND fiscal_month = 12) AS closing,
        SUM(fte)       FILTER (WHERE movement_category = 'Closing' AND fiscal_month = 12) AS closing_fte,
        SUM(part_time_headcount) FILTER (WHERE movement_category = 'Closing' AND fiscal_month = 12) AS closing_part_time,
        SUM(headcount) FILTER (WHERE movement_category IN ('Opening', 'Closing')) / 2.0
            / COUNT(DISTINCT month_end_date)                                              AS avg_headcount
    FROM w
"""
walk = rows(WALK, [FY])[0]

trend = rows("""
    SELECT strftime(w.month_end_date, '%Y-%m-%d') AS month_end_date, m.fiscal_year, SUM(w.headcount) AS closing
    FROM marts.mart_headcount_fte_walk AS w
    JOIN marts.mart_dim_month AS m USING (month_end_date)
    WHERE w.movement_category = 'Closing'
    GROUP BY ALL ORDER BY 1""")

# Annualized turnover by function; the Executive function (a handful of officers) is left
# out because rates on very small groups swing wildly.
by_function = rows("""
    WITH w AS (
        SELECT w.*, d.function_name
        FROM marts.mart_headcount_fte_walk AS w
        JOIN marts.mart_dim_month AS m USING (month_end_date)
        JOIN marts.mart_dim_department AS d USING (department_id)
        WHERE m.fiscal_year = ?
    ),
    f AS (
        SELECT
            function_name,
            SUM(headcount) FILTER (WHERE movement_category IN ('Opening', 'Closing')) / 2.0 / 12 AS avg_hc,
            -COALESCE(SUM(headcount) FILTER (WHERE movement_category = 'Voluntary Terminations'), 0)   AS vol,
            -COALESCE(SUM(headcount) FILTER (WHERE movement_category = 'Involuntary Terminations'), 0) AS invol
        FROM w
        WHERE function_name <> 'Executive'
        GROUP BY 1
    )
    SELECT function_name, avg_hc, vol / avg_hc AS vol_rate, invol / avg_hc AS invol_rate
    FROM f ORDER BY vol_rate + invol_rate DESC""", [FY])

out = Path(__file__).with_name("headcount_data.json")
out.write_text(json.dumps({"fy": FY, "walk": walk, "trend": trend, "by_function": by_function}, indent=1))
print(f"Wrote {out.name}: FY{str(FY)[-2:]}, {len(trend)} months, {len(by_function)} functions")
