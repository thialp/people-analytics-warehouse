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

# Salary structures move every July 1 (Arcadia pay policy, an assumption, not sourced data).
# The level bases above, at LEVEL_BASE_FX_DATE rates, are the FY2023 range midpoints;
# earlier years are divided back and later years multiplied forward by these increases.
RANGE_ANCHOR_FY = 2023
RANGE_STRUCTURE_INCREASE = {2022: 0.025, 2023: 0.040, 2024: 0.035, 2025: 0.030, 2026: 0.030}
RANGE_STRUCTURE_COUNTRY_PP = {"IN": 0.040, "BR": 0.020, "ZA": 0.020, "PL": 0.020, "PH": 0.020,
                              "MX": 0.015, "JP": -0.015, "CH": -0.015}
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
FIRST_SNAPSHOT = "2021-06-30"
LAST_SNAPSHOT = "2026-06-30"
START_HEADCOUNT = 23_500               # non-executive population at the first month-end (about 25,000 by Jun 2022)
COMP_CONVERSION_DATE = "2021-03-01"    # pay history starts at the HR system conversion

FY_NET_GROWTH = {2022: 0.065, 2023: 0.075, 2024: 0.010, 2025: 0.045, 2026: 0.055}

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

# --------------------------------------------------------------------------------------
# Seats (positions) and requisitions
# --------------------------------------------------------------------------------------
# What happens to a seat when its incumbent leaves or moves to another seat. Leader seats
# (department, sub-function and function heads) and manager seats whose team is handed to
# a successor are always refilled and skip this decision.
SEAT_DECISION = {
    "Backfill as is": 0.60,
    "Backfill re-levelled": 0.15,          # usually one level down; a manager seat becomes an IC seat
    "Backfill relocated": 0.10,            # another office in the same country, leaning to lower pay zones
    "Freeze": 0.10,
    "Eliminate": 0.05,
}
SEAT_DECISION_RESTRUCTURING = {"Eliminate": 0.75, "Freeze": 0.25}
RELEVEL_DOWN_SHARE = 0.80
RELOCATE_ZONE_POWER = 6                    # office weight x pay_zone ** -6: San Francisco seats drift to Austin
FROZEN_SEAT_DAYS = (60, 300)               # a frozen seat is resolved after this many days ...
FROZEN_SEAT_UNFREEZE_SHARE = 0.50          # ... reopened for hiring, otherwise eliminated
REQ_APPROVAL_DAYS = (0, 14)                # requisition opened -> approved
REQ_LATE_APPROVAL = (0.08, (30, 75))       # share of requisitions approved late, and how late
REQ_TIME_TO_FILL_MEDIAN = {1: 35, 2: 35, 3: 40, 4: 48, 5: 55, 6: 62, 7: 80, 8: 90, 9: 100, 10: 100, 11: 100}
REQ_TIME_TO_FILL_SIGMA = 0.45
REQ_TIME_TO_FILL_MIN = 10
REQ_MAX_OPEN_DAYS = 210                    # an approved requisition still open after this is cancelled
REQ_CANCELLED_FREEZE_SHARE = 0.50          # a cancelled seat is frozen, otherwise eliminated
TRANSFER_TAKES_OPEN_SEAT = 0.85            # an internal mover takes a ready open seat when one fits

# Release 5: time to fill varies by function and by graduate season (Dashboard #5, Seats to Fill).
# Applied to the approval date only: the hire date the simulation draws never moves, so headcount,
# pay and contractors are unchanged. Net-new PIDs are approved this much earlier or later before
# the hire; a filled external backfill has its approval moved, never more than
# REQ_BACKFILL_EARLY_APPROVAL_DAYS before the person who left gave notice (their last day).
REQ_TTF_FUNCTION_FACTOR = {"Technology": 1.15, "Legal & Compliance": 1.15, "Operations": 0.85}
REQ_TTF_GRAD_LEVELS = (1, 2)               # graduate hiring: Associate and Analyst levels
REQ_TTF_GRAD_FACTOR = 0.75                 # a fill in its country's graduate season takes 25% less time
REQ_TTF_GRAD_SEASON_DEFAULT = (9, 10)      # September and October: North America and Europe
REQ_TTF_GRAD_SEASON = {"BR": (12, 1), "ZA": (12, 1), "AU": (12, 1),   # southern hemisphere: Dec and Jan
                       "IN": (7, 8), "SG": (7, 8), "PH": (6, 7), "MX": (7, 8),
                       "JP": (4, 4), "KR": (2, 3)}
