"""
Static reference data for Arcadia Systems, a fictional global technology company.

Everything here is invented for portfolio purposes. Pay levels, fringe rates and
FX starting points are rough, plausible magnitudes, not real company or market data.
"""

# --------------------------------------------------------------------------------------
# Countries, currencies and pay levels
# --------------------------------------------------------------------------------------
# pay_index   : local pay level relative to the US for the same grade (US = 1.00)
# fx_start    : USD per 1 unit of local currency at the first month-end (2022-06-30)
# fx_vol      : monthly volatility of the synthetic FX path (0 = pegged)
# fx_drift    : average monthly log change (negative = local currency weakens vs USD)
# fringe_base : employer-paid benefits, payroll taxes and social charges as % of base
# merit_adder : extra merit budget (percentage points) for higher-inflation markets
COUNTRIES = {
    # code: (name, region, currency, pay_index, fx_start, fx_vol, fx_drift, fringe_base, merit_adder, workforce_weight)
    "US": ("United States",  "North America", "USD", 1.00, 1.0000, 0.000,  0.0000, 0.28, 0.0, 0.38),
    "CA": ("Canada",         "North America", "CAD", 0.80, 0.7300, 0.015,  0.0000, 0.22, 0.0, 0.04),
    "BR": ("Brazil",         "Latin America", "BRL", 0.38, 0.1850, 0.035, -0.0020, 0.68, 2.5, 0.05),
    "MX": ("Mexico",         "Latin America", "MXN", 0.35, 0.0497, 0.025,  0.0010, 0.35, 1.5, 0.03),
    "GB": ("United Kingdom", "Europe",        "GBP", 0.85, 1.1150, 0.020,  0.0005, 0.18, 0.0, 0.07),
    "IE": ("Ireland",        "Europe",        "EUR", 0.82, 0.9800, 0.018,  0.0006, 0.14, 0.0, 0.04),
    "DE": ("Germany",        "Europe",        "EUR", 0.88, 0.9800, 0.018,  0.0006, 0.21, 0.0, 0.04),
    "FR": ("France",         "Europe",        "EUR", 0.80, 0.9800, 0.018,  0.0006, 0.45, 0.0, 0.02),
    "PL": ("Poland",         "Europe",        "PLN", 0.45, 0.2020, 0.025,  0.0010, 0.20, 1.5, 0.05),
    "IN": ("India",          "Asia Pacific",  "INR", 0.28, 0.0123, 0.012, -0.0015, 0.12, 3.0, 0.12),
    "SG": ("Singapore",      "Asia Pacific",  "SGD", 0.85, 0.6980, 0.010,  0.0005, 0.17, 0.0, 0.04),
    "JP": ("Japan",          "Asia Pacific",  "JPY", 0.70, 0.0069, 0.025, -0.0020, 0.16, 0.0, 0.02),
    "AU": ("Australia",      "Asia Pacific",  "AUD", 0.85, 0.6450, 0.022,  0.0000, 0.17, 0.0, 0.03),
    "AE": ("United Arab Emirates", "Middle East & Africa", "AED", 0.75, 0.2723, 0.000, 0.0000, 0.10, 0.0, 0.03),
    "ZA": ("South Africa",   "Middle East & Africa", "ZAR", 0.35, 0.0556, 0.035, -0.0015, 0.08, 2.0, 0.04),
}

# Cities. Several countries have more than one site so that location moves can
# happen inside a country (no currency change) as well as across countries.
LOCATIONS = [
    # location_id, city, country_code, site_type
    ("LOC-001", "Austin",        "US", "Headquarters"),
    ("LOC-002", "New York",      "US", "Office"),
    ("LOC-003", "San Francisco", "US", "Office"),
    ("LOC-004", "Atlanta",       "US", "Office"),
    ("LOC-005", "Remote - US",   "US", "Remote"),
    ("LOC-006", "Toronto",       "CA", "Office"),
    ("LOC-007", "Sao Paulo",     "BR", "Office"),
    ("LOC-008", "Mexico City",   "MX", "Office"),
    ("LOC-009", "London",        "GB", "Regional Hub"),
    ("LOC-010", "Dublin",        "IE", "Office"),
    ("LOC-011", "Berlin",        "DE", "Office"),
    ("LOC-012", "Paris",         "FR", "Office"),
    ("LOC-013", "Warsaw",        "PL", "Engineering Center"),
    ("LOC-014", "Krakow",        "PL", "Engineering Center"),
    ("LOC-015", "Bangalore",     "IN", "Engineering Center"),
    ("LOC-016", "Hyderabad",     "IN", "Engineering Center"),
    ("LOC-017", "Singapore",     "SG", "Regional Hub"),
    ("LOC-018", "Tokyo",         "JP", "Office"),
    ("LOC-019", "Sydney",        "AU", "Office"),
    ("LOC-020", "Dubai",         "AE", "Regional Hub"),
    ("LOC-021", "Johannesburg",  "ZA", "Office"),
    ("LOC-022", "Cape Town",     "ZA", "Office"),
]

