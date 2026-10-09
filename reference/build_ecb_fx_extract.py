"""
Extract the official ECB euro foreign exchange reference rates used by the warehouse.

Source: European Central Bank, euro foreign exchange reference rates (daily, ~16:00 CET),
the full history file `eurofxref-hist.csv`. The `currencyconverter` package on PyPI
ships an unmodified copy of that file, which is how it is read here (no web call):

    pip install currencyconverter==0.18.22
    python reference/build_ecb_fx_extract.py

Output: reference/ecb_fx_reference_rates.csv, one row per ECB publication day and
currency, as units of currency per 1 EUR, exactly as the ECB publishes them.
The generator turns these into USD per unit of local currency (cross via EUR).

The UAE dirham is not in the ECB basket. It has been pegged at AED 3.6725 per USD by
the Central Bank of the UAE since 1997, so the generator applies the peg directly.
"""

from __future__ import annotations

import csv
import io
import zipfile
from pathlib import Path

import currency_converter

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reference" / "ecb_fx_reference_rates.csv"

START = "2022-01-01"   # covers the comp-history conversion date (2022-03-01) with room to spare
CURRENCIES = ["USD", "CAD", "BRL", "MXN", "GBP", "PLN", "CHF", "SEK", "ZAR",
              "INR", "SGD", "JPY", "AUD", "KRW", "PHP"]


def main():
    src = Path(currency_converter.__file__).parent / "eurofxref-hist.zip"
    with zipfile.ZipFile(src) as z:
        text = z.read(z.namelist()[0]).decode("utf-8")
    reader = csv.DictReader(io.StringIO(text))
    rows = []
    for rec in reader:
        day = rec["Date"]
        if day < START:
            continue
        for cur in CURRENCIES:
            value = (rec.get(cur) or "").strip()
            if value and value != "N/A":
                rows.append((day, cur, value))
    rows.sort()
    with OUT.open("w", newline="") as f:
        w = csv.writer(f, lineterminator="\n")
        w.writerow(["rate_date", "currency_code", "units_per_eur"])
        w.writerows(rows)
    days = sorted({r[0] for r in rows})
    print(f"Wrote {len(rows):,} rates for {len(CURRENCIES)} currencies, {days[0]} to {days[-1]} -> {OUT}")


if __name__ == "__main__":
    main()
