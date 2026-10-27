"""
The PID fill forecast, end to end (release 5, Dashboard #5, Seats to Fill).

    python forecast/run_forecast.py            # after pipeline/run_pipeline.py

Steps
  1. Read the warehouse (warehouse/arcadia.duckdb): requisitions, headcount, every plan version,
     the report calendar.
  2. Fit the time-to-fill model on what was known on the report date, simulate the forward year
     DRAWS times, and keep every draw.
  3. Backtest: at each of the eight quarter-ends before the report date, refit on what was known
     then, forecast the quarters its plan covered, and compare with what happened.
  4. Write the history, survival, forecast, backtest and model tables to the warehouse's
     `forecast` schema and to data/marts/ for Tableau, then run the tests in tests/forecast/.

Everything is seeded, so the files reproduce byte for byte (CI checks it). Executive officers are
excluded. Arcadia Systems is fictional; all data is synthetic.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import duckdb
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
import data as D            # noqa: E402
import fill_model as FM     # noqa: E402
import settings as S        # noqa: E402
import simulate as SIM      # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "warehouse" / "arcadia.duckdb"
MART_DIR = ROOT / "data" / "marts"
TEST_DIR = ROOT / "tests" / "forecast"
COUNTS = ["vacant_start", "opened_backfill", "opened_net_new", "opened_immediate", "filled", "vacant_end"]


def log(msg: str = ""):
    print(msg, flush=True)


def fit_at(inp: D.Inputs, origin: pd.Timestamp) -> tuple[FM.FillModel, pd.DataFrame]:
    hs = pd.Timestamp(inp.calendar["history_start_date"])
    known = D.as_of_origin(inp.reqs[inp.reqs["approved_date"] >= hs], origin)
    functions = sorted(inp.cells["function_name"].unique())
    countries = sorted(inp.cells["country_code"].unique())
    return FM.fit(known, functions, countries), known


# --------------------------------------------------------------------------------------
# History: what happened, per department x office x quarter
# --------------------------------------------------------------------------------------
def history(inp: D.Inputs) -> pd.DataFrame:
    q = inp.quarters
    ends = [pd.Timestamp(x) for x in q["quarter_end_date"]]
    starts = [pd.Timestamp(x) for x in q["quarter_start_date"]]
    as_of = pd.Timestamp(inp.calendar["report_as_of_date"])
    r = inp.reqs.copy()
    key = ["department_id", "location_id"]
    rows = []
    for s, e, off in zip(starts, ends, q["quarter_offset"]):
        if e > as_of:
            continue
        opened = r[(r["approved_date"] >= s) & (r["approved_date"] <= e)]
        filled = r[r["filled_date"].notna() & (r["filled_date"] >= s) & (r["filled_date"] <= e)]
        waiting = r[(r["approved_date"] <= e) & ~r["is_immediate"]
                    & (r["filled_date"].isna() | (r["filled_date"] > e))
                    & (r["cancelled_date"].isna() | (r["cancelled_date"] > e))]
        parts = {
            "opened_backfill": opened[~opened["is_immediate"] & ~opened["is_net_new"]],
            "opened_net_new": opened[~opened["is_immediate"] & opened["is_net_new"]],
            "opened_immediate": opened[opened["is_immediate"]],
            "filled_backfill": filled[~filled["is_net_new"]],
            "filled_net_new": filled[filled["is_net_new"]],
            "vacant_end": waiting,
        }
        g = pd.concat([v.groupby(key).size().rename(k) for k, v in parts.items()], axis=1).fillna(0).astype(int)
        g["quarter_offset"] = off
        rows.append(g.reset_index())
    h = pd.concat(rows, ignore_index=True)
    h["filled"] = h["filled_backfill"] + h["filled_net_new"]
    return h


def plan_by_office(inp: D.Inputs) -> pd.DataFrame:
    """Each fiscal year's Budget, per quarter, allocated from cost center (department x country) to
    its offices by their share of the cost center's employees at the quarter's start."""
    q = inp.quarters
    as_of = pd.Timestamp(inp.calendar["report_as_of_date"])
    hc = inp.headcount
    cells = inp.cells
    out = []
    budget = inp.plan[inp.plan["version_type"] == "Budget"]
    for e, off in zip(q["quarter_end_date"], q["quarter_offset"]):
        e = pd.Timestamp(e)
        start_hc = min(e - pd.offsets.QuarterEnd(1), as_of)
        h = hc[hc["quarter_end_date"] == start_hc].merge(cells[["department_id", "location_id", "cost_center_id"]])
        b = budget[budget["quarter_end_date"] == e]
        x = cells[["department_id", "location_id", "cost_center_id"]].merge(
            h[["department_id", "location_id", "headcount"]], how="left").fillna({"headcount": 0})
        tot = x.groupby("cost_center_id")["headcount"].transform("sum")
        n = x.groupby("cost_center_id")["headcount"].transform("size")
        x["share"] = np.where(tot > 0, x["headcount"] / tot.where(tot > 0, 1), 1.0 / n)
        x = x.merge(b[["cost_center_id", "planned_net_new", "planned_backfills"]], on="cost_center_id")
        x["planned_net_new"] = x["planned_net_new"] * x["share"]
        x["planned_backfills"] = x["planned_backfills"] * x["share"]
        x["quarter_offset"] = off
        x = x.rename(columns={"headcount": "headcount_start"})
        out.append(x[["quarter_offset", "department_id", "location_id", "headcount_start",
                      "planned_net_new", "planned_backfills"]])
    p = pd.concat(out, ignore_index=True)
    p[["planned_net_new", "planned_backfills"]] = p[["planned_net_new", "planned_backfills"]].round(4)
    return p


# --------------------------------------------------------------------------------------
# Survival inputs: PIDs at risk and filled, per ten-day period of waiting
# --------------------------------------------------------------------------------------
def survival(inp: D.Inputs) -> pd.DataFrame:
    as_of = pd.Timestamp(inp.calendar["report_as_of_date"])
    hs = pd.Timestamp(inp.calendar["history_start_date"])
    r = D.as_of_origin(inp.reqs[inp.reqs["approved_date"] >= hs], as_of)
    r = r[~r["is_immediate"]].reset_index(drop=True)
    pp = FM.person_periods(r)
    # person_periods drops the requisition key; rebuild it in the same order
    n = np.where(r["known_filled"], r["fill_day"].astype(int) // S.PERIOD_DAYS + 1,
                 (r["observed_days"].astype(int) + 1) // S.PERIOD_DAYS)
    keep = n > 0
    idx = np.repeat(np.arange(len(r))[keep], n[keep])
    q = inp.quarters
    qe = pd.to_datetime(q["quarter_end_date"]).to_numpy()
    appr = r["approved_date"].to_numpy()
    cohort = q["quarter_offset"].to_numpy()[np.searchsorted(qe, appr)]
    pp["cohort_quarter_offset"] = cohort[idx]
    pp["department_id"] = r["department_id"].to_numpy()[idx]
    pp["location_id"] = r["location_id"].to_numpy()[idx]
    pp["req_type"] = r["req_type"].to_numpy()[idx]
    pp = pp[pp["k"] < S.OBSERVED_PERIODS]
    s = pp.groupby(["cohort_quarter_offset", "department_id", "location_id", "band", "req_type", "k"], as_index=False) \
          .agg(at_risk=("filled", "size"), filled=("filled", "sum"))
    s = s.rename(columns={"band": "level_band", "k": "period"})
    s["days_from"] = s["period"] * S.PERIOD_DAYS
    s["days_to"] = s["days_from"] + S.PERIOD_DAYS - 1
    return s


# --------------------------------------------------------------------------------------
# The forward forecast and the backtest
# --------------------------------------------------------------------------------------
def label_targets(inp: D.Inputs, out: pd.DataFrame, targets: list[pd.Timestamp]) -> pd.DataFrame:
    q = inp.quarters.set_index(pd.to_datetime(inp.quarters["quarter_end_date"]))
    t = pd.DataFrame({"target": range(len(targets)),
                      "quarter_offset": [int(q.loc[x, "quarter_offset"]) for x in targets]})
    cells = inp.cells[["department_id", "location_id"]].reset_index().rename(columns={"index": "cell"})
    return out.merge(t, on="target").merge(cells, on="cell").drop(columns=["target", "cell"])


def forward(inp: D.Inputs) -> tuple[pd.DataFrame, dict]:
    origin = pd.Timestamp(inp.calendar["report_as_of_date"])
    q = inp.quarters
    targets = [pd.Timestamp(x) for x in q.loc[q["is_forward"], "quarter_end_date"]]
    model, known = fit_at(inp, origin)
    out, demand, pool = SIM.run(inp, model, origin, targets, S.DRAWS, seed_key=0)
    out = label_targets(inp, out, targets)
    meta = run_meta("Forward", origin, known, model, len(targets), S.DRAWS, pool)
    return out[["quarter_offset", "department_id", "location_id", "draw", *COUNTS]], {"model": model, "meta": meta,
                                                                                       "demand": demand}


def run_meta(kind: str, origin: pd.Timestamp, known: pd.DataFrame, model: FM.FillModel, quarters: int, draws: int,
             pool: pd.DataFrame) -> dict:
    fills = known.loc[known["known_filled"], "filled_date"]
    return {"run_type": kind, "origin_date": origin.date(),
            "latest_approval_used": known["approved_date"].max().date(),
            "latest_fill_used": fills.max().date() if len(fills) else None,
            "requisitions_fit": model.requisitions, "requisition_periods_fit": model.rows,
            "waiting_at_origin": len(pool), "quarters_forecast": quarters, "draws": draws}


def backtest(inp: D.Inputs, hist: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame, list[dict]]:
    q = inp.quarters
    as_of = pd.Timestamp(inp.calendar["report_as_of_date"])
    ends = [pd.Timestamp(x) for x in q["quarter_end_date"]]
    offs = list(q["quarter_offset"])
    origin_offsets = list(range(-S.BACKTEST_ORIGINS, 0))
    cell_rows, company_rows, metas = [], [], []
    actual = hist.set_index(["quarter_offset", "department_id", "location_id"])[["filled", "vacant_end"]]
    for o_off in origin_offsets:
        origin = ends[offs.index(o_off)]
        known_plan = D.known_plan(inp.plan, origin)
        covered = sorted(set(known_plan["quarter_end_date"]))
        targets = [t for t in covered if t <= as_of][:4]
        if not targets:
            continue
        model, known = fit_at(inp, origin)
        out, demand, pool = SIM.run(inp, model, origin, targets, S.BACKTEST_DRAWS, seed_key=1000 + o_off + 100)
        out = label_targets(inp, out, targets)
        metas.append(run_meta("Backtest", origin, known, model, len(targets), S.BACKTEST_DRAWS, pool))
        # every draw must have a row for every cell x quarter for means and variances: fill the zeros
        full = out.set_index(["quarter_offset", "department_id", "location_id", "draw"])[["filled", "vacant_end"]]
        keys = out[["quarter_offset", "department_id", "location_id"]].drop_duplicates()
        grid = keys.merge(pd.DataFrame({"draw": range(1, S.BACKTEST_DRAWS + 1)}), how="cross")
        full = grid.merge(full.reset_index(), how="left").fillna(0)
        stats = full.groupby(["quarter_offset", "department_id", "location_id"]).agg(
            filled_mean=("filled", "mean"), filled_var=("filled", "var"),
            vacant_end_mean=("vacant_end", "mean"), vacant_end_var=("vacant_end", "var")).reset_index()
        stats = stats.merge(actual.reset_index(), how="outer", on=["quarter_offset", "department_id", "location_id"])
        stats = stats[stats["quarter_offset"].isin([offs[ends.index(t)] for t in targets])].fillna(0)
        stats = stats.rename(columns={"filled": "actual_filled", "vacant_end": "actual_vacant_end"})
        stats["origin_quarter_offset"] = o_off
        stats["horizon"] = stats["quarter_offset"] - o_off
        cell_rows.append(stats)
        comp = out.groupby(["quarter_offset", "draw"])[["filled", "vacant_end"]].sum().reset_index()
        for t_off, g in comp.groupby("quarter_offset"):
            a = actual.loc[t_off].sum() if t_off in actual.index.get_level_values(0) else pd.Series({"filled": 0, "vacant_end": 0})
            row = {"origin_quarter_offset": o_off, "quarter_offset": int(t_off), "horizon": int(t_off - o_off)}
            for m in ("filled", "vacant_end"):
                vals = g[m].to_numpy()
                p10, p50, p90 = np.percentile(vals, [10, 50, 90])
                row.update({f"{m}_p10": round(float(p10), 1), f"{m}_p50": round(float(p50), 1),
                            f"{m}_p90": round(float(p90), 1), f"actual_{m}": int(a[m]),
                            f"{m}_in_range": bool(p10 <= a[m] <= p90),
                            f"{m}_error_pct": round(float((p50 - a[m]) / a[m] * 100), 2) if a[m] else None})
            company_rows.append(row)
    cells = pd.concat(cell_rows, ignore_index=True)
    for c in ("filled_mean", "filled_var", "vacant_end_mean", "vacant_end_var"):
        cells[c] = cells[c].round(4)
    cells[["actual_filled", "actual_vacant_end"]] = cells[["actual_filled", "actual_vacant_end"]].astype(int)
    cells = cells[(cells[["filled_mean", "vacant_end_mean", "actual_filled", "actual_vacant_end"]] != 0).any(axis=1)]
    return cells, pd.DataFrame(company_rows), metas


# --------------------------------------------------------------------------------------
# Contingent budget: one line, by function
# --------------------------------------------------------------------------------------
def cw_budget(inp: D.Inputs) -> pd.DataFrame:
    """Each fiscal year's Budget for contingent workers, by function, at the fiscal year's last
    quarter-end: planned workers and their annualized spend, and the spend per worker it implies."""
    b = inp.plan[(inp.plan["version_type"] == "Budget") & (inp.plan["fiscal_quarter"] == 4)]
    fn = inp.cells.drop_duplicates("department_id").set_index("department_id")["function_name"]
    b = b.assign(function_name=b["department_id"].map(fn))
    g = b.groupby(["fiscal_year", "function_name"], as_index=False)[["planned_cw_headcount", "planned_cw_spend_usd"]].sum()
    g["planned_spend_per_worker_usd"] = (g["planned_cw_spend_usd"] / g["planned_cw_headcount"].where(
        g["planned_cw_headcount"] > 0)).round(2)
    g["planned_cw_spend_usd"] = g["planned_cw_spend_usd"].round(2)
    fy = inp.quarters.drop_duplicates("fiscal_year").set_index("fiscal_year")["fy_offset"]
    g["fy_offset"] = g["fiscal_year"].map(fy)
    return g[g["fy_offset"].notna()].astype({"fy_offset": int})


# --------------------------------------------------------------------------------------
def write(con: duckdb.DuckDBPyConnection, name: str, df: pd.DataFrame, export: bool = True):
    con.register("df_out", df)
    con.execute(f"CREATE OR REPLACE TABLE forecast.{name} AS SELECT * FROM df_out")
    con.unregister("df_out")
    if export:
        out = MART_DIR / f"{name}.csv"
        con.execute(f"COPY forecast.{name} TO '{out.as_posix()}' (HEADER, DELIMITER ',')")
        log(f"   {out.relative_to(ROOT)}  {len(df):>9,} rows  ({out.stat().st_size / 1e6:.1f} MB)")
    else:
        log(f"   forecast.{name:<34}{len(df):>9,} rows")


def run_tests(con: duckdb.DuckDBPyConnection) -> bool:
    ok = True
    for f in sorted(TEST_DIR.glob("*.sql")):
        q = f.read_text().rstrip().rstrip(";")
        n = con.execute(f"SELECT COUNT(*) FROM ({q})").fetchone()[0]
        log(f"   {'PASS' if n == 0 else f'FAIL ({n:,} rows)':<18}{f.stem}")
        if n:
            ok = False
            log(con.execute(f"SELECT * FROM ({q}) LIMIT 5").fetchdf().to_string(index=False))
    return ok


def main():
    started = time.perf_counter()
    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE SCHEMA IF NOT EXISTS forecast")
    log("1. Reading the warehouse")
    inp = D.load(con)
    log(f"   report date {inp.calendar['report_as_of_date']}, forward year {inp.calendar['forward_fiscal_year_label']}, "
        f"{len(inp.reqs):,} requisitions, {len(inp.cells):,} department x office cells")
    log("\n2. History, survival inputs and the forward forecast")
    hist = history(inp)
    plan = plan_by_office(inp)
    fwd, info = forward(inp)
    log("\n3. Backtest")
    bt_cells, bt_company, metas = backtest(inp, hist)
    log(f"   {bt_company['origin_quarter_offset'].nunique()} origins, {len(bt_company)} quarters forecast; next quarter "
        f"in range: fills {int(bt_company.loc[bt_company['horizon'] == 1, 'filled_in_range'].sum())} of "
        f"{int((bt_company['horizon'] == 1).sum())}")
    log("\n4. Writing tables")
    quarter = plan.merge(hist, how="outer", on=["quarter_offset", "department_id", "location_id"])
    num = [c for c in quarter.columns if c not in ("quarter_offset", "department_id", "location_id")]
    is_hist = quarter["quarter_offset"] <= 0
    quarter.loc[is_hist, num] = quarter.loc[is_hist, num].fillna(0)
    quarter = quarter[(quarter[num].fillna(0) != 0).any(axis=1)]
    for c in ("opened_backfill", "opened_net_new", "opened_immediate", "filled_backfill", "filled_net_new",
              "filled", "vacant_end", "headcount_start"):
        quarter[c] = quarter[c].astype("Int64")
    quarter = quarter.sort_values(["quarter_offset", "department_id", "location_id"]).reset_index(drop=True)
    write(con, "mart_pid_fill_quarter", quarter)
    write(con, "mart_fill_survival", survival(inp).sort_values(
        ["cohort_quarter_offset", "department_id", "location_id", "level_band", "req_type", "period"]).reset_index(drop=True))
    write(con, "mart_pid_forecast_draws", fwd.sort_values(["quarter_offset", "department_id", "location_id", "draw"])
          .reset_index(drop=True))
    write(con, "mart_pid_forecast_backtest", bt_cells.sort_values(
        ["origin_quarter_offset", "quarter_offset", "department_id", "location_id"])[
        ["origin_quarter_offset", "quarter_offset", "horizon", "department_id", "location_id", "filled_mean", "filled_var",
         "vacant_end_mean", "vacant_end_var", "actual_filled", "actual_vacant_end"]].reset_index(drop=True))
    write(con, "mart_pid_forecast_accuracy", bt_company)
    coef = info["model"].coefficients()
    coef["coefficient"] = coef["coefficient"].round(S.COEF_DECIMALS)
    write(con, "mart_pid_forecast_model", coef)
    write(con, "mart_pid_forecast_run", pd.DataFrame([info["meta"], *metas]))
    write(con, "mart_cw_budget_function", cw_budget(inp))
    log("\n5. Forecast tests")
    passed = run_tests(con)
    con.close()
    if not passed:
        log("\nForecast tests failed.")
        sys.exit(1)
    log(f"\nDone in {time.perf_counter() - started:.1f}s. All forecast tests passed.")


if __name__ == "__main__":
    main()