# --------------------------------------------------------------------------------------
# Organization: function -> sub-function -> department
# --------------------------------------------------------------------------------------
# Each department lists the job families it hires (with weights) and a country
# profile that shifts where its people sit.
# country profiles: "tech" leans on engineering centers, "commercial" spreads
# across sales markets, "corporate" concentrates in hubs.
DEPARTMENTS = [
    # dept_id, name, sub_function, function, families {family: weight}, country_profile, size_weight, growth_weight
    ("D-101", "Core Platform Engineering",   "Engineering",        "Technology", {"SWE": 0.85, "DAT": 0.08, "PRD": 0.07}, "tech", 0.090, 1.2),
    ("D-102", "Product Engineering",         "Engineering",        "Technology", {"SWE": 0.82, "DAT": 0.10, "PRD": 0.08}, "tech", 0.075, 1.2),
    ("D-103", "Mobile & Web Engineering",    "Engineering",        "Technology", {"SWE": 0.88, "DSN": 0.06, "PRD": 0.06}, "tech", 0.060, 1.0),
    ("D-104", "Analytics Engineering",       "Engineering",        "Technology", {"DAT": 0.70, "SWE": 0.30},              "tech", 0.030, 1.0),
    ("D-105", "Site Reliability",            "Infrastructure",     "Technology", {"SWE": 0.75, "ITS": 0.25},              "tech", 0.040, 0.9),
    ("D-106", "Information Security",        "Infrastructure",     "Technology", {"SEC": 0.85, "SWE": 0.15},              "tech", 0.035, 1.3),
    ("D-107", "Enterprise IT",               "Infrastructure",     "Technology", {"ITS": 0.90, "SWE": 0.10},              "tech", 0.035, 0.7),
    ("D-108", "Data & AI Platform",          "Engineering",        "Technology", {"DAT": 0.75, "SWE": 0.25},              "tech", 0.000, 1.8),  # created in the FY25 reorg
    ("D-201", "Product Management",          "Product",            "Product",    {"PRD": 0.90, "DAT": 0.10},              "corporate", 0.040, 1.0),
    ("D-202", "Design & Research",           "Product",            "Product",    {"DSN": 0.90, "PRD": 0.10},              "corporate", 0.020, 0.9),
    ("D-301", "Enterprise Sales - Americas", "Sales",              "Commercial", {"SAL": 0.90, "CSM": 0.10},              "amer", 0.055, 1.0),
    ("D-302", "Enterprise Sales - EMEA",     "Sales",              "Commercial", {"SAL": 0.90, "CSM": 0.10},              "emea", 0.040, 1.0),
    ("D-303", "Enterprise Sales - APAC",     "Sales",              "Commercial", {"SAL": 0.90, "CSM": 0.10},              "apac", 0.030, 1.1),
    ("D-304", "Sales Operations",            "Sales",              "Commercial", {"OPS": 0.70, "DAT": 0.30},              "commercial", 0.020, 0.8),
    ("D-305", "Client Success",              "Client Services",    "Commercial", {"CSM": 0.95, "OPS": 0.05},              "commercial", 0.060, 1.0),
    ("D-306", "Technical Support",           "Client Services",    "Commercial", {"CSM": 0.60, "SWE": 0.20, "OPS": 0.20}, "support", 0.050, 0.8),
    ("D-307", "Partnerships",                "Sales",              "Commercial", {"SAL": 0.80, "PRD": 0.20},              "commercial", 0.015, 1.0),
    ("D-401", "Brand & Communications",      "Marketing",          "Marketing",  {"MKT": 1.00},                           "corporate", 0.015, 0.8),
    ("D-402", "Growth Marketing",            "Marketing",          "Marketing",  {"MKT": 0.80, "DAT": 0.20},              "corporate", 0.020, 0.9),
    ("D-501", "FP&A",                        "Finance",            "Corporate",  {"FIN": 0.90, "DAT": 0.10},              "corporate", 0.015, 0.8),
    ("D-502", "Accounting & Controllership", "Finance",            "Corporate",  {"FIN": 1.00},                           "corporate", 0.020, 0.7),
    ("D-503", "Treasury & Tax",              "Finance",            "Corporate",  {"FIN": 1.00},                           "corporate", 0.008, 0.7),
    ("D-601", "HR Business Partners",        "People",             "Corporate",  {"HRM": 1.00},                           "corporate", 0.012, 0.8),
    ("D-602", "Talent Acquisition",          "People",             "Corporate",  {"HRM": 1.00},                           "corporate", 0.012, 1.0),
    ("D-603", "Total Rewards",               "People",             "Corporate",  {"HRM": 0.80, "DAT": 0.20},              "corporate", 0.006, 0.8),
    ("D-604", "People Analytics",            "People",             "Corporate",  {"DAT": 0.70, "HRM": 0.30},              "corporate", 0.004, 1.1),
    ("D-701", "Legal",                       "Legal & Compliance", "Corporate",  {"LGL": 1.00},                           "corporate", 0.010, 0.8),
    ("D-702", "Compliance & Risk",           "Legal & Compliance", "Corporate",  {"LGL": 0.60, "OPS": 0.40},              "corporate", 0.015, 1.0),
    ("D-801", "Customer Operations",         "Operations",         "Operations", {"OPS": 0.95, "DAT": 0.05},              "ops", 0.080, 1.0),
    ("D-802", "Trust & Safety Operations",   "Operations",         "Operations", {"OPS": 0.80, "DAT": 0.20},              "ops", 0.045, 1.1),
    ("D-803", "Workplace & Procurement",     "Operations",         "Operations", {"OPS": 1.00},                           "ops", 0.015, 0.7),
    ("D-901", "Office of the CEO",           "Executive",          "Executive",  {"EXE": 1.00},                           "us_only", 0.002, 0.0),
]

