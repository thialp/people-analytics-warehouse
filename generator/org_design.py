"""
Org design data for Arcadia Systems (release 7, case study 7: Who Leads Where).

Arcadia's solid line (who reports to whom) lives in the job history. Release 7 adds what a
real HR system keeps beside it, and lets it drift the way it drifts in real life:

  * Matrix orgs. Keystone goes live with a matrix line on Jul 1, 2023: five region
    matrices and a country (or cluster) matrix for every country, each with a manager
    who can leave and leave the seat open. A cluster split in FY26 ends one matrix.
  * Matrix membership. Every person Keystone holds (employees and contingent workers)
    belongs to the country matrix of the office they sit in. After an international move
    the change lags; sometimes the old membership is never ended, sometimes the new one
    is never added. After the cluster split some members are never moved.
  * Role assignments. An HR partner and a Finance partner on every function and every
    unit led by an L1 leader, inherited by the departments below. The target's name
    carries its leader when the row was issued; after a leadership change some rows are
    never re-issued and keep naming the former leader.
  * Borrowed reporting lines. After the FY25 reorganization moved Data roles into Data &
    AI Platform, some people kept reporting to their old manager; after some department
    transfers the manager change waits for the person's next job change. Only
    `manager_worker_id` changes, on whole job records: no row, date, department, office,
    level or pay moves.
  * The answer key, `gen_org_drift_truth`: every seeded gap with its cause and dates.

Everything draws from its own random stream, after the existing simulation, so no earlier
number moves. Arcadia Systems and Keystone HR are fictional; all data is synthetic.

Standalone (reads data/raw, writes the release 7 tables and the updated job history to OUT):

    python generator/org_design.py --out /tmp/r7
"""

from __future__ import annotations

import datetime as dt
from collections import defaultdict

import numpy as np
import pandas as pd

# --------------------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------------------
MATRIX_GO_LIVE = dt.date(2023, 7, 1)           # start of FY24
CLUSTER_SPLIT_DATE = dt.date(2025, 11, 1)      # FY26 Q2: Southern Europe splits into Iberia and France

# Borrowed reporting lines
REORG_KEEP_OLD_MANAGER = 0.30                  # share of people moved by the reorg who keep their old manager
TRANSFER_KEEP_OLD_MANAGER = 0.07               # share of transfers whose manager change waits
CARRY_TO_NEXT_RECORD = {"reorg": 0.60, "transfer": 0.35}   # the borrowed line survives the next job change

# Matrix membership after an international move (or a cluster split)
MATRIX_LAG_MEAN_DAYS = 12                      # days before the matrix change is keyed
MATRIX_NEVER_MOVED = 0.10                      # the move is never keyed: the old matrix stays
MATRIX_NEVER_ENDED = 0.06                      # the new matrix is added, the old one never ended
SPLIT_NEVER_MOVED = 0.05                       # left in the ended cluster after the split
MATRIX_SUCCESSOR_MEAN_DAYS = 75                # a matrix leader seat stays open this long on average

# Role assignments
ROLES = ["HR Partner", "Finance Partner"]
STALE_AFTER_LEADER_CHANGE = {"Direct": 0.15, "Inherited": 0.55}
ASSIGNEE_REPLACEMENT_DAYS = (5, 40)

