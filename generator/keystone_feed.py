"""
Keystone HR's view of the contingent workforce, the Bridgeway -> Keystone feed, and the
answer key of every discrepancy between the two (warehouse release 3, phase 4).

Bridgeway VMS is the source of truth for contingent workers (phase 3). Keystone HR is where
managers look: it holds a person record for each contingent worker, written by a one-way
feed from Bridgeway, and edited by hand by managers and HR Operations. This module
simulates that and returns:

    feed_bridgeway_keystone_event   every change Bridgeway sent, when it was applied, or that it failed
    ks_contingent_worker            Keystone's effective-dated person record (SCD Type 2)
    gen_cw_discrepancy_truth        the answer key: every discrepancy, its cause and its dates
    ref_cw_discrepancy_type         the catalogue of discrepancy types (warehouse metadata)

and Bridgeway's tables with three of its own hygiene problems seeded:
    * some ended orders are closed late, or never (CW04)
    * some ended orders bill time in the month after the last day (CW11)
    * some renewals were submitted as a new worker: a second Bridgeway ID for the same person (CW07)

How the feed works
  * One event per Bridgeway revision that Keystone cares about: New Worker and Renewal
    (revision 0 of an approved order), Extension, Early End, Attribute Change (cost center,
    manager, office). Rate changes and closures are not sent: Keystone holds no rates.
  * The event's payload is its revision: New Worker carries the contract start and end and
    the attributes; Renewal, Extension and Early End carry the new end date and the
    attributes (Keystone's contract start stays the worker's first day); Attribute Change
    carries the attributes only.
    Any event that is applied leaves Keystone matching Bridgeway for what it carries.
  * Keystone finds the person by the Bridgeway ID it stored. If that is blank or mistyped,
    or the record was never created, the event fails ("Worker not found").
  * Events for one worker are applied first in, first out: a late event holds up the ones
    behind it, so an older change never overwrites a newer one.
  * Keystone inactivates a contingent worker the day after the contract end date it holds.

How the answer key is built
  Each Bridgeway worker's Keystone record is replayed twice: an ideal replay (every event
  applied the day it is sent, nothing failing, nobody editing by hand) and the real one.
  Wherever the two disagree on a day when either shows the worker active, that is a
  discrepancy; its cause is the seeded action that made them diverge. Bridgeway-only
  problems (CW04, CW10, CW11), the second-ID cases (CW07) and the Keystone-only workers
  (CW09) are recorded directly. The key is what the warehouse's detection is scored against.

It draws from its own random stream, after the Bridgeway simulation, so nothing upstream moves.
Arcadia Systems, Keystone HR, Bridgeway VMS and every person here are fictional.
"""

from __future__ import annotations

import bisect
import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd

import reference_data as ref
from contingent_workforce import ONE_DAY, add_months, month_end, money

CONTRACT = ("status", "contract_start_date", "contract_end_date")
GROUP_FIELDS = {"contract": CONTRACT, "cost_center": ("department_id", "cost_center_id"),
                "manager": ("manager_worker_id",), "office": ("location_id",)}
GROUP_LABEL = {"record": "Whole record", "link": "Bridgeway worker ID", "contract": "Status and contract dates",
               "cost_center": "Cost center", "manager": "Manager", "office": "Office"}
OUT_FIELDS = ["bw_worker_id", "first_name", "last_name", "cw_type", "supplier_name", "status",
              "contract_start_date", "contract_end_date", "inactive_reason", "department_id",
              "cost_center_id", "location_id", "manager_worker_id"]
ATTR_FIELDS = ("department_id", "cost_center_id", "location_id", "manager_worker_id")

EVENT_OF_REASON = {"Extension": "Extension", "Early end": "Early End", "Cost center change": "Attribute Change",
                   "Manager change": "Attribute Change", "Office change": "Attribute Change"}
FAIL_CODE = {"New Worker": "CW08", "Renewal": "CW02", "Extension": "CW02", "Early End": "CW03",
             "Attribute Change": "CW12"}

# code, name, what happened, what a manager in Keystone sees, who can fix it, severity
DISCREPANCY_TYPES = [
    ("CW00", "Change in transit", "Bridgeway sent a change in the last two days that Keystone has not applied yet",
     "Yesterday's values", "Nobody: it clears itself", "Expected"),
    ("CW01", "Change arrived late", "The feed applied a change 3 or more days after Bridgeway sent it, or it is still queued",
     "An old end date, cost center, manager or office for days", "Integration support", "Data hygiene"),
    ("CW02", "Extension never arrived", "An extension or renewal failed on the feed",
     "Keystone ends the worker at the old end date while Bridgeway has them working", "Integration support, then HR Ops", "Access risk"),
    ("CW03", "Early end never arrived", "An early end failed on the feed",
     "The worker is still active in Keystone after their last day", "HR Ops", "Access risk"),
    ("CW04", "Ended but not closed in Bridgeway", "The order is still open more than 15 days after the worker's last day",
     "Nothing: Bridgeway hygiene", "Vendor management", "Cost risk"),
    ("CW05", "Changed in Keystone only", "A manager or HR Ops changed the cost center, manager or office in Keystone, not in Bridgeway",
     "Values Bridgeway does not have; the supplier still bills Bridgeway's cost center", "The manager, in Bridgeway", "Cost risk"),
    ("CW06", "Link ID missing or mistyped", "Keystone holds a blank or wrong Bridgeway worker ID",
     "Nothing, but later feed changes cannot find the worker", "HR Ops", "Data hygiene"),
    ("CW07", "One person, two IDs", "A renewal was submitted as a new worker: a second Bridgeway ID and a second Keystone person",
     "The same person twice", "HR Ops and vendor management", "Data hygiene"),
    ("CW08", "Never reached Keystone", "The new-worker event failed, so Keystone has no record",
     "A worker missing from the team", "Integration support, then HR Ops", "Access risk"),
    ("CW09", "Keystone-only contingent worker", "Someone created a contingent worker by hand in Keystone with no Bridgeway order",
     "A worker no supplier bills for", "HR Ops", "Access risk"),
    ("CW10", "Over the duration cap", "A Contractor or Consultant engagement runs past 48 months",
     "Nothing", "Vendor management and the hiring manager", "Compliance risk"),
    ("CW11", "Billed after the assignment ended", "Time billed in a month after the worker's last day",
     "Nothing: rates and timesheets are not in Keystone", "Vendor management and Finance", "Cost risk"),
    ("CW12", "Attribute change never arrived", "A cost center, manager or office change failed on the feed",
     "The old cost center, manager or office", "Integration support, then HR Ops", "Data hygiene"),
]


