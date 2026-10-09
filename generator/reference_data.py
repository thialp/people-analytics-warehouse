"""
Static reference data for Arcadia Systems, a fictional global technology company.

What is real and what is invented
---------------------------------
Real (public sources, cited where used):
  * Office postal codes and their map coordinates (GeoNames postal-code centroids,
    CC BY 4.0; two exceptions are noted on the office rows).
  * Daily FX rates (ECB euro reference rates; see reference/).
  * Fringe rates by country and year (OECD, BLS and statutory sources; see
    generator/fringe_research.py).

Invented for the portfolio:
  * The company, its people, names, street addresses, org design, pay levels,
    geographic pay differentials, tenure raise schedule and bonus plan.
"""

# --------------------------------------------------------------------------------------
# Countries
# --------------------------------------------------------------------------------------
# pay_index        : Arcadia's geographic pay differential vs. the US for the same level
# workforce_weight : relative share of the workforce the company aims for
COUNTRIES = {
    # code: (name, region, currency, pay_index, workforce_weight)
    "US": ("United States",        "North America",        "USD", 1.00, 0.300),
    "CA": ("Canada",               "North America",        "CAD", 0.78, 0.035),
    "BR": ("Brazil",               "Latin America",        "BRL", 0.36, 0.040),
    "MX": ("Mexico",               "Latin America",        "MXN", 0.34, 0.035),
    "GB": ("United Kingdom",       "Europe",               "GBP", 0.84, 0.060),
    "IE": ("Ireland",              "Europe",               "EUR", 0.82, 0.030),
    "DE": ("Germany",              "Europe",               "EUR", 0.86, 0.040),
    "FR": ("France",               "Europe",               "EUR", 0.78, 0.020),
    "NL": ("Netherlands",          "Europe",               "EUR", 0.84, 0.020),
    "ES": ("Spain",                "Europe",               "EUR", 0.60, 0.030),
    "PT": ("Portugal",             "Europe",               "EUR", 0.50, 0.015),
    "PL": ("Poland",               "Europe",               "PLN", 0.46, 0.050),
    "CH": ("Switzerland",          "Europe",               "CHF", 1.12, 0.008),
    "SE": ("Sweden",               "Europe",               "SEK", 0.76, 0.010),
    "AE": ("United Arab Emirates", "Middle East & Africa", "AED", 0.78, 0.015),
    "ZA": ("South Africa",         "Middle East & Africa", "ZAR", 0.36, 0.030),
    "IN": ("India",                "Asia Pacific",         "INR", 0.27, 0.150),
    "SG": ("Singapore",            "Asia Pacific",         "SGD", 0.86, 0.030),
    "JP": ("Japan",                "Asia Pacific",         "JPY", 0.66, 0.020),
    "AU": ("Australia",            "Asia Pacific",         "AUD", 0.84, 0.030),
    "KR": ("South Korea",          "Asia Pacific",         "KRW", 0.62, 0.010),
    "PH": ("Philippines",          "Asia Pacific",         "PHP", 0.26, 0.032),
}

