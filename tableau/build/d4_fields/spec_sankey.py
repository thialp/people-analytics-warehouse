# Native Sankey, v2 (build doc section 9N): the extension's look, built natively: parameters and Sk calcs, by caption.
# Same format as spec.py: (caption, datatype, kind, formula); kind 'row' | 'agg'.
# Reads existing fields (Total Gaps, Flag Gaps, Risk Gaps, Place Gaps, Sankey Gap Row, Sankey Gap,
# Scope Is All, Place Sub, ...) but never changes them, so the extension Sankey (version A) stays as it is.
# Every position is a FIXED LOD over the Gap rows of the selection (Sankey Gap = Gap Now), evaluated
# on the Sankey scaffold rows (row_type 'Sankey') that carry the flag, risk and place keys.

PARAMS = [
    ("p_SkFlag", "string", "any", '""'),     # a click on the native Sankey: flag_code, risk, place
    ("p_SkRisk", "string", "any", '""'),
    ("p_SkPlace", "string", "any", '""'),
]

C = []
def add(cap, dt, kind, f):
    C.append((cap, dt, kind, f))

# ---------- constants (v2: the Sankey is one 726 x 540 sheet; tune here, everything follows)
for cap, v in (("Sk W", "726"), ("Sk H", "540"), ("Sk Top", "36"), ("Sk Bottom", "2"), ("Sk Node W", "156"),
               ("Sk Pad", "6"), ("Sk X1", "0"), ("Sk X3", "570"), ("Sk Points", "25"),
               ("Sk Min H", "14"), ("Sk Max Scale", "12"), ("Sk Count Min H", "28")):
    add(cap, "integer", "row", v)
add("Sk X2", "real", "row", "([Sk X1] + [Sk Node W] + [Sk X3]) / 2 - [Sk Node W] / 2")
add("Sk Label DY", "real", "row", "0")   # nudge (px, + is down) if the box labels sit high or low

# Revision 8: every LOD reads raw rows only (one level deep). Tableau turns each LOD into a subquery and nests
# the LODs it references inside it; revision 7 nested them 12 deep and the sheet's query never finished.
# Positions are now closed-form arithmetic on one-level LODs: a box is Sk Min H plus its gaps times one scale,
# so no fitting loop is needed and every column fits by construction.
# ---------- the rows
add("Sk Row", "boolean", "row", '[row_type] = "Sankey"')
add("Sk Fi", "integer", "row", "INT(MID([flag_code], 2, 2))")

# ---------- node counts of the selection (9 flags, 5 risks, 3 places: the taxonomy is fixed)
for k in range(1, 10):
    add(f"Sk F{k}", "integer", "row", f'{{ FIXED : SUM(IF [Sankey Gap Row] AND [flag_code] = "F0{k}" THEN 1 ELSE 0 END) }}')
for k in range(1, 6):
    add(f"Sk R{k}", "integer", "row", f"{{ FIXED : SUM(IF [Sankey Gap Row] AND [risk_order] = {k} THEN 1 ELSE 0 END) }}")
for k in range(1, 4):
    add(f"Sk P{k}", "integer", "row", f"{{ FIXED : SUM(IF [Sankey Gap Row] AND [place_order] = {k} THEN 1 ELSE 0 END) }}")
COLS = (("F", 9), ("R", 5), ("P", 3))
ne = lambda p, n: " + ".join(f"IIF([Sk {p}{k}] > 0, 1, 0)" for k in range(1, n + 1))
add("Sk NF", "integer", "row", "{ FIXED : COUNTD(IF [Sankey Gap Row] THEN [flag_code] END) }")
add("Sk NR", "integer", "row", "{ FIXED : COUNTD(IF [Sankey Gap Row] THEN [risk] END) }")
add("Sk NP", "integer", "row", "{ FIXED : COUNTD(IF [Sankey Gap Row] THEN [place] END) }")
add("Sk Avail", "real", "row", "[Sk H] - [Sk Top] - [Sk Bottom]")