# Country weight multipliers by profile (applied on top of COUNTRIES workforce_weight).
COUNTRY_PROFILES = {
    "tech":       {"US": 1.0, "IN": 2.2, "PL": 2.0, "IE": 1.2, "CA": 1.2, "BR": 0.8, "GB": 0.8, "DE": 0.6, "FR": 0.3, "MX": 0.6, "SG": 0.6, "JP": 0.3, "AU": 0.4, "AE": 0.2, "ZA": 0.6},
    "corporate":  {"US": 1.6, "IN": 0.8, "PL": 0.8, "IE": 1.2, "CA": 0.6, "BR": 0.6, "GB": 1.4, "DE": 0.5, "FR": 0.3, "MX": 0.4, "SG": 1.2, "JP": 0.3, "AU": 0.4, "AE": 0.6, "ZA": 0.5},
    "commercial": {"US": 1.2, "IN": 0.7, "PL": 0.4, "IE": 0.8, "CA": 1.0, "BR": 1.3, "GB": 1.4, "DE": 1.3, "FR": 1.4, "MX": 1.3, "SG": 1.4, "JP": 1.8, "AU": 1.4, "AE": 1.6, "ZA": 1.0},
    "amer":       {"US": 2.0, "CA": 2.0, "BR": 2.2, "MX": 2.2},
    "emea":       {"GB": 2.0, "IE": 1.0, "DE": 2.0, "FR": 2.0, "PL": 0.6, "AE": 2.0, "ZA": 1.5},
    "apac":       {"IN": 1.0, "SG": 2.5, "JP": 3.0, "AU": 3.0},
    "support":    {"US": 0.6, "IN": 2.5, "PL": 2.0, "IE": 1.2, "BR": 1.5, "MX": 1.5, "ZA": 1.8, "SG": 0.5},
    "ops":        {"US": 1.0, "IN": 2.5, "PL": 1.8, "IE": 1.0, "BR": 1.4, "MX": 1.2, "ZA": 1.5, "SG": 0.8, "AE": 0.6},
    "us_only":    {"US": 1.0},
}