# --------------------------------------------------------------------------------------
# Offices: 35 sites in 22 countries, every region covered
# --------------------------------------------------------------------------------------
# Street addresses are FICTIONAL. Postal codes are real codes for the business district
# named, and latitude/longitude is the GeoNames centroid of that postal code, except:
#   LOC-007 Sao Paulo: GeoNames only carries city-level CEPs for Brazil, so the point is
#           the map location of CEP 04538-132 (Av. Brig. Faria Lima, Itaim Bibi).
#   LOC-020 Dubai: the UAE has no postal-code system; the point is the Dubai
#           International Financial Centre (DIFC).
# pay_zone   : pay differential inside the country (1.00 = country level)
# opened     : offices opened during the simulation take no one before that date
OFFICES = [
    # id,  office name,          site type,            street (fictional),                  city,            state/province,      postal,     cc,  lat,      lon,       pay_zone, opened,       weight
    ("LOC-001", "Austin HQ",          "Headquarters",       "410 Lantana Crossing, Floor 12",       "Austin",        "Texas",             "78701",    "US", 30.2713,  -97.7426, 1.00, "2012-01-01", 3.0),
    ("LOC-002", "New York",           "Office",             "77 Garnet Lane, Floor 30",             "New York",      "New York",          "10017",    "US", 40.7517,  -73.9707, 1.12, "2014-01-01", 1.4),
    ("LOC-003", "San Francisco",      "Office",             "250 Harbor Light Street, Suite 900",   "San Francisco", "California",        "94105",    "US", 37.7864, -122.3892, 1.15, "2013-01-01", 1.3),
    ("LOC-004", "Atlanta",            "Office",             "1180 Peachwood Parkway, Suite 400",    "Atlanta",       "Georgia",           "30308",    "US", 33.7718,  -84.3757, 0.95, "2016-01-01", 0.9),
    ("LOC-006", "Toronto",            "Office",             "18 Wellmont Street West, Floor 22",    "Toronto",       "Ontario",           "M5H",      "CA", 43.6496,  -79.3833, 1.00, "2015-01-01", 1.0),
    ("LOC-007", "Sao Paulo",          "Regional Hub",       "Rua Jacaranda Azul, 1450, 9o andar",   "Sao Paulo",     "Sao Paulo",         "04538-132","BR",-23.5856,  -46.6830, 1.00, "2015-01-01", 1.0),
    ("LOC-008", "Mexico City",        "Office",             "Calle Bosque Alto 210, Piso 7",        "Mexico City",   "Ciudad de Mexico",  "11560",    "MX", 19.4343,  -99.1933, 1.00, "2016-01-01", 1.0),
    ("LOC-009", "London",             "Regional Hub",       "9 Fenwick Yard",                       "London",        "England",           "EC2A",     "GB", 51.5237,   -0.0877, 1.00, "2013-01-01", 1.0),
    ("LOC-010", "Dublin",             "Office",             "4 Linden Quay",                        "Dublin",        "Leinster",          "D02",      "IE", 53.3400,   -6.2543, 1.00, "2014-01-01", 1.0),
    ("LOC-011", "Berlin",             "Office",             "Lindenhofstrasse 41",                  "Berlin",        "Berlin",            "10117",    "DE", 52.5170,   13.3872, 1.00, "2016-01-01", 1.0),
    ("LOC-012", "Paris",              "Office",             "18 Rue des Tilleuls Clairs",           "Paris",         "Ile-de-France",     "75008",    "FR", 48.8763,    2.3183, 1.00, "2016-01-01", 1.0),
    ("LOC-013", "Warsaw",             "Engineering Center", "ul. Jasnych Ogrodow 12",               "Warsaw",        "Mazowieckie",       "00-844",   "PL", 52.2335,   20.9846, 1.00, "2017-01-01", 1.2),
    ("LOC-014", "Krakow",             "Engineering Center", "ul. Srebrnej Wierzby 8",               "Krakow",        "Malopolskie",       "31-864",   "PL", 50.0748,   19.9964, 0.95, "2018-01-01", 1.0),
    ("LOC-015", "Bengaluru",          "Engineering Center", "Tower B, 88 Silver Oak Ring Road",     "Bengaluru",     "Karnataka",         "560103",   "IN", 13.0907,   77.6423, 1.00, "2014-01-01", 1.4),
    ("LOC-016", "Hyderabad",          "Engineering Center", "Block 3, 21 Pearl Valley Road",        "Hyderabad",     "Telangana",         "500032",   "IN", 17.3939,   78.4529, 0.97, "2017-01-01", 1.2),
    ("LOC-017", "Singapore",          "Regional Hub",       "12 Marina Lantern Way, #20-01",        "Singapore",     "Singapore",         "018989",   "SG",  1.2823,  103.8526, 1.00, "2014-01-01", 1.0),
    ("LOC-018", "Tokyo",              "Office",             "Kiri Building 9F, 2-4 Marunouchi",     "Tokyo",         "Tokyo",             "100-0005", "JP", 35.6738,  139.7616, 1.00, "2016-01-01", 1.0),
    ("LOC-019", "Sydney",             "Office",             "Level 18, 60 Wattlebird Street",       "Sydney",        "New South Wales",   "2000",     "AU",-33.8718,  151.2002, 1.00, "2015-01-01", 1.2),
    ("LOC-020", "Dubai",              "Regional Hub",       "Gate Avenue, Level 6, Unit 604",       "Dubai",         "Dubai",             None,       "AE", 25.2085,   55.2755, 1.00, "2017-01-01", 1.0),
    ("LOC-021", "Johannesburg",       "Office",             "14 Acacia Ridge Drive, Sandton",       "Johannesburg",  "Gauteng",           "2196",     "ZA",-26.1345,   28.0529, 1.00, "2017-01-01", 1.2),
    ("LOC-022", "Cape Town",          "Office",             "3 Fynbos Wharf",                       "Cape Town",     "Western Cape",      "8001",     "ZA",-33.9258,   18.4232, 0.97, "2019-01-01", 0.8),
    ("LOC-023", "Seattle",            "Office",             "1500 Cedar Sound Avenue, Floor 9",     "Seattle",       "Washington",        "98101",    "US", 47.6114, -122.3305, 1.10, "2017-01-01", 1.1),
    ("LOC-024", "Chicago",            "Office",             "320 Prairie Light Drive, Suite 1700",  "Chicago",       "Illinois",          "60606",    "US", 41.8868,  -87.6386, 1.00, "2018-01-01", 1.0),
    ("LOC-025", "Vancouver",          "Office",             "1088 Saltspray Street, Floor 14",      "Vancouver",     "British Columbia",  "V6C",      "CA", 49.2866, -123.1158, 0.98, "2025-01-06", 0.8),
    ("LOC-026", "Guadalajara",        "Engineering Center", "Avenida Paseo Jacaranda 3100, Piso 5", "Zapopan",       "Jalisco",           "45116",    "MX", 20.6847, -103.2189, 0.92, "2023-03-01", 1.1),
    ("LOC-027", "Munich",             "Office",             "Ahornweg 27",                          "Munich",        "Bavaria",           "80333",    "DE", 48.1452,   11.5668, 1.05, "2018-01-01", 0.9),
    ("LOC-028", "Amsterdam",          "Regional Hub",       "Zilverspar 140",                       "Amsterdam",     "North Holland",     "1082",     "NL", 52.3311,    4.8742, 1.00, "2016-01-01", 1.0),
    ("LOC-029", "Madrid",             "Office",             "Calle de los Almendros Blancos 61",    "Madrid",        "Madrid",            "28046",    "ES", 40.4599,   -3.6884, 1.00, "2017-01-01", 1.0),
    ("LOC-030", "Lisbon",             "Engineering Center", "Rua das Acacias Douradas 22",          "Lisbon",        "Lisboa",            "1050-138", "PT", 38.7167,   -9.1333, 1.00, "2023-09-04", 1.0),
    ("LOC-031", "Zurich",             "Office",             "Lindengarten 9",                       "Zurich",        "Zurich",            "8001",     "CH", 47.3721,    8.5417, 1.00, "2019-01-01", 1.0),
    ("LOC-032", "Stockholm",          "Office",             "Bjorkallen 15",                        "Stockholm",     "Stockholm",         "111 57",   "SE", 59.3326,   18.0649, 1.00, "2019-01-01", 1.0),
    ("LOC-033", "Pune",               "Engineering Center", "Wing C, 7 Monsoon Heights",            "Pune",          "Maharashtra",       "411014",   "IN", 18.5685,   73.9158, 0.95, "2024-07-01", 1.0),
    ("LOC-034", "Melbourne",          "Office",             "Level 11, 45 Bluegum Lane",            "Melbourne",     "Victoria",          "3000",     "AU",-37.8130,  144.9611, 0.97, "2018-01-01", 0.9),
    ("LOC-035", "Seoul",              "Office",             "17F, 30 Hanbit-ro",                    "Seoul",         "Seoul",             "06164",    "KR", 37.5108,  127.0593, 1.00, "2024-03-04", 1.0),
    ("LOC-036", "Manila",             "Operations Center",  "28th Avenue Skypark Tower, 15F",       "Taguig",        "Metro Manila",      "1634",     "PH", 14.5195,  121.0621, 1.00, "2022-10-03", 1.0),
]
GEO_SOURCE = {
    "LOC-007": "Map location of CEP 04538-132 (guiafacil.com/cep/04538132)",
    "LOC-020": "Dubai International Financial Centre (latitude.to); the UAE has no postal codes",
}
GEO_SOURCE_DEFAULT = "GeoNames postal code centroid (CC BY 4.0)"