# ---------- scale: a box is Sk Min H + its gaps x Sk Scale. Per column, n boxes fit when
# n x Sk Min H + Sk Pad x (n - 1) + Total Gaps x scale = Sk Avail, so the column with the most boxes sets the scale.
# One LOD, aggregates of raw rows only (the constants are written in as numbers, not as fields).
_K = dict(H=540, Top=36, Bottom=2, Pad=6, MinH=14)
_AV = _K["H"] - _K["Top"] - _K["Bottom"]
_n = {c: f"COUNTD(IF [Sankey Gap Row] THEN [{k}] END)" for c, k in (("F", "flag_code"), ("R", "risk"), ("P", "place"))}
_maxn = f"IF {_n['F']} >= {_n['R']} AND {_n['F']} >= {_n['P']} THEN {_n['F']} ELSEIF {_n['R']} >= {_n['P']} THEN {_n['R']} ELSE {_n['P']} END"
add("Sk Fit Scale", "real", "row", "{ FIXED : IF SUM([Sankey Gap]) > 0\n"
    f"  THEN ({_AV + _K['Pad']} - {_K['MinH'] + _K['Pad']} * ({_maxn})) / SUM([Sankey Gap]) END }}")
add("Sk Capped", "boolean", "row", "[Sk Fit Scale] > [Sk Max Scale]")
add("Sk Scale", "real", "row", "IF [Sk Fit Scale] > [Sk Max Scale] THEN [Sk Max Scale] ELSE [Sk Fit Scale] END")

# ---------- each column's space between boxes (all the room left over, or Sk Pad when a small selection is capped)
for col in ("F", "R", "P"):
    add(f"Sk Gap {col}", "real", "row",
        f"IF [Sk Capped] THEN [Sk Pad] ELSEIF [Sk N{col}] > 1\n"
        f"THEN ([Sk Avail] - [Sk Min H] * [Sk N{col}] - [Sk Scale] * [Total Gaps]) / ([Sk N{col}] - 1) ELSE 0 END")


def before(term, n, idx):
    parts = ["WHEN 1 THEN 0"] + [f"WHEN {k} THEN " + " + ".join(term(j) for j in range(1, k)) for k in range(2, n + 1)]
    return f"CASE {idx}\n  " + "\n  ".join(parts) + "\nEND"


IDX = {"F": "[Sk Fi]", "R": "[risk_order]", "P": "[place_order]"}
for col, n in COLS:
    add(f"Sk {col} Before", "integer", "row", before(lambda j, c=col: f"[Sk {c}{j}]", n, IDX[col]))          # gaps before
    add(f"Sk {col} NE Before", "integer", "row", before(lambda j, c=col: f"IIF([Sk {c}{j}] > 0, 1, 0)", n, IDX[col]))  # boxes before
for col, gaps in (("F", "Flag Gaps"), ("R", "Risk Gaps"), ("P", "Place Gaps")):
    add(f"Sk {col}H This", "real", "row", f"IF [{gaps}] > 0 THEN [Sk Min H] + [{gaps}] * [Sk Scale] ELSE 0 END")
for col, nm in (("F", "Flag"), ("R", "Risk"), ("P", "Place")):
    add(f"Sk Y {nm}", "real", "row", f"[Sk Top] + ([Sk Min H] + [Sk Gap {col}]) * [Sk {col} NE Before] + [Sk Scale] * [Sk {col} Before]")
# one gap's height inside each box (the Sk Min H part is shared out too, so ribbons fill the box)
add("Sk F Unit", "real", "row", "IF [Flag Gaps] > 0 THEN [Sk FH This] / [Flag Gaps] END")
add("Sk R Unit", "real", "row", "IF [Risk Gaps] > 0 THEN [Sk RH This] / [Risk Gaps] END")
add("Sk P Unit", "real", "row", "IF [Place Gaps] > 0 THEN [Sk PH This] / [Place Gaps] END")

