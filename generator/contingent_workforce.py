"""
Contingent workforce simulation for Bridgeway VMS (warehouse release 3, phase 3).

Arcadia engages contingent workers (CW) through suppliers in Bridgeway VMS, its vendor
management system. This module simulates that program month by month and returns the
Bridgeway extract the warehouse loads:

    bw_supplier, bw_rate_card, bw_contingent_worker, bw_service_order,
    bw_service_order_revision, bw_timesheet_month

How an engagement lives
  * A manager raises a request; a supplier submits a vetted worker; a service order is
    opened, approved, and the assignment starts on a weekday.
  * Contractor and Consultant: an initial term, then extensions (each a new revision of the
    order). The whole engagement stops at 48 months from the original start; a few are
    extended past the cap anyway (they are the cap breaches the warehouse must flag).
    Some extensions renegotiate the rate (a separate Rate change revision effective on the
    first day of the extension), and some are processed as a new service order (Renewal),
    repriced on the current rate card.
  * BPO: orders run to June 30 and are renewed as a new order on July 1; no cap.
  * Monthly hazards: early ends, cost center, manager and office changes. When the hiring
    manager stops being a people manager in that department, the order gets a manager change.
  * The February 2024 restructuring ends a share of Commercial and Marketing contingent workers.
  * Every ended order is closed in Bridgeway a few days after its last day (a Closure revision).
  * A few submitted workers are withdrawn or rejected before they start.

What the extract contains
  * Only what Bridgeway knows on the extract date (2026-06-30): later revisions, approvals
    and closures are not in it; orders opened by then but starting in July are.
  * Workers whose last assignment ended before 2020-07-01 are archived (not extracted).
  * Timesheets for the warehouse's history window (Jun 2021 to Jun 2026).

Everything here is a clean program. The disagreements between Bridgeway and Keystone HR
are added in phase 4, on top of this truth. The engagements are also returned, so phase 4
can build Keystone's view and the discrepancy truth table from the same facts.

It draws from its own random stream (passed in), so the employee simulation is unchanged.
Arcadia Systems, Bridgeway VMS and every supplier and person here are fictional.
"""

from __future__ import annotations

import calendar
import math
import datetime as dt
import re
from collections import defaultdict
from dataclasses import dataclass, field
from decimal import ROUND_HALF_UP, Decimal

import numpy as np
import pandas as pd

import fx_rates
import reference_data as ref

ONE_DAY = dt.timedelta(days=1)
FX_FIRST_DAY = fx_rates.FIRST_DAY
WHOLE_UNIT_CURRENCIES = {"INR", "JPY", "KRW", "PHP"}
# ties on the same day: the order revisions are written in
REASON_PRIORITY = {"Original": 0, "Renewal": 0, "Extension": 1, "Rate change": 2, "Cost center change": 3,
                   "Manager change": 4, "Office change": 5, "Early end": 6, "Closure": 7}


# ======================================================================================
# Date helpers
# ======================================================================================
def month_end(y: int, m: int) -> dt.date:
    return dt.date(y, m, calendar.monthrange(y, m)[1])


def add_months(d: dt.date, n: int) -> dt.date:
    y, m = divmod(d.month - 1 + n, 12)
    y, m = d.year + y, m + 1
    return dt.date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def fiscal_year(d: dt.date) -> int:
    return d.year + 1 if d.month >= ref.FISCAL_YEAR_START_MONTH else d.year


def next_weekday(d: dt.date) -> dt.date:
    while d.weekday() >= 5:
        d += ONE_DAY
    return d


def fiscal_year_end(d: dt.date) -> dt.date:
    return dt.date(fiscal_year(d), 6, 30)


def weekdays_between(a: dt.date, b: dt.date) -> int:
    """Weekdays from a to b, both inclusive."""
    return int(np.busday_count(a, b + ONE_DAY)) if b >= a else 0


# ======================================================================================
# The program
# ======================================================================================
@dataclass
class Order:
    service_order_id: str
    bw_worker_id: str
    supplier_id: str
    order_type: str                     # New engagement, Renewal
    renews: str | None
    opened: dt.date
    submitted: dt.date
    approved: dt.date | None
    base: dict                          # revision 0 snapshot
    events: list = field(default_factory=list)   # (effective date, reason, changes)
    withdrawn: str | None = None        # Withdrawn / Rejected


@dataclass
class Engagement:
    eng_id: int
    bw_worker_id: str
    cw_type: str
    supplier_id: str
    country: str
    office: str
    dept: str
    cost_center: str
    role_family: str
    seniority: str
    job_title: str
    orig_start: dt.date
    manager_id: str
    manager_until: dt.date
    bill_rate: float
    billing_currency: str
    order: Order
    end: dt.date                        # last day of the current assignment
    extensions: int = 0
    cap_breach: bool = False
    end_reason: str | None = None       # Completed, Ended early, Restructuring
    orders: list = field(default_factory=list)


