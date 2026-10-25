# Dashboard #4 field spec: parameters and calculated fields from dashboard_4_build.md
# (sections 6, 7.1-7.8, 10, 11, 12.4, 13.1, 13.3, 14.1, 15.1, 16).
# Each calc: (caption, datatype, kind, formula)  kind: 'row' | 'agg' | 'tc' (table calc)
# References use captions: [Gap Now], [p_Close]; the builder turns them into internal names.

PARAMS = [
    # caption, datatype, domain, value
    ("p_Close", "date", "any", "#2026-06-30#"),
    ("p_Functions", "string", "any", '""'),
    ("p_Departments", "string", "any", '""'),
    ("p_Countries", "string", "any", '""'),
    ("p_ShowList", "boolean", "list", "false"),
    ("p_CloseOpen", "boolean", "list", "false"),
    ("p_FunctionOpen", "boolean", "list", "false"),
    ("p_DepartmentOpen", "boolean", "list", "false"),
    ("p_CountryOpen", "boolean", "list", "false"),
    ("p_InfoOpen", "boolean", "list", "false"),
]


def comma(x):
    return (f'IF ISNULL({x}) THEN "N/A"\n'
            f'ELSEIF {x} >= 1000 THEN STR(DIV(INT({x}), 1000)) + "," + RIGHT("00" + STR(INT({x}) % 1000), 3)\n'
            f'ELSE STR(INT({x})) END')


def rate(x):
    return (f'IF ISNULL({x}) THEN "N/A" ELSE\n'
            f'STR(DIV(INT(ROUND({x} * 10000, 0)), 100)) + "." + RIGHT("0" + STR(INT(ROUND({x} * 10000, 0)) % 100), 2) + "%" END')


def field_text(count, p, cut):
    name = f'MID({p}, 2, LEN({p}) - 2)'
    single = f'(IF LEN({name}) > 20 THEN LEFT({name}, 19) + "…" ELSE {name} END)' if cut else name
    return (f'IF {count} = 0 THEN "All"\n'
            f'ELSEIF {count} = 1 THEN {single}\n'
            f'ELSE STR({count}) + " selected" END')


def toggle(p, f):
    return (f'IF CONTAINS({p}, "|" + {f} + "|")\n'
            f'THEN (IF {p} = "|" + {f} + "|" THEN "" ELSE REPLACE({p}, "|" + {f} + "|", "|") END)\n'
            f'ELSE (IF {p} = "" THEN "|" + {f} + "|" ELSE {p} + {f} + "|" END) END')


def day_text(x):
    return f'LEFT(DATENAME(\'month\', {x}), 3) + " " + STR(DAY({x})) + ", " + STR(YEAR({x}))'


def tip_place(place, words):
    n = f'SUM(IF [Sankey Gap Row] AND [place] = "{place}" THEN 1 END)'
    return f'IF {n} > 0\nTHEN "{words} " + STR({n}) END'


C = []
def add(cap, dt, kind, f):
    C.append((cap, dt, kind, f))

