"""Reconciliation operations (release 4, case study 4): when things happened, Keystone's job data,
and the warehouse's own load log.

Release 3 records the contingent workforce in days: the day Bridgeway sent a change, the day
Keystone applied it, the day a version took effect. Finance's month-end report is built by a run
at a clock time, so this module adds the times, on new tables only:

- **feed_event_delivery**  the hour each feed change was sent (the hourly batch that picked it
  up) and the hour Keystone applied it. Consistent with the dates already in the feed log.
- **ks_contingent_worker_audit**  when each Keystone contingent version was written, and by
  whom: the feed (at the hour it was applied), Keystone's nightly job (00:05 GMT), a manager in
  their office's working hours, or HR Operations in Bangalore.
- **ks_cw_job**  Keystone job data: the PID each contingent worker's job record (EMPLID x record
  number) holds. It follows the PID ledger (fact_position_assignment), with two seeded
  imperfections: an old job left active when a contractor returns on another PID (one person,
  two active PIDs) and a job ended late (still in the PID after the contract ended). HR Ops fixes
  them on the day they notice, never backdated, so a past close replays as it was.
- **gen_cw_job_defect**  the answer key for those two: every period in which a person holds two
  active jobs, or one active job on a PID the ledger shows they left.
- **etl_load_run**  the warehouse's runs: Bridgeway at 00:00 GMT, Keystone after it, Helix at
  00:00 and 12:00, with a few late and failed loads.

Every draw comes from streams of its own, and nothing that exists is changed.
"""
from __future__ import annotations

import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd

import reference_data as ref

ONE_DAY = dt.timedelta(days=1)
EXTRACT = dt.date.fromisoformat(ref.CW_EXTRACT_DATE)


def _dates(s: pd.Series) -> pd.Series:
    return pd.to_datetime(s.replace("", None), errors="coerce")


def _d(x) -> dt.date | None:
    if x is None or (isinstance(x, float) and np.isnan(x)) or x == "" or pd.isna(x):
        return None
    return x if isinstance(x, dt.date) and not isinstance(x, dt.datetime) else dt.date.fromisoformat(str(x)[:10])


def _hours(rng: np.random.Generator, lo: int, hi: int, n: int) -> np.ndarray:
    """Clock times inside [lo:00, hi:59], as hours with minutes (float)."""
    return rng.integers(lo, hi + 1, n) + rng.integers(0, 60, n) / 60.0


# ---------------------------------------------------------------------------------- feed times
def feed_delivery(stream: np.random.Generator, feed: pd.DataFrame) -> pd.DataFrame:
    """sent_at and applied_at for every feed event, on the hour (the hourly batch)."""
    n = len(feed)
    sent = _dates(feed["sent_date"])
    applied = _dates(feed["applied_date"])
    regions = list(ref.OPS_SEND_HOURS.values())
    pick = stream.choice(len(regions), size=n, p=[r[2] for r in regions])
    lo = np.array([regions[i][0] for i in pick])
    hi = np.array([regions[i][1] for i in pick])
    s = lo + np.floor(stream.random(n) * (hi - lo + 1)).astype(int)
    lag = (applied - sent).dt.days.to_numpy()
    same_day = lag == 0
    s = np.where(same_day, np.minimum(s, 22), s)
    a_same = s + 1 + np.floor(stream.random(n) * (23 - s)).astype(int)       # later the same day
    a_later = stream.integers(1, 24, n)                                          # 01:00 to 23:00
    a = np.where(same_day, a_same, a_later)
    out = pd.DataFrame({"feed_event_id": feed["feed_event_id"].to_numpy()})
    out["sent_at"] = sent + pd.to_timedelta(s, unit="h")
    out["applied_at"] = applied + pd.to_timedelta(a, unit="h")
    out.loc[applied.isna().to_numpy(), "applied_at"] = pd.NaT
    return out