# ---------- ribbons: both links are one band per flag x place, so a flag's whole path can light up
add("Sk FP", "integer", "row", "{ FIXED [flag_label], [place] : SUM([Sankey Gap]) }")
for k in (1, 2):
    add(f"Sk F PB{k}", "integer", "row", f"{{ FIXED [flag_label] : SUM(IF [Sankey Gap Row] AND [place_order] <= {k} THEN 1 ELSE 0 END) }}")
    add(f"Sk R PB{k}", "integer", "row", f"{{ FIXED [risk] : SUM(IF [Sankey Gap Row] AND [place_order] <= {k} THEN 1 ELSE 0 END) }}")
for k in (1, 2, 3, 4):
    add(f"Sk P RB{k}", "integer", "row", f"{{ FIXED [place] : SUM(IF [Sankey Gap Row] AND [risk_order] <= {k} THEN 1 ELSE 0 END) }}")
for k in range(1, 9):
    add(f"Sk P FB{k}", "integer", "row", f"{{ FIXED [place] : SUM(IF [Sankey Gap Row] AND [flag_code] <= \"F0{k}\" THEN 1 ELSE 0 END) }}")
add("Sk FP Before", "integer", "row", "CASE [place_order] WHEN 1 THEN 0 WHEN 2 THEN [Sk F PB1] ELSE [Sk F PB2] END")
add("Sk RP Before", "integer", "row", "CASE [place_order] WHEN 1 THEN 0 WHEN 2 THEN [Sk R PB1] ELSE [Sk R PB2] END")
add("Sk PR Before", "integer", "row",
    "CASE [risk_order] WHEN 1 THEN 0 WHEN 2 THEN [Sk P RB1] WHEN 3 THEN [Sk P RB2] WHEN 4 THEN [Sk P RB3] ELSE [Sk P RB4] END")
add("Sk PF Before", "integer", "row",
    "CASE [Sk Fi] WHEN 1 THEN 0 " + " ".join(f"WHEN {k} THEN [Sk P FB{k - 1}]" for k in range(2, 10)) + " END")
add("Sk Link N", "integer", "row", "[Sk FP]")
# level 1, flag to risk: leaves the flag box by place; enters the risk box by flag, then place
# level 2, risk to place: leaves the risk box by place, then flag; enters the place box by risk, then flag
add("Sk Link Y0", "real", "row", """IF [sk_level] = 1 THEN [Sk Y Flag] + [Sk FP Before] * [Sk F Unit]
ELSE [Sk Y Risk] + ([Sk RP Before] + [Sk PF Before] - [Sk PR Before]) * [Sk R Unit] END""")
add("Sk Link H0", "real", "row", "[Sk FP] * IIF([sk_level] = 1, [Sk F Unit], [Sk R Unit])")
add("Sk Link Y1", "real", "row", """IF [sk_level] = 1 THEN [Sk Y Risk] + ([Sk F Before] - [Sk R Before] + [Sk FP Before]) * [Sk R Unit]
ELSE [Sk Y Place] + [Sk PF Before] * [Sk P Unit] END""")
add("Sk Link H1", "real", "row", "[Sk FP] * IIF([sk_level] = 1, [Sk R Unit], [Sk P Unit])")
add("Sk Link X0", "real", "row", "IF [sk_level] = 1 THEN [Sk X1] + [Sk Node W] ELSE [Sk X2] + [Sk Node W] END")
add("Sk Link X1", "real", "row", "IF [sk_level] = 1 THEN [Sk X2] ELSE [Sk X3] END")
add("Sk Is Bottom", "boolean", "row", "[sk_point] >= [Sk Points]")
add("Sk T Along", "real", "row",
    "IF [sk_point] < [Sk Points] THEN FLOAT([sk_point]) / ([Sk Points] - 1)\nELSE FLOAT(2 * [Sk Points] - 1 - [sk_point]) / ([Sk Points] - 1) END")
