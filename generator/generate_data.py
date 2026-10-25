"""
Synthetic HR data warehouse generator for Arcadia Systems (fictional).

Simulates the company day by day from the opening month-end (2021-06-30) to the end
of FY2026 (2026-06-30) and writes raw warehouse tables (CSV) to data/raw/.

What it simulates
  * An org design: CEO -> 8 function heads -> sub-function heads -> department
    heads -> directors -> people managers -> individual contributors. Every worker
    has exactly one manager (the CEO reports to the board), and the hierarchy is
    kept valid every day: when a manager leaves, the team is reassigned the next
    day; when a team grows past 10, it is split and a new manager is appointed.
  * Job levels L1-L12 with a base salary per level and country, raises on each hire
    anniversary from a tenure schedule, promotions (one level up) and demotions
    (one level down) after the annual review, and a performance bonus.
  * Hires, voluntary and involuntary terminations, transfers, international moves,
    office relocations, a restructuring and a reorganization. Every employee is 1.0 FTE
    (release 3: no part-time).
  * Real ECB FX rates and researched fringe rates (see fx_rates.py, fringe_research.py).

Events inside a month are applied in date order, so effective-dated records never
overlap. The output is deterministic: the same seed always produces the same files.

    python generator/generate_data.py
"""

from __future__ import annotations

import bisect
import calendar
import datetime as dt
import math
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

import contingent_workforce
import cw_operations
import cw_positions
import fringe_research
import fx_rates
import helix_service_desk
import keystone_feed
import source_systems
import reference_data as ref

SEED = 20261009
ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "raw"
rng = np.random.default_rng(SEED)
name_rng = np.random.default_rng(SEED + 1)   # names draw from their own stream, so they never shift the simulation


def domain_stream(domain: str) -> np.random.Generator:
    """A random stream of its own for one domain of the simulation.

    Each domain (positions, recruiting, plan, ...) draws from a stream seeded by SEED and
    the domain's name, so adding draws in one domain never shifts the draws of another.
    The worker simulation keeps `rng` and the names keep `name_rng`, unchanged.
    """
    key = int.from_bytes(domain.encode("utf-8"), "big") % (2**63)
    return np.random.default_rng(np.random.SeedSequence([SEED, key]))


position_rng = domain_stream("positions")      # vacancy decisions, re-levelling, seat relocation
recruiting_rng = domain_stream("recruiting")   # requisitions, candidates, time to fill
plan_rng = domain_stream("plan")               # budget and reforecast versions
ONE_DAY = dt.timedelta(days=1)


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


def weighted_choice(options: dict, stream: np.random.Generator | None = None):
    keys = list(options.keys())
    weights = np.array([options[k] for k in keys], dtype=float)
    return keys[(stream or rng).choice(len(keys), p=weights / weights.sum())]


def round_salary(amount: float) -> float:
    return float(round(amount / 100.0) * 100)


def anniversary(hire: dt.date, year: int) -> dt.date:
    day = min(hire.day, calendar.monthrange(year, hire.month)[1])
    return dt.date(year, hire.month, day)


MONTH_ENDS: list[dt.date] = []
_d = dt.date.fromisoformat(ref.FIRST_SNAPSHOT)
while _d <= dt.date.fromisoformat(ref.LAST_SNAPSHOT):
    MONTH_ENDS.append(_d)
    _d = month_end((_d + ONE_DAY).year, (_d + ONE_DAY).month)

COUNTRY = {c: dict(zip(["name", "region", "currency", "pay_index", "weight"], v)) for c, v in ref.COUNTRIES.items()}
OFFICE = {o[0]: dict(zip(["id", "name", "site_type", "street", "city", "state", "postal", "country",
                          "lat", "lon", "pay_zone", "opened", "weight"], o)) for o in ref.OFFICES}
for o in OFFICE.values():
    o["opened"] = dt.date.fromisoformat(o["opened"])
DEPT = {d[0]: dict(zip(["id", "name", "sub_function", "function", "families", "profile", "size_weight", "growth_weight"], d))
        for d in ref.DEPARTMENTS}
REORG_DATE = dt.date.fromisoformat(ref.REORGANIZATION["date"])
RESTRUCTURE_DATE = dt.date.fromisoformat(ref.RESTRUCTURING["date"])
CONVERSION_DATE = dt.date.fromisoformat(ref.COMP_CONVERSION_DATE)
FIRST_ME, LAST_ME = MONTH_ENDS[0], MONTH_ENDS[-1]


# ======================================================================================
# 1. Pay structure: base salary per level and country (local currency), moving each July 1
# ======================================================================================
LEVEL_FX_DATE = dt.date.fromisoformat(ref.LEVEL_BASE_FX_DATE)
LEVEL_BASE: dict[tuple[int, str], float] = {}
for lvl, (_, _, _, us_base) in ref.JOB_LEVELS.items():
    for cc, c in COUNTRY.items():
        LEVEL_BASE[(lvl, cc)] = round_salary(us_base * c["pay_index"] / fx_rates.usd_per_local(c["currency"], LEVEL_FX_DATE))

RANGE_FISCAL_YEARS = list(range(fiscal_year(FIRST_ME), fiscal_year(LAST_ME) + 1))


def structure_increase(fy: int, cc: str) -> float:
    return ref.RANGE_STRUCTURE_INCREASE[fy] + ref.RANGE_STRUCTURE_COUNTRY_PP.get(cc, 0.0)


def _range_factor(fy: int, cc: str) -> float:
    """Range midpoint in fiscal year `fy` relative to the anchor year's level base."""
    f = 1.0
    for y in range(ref.RANGE_ANCHOR_FY + 1, fy + 1):
        f *= 1 + structure_increase(y, cc)
    for y in range(fy + 1, ref.RANGE_ANCHOR_FY + 1):
        f /= 1 + structure_increase(y, cc)
    return f


RANGE_MID: dict[tuple[int, int, str], float] = {
    (fy, lvl, cc): round_salary(base * _range_factor(fy, cc))
    for fy in RANGE_FISCAL_YEARS for (lvl, cc), base in LEVEL_BASE.items()}


def level_base(level: int, loc: str, on: dt.date) -> float:
    """Range midpoint for the level at this office on `on` (country structure x office pay zone)."""
    o = OFFICE[loc]
    fy = min(max(fiscal_year(on), RANGE_FISCAL_YEARS[0]), RANGE_FISCAL_YEARS[-1])
    return RANGE_MID[(fy, level, o["country"])] * o["pay_zone"]


def range_max(level: int, loc: str, on: dt.date) -> float:
    return level_base(level, loc, on) * ref.RANGE_MAX_PCT


def range_min(level: int, loc: str, on: dt.date) -> float:
    return level_base(level, loc, on) * ref.RANGE_MIN_PCT


def tenure_raise(completed_years: int) -> float:
    for lo, hi, pct in ref.TENURE_INCREASE:
        if lo <= completed_years <= hi:
            return pct
    return 0.0


def offer_factor() -> float:
    return float(np.clip(rng.lognormal(0.0, 0.045), 0.90, 1.10))


# ======================================================================================
# 2. State and record writers
# ======================================================================================
job_rows: list[dict] = []
comp_rows: list[dict] = []
review_rows: list[dict] = []
bonus_rows: list[dict] = []
workers: dict[str, dict] = {}          # everyone ever employed
active: dict[str, dict] = {}           # current employees, insertion-ordered
reports: dict[str, dict] = defaultdict(dict)        # manager -> {report: None}
dept_pms: dict[str, dict] = defaultdict(dict)       # department -> {people manager: None}
dept_members: dict[str, dict] = defaultdict(dict)   # department -> {worker: None}
dept_head: dict[str, str] = {}
sub_head: dict[str, str] = {}
func_head: dict[str, str] = {}
ceo_id: str | None = None
pending: dict[dt.date, list] = defaultdict(list)    # day -> [("reassign", worker_id) | ("succession", org)]
_seq = {"worker": 100000, "position": 200000, "requisition": 300000, "assignment": 0}

JOB_REASON_RANK = {r: i for i, r in enumerate([
    "Hire", "Reorganization", "Transfer", "Succession", "Promotion", "Demotion", "Location Change",
    "Became People Manager", "Returned to Individual Contributor", "FTE Change", "Manager Change"])}
COMP_REASON_RANK = {r: i for i, r in enumerate([
    "Hire", "Conversion", "Promotion", "Demotion", "International Transfer", "Relocation Adjustment",
    "Tenure Increase", "Market Adjustment"])}
EXEC_TITLES = {"CEO": ("EXE-CEO", "Chief Executive Officer")}
for fn, (org, title, _) in ref.FUNCTIONS.items():
    EXEC_TITLES[fn] = (f"EXE-{org[4:]}", title)


def next_id(kind: str, prefix: str) -> str:
    _seq[kind] += 1
    return f"{prefix}{_seq[kind]}"


def org_role(w: dict) -> str | None:
    """Org unit this worker leads, if any."""
    return w.get("leads")


def is_org_leader(w: dict) -> bool:
    return w["leads"] is not None


def job_profile_id(w: dict) -> str:
    if w["is_exec"]:
        return w["exec_profile"]
    if w["is_pm"] and w["level"] in (5, 6):
        return f'{w["family"]}-M{w["level"]}'
    return f'{w["family"]}-L{w["level"]}'


def job_fields(w: dict) -> dict:
    return {"position_id": w["position_id"], "department_id": w["dept"], "location_id": w["loc"],
            "job_profile_id": job_profile_id(w), "job_level": w["level"], "fte": w["fte"],
            "manager_worker_id": w["mgr"], "is_people_manager": w["is_pm"], "leads_org_unit_id": w["leads"]}


def job_change(w: dict, on: dt.date, reason: str):
    cur = w.get("job")
    if cur is not None:
        if on < cur["effective_start_date"]:
            raise RuntimeError(f"Out-of-order job change for {w['worker_id']} on {on}")
        if on == cur["effective_start_date"]:
            cur.update(job_fields(w))
            if JOB_REASON_RANK[reason] < JOB_REASON_RANK[cur["action_reason"]]:
                cur["action_reason"] = reason
            seat_follow(w, on, reason)
            return
        cur["effective_end_date"] = on - ONE_DAY
    w["job"] = {"worker_id": w["worker_id"], "effective_start_date": on, "effective_end_date": None,
                "action_reason": reason, **job_fields(w)}
    job_rows.append(w["job"])
    seat_follow(w, on, reason)


def comp_change(w: dict, on: dt.date, reason: str):
    cur = w.get("comp")
    if cur is not None:
        if on < cur["effective_start_date"]:
            raise RuntimeError(f"Out-of-order comp change for {w['worker_id']} on {on}")
        if on == cur["effective_start_date"]:
            cur["base_salary_annual_local"] = w["salary"]
            cur["currency_code"] = COUNTRY[w["country"]]["currency"]
            if COMP_REASON_RANK[reason] < COMP_REASON_RANK[cur["action_reason"]]:
                cur["action_reason"] = reason
            return
        cur["effective_end_date"] = on - ONE_DAY
    w["comp"] = {"worker_id": w["worker_id"], "effective_start_date": on, "effective_end_date": None,
                 "action_reason": reason, "currency_code": COUNTRY[w["country"]]["currency"],
                 "base_salary_annual_local": w["salary"]}
    comp_rows.append(w["comp"])


# --------------------------------------------------------------------------------------
# Seats: positions, requisitions and seat assignments
# --------------------------------------------------------------------------------------
# A position is a seat that outlives the people in it. Every worker holds exactly one
# seat; while it is filled the seat follows its incumbent (a promotion re-levels the seat
# in place). When the incumbent leaves or moves to another seat, the seat is decided:
# backfilled as is, re-levelled, relocated within the country, frozen or eliminated.
# Hires and internal moves fill ready open seats first and create net-new seats only
# when none fits. Leader seats are refilled through succession.
pos_rows: list[dict] = []                  # dim_position, SCD2
assign_rows: list[dict] = []               # fact_position_assignment
req_rows: dict[str, dict] = {}             # fact_requisition, by id
seats: dict[str, dict] = {}
open_seats: dict[str, None] = {}           # status Open with an open requisition, waiting for a fill
frozen_seats: dict[str, None] = {}
org_seat: dict[str, str] = {}              # org unit -> the seat its leader holds

SEAT_REASON_FROM_JOB = {
    "Promotion": "Re-levelled with incumbent", "Demotion": "Re-levelled with incumbent",
    "Succession": "Re-levelled with incumbent", "Location Change": "Relocated with incumbent",
    "FTE Change": "FTE change with incumbent", "Became People Manager": "Job change with incumbent",
    "Returned to Individual Contributor": "Job change with incumbent", "Reorganization": "Reorganization",
}


