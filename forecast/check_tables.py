"""
Check tables for Dashboard #5, Seats to Fill: every number the page shows, for the selections the
build is tested on, computed from the forecast marts the way the page computes them.

    python forecast/check_tables.py      # writes docs/projects/workforce-planning/seats_to_fill_check_tables.md

Definitions (the page's):
  - Central numbers are the average of the 100 draws (they add up: the bridge and the functions
    reconcile). Ranges are P10 to P90 of the draws, summed over the selection per draw.
  - Plan attainment = forecast fills / the forward Budget's planned fills (net-new + backfills).
  - Time to fill: Kaplan-Meier over PIDs approved in the last four quarters, by ten-day period;
    "within N days" is the share at day N; the median wait is interpolated linearly between the two
    ten-day boundaries around 50%.
  - Backtest range for a selection: sum of means +- 1.2816 x sqrt(sum of variances + (shared cv x sum
    of means)^2), floored at zero; in range when the actual lies inside.
Arcadia Systems is fictional; all data is synthetic.
"""
from __future__ import annotations

import math
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
M = ROOT / "data" / "marts"
RAW = ROOT / "data" / "raw"
OUT = ROOT / "docs" / "projects" / "workforce-planning" / "seats_to_fill_check_tables.md"
Z = 1.2816

SELECTIONS = [
    ("Nothing chosen (all of Arcadia)", "TRUE"),
    ("Technology", "function_name = 'Technology'"),
    ("People without Talent Acquisition", "function_name = 'People' AND department_name <> 'Talent Acquisition'"),
    ("Asia Pacific", "region = 'Asia Pacific'"),
    ("Asia Pacific without Pune", "region = 'Asia Pacific' AND office_name <> 'Pune'"),
    ("Legal & Compliance in Latin America", "function_name = 'Legal & Compliance' AND region = 'Latin America'"),
]
BANDS = ["L1-L2", "L3-L4", "L5-L6", "L7+"]


def f0(x):
    return "" if x is None else f"{x:,.0f}"


def f1(x):
    return f"{x:,.1f}"


def pct(x):
    return f"{x * 100:.1f}%"


def connect():
    c = duckdb.connect()
    c.execute(f"CREATE VIEW dd AS SELECT department_id, department_name, function_name FROM read_csv('{M / 'mart_dim_department.csv'}', header=true)")
    c.execute(f"CREATE VIEW ll AS SELECT location_id, office_name, country_name, region FROM read_csv('{M / 'mart_dim_location.csv'}', header=true)")
    c.execute(f"CREATE VIEW rq AS SELECT * FROM read_csv('{RAW / 'ref_report_quarter.csv'}', header=true)")
    for t in ("mart_pid_fill_quarter", "mart_pid_forecast_draws", "mart_fill_survival", "mart_pid_forecast_backtest",
              "mart_pid_forecast_accuracy"):
        c.execute(f"CREATE VIEW {t} AS SELECT * FROM read_csv('{M / (t + '.csv')}', header=true)")
    return c


def scoped(t, w):
    return f"(SELECT x.* FROM {t} x JOIN dd USING (department_id) JOIN ll USING (location_id) WHERE {w})"


def km(c, w, band=None):
    b = f"AND level_band = '{band}'" if band else ""
    rows = c.execute(f"SELECT days_to, SUM(at_risk), SUM(filled) FROM {scoped('mart_fill_survival', w)} "
                     f"WHERE cohort_quarter_offset >= -3 {b} GROUP BY 1 ORDER BY 1").fetchall()
    s, out = 1.0, [(0, 0.0)]
    for d, r, f in rows:
        if r:
            s *= 1 - f / r
        out.append((d + 1, 1 - s))
    return out


def median_days(curve):
    prev = curve[0]
    for d, s in curve[1:]:
        if s >= 0.5:
            return prev[0] + (0.5 - prev[1]) / (s - prev[1]) * (d - prev[0])
        prev = (d, s)
    return None


def at(curve, day):
    v = [s for d, s in curve if d <= day]
    return v[-1] if v else 0.0


