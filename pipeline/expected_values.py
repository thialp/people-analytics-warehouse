"""
Expected values for the two published dashboards, written as Markdown check tables.

The pipeline runs it after the export (so CI fails if a check table is out of date); on its own:

    python pipeline/expected_values.py

It reads the marts in warehouse/arcadia.duckdb and writes

    docs/projects/headcount-fte-walk/expected_values.md   Dashboard #1, Headcount & FTE Walk
    docs/projects/compensation-walk/expected_values.md    Dashboard #2, Compensation Walk

Every number is computed with the same formula as the workbook calculation that shows it
(named next to each table), so after an extract refresh each card, title and tooltip can be
checked against one line here. Rebuilding the data regenerates the tables; nothing is typed by
hand. Arcadia Systems is fictional and all data is synthetic.
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse" / "arcadia.duckdb"
OUT_1 = ROOT / "docs" / "projects" / "headcount-fte-walk" / "expected_values.md"
OUT_2 = ROOT / "docs" / "projects" / "compensation-walk" / "expected_values.md"

MINUS = "−"  # the dashboards print a true minus sign


# ----------------------------------------------------------------------------- formatting
def n0(x: float) -> str:
    return f"{round(x):,}".replace("-", MINUS)


def n1(x: float) -> str:
    return f"{x:,.1f}".replace("-", MINUS)


def signed(x: float, fmt=n0) -> str:
    return ("+" if x >= 0 else "") + fmt(x)


def pct(x: float, d: int = 1) -> str:
    return f"{x * 100:.{d}f}%".replace("-", MINUS)


def usd(x: float, d: int = 0) -> str:
    s = f"${abs(x):,.{d}f}"
    return (MINUS if x < 0 else "") + s


def usd_m(x: float) -> str:
    return (MINUS if x < 0 else "") + f"${abs(x) / 1e6:,.1f}M"


def signed_usd(x: float, d: int = 0) -> str:
    return ("+" if x >= 0 else "") + usd(x, d)


def signed_usd_m(x: float) -> str:
    return ("+" if x >= 0 else "") + usd_m(x)


def month_label(d: date) -> str:
    return d.strftime("%b %Y")


def day_label(d: date) -> str:
    return f"{d:%b} {d.day}, {d.year}"


def fl(rows):
    """Decimals from DuckDB's exact sums become floats for formatting (the sums are exact to the cent)."""
    return [tuple(float(x) if isinstance(x, Decimal) else x for x in r) for r in rows]


def table(header: list[str], rows: list[list], align: str | None = None) -> str:
    align = align or "l" + "r" * (len(header) - 1)
    sep = ["---:" if a == "r" else "---" for a in align]
    lines = ["| " + " | ".join(header) + " |", "|" + "|".join(sep) + "|"]
    lines += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(lines)