# ---------- 7.1 Close and scope
add("Latest Close", "date", "row", "{ MAX([month_end_date]) }")
add("First Close", "date", "row", "{ MIN([month_end_date]) }")
add("Prior Close", "date", "row", "DATEADD('day', -1, DATETRUNC('month', [p_Close]))")
add("Year Ago Close", "date", "row", "DATEADD('day', -1, DATEADD('month', -11, DATETRUNC('month', [p_Close])))")
add("Is Selected Close", "boolean", "row", "[month_end_date] = [p_Close]")
add("Is Prior Close", "boolean", "row", "[month_end_date] = [Prior Close]")
add("Is Current", "boolean", "row", "[p_Close] = [Latest Close]")
# aggregate, so it mixes with the K strings on the KPI cards
add("Has Prior", "boolean", "agg", "[p_Close] > MIN([First Close])")
add("Close Month", "string", "row", "DATENAME('month', [p_Close])")
add("Close Name", "string", "row", "DATENAME('month', [p_Close]) + \" \" + STR(YEAR([p_Close]))")
add("Close Short", "string", "row", "LEFT(DATENAME('month', [p_Close]), 3) + \" \" + STR(YEAR([p_Close]))")
add("Prior Month", "string", "row", "DATENAME('month', [Prior Close])")
add("Prior Short", "string", "row", "LEFT(DATENAME('month', [Prior Close]), 3)")
add("In Function", "boolean", "row", '[p_Functions] = "" OR CONTAINS([p_Functions], "|" + [function_name] + "|")')
add("In Department", "boolean", "row", '[p_Departments] = "" OR CONTAINS([p_Departments], "|" + [department_name] + "|")')
add("In Country", "boolean", "row", '[p_Countries] = "" OR CONTAINS([p_Countries], "|" + [country_name] + "|")')
add("In Scope", "boolean", "row", "[In Function] AND [In Department] AND [In Country]")
add("Scope Is All", "boolean", "row", '[p_Functions] = "" AND [p_Departments] = "" AND [p_Countries] = ""')
add("Is Gap", "boolean", "row", '[row_type] = "Gap"')
add("Is Pop", "boolean", "row", '[row_type] = "Population"')
add("Is Ticket", "boolean", "row", '[row_type] = "Ticket"')
add("Gap Now", "boolean", "row", "[Is Gap] AND [Is Selected Close] AND [In Scope]")
add("Pop Now", "boolean", "row", "[Is Pop] AND [Is Selected Close] AND [In Scope]")
add("Pop Prior", "boolean", "row", "[Is Pop] AND [Is Prior Close] AND [In Scope]")
add("Ticket Now", "boolean", "row", "[Is Ticket] AND [Is Selected Close] AND [In Scope]")
add("zzTrue", "boolean", "row", "TRUE")
add("zzFalse", "boolean", "row", "FALSE")
add("Close Panel", "boolean", "row", "FALSE")

# ---------- 7.2 Scope words
for nm, p in (("Function", "[p_Functions]"), ("Department", "[p_Departments]"), ("Country", "[p_Countries]")):
    add(f"{nm} Count", "integer", "row", f'IF {p} = "" THEN 0 ELSE LEN({p}) - LEN(REPLACE({p}, "|", "")) - 1 END')
add("Function Field Text", "string", "row", field_text("[Function Count]", "[p_Functions]", False))
add("Department Field Text", "string", "row", field_text("[Department Count]", "[p_Departments]", True))
add("Country Field Text", "string", "row", field_text("[Country Count]", "[p_Countries]", True))
add("Scope Text", "string", "row", '''IF [Scope Is All] THEN ""
ELSE " · " + (IF [Function Count] = 0 THEN "" ELSEIF [Function Count] = 1 THEN [Function Field Text] ELSE STR([Function Count]) + " functions" END)
   + (IF [Department Count] = 0 THEN "" ELSE (IF [Function Count] > 0 THEN ", " ELSE "" END)
        + (IF [Department Count] = 1 THEN [Department Field Text] ELSE STR([Department Count]) + " departments" END) END)
   + (IF [Country Count] = 0 THEN "" ELSE (IF [Function Count] + [Department Count] > 0 THEN ", " ELSE "" END)
        + (IF [Country Count] = 1 THEN [Country Field Text] ELSE STR([Country Count]) + " countries" END) END)
END''')

# ---------- 7.3 Toggles
add("Function Toggle", "string", "row", toggle("[p_Functions]", "[function_name]"))
add("Department Toggle", "string", "row", toggle("[p_Departments]", "[department_name]"))
add("Country Toggle", "string", "row", toggle("[p_Countries]", "[country_name]"))
add("Function Is On", "boolean", "row", 'CONTAINS([p_Functions], "|" + [function_name] + "|")')
add("Department Is On", "boolean", "row", 'CONTAINS([p_Departments], "|" + [department_name] + "|")')
add("Country Is On", "boolean", "row", 'CONTAINS([p_Countries], "|" + [country_name] + "|")')
add("Dept In Functions", "boolean", "row", '[p_Functions] = "" OR CONTAINS([p_Functions], "|" + [function_name] + "|")')
add("Function State", "string", "row", 'IF [Function Is On] THEN "on" ELSE "off" END')
add("Department State", "string", "row", 'IF [Department Is On] THEN "on" ELSEIF [Dept In Functions] THEN "off" ELSE "dim" END')
add("Country State", "string", "row", 'IF [Country Is On] THEN "on" ELSE "off" END')
add("Function Tick Shape", "string", "row", 'IF [Function Is On] THEN "d4_tick_on" ELSE "d4_tick_off" END')
add("Department Tick Shape", "string", "row", 'IF [Department Is On] THEN "d4_tick_on" ELSEIF [Dept In Functions] THEN "d4_tick_off" ELSE "d4_tick_dim" END')
add("Country Tick Shape", "string", "row", 'IF [Country Is On] THEN "d4_tick_on" ELSE "d4_tick_off" END')
add("Empty Text", "string", "row", '""')
add("Toggle Close Panel", "boolean", "row", "NOT [p_CloseOpen]")
add("Toggle Function Panel", "boolean", "row", "NOT [p_FunctionOpen]")
add("Toggle Department Panel", "boolean", "row", "NOT [p_DepartmentOpen]")
add("Toggle Country Panel", "boolean", "row", "NOT [p_CountryOpen]")
add("Toggle Info", "boolean", "row", "NOT [p_InfoOpen]")

