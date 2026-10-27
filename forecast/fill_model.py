"""
Time to fill: a discrete-time survival (hazard) model (release 5).

In plain words: for a requisition that has already waited k ten-day periods, what is the chance it
is filled in the next one? That chance depends on how long it has waited (the baseline), its level,
function, country, whether it is a net-new PID, and, for graduate levels, the calendar month in its
country (graduate seasons). It is a logistic regression on requisition-periods.

Why this and not an average: requisitions still open on the forecast date have not finished
waiting. Averaging only the filled ones makes recent quarters look fast; dropping them makes them
look slow. Here an open requisition counts as "not filled yet" for every period it was observed and
then simply leaves the data (it is censored), which is the standard survival-analysis answer.

The fit is plain Newton-Raphson (iteratively reweighted least squares) on binomial counts, with a
small ridge penalty, written in numpy so every step can be read. Coefficients are rounded before
they are used, so the forecast reproduces byte for byte.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

import settings as S

_BIN_OF_PERIOD = np.array([max(i for i, b in enumerate(S.PERIOD_BINS) if k >= b) for k in range(S.SIM_PERIODS + 1)])


def period_bin(k: np.ndarray) -> np.ndarray:
    return _BIN_OF_PERIOD[np.minimum(k, S.SIM_PERIODS)]


@dataclass
class FillModel:
    functions: list[str]
    countries: list[str]
    b_bin: np.ndarray            # baseline log-odds for each waiting-time bin
    b_band: np.ndarray           # level band (L1-L2 = 0)
    b_function: np.ndarray       # function (the first alphabetically = 0)
    b_country: np.ndarray        # country (the first alphabetically = 0)
    b_net_new: float             # a net-new PID against a backfill
    b_season: np.ndarray         # graduate levels only: country x calendar month
    rows: int                    # requisition-periods the model was fit on
    requisitions: int

    def index(self, values, names: list[str]) -> np.ndarray:
        pos = {n: i for i, n in enumerate(names)}
        return np.array([pos[v] for v in values])

    def logit(self, k, band_idx, func_idx, cty_idx, net_new, month) -> np.ndarray:
        junior = band_idx == 0
        return (self.b_bin[period_bin(k)] + self.b_band[band_idx] + self.b_function[func_idx]
                + self.b_country[cty_idx] + self.b_net_new * net_new
                + np.where(junior, self.b_season[cty_idx, month - 1], 0.0))

    def hazard(self, *args) -> np.ndarray:
        return 1.0 / (1.0 + np.exp(-self.logit(*args)))

    def coefficients(self) -> pd.DataFrame:
        """Every coefficient, named, for the methodology page and the tests."""
        rows = [("baseline", f"periods {S.PERIOD_BINS[i]}+" if i == len(S.PERIOD_BINS) - 1
                 else f"periods {S.PERIOD_BINS[i]}-{S.PERIOD_BINS[i + 1] - 1}", v) for i, v in enumerate(self.b_bin)]
        rows += [("level band", b, v) for b, v in zip(S.LEVEL_BAND_ORDER, self.b_band)]
        rows += [("function", f, v) for f, v in zip(self.functions, self.b_function)]
        rows += [("country", c, v) for c, v in zip(self.countries, self.b_country)]
        rows += [("net-new", "Net-new PID", self.b_net_new)]
        rows += [("graduate season", f"{c} month {m + 1:02d}", self.b_season[i, m])
                 for i, c in enumerate(self.countries) for m in range(12)]
        return pd.DataFrame(rows, columns=["term_group", "term", "coefficient"])


def person_periods(r: pd.DataFrame) -> pd.DataFrame:
    """One row per requisition per ten-day period it was observed, with `filled` 1 in the period
    it was filled. Open and cancelled requisitions stop at their last fully observed period."""
    r = r[~r["is_immediate"]]
    filled = r["known_filled"].to_numpy()
    fill_k = np.where(filled, r["fill_day"].to_numpy().astype(int) // S.PERIOD_DAYS, -1)
    obs_k = (r["observed_days"].to_numpy().astype(int) + 1) // S.PERIOD_DAYS   # fully observed periods
    n = np.where(filled, fill_k + 1, obs_k).astype(int)
    keep = n > 0
    idx = np.repeat(np.arange(len(r))[keep], n[keep])
    k = np.concatenate([np.arange(m) for m in n[keep]]) if keep.any() else np.array([], dtype=int)
    approved = r["approved_date"].to_numpy().astype("datetime64[D]")[idx]
    mid = approved + (k * S.PERIOD_DAYS + S.PERIOD_DAYS // 2).astype("timedelta64[D]")
    return pd.DataFrame({
        "k": k,
        "band": r["level_band"].to_numpy()[idx],
        "function_name": r["function_name"].to_numpy()[idx],
        "country_code": r["country_code"].to_numpy()[idx],
        "net_new": r["is_net_new"].to_numpy().astype(int)[idx],
        "month": (mid.astype("datetime64[M]").astype(int) % 12) + 1,
        "filled": ((k == fill_k[idx]) & filled[idx]).astype(int),
    })


def fit(r: pd.DataFrame, functions: list[str], countries: list[str]) -> FillModel:
    pp = person_periods(r)
    pp["bin"] = period_bin(pp["k"].to_numpy())
    pp.loc[pp["band"] != S.GRADUATE_BAND, "month"] = 0                     # the month matters for graduates only
    g = pp.groupby(["bin", "band", "function_name", "country_code", "net_new", "month"], as_index=False) \
          .agg(y=("filled", "sum"), n=("filled", "size"))
    nb, nband, nf, nc = len(S.PERIOD_BINS), len(S.LEVEL_BAND_ORDER), len(functions), len(countries)
    band_i = g["band"].map({b: i for i, b in enumerate(S.LEVEL_BAND_ORDER)}).to_numpy()
    f_i = g["function_name"].map({f: i for i, f in enumerate(functions)}).to_numpy()
    c_i = g["country_code"].map({c: i for i, c in enumerate(countries)}).to_numpy()
    m = g["month"].to_numpy()
    # design: bins (no intercept) | bands 1.. | functions 1.. | countries 1.. | net-new | season (country x month)
    o_band, o_f = nb, nb + nband - 1
    o_c = o_f + nf - 1
    o_nn = o_c + nc - 1
    o_s = o_nn + 1
    p = o_s + nc * 12
    X = np.zeros((len(g), p))
    rows = np.arange(len(g))
    X[rows, g["bin"].to_numpy()] = 1.0
    sel = band_i > 0
    X[rows[sel], o_band + band_i[sel] - 1] = 1.0
    sel = f_i > 0
    X[rows[sel], o_f + f_i[sel] - 1] = 1.0
    sel = c_i > 0
    X[rows[sel], o_c + c_i[sel] - 1] = 1.0
    X[:, o_nn] = g["net_new"].to_numpy()
    sel = m > 0
    X[rows[sel], o_s + c_i[sel] * 12 + m[sel] - 1] = 1.0
    y, n = g["y"].to_numpy(float), g["n"].to_numpy(float)
    penalty = np.full(p, S.RIDGE)
    penalty[:nb] = 0.0
    beta = np.zeros(p)
    beta[:nb] = np.log(max(y.sum(), 1) / max(n.sum() - y.sum(), 1))      # start every bin at the overall rate
    for _ in range(S.IRLS_ITERATIONS):
        eta = X @ beta
        mu = 1.0 / (1.0 + np.exp(-eta))
        w = n * mu * (1 - mu)
        grad = X.T @ (y - n * mu) - penalty * beta
        hess = (X * w[:, None]).T @ X + np.diag(penalty)
        step = np.linalg.solve(hess, grad)
        beta += step
        if np.max(np.abs(step)) < 1e-9:
            break
    beta = np.round(beta, S.COEF_DECIMALS)
    b_band = np.concatenate([[0.0], beta[o_band:o_f]])
    b_f = np.concatenate([[0.0], beta[o_f:o_c]])
    b_c = np.concatenate([[0.0], beta[o_c:o_nn]])
    return FillModel(functions=functions, countries=countries, b_bin=beta[:nb], b_band=b_band, b_function=b_f,
                     b_country=b_c, b_net_new=float(beta[o_nn]), b_season=beta[o_s:].reshape(nc, 12),
                     rows=int(n.sum()), requisitions=int((~r["is_immediate"]).sum()))
