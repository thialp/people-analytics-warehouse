"""
Source systems and raw-table lineage for the Arcadia Systems warehouse (release 3).

Arcadia runs two operational systems for its people:

  * Keystone HR     the HR system of record. Employees, jobs, pay, seats, requisitions,
                    applicants and the workforce plan live here, and managers see every
                    worker here, contingent workers included.
  * Bridgeway VMS   the vendor management system. Suppliers submit vetted contingent
                    workers; service orders, revisions, bill rates and timesheets live
                    here. It is the source of truth for who is a contingent worker.

Bridgeway pushes changes to Keystone through a one-way integration. Nothing typed in
Keystone flows back, and Bridgeway never stores the Keystone person ID: Keystone stores
the Bridgeway worker ID, and the warehouse joins the two systems on it.

This module is the single place that says which system every raw table comes from and,
for the tables release 3 adds, exactly which columns the extract carries. The generator
writes both registries as raw tables (ref_source_system, ref_raw_table_lineage,
ref_raw_column), so lineage is data the warehouse can test and Tableau can show:
  test 60  every raw table has exactly one lineage row, and every lineage row a table
  test 61  each release 3 table carries exactly the documented columns, in order

Arcadia Systems, Keystone HR and Bridgeway VMS are fictional; all data is synthetic.
"""

from __future__ import annotations

# --------------------------------------------------------------------------------------
# Systems
# --------------------------------------------------------------------------------------
SOURCE_SYSTEMS = [
    {"system_code": "KS", "system_name": "Keystone HR", "system_type": "HR system of record",
     "record_of": "Employees, jobs, pay, seats, requisitions, applicants, workforce plan; the HR profile of every contingent worker",
     "used_by": "Managers, employees, HR Operations, Talent Acquisition, Finance planning",
     "extract": "Nightly full extract of current and history tables"},
    {"system_code": "BW", "system_name": "Bridgeway VMS", "system_type": "Vendor management system",
     "record_of": "Suppliers, contingent workers, service orders and their revisions, bill rates, timesheets",
     "used_by": "Vendor Management, hiring managers raising requests, suppliers",
     "extract": "Nightly full extract; revisions are effective-dated, one current per service order"},
    {"system_code": "INT", "system_name": "Bridgeway to Keystone integration", "system_type": "Integration log",
     "record_of": "Every change Bridgeway sent to Keystone, when it was applied and whether it failed",
     "used_by": "Integration support",
     "extract": "Nightly extract of the event log"},
    {"system_code": "WH", "system_name": "Arcadia warehouse metadata", "system_type": "Warehouse metadata",
     "record_of": "Which system every raw table comes from, and the column contract of every release 3 extract",
     "used_by": "The warehouse build and its tests; the methodology pages of the dashboards",
     "extract": "Written with the data by generator/source_systems.py"},
    {"system_code": "PUB", "system_name": "Public reference data", "system_type": "External reference",
     "record_of": "ECB euro reference rates; employer fringe rates researched from OECD, BLS and national sources",
     "used_by": "Finance, the warehouse",
     "extract": "Loaded when sources publish"},
]