# ---------- 7.4 KPI numbers
def ksum(col, flag="Pop Now"):
    return f"SUM(IF [{flag}] THEN [{col}] END)"
add("K Working", "integer", "agg", ksum("contractors_working"))
add("K Keystone", "integer", "agg", ksum("contractors_working_keystone"))
add("K BW Only", "integer", "agg", ksum("working_bridgeway_only"))
add("K KS Only", "integer", "agg", ksum("working_keystone_only"))
add("K Net", "integer", "agg", "[K Working] - [K Keystone]")
add("K With Gap", "integer", "agg", ksum("contractors_with_gap"))
add("K Rate", "real", "agg", "IF ZN([K Working]) = 0 THEN NULL ELSE [K With Gap] / [K Working] END")
add("K Rate Prior", "real", "agg", """IF ZN(SUM(IF [Pop Prior] THEN [contractors_working] END)) = 0 THEN NULL
ELSE SUM(IF [Pop Prior] THEN [contractors_with_gap] END) / SUM(IF [Pop Prior] THEN [contractors_working] END) END""")
add("K Target", "real", "agg", "MIN(IF [Is Pop] THEN [gap_rate_target] END)")
add("K Gaps", "integer", "agg", ksum("gaps_counted"))
add("K Clear Own", "integer", "agg", ksum("gaps_clear_on_own"))
add("K Carry", "integer", "agg", ksum("gaps_open_prior_close"))
add("K No Ticket", "integer", "agg", ksum("gaps_no_ticket"))
add("K Over 90", "integer", "agg", ksum("gaps_over_90_days"))
add("K Oldest", "integer", "agg", "MAX(IF [Gap Now] AND [is_counted] THEN [days_open] END)")
add("K Tickets", "integer", "agg", "SUM(IF [Ticket Now] THEN [tickets] END)")
for k in ("K Working", "K Keystone", "K With Gap", "K Gaps", "K Carry", "K No Ticket", "K Over 90", "K Oldest", "K BW Only", "K KS Only"):
    add(f"{k} Str", "string", "agg", comma(f"[{k}]"))
add("K Rate Str", "string", "agg", rate("[K Rate]"))
add("K Rate Prior Str", "string", "agg", rate("[K Rate Prior]"))
add("K Carry Pct Str", "string", "agg", 'IF ZN([K Gaps]) = 0 THEN "N/A" ELSE STR(INT(ROUND([K Carry] / [K Gaps] * 100, 0))) + "%" END')
add("K No Ticket Pct Str", "string", "agg", 'IF ZN([K Gaps]) = 0 THEN "N/A" ELSE STR(INT(ROUND([K No Ticket] / [K Gaps] * 100, 0))) + "%" END')
add("K Net Str", "string", "agg", '(IF [K Net] > 0 THEN "+" ELSEIF [K Net] < 0 THEN "−" ELSE "" END) + STR(ABS(INT([K Net])))')
add("K Points Str", "string", "agg", '''IF ISNULL([K Rate]) THEN "" ELSE
  STR(DIV(INT(ROUND(ABS([K Rate] - [K Target]) * 10000, 0)), 100)) + "." + RIGHT("0" + STR(INT(ROUND(ABS([K Rate] - [K Target]) * 10000, 0)) % 100), 2)
  + (IF ROUND([K Rate] - [K Target], 4) > 0 THEN " pts above" ELSEIF ROUND([K Rate] - [K Target], 4) < 0 THEN " pts below" ELSE " pts: on" END) END''')
add("K Target Str", "string", "agg", 'STR(INT(ROUND([K Target] * 100, 0))) + "%"')

