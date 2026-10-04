"""
Synthetic HR data warehouse generator for Arcadia Systems (fictional).

Simulates four fiscal years (FY2023-FY2026) of workforce history month by month:
hires, terminations, transfers, promotions, merit cycles, market adjustments,
FTE changes, relocations, a restructuring and a reorganization. The result is
written as raw warehouse tables (CSV) in data/raw/.

The output is deterministic: the same seed always produces the same files.

    python generator/generate_data.py
"""

from __future__ import annotations

import calendar
import datetime as dt
import math
from pathlib import Path

import numpy as np
import pandas as pd

import reference_data as ref

SEED = 20261004
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw"

rng = np.random.default_rng(SEED)


# ======================================================================================
# Helpers
# ======================================================================================
def fiscal_year(d: dt.date) -> int:
    return d.year + 1 if d.month >= ref.FISCAL_YEAR_START_MONTH else d.year


def month_end(year: int, month: int) -> dt.date:
    return dt.date(year, month, calendar.monthrange(year, month)[1])


def random_day_in_month(year: int, month: int, first_day: int = 1) -> dt.date:
    last = calendar.monthrange(year, month)[1]
    return dt.date(year, month, int(rng.integers(first_day, last + 1)))


def weighted_choice(options: dict):
    keys = list(options.keys())
    weights = np.array([options[k] for k in keys], dtype=float)
    return keys[rng.choice(len(keys), p=weights / weights.sum())]


def round_salary(amount: float) -> float:
    return float(round(amount / 100.0) * 100)


MONTH_ENDS: list[dt.date] = []
_d = dt.date.fromisoformat(ref.FIRST_SNAPSHOT)
while _d <= dt.date.fromisoformat(ref.LAST_SNAPSHOT):
    MONTH_ENDS.append(_d)
    _next = _d + dt.timedelta(days=1)
    _d = month_end(_next.year, _next.month)

COUNTRY = {c: dict(zip(
    ["name", "region", "currency", "pay_index", "fx_start", "fx_vol", "fx_drift",
     "fringe_base", "merit_adder", "weight"], v)) for c, v in ref.COUNTRIES.items()}
DEPT = {d[0]: dict(zip(
    ["id", "name", "sub_function", "function", "families", "profile", "size_weight", "growth_weight"], d))
    for d in ref.DEPARTMENTS}
LOCS_BY_COUNTRY: dict[str, list[str]] = {}
for loc_id, city, cc, site in ref.LOCATIONS:
    LOCS_BY_COUNTRY.setdefault(cc, []).append(loc_id)
LOC_COUNTRY = {loc_id: cc for loc_id, _, cc, _ in ref.LOCATIONS}
LOC_SITE = {loc_id: site for loc_id, _, _, site in ref.LOCATIONS}

REORG_DATE = dt.date.fromisoformat(ref.REORGANIZATION["date"])
RESTRUCTURE_DATE = dt.date.fromisoformat(ref.RESTRUCTURING["date"])


# ======================================================================================
# 1. FX rates (synthetic monthly paths) and constant plan rates
# ======================================================================================
def build_fx() -> dict[str, dict[dt.date, float]]:
    params = {}
    for cc, c in COUNTRY.items():
        params.setdefault(c["currency"], (c["fx_start"], c["fx_vol"], c["fx_drift"]))
    fx: dict[str, dict[dt.date, float]] = {}
    for cur, (start, vol, drift) in params.items():
        path, level = {}, math.log(start)
        for i, me in enumerate(MONTH_ENDS):
            if i > 0:
                level += drift + vol * rng.standard_normal()
            path[me] = round(math.exp(level), 8)
        fx[cur] = path
    return fx


FX = build_fx()
PLAN_DATE = dt.date.fromisoformat(ref.FX_CONSTANT_RATE_DATE)
FX_PLAN = {cur: path[PLAN_DATE] for cur, path in FX.items()}