# Country matrices: (code, name, region, countries covered, active from, active to)
COUNTRY_MATRICES = [
    ("MX-US", "Country Leader · United States", "North America", "US", None, None),
    ("MX-CA", "Country Leader · Canada", "North America", "CA", None, None),
    ("MX-MX", "Country Leader · Mexico", "Latin America", "MX", None, None),
    ("MX-BR", "Country Leader · Brazil", "Latin America", "BR", None, None),
    ("MX-UKI", "Cluster Leader · UK & Ireland", "Europe", "GB;IE", None, None),
    ("MX-DACH", "Cluster Leader · DACH", "Europe", "DE;CH", None, None),
    ("MX-SEU", "Cluster Leader · Southern Europe", "Europe", "ES;PT;FR", None, CLUSTER_SPLIT_DATE),
    ("MX-IBE", "Cluster Leader · Iberia", "Europe", "ES;PT", CLUSTER_SPLIT_DATE, None),
    ("MX-FR", "Country Leader · France", "Europe", "FR", CLUSTER_SPLIT_DATE, None),
    ("MX-BNN", "Cluster Leader · Benelux & Nordics", "Europe", "NL;SE", None, None),
    ("MX-PL", "Country Leader · Poland", "Europe", "PL", None, None),
    ("MX-AE", "Country Leader · United Arab Emirates", "Middle East & Africa", "AE", None, None),
    ("MX-ZA", "Country Leader · South Africa", "Middle East & Africa", "ZA", None, None),
    ("MX-IN", "Country Leader · India", "Asia Pacific", "IN", None, None),
    ("MX-ANZ", "Country Leader · Australia", "Asia Pacific", "AU", None, None),
    ("MX-JP", "Country Leader · Japan", "Asia Pacific", "JP", None, None),
    ("MX-KR", "Country Leader · Korea", "Asia Pacific", "KR", None, None),
    ("MX-SEA", "Cluster Leader · Southeast Asia", "Asia Pacific", "SG;PH", None, None),
]
REGION_MATRICES = [
    ("MX-R-NA", "Region President · North America", "North America"),
    ("MX-R-LA", "Region President · Latin America", "Latin America"),
    ("MX-R-EU", "Region President · Europe", "Europe"),
    ("MX-R-MEA", "Region President · Middle East & Africa", "Middle East & Africa"),
    ("MX-R-AP", "Region President · Asia Pacific", "Asia Pacific"),
]

# The function that usually hires each job family; shared families are hired everywhere
JOB_FAMILY_HOME = [
    ("SWE", "Technology", False), ("ITS", "Technology", False), ("SEC", "Technology", False),
    ("PRD", "Product", False), ("DSN", "Product", False),
    ("SAL", "Commercial", False), ("CSM", "Commercial", False),
    ("MKT", "Marketing", False), ("FIN", "Finance", False), ("HRM", "People", False),
    ("LGL", "Legal & Compliance", False), ("EXE", "Executive", False),
    ("DAT", None, True), ("OPS", None, True),
]

# Where each function means its people to sit: the offices that hold its training, its senior managers and its
# support (release 7). A person is "in the hub" when their office is one of their own function's hubs. The hubs follow
# where each function already concentrates; nobody is moved.
FUNCTION_HUBS = [
    ("Technology", "LOC-001", "Austin engineering hub"), ("Technology", "LOC-015", "India engineering hub"),
    ("Technology", "LOC-016", "India engineering hub"), ("Technology", "LOC-033", "India engineering hub"),
    ("Technology", "LOC-013", "Poland engineering hub"), ("Technology", "LOC-014", "Poland engineering hub"),
    ("Operations", "LOC-015", "India operations hub"), ("Operations", "LOC-016", "India operations hub"),
    ("Operations", "LOC-001", "Austin headquarters"), ("Operations", "LOC-013", "Poland operations hub"),
    ("Operations", "LOC-014", "Poland operations hub"), ("Operations", "LOC-036", "Manila operations hub"),
    ("Product", "LOC-001", "Austin headquarters"), ("Product", "LOC-015", "India product hub"),
    ("Product", "LOC-016", "India product hub"), ("Product", "LOC-009", "London product hub"),
    ("Product", "LOC-003", "San Francisco product hub"),
    ("Commercial", "LOC-001", "Austin headquarters"), ("Commercial", "LOC-009", "London sales hub"),
    ("Commercial", "LOC-002", "New York sales hub"), ("Commercial", "LOC-007", "Sao Paulo sales hub"),
    ("Commercial", "LOC-017", "Singapore sales hub"), ("Commercial", "LOC-015", "India sales hub"),
    ("Commercial", "LOC-016", "India sales hub"),
    ("Marketing", "LOC-001", "Austin headquarters"), ("Marketing", "LOC-002", "New York marketing hub"),
    ("Marketing", "LOC-009", "London marketing hub"), ("Marketing", "LOC-015", "India marketing hub"),
    ("Finance", "LOC-001", "Austin headquarters"), ("Finance", "LOC-009", "London finance hub"),
    ("Finance", "LOC-015", "India finance hub"), ("Finance", "LOC-016", "India finance hub"),
    ("People", "LOC-001", "Austin headquarters"), ("People", "LOC-009", "London people hub"),
    ("People", "LOC-015", "India people hub"), ("People", "LOC-016", "India people hub"),
    ("Legal & Compliance", "LOC-001", "Austin headquarters"), ("Legal & Compliance", "LOC-009", "London legal hub"),
    ("Legal & Compliance", "LOC-002", "New York legal hub"), ("Legal & Compliance", "LOC-015", "India legal hub"),
    ("Executive", "LOC-001", "Austin headquarters"),
]