# ---------- 7.5 KPI card texts and hovers
add("KPI 1 Title", "string", "row", '"Working in Bridgeway"')
add("KPI 1 Value", "string", "agg", "[K Working Str]")
add("KPI 1 Unit", "string", "row", '"contractors"')
add("KPI 1 Note", "string", "agg", '"Keystone shows " + [K Keystone Str] + " · net " + [K Net Str]')
add("KPI 2 Title", "string", "agg", '"Gap rate at the close · target " + [K Target Str]')
add("KPI 2 Value", "string", "agg", "[K Rate Str]")
add("KPI 2 Known", "string", "agg", 'IF [K Rate] > [K Target] THEN "Known risk" END')
add("KPI 2 Low", "string", "agg", 'IF [K Rate] <= [K Target] THEN "Low risk" END')
add("KPI 2 Note", "string", "agg", '[K With Gap Str] + " with a gap · " + (IF [Has Prior] THEN [Prior Short] + " " + [K Rate Prior Str] ELSE "first close in the data" END)')
add("KPI 3 Title", "string", "agg", 'IF [Has Prior] THEN "Still open from the " + [Prior Month] + " close" ELSE "Still open from the prior close" END')
add("KPI 3 Value", "string", "agg", 'IF [Has Prior] THEN [K Carry Str] ELSE "N/A" END')
add("KPI 3 Unit", "string", "agg", '"of " + [K Gaps Str] + " gaps"')
add("KPI 3 Note", "string", "agg", 'IF [Has Prior] THEN [K Carry Pct Str] + " open since the " + [Prior Month] + " close" ELSE "No prior close in the data" END')
add("KPI 4 Title", "string", "row", '"No linked ticket"')
add("KPI 4 Value", "string", "agg", "[K No Ticket Str]")
add("KPI 4 Unit", "string", "agg", '[K No Ticket Pct Str] + " of the gaps"')
add("KPI 4 Note", "string", "row", '"No Helix ticket linked to the gap"')
add("KPI 5 Title", "string", "row", '"Open over 90 days"')
add("KPI 5 Value", "string", "agg", "[K Over 90 Str]")
add("KPI 5 Unit", "string", "agg", '"of " + [K Gaps Str] + " gaps"')
add("KPI 5 Note", "string", "agg", '"Oldest gap " + [K Oldest Str] + " days"')
add("KPI 1 Tip", "string", "agg", '[K BW Only Str] + " working in Bridgeway but not active in Keystone, " + [K KS Only Str] + " the other way. Contractors, not gaps."')
add("KPI 2 Tip", "string", "agg", '''"Contractors with at least one gap in the rate, divided by contractors working in Bridgeway. " + [K Points Str]
+ " a provisional " + [K Target Str] + " target. The target flags risk; it does not certify the report."
+ (IF ZN([K Clear Own]) > 0 THEN " " + STR([K Clear Own]) + " gaps clear on their own by the next run and are left out." ELSE "" END)''')
add("KPI 3 Tip", "string", "row", '"A gap open at the " + [Prior Month] + " close and still open now, as one continuous episode. A flag that cleared and came back is a new gap."')
add("KPI 4 Tip", "string", "row", '"No Helix ticket carries an ID that links it to the gap. A ticket may exist without one: \'no linked ticket\' does not mean nobody is working on it."')
add("KPI 5 Tip", "string", "row", '"Days since the gap began, strictly over 90. Gap age, not ticket age: a gap can be older than its ticket."')
add("Hover Cell", "string", "row", '"."')
add("Rail One", "boolean", "row", "{ FIXED : MIN([cost_center_id]) } = [cost_center_id]")

# ---------- 7.6 Sankey
add("Sankey Gap Row", "boolean", "row", "[Gap Now]")
add("Sankey Gap", "integer", "row", "IIF([Sankey Gap Row], 1, 0)")
add("Anchor Key", "string", "row", 'STR([month_end_date]) + "|" + [ticket_number]')
add("Is Anchor", "boolean", "row", "[Is Ticket] AND [Anchor Key] = { FIXED [place] : MIN(IF [Is Ticket] THEN [Anchor Key] END) }")
add("Place Gaps", "integer", "row", "{ FIXED [place] : SUM([Sankey Gap]) }")
add("Sankey Anchor", "boolean", "row", "[Is Anchor] AND [Place Gaps] > 0")
add("Sankey Row", "boolean", "row", "[Sankey Gap Row] OR [Sankey Anchor]")
add("Sankey Weight", "real", "row", "IF [Sankey Anchor] THEN 0 ELSE [Sankey Gap] END")
add("Flag Gaps", "integer", "row", "{ FIXED [flag_label] : SUM([Sankey Gap]) }")
add("Flag Text", "string", "row", '[flag_name] + " (" + STR([Flag Gaps]) + ")"')
add("First Flag", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] THEN [flag_label] END) }")
add("First Flag Text", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] AND [flag_label] = [First Flag] THEN [Flag Text] END) }")
add("Flag Sort", "string", "row", "IF [Sankey Anchor] THEN [First Flag] ELSE [flag_label] END")
add("Risk Gaps", "integer", "row", "{ FIXED [risk] : SUM([Sankey Gap]) }")
add("Risk Text", "string", "row", '[risk] + " (" + STR([Risk Gaps]) + ")"')
add("First Risk", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] THEN [risk] END) }")
add("First Risk Text", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] AND [risk] = [First Risk] THEN [Risk Text] END) }")
# the three levels: existing spike calcs renamed (see EXISTING)