# --------------------------------------------------------------------------------------
# Every raw table: source system, module, grain and history type
# --------------------------------------------------------------------------------------
_KS, _BW, _INT, _PUB, _WH = "KS", "BW", "INT", "PUB", "WH"
RAW_TABLE_LINEAGE = [
    # Keystone HR: people
    ("dim_worker", _KS, "Core HR", "worker", "Type 1", 2),
    ("fact_job_history", _KS, "Core HR", "worker x effective-dated job record", "SCD Type 2", 2),
    ("fact_compensation_history", _KS, "Compensation", "worker x effective-dated pay record", "SCD Type 2", 2),
    ("fact_performance_review", _KS, "Performance", "worker x fiscal year", "Transaction", 2),
    ("fact_bonus_payout", _KS, "Compensation", "worker x fiscal year", "Transaction", 2),
    # Keystone HR: organization and pay structure
    ("dim_org_unit", _KS, "Organization", "org unit", "Type 1", 2),
    ("dim_department", _KS, "Organization", "department", "Type 1", 2),
    ("dim_cost_center", _KS, "Organization", "department x country", "Type 1", 2),
    ("dim_location", _KS, "Organization", "office", "Type 1", 2),
    ("dim_country", _KS, "Organization", "country", "Type 1", 2),
    ("dim_job_level", _KS, "Compensation", "job level", "Type 1", 2),
    ("dim_job_profile", _KS, "Compensation", "job family x level", "Type 1", 2),
    ("ref_job_level_base_salary", _KS, "Compensation", "job level x country", "Type 1", 2),
    ("ref_salary_range", _KS, "Compensation", "fiscal year x job level x country", "Dated", 2),
    ("ref_tenure_increase", _KS, "Compensation", "completed years of service", "Type 1", 2),
    ("ref_performance_bonus", _KS, "Performance", "rating", "Type 1", 2),
    # Keystone HR: seats, recruiting, plan
    ("dim_position", _KS, "Position management", "seat x effective-dated record", "SCD Type 2", 2),
    ("fact_position_assignment", _KS, "Position management", "seat x worker x dates", "Effective-dated", 2),
    ("fact_requisition", _KS, "Recruiting", "requisition", "Accumulating snapshot", 2),
    ("dim_candidate", _KS, "Recruiting", "applicant x requisition", "Type 1", 2),
    ("fact_candidate_stage_event", _KS, "Recruiting", "applicant x stage", "Transaction", 2),
    ("fact_workforce_plan", _KS, "Workforce planning", "plan version x cost center x fiscal quarter", "Versioned", 2),
    # Keystone HR: the contingent worker profile (release 3)
    ("ks_contingent_worker", _KS, "Contingent worker profile", "person x effective-dated version", "SCD Type 2", 3),
    # Bridgeway VMS (release 3)
    ("bw_supplier", _BW, "Suppliers", "supplier", "Type 1", 3),
    ("bw_rate_card", _BW, "Rate cards", "fiscal year x country x CW type x role family x seniority", "Dated", 3),
    ("bw_contingent_worker", _BW, "Workers", "worker in Bridgeway", "Type 1", 3),
    ("bw_service_order", _BW, "Service orders", "service order", "Accumulating snapshot", 3),
    ("bw_service_order_revision", _BW, "Service orders", "service order x revision", "SCD Type 2", 3),
    ("bw_timesheet_month", _BW, "Timesheets", "worker x service order x month", "Transaction", 3),
    # Integration (release 3)
    ("feed_bridgeway_keystone_event", _INT, "Integration log", "change sent from Bridgeway", "Transaction", 3),
    # Public reference data
    ("ref_fx_rate_daily", _PUB, "FX", "currency x ECB publication day", "Transaction", 1),
    ("ref_fx_rate_monthly", _PUB, "FX", "currency x month-end", "Transaction", 1),
    ("ref_fx_rate_constant", _PUB, "FX", "rate set x currency", "Type 1", 1),
    ("ref_fringe_rate", _PUB, "Fringe research", "country x calendar year", "Dated", 1),
    ("ref_fringe_source", _PUB, "Fringe research", "country x year x component x source", "Type 1", 1),
    # The registry itself (written by this module)
    ("ref_source_system", _WH, "Warehouse metadata", "source system", "Type 1", 3),
    ("ref_raw_table_lineage", _WH, "Warehouse metadata", "raw table", "Type 1", 3),
    ("ref_raw_column", _WH, "Warehouse metadata", "release 3 raw table x column", "Type 1", 3),
]