class Program:
    def __init__(self, *, stream: np.random.Generator, office: dict, dept: dict, country: dict,
                 job: pd.DataFrame, workers: pd.DataFrame, cost_centers: list[dict],
                 reorg_date: dt.date, restructure_date: dt.date):
        self.rng = stream
        self.office, self.dept, self.country = office, dept, country
        self.reorg_date, self.restructure_date = reorg_date, restructure_date
        self.cc = {(c["department_id"], c["country_code"]): c["cost_center_id"] for c in cost_centers}
        self.burn_start = dt.date.fromisoformat(ref.CW_BURN_IN_START)
        self.extract = dt.date.fromisoformat(ref.CW_EXTRACT_DATE)
        self.history_start = dt.date.fromisoformat(ref.FIRST_SNAPSHOT)
        self.archive_before = dt.date.fromisoformat(ref.CW_ARCHIVE_BEFORE)
        self.suppliers = [dict(zip(["id", "name", "types", "hq", "serves", "weight", "onboarded", "offboarded"], s))
                          for s in ref.CW_SUPPLIERS]
        for s in self.suppliers:
            s["onboarded"] = dt.date.fromisoformat(s["onboarded"])
            s["offboarded"] = dt.date.fromisoformat(s["offboarded"]) if s["offboarded"] else None
            s["types"] = s["types"].split(";")
        self._managers(job)
        self._emails(workers)
        self.engagements: list[Engagement] = []
        self.withdrawn_orders: list[tuple[Order, dict]] = []
        self.worker_rows: dict[str, dict] = {}
        self.cw_email_seen: dict[str, int] = defaultdict(int)
        self.n_worker = self.n_order = 0

    # ---------------------------------------------------------------- reference lookups
    def _managers(self, job: pd.DataFrame):
        """Contiguous people-manager tenures per worker and department, with the office country."""
        j = job[job["is_people_manager"].astype(str).isin(["True", "true", "1"])].copy()
        j["start"] = pd.to_datetime(j["effective_start_date"]).dt.date
        j["end"] = pd.to_datetime(j["effective_end_date"]).dt.date
        j["end"] = j["end"].where(j["end"].notna(), dt.date(9999, 12, 31))
        j["country"] = j["location_id"].map(lambda loc: self.office[loc]["country"])
        j = j.sort_values(["worker_id", "start"])
        tenures = []
        for (wid, dep), g in j.groupby(["worker_id", "department_id"], sort=True):
            cur = None
            for r in g.itertuples(index=False):
                if cur and r.start <= cur["end"] + ONE_DAY:
                    cur["end"] = max(cur["end"], r.end)
                else:
                    if cur:
                        tenures.append(cur)
                    cur = {"worker_id": wid, "dept": dep, "start": r.start, "end": r.end, "country": r.country}
            tenures.append(cur)
        t = pd.DataFrame(tenures)
        self.mgr_by_dept = {}
        for d, g in t.groupby("dept"):            # plain arrays: this lookup runs ~80,000 times
            self.mgr_by_dept[d] = (g["worker_id"].to_numpy(), np.array([x.toordinal() for x in g["start"]]),
                                   np.array([x.toordinal() for x in g["end"]]), g["end"].to_numpy(),
                                   g["country"].to_numpy())

    def _emails(self, workers: pd.DataFrame):
        self.emp_email = dict(zip(workers["worker_id"], employee_emails(workers)))

    def pick_manager(self, dept: str, cc: str, on: dt.date) -> tuple[str, dt.date]:
        wid, start, end, end_date, country = self.mgr_by_dept[dept]
        o = on.toordinal()
        live = np.flatnonzero((start <= o) & (end >= o))
        if not len(live):               # before history for this department: anyone who managed it
            live = np.flatnonzero(end >= o)
            if not len(live):
                live = np.arange(len(wid))
        same = live[country[live] == cc]
        pool = same if len(same) else live
        k = pool[int(self.rng.integers(len(pool)))]
        return wid[k], end_date[k]

    def choose(self, options: dict):
        keys = list(options)
        w = np.array([options[k] for k in keys], dtype=float)
        return keys[self.rng.choice(len(keys), p=w / w.sum())]

    def open_offices(self, cc: str, on: dt.date) -> dict:
        return {o["id"]: o["weight"] for o in self.office.values() if o["country"] == cc and o["opened"] <= on}

    # ---------------------------------------------------------------- rates
    def anchor_usd(self, cc: str) -> float:
        return ref.CW_RATE_ANCHOR_USD.get(cc, 20.0 + 70.0 * self.country[cc]["pay_index"])

    def target_rate_usd(self, fy: int, cc: str, cw_type: str, role: str, seniority: str) -> tuple[float, str]:
        idx = (1 + ref.CW_RATE_MARKET_INDEX + ref.CW_RATE_MARKET_INDEX_COUNTRY_PP.get(cc, 0.0)) ** (fy - 2026)
        if cw_type == "BPO":
            sen = {"Junior": 0.85, "Mid": 1.00, "Senior": 1.20, "Lead": 1.40}[seniority]
            return 168 * self.anchor_usd(cc) * ref.CW_BPO_HOURLY_SHARE * ref.CW_BPO_ROLE_FACTOR[role] * sen * idx, "Monthly"
        return (self.anchor_usd(cc) * ref.CW_TYPE_FACTOR[cw_type] * ref.CW_ROLE_FACTOR[role]
                * ref.CW_SENIORITY_FACTOR[seniority] * idx), "Hourly"

    def order_rate(self, e_like: dict, on: dt.date, currency: str) -> float:
        usd, _ = self.target_rate_usd(fiscal_year(on), e_like["country"], e_like["cw_type"],
                                      e_like["role_family"], e_like["seniority"])
        usd *= float(np.exp(self.rng.normal(0, ref.CW_RATE_NOISE_SD)))
        return to_currency(usd, currency, on)

    def billing_currency(self, cc: str, cw_type: str) -> str:
        share = ref.CW_BPO_LOCAL_BILLING_SHARE if cw_type == "BPO" else ref.CW_LOCAL_BILLING_SHARE.get(cc, 0.1)
        return self.country[cc]["currency"] if self.rng.random() < share else "USD"

    # ---------------------------------------------------------------- new engagements
    def target(self, me: dt.date) -> float:
        jun21 = dt.date(2021, 6, 30)
        if me <= jun21:
            months = (jun21.year - self.burn_start.year) * 12 + jun21.month - self.burn_start.month
            k = (me.year - self.burn_start.year) * 12 + me.month - self.burn_start.month
            return ref.CW_TARGET_START * (ref.CW_TARGET_JUN_2021 / ref.CW_TARGET_START) ** (k / months)
        level = ref.CW_TARGET_JUN_2021
        for fy in range(2022, fiscal_year(me)):
            level *= 1 + ref.CW_FY_GROWTH[fy]
        g = ref.CW_FY_GROWTH.get(fiscal_year(me), 0.04)
        months_in = (me.month - 7) % 12 + 1
        return level * (1 + g) ** (months_in / 12)

    def pick_country(self, cw_type: str, on: dt.date) -> str:
        mix = ref.CW_COUNTRY_MIX[cw_type]
        if mix == "workforce":
            mix = {c: v["weight"] for c, v in self.country.items()}
        mix = {c: w for c, w in mix.items() if self.open_offices(c, on)}
        return self.choose(mix)

    def pick_department(self, cw_type: str, cc: str, on: dt.date) -> str:
        mix = ref.CW_FUNCTION_MIX[cw_type]
        if cw_type == "BPO":
            return self.choose({d: w for d, w in mix.items() if (d, cc) in self.cc})
        fn = self.choose(mix)
        depts = {d: (v["size_weight"] or 0.06) for d, v in self.dept.items()
                 if v["function"] == fn and (d, cc) in self.cc and d != "D-901"
                 and (d != "D-108" or on >= self.reorg_date)}
        if not depts:                   # the function has no cost center in that country: any department that does
            depts = {d: (v["size_weight"] or 0.06) for d, v in self.dept.items()
                     if (d, cc) in self.cc and d != "D-901" and (d != "D-108" or on >= self.reorg_date)}
        return self.choose(depts)

    def pick_supplier(self, cw_type: str, cc: str, role: str, on: dt.date) -> str:
        opts = {}
        for s in self.suppliers:
            if cw_type not in s["types"] or s["onboarded"] > on or (s["offboarded"] and s["offboarded"] < on):
                continue
            if s["serves"] and cc not in s["serves"]:
                continue
            if cw_type == "BPO" and role not in ref.CW_BPO_SUPPLIER_ROLES.get(s["id"], []):
                continue
            opts[s["id"]] = s["weight"]
        if not opts:                    # nobody serves that country yet: any supplier of the type
            opts = {s["id"]: s["weight"] for s in self.suppliers if cw_type in s["types"] and s["onboarded"] <= on
                    and (cw_type != "BPO" or role in ref.CW_BPO_SUPPLIER_ROLES.get(s["id"], []))}
        return self.choose(opts)

    def new_worker(self, cc: str, supplier: str, cw_type: str, created: dt.date) -> str:
        self.n_worker += 1
        wid = f"BW{10_000 + self.n_worker:08d}"
        first_pool, last_pool = ref.NAMES[self.country[cc]["region"]]
        first = first_pool[int(self.rng.integers(len(first_pool)))]
        last = last_pool[int(self.rng.integers(len(last_pool)))]
        base = f"{_slug(first)}.{_slug(last)}"
        self.cw_email_seen[base] += 1
        n = self.cw_email_seen[base]
        self.worker_rows[wid] = {"bw_worker_id": wid, "first_name": first, "last_name": last,
                                 "email": f"{base}{'' if n == 1 else n}@{ref.CW_EMAIL_DOMAIN}",
                                 "supplier_id": supplier, "cw_type": cw_type, "original_start_date": None,
                                 "created_date": created}
        return wid

    def new_order_id(self) -> str:
        self.n_order += 1
        return f"SO{1_000_000 + self.n_order:07d}"

    def request_dates(self, start: dt.date) -> tuple[dt.date, dt.date, dt.date]:
        opened = start - dt.timedelta(days=int(self.rng.integers(21, 75)))
        submitted = opened + dt.timedelta(days=int(self.rng.integers(3, 21)))
        approved = submitted + dt.timedelta(days=int(self.rng.integers(1, 12)))
        approved = min(approved, start - ONE_DAY)
        submitted = min(submitted, approved)
        return opened, submitted, approved

    def first_term_end(self, cw_type: str, start: dt.date) -> dt.date:
        if cw_type == "BPO":
            end = fiscal_year_end(start)
            return end if (end - start).days >= 90 else dt.date(end.year + 1, 6, 30)
        months = self.choose(ref.CW_INITIAL_TERM_MONTHS[cw_type])
        return add_months(start, months) - ONE_DAY

    def start_engagement(self, start: dt.date):
        cw_type = self.choose(ref.CW_TYPE_FLOW)
        cc = self.pick_country(cw_type, start)
        dept = self.pick_department(cw_type, cc, start)
        if cw_type == "BPO":
            role = self.choose(ref.CW_ROLE_FAMILIES_BPO[dept])
        elif self.dept[dept]["function"] == "Technology":
            role = self.choose(ref.CW_ROLE_FAMILIES_TECH)
        else:
            role = self.choose(ref.CW_ROLE_FAMILIES_BUSINESS)
        seniority = self.choose(ref.CW_SENIORITY_MIX[cw_type])
        title = f"{seniority} {ref.CW_ROLE_TITLES[role]}" if seniority != "Mid" else ref.CW_ROLE_TITLES[role]
        supplier = self.pick_supplier(cw_type, cc, role, start)
        office = self.choose(self.open_offices(cc, start))
        opened, submitted, approved = self.request_dates(start)

        if self.rng.random() < ref.CW_WITHDRAWN_SHARE:     # a first candidate falls through
            w_sub = opened + dt.timedelta(days=int(self.rng.integers(2, 10)))
            wid = self.new_worker(cc, supplier, cw_type, w_sub)
            o = Order(self.new_order_id(), wid, supplier, "New engagement", None, opened, w_sub, None, {},
                      withdrawn="Withdrawn" if self.rng.random() < 0.65 else "Rejected")
            o.base = {"status": o.withdrawn, "effective": w_sub + dt.timedelta(days=int(self.rng.integers(2, 12))),
                      "role_family": role, "seniority": seniority, "job_title": title,
                      "cost_center_code": self.cc[(dept, cc)], "office_code": office,
                      "hiring_manager_email": None, "assignment_start_date": start,
                      "assignment_end_date": self.first_term_end(cw_type, start),
                      "bill_rate": None, "rate_type": None, "billing_currency": None, "hours_per_week": None}
            self.withdrawn_orders.append((o, {"country": cc}))

        wid = self.new_worker(cc, supplier, cw_type, submitted)
        mgr, until = self.pick_manager(dept, cc, start)
        currency = self.billing_currency(cc, cw_type)
        e_like = {"country": cc, "cw_type": cw_type, "role_family": role, "seniority": seniority}
        rate = self.order_rate(e_like, approved, currency)
        end = self.first_term_end(cw_type, start)
        order = Order(self.new_order_id(), wid, supplier, "New engagement", None, opened, submitted, approved, {})
        e = Engagement(len(self.engagements) + 1, wid, cw_type, supplier, cc, office, dept, self.cc[(dept, cc)],
                       role, seniority, title, start, mgr, until, rate, currency, order, end)
        order.base = self.snapshot(e, start, end, "Original")
        e.orders.append(order)
        self.worker_rows[wid]["original_start_date"] = start
        self.engagements.append(e)
        return e

    def snapshot(self, e: Engagement, start: dt.date, end: dt.date, reason: str) -> dict:
        return {"status": "Approved", "reason": reason, "role_family": e.role_family, "seniority": e.seniority,
                "job_title": e.job_title, "cost_center_code": e.cost_center, "office_code": e.office,
                "hiring_manager_email": self.emp_email[e.manager_id], "assignment_start_date": start,
                "assignment_end_date": end, "bill_rate": e.bill_rate,
                "rate_type": "Monthly" if e.cw_type == "BPO" else "Hourly", "billing_currency": e.billing_currency,
                "hours_per_week": None if e.cw_type == "BPO" else 40.0}

    # ---------------------------------------------------------------- what happens to an engagement
    def cap_end(self, e: Engagement) -> dt.date:
        return add_months(e.orig_start, ref.CW_MAX_MONTHS) - ONE_DAY

    def end_of_term(self, e: Engagement) -> bool:
        """The current term ends this month: extend, renew or let it end. Returns True if it continues."""
        old_end = e.end
        if e.cw_type == "BPO":
            if old_end.month == 6 and old_end.day == 30 and self.rng.random() < ref.CW_BPO_RENEWAL_PROBABILITY:
                self.renew(e, old_end, dt.date(old_end.year + 1, 6, 30))
                return True
            return False
        cap = self.cap_end(e)
        p = ref.CW_EXTEND_PROBABILITY[e.cw_type] * (0.93 ** e.extensions)
        if self.rng.random() >= p:
            return False
        months = self.choose(ref.CW_EXTENSION_MONTHS)
        new_end = add_months(old_end + ONE_DAY, months) - ONE_DAY
        if new_end > cap:
            if (cap - old_end).days >= 45:
                new_end = cap
            elif self.rng.random() < ref.CW_CAP_BREACH:          # extended past the cap anyway
                new_end = add_months(old_end + ONE_DAY, int(self.rng.choice([3, 6]))) - ONE_DAY
                e.cap_breach = True
            else:
                return False
        e.extensions += 1
        if self.rng.random() < ref.CW_RENEWAL_SHARE:
            self.renew(e, old_end, new_end)
            return True
        if self.rng.random() < ref.CW_LATE_EXTENSION_SHARE:
            approved = old_end + dt.timedelta(days=int(self.rng.integers(1, 21)))
        else:
            approved = old_end - dt.timedelta(days=int(self.rng.integers(5, 41)))
        e.order.events.append((approved, "Extension", {"assignment_end_date": new_end}))
        if self.rng.random() < ref.CW_RENEGOTIATE_SHARE:
            lo, hi = ref.CW_RENEGOTIATE_RANGE
            e.bill_rate = round_rate(e.bill_rate * (1 + self.rng.uniform(lo, hi)), e.billing_currency)
            e.order.events.append((old_end + ONE_DAY, "Rate change", {"bill_rate": e.bill_rate}))
        e.end = new_end
        return True

    def renew(self, e: Engagement, old_end: dt.date, new_end: dt.date):
        """A new service order for the same worker, starting the day after the old one ends."""
        start = old_end + ONE_DAY
        opened = old_end - dt.timedelta(days=int(self.rng.integers(30, 60)))
        submitted = opened + dt.timedelta(days=int(self.rng.integers(1, 8)))
        approved = submitted + dt.timedelta(days=int(self.rng.integers(2, 20)))
        if self.rng.random() < ref.CW_LATE_EXTENSION_SHARE:
            approved = old_end + dt.timedelta(days=int(self.rng.integers(1, 21)))
        e.bill_rate = self.order_rate({"country": e.country, "cw_type": e.cw_type, "role_family": e.role_family,
                                       "seniority": e.seniority}, start, e.billing_currency)
        self.close(e.order, old_end)
        o = Order(self.new_order_id(), e.bw_worker_id, e.supplier_id, "Renewal", e.order.service_order_id,
                  opened, submitted, approved, {})
        o.base = self.snapshot(e, start, new_end, "Renewal")
        e.order = o
        e.orders.append(o)
        e.end = new_end

    def close(self, order: Order, last_day: dt.date):
        closed = last_day + dt.timedelta(days=int(self.rng.integers(0, 16)))
        order.events.append((closed, "Closure", {"status": "Closed", "closed_date": closed}))

    def end_early(self, e: Engagement, last_day: dt.date, reason: str):
        notice = last_day - dt.timedelta(days=int(self.rng.integers(0, 11)))
        e.order.events.append((max(notice, e.order.base["assignment_start_date"]), "Early end",
                               {"assignment_end_date": last_day}))
        e.end, e.end_reason = last_day, reason

    def attribute_change(self, e: Engagement, kind: str, on: dt.date):
        if kind == "Cost center change":
            dept = self.pick_department(e.cw_type, e.country, on)
            if dept == e.dept or (e.cw_type == "BPO" and e.role_family not in ref.CW_ROLE_FAMILIES_BPO[dept]):
                return
            e.dept, e.cost_center = dept, self.cc[(dept, e.country)]
            e.manager_id, e.manager_until = self.pick_manager(dept, e.country, on)
            e.order.events.append((on, kind, {"cost_center_code": e.cost_center,
                                              "hiring_manager_email": self.emp_email[e.manager_id]}))
        elif kind == "Manager change":
            mgr, until = self.pick_manager(e.dept, e.country, on)
            if mgr == e.manager_id:
                return
            e.manager_id, e.manager_until = mgr, until
            e.order.events.append((on, kind, {"hiring_manager_email": self.emp_email[mgr]}))
        elif kind == "Office change":
            offices = {k: w for k, w in self.open_offices(e.country, on).items() if k != e.office}
            if not offices:
                return
            e.office = self.choose(offices)
            e.order.events.append((on, kind, {"office_code": e.office}))

    # ---------------------------------------------------------------- the monthly loop
    def run(self):
        month_ends = []
        d = self.burn_start
        last = month_end(self.extract.year, self.extract.month + 1) if self.extract.month < 12 else month_end(self.extract.year + 1, 1)
        while d <= last:
            month_ends.append(d)
            d = month_end((d + ONE_DAY).year, (d + ONE_DAY).month)
        active: dict[int, Engagement] = {}
        hazards = list(ref.CW_ATTRIBUTE_CHANGE_MONTHLY.items())
        for me in month_ends:
            ms = dt.date(me.year, me.month, 1)
            ids = list(active)
            r_early = self.rng.random(len(ids))
            r_attr = self.rng.random((len(ids), len(hazards)))
            for i, eid in enumerate(ids):
                e = active[eid]
                if ms <= e.end <= me:
                    continue                                         # decided below
                # restructuring: Commercial and Marketing contingent workers cut
                if (me.year, me.month) == (self.restructure_date.year, self.restructure_date.month) \
                        and self.dept[e.dept]["function"] in ("Commercial", "Marketing") \
                        and r_early[i] < ref.CW_RESTRUCTURING_CUT:
                    day = self.restructure_date + dt.timedelta(days=int(self.rng.integers(0, (me - self.restructure_date).days + 1)))
                    self.end_early(e, max(day, e.order.base["assignment_start_date"]), "Restructuring")
                    continue
                if r_early[i] < ref.CW_EARLY_END_MONTHLY[e.cw_type]:
                    first = max(ms, e.order.base["assignment_start_date"] + dt.timedelta(days=7))
                    if first <= me:
                        day = first + dt.timedelta(days=int(self.rng.integers(0, (me - first).days + 1)))
                        self.end_early(e, day, "Ended early")
                        continue
                for k, (kind, p) in enumerate(hazards):
                    if r_attr[i, k] < p:
                        on = ms + dt.timedelta(days=int(self.rng.integers(0, me.day)))
                        if e.order.base["assignment_start_date"] < on < e.end:
                            self.attribute_change(e, kind, on)
                if e.manager_until < me and e.manager_until + ONE_DAY < e.end:
                    self.attribute_change(e, "Manager change", e.manager_until + ONE_DAY)
            # terms ending this month
            for eid in list(active):
                e = active[eid]
                if e.end <= me and e.end_reason is None:
                    while e.end <= me and self.end_of_term(e):
                        pass
                if e.end <= me:
                    e.end_reason = e.end_reason or "Completed"
                    self.close(e.order, e.end)
                    del active[eid]
            # new engagements to reach the month-end target
            for _ in range(max(0, int(round(self.target(me) - len(active))))):
                day = next_weekday(ms + dt.timedelta(days=int(self.rng.integers(0, me.day))))
                if day > me:
                    day = next_weekday(ms)
                e = self.start_engagement(day)
                active[e.eng_id] = e
        self.active_at_end = active

    # ---------------------------------------------------------------- conversions (phase 5)
    def convert(self, hires: pd.DataFrame, stream: np.random.Generator):
        """Some contingent workers are hired as employees when their engagement ends.

        `hires` holds the external hires into requisitions (worker_id, hire_date, country,
        department_id, function, first_name, last_name). For a share of Contractor and
        Consultant engagements that end (completed or early, not in the restructuring), look
        for a hire in the same country and department (or function) in the same calendar month
        as the first day after the engagement, within CW_CONVERSION_MAX_GAP_DAYS: that hire is
        the same person. Bridgeway's worker takes the employee's name; the engagement is marked
        Converted. Drawn from its own stream, so nothing else in the program moves.
        """
        by_dept, by_fn = defaultdict(list), defaultdict(list)
        for h in hires.sort_values(["hire_date", "worker_id"]).itertuples(index=False):
            by_dept[(h.country, h.department_id)].append(h)
            by_fn[(h.country, h.function)].append(h)
        start = dt.date.fromisoformat(ref.CW_CONVERSION_FROM)
        claimed: set[str] = set()
        self.conversions: dict[str, dict] = {}
        exits = sorted((e for e in self.engagements
                        if e.end_reason in ("Completed", "Ended early") and e.cw_type != "BPO"
                        and start <= e.end + ONE_DAY and e.end < self.extract),
                       key=lambda e: (e.end, e.eng_id))
        for e in exits:
            if stream.random() >= ref.CW_CONVERSION_ATTEMPT:
                continue
            first = e.end + ONE_DAY
            last = min(e.end + dt.timedelta(days=ref.CW_CONVERSION_MAX_GAP_DAYS), month_end(first.year, first.month))
            options = []
            for pool in (by_dept[(e.country, e.dept)], by_fn[(e.country, self.dept[e.dept]["function"])]):
                options = [h for h in pool if first <= h.hire_date <= last and h.worker_id not in claimed]
                if options:
                    break
            if not options:
                continue
            h = options[int(stream.integers(len(options)))]
            claimed.add(h.worker_id)
            e.end_reason = "Converted"
            self.conversions[e.bw_worker_id] = {"worker_id": h.worker_id, "hire_date": h.hire_date,
                                                "last_day": e.end, "candidate_id": h.candidate_id}
            row = self.worker_rows[e.bw_worker_id]
            base = f"{_slug(h.first_name)}.{_slug(h.last_name)}"
            self.cw_email_seen[base] += 1
            n = self.cw_email_seen[base]
            row.update(first_name=h.first_name, last_name=h.last_name,
                       email=f"{base}{'' if n == 1 else n}@{ref.CW_EMAIL_DOMAIN}")

    # ---------------------------------------------------------------- the extract
    def tables(self) -> dict[str, pd.DataFrame]:
        keep_workers = {e.bw_worker_id for e in self.engagements if e.end >= self.archive_before}
        orders, revisions = [], []
        all_orders = [(o, e) for e in self.engagements if e.bw_worker_id in keep_workers for o in e.orders]
        all_orders += [(o, None) for o, _ in self.withdrawn_orders if o.submitted >= self.archive_before]
        for o, e in all_orders:
            if o.opened > self.extract:
                continue
            revs = self.revisions(o)
            if not revs:
                continue
            orders.append({"service_order_id": o.service_order_id, "bw_worker_id": o.bw_worker_id,
                           "supplier_id": o.supplier_id, "order_type": o.order_type,
                           "renews_service_order_id": o.renews, "opened_date": o.opened,
                           "submitted_date": o.submitted,
                           "approved_date": o.approved if o.approved and o.approved <= self.extract else None,
                           "final_status": revs[-1]["status"]})
            revisions += revs
        rev = pd.DataFrame(revisions)
        rev.insert(0, "revision_id", [f"SR{n:08d}" for n in range(1, len(rev) + 1)])
        extracted = {o["bw_worker_id"] for o in orders}
        workers = pd.DataFrame([w for wid, w in self.worker_rows.items() if wid in extracted])
        return {"bw_supplier": self.supplier_table(), "bw_rate_card": self.rate_card(),
                "bw_contingent_worker": workers.sort_values("bw_worker_id"),
                "bw_service_order": pd.DataFrame(orders).sort_values("service_order_id"),
                "bw_service_order_revision": rev,
                "bw_timesheet_month": self.timesheets(rev)}

    def revisions(self, o: Order) -> list[dict]:
        """Cumulative revision snapshots, as Bridgeway holds them on the extract date."""
        b = o.base
        if o.withdrawn:
            start_eff = b["effective"]
        elif o.approved and o.approved <= self.extract:
            start_eff = o.approved
        else:
            start_eff = o.submitted          # still pending approval on the extract date
        if start_eff > self.extract:
            return []
        state = {k: v for k, v in b.items() if k not in ("reason", "effective")}
        state["closed_date"] = None
        if not o.withdrawn and not (o.approved and o.approved <= self.extract):
            state["status"] = "Pending Approval"
        rows = [(start_eff, b.get("reason", "Original"), dict(state))]
        events = sorted(o.events, key=lambda ev: (ev[0], REASON_PRIORITY[ev[1]]))
        for when, reason, changes in events:
            if when > self.extract or state["status"] in ("Pending Approval", "Withdrawn", "Rejected"):
                continue
            when = max(when, rows[-1][0] + ONE_DAY)      # one revision per day: a same-day change takes the next day
            if when > self.extract:
                continue
            state.update(changes)
            rows.append((when, reason, dict(state)))
        out = []
        for i, (when, reason, st) in enumerate(rows):
            nxt = rows[i + 1][0] if i + 1 < len(rows) else None
            end = (nxt - ONE_DAY) if nxt else None
            out.append({"service_order_id": o.service_order_id, "revision_no": i, "revision_reason": reason,
                        "effective_start_date": when, "effective_end_date": end, "is_current": nxt is None,
                        "status": st["status"], "assignment_start_date": st["assignment_start_date"],
                        "assignment_end_date": st["assignment_end_date"], "closed_date": st.get("closed_date"),
                        "role_family": st["role_family"], "seniority": st["seniority"], "job_title": st["job_title"],
                        "cost_center_code": st["cost_center_code"], "hiring_manager_email": st["hiring_manager_email"],
                        "office_code": st["office_code"], "bill_rate": st["bill_rate"], "rate_type": st["rate_type"],
                        "billing_currency": st["billing_currency"], "hours_per_week": st["hours_per_week"]})
        return out

    def timesheets(self, rev: pd.DataFrame) -> pd.DataFrame:
        """Billed time per order and month, at the rate in effect on each working day."""
        rows = []
        r = rev[rev["status"].isin(["Approved", "Closed"])].sort_values(["service_order_id", "revision_no"])
        worker_of = {o.service_order_id: o.bw_worker_id for e in self.engagements for o in e.orders}
        by_order: dict[str, list] = defaultdict(list)
        for row in r.itertuples(index=False):    # plain tuples: ~650,000 timesheet rows come out of this
            by_order[row.service_order_id].append(row)
        months = []
        d = self.history_start
        while d <= self.extract:
            months.append(d)
            d = month_end((d + ONE_DAY).year, (d + ONE_DAY).month)
        n = 0
        for so in sorted(by_order):
            g = by_order[so]
            cur = g[-1]
            start, end = cur.assignment_start_date, min(cur.assignment_end_date, self.extract)
            if end < self.history_start or start > self.extract:
                continue
            # rate periods: each revision's rate from its effective start (revision 0 from the assignment start)
            periods = []
            for row in g:
                p0 = start if row.revision_no == 0 else max(row.effective_start_date, start)
                periods.append((p0, row.bill_rate))
            bounds = []
            for i, (p0, rate) in enumerate(periods):
                p1 = periods[i + 1][0] - ONE_DAY if i + 1 < len(periods) else end
                if p1 >= p0:
                    bounds.append((p0, p1, rate))
            merged = []
            for p0, p1, rate in bounds:                 # adjacent periods at the same rate are one period
                if merged and merged[-1][2] == rate and merged[-1][1] + ONE_DAY == p0:
                    merged[-1] = (merged[-1][0], p1, rate)
                else:
                    merged.append((p0, p1, rate))
            monthly = cur.rate_type == "Monthly"
            wid = worker_of[so]
            for me in months:
                ms = dt.date(me.year, me.month, 1)
                if me < start or ms > end:
                    continue
                pto = float(self.rng.beta(1.5, 28)) if not monthly else 0.0
                for p0, p1, rate in merged:
                    a, b = max(ms, p0, start), min(me, p1, end)
                    if b < a:
                        continue
                    if monthly:
                        units = round((b - a).days / me.day + 1 / me.day, 4)
                        hours = 0.0
                    else:
                        hours = round(weekdays_between(a, b) * 8 * (1 - pto) * 4) / 4
                        units = hours
                    if units <= 0:
                        continue
                    n += 1
                    rows.append({"timesheet_id": f"TS{n:09d}", "bw_worker_id": wid, "service_order_id": so,
                                 "month_end_date": me, "billed_hours": hours, "billed_units": units,
                                 "bill_rate": rate, "billing_currency": cur.billing_currency,
                                 "billed_amount_local": money(units, rate)})
        return pd.DataFrame(rows)

    def supplier_table(self) -> pd.DataFrame:
        return pd.DataFrame([{"supplier_id": s["id"], "supplier_name": s["name"],
                              "cw_types_offered": ";".join(s["types"]), "hq_country_code": s["hq"],
                              "onboarded_date": s["onboarded"], "is_active": s["offboarded"] is None}
                             for s in self.suppliers])

    def rate_card(self) -> pd.DataFrame:
        rows = []
        roles = {"Contractor": list(ref.CW_ROLE_FACTOR), "Consultant": list(ref.CW_ROLE_FACTOR),
                 "BPO": list(ref.CW_BPO_ROLE_FACTOR)}
        sens = {"Contractor": list(ref.CW_SENIORITY_FACTOR), "Consultant": list(ref.CW_SENIORITY_FACTOR),
                "BPO": ["Junior", "Mid", "Senior"]}
        lo, hi = ref.CW_RATE_BAND
        for fy in range(fiscal_year(self.burn_start), fiscal_year(self.extract) + 2):
            for cc in sorted(self.country):
                for t in ref.CW_TYPES:
                    for role in roles[t]:
                        for sen in sens[t]:
                            usd, rtype = self.target_rate_usd(fy, cc, t, role, sen)
                            rows.append({"fiscal_year": fy, "country_code": cc, "cw_type": t, "role_family": role,
                                         "seniority": sen, "rate_type": rtype, "billing_currency": "USD",
                                         "rate_low": round(usd * lo, 2), "rate_target": round(usd, 2),
                                         "rate_high": round(usd * hi, 2)})
        df = pd.DataFrame(rows)
        df.insert(0, "rate_card_id", [f"RC{n:06d}" for n in range(1, len(df) + 1)])
        return df