# ---------- 7.7 Sankey tooltip (new ones; the existing Tip calcs are rewritten in EXISTING)
add("Tip Flags", "integer", "agg", "COUNTD(IF [Sankey Gap Row] THEN [flag_label] END)")
add("Tip Risks", "integer", "agg", "COUNTD(IF [Sankey Gap Row] THEN [risk] END)")
add("Tip Places", "integer", "agg", "COUNTD(IF [Sankey Gap Row] THEN [place] END)")
add("Tip Ranked", "boolean", "agg", "[Tip Is Flag] AND [Scope Is All]")

# ---------- 7.8 Main card headline and subtitle
add("Total Gaps", "integer", "row", "{ FIXED : SUM([Sankey Gap]) }")
add("Top Place Gaps", "integer", "row", "{ FIXED : MAX(IF [Sankey Gap Row] THEN [Place Gaps] END) }")
add("Top Place", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] AND [Place Gaps] = [Top Place Gaps] THEN [place] END) }")
add("Top Flag Gaps", "integer", "row", "{ FIXED : MAX(IF [Sankey Gap Row] THEN [Flag Gaps] END) }")
add("Top Flag", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] AND [Flag Gaps] = [Top Flag Gaps] THEN [flag_name] END) }")
add("Top Flag Prior Rank", "integer", "row", "{ FIXED : MIN(IF [Sankey Gap Row] AND [flag_name] = [Top Flag] THEN [flag_rank_prior_close] END) }")
add("Move", "integer", "row", "ABS([flag_rank_year_ago] - [flag_rank])")
add("Max Move", "integer", "row", "{ FIXED : MAX(IF [Sankey Gap Row] THEN [Move] END) }")
add("Mover", "string", "row", "{ FIXED : MIN(IF [Sankey Gap Row] AND [Move] = [Max Move] THEN [flag_label] END) }")
ordinal = lambda r: f'STR({r}) + (CASE {r} WHEN 1 THEN "st" WHEN 2 THEN "nd" WHEN 3 THEN "rd" ELSE "th" END)'
add("Ordinal Now", "string", "row", ordinal("[flag_rank]"))
add("Ordinal YA", "string", "row", ordinal("[flag_rank_year_ago]"))
add("Mover Text", "string", "row", '''{ FIXED : MIN(IF [Sankey Gap Row] AND [flag_label] = [Mover] THEN
  [flag_name] + ": " + [Ordinal YA] + " a year ago (" + STR([flag_count_year_ago]) + "), "
  + [Ordinal Now] + " now (" + STR([Flag Gaps]) + ")" END) }''')
add("Clear Own Gaps", "integer", "row", "{ FIXED : SUM(IF [Sankey Gap Row] AND NOT [is_counted] THEN 1 ELSE 0 END) }")
add("Total Gaps Str", "string", "row", comma("[Total Gaps]"))
add("Top Place Gaps Str", "string", "row", comma("[Top Place Gaps]"))
add("Top Flag Gaps Str", "string", "row", comma("[Top Flag Gaps]"))
add("Main Title", "string", "row", '''IF ZN([Total Gaps]) = 0 THEN "No gaps in this selection"
ELSE [Top Place] + " holds " + [Top Place Gaps Str] + " of " + [Total Gaps Str] + " gaps. Largest flag: " + [Top Flag] + " (" + [Top Flag Gaps Str] + ")" END''')
# aggregate version: every LOD wrapped in MIN() so it can use Has Prior (aggregate)
add("Main Subtitle", "string", "agg", '''(IF ZN(MIN([Total Gaps])) = 0 THEN "Choose another close or fewer groups"
ELSEIF NOT [Scope Is All] THEN "Ranks and year-ago comparisons cover all of Arcadia: choose All in the rail to see them"
ELSEIF NOT [Has Prior] THEN "First close in the data"
ELSE (IF MIN([Top Flag Prior Rank]) = 1 THEN "Same largest flag as " ELSE "New largest flag since " END) + [Prior Month] + ". "
   + (IF ZN(MIN([Max Move])) = 0 THEN "No flag changed rank since a year ago" ELSE MIN([Mover Text]) END)
END)
+ (IF MIN([Clear Own Gaps]) > 0 THEN " · " + STR(MIN([Clear Own Gaps])) + " clear on their own by the next run" ELSE "" END)''')