add("Sk Ease", "real", "row", "[Sk T Along] * [Sk T Along] * (3 - 2 * [Sk T Along])")

# ---------- boxes
add("Sk Node X", "real", "row", "CASE [sk_level] WHEN 1 THEN [Sk X1] WHEN 2 THEN [Sk X2] ELSE [Sk X3] END")
add("Sk Node Y", "real", "row", "CASE [sk_level] WHEN 1 THEN [Sk Y Flag] WHEN 2 THEN [Sk Y Risk] ELSE [Sk Y Place] END")
add("Sk Node N", "integer", "row", "CASE [sk_level] WHEN 1 THEN [Flag Gaps] WHEN 2 THEN [Risk Gaps] ELSE [Place Gaps] END")
add("Sk Node H", "real", "row", "CASE [sk_level] WHEN 1 THEN [Sk FH This] WHEN 2 THEN [Sk RH This] ELSE [Sk PH This] END")
# lines of text a box can hold: places 3 (name, system, count and share), flags and risks 2 (name, count and share)
add("Sk Lines", "integer", "row", "IF [sk_level] = 3 THEN IIF([Sk Node H] >= 40, 3, 1) ELSE IIF([Sk Node H] >= [Sk Count Min H], 2, 1) END")
add("Sk Show Count", "boolean", "row", "[Sk Lines] >= 2")

# ---------- the two coordinates every mark uses
add("Sk X", "real", "row", """CASE [sk_part]
  WHEN "Link"   THEN [Sk Link X0] + ([Sk Link X1] - [Sk Link X0]) * [Sk T Along]
  WHEN "Node"   THEN [Sk Node X] + IIF([sk_point] = 1 OR [sk_point] = 2, [Sk Node W], 0)
  ELSE [Sk Node X] + [Sk Node W] / 2
END""")
add("Sk Y", "real", "row", """CASE [sk_part]
  WHEN "Link"   THEN IF [Sk Is Bottom] THEN [Sk Link Y0] + [Sk Link H0] + ([Sk Link Y1] + [Sk Link H1] - [Sk Link Y0] - [Sk Link H0]) * [Sk Ease]
                     ELSE [Sk Link Y0] + ([Sk Link Y1] - [Sk Link Y0]) * [Sk Ease] END
  WHEN "Node"   THEN [Sk Node Y] + IIF([sk_point] >= 2, [Sk Node H], 0)
  WHEN "Label"  THEN [Sk Node Y] + [Sk Node H] / 2 + [Sk Label DY]
                     + CASE [Sk Lines] WHEN 1 THEN 0 WHEN 2 THEN IIF([sk_point] = 0, -6, 7) ELSE IIF([sk_point] = 0, -12, 0) END
  WHEN "Header" THEN 20
END""")
add("Sk Y Shape", "real", "row", 'IF [sk_part] = "Link" OR [sk_part] = "Node" THEN [Sk Y] END')
# a place's third line rides on its box rows (the text layer averages the 4 corners to the box centre)
add("Sk Y Text", "real", "row", """IF [sk_part] = "Label" OR [sk_part] = "Header" THEN [Sk Y]
ELSEIF [sk_part] = "Node" AND [sk_level] = 3 AND [Sk Lines] = 3 THEN [Sk Node Y] + [Sk Node H] / 2 + 12 + [Sk Label DY] END""")

# ---------- what shows, in what order, in what colour
add("Sk N", "integer", "row", 'CASE [sk_part] WHEN "Link" THEN [Sk Link N] WHEN "Header" THEN 1 ELSE [Sk Node N] END')
add("Sk Show", "boolean", "row",
    '[Sk Row] AND [Sk N] > 0 AND NOT ([sk_part] = "Label" AND [sk_point] = 1 AND NOT [Sk Show Count])')