# --------------------------------------------------------------------------------------
# Column contracts for the tables release 3 adds: (column, type, description)
# Types are the warehouse types staging casts to; raw lands everything as text.
# --------------------------------------------------------------------------------------
RAW_COLUMNS: dict[str, list[tuple[str, str, str]]] = {
    "bw_supplier": [
        ("supplier_id", "VARCHAR", "Supplier key, e.g. SUP-014"),
        ("supplier_name", "VARCHAR", "Fictional supplier name"),
        ("cw_types_offered", "VARCHAR", "CW types the supplier provides, semicolon separated: Contractor, Consultant, BPO"),
        ("hq_country_code", "VARCHAR", "Country of the supplier's head office"),
        ("onboarded_date", "DATE", "First day the supplier could take service orders"),
        ("is_active", "BOOLEAN", "False once Arcadia stopped using the supplier"),
    ],
    "bw_rate_card": [
        ("rate_card_id", "VARCHAR", "Rate card line key"),
        ("fiscal_year", "INTEGER", "Arcadia fiscal year the line applies to (July to June)"),
        ("country_code", "VARCHAR", "Country where the work is done"),
        ("cw_type", "VARCHAR", "Contractor, Consultant or BPO"),
        ("role_family", "VARCHAR", "Development, QA, Data, Analyst, Project Delivery, Architecture, Design, Operations; BPO: Security, Facilities, Service Desk"),
        ("seniority", "VARCHAR", "Junior, Mid, Senior or Lead"),
        ("rate_type", "VARCHAR", "Hourly, or Monthly for BPO"),
        ("billing_currency", "VARCHAR", "Currency the rate is billed in"),
        ("rate_low", "DECIMAL", "Bottom of the band"),
        ("rate_target", "DECIMAL", "Target rate"),
        ("rate_high", "DECIMAL", "Top of the band"),
    ],
    "bw_contingent_worker": [
        ("bw_worker_id", "VARCHAR", "Bridgeway worker key, e.g. BW00012345. Bridgeway never stores the Keystone person ID"),
        ("first_name", "VARCHAR", "Fictional"),
        ("last_name", "VARCHAR", "Fictional"),
        ("email", "VARCHAR", "Work email issued for the engagement (fictional domain)"),
        ("supplier_id", "VARCHAR", "-> bw_supplier"),
        ("cw_type", "VARCHAR", "Contractor, Consultant or BPO"),
        ("original_start_date", "DATE", "First day of the first engagement under this Bridgeway ID"),
        ("created_date", "DATE", "Day the supplier submitted the worker"),
    ],
    "bw_service_order": [
        ("service_order_id", "VARCHAR", "Service order key, e.g. SO0012345"),
        ("bw_worker_id", "VARCHAR", "-> bw_contingent_worker"),
        ("supplier_id", "VARCHAR", "-> bw_supplier"),
        ("order_type", "VARCHAR", "New engagement, or Renewal of an earlier order for the same worker"),
        ("renews_service_order_id", "VARCHAR", "The order this one renews; empty for a new engagement"),
        ("opened_date", "DATE", "Manager raised the request"),
        ("submitted_date", "DATE", "Supplier submitted the worker"),
        ("approved_date", "DATE", "Order approved; empty if never approved"),
        ("final_status", "VARCHAR", "Status of the current revision at the extract date"),
    ],
    "bw_service_order_revision": [
        ("revision_id", "VARCHAR", "Revision key"),
        ("service_order_id", "VARCHAR", "-> bw_service_order"),
        ("revision_no", "INTEGER", "0 for the original order, then 1, 2, ..."),
        ("revision_reason", "VARCHAR", "Original, Extension, Extension with rate change, Early end, Cost center change, Manager change, Office change, Closure"),
        ("effective_start_date", "DATE", "First day the revision is in effect"),
        ("effective_end_date", "DATE", "Last day in effect (inclusive); empty for the current revision"),
        ("is_current", "BOOLEAN", "True on exactly one revision per order"),
        ("status", "VARCHAR", "Draft, Pending Approval, Approved, Active, Ended, Closed, Withdrawn, Rejected"),
        ("assignment_start_date", "DATE", "First working day of the assignment"),
        ("assignment_end_date", "DATE", "Last working day of the assignment as this revision states it"),
        ("closed_date", "DATE", "Day the order was closed in Bridgeway; empty while open"),
        ("role_family", "VARCHAR", "See bw_rate_card"),
        ("seniority", "VARCHAR", "Junior, Mid, Senior or Lead"),
        ("job_title", "VARCHAR", "Title on the order"),
        ("cost_center_code", "VARCHAR", "Cost center as typed on the order (text, not validated against Keystone)"),
        ("hiring_manager_email", "VARCHAR", "Arcadia manager who owns the order"),
        ("office_code", "VARCHAR", "Arcadia office where the work is done"),
        ("bill_rate", "DECIMAL", "Rate in billing currency: per hour, or per month for BPO"),
        ("rate_type", "VARCHAR", "Hourly or Monthly"),
        ("billing_currency", "VARCHAR", "ISO currency code"),
        ("hours_per_week", "DECIMAL", "Contracted hours; empty for monthly BPO orders"),
    ],
    "bw_timesheet_month": [
        ("timesheet_id", "VARCHAR", "Timesheet month key"),
        ("bw_worker_id", "VARCHAR", "-> bw_contingent_worker"),
        ("service_order_id", "VARCHAR", "-> bw_service_order"),
        ("month_end_date", "DATE", "Month billed"),
        ("billed_hours", "DECIMAL", "Approved hours; 0 for monthly BPO orders"),
        ("billed_units", "DECIMAL", "Hours for hourly orders; months (1.0, or a fraction in start and end months) for BPO"),
        ("bill_rate", "DECIMAL", "Rate applied"),
        ("billing_currency", "VARCHAR", "ISO currency code"),
        ("billed_amount_local", "DECIMAL", "billed_units x bill_rate"),
    ],
    "ks_contingent_worker": [
        ("ks_record_id", "VARCHAR", "Record key"),
        ("person_id", "VARCHAR", "Keystone person ID, the same W... key space as employees"),
        ("bw_worker_id", "VARCHAR", "Bridgeway worker ID as Keystone stored it from the feed; can be blank or mistyped"),
        ("effective_start_date", "DATE", "First day the version applies"),
        ("effective_end_date", "DATE", "Last day (inclusive); empty for the current version"),
        ("change_source", "VARCHAR", "Feed, HR Ops or Manager: who wrote the version"),
        ("feed_event_id", "VARCHAR", "-> feed_bridgeway_keystone_event when change_source = Feed"),
        ("first_name", "VARCHAR", "As Keystone holds it"),
        ("last_name", "VARCHAR", "As Keystone holds it"),
        ("cw_type", "VARCHAR", "Contractor, Consultant or BPO"),
        ("supplier_name", "VARCHAR", "Free text as fed; Keystone has no supplier table"),
        ("status", "VARCHAR", "Active or Inactive"),
        ("contract_start_date", "DATE", "As Keystone knows it"),
        ("contract_end_date", "DATE", "As Keystone knows it; Keystone inactivates the worker the day after"),
        ("inactive_reason", "VARCHAR", "Contract ended, Ended early, Converted to employee, Manual; empty while active"),
        ("department_id", "VARCHAR", "-> dim_department"),
        ("cost_center_id", "VARCHAR", "-> dim_cost_center"),
        ("location_id", "VARCHAR", "-> dim_location"),
        ("manager_worker_id", "VARCHAR", "Arcadia employee the worker reports to (-> dim_worker)"),
    ],
    "feed_bridgeway_keystone_event": [
        ("feed_event_id", "VARCHAR", "Event key"),
        ("revision_id", "VARCHAR", "-> bw_service_order_revision that caused the event"),
        ("bw_worker_id", "VARCHAR", "-> bw_contingent_worker"),
        ("event_type", "VARCHAR", "New Worker, Extension, Early End, Rate Change, Attribute Change, Renewal, Closure"),
        ("sent_date", "DATE", "Day Bridgeway sent the change"),
        ("applied_date", "DATE", "Day Keystone applied it; empty if it failed"),
        ("outcome", "VARCHAR", "Applied, Applied Late, Partly Applied, Failed"),
        ("error_text", "VARCHAR", "Integration message for failures and partial loads"),
    ],
}