# ------------------------------------------------------------------------ Keystone audit trail
def ks_audit(stream: np.random.Generator, ks: pd.DataFrame, delivery: pd.DataFrame,
             location_region: dict[str, str]) -> pd.DataFrame:
    """When each Keystone contingent version was written (GMT) and by whom."""
    n = len(ks)
    eff = _dates(ks["effective_start_date"])
    src = ks["change_source"].to_numpy()
    applied = ks["feed_event_id"].map(delivery.set_index("feed_event_id")["applied_at"])
    changed = pd.Series(pd.NaT, index=ks.index, dtype="datetime64[ns]")

    minutes = stream.integers(0, 50, n)
    feed_ok = (src == "Feed") & applied.notna().to_numpy() & (applied.dt.normalize() == eff).to_numpy()
    changed[feed_ok] = (applied + pd.to_timedelta(minutes, unit="m"))[feed_ok]
    feed_other = (src == "Feed") & ~feed_ok
    changed[feed_other] = (eff + pd.to_timedelta(stream.integers(1, 24, n), unit="h"))[feed_other]

    system = src == "System"
    changed[system] = (eff + pd.to_timedelta(5 + stream.integers(0, 10, n), unit="m"))[system]

    hr = src == "HR Ops"
    changed[hr] = (eff + pd.to_timedelta(_hours(stream, *ref.OPS_HR_OPS_HOURS, n), unit="h"))[hr]

    mgr = src == "Manager"
    region = ks["location_id"].map(location_region).fillna("North America").to_numpy()
    lo = np.array([ref.OPS_OFFICE_HOURS[r][0] for r in region])
    hi = np.array([ref.OPS_OFFICE_HOURS[r][1] for r in region])
    h = lo + np.floor(stream.random(n) * (hi - lo + 1)) + stream.integers(0, 60, n) / 60.0
    changed[mgr] = (eff + pd.to_timedelta(h, unit="h"))[mgr]

    by = pd.Series(src).map({"Feed": "Integration", "System": "Keystone nightly job", "HR Ops": "HR Operations",
                              "Manager": "Manager"}).to_numpy()
    return pd.DataFrame({"ks_record_id": ks["ks_record_id"].to_numpy(),
                         "changed_at": changed.dt.floor("min").to_numpy(), "changed_by": by})