# ======================================================================================
# 2. Fringe rates by country and fiscal year
# ======================================================================================
FISCAL_YEARS = list(range(fiscal_year(MONTH_ENDS[0]), fiscal_year(MONTH_ENDS[-1]) + 1))
FRINGE: dict[tuple[str, int], float] = {}
for cc, c in COUNTRY.items():
    rate = c["fringe_base"]
    for fy in FISCAL_YEARS:
        if fy > FISCAL_YEARS[0]:
            rate = max(0.03, rate + rng.normal(0.002, 0.006))
        FRINGE[(cc, fy)] = round(rate, 4)


# ======================================================================================
# 3. Salary ranges (local currency) by fiscal year, grade and country
# ======================================================================================
def range_factor(fy: int) -> float:
    factor = 1.0
    for y in range(2023, fy + 1):
        factor *= 1 + ref.GRADE_RANGE_MOVEMENT.get(y, 0.03)
    if fy < 2023:
        factor *= 1 + ref.GRADE_RANGE_MOVEMENT[2022]
    return factor


RANGE_MID: dict[tuple[int, int, str], float] = {}
for fy in FISCAL_YEARS:
    for g, (_, _, mid_usd) in ref.GRADES.items():
        for cc, c in COUNTRY.items():
            mid_local = mid_usd * range_factor(fy) * c["pay_index"] / FX_PLAN[c["currency"]]
            RANGE_MID[(fy, g, cc)] = round_salary(mid_local)


def starting_salary(grade: int, cc: str, fy: int) -> float:
    mid = RANGE_MID[(fy, grade, cc)]
    position_in_range = float(np.clip(rng.lognormal(0.0, 0.085), 0.82, 1.18))
    return round_salary(mid * position_in_range)


# ======================================================================================
# 4. Simulation state and record writers
# ======================================================================================
job_rows: list[dict] = []
comp_rows: list[dict] = []
workers: dict[str, dict] = {}          # every worker ever employed
active: dict[str, dict] = {}           # current employees
_seq = {"worker": 100000, "position": 200000}


def next_id(kind: str, prefix: str) -> str:
    _seq[kind] += 1
    return f"{prefix}{_seq[kind]}"


def pick_country(dept_id: str, exclude: str | None = None) -> str:
    prof = ref.COUNTRY_PROFILES[DEPT[dept_id]["profile"]]
    options = {cc: COUNTRY[cc]["weight"] * prof[cc] for cc in prof if cc != exclude}
    return weighted_choice(options)


def pick_location(cc: str, exclude: str | None = None) -> str:
    locs = [l for l in LOCS_BY_COUNTRY[cc] if l != exclude]
    weights = {l: (0.4 if LOC_SITE[l] == "Remote" else 1.6 if LOC_SITE[l] == "Headquarters" else 1.0) for l in locs}
    return weighted_choice(weights)


def pick_family(dept_id: str) -> str:
    return weighted_choice(DEPT[dept_id]["families"])


def open_job(w: dict, start: dt.date, reason: str):
    w["job"] = {"worker_id": w["worker_id"], "effective_start_date": start, "effective_end_date": None,
                "action_reason": reason, "position_id": w["position_id"], "department_id": w["dept"],
                "location_id": w["loc"], "job_profile_id": f'{w["family"]}-{w["grade"]}',
                "grade": w["grade"], "fte": w["fte"]}
    job_rows.append(w["job"])


def close_job(w: dict, end: dt.date):
    w["job"]["effective_end_date"] = end


def open_comp(w: dict, start: dt.date, reason: str):
    w["comp"] = {"worker_id": w["worker_id"], "effective_start_date": start, "effective_end_date": None,
                 "action_reason": reason, "currency_code": COUNTRY[w["country"]]["currency"],
                 "base_salary_annual_local": w["salary"]}
    comp_rows.append(w["comp"])


def close_comp(w: dict, end: dt.date):
    w["comp"]["effective_end_date"] = end


def change_job(w: dict, on: dt.date, reason: str):
    close_job(w, on - dt.timedelta(days=1))
    open_job(w, on, reason)


def change_comp(w: dict, on: dt.date, reason: str):
    close_comp(w, on - dt.timedelta(days=1))
    open_comp(w, on, reason)