def seat_profile(s: dict) -> str:
    if s["exec_profile"]:
        return s["exec_profile"]
    if s["is_pm"] and s["level"] in (5, 6):
        return f'{s["family"]}-M{s["level"]}'
    return f'{s["family"]}-L{s["level"]}'


def cost_center_id(dept: str, loc: str) -> str:
    """Cost center = department x country: the department's code plus the office's country."""
    return f"CC-{dept[2:]}0-{OFFICE[loc]['country']}"


def seat_fields(s: dict) -> dict:
    return {"status": s["status"], "department_id": s["dept"], "cost_center_id": cost_center_id(s["dept"], s["loc"]),
            "location_id": s["loc"], "job_profile_id": seat_profile(s), "job_level": s["level"], "fte": s["fte"]}


def seat_write(s: dict, on: dt.date, reason: str):
    """Write the seat's state from `on` (SCD2): close the current row, or merge into it on the same day."""
    fields = seat_fields(s)
    cur = s["row"]
    if cur is not None:
        if on < cur["effective_start_date"]:
            raise RuntimeError(f"Out-of-order seat change for {s['id']} on {on}")
        if all(cur[k] == v for k, v in fields.items()):
            return
        if on == cur["effective_start_date"]:
            if cur["status"] != fields["status"]:
                cur["change_reason"] = reason
            cur.update(fields)
            return
        cur["effective_end_date"] = on - ONE_DAY
    s["row"] = {"position_id": s["id"], "effective_start_date": on, "effective_end_date": None,
                "change_reason": reason, **fields, "created_date": s["created"], "created_reason": s["created_reason"]}
    pos_rows.append(s["row"])


def new_seat(on: dt.date, reason: str, dept: str, family: str, level: int, loc: str, is_pm: bool, fte: float,
             status: str = "Open", exec_profile: str | None = None) -> dict:
    s = {"id": next_id("position", "P"), "created": on, "created_reason": reason, "row": None, "status": status,
         "dept": dept, "family": family, "level": level, "loc": loc, "is_pm": is_pm, "fte": fte,
         "exec_profile": exec_profile, "incumbent": None, "filled_before": False, "req": None,
         "ready_on": None, "deadline": None, "resolve": None, "vacated_on": None, "reserved": False}
    seats[s["id"]] = s
    seat_write(s, on, reason)
    return s


def seat_from_worker(s: dict, w: dict):
    s.update(dept=w["dept"], family=w["family"], level=w["level"], loc=w["loc"], is_pm=w["is_pm"], fte=w["fte"],
             exec_profile=w["exec_profile"] if w["is_exec"] else None)


def seat_follow(w: dict, on: dt.date, reason: str):
    """A filled seat follows its incumbent's job changes."""
    s = seats.get(w["position_id"])
    if s is None or s["incumbent"] != w["worker_id"]:
        return
    seat_from_worker(s, w)
    seat_write(s, on, SEAT_REASON_FROM_JOB.get(reason, "Job change with incumbent"))


def time_to_fill(level: int) -> int:
    med = ref.REQ_TIME_TO_FILL_MEDIAN[min(level, 11)]
    days = recruiting_rng.lognormal(math.log(med), ref.REQ_TIME_TO_FILL_SIGMA)
    return int(np.clip(round(days), ref.REQ_TIME_TO_FILL_MIN, 240))


def approval_lag() -> int:
    share, (lo, hi) = ref.REQ_LATE_APPROVAL
    if recruiting_rng.random() < share:
        return int(recruiting_rng.integers(lo, hi + 1))
    return int(recruiting_rng.integers(ref.REQ_APPROVAL_DAYS[0], ref.REQ_APPROVAL_DAYS[1] + 1))


def new_requisition(s: dict, opened: dt.date, approved: dt.date, hiring_manager: str | None) -> dict:
    r = {"requisition_id": next_id("requisition", "R"), "position_id": s["id"],
         "req_type": "Backfill" if s["filled_before"] else "Net-new",
         "opened_date": opened, "approved_date": approved, "target_start_date": approved + dt.timedelta(days=45),
         "filled_date": None, "cancelled_date": None, "status": "Open",
         "department_id": s["dept"], "cost_center_id": cost_center_id(s["dept"], s["loc"]), "location_id": s["loc"],
         "job_profile_id": seat_profile(s), "job_level": s["level"],
         "hiring_manager_id": hiring_manager, "filled_by_worker_id": None, "fill_source": None}
    req_rows[r["requisition_id"]] = r
    s["req"] = r["requisition_id"]
    return r


def open_for_hiring(s: dict, day: dt.date, reason: str, hiring_manager: str | None):
    """Seat goes to Open with an approved requisition; it can be filled once recruiting had time."""
    s["status"] = "Open"
    seat_write(s, day, reason)
    approved = day + dt.timedelta(days=approval_lag())
    new_requisition(s, day, approved, hiring_manager)
    s["ready_on"] = approved + dt.timedelta(days=time_to_fill(s["level"]))
    s["deadline"] = approved + dt.timedelta(days=ref.REQ_MAX_OPEN_DAYS)
    s["reserved"] = False
    frozen_seats.pop(s["id"], None)
    open_seats[s["id"]] = None


def is_ready(s: dict, on: dt.date) -> bool:
    return not s["reserved"] and s["ready_on"] is not None and s["ready_on"] <= on < s["deadline"]


def assign(w: dict, s: dict, on: dt.date, fill_type: str):
    """`w` starts in seat `s` on `on`. The seat takes the worker's job as it stands."""
    if s["incumbent"] is not None:
        raise RuntimeError(f"Seat {s['id']} already has {s['incumbent']}")
    if fill_type != "Initial" and s["req"] is None:   # an immediate refill (succession, team backfill)
        opened = s["vacated_on"] or on
        new_requisition(s, opened, opened, None)
    req_id = s["req"]
    if req_id:
        r = req_rows[req_id]
        r.update(filled_date=on, status="Filled", filled_by_worker_id=w["worker_id"],
                 fill_source="Internal" if fill_type == "Internal Move" else "External")
    w["position_id"] = s["id"]
    s.update(incumbent=w["worker_id"], status="Filled", filled_before=True, req=None, ready_on=None,
             deadline=None, resolve=None, reserved=False)
    open_seats.pop(s["id"], None)
    frozen_seats.pop(s["id"], None)
    seat_from_worker(s, w)
    seat_write(s, on, "Initial" if fill_type == "Initial" else "Filled")
    _seq["assignment"] += 1
    w["assignment"] = {"assignment_id": f"PA{_seq['assignment']:07d}", "position_id": s["id"],
                       "worker_id": w["worker_id"], "start_date": on, "end_date": None, "fill_type": fill_type,
                       "requisition_id": req_id, "vacate_reason": None}
    assign_rows.append(w["assignment"])


def vacate(w: dict, last_day: dt.date, reason: str) -> dict:
    """`w` leaves their seat after `last_day`. Returns the seat, not yet decided."""
    s = seats[w["position_id"]]
    w["assignment"].update(end_date=last_day, vacate_reason=reason)
    s["incumbent"] = None
    s["vacated_on"] = last_day + ONE_DAY
    s["last_manager"] = w["mgr"]
    return s


def reserve(s: dict, day: dt.date):
    """A leader or team-backfill seat: open, refilled by the succession routine, not by recruiting."""
    s["status"], s["reserved"] = "Open", True
    seat_write(s, day, "Vacated")


def relocation_office(s: dict, on: dt.date) -> str | None:
    cc = OFFICE[s["loc"]]["country"]
    opts = {o["id"]: o["weight"] * o["pay_zone"] ** -ref.RELOCATE_ZONE_POWER
            for o in OFFICE.values() if o["country"] == cc and o["opened"] <= on and o["id"] != s["loc"]}
    return weighted_choice(opts, position_rng) if opts else None


def decide_seat(s: dict, day: dt.date, restructuring: bool = False):
    """What happens to a vacated seat, effective `day` (the first day it is empty)."""
    options = ref.SEAT_DECISION_RESTRUCTURING if restructuring else ref.SEAT_DECISION
    outcome = weighted_choice(options, position_rng)
    hm = s.get("last_manager")
    if outcome == "Backfill re-levelled":
        if s["level"] >= 7 or s["exec_profile"]:
            outcome = "Backfill as is"
        else:
            down = position_rng.random() < ref.RELEVEL_DOWN_SHARE
            if s["is_pm"]:                           # a manager seat is refilled as an IC seat one level down
                s["is_pm"], s["level"] = False, s["level"] - 1
            elif (down and s["level"] > 1) or s["level"] == 6:
                s["level"] -= 1
            else:
                s["level"] += 1
            open_for_hiring(s, day, "Re-levelled for backfill", hm)
            return
    if outcome == "Backfill relocated":
        new_loc = relocation_office(s, day)
        if new_loc is None:
            outcome = "Backfill as is"
        else:
            s["loc"] = new_loc
            open_for_hiring(s, day, "Relocated for backfill", hm)
            return
    if outcome == "Backfill as is":
        open_for_hiring(s, day, "Vacated", hm)
    elif outcome == "Freeze":
        freeze(s, day, "Frozen")
    else:
        eliminate(s, day)


def freeze(s: dict, day: dt.date, reason: str):
    s["status"], s["reserved"] = "Frozen", False
    seat_write(s, day, reason)
    open_seats.pop(s["id"], None)
    frozen_seats[s["id"]] = None
    lo, hi = ref.FROZEN_SEAT_DAYS
    s["resolve"] = (day + dt.timedelta(days=int(position_rng.integers(lo, hi + 1))),
                    "Unfreeze" if position_rng.random() < ref.FROZEN_SEAT_UNFREEZE_SHARE else "Eliminate")


def eliminate(s: dict, day: dt.date):
    s["status"], s["reserved"] = "Eliminated", False
    seat_write(s, day, "Eliminated")
    open_seats.pop(s["id"], None)
    frozen_seats.pop(s["id"], None)


def seat_housekeeping(me: dt.date):
    """Month-end: cancel requisitions open too long, resolve frozen seats that are due."""
    for sid in list(open_seats):
        s = seats[sid]
        if s["deadline"] <= me:
            r = req_rows[s["req"]]
            r.update(cancelled_date=s["deadline"], status="Cancelled")
            s["req"] = None
            if position_rng.random() < ref.REQ_CANCELLED_FREEZE_SHARE:
                freeze(s, s["deadline"], "Requisition cancelled")
            else:
                eliminate(s, s["deadline"])
    for sid in list(frozen_seats):
        s = seats[sid]
        due, outcome = s["resolve"]
        if due <= me:
            if outcome == "Unfreeze":
                open_for_hiring(s, due, "Unfrozen", s.get("last_manager"))
            else:
                eliminate(s, due)


def take_ready_seat(on: dt.date, fits=None, internal: bool = False) -> dict | None:
    """The ready open seat waiting longest (optionally among those `fits` accepts). An internal
    candidate can take a seat as soon as its requisition is approved: no external search needed."""
    best = None
    for sid in open_seats:
        s = seats[sid]
        if internal:
            ok = (not s["reserved"] and req_rows[s["req"]]["approved_date"] <= on < s["deadline"])
        else:
            ok = is_ready(s, on)
        if ok and (fits is None or fits(s)) and (best is None or s["ready_on"] < best["ready_on"]):
            best = s
    return best


# --------------------------------------------------------------------------------------
# Hierarchy rules
# --------------------------------------------------------------------------------------
def can_manage(m: dict, w: dict) -> bool:
    """A manager outranks people managers; individual contributors may share the level."""
    if m is w or m["worker_id"] not in active:
        return False
    if w["is_pm"] or w["level"] >= 7:
        return m["level"] > w["level"]
    return m["level"] >= w["level"]


def leader_manager(w: dict) -> str | None:
    """Manager of an org leader: the next leader up the org design."""
    if w["worker_id"] == ceo_id:
        return None
    if w["is_exec"]:
        return ceo_id
    d = DEPT[w["dept"]]
    if w["leads"] in {v[0] for v in ref.SUB_FUNCTIONS.values()}:
        return func_head[d["function"]]
    # department head
    sh = sub_head.get(d["sub_function"])
    if sh and sh != w["worker_id"] and sh in active:
        return sh
    return func_head[d["function"]]