# --------------------------------------------------------------------------------------
# Organization design
# --------------------------------------------------------------------------------------
# Company -> function (led by an executive officer) -> sub-function (led by an SVP/VP
# where a function has more than one) -> department (led by a department head).
FUNCTIONS = {
    # function: (org_unit_id, leader title, leader job level)
    "Technology":         ("ORG-TEC", "Chief Technology Officer",    11),
    "Product":            ("ORG-PRD", "Chief Product Officer",       11),
    "Commercial":         ("ORG-COM", "Chief Revenue Officer",       11),
    "Operations":         ("ORG-OPS", "Chief Operating Officer",     11),
    "Finance":            ("ORG-FIN", "Chief Financial Officer",     11),
    "Marketing":          ("ORG-MKT", "Chief Marketing Officer",     10),
    "People":             ("ORG-PPL", "Chief People Officer",        10),
    "Legal & Compliance": ("ORG-LGL", "General Counsel",             10),
}
CEO = ("ORG-000", "Arcadia Systems", "Chief Executive Officer", 12)

SUB_FUNCTIONS = {
    # sub-function: (org_unit_id, function, leader title or None, leader level, home department)
    "Engineering":     ("ORG-TEC-ENG", "Technology", "Senior Vice President, Engineering",    10, "D-101"),
    "Infrastructure":  ("ORG-TEC-INF", "Technology", "Senior Vice President, Infrastructure",  10, "D-105"),
    "Sales":           ("ORG-COM-SAL", "Commercial", "Senior Vice President, Sales",          10, "D-301"),
    "Client Services": ("ORG-COM-CLS", "Commercial", "Senior Vice President, Client Services", 10, "D-305"),
}