# ---------- 10 Rail controls
add("Close Field Text", "string", "row", 'IF [Is Current] THEN "Current · " + [Close Short] ELSE [Close Short] + " close" END')
add("Close Day Text", "string", "row", day_text("[p_Close]"))
add("Run Day Text", "string", "row", day_text("DATEADD('day', 1, [p_Close])"))
add("Rail As Of Line 1", "string", "row", 'IF [Is Current] THEN "Data as of " + [Close Day Text] ELSE "Replaying the " + [Close Short] + " close" END')
add("Rail As Of Line 2", "string", "row", '"The 00:00 GMT run on " + [Run Day Text]')
add("Info Shape", "string", "row", 'IF [p_InfoOpen] THEN "d2_info_close" ELSE "d2_info_open" END')
add("Default Close", "date", "row", "[Latest Close]")
add("Toggle Option", "string", "row", 'IF [place] = "Bridgeway" THEN "Overview" ELSEIF [place] = "Keystone" THEN "Gap list" END')
add("Toggle Row", "boolean", "row", "[Is Gap] AND [month_end_date] = [Latest Close] AND NOT ISNULL([Toggle Option])")
add("Show Pick", "boolean", "row", '[Toggle Option] = "Gap list"')
add("Show Shape", "string", "row", '''IF [Toggle Option] = "Overview" THEN (IF [p_ShowList] THEN "d4_show_overview_off" ELSE "d4_show_overview_on" END)
ELSE (IF [p_ShowList] THEN "d4_show_gaplist_on" ELSE "d4_show_gaplist_off" END) END''')

# ---------- 11 Popovers
add("Close Slot", "integer", "row", "2 * (2026 - YEAR([month_end_date])) + 1")
add("Close Col", "integer", "row", "2 * MONTH([month_end_date]) - 1")
add("Close Cell", "string", "row", "LEFT(DATENAME('month', [month_end_date]), 3)")
add("Close State", "string", "row", 'IF [month_end_date] = [p_Close] THEN "current" ELSE "on" END')
add("Close Pick", "date", "row", "[month_end_date]")
add("Close Year Label", "string", "row", "STR(YEAR([month_end_date]))")
add("Close Grid Row", "boolean", "row", "[Is Pop] AND { FIXED [month_end_date] : MIN([cost_center_id]) } = [cost_center_id]")
add("Function List Row", "boolean", "row", "[Is Pop] AND { FIXED [function_name] : MIN([cost_center_id]) } = [cost_center_id]")
add("Department List Row", "boolean", "row", "[Is Pop] AND { FIXED [department_name] : MIN([cost_center_id]) } = [cost_center_id]")
add("Country List Row", "boolean", "row", "[Is Pop] AND { FIXED [country_name] : MIN([cost_center_id]) } = [cost_center_id]")
add("Function Slot", "integer", "tc", "2 * (INDEX() - 1) + 1")
add("Tick X", "real", "agg", "MIN(0.6)")
add("Pick Rows", "integer", "tc", "INT((SIZE() + 2) / 3)")
add("Pick Col", "integer", "tc", "INT((INDEX() - 1) / [Pick Rows])")
add("Pick Row", "integer", "tc", "2 * ((INDEX() - 1) - [Pick Col] * [Pick Rows]) + 1")