# ======================================================================================
# A Keystone person record, replayed through time
# ======================================================================================
def _same(a: dict | None, b: dict | None) -> bool:
    if a is None or b is None:
        return a is b
    return all(a.get(k) == b.get(k) for k in OUT_FIELDS)


class Record:
    """One Keystone person record: its current state and its versions, one per day."""

    def __init__(self):
        self.state: dict | None = None
        self.versions: list[tuple[dt.date, dict, str, str | None]] = []   # (date, state, source, feed event)

    def push(self, d: dt.date, st: dict, source: str, fe: str | None):
        if self.versions and d < self.versions[-1][0]:
            d = self.versions[-1][0]
        if self.versions and self.versions[-1][0] == d:          # one version per day: the day's last state
            self.versions[-1] = (d, st, source, fe)
            if len(self.versions) > 1 and _same(self.versions[-2][1], st):
                self.versions.pop()
        elif not self.versions or not _same(self.versions[-1][1], st):
            self.versions.append((d, st, source, fe))
        self.state = st

    def advance(self, d: dt.date):
        """Keystone inactivates the worker the day after the contract end date it holds."""
        s = self.state
        if s and s["status"] == "Active" and s["contract_end_date"] + ONE_DAY <= d:
            self.push(s["contract_end_date"] + ONE_DAY,
                      dict(s, status="Inactive", inactive_reason=s["_end_kind"]), "System", None)

    def apply(self, d: dt.date, payload: dict, contract: bool, end_kind: str, source: str, fe: str | None):
        self.advance(d)
        st = dict(self.state or {})
        st.update(payload)
        if contract:
            st["_end_kind"] = end_kind
            if st["contract_end_date"] >= d:
                st["status"], st["inactive_reason"] = "Active", None
            else:
                st["status"], st["inactive_reason"] = "Inactive", end_kind
        self.push(d, st, source, fe)

    def at(self, d: dt.date) -> dict | None:
        i = bisect.bisect_right(self._dates, d) - 1
        return self.versions[i][1] if i >= 0 else None

    def freeze(self):
        self._dates = [v[0] for v in self.versions]


def _active(st: dict | None) -> bool:
    return bool(st) and st["status"] == "Active"


def _working(st: dict | None, d: dt.date) -> bool:
    """Active in Keystone and past the contract start: someone who should be working that day."""
    return _active(st) and st["contract_start_date"] <= d


def _groups(st: dict) -> dict:
    return {g: tuple(st.get(f) for f in fs) for g, fs in GROUP_FIELDS.items()}