ONE_DAY = dt.timedelta(days=1)


def _d(x) -> dt.date | None:
    if x is None or (isinstance(x, float) and np.isnan(x)) or x == "" or pd.isna(x):
        return None
    return x if isinstance(x, dt.date) else dt.date.fromisoformat(str(x)[:10])


def _s(d: dt.date | None) -> str | None:
    return d.isoformat() if d else None


# ======================================================================================
# 1. Borrowed reporting lines
# ======================================================================================
class _Jobs:
    """The job history indexed for fast look-ups: records by worker, in date order."""

    def __init__(self, job: pd.DataFrame, workers: pd.DataFrame, horizon: dt.date):
        self.horizon = horizon
        self.by_worker: dict[str, list[dict]] = defaultdict(list)
        for r in job.to_dict("records"):
            r["_s"], r["_e"] = _d(r["effective_start_date"]), _d(r["effective_end_date"])
            r["_pm"] = str(r["is_people_manager"]) == "True"
            r["_lvl"] = int(r["job_level"])
            self.by_worker[r["worker_id"]].append(r)
        for rs in self.by_worker.values():
            rs.sort(key=lambda r: r["_s"])
        self.term = {w: _d(t) for w, t in zip(workers["worker_id"], workers["termination_date"])}
        R = job[["worker_id", "location_id", "department_id", "job_profile_id", "job_level", "is_people_manager"]].copy()
        R["s"] = pd.to_datetime(job["effective_start_date"]).dt.date
        R["e"] = pd.to_datetime(job["effective_end_date"]).dt.date.where(job["effective_end_date"].notna(), horizon)
        t = workers.set_index("worker_id")["termination_date"]
        R["t"] = pd.to_datetime(R["worker_id"].map(t)).dt.date
        R["t"] = R["t"].where(R["t"].notna(), dt.date(9999, 12, 31))
        R["lvl"] = R["job_level"].astype(int)
        R["pm"] = R["is_people_manager"].astype(str) == "True"
        self.R = R

    def on(self, day: dt.date) -> pd.DataFrame:
        """Every worker's record on `day` (employed that day)."""
        R = self.R
        return R[(R["s"] <= day) & (R["e"] >= day) & (R["t"] > day)]

    def end(self, r) -> dt.date:
        return r["_e"] or self.horizon

    def manages_through(self, mgr: str, start: dt.date, end: dt.date, level: int, dept: str) -> bool:
        """Can `mgr` be the manager of an IC at `level` in `dept` for every day of [start, end]?"""
        t = self.term.get(mgr)
        if t is not None and t <= end:
            return False
        day = start
        for r in self.by_worker.get(mgr, []):
            if self.end(r) < day or r["_s"] > end:
                continue
            if r["_s"] > day:            # a hole in the manager's records
                return False
            if not r["_pm"] or r["department_id"] == dept:
                return False
            if (level >= 7 and r["_lvl"] <= level) or (level < 7 and r["_lvl"] < level):
                return False
            day = self.end(r) + ONE_DAY
            if day > end:
                return True
        return False


def borrowed_reporting(stream: np.random.Generator, job: pd.DataFrame, workers: pd.DataFrame,
                       horizon: dt.date) -> tuple[pd.DataFrame, list[dict]]:
    """Let some people keep their old manager after the reorg or a transfer.

    Returns the job history with `manager_worker_id` replaced on the borrowed records (no
    other column, no row added) and one answer-key row per borrowed run.
    """
    J = _Jobs(job, workers, horizon)
    new_manager: dict[str, str] = {}
    truth: list[dict] = []
    for wid, rs in J.by_worker.items():
        for i, r in enumerate(rs):
            cause = {"Reorganization": "reorg", "Transfer": "transfer"}.get(r["action_reason"])
            if cause is None or i == 0 or r["_pm"] or str(r["leads_org_unit_id"]) not in ("nan", "None", ""):
                continue
            keep = REORG_KEEP_OLD_MANAGER if cause == "reorg" else TRANSFER_KEEP_OLD_MANAGER
            draw = stream.random()
            old = rs[i - 1]["manager_worker_id"]
            if draw >= keep or not isinstance(old, str) or rs[i - 1]["department_id"] == r["department_id"]:
                continue
            run = []
            for k in range(i, len(rs)):
                rk = rs[k]
                if k > i and (rk["department_id"] != r["department_id"] or stream.random() >= CARRY_TO_NEXT_RECORD[cause]):
                    break
                if rk["_pm"] or not J.manages_through(old, rk["_s"], J.end(rk), rk["_lvl"], rk["department_id"]):
                    break
                run.append(rk)
            if not run:
                continue
            for rk in run:
                new_manager[rk["job_record_id"]] = old
            last = run[-1]
            truth.append({
                "signal_code": "S1", "cause": "Reorganization" if cause == "reorg" else "Transfer",
                "person_id": wid, "matrix_org_id": None, "assignment_id": None,
                "job_record_ids": ";".join(x["job_record_id"] for x in run),
                "original_values": ";".join(str(x["manager_worker_id"]) for x in run),
                "seeded_value": old,
                "start_date": _s(run[0]["_s"]), "end_date": _s(last["_e"]),
                "detail": f"Moved to {r['department_id']} on {_s(r['_s'])} but kept reporting to {old}, "
                          f"a manager in {rs[i - 1]['department_id']}"})
    out = job.copy()
    hit = out["job_record_id"].isin(new_manager)
    out.loc[hit, "manager_worker_id"] = out.loc[hit, "job_record_id"].map(new_manager)
    return out, truth