def new_worker(hire_date: dt.date, dept_id: str, grade: int, family: str, cc: str,
               salary: float, fte: float, is_exec: bool = False, comp_start: dt.date | None = None) -> dict:
    w = {"worker_id": next_id("worker", "W"), "hire_date": hire_date, "termination_date": None,
         "termination_type": None, "is_exec": is_exec, "position_id": next_id("position", "P"),
         "dept": dept_id, "family": family, "grade": grade, "country": cc,
         "loc": pick_location(cc), "fte": fte, "salary": salary}
    workers[w["worker_id"]] = w
    active[w["worker_id"]] = w
    open_job(w, hire_date, "Hire")
    open_comp(w, comp_start or hire_date, "Hire" if comp_start is None else "Conversion")
    return w


def terminate(w: dict, on: dt.date, kind: str):
    w["termination_date"], w["termination_type"] = on, kind
    close_job(w, on)
    close_comp(w, on)
    del active[w["worker_id"]]


def random_fte() -> float:
    return float(rng.choice([1.0, 0.8, 0.5], p=[0.965, 0.025, 0.010]))


# ======================================================================================
# 5. Opening population (as of the first month-end)
# ======================================================================================
first_me = MONTH_ENDS[0]
COMP_CONVERSION_DATE = dt.date(2022, 3, 1)   # comp history loaded into the warehouse from here

dept_sizes = {d: DEPT[d]["size_weight"] for d in DEPT if d not in ("D-108", "D-901")}
for _ in range(ref.START_HEADCOUNT):
    dept_id = weighted_choice(dept_sizes)
    family = pick_family(dept_id)
    grade = weighted_choice(ref.START_GRADE_MIX)
    cc = pick_country(dept_id)
    tenure_years = min(20.0, max(0.05, rng.exponential(4.5)))
    hire_date = first_me - dt.timedelta(days=int(tenure_years * 365.25))
    comp_start = max(hire_date, COMP_CONVERSION_DATE)
    salary = starting_salary(grade, cc, fiscal_year(comp_start))
    new_worker(hire_date, dept_id, grade, family, cc, salary, random_fte(),
               comp_start=comp_start if comp_start > hire_date else None)

# Executive leadership team: excluded from compensation reporting downstream.
for grade in [9] * 8 + [8] * 4:
    tenure_years = rng.uniform(2, 14)
    hire_date = first_me - dt.timedelta(days=int(tenure_years * 365.25))
    comp_start = max(hire_date, COMP_CONVERSION_DATE)
    salary = round_salary(RANGE_MID[(2022, grade, "US")] * rng.uniform(1.3, 2.2))
    new_worker(hire_date, "D-901", grade, "EXE", "US", salary, 1.0, is_exec=True,
               comp_start=comp_start if comp_start > hire_date else None)


# ======================================================================================
# 6. Monthly simulation
# ======================================================================================
def attrition_probability(w: dict, on: dt.date) -> float:
    tenure = (on - w["hire_date"]).days / 365.25
    p = ref.MONTHLY_ATTRITION
    p *= 1.6 if tenure < 1 else 1.15 if tenure < 2 else 0.85 if tenure > 6 else 1.0
    p *= 0.7 if w["grade"] >= 7 else 1.0
    p *= {2023: 1.10, 2024: 0.85, 2025: 0.90, 2026: 1.00}.get(fiscal_year(on), 1.0)
    p *= 1.25 if DEPT[w["dept"]]["function"] == "Commercial" else 1.0
    return p


def available_departments(on: dt.date) -> list[str]:
    return [d for d in DEPT if d != "D-901" and (d != "D-108" or on >= REORG_DATE)]


