"""
Demand and the Monte Carlo simulation (release 5).

For one forecast origin (a quarter-end) and the quarters after it that a known plan covers:

  1. Who is already waiting: every employee requisition approved by the origin and not yet filled
     or cancelled, with how long it has waited.
  2. New PIDs to fill, per department x office x quarter:
       backfills   headcount x the backfill rate per head of its function and country (last eight
                   quarters), times the fiscal quarter's seasonal index;
       net-new     the plan's net-new PIDs for its cost center, times how many net-new PIDs the
                   function opened per planned one (last four quarters), split across the cost
                   center's offices by their recent share;
       immediate   refills on the day of approval (successions), at their recent pace; they are
                   filled the day they open and never stand vacant.
  3. Each PID waits until the fill model says it is filled: period by period, a random draw
     against its fill chance. Repeated DRAWS times, each a possible future.

Out: for each draw, department x office x quarter, PIDs opened, PIDs filled and PIDs still
vacant at the quarter-end. Sums over any selection, then percentiles across draws, give the
likely range; percentiles themselves never add up across a selection, draws do.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import data as D
import fill_model as FM
import settings as S


@dataclass
class Origin:
    origin: pd.Timestamp
    targets: list[pd.Timestamp]          # quarter-ends forecast
    target_starts: list[pd.Timestamp]


def _quarter_start(qe: pd.Timestamp) -> pd.Timestamp:
    return (qe - pd.offsets.QuarterEnd(1)) + pd.Timedelta(days=1)


def _fiscal_quarter(qe: pd.Timestamp) -> int:
    return (qe.month - 7) % 12 // 3 + 1


def _trailing_ends(origin: pd.Timestamp, n: int) -> list[pd.Timestamp]:
    """The n quarter-ends up to and including `origin`."""
    return [origin - pd.offsets.QuarterEnd(i) if i else origin for i in range(n)][::-1]


class Demand:
    """Rates and mixes estimated from what was known on the origin date."""

    def __init__(self, inp: D.Inputs, model: FM.FillModel, origin: pd.Timestamp, targets: list[pd.Timestamp]):
        self.inp, self.model, self.origin, self.targets = inp, model, origin, targets
        cells = inp.cells
        self.cells = cells
        self.cell_index = {(d, l): i for i, (d, l) in enumerate(zip(cells["department_id"], cells["location_id"]))}
        self.f_idx = model.index(cells["function_name"], model.functions)
        self.c_idx = model.index(cells["country_code"], model.countries)
        reqs = inp.reqs
        rate_start = _quarter_start(_trailing_ends(origin, S.RATE_QUARTERS)[0])
        self.recent = reqs[(reqs["approved_date"] >= rate_start) & (reqs["approved_date"] <= origin)].copy()
        self.recent["cell"] = [self.cell_index.get((d, l), -1) for d, l in zip(self.recent["department_id"], self.recent["location_id"])]
        self.recent = self.recent[self.recent["cell"] >= 0]
        hc = inp.headcount
        self.head_now = np.zeros(len(cells))
        now = hc[hc["quarter_end_date"] == origin]
        for d, l, h in zip(now["department_id"], now["location_id"], now["headcount"]):
            i = self.cell_index.get((d, l))
            if i is not None:
                self.head_now[i] = h
        self._backfill_rates(hc, rate_start)
        self._immediate()
        self._net_new()
        self._band_mix()

    # -- backfills: rate per head by function x country, with a fiscal-quarter seasonal index
    def _backfill_rates(self, hc: pd.DataFrame, rate_start: pd.Timestamp):
        ends = _trailing_ends(self.origin, S.RATE_QUARTERS)
        h = hc[hc["quarter_end_date"].isin(ends)].merge(self.cells[["department_id", "location_id", "function_name", "country_code"]])
        head_q = h.groupby(["function_name", "country_code"])["headcount"].sum()          # head-quarters
        bf = self.recent[~self.recent["is_net_new"] & ~self.recent["is_immediate"]]
        n = bf.groupby(["function_name", "country_code"]).size()
        rate = (n / head_q).fillna(0.0)
        fn_rate = (bf.groupby("function_name").size() / h.groupby("function_name")["headcount"].sum()).fillna(0.0)
        self.bf_rate = np.array([rate.get((f, c), fn_rate.get(f, 0.0)) for f, c in
                                 zip(self.cells["function_name"], self.cells["country_code"])])
        fq = bf["approved_date"].map(lambda d: _fiscal_quarter(d + pd.offsets.QuarterEnd(0)))
        counts = fq.value_counts().reindex([1, 2, 3, 4], fill_value=0).to_numpy(float)
        self.season = counts / counts.mean() if counts.sum() else np.ones(4)
        # how much a quarter's backfill openings vary around the rate, beyond chance (Poisson): the
        # spread of log(opened / expected) over the last eight quarters, less the Poisson part
        per_q = bf.groupby(bf["approved_date"] + pd.offsets.QuarterEnd(0)).size().reindex(ends, fill_value=0)
        head_by_q = h.groupby("quarter_end_date")["headcount"].sum().reindex(ends)
        prev_head = head_by_q.shift(1).fillna(head_by_q)
        expected = prev_head * (n.sum() / head_q.sum()) * np.array(
            [self.season[_fiscal_quarter(e) - 1] for e in ends])
        resid = np.log(per_q.clip(lower=1) / expected)
        self.bf_sigma = float(np.sqrt(max(np.var(resid, ddof=1) - 1.0 / max(expected.mean(), 1), 0.0)))

    # -- immediate refills: their recent pace per cell
    def _immediate(self):
        start = _quarter_start(_trailing_ends(self.origin, 4)[0])
        imm = self.recent[self.recent["is_immediate"] & (self.recent["approved_date"] >= start)]
        self.imm_rate = np.bincount(imm["cell"], minlength=len(self.cells)) / 4.0
        self.imm_nn_share = float(imm["is_net_new"].mean()) if len(imm) else 0.0

    # -- net-new: the plan, times opened-per-planned, split across offices
    def _net_new(self):
        """Net-new PIDs opened per net-new fill the budget planned. The company ratio is the median
        over every quarter of history known on the origin date (robust to a one-off year such as the
        FY24 restructuring), its spread the median absolute deviation; each function keeps its own
        share of what was opened against its share of the plan."""
        plan = self.inp.plan
        first = pd.Timestamp(self.inp.calendar["history_start_date"]) + pd.offsets.QuarterEnd(0)
        ends = [e for e in _trailing_ends(self.origin, 40) if e >= first]
        start = _quarter_start(ends[0])
        past = plan[(plan["version_type"] == "Budget") & (plan["quarter_end_date"].isin(ends))]
        fn = self.cells.drop_duplicates("department_id").set_index("department_id")["function_name"]
        past = past.assign(function_name=past["department_id"].map(fn))
        reqs = self.inp.reqs
        nn = reqs[reqs["is_net_new"] & ~reqs["is_immediate"] & (reqs["approved_date"] >= start)
                  & (reqs["approved_date"] <= self.origin)]
        nn_q = nn["approved_date"] + pd.offsets.QuarterEnd(0)
        planned_q = past.groupby("quarter_end_date")["planned_net_new"].sum().reindex(ends, fill_value=0)
        opened_q = nn.groupby(nn_q).size().reindex(ends, fill_value=0)
        ratios = (opened_q / planned_q.where(planned_q > 0)).dropna()
        ratios = ratios[ratios > 0]
        company = float(np.median(ratios)) if len(ratios) else 0.5
        logr = np.log(ratios.to_numpy())
        self.nn_sigma = float(1.4826 * np.median(np.abs(logr - np.median(logr)))) if len(logr) > 2 else 0.2
        planned_f = past.groupby("function_name")["planned_net_new"].sum()
        opened_f = nn.groupby("function_name").size()
        rel = {f: (opened_f.get(f, 0) / max(opened_f.sum(), 1)) / (planned_f[f] / planned_f.sum())
               if planned_f.get(f, 0) > 0 and planned_f.sum() > 0 else 1.0 for f in self.model.functions}
        self.open_ratio = {f: float(np.clip(company * np.clip(v, 0.5, 2.0), 0.05, 3.0)) for f, v in rel.items()}
        # office share inside each cost center: recent net-new PIDs, else headcount, else equal
        share = np.zeros(len(self.cells))
        nn_cell = np.bincount(self.recent.loc[self.recent["is_net_new"], "cell"], minlength=len(self.cells)).astype(float)
        for cc, g in self.cells.groupby("cost_center_id"):
            idx = g.index.to_numpy()
            for w in (nn_cell[idx], self.head_now[idx], np.ones(len(idx))):
                if w.sum() > 0:
                    share[idx] = w / w.sum()
                    break
        self.office_share = share
        known = D.known_plan(plan, self.origin)
        self.plan_nn = np.zeros((len(self.cells), len(self.targets)))
        self.plan_bf = np.zeros((len(self.cells), len(self.targets)))
        cc_cells = self.cells.groupby("cost_center_id").groups
        for t, qe in enumerate(self.targets):
            rows = known[known["quarter_end_date"] == qe]
            for cc, pn, pb in zip(rows["cost_center_id"], rows["planned_net_new"], rows["planned_backfills"]):
                idx = cc_cells.get(cc)
                if idx is None:
                    continue
                idx = np.asarray(idx)
                self.plan_nn[idx, t] += pn * share[idx]
                self.plan_bf[idx, t] += pb * share[idx]
        ratio_cell = np.array([self.open_ratio[f] for f in self.cells["function_name"]])
        self.nn_lambda = self.plan_nn * ratio_cell[:, None]

    # -- level-band mix of new PIDs, by cell and type, falling back to the function's
    def _band_mix(self):
        bands = {b: i for i, b in enumerate(S.LEVEL_BAND_ORDER)}
        r = self.recent[~self.recent["is_immediate"]]
        self.mix = np.zeros((2, len(self.cells), len(bands)))
        for t, sub in ((0, r[~r["is_net_new"]]), (1, r[r["is_net_new"]])):
            m = np.zeros((len(self.cells), len(bands)))
            np.add.at(m, (sub["cell"].to_numpy(), sub["level_band"].map(bands).to_numpy()), 1.0)
            fm = sub.groupby(["function_name", "level_band"]).size().unstack(fill_value=0).reindex(
                columns=S.LEVEL_BAND_ORDER, fill_value=0)
            for i, f in enumerate(self.cells["function_name"]):
                if m[i].sum() == 0:
                    m[i] = fm.loc[f].to_numpy(float) if f in fm.index and fm.loc[f].sum() else np.array([1.0, 0, 0, 0])
            self.mix[t] = m / m.sum(axis=1, keepdims=True)
        self.mix_cum = np.cumsum(self.mix, axis=2)

    def speed_sigma(self) -> float:
        """How much hiring speed varies from quarter to quarter: the spread, across the last eight
        approval quarters with complete follow-up, of the log-odds of filling within 60 days."""
        r = self.recent[~self.recent["is_immediate"]]
        r = r[r["approved_date"] <= self.origin - pd.Timedelta(days=60)]
        q = r["approved_date"] + pd.offsets.QuarterEnd(0)
        within = (r["filled_date"].notna() & (r["filled_date"] <= self.origin)
                  & ((r["filled_date"] - r["approved_date"]).dt.days <= 60))
        share = within.groupby(q).mean()
        share = share.clip(0.02, 0.98)
        lo = np.log(share / (1 - share))
        return float(np.std(lo, ddof=1)) if len(lo) > 2 else 0.1

    def lambdas(self) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Expected new PIDs per cell x target quarter: backfills, net-new, immediate refills."""
        fq = np.array([_fiscal_quarter(q) for q in self.targets])
        bf = (self.head_now * self.bf_rate)[:, None] * self.season[fq - 1][None, :]
        imm = np.repeat(self.imm_rate[:, None], len(self.targets), axis=1)
        return bf, self.nn_lambda, imm


