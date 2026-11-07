"""
Time off for Arcadia Systems (release 7, case study 7: Who Leads Where).

Who is at work on a day is the people in an organization minus anyone off: on approved
time off, on a leave of absence, or on a public holiday. Release 7 adds the absence data a
real HR system keeps, for FY26 and the approved requests already booked for the 60 days
after the report date:

  * Keystone time off (`ks_time_off_request`): employees request time off in Keystone,
    with the plan and the units of their country (US and Canada book hours, everyone else
    days), half days, sick days booked on the day, and corrections that take days back.
  * Keystone leave of absence (`ks_leave_of_absence`): parental, medical, family care and
    personal leaves, with an estimated return and, once they are back, the actual one.
  * Bridgeway time off (`bw_time_off`): contingent workers book time off in the vendor
    system. Bridgeway sends every approved booking to Keystone, which stores it beside
    employee time off (`source_system` = BW). A worker Keystone holds no profile for
    cannot receive it: the booking stays in Bridgeway only.
  * Public holidays (`ref_public_holiday`): national holidays for the 22 countries, from the
    open-source python-holidays package.

A request is known only once it is made: nothing is created after the data-through date,
so the further a day lies past the report date, the fewer requests it has, as in a real
extract. Everything draws from its own random stream after the existing simulation.

Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.

    python generator/time_off.py --out /tmp/r7
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd

ONE_DAY = dt.timedelta(days=1)
FORWARD_DAYS = 60                       # approved requests already booked past the report date

# Annual time off (days) by country, and the share of it people take
ALLOWANCE = {"US": 18, "CA": 17, "MX": 14, "BR": 26, "GB": 25, "IE": 22, "DE": 28, "CH": 25, "ES": 25, "PT": 23,
             "FR": 27, "NL": 25, "SE": 27, "PL": 24, "AE": 25, "ZA": 18, "IN": 20, "AU": 20, "JP": 15, "KR": 15,
             "SG": 16, "PH": 15}
HOURS_COUNTRIES = {"US", "CA"}          # these plans book hours (8 a day)
USE_SHARE = (0.70, 1.00)
SICK_PER_YEAR = 3.5
CW_DAYS_PER_YEAR = 9                   # contingent workers book unpaid time off in Bridgeway
CW_SICK_PER_YEAR = 2.0
HALF_DAY_SHARE = 0.10                   # of single-day requests
CORRECTION_SHARE = 0.04                 # of requests, later reduced or withdrawn
LEAVE_STARTS_PER_YEAR = 0.035           # employees starting a leave of absence per year

# Month weights by region, July to June (index 0 = July)
SEASON = {
    "North America":        [1.6, 1.4, 0.8, 0.8, 1.1, 1.8, 0.7, 0.7, 1.0, 0.9, 1.0, 1.3],
    "Europe":               [2.0, 2.4, 0.8, 0.9, 0.7, 1.5, 0.6, 0.8, 0.8, 1.1, 1.1, 1.2],
    "Latin America":        [1.4, 0.8, 0.8, 0.8, 0.8, 1.6, 2.0, 1.3, 0.8, 0.8, 0.8, 0.9],
    "Asia Pacific":         [0.9, 0.9, 0.9, 1.2, 1.1, 1.4, 1.2, 0.9, 0.9, 1.0, 1.2, 0.9],
    "Middle East & Africa": [1.5, 1.5, 0.9, 0.9, 0.9, 1.4, 0.9, 0.9, 0.9, 1.0, 0.9, 1.0],
}
BRIDGE_WEIGHT = 3.0                     # a working day next to a public holiday is popular

LEAVE_TYPES = [   # (type, share, weeks low, weeks high)
    ("Parental Leave", 0.50, 6, 26), ("Medical Leave", 0.25, 2, 12),
    ("Family Care Leave", 0.12, 1, 6), ("Personal Leave (unpaid)", 0.10, 1, 8), ("Military Leave", 0.03, 2, 10),
]


def _d(x):
    if x is None or (isinstance(x, float) and np.isnan(x)) or pd.isna(x) or x == "":
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _s(d):
    return d.isoformat() if d else None


# ======================================================================================
# Public holidays
# ======================================================================================
def public_holidays(countries, first: dt.date, last: dt.date) -> pd.DataFrame:
    import holidays
    rows = []
    for cc in sorted(countries):
        try:
            h = holidays.country_holidays(cc, years=range(first.year, last.year + 1), language="en_US")
        except Exception:
            h = holidays.country_holidays(cc, years=range(first.year, last.year + 1))
        for day, name in sorted(h.items()):
            if first <= day <= last:
                rows.append({"country_code": cc, "holiday_date": _s(day), "holiday_name": name,
                             "source": f"python-holidays {holidays.__version__}, national holidays"})
    return pd.DataFrame(rows)


# ======================================================================================
# Booking days
# ======================================================================================
class _Calendar:
    def __init__(self, hol: pd.DataFrame, first: dt.date, last: dt.date, office_region: dict):
        self.first, self.last = first, last
        self.days = [first + dt.timedelta(days=i) for i in range((last - first).days + 1)]
        self.hol = defaultdict(set)
        for c, d in zip(hol["country_code"], hol["holiday_date"]):
            self.hol[c].add(dt.date.fromisoformat(d))

    def working(self, cc: str, d: dt.date) -> bool:
        return d.weekday() < 5 and d not in self.hol[cc]

    def weight(self, cc: str, region: str, d: dt.date) -> float:
        if not self.working(cc, d):
            return 0.0
        w = SEASON[region][(d.month - 7) % 12]
        if (d + ONE_DAY) in self.hol[cc] or (d - ONE_DAY) in self.hol[cc] \
                or (d.weekday() == 4 and (d + dt.timedelta(days=3)) in self.hol[cc]) \
                or (d.weekday() == 0 and (d - dt.timedelta(days=3)) in self.hol[cc]):
            w *= BRIDGE_WEIGHT
        return w


def _block_len(rng) -> int:
    u = rng.random()
    if u < 0.42:
        return 1
    if u < 0.82:
        return int(rng.integers(2, 6))
    return int(rng.integers(6, 16))


def _book(rng, cal: _Calendar, cc: str, region: str, start: dt.date, end: dt.date, target_days: float,
          taken: set) -> list[tuple[dt.date, dt.date, list[dt.date]]]:
    """Blocks of working days between start and end, weighted by season, not overlapping `taken`."""
    span = [d for d in cal.days if start <= d <= end]
    if not span:
        return []
    w = np.array([cal.weight(cc, region, d) for d in span])
    if w.sum() == 0:
        return []
    p = w / w.sum()
    out, used, tries = [], 0.0, 0
    while used < target_days and tries < 60:
        tries += 1
        k = _block_len(rng)
        i = int(rng.choice(len(span), p=p))
        days = []
        j = i
        while len(days) < k and j < len(span):
            d = span[j]
            if d in taken:
                break
            if cal.working(cc, d):
                days.append(d)
            j += 1
        if not days:
            continue
        taken.update(days)
        out.append((days[0], days[-1], days))
        used += len(days)
    return out


# ======================================================================================
# Build
# ======================================================================================
def build(stream, workers: pd.DataFrame, job: pd.DataFrame, offices: pd.DataFrame, countries: pd.DataFrame,
          bw_worker: pd.DataFrame, bw_revision: pd.DataFrame, ks_cw: pd.DataFrame,
          report_date: dt.date, data_through: dt.date) -> dict[str, pd.DataFrame]:
    first = dt.date(report_date.year if report_date.month >= 7 else report_date.year - 1, 7, 1)  # start of the fiscal year
    last = report_date + dt.timedelta(days=FORWARD_DAYS)
    office_country = dict(zip(offices["location_id"], offices["country_code"]))
    office_region = dict(zip(offices["location_id"], offices["region"]))
    country_name = dict(zip(countries["country_code"], countries["country_name"]))
    country_region = dict(zip(countries["country_code"], countries["region"]))
    hol = public_holidays(set(office_country.values()), first, last)
    cal = _Calendar(hol, first, last, office_region)
    known = dt.datetime.combine(data_through, dt.time(23, 59))
    s_emp, s_leave, s_cw = (np.random.default_rng(stream.integers(2**63)) for _ in range(3))

    def stamp(rng, day: dt.date, lead_lo: int, lead_hi: int) -> tuple[dt.datetime, dt.datetime]:
        created = dt.datetime.combine(day - dt.timedelta(days=int(rng.integers(lead_lo, lead_hi + 1))), dt.time(8)) \
            + dt.timedelta(minutes=int(rng.integers(0, 10 * 60)))
        approved = created + dt.timedelta(minutes=int(rng.integers(5, 3 * 24 * 60)))
        return created, approved

    def plan_type(cc: str, kind: str) -> str:
        name = country_name.get(cc, cc)
        if kind == "annual":
            return "United States · Paid Time Off (PTO)" if cc == "US" else f"{name} · Annual Leave"
        if kind == "sick":
            return f"{name} · Sick Leave"
        return f"{name} · Personal & Family Care"

    # ---------------------------------------------------------------- employees
    term = {w: _d(t) for w, t in zip(workers["worker_id"], workers["termination_date"])}
    execs = set(workers.loc[workers["is_executive_officer"].astype(str) == "True", "worker_id"])
    jh = job.copy()
    jh["s"] = pd.to_datetime(jh["effective_start_date"]).dt.date
    jh["e"] = pd.to_datetime(jh["effective_end_date"]).dt.date.where(jh["effective_end_date"].notna(), last)
    jh = jh[(jh["e"] >= first) & (jh["s"] <= last)]
    segs = defaultdict(list)    # worker -> [(start, end, country)]
    for r in jh.sort_values(["worker_id", "s"]).itertuples(index=False):
        s, e = max(r.s, first), min(r.e, last)
        t = term.get(r.worker_id)
        if t is not None:
            e = min(e, t)
        if e < s:
            continue
        c = office_country[r.location_id]
        if segs[r.worker_id] and segs[r.worker_id][-1][2] == c and segs[r.worker_id][-1][1] + ONE_DAY >= s:
            segs[r.worker_id][-1] = (segs[r.worker_id][-1][0], max(segs[r.worker_id][-1][1], e), c)
        else:
            segs[r.worker_id].append((s, e, c))

    req, leaves = [], []
    n_req = n_leave = 0
    leave_days = defaultdict(set)

    # leaves first, so time off never falls inside a leave
    for wid in sorted(segs):
        if wid in execs:
            continue
        s0, e0, cc = segs[wid][0][0], segs[wid][-1][1], segs[wid][0][2]
        years = ((e0 - s0).days + 200) / 365.0
        if s_leave.random() >= LEAVE_STARTS_PER_YEAR * years:
            continue
        lo_day = max(s0 - dt.timedelta(days=200), first - dt.timedelta(days=200))
        start = lo_day + dt.timedelta(days=int(s_leave.integers(0, max(1, (e0 - lo_day).days))))
        start = max(start, s0 if s0 > first else start)
        if start > e0 or start.weekday() >= 5:
            start = start + dt.timedelta(days=(7 - start.weekday()) % 7)
        if start > e0:
            continue
        u, acc = s_leave.random(), 0.0
        for ltype, share, wlo, whi in LEAVE_TYPES:
            acc += share
            if u < acc:
                break
        weeks = int(s_leave.integers(wlo, whi + 1))
        if ltype == "Parental Leave" and cc in {"SE", "DE", "PL", "CA"}:
            weeks = int(weeks * 1.6)
        est_last = start + dt.timedelta(weeks=weeks) - ONE_DAY
        drift = int(s_leave.choice([0, 0, 0, 0, 7, 14, -7, 21]))
        act_last = max(est_last + dt.timedelta(days=drift), start)
        initiated = start - dt.timedelta(days=int(s_leave.integers(3, 90 if ltype == "Parental Leave" else 20)))
        if initiated > data_through:
            continue
        t = term.get(wid)
        if t is not None and t < start:
            continue
        back_known = act_last < data_through and (t is None or t > act_last)
        if t is not None and t < act_last:
            act_last, back_known = t, True
        n_leave += 1
        last_known = act_last if back_known else None
        leaves.append({
            "leave_id": f"LOA{n_leave:06d}", "worker_id": wid, "leave_type": ltype, "status": "Approved",
            "initiated_date": _s(initiated), "approved_date": _s(initiated + dt.timedelta(days=int(s_leave.integers(0, 6)))),
            "last_day_of_work": _s(start - ONE_DAY), "first_day_of_leave": _s(start),
            "estimated_last_day_of_leave": _s(est_last), "actual_last_day_of_leave": _s(last_known),
            "first_day_back_at_work": _s(last_known + ONE_DAY) if last_known and (t is None or t > last_known) else None,
            "total_days_on_leave": ((last_known or est_last) - start).days + 1,
            "is_estimated": last_known is None})
        d = start
        while d <= (last_known or est_last):
            leave_days[wid].add(d)
            d += ONE_DAY

    for wid in sorted(segs):
        if wid in execs:
            continue
        taken = set(leave_days.get(wid, set()))
        u_share = float(s_emp.uniform(*USE_SHARE))
        for s, e, cc in segs[wid]:
            region = country_region[cc]
            frac = ((e - s).days + 1) / 365.0
            hours = cc in HOURS_COUNTRIES
            # planned time off
            for b0, b1, days in _book(s_emp, cal, cc, region, s, e, ALLOWANCE[cc] * u_share * frac, taken):
                lead = (1, 30) if len(days) <= 2 else (14, 120)
                created, approved = stamp(s_emp, b0, *lead)
                if created > known:
                    for x in days:
                        taken.discard(x)
                    continue
                units = float(len(days))
                if len(days) == 1 and s_emp.random() < HALF_DAY_SHARE:
                    units = 0.5
                kind = "annual" if s_emp.random() > 0.06 else "personal"
                n_req += 1
                rid = f"TO{n_req:07d}"
                req.append({"time_off_request_id": rid, "person_id": wid, "person_type": "Employee",
                            "source_system": "KS", "bw_booking_id": None, "time_off_type": plan_type(cc, kind),
                            "request_type": "Absence Request", "first_day": _s(b0), "last_day": _s(b1),
                            "units": units * (8 if hours else 1), "unit_of_time": "Hours" if hours else "Days",
                            "days_requested": units, "corrects_request_id": None, "status": "Approved",
                            "created_at": created.isoformat(sep=" "), "approved_at": min(approved, known).isoformat(sep=" ")})
                # a later correction that takes days back
                if s_emp.random() < CORRECTION_SHARE and len(days) >= 2:
                    k = int(s_emp.integers(1, len(days)))
                    back = days[-k:]
                    c_at = created + dt.timedelta(days=int(s_emp.integers(1, max(2, (b0 - created.date()).days + 1))))
                    if c_at <= known:
                        for x in back:
                            taken.discard(x)
                        n_req += 1
                        req.append({"time_off_request_id": f"TO{n_req:07d}", "person_id": wid, "person_type": "Employee",
                                    "source_system": "KS", "bw_booking_id": None, "time_off_type": plan_type(cc, kind),
                                    "request_type": "Absence Correction", "first_day": _s(back[0]), "last_day": _s(back[-1]),
                                    "units": -float(len(back)) * (8 if hours else 1), "unit_of_time": "Hours" if hours else "Days",
                                    "days_requested": -float(len(back)), "corrects_request_id": rid, "status": "Approved",
                                    "created_at": c_at.isoformat(sep=" "), "approved_at": c_at.isoformat(sep=" ")})
            # sick days, booked on the day (only days already lived)
            sick_end = min(e, data_through)
            if sick_end >= s:
                n_sick = s_emp.poisson(SICK_PER_YEAR * ((sick_end - s).days + 1) / 365.0)
                span = [d for d in cal.days if s <= d <= sick_end and cal.working(cc, d) and d not in taken]
                for _ in range(n_sick):
                    if not span:
                        break
                    d0 = span[int(s_emp.integers(len(span)))]
                    days = [d0]
                    nxt = d0 + ONE_DAY
                    if s_emp.random() < 0.3 and nxt <= sick_end and cal.working(cc, nxt) and nxt not in taken:
                        days.append(nxt)
                    if any(x in taken for x in days):
                        continue
                    taken.update(days)
                    created = dt.datetime.combine(d0, dt.time(7)) + dt.timedelta(minutes=int(s_emp.integers(0, 36 * 60)))
                    created = min(created, known)
                    n_req += 1
                    req.append({"time_off_request_id": f"TO{n_req:07d}", "person_id": wid, "person_type": "Employee",
                                "source_system": "KS", "bw_booking_id": None, "time_off_type": plan_type(cc, "sick"),
                                "request_type": "Absence Request", "first_day": _s(days[0]), "last_day": _s(days[-1]),
                                "units": float(len(days)) * (8 if hours else 1), "unit_of_time": "Hours" if hours else "Days",
                                "days_requested": float(len(days)), "corrects_request_id": None, "status": "Approved",
                                "created_at": created.isoformat(sep=" "), "approved_at": created.isoformat(sep=" ")})

    # ---------------------------------------------------------------- contingent workers (Bridgeway)
    rev = bw_revision[bw_revision["is_current"].astype(str) == "True"].copy()
    rev = rev[rev["status"].isin(["Approved", "Closed"])]
    rev["s"] = pd.to_datetime(rev["assignment_start_date"]).dt.date
    rev["e"] = pd.to_datetime(rev["assignment_end_date"]).dt.date
    rev["c"] = pd.to_datetime(rev["closed_date"]).dt.date
    ks_person = (ks_cw.dropna(subset=["bw_worker_id"]).sort_values("effective_start_date")
                 .drop_duplicates("bw_worker_id", keep="last").set_index("bw_worker_id")["person_id"].to_dict())
    return_tables = {"hol": hol, "req": req, "leaves": leaves, "cal": cal, "rev": rev, "ks_person": ks_person,
                     "known": known, "first": first, "last": last, "s_cw": s_cw, "office_country": office_country,
                     "office_region": office_region, "plan_type": plan_type, "stamp": stamp}
    return return_tables


def build_cw(state: dict, bw_order: pd.DataFrame, data_through: dt.date) -> tuple[list, list]:
    """Contingent bookings in Bridgeway, and the copy the feed delivers to Keystone."""
    cal, rev, s_cw, known = state["cal"], state["rev"], state["s_cw"], state["known"]
    first, last = state["first"], state["last"]
    office_country, office_region = state["office_country"], state["office_region"]
    worker_of = dict(zip(bw_order["service_order_id"], bw_order["bw_worker_id"]))
    rev = rev.assign(bw_worker_id=rev["service_order_id"].map(worker_of))
    bookings, ks_rows = [], []
    n_bk = 0
    taken = defaultdict(set)
    for r in rev.sort_values(["bw_worker_id", "s"]).itertuples(index=False):
        s = max(r.s, first)
        e = min(r.e if r.e is not None and not pd.isna(r.e) else last, last)
        if r.c is not None and not pd.isna(r.c):
            e = min(e, r.c)
        if e < s or r.office_code not in office_country:
            continue
        cc, region = office_country[r.office_code], office_region[r.office_code]
        frac = ((e - s).days + 1) / 365.0
        plan = _book(s_cw, cal, cc, region, s, e, CW_DAYS_PER_YEAR * frac, taken[r.bw_worker_id])
        sick_n = s_cw.poisson(CW_SICK_PER_YEAR * frac)
        for _ in range(sick_n):
            span = [d for d in cal.days if s <= d <= min(e, data_through) and cal.working(cc, d) and d not in taken[r.bw_worker_id]]
            if span:
                d0 = span[int(s_cw.integers(len(span)))]
                taken[r.bw_worker_id].add(d0)
                plan.append((d0, d0, [d0], "Sick"))
        for item in plan:
            b0, b1, days = item[0], item[1], item[2]
            kind = item[3] if len(item) > 3 else "Planned time off"
            if kind == "Sick":
                created = dt.datetime.combine(b0, dt.time(7)) + dt.timedelta(minutes=int(s_cw.integers(0, 30 * 60)))
                approved = created + dt.timedelta(minutes=int(s_cw.integers(5, 8 * 60)))
            else:
                created, approved = state["stamp"](s_cw, b0, *((1, 30) if len(days) <= 2 else (10, 90)))
            if created > known:
                for x in days:
                    taken[r.bw_worker_id].discard(x)
                continue
            approved = min(approved, known)
            n_bk += 1
            bid = f"BT{n_bk:07d}"
            hpd = 8.0
            bookings.append({"booking_id": bid, "bw_worker_id": r.bw_worker_id, "service_order_id": r.service_order_id,
                             "booking_type": kind, "first_day": _s(b0), "last_day": _s(b1),
                             "working_days": len(days), "hours": len(days) * hpd, "status": "Approved",
                             "submitted_at": created.isoformat(sep=" "), "approved_at": approved.isoformat(sep=" ")})
            pid = state["ks_person"].get(r.bw_worker_id)
            sent = approved + dt.timedelta(minutes=int(s_cw.integers(30, 12 * 60)))
            if pid and sent <= known:
                ks_rows.append({"person_id": pid, "person_type": "Contingent", "source_system": "BW", "bw_booking_id": bid,
                                "time_off_type": "Contingent worker · " + kind, "request_type": "Absence Request",
                                "first_day": _s(b0), "last_day": _s(b1), "units": float(len(days)), "unit_of_time": "Days",
                                "days_requested": float(len(days)), "corrects_request_id": None, "status": "Approved",
                                "created_at": sent.isoformat(sep=" "), "approved_at": approved.isoformat(sep=" ")})
    return bookings, ks_rows


def build_all(stream, workers, job, offices, countries, bw_worker, bw_order, bw_revision, ks_cw,
              report_date: dt.date, data_through: dt.date) -> dict[str, pd.DataFrame]:
    st = build(stream, workers, job, offices, countries, bw_worker, bw_revision, ks_cw, report_date, data_through)
    bookings, ks_cw_rows = build_cw(st, bw_order, data_through)
    req = pd.DataFrame(st["req"])
    n = len(req)
    cw = pd.DataFrame(ks_cw_rows)
    cw.insert(0, "time_off_request_id", [f"TO{n + i:07d}" for i in range(1, len(cw) + 1)])
    req = pd.concat([req, cw[req.columns]], ignore_index=True)
    return {"ks_time_off_request": req, "ks_leave_of_absence": pd.DataFrame(st["leaves"]),
            "bw_time_off": pd.DataFrame(bookings), "ref_public_holiday": st["hol"]}


if __name__ == "__main__":
    import argparse
    import time
    from pathlib import Path

    import reference_data as ref

    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "raw")
    ap.add_argument("--job", type=Path, default=None, help="job history to use (default: raw)")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    t0 = time.time()
    rd = lambda n: pd.read_csv(a.raw / f"{n}.csv", dtype=str, keep_default_na=False, na_values=[""])
    key = int.from_bytes("time_off".encode(), "big") % (2**63)
    st = np.random.default_rng(np.random.SeedSequence([20261009, key]))
    res = build_all(st, rd("dim_worker"), pd.read_csv(a.job, dtype=str, keep_default_na=False, na_values=[""]) if a.job else rd("fact_job_history"),
                    rd("dim_location"), rd("dim_country"), rd("bw_contingent_worker"), rd("bw_service_order"),
                    rd("bw_service_order_revision"), rd("ks_contingent_worker"),
                    dt.date.fromisoformat(ref.LAST_SNAPSHOT), dt.date.fromisoformat(ref.DATA_THROUGH))
    a.out.mkdir(parents=True, exist_ok=True)
    for name, df in res.items():
        df.to_csv(a.out / f"{name}.csv", index=False, lineterminator="\n")
        print(f"  {name:<24} {len(df):>9,} rows")
    print(f"done in {time.time() - t0:.0f}s")