# ------------------------------------------------------------------------- Keystone job data
def job_data(stream: np.random.Generator, assign_rows: list[dict]) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Keystone job rows for contingent workers (ks_cw_job) and the answer key (gen_cw_job_defect).

    One job record (EMPLID x record number) per PID a person holds. An assignment starts or
    reactivates the record (a return to the same PID reuses it) and its end terminates it the next
    day. Seeded, from the ledger's own returns and ends:
      - a return within 120 days on another PID leaves the old record active (CW_JOB_RETURN_KEEP_OLD);
      - a return to the same PID is entered as a new record while the old one stays active
        (CW_JOB_SAME_PID_NEW_RECORD);
      - any other end is entered late (CW_JOB_LATE_END).
    HR Ops ends the old record on the day they notice (never backdated), or never.
    """
    by_person = defaultdict(list)
    for a in assign_rows:
        if a["worker_id"]:
            by_person[a["worker_id"]].append(a)

    def later(base: dt.date, days: tuple[int, int], never: float) -> dt.date | None:
        u, d = stream.random(), stream.random()
        if u < never:
            return None
        stop = base + dt.timedelta(days=int(days[0] + d * (days[1] - days[0])))
        return None if stop > EXTRACT else stop

    rows: list[dict] = []
    seeded: set[str] = set()
    for person in sorted(by_person):
        assigns = sorted(by_person[person], key=lambda a: (a["start_date"], a["assignment_id"]))
        # decide each end: the day the record is terminated, and whether the next one gets a new record
        stop, new_record = {}, set()
        for i, a in enumerate(assigns):
            e = a["end_date"]
            if e is None or e + ONE_DAY > EXTRACT:
                stop[a["assignment_id"]] = None
                continue
            nxt = next((b for b in assigns[i + 1:] if b["start_date"] > e), None)
            back = nxt is not None and (nxt["start_date"] - e).days <= 120
            u = stream.random()
            stop[a["assignment_id"]] = e + ONE_DAY
            if back and nxt["position_id"] != a["position_id"] and u < ref.CW_JOB_RETURN_KEEP_OLD:
                stop[a["assignment_id"]] = later(nxt["start_date"], ref.CW_JOB_RETURN_KEEP_DAYS, ref.CW_JOB_RETURN_NEVER)
                seeded.add(a["assignment_id"])
            elif back and nxt["position_id"] == a["position_id"] and u < ref.CW_JOB_SAME_PID_NEW_RECORD:
                stop[a["assignment_id"]] = later(nxt["start_date"], ref.CW_JOB_RETURN_KEEP_DAYS, ref.CW_JOB_RETURN_NEVER)
                new_record.add(nxt["assignment_id"])
                seeded.add(a["assignment_id"])
            elif not back and u < ref.CW_JOB_LATE_END:
                stop[a["assignment_id"]] = later(e + ONE_DAY, ref.CW_JOB_LATE_END_DAYS, ref.CW_JOB_LATE_END_NEVER)
                seeded.add(a["assignment_id"])

        # walk the assignments, keeping each record's state
        records: list[dict] = []                     # {rcd, pid, stop}: stop None = active with no end entered
        for a in assigns:
            base = {"person_id": person, "position_id": a["position_id"], "assignment_id": a["assignment_id"]}
            same = [r for r in records if r["pid"] == a["position_id"]]
            rec = same[-1] if same else None
            if rec is not None and a["assignment_id"] not in new_record:
                if rec["stop"] is None or rec["stop"] >= a["start_date"]:
                    if rec["stop"] is not None:      # its late end now falls inside the new assignment: dropped
                        rows.pop(rec["end_row"])
                        for r in records:
                            if r.get("end_row") is not None and r["end_row"] > rec["end_row"]:
                                r["end_row"] -= 1
                        rec["end_row"] = None
                else:
                    rows.append({**base, "empl_rcd": rec["rcd"], "effective_start_date": a["start_date"],
                                 "job_status": "Active", "action": "Return", "change_source": "Feed"})
            else:
                rec = {"rcd": len(records), "pid": a["position_id"], "end_row": None}
                records.append(rec)
                rows.append({**base, "empl_rcd": rec["rcd"], "effective_start_date": a["start_date"],
                             "job_status": "Active", "action": "Assignment start" if rec["rcd"] == 0 else "Return",
                             "change_source": "Feed"})
            rec["stop"] = stop[a["assignment_id"]]
            if rec["stop"] is not None:
                rec["end_row"] = len(rows)
                rows.append({**base, "empl_rcd": rec["rcd"], "effective_start_date": rec["stop"],
                             "job_status": "Terminated", "action": "Assignment end",
                             "change_source": "HR Ops" if a["assignment_id"] in seeded else "Feed"})

    job = pd.DataFrame(rows)
    job = job.sort_values(["person_id", "empl_rcd", "effective_start_date"], kind="stable").reset_index(drop=True)
    nxt_start = job.groupby(["person_id", "empl_rcd"])["effective_start_date"].shift(-1)
    job["effective_end_date"] = [None if pd.isna(x) else x - ONE_DAY for x in nxt_start]
    job.insert(0, "job_record_id", [f"KJ{n:07d}" for n in range(1, len(job) + 1)])
    job = job[["job_record_id", "person_id", "empl_rcd", "position_id", "effective_start_date", "effective_end_date",
               "job_status", "action", "change_source", "assignment_id"]]
    seeded_people = {a["worker_id"] for p in by_person.values() for a in p if a["assignment_id"] in seeded}
    return job, _defect_truth(job, by_person, seeded_people)


def _defect_truth(job: pd.DataFrame, by_person: dict[str, list[dict]], seeded_people: set[str]) -> pd.DataFrame:
    """Every period in which a person holds two active jobs (F07), or one active job on a PID the
    ledger shows they are not in (F08), evaluated from the rows themselves, day by day between
    change points. Independent of the SQL that finds them."""
    active = job[job["job_status"] == "Active"]
    out = []
    far = dt.date(9999, 12, 31)
    for person, js in active.groupby("person_id", sort=True):
        jobs = [(r.position_id, r.effective_start_date, r.effective_end_date or far) for r in js.itertuples()]
        ledger = [(a["position_id"], a["start_date"], a["end_date"] or far) for a in by_person[person]]
        if len(jobs) == 1 and person not in seeded_people:
            pid, s, e = jobs[0]
            if any(lp == pid and ls <= s and e <= le for lp, ls, le in ledger):
                continue                                   # one job, inside one ledger assignment: clean
        cuts = sorted({s for _, s, _ in jobs} | {e + ONE_DAY for _, _, e in jobs if e < far}
                      | {s for _, s, _ in ledger} | {e + ONE_DAY for _, _, e in ledger if e < far})
        cur = None
        for k, day in enumerate(cuts):
            if day > EXTRACT:
                break
            on = [j for j in jobs if j[1] <= day <= j[2]]
            if len(on) >= 2:
                flag, pid = "F07", min(p for p, _, _ in on)        # two active records (the same PID twice, or two PIDs)
            elif len(on) == 1 and not any(lp == on[0][0] and ls <= day <= le for lp, ls, le in ledger):
                flag, pid = "F08", on[0][0]
            else:
                flag, pid = None, None
            if cur and (cur["flag_code"], cur["position_id"]) != (flag, pid):
                cur["end_date"] = day - ONE_DAY
                out.append(cur)
                cur = None
            if flag and cur is None:
                cur = {"flag_code": flag, "person_id": person, "position_id": pid, "start_date": day}
        if cur:
            cur["end_date"] = None
            out.append(cur)
    t = pd.DataFrame(out, columns=["flag_code", "person_id", "position_id", "start_date", "end_date"])
    t = t[t["end_date"].isna() | (t["end_date"] >= dt.date.fromisoformat(ref.KS_HISTORY_KEEP_FROM))]
    t = t.sort_values(["start_date", "person_id", "flag_code"]).reset_index(drop=True)
    t.insert(0, "defect_id", [f"JD{n:06d}" for n in range(1, len(t) + 1)])
    t["origin"] = ["Seeded" if p in seeded_people else "PID ledger" for p in t["person_id"]]
    t["resolution"] = np.where(t["end_date"].isna(), "Open at extract", "Ended")
    t["detail"] = [
        (f"{p} holds two active job records (PID {pos})" if f == "F07"
         else f"{p}'s job on {pos} is still active; the PID ledger shows them out of it")
        for f, p, pos in zip(t["flag_code"], t["person_id"], t["position_id"])]
    return t


# --------------------------------------------------------------------------------- load log
def load_log(stream: np.random.Generator, rows_read: dict[str, callable]) -> pd.DataFrame:
    """The warehouse's daily runs, Jun 1, 2021 to Jul 1, 2026. rows_read[source](x) gives the rows a
    successful run reads: x is the data date for Bridgeway and Keystone, the start time for Helix."""
    first, last = dt.date.fromisoformat(ref.OPS_LOG_FROM), dt.date.fromisoformat(ref.OPS_LOG_TO)
    forced = {}
    for d, (src, nights) in ref.OPS_CLOSE_FAILURES.items():
        for k in range(nights):
            forced[dt.date.fromisoformat(d) + ONE_DAY - dt.timedelta(days=k)] = src
    out = []
    day = first
    while day <= last:
        close = day.day == 1
        bw_done = None
        for src, at, dur in (("BW", 0, (8, 14)), ("KS", None, (12, 22)), ("HLX", 0, (2, 5)), ("HLX", 12, (2, 5))):
            if src == "KS":
                sched = dt.datetime.combine(day, dt.time(0, 20))
            else:
                sched = dt.datetime.combine(day, dt.time(at, 0))
            u = stream.random()
            fail = (forced.get(day) == src and at in (0, None)) or (not close and u < ref.OPS_LOAD_FAIL[src])
            late = not fail and stream.random() < ref.OPS_LOAD_LATE[src]
            delay = stream.integers(1, 5) if not late else stream.integers(65, 7 * 60)
            start = sched + dt.timedelta(minutes=int(delay))
            if src == "KS" and bw_done is not None and bw_done > start:
                start = bw_done + dt.timedelta(minutes=1)       # Keystone waits for Bridgeway
            data_date = day - ONE_DAY if at in (0, None) else day        # 12:00 Helix reads the same day
            minutes = stream.integers(*dur) if not fail else stream.integers(1, 4)
            finish = start + dt.timedelta(minutes=int(minutes), seconds=int(stream.integers(0, 60)))
            if src == "BW":
                bw_done = finish
            out.append({"source_system": src, "scheduled_at": sched, "started_at": start, "finished_at": finish,
                        "status": "Failed" if fail else ("Late" if late else "Succeeded"),
                        "rows_read": None if fail else int(rows_read[src](start if src == "HLX" else data_date)),
                        "error_text": ref.OPS_LOAD_ERRORS[src] if fail else None})
        day += ONE_DAY
    log = pd.DataFrame(out).sort_values(["scheduled_at", "source_system"]).reset_index(drop=True)
    log.insert(0, "run_id", [f"LR{n:06d}" for n in range(1, len(log) + 1)])
    log["rows_read"] = log["rows_read"].astype("Int64")
    return log
