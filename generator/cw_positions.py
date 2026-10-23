"""Contingent worker PIDs in Keystone HR (release 3.1).

Every contingent worker holds a PID in Keystone, Arcadia's HR system, exactly like an employee:

- **Recruiting creates or reuses the PID.** When a manager's request for a contingent worker is
  approved (the Bridgeway service order's approval date), HR Ops gives it a PID: a vacant
  contingent PID with the same department, office, worker type and role when one is reused,
  otherwise a **new PID**, created that day. Between approval and the first day the PID is vacant
  and new.
- **The worker fills it.** From the first day of the assignment to the last, the PID is Filled. The
  holder is the worker's Keystone person ID (Bridgeway's worker ID converted to an Arcadia ID
  when Keystone first heard of them). An assignment follows Bridgeway as held each day, the same
  rule as the month-end contingent headcount, so filled contingent PIDs equal that headcount on
  every month-end.
- **When the assignment ends the PID stays vacant.** It waits to be reused by the next contingent
  worker in the same role, or until the position audit (end of January and end of July) closes
  it. The audit closes only part of what it finds: a share of PIDs vacant for 180 days or more.
- **A worker returning after a lapse goes back to their own PID** when it is still vacant.

Bridgeway is untouched. This module reads its finished tables (and Keystone's person IDs) and
draws from its own random stream, so no number in any other table moves.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd

import reference_data as ref

ONE_DAY = dt.timedelta(days=1)
FAR = dt.date(9999, 12, 31)


def _d(x) -> dt.date | None:
    if x is None or (isinstance(x, float) and np.isnan(x)) or x == "" or pd.isna(x):
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _periods(rev: pd.DataFrame) -> dict[str, list[dict]]:
    """Per Bridgeway worker, the contiguous spans on which a revision in effect that day says the
    assignment has started and not ended (the int_cw_month_end_snapshot rule, day by day), with
    the attributes of each revision inside the span."""
    spans = defaultdict(list)
    for r in rev.itertuples(index=False):
        es, ee = _d(r.effective_start_date), _d(r.effective_end_date) or FAR
        a_s, a_e = _d(r.assignment_start_date), _d(r.assignment_end_date)
        lo, hi = max(es, a_s), min(ee, a_e)
        if lo <= hi:
            spans[r.bw_worker_id].append((lo, hi, r))
    out = {}
    for bw, rows in spans.items():
        rows.sort(key=lambda t: (t[0], t[1]))
        periods = []
        for lo, hi, r in rows:
            if periods and lo <= periods[-1]["end"] + ONE_DAY:
                p = periods[-1]
                p["end"] = max(p["end"], hi)
            else:
                p = {"start": lo, "end": hi, "revs": []}
                periods.append(p)
            p["revs"].append((lo, r))
        out[bw] = periods
    return out


class PidBook:
    def __init__(self, stream: np.random.Generator, extract: dt.date, start_number: int):
        self.rng, self.extract = stream, extract
        self.n_pid, self.n_assign = start_number, 0
        self.pids: dict[str, dict] = {}
        self.vacant: dict[tuple, dict[str, None]] = defaultdict(dict)   # key -> vacant, unreserved PIDs
        self.rows: list[dict] = []
        self.assign_rows: list[dict] = []

    # ------------------------------------------------------------------ PID history (SCD2)
    def write(self, p: dict, on: dt.date, reason: str):
        fields = {"status": p["status"], "department_id": p["dept"], "cost_center_id": p["cc"],
                  "location_id": p["loc"]}
        cur = p["row"]
        if cur is not None:
            if all(cur[k] == v for k, v in fields.items()):
                return
            if on == cur["effective_start_date"]:
                if cur["status"] != fields["status"]:
                    cur["change_reason"] = reason
                cur.update(fields)
                return
            cur["effective_end_date"] = on - ONE_DAY
        p["row"] = {"position_id": p["id"], "effective_start_date": on, "effective_end_date": None,
                    "change_reason": reason, **fields, "job_profile_id": None, "job_level": None, "fte": 1.0,
                    "created_date": p["created"], "created_reason": "Net-new", "worker_type": "Contingent",
                    "cw_type": p["key"][2], "cw_role_family": p["key"][3]}
        self.rows.append(p["row"])

    def new_pid(self, key: tuple, on: dt.date) -> dict:
        self.n_pid += 1
        dept, cc, loc = key[0], key[4], key[1]
        p = {"id": f"P{self.n_pid}", "key": key, "dept": dept, "cc": cc, "loc": loc, "status": "Open",
             "created": on, "row": None, "holder": None, "reserved": False, "vacant_since": on}
        self.pids[p["id"]] = p
        self.write(p, on, "Net-new")
        return p

    # ------------------------------------------------------------------ events
    def approve(self, period: dict, on: dt.date, last_pid: str | None):
        key = period["key"]
        p = self.pids.get(last_pid) if last_pid else None
        if p is not None and p["status"] == "Open" and not p["reserved"] and p["holder"] is None and p["key"] == key:
            pass                                             # a returning worker goes back to their own PID
        else:
            pool = self.vacant.get(key)
            p = None
            if pool and self.rng.random() < ref.CW_PID_REUSE_SHARE:
                p = min((self.pids[i] for i in pool), key=lambda x: (x["vacant_since"], x["id"]))
            if p is None:
                p = self.new_pid(key, on)
        p["reserved"] = True
        self.vacant[key].pop(p["id"], None)
        period["pid"] = p["id"]

    def start(self, period: dict, person_id: str | None, bw: str):
        p = self.pids[period["pid"]]
        p.update(status="Filled", holder=bw, reserved=False)
        on = period["start"]
        self.write(p, on, "Filled")
        self.n_assign += 1
        period["assign"] = {"assignment_id": f"PC{self.n_assign:07d}", "position_id": p["id"],
                            "worker_id": person_id, "start_date": on, "end_date": None,
                            "fill_type": "Contingent Assignment", "requisition_id": period["order"],
                            "vacate_reason": None, "worker_type": "Contingent", "bw_worker_id": bw}
        self.assign_rows.append(period["assign"])
        for day, attrs in period["changes"]:               # the PID follows the order's cost center and office
            p.update(dept=attrs[0], cc=attrs[1], loc=attrs[2])
            if day <= self.extract:
                self.write(p, day, "Job change with incumbent")
        p["key"] = (p["dept"], p["loc"], p["key"][2], p["key"][3], p["cc"])

    def end(self, period: dict, reason: str):
        p = self.pids[period["pid"]]
        period["assign"].update(end_date=period["end"], vacate_reason=reason)
        p.update(status="Open", holder=None, reserved=False, vacant_since=period["end"] + ONE_DAY)
        self.write(p, period["end"] + ONE_DAY, "Vacated")
        self.vacant[p["key"]][p["id"]] = None

    def audit(self, on: dt.date):
        for key, pool in self.vacant.items():
            for pid in list(pool):
                p = self.pids[pid]
                if (on - p["vacant_since"]).days >= ref.CW_PID_AUDIT_MIN_DAYS \
                        and self.rng.random() < ref.CW_PID_AUDIT_CLOSE_SHARE:
                    p["status"] = "Eliminated"
                    self.write(p, on + ONE_DAY, "Closed by position audit")
                    del pool[pid]


def build(*, stream: np.random.Generator, tables: dict[str, pd.DataFrame], program, cost_centers: list[dict],
          start_number: int) -> tuple[list[dict], list[dict]]:
    """Contingent PIDs (dim_position rows) and assignments (fact_position_assignment rows)."""
    extract = dt.date.fromisoformat(ref.CW_EXTRACT_DATE)
    cc_dept = {c["cost_center_id"]: c["department_id"] for c in cost_centers}
    rev = tables["bw_service_order_revision"]
    rev = rev[rev["status"].isin(["Approved", "Closed"])]
    orders = tables["bw_service_order"].set_index("service_order_id")
    rev = rev.merge(orders[["bw_worker_id"]], left_on="service_order_id", right_index=True)
    cw_type = dict(zip(tables["bw_contingent_worker"]["bw_worker_id"], tables["bw_contingent_worker"]["cw_type"]))
    ks = tables["ks_contingent_worker"]
    person = ks.dropna(subset=["bw_worker_id"]).sort_values("effective_start_date") \
               .drop_duplicates("bw_worker_id").set_index("bw_worker_id")["person_id"].to_dict()
    end_reason = defaultdict(dict)
    for e in program.engagements:
        end_reason[e.bw_worker_id][e.end] = e.end_reason

    book = PidBook(stream, extract, start_number)
    events = []
    all_periods = _periods(rev)
    for bw, periods in sorted(all_periods.items()):
        for k, p in enumerate(periods):
            first = p["revs"][0][1]
            attrs = lambda r: (cc_dept[r.cost_center_code], r.cost_center_code, r.office_code)
            a0 = attrs(first)
            p["key"] = (a0[0], a0[2], cw_type[bw], first.role_family, a0[1])
            p["order"] = first.service_order_id
            p["changes"], last = [], a0
            for day, r in p["revs"][1:]:
                a = attrs(r)
                if a != last:
                    p["changes"].append((max(day, p["start"]), a))
                    last = a
            approved = _d(orders.at[first.service_order_id, "approved_date"]) or p["start"]
            if k > 0 and approved <= periods[k - 1]["end"]:   # a late extension or return on an old order
                approved = p["start"]
            approved = min(approved, p["start"])
            p["bw"] = bw
            if approved > extract:
                continue
            events.append((approved, 1, bw, k, "approve"))
            if p["start"] <= extract:
                events.append((p["start"], 2, bw, k, "start"))
                if p["end"] < extract:
                    events.append((p["end"] + ONE_DAY, 0, bw, k, "end"))
    first_day = min(e[0] for e in events)
    y = first_day.year
    while dt.date(y, 1, 31) <= extract:
        for m in ref.CW_PID_AUDIT_MONTHS:
            day = (dt.date(y, m, 28) + dt.timedelta(days=4)).replace(day=1) - ONE_DAY
            if first_day <= day <= extract:
                events.append((day, 3, "", 0, "audit"))
        y += 1
    events.sort(key=lambda e: (e[0], e[1], e[2], e[3]))

    last_pid: dict[str, str] = {}
    for day, _, bw, k, kind in events:
        if kind == "audit":
            book.audit(day)
            continue
        p = all_periods[bw][k]
        if kind == "approve":
            book.approve(p, day, last_pid.get(bw))
        elif kind == "start":
            book.start(p, person.get(bw), bw)
            last_pid[bw] = p["pid"]
        else:
            reason = {"Converted": "Converted to employee", "Ended early": "Ended early",
                      "Restructuring": "Ended early"}.get(end_reason[bw].get(p["end"]), "Contract ended")
            book.end(p, reason)
    return book.rows, book.assign_rows