# one polygon per ribbon or box (sk_point is on Path, so it must not split the shape); a text mark per point
add("Sk Mark", "string", "row",
    '[sk_part] + "|" + STR([sk_level]) + "|" + IIF([sk_part] = "Link" OR [sk_part] = "Node", "", STR([sk_point]))'
    ' + "|" + IFNULL([flag_code], "") + "|" + IFNULL([risk], "") + "|" + IFNULL([place], "")')
add("Sk Draw", "real", "row", 'IF [sk_part] = "Link" THEN -[Sk Link N] ELSE 100000 END')
add("Sk Colour", "string", "row", """IF [sk_part] = "Link" THEN (IF [sk_level] = 1 THEN [flag_code] + " ribbon" ELSE "Risk ribbon" END)
ELSEIF [sk_level] = 1 THEN [flag_code]
ELSEIF [sk_level] = 2 THEN "Risk"
ELSE [place] END""")

# ---------- box labels: row 0 the name, row 1 the count (only when the box is tall enough); white on the slate risks
add("Sk Lbl Header", "string", "row",
    'IF [sk_part] = "Header" THEN CASE [sk_level] WHEN 1 THEN "What differs" WHEN 2 THEN "What it puts at risk" ELSE "Where it is aligned" END END')
add("Sk Pct Str", "string", "row", 'IF [Total Gaps] > 0 THEN STR(ROUND(100 * [Sk Node N] / [Total Gaps], 1)) + "%" END')
add("Sk Count Str", "string", "row", 'STR([Sk Node N]) + " · " + [Sk Pct Str]')
add("Sk Box Text", "string", "row", """IF [sk_part] = "Label" THEN
  IF [sk_point] = 0 THEN CASE [sk_level] WHEN 1 THEN [flag_short] WHEN 2 THEN [risk] ELSE [place] END
  ELSEIF [sk_level] = 3 THEN CASE [place] WHEN "Bridgeway" THEN "vendor system" WHEN "Keystone" THEN "HR system" ELSE "integration" END
  ELSE [Sk Count Str] END
ELSEIF [sk_part] = "Node" AND [sk_level] = 3 THEN [Sk Count Str]
END""")
add("Sk Lbl Dark", "string", "row", "IF [sk_level] <> 2 THEN [Sk Box Text] END")
add("Sk Lbl White", "string", "row", "IF [sk_level] = 2 THEN [Sk Box Text] END")

# ---------- tooltips (row level: every number is an LOD of the selection)
add("Sk Is Flag Node", "boolean", "row", '[sk_part] = "Node" AND [sk_level] = 1')
add("Sk Tip Title", "string", "row", """CASE [sk_part]
  WHEN "Link" THEN [flag_short] + ", aligned in " + [place]
  WHEN "Node" THEN CASE [sk_level] WHEN 1 THEN [flag_short] WHEN 2 THEN [risk] ELSE [place_label] END
END""")
add("Sk Tip Full", "string", "row", "IF [Sk Is Flag Node] THEN [flag_name] END")
add("Sk Tip N", "integer", "row", 'IF [sk_part] = "Link" THEN [Sk Link N] ELSE [Sk Node N] END')
add("Sk Tip Share", "real", "row", "IF [Total Gaps] > 0 THEN [Sk Tip N] / [Total Gaps] END")
for cap, col in (("Sk Flag Rank", "flag_rank"), ("Sk Flag Rank Prior", "flag_rank_prior_close"),
                 ("Sk Flag Count Prior", "flag_count_prior_close"), ("Sk Flag Rank YA", "flag_rank_year_ago"),
                 ("Sk Flag Count YA", "flag_count_year_ago")):
    add(cap, "integer", "row", f"{{ FIXED [flag_label] : MIN(IF [Sankey Gap Row] THEN [{col}] END) }}")