def stats(c, w):
    d = {}
    yr = c.execute(f"""
        WITH x AS (SELECT draw, SUM(filled) f, SUM(CASE WHEN quarter_offset = 4 THEN vacant_end END) v,
                          SUM(CASE WHEN quarter_offset = 1 THEN vacant_start END) vs, SUM(opened_backfill) ob,
                          SUM(opened_net_new) onn, SUM(opened_immediate) oi
                   FROM {scoped('mart_pid_forecast_draws', w)} GROUP BY 1)
        SELECT AVG(f), QUANTILE_CONT(f, .1), QUANTILE_CONT(f, .9), AVG(v), QUANTILE_CONT(v, .1), QUANTILE_CONT(v, .9),
               AVG(vs), AVG(ob), AVG(onn), AVG(oi), AVG(vs + ob + onn + oi), QUANTILE_CONT(vs + ob + onn + oi, .1),
               QUANTILE_CONT(vs + ob + onn + oi, .9) FROM x""").fetchone()
    keys = "fills fills_lo fills_hi vac vac_lo vac_hi waiting backfill netnew immediate to_fill to_fill_lo to_fill_hi".split()
    d.update(dict(zip(keys, yr)))
    q = c.execute(f"""
        SELECT quarter_offset, quarter_label, fiscal_year_label, SUM(filled), SUM(planned_net_new + planned_backfills), SUM(vacant_end)
        FROM {scoped('mart_pid_fill_quarter', w)} JOIN rq USING (quarter_offset) GROUP BY ALL ORDER BY 1""").fetchall()
    d["quarters"] = q
    fq = c.execute(f"""
        WITH x AS (SELECT quarter_offset, draw, SUM(filled) f, SUM(vacant_end) v FROM {scoped('mart_pid_forecast_draws', w)} GROUP BY 1, 2)
        SELECT quarter_offset, AVG(f), QUANTILE_CONT(f, .1), QUANTILE_CONT(f, .9), AVG(v), QUANTILE_CONT(v, .1), QUANTILE_CONT(v, .9)
        FROM x GROUP BY 1 ORDER BY 1""").fetchall()
    d["forecast"] = fq
    fy = {}
    for _, _, fyl, f, p, _ in q:
        a = fy.setdefault(fyl, [0, 0])
        a[0] += f or 0
        a[1] += p or 0
    d["fy"] = fy
    d["plan_fwd"] = fy[q[-1][2]][1]
    d["vac_now"] = [r[5] for r in q if r[0] == 0][0]
    d["fy_cur_fills"] = fy[[r[2] for r in q if r[0] == 0][0]][0]
    d["fy_cur_plan"] = fy[[r[2] for r in q if r[0] == 0][0]][1]
    d["curves"] = {b: km(c, w, b) for b in BANDS}
    d["curve_all"] = km(c, w)
    bt = c.execute(f"""SELECT quarter_offset, SUM(filled_mean), SUM(filled_var), MIN(filled_shared_cv), SUM(actual_filled)
                       FROM {scoped('mart_pid_forecast_backtest', w)} WHERE horizon = 1 GROUP BY 1 ORDER BY 1""").fetchall()
    d["backtest"] = []
    for qo, m, v, cv, act in bt:
        sd = math.sqrt(v + (cv * m) ** 2)
        d["backtest"].append((qo, max(0.0, m - Z * sd), m, m + Z * sd, act))   # a range never goes below zero
    return d