DEPARTMENTS = [
    # dept_id, name, sub_function, function, families {family: weight}, country_profile, size_weight, growth_weight
    ("D-101", "Core Platform Engineering",   "Engineering",        "Technology",         {"SWE": 0.85, "DAT": 0.08, "PRD": 0.07}, "tech",       0.090, 1.2),
    ("D-102", "Product Engineering",         "Engineering",        "Technology",         {"SWE": 0.82, "DAT": 0.10, "PRD": 0.08}, "tech",       0.075, 1.2),
    ("D-103", "Mobile & Web Engineering",    "Engineering",        "Technology",         {"SWE": 0.88, "DSN": 0.06, "PRD": 0.06}, "tech",       0.060, 1.0),
    ("D-104", "Analytics Engineering",       "Engineering",        "Technology",         {"DAT": 0.70, "SWE": 0.30},              "tech",       0.030, 1.0),
    ("D-108", "Data & AI Platform",          "Engineering",        "Technology",         {"DAT": 0.75, "SWE": 0.25},              "tech",       0.000, 1.8),
    ("D-105", "Site Reliability",            "Infrastructure",     "Technology",         {"SWE": 0.75, "ITS": 0.25},              "tech",       0.040, 0.9),
    ("D-106", "Information Security",        "Infrastructure",     "Technology",         {"SEC": 0.85, "SWE": 0.15},              "tech",       0.035, 1.3),
    ("D-107", "Enterprise IT",               "Infrastructure",     "Technology",         {"ITS": 0.90, "SWE": 0.10},              "tech",       0.035, 0.7),
    ("D-201", "Product Management",          "Product",            "Product",            {"PRD": 0.90, "DAT": 0.10},              "corporate",  0.040, 1.0),
    ("D-202", "Design & Research",           "Product",            "Product",            {"DSN": 0.90, "PRD": 0.10},              "corporate",  0.020, 0.9),
    ("D-301", "Enterprise Sales - Americas", "Sales",              "Commercial",         {"SAL": 0.90, "CSM": 0.10},              "amer",       0.055, 1.0),
    ("D-302", "Enterprise Sales - EMEA",     "Sales",              "Commercial",         {"SAL": 0.90, "CSM": 0.10},              "emea",       0.040, 1.0),
    ("D-303", "Enterprise Sales - APAC",     "Sales",              "Commercial",         {"SAL": 0.90, "CSM": 0.10},              "apac",       0.030, 1.1),
    ("D-304", "Sales Operations",            "Sales",              "Commercial",         {"OPS": 0.70, "DAT": 0.30},              "commercial", 0.020, 0.8),
    ("D-307", "Partnerships",                "Sales",              "Commercial",         {"SAL": 0.80, "PRD": 0.20},              "commercial", 0.015, 1.0),
    ("D-305", "Client Success",              "Client Services",    "Commercial",         {"CSM": 0.95, "OPS": 0.05},              "commercial", 0.060, 1.0),
    ("D-306", "Technical Support",           "Client Services",    "Commercial",         {"CSM": 0.60, "SWE": 0.20, "OPS": 0.20}, "support",    0.050, 0.8),
    ("D-401", "Brand & Communications",      "Marketing",          "Marketing",          {"MKT": 1.00},                           "corporate",  0.015, 0.8),
    ("D-402", "Growth Marketing",            "Marketing",          "Marketing",          {"MKT": 0.80, "DAT": 0.20},              "corporate",  0.020, 0.9),
    ("D-501", "FP&A",                        "Finance",            "Finance",            {"FIN": 0.90, "DAT": 0.10},              "corporate",  0.015, 0.8),
    ("D-502", "Accounting & Controllership", "Finance",            "Finance",            {"FIN": 1.00},                           "corporate",  0.020, 0.7),
    ("D-503", "Treasury & Tax",              "Finance",            "Finance",            {"FIN": 1.00},                           "corporate",  0.008, 0.7),
    ("D-601", "HR Business Partners",        "People",             "People",             {"HRM": 1.00},                           "corporate",  0.012, 0.8),
    ("D-602", "Talent Acquisition",          "People",             "People",             {"HRM": 1.00},                           "corporate",  0.012, 1.0),
    ("D-603", "Total Rewards",               "People",             "People",             {"HRM": 0.80, "DAT": 0.20},              "corporate",  0.006, 0.8),
    ("D-604", "People Analytics",            "People",             "People",             {"DAT": 0.70, "HRM": 0.30},              "corporate",  0.004, 1.1),
    ("D-701", "Legal",                       "Legal & Compliance", "Legal & Compliance", {"LGL": 1.00},                           "corporate",  0.010, 0.8),
    ("D-702", "Compliance & Risk",           "Legal & Compliance", "Legal & Compliance", {"LGL": 0.60, "OPS": 0.40},              "corporate",  0.015, 1.0),
    ("D-801", "Customer Operations",         "Operations",         "Operations",         {"OPS": 0.95, "DAT": 0.05},              "ops",        0.080, 1.0),
    ("D-802", "Trust & Safety Operations",   "Operations",         "Operations",         {"OPS": 0.80, "DAT": 0.20},              "ops",        0.045, 1.1),
    ("D-803", "Workplace & Procurement",     "Operations",         "Operations",         {"OPS": 1.00},                           "ops",        0.015, 0.7),
    ("D-901", "Office of the CEO",           "Executive",          "Executive",          {"EXE": 1.00},                           "us_only",    0.000, 0.0),
]

