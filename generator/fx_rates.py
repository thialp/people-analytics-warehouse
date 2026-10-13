"""
Real FX rates for the simulation and the warehouse, from the ECB extract in reference/.

The ECB publishes units of each currency per 1 EUR. Arcadia reports in USD, so every
rate is turned into USD per 1 unit of local currency by crossing through the euro:

    usd_per_local(CUR) = (USD per EUR) / (CUR per EUR)

EUR itself is USD per EUR; USD is 1; AED uses the Central Bank of the UAE peg.
ECB rates exist only on TARGET business days; any other day takes the latest
published rate on or before it (the "as-of" rule a payroll system would use).
"""

from __future__ import annotations

import bisect
import csv
import datetime as dt
from pathlib import Path

import reference_data as ref

ROOT = Path(__file__).resolve().parents[1]
ECB_FILE = ROOT / "reference" / "ecb_fx_reference_rates.csv"


def _load() -> dict[str, tuple[list[dt.date], list[float]]]:
    per_eur: dict[str, dict[dt.date, float]] = {}
    with ECB_FILE.open() as f:
        for row in csv.DictReader(f):
            per_eur.setdefault(row["currency_code"], {})[dt.date.fromisoformat(row["rate_date"])] = float(row["units_per_eur"])
    usd = per_eur["USD"]
    days = sorted(usd)
    series: dict[str, tuple[list[dt.date], list[float]]] = {}
    currencies = sorted({c[2] for c in ref.COUNTRIES.values()})
    for cur in currencies:
        if cur == "USD":
            series[cur] = (days, [1.0] * len(days))
        elif cur == "EUR":
            series[cur] = (days, [round(usd[d], 8) for d in days])
        elif cur == "AED":
            series[cur] = (days, [round(1 / ref.AED_PER_USD_PEG, 8)] * len(days))
        else:
            cur_days = [d for d in days if d in per_eur[cur]]
            series[cur] = (cur_days, [round(usd[d] / per_eur[cur][d], 8) for d in cur_days])
    return series


SERIES = _load()
FIRST_DAY = max(v[0][0] for v in SERIES.values())
LAST_DAY = min(v[0][-1] for v in SERIES.values())


def usd_per_local(currency: str, on: dt.date) -> float:
    """Latest ECB-based rate published on or before `on`."""
    days, values = SERIES[currency]
    i = bisect.bisect_right(days, on) - 1
    if i < 0:
        raise ValueError(f"No {currency} rate on or before {on}")
    return values[i]


def daily_rows():
    """Every published rate, for the raw ref_fx_rate_daily table."""
    for cur, (days, values) in SERIES.items():
        source = ("Central Bank of the UAE peg (AED 3.6725 per USD)" if cur == "AED"
                  else "Base currency" if cur == "USD" else "ECB euro reference rate, crossed via EUR")
        for d, v in zip(days, values):
            yield {"currency_code": cur, "rate_date": d, "usd_per_local": v, "source": source}