def main():
    c = connect()
    cal = c.execute(f"SELECT * FROM read_csv('{RAW / 'ref_report_calendar.csv'}', header=true)").fetchdf().iloc[0]
    qlabel = dict(c.execute("SELECT quarter_offset, quarter_label FROM rq").fetchall())
    fwd, cur = cal["forward_fiscal_year_label"], cal["current_fiscal_year_label"]
    L = [f"# Seats to Fill: check tables (phase 5)",
         "",
         f"Every number the page shows, for the selections the build is tested on, computed from the forecast marts the way the page computes them. "
         f"Report date {cal['report_as_of_label']}; forward year {fwd}. Generated by [`forecast/check_tables.py`](../../../forecast/check_tables.py); rerun it after a refresh. "
         "Arcadia Systems is fictional; all data is synthetic.",
         "",
         "**Definitions.** Central numbers are the average of the 100 draws (they add up, so the bridge and the functions reconcile). "
         "Ranges are P10 to P90 across the draws, summed over the selection per draw. Attainment is forecast fills over the forward Budget's planned fills. "
         "Time to fill is Kaplan–Meier over PIDs approved in the last four quarters; the median wait is interpolated between the ten-day boundaries around 50%. "
         "The backtest range for a selection is Σ mean ± 1.2816 × √(Σ variance + (shared cv × Σ mean)²).",
         ""]
    S = {name: stats(c, w) for name, w in SELECTIONS}

    L += ["## 1. KPI band", "",
          f"| Selection | Hero: fills {fwd} (range) | Attainment · plan | {cur} fills (att.) | PIDs to fill (range) · waiting | Vacant at year end (range) · change | Median wait · within 90 days |",
          "|---|---|---|---|---|---|---|"]
    for name, _ in SELECTIONS:
        d = S[name]
        att = d["fills"] / d["plan_fwd"]
        dv = d["vac"] - d["vac_now"]
        L.append(f"| {name} | **{f0(d['fills'])}** ({f0(d['fills_lo'])} to {f0(d['fills_hi'])}) | {att * 100:.0f}% of {f0(d['plan_fwd'])} "
                 f"({d['fills_lo'] / d['plan_fwd'] * 100:.0f}% to {d['fills_hi'] / d['plan_fwd'] * 100:.0f}%) | {f0(d['fy_cur_fills'])} "
                 f"({d['fy_cur_fills'] / d['fy_cur_plan'] * 100:.0f}%) | **{f0(d['to_fill'])}** ({f0(d['to_fill_lo'])} to {f0(d['to_fill_hi'])}) · "
                 f"{f0(d['waiting'])} | **{f0(d['vac'])}** ({f0(d['vac_lo'])} to {f0(d['vac_hi'])}) · {'+' if dv >= 0 else '−'}{f0(abs(dv))} "
                 f"| **{median_days(d['curve_all']):.0f} days** · {pct(at(d['curve_all'], 90))} |")
    L += ["", "Unrounded hero values to type-check a calculation: " +
          "; ".join(f"{n}: {S[n]['fills']:.2f}" for n, _ in SELECTIONS) + ".", ""]

    L += ["## 2. The seat bridge (hover on the vacant card)", "",
          "Waiting on the report date + backfills + net-new + immediate refills = PIDs to fill; minus filled = vacant at year end. Averages, so every row adds up exactly.", "",
          "| Selection | Waiting | + Backfills | + Net-new | + Immediate | = To fill | − Filled | = Vacant |", "|---|---:|---:|---:|---:|---:|---:|---:|"]
    for name, _ in SELECTIONS:
        d = S[name]
        L.append(f"| {name} | {f1(d['waiting'])} | {f1(d['backfill'])} | {f1(d['netnew'])} | {f1(d['immediate'])} | {f1(d['to_fill'])} | "
                 f"{f1(d['fills'])} | {f1(d['vac'])} |")
    L.append("")

    L += ["## 3. Fiscal-year chips (attainment) on the main chart", "",
          "| Selection | " + " | ".join(S[SELECTIONS[0][0]]["fy"].keys()) + " |", "|---|" + "---:|" * len(S[SELECTIONS[0][0]]["fy"])]
    for name, _ in SELECTIONS:
        d = S[name]
        cells = []
        for fyl, (f, p) in d["fy"].items():
            cells.append(f"{(d['fills'] if fyl == fwd else f) / p * 100:.0f}%" if p else "")
        L.append(f"| {name} | " + " | ".join(cells) + " |")
    L += ["", f"{fwd} is the forecast (average fills over the Budget).", ""]

    for name, _ in SELECTIONS[:2] + SELECTIONS[3:4]:
        d = S[name]
        lo = min(r[1] for r in d["forecast"])
        hi = max(r[1] for r in d["forecast"])
        L += [f"## 4. Main chart: {name}", "",
              f"Forecast quarters average {f0(lo)} to {f0(hi)} fills; the title rounds them to tens.", "",
              "| Quarter | Filled | Budget | Vacant at the end | Forecast (average) | Range P10 to P90 | Vacant, forecast (range) |",
              "|---|---:|---:|---:|---:|---|---|"]
        fc = {r[0]: r for r in d["forecast"]}
        for qo, ql, _, f, p, v in d["quarters"]:
            if qo in fc:
                r = fc[qo]
                L.append(f"| {ql} | | {f0(p)} | | **{f1(r[1])}** | {f1(r[2])} to {f1(r[3])} | {f1(r[4])} ({f1(r[5])} to {f1(r[6])}) |")
            else:
                L.append(f"| {ql} | {f0(f)} | {f0(p)} | {f0(v)} | | | |")
        L.append("")

    L += ["## 5. Time to fill", "",
          "Share filled within 30, 60 and 90 days, and the median wait, by level band (L1–L2 Associate, L3–L4 Senior, L5–L6 Manager, L7+ Director).", "",
          "| Selection | Level | 30 days | 60 days | 90 days | Median wait |", "|---|---|---:|---:|---:|---:|"]
    for name, _ in SELECTIONS:
        d = S[name]
        for b in [None] + BANDS:
            cv = d["curve_all"] if b is None else d["curves"][b]
            md = median_days(cv)
            L.append(f"| {name if b is None else ''} | {b or 'All levels'} | {pct(at(cv, 30))} | {pct(at(cv, 60))} | {pct(at(cv, 90))} | "
                     f"{'' if md is None else f'{md:.0f} days'} |")
    L.append("")

    L += ["## 6. The backtest (one quarter ahead)", "",
          "| Selection | " + " | ".join(qlabel[r[0]] for r in S[SELECTIONS[0][0]]["backtest"]) + " | In range | Average error |",
          "|---|" + "---|" * len(S[SELECTIONS[0][0]]["backtest"]) + "---:|---:|"]
    for name, _ in SELECTIONS:
        d = S[name]
        cells = [f"{f0(lo)}–{f0(hi)} · **{f0(act)}**{'' if lo <= act <= hi else ' (out)'}" for _, lo, m, hi, act in d["backtest"]]
        n_in = sum(1 for _, lo, m, hi, act in d["backtest"] if lo <= act <= hi)
        err = sum(abs(m - act) / act for _, lo, m, hi, act in d["backtest"] if act) / len(d["backtest"]) * 100
        L.append(f"| {name} | " + " | ".join(cells) + f" | {n_in} of {len(d['backtest'])} | {err:.1f}% |")
    L += ["", "Each cell: the range, then the actual fills in bold. The forecast origin is the quarter-end before the target quarter.", ""]

    L += ["## 7. The Period capsule: one forward quarter", "",
          "With a quarter chosen, the KPI band reads that quarter: fills in it, PIDs to fill (waiting as it opens + opened in it), "
          "vacant at its end, its budget, and the same quarter a year earlier. Averages; ranges P10 to P90.", "",
          "| Selection | Quarter | Fills (range) | Budget · attainment | Same quarter a year earlier (att.) | Waiting as it opens | To fill (range) | Vacant at its end (range) |",
          "|---|---|---|---|---|---:|---|---|"]
    for name, w in SELECTIONS[:2] + SELECTIONS[3:4]:
        rows = c.execute(f"""
            WITH x AS (SELECT quarter_offset, draw, SUM(filled) f, SUM(vacant_start) vs,
                              SUM(vacant_start + opened_backfill + opened_net_new + opened_immediate) tf, SUM(vacant_end) v
                       FROM {scoped('mart_pid_forecast_draws', w)} GROUP BY 1, 2)
            SELECT quarter_offset, AVG(f), QUANTILE_CONT(f, .1), QUANTILE_CONT(f, .9), AVG(vs), AVG(tf), QUANTILE_CONT(tf, .1),
                   QUANTILE_CONT(tf, .9), AVG(v), QUANTILE_CONT(v, .1), QUANTILE_CONT(v, .9) FROM x GROUP BY 1 ORDER BY 1""").fetchall()
        q = {r[0]: r for r in S[name]["quarters"]}
        for i, (qo, f, flo, fhi, vs, tf, tlo, thi, v, vlo, vhi) in enumerate(rows):
            plan = q[qo][4]
            ly = q[qo - 4]
            L.append(f"| {name if i == 0 else ''} | {qlabel[qo]} | **{f1(f)}** ({f1(flo)} to {f1(fhi)}) | {f0(plan)} · {f / plan * 100:.0f}% | "
                     f"{qlabel[qo - 4]}: {f0(ly[3])} ({ly[3] / ly[4] * 100:.0f}%) | {f1(vs)} | **{f1(tf)}** ({f1(tlo)} to {f1(thi)}) | "
                     f"**{f1(v)}** ({f1(vlo)} to {f1(vhi)}) |")
    L.append("")
    OUT.write_text("\n".join(L) + "\n")
    print(f"Wrote {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