REQ_BACKFILL_EARLY_APPROVAL_DAYS = 14

# --------------------------------------------------------------------------------------
# Workforce plan: a budget before each fiscal year, then a reforecast after each of the
# first three quarters (RF1-RF3), each covering the quarters still ahead. Versions are
# never overwritten. The generator writes the plan around what happened, with an error
# that shrinks with each reforecast: (log-mean, log-sd) of planned / actual.
# --------------------------------------------------------------------------------------
PLAN_VERSIONS = [  # name, (month, day) of the version date, first quarter covered
    ("Budget", (5, 15), 1), ("RF1", (10, 15), 2), ("RF2", (1, 15), 3), ("RF3", (4, 15), 4)]
PLAN_NET_NEW_ERROR = {"Budget": (0.15, 0.35), "RF1": (0.08, 0.25), "RF2": (0.04, 0.18), "RF3": (0.02, 0.12)}
PLAN_BACKFILL_ERROR = {"Budget": (0.04, 0.20), "RF1": (0.02, 0.15), "RF2": (0.01, 0.10), "RF3": (0.00, 0.07)}
PLAN_HEADCOUNT_ERROR = {"Budget": (0.012, 0.030), "RF1": (0.008, 0.020), "RF2": (0.004, 0.012), "RF3": (0.002, 0.007)}
PLAN_COST_EXTRA_SD = 0.010                 # cost error on top of the headcount error
PLAN_FY_BUDGET_SHIFT = {2024: (0.80, 0.035)}  # FY24 budget was set before the Feb 2024 restructuring

# Release 5: the budget for the year after the report date (the forward budget), approved on May 15
# before the report date, like every budget. Nothing after the report date has been simulated, so it
# is a projection: each cost center's fills in the same quarter of the last fiscal year, scaled by
# the planned growth, with the budget's planning error; headcount grows from the report date.
FORWARD_BUDGET_NET_GROWTH = 0.050          # planned net headcount growth in the forward year
FORWARD_BUDGET_CW_GROWTH = 0.060           # planned contingent headcount growth in the forward year

# --------------------------------------------------------------------------------------
# Candidates (applicant tracking): applicants per requisition with a real search,
# and where the others drop out
# --------------------------------------------------------------------------------------
CANDIDATES_PER_REQ = {1: 7, 2: 7, 3: 6, 4: 5, 5: 5, 6: 4, 7: 4, 8: 3, 9: 3, 10: 3, 11: 3}
CANDIDATE_EXIT_STAGE = {"Screen": 0.55, "Interview": 0.27, "Offer": 0.05, "Withdrawn": 0.13}
OFFER_DECLINED_SHARE = 0.12                # a search where an earlier offer was declined
CANDIDATE_SOURCES = {"Job board": 0.40, "Referral": 0.22, "Agency": 0.10, "Career site": 0.20, "Sourced": 0.08}

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


# --------------------------------------------------------------------------------------
# Contingent workforce (release 3): Bridgeway VMS
# --------------------------------------------------------------------------------------
# Every value here is a fictional design choice. Hourly rates were sanity-checked against
# aggregate public market ranges for IT contracting (medians by country, no source rows).
CW_BURN_IN_START = "2013-07-31"       # the simulation starts here so the Jun 2021 population has real ages
CW_ARCHIVE_BEFORE = "2020-07-01"      # Bridgeway archives workers whose last assignment ended before this
CW_EXTRACT_DATE = "2026-06-30"        # the extract the warehouse loads: nothing dated later is in it
# Active contingent workers at each month-end: Jul 2013 start, Jun 2021, then growth by fiscal year.
CW_TARGET_START = 4_600
CW_TARGET_JUN_2021 = 8_350
CW_FY_GROWTH = {2022: 0.08, 2023: 0.10, 2024: -0.03, 2025: 0.08, 2026: 0.115}   # FY24: the restructuring cut contractors too