# Country mix multipliers by department profile (1.0 when a country is not listed;
# 0 removes a country from that profile).
_ALL = list(COUNTRIES)
COUNTRY_PROFILES = {
    "tech":       {"IN": 2.2, "PL": 2.0, "PT": 1.8, "IE": 1.2, "CA": 1.2, "MX": 1.2, "GB": 0.8, "FR": 0.4,
                   "JP": 0.3, "AE": 0.2, "PH": 0.5, "CH": 0.8, "AU": 0.5, "KR": 0.6, "SE": 0.8, "SG": 0.6},
    "corporate":  {"US": 1.6, "GB": 1.4, "IE": 1.2, "SG": 1.2, "IN": 0.8, "PL": 0.8, "PT": 0.7, "PH": 0.6,
                   "FR": 0.4, "JP": 0.3, "KR": 0.3, "CH": 0.5, "SE": 0.4, "AU": 0.5, "AE": 0.6, "ZA": 0.5,
                   "BR": 0.6, "MX": 0.5, "CA": 0.6, "DE": 0.5, "NL": 0.6, "ES": 0.5},
    "commercial": {"US": 1.2, "IN": 0.6, "PL": 0.4, "PH": 0.6, "JP": 1.8, "KR": 1.6, "AE": 1.6, "FR": 1.4,
                   "DE": 1.3, "GB": 1.4, "SG": 1.4, "AU": 1.4, "BR": 1.3, "MX": 1.3, "SE": 1.2, "CH": 1.0},
    "amer":       {c: 0.0 for c in _ALL} | {"US": 2.0, "CA": 2.0, "BR": 2.2, "MX": 2.2},
    "emea":       {c: 0.0 for c in _ALL} | {"GB": 2.0, "IE": 1.0, "DE": 2.0, "FR": 2.0, "NL": 1.6, "ES": 1.6,
                                            "PT": 0.6, "PL": 0.6, "CH": 1.5, "SE": 1.5, "AE": 2.0, "ZA": 1.5},
    "apac":       {c: 0.0 for c in _ALL} | {"IN": 1.0, "SG": 2.5, "JP": 3.0, "AU": 3.0, "KR": 2.5, "PH": 0.6},
    "support":    {c: 0.0 for c in _ALL} | {"US": 0.6, "IN": 2.5, "PH": 2.8, "PL": 2.0, "PT": 1.5, "IE": 1.2,
                                            "BR": 1.5, "MX": 1.5, "ZA": 1.8, "SG": 0.5, "CA": 0.5},
    "ops":        {c: 0.0 for c in _ALL} | {"US": 1.0, "IN": 2.5, "PH": 3.0, "PL": 1.8, "PT": 1.2, "IE": 1.0,
                                            "BR": 1.4, "MX": 1.2, "ZA": 1.5, "SG": 0.8, "AE": 0.6, "CA": 0.6},
    "us_only":    {c: 0.0 for c in _ALL} | {"US": 1.0},
}