add("Sk Tip Ranked", "boolean", "row", "[Sk Is Flag Node] AND [Scope Is All]")
add("Sk Tip Rank", "string", "row", 'IF [Sk Tip Ranked] THEN "Rank " + STR([Sk Flag Rank]) + " of 9" END')
add("Sk Tip Rank Worse", "string", "row",
    'IF [Sk Tip Ranked] AND [Sk Flag Rank] < [Sk Flag Rank Prior]\nTHEN "up from " + STR([Sk Flag Rank Prior]) + " at the prior close (" + STR([Sk Flag Count Prior]) + ")" END')
add("Sk Tip Rank Better", "string", "row",
    'IF [Sk Tip Ranked] AND [Sk Flag Rank] > [Sk Flag Rank Prior]\nTHEN "down from " + STR([Sk Flag Rank Prior]) + " at the prior close (" + STR([Sk Flag Count Prior]) + ")" END')
add("Sk Tip Rank Same", "string", "row",
    'IF [Sk Tip Ranked] AND [Sk Flag Rank] = [Sk Flag Rank Prior]\nTHEN "same rank as the prior close (" + STR([Sk Flag Count Prior]) + ")" END')
add("Sk Tip Year Ago", "string", "row",
    'IF [Sk Tip Ranked] AND NOT ISNULL([Sk Flag Rank YA])\nTHEN "A year ago: " + STR([Sk Flag Count YA]) + " gaps, rank " + STR([Sk Flag Rank YA]) END')
add("Sk Tip Puts At Risk", "string", "row", 'IF [Sk Is Flag Node] THEN "Puts at risk: " + [risk] END')
# where the node's gaps are aligned (flag and risk nodes)
add("Sk Node B", "integer", "row", "CASE [sk_level] WHEN 1 THEN [Sk F PB1] WHEN 2 THEN [Sk R PB1] END")
add("Sk Node K", "integer", "row", "CASE [sk_level] WHEN 1 THEN [Sk F PB2] - [Sk F PB1] WHEN 2 THEN [Sk R PB2] - [Sk R PB1] END")
add("Sk Node S", "integer", "row", "CASE [sk_level] WHEN 1 THEN [Flag Gaps] - [Sk F PB2] WHEN 2 THEN [Risk Gaps] - [Sk R PB2] END")
add("Sk Tip Aligned", "boolean", "row", '[sk_part] = "Node" AND [sk_level] < 3')
add("Sk Tip Aligned In", "string", "row", 'IF [Sk Tip Aligned] THEN "Aligned in:" END')
add("Sk Tip Bridgeway", "string", "row", 'IF [Sk Tip Aligned] AND [Sk Node B] > 0 THEN "Bridgeway (vendor system) " + STR([Sk Node B]) END')
add("Sk Tip Keystone", "string", "row", 'IF [Sk Tip Aligned] AND [Sk Node K] > 0 THEN "Keystone (HR system) " + STR([Sk Node K]) END')
add("Sk Tip System Feed", "string", "row", 'IF [Sk Tip Aligned] AND [Sk Node S] > 0 THEN "System feed (integration) " + STR([Sk Node S]) END')
add("Sk Risk Flags", "integer", "row", "{ FIXED [risk] : COUNTD(IF [Sankey Gap Row] THEN [flag_code] END) }")
add("Sk Place Flags", "integer", "row", "{ FIXED [place] : COUNTD(IF [Sankey Gap Row] THEN [flag_code] END) }")
add("Sk Tip From", "string", "row", """IF [sk_part] = "Node" AND [sk_level] = 2 THEN "From " + STR([Sk Risk Flags]) + IIF([Sk Risk Flags] = 1, " flag", " flags")
ELSEIF [sk_part] = "Node" AND [sk_level] = 3 THEN "From " + STR([Sk Place Flags]) + IIF([Sk Place Flags] = 1, " flag", " flags") END""")
for lvl, key in ((1, "flag_label"), (2, "risk"), (3, "place")):
    add(f"Sk No Ticket {lvl}", "integer", "row", f"{{ FIXED [{key}] : SUM(IF [Sankey Gap Row] AND NOT [has_ticket] THEN 1 ELSE 0 END) }}")
    add(f"Sk Over 90 {lvl}", "integer", "row", f"{{ FIXED [{key}] : SUM(IF [Sankey Gap Row] AND [days_open] > 90 THEN 1 ELSE 0 END) }}")