CW_TYPES = ["Contractor", "Consultant", "BPO"]
CW_TYPE_FLOW = {"Contractor": 0.700, "Consultant": 0.225, "BPO": 0.075}   # share of NEW engagements (BPO stays longest)
CW_MAX_MONTHS = 48                    # Contractor and Consultant: 24 initial + 24 extension; BPO uncapped
CW_CAP_BREACH = 0.012                 # share of engagements reaching the cap that are extended anyway
CW_INITIAL_TERM_MONTHS = {"Contractor": ({6: 0.15, 9: 0.10, 12: 0.40, 18: 0.15, 24: 0.20}),
                          "Consultant": ({3: 0.20, 6: 0.40, 9: 0.15, 12: 0.25})}
CW_EXTENSION_MONTHS = {3: 0.20, 6: 0.40, 9: 0.15, 12: 0.25}
CW_EXTEND_PROBABILITY = {"Contractor": 0.66, "Consultant": 0.45}
CW_RENEWAL_SHARE = 0.12               # extensions processed as a new service order instead of a revision
CW_RENEGOTIATE_SHARE = 0.30           # extensions and renewals that change the rate
CW_RENEGOTIATE_RANGE = (-0.05, 0.08)
CW_BPO_RENEWAL_PROBABILITY = 0.82     # BPO orders run to June 30 and are renewed as a new order on July 1
CW_EARLY_END_MONTHLY = {"Contractor": 0.0055, "Consultant": 0.0090, "BPO": 0.0035}
CW_RESTRUCTURING_CUT = 0.35           # Commercial and Marketing contingent workers ended in the Feb 2024 restructuring
CW_ATTRIBUTE_CHANGE_MONTHLY = {"Cost center change": 0.004, "Manager change": 0.006, "Office change": 0.002}
CW_WITHDRAWN_SHARE = 0.04             # requests whose submitted worker is withdrawn or rejected before starting
CW_LATE_EXTENSION_SHARE = 0.06        # extensions approved after the old end date
# Contingent PIDs in Keystone (release 3.1, generator/cw_positions.py)
CW_PID_REUSE_SHARE = 0.45             # an approved request takes a matching vacant PID this often; otherwise HR Ops creates a new one
CW_PID_AUDIT_MONTHS = (1, 7)          # the position audit runs at the end of January and July
CW_PID_AUDIT_MIN_DAYS = 180           # it looks at contingent PIDs vacant this long or longer
CW_PID_AUDIT_CLOSE_SHARE = 0.30       # and closes this share of them; the rest stay vacant
CW_PID_START_NUMBER = 800000          # contingent PIDs are P800001 upward (employee PIDs start at P200001)
CW_LOCAL_BILLING_SHARE = {"IN": 0.10, "PL": 0.30, "GB": 0.50, "CA": 0.60, "SG": 0.30, "AU": 0.50, "JP": 0.70,
                          "DE": 0.40, "FR": 0.40, "NL": 0.40, "IE": 0.40, "ES": 0.40, "PT": 0.30, "CH": 0.60,
                          "SE": 0.50, "MX": 0.10, "BR": 0.20, "ZA": 0.30, "AE": 0.20, "KR": 0.50, "PH": 0.10, "US": 0.0}
CW_BPO_LOCAL_BILLING_SHARE = 0.80

