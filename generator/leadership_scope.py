"""
Release 7: org design and time off (case study 7, Who Leads Where).

Runs after the month-end close and the Core HR extract, on the files in data/raw:

    python generator/generate_data.py          # the month-end close
    python generator/core_hr_extract.py        # Core HR and Compensation to the data-through date
    python generator/leadership_scope.py       # release 7: matrix, role assignments, borrowed lines, time off

What it changes
  * Writes the nine release 7 tables (generator/source_systems.py, RELEASE_7_TABLES).
  * Replaces `manager_worker_id` on the job records where someone kept a manager in another
    department (the answer key lists every one, with the manager the simulation gave it).
    Nothing else in fact_job_history changes: no row, id, date, department, office or level.
  * Rewrites the lineage registry (ref_raw_table_lineage, ref_raw_column) to include them.

Safe to run again: it first puts back the managers the previous run replaced (from the
answer key it wrote), so the result is the same every time. The check at the end asserts
that the job history differs from the input only where the answer key says.

Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
"""

from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

import org_design
import reference_data as ref
import source_systems
import time_off

SEED = 20261009
ROOT = Path(__file__).resolve().parents[1]


def stream(domain: str) -> np.random.Generator:
    key = int.from_bytes(domain.encode("utf-8"), "big") % (2**63)
    return np.random.default_rng(np.random.SeedSequence([SEED, key]))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[1])
    ap.add_argument("--raw", type=Path, default=ROOT / "data" / "raw")
    a = ap.parse_args()
    raw = a.raw

    def rd(name):
        return pd.read_csv(raw / f"{name}.csv", dtype=str, keep_default_na=False, na_values=[""])

    def write(df, name):
        df.to_csv(raw / f"{name}.csv", index=False, lineterminator="\n")
        print(f"  {name:<28} {len(df):>9,} rows")

    report_date = dt.date.fromisoformat(ref.LAST_SNAPSHOT)
    data_through = dt.date.fromisoformat(ref.DATA_THROUGH)

    # 1. put back the managers a previous run replaced
    job = rd("fact_job_history")
    truth_path = raw / "gen_org_drift_truth.csv"
    if truth_path.exists():
        prev = pd.read_csv(truth_path, dtype=str, keep_default_na=False, na_values=[""])
        back = {}
        for ids, orig in prev.loc[prev["signal_code"] == "S1", ["job_record_ids", "original_values"]].itertuples(index=False):
            back.update(zip(ids.split(";"), orig.split(";")))
        hit = job["job_record_id"].isin(back)
        job.loc[hit, "manager_worker_id"] = job.loc[hit, "job_record_id"].map(back)
        print(f"Restored {int(hit.sum()):,} manager values from the previous run")
    before = job.copy()

    # 2. org design
    od = org_design.build(stream("org_design"), job, rd("dim_worker"), rd("ks_contingent_worker"), rd("dim_location"),
                          rd("dim_org_unit"), rd("dim_department"), data_through, report_date)
    job7 = od["fact_job_history"]

    # 3. time off, on the final job history
    to = time_off.build_all(stream("time_off"), rd("dim_worker"), job7, rd("dim_location"), rd("dim_country"),
                            rd("bw_contingent_worker"), rd("bw_service_order"), rd("bw_service_order_revision"),
                            rd("ks_contingent_worker"), report_date, data_through)

    # 4. check: only the answer key's records changed, and only their manager
    tr = od["gen_org_drift_truth"]
    listed = {x for ids in tr.loc[tr["signal_code"] == "S1", "job_record_ids"].dropna() for x in ids.split(";")}
    assert list(job7.columns) == list(before.columns) and len(job7) == len(before)
    other = [c for c in job7.columns if c != "manager_worker_id"]
    assert job7[other].equals(before[other]), "a column other than manager_worker_id changed"
    changed = set(job7.loc[job7["manager_worker_id"].fillna("") != before["manager_worker_id"].fillna(""), "job_record_id"])
    assert changed == listed, f"{len(changed ^ listed)} job records changed outside the answer key"

    # 5. write
    print("Writing release 7 tables to", raw)
    write(job7, "fact_job_history")
    tables = {**{k: v for k, v in od.items() if k != "fact_job_history"}, **to}
    for name in source_systems.RELEASE_7_TABLES:
        write(tables[name][source_systems.columns(name)], name)
    write(pd.DataFrame(source_systems.lineage_rows()), "ref_raw_table_lineage")
    write(pd.DataFrame(source_systems.column_rows()), "ref_raw_column")
    print(f"Job records with a borrowed manager: {len(listed):,} (only manager_worker_id changed)")


if __name__ == "__main__":
    main()
