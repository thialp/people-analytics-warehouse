# Workforce Planning: headline values

The numbers Dashboard #3 should show for FY26 (Jul 2025 to Jun 2026), from the release 2 build after phase 5. Use them as the check table while building the workbook: if a sheet disagrees, the sheet is wrong or the data changed. Arcadia Systems is fictional and all data is synthetic.

Rebuild these after any generator change (`python generator/generate_data.py`, then `python pipeline/run_pipeline.py`).

## Seat fills (`mart_position_fill`, `fiscal_year = 2026`)

| Measure | Value |
|---|---:|
| Seat fills (external hires + internal moves) | 6,849 |
| Backfills | 4,668 |
| Net-new seats filled | 2,181 |
| Filled by internal moves | 1,614 |
| Net-new seats approved while a matching seat stood vacant 90+ days (`reuse_candidate`) | 628 (29% of net-new) |
| Backfills by why the seat was empty: voluntary exit / internal move out / involuntary exit | 2,612 / 1,397 / 659 |
| Backfills by level change: same / down / up | 3,916 / 567 / 185 |
| Median days from approval to fill (backfills, excluding immediate refills) | 42 |
| Median days a backfilled seat stood empty (same population) | 54 |

## Pay walk, prior incumbent to new incumbent (backfills, constant USD, annual base rate)

| Step | Average per backfill |
|---|---:|
| Level effect | −$1,454 |
| Location effect | −$144 |
| Market effect (range moves between exit and fill) | +$474 |
| Positioning in the range | −$376 |
| **Pay change** | **−$1,500** |

Total across the 4,668 backfills: −$7.0M a year of base pay.

## Vacancy pool at Jun 30, 2026 (`mart_vacancy_pool`)

| Status | Seats | Stale (vacant 90+ days) |
|---|---:|---:|
| Open | 725 | 77 |
| Frozen | 252 | 136 |

## Plan vs actual, FY26 company (`mart_plan_vs_actual`)

Each reforecast covers only the quarters still ahead, so its hire totals cover fewer quarters.

| Version | Planned net-new | Actual net-new | Planned backfills | Actual backfills | Planned Jun 30 headcount | Actual |
|---|---:|---:|---:|---:|---:|---:|
| FY26 Budget | 2,762 | 2,181 | 5,031 | 4,668 | 30,347 | 30,014 |
| FY26 RF1 (Q2–Q4) | 1,845 | 1,532 | 3,772 | 3,639 | 30,229 | 30,014 |
| FY26 RF2 (Q3–Q4) | 1,097 | 981 | 2,524 | 2,408 | 30,151 | 30,014 |
| FY26 RF3 (Q4) | 549 | 510 | 1,202 | 1,207 | 30,095 | 30,014 |

## Seat corridors, FY26 US (`mart_seat_corridors`)

| From → to | Seats |
|---|---:|
| Austin → Chicago | 19 |
| Austin → Atlanta | 14 |
| San Francisco → Austin | 14 |
| Austin → New York | 12 |
| New York → Austin | 12 |