# ======================================================================================
# 2. People and where they sit (employees and contingent workers in Keystone)
# ======================================================================================
def person_locations(job: pd.DataFrame, workers: pd.DataFrame, ks_cw: pd.DataFrame, office_country: dict,
                     horizon: dt.date) -> dict[str, list[tuple[dt.date, dt.date, str]]]:
    """Country segments per person: [(start, end, country)], merged across records."""
    seg: dict[str, list[list]] = defaultdict(list)
    term = {w: _d(t) for w, t in zip(workers["worker_id"], workers["termination_date"])}

    def add(pid, s, e, c):
        if s is None or (e is not None and e < s):
            return
        e = e or horizon
        lst = seg[pid]
        if lst and lst[-1][2] == c and lst[-1][1] + ONE_DAY >= s:
            lst[-1][1] = max(lst[-1][1], e)
        else:
            lst.append([s, e, c])

    for r in job.sort_values(["worker_id", "effective_start_date"]).itertuples(index=False):
        e = _d(r.effective_end_date)
        t = term.get(r.worker_id)
        if t is not None and (e is None or e > t):
            e = t
        add(r.worker_id, _d(r.effective_start_date), e, office_country[r.location_id])
    act = ks_cw[ks_cw["status"] == "Active"].sort_values(["person_id", "effective_start_date"])
    for r in act.itertuples(index=False):
        if r.location_id in office_country:
            add(r.person_id, _d(r.effective_start_date), _d(r.effective_end_date), office_country[r.location_id])
    return {p: [tuple(x) for x in v] for p, v in seg.items()}


# ======================================================================================
# 3. Matrix orgs and their leaders
# ======================================================================================
def _matrix_leaders(stream, job, workers, office_country, office_region, horizon):
    """Pick and replace the leader of every matrix: the most senior employee who sits in its
    countries (Commercial first). When a leader leaves, the seat is open until a successor
    is named."""
    J = _Jobs(job, workers, horizon)
    def candidates(countries: set[str] | None, region: str | None, on: dt.date, exclude: set[str]):
        x = J.on(on)
        x = x[(x["lvl"] >= 6) & x["pm"] & ~x["job_profile_id"].str.startswith("EXE") & ~x["worker_id"].isin(exclude)]
        if countries:
            x = x[x["location_id"].map(office_country).isin(countries)]
        else:
            x = x[x["location_id"].map(office_region) == region]
        best = [(int(l), d.startswith("D-3"), w) for l, d, w in zip(x["lvl"], x["department_id"], x["worker_id"])]
        best.sort(reverse=True)
        return best

    def stays(wid, countries, region, frm):
        """Last day `wid` sits in the matrix's countries (or region), from `frm`."""
        last = None
        for r in J.by_worker[wid]:
            if J.end(r) < frm:
                continue
            c = office_country[r["location_id"]]
            ok = (countries and c in countries) or (region and office_region[r["location_id"]] == region)
            if not ok:
                break
            last = J.end(r)
        t = J.term.get(wid)
        if t is not None and last is not None:
            last = min(last, t)
        return last

    specs = [(c, n, reg, set(cov.split(";")), s or MATRIX_GO_LIVE, e, "Country") for c, n, reg, cov, s, e in COUNTRY_MATRICES]
    specs += [(c, n, reg, None, MATRIX_GO_LIVE, None, "Region") for c, n, reg in REGION_MATRICES]
    rows, taken = [], set()
    for code, name, region, countries, start, end, kind in specs:
        day = start
        stop = (end - ONE_DAY) if end else horizon
        while day <= stop:
            pool = candidates(countries, region if kind == "Region" else None, day, taken)
            if not pool:
                rows.append((code, day, stop, None))
                break
            top = pool[: max(1, min(3, len(pool)))]
            wid = top[int(stream.integers(len(top)))][2]
            taken.add(wid)
            last = stays(wid, countries, region if kind == "Region" else None, day) or stop
            last = min(last, stop)
            rows.append((code, day, last, wid))
            if last >= stop:
                break
            gap = int(stream.exponential(MATRIX_SUCCESSOR_MEAN_DAYS)) + 1
            vacant_end = min(last + dt.timedelta(days=gap), stop)
            rows.append((code, last + ONE_DAY, vacant_end, None))
            day = vacant_end + ONE_DAY
    return rows


