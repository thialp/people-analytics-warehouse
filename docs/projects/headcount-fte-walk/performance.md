# Performance: choosing the grain of workforce history

A headcount walk looks like a reporting problem, but its cost is decided by a modelling choice: **at what grain is workforce history stored?** This page compares three common answers on the Arcadia data, at its real size and at 10 times its size (469,800 workers; five years of history, measured on warehouse release 2).

Run it yourself:

```bash
python pipeline/run_pipeline.py --no-export
python benchmarks/benchmark_headcount_walk.py              # scales 1 and 10
python benchmarks/benchmark_headcount_walk.py --scales 1 5 20
```

The script writes [`performance_results.md`](performance_results.md) and stops if the two SQL strategies ever disagree.

## The three designs

| Design | How it works | Where it shows up |
|---|---|---|
| **1. Daily scaffold** | One row per worker per day employed; every month-end question is answered from it | The classic "date scaffolding" pattern in Tableau or SQL, used to get headcount on any date |
| **2. As-of join, twice** | Nothing stored. For each month, find every worker's job record in effect at the prior and the current month-end with a date-range join, then compare | Ad hoc SQL written against effective-dated tables |
| **3. Snapshot, then join** | Build one row per worker per month-end once, then compare consecutive months on an exact key | This repository: `int_worker_month_end_snapshot` → `int_worker_movement` |

## Results

From [`performance_results.md`](performance_results.md) (DuckDB 1.5.6 in a small cloud container; times vary by machine, row counts don't):

| Workers | Design | Rows stored | Fits Tableau Public (15M rows)? | Seconds |
|---|---|---|---|---|
| 46,980 | 1. Daily scaffold | 49,789,268 | no | 10.33 |
| 46,980 | 2. As-of join, twice | none | n/a | 1.04 |
| 46,980 | 3. Snapshot, then join | 1,639,687 | yes | 0.47 (0.31 build + 0.15 walk) |
| 469,800 | 1. Daily scaffold | 497,892,680 | no | 46.35 |
| 469,800 | 2. As-of join, twice | none | n/a | 4.57 |
| 469,800 | 3. Snapshot, then join | 16,396,870 | no (the walk mart is) | 3.75 (1.93 build + 1.83 walk) |

Designs 2 and 3 return identical hires, leavers and department moves at every scale.

## What the numbers say

- **The daily scaffold is the expensive mistake.** It stores 30 times more rows than a month-end snapshot (49.8M vs 1.64M) to answer month-end questions. At Arcadia's real size it is already more than three times Tableau Public's 15-million-row limit, and at 10x it reaches 498 million rows and is the slowest design by a factor of 12. Most of those rows say "nothing changed today".
- **The snapshot is paid for once.** Building it takes 1.93 seconds at 10x; after that a walk takes 1.83 seconds, 2.5 times faster than recomputing the date-range joins (4.57 seconds). At 10x and five years of history the snapshot itself passes Tableau Public's limit (16.4M rows), which is why it stays in the warehouse and Tableau gets the aggregated walk mart. The same snapshot feeds four downstream models here (the cost bridge, the cost snapshot, the movement model and the headcount walk), so design 2 would repeat its joins for each of them where design 3 builds once.
- **Equality joins are simpler to test.** Joining on `worker_id + month_end_date` makes "one row per worker per month" a one-line test (test 05). A date-range join can silently fan out when two records overlap; tests 02 and 03 exist to stop that before it reaches the snapshot.
- **The mart is smaller again.** The walk mart aggregates 1,633,133 worker-month comparisons into 521,029 slice-level lines, and ships its names in five small dimension files. The export is 28 MB instead of 98 MB with the names on every line.

## The general lesson

In-memory engines make all three designs fast on small data, which hides the problem until volume grows or a BI tool has to hold the result. The design choice that scales is to **store history at the grain the business asks questions at** (here, the month-end), do the expensive date logic once, and give every downstream model an exact key to join on.
