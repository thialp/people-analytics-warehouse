# Performance: choosing the grain of workforce history

A headcount walk looks like a reporting problem, but its cost is decided by a modelling choice: **at what grain is workforce history stored?** This page compares three common answers on the Arcadia data, at its real size and at 10 times its size (192,760 workers).

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
| 19,276 | 1. Daily scaffold | 18,003,909 | no | 1.30 |
| 19,276 | 2. As-of join, twice | none | n/a | 0.28 |
| 19,276 | 3. Snapshot, then join | 592,823 | yes | 0.29 (0.20 build + 0.09 walk) |
| 192,760 | 1. Daily scaffold | 180,039,090 | no | 10.48 |
| 192,760 | 2. As-of join, twice | none | n/a | 2.32 |
| 192,760 | 3. Snapshot, then join | 5,928,230 | yes | 1.78 (1.03 build + 0.75 walk) |

Designs 2 and 3 return identical hires, leavers and department moves at every scale.

## What the numbers say

- **The daily scaffold is the expensive mistake.** It stores 30 times more rows than a month-end snapshot (18.0M vs 0.59M) to answer month-end questions. At Arcadia's real size it is already over Tableau Public's 15-million-row limit, and at 10x it reaches 180 million rows. Most of those rows say "nothing changed today".
- **The snapshot is paid for once.** Building it takes 1.03 seconds at 10x; after that a walk takes 0.75 seconds, three times faster than recomputing the date-range joins (2.32 seconds). The same snapshot feeds four downstream models here (the cost bridge, the cost snapshot, the movement model and the headcount walk), so design 2 would repeat its joins for each of them where design 3 builds once.
- **Equality joins are simpler to test.** Joining on `worker_id + month_end_date` makes "one row per worker per month" a one-line test (test 05). A date-range join can silently fan out when two records overlap; tests 02 and 03 exist to stop that before it reaches the snapshot.
- **The mart is smaller again.** The walk mart aggregates 587,886 worker-month comparisons into 292,696 slice-level lines, and ships its names in five small dimension files. The export is 15 MB instead of 57 MB.

## The general lesson

In-memory engines make all three designs fast on small data, which hides the problem until volume grows or a BI tool has to hold the result. The design choice that scales is to **store history at the grain the business asks questions at** (here, the month-end), do the expensive date logic once, and give every downstream model an exact key to join on.