def transfer(w: dict, on: dt.date, prior_me: dt.date):
    same_function = rng.random() < 0.7
    options = [d for d in available_departments(on) if d != w["dept"]
               and (not same_function or DEPT[d]["function"] == DEPT[w["dept"]]["function"])]
    if not options:
        options = [d for d in available_departments(on) if d != w["dept"]]
    new_dept = options[rng.integers(len(options))]
    if w["family"] not in DEPT[new_dept]["families"]:
        w["family"] = pick_family(new_dept)
    w["dept"], w["position_id"] = new_dept, next_id("position", "P")

    if rng.random() < ref.INTERNATIONAL_SHARE_OF_TRANSFERS:
        old_cc, new_cc = w["country"], pick_country(new_dept, exclude=w["country"])
        # re-level pay for the new market, converting at last month-end FX
        usd = w["salary"] * FX[COUNTRY[old_cc]["currency"]][prior_me]
        new_usd = usd * COUNTRY[new_cc]["pay_index"] / COUNTRY[old_cc]["pay_index"] * rng.uniform(0.97, 1.06)
        w["country"], w["loc"] = new_cc, pick_location(new_cc)
        w["salary"] = round_salary(new_usd / FX[COUNTRY[new_cc]["currency"]][prior_me])
        change_job(w, on, "Transfer")
        change_comp(w, on, "International Transfer")
    else:
        if rng.random() < 0.3 and len(LOCS_BY_COUNTRY[w["country"]]) > 1:
            w["loc"] = pick_location(w["country"], exclude=w["loc"])
        change_job(w, on, "Transfer")


def promote(w: dict, on: dt.date, increase: float, reason: str = "Promotion"):
    w["grade"] += 1
    w["salary"] = round_salary(w["salary"] * (1 + increase))
    change_job(w, on, "Promotion")
    change_comp(w, on, reason)