# Where engagements are placed, by type (renormalised over countries with an office open that day)
CW_COUNTRY_MIX = {
    "Contractor": {"IN": 0.50, "PL": 0.12, "MX": 0.10, "PH": 0.07, "PT": 0.05, "US": 0.06, "GB": 0.02, "CA": 0.02,
                   "BR": 0.03, "ZA": 0.02, "ES": 0.01},
    "Consultant": {"US": 0.28, "GB": 0.10, "IN": 0.24, "DE": 0.05, "SG": 0.05, "AU": 0.03, "FR": 0.03, "NL": 0.03,
                   "CA": 0.04, "IE": 0.03, "ES": 0.03, "CH": 0.01, "SE": 0.02, "AE": 0.02, "JP": 0.02, "BR": 0.02},
    "BPO": "workforce",               # proportional to each country's employee weight
}
CW_FUNCTION_MIX = {                   # department picked by function share, then by department size
    "Contractor": {"Technology": 0.75, "Product": 0.06, "Operations": 0.08, "Commercial": 0.05,
                   "Finance": 0.02, "People": 0.02, "Marketing": 0.01, "Legal & Compliance": 0.01},
    "Consultant": {"Technology": 0.45, "Finance": 0.15, "People": 0.10, "Marketing": 0.10,
                   "Legal & Compliance": 0.08, "Product": 0.07, "Commercial": 0.05},
    "BPO": {"D-803": 0.55, "D-107": 0.25, "D-801": 0.20},   # facilities and security, service desk, customer support
}
CW_ROLE_FAMILIES_TECH = {"Development": 0.52, "QA": 0.15, "Data": 0.12, "Project Delivery": 0.08,
                         "Architecture": 0.06, "Design": 0.07}
CW_ROLE_FAMILIES_BUSINESS = {"Analyst": 0.40, "Project Delivery": 0.30, "Data": 0.15, "Operations": 0.15}
CW_ROLE_FAMILIES_BPO = {"D-803": {"Security": 0.55, "Facilities": 0.45}, "D-107": {"Service Desk": 1.0},
                        "D-801": {"Customer Support": 1.0}}
CW_SENIORITY_MIX = {"Contractor": {"Junior": 0.20, "Mid": 0.45, "Senior": 0.27, "Lead": 0.08},
                    "Consultant": {"Mid": 0.20, "Senior": 0.50, "Lead": 0.30},
                    "BPO": {"Junior": 0.50, "Mid": 0.40, "Senior": 0.10}}
CW_ROLE_TITLES = {"Development": "Software Developer", "QA": "QA Engineer", "Data": "Data Engineer",
                  "Project Delivery": "Project Manager", "Architecture": "Solutions Architect",
                  "Design": "UX Designer", "Analyst": "Business Analyst", "Operations": "Operations Specialist",
                  "Security": "Security Officer", "Facilities": "Facilities Technician",
                  "Service Desk": "Service Desk Analyst", "Customer Support": "Customer Support Agent"}

# Rate card. Hourly USD target for a Mid Contractor in Development, FY2026. Anchors where aggregate
# market medians were checked; other countries 20 + 70 x pay_index.
CW_RATE_ANCHOR_USD = {"IN": 31.0, "PH": 28.0, "MX": 53.0, "PL": 63.0, "PT": 50.0, "US": 80.0, "GB": 93.0,
                      "SG": 64.0, "CA": 78.0}
CW_SENIORITY_FACTOR = {"Junior": 0.75, "Mid": 1.00, "Senior": 1.30, "Lead": 1.55}
CW_TYPE_FACTOR = {"Contractor": 1.00, "Consultant": 1.35}
CW_ROLE_FACTOR = {"Development": 1.00, "QA": 0.85, "Data": 1.10, "Analyst": 0.90, "Project Delivery": 1.00,
                  "Architecture": 1.30, "Design": 0.95, "Operations": 0.75}
CW_BPO_HOURLY_SHARE = 0.30            # BPO monthly fee = 168 h x anchor x this x role x seniority
CW_BPO_ROLE_FACTOR = {"Security": 1.00, "Facilities": 0.90, "Service Desk": 1.25, "Customer Support": 1.10}
CW_RATE_MARKET_INDEX = 0.03           # rate cards rise this much each July 1 (India +2 points)
CW_RATE_MARKET_INDEX_COUNTRY_PP = {"IN": 0.02, "PH": 0.01, "MX": 0.01, "BR": 0.02}
CW_RATE_BAND = (0.88, 1.15)           # band low / high as a share of target
CW_RATE_NOISE_SD = 0.07               # order rates scatter around the target