def matrix_orgs(stream, job, workers, office_country, office_region, horizon, report_date) -> pd.DataFrame:
    leaders = _matrix_leaders(stream, job, workers, office_country, office_region, horizon)
    info = {c: (n, reg, cov, "Country", s or MATRIX_GO_LIVE, e) for c, n, reg, cov, s, e in COUNTRY_MATRICES}
    info.update({c: (n, reg, None, "Region", MATRIX_GO_LIVE, None) for c, n, reg in REGION_MATRICES})
    parent = {reg: c for c, _, reg in REGION_MATRICES}
    out, n = [], 0
    by_code = defaultdict(list)
    for code, s, e, wid in leaders:
        by_code[code].append((s, e, wid))
    for code, segs in by_code.items():
        name, region, cov, kind, start, end = info[code]
        segs.sort()
        for j, (s, e, wid) in enumerate(segs):
            open_end = (j == len(segs) - 1) and end is None and e >= horizon
            n += 1
            out.append({"matrix_record_id": f"MR{n:05d}", "matrix_org_id": code, "matrix_org_name": name,
                        "matrix_type": kind, "region": region,
                        "parent_matrix_org_id": None if kind == "Region" else parent[region],
                        "covers_country_codes": cov, "effective_start_date": _s(s),
                        "effective_end_date": None if open_end else _s(e),
                        "manager_worker_id": wid, "status": "Active", "inactive_date": None,
                        "created_date": _s(start)})
        if end is not None:   # the ended matrix keeps one Inactive record, open, so members left in it still point at it
            n += 1
            out.append({"matrix_record_id": f"MR{n:05d}", "matrix_org_id": code, "matrix_org_name": name,
                        "matrix_type": kind, "region": region, "parent_matrix_org_id": parent[region],
                        "covers_country_codes": cov, "effective_start_date": _s(end), "effective_end_date": None,
                        "manager_worker_id": None, "status": "Inactive", "inactive_date": _s(end),
                        "created_date": _s(start)})
    return pd.DataFrame(out).sort_values(["matrix_org_id", "effective_start_date"]).reset_index(drop=True)


# ======================================================================================
# 4. Matrix membership
# ======================================================================================
def _matrix_for(country: str, on: dt.date) -> str:
    for c, _, _, cov, s, e in COUNTRY_MATRICES:
        if country in cov.split(";") and (s is None or on >= s) and (e is None or on < e):
            return c
    raise KeyError((country, on))


def _covers(mx: str, country: str) -> bool:
    for c, _, _, cov, _, _ in COUNTRY_MATRICES:
        if c == mx:
            return country in cov.split(";")
    return False