hire_target_base = None
for i in range(1, len(MONTH_ENDS)):
    me, prior_me = MONTH_ENDS[i], MONTH_ENDS[i - 1]
    y, m = me.year, me.month
    fy = fiscal_year(me)
    touched: set[str] = set()   # one event per worker per month keeps SCD2 dates clean

    # --- start of fiscal year: set the headcount target for the year
    if m == ref.FISCAL_YEAR_START_MONTH or hire_target_base is None:
        hire_target_base = len(active)
        fy_start_index = i

    # --- one-off: FY24 restructuring (involuntary exits in Commercial and Marketing)
    if (y, m) == (RESTRUCTURE_DATE.year, RESTRUCTURE_DATE.month):
        pool = [w for w in active.values() if DEPT[w["dept"]]["function"] in ref.RESTRUCTURING["functions"]]
        for w in rng.choice(pool, size=int(len(pool) * ref.RESTRUCTURING["share"]), replace=False):
            terminate(w, RESTRUCTURE_DATE, "Involuntary")
            touched.add(w["worker_id"])

    # --- one-off: FY25 reorganization (data people move into the new Data & AI Platform)
    if (y, m) == (REORG_DATE.year, REORG_DATE.month):
        for w in list(active.values()):
            if w["dept"] in ref.REORGANIZATION["source_departments"] and w["family"] in ref.REORGANIZATION["families"]:
                w["dept"], w["position_id"] = ref.REORGANIZATION["target_department"], next_id("position", "P")
                change_job(w, REORG_DATE, "Reorganization")
                touched.add(w["worker_id"])

    # --- individual events for everyone else
    order = list(active.values())
    rng.shuffle(order)
    for w in order:
        if w["worker_id"] in touched:
            continue

        # attrition (executives are held constant)
        if not w["is_exec"] and rng.random() < attrition_probability(w, me):
            first_day = 2 if m == ref.MERIT_EFFECTIVE_MONTH else 1
            terminate(w, random_day_in_month(y, m, first_day),
                      "Voluntary" if rng.random() < 0.8 else "Involuntary")
            touched.add(w["worker_id"])
            continue

        # annual merit and promotion cycle (March 1)
        if m == ref.MERIT_EFFECTIVE_MONTH:
            cycle_date = dt.date(y, m, 1)
            eligible = w["hire_date"] <= dt.date(y - 1, 12, 31)
            if not eligible:
                continue
            merit = 0.0 if rng.random() < 0.08 else max(
                0.0, rng.normal(ref.MERIT_BUDGET[fy] + COUNTRY[w["country"]]["merit_adder"] / 100, 0.012))
            tenure = (cycle_date - w["hire_date"]).days / 365.25
            if not w["is_exec"] and w["grade"] < 9 and tenure > 1 and rng.random() < ref.PROMOTION_CYCLE_RATE:
                promote(w, cycle_date, merit + rng.uniform(0.07, 0.12))
            elif merit > 0:
                w["salary"] = round_salary(w["salary"] * (1 + merit))
                change_comp(w, cycle_date, "Merit")
            touched.add(w["worker_id"])
            continue

        if w["is_exec"]:
            continue

        # everything else happens on a random day in the month
        r = rng.random()
        on = random_day_in_month(y, m)
        cut1 = ref.MONTHLY_TRANSFER
        cut2 = cut1 + ref.OFF_CYCLE_PROMOTION_MONTHLY
        cut3 = cut2 + ref.MONTHLY_MARKET_ADJUSTMENT
        cut4 = cut3 + ref.MONTHLY_FTE_CHANGE
        cut5 = cut4 + ref.LOCATION_MOVE_MONTHLY
        if r < cut1:
            transfer(w, on, prior_me)
        elif r < cut2 and w["grade"] < 9:
            promote(w, on, rng.uniform(0.08, 0.14))
        elif r < cut3:
            w["salary"] = round_salary(w["salary"] * (1 + rng.uniform(0.03, 0.08)))
            change_comp(w, on, "Market Adjustment")
        elif r < cut4:
            w["fte"] = 1.0 if w["fte"] < 1.0 else float(rng.choice([0.8, 0.5], p=[0.75, 0.25]))
            change_job(w, on, "FTE Change")
        elif r < cut5 and len(LOCS_BY_COUNTRY[w["country"]]) > 1:
            w["loc"] = pick_location(w["country"], exclude=w["loc"])
            change_job(w, on, "Location Change")
        else:
            continue
        touched.add(w["worker_id"])

    # --- hiring: backfill attrition and grow toward the fiscal-year target
    months_into_fy = i - fy_start_index + 1
    target = hire_target_base * (1 + ref.FY_NET_GROWTH[fy]) ** (months_into_fy / 12)
    n_hires = max(0, int(round(target - len(active) + rng.normal(0, 6))))
    dept_hc: dict[str, int] = {}
    for w in active.values():
        dept_hc[w["dept"]] = dept_hc.get(w["dept"], 0) + 1
    hire_weights = {d: (dept_hc.get(d, 0) + 15) * DEPT[d]["growth_weight"] for d in available_departments(me)}
    if (y, m) == (RESTRUCTURE_DATE.year, RESTRUCTURE_DATE.month):
        n_hires = int(n_hires * 0.3)       # hiring freeze in the restructuring month
    for _ in range(n_hires):
        dept_id = weighted_choice(hire_weights)
        cc = pick_country(dept_id)
        grade = weighted_choice(ref.HIRE_GRADE_MIX)
        hire_date = random_day_in_month(y, m)
        new_worker(hire_date, dept_id, grade, pick_family(dept_id), cc,
                   starting_salary(grade, cc, fiscal_year(hire_date)), random_fte())


# ======================================================================================
# 7. Same-day correction records in compensation history
# ======================================================================================
# In the source system a correction creates a second row with the same effective
# date. The earlier row keeps the mistyped amount; the later row is the truth.
corrections = []
for row in comp_rows:
    if rng.random() < ref.COMP_CORRECTION_RATE:
        wrong = dict(row)
        wrong["base_salary_annual_local"] = round_salary(
            row["base_salary_annual_local"] * float(rng.choice([1.10, 0.90, 10.0, 1.01])))
        wrong["transaction_type"] = "Original"
        row["transaction_type"] = "Correction"
        corrections.append(wrong)
for row in comp_rows:
    row.setdefault("transaction_type", "Original")
comp_rows.extend(corrections)


# ======================================================================================
# 8. Write raw tables
# ======================================================================================
def write(df: pd.DataFrame, name: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / f"{name}.csv", index=False)
    print(f"  {name:<28} {len(df):>9,} rows")


print("Writing raw tables to", OUT_DIR)