# Suppliers (fictional names, invented to match no real firm)
#   id, name, types offered, HQ country, countries served (None = everywhere), size weight, onboarded, offboarded
CW_SUPPLIERS = [
    ("SUP-001", "Vantrell Technical Staffing",     "Contractor",            "US", None,                          5.0, "2012-03-01", None),
    ("SUP-002", "Quorlan Digital Workforce",       "Contractor",            "IN", ["IN", "PL", "MX", "PH"],      6.0, "2014-06-01", None),
    ("SUP-003", "Halvery Engineering Services",    "Contractor",            "IN", ["IN", "PH", "SG"],            4.0, "2015-01-15", None),
    ("SUP-004", "Brennick Talent Partners",        "Contractor;Consultant", "US", ["US", "CA", "GB", "IE"],      3.0, "2013-09-01", None),
    ("SUP-005", "Thornquist Systems Staffing",     "Contractor",            "PL", ["PL", "PT", "ES", "DE", "IE"], 3.5, "2016-02-01", None),
    ("SUP-006", "Ellsmere IT Resourcing",          "Contractor",            "IN", ["IN"],                        3.0, "2015-05-01", None),
    ("SUP-007", "Marrowby Software Services",      "Contractor",            "MX", ["MX", "BR", "US"],            2.5, "2016-01-10", None),
    ("SUP-008", "Calderine Tech Partners",         "Contractor",            "SG", ["PH", "SG", "AU", "JP", "KR"], 1.5, "2017-04-01", None),
    ("SUP-009", "Ostrel Data Staffing",            "Contractor",            "GB", None,                          1.5, "2018-08-01", None),
    ("SUP-010", "Wexcombe Delivery Group",         "Contractor",            "ZA", ["ZA", "AE", "GB", "IE"],      1.0, "2017-11-01", None),
    ("SUP-011", "Pellatine Contract Talent",       "Contractor",            "US", ["US"],                        1.0, "2014-02-01", "2022-06-30"),
    ("SUP-012", "Drumlow Engineering",             "Contractor",            "DE", ["DE", "NL", "SE", "CH", "FR"], 1.0, "2019-03-01", None),
    ("SUP-013", "Fenwarren Staffing",              "Contractor",            "CA", ["CA", "US"],                  1.0, "2020-01-15", None),
    ("SUP-014", "Ashgrove Advisory",               "Consultant",            "US", None,                          3.0, "2013-01-01", None),
    ("SUP-015", "Kilnford Consulting",             "Consultant",            "GB", None,                          2.5, "2014-10-01", None),
    ("SUP-016", "Merriden Vale Partners",          "Consultant",            "US", ["US", "CA", "GB"],            1.5, "2016-07-01", None),
    ("SUP-017", "Corvanne Consulting",             "Consultant",            "SG", ["SG", "IN", "AU", "JP", "KR", "AE"], 1.5, "2018-02-01", None),
    ("SUP-018", "Halsted Brook Advisory",          "Consultant",            "DE", ["DE", "FR", "NL", "CH", "SE", "ES", "IE"], 1.0, "2019-09-01", None),
    ("SUP-019", "Sentrel Security Services",       "BPO",                   "GB", None,                          3.0, "2012-01-01", None),
    ("SUP-020", "Brightmoor Facility Services",    "BPO",                   "US", None,                          3.0, "2012-01-01", None),
    ("SUP-021", "Quaystone Service Desk Solutions", "BPO",                  "IN", None,                          2.0, "2011-03-01", None),
    ("SUP-022", "Ravelin Customer Care",           "BPO",                   "PH", None,                          2.0, "2012-05-01", None),
    ("SUP-023", "Tollbrook Facilities Group",      "BPO",                   "MX", ["MX", "BR", "US", "CA"],      1.0, "2018-01-01", None),
]
CW_BPO_SUPPLIER_ROLES = {"SUP-019": ["Security"], "SUP-020": ["Facilities", "Security"], "SUP-023": ["Facilities"],
                         "SUP-021": ["Service Desk"], "SUP-022": ["Customer Support"]}
CW_EMAIL_DOMAIN = "ext.arcadia-systems.example"      # reserved .example domain: never a real address
EMPLOYEE_EMAIL_DOMAIN = "arcadia-systems.example"


