"""
Draw a static preview of the Headcount & FTE Walk dashboard for the README.

    pip install matplotlib
    python pipeline/run_pipeline.py --no-export
    python docs/make_headcount_walk_preview.py

The interactive version lives on Tableau Public; this image only gives a reader
of the repository the picture at a glance. Every number comes from the marts.
"""

from pathlib import Path

import duckdb
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.ticker import FuncFormatter  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "images" / "headcount_walk_preview.png"

SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_2 = "#52514e"
GRID = "#e6e5e1"
NEUTRAL = "#8a8984"      # totals: levels, not a category
INCREASE = "#2a78d6"     # categorical slot 1
DECREASE = "#e34948"     # red: decreases in the walk
SERIES_2 = "#eb6834"     # categorical slot 2

con = duckdb.connect(str(ROOT / "warehouse" / "arcadia.duckdb"), read_only=True)
FY = con.execute("SELECT MAX(fiscal_year) FROM marts.mart_dim_month").fetchone()[0]

walk = con.execute("""
    WITH w AS (
        SELECT w.*, m.fiscal_year FROM marts.mart_headcount_fte_walk AS w
        JOIN marts.mart_dim_month AS m USING (month_end_date)
        WHERE m.fiscal_year = ?
    ),
    bounds AS (SELECT MIN(month_end_date) AS first_m, MAX(month_end_date) AS last_m FROM w)
    SELECT
        SUM(headcount) FILTER (WHERE movement_category = 'Opening' AND month_end_date = first_m),
        SUM(headcount) FILTER (WHERE movement_category = 'Hires'),
        SUM(headcount) FILTER (WHERE movement_category = 'Voluntary Terminations'),
        SUM(headcount) FILTER (WHERE movement_category = 'Involuntary Terminations'),
        SUM(headcount) FILTER (WHERE movement_category = 'Internal Moves In'),
        SUM(headcount) FILTER (WHERE movement_category = 'Closing' AND month_end_date = last_m),
        SUM(fte)       FILTER (WHERE movement_category = 'Closing' AND month_end_date = last_m),
        SUM(headcount) FILTER (WHERE movement_category IN ('Opening', 'Closing')) / 2.0
            / COUNT(DISTINCT month_end_date)
    FROM w, bounds
""", [FY]).fetchone()
opening, hires, vol, invol, moves, closing, closing_fte, avg_hc = walk

trend = con.execute("""
    SELECT month_end_date, SUM(headcount) FROM marts.mart_headcount_fte_walk
    WHERE movement_category = 'Closing' GROUP BY 1 ORDER BY 1
""").fetchall()

by_function = con.execute("""
    WITH w AS (
        SELECT w.*, d.function_name FROM marts.mart_headcount_fte_walk AS w
        JOIN marts.mart_dim_month AS m USING (month_end_date)
        JOIN marts.mart_dim_department AS d USING (department_id)
        WHERE m.fiscal_year = ?
    )
    SELECT
        function_name,
        -COALESCE(SUM(headcount) FILTER (WHERE movement_category = 'Voluntary Terminations'), 0)
            / (SUM(headcount) FILTER (WHERE movement_category IN ('Opening', 'Closing')) / 2.0 / 12) AS vol_rate,
        -COALESCE(SUM(headcount) FILTER (WHERE movement_category = 'Involuntary Terminations'), 0)
            / (SUM(headcount) FILTER (WHERE movement_category IN ('Opening', 'Closing')) / 2.0 / 12) AS invol_rate
    FROM w
    WHERE function_name <> 'Executive'   -- a handful of officers; rates on tiny groups mislead
    GROUP BY 1 ORDER BY vol_rate + invol_rate
""", [FY]).fetchall()

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "text.color": INK,
    "axes.edgecolor": GRID, "axes.labelcolor": INK_2, "xtick.color": INK_2, "ytick.color": INK_2,
    "axes.spines.top": False, "axes.spines.right": False,
})
fig = plt.figure(figsize=(16, 9.6), facecolor=SURFACE)
fy = f"FY{str(FY)[-2:]}"

fig.text(0.04, 0.945, "Arcadia Systems  ·  Headcount & FTE Walk", fontsize=22, weight="bold")
fig.text(0.04, 0.912, f"{fy} (Jul {FY - 1} to Jun {FY}) · synthetic data · every line reconciles: "
         "opening + hires − leavers ± internal moves = closing", fontsize=12, color=INK_2)