def open_pool(inp: D.Inputs, demand: Demand, origin: pd.Timestamp) -> pd.DataFrame:
    """Requisitions waiting on the origin date (not immediate, not filled or cancelled by then)."""
    r = D.as_of_origin(inp.reqs, origin)
    r = r[~r["known_filled"] & ~r["known_cancelled"] & ~r["is_immediate"]].copy()
    r["cell"] = [demand.cell_index.get((d, l), -1) for d, l in zip(r["department_id"], r["location_id"])]
    return r[r["cell"] >= 0]


def run(inp: D.Inputs, model: FM.FillModel, origin: pd.Timestamp, targets: list[pd.Timestamp], draws: int,
        seed_key: int) -> tuple[pd.DataFrame, Demand, pd.DataFrame]:
    """Simulate `draws` futures. Returns one row per draw x cell x target quarter (zero rows dropped),
    the demand it used, and the open pool."""
    demand = Demand(inp, model, origin, targets)
    pool = open_pool(inp, demand, origin)
    ncell, nq = len(inp.cells), len(targets)
    lam_bf, lam_nn, lam_imm = demand.lambdas()
    starts = [_quarter_start(q) for q in targets]
    q_days = np.array([(q - s).days + 1 for s, q in zip(starts, targets)])
    q_start_day = np.array([D.to_day(s) for s in starts])
    q_end_day = np.array([D.to_day(q) for q in targets])
    origin_day = D.to_day(origin)
    bands = {b: i for i, b in enumerate(S.LEVEL_BAND_ORDER)}
    pool_cell = pool["cell"].to_numpy()
    pool_band = pool["level_band"].map(bands).to_numpy()
    pool_nn = pool["is_net_new"].to_numpy().astype(int)
    pool_appr = pool["approved_date"].to_numpy().astype("datetime64[D]")
    pool_k0 = ((origin_day - pool_appr).astype(int) + 1) // S.PERIOD_DAYS
    rng = np.random.default_rng(np.random.SeedSequence([S.SEED, seed_key]))
    tau = demand.speed_sigma()
    out = []
    vacant_start0 = np.bincount(pool_cell, minlength=ncell)
    for draw in range(draws):
        # new PIDs: counts per cell x quarter x type, then their approval days and level bands
        # each future draws its own demand level and hiring speed, from how much quarters have varied
        z_bf = np.exp(rng.normal(0.0, demand.bf_sigma) - demand.bf_sigma ** 2 / 2)
        z_nn = np.exp(rng.normal(0.0, demand.nn_sigma) - demand.nn_sigma ** 2 / 2)
        speed = rng.normal(0.0, tau)
        n_bf = rng.poisson(lam_bf * z_bf)
        n_nn = rng.poisson(lam_nn * z_nn)
        n_imm = rng.poisson(lam_imm)
        cells_new, q_new, nn_new = [], [], []
        for counts, is_nn in ((n_bf, 0), (n_nn, 1)):
            c, q = np.nonzero(counts)
            rep = counts[c, q]
            cells_new.append(np.repeat(c, rep))
            q_new.append(np.repeat(q, rep))
            nn_new.append(np.full(rep.sum(), is_nn))
        c_new, q_new, nn_new = np.concatenate(cells_new), np.concatenate(q_new), np.concatenate(nn_new)
        day_new = q_start_day[q_new] + (rng.random(len(c_new)) * q_days[q_new]).astype(int).astype("timedelta64[D]")
        u = rng.random(len(c_new))
        band_new = (u[:, None] > demand.mix_cum[nn_new, c_new]).sum(axis=1).clip(0, 3)
        # everyone waiting: the pool, then the new PIDs
        cell = np.concatenate([pool_cell, c_new])
        band = np.concatenate([pool_band, band_new])
        nn = np.concatenate([pool_nn, nn_new])
        appr = np.concatenate([pool_appr, day_new])
        k = np.concatenate([pool_k0, np.zeros(len(c_new), dtype=int)])
        fill = np.full(len(cell), np.datetime64("2999-12-31"), dtype="datetime64[D]")
        active = np.ones(len(cell), dtype=bool)
        f_i, c_i = demand.f_idx[cell], demand.c_idx[cell]
        for step in range(S.SIM_PERIODS + 1):
            a = np.nonzero(active)[0]
            if len(a) == 0:
                break
            mid = appr[a] + (k[a] * S.PERIOD_DAYS + S.PERIOD_DAYS // 2).astype("timedelta64[D]")
            month = (mid.astype("datetime64[M]").astype(int) % 12) + 1
            h = 1.0 / (1.0 + np.exp(-(model.logit(k[a], band[a], f_i[a], c_i[a], nn[a], month) + speed)))
            hit = rng.random(len(a)) < h
            offs = rng.integers(0, S.PERIOD_DAYS, len(a))
            d = appr[a] + (k[a] * S.PERIOD_DAYS + offs).astype("timedelta64[D]")
            d = np.maximum(d, origin_day + np.timedelta64(1, "D"))
            fill[a[hit]] = d[hit]
            active[a[hit]] = False
            k[a[~hit]] += 1
        # tally per cell x quarter
        key = lambda c, q: c * nq + q
        size = ncell * nq
        opened_bf = np.bincount(key(c_new[nn_new == 0], q_new[nn_new == 0]), minlength=size)
        opened_nn = np.bincount(key(c_new[nn_new == 1], q_new[nn_new == 1]), minlength=size)
        imm = n_imm.reshape(-1)                                            # cell-major, like key()
        filled = np.zeros(size, dtype=int)
        vacant_end = np.zeros(size, dtype=int)
        for qi in range(nq):
            in_q = (fill >= q_start_day[qi]) & (fill <= q_end_day[qi])
            filled += np.bincount(key(cell[in_q], qi), minlength=size)
            waiting = (appr <= q_end_day[qi]) & (fill > q_end_day[qi])
            vacant_end += np.bincount(key(cell[waiting], qi), minlength=size)
        filled_total = filled + imm
        vac_end = vacant_end.reshape(ncell, nq)
        vac_start = np.concatenate([vacant_start0[:, None], vac_end[:, :-1]], axis=1).reshape(-1)
        rows = pd.DataFrame({
            "draw": draw + 1,
            "cell": np.repeat(np.arange(ncell), nq),
            "target": np.tile(np.arange(nq), ncell),
            "vacant_start": vac_start,
            "opened_backfill": opened_bf,
            "opened_net_new": opened_nn,
            "opened_immediate": imm,
            "filled": filled_total,
            "vacant_end": vacant_end,
        })
        out.append(rows[(rows[["vacant_start", "opened_backfill", "opened_net_new", "opened_immediate",
                               "filled", "vacant_end"]] != 0).any(axis=1)])
    return pd.concat(out, ignore_index=True), demand, pool