# ======================================================================================
# Keystone HR and the Bridgeway -> Keystone feed (release 3, phase 4)
# How the one-way integration behaves, and what people do by hand in Keystone. Every rate
# here is a seeded imperfection; the answer key (gen_cw_discrepancy_truth) records each one.
# ======================================================================================
KS_CW_PERSON_ID_START = 500_001          # contingent workers take Keystone person IDs from W500001
KS_HISTORY_KEEP_FROM = "2021-06-30"      # the answer key covers the warehouse history window

# Days from sent to applied for an event that goes through; 3+ days is "arrived late"
FEED_LAG_DAYS = {0: 0.50, 1: 0.33, 2: 0.11}
FEED_LATE_DAYS = (3, 15)                  # the remaining 6%: uniform, inclusive
# Share of events that fail outright, by event type
FEED_FAIL = {"New Worker": 0.005, "Renewal": 0.015, "Extension": 0.015, "Early End": 0.02,
             "Attribute Change": 0.01}
FEED_PARTIAL_LINK = 0.006                 # a New Worker loads without the Bridgeway ID (blank link)
FEED_ERRORS = {
    "timeout": "Delivery failed: message dead-lettered after 3 retries",
    "validation": "Validation failed: target record locked by another transaction",
    "mapping": "Mapping error: payload rejected by the inbound schema",
    "not_found": "Worker not found for external ID {bw}",
    "partial": "Partial load: external worker ID not mapped; record created without it",
    "converted": "Rejected: worker {bw} was converted to an employee; the contingent record is closed",
}

# HR Ops repairs: probability a case is fixed by hand, and the delay in days (uniform, inclusive)
KS_FIX = {"Never reached Keystone": (0.65, (7, 60)), "Link ID missing or mistyped": (0.55, (15, 120)),
          "Extension never arrived": (0.60, (2, 20)), "Early end never arrived": (0.50, (3, 30)),
          "Attribute change never arrived": (0.30, (10, 60))}
KS_MANUAL_LINK_TYPO = 0.25                # a record HR Ops creates by hand has the Bridgeway ID mistyped
KS_MANUAL_SUPPLIER_VARIANT = 0.50         # ... and the supplier typed its own way

# Edits made in Keystone only (managers and HR Ops), per active worker per month
KS_LOCAL_EDIT_MONTHLY = {"Cost center": 0.0012, "Manager": 0.0016, "Office": 0.0006}
KS_LOCAL_EDIT_BY_MANAGER = 0.60           # the rest by HR Ops

# Contingent workers created by hand in Keystone with no Bridgeway order, per month from KS_ONLY_FROM
KS_ONLY_MONTHLY = 0.6
KS_ONLY_FROM = "2019-01-01"

# Bridgeway-side hygiene
BW_SLOW_CLOSURE_SHARE = 0.03              # ended orders not closed within the normal 0-15 days
BW_SLOW_CLOSURE_DAYS = (17, 400)          # closed this late (open past the 15-day grace), or never if that falls after the extract
BW_BILLED_AFTER_END_SHARE = 0.004         # ended orders that bill time in the month after the last day
BW_SPLIT_RENEWAL_SHARE = 0.005            # renewals the supplier submitted as a new worker (a second Bridgeway ID)