# ======================================================================================
# Small helpers
# ======================================================================================
def money(units: float, rate: float) -> float:
    """units x rate to the cent, multiplied in decimals and rounded half up, as invoices are
    (binary floats land 0.3 x 1670.75 on 501.22499..., and Python's round() goes half to even)."""
    exact = Decimal(repr(units)) * Decimal(repr(rate))
    return float(exact.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def employee_emails(workers: pd.DataFrame) -> list[str]:
    """Each employee's work email, in the row order of `workers`: first.last@ the employee domain,
    numbered 2, 3, ... on a clash, in worker ID order."""
    seen: dict[str, int] = defaultdict(int)
    email = {}
    for r in workers.sort_values("worker_id").itertuples(index=False):
        base = f"{_slug(r.first_name)}.{_slug(r.last_name)}"
        seen[base] += 1
        n = seen[base]
        email[r.worker_id] = f"{base}{'' if n == 1 else n}@{ref.EMPLOYEE_EMAIL_DOMAIN}"
    return [email[w] for w in workers["worker_id"]]


def _slug(name: str) -> str:
    return re.sub(r"[^a-z0-9]", "", name.lower())


def round_rate(value: float, currency: str) -> float:
    return float(round(value)) if currency in WHOLE_UNIT_CURRENCIES else round(value * 4) / 4


def to_currency(usd: float, currency: str, on: dt.date) -> float:
    if currency == "USD":
        return round_rate(usd, currency)
    return round_rate(usd / fx_rates.usd_per_local(currency, max(on, FX_FIRST_DAY)), currency)


def plan_line(plan: pd.DataFrame, bw: dict[str, pd.DataFrame], stream: np.random.Generator) -> pd.DataFrame:
    """The contingent line of the workforce plan (phase 5).

    For every plan row (version x cost center x quarter), the planned contingent headcount at
    the quarter end and the planned annualized spend run-rate, in USD at the plan's FX date.
    Like the employee plan, each version is the quarter's actual (as Bridgeway held it on the
    quarter end) with a version's planning error: the budget furthest out and least accurate.
    """
    rev, so = bw["bw_service_order_revision"], bw["bw_service_order"]
    rev = rev[rev["status"].isin(["Approved", "Closed"])].merge(so[["service_order_id", "bw_worker_id"]])
    actual: dict[tuple, dict] = {}
    for qe in sorted(plan["quarter_end_date"].unique()):
        cur = rev[(rev["effective_start_date"] <= qe)
                  & (rev["effective_end_date"].isna() | (rev["effective_end_date"].map(lambda d: d is not None and d >= qe)))
                  & (rev["assignment_start_date"] <= qe) & (rev["assignment_end_date"] >= qe)]
        cur = cur.drop_duplicates("bw_worker_id", keep="last")
        annual = np.where(cur["rate_type"] == "Monthly", cur["bill_rate"] * 12,
                          cur["bill_rate"] * cur["hours_per_week"].fillna(0).astype(float) * 52)
        for cc, cur_g, ann in zip(cur["cost_center_code"], cur["billing_currency"], annual):
            a = actual.setdefault((qe, cc), {"headcount": 0, "annual_local": defaultdict(float)})
            a["headcount"] += 1
            a["annual_local"][cur_g] += float(ann)
    # cost centers with contingent workers but no employee plan line that year get one, with
    # zeros on the employee side, in every version covering the quarter
    first_q = {n: q for n, _, q in ref.PLAN_VERSIONS}
    versions = plan[["plan_version", "version_type", "version_date", "fiscal_year"]].drop_duplicates()
    have = set(zip(plan["plan_version"], plan["cost_center_id"], plan["quarter_end_date"]))
    quarter_of = dict(zip(plan["quarter_end_date"], plan["fiscal_quarter"]))
    fy_of = dict(zip(plan["quarter_end_date"], plan["fiscal_year"]))
    extra = []
    for (qe, cc) in sorted(actual):
        for v in versions[versions["fiscal_year"] == fy_of[qe]].itertuples(index=False):
            if quarter_of[qe] >= first_q[v.version_type] and (v.plan_version, cc, qe) not in have:
                extra.append({"plan_version": v.plan_version, "version_type": v.version_type,
                              "version_date": v.version_date, "fiscal_year": v.fiscal_year,
                              "fiscal_quarter": quarter_of[qe], "quarter_end_date": qe, "cost_center_id": cc,
                              "planned_ending_headcount": 0, "planned_ending_fte": 0.0, "planned_net_new": 0,
                              "planned_backfills": 0, "planned_cost_usd": 0.0, "plan_fx_rate_date": v.version_date})
    if extra:
        plan = pd.concat([plan, pd.DataFrame(extra)], ignore_index=True) \
            .sort_values(["fiscal_year", "version_date", "cost_center_id", "fiscal_quarter"]).reset_index(drop=True)
    hc_out, spend_out = [], []
    z_cc = {}
    for r in plan.itertuples(index=False):
        key = (r.plan_version, r.cost_center_id)
        if key not in z_cc:
            z_cc[key] = stream.normal()              # a cost center's planning bias in this version
        act = actual.get((r.quarter_end_date, r.cost_center_id))
        z_q = stream.normal()
        if not act:
            hc_out.append(0)
            spend_out.append(0.0)
            continue
        mu, sd = ref.PLAN_CW_ERROR[r.version_type]
        if r.version_type == "Budget":
            mu += ref.PLAN_CW_FY_BUDGET_SHIFT.get(r.fiscal_year, 0.0)
        horizon = r.fiscal_quarter - first_q[r.version_type] + 1
        hc = int(round(act["headcount"] * math.exp(mu + sd * math.sqrt(horizon) * (0.7 * z_cc[key] + 0.7 * z_q))))
        usd = sum(v * fx_rates.usd_per_local(c, max(r.version_date, FX_FIRST_DAY)) for c, v in act["annual_local"].items())
        usd *= (hc / act["headcount"]) * math.exp(stream.normal(0, ref.PLAN_CW_COST_EXTRA_SD))
        hc_out.append(hc)
        spend_out.append(round(usd, 2))
    plan = plan.copy()
    at = plan.columns.get_loc("planned_cost_usd") + 1
    plan.insert(at, "planned_cw_headcount", hc_out)
    plan.insert(at + 1, "planned_cw_spend_usd", spend_out)
    return plan


def simulate(*, hires: pd.DataFrame | None = None, conversion_stream: np.random.Generator | None = None,
             **kwargs) -> tuple[dict[str, pd.DataFrame], Program]:
    program = Program(**kwargs)
    program.run()
    program.conversions = {}
    if hires is not None:
        program.convert(hires, conversion_stream)
    return program.tables(), program