def matrix_membership(stream, locations: dict, person_type: dict, horizon: dt.date):
    """Country matrix memberships, with the drift a real HR system shows.

    After a move to a country the current matrix does not cover, the change is keyed after a lag
    (M1 while it waits), sometimes never (M1 until the person moves again or leaves), and
    sometimes the new matrix is added without ending the old one (M2). At the cluster split some
    members stay in the ended matrix (M3). Every seeded case closes on the day the membership it
    describes ends.
    """
    rows, truth = [], []
    n = 0

    def add(pid, mx, s, reason):
        nonlocal n
        n += 1
        rows.append({"membership_id": f"MM{n:07d}", "person_id": pid, "person_type": person_type[pid],
                     "matrix_org_id": mx, "effective_start_date": _s(s), "effective_end_date": None,
                     "assigned_reason": reason})
        return rows[-1]

    for pid in sorted(locations):
        segs = [(max(s, MATRIX_GO_LIVE), e, c) for s, e, c in locations[pid] if e >= MATRIX_GO_LIVE]
        if not segs:
            continue
        mine: list[dict] = []        # this person's open truths

        def seed(code, cause, mx, should, start, end, detail):
            t = {"signal_code": code, "cause": cause, "person_id": pid, "matrix_org_id": mx, "assignment_id": None,
                 "job_record_ids": None, "original_values": None, "seeded_value": should, "start_date": _s(start),
                 "end_date": _s(end) if end else None, "detail": detail}
            truth.append(t)
            if end is None:
                mine.append(t)

        def close(m: dict, last_day: dt.date):
            m["effective_end_date"] = _s(last_day)
            for t in mine:
                if t["end_date"] is None and t["matrix_org_id"] == m["matrix_org_id"]:
                    t["end_date"] = _s(last_day)

        cur, extra = None, []
        for k, (s, e, c) in enumerate(segs):
            target = _matrix_for(c, s)
            for m in [cur] + extra if cur else []:      # moving back into a covered country ends M1
                if _covers(m["matrix_org_id"], c):
                    for t in mine:
                        if t["end_date"] is None and t["signal_code"] == "M1" and t["matrix_org_id"] == m["matrix_org_id"]:
                            t["end_date"] = _s(s - ONE_DAY)
            if cur is None:
                cur = add(pid, target, s, "Matrix go-live" if s == MATRIX_GO_LIVE else "Hire")
            elif cur["matrix_org_id"] != target:
                old = cur["matrix_org_id"]
                if _covers(old, c):          # still covered (an ended cluster): keyed with the move
                    close(cur, s - ONE_DAY)
                    cur = add(pid, target, s, "Location change")
                else:
                    lag = int(stream.exponential(MATRIX_LAG_MEAN_DAYS))
                    key_day = min(s + dt.timedelta(days=lag), e)
                    u = stream.random()
                    if u < MATRIX_NEVER_MOVED:
                        seed("M1", "International move not keyed", old, target, s, None,
                             f"Moved to {c} on {_s(s)}; the matrix change to {target} was never keyed")
                    else:
                        if key_day > s:
                            seed("M1", "Matrix change keyed late", old, target, s, key_day - ONE_DAY,
                                 f"Moved to {c} on {_s(s)}; matrix keyed {(key_day - s).days} days later")
                        if u < MATRIX_NEVER_MOVED + MATRIX_NEVER_ENDED:
                            seed("M2", "Old membership never ended", old, target, key_day, None,
                                 f"Added to {target} on {_s(key_day)}; {old} was never ended")
                            extra.append(cur)
                        else:
                            close(cur, key_day - ONE_DAY)
                        cur = add(pid, target, key_day, "Location change")
            # the cluster split inside this segment
            if cur["matrix_org_id"] == "MX-SEU" and s < CLUSTER_SPLIT_DATE <= e:
                new = _matrix_for(c, CLUSTER_SPLIT_DATE)
                if stream.random() < SPLIT_NEVER_MOVED:
                    seed("M3", "Left in an ended matrix", "MX-SEU", new, CLUSTER_SPLIT_DATE, None,
                         f"Southern Europe ended on {_s(CLUSTER_SPLIT_DATE)}; never moved to {new}")
                else:
                    close(cur, CLUSTER_SPLIT_DATE - ONE_DAY)
                    cur = add(pid, new, CLUSTER_SPLIT_DATE, "Matrix reorganization")
        # leaving ends every open membership, and every case still open
        last_end = segs[-1][1]
        if last_end < horizon:
            for m in [cur] + extra:
                if m["effective_end_date"] is None:
                    m["effective_end_date"] = _s(last_end)
            for t in mine:
                if t["end_date"] is None:
                    t["end_date"] = _s(last_end)
    return pd.DataFrame(rows), truth