add("Sk Node No Ticket", "integer", "row", "CASE [sk_level] WHEN 1 THEN [Sk No Ticket 1] WHEN 2 THEN [Sk No Ticket 2] ELSE [Sk No Ticket 3] END")
add("Sk Node Over 90", "integer", "row", "CASE [sk_level] WHEN 1 THEN [Sk Over 90 1] WHEN 2 THEN [Sk Over 90 2] ELSE [Sk Over 90 3] END")
add("Sk Tip No Ticket", "string", "row", 'IF [sk_part] = "Node" AND [Sk Node No Ticket] > 0 THEN STR([Sk Node No Ticket]) + " with no ticket" END')
add("Sk Tip Over 90", "string", "row", 'IF [sk_part] = "Node" AND [Sk Node Over 90] > 0 THEN STR([Sk Node Over 90]) + " open more than 90 days" END')
for cap, cls in (("Sk Feed Event", "Feed event failed"), ("Sk Feed Load", "Load failed"), ("Sk Feed Stuck", "Feed stuck")):
    add(cap, "integer", "row", f'{{ FIXED [place] : SUM(IF [Sankey Gap Row] AND [timing_class] = "{cls}" THEN 1 ELSE 0 END) }}')
add("Sk Tip Feed Causes", "string", "row", """IF [sk_part] = "Node" AND [sk_level] = 3 AND [place] = "System feed"
THEN STR([Sk Feed Event]) + " failed feed events, " + STR([Sk Feed Load]) + " failed loads, " + STR([Sk Feed Stuck]) + " stuck" END""")
add("Sk Flag Next Step", "string", "row", "{ FIXED [flag_label] : MIN(IF [Sankey Gap Row] THEN [next_step] END) }")
add("Sk Tip Next Step", "string", "row", """IF [Sk Is Flag Node] THEN "Next step: " + [Sk Flag Next Step]
ELSEIF [sk_part] = "Node" AND [sk_level] = 3 THEN "Worked by " + CASE [place] WHEN "Bridgeway" THEN "Vendor Management" WHEN "Keystone" THEN "HR Operations" ELSE "Data Engineering" END
ELSEIF [sk_part] = "Node" THEN "Next steps differ by gap: see the gap list" END""")

# ---------- a click picks a flag, a risk or a place (parameter actions; the gap list filters on Sk Pick Match)
add("Sk Pick Flag", "string", "row", 'IF [sk_part] = "Link" OR ([sk_level] = 1 AND [sk_part] <> "Header") THEN [flag_code] ELSE "" END')
add("Sk Pick Risk", "string", "row", 'IF [sk_level] = 2 AND ([sk_part] = "Node" OR [sk_part] = "Label") THEN [risk] ELSE "" END')
add("Sk Pick Place", "string", "row", 'IF [sk_part] = "Link" OR ([sk_level] = 3 AND [sk_part] <> "Header") THEN [place] ELSE "" END')
add("Sk Picked", "boolean", "row", '[p_SkFlag] <> "" OR [p_SkRisk] <> "" OR [p_SkPlace] <> ""')
add("Sk Pick Match", "boolean", "row",
    '([p_SkFlag] = "" OR [flag_code] = [p_SkFlag]) AND ([p_SkRisk] = "" OR [risk] = [p_SkRisk]) AND ([p_SkPlace] = "" OR [place] = [p_SkPlace])')

# ---------- the main card headline in short names (copies of 7.8 with flag_short; the originals stay)
add("Sk Top Flag", "string", "row",
    "{ FIXED : MIN(IF [Sankey Gap Row] AND [Flag Gaps] = [Top Flag Gaps] THEN [flag_short] END) }")