def best_manager(w: dict, exclude: set[str] = frozenset(), cap: int | None = None) -> str:
    cap = cap or ref.SPAN_OF_CONTROL_MAX
    best, best_score = None, None
    for mid in dept_pms[w["dept"]]:
        if mid in exclude:
            continue
        m = active.get(mid)
        if m is None or not can_manage(m, w):
            continue
        span = len(reports[mid])
        score = (span >= cap, m["level"] - w["level"], m["country"] != w["country"], span, rng.random())
        if best_score is None or score < best_score:
            best, best_score = mid, score
    if best is None:                       # nobody in the department outranks them
        head = dept_head.get(w["dept"])
        if head and head in active and head not in exclude and head != w["worker_id"] and can_manage(active[head], w):
            return head
        d = DEPT[w["dept"]]
        sh = sub_head.get(d["sub_function"])
        if sh and sh in active and can_manage(active[sh], w):
            return sh
        return func_head[d["function"]]
    return best


def set_manager(w: dict, mid: str | None, on: dt.date, reason: str = "Manager Change"):
    old = w["mgr"]
    if old == mid:
        return
    if old is not None:
        reports[old].pop(w["worker_id"], None)
    if mid is not None:
        reports[mid][w["worker_id"]] = None
    w["mgr"] = mid
    job_change(w, on, reason)


def place(w: dict, on: dt.date, reason: str = "Manager Change", exclude: set[str] = frozenset(), cap=None):
    mid = leader_manager(w) if is_org_leader(w) or w["is_exec"] else best_manager(w, exclude, cap)
    set_manager(w, mid, on, reason)


def manager_is_valid(w: dict) -> bool:
    if w["worker_id"] == ceo_id:
        return w["mgr"] is None
    m = active.get(w["mgr"]) if w["mgr"] else None
    if m is None or not can_manage(m, w):
        return False
    if is_org_leader(w) or w["is_exec"]:
        return True
    return m["dept"] == w["dept"]


def fix_manager(w: dict, on: dt.date, reason: str = "Manager Change"):
    if not manager_is_valid(w):
        place(w, on, reason)


def fix_reports_of(m: dict, on: dt.date):
    for rid in list(reports[m["worker_id"]]):
        r = active.get(rid)
        if r is not None and not manager_is_valid(r):
            place(r, on)


def make_pm(w: dict, flag: bool):
    w["is_pm"] = flag
    if flag:
        dept_pms[w["dept"]][w["worker_id"]] = None
    else:
        dept_pms[w["dept"]].pop(w["worker_id"], None)


# --------------------------------------------------------------------------------------
# People
# --------------------------------------------------------------------------------------
def pick_country(dept_id: str, on: dt.date, exclude: str | None = None) -> str:
    prof = ref.COUNTRY_PROFILES[DEPT[dept_id]["profile"]]
    options = {}
    for cc, c in COUNTRY.items():
        if cc == exclude:
            continue
        open_offices = [o for o in OFFICE.values() if o["country"] == cc and o["opened"] <= on]
        if not open_offices:
            continue
        boost = 3.0 if any((on - o["opened"]).days < 365 for o in open_offices) else 1.0
        wgt = c["weight"] * prof.get(cc, 1.0) * boost
        if wgt > 0:
            options[cc] = wgt
    return weighted_choice(options)


def pick_office(cc: str, on: dt.date, exclude: str | None = None) -> str | None:
    opts = {o["id"]: o["weight"] * (2.5 if (on - o["opened"]).days < 365 else 1.0)
            for o in OFFICE.values() if o["country"] == cc and o["opened"] <= on and o["id"] != exclude}
    return weighted_choice(opts) if opts else None


def pick_family(dept_id: str) -> str:
    return weighted_choice(DEPT[dept_id]["families"])


def random_fte() -> float:
    return float(rng.choice([1.0, 0.8, 0.5], p=[0.965, 0.025, 0.010]))


def random_name(cc: str) -> tuple[str, str]:
    first, last = ref.NAMES[COUNTRY[cc]["region"]]
    return first[name_rng.integers(len(first))], last[name_rng.integers(len(last))]


def new_worker(hire_date: dt.date, dept_id: str, level: int, family: str, cc: str, loc: str, salary: float,
               fte: float, is_exec: bool = False, comp_start: dt.date | None = None, exec_profile: str | None = None,
               leads: str | None = None, is_pm: bool = False) -> dict:
    first, last = random_name(cc)
    w = {"worker_id": next_id("worker", "W"), "first_name": first, "last_name": last,
         "hire_date": hire_date, "termination_date": None, "termination_type": None,
         "is_exec": is_exec, "exec_profile": exec_profile, "position_id": None, "assignment": None,
         "dept": dept_id, "family": family, "level": level, "country": cc, "loc": loc, "fte": 1.0,
         "fte_draw": fte,
         "salary": salary, "mgr": None, "is_pm": False, "leads": leads, "level_since": hire_date,
         "last_rating": None, "job": None, "comp": None}
    workers[w["worker_id"]] = w
    active[w["worker_id"]] = w
    dept_members[dept_id][w["worker_id"]] = None
    if is_pm:
        make_pm(w, True)
    return w


def hire_salary(level: int, loc: str, on: dt.date) -> float:
    return round_salary(level_base(level, loc, on) * offer_factor())


# ======================================================================================
# 3. Opening organization (as of the first month-end)
# ======================================================================================
def head_level_for(expected_size: float) -> int:
    return 9 if expected_size >= 1000 else 8 if expected_size >= 300 else 7


EXPECTED = {d: DEPT[d]["size_weight"] / sum(x["size_weight"] for x in DEPT.values()) * ref.START_HEADCOUNT for d in DEPT}
HEAD_LEVEL = {d: head_level_for(EXPECTED[d]) for d in DEPT}
HEAD_LEVEL["D-108"] = 8


def opening_hire(level: int, cc: str, loc: str, min_years: float = 0.05, mean_years: float = 4.5):
    tenure = min(20.0, max(min_years, rng.exponential(mean_years)))
    hire = FIRST_ME - dt.timedelta(days=int(tenure * 365.25))
    years_in_level = min(tenure, rng.exponential(2.5))
    salary = level_base(level, loc, FIRST_ME) * offer_factor()
    for y in range(1, int(years_in_level) + 1):
        salary = min(salary * (1 + tenure_raise(y)), range_max(level, loc, FIRST_ME))
    comp_start = max(hire, CONVERSION_DATE)
    return hire, round_salary(salary), comp_start


def open_records(w: dict, comp_start: dt.date):
    """An opening worker: a seat of their own since their hire date, then the job and pay records."""
    s = new_seat(w["hire_date"], "Initial", w["dept"], w["family"], w["level"], w["loc"], w["is_pm"], w["fte"],
                 exec_profile=w["exec_profile"] if w["is_exec"] else None)
    assign(w, s, w["hire_date"], "Initial")
    if w["leads"]:
        org_seat[w["leads"]] = s["id"]
    job_change(w, w["hire_date"], "Hire")
    comp_change(w, comp_start, "Hire" if comp_start == w["hire_date"] else "Conversion")


# Executive team: CEO and the eight function heads (held constant; excluded from pay reporting)
hq = "LOC-001"
hire, salary, cstart = opening_hire(12, "US", hq, min_years=3, mean_years=6)
ceo = new_worker(hire, "D-901", 12, "EXE", "US", hq, round_salary(salary * 1.6), 1.0, is_exec=True,
                 exec_profile="EXE-CEO", leads=ref.CEO[0], is_pm=True)
ceo_id = ceo["worker_id"]
open_records(ceo, cstart)
for fn, (org, title, lvl) in ref.FUNCTIONS.items():
    hire, salary, cstart = opening_hire(lvl, "US", hq, min_years=2, mean_years=5)
    w = new_worker(hire, "D-901", lvl, "EXE", "US", hq, round_salary(salary * 1.3), 1.0, is_exec=True,
                   exec_profile=EXEC_TITLES[fn][0], leads=org, is_pm=True)
    func_head[fn] = w["worker_id"]
    open_records(w, cstart)
for w in [ceo] + [workers[func_head[f]] for f in ref.FUNCTIONS]:
    set_manager(w, leader_manager(w), w["hire_date"])

# Sub-function heads sit in their home department
for sf, (org, fn, title, lvl, home) in ref.SUB_FUNCTIONS.items():
    fam = {"Engineering": "SWE", "Infrastructure": "ITS", "Sales": "SAL", "Client Services": "CSM"}[sf]
    hire, salary, cstart = opening_hire(lvl, "US", hq, min_years=2)
    w = new_worker(hire, home, lvl, fam, "US", hq, salary, 1.0, leads=org, is_pm=True)
    dept_pms[home].pop(w["worker_id"])       # leads department heads only, not teams in its home department
    sub_head[sf] = w["worker_id"]
    open_records(w, cstart)
    set_manager(w, leader_manager(w), w["hire_date"])

# Departments: members, head, people managers, then the reporting lines top-down
for dept_id, d in DEPT.items():
    if dept_id in ("D-108", "D-901"):
        continue
    n = int(round(EXPECTED[dept_id]))
    head_lvl = HEAD_LEVEL[dept_id]
    head_cc = "US" if d["profile"] in ("corporate", "us_only") or rng.random() < 0.5 else pick_country(dept_id, FIRST_ME)
    head_loc = pick_office(head_cc, FIRST_ME)
    hire, salary, cstart = opening_hire(head_lvl, head_cc, head_loc, min_years=1.5)
    head = new_worker(hire, dept_id, head_lvl, pick_family(dept_id), head_cc, head_loc, salary, 1.0,
                      leads=dept_id, is_pm=True)
    dept_head[dept_id] = head["worker_id"]
    open_records(head, cstart)

    n_l7 = 0 if head_lvl == 7 else round(n / ref.DIRECTOR_RATIO)
    if head_lvl == 8:
        n_l7 = min(n_l7, 8)
    n_l8 = math.ceil(n_l7 / 6) if head_lvl >= 9 else 0
    levels = [8] * n_l8 + [7] * n_l7
    levels += [weighted_choice(ref.START_LEVEL_MIX) for _ in range(n - 1 - len(levels))]
    members = []
    for lvl in levels:
        cc = pick_country(dept_id, FIRST_ME)
        loc = pick_office(cc, FIRST_ME)
        hire, salary, cstart = opening_hire(lvl, cc, loc, min_years=1.0 if lvl >= 7 else 0.05)
        w = new_worker(hire, dept_id, lvl, pick_family(dept_id), cc, loc, salary, 1.0 if lvl >= 7 else random_fte(),
                       comp_start=cstart, is_pm=lvl >= 7)
        open_records(w, cstart)
        members.append(w)

    # appoint people managers until there is one per SPAN_OF_CONTROL_TARGET people
    needed = math.ceil(n / ref.SPAN_OF_CONTROL_TARGET) - 1 - sum(1 for w in members if w["is_pm"])
    needed = max(0, needed)
    l6 = [w for w in members if w["level"] == 6]
    l5 = [w for w in members if w["level"] == 5]
    rng.shuffle(l6)
    rng.shuffle(l5)
    take6 = min(len(l6), round(needed / 3))           # one Senior Manager per two Managers
    chosen = l6[:take6] + l5[:needed - take6]
    chosen += l6[take6:take6 + needed - len(chosen)]  # small departments may lack L5s
    for w in chosen:
        make_pm(w, True)
        job_change(w, w["hire_date"], "Hire")

    set_manager(head, leader_manager(head), head["hire_date"], "Hire")
    for w in sorted(members, key=lambda x: (-int(x["is_pm"]), -x["level"], x["worker_id"])):
        # opening reporting lines are stated on each worker's current record
        place(w, w["job"]["effective_start_date"], "Hire", cap=ref.SPAN_OF_CONTROL_TARGET + 1)

# Opening records start on each worker's hire date, which can be years before their
# current manager joined. History before the HR system conversion has no reporting
# line, so the record is split on the manager's start date: no manager before it.
for w in list(active.values()):
    mid = w["mgr"]
    if mid is None:
        continue
    m = workers[mid]
    if m["hire_date"] > w["job"]["effective_start_date"]:
        reports[mid].pop(w["worker_id"], None)
        w["mgr"] = None
        w["job"]["manager_worker_id"] = None
        set_manager(w, mid, m["hire_date"])

print(f"Opening organization: {len(active):,} people, "
      f"{sum(1 for w in active.values() if w['is_pm']):,} people managers")


