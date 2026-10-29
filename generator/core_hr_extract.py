"""
Release 6: extend Keystone's Core HR and Compensation tables to the data-through date.

Arcadia's warehouse closes the month on the report date (2026-06-30): every system and module is loaded as of that
day. Keystone's Core HR and Compensation modules are also read every night, so the warehouse holds them up to the
latest nightly extract, the data-through date (reference_data.DATA_THROUGH, 2026-07-05). That is what lets a page
show headcount "to date" (year to date, quarter to date, month to date) between two month-end closes.

    python generator/generate_data.py          # the month-end close: every raw table, as of the report date
    python generator/core_hr_extract.py        # then: dim_worker, fact_job_history and fact_compensation_history
                                               # run on to the data-through date

How it works
  1. Run the generator again with --simulate-through (the month-end of the data-through date) into a scratch folder.
     The day-by-day simulation is deterministic and draws in date order, so every worker, job record and pay record
     up to the report date comes out the same as in the close; only the days after it are new.
  2. Merge three tables into data/raw/, reading every value as text so the close's rows stay byte-identical:
       * rows dated up to the report date keep their record ids and values;
       * a record still open at the report date takes the end date the extension gives it, if that end falls on or
         before the data-through date (a job change on Jul 2 closes the old job on Jul 1);
       * records that start after the report date and on or before the data-through date are appended with new ids,
         and anything they record after the data-through date is not known yet: end dates and termination dates
         later than it are left empty, as in a real extract.
  3. Every other raw table (positions, requisitions, applicants, plans, contingent workers, tickets) is left as of
     the report date. A seat created and filled between the two dates is therefore in Core HR and not yet in
     position management, as it would be between two month-end loads.

The check at the end asserts that no row dated up to the report date changed, apart from end dates filled in.
"""

from __future__ import annotations

import argparse
import calendar
import datetime as dt
import subprocess
import sys
import tempfile
from pathlib import Path

import pandas as pd

import reference_data as ref

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
RA = ref.LAST_SNAPSHOT            # the report date (month-end close), ISO text
DT = ref.DATA_THROUGH             # the data-through date, ISO text

JOB_KEY = ["worker_id", "effective_start_date", "action_reason", "position_id"]
PAY_KEY = ["worker_id", "effective_start_date", "action_reason", "currency_code"]


def read(folder: Path, table: str) -> pd.DataFrame:
    return pd.read_csv(folder / f"{table}.csv", dtype=str, keep_default_na=False)


def write(df: pd.DataFrame, table: str) -> None:
    df.to_csv(RAW / f"{table}.csv", index=False, lineterminator="\n")


def unknown_after(d: pd.Series) -> pd.Series:
    """a date the extract cannot know yet (later than the data-through date) becomes empty"""
    return d.where((d == "") | (d <= DT), "")


def next_ids(existing: pd.Series, n: int, prefix: str) -> list[str]:
    width = len(existing.iloc[0]) - len(prefix)
    start = int(existing.str[len(prefix):].astype(int).max()) + 1
    return [f"{prefix}{i:0{width}d}" for i in range(start, start + n)]


def close_open_records(base: pd.DataFrame, ext: pd.DataFrame, key: list[str], end: str) -> pd.DataFrame:
    """base rows open on the report date take the extension's end date (if it is known by the data-through date)"""
    ends = ext[ext["effective_start_date"] <= RA].drop_duplicates(key).set_index(key)[end]
    out = base.copy()
    open_at_ra = (out[end] == "") | (out[end] >= RA)
    idx = pd.MultiIndex.from_frame(out.loc[open_at_ra, key])
    new_end = unknown_after(pd.Series(ends.reindex(idx).fillna("").to_numpy(), index=out.index[open_at_ra]))
    out.loc[open_at_ra, end] = new_end
    return out