add("Sk Main Title", "string", "row", """IF ZN([Total Gaps]) = 0 THEN "No gaps in this selection"
ELSE [Top Place] + " holds " + [Top Place Gaps Str] + " of " + [Total Gaps Str] + " gaps. Largest flag: " + [Sk Top Flag] + " (" + [Top Flag Gaps Str] + ")" END""")
add("Sk Mover Text", "string", "row", """{ FIXED : MIN(IF [Sankey Gap Row] AND [flag_label] = [Mover] THEN
  [flag_short] + ": " + [Ordinal YA] + " a year ago (" + STR([flag_count_year_ago]) + "), "
  + [Ordinal Now] + " now (" + STR([Flag Gaps]) + ")" END) }""")
add("Sk Main Subtitle", "string", "agg", """(IF ZN(MIN([Total Gaps])) = 0 THEN "Choose another close or fewer groups"
ELSEIF NOT [Scope Is All] THEN "Ranks and year-ago comparisons cover all of Arcadia: choose All in the rail to see them"
ELSEIF NOT [Has Prior] THEN "First close in the data"
ELSE (IF MIN([Top Flag Prior Rank]) = 1 THEN "Same largest flag as " ELSE "New largest flag since " END) + [Prior Month] + ". "
   + (IF ZN(MIN([Max Move])) = 0 THEN "No flag changed rank since a year ago" ELSE MIN([Sk Mover Text]) END)
END)
+ (IF MIN([Clear Own Gaps]) > 0 THEN " · " + STR(MIN([Clear Own Gaps])) + " clear on their own by the next run" ELSE "" END)""")

# v1 and revision 5 fields that v2 no longer uses (apply_sankey_v2.py removes them from the workbook)
OBSOLETE = ["Sk N Max", "Sk Gap F", "Sk Gap R", "Sk Gap P", "Sk Link H", "Sk Label DX", "Sk Lbl Name", "Sk Lbl Count",
            "Sk Lbl Place", "Sk Lbl Sub", "Sk Flag Y", "Sk Flag X"]
# revision 7 fitting loop and per-box heights, replaced by the closed form (revision 8)
OBSOLETE += [f"Sk {x} {c}" for c in "FRP" for x in ("S0", "S1", "S2", "Small N1", "Small Sum1", "Small N2", "Small Sum2")]
OBSOLETE += [f"Sk {c}H{k}" for c, n in (("F", 9), ("R", 5), ("P", 3)) for k in range(1, n + 1)]
OBSOLETE += [f"Sk {c} Used" for c in "FRP"] + [f"Sk {c} H Before" for c in "FRP"]
OBSOLETE = [c for c in OBSOLETE if c not in {x[0] for x in C}]

# ---------- the Sk Colour palette (revision 7: palette A, muted families; risks slate, places as on the rest of the page)
def _tint(h, a=0.45):
    h = h.lstrip('#'); r, g, b = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return '#%02X%02X%02X' % tuple(round(a * v + (1 - a) * 255) for v in (r, g, b))
# revision 8: nine independent hues at one strength (OKLCH lightness 0.68, chroma 0.11), none near the place hues
# ordered so neighbouring flags contrast (no column of look-alike families)
FLAG_COLOURS = {'F01': '#D47B7C', 'F02': '#3AA6CB', 'F03': '#90A250', 'F04': '#B582C4', 'F05': '#AE9740',
                'F06': '#20ACB3', 'F07': '#CB7BA2', 'F08': '#70A969', 'F09': '#619DDA'}
PALETTE = {**FLAG_COLOURS, **{f'{k} ribbon': _tint(v) for k, v in FLAG_COLOURS.items()},
           'Risk': '#4F6980', 'Risk ribbon': _tint('#4F6980'),   # same tint as the flag ribbons; white borders show the crossings
           'Bridgeway': '#F89217', 'Keystone': '#7873C0', 'System feed': '#21B087'}