# --------------------------------------------------------------------------------------
# Jobs and grades
# --------------------------------------------------------------------------------------
JOB_FAMILIES = {
    # code: (family name, title stem for IC grades)
    "SWE": ("Software Engineering",  "Software Engineer"),
    "DAT": ("Data & Analytics",      "Data Analyst"),
    "PRD": ("Product Management",    "Product Manager"),
    "DSN": ("Design",                "Product Designer"),
    "SEC": ("Security",              "Security Engineer"),
    "ITS": ("IT & Infrastructure",   "Systems Engineer"),
    "SAL": ("Sales",                 "Account Executive"),
    "CSM": ("Client Success",        "Client Success Manager"),
    "MKT": ("Marketing",             "Marketing Specialist"),
    "FIN": ("Finance",               "Financial Analyst"),
    "HRM": ("Human Resources",       "HR Specialist"),
    "LGL": ("Legal & Compliance",    "Counsel"),
    "OPS": ("Operations",            "Operations Analyst"),
    "EXE": ("Executive Leadership",  "Executive"),
}

# Grade ladder. US annual base midpoint in USD for FY2023; ranges move with the
# structural increase in GRADE_RANGE_MOVEMENT each fiscal year.
GRADES = {
    # grade: (level label, track, US midpoint USD FY2023)
    1: ("Associate",          "Individual Contributor",  58_000),
    2: ("Professional",       "Individual Contributor",  74_000),
    3: ("Senior",             "Individual Contributor",  92_000),
    4: ("Lead",               "Individual Contributor", 115_000),
    5: ("Manager / Staff",    "Manager or Expert",      142_000),
    6: ("Senior Manager / Principal", "Manager or Expert", 176_000),
    7: ("Director",           "Leadership",             218_000),
    8: ("Senior Director",    "Leadership",             272_000),
    9: ("Vice President",     "Leadership",             345_000),
}
GRADE_RANGE_MOVEMENT = {2022: -0.035, 2023: 0.0, 2024: 0.030, 2025: 0.030, 2026: 0.035}

# Grade mix for the starting population and for new hires.
START_GRADE_MIX = {1: 0.06, 2: 0.15, 3: 0.22, 4: 0.22, 5: 0.16, 6: 0.10, 7: 0.06, 8: 0.025, 9: 0.005}
HIRE_GRADE_MIX  = {1: 0.12, 2: 0.22, 3: 0.25, 4: 0.19, 5: 0.11, 6: 0.07, 7: 0.03, 8: 0.008, 9: 0.002}

# --------------------------------------------------------------------------------------
# Business calendar and workforce assumptions
# --------------------------------------------------------------------------------------
FISCAL_YEAR_START_MONTH = 7            # FY2026 = 2025-07-01 .. 2026-06-30
FIRST_SNAPSHOT = "2022-06-30"          # opening month-end
LAST_SNAPSHOT = "2026-06-30"           # closing month-end (end of FY2026)
START_HEADCOUNT = 11_000

# Net headcount growth targeted per fiscal year (before attrition backfill).
FY_NET_GROWTH = {2023: 0.075, 2024: 0.010, 2025: 0.045, 2026: 0.055}

# Annual merit cycle, effective March 1. Budget = average increase for eligible staff.
MERIT_EFFECTIVE_MONTH = 3
MERIT_BUDGET = {2023: 0.042, 2024: 0.034, 2025: 0.031, 2026: 0.035}
PROMOTION_CYCLE_RATE = 0.065           # share promoted in the March cycle
OFF_CYCLE_PROMOTION_MONTHLY = 0.0025

MONTHLY_ATTRITION = 0.0095             # ~11% annualized before adjustments
MONTHLY_TRANSFER = 0.0045
MONTHLY_MARKET_ADJUSTMENT = 0.0015
MONTHLY_FTE_CHANGE = 0.0012
INTERNATIONAL_SHARE_OF_TRANSFERS = 0.10
LOCATION_MOVE_MONTHLY = 0.0008         # same-department relocations

# One-off events that give the history a story.
RESTRUCTURING = {"date": "2024-02-15", "functions": ["Commercial", "Marketing"], "share": 0.05}
REORGANIZATION = {"date": "2024-11-01", "target_department": "D-108",
                  "source_departments": ["D-101", "D-102", "D-104"], "families": ["DAT"]}

# Same-day correction records in compensation history (the raw table keeps both rows).
COMP_CORRECTION_RATE = 0.006

FX_CONSTANT_RATE_SET = "FY26 Plan"
FX_CONSTANT_RATE_DATE = "2025-06-30"   # plan rates are taken from this month-end
