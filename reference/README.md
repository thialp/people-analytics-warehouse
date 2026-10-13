# Reference data

Public data the warehouse uses as is, kept here so every build reads the same inputs and GitHub Actions never needs the internet.

| File | What it is | Source | Rebuild |
|---|---|---|---|
| [`ecb_fx_reference_rates.csv`](ecb_fx_reference_rates.csv) | Every ECB euro reference rate from 2022-01-03 to 2026-09-14 for the 15 currencies Arcadia pays in besides the euro and the UAE dirham, as units per 1 EUR, exactly as published | European Central Bank, euro foreign exchange reference rates (`eurofxref-hist.csv`), read from the unmodified copy shipped in the [`currencyconverter`](https://pypi.org/project/currencyconverter/) package | `pip install currencyconverter==0.18.22` then `python reference/build_ecb_fx_extract.py` |

The generator turns these into USD per unit of local currency ([`generator/fx_rates.py`](../generator/fx_rates.py)) and adds the euro (USD per EUR) and the UAE dirham (fixed at AED 3.6725 per USD, the Central Bank of the UAE peg).

Other public inputs live in code next to the citation for each number:

- **Fringe rates** (OECD Taxing Wages, BLS Employer Costs for Employee Compensation, statutory sources): [`generator/fringe_research.py`](../generator/fringe_research.py), explained in [`docs/company/organization_and_pay_model.md`](../docs/company/organization_and_pay_model.md#fringe-rates).
- **Office postal codes and coordinates** (GeoNames postal-code centroids, CC BY 4.0): the `OFFICES` table in [`generator/reference_data.py`](../generator/reference_data.py).