# ======================================================================================
# 4. Events
# ======================================================================================
def leave_structures(w: dict, eff: dt.date) -> bool:
    """Take a worker out of the org on `eff - 1` (their last day): queue their team.
    Returns True when their seat is refilled by succession or a team backfill."""
    wid = w["worker_id"]
    dept_members[w["dept"]].pop(wid, None)
    dept_pms[w["dept"]].pop(wid, None)
    if w["mgr"]:
        reports[w["mgr"]].pop(wid, None)
    for rid in list(reports[wid]):
        pending[eff].append(("reassign", rid))
    if w["leads"]:
        pending[eff].insert(0, ("succession", w["leads"]))
        return True
    elif w["is_pm"] and reports[wid] and rng.random() < MANAGER_BACKFILL_RATE:
        pending[eff].insert(0, ("backfill", wid))
        return True
    return False


def terminate(w: dict, on: dt.date, kind: str, restructuring: bool = False):
    w["termination_date"], w["termination_type"] = on, kind
    w["job"]["effective_end_date"] = on
    w["comp"]["effective_end_date"] = on
    del active[w["worker_id"]]
    s = vacate(w, on, kind)
    if leave_structures(w, on + ONE_DAY):
        reserve(s, on + ONE_DAY)
    else:
        decide_seat(s, on + ONE_DAY, restructuring)


def promote(w: dict, on: dt.date, reason: str = "Promotion", increase: float | None = None):
    w["level"] += 1
    w["level_since"] = on
    inc = increase if increase is not None else rng.uniform(*ref.PROMOTION_INCREASE)
    w["salary"] = round_salary(max(w["salary"] * (1 + inc), range_min(w["level"], w["loc"], on)))
    job_change(w, on, reason)
    comp_change(w, on, "Promotion")
    fix_manager(w, on)


def demote(w: dict, on: dt.date):
    w["level"] -= 1
    w["level_since"] = on
    w["salary"] = round_salary(w["salary"] * (1 - rng.uniform(*ref.DEMOTION_DECREASE)))
    job_change(w, on, "Demotion")
    comp_change(w, on, "Demotion")
    fix_manager(w, on)


def net_new_seat(w: dict, on: dt.date, reason: str, recruited: bool) -> dict:
    """A seat created for `w`. A recruited seat was approved earlier, as long before the hire as
    recruiting takes; a seat created by an internal decision (team split, internal move) opens that day."""
    approved = opened = on
    if recruited:
        approved = on - dt.timedelta(days=time_to_fill(w["level"]))
        earliest = max(OFFICE[w["loc"]]["opened"], REORG_DATE if w["dept"] == "D-108" else approved)
        approved = max(approved, earliest)
        opened = approved - dt.timedelta(days=approval_lag())
    s = new_seat(approved, reason, w["dept"], w["family"], w["level"], w["loc"], w["is_pm"], w["fte"])
    new_requisition(s, opened, approved, None)
    return s


def hire_into(dept_id: str, level: int, on: dt.date, cc: str | None = None, loc: str | None = None,
              is_pm: bool = False, leads: str | None = None, seat: dict | None = None,
              seat_reason: str = "Net-new") -> dict:
    """An external hire, into `seat` when given (a backfill or a leader seat), otherwise into a net-new seat."""
    if seat is not None:
        dept_id, level, family = seat["dept"], seat["level"], seat["family"]
        is_pm = is_pm or seat["is_pm"]
        if cc is None:
            loc = seat["loc"]
            cc = OFFICE[loc]["country"]
        else:
            loc = loc or pick_office(cc, on)
    else:
        family = pick_family(dept_id)
        cc = cc or pick_country(dept_id, on)
        loc = loc or pick_office(cc, on)
    w = new_worker(on, dept_id, level, family, cc, loc, hire_salary(level, loc, on), 1.0 if leads else random_fte(),
                   leads=leads, is_pm=is_pm)
    if seat is None:
        seat = net_new_seat(w, on, seat_reason, recruited=seat_reason == "Net-new")
    assign(w, seat, on, "External Hire")
    job_change(w, on, "Hire")
    comp_change(w, on, "Hire")
    place(w, on, "Hire")
    r = req_rows.get(w["assignment"]["requisition_id"])
    if r is not None and r["hiring_manager_id"] is None:
        r["hiring_manager_id"] = w["mgr"]
    return w


def move_seat(w: dict, seat: dict, on: dt.date):
    """`w` leaves their seat the day before `on` and starts in `seat`; their old seat is decided."""
    old = vacate(w, on - ONE_DAY, "Internal Move Out")
    assign(w, seat, on, "Internal Move")
    decide_seat(old, on)


def succession(org: str, on: dt.date):
    """Fill a leader vacancy the day after the leader left."""
    if org in DEPT:                                   # department head
        if dept_head.get(org) in active:
            return
        others = [active[x]["level"] for x in dept_members[org] if x in active and not active[x]["leads"]]
        need = max(HEAD_LEVEL[org], (max(others) + 1) if others else 0)
        cands = [active[m] for m in dept_pms[org] if m in active and active[m]["level"] >= need - 1
                 and active[m]["assignment"]["start_date"] < on]
        cands.sort(key=lambda w: (-w["level"], w["hire_date"], w["worker_id"]))
        if cands and rng.random() >= ref.EXTERNAL_SUCCESSOR_SHARE:
            s = cands[0]
            dept_pms[org].pop(s["worker_id"], None)
            s["leads"] = org
            dept_head[org] = s["worker_id"]
            move_seat(s, seats[org_seat[org]], on)
            if s["level"] < need:
                promote(s, on, "Succession")
            else:
                job_change(s, on, "Succession")
            set_manager(s, leader_manager(s), on)
            dept_pms[org][s["worker_id"]] = None
        else:
            cc = "US" if rng.random() < 0.5 else pick_country(org, on)
            s = hire_into(org, need, on, cc=cc, leads=org, is_pm=True, seat=seats[org_seat[org]])
            dept_head[org] = s["worker_id"]
            set_manager(s, leader_manager(s), on, "Hire")
        return
    # sub-function head
    sf = next(k for k, v in ref.SUB_FUNCTIONS.items() if v[0] == org)
    if sub_head.get(sf) in active:
        return
    _, fn, _, need, home = ref.SUB_FUNCTIONS[sf]
    heads = [active[dept_head[d]] for d, x in DEPT.items()
             if x["sub_function"] == sf and dept_head.get(d) in active
             and active[dept_head[d]]["assignment"]["start_date"] < on]
    heads.sort(key=lambda w: (-w["level"], w["hire_date"], w["worker_id"]))
    if heads and rng.random() >= ref.EXTERNAL_SUCCESSOR_SHARE:
        s = heads[0]
        old_dept = s["leads"]
        dept_pms[s["dept"]].pop(s["worker_id"], None)
        dept_members[s["dept"]].pop(s["worker_id"], None)
        for rid in list(reports[s["worker_id"]]):      # their department gets a new head
            pending[on].append(("reassign", rid))
        s["leads"] = org
        sub_head[sf] = s["worker_id"]
        dept_head.pop(old_dept, None)
        own = vacate(s, on - ONE_DAY, "Internal Move Out")
        reserve(own, on)                               # their department head seat goes to succession
        s["dept"] = home
        assign(s, seats[org_seat[org]], on, "Internal Move")
        dept_members[home][s["worker_id"]] = None
        while s["level"] < need:
            promote(s, on, "Succession")
        job_change(s, on, "Succession")
        set_manager(s, leader_manager(s), on)
        pending[on].insert(0, ("succession", old_dept))
    else:
        s = hire_into(home, need, on, cc="US", leads=org, is_pm=True, seat=seats[org_seat[org]])
        dept_pms[home].pop(s["worker_id"], None)
        sub_head[sf] = s["worker_id"]
        set_manager(s, leader_manager(s), on, "Hire")
    for d, x in DEPT.items():                      # department heads now report to the new leader
        if x["sub_function"] == sf and dept_head.get(d) in active:
            fix_manager(active[dept_head[d]], on)
            h = active[dept_head[d]]
            if h["mgr"] != s["worker_id"] and can_manage(s, h):
                set_manager(h, s["worker_id"], on)


MANAGER_BACKFILL_RATE = 0.75


def backfill(departed_id: str, on: dt.date):
    """Replace a departed manager with one person who inherits the whole team."""
    gone = workers[departed_id]
    seat = seats[gone["position_id"]]
    team = [active[r] for r in reports[departed_id] if r in active and active[r]["dept"] == gone["dept"]
            and active[r]["mgr"] == departed_id]
    if not team:
        decide_seat(seat, on)
        return
    if gone["level"] >= 7:      # a director: their most senior manager steps up
        pool = [r for r in team if r["is_pm"] and r["level"] == gone["level"] - 1
                and r["assignment"]["start_date"] < on]
        if pool and rng.random() < 0.7:
            s = max(pool, key=lambda r: (r["level"], -r["hire_date"].toordinal(), r["worker_id"]))
            move_seat(s, seat, on)
            promote(s, on)
        else:
            s = hire_into(gone["dept"], gone["level"], on, cc=gone["country"], loc=gone["loc"], is_pm=True, seat=seat)
    else:                       # a first-line manager: a senior IC steps up, or an external hire
        pool = [r for r in team if not r["is_pm"] and 4 <= r["level"] <= gone["level"]
                and r["assignment"]["start_date"] < on]
        if pool and rng.random() < 0.6:
            s = max(pool, key=lambda r: (r["level"], -r["hire_date"].toordinal(), r["worker_id"]))
            make_pm(s, True)
            move_seat(s, seat, on)
            if s["level"] == 4:
                promote(s, on)
            else:
                job_change(s, on, "Became People Manager")
                fix_manager(s, on)
        else:
            s = hire_into(gone["dept"], gone["level"], on, cc=gone["country"], loc=gone["loc"], is_pm=True, seat=seat)
    for r in team:
        if r is not s and r["worker_id"] in active and can_manage(s, r):
            set_manager(r, s["worker_id"], on)


def run_pending(day: dt.date):
    while pending and min(pending) <= day:
        d = min(pending)
        items = pending.pop(d)
        for kind, key in items:
            if kind == "succession":
                succession(key, d)
        for kind, key in items:
            if kind == "backfill":
                backfill(key, d)
        for kind, key in items:
            if kind == "reassign":
                w = active.get(key)
                if w is not None and not manager_is_valid(w):
                    place(w, d)


def transfer(w: dict, on: dt.date):
    """Individual contributor changes department (10% also change country). They take a ready
    open seat that fits when there is one (an internal fill), otherwise a net-new seat."""
    if w["assignment"]["start_date"] >= on:
        return
    same_function = rng.random() < 0.7
    avail = [d for d in DEPT if d != "D-901" and (d != "D-108" or on >= REORG_DATE) and d != w["dept"]]
    options = [d for d in avail if not same_function or DEPT[d]["function"] == DEPT[w["dept"]]["function"]] or avail
    international = rng.random() < ref.INTERNATIONAL_SHARE_OF_TRANSFERS
    target = None
    if recruiting_rng.random() < ref.TRANSFER_TAKES_OPEN_SEAT:
        allowed = set(options)
        target = take_ready_seat(on, lambda s: s["dept"] in allowed and s["level"] == w["level"] and not s["is_pm"]
                                 and (OFFICE[s["loc"]]["country"] != w["country"]) == international, internal=True)
    if target is not None:
        new_dept, new_family, new_loc = target["dept"], target["family"], target["loc"]
    else:
        new_dept = options[rng.integers(len(options))]
        new_family = w["family"] if w["family"] in DEPT[new_dept]["families"] else pick_family(new_dept)
        new_loc = pick_office(pick_country(new_dept, on, exclude=w["country"]), on) if international else w["loc"]
    new_cc = OFFICE[new_loc]["country"]
    old_cc, old_loc = w["country"], w["loc"]
    dept_members[w["dept"]].pop(w["worker_id"], None)
    w["dept"], w["family"] = new_dept, new_family
    dept_members[new_dept][w["worker_id"]] = None
    pay_reason = None
    if new_cc != old_cc:
        old_usd = w["salary"] * fx_rates.usd_per_local(COUNTRY[old_cc]["currency"], on)
        old_index = COUNTRY[old_cc]["pay_index"] * OFFICE[old_loc]["pay_zone"]
        new_index = COUNTRY[new_cc]["pay_index"] * OFFICE[new_loc]["pay_zone"]
        new_usd = old_usd * new_index / old_index * rng.uniform(0.98, 1.05)
        w["salary"] = round_salary(new_usd / fx_rates.usd_per_local(COUNTRY[new_cc]["currency"], on))
        pay_reason = "International Transfer"
    elif OFFICE[new_loc]["pay_zone"] != OFFICE[old_loc]["pay_zone"]:
        w["salary"] = round_salary(w["salary"] * OFFICE[new_loc]["pay_zone"] / OFFICE[old_loc]["pay_zone"])
        pay_reason = "Relocation Adjustment"
    w["country"], w["loc"] = new_cc, new_loc
    move_seat(w, target or net_new_seat(w, on, "Net-new", recruited=False), on)
    job_change(w, on, "Transfer")
    if pay_reason:
        comp_change(w, on, pay_reason)
    place(w, on, "Transfer")


