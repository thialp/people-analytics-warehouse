"""Helix Service Desk (release 4, case study 4): the tickets people raise to fix the gaps.

Helix is a fictional IT service management system. Its tables are generic (a ticket, its state
changes, what it is about, a category list), seeded here with contingent worker tickets only, so
employee or position tickets can be added later without a new design.

Tickets are derived from the answer keys, which already know when every gap began and how it
ended (gen_cw_discrepancy_truth, gen_cw_job_defect), plus the warehouse's failed loads
(etl_load_run). For each gap:

- **whether and when someone raises a ticket** depends on what the gap does to people: a
  contractor who lost access complains within days; a wrong cost center is noticed by Finance
  after a close; vendor management reviews open orders on the 10th of the month.
- **who works it** is the place the record is corrected (Vendor Management for Bridgeway, HR
  Operations for Keystone, Data Engineering for the feed and loads); 1 in 10 lands with the wrong
  group first and is reassigned.
- **how it ends** follows the gap: resolved when the gap is fixed (a Bridgeway fix often a day or
  two before the feed brings it to Keystone: "fix pending next run"), closed as "No longer
  reproducible" weeks after a gap that ended by itself, resolved in error now and then (most of
  those reopen), or still open on the extract date.
- **what it links to**: 7 in 10 carry the worker ID in a field, 2 in 10 only the name in the text,
  1 in 10 nothing. The warehouse links them in tiers.

Own random stream; nothing that exists moves. All times are GMT.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd

import reference_data as ref

ONE_DAY = dt.timedelta(days=1)
EXTRACT = dt.date.fromisoformat(ref.CW_EXTRACT_DATE)
CUTOFF = dt.datetime.combine(EXTRACT, dt.time(23, 59, 59))     # Helix as the last run reads it
START = dt.date.fromisoformat(ref.HLX_START)

GROUPS = {"Bridgeway": "Vendor Management", "Keystone": "HR Operations", "System feed": "Data Engineering"}
GROUP_HOURS = {"Vendor Management": ref.OPS_VENDOR_MGMT_HOURS, "HR Operations": ref.OPS_HR_OPS_HOURS,
               "Data Engineering": ref.OPS_DATA_ENG_HOURS}

# category: (name, flag, risk, place, priority, title)
CATEGORIES = {
    "CW-F01": ("One person, two IDs", "F01", "Active headcount mismatch", "Bridgeway", "P4", "Duplicate contractor IDs"),
    "CW-F02": ("Bridgeway ID missing or different", "F02", "Active headcount mismatch", "Keystone", "P4", "Bridgeway ID missing or different"),
    "CW-F03": ("In Bridgeway, not in Keystone", "F03", "Active headcount mismatch", "System feed", "P2", "Contractor not in Keystone"),
    "CW-F04": ("Order open or billed after the end date", "F04", "Billing after the end date", "Bridgeway", "P3", "Order open or billed after the end date"),
    "CW-F05": ("Cost center differs", "F05", "Cost center mismatch", "Bridgeway", "P3", "Cost center differs between systems"),
    "CW-F06": ("PID still filled after the end date", "F06", "PID mismatch", "Keystone", "P4", "PID still filled after the end date"),
    "CW-F07": ("Two active PID records", "F07", "PID mismatch", "Keystone", "P4", "Two active PIDs"),
    "CW-F08": ("Working in Bridgeway, ended in Keystone", "F08", "Status mismatch", "System feed", "P2", "Contractor ended in Keystone while working"),
    "CW-F09": ("Active in Keystone, not working in Bridgeway", "F09", "Status mismatch", "Keystone", "P2", "Contractor active in Keystone after the end"),
    "INT-FEED": ("Feed change stuck", None, None, "System feed", "P2", "Feed change stuck in the queue"),
    "INT-LOAD": ("Warehouse load failed", None, None, "System feed", "P1", "Warehouse load failed"),
}
# how quickly people raise a ticket, by what the gap does to them (reference_data.HLX_TICKET_RULES)
BEHAVIOUR = {"CW-F01": "Headcount", "CW-F02": "Headcount", "CW-F03": "Access lost", "CW-F04": "Billing",
             "CW-F05": "Cost center", "CW-F06": "PID", "CW-F07": "PID", "CW-F08": "Access lost",
             "CW-F09": "Access kept", "INT-FEED": "Feed stuck"}
# a failed feed event (CW02, CW08, CW12) is replayed by data engineering, unless it failed because
# Keystone holds a wrong Bridgeway ID (root cause CW06): then HR Ops repairs the record
FEED_FAILURES = {"CW02", "CW08", "CW12"}

FIXED = {"Fixed by hand in Keystone", "Bridgeway changed to match", "Closed late in Bridgeway"}


def category_rows() -> list[dict]:
    return [{"category_code": c, "category_name": n, "subject_type": "Data load" if c == "INT-LOAD" else "Contingent worker",
             "default_group": GROUPS[p], "flag_code": f, "risk": r, "priority": pr, "title_template": t}
            for c, (n, f, r, p, pr, t) in CATEGORIES.items()]


def _d(x) -> dt.date | None:
    if x is None or (isinstance(x, float) and np.isnan(x)) or x == "" or pd.isna(x):
        return None
    if isinstance(x, pd.Timestamp):
        return x.date()
    return x if isinstance(x, dt.date) and not isinstance(x, dt.datetime) else dt.date.fromisoformat(str(x)[:10])


def simulate(*, stream: np.random.Generator, tables: dict[str, pd.DataFrame], job_defects: pd.DataFrame,
             load_runs: pd.DataFrame, conversions: dict) -> dict[str, pd.DataFrame]:
    rng = stream
    truth = tables["gen_cw_discrepancy_truth"]
    feed_type = dict(zip(tables["feed_bridgeway_keystone_event"]["feed_event_id"],
                         tables["feed_bridgeway_keystone_event"]["event_type"]))
    bw = tables["bw_contingent_worker"].set_index("bw_worker_id")
    ks = tables["ks_contingent_worker"]
    ks_name = ks.drop_duplicates("person_id", keep="last").set_index("person_id")[["first_name", "last_name"]]
    person_of_bw = (ks.dropna(subset=["bw_worker_id"]).drop_duplicates("bw_worker_id")
                    .set_index("bw_worker_id")["person_id"].to_dict())

    # ------------------------------------------------------------------ the gaps worth a ticket
    gaps = []
    for r in truth.itertuples(index=False):
        code, fields = r.discrepancy_code, r.fields_affected or ""
        start, end = _d(r.start_date), _d(r.end_date)
        person = r.person_id if isinstance(r.person_id, str) and r.person_id else None
        bwid = r.bw_worker_id if isinstance(r.bw_worker_id, str) and r.bw_worker_id else None
        cat, conv_case = None, False
        if code == "CW01":
            cat = "INT-FEED"
        elif code == "CW02":
            cat = "CW-F08"
        elif code == "CW03":
            conv = conversions.get(bwid)
            conv_case = bool(conv and conv["last_day"] < start)
            cat = "CW-F01" if conv_case else "CW-F09"
        elif code in ("CW04", "CW11"):
            cat = "CW-F04"
        elif code in ("CW05", "CW12") and "Cost center" in fields:
            cat = "CW-F05"
        elif code in ("CW06", "CW07", "CW08", "CW09"):
            cat = {"CW06": "CW-F02", "CW07": "CW-F01", "CW08": "CW-F03", "CW09": "CW-F09"}[code]
        if cat is None:
            continue
        kind = ("credit" if code == "CW11" else "open" if r.resolution == "Open at extract"
                else "fix" if r.resolution in FIXED else "self")
        if conv_case:
            place = "Keystone"
        elif code in FEED_FAILURES:
            place = "Keystone" if r.root_cause_code == "CW06" else "System feed"
        else:
            place = "Bridgeway" if cat == "CW-F05" else CATEGORIES[cat][3]
        gaps.append({"cat": cat, "place": place, "bw": bwid, "person": person or person_of_bw.get(bwid),
                     "start": start, "end": end, "kind": kind, "code": code,
                     "order": r.service_order_id, "feed": r.feed_event_id, "detail": r.detail,
                     "event_type": feed_type.get(r.feed_event_id)})
    bw_of_person = {p: b for b, p in person_of_bw.items()}
    bw_names = bw[["first_name", "last_name"]].to_dict("index")
    ks_names = ks_name.to_dict("index")
    for r in job_defects.itertuples(index=False):
        gaps.append({"cat": "CW-F07" if r.flag_code == "F07" else "CW-F06", "place": "Keystone",
                     "bw": bw_of_person.get(r.person_id), "person": r.person_id, "start": _d(r.start_date),
                     "end": _d(r.end_date), "kind": "open" if r.resolution == "Open at extract" else "fix",
                     "code": r.flag_code, "order": None, "feed": None, "detail": r.detail, "event_type": None,
                     "pid": r.position_id})

    # ------------------------------------------------------------------ tickets
    tickets, events, links = [], [], []

    def at(day: dt.date, group: str) -> dt.datetime:
        lo, hi = GROUP_HOURS[group]
        return dt.datetime.combine(day, dt.time(0)) + dt.timedelta(hours=int(rng.integers(lo, hi + 1)),
                                                                   minutes=int(rng.integers(0, 60)))

    def days(lo: float, hi: float) -> dt.timedelta:
        return dt.timedelta(days=float(lo + rng.random() * (hi - lo)))

    for g in sorted(gaps, key=lambda g: (g["start"], g["cat"], g["bw"] or "", g["person"] or "")):
        nm = bw_names.get(g["bw"]) or ks_names.get(g["person"])
        g["_name"] = f"{nm['first_name']} {nm['last_name']}" if nm else None
        name, flag, risk, _, priority, title = CATEGORIES[g["cat"]]
        rule = BEHAVIOUR[g["cat"]]
        share, window = ref.HLX_TICKET_RULES[rule]
        u = rng.random()
        start, end = g["start"], g["end"]
        if start < START:
            if end is not None and end < START:
                continue
            open_day = START + dt.timedelta(days=int(rng.exponential(ref.HLX_LEGACY_MEAN_DAYS)))
        elif window is not None:
            open_day = start + dt.timedelta(days=int(rng.integers(window[0], window[1] + 1)))
        elif g["cat"] == "CW-F05":
            if rng.random() < ref.HLX_COST_CENTER_AFTER_CLOSE:
                me = (start.replace(day=28) + dt.timedelta(days=4)).replace(day=1)       # the 1st after the close
                open_day = me + dt.timedelta(days=int(rng.integers(1, 6)))
            else:
                open_day = start + dt.timedelta(days=int(rng.integers(2, 31)))
        elif g["code"] == "CW04":
            tenth = start.replace(day=10) if start.day <= 10 else (start.replace(day=28) + dt.timedelta(days=4)).replace(day=10)
            open_day = tenth + dt.timedelta(days=int(rng.integers(0, 3)))
        else:                                                                         # CW11: the invoice
            open_day = start + dt.timedelta(days=int(rng.integers(5, 26)))
        if u >= share and rule != "Feed stuck":         # nobody raised it at first: noticed later, if it lasts
            open_day = max(open_day, start) + dt.timedelta(days=int(1 + rng.exponential(ref.HLX_LATE_NOTICE_MEAN_DAYS)))
        elif u >= share:
            continue
        if open_day > EXTRACT or (end is not None and open_day > end):
            continue
        group = GROUPS[g["place"]]
        opened = at(open_day, group)
        first_group = group
        if rng.random() < ref.HLX_MISROUTED:
            first_group = [x for x in GROUPS.values() if x != group][int(rng.integers(2))]
        ev = [(opened, None, "New", first_group, "Opened")]
        t = opened
        if first_group != group:
            t = at((t + days(1, 4)).date(), group)
            ev.append((t, "New", "New", group, f"Reassigned from {first_group} to {group}"))
        t = max(t, at((opened + days(0, 3)).date(), group))
        if t <= ev[-1][0]:
            t = ev[-1][0] + dt.timedelta(hours=1)
        ev.append((t, "New", "In progress", group, "Work started"))
        if g["place"] == "Bridgeway" and rng.random() < ref.HLX_PENDING_SUPPLIER:
            t = at((t + days(1, 10)).date(), group) + dt.timedelta(hours=1)
            ev.append((t, "In progress", "Pending", group, "Waiting on the supplier"))
            t = at((t + days(2, 15)).date(), group) + dt.timedelta(hours=1)
            ev.append((t, "Pending", "In progress", group, "Supplier replied"))

        # how it ends
        if g["kind"] == "fix":
            fix_day = end + ONE_DAY
            off = days(-2, 0) if g["place"] == "Bridgeway" else days(0, 2)
            resolve, code = at((dt.datetime.combine(fix_day, dt.time()) + off).date(), group), "Fixed in source"
        elif g["kind"] == "self":
            resolve = at(end + ONE_DAY + days(*ref.HLX_NO_LONGER_REPRODUCIBLE_DAYS), group)
            code = "No longer reproducible"
        elif g["kind"] == "credit":
            resolve, code = at((opened + days(5, 30)).date(), group), "Credit requested from supplier"
        else:
            resolve, code = None, None

        # resolved in error: while the gap is still there
        gap_until = dt.datetime.combine(end or EXTRACT, dt.time(23, 59))
        if rng.random() < ref.HLX_RESOLVED_IN_ERROR and gap_until - ev[-1][0] > dt.timedelta(days=6):
            e_t = ev[-1][0] + days(1, max(1.5, (gap_until - ev[-1][0]).days - 3))
            e_t = at(e_t.date(), group) + dt.timedelta(hours=1)
            if e_t > ev[-1][0] and (resolve is None or e_t < resolve):
                ev.append((e_t, ev[-1][2], "Resolved", group, "Resolved: Fixed in source"))
                if rng.random() < ref.HLX_REOPENED:
                    r_t = at((e_t + days(3, 15)).date(), group) + dt.timedelta(hours=2)
                    ev.append((r_t, "Resolved", "Reopened", group, "Reopened: the gap is still there"))
                    ev.append((r_t + dt.timedelta(hours=float(1 + rng.random() * 20)), "Reopened", "In progress", group,
                               "Work restarted"))
                else:
                    ev.append((e_t + dt.timedelta(days=3), "Resolved", "Closed", "Helix", "Closed automatically"))
                    resolve = None
        if resolve is not None:
            if resolve <= ev[-1][0]:
                resolve = ev[-1][0] + dt.timedelta(hours=float(1 + rng.random() * 6))
            ev.append((resolve, ev[-1][2], "Resolved", group, f"Resolved: {code}"))
            ev.append((resolve + dt.timedelta(days=3), "Resolved", "Closed", "Helix", "Closed automatically"))

        ev = [e for e in ev if e[0] <= CUTOFF]
        tickets.append(_ticket(g, ev, name, flag, title, priority, group, rng))
        events.append(ev)

    for run in load_runs[load_runs["status"] == "Failed"].itertuples(index=False):
        opened = pd.Timestamp(run.finished_at).to_pydatetime() + dt.timedelta(minutes=int(rng.integers(20, 80)))
        if opened > CUTOFF:
            continue
        t1 = opened + dt.timedelta(minutes=int(rng.integers(5, 30)))
        t2 = t1 + dt.timedelta(hours=float(2 + rng.random() * 6))
        ev = [(opened, None, "New", "Data Engineering", "Opened by load monitoring"),
              (t1, "New", "In progress", "Data Engineering", "Work started"),
              (t2, "In progress", "Resolved", "Data Engineering", "Resolved: Source fixed; next run reloads"),
              (t2 + dt.timedelta(days=3), "Resolved", "Closed", "Helix", "Closed automatically")]
        ev = [e for e in ev if e[0] <= CUTOFF]
        src = {"BW": "Bridgeway", "KS": "Keystone", "HLX": "Helix"}[run.source_system]
        tickets.append({"_open": opened, "_link": ("Data load", run.run_id, None, "ID field"),
                        "title": f"Warehouse load failed · {src} {run.scheduled_at:%Y-%m-%d %H:%M}",
                        "short_description": f"The {src} load scheduled {run.scheduled_at:%Y-%m-%d %H:%M} GMT failed: "
                                             f"{run.error_text}. The warehouse kept the previous load.",
                        "category_code": "INT-LOAD", "priority": "P1", "assignment_group": "Data Engineering",
                        **_outcome(ev)})
        events.append(ev)

    order = sorted(range(len(tickets)), key=lambda i: (tickets[i]["_open"], tickets[i]["title"]))
    t_rows, e_rows, l_rows = [], [], []
    for n, i in enumerate(order):
        number = f"HLX-{ref.HLX_FIRST_NUMBER + n}"
        t = tickets[i]
        t_rows.append({"ticket_number": number, "title": t["title"], "short_description": t["short_description"],
                       "category_code": t["category_code"], "priority": t["priority"],
                       "assignment_group": t["assignment_group"], "opened_at": t["_open"],
                       "resolved_at": t["resolved_at"], "closed_at": t["closed_at"], "close_code": t["close_code"]})
        for e in events[i]:
            e_rows.append({"ticket_number": number, "event_at": e[0], "from_state": e[1], "to_state": e[2],
                           "actor_group": e[3], "note": e[4]})
        st, sid, sec, q = t["_link"]
        l_rows.append({"ticket_number": number, "subject_type": st, "subject_id": sid, "secondary_id": sec,
                       "link_quality": q})
    fmt = lambda df, cols: df.assign(**{c: pd.to_datetime(df[c]).dt.floor("min") for c in cols})
    return {
        "itsm_ticket": fmt(pd.DataFrame(t_rows), ["opened_at", "resolved_at", "closed_at"]),
        "itsm_ticket_event": fmt(pd.DataFrame(e_rows), ["event_at"]),
        "itsm_ticket_link": pd.DataFrame(l_rows),
        "ref_ticket_category": pd.DataFrame(category_rows()),
    }


def _outcome(ev: list[tuple]) -> dict:
    """Ticket columns from the events as of the cutoff: the latest resolution (unless reopened since)."""
    resolved = closed = code = None
    for t, _, to, _, note in ev:
        if to == "Resolved":
            resolved, code = t, note.split(": ", 1)[1] if ": " in note else None
        elif to == "Reopened":
            resolved = code = None
        elif to == "Closed":
            closed = t
    return {"resolved_at": resolved, "closed_at": closed, "close_code": code}


def _ticket(g: dict, ev: list[tuple], name: str, flag: str | None, title: str, priority: str, group: str,
            rng: np.random.Generator) -> dict:
    q = list(ref.HLX_LINK_QUALITY)[int(rng.choice(3, p=list(ref.HLX_LINK_QUALITY.values())))]
    bw, person = g["bw"], g["person"]
    pid = g.get("pid")
    if q == "ID field":
        who = bw or person
        tail = f" · {who}"
        lead = f"Contractor {bw or person}"
        if bw and person:
            lead += f" (Keystone {person})"
        link = ("Contingent worker", bw, person, q)
    elif q == "Name in text":
        nm = g.get("_name") or ""
        tail = f" · {nm}" if nm else ""
        lead = f"Contractor {nm}" if nm else "A contractor"
        link = ("Contingent worker", None, None, q)
    else:
        tail, lead = "", "A contractor"
        link = ("Contingent worker", None, None, q)
    what = {
        "CW-F01": "the same person appears under two IDs",
        "CW-F02": "the Bridgeway ID stored in Keystone is missing or belongs to someone else",
        "CW-F03": "Bridgeway shows the contractor working but Keystone has no record",
        "CW-F04": ("time was billed for a month after the assignment ended" if g["code"] == "CW11"
                   else "the Bridgeway order is still open after the assignment ended"),
        "CW-F05": "the cost center in Keystone differs from the one Bridgeway bills",
        "CW-F06": "Keystone still shows the PID filled after the contract ended",
        "CW-F07": "Keystone shows two active PIDs for one person",
        "CW-F08": "Keystone ended the contractor while Bridgeway shows the contract running",
        "CW-F09": ("Keystone shows the contractor active with no Bridgeway worker" if g["code"] == "CW09"
                   else "Bridgeway ended the contract but Keystone still shows the contractor active"),
        "INT-FEED": "a change from Bridgeway is still waiting in the integration queue",
    }[g["cat"]]
    desc = f"{lead}: {what}."
    if q == "ID field" and g.get("detail"):
        desc += f" {g['detail']}."
    if q == "ID field" and pid:
        desc += f" PID {pid}."
    return {"_open": ev[0][0], "_link": link, "title": title + tail, "short_description": desc,
            "category_code": g["cat"], "priority": priority, "assignment_group": group, **_outcome(ev)}