# ======================================================================================
# 5. Role assignments
# ======================================================================================
def role_assignments(stream, job, workers, org_units, departments, horizon):
    """HR and Finance partners on every function and every unit an L1 leads; inherited below."""
    J = _Jobs(job, workers, horizon)
    names = {w: f"{f} {l}" for w, f, l in zip(workers["worker_id"], workers["first_name"], workers["last_name"])}
    # unit leaders over time: [(start, end, worker)]
    lead = defaultdict(list)
    for wid, rs in J.by_worker.items():
        for r in rs:
            u = r["leads_org_unit_id"]
            if isinstance(u, str) and u:
                t = J.term.get(wid)
                e = min(J.end(r), t) if t else J.end(r)
                if lead[u] and lead[u][-1][2] == wid and lead[u][-1][1] + ONE_DAY >= r["_s"]:
                    lead[u][-1] = (lead[u][-1][0], max(lead[u][-1][1], e), wid)
                else:
                    lead[u].append((r["_s"], e, wid))
    for u in lead:
        lead[u].sort()
    ou = org_units.set_index("org_unit_id")
    unit_name = ou["org_unit_name"].to_dict()
    unit_name.update(dict(zip(departments["department_id"], departments["department_name"])))
    parent = ou["parent_org_unit_id"].to_dict()
    parent.update(dict(zip(departments["department_id"], departments["parent_org_unit_id"])))
    functions = [u for u, t in ou["org_unit_type"].items() if t == "Function"]
    direct_units = list(functions) + [u for u in parent if parent.get(u) in functions]
    children = defaultdict(list)
    for u, p in parent.items():
        if isinstance(p, str):
            children[p].append(u)

    # assignee pools: HR partners from People (HRM), Finance partners from Finance (FIN), levels 6-8
    def pool(prefix, on):
        x = J.on(on)
        x = x[x["job_profile_id"].str.startswith(prefix) & x["lvl"].between(6, 8)]
        return sorted(x["worker_id"].tolist())

    def until(wid, frm, prefix):
        last = None
        for r in J.by_worker[wid]:
            if J.end(r) < frm:
                continue
            if not (str(r["job_profile_id"]).startswith(prefix) and 6 <= r["_lvl"] <= 8):
                break
            last = J.end(r)
        t = J.term.get(wid)
        return min(last, t) if (last and t) else last

    def leader_on(u, day):
        for s, e, w in lead.get(u, []):
            if s <= day <= e:
                return w
        return None

    rows, truth, n = [], [], 0

    def issue(role, wid, unit, via, src, s, e, leader):
        nonlocal n
        n += 1
        nm = unit_name[unit] + (f" ({names[leader]})" if leader else " (no leader)") + (" (Inherited)" if via == "Inherited" else "")
        rows.append({"assignment_id": f"RA{n:06d}", "role_name": role, "assignee_worker_id": wid,
                     "target_org_unit_id": unit, "target_org_name": nm, "named_leader_worker_id": leader,
                     "assigned_via": via, "inherited_from_org_unit_id": src,
                     "effective_start_date": _s(s), "effective_end_date": None if e is None or e >= horizon else _s(e)})
        return rows[-1]

    prefixes = {"HR Partner": "HRM", "Finance Partner": "FIN"}
    for role in ROLES:
        prefix = prefixes[role]
        for unit in sorted(direct_units):
            targets = [(unit, "Direct", None)] + [(c, "Inherited", unit) for c in sorted(children.get(unit, []))
                                                  if c not in direct_units]
            day = MATRIX_GO_LIVE
            while day <= horizon:
                cands = pool(prefix, day)
                if not cands:
                    break
                wid = cands[int(stream.integers(len(cands)))]
                end_assignee = until(wid, day, prefix) or horizon
                # issue rows for each target; re-issue on leader changes inside the assignee's tenure
                for tgt, via, src in targets:
                    seg_start = day
                    while seg_start <= end_assignee:
                        ldr = leader_on(tgt, seg_start)
                        # the next change of the target's leader: the current leader's last day, or,
                        # while the unit has no leader, the day before the next one starts
                        nxt = None
                        for s, e, w in lead.get(tgt, []):
                            if s <= seg_start <= e:
                                nxt = e
                                break
                            if s > seg_start:
                                nxt = s - ONE_DAY
                                break
                        seg_end = min(nxt or end_assignee, end_assignee)
                        row = issue(role, wid, tgt, via, src, seg_start, seg_end, ldr)
                        if seg_end >= end_assignee:
                            break
                        # leader changes on seg_end + 1: re-issued, or the row keeps naming the former leader
                        if ldr and stream.random() < STALE_AFTER_LEADER_CHANGE[via]:
                            row["effective_end_date"] = None if end_assignee >= horizon else _s(end_assignee)
                            truth.append({"signal_code": "R1", "cause": "Not re-issued after a leadership change",
                                          "person_id": None, "matrix_org_id": None, "assignment_id": row["assignment_id"],
                                          "job_record_ids": None, "original_values": ldr,
                                          "seeded_value": leader_on(tgt, seg_end + ONE_DAY),
                                          "start_date": _s(seg_end + ONE_DAY), "end_date": row["effective_end_date"],
                                          "detail": f"{role} row on {tgt} still names {ldr} after {_s(seg_end + ONE_DAY)}"})
                            break
                        seg_start = seg_end + ONE_DAY
                if end_assignee >= horizon:
                    break
                lo, hi = ASSIGNEE_REPLACEMENT_DAYS
                day = end_assignee + dt.timedelta(days=int(stream.integers(lo, hi + 1)))
    return pd.DataFrame(rows), truth