kpis = [
    ("Closing headcount", f"{closing:,}", f"{closing - opening:+,} ({(closing - opening) / opening:+.1%}) in {fy}"),
    ("Closing FTE", f"{closing_fte:,.1f}", f"{closing - closing_fte:,.1f} FTE below headcount (part-time)"),
    ("Hires", f"{hires:,}", f"{hires / avg_hc:.1%} of average headcount"),
    ("Voluntary turnover", f"{-vol / avg_hc:.1%}", f"{-vol:,} leavers · annualized"),
    ("Internal moves", f"{moves:,}", "promotions and transfers · net zero"),
]
for i, (label, value, note) in enumerate(kpis):
    x = 0.04 + i * 0.188
    fig.patches.append(plt.Rectangle((x, 0.755), 0.175, 0.125, transform=fig.transFigure,
                                     facecolor="white", edgecolor=GRID, linewidth=1))
    fig.text(x + 0.012, 0.85, label, fontsize=11, color=INK_2)
    fig.text(x + 0.012, 0.795, value, fontsize=24, weight="bold")
    fig.text(x + 0.012, 0.768, note, fontsize=9.5, color=INK_2)

thousands = FuncFormatter(lambda v, _: f"{v / 1000:.1f}k")

# 1. Waterfall
ax = fig.add_axes([0.05, 0.08, 0.36, 0.58], facecolor=SURFACE)
steps = [("Opening", opening, "total"), ("Hires", hires, "up"), ("Voluntary\nterms", vol, "down"),
         ("Involuntary\nterms", invol, "down"), ("Closing", closing, "total")]
running = 0
for i, (name, value, kind) in enumerate(steps):
    if kind == "total":
        bottom, height, color, running = 0, value, NEUTRAL, value
    else:
        bottom = running if value > 0 else running + value
        height, color = abs(value), INCREASE if value > 0 else DECREASE
        running += value
    ax.bar(i, height, bottom=bottom, color=color, width=0.62, edgecolor=SURFACE, linewidth=2)
    label = f"{value:,}" if kind == "total" else f"{value:+,}"
    ax.text(i, bottom + height + 60, label, ha="center", va="bottom", fontsize=11, weight="bold")
ax.set_xticks(range(len(steps)), [s[0] for s in steps])
ax.set_ylim(10000, closing + 2900)
ax.yaxis.set_major_formatter(thousands)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.set_title(f"{fy} headcount walk (axis starts at 10k)", loc="left", fontsize=13, weight="bold", pad=12)

# 2. Monthly closing headcount
ax = fig.add_axes([0.47, 0.08, 0.24, 0.58], facecolor=SURFACE)
months = [t[0] for t in trend]
values = [t[1] for t in trend]
ax.plot(months, values, color=INCREASE, linewidth=2)
ax.scatter([months[-1]], [values[-1]], color=INCREASE, s=40, zorder=3)
ax.annotate(f"{values[-1]:,}", (months[-1], values[-1]), textcoords="offset points", xytext=(-4, 10),
            ha="right", fontsize=11, weight="bold")
dip = min(range(1, len(values) - 1), key=lambda i: values[i] - values[i - 1])
ax.annotate("FY24 restructuring", (months[dip], values[dip]), textcoords="offset points", xytext=(12, -28),
            fontsize=10, color=INK_2, arrowprops={"arrowstyle": "-", "color": INK_2, "linewidth": 0.8})
year_starts = [m for m in months if m.month == 7]
ax.set_xticks(year_starts, [f"FY{str(m.year + 1)[-2:]}" for m in year_starts])
ax.yaxis.set_major_formatter(thousands)
ax.grid(axis="y", color=GRID, linewidth=0.8)
ax.set_title("Month-end headcount, FY23 to date", loc="left", fontsize=13, weight="bold", pad=12)

# 3. Turnover by function
ax = fig.add_axes([0.82, 0.08, 0.15, 0.55], facecolor=SURFACE)
names = [r[0] for r in by_function]
vol_r = [r[1] for r in by_function]
inv_r = [r[2] for r in by_function]
ax.barh(names, vol_r, color=INCREASE, height=0.62, label="Voluntary", edgecolor=SURFACE, linewidth=2)
ax.barh(names, inv_r, left=vol_r, color=SERIES_2, height=0.62, label="Involuntary", edgecolor=SURFACE, linewidth=2)
for i, (v, n) in enumerate(zip(vol_r, inv_r)):
    ax.text(v + n + 0.003, i, f"{v + n:.1%}", va="center", fontsize=10)
ax.xaxis.set_major_formatter(FuncFormatter(lambda v, _: f"{v:.0%}"))
ax.set_xlim(0, max(v + n for v, n in zip(vol_r, inv_r)) * 1.3)
ax.grid(axis="x", color=GRID, linewidth=0.8)
ax.set_axisbelow(True)
ax.legend(loc="lower left", bbox_to_anchor=(-0.02, 1.0), ncol=2, frameon=False, fontsize=10,
          handlelength=1.2, borderaxespad=0.2)
ax.set_title(f"{fy} annualized turnover by function", loc="right", fontsize=13, weight="bold", pad=34)

fig.text(0.04, 0.012, "Source: thialp/people-analytics-warehouse · mart_headcount_fte_walk · "
         "static preview; the interactive dashboard is on Tableau Public", fontsize=9.5, color=INK_2)

OUT.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(OUT, dpi=110, facecolor=SURFACE)
print(f"Wrote {OUT.relative_to(ROOT)}")