# ---------- 13 Gap list
add("Gap List Row", "boolean", "row", "[Gap Now]")
add("WHERE ALIGNED", "string", "row", '[place] + CHAR(10) + STR([Place Gaps]) + " gaps"')
add("WHAT DIFFERS", "string", "row", "[flag_name]")
add("CONTRACTOR", "string", "row", '[contractor_name] + " · " + [bw_worker_id]')
add("KEYSTONE SHOWS", "string", "row", "[keystone_shows]")
add("BRIDGEWAY HAS", "string", "row", "[bridgeway_has]")
add("TICKET", "string", "row", 'IFNULL([ticket_number], "No ticket")')
add("DAYS OPEN", "integer", "row", "[days_open]")
add("Days Band", "string", "row", 'IF [days_open] > 90 THEN "over 90" ELSE "90 or less" END')
add("Gap List Title", "string", "row", '''IF ZN([Total Gaps]) = 0 THEN "No gaps in this selection"
ELSE [Total Gaps Str] + " gaps at the " + [Close Month] + " close, by where they are aligned" END''')
add("Gap List Subtitle", "string", "row", '"Oldest first. Hover a row for the evidence, the next step and the ticket. Click a node in the Overview to narrow the list."')
add("Show Overview", "boolean", "row", "NOT [p_ShowList]")
add("Show List On Click", "boolean", "row", "TRUE")

# ---------- 14 Timeline
add("Timeline Row", "boolean", "row", """[Is Pop] AND [In Scope] AND DATEDIFF('month', [month_end_date], [p_Close]) >= 0
AND DATEDIFF('month', [month_end_date], [p_Close]) <= 12""")
add("TL Rate", "real", "agg", "IF SUM([contractors_working]) = 0 THEN NULL ELSE SUM([contractors_with_gap]) / SUM([contractors_working]) END")
add("TL Rate Str", "string", "agg", rate("[TL Rate]"))
add("TL Is Selected", "boolean", "agg", "MIN([month_end_date]) = [p_Close]")
add("TL Label", "string", "agg", "IF [TL Is Selected] THEN [TL Rate Str] END")
add("TL Target", "real", "agg", "MIN([gap_rate_target])")
add("TL Dot", "string", "agg", 'IF [TL Is Selected] THEN (IF [TL Rate] > [TL Target] THEN "selected above" ELSE "selected below" END) ELSE "other" END')
add("Timeline Subtitle", "string", "row", '"Contractors with a gap divided by contractors working in Bridgeway · last 13 closes" + [Scope Text]')

# ---------- 15 Ticket card
add("Ticket Card Row", "boolean", "row", "[Ticket Now]")
add("Ticket Row Y", "real", "row", "3.5 - [place_order]")
add("Band X", "real", "row", "[age_band_order] - 0.5")
add("Place Open", "integer", "row", "{ FIXED [place] : SUM(IF [Ticket Card Row] THEN [tickets] END) }")
add("Band Open", "integer", "row", "{ FIXED [age_band] : SUM(IF [Ticket Card Row] THEN [tickets] END) }")
add("Place Sub", "string", "row", 'CASE [place] WHEN "Bridgeway" THEN "vendor system" WHEN "Keystone" THEN "HR system" ELSE "integration" END')
add("Tickets Subtitle", "string", "row", '"One dot per Helix ticket open at the close" + [Scope Text]')

# ---------- 16 Title and load note
add("Page Subtitle", "string", "row", '''"Where Bridgeway and Keystone " + (IF [Is Current] THEN "disagree" ELSE "disagreed" END)
+ " at the " + [Close Name] + " close, and where each gap is aligned" + [Scope Text]''')
add("Load Note", "string", "agg", "MIN(IF [Is Pop] AND [Is Selected Close] THEN [load_note] END)")
add("Show Load Note", "boolean", "row", '{ FIXED : MAX(IF [Is Pop] AND [Is Selected Close] AND CONTAINS([load_note], "failed") THEN 1 ELSE 0 END) } = 1')