def relocate(w: dict, on: dt.date):
    new_loc = pick_office(w["country"], on, exclude=w["loc"])
    if new_loc is None:
        return False
    old_zone, new_zone = OFFICE[w["loc"]]["pay_zone"], OFFICE[new_loc]["pay_zone"]
    w["loc"] = new_loc
    job_change(w, on, "Location Change")
    if old_zone != new_zone:
        w["salary"] = round_salary(w["salary"] * new_zone / old_zone)
        comp_change(w, on, "Relocation Adjustment")
    return True


def attrition_probability(w: dict, on: dt.date) -> float:
    tenure = (on - w["hire_date"]).days / 365.25
    p = ref.MONTHLY_ATTRITION
    p *= 1.6 if tenure < 1 else 1.15 if tenure < 2 else 0.85 if tenure > 6 else 1.0
    p *= 0.5 if w["leads"] else 0.7 if w["level"] >= 7 else 1.0
    p *= {2023: 1.10, 2024: 0.85, 2025: 0.90, 2026: 1.00}.get(fiscal_year(on), 1.0)
    p *= 1.25 if DEPT[w["dept"]]["function"] == "Commercial" else 1.0
    p *= 1.6 if w["last_rating"] == "Needs Improvement" else 0.7 if w["last_rating"] == "Excellent" else 1.0
    return p


def rebalance(on: dt.date):
    """Month-end org hygiene, effective the next day: split big teams, staff empty ones."""
    for dept_id in DEPT:
        if dept_id == "D-901":
            continue
        for mid in list(dept_pms[dept_id]):
            m = active.get(mid)
            guard = 0
            while m is not None and len(reports[mid]) > ref.SPAN_OF_CONTROL_MAX and guard < 6:
                guard += 1
                if not split_team(m, on):
                    break
        for mid in list(dept_pms[dept_id]):
            m = active.get(mid)
            if m is None or reports[mid] or m["leads"]:
                continue
            if m["level"] <= 6:                       # a manager with no team goes back to IC work
                make_pm(m, False)
                job_change(m, on, "Returned to Individual Contributor")
                fix_manager(m, on)