# The registry tables themselves, so test 61 covers them too
RAW_COLUMNS["ref_source_system"] = [
    ("system_code", "VARCHAR", "KS, BW, INT, WH or PUB"),
    ("system_name", "VARCHAR", "System name"),
    ("system_type", "VARCHAR", "What kind of system it is"),
    ("record_of", "VARCHAR", "What it is the system of record for"),
    ("used_by", "VARCHAR", "Who works in it"),
    ("extract", "VARCHAR", "How the warehouse receives it"),
]
RAW_COLUMNS["ref_raw_table_lineage"] = [
    ("table_name", "VARCHAR", "Raw table"),
    ("system_code", "VARCHAR", "-> ref_source_system"),
    ("module", "VARCHAR", "Module of the source system"),
    ("grain", "VARCHAR", "One row per ..."),
    ("history_type", "VARCHAR", "Type 1, SCD Type 2, Dated, Transaction, Accumulating snapshot, Versioned, Effective-dated"),
    ("added_in_release", "INTEGER", "Warehouse release that added the table"),
]
RAW_COLUMNS["ref_raw_column"] = [
    ("table_name", "VARCHAR", "Raw table"),
    ("column_order", "INTEGER", "1-based position in the extract"),
    ("column_name", "VARCHAR", "Column"),
    ("data_type", "VARCHAR", "Type staging casts to"),
    ("description", "VARCHAR", "What it holds"),
]


def lineage_rows() -> list[dict]:
    return [{"table_name": t, "system_code": s, "module": m, "grain": g, "history_type": h, "added_in_release": r}
            for t, s, m, g, h, r in RAW_TABLE_LINEAGE]


def column_rows() -> list[dict]:
    return [{"table_name": t, "column_order": i, "column_name": c, "data_type": ty, "description": d}
            for t, cols in RAW_COLUMNS.items() for i, (c, ty, d) in enumerate(cols, start=1)]


def columns(table: str) -> list[str]:
    """Column names of a release 3 raw table, in extract order."""
    return [c for c, _, _ in RAW_COLUMNS[table]]


# Release 3 operational tables (not the registry). The generator writes them; until the
# contingent workforce simulation lands (phase 3) they are written with headers only.
RELEASE_3_TABLES = [t for t, _, _, _, _, r in RAW_TABLE_LINEAGE if r == 3 and not t.startswith("ref_")]