# ---------- Existing spike calcs: (current caption) -> (new caption, formula). Internal names stay,
# so the Sankey sheet keeps its pills.
EXISTING = {
    "Flag Label (n)": ("What differs", "IF [Sankey Anchor] THEN [First Flag Text] ELSE [Flag Text] END"),
    "Risk Label (n)": ("What it puts at risk", "IF [Sankey Anchor] THEN [First Risk Text] ELSE [Risk Text] END"),
    "Place Label (n)": ("Where it is aligned", '[place_label] + " (" + STR([Place Gaps]) + ")"'),
    "Tip Gaps": ("Tip Gaps", "SUM([Sankey Gap])"),
    "Tip Share": ("Tip Share", "SUM([Sankey Gap]) / MIN({ FIXED : SUM([Sankey Gap]) })"),
    "Tip Is Flag": ("Tip Is Flag", "[Tip Flags] = 1"),
    "Tip Title": ("Tip Title", '''IF [Tip Is Flag] THEN MIN(IF [Sankey Gap Row] THEN [flag_name] END)
ELSEIF [Tip Risks] = 1 AND [Tip Places] = 1
  THEN MIN(IF [Sankey Gap Row] THEN [risk] END) + ", aligned in " + MIN(IF [Sankey Gap Row] THEN [place] END)
ELSEIF [Tip Risks] = 1 THEN MIN(IF [Sankey Gap Row] THEN [risk] END)
ELSE MIN(IF [Sankey Gap Row] THEN [place_label] END) END'''),
    "Tip Rank": ("Tip Rank", 'IF [Tip Ranked] THEN "Rank " + STR(MIN([flag_rank])) + " of 9" END'),
    "Tip Rank Worse": ("Tip Rank Worse", '''IF [Tip Ranked] AND MIN([flag_rank]) < MIN([flag_rank_prior_close])
THEN "up from " + STR(MIN([flag_rank_prior_close])) + " at the prior close (" + STR(MIN([flag_count_prior_close])) + ")" END'''),
    "Tip Rank Better": ("Tip Rank Better", '''IF [Tip Ranked] AND MIN([flag_rank]) > MIN([flag_rank_prior_close])
THEN "down from " + STR(MIN([flag_rank_prior_close])) + " at the prior close (" + STR(MIN([flag_count_prior_close])) + ")" END'''),
    "Tip Rank Same": ("Tip Rank Same", '''IF [Tip Ranked] AND MIN([flag_rank]) = MIN([flag_rank_prior_close])
THEN "same rank as the prior close (" + STR(MIN([flag_count_prior_close])) + ")" END'''),
    "Tip Year Ago": ("Tip Year Ago", '''IF [Tip Ranked] AND NOT ISNULL(MIN([flag_rank_year_ago]))
THEN "A year ago: " + STR(MIN([flag_count_year_ago])) + " gaps, rank " + STR(MIN([flag_rank_year_ago])) END'''),
    "Tip Puts At Risk": ("Tip Puts At Risk", 'IF [Tip Is Flag] THEN "Puts at risk: " + MIN(IF [Sankey Gap Row] THEN [risk] END) END'),
    "Tip Bridgeway": ("Tip Bridgeway", tip_place("Bridgeway", "Bridgeway (vendor system)")),
    "Tip Keystone": ("Tip Keystone", tip_place("Keystone", "Keystone (HR system)")),
    "Tip System Feed": ("Tip System Feed", tip_place("System feed", "System feed (integration)")),
    "Tip From": ("Tip From", 'IF NOT [Tip Is Flag] THEN "From " + STR([Tip Flags]) + " flags" END'),
    "Tip Feed Causes": ("Tip Feed Causes", '''IF [Tip Places] = 1 AND MIN(IF [Sankey Gap Row] THEN [place] END) = "System feed"
THEN STR(SUM(IF [Sankey Gap Row] AND [timing_class] = "Feed event failed" THEN 1 ELSE 0 END)) + " failed feed events, "
   + STR(SUM(IF [Sankey Gap Row] AND [timing_class] = "Load failed" THEN 1 ELSE 0 END)) + " failed loads, "
   + STR(SUM(IF [Sankey Gap Row] AND [timing_class] = "Feed stuck" THEN 1 ELSE 0 END)) + " stuck" END'''),
    "Tip No Ticket": ("Tip No Ticket", '''IF SUM(IF [Sankey Gap Row] AND NOT [has_ticket] THEN 1 END) > 0
THEN STR(SUM(IF [Sankey Gap Row] AND NOT [has_ticket] THEN 1 END)) + " with no ticket" END'''),
    "Tip Over 90": ("Tip Over 90", '''IF SUM(IF [Sankey Gap Row] AND [days_open] > 90 THEN 1 END) > 0
THEN STR(SUM(IF [Sankey Gap Row] AND [days_open] > 90 THEN 1 END)) + " open more than 90 days" END'''),
    "Tip Next Step": ("Tip Next Step", '''IF [Tip Is Flag] THEN "Next step: " + MIN(IF [Sankey Gap Row] THEN [next_step] END)
ELSEIF [Tip Places] = 1 AND MIN(IF [Sankey Gap Row] THEN [place] END) = "System feed" THEN "Worked by Data Engineering"
ELSE "Next steps differ by gap: see the gap list" END'''),
}