# ======================================================================================
# 6. Everything together
# ======================================================================================
def build(stream: np.random.Generator, job: pd.DataFrame, workers: pd.DataFrame, ks_cw: pd.DataFrame,
          offices: pd.DataFrame, org_units: pd.DataFrame, departments: pd.DataFrame,
          horizon: dt.date, report_date: dt.date) -> dict[str, pd.DataFrame]:
    """All release 7 org design tables. `horizon` is the data-through date of Keystone Core HR."""
    office_country = dict(zip(offices["location_id"], offices["country_code"]))
    office_region = dict(zip(offices["location_id"], offices["region"]))
    s_borrow, s_mx, s_mem, s_ra = (np.random.default_rng(stream.integers(2**63)) for _ in range(4))

    job7, truth = borrowed_reporting(s_borrow, job, workers, horizon)
    mx = matrix_orgs(s_mx, job7, workers, office_country, office_region, horizon, report_date)
    for r in mx[(mx["manager_worker_id"].isna()) & (mx["status"] == "Active")].itertuples(index=False):
        truth.append({"signal_code": "M3", "cause": "Matrix leader seat open", "person_id": None,
                      "matrix_org_id": r.matrix_org_id, "assignment_id": None, "job_record_ids": None,
                      "original_values": None, "seeded_value": None, "start_date": r.effective_start_date,
                      "end_date": r.effective_end_date, "detail": f"{r.matrix_org_name} has no leader"})
    locs = person_locations(job7, workers, ks_cw, office_country, horizon)
    cw_ids = set(ks_cw["person_id"])
    ptype = {p: ("Contingent" if p in cw_ids else "Employee") for p in locs}
    mem, t2 = matrix_membership(s_mem, locs, ptype, horizon)
    ra, t3 = role_assignments(s_ra, job7, workers, org_units, departments, horizon)
    tr = pd.DataFrame(truth + t2 + t3)
    tr.insert(0, "drift_id", [f"OD{n:06d}" for n in range(1, len(tr) + 1)])
    home = pd.DataFrame(JOB_FAMILY_HOME, columns=["job_family_code", "home_function", "is_shared"])
    hubs = pd.DataFrame(FUNCTION_HUBS, columns=["function_name", "location_id", "hub_name"])
    return {"fact_job_history": job7, "ks_matrix_org": mx, "ks_matrix_membership": mem,
            "ks_role_assignment": ra, "ref_job_family_home": home, "ref_function_hub": hubs, "gen_org_drift_truth": tr}


if __name__ == "__main__":
    import argparse
    from pathlib import Path
    import time

    import reference_data as ref

    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", type=Path, default=Path(__file__).resolve().parents[1] / "data" / "raw")
    ap.add_argument("--out", type=Path, required=True)
    a = ap.parse_args()
    t0 = time.time()
    rd = lambda n: pd.read_csv(a.raw / f"{n}.csv", dtype=str, keep_default_na=False, na_values=[""])
    key = int.from_bytes("org_design".encode(), "big") % (2**63)
    st = np.random.default_rng(np.random.SeedSequence([20261009, key]))
    res = build(st, rd("fact_job_history"), rd("dim_worker"), rd("ks_contingent_worker"), rd("dim_location"),
                rd("dim_org_unit"), rd("dim_department"), dt.date.fromisoformat(ref.DATA_THROUGH),
                dt.date.fromisoformat(ref.LAST_SNAPSHOT))
    a.out.mkdir(parents=True, exist_ok=True)
    for name, df in res.items():
        df.to_csv(a.out / f"{name}.csv", index=False, lineterminator="\n")
        print(f"  {name:<26} {len(df):>9,} rows")
    print(f"done in {time.time() - t0:.0f}s")