def split_team(m: dict, on: dt.date) -> bool:
    team = [active[r] for r in reports[m["worker_id"]] if r in active]
    leaders = [r for r in team if r["is_pm"] or r["level"] >= 7]
    ics = [r for r in team if not (r["is_pm"] or r["level"] >= 7)]
    leader_branch = False
    if leaders and len(leaders) >= len(ics):
        ranked = sorted(leaders, key=lambda r: (-r["level"], r["hire_date"], r["worker_id"]))
        cand = None
        for r in ranked:                       # a senior leader takes over more junior ones
            if sum(1 for x in leaders if x["level"] < r["level"]) >= 2:
                cand = r
                break
        if cand is None and m["level"] >= ranked[0]["level"] + 2:
            cand = ranked[0]                   # or steps up a level to add a layer
            promote(cand, on)
        if cand is not None:
            leader_branch = True
            movers = [r for r in leaders if r is not cand and can_manage(cand, r)]
            movers = movers[: max(2, len(leaders) // 2)]
    if not leader_branch:
        pool = [r for r in ics if r["level"] >= 4 and r["level"] < 7]
        if pool:
            cand = max(pool, key=lambda r: (r["level"], -r["hire_date"].toordinal()))
            if cand["level"] == 4:
                make_pm(cand, True)
                promote(cand, on)
            else:
                make_pm(cand, True)
                job_change(cand, on, "Became People Manager")
                fix_manager(cand, on)
        else:
            lvl = max(5, min(m["level"] - 1, 6)) if m["level"] > 5 else 5
            if lvl > m["level"] or (lvl == m["level"]):
                return False
            cand = hire_into(m["dept"], lvl, on, cc=m["country"], loc=m["loc"], is_pm=True, seat_reason="Team split")
        movers = [r for r in ics if r is not cand and can_manage(cand, r)]
        movers.sort(key=lambda r: (r["country"] != cand["country"], r["worker_id"]))
        movers = movers[: len(ics) // 2]
    for r in movers:
        set_manager(r, cand["worker_id"], on)
    return bool(movers)


def annual_review(fy_end: dt.date):
    """Rate everyone employed at least three months; bonuses pay on Aug 31."""
    fy = fiscal_year(fy_end)
    fy_start = dt.date(fy_end.year - 1, 7, 1)
    cutoff = dt.date(fy_end.year, 3, 31)
    ratings = list(ref.PERFORMANCE_RATINGS)
    shares = np.array([ref.PERFORMANCE_RATINGS[r][1] for r in ratings])
    for w in active.values():
        if w["hire_date"] > cutoff:
            continue
        probs = shares.copy()
        if w["last_rating"] == "Excellent":
            probs = probs * np.array([1.8, 0.9, 0.5])
        elif w["last_rating"] == "Needs Improvement":
            probs = probs * np.array([0.4, 1.0, 2.5])
        rating = ratings[rng.choice(len(ratings), p=probs / probs.sum())]
        w["last_rating"] = rating
        pct = ref.PERFORMANCE_RATINGS[rating][0]
        months = min(12, (fy_end.year - max(w["hire_date"], fy_start).year) * 12
                     + fy_end.month - max(w["hire_date"], fy_start).month + 1)
        proration = round(months / 12, 4)
        review_rows.append({"worker_id": w["worker_id"], "fiscal_year": fy, "review_date": fy_end,
                            "rating": rating, "bonus_pct": pct})
        bonus_rows.append({"worker_id": w["worker_id"], "fiscal_year": fy, "payout_date": dt.date(fy_end.year, 8, 31),
                           "currency_code": COUNTRY[w["country"]]["currency"],
                           "base_salary_annual_local": w["salary"], "fte": w["fte"], "proration_factor": proration,
                           "bonus_pct": pct,
                           "bonus_amount_local": round(w["salary"] * w["fte"] * pct * proration, 2),
                           "payout_status": None})


def settle_bonuses(payout: dt.date):
    for b in bonus_rows:
        if b["payout_date"] == payout and b["payout_status"] is None:
            w = workers[b["worker_id"]]
            gone = w["termination_date"] is not None and w["termination_date"] < payout
            b["payout_status"] = "Forfeited" if gone else "Paid"


def promotion_cycle(on: dt.date):
    """July 1, after the June 30 review: promotions and the rare demotion."""
    for w in list(active.values()):
        if w["is_exec"] or w["leads"] or w["last_rating"] is None:
            continue
        if (on - w["level_since"]).days < 365 or w["hire_date"] > on - dt.timedelta(days=365):
            continue
        p_promo = ref.PROMOTION_PROBABILITY[w["last_rating"]] * (ref.PROMOTION_TO_L6_FACTOR if w["level"] == 5 else 1.0)
        if w["level"] <= 5 and rng.random() < p_promo:
            if w["is_pm"] and w["level"] == 5:
                promote(w, on)
                fix_reports_of(w, on)
            elif not w["is_pm"]:
                promote(w, on)
        elif (w["last_rating"] == "Needs Improvement" and not w["is_pm"] and w["level"] >= 2
              and rng.random() < ref.DEMOTION_PROBABILITY_NI):
            demote(w, on)


def reorganization(on: dt.date):
    movers = [w for w in active.values()
              if w["dept"] in ref.REORGANIZATION["source_departments"]
              and w["family"] in ref.REORGANIZATION["families"] and not w["leads"]]
    mover_ids = {w["worker_id"] for w in movers}
    target = ref.REORGANIZATION["target_department"]
    orphans = []
    for w in movers:
        dept_members[w["dept"]].pop(w["worker_id"], None)
        dept_pms[w["dept"]].pop(w["worker_id"], None)
        for rid in reports[w["worker_id"]]:
            if rid not in mover_ids:
                orphans.append(rid)
    head = max(movers, key=lambda w: (w["level"], -w["hire_date"].toordinal()))
    for w in movers:
        w["dept"] = target                      # the seat moves with its incumbent (job change below)
        dept_members[target][w["worker_id"]] = None
        if w["is_pm"]:
            dept_pms[target][w["worker_id"]] = None
    head["leads"] = target
    dept_head[target] = head["worker_id"]
    org_seat[target] = head["position_id"]
    if not head["is_pm"]:
        make_pm(head, True)
    top_other = max((w["level"] for w in movers if w is not head), default=0)
    while head["level"] < max(HEAD_LEVEL[target], top_other + 1):
        promote(head, on, "Reorganization")
    for w in sorted(movers, key=lambda x: (x is not head, -x["level"], x["worker_id"])):
        job_change(w, on, "Reorganization")
        if not manager_is_valid(w) or w["mgr"] not in mover_ids | {head["worker_id"]} or w is head:
            place(w, on, "Reorganization")
    for rid in orphans:
        r = active.get(rid)
        if r is not None and not manager_is_valid(r):
            place(r, on)


# ======================================================================================
# 5. Monthly simulation, events in date order
# ======================================================================================
def check_org(on: dt.date):
    """Every active worker has a valid manager on `on` (a leaver counts through their last day)."""
    bad = []
    for w in active.values():
        if w["worker_id"] == ceo_id:
            ok = w["mgr"] is None
        else:
            m = workers.get(w["mgr"]) if w["mgr"] else None
            ok = (m is not None and (m["termination_date"] is None or m["termination_date"] >= on)
                  and (m["level"] > w["level"] if (w["is_pm"] or w["level"] >= 7) else m["level"] >= w["level"])
                  and (is_org_leader(w) or w["is_exec"] or m["dept"] == w["dept"]))
        if not ok:
            bad.append(w["worker_id"])
    if bad:
        for wid in bad[:3]:
            w = workers[wid]; m = workers.get(w["mgr"]) if w["mgr"] else None
            print("BAD", {k: w[k] for k in ("worker_id", "dept", "level", "is_pm", "leads", "mgr", "hire_date")})
            if m: print("   MGR", {k: m[k] for k in ("worker_id", "dept", "level", "is_pm", "leads", "termination_date")})
            print("   JOB", w["job"])
        raise RuntimeError(f"{len(bad)} invalid reporting lines on {on}, e.g. {bad[:5]}")


check_org(FIRST_ME)
annual_review(FIRST_ME)          # FY2022 review on the opening month-end
hire_target_base = None
for i in range(1, len(MONTH_ENDS)):
    me = MONTH_ENDS[i]
    y, m = me.year, me.month
    fy = fiscal_year(me)
    first_day = dt.date(y, m, 1)

    run_pending(first_day)
    if m == ref.FISCAL_YEAR_START_MONTH or hire_target_base is None:
        hire_target_base = len(active)
        fy_start_index = i
    if m == 7:
        promotion_cycle(first_day)

    events: list[tuple[dt.date, int, str, object]] = []   # (date, order, kind, payload)
    n = 0

    # anniversaries: base salary moves with tenure
    for w in active.values():
        if w["hire_date"].month == m and w["hire_date"].year < y:
            on = anniversary(w["hire_date"], y)
            events.append((on, n, "tenure", w["worker_id"])); n += 1

    if (y, m) == (RESTRUCTURE_DATE.year, RESTRUCTURE_DATE.month):
        pool = [w["worker_id"] for w in active.values()
                if DEPT[w["dept"]]["function"] in ref.RESTRUCTURING["functions"] and not w["leads"] and not w["is_exec"]]
        for wid in rng.choice(pool, size=int(len(pool) * ref.RESTRUCTURING["share"]), replace=False):
            events.append((RESTRUCTURE_DATE, n, "restructure", wid)); n += 1
    if (y, m) == (REORG_DATE.year, REORG_DATE.month):
        events.append((REORG_DATE, -1, "reorg", None))

    for w in list(active.values()):
        if w["is_exec"]:
            continue
        if rng.random() < attrition_probability(w, me):
            on = random_day_in_month(y, m, 2 if m == 7 else 1)
            events.append((on, n, "terminate", (w["worker_id"], "Voluntary" if rng.random() < 0.8 else "Involuntary"))); n += 1
            continue
        r = rng.random()
        on = random_day_in_month(y, m, 2)
        cut1 = ref.MONTHLY_TRANSFER
        cut2 = cut1 + ref.OFF_CYCLE_PROMOTION_MONTHLY
        cut3 = cut2 + ref.MONTHLY_MARKET_ADJUSTMENT
        cut4 = cut3 + ref.MONTHLY_FTE_CHANGE
        cut5 = cut4 + ref.LOCATION_MOVE_MONTHLY
        kind = ("transfer" if r < cut1 else "promote" if r < cut2 else "market" if r < cut3
                else "fte" if r < cut4 else "relocate" if r < cut5 else None)
        if kind:
            events.append((on, n, kind, w["worker_id"])); n += 1

    # hiring toward the fiscal-year headcount target
    months_into_fy = i - fy_start_index + 1
    target = hire_target_base * (1 + ref.FY_NET_GROWTH[fy]) ** (months_into_fy / 12)
    expected_leavers = sum(1 for e in events if e[2] in ("terminate", "restructure"))
    n_hires = max(0, int(round(target - len(active) + expected_leavers + rng.normal(0, 8))))
    if (y, m) == (RESTRUCTURE_DATE.year, RESTRUCTURE_DATE.month):
        n_hires = int(n_hires * 0.3)
    for _ in range(n_hires):
        events.append((random_day_in_month(y, m), n, "hire", None)); n += 1

    events.sort(key=lambda e: (e[0], e[1]))
    for on, _, kind, payload in events:
        run_pending(on)
        if kind == "hire":
            dept_hc = {d: len(dept_members[d]) for d in DEPT}
            weights = {d: (dept_hc[d] + 15) * DEPT[d]["growth_weight"] for d in DEPT
                       if d != "D-901" and (d != "D-108" or on >= REORG_DATE)}
            seat = take_ready_seat(on)
            if seat is not None:                 # a backfill or a reopened seat
                hire_into(seat["dept"], seat["level"], on, seat=seat)
            else:                                # nothing ready: a net-new seat
                dept_id = weighted_choice(weights)
                hire_into(dept_id, weighted_choice(ref.HIRE_LEVEL_MIX), on)
            continue
        if kind == "reorg":
            reorganization(on)
            continue
        if kind == "terminate":
            wid, tt = payload
        else:
            wid = payload
        w = active.get(wid)
        if w is None:
            continue
        if kind == "terminate":
            terminate(w, on, tt)
        elif kind == "restructure":
            terminate(w, on, "Involuntary", restructuring=True)
        elif kind == "tenure":
            years = on.year - w["hire_date"].year
            cap = range_max(w["level"], w["loc"], on)
            new_salary = round_salary(min(w["salary"] * (1 + tenure_raise(years)), cap))
            if years >= 1 and new_salary > w["salary"] and on > CONVERSION_DATE:
                w["salary"] = new_salary
                comp_change(w, on, "Tenure Increase")
        elif kind == "transfer":
            if not w["is_pm"] and not w["leads"] and w["level"] <= 6:
                transfer(w, on)
        elif kind == "promote":
            if not w["leads"] and w["level"] <= 5 and (not w["is_pm"] or w["level"] == 5):
                promote(w, on)
                fix_reports_of(w, on)
        elif kind == "market":
            cap = range_max(w["level"], w["loc"], on)
            new_salary = round_salary(min(w["salary"] * (1 + rng.uniform(0.03, 0.07)), cap))
            if new_salary > w["salary"] and w["comp"]["effective_start_date"] != on:   # one pay change per day
                w["salary"] = new_salary
                comp_change(w, on, "Market Adjustment")
        elif kind == "fte":
            # Release 3: every employee is 1.0 FTE, so there are no FTE changes. The draw that
            # release 2 made is still made (tracked in fte_draw, never written out), so every
            # other random decision is unchanged and release 3 checks as a pure FTE change.
            if not w["leads"]:
                w["fte_draw"] = 1.0 if w["fte_draw"] < 1.0 else float(rng.choice([0.8, 0.5], p=[0.75, 0.25]))
        elif kind == "relocate":
            if not w["is_exec"]:
                relocate(w, on)

    run_pending(me)
    seat_housekeeping(me)
    if m == 6:
        annual_review(me)
    if m == 8:
        settle_bonuses(me)
    rebalance(me + ONE_DAY)
    check_org(me)
    if i % 12 == 0:
        print(f"  {me}: {len(active):,} active, {sum(1 for w in active.values() if w['is_pm']):,} people managers")

for b in bonus_rows:
    if b["payout_status"] is None:
        b["payout_status"] = "Scheduled"


# ======================================================================================
# 6. Same-day correction records in compensation history
# ======================================================================================
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
# 6b. Cost centers, the workforce plan and candidates
# ======================================================================================
# Written after the simulation from what happened, so they never change it. The plan is
# drawn around the actuals with an error that shrinks with each reforecast; candidates
# are the applicant pipeline behind each requisition.
QUARTER_ENDS = [me for me in MONTH_ENDS if me.month in (3, 6, 9, 12) and fiscal_year(me) > fiscal_year(FIRST_ME)]
FRINGE_RATE = {(r["country_code"], r["year"]): r["fringe_rate"] for r in fringe_research.build()[0]}

_wrong_ids = {id(c) for c in corrections}
_job_df = pd.DataFrame(job_rows)[["worker_id", "effective_start_date", "effective_end_date", "department_id",
                                  "location_id", "fte"]]
_job_df["cost_center_id"] = [cost_center_id(d, l) for d, l in zip(_job_df["department_id"], _job_df["location_id"])]
_comp_df = pd.DataFrame([r for r in comp_rows if id(r) not in _wrong_ids])[
    ["worker_id", "effective_start_date", "effective_end_date", "currency_code", "base_salary_annual_local"]]


def _as_of(df: pd.DataFrame, d: dt.date) -> pd.DataFrame:
    return df[(df["effective_start_date"] <= d) & (df["effective_end_date"].isna() | (df["effective_end_date"] >= d))]


# actuals at each quarter-end, by cost center: headcount, FTE, loaded run-rate by currency
_actual = {}
for qe in QUARTER_ENDS:
    j = _as_of(_job_df, qe)
    c = _as_of(_comp_df, qe)
    x = j.merge(c[["worker_id", "currency_code", "base_salary_annual_local"]], on="worker_id")
    x["loaded_local"] = x["base_salary_annual_local"] * x["fte"] * [
        1 + FRINGE_RATE[(OFFICE[l]["country"], qe.year)] for l in x["location_id"]]
    for cc, g in x.groupby("cost_center_id"):
        _actual[(qe, cc)] = {"headcount": len(g), "fte": float(g["fte"].sum()),
                             "loaded_local": g.groupby("currency_code")["loaded_local"].sum().to_dict()}

# fills in each quarter, by cost center and requisition type
_fill = defaultdict(lambda: {"Net-new": 0, "Backfill": 0})
_start_cc = {(w, d): cc for w, d, cc in zip(_job_df["worker_id"], _job_df["effective_start_date"], _job_df["cost_center_id"])}
for a in assign_rows:
    if a["fill_type"] == "Initial" or a["start_date"] > LAST_ME or a["start_date"] <= FIRST_ME:
        continue
    qe = next(q for q in QUARTER_ENDS if q >= a["start_date"])
    _fill[(qe, _start_cc[(a["worker_id"], a["start_date"])])][req_rows[a["requisition_id"]]["req_type"]] += 1

plan_rows = []
_cost_centers = sorted({cc for (_, cc) in _actual} | {cc for (_, cc) in _fill})
for fy in sorted({fiscal_year(q) for q in QUARTER_ENDS}):
    fy_quarters = [q for q in QUARTER_ENDS if fiscal_year(q) == fy]
    active_ccs = [cc for cc in _cost_centers if any((q, cc) in _actual or (q, cc) in _fill for q in fy_quarters)]
    for name, (vm, vd), first_q in ref.PLAN_VERSIONS:
        version_date = dt.date(fy - 1 if vm >= 5 else fy, vm, vd)
        mu_n, sd_n = ref.PLAN_NET_NEW_ERROR[name]
        mu_b, sd_b = ref.PLAN_BACKFILL_ERROR[name]
        mu_h, sd_h = ref.PLAN_HEADCOUNT_ERROR[name]
        if name == "Budget" and fy in ref.PLAN_FY_BUDGET_SHIFT:
            shift_n, shift_h = ref.PLAN_FY_BUDGET_SHIFT[fy]
            mu_n, mu_h = mu_n + shift_n, mu_h + shift_h
        for cc in active_ccs:
            z_cc = plan_rng.normal()                   # a cost center's planning bias in this version
            for q, qe in enumerate(fy_quarters, start=1):
                if q < first_q:
                    continue
                horizon = q - first_q + 1
                act = _actual.get((qe, cc), {"headcount": 0, "fte": 0.0, "loaded_local": {}})
                fills = _fill.get((qe, cc), {"Net-new": 0, "Backfill": 0})
                z_q = plan_rng.normal()
                net_new = int(plan_rng.poisson((fills["Net-new"] + 0.05) * math.exp(mu_n + sd_n * (0.7 * z_cc + 0.7 * z_q))))
                backfills = int(plan_rng.poisson((fills["Backfill"] + 0.05) * math.exp(mu_b + sd_b * (0.7 * z_cc + 0.7 * z_q))))
                hc_factor = math.exp(mu_h + sd_h * math.sqrt(horizon) * (0.7 * z_cc + 0.7 * plan_rng.normal()))
                hc = int(round(act["headcount"] * hc_factor))
                fte_per_head = act["fte"] / act["headcount"] if act["headcount"] else 1.0
                cost_usd = sum(v * fx_rates.usd_per_local(cur, version_date) for cur, v in act["loaded_local"].items())
                cost_usd *= (hc / act["headcount"] if act["headcount"] else 0.0) * math.exp(plan_rng.normal(0, ref.PLAN_COST_EXTRA_SD))
                plan_rows.append({
                    "plan_version": f"FY{fy % 100:02d} {name}", "version_type": name, "version_date": version_date,
                    "fiscal_year": fy, "fiscal_quarter": q, "quarter_end_date": qe, "cost_center_id": cc,
                    "planned_ending_headcount": hc, "planned_ending_fte": round(hc * fte_per_head, 2),
                    "planned_net_new": net_new, "planned_backfills": backfills,
                    "planned_cost_usd": round(cost_usd, 2), "plan_fx_rate_date": version_date})

# cost centers: every department x country that ever held a seat or a plan line
_cc_ids = sorted({r["cost_center_id"] for r in pos_rows} | {r["cost_center_id"] for r in plan_rows})
cost_center_rows = []
for cc in _cc_ids:
    _, code, country = cc.split("-")
    dept_id = "D-" + code[:-1]
    cost_center_rows.append({"cost_center_id": cc, "cost_center_name": f'{DEPT[dept_id]["name"]} - {COUNTRY[country]["name"]}',
                             "department_id": dept_id, "department_cost_center": f"CC-{code}", "country_code": country,
                             "function": DEPT[dept_id]["function"]})

# candidates: the applicant pipeline behind each requisition
STAGES = ["Applied", "Screen", "Interview", "Offer"]
candidate_rows = []                        # dim_candidate: one row per applicant to one requisition
candidate_event_rows = []                  # fact_candidate_stage_event: one row per stage reached


def _stage_dates(start: dt.date, end: dt.date, k: int) -> list[dt.date]:
    span = max(0, (end - start).days)
    return [start + dt.timedelta(days=int(d)) for d in sorted(recruiting_rng.integers(0, span + 1, k))]


def _candidate(req_id: str, stages: list[str], dates: list[dt.date], internal: bool, worker_id: str | None):
    cid = next_id("candidate", "C")
    source = "Internal" if internal else weighted_choice(ref.CANDIDATE_SOURCES, recruiting_rng)
    final = stages[-1] if stages[-1] in ("Accepted", "Declined", "Rejected", "Withdrawn") else "In process"
    candidate_rows.append({"candidate_id": cid, "requisition_id": req_id, "is_internal": internal,
                           "candidate_source": source, "worker_id": worker_id, "final_status": final})
    for order, (stage, day) in enumerate(zip(stages, dates), start=1):
        candidate_event_rows.append({"candidate_id": cid, "stage": stage, "stage_order": order, "stage_date": day})


_seq["candidate"] = 400000
for r in req_rows.values():
    start = r["approved_date"]
    end = r["filled_date"] or r["cancelled_date"] or LAST_ME
    if start > LAST_ME or start < FIRST_ME:        # approved before history starts: the search is not in the ATS
        if r["status"] == "Filled":
            _candidate(r["requisition_id"], ["Offer", "Accepted"], [r["filled_date"], r["filled_date"]],
                       r["fill_source"] == "Internal", r["filled_by_worker_id"])
        continue
    search = (end - start).days >= 7
    if r["status"] == "Filled":
        if search:
            _candidate(r["requisition_id"], STAGES + ["Accepted"], _stage_dates(start, end, 5),
                       r["fill_source"] == "Internal", r["filled_by_worker_id"])
        else:                                      # an immediate refill: succession or a team handed over
            _candidate(r["requisition_id"], ["Offer", "Accepted"], [start, end],
                       r["fill_source"] == "Internal", r["filled_by_worker_id"])
    if not search:
        continue
    if r["status"] == "Filled" and recruiting_rng.random() < ref.OFFER_DECLINED_SHARE:
        _candidate(r["requisition_id"], STAGES + ["Declined"], _stage_dates(start, end, 5), False, None)
    for _ in range(int(recruiting_rng.poisson(ref.CANDIDATES_PER_REQ[min(r["job_level"], 11)]))):
        exit_stage = weighted_choice(ref.CANDIDATE_EXIT_STAGE, recruiting_rng)
        reached = {"Screen": 1, "Interview": 2, "Offer": 3, "Withdrawn": int(recruiting_rng.integers(1, 3))}[exit_stage]
        outcome = "Withdrawn" if exit_stage == "Withdrawn" else "Rejected"
        stages = STAGES[:reached] + [outcome]
        dates = _stage_dates(start, end, len(stages))
        if r["status"] == "Open" and recruiting_rng.random() < 0.5:   # still in process at the last month-end
            stages, dates = stages[:-1], dates[:-1]
        _candidate(r["requisition_id"], stages, dates, False, None)


# ======================================================================================
# 6c. The hiring pipeline at the extract (release 3.1)
# ======================================================================================
# A net-new seat is created when its requisition is approved, as long before the hire as
# recruiting takes. The simulation stops on the last month-end, so the hires due after it never
# happen and, without this step, no new seat would be open on that day. Here the net-new hires of
# the next six months are drawn at FY26's pace and mix; the seats and requisitions of those
# approved by the extract are kept, still Open, with their applicants in process. Own stream:
# nothing simulated before moves.
tail_rng = domain_stream("pipeline_tail")
_fy_start = dt.date(LAST_ME.year - 1, 7, 1)
_mix = [r for r in req_rows.values() if r["req_type"] == "Net-new" and r["status"] == "Filled"
        and _fy_start <= r["filled_date"] <= LAST_ME and r["department_id"] != "D-901"]
_per_day = len(_mix) / ((LAST_ME - _fy_start).days + 1)
_mgrs = defaultdict(list)
for _w in active.values():
    if _w["is_pm"] and not _w["is_exec"]:
        _mgrs[_w["dept"]].append(_w["worker_id"])
_day = LAST_ME + ONE_DAY
while _day <= LAST_ME + dt.timedelta(days=183):
    for _ in range(int(tail_rng.poisson(_per_day))):
        r0 = _mix[int(tail_rng.integers(len(_mix)))]
        lvl = int(r0["job_level"])
        med = ref.REQ_TIME_TO_FILL_MEDIAN[min(lvl, 11)]
        ttf = int(np.clip(round(tail_rng.lognormal(math.log(med), ref.REQ_TIME_TO_FILL_SIGMA)),
                          ref.REQ_TIME_TO_FILL_MIN, 240))
        approved = _day - dt.timedelta(days=ttf)
        if approved > LAST_ME:
            continue
        share, (lo, hi) = ref.REQ_LATE_APPROVAL
        lag = int(tail_rng.integers(lo, hi + 1)) if tail_rng.random() < share else \
            int(tail_rng.integers(ref.REQ_APPROVAL_DAYS[0], ref.REQ_APPROVAL_DAYS[1] + 1))
        fam, track = r0["job_profile_id"].split("-")[0], r0["job_profile_id"].split("-")[1][0]
        s = new_seat(approved, "Net-new", r0["department_id"], fam, lvl, r0["location_id"],
                     is_pm=track == "M", fte=1.0)
        pool = _mgrs.get(r0["department_id"]) or [None]
        r = new_requisition(s, approved - dt.timedelta(days=lag), approved, pool[int(tail_rng.integers(len(pool)))])
        r["target_start_date"] = _day
        for _ in range(int(tail_rng.poisson(ref.CANDIDATES_PER_REQ[min(lvl, 11)] * 0.6))):
            reached = int(tail_rng.integers(1, 4))
            span = max(0, (LAST_ME - approved).days)
            days = sorted(int(x) for x in tail_rng.integers(0, span + 1, reached))
            cid = next_id("candidate", "C")
            candidate_rows.append({"candidate_id": cid, "requisition_id": r["requisition_id"], "is_internal": False,
                                   "candidate_source": weighted_choice(ref.CANDIDATE_SOURCES, tail_rng),
                                   "worker_id": None, "final_status": "In process"})
            for order, (stage, dd) in enumerate(zip(STAGES[:reached], days), start=1):
                candidate_event_rows.append({"candidate_id": cid, "stage": stage, "stage_order": order,
                                             "stage_date": approved + dt.timedelta(days=dd)})
    _day += ONE_DAY


# ======================================================================================
# 7. Write raw tables
# ======================================================================================
def write(df: pd.DataFrame, name: str):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT_DIR / f"{name}.csv", index=False, lineterminator="\n")
    print(f"  {name:<30} {len(df):>9,} rows")


print("Writing raw tables to", OUT_DIR)
for old in ("ref_fx_rate_monthly_synthetic",):
    (OUT_DIR / f"{old}.csv").unlink(missing_ok=True)

dim_worker = pd.DataFrame([{
    "worker_id": w["worker_id"], "first_name": w["first_name"], "last_name": w["last_name"],
    "original_hire_date": w["hire_date"], "termination_date": w["termination_date"],
    "termination_type": w["termination_type"], "worker_type": "Regular Employee",
    "is_executive_officer": w["is_exec"],
} for w in workers.values()]).sort_values("worker_id")
# Release 3: the work email (first.last@, numbered on a clash, in worker ID order). Bridgeway names
# a contingent worker's manager by email, so the warehouse needs it to compare managers.
dim_worker["work_email"] = contingent_workforce.employee_emails(dim_worker)
write(dim_worker, "dim_worker")

job = pd.DataFrame(job_rows)
_bad = job[job["effective_end_date"].notna() & (job["effective_end_date"] < job["effective_start_date"])]
if len(_bad):
    raise RuntimeError(f"{len(_bad)} job records end before they start")
job = job.sort_values(["worker_id", "effective_start_date"]).reset_index(drop=True)
job.insert(0, "job_record_id", [f"JR{n:07d}" for n in range(1, len(job) + 1)])
job = job[["job_record_id", "worker_id", "effective_start_date", "effective_end_date", "action_reason", "position_id",
           "department_id", "location_id", "job_profile_id", "job_level", "fte", "manager_worker_id",
           "is_people_manager", "leads_org_unit_id"]]
write(job, "fact_job_history")

# seats: dim_position and fact_position_assignment are written in section 8, after the
# contingent PIDs join them (release 3.1)
write(pd.DataFrame(req_rows.values())[[
    "requisition_id", "position_id", "req_type", "opened_date", "approved_date", "target_start_date", "filled_date",
    "cancelled_date", "status", "department_id", "cost_center_id", "location_id", "job_profile_id", "job_level",
    "hiring_manager_id",
    "filled_by_worker_id", "fill_source"]].sort_values("requisition_id"), "fact_requisition")
write(pd.DataFrame(cost_center_rows), "dim_cost_center")
# fact_workforce_plan and dim_candidate are written in section 8: the plan gains its
# contingent line and some hires turn out to be contingent conversions.
cand = pd.DataFrame(candidate_event_rows).sort_values(["candidate_id", "stage_order"]).reset_index(drop=True)
cand.insert(0, "candidate_event_id", [f"CE{n:07d}" for n in range(1, len(cand) + 1)])
write(cand, "fact_candidate_stage_event")

comp = pd.DataFrame(comp_rows)
comp["_order"] = (comp["transaction_type"] == "Correction").astype(int)
comp = comp.sort_values(["worker_id", "effective_start_date", "_order"]).drop(columns="_order").reset_index(drop=True)
comp.insert(0, "comp_record_id", [f"CR{n:07d}" for n in range(1, len(comp) + 1)])
comp = comp[["comp_record_id", "worker_id", "effective_start_date", "effective_end_date", "action_reason",
             "transaction_type", "currency_code", "base_salary_annual_local"]]
write(comp, "fact_compensation_history")

rev = pd.DataFrame(review_rows).sort_values(["fiscal_year", "worker_id"]).reset_index(drop=True)
rev.insert(0, "review_id", [f"PR{n:07d}" for n in range(1, len(rev) + 1)])
write(rev, "fact_performance_review")

bon = pd.DataFrame(bonus_rows).sort_values(["fiscal_year", "worker_id"]).reset_index(drop=True)
bon.insert(0, "bonus_id", [f"BP{n:07d}" for n in range(1, len(bon) + 1)])
write(bon, "fact_bonus_payout")

# organization
SUB_ORG = {sf: v[0] for sf, v in ref.SUB_FUNCTIONS.items()}
write(pd.DataFrame([{
    "department_id": d["id"], "department_name": d["name"], "sub_function": d["sub_function"],
    "function": d["function"],
    "parent_org_unit_id": SUB_ORG.get(d["sub_function"], ref.FUNCTIONS.get(d["function"], (ref.CEO[0],))[0]),
    "cost_center": "CC-" + d["id"][2:] + "0", "head_job_level": HEAD_LEVEL[d["id"]] if d["id"] != "D-901" else 12,
    "effective_from_date": REORG_DATE if d["id"] == "D-108" else dt.date(2012, 1, 1),
} for d in DEPT.values()]), "dim_department")

org_units = [{"org_unit_id": ref.CEO[0], "org_unit_name": ref.CEO[1], "org_unit_type": "Company",
              "parent_org_unit_id": None, "function": None, "leader_title": ref.CEO[2], "leader_job_level": 12}]
for fn, (org, title, lvl) in ref.FUNCTIONS.items():
    org_units.append({"org_unit_id": org, "org_unit_name": fn, "org_unit_type": "Function",
                      "parent_org_unit_id": ref.CEO[0], "function": fn, "leader_title": title, "leader_job_level": lvl})
for sf, (org, fn, title, lvl, _) in ref.SUB_FUNCTIONS.items():
    org_units.append({"org_unit_id": org, "org_unit_name": sf, "org_unit_type": "Sub-function",
                      "parent_org_unit_id": ref.FUNCTIONS[fn][0], "function": fn, "leader_title": title,
                      "leader_job_level": lvl})
for d in DEPT.values():
    if d["id"] == "D-901":
        continue
    org_units.append({"org_unit_id": d["id"], "org_unit_name": d["name"], "org_unit_type": "Department",
                      "parent_org_unit_id": SUB_ORG.get(d["sub_function"], ref.FUNCTIONS[d["function"]][0]),
                      "function": d["function"], "leader_title": "Head of " + d["name"],
                      "leader_job_level": HEAD_LEVEL[d["id"]]})
write(pd.DataFrame(org_units), "dim_org_unit")

write(pd.DataFrame([{
    "location_id": o["id"], "office_name": o["name"], "site_type": o["site_type"],
    "street_address": o["street"], "city": o["city"], "state_province": o["state"], "postal_code": o["postal"],
    "country_code": o["country"], "country_name": COUNTRY[o["country"]]["name"],
    "region": COUNTRY[o["country"]]["region"], "currency_code": COUNTRY[o["country"]]["currency"],
    "latitude": o["lat"], "longitude": o["lon"],
    "geo_source": ref.GEO_SOURCE.get(o["id"], ref.GEO_SOURCE_DEFAULT),
    "pay_zone_factor": o["pay_zone"], "opened_date": o["opened"],
} for o in OFFICE.values()]).sort_values("location_id"), "dim_location")

write(pd.DataFrame([{
    "country_code": cc, "country_name": c["name"], "region": c["region"], "currency_code": c["currency"],
    "pay_index": c["pay_index"],
} for cc, c in COUNTRY.items()]).sort_values("country_code"), "dim_country")

write(pd.DataFrame([{
    "job_level": lvl, "level_code": code, "level_name": name, "career_track": track,
    "us_base_salary_usd": us_base, "range_min_pct": ref.RANGE_MIN_PCT, "range_max_pct": ref.RANGE_MAX_PCT,
} for lvl, (code, name, track, us_base) in ref.JOB_LEVELS.items()]), "dim_job_level")

TITLES_IC = {1: "Associate {s}", 2: "{s}", 3: "Senior {s}", 4: "Lead {s}", 5: "Staff {s}", 6: "Principal {s}"}
TITLES_LEAD = {5: "Manager, {f}", 6: "Senior Manager, {f}", 7: "Director, {f}", 8: "Senior Director, {f}",
               9: "Vice President, {f}", 10: "Senior Vice President, {f}"}
profiles = []
for code, (family, stem) in ref.JOB_FAMILIES.items():
    if code == "EXE":
        continue
    for lvl in range(1, 11):
        if lvl <= 6:
            profiles.append({"job_profile_id": f"{code}-L{lvl}", "job_family_code": code, "job_family": family,
                             "job_title": TITLES_IC[lvl].format(s=stem), "job_level": lvl,
                             "level_name": ref.JOB_LEVELS[lvl][1], "career_track": "Individual Contributor"})
        if lvl in (5, 6):
            profiles.append({"job_profile_id": f"{code}-M{lvl}", "job_family_code": code, "job_family": family,
                             "job_title": TITLES_LEAD[lvl].format(f=family), "job_level": lvl,
                             "level_name": ref.JOB_LEVELS[lvl][1], "career_track": "People Manager"})
        if lvl >= 7:
            profiles.append({"job_profile_id": f"{code}-L{lvl}", "job_family_code": code, "job_family": family,
                             "job_title": TITLES_LEAD[lvl].format(f=family), "job_level": lvl,
                             "level_name": ref.JOB_LEVELS[lvl][1], "career_track": "People Leader"})
exec_rows = [("EXE-CEO", "Chief Executive Officer", 12)] + [
    (EXEC_TITLES[fn][0], EXEC_TITLES[fn][1], lvl) for fn, (_, _, lvl) in ref.FUNCTIONS.items()]
for pid, title, lvl in exec_rows:
    profiles.append({"job_profile_id": pid, "job_family_code": "EXE", "job_family": "Executive Leadership",
                     "job_title": title, "job_level": lvl, "level_name": ref.JOB_LEVELS[lvl][1],
                     "career_track": "Executive"})
write(pd.DataFrame(profiles), "dim_job_profile")

write(pd.DataFrame([{
    "job_level": lvl, "country_code": cc, "currency_code": COUNTRY[cc]["currency"],
    "base_salary_local": LEVEL_BASE[(lvl, cc)],
    "base_salary_usd_at_reference": round(LEVEL_BASE[(lvl, cc)] * fx_rates.usd_per_local(COUNTRY[cc]["currency"], LEVEL_FX_DATE), 2),
    "fx_reference_date": LEVEL_FX_DATE,
} for (lvl, cc) in sorted(LEVEL_BASE)]), "ref_job_level_base_salary")

write(pd.DataFrame([{"tenure_year_from": lo, "tenure_year_to": hi, "increase_pct": pct}
                    for lo, hi, pct in ref.TENURE_INCREASE]), "ref_tenure_increase")

write(pd.DataFrame([{"rating": r, "bonus_pct": pct, "target_share": share}
                    for r, (pct, share) in ref.PERFORMANCE_RATINGS.items()]), "ref_performance_bonus")

write(pd.DataFrame([{
    "fiscal_year": fy, "job_level": lvl, "country_code": cc, "currency_code": COUNTRY[cc]["currency"],
    "range_min": round_salary(RANGE_MID[(fy, lvl, cc)] * ref.RANGE_MIN_PCT), "range_mid": RANGE_MID[(fy, lvl, cc)],
    "range_max": round_salary(RANGE_MID[(fy, lvl, cc)] * ref.RANGE_MAX_PCT),
    "structure_increase_pct": round(structure_increase(fy, cc), 4) if fy > RANGE_FISCAL_YEARS[0] else None,
} for fy in RANGE_FISCAL_YEARS for (lvl, cc) in sorted(LEVEL_BASE)]), "ref_salary_range")

# FX: every ECB day, the month-end rates the snapshot uses, and the constant rate set
write(pd.DataFrame(list(fx_rates.daily_rows())).sort_values(["currency_code", "rate_date"]), "ref_fx_rate_daily")
write(pd.DataFrame([{"currency_code": cur, "rate_date": me, "usd_per_local": fx_rates.usd_per_local(cur, me)}
                    for cur in sorted(fx_rates.SERIES) for me in MONTH_ENDS]), "ref_fx_rate_monthly")
CONST_DATE = dt.date.fromisoformat(ref.FX_CONSTANT_RATE_DATE)
write(pd.DataFrame([{"rate_set": ref.FX_CONSTANT_RATE_SET, "rate_date": CONST_DATE, "currency_code": cur,
                     "usd_per_local": fx_rates.usd_per_local(cur, CONST_DATE)}
                    for cur in sorted(fx_rates.SERIES)]), "ref_fx_rate_constant")

fringe, fringe_cites = fringe_research.build()
write(pd.DataFrame(fringe), "ref_fringe_rate")
write(pd.DataFrame(fringe_cites).drop_duplicates(), "ref_fringe_source")

# Release 3: where every raw table comes from (Keystone HR, Bridgeway VMS, the integration
# log, public reference data) and the column contract of every table release 3 adds.
write(pd.DataFrame(source_systems.SOURCE_SYSTEMS), "ref_source_system")
write(pd.DataFrame(source_systems.lineage_rows()), "ref_raw_table_lineage")
write(pd.DataFrame(source_systems.column_rows()), "ref_raw_column")

# ======================================================================================
# 8. Contingent workforce (release 3): Bridgeway VMS, Keystone HR and the feed between them
# ======================================================================================
# Each on its own random stream, run after the employee simulation, so no employee draw moves.
# First the clean Bridgeway program; then Keystone's view of it through the one-way feed,
# with the seeded discrepancies and their answer key (which also seeds Bridgeway's own
# hygiene problems, so the Bridgeway tables are written from its output).
#
# Conversions (phase 5): external hires into requisitions are the pool a contingent worker can
# be hired from when their engagement ends. The hire stays exactly as simulated; the
# contingent worker turns out to be that person, and the applicant's source says so.
_accepted = {(c["requisition_id"], c["worker_id"]): c["candidate_id"] for c in candidate_rows
             if c["final_status"] == "Accepted" and not c["is_internal"]}
external_hires = pd.DataFrame([{
    "worker_id": r["filled_by_worker_id"], "hire_date": r["filled_date"], "candidate_id": cid,
    "country": r["cost_center_id"].rsplit("-", 1)[1], "department_id": r["department_id"],
    "function": DEPT[r["department_id"]]["function"],
    "first_name": workers[r["filled_by_worker_id"]]["first_name"],
    "last_name": workers[r["filled_by_worker_id"]]["last_name"]}
    for r in req_rows.values()
    if r["status"] == "Filled" and r["fill_source"] == "External"
    and (cid := _accepted.get((r["requisition_id"], r["filled_by_worker_id"])))
    and workers[r["filled_by_worker_id"]]["hire_date"] == r["filled_date"]])
cw_tables, cw_program = contingent_workforce.simulate(
    stream=domain_stream("contingent"), office=OFFICE, dept=DEPT, country=COUNTRY, job=job, workers=dim_worker,
    cost_centers=cost_center_rows, reorg_date=REORG_DATE, restructure_date=RESTRUCTURE_DATE,
    hires=external_hires, conversion_stream=domain_stream("conversions"))
cw_tables, keystone = keystone_feed.simulate(
    stream=domain_stream("keystone"), bw=cw_tables, program=cw_program, cost_centers=cost_center_rows)
for _table in source_systems.RELEASE_3_TABLES:
    write(cw_tables[_table][source_systems.columns(_table)], _table)
write(cw_tables["ref_cw_discrepancy_type"], "ref_cw_discrepancy_type")

_converted = {c["candidate_id"] for c in cw_program.conversions.values()}
for c in candidate_rows:
    if c["candidate_id"] in _converted:
        c["candidate_source"] = "Contingent conversion"
write(pd.DataFrame(candidate_rows).sort_values("candidate_id"), "dim_candidate")

# PIDs (release 3.1). Every contingent worker holds a PID in Keystone like an employee does: the
# PID is created (or a vacant one reused) when the request is approved, filled for the days
# Bridgeway holds the assignment, and left vacant afterwards until reused or closed by the
# position audit. Own stream; employee PIDs keep their rows and IDs (P200001 up), contingent
# PIDs are P800001 up.
cw_pos_rows, cw_assign_rows = cw_positions.build(
    stream=domain_stream("cw_positions"), tables=cw_tables, program=cw_program, cost_centers=cost_center_rows,
    start_number=ref.CW_PID_START_NUMBER)
for _r in pos_rows:
    _r.update(worker_type="Employee", cw_type=None, cw_role_family=None)
for _r in assign_rows:
    _r.update(worker_type="Employee", bw_worker_id=None)
pos = pd.DataFrame(pos_rows + cw_pos_rows).sort_values(["position_id", "effective_start_date"]).reset_index(drop=True)
pos.insert(0, "position_record_id", [f"PS{n:07d}" for n in range(1, len(pos) + 1)])
pos["job_level"] = pos["job_level"].astype("Int64")          # contingent PIDs have no grade
write(pos[["position_record_id", "position_id", "effective_start_date", "effective_end_date", "change_reason", "status",
           "department_id", "cost_center_id", "location_id", "job_profile_id", "job_level", "fte", "created_date",
           "created_reason", "worker_type", "cw_type", "cw_role_family"]],
      "dim_position")
write(pd.DataFrame(assign_rows + cw_assign_rows)[[
    "assignment_id", "position_id", "worker_id", "start_date", "end_date", "fill_type", "requisition_id",
    "vacate_reason", "worker_type", "bw_worker_id"]].sort_values("assignment_id"), "fact_position_assignment")

# ======================================================================================
# 9. Reconciliation operations (release 4, case study 6): times, job data, load log, tickets
# ======================================================================================
# New tables only, each from its own stream: the hour every feed change was sent and applied,
# when every Keystone contingent version was written, Keystone's job data (the PID each
# contingent job record holds, with two seeded imperfections and their answer key), the
# warehouse's load log, and the Helix Service Desk tickets raised to fix the gaps.
_delivery = cw_operations.feed_delivery(domain_stream("feed_times"), cw_tables["feed_bridgeway_keystone_event"])
_region = {o["id"]: COUNTRY[o["country"]]["region"] for o in OFFICE.values()}
_audit = cw_operations.ks_audit(domain_stream("keystone_times"), cw_tables["ks_contingent_worker"], _delivery, _region)
_job, _job_defect = cw_operations.job_data(domain_stream("ks_job"), cw_assign_rows)


def _counter(dates):
    """Rows dated on or before a day (or time): what a full extract taken then holds."""
    _s = sorted(pd.to_datetime(pd.Series(dates).replace("", None), errors="coerce").dropna())
    return lambda t: bisect.bisect_right(_s, pd.Timestamp(t))


_rows_bw = _counter(cw_tables["bw_service_order_revision"]["effective_start_date"])
_rows_ks = _counter(list(cw_tables["ks_contingent_worker"]["effective_start_date"]) + list(_job["effective_start_date"]))
_runs = cw_operations.load_log(domain_stream("load_log"), {"BW": _rows_bw, "KS": _rows_ks, "HLX": lambda t: 0})
_helix = helix_service_desk.simulate(
    stream=domain_stream("helix"), tables=cw_tables, job_defects=_job_defect, load_runs=_runs,
    conversions=cw_program.conversions, cc_function={c["cost_center_id"]: DEPT[c["department_id"]]["function"] for c in cost_center_rows})
_ev = _counter(_helix["itsm_ticket_event"]["event_at"])
_ok = _runs["source_system"].eq("HLX") & _runs["status"].ne("Failed")
_runs.loc[_ok, "rows_read"] = [_ev(t) for t in _runs.loc[_ok, "started_at"]]
_new = {"feed_event_delivery": _delivery, "ks_contingent_worker_audit": _audit, "ks_cw_job": _job,
        "gen_cw_job_defect": _job_defect, "etl_load_run": _runs, **_helix}
for _table in source_systems.RELEASE_4_TABLES:
    write(_new[_table][source_systems.columns(_table)], _table)

# The plan's contingent line, from its own stream so no employee plan number moves.
_plan = pd.DataFrame(plan_rows).sort_values(["fiscal_year", "version_date", "cost_center_id", "fiscal_quarter"])
write(contingent_workforce.plan_line(_plan, cw_tables, domain_stream("plan_cw")), "fact_workforce_plan")

print(f"Active headcount at {LAST_ME}: {len(active):,}  |  workers ever employed: {len(workers):,}  |  "
      f"people managers: {sum(1 for w in active.values() if w['is_pm']):,}")