# ======================================================================================
# The simulation
# ======================================================================================
class Keystone:
    def __init__(self, *, stream: np.random.Generator, bw: dict[str, pd.DataFrame], program, cost_centers: list[dict]):
        self.rng = stream
        self.bw = {k: v.copy() for k, v in bw.items()}
        self.p = program
        self.extract = program.extract
        self.keep_from = dt.date.fromisoformat(ref.KS_HISTORY_KEEP_FROM)
        self.cc_dept = {c["cost_center_id"]: c["department_id"] for c in cost_centers}
        self.cc_country = {c["cost_center_id"]: c["country_code"] for c in cost_centers}
        self.email_worker = {v: k for k, v in program.emp_email.items()}
        self.supplier_name = dict(zip(self.bw["bw_supplier"]["supplier_id"], self.bw["bw_supplier"]["supplier_name"]))
        self.truth: list[dict] = []
        self.marker_seq = 0

    # ---------------------------------------------------------------- small helpers
    def pick(self, options: list):
        return options[int(self.rng.integers(len(options)))]

    def days(self, lo_hi: tuple[int, int]) -> dt.timedelta:
        return dt.timedelta(days=int(self.rng.integers(lo_hi[0], lo_hi[1] + 1)))

    def manager_in(self, dept: str, country: str, on: dt.date, other_than: str | None = None) -> str | None:
        wid, start, end, _, ctry = self.p.mgr_by_dept[dept]
        o = on.toordinal()
        live = np.flatnonzero((start <= o) & (end >= o) & (wid != other_than))
        same = live[ctry[live] == country]
        pool = same if len(same) else live
        return str(wid[pool[int(self.rng.integers(len(pool)))]]) if len(pool) else None

    def supplier_variant(self, name: str) -> str:
        return self.pick(ref.KS_SUPPLIER_VARIANTS[name]) if self.rng.random() < ref.KS_MANUAL_SUPPLIER_VARIANT else name

    def typo(self, bw_id: str) -> str:
        """A transposed pair of digits, as typed by hand."""
        digits = list(bw_id[2:])
        for _ in range(10):
            i = int(self.rng.integers(len(digits) - 1))
            if digits[i] != digits[i + 1]:
                digits[i], digits[i + 1] = digits[i + 1], digits[i]
                return "BW" + "".join(digits)
        return "BW" + "".join(digits[:-1])          # all digits equal: one dropped instead

    def add_truth(self, code: str, *, root: str | None = None, bw_worker_id=None, person=None,
                  service_order_id=None, feed_event=None, timesheet_id=None, fields="", start, end, resolution, detail):
        if end is not None and end < self.keep_from:
            return
        self.truth.append({"discrepancy_code": code, "root_cause_code": root or code, "bw_worker_id": bw_worker_id,
                           "person_key": person, "service_order_id": service_order_id, "feed_event_key": feed_event,
                           "timesheet_id": timesheet_id, "fields_affected": fields, "start_date": start,
                           "end_date": end, "resolution": resolution, "detail": detail})

    # ---------------------------------------------------------------- 1. Bridgeway hygiene
    def split_renewals(self):
        """CW07: a few renewals were submitted by the supplier as a brand new worker."""
        so, rev, wk = self.bw["bw_service_order"], self.bw["bw_service_order_revision"], self.bw["bw_contingent_worker"]
        rev0 = rev[rev["revision_no"] == 0].set_index("service_order_id")
        breach = {e.bw_worker_id for e in self.p.engagements if e.cap_breach}
        cand = so[(so["order_type"] == "Renewal") & so["approved_date"].notna()].sort_values("service_order_id")
        chosen, seen = [], set()
        for o in cand.itertuples(index=False):
            draw = self.rng.random()
            start = rev0.at[o.service_order_id, "assignment_start_date"]
            if (draw < ref.BW_SPLIT_RENEWAL_SHARE and o.bw_worker_id not in seen and o.bw_worker_id not in breach
                    and o.approved_date < start):
                chosen.append((o, start))
                seen.add(o.bw_worker_id)
        self.splits = []
        next_no = int(wk["bw_worker_id"].str[2:].astype(int).max())
        new_rows = []
        for o, start in chosen:
            next_no += 1
            new_id = f"BW{next_no:08d}"
            old = wk[wk["bw_worker_id"] == o.bw_worker_id].iloc[0].to_dict()
            base = old["email"].split("@")[0].rstrip("0123456789")
            self.p.cw_email_seen[base] += 1
            n = self.p.cw_email_seen[base]
            new_rows.append(dict(old, bw_worker_id=new_id, email=f"{base}{n}@{ref.CW_EMAIL_DOMAIN}",
                                 original_start_date=start, created_date=o.submitted_date))
            moving = so[(so["bw_worker_id"] == o.bw_worker_id) & (so["opened_date"] >= o.opened_date)]["service_order_id"]
            so.loc[so["service_order_id"].isin(moving), "bw_worker_id"] = new_id
            ts = self.bw["bw_timesheet_month"]
            ts.loc[ts["service_order_id"].isin(moving), "bw_worker_id"] = new_id
            so.loc[so["service_order_id"] == o.service_order_id, ["order_type", "renews_service_order_id"]] = \
                ["New engagement", None]
            self.splits.append((o.bw_worker_id, new_id, o.service_order_id, start))
        self.bw["bw_contingent_worker"] = pd.concat([wk, pd.DataFrame(new_rows)], ignore_index=True) \
            .sort_values("bw_worker_id").reset_index(drop=True)

    def slow_closures(self):
        """CW04: some ended orders are closed late, or are still open on the extract date."""
        rev, so = self.bw["bw_service_order_revision"], self.bw["bw_service_order"]
        rev = rev.sort_values(["service_order_id", "revision_no"]).reset_index(drop=True)
        closures = rev.index[rev["revision_reason"] == "Closure"]
        draws = self.rng.random(len(closures))
        drop, status_of = [], {}
        self.slow = []
        for i, draw in zip(closures, draws):
            if draw >= ref.BW_SLOW_CLOSURE_SHARE:
                continue
            last_day = rev.at[i, "assignment_end_date"]
            closed = last_day + self.days(ref.BW_SLOW_CLOSURE_DAYS)
            prev = i - 1
            if closed > self.extract:
                drop.append(i)
                rev.at[prev, "effective_end_date"], rev.at[prev, "is_current"] = None, True
                status_of[rev.at[i, "service_order_id"]] = rev.at[prev, "status"]
                closed = None
            else:
                rev.at[i, "effective_start_date"], rev.at[i, "closed_date"] = closed, closed
                rev.at[prev, "effective_end_date"] = closed - ONE_DAY
            self.slow.append((rev.at[i, "service_order_id"], last_day, closed))
        self.bw["bw_service_order_revision"] = rev.drop(index=drop).sort_values("revision_id").reset_index(drop=True)
        for o, st in status_of.items():
            so.loc[so["service_order_id"] == o, "final_status"] = st

    def billed_after_end(self):
        """CW11: a few ended orders bill time in the month after the worker's last day."""
        rev, ts = self.bw["bw_service_order_revision"], self.bw["bw_timesheet_month"]
        cur = rev[rev["is_current"] & rev["status"].isin(["Approved", "Closed"])].sort_values("service_order_id")
        last_ts = ts.sort_values("timesheet_id").groupby("service_order_id").tail(1).set_index("service_order_id")
        hist = dt.date.fromisoformat(ref.FIRST_SNAPSHOT)
        rows, n = [], int(ts["timesheet_id"].str[2:].astype(int).max())
        self.after_end = []
        for r in cur.itertuples(index=False):
            draw = self.rng.random()
            end = r.assignment_end_date
            nxt = month_end((end + dt.timedelta(days=32 - end.day)).year, (end + dt.timedelta(days=32 - end.day)).month)
            if draw >= ref.BW_BILLED_AFTER_END_SHARE or end < hist or nxt > self.extract \
                    or r.service_order_id not in last_ts.index:
                continue
            last = last_ts.loc[r.service_order_id]
            if r.rate_type == "Monthly":
                units, hours = round(float(self.rng.uniform(0.2, 1.0)), 4), 0.0
            else:
                hours = float(self.rng.integers(8, 41)) + float(self.rng.integers(0, 4)) / 4
                units = hours
            n += 1
            tid = f"TS{n:09d}"
            rows.append({"timesheet_id": tid, "bw_worker_id": last["bw_worker_id"], "service_order_id": r.service_order_id,
                         "month_end_date": nxt, "billed_hours": hours, "billed_units": units,
                         "bill_rate": last["bill_rate"], "billing_currency": last["billing_currency"],
                         "billed_amount_local": money(units, float(last["bill_rate"]))})
            self.after_end.append((tid, last["bw_worker_id"], r.service_order_id, end, nxt))
        self.bw["bw_timesheet_month"] = pd.concat([ts, pd.DataFrame(rows)], ignore_index=True)

    # ---------------------------------------------------------------- 2. the feed
    def build_events(self):
        rev = self.bw["bw_service_order_revision"]
        so = self.bw["bw_service_order"].set_index("service_order_id")
        wk = self.bw["bw_contingent_worker"].set_index("bw_worker_id")
        events = defaultdict(list)
        for r in rev.sort_values(["service_order_id", "revision_no"]).itertuples(index=False):
            if r.status not in ("Approved", "Closed"):
                continue
            if r.revision_no == 0:
                etype = "New Worker" if so.at[r.service_order_id, "order_type"] == "New engagement" else "Renewal"
            else:
                etype = EVENT_OF_REASON.get(r.revision_reason)
                if etype is None:
                    continue
            bw_id = so.at[r.service_order_id, "bw_worker_id"]
            payload = {"department_id": self.cc_dept[r.cost_center_code], "cost_center_id": r.cost_center_code,
                       "location_id": r.office_code, "manager_worker_id": self.email_worker[r.hiring_manager_email]}
            contract = etype != "Attribute Change"
            if contract:                       # a renewal or extension moves the end; only a new worker sets the start
                payload["contract_end_date"] = r.assignment_end_date
            if etype == "New Worker":
                payload["contract_start_date"] = r.assignment_start_date
                w = wk.loc[bw_id]
                payload.update(bw_worker_id=bw_id, first_name=w["first_name"], last_name=w["last_name"],
                               cw_type=w["cw_type"], supplier_name=self.supplier_name[w["supplier_id"]])
            events[bw_id].append({"revision_id": r.revision_id, "service_order_id": r.service_order_id,
                                  "bw_worker_id": bw_id, "event_type": etype, "sent": r.effective_start_date,
                                  "payload": payload, "contract": contract,
                                  "end_kind": "Ended early" if etype == "Early End" else "Contract ended"})
        self.events = {}
        for bw_id in sorted(events):
            evs = sorted(events[bw_id], key=lambda e: (e["sent"], e["event_type"] != "New Worker", e["revision_id"]))
            if evs[0]["event_type"] != "New Worker":     # the worker's first order was archived: its renewal creates the record
                evs[0]["event_type"] = "New Worker"
                w = wk.loc[bw_id]
                first_rev = rev[rev["revision_id"] == evs[0]["revision_id"]].iloc[0]
                evs[0]["payload"].update(bw_worker_id=bw_id, contract_start_date=first_rev["assignment_start_date"], first_name=w["first_name"], last_name=w["last_name"],
                                         cw_type=w["cw_type"], supplier_name=self.supplier_name[w["supplier_id"]])
            self.events[bw_id] = evs

    def draw_outcomes(self, evs: list[dict]):
        """Lag, failure or partial load for each event; first in, first out per worker."""
        prev_applied = None
        for ev in evs:
            ev["fail"] = self.rng.random() < ref.FEED_FAIL[ev["event_type"]]
            ev["partial"] = ev["event_type"] == "New Worker" and not ev["fail"] and self.rng.random() < ref.FEED_PARTIAL_LINK
            r = self.rng.random()
            acc, lag = 0.0, None
            for k, p in ref.FEED_LAG_DAYS.items():
                acc += p
                if r < acc:
                    lag = k
                    break
            if lag is None:
                lag = int(self.rng.integers(ref.FEED_LATE_DAYS[0], ref.FEED_LATE_DAYS[1] + 1))
            ev["error"] = self.pick(["timeout", "validation", "mapping"]) if ev["fail"] else None
            if ev["fail"]:
                ev["applied"] = None
                continue
            applied = ev["sent"] + dt.timedelta(days=lag)
            if prev_applied and applied < prev_applied:
                applied = prev_applied                    # queued behind an earlier, slower event
            ev["applied"] = applied
            prev_applied = applied

    # ---------------------------------------------------------------- 3. replays
    def replay_ideal(self, evs: list[dict]) -> Record:
        rec = Record()
        for ev in evs:
            before = rec.state
            if ev["event_type"] == "New Worker" and before is None:
                rec.apply(ev["sent"], ev["payload"], True, ev["end_kind"], "Feed", None)
                ev["groups"] = {"record", "link", "contract", "cost_center", "manager", "office"}
            else:
                rec.advance(ev["sent"])
                g0 = _groups(rec.state)
                rec.apply(ev["sent"], ev["payload"], ev["contract"], ev["end_kind"], "Feed", None)
                g1 = _groups(rec.state)
                ev["groups"] = {g for g in g0 if g0[g] != g1[g]} or ({"contract"} if ev["contract"] else {"manager"})
        rec.advance(self.extract)
        rec.freeze()
        return rec

    def replay_actual(self, bw_id: str, evs: list[dict], ideal: Record) -> tuple[Record, list]:
        rec = Record()
        markers = []                        # (date, groups, code, root, marker key, event)

        def mark(d, groups, code, root=None, ev=None):
            self.marker_seq += 1
            markers.append((d, set(groups), code, root or code, self.marker_seq, ev))

        actions = []                        # (date, order, seq, kind, data)
        for i, ev in enumerate(evs):
            if ev["applied"] is not None and ev["applied"] <= self.extract:
                actions.append((ev["applied"], 0, i, "event", ev))
            elif ev["fail"]:
                fix_p, delay = ref.KS_FIX[_fix_name(FAIL_CODE[ev["event_type"]])]
                if self.rng.random() < fix_p:
                    kind = "create" if ev["event_type"] == "New Worker" else "resync"
                    actions.append((ev["sent"] + self.days(delay), 1, i, kind, ev))
        # hand edits in Keystone while the worker is active
        first = evs[0]["sent"]
        last = min(ideal.versions[-1][0] if ideal.versions[-1][1]["status"] == "Inactive" else self.extract, self.extract)
        months = []
        d = month_end(first.year, first.month)
        while d <= month_end(last.year, last.month):
            months.append(d)
            d = month_end((d + ONE_DAY).year, (d + ONE_DAY).month)
        kinds = list(ref.KS_LOCAL_EDIT_MONTHLY.items())
        draws = self.rng.random((len(months), len(kinds)))
        for m, me in enumerate(months):
            for k, (kind, p) in enumerate(kinds):
                if draws[m, k] < p:
                    on = dt.date(me.year, me.month, 1) + dt.timedelta(days=int(self.rng.integers(0, me.day)))
                    if first < on <= self.extract:
                        actions.append((on, 2, len(actions), "edit", kind))
        actions.sort(key=lambda a: (a[0], a[1], a[2]))

        k = 0
        while k < len(actions):
            when, _, _, kind, data = actions[k]
            k += 1
            if when > self.extract:
                break
            st = rec.state
            if kind == "event":
                ev = data
                if ev["event_type"] == "New Worker" and st is None:
                    payload = dict(ev["payload"])
                    if ev["partial"]:
                        payload["bw_worker_id"] = None
                        mark(when, {"link"}, "CW06")
                        fix_p, delay = ref.KS_FIX["Link ID missing or mistyped"]
                        if self.rng.random() < fix_p:
                            actions.append((when + self.days(delay), 1, len(actions), "relink", ev))
                            actions.sort(key=lambda a: (a[0], a[1], a[2]))
                    rec.apply(when, payload, True, ev["end_kind"], "Feed", ev["key"])
                    ev["outcome"] = "Partly Applied" if ev["partial"] else None
                elif st is None or st.get("bw_worker_id") != bw_id:
                    ev["not_found"] = "CW08" if st is None else "CW06"
                    ev["applied"] = None
                else:
                    rec.apply(when, ev["payload"], ev["contract"], ev["end_kind"], "Feed", ev["key"])
            elif kind in ("create", "resync", "relink"):
                target = ideal.at(when)
                if kind == "create":
                    if st is not None or not _active(target):
                        continue
                    payload = {f: target.get(f) for f in OUT_FIELDS}
                    payload["supplier_name"] = self.supplier_variant(target["supplier_name"])
                    if self.rng.random() < ref.KS_MANUAL_LINK_TYPO:
                        payload["bw_worker_id"] = self.typo(bw_id)
                        mark(when, {"link"}, "CW06")
                        fix_p, delay = ref.KS_FIX["Link ID missing or mistyped"]
                        if self.rng.random() < fix_p:
                            actions.append((when + self.days(delay), 1, len(actions), "relink", data))
                            actions.sort(key=lambda a: (a[0], a[1], a[2]))
                    rec.advance(when)
                    payload["_end_kind"] = target["_end_kind"]
                    rec.push(when, payload, "HR Ops", None)
                    continue
                if st is None:
                    continue
                rec.advance(when)
                payload = {f: target.get(f) for f in CONTRACT + ATTR_FIELDS + ("inactive_reason",)}
                payload["_end_kind"] = target["_end_kind"]
                if kind == "relink":
                    payload["bw_worker_id"] = bw_id
                rec.push(when, dict(rec.state, **payload), "HR Ops", None)
            elif kind == "edit":
                rec.advance(when)
                st = rec.state
                if not _active(st) or when > st["contract_end_date"]:
                    continue
                new = dict(st)
                ctry = self.cc_country[st["cost_center_id"]]
                if data == "Cost center":
                    depts = sorted(d for (d, c) in self.p.cc if c == ctry and d != st["department_id"]
                                   and d in self.p.mgr_by_dept and d != "D-901")
                    if not depts:
                        continue
                    dept = self.pick(depts)
                    mgr = self.manager_in(dept, ctry, when)
                    if mgr is None:
                        continue
                    new.update(department_id=dept, cost_center_id=self.p.cc[(dept, ctry)], manager_worker_id=mgr)
                    groups = {"cost_center", "manager"}
                elif data == "Manager":
                    mgr = self.manager_in(st["department_id"], ctry, when, other_than=st["manager_worker_id"])
                    if mgr is None:
                        continue
                    new["manager_worker_id"] = mgr
                    groups = {"manager"}
                else:
                    offices = sorted(o for o, v in self.p.office.items()
                                     if v["country"] == ctry and v["opened"] <= when and o != st["location_id"])
                    if not offices:
                        continue
                    new["location_id"] = self.pick(offices)
                    groups = {"office"}
                source = "Manager" if self.rng.random() < ref.KS_LOCAL_EDIT_BY_MANAGER else "HR Ops"
                mark(when, groups, "CW05")
                rec.push(when, new, source, None)
        rec.advance(self.extract)
        rec.freeze()

        # markers for every event that did not land the day it was sent
        for ev in evs:
            if ev["fail"]:
                code = FAIL_CODE[ev["event_type"]]
                mark(ev["sent"], {"record"} if code == "CW08" else ev["groups"], code, ev=ev)
            elif ev.get("not_found"):
                mark(ev["sent"], ev["groups"], FAIL_CODE[ev["event_type"]], root=ev["not_found"], ev=ev)
            else:
                lag = ((ev["applied"] if ev["applied"] <= self.extract else self.extract + ONE_DAY) - ev["sent"]).days
                if lag > 0:
                    mark(ev["sent"], ev["groups"], "CW00" if lag <= 2 and ev["applied"] <= self.extract else "CW01", ev=ev)
        return rec, markers

    # ---------------------------------------------------------------- 4. the answer key
    def compare(self, bw_id: str, ideal: Record, actual: Record, markers: list):
        by_group = defaultdict(list)
        for m in sorted(markers, key=lambda m: (m[0], m[4])):
            for g in m[1]:
                by_group[g].append(m)
        mdates = {g: [m[0] for m in ms] for g, ms in by_group.items()}
        points = sorted({v[0] for v in ideal.versions} | {v[0] for v in actual.versions}
                        | {v[1]["contract_start_date"] for v in ideal.versions + actual.versions}
                        | {m[0] for m in markers})
        points = [p for p in points if p <= self.extract] + [self.extract + ONE_DAY]
        spans = defaultdict(list)         # marker key -> [(start, end, group)]
        unexplained = 0
        for a, b in zip(points, points[1:]):
            i, s = ideal.at(a), actual.at(a)
            if not (_working(i, a) or _working(s, a)):
                continue
            diffs = []
            if i is not None and s is None:
                diffs = ["record"]
            elif s is not None and i is not None:
                if s.get("bw_worker_id") != bw_id:
                    diffs.append("link")
                gi, gs = _groups(i), _groups(s)
                diffs += [g for g in GROUP_FIELDS if gi[g] != gs[g]]
            for g in diffs:
                j = bisect.bisect_right(mdates.get(g, []), a) - 1
                if j < 0:
                    unexplained += 1
                    continue
                spans[by_group[g][j][4]].append((a, b - ONE_DAY, g))
        self.unexplained += unexplained
        person = id(actual) if actual.versions else None
        marker = {m[4]: m for m in markers}
        for key, sp in spans.items():
            m = marker[key]
            sp.sort()
            runs = []
            for a, b, g in sp:
                if runs and a <= runs[-1][1] + ONE_DAY:
                    runs[-1][1] = max(runs[-1][1], b)
                    runs[-1][2].add(g)
                else:
                    runs.append([a, b, {g}])
            d, groups, code, root, key, ev = m
            for a, b, gs in runs:
                end = None if b >= self.extract else b
                self.add_truth(code, root=root, bw_worker_id=bw_id, person=person,
                               service_order_id=ev["service_order_id"] if ev else None,
                               feed_event=ev["key"] if ev else None,
                               fields="; ".join(GROUP_LABEL[g] for g in GROUP_LABEL if g in gs),
                               start=a, end=end, resolution=self.resolution(code, end, ideal, actual),
                               detail=self.detail(code, root, ev, a))

    def resolution(self, code: str, end, ideal: Record, actual: Record) -> str:
        if end is None:
            return "Open at extract"
        nxt = end + ONE_DAY
        if code in ("CW00", "CW01"):
            return "Applied in Keystone"
        changed = [v for v in actual.versions if v[0] == nxt]
        if changed and changed[0][2] == "HR Ops":
            return "Fixed by hand in Keystone"
        if changed and changed[0][2] == "Feed":
            return "Overwritten by a later feed event"
        if not (_working(ideal.at(nxt), nxt) or _working(actual.at(nxt), nxt)):
            return "Worker no longer active"
        if any(v[0] == nxt for v in ideal.versions):
            return "Bridgeway changed to match"
        return "Systems realigned"

    def detail(self, code, root, ev, start) -> str:
        if ev is None:
            return {"CW05": "Changed by hand in Keystone", "CW06": "Keystone stored a blank or mistyped Bridgeway worker ID",
                    "CW08": "No Keystone record"}.get(code, "")
        what = f"{ev['event_type']} sent {ev['sent']:%Y-%m-%d}"
        if ev["fail"]:
            return f"{what} failed: {ref.FEED_ERRORS[ev['error']]}"
        if ev.get("not_found"):
            why = "the record was never created" if ev["not_found"] == "CW08" else "the stored Bridgeway ID is blank or mistyped"
            return f"{what} failed: worker not found because {why}"
        if ev["applied"] is None or ev["applied"] > self.extract:
            return f"{what}, still queued"
        return f"{what}, applied {ev['applied']:%Y-%m-%d}"

    # ---------------------------------------------------------------- Keystone-only workers (CW09)
    def keystone_only(self) -> list[Record]:
        recs = []
        start = dt.date.fromisoformat(ref.KS_ONLY_FROM)
        me = month_end(start.year, start.month)
        countries = sorted(self.p.country)
        weights = np.array([self.p.country[c]["weight"] for c in countries], dtype=float)
        sup = sorted(ref.KS_SUPPLIER_VARIANTS)
        while me <= self.extract:
            for _ in range(int(self.rng.poisson(ref.KS_ONLY_MONTHLY))):
                on = dt.date(me.year, me.month, 1) + dt.timedelta(days=int(self.rng.integers(0, me.day)))
                ctry = countries[self.rng.choice(len(countries), p=weights / weights.sum())]
                depts = sorted(d for (d, c) in self.p.cc if c == ctry and d in self.p.mgr_by_dept and d != "D-901")
                dept = self.pick(depts)
                mgr = self.manager_in(dept, ctry, on)
                offices = sorted(o for o, v in self.p.office.items() if v["country"] == ctry and v["opened"] <= on)
                if mgr is None or not offices:
                    continue
                first_pool, last_pool = ref.NAMES[self.p.country[ctry]["region"]]
                cw_type = "Contractor" if self.rng.random() < 0.8 else "Consultant"
                begin = on + dt.timedelta(days=int(self.rng.integers(0, 15)))
                end = add_months(begin, int(self.rng.integers(3, 13))) - ONE_DAY
                rec = Record()
                rec.push(on, {"bw_worker_id": None, "first_name": self.pick(first_pool), "last_name": self.pick(last_pool),
                              "cw_type": cw_type, "supplier_name": self.supplier_variant(self.pick(sup)),
                              "status": "Active", "contract_start_date": begin, "contract_end_date": end,
                              "inactive_reason": None, "department_id": dept, "cost_center_id": self.p.cc[(dept, ctry)],
                              "location_id": self.pick(offices), "manager_worker_id": mgr, "_end_kind": "Contract ended"},
                         "HR Ops", None)
                if self.rng.random() < 0.4:                    # HR Ops notices and inactivates it by hand
                    off = on + dt.timedelta(days=int(self.rng.integers(5, 91)))
                    if off <= min(end, self.extract):
                        rec.push(off, dict(rec.state, status="Inactive", inactive_reason="Manual"), "HR Ops", None)
                rec.advance(self.extract)
                rec.freeze()
                last_active = next((v[0] - ONE_DAY for v in rec.versions if v[1]["status"] == "Inactive"), None)
                recs.append(rec)
                if begin > self.extract or (last_active and last_active < begin):
                    continue                                  # never working before the extract: nothing to flag yet
                self.add_truth("CW09", person=id(rec), fields=GROUP_LABEL["record"], start=begin,
                               end=last_active if last_active and last_active < self.extract else None,
                               resolution=("Open at extract" if not last_active or last_active >= self.extract else
                                           "Fixed by hand in Keystone" if rec.versions[-1][1]["inactive_reason"] == "Manual"
                                           else "Worker no longer active"),
                               detail="Created by hand in Keystone; no Bridgeway worker or service order")
            me = month_end((me + ONE_DAY).year, (me + ONE_DAY).month)
        return recs

    # ---------------------------------------------------------------- run everything
    def run(self):
        self.unexplained = 0
        self.split_renewals()
        self.slow_closures()
        self.billed_after_end()
        self.build_events()
        n = 0
        for bw_id, evs in self.events.items():          # event keys in worker order; final IDs by sent date below
            for ev in evs:
                n += 1
                ev["key"] = n
        self.records: dict[str, Record] = {}
        self.ideal: dict[str, Record] = {}
        for bw_id, evs in self.events.items():
            self.draw_outcomes(evs)
            ideal = self.replay_ideal(evs)
            actual, markers = self.replay_actual(bw_id, evs, ideal)
            self.ideal[bw_id], self.records[bw_id] = ideal, actual
            self.compare(bw_id, ideal, actual, markers)
        self.ks_only = self.keystone_only()
        self.bridgeway_truth()

    def last_active(self, bw_id: str) -> dt.date | None:
        """Last day the worker is active in either system; None if still active at the extract."""
        days = []
        for rec in (self.ideal.get(bw_id), self.records.get(bw_id)):
            if rec and rec.versions:
                st = rec.versions[-1][1]
                if st["status"] == "Active":
                    return None
                days.append(rec.versions[-1][0] - ONE_DAY)
        return max(days) if days else None

    def bridgeway_truth(self):
        so = self.bw["bw_service_order"].set_index("service_order_id")
        for so_id, last_day, closed in self.slow:
            start = last_day + dt.timedelta(days=16)
            if start > self.extract:
                continue
            bw_id = so.at[so_id, "bw_worker_id"]
            self.add_truth("CW04", bw_worker_id=bw_id, person=self.person_of(bw_id), service_order_id=so_id,
                           fields="Order status", start=start, end=closed - ONE_DAY if closed else None,
                           resolution="Closed late in Bridgeway" if closed else "Open at extract",
                           detail=f"Last day {last_day:%Y-%m-%d}; " + (f"closed {closed:%Y-%m-%d}" if closed else "still open"))
        for tid, bw_id, so_id, last_day, me in self.after_end:
            self.add_truth("CW11", bw_worker_id=bw_id, person=self.person_of(bw_id), service_order_id=so_id,
                           timesheet_id=tid, fields="Timesheet", start=dt.date(me.year, me.month, 1), end=me,
                           resolution="Billed", detail=f"Last day {last_day:%Y-%m-%d}; billed for {me:%B %Y}")
        extracted = set(self.bw["bw_contingent_worker"]["bw_worker_id"])
        for e in self.p.engagements:
            if not e.cap_breach or e.bw_worker_id not in extracted:
                continue
            cap = add_months(e.orig_start, ref.CW_MAX_MONTHS)
            if cap > self.extract:
                continue
            end = e.end if e.end < self.extract else None
            self.add_truth("CW10", bw_worker_id=e.bw_worker_id, person=self.person_of(e.bw_worker_id),
                           service_order_id=e.orders[-1].service_order_id, fields="Engagement length", start=cap, end=end,
                           resolution="Open at extract" if end is None else "Engagement ended",
                           detail=f"Started {e.orig_start:%Y-%m-%d}; 48 months reached {cap - ONE_DAY:%Y-%m-%d}; "
                                  f"last day {e.end:%Y-%m-%d}")
        for old_id, new_id, so_id, start in self.splits:
            created = self.records[new_id].versions[0][0] if self.records[new_id].versions else start
            self.add_truth("CW07", bw_worker_id=new_id, person=self.person_of(new_id), service_order_id=so_id,
                           fields="Bridgeway worker ID; Keystone person", start=created, end=self.last_active(new_id),
                           resolution="Open at extract" if self.last_active(new_id) is None else "Worker no longer active",
                           detail=f"Same person as Bridgeway {old_id} (Keystone {{person:{old_id}}})")

    def person_of(self, bw_id: str):
        rec = self.records.get(bw_id)
        return id(rec) if rec and rec.versions else None

    # ---------------------------------------------------------------- the extract
    def tables(self) -> dict[str, pd.DataFrame]:
        # Keystone person IDs in the order records were created
        all_recs = [(rec.versions[0][0], 0, bw, rec) for bw, rec in self.records.items() if rec.versions]
        all_recs += [(rec.versions[0][0], 1, f"{i:06d}", rec) for i, rec in enumerate(self.ks_only)]
        all_recs.sort(key=lambda t: (t[0], t[1], t[2]))
        person = {id(rec): f"W{ref.KS_CW_PERSON_ID_START + n}" for n, (_, _, _, rec) in enumerate(all_recs)}
        person_by_bw = {bw: person[id(rec)] for bw, rec in self.records.items() if rec.versions}

        # feed events: IDs by sent date
        evs = [ev for e in self.events.values() for ev in e]
        evs.sort(key=lambda ev: (ev["sent"], ev["bw_worker_id"], ev["revision_id"]))
        fe_id = {}
        feed = []
        for n, ev in enumerate(evs, 1):
            fe_id[ev["key"]] = f"FE{n:09d}"
            if ev["fail"]:
                outcome, applied, err = "Failed", None, ref.FEED_ERRORS[ev["error"]]
            elif ev.get("not_found"):
                outcome, applied, err = "Failed", None, ref.FEED_ERRORS["not_found"].format(bw=ev["bw_worker_id"])
            elif ev["applied"] > self.extract:
                outcome, applied, err = "Queued", None, None
            elif ev.get("partial"):
                outcome, applied, err = "Partly Applied", ev["applied"], ref.FEED_ERRORS["partial"]
            else:
                late = (ev["applied"] - ev["sent"]).days >= ref.FEED_LATE_DAYS[0]
                outcome, applied, err = ("Applied Late" if late else "Applied"), ev["applied"], None
            feed.append({"feed_event_id": fe_id[ev["key"]], "revision_id": ev["revision_id"],
                         "bw_worker_id": ev["bw_worker_id"], "event_type": ev["event_type"], "sent_date": ev["sent"],
                         "applied_date": applied, "outcome": outcome, "error_text": err})

        # Keystone versions
        rows = []
        for _, _, _, rec in all_recs:
            pid = person[id(rec)]
            for i, (d, st, source, fe) in enumerate(rec.versions):
                nxt = rec.versions[i + 1][0] if i + 1 < len(rec.versions) else None
                row = {"person_id": pid, "effective_start_date": d, "effective_end_date": nxt - ONE_DAY if nxt else None,
                       "change_source": source, "feed_event_id": fe_id.get(fe) if fe else None}
                row.update({f: st.get(f) for f in OUT_FIELDS})
                rows.append(row)
        ks = pd.DataFrame(rows).sort_values(["person_id", "effective_start_date"]).reset_index(drop=True)
        ks.insert(0, "ks_record_id", [f"KS{n:09d}" for n in range(1, len(ks) + 1)])

        # the answer key
        truth = pd.DataFrame(self.truth)
        truth["person_id"] = truth["person_key"].map(lambda k: person.get(k) if k else None)
        truth["feed_event_id"] = truth["feed_event_key"].map(lambda k: fe_id.get(k) if k else None)
        truth["detail"] = [_fill_person(d, person_by_bw) for d in truth["detail"]]
        truth = truth.sort_values(["start_date", "discrepancy_code", "bw_worker_id", "person_id"],
                                  na_position="first").reset_index(drop=True)
        truth.insert(0, "discrepancy_id", [f"DQ{n:07d}" for n in range(1, len(truth) + 1)])

        types = pd.DataFrame(DISCREPANCY_TYPES, columns=["discrepancy_code", "discrepancy_name", "what_happened",
                                                          "what_a_manager_sees", "who_can_fix_it", "severity"])
        out = dict(self.bw)
        out.update({"feed_bridgeway_keystone_event": pd.DataFrame(feed), "ks_contingent_worker": ks,
                    "gen_cw_discrepancy_truth": truth, "ref_cw_discrepancy_type": types})
        return out


def _fix_name(code: str) -> str:
    return {"CW02": "Extension never arrived", "CW03": "Early end never arrived", "CW08": "Never reached Keystone",
            "CW12": "Attribute change never arrived", "CW06": "Link ID missing or mistyped"}[code]


def _fill_person(detail: str, person_by_bw: dict) -> str:
    if "{person:" not in detail:
        return detail
    head, rest = detail.split("{person:", 1)
    bw, tail = rest.split("}", 1)
    return f"{head}{person_by_bw.get(bw, 'no record')}{tail}"


def simulate(*, stream, bw, program, cost_centers) -> tuple[dict[str, pd.DataFrame], Keystone]:
    ks = Keystone(stream=stream, bw=bw, program=program, cost_centers=cost_centers)
    ks.run()
    return ks.tables(), ks