# Supplier names as people type them in Keystone (by hand); the feed sends the exact name
KS_SUPPLIER_VARIANTS = {
    "Vantrell Technical Staffing": ["Vantrell Tech Staffing", "VANTRELL TECHNICAL STAFFING INC"],
    "Quorlan Digital Workforce": ["Quorlan Digital", "Quorlan Digital Workforce Pvt Ltd"],
    "Halvery Engineering Services": ["Halvery Engg Services", "Halvery Engineering"],
    "Brennick Talent Partners": ["Brennick Talent", "Brennick Talent Partners LLC"],
    "Thornquist Systems Staffing": ["Thornquist Systems", "Thornquist Staffing Sp. z o.o."],
    "Ellsmere IT Resourcing": ["Ellsmere IT", "Ellsmere I.T. Resourcing"],
    "Marrowby Software Services": ["Marrowby Software", "Marrowby SW Services"],
    "Calderine Tech Partners": ["Calderine Tech", "Calderine Technology Partners"],
    "Ostrel Data Staffing": ["Ostrel Data", "Ostrel Data Staffing Ltd"],
    "Wexcombe Delivery Group": ["Wexcombe Delivery", "Wexcombe Group"],
    "Pellatine Contract Talent": ["Pellatine Contract", "Pellatine Talent"],
    "Drumlow Engineering": ["Drumlow Engineering GmbH", "Drumlow Eng."],
    "Fenwarren Staffing": ["Fenwarren Staffing Inc", "Fen Warren Staffing"],
    "Ashgrove Advisory": ["Ashgrove Advisory Group", "Ashgrove"],
    "Kilnford Consulting": ["Kilnford Consulting Ltd", "Kilnford"],
    "Merriden Vale Partners": ["Merriden Vale", "MerridenVale Partners"],
    "Corvanne Consulting": ["Corvanne Consulting Pte", "Corvanne"],
    "Halsted Brook Advisory": ["Halsted Brook", "Halstead Brook Advisory"],
    "Sentrel Security Services": ["Sentrel Security", "Sentrel Security Svcs"],
    "Brightmoor Facility Services": ["Brightmoor Facilities", "Brightmoor Facility Svcs"],
    "Quaystone Service Desk Solutions": ["Quaystone Service Desk", "Quaystone SD Solutions"],
    "Ravelin Customer Care": ["Ravelin CX", "Ravelin Customer Care Inc"],
    "Tollbrook Facilities Group": ["Tollbrook Facilities", "Tollbrook Group"],
}


# ======================================================================================
# Conversions and the contingent workforce plan line (release 3, phase 5)
# ======================================================================================
# A contingent worker whose engagement ends may be hired as an employee into an open
# requisition: the same person, a new employee ID. Only Contractors and Consultants; the
# hire is in the same country and department (or, failing that, function), in the same
# calendar month as the first day after the engagement, and at most this many days later,
# so a conversion moves a person between worker types without changing the total.
CW_CONVERSION_ATTEMPT = 0.065            # share of eligible engagement ends that look for a requisition to fill
CW_CONVERSION_MAX_GAP_DAYS = 21
CW_CONVERSION_FROM = "2021-07-01"        # requisitions (and so conversions) are in the warehouse from FY22

# The plan carries a contingent line per cost center x quarter x version: planned CW
# headcount at the quarter end and the annualized spend run-rate (hourly rate x contracted
# hours x 52, or monthly rate x 12), in USD at the plan's FX date. Contingent plans are
# looser than employee plans: managers bring contractors in as work appears.
PLAN_CW_ERROR = {"Budget": (0.030, 0.080), "RF1": (0.020, 0.060), "RF2": (0.010, 0.040), "RF3": (0.005, 0.025)}
PLAN_CW_COST_EXTRA_SD = 0.020
PLAN_CW_FY_BUDGET_SHIFT = {2024: 0.050}  # the FY24 budget did not foresee the February 2024 contractor cuts


# ======================================================================================
# Reconciliation operations (release 4, case study 4): times, Keystone job data, the
# warehouse load log and the Helix Service Desk
# ======================================================================================
# Each piece draws from its own random stream after everything above, so no earlier table moves.
# The warehouse runs on GMT (Bangalore): it reads Bridgeway at 00:00, Keystone when Bridgeway is
# done (about 00:20) and Helix at 00:00 and 12:00. A month-end close is the 00:00 run on the 1st.
OPS_LOG_FROM = "2021-06-01"               # the first run in the load log (it reads May 31, 2021)
OPS_LOG_TO = "2026-07-01"                 # the last run: reads the extract date, Jun 30, 2026

# Hours (GMT) people and systems work in. A change is sent by the hourly feed batch that picks it up.
OPS_SEND_HOURS = {"Americas": (14, 23, 0.55), "EMEA": (7, 16, 0.30), "APAC": (1, 9, 0.15)}   # first, last, share
OPS_OFFICE_HOURS = {"North America": (14, 23), "Latin America": (13, 22), "Europe": (7, 16),
                    "Middle East & Africa": (6, 15), "Asia Pacific": (1, 9)}