# ------------------------------------------------------------------ Dashboard #1 (CSV walk)
class HeadcountWalk:
    """The Executive Summary measures (build book section 6) for one Start..End month range."""

    def __init__(self, con: duckdb.DuckDBPyConnection, start: str, end: str, function: str | None = None,
                 worker_type: str | None = "Employee"):
        """worker_type Employee (the default, the dashboard's employee view), Contingent, or None
        for the Total workforce. For contingent workers, hires are engagement starts and the
        leavers are in `ends`; `conv` is the signed conversions (+ into Employee, - out of Contingent)."""
        self.start, self.end = date.fromisoformat(start), date.fromisoformat(end)
        where = "w.month_end_date BETWEEN ? AND ?"
        params: list = [start, end]
        if worker_type:
            where += " AND w.worker_type = ?"
            params.append(worker_type)
        if function:
            where += " AND d.function_name = ?"
            params.append(function)
        row = con.execute(f"""
            SELECT
              COUNT(DISTINCT w.month_end_date)                                                          AS months,
              SUM(CASE WHEN w.movement_category IN ('Opening', 'Closing') THEN w.headcount END)         AS oc_sum,
              SUM(CASE WHEN w.movement_category = 'Opening' AND w.month_end_date = ? THEN w.headcount END) AS open_hc,
              SUM(CASE WHEN w.movement_category = 'Opening' AND w.month_end_date = ? THEN w.fte END)       AS open_fte,
              SUM(CASE WHEN w.movement_category = 'Closing' AND w.month_end_date = ? THEN w.headcount END) AS close_hc,
              SUM(CASE WHEN w.movement_category = 'Closing' AND w.month_end_date = ? THEN w.fte END)       AS close_fte,
              SUM(CASE WHEN w.movement_category IN ('Hires', 'Starts') THEN w.headcount END)       AS hires,
              SUM(CASE WHEN w.movement_category IN ('Hires', 'Starts') THEN w.fte END)             AS hires_fte,
              -SUM(CASE WHEN w.movement_category = 'Voluntary Terminations' THEN w.headcount END)  AS vol,
              -SUM(CASE WHEN w.movement_category = 'Voluntary Terminations' THEN w.fte END)        AS vol_fte,
              -SUM(CASE WHEN w.movement_category = 'Involuntary Terminations' THEN w.headcount END) AS invol,
              -SUM(CASE WHEN w.movement_category = 'Involuntary Terminations' THEN w.fte END)      AS invol_fte,
              SUM(CASE WHEN w.movement_category = 'Internal Moves In' THEN w.headcount END)        AS moves,
              SUM(CASE WHEN w.movement_category = 'Internal Moves In' AND w.movement_reason = 'Promotion'
                       THEN w.headcount END)                                                       AS promotions,
              -SUM(CASE WHEN w.movement_category = 'Ends' THEN w.headcount END)                    AS ends,
              SUM(CASE WHEN w.movement_category = 'Conversions' THEN w.headcount END)              AS conv
            FROM marts.mart_headcount_fte_walk AS w
            LEFT JOIN marts.mart_dim_department AS d ON d.department_id = w.department_id
            WHERE {where}
        """, [start, start, end, end, *params]).fetchone()
        names = ["months", "oc_sum", "open_hc", "open_fte", "close_hc", "close_fte",
                 "hires", "hires_fte", "vol", "vol_fte", "invol", "invol_fte", "moves", "promotions", "ends", "conv"]
        for k, v in zip(names, row):
            setattr(self, k, float(v or 0))
        self.avg_hc = self.oc_sum / 2 / self.months if self.months else 0
        ann = 12 / self.months if self.months else 0
        self.vol_rate = self.vol / self.avg_hc * ann if self.avg_hc else 0
        self.invol_rate = self.invol / self.avg_hc * ann if self.avg_hc else 0
        self.hire_rate = self.hires / self.avg_hc * ann if self.avg_hc else 0

    @property
    def label(self) -> str:
        if self.start.month == 7 and self.end.month == 6 and self.end.year == self.start.year + 1:
            return f"FY{str(self.end.year)[2:]}"
        return f"{month_label(self.start)} to {month_label(self.end)}"