def extend(ext_dir: Path) -> None:
    # ---------------------------------------------------------------- workers
    base_w, ext_w = read(RAW, "dim_worker"), read(ext_dir, "dim_worker")
    keep = base_w[base_w["original_hire_date"] <= RA].copy()
    ext_known = ext_w.set_index("worker_id")
    left = (keep["termination_date"] == "") & keep["worker_id"].map(
        lambda w: RA < ext_known.at[w, "termination_date"] <= DT if ext_known.at[w, "termination_date"] else False)
    keep.loc[left, "termination_date"] = keep.loc[left, "worker_id"].map(ext_known["termination_date"])
    keep.loc[left, "termination_type"] = keep.loc[left, "worker_id"].map(ext_known["termination_type"])
    hires = ext_w[(ext_w["original_hire_date"] > RA) & (ext_w["original_hire_date"] <= DT)].copy()
    gone = hires["termination_date"] > DT
    hires.loc[gone, ["termination_date", "termination_type"]] = ""
    workers = pd.concat([keep, hires], ignore_index=True)
    assert not workers["worker_id"].duplicated().any()

    # ---------------------------------------------------------------- jobs
    base_j, ext_j = read(RAW, "fact_job_history"), read(ext_dir, "fact_job_history")
    keep_j = close_open_records(base_j[base_j["effective_start_date"] <= RA], ext_j, JOB_KEY, "effective_end_date")
    new_j = ext_j[(ext_j["effective_start_date"] > RA) & (ext_j["effective_start_date"] <= DT)].copy()
    new_j["effective_end_date"] = unknown_after(new_j["effective_end_date"])
    new_j["job_record_id"] = next_ids(base_j["job_record_id"], len(new_j), "JR")
    jobs = pd.concat([keep_j, new_j], ignore_index=True)

    # ---------------------------------------------------------------- pay
    base_c, ext_c = read(RAW, "fact_compensation_history"), read(ext_dir, "fact_compensation_history")
    keep_c = close_open_records(base_c[base_c["effective_start_date"] <= RA], ext_c, PAY_KEY, "effective_end_date")
    new_c = ext_c[(ext_c["effective_start_date"] > RA) & (ext_c["effective_start_date"] <= DT)].copy()
    new_c["effective_end_date"] = unknown_after(new_c["effective_end_date"])
    new_c["comp_record_id"] = next_ids(base_c["comp_record_id"], len(new_c), "CR")
    pay = pd.concat([keep_c, new_c], ignore_index=True)

    # ---------------------------------------------------------------- the check: the close is untouched
    for name, before, after, end in (("fact_job_history", base_j, jobs, "effective_end_date"),
                                     ("fact_compensation_history", base_c, pay, "effective_end_date")):
        b = before[before["effective_start_date"] <= RA].drop(columns=[end]).reset_index(drop=True)
        a = after.iloc[:len(b)].drop(columns=[end]).reset_index(drop=True)
        assert b.equals(a), f"{name}: a row dated up to the report date changed"
        moved = (before[before["effective_start_date"] <= RA][end].reset_index(drop=True)
                 != after.iloc[:len(b)][end].reset_index(drop=True))
        assert (before[before["effective_start_date"] <= RA][end].reset_index(drop=True)[moved].isin(["", RA])).all(), \
            f"{name}: an end date before the report date changed"
    b = base_w[base_w["original_hire_date"] <= RA].drop(columns=["termination_date", "termination_type"]).reset_index(drop=True)
    assert b.equals(workers.iloc[:len(b)].drop(columns=["termination_date", "termination_type"]).reset_index(drop=True))

    write(workers, "dim_worker")
    write(jobs, "fact_job_history")
    write(pay, "fact_compensation_history")
    print(f"Core HR extended from {RA} to {DT}: {len(hires):,} hires, {int(left.sum()):,} leavers, "
          f"{len(new_j):,} job records and {len(new_c):,} pay records after the report date")


def main() -> None:
    cli = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    cli.add_argument("--ext-dir", type=Path, default=None,
                     help="an extension run already written (skips running the generator again)")
    args = cli.parse_args()
    if args.ext_dir:
        extend(args.ext_dir)
        return
    d = dt.date.fromisoformat(DT)
    through = dt.date(d.year, d.month, calendar.monthrange(d.year, d.month)[1])
    with tempfile.TemporaryDirectory() as tmp:
        print(f"Simulating through {through} into a scratch folder ...")
        subprocess.run([sys.executable, str(Path(__file__).with_name("generate_data.py")),
                        "--simulate-through", through.isoformat(), "--out", tmp], check=True,
                       stdout=subprocess.DEVNULL)
        extend(Path(tmp))


if __name__ == "__main__":
    main()