# --------------------------------------------------------------------------------------
# Jobs and levels
# --------------------------------------------------------------------------------------
JOB_FAMILIES = {
    # code: (family name, title stem for individual contributor levels)
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

# Job levels. us_base is the annual base salary (USD) Arcadia pays a new hire at that
# level in a US pay-zone-1.00 office. Other countries: us_base x pay_index, fixed in local
# currency at the FX reference date below. Range: 85% to 135% of the level base.
#  level: (code, level name, career track, us_base)
JOB_LEVELS = {
    1:  ("L1",  "Associate",                  "Individual Contributor",  65_000),
    2:  ("L2",  "Professional",               "Individual Contributor",  82_000),
    3:  ("L3",  "Senior",                     "Individual Contributor", 102_000),
    4:  ("L4",  "Lead",                       "Individual Contributor", 125_000),
    5:  ("L5",  "Staff / Manager",            "IC or People Manager",   150_000),
    6:  ("L6",  "Principal / Senior Manager", "IC or People Manager",   180_000),
    7:  ("L7",  "Director",                   "People Leader",          220_000),
    8:  ("L8",  "Senior Director",            "People Leader",          265_000),
    9:  ("L9",  "Vice President",             "People Leader",          320_000),
    10: ("L10", "Senior Vice President",      "Executive",              400_000),
    11: ("L11", "Executive Vice President",   "Executive",              480_000),
    12: ("L12", "Chief Executive Officer",    "Executive",              650_000),
}
RANGE_MIN_PCT, RANGE_MAX_PCT = 0.85, 1.35
LEVEL_BASE_FX_DATE = "2022-06-30"      # local level bases are set with this day's ECB rates

# Base salary grows with tenure, not with performance: on each hire anniversary the
# worker gets the raise for the tenure year just completed (capped at the range max).
TENURE_INCREASE = [
    # (completed years from, to inclusive, raise)
    (1, 1, 0.050),
    (2, 2, 0.060),
    (3, 3, 0.050),
    (4, 4, 0.045),
    (5, 5, 0.040),
    (6, 10, 0.030),
    (11, 99, 0.020),
]

# Annual bonus on the fiscal-year review. Paid on Aug 31 to people still employed.
PERFORMANCE_RATINGS = {
    # rating: (bonus as % of base, share of people rated)
    "Excellent":         (0.25, 0.20),
    "Good":              (0.10, 0.70),
    "Needs Improvement": (0.05, 0.10),
}
PROMOTION_PROBABILITY = {"Excellent": 0.22, "Good": 0.055, "Needs Improvement": 0.0}
PROMOTION_TO_L6_FACTOR = 0.6           # Principal / Senior Manager is a harder step
DEMOTION_PROBABILITY_NI = 0.08
PROMOTION_INCREASE = (0.08, 0.12)
DEMOTION_DECREASE = (0.03, 0.08)

# Level mix of the opening population below director (non-executive) and of ordinary
# hires. Directors are placed by org design, not drawn at random: about one Director
# (L7) per DIRECTOR_RATIO people in departments led by L8+, at most 8 under an L8 head,
# and one Senior Director (L8) per 6 Directors in departments led by a VP (L9).
START_LEVEL_MIX = {1: 0.075, 2: 0.18, 3: 0.25, 4: 0.22, 5: 0.165, 6: 0.11}
DIRECTOR_RATIO = 55
HIRE_LEVEL_MIX  = {1: 0.13, 2: 0.24, 3: 0.27, 4: 0.19, 5: 0.11, 6: 0.06}
SPAN_OF_CONTROL_TARGET = 7     # direct reports per manager used to size the first org
SPAN_OF_CONTROL_MAX = 9        # above this a team is split at month-end

# --------------------------------------------------------------------------------------
# Business calendar and workforce assumptions
# --------------------------------------------------------------------------------------
FISCAL_YEAR_START_MONTH = 7            # FY2026 = 2025-07-01 .. 2026-06-30
FIRST_SNAPSHOT = "2022-06-30"
LAST_SNAPSHOT = "2026-06-30"
START_HEADCOUNT = 25_000               # non-executive population at the first month-end
COMP_CONVERSION_DATE = "2022-03-01"    # pay history starts at the HR system conversion

FY_NET_GROWTH = {2023: 0.075, 2024: 0.010, 2025: 0.045, 2026: 0.055}

MONTHLY_ATTRITION = 0.0095
MONTHLY_TRANSFER = 0.0045
OFF_CYCLE_PROMOTION_MONTHLY = 0.0015
MONTHLY_MARKET_ADJUSTMENT = 0.0010
MONTHLY_FTE_CHANGE = 0.0012
LOCATION_MOVE_MONTHLY = 0.0010
INTERNATIONAL_SHARE_OF_TRANSFERS = 0.10
EXTERNAL_SUCCESSOR_SHARE = 0.35        # leader vacancies filled from outside

RESTRUCTURING = {"date": "2024-02-15", "functions": ["Commercial", "Marketing"], "share": 0.05}
REORGANIZATION = {"date": "2024-11-01", "target_department": "D-108",
                  "source_departments": ["D-101", "D-102", "D-104"], "families": ["DAT"]}

COMP_CORRECTION_RATE = 0.006

FX_CONSTANT_RATE_SET = "Latest close (2026-06-30)"
FX_CONSTANT_RATE_DATE = "2026-06-30"
AED_PER_USD_PEG = 3.6725               # Central Bank of the UAE peg, in place since 1997

# --------------------------------------------------------------------------------------
# Names (fictional people). Pools by region; any match with a real person is chance.
# --------------------------------------------------------------------------------------
NAMES = {
    "North America": (["James", "Maria", "Olivia", "Ethan", "Ava", "Noah", "Sophia", "Liam", "Grace", "Daniel",
                       "Chloe", "Marcus", "Hannah", "Tyler", "Nora", "Caleb", "Leah", "Owen", "Ruby", "Isaac",
                       "Avery", "Brandon", "Claire", "Dylan", "Elena", "Gavin", "Harper", "Jordan", "Kayla", "Logan",
                       "Madison", "Nathan", "Paige", "Riley", "Sydney", "Trevor", "Vanessa", "Wesley", "Zoe", "Aaron"],
                      ["Bennett", "Carter", "Hayes", "Morgan", "Reed", "Parker", "Brooks", "Foster", "Graham", "Hughes",
                       "Ellis", "Porter", "Sullivan", "Warren", "Barnes", "Coleman", "Dalton", "Fletcher", "Holland", "Keller",
                       "Abbott", "Baxter", "Caldwell", "Dawson", "Emerson", "Garrett", "Harmon", "Jennings", "Lowell", "Mercer",
                       "Norris", "Osborne", "Prescott", "Quinlan", "Ramsey", "Shelton", "Thornton", "Vaughn", "Whitaker", "Yates"]),
    "Latin America": (["Lucas", "Mariana", "Gabriel", "Camila", "Rafael", "Isabela", "Diego", "Valentina", "Mateus", "Fernanda",
                       "Andres", "Lucia", "Thiago", "Beatriz", "Emilio", "Renata", "Bruno", "Paula", "Joaquin", "Larissa",
                       "Alejandro", "Bianca", "Caio", "Daniela", "Eduardo", "Gabriela", "Hector", "Juliana", "Leonardo", "Marisol",
                       "Nicolas", "Olivia", "Pedro", "Rocio", "Santiago", "Tatiana", "Vicente", "Ximena", "Yago", "Ana"],
                      ["Almeida", "Barbosa", "Cardoso", "Duarte", "Esteves", "Fonseca", "Guerra", "Herrera", "Lozano", "Medeiros",
                       "Navarro", "Ortega", "Pacheco", "Quintero", "Ramos", "Salgado", "Teixeira", "Valdez", "Zamora", "Moreira",
                       "Aguilar", "Bastos", "Cabral", "Dominguez", "Escobar", "Figueroa", "Godoy", "Ibarra", "Jimenez", "Leal",
                       "Mendonca", "Nogueira", "Ochoa", "Peixoto", "Rocha", "Sandoval", "Tavares", "Uribe", "Vidal", "Zapata"]),
    "Europe": (["Lena", "Jonas", "Clara", "Mateo", "Elena", "Lukas", "Sofia", "Hugo", "Anna", "Piotr",
                "Ines", "Felix", "Marta", "Oskar", "Julia", "Pierre", "Aoife", "Niamh", "Sven", "Zofia",
                "Amelie", "Bastian", "Chiara", "Dario", "Elise", "Florian", "Greta", "Henrik", "Ida", "Jakub",
                "Klara", "Lars", "Mila", "Nils", "Ondrej", "Paolo", "Rosa", "Sean", "Tomas", "Ursula"],
               ["Becker", "Dubois", "Fischer", "Garcia", "Jansen", "Kowalski", "Lindqvist", "Moreau", "Novak", "Murphy",
                "Ribeiro", "Schneider", "Vermeulen", "Wagner", "Nowak", "Byrne", "Lambert", "Hoffmann", "Andersson", "Costa",
                "Arnaud", "Brandt", "Castellanos", "De Vries", "Engel", "Fontaine", "Gallagher", "Hansen", "Ivanova", "Jensen",
                "Kaminski", "Lefevre", "Martens", "Nielsen", "O'Connor", "Pereira", "Rossi", "Sandberg", "Visser", "Zielinski"]),
    "Middle East & Africa": (["Omar", "Layla", "Thabo", "Amara", "Karim", "Naledi", "Yusuf", "Zanele", "Samir", "Lerato",
                              "Hassan", "Noura", "Sipho", "Rania", "Tariq", "Ayanda", "Faris", "Mira", "Kagiso", "Salma",
                              "Adel", "Bongani", "Dalia", "Ebrahim", "Fatima", "Ghassan", "Hana", "Imran", "Jamila", "Khaled",
                              "Lindiwe", "Mandla", "Nadia", "Pieter", "Reem", "Sizwe", "Thandeka", "Waleed", "Yasmin", "Ziad"],
                             ["Haddad", "Naidoo", "Mansour", "Dlamini", "Khalil", "Mokoena", "Farouk", "Botha", "Saleh", "Nkosi",
                              "Rahman", "Pillay", "Aziz", "Van Wyk", "Nasser", "Mahlangu", "Qureshi", "Petersen", "Hamdan", "Zulu",
                              "Abdullah", "Bekker", "Chaudhry", "Du Plessis", "El-Amin", "Fourie", "Ghanem", "Hendricks", "Ismail", "Jacobs",
                              "Kruger", "Malik", "Ndlovu", "Osman", "Rashid", "Sithole", "Toure", "Venter", "Yousef", "Zayed"]),
    "Asia Pacific": (["Arjun", "Priya", "Wei", "Yuki", "Rahul", "Ananya", "Min-jun", "Hana", "Vikram", "Mei",
                      "Haruto", "Isha", "Ji-woo", "Aditya", "Sakura", "Kevin", "Angela", "Rohan", "Seo-yeon", "Joshua",
                      "Aarav", "Bianca", "Chen", "Divya", "Eun-ji", "Farhan", "Grace", "Hiroshi", "Ishaan", "Jasmine",
                      "Kenji", "Lakshmi", "Mark", "Neha", "Paolo", "Riya", "Sanjay", "Takumi", "Vivek", "Xin"],
                     ["Sharma", "Tanaka", "Lim", "Kim", "Reddy", "Nakamura", "Tan", "Park", "Iyer", "Wong",
                      "Sato", "Gupta", "Choi", "Santos", "Mehta", "Ong", "Kobayashi", "Rao", "Cruz", "Nair",
                      "Agarwal", "Bautista", "Chua", "Desai", "Fujita", "Ho", "Inoue", "Joshi", "Kapoor", "Lee",
                      "Menon", "Ng", "Pillai", "Reyes", "Suzuki", "Thomas", "Verma", "Watanabe", "Yamamoto", "Zhang"]),
}
