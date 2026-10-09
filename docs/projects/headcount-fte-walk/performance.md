# Performance: choosing the grain of workforce history

A headcount walk looks like a reporting problem, but its cost is decided by a modelling choice: **at what grain is workforce history stored?** This page compares three common answers on the Arcadia data, at its real size and at 10 times its size (435,690 workers).

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
| 43,569 | 1. Daily scaffold | 40,939,132 | no | 3.01 |
| 43,569 | 2. As-of join, twice | none | n/a | 0.62 |
| 43,569 | 3. Snapshot, then join | 1,347,949 | yes | 0.52 (0.35 build + 0.18 walk) |
| 435,690 | 1. Daily scaffold | 409,391,320 | no | 21.82 |
| 435,690 | 2. As-of join, twice | none | n/a | 5.66 |
| 435,690 | 3. Snapshot, then join | 13,479,490 | yes | 4.03 (2.15 build + 1.88 walk) |

Designs 2 and 3 return identical hires, leavers and department moves at every scale.

## What the numbers say

- **The daily scaffold is the expensive mistake.** It stores 30 times more rows than a month-end snapshot (40.9M vs 1.35M) to answer month-end questions. At Arcadia's real size it is already almost three times Tableau Public's 15-million-row limit, and at 10x it reaches 409 million rows. Most of those rows say "nothing changed today".
- **The snapshot is paid for once.** Building it takes 2.15 seconds at 10x; after that a walk takes 1.88 seconds, three times faster than recomputing the date-range joins (5.66 seconds). At 10x the snapshot is still under Tableau Public's limit (13.5M rows). The same snapshot feeds four downstream models here (the cost bridge, the cost snapshot, the movement model and the headcount walk), so design 2 would repeat its joins for each of them where design 3 builds once.
- **Equality joins are simpler to test.** Joining on `worker_id + month_end_date` makes "one row per worker per month" a one-line test (test 05). A date-range join can silently fan out when two records overlap; tests 02 and 03 exist to stop that before it reaches the snapshot.
- **The mart is smaller again.** The walk mart aggregates 1,336,479 worker-month comparisons into 436,501 slice-level lines, and ships its names in five small dimension files. The export is 24 MB instead of 73 MB.

## The general lesson

In-memory engines make all three designs fast on small data, which hides the problem until volume grows or a BI tool has to hold the result. The design choice that scales is to **store history at the grain the business asks questions at** (here, the month-end), do the expensive date logic once, and give every downstream model an exact key to join on.
