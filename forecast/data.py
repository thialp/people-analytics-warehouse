"""
What the forecast reads from the warehouse (release 5).

Everything comes from the DuckDB warehouse the pipeline builds (`warehouse/arcadia.duckdb`), so
the forecast sees exactly what the dashboards see. Executive officers (D-901) are excluded.

A requisition here is an employee requisition with a search: one filled the same day it was
approved (a succession, a team handed to a new manager) never stands vacant, so it is counted
separately as an immediate refill and never enters the time-to-fill model.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass

import duckdb
import numpy as np
import pandas as pd

import settings as S


@dataclass
class Inputs:
    calendar: pd.Series                 # the one row of ref_report_calendar
    quarters: pd.DataFrame              # ref_report_quarter (24 quarters)
    reqs: pd.DataFrame                  # every employee requisition, with its cell and attributes
    headcount: pd.DataFrame             # employees by quarter-end x department x office
    plan: pd.DataFrame                  # every plan version x cost center x quarter
    cells: pd.DataFrame                 # department x office: function, country, cost center


def level_band(grade: int) -> str:
    return S.LEVEL_BANDS.get(int(grade), S.LEVEL_BAND_LEADER)


def load(con: duckdb.DuckDBPyConnection) -> Inputs:
    cal = con.execute("SELECT * FROM staging.stg_report_calendar").fetchdf().iloc[0]
    quarters = con.execute("SELECT * FROM staging.stg_report_quarter ORDER BY quarter_offset").fetchdf()
    reqs = con.execute(f"""
        SELECT r.requisition_id, r.req_type, r.approved_date, r.filled_date, r.cancelled_date, r.status,
               r.department_id, r.location_id, r.cost_center_id, r.grade,
               d.function_name, l.country_code
        FROM staging.stg_requisition AS r
        JOIN staging.stg_department AS d USING (department_id)
        JOIN staging.stg_location AS l USING (location_id)
        WHERE r.department_id <> '{S.EXCLUDED_DEPARTMENT}'
    """).fetchdf()
    for c in ("approved_date", "filled_date", "cancelled_date"):
        reqs[c] = pd.to_datetime(reqs[c])
    reqs["level_band"] = [level_band(g) for g in reqs["grade"]]
    reqs["is_immediate"] = reqs["filled_date"].notna() & (reqs["filled_date"] == reqs["approved_date"])
    reqs["is_net_new"] = reqs["req_type"].eq("Net-new")
    headcount = con.execute(f"""
        SELECT s.month_end_date AS quarter_end_date, s.department_id, s.location_id, COUNT(*) AS headcount
        FROM intermediate.int_worker_month_end_snapshot AS s
        WHERE s.department_id <> '{S.EXCLUDED_DEPARTMENT}' AND MONTH(s.month_end_date) IN (3, 6, 9, 12)
        GROUP BY ALL
    """).fetchdf()
    headcount["quarter_end_date"] = pd.to_datetime(headcount["quarter_end_date"])
    plan = con.execute(f"""
        SELECT p.plan_version, p.version_type, p.version_date, p.fiscal_year, p.fiscal_quarter, p.quarter_end_date,
               p.cost_center_id, c.department_id, c.country_code, p.planned_net_new, p.planned_backfills,
               p.planned_ending_headcount, p.planned_cw_headcount, p.planned_cw_spend_usd
        FROM staging.stg_workforce_plan AS p
        JOIN staging.stg_cost_center AS c USING (cost_center_id)
        WHERE c.department_id <> '{S.EXCLUDED_DEPARTMENT}'
    """).fetchdf()
    for c in ("version_date", "quarter_end_date"):
        plan[c] = pd.to_datetime(plan[c])
    cells = con.execute(f"""
        SELECT DISTINCT p.department_id, p.location_id, d.function_name, d.department_name, d.sub_function,
               l.country_code, l.country_name, l.region, l.office_name
        FROM staging.stg_position AS p
        JOIN staging.stg_department AS d USING (department_id)
        JOIN staging.stg_location AS l USING (location_id)
        WHERE p.department_id <> '{S.EXCLUDED_DEPARTMENT}'
    """).fetchdf().sort_values(["department_id", "location_id"]).reset_index(drop=True)
    cells["cost_center_id"] = ["CC-" + d[2:] + "0-" + c for d, c in zip(cells["department_id"], cells["country_code"])]
    return Inputs(calendar=cal, quarters=quarters, reqs=reqs, headcount=headcount, plan=plan, cells=cells)


def quarter_ends(inputs: Inputs) -> list[pd.Timestamp]:
    return [pd.Timestamp(d) for d in inputs.quarters["quarter_end_date"]]


def as_of_origin(reqs: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """The requisitions as the warehouse knew them on `origin`: approved by then, with every fill and
    cancellation after it unknown. `event_day` is the fill offset in days, or None if still open."""
    r = reqs[reqs["approved_date"] <= origin].copy()
    filled = r["filled_date"].notna() & (r["filled_date"] <= origin)
    cancelled = r["cancelled_date"].notna() & (r["cancelled_date"] <= origin)
    r["known_filled"] = filled
    r["known_cancelled"] = cancelled & ~filled
    r["fill_day"] = np.where(filled, (r["filled_date"] - r["approved_date"]).dt.days, -1)
    end = np.where(filled, r["filled_date"], np.where(cancelled, r["cancelled_date"], origin))
    r["observed_days"] = (pd.to_datetime(end) - r["approved_date"]).dt.days
    return r


def known_plan(plan: pd.DataFrame, origin: pd.Timestamp) -> pd.DataFrame:
    """For each quarter after `origin`, the latest plan version that existed on `origin` and covers it."""
    p = plan[(plan["version_date"] <= origin) & (plan["quarter_end_date"] > origin)]
    if p.empty:
        return p
    latest = p.groupby("quarter_end_date")["version_date"].transform("max")
    return p[p["version_date"] == latest].copy()


def month_of(days: np.ndarray) -> np.ndarray:
    """Calendar month (1-12) of numpy datetime64[D] values."""
    return (days.astype("datetime64[M]").astype(int) % 12) + 1


def to_day(ts) -> np.datetime64:
    return np.datetime64(pd.Timestamp(ts).date(), "D")


def days_between(a: pd.Timestamp, b: pd.Timestamp) -> int:
    return (pd.Timestamp(b) - pd.Timestamp(a)).days


def first_day_after(ts: pd.Timestamp) -> pd.Timestamp:
    return pd.Timestamp(ts) + dt.timedelta(days=1)
