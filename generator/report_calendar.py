"""
The report calendar (release 5): one anchor date, and every label derived from it.

Every dashboard used to type its dates ("Jun 30, 2026", "FY26", a parameter list of 2022 to
2026). Here the generator writes them as data instead, from one setting, the report as-of
date (`reference_data.LAST_SNAPSHOT`):

  ref_report_calendar   one row: the as-of date, the current fiscal year (the one it closes),
                        the forward year (the one after it, which the forward budget plans and
                        Dashboard #5 forecasts), the first year of the history window, and
                        their labels.
  ref_report_quarter    one row per fiscal quarter in the window: five years of history and
                        the forward year (24 quarters). Each carries its labels and two
                        offsets from the as-of date: fy_offset (0 = the current fiscal year,
                        +1 = the forward year, -1 = last year ...) and quarter_offset (0 = the
                        quarter that ends on the as-of date, +1 the next ...).

A workbook that reads labels from these tables, and stores offsets rather than years in its
parameters, rolls forward by itself when the as-of date moves a year: FY27 becomes FY28 and
Jun 30, 2026 becomes Jun 30, 2027 without editing a calculation. The window keeps the same
length, so axes and card sizes never change.

Arcadia Systems is fictional; all data is synthetic.
"""

from __future__ import annotations

import datetime as dt

import pandas as pd

FY_START_MONTH = 7
HISTORY_YEARS = 5
_MONTH = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def fiscal_year(d: dt.date) -> int:
    return d.year + 1 if d.month >= FY_START_MONTH else d.year


def fy_label(fy: int) -> str:
    return f"FY{fy % 100:02d}"


def day_label(d: dt.date) -> str:
    return f"{_MONTH[d.month - 1]} {d.day}, {d.year}"


def _month_end(year: int, month: int) -> dt.date:
    nxt = dt.date(year + (month == 12), month % 12 + 1, 1)
    return nxt - dt.timedelta(days=1)


def _quarter_bounds(fy: int, q: int) -> tuple[dt.date, dt.date]:
    month0 = FY_START_MONTH + 3 * (q - 1)                    # 7, 10, 13, 16
    year = fy - 1 + (month0 - 1) // 12
    month = (month0 - 1) % 12 + 1
    start = dt.date(year, month, 1)
    end_month0 = month0 + 2
    end = _month_end(fy - 1 + (end_month0 - 1) // 12, (end_month0 - 1) % 12 + 1)
    return start, end


def _months_label(start: dt.date, end: dt.date) -> str:
    """'Jul - Sep 26' inside one calendar year, 'Oct - Dec 25', 'Jul 25 - Jun 26' across two."""
    if start.year == end.year:
        return f"{_MONTH[start.month - 1]} - {_MONTH[end.month - 1]} {end.year % 100:02d}"
    return f"{_MONTH[start.month - 1]} {start.year % 100:02d} - {_MONTH[end.month - 1]} {end.year % 100:02d}"


def build(as_of: dt.date, budget_month_day: tuple[int, int] = (5, 15)) -> dict[str, pd.DataFrame]:
    """Both calendar tables for a report as-of date, which must be a fiscal quarter end."""
    cur_fy = fiscal_year(as_of)
    cur_q = (as_of.month - FY_START_MONTH) % 12 // 3 + 1
    if _quarter_bounds(cur_fy, cur_q)[1] != as_of:
        raise ValueError(f"The report as-of date {as_of} is not a fiscal quarter end")
    fwd_fy = cur_fy + 1
    first_fy = cur_fy - HISTORY_YEARS + 1
    fwd_start = _quarter_bounds(fwd_fy, 1)[0]
    fwd_end = _quarter_bounds(fwd_fy, 4)[1]
    budget_date = dt.date(fwd_fy - 1, *budget_month_day)
    calendar = pd.DataFrame([{
        "report_as_of_date": as_of,
        "report_as_of_label": day_label(as_of),
        "current_fiscal_year": cur_fy,
        "current_fiscal_year_label": fy_label(cur_fy),
        "forward_fiscal_year": fwd_fy,
        "forward_fiscal_year_label": fy_label(fwd_fy),
        "history_first_fiscal_year": first_fy,
        "history_first_fiscal_year_label": fy_label(first_fy),
        "history_start_date": _quarter_bounds(first_fy, 1)[0],
        "forward_start_date": fwd_start,
        "forward_end_date": fwd_end,
        "forward_period_label": f"{_MONTH[fwd_start.month - 1]} {fwd_start.year} to "
                                f"{_MONTH[fwd_end.month - 1]} {fwd_end.year}",
        "forward_budget_version": f"{fy_label(fwd_fy)} Budget",
        "forward_budget_date": budget_date,
    }])
    rows = []
    cur_index = cur_fy * 4 + cur_q
    for fy in range(first_fy, fwd_fy + 1):
        for q in range(1, 5):
            start, end = _quarter_bounds(fy, q)
            rows.append({
                "fiscal_year": fy, "fiscal_year_label": fy_label(fy), "fiscal_quarter": q,
                "quarter_label": f"{fy_label(fy)} Q{q}", "quarter_months_label": _months_label(start, end),
                "quarter_start_date": start, "quarter_end_date": end,
                "fy_offset": fy - cur_fy, "quarter_offset": fy * 4 + q - cur_index,
                "is_forward": end > as_of,
            })
    return {"ref_report_calendar": calendar, "ref_report_quarter": pd.DataFrame(rows)}