def dashboard_1(con: duckdb.DuckDBPyConnection) -> str:
    months = [r[0] for r in con.execute(
        "SELECT month_end_date FROM marts.mart_dim_month ORDER BY 1").fetchall()]
    counts = {t: con.execute(f"SELECT COUNT(*) FROM marts.{t}").fetchone()[0] for t in (
        "mart_headcount_fte_walk", "mart_dim_month", "mart_dim_department", "mart_dim_country",
        "mart_dim_job_family", "mart_dim_grade")}
    last = months[-1]
    out = [f"""# Dashboard #1, Headcount & FTE Walk: expected values

Generated by `python pipeline/expected_values.py` from the marts; do not edit by hand. Arcadia Systems is fictional and all data is synthetic.

Check every card, title, caption and tooltip against these after refreshing the extract. Formulas are the ones in the [Executive Summary build book](executive_summary_build_book.md), section 6: rates are annualized on **average headcount** (each month's opening and closing, halved, averaged over the months), shares in tooltips use **opening** headcount, and FTE is shown to one decimal where the build book does.

## Data source

| File | Rows |
|---|---:|
""" + "\n".join(f"| `{t}.csv` | {c:,} |" for t, c in counts.items()) + f"""

Month-ends: {month_label(months[0])} to {month_label(last)} ({len(months)}). The trend shows all {len(months)}; the Start and End month lists offer the same {len(months)} months (set each parameter's list to **When workbook opens** from `month_end_date`, so it follows the data; a fixed list keeps the old 48 months). The earliest full fiscal year is FY{str(months[0].year + 1)[2:]}.
"""]

    def period(start: str, end: str, title: str) -> str:
        w = HeadcountWalk(con, start, end)
        leavers, leavers_fte = w.vol + w.invol, w.vol_fte + w.invol_fte
        net, net_fte = w.close_hc - w.open_hc, w.close_fte - w.open_fte
        verb = "outpaced" if w.hires >= leavers else "trailed"
        add = "adding" if net >= 0 else "losing"
        prior = (w.start.replace(day=1) - __import__("datetime").timedelta(days=1))
        s = [f"## {title}\n",
             table(["Item", "Headcount", "FTE"], [
                 [f"Opening ({month_label(prior)})", n0(w.open_hc), f"{n0(w.open_fte)} ({n1(w.open_fte)})"],
                 ["Hires", signed(w.hires), f"{signed(w.hires_fte)} ({n1(w.hires_fte)})"],
                 ["Voluntary leavers", n0(-w.vol), f"{n0(-w.vol_fte)} ({n1(w.vol_fte)})"],
                 ["Involuntary leavers", n0(-w.invol), f"{n0(-w.invol_fte)} ({n1(w.invol_fte)})"],
                 ["Conversions from contingent (release 3)", signed(w.conv), f"{signed(w.conv)} ({n1(w.conv)})"],
                 [f"Closing ({month_label(w.end)})", n0(w.close_hc), f"{n0(w.close_fte)} ({n1(w.close_fte)})"],
                 ["Waterfall title",
                  f"{w.label}: {n0(w.hires)} hires {verb} {n0(leavers)} leavers, {add} {n0(abs(net))} people",
                  f"{w.label} in FTE: {n0(w.hires_fte)} FTE hired, {n0(leavers_fte)} FTE left, {signed(net_fte)} FTE net"],
             ]),
             "",
             f"FTE ties: {n1(w.open_fte)} + {n1(w.hires_fte)} − {n1(w.vol_fte)} − {n1(w.invol_fte)} + {n1(w.conv)} conversions = {n1(w.close_fte)}. "
             "Every employee is 1.0 FTE (release 3 removed part-time), so FTE equals headcount. "
             "Since release 3, a contingent worker hired as an employee is a Conversion, not a Hire: "
             "the employee view's Hires exclude them.",
             ""]
        if w.months >= 3:
            s += [table(["Card", "Value", "Note (Headcount mode)"], [
                ["Closing headcount", n0(w.close_hc),
                 f"{signed(round((w.close_hc / w.open_hc - 1) * 1000) / 10, n1)}% vs {n0(w.open_hc)} at start"],
                ["Closing FTE", n1(w.close_fte), "Equals headcount: every employee is 1.0 FTE"],
                ["Hires", n0(w.hires), f"{pct(w.hire_rate)} annualized · {n0(w.hires_fte)} FTE"],
                ["Voluntary turnover (annualized)", pct(w.vol_rate),
                 f"{n0(w.vol)} left by choice · {n0(w.vol_fte)} FTE"],
                ["Internal moves", n0(w.moves),
                 f"{n0(w.promotions)} promotions · {n0(w.moves - w.promotions)} other moves"],
            ], "lrl"), "",
                f"Caption: *{n0(w.moves)} internal moves ({n0(w.promotions)} promotions, {n0(w.moves - w.promotions)} other) "
                f"move people between teams, so they net to zero at company level.*", "",
                "Waterfall tooltips (Headcount):", "",
                table(["Bar", "Line 1", "Line 2"], [
                    ["Opening", f"Active at the end of {month_label(prior)}",
                     f"{n0(w.open_hc)} people = {n1(w.open_fte)} FTE"],
                    ["Hires", f"{pct(w.hires / w.open_hc)} of opening headcount · about {n0(w.hires / w.months)} per month",
                     f"{n0(w.hires)} people = {n1(w.hires_fte)} FTE"],
                    ["Voluntary", f"{pct(w.vol / w.open_hc)} of opening headcount · about {n0(w.vol / w.months)} per month",
                     f"{n0(w.vol)} people = {n1(w.vol_fte)} FTE"],
                    ["Involuntary", f"{pct(w.invol / w.open_hc)} of opening headcount · about {n0(w.invol / w.months)} per month",
                     f"{n0(w.invol)} people = {n1(w.invol_fte)} FTE"],
                    ["Closing", f"Active at the end of {month_label(w.end)} · {signed(round((w.close_hc / w.open_hc - 1) * 1000) / 10, n1)}% vs opening",
                     f"{n0(w.close_hc)} people = {n1(w.close_fte)} FTE"],
                ], "lll"), ""]
            funcs = [r[0] for r in con.execute(
                "SELECT DISTINCT function_name FROM marts.mart_dim_department ORDER BY 1").fetchall()]
            rows = []
            for f in funcs:
                fw = HeadcountWalk(con, start, end, f)
                hidden = fw.avg_hc < 20
                rows.append((fw.vol_rate + fw.invol_rate, f, fw, hidden))
            rows.sort(key=lambda r: (r[3], -r[0]))
            s += [f"Turnover by function (sorted; groups averaging under 20 people hidden). Title: "
                  f"*{rows[0][1]} has the highest turnover in {w.label}*", "",
                  table(["Function", "Total", "Voluntary", "Involuntary", "Leavers (vol + invol)", "Average headcount"], [
                      [f, "hidden" if h else pct(t), "" if h else pct(fw.vol_rate), "" if h else pct(fw.invol_rate),
                       f"{n0(fw.vol)} + {n0(fw.invol)}", n1(fw.avg_hc)] for t, f, fw, h in rows]), ""]
        return "\n".join(s)

    def fy(y: int) -> tuple[str, str]:
        return (f"{y - 1}-07-31", f"{y}-06-30")

    out.append(period(*fy(last.year), f"FY{str(last.year)[2:]} (From Jul {last.year - 1}, To Jun {last.year})"))
    first_fy = months[0].year + 1
    out.append(period(*fy(first_fy), f"FY{str(first_fy)[2:]}, the first full year of history (From Jul {first_fy - 1}, To Jun {first_fy})"))
    out.append(period(f"{last.year - 1}-07-31", f"{last.year - 1}-08-31",
                      f"Short-range check (From Jul {last.year - 1}, To Aug {last.year - 1})"))
    same = HeadcountWalk(con, f"{last.year - 1}-07-31", f"{last.year - 1}-07-31")
    out.append(f"## Same month (From Jul {last.year - 1}, To Jul {last.year - 1})\n\n"
               f"Opening (Jun {last.year - 1}) {n0(same.open_hc)}, closing (Jul {last.year - 1}) {n0(same.close_hc)}.\n")

    fy_rows = []
    for y in range(first_fy, last.year + 1):
        w = HeadcountWalk(con, *fy(y))
        fy_rows.append([f"FY{str(y)[2:]}", n0(w.open_hc), n0(w.hires), n0(w.vol), n0(w.invol), n0(w.close_hc),
                        n1(w.close_fte), pct(w.vol_rate), n0(w.moves)])
    out.append("## Every fiscal year (Trend and quick checks)\n\n" + table(
        ["FY", "Opening", "Hires", "Voluntary", "Involuntary", "Closing", "Closing FTE", "Voluntary turnover", "Internal moves"],
        fy_rows) + "\n")

    # Release 3: the worker-type split (Employees / Contingent / Total)
    split_rows = []
    for y in range(first_fy, last.year + 1):
        e = HeadcountWalk(con, *fy(y))
        c = HeadcountWalk(con, *fy(y), worker_type="Contingent")
        t = HeadcountWalk(con, *fy(y), worker_type=None)
        split_rows.append([f"FY{str(y)[2:]}", n0(e.close_hc), n0(c.close_hc), n0(t.close_hc),
                           pct(c.close_hc / t.close_hc), n0(c.hires), n0(c.ends), n0(-c.conv),
                           signed(t.close_hc - t.open_hc)])
    c = HeadcountWalk(con, *fy(last.year), worker_type="Contingent")
    t = HeadcountWalk(con, *fy(last.year), worker_type=None)
    reasons = con.execute("""
        SELECT movement_category, movement_reason, SUM(headcount) FROM marts.mart_headcount_fte_walk
        WHERE worker_type = 'Contingent' AND month_end_date BETWEEN ? AND ?
          AND movement_category IN ('Starts', 'Ends', 'Conversions')
        GROUP BY ALL ORDER BY 1 DESC, 3 DESC""", list(fy(last.year))).fetchall()
    out.append(f"""## Worker type split (release 3: Employees, Contingent, Total)

The walk carries `worker_type`. **Employee** is the view above. **Contingent** counts contingent workers from Bridgeway as held at each month-end: Starts, Ends and Internal Moves, plus Conversions out to Employee. **Total** is both: a conversion is -1 Contingent and +1 Employee in the same month, so it never moves the Total. In a Total waterfall, use `walk_step` (Opening, Joined, Left, Moved out, Moved in, Converted, Closing) to put the two vocabularies on one axis.

""" + table(["FY", "Employees (closing)", "Contingent (closing)", "Total (closing)", "Contingent share",
             "Contingent starts", "Contingent ends", "Conversions", "Total net change"], split_rows) + f"""

FY{str(last.year)[2:]} contingent walk: {n0(c.open_hc)} + {n0(c.hires)} starts − {n0(c.ends)} ends − {n0(-c.conv)} conversions = {n0(c.close_hc)} (internal moves net to zero). Total: {n0(t.open_hc)} + {n0(t.hires)} joined − {n0(t.vol + t.invol + t.ends)} left = {n0(t.close_hc)}.

""" + table(["Contingent line", "Reason", f"FY{str(last.year)[2:]}"], [[a, b, signed(int(n))] for a, b, n in reasons], "llr") + "\n")
    return "\n".join(out)