OPS_HR_OPS_HOURS = (3, 12)                # HR Operations sits in Bangalore: 09:00 to 18:00 IST
OPS_VENDOR_MGMT_HOURS = (14, 23)          # Vendor Management sits in Austin
OPS_DATA_ENG_HOURS = (3, 13)              # Data engineering sits in Bangalore

# Load log: share of daily runs that start late (more than an hour after schedule) or fail.
# A failed run reads nothing; the warehouse keeps the source's previous load, one day stale.
OPS_LOAD_LATE = {"BW": 0.015, "KS": 0.020, "HLX": 0.010}
OPS_LOAD_FAIL = {"BW": 0.003, "KS": 0.003, "HLX": 0.003}
# Failures on a close run are not left to chance (random failures skip close runs): these closes
# had an outage of that many nights, so the page can show what a stale source does to Finance's
# report. The close then runs on the source as it stood before the outage.
OPS_CLOSE_FAILURES = {"2023-09-30": ("BW", 2), "2024-12-31": ("KS", 3), "2026-03-31": ("HLX", 2)}
OPS_LOAD_ERRORS = {"BW": "Extract not delivered: SFTP transfer timed out after 3 retries",
                   "KS": "Extract job failed: snapshot lock not released by the nightly batch",
                   "HLX": "API read failed: HTTP 503 from the Helix export endpoint"}

# Keystone job data: the PID each contingent worker's job record holds (EMPLID x record number).
# Normally a job row starts on the assignment's first day and is terminated the day after its last
# day. Two seeded imperfections, fixed by HR Ops on the day they notice (never backdated):
CW_JOB_RETURN_KEEP_OLD = 0.60             # a return on another PID within 120 days leaves the old job active
CW_JOB_RETURN_KEEP_DAYS = (15, 240)       # until HR Ops ends it this many days after the return
CW_JOB_RETURN_NEVER = 0.08                # ... or never
CW_JOB_SAME_PID_NEW_RECORD = 0.16         # a return to the same PID entered as a new record, the old one left active
CW_JOB_LATE_END = 0.004                   # any other end: the job stays active after the last day
CW_JOB_LATE_END_DAYS = (16, 180)
CW_JOB_LATE_END_NEVER = 0.05

# Helix Service Desk (fictional): contingent worker tickets only; the tables are generic.
HLX_START = "2021-01-01"                  # Helix went live; gaps already open then get a ticket later, if at all
HLX_LEGACY_MEAN_DAYS = 300                # ... after this many days on average
HLX_FIRST_NUMBER = 100001
# Per behaviour: share of gaps that get a ticket, and the delay in days from the gap's first day.
# The behaviour follows what the gap does to people, so it is set per category in helix_service_desk.
HLX_TICKET_RULES = {
    "Access lost":          (0.90, (1, 3)),        # the contractor cannot log in and says so
    "Access kept":          (0.60, (3, 20)),
    "Cost center":          (0.40, None),          # mostly 1 to 5 days after the next close (Finance notices)
    "Billing":              (0.50, None),          # an open order at Vendor Management's review on the 10th; a late invoice when it comes in
    "Headcount":            (0.30, (5, 45)),
    "PID":                  (0.30, (10, 60)),
    "Feed stuck":           (0.15, (1, 2)),        # data engineering's monitoring
}
HLX_COST_CENTER_AFTER_CLOSE = 0.75
HLX_LATE_NOTICE_MEAN_DAYS = 150           # a gap nobody raised at first is noticed later (a review, an audit), if it lasts
HLX_MISROUTED = 0.10                      # first assigned to the wrong group, reassigned within 1 to 4 days
HLX_RESOLVED_IN_ERROR = 0.08              # resolved while the gap is still there
HLX_REOPENED = 0.70                       # ... and reopened 3 to 15 days later
HLX_NO_LONGER_REPRODUCIBLE_DAYS = (10, 60)
HLX_PENDING_SUPPLIER = 0.35               # Bridgeway tickets that wait on the supplier for a while
HLX_LINK_QUALITY = {"ID field": 0.70, "Name in text": 0.20, "None": 0.10}