# dim_worker
write(pd.DataFrame([{
    "worker_id": w["worker_id"], "original_hire_date": w["hire_date"],
    "termination_date": w["termination_date"], "termination_type": w["termination_type"],
    "worker_type": "Regular Employee", "is_executive_officer": w["is_exec"],
} for w in workers.values()]).sort_values("worker_id"), "dim_worker")

# fact_job_history
job = pd.DataFrame(job_rows).sort_values(["worker_id", "effective_start_date"]).reset_index(drop=True)
job.insert(0, "job_record_id", [f"JR{n:07d}" for n in range(1, len(job) + 1)])
write(job, "fact_job_history")

# fact_compensation_history: ids follow entry order, so a correction always has
# a higher id than the row it corrects.
comp = pd.DataFrame(comp_rows)
comp["_order"] = (comp["transaction_type"] == "Correction").astype(int)
comp = comp.sort_values(["worker_id", "effective_start_date", "_order"]).drop(columns="_order").reset_index(drop=True)
comp.insert(0, "comp_record_id", [f"CR{n:07d}" for n in range(1, len(comp) + 1)])
comp = comp[["comp_record_id", "worker_id", "effective_start_date", "effective_end_date", "action_reason",
             "transaction_type", "currency_code", "base_salary_annual_local"]]
write(comp, "fact_compensation_history")

# dim_department
write(pd.DataFrame([{
    "department_id": d["id"], "department_name": d["name"], "sub_function": d["sub_function"],
    "function": d["function"], "cost_center": "CC-" + d["id"][2:] + "0",
    "effective_from_date": REORG_DATE if d["id"] == "D-108" else dt.date(2015, 1, 1),
} for d in DEPT.values()]), "dim_department")

# dim_location
write(pd.DataFrame([{
    "location_id": loc_id, "city": city, "country_code": cc, "country_name": COUNTRY[cc]["name"],
    "region": COUNTRY[cc]["region"], "currency_code": COUNTRY[cc]["currency"], "site_type": site,
} for loc_id, city, cc, site in ref.LOCATIONS]), "dim_location")

# dim_job_profile
TITLE = {1: "Associate {s}", 2: "{s}", 3: "Senior {s}", 4: "Lead {s}", 5: "Manager, {f}",
         6: "Senior Manager, {f}", 7: "Director, {f}", 8: "Senior Director, {f}", 9: "Vice President, {f}"}
EXEC_TITLE = {8: "Senior Vice President", 9: "Executive Vice President"}
profiles = []
for code, (family, stem) in ref.JOB_FAMILIES.items():
    for g, (level, track, _) in ref.GRADES.items():
        if code == "EXE" and g < 8:
            continue
        title = EXEC_TITLE[g] if code == "EXE" else TITLE[g].format(s=stem, f=family)
        profiles.append({"job_profile_id": f"{code}-{g}", "job_family_code": code, "job_family": family,
                         "job_title": title, "grade": g, "grade_level": level, "career_track": track})
write(pd.DataFrame(profiles), "dim_job_profile")

# ref_fx_rate_monthly
write(pd.DataFrame([{"currency_code": cur, "rate_date": d, "usd_per_local": r}
                    for cur, path in FX.items() for d, r in path.items()]), "ref_fx_rate_monthly")

# ref_fx_rate_constant
write(pd.DataFrame([{"rate_set": ref.FX_CONSTANT_RATE_SET, "currency_code": cur, "usd_per_local": r}
                    for cur, r in FX_PLAN.items()]), "ref_fx_rate_constant")

# ref_fringe_rate
write(pd.DataFrame([{"country_code": cc, "fiscal_year": fy, "fringe_rate": r}
                    for (cc, fy), r in FRINGE.items()]), "ref_fringe_rate")

# ref_salary_range
write(pd.DataFrame([{"fiscal_year": fy, "grade": g, "country_code": cc,
                     "currency_code": COUNTRY[cc]["currency"],
                     "range_min": round_salary(mid * 0.80), "range_mid": mid,
                     "range_max": round_salary(mid * 1.20)}
                    for (fy, g, cc), mid in RANGE_MID.items()]), "ref_salary_range")

print(f"Active headcount at {MONTH_ENDS[-1]}: {len(active):,}  |  workers ever employed: {len(workers):,}")