# ------------------------------------------------------------- Dashboard #2 (walk Custom SQL)
def dashboard_2(con: duckdb.DuckDBPyConnection) -> str:
    to_me = con.execute("SELECT MAX(to_month_end) FROM marts.mart_compensation_walk").fetchone()[0]
    from_me = date(to_me.year - 1, to_me.month, to_me.day)
    rs, ra = con.execute("SELECT MIN(report_start_date), MIN(report_as_of_date) FROM marts.mart_compensation_walk").fetchone()
    pair = [from_me, to_me]
    fy = f"FY{str(to_me.year)[2:]}"
    rows = con.execute("""
        SELECT step_order, step, step_group, SUM(worker_count), SUM(headcount), SUM(fte),
               SUM(loaded_usd_constant), SUM(avg_loaded_usd_constant),
               SUM(loaded_usd_nominal), SUM(avg_loaded_usd_nominal),
               SUM(base_usd_constant), SUM(avg_base_usd_constant)
        FROM marts.mart_compensation_walk
        WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?
        GROUP BY step_order, step, step_group ORDER BY step_order""", pair).fetchall()
    rows = fl(rows)
    steps = {r[1]: r for r in rows}
    op, cl = steps["Opening"], steps["Closing"]
    counts = {t: con.execute(f"SELECT COUNT(*) FROM marts.{t}").fetchone()[0] for t in (
        "mart_compensation_walk", "mart_office_moves", "mart_region_walk", "mart_career_moves")}

    out = [f"""# Dashboard #2, Compensation Walk: expected values

Generated by `python pipeline/expected_values.py` from the marts; do not edit by hand. Arcadia Systems is fictional and all data is synthetic.

Default state: **{fy}** ({day_label(from_me)} to {day_label(to_me)}), view **Company**, cost **Loaded**, currency **Constant**. The data covers {day_label(rs)} to {day_label(ra)} (`report_start_date`, `report_as_of_date`).

## Data sources

| Custom SQL | Mart it matches | Rows |
|---|---|---:|
| `custom_sql_compensation_walk.sql` | `mart_compensation_walk` | {counts['mart_compensation_walk']:,} |
| `custom_sql_office_moves.sql` | `mart_office_moves` | {counts['mart_office_moves']:,} |
| `custom_sql_region_walk.sql` (new) | `mart_region_walk` | {counts['mart_region_walk']:,} |
| `custom_sql_career_moves.sql` (new) | `mart_career_moves` | {counts['mart_career_moves']:,} |

88 date pairs in each (Month over Month, Quarter over Quarter, Year over Year, Fiscal Year to Date); no Custom Range pairs.

## Walk, {fy}, Company (both lenses)

Pay per FTE is the step's `avg_loaded_usd_constant`; Total payroll is `loaded_usd_constant`.
"""]
    trs = []
    for r in rows:
        bal = r[1] in ("Opening", "Closing")
        trs.append([r[1], r[2], n0(r[3]), n0(r[4]),
                    usd(r[7], 2) if bal else signed_usd(r[7], 2),
                    usd_m(r[6]) if bal else signed_usd_m(r[6])])
    out.append(table(["Step", "Group", "People", "Headcount", "Pay per FTE", "Total payroll"], trs, "llrrrr") + "\n")

    d_fte, d_tot = cl[7] - op[7], cl[6] - op[6]
    out.append(f"Checks: Pay per FTE {usd(op[7], 2)} + steps = {usd(cl[7], 2)} (change {signed_usd(d_fte, 2)}); "
               f"Total payroll {usd(op[6], 2)} + steps = {usd(cl[6], 2)}.\n")

    def biggest(idx: int, fmt) -> str:
        g: dict[str, float] = {}
        for r in rows:
            if r[2] != "Balance":
                g[r[2]] = g.get(r[2], 0) + r[idx]
        names = {"Pay Rate": "raises", "Headcount": "hires and exits", "Career": "promotions and demotions"}
        top = sorted(g.items(), key=lambda kv: -abs(kv[1]))[:2]
        return ", ".join(f"{names.get(k, k.lower())} {fmt(v)}" for k, v in top)

    verb = lambda x: "rose" if x >= 0 else "fell"
    out.append("## Titles and headlines\n\n" + table(["Element", "Pay per FTE lens", "Total payroll lens"], [
        ["Waterfall headline",
         f"Average pay per FTE {verb(d_fte)} {usd(abs(d_fte))} ({signed(round(d_fte / op[7] * 1000) / 10, n1)}%)",
         f"Total payroll {verb(d_tot)} {usd_m(abs(d_tot))} ({signed(round(d_tot / op[6] * 1000) / 10, n1)}%)"],
        ["Waterfall subtitle, line 1",
         f"{day_label(from_me)} to {day_label(to_me)} · Pay per FTE = loaded cost ÷ FTE",
         f"{day_label(from_me)} to {day_label(to_me)} · Total payroll = loaded cost of all workers"],
        ["Waterfall subtitle, line 2 (two largest step groups)",
         f"Biggest moves: {biggest(7, signed_usd)}", f"Biggest moves: {biggest(6, signed_usd_m)}"],
        ["Page subtitle data note", f"Data covers {day_label(rs)} to {day_label(ra)}", "same"],
    ], "lll") + "\n")

    def drivers(idx: int, fmt) -> list[list]:
        ind = [r for r in rows if r[1] not in ("Opening", "Closing") and round(abs(r[idx]), 2) > 0]
        return [[i + 1, r[1], fmt(r[idx]), n0(r[3])] for i, r in enumerate(sorted(ind, key=lambda r: -abs(r[idx]))[:4])]

    out.append("## Top drivers card (four largest individual steps)\n\n**Pay per FTE**\n\n"
               + table(["Rank", "Step", "Value", "People"], drivers(7, signed_usd), "llrr") + "\n\n**Total payroll**\n\n"
               + table(["Rank", "Step", "Value", "People"], drivers(6, signed_usd_m), "llrr") + "\n")

    combos = []
    for cost, cur, col in (("Loaded", "Constant", "loaded_usd_constant"), ("Loaded", "Nominal", "loaded_usd_nominal"),
                           ("Base", "Constant", "base_usd_constant"), ("Base", "Nominal", "base_usd_nominal")):
        o, c, ao, ac = con.execute(f"""
            SELECT SUM(CASE WHEN step = 'Opening' THEN {col} END), SUM(CASE WHEN step = 'Closing' THEN {col} END),
                   SUM(CASE WHEN step = 'Opening' THEN avg_{col} END), SUM(CASE WHEN step = 'Closing' THEN avg_{col} END)
            FROM marts.mart_compensation_walk
            WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?""", pair).fetchone()
        o, c, ao, ac = fl([(o, c, ao, ac)])[0]
        combos.append([cost, cur, usd(ao, 2), usd(ac, 2), signed_usd(ac - ao, 2), usd_m(o), usd_m(c)])
    out.append("## Cost and Currency toggles\n\n" + table(
        ["Cost", "Currency", "Opening per FTE", "Closing per FTE", "Change", "Opening total", "Closing total"], combos,
        "llrrrrr") + "\n")

    # office moves
    om = con.execute("""
        SELECT SUM(workers), SUM(CASE WHEN flow_scope = 'Domestic' THEN workers END), MIN(open_headcount)
        FROM marts.mart_office_moves
        WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?""", pair).fetchone()
    routes = con.execute("""
        SELECT from_city, to_city, SUM(workers) AS w FROM marts.mart_office_moves
        WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?
        GROUP BY ALL ORDER BY w DESC, from_city, to_city LIMIT 5""", pair).fetchall()
    both = con.execute("""
        WITH r AS (SELECT LEAST(from_city, to_city) AS a, GREATEST(from_city, to_city) AS b, SUM(workers) AS w
                   FROM marts.mart_office_moves
                   WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ? GROUP BY ALL)
        SELECT a, b, w FROM r ORDER BY w DESC, a, b LIMIT 5""", pair).fetchall()
    total, dom, openhc = om
    out.append(f"""## Office moves panel

- Map headline: **{n0(total)} people changed office ({pct(total / openhc)} of headcount); {round(dom / total * 100)}% stayed inside one country**
- Subtitle: {n0(dom)} within one country · {n0(total - dom)} across a border
- `open_headcount` (Company): {n0(openhc)}, equal to the walk's Opening

Top 5 busiest routes (one direction). Headline: *{routes[0][0]} to {routes[0][1]} leads, {n0(routes[0][2])} people*

""" + table(["Rank", "Route", "People"], [[i + 1, f"{a} → {b}", n0(w)] for i, (a, b, w) in enumerate(routes)], "llr")
               + "\n\nBoth directions together: " + ", ".join(f"{a} ↔ {b} {n0(w)}" for a, b, w in both) + ".\n")

    reg = con.execute("""
        SELECT region, opening_headcount, closing_headcount,
               exits + transfers_out + region_moves_out AS departures
        FROM marts.mart_region_walk
        WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?
        ORDER BY closing_headcount * 1.0 / opening_headcount DESC""", pair).fetchall()
    o_all, c_all = sum(r[1] for r in reg), sum(r[2] for r in reg)
    out.append(f"## Growth by region (from the region walk)\n\nHeadline: **Arcadia overall {signed(round((c_all / o_all - 1) * 1000) / 10, n1)}% "
               f"({n0(o_all)} | {n0(c_all)})**\n\n" + table(
                   ["Region", "Opening", "Closing", "Growth", "Departures (exits + transfers out + region moves out)"],
                   [[r[0], n0(r[1]), n0(r[2]), signed(round((r[2] / r[1] - 1) * 1000) / 10, n1) + "%", n0(r[3])] for r in reg]) + "\n")
    tech = con.execute("""
        SELECT opening_headcount, closing_headcount FROM marts.mart_region_walk
        WHERE view_name = 'Function' AND group_name = 'Technology' AND region = 'North America'
          AND from_month_end = ? AND to_month_end = ?""", pair).fetchone()
    out.append(f"Follows the group: View Function, Group Technology, North America {n0(tech[0])} → {n0(tech[1])}.\n")

    cm = con.execute("""
        SELECT SUM(CASE WHEN move_type = 'Promotion' THEN moves END), SUM(CASE WHEN move_type = 'Demotion' THEN moves END),
               SUM(CASE WHEN into_director THEN moves END)
        FROM marts.mart_career_moves WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?""", pair).fetchone()
    flows = con.execute("""
        SELECT from_grade_level || ' → ' || to_grade_level, SUM(moves) FROM marts.mart_career_moves
        WHERE view_name = 'Company' AND move_type = 'Promotion' AND from_month_end = ? AND to_month_end = ?
        GROUP BY ALL ORDER BY 2 DESC LIMIT 5""", pair).fetchall()
    out.append(f"""## Career moves panel (new)

Headline: **{n0(cm[0])} promotions and {n0(cm[1])} demotions; {n0(cm[2])} reached Director and above**. The walk's Promotions step counts {n0(steps['Promotions'][3])} people (some were promoted twice).

""" + table(["Largest promotion steps", "Moves"], [[a, n0(b)] for a, b in flows]) + "\n")

    fy_rows = []
    for y in range(rs.year + 1, to_me.year + 1):
        r = con.execute("""
            SELECT SUM(CASE WHEN step = 'Opening' THEN headcount END), SUM(CASE WHEN step = 'Closing' THEN headcount END),
                   SUM(CASE WHEN step = 'Opening' THEN avg_loaded_usd_constant END),
                   SUM(CASE WHEN step = 'Closing' THEN avg_loaded_usd_constant END),
                   SUM(CASE WHEN step = 'Opening' THEN loaded_usd_constant END),
                   SUM(CASE WHEN step = 'Closing' THEN loaded_usd_constant END)
            FROM marts.mart_compensation_walk
            WHERE view_name = 'Company' AND from_month_end = ? AND to_month_end = ?""",
                        [date(y - 1, 6, 30), date(y, 6, 30)]).fetchone()
        r = fl([r])[0]
        fy_rows.append([f"FY{str(y)[2:]}", n0(r[0]), n0(r[1]), usd(r[2], 2), usd(r[3], 2),
                        signed(round((r[3] / r[2] - 1) * 1000) / 10, n1) + "%", usd_m(r[4]), usd_m(r[5])])
    out.append("## Every fiscal year (quick picks and the FY column of the Period popover)\n\n" + table(
        ["FY", "Opening", "Closing", "Opening per FTE", "Closing per FTE", "Change", "Opening total", "Closing total"],
        fy_rows) + "\n")
    return "\n".join(out)


def main(con: duckdb.DuckDBPyConnection | None = None) -> None:
    con = con or duckdb.connect(str(DB_PATH), read_only=True)
    OUT_1.write_text(dashboard_1(con))
    OUT_2.write_text(dashboard_2(con))
    print(f"Wrote {OUT_1.relative_to(ROOT)}\nWrote {OUT_2.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
