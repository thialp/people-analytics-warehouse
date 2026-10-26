"""Build doc section 11 (step 8): the five popovers, their close sheets and the show/hide wiring.

  python3 build_popovers.py "in.twb" "out.twb"          (close Tableau first)

Stage 1 (this file): each popover is a floating vertical container hung from the rail edge (x 216), with header,
line, body and footer. Headers, lines, footers and the Info text are final. The ✕ buttons are sheets (`Close Close`,
`Function Close`, `Department Close`, `Country Close`). Bodies hold placeholder zones until their sheets exist
(stage 2: Close Years / Close Grid, Function List, Department List, Country List and the three Clear buttons).
Visibility is Tableau's "Control visibility using value": a `<datagraph>` after the windows, one node pair per
popover: single-value-field-node (the p_*Open parameter) -> dashboard-zone-visibility-node (the popover zone).
The helper functions are taken from build_rail_sheets.py so both builds draw sheets the same way.
"""
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
src, out = sys.argv[1], sys.argv[2]
head = open(os.path.join(HERE, 'build_rail_sheets.py'), encoding='utf-8').read()
head = head[:head.index('ONE = [')]
head = re.sub(r"for n in \('Close Field', 'Show Toggle', 'Rail As Of'\):\n    assert [^\n]*\n", '', head)
head = head.replace("src, out = sys.argv[1], sys.argv[2]\n", '')
head = head.replace("SKIP = set(sys.argv[3].split(',')) if len(sys.argv) > 3 else set()", 'SKIP = set()')
# new calc, inserted before the first calc so the helper's parser finds it
NEWCALC = ("      <column caption='Popover X Text' datatype='string' name='[Calculation_0725102600000220]' role='dimension' type='nominal'>\n"
           "        <calculation class='tableau' formula='// Popover X Text&#10;&quot;✕&quot;' />\n      </column>\n")
exec(compile(head, 'helpers', 'exec'), globals())
assert "Popover X Text" not in s, 'already built'
k = s.index("      <column caption='Close Field Text'")
s = s[:k] + NEWCALC + s[k:]
DSX = s[s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'"):]
DSX = DSX[:DSX.index('</datasource>')]
CALC.clear()
for m in re.finditer(r"      <column caption='([^']*)' datatype='(\w+)' name='(\[Calculation_\d+\])'[^>]*>\n.*?\n      </column>\n", DSX, re.S):
    CALC[m.group(1)] = (m.group(3), m.group(0), m.group(2))
CAP_OF.clear()
CAP_OF.update({v[0]: k2 for k2, v in CALC.items()})

ONE = [('Is Selected Close', True), ('Is Pop', True)]
HID = ['zzFalse', 'zzTrue', 'Close Panel']
SHEETS = []
for nm in ('Close', 'Function', 'Department', 'Country'):
    SHEETS.append(sheet_xml(f'{nm} Close', HID, text=['Popover X Text'], filters=ONE, mark='Automatic',
                            tooltip='Close', label=[('Popover X Text', 'Tableau Book', '#B8C0CC', '12')]))

w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[0] for x in SHEETS) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[1] for x in SHEETS) + s[win_end:]
w0 = s.index('<worksheets>') + len('<worksheets>\n')
w1 = s.index('  </worksheets>')
parts = [(m.group(1), m.group(0)) for m in re.finditer(r"    <worksheet name='([^']*)'>.*?\n    </worksheet>\n", s[w0:w1], re.S)]
assert ''.join(p[1] for p in parts) == s[w0:w1], 'unexpected worksheet layout'
s = s[:w0] + ''.join(b for _, b in sorted(parts, key=lambda p: p[0])) + s[w1:]

# ---- zones -----------------------------------------------------------------------------------------------
a = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b = s.index('</dashboard>', a)
d = s[a:b]
dash_id = re.findall(r"<simple-id uuid='(\{[0-9A-F-]+\})' />", s[a:b + len('</dashboard>')])[-1]
nid = [200]
IMG = '/Users/thiagoalpoin/Documents/Tableau/Tableau Public/ArcadiaHR/4 Contingent Workforce Reconciliation/Images and Buttons/'


def ux(px):
    return round(px * 100000 / 1400)


def uy(px):
    return round(px * 100000 / 850)


def zid():
    nid[0] += 1
    return nid[0]


NO_BORDER = ("<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
             "<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n")


def e(t):
    return t.replace('&', '&amp;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;')


def geo(x, y, w, h):
    return f"h='{uy(h)}' w='{ux(w)}' x='{ux(x)}' y='{uy(y)}'"


def text_zone(name, x, y, w, h, runs, pad, fixed=None, flex=False):
    fx = '' if flex else f" fixed-size='{fixed}' is-fixed='true'"
    return (f"<zone{fx} forceUpdate='true' friendly-name='{name}' {geo(x, y, w, h)} hidden-by-user='true' id='{zid()}' type-v2='text'>\n"
            f"<formatted-text>\n{runs}</formatted-text>\n<zone-style>\n{NO_BORDER}{pad}</zone-style>\n</zone>\n")


def sheet_zone(name, x, y, w, h, fixed):
    return (f"<zone fixed-size='{fixed}' {geo(x, y, w, h)} hidden-by-user='true' id='{zid()}' is-fixed='true' name='{name}' show-title='false'>\n"
            f"<layout-cache type-h='cell' type-w='fixed' />\n<zone-style>\n{NO_BORDER}</zone-style>\n</zone>\n")


def empty_zone(name, x, y, w, h, fixed=None):
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    return (f"<zone{fx} friendly-name='{name}' {geo(x, y, w, h)} hidden-by-user='true' id='{zid()}' type-v2='empty'>\n"
            f"<zone-style>\n{NO_BORDER}</zone-style>\n</zone>\n")


def line_zone(img, x, y, w):
    return (f"<zone fixed-size='9' {geo(x, y, w, 9)} hidden-by-user='true' id='{zid()}' is-centered='0' is-fixed='true' is-scaled='1' "
            f"param='{IMG}{img}' type-v2='bitmap'>\n<zone-style>\n{NO_BORDER}</zone-style>\n</zone>\n")


def flow(name, x, y, w, h, kids, fixed=None, direction='horz'):
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    return (f"<zone{fx} friendly-name='{name}' {geo(x, y, w, h)} hidden-by-user='true' id='{zid()}' param='{direction}' type-v2='layout-flow'>\n"
            f"{kids}<zone-style>\n{NO_BORDER}</zone-style>\n</zone>\n")


TITLE_PAD = "<format attr='padding-top' value='12' />\n<format attr='padding-left' value='16' />\n"
FOOT_PAD = "<format attr='padding-top' value='6' />\n<format attr='padding-left' value='16' />\n"
BODY_PAD = ("<format attr='padding-top' value='4' />\n<format attr='padding-right' value='16' />\n"
            "<format attr='padding-left' value='16' />\n")
FRAME = ("<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
         "<format attr='border-width' value='0' />\n"
         "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='4' />\n"
         "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-top-left' value='0' />\n"
         "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-top-right' value='10' />\n"
         "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-bottom-left' value='0' />\n"
         "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-bottom-right' value='10' />\n"
         "<format attr='padding' value='0' />\n<format attr='background-color' value='#13233a' />\n</zone-style>\n")


def title_runs(t):
    return f"<run fontcolor='#ffffff' fontname='Tableau Bold' fontsize='12'>{e(t)}</run>\n"


def foot_runs(t):
    return f"<run fontcolor='#8fa0b8' fontname='Tableau Book' fontsize='9'>{e(t)}</run>\n"


def popover(name, flag, x, y, w, title, line, body, foot, clear=False, close=None):
    """body: (height, kids-builder(x, y)). Returns (zone xml, zone id)."""
    top = y
    hy = top
    kids = ''
    tw = w - 44 - (80 if clear else 0) if close else w
    kids_h = text_zone(f'{name} Title', x, hy, tw, 44, title_runs(title), TITLE_PAD, flex=True)
    cx = x + tw
    if clear:
        kids_h += text_zone(f'{name} Clear (placeholder)', cx, hy, 80, 44,
                            "<run fontcolor='#b8c0cc' fontname='Tableau Book' fontsize='9'>Clear all</run>\n", TITLE_PAD, fixed=80)
        cx += 80
    if close:
        kids_h += sheet_zone(close, cx, hy, 44, 44, 44)
    kids += flow(f'{name} Header', x, hy, w, 44, kids_h, fixed=44)
    kids += line_zone(line, x, hy + 44, w)
    bh, bk = body
    kids += bk(x, hy + 53, w)
    fy = hy + 53 + bh
    h = 53 + bh
    if foot:
        kids += text_zone(f'{name} Footer', x, fy, w, 28, foot_runs(foot), FOOT_PAD, fixed=28)
        h += 28
    pid = nid[0] + 1
    nid[0] += 1
    z = (f"<zone friendly-name='{name}' {geo(x, y, w, h)} hidden-by-user='true' id='{pid}' param='vert' type-v2='layout-flow'>\n"
         f"{kids}{FRAME}</zone>\n")
    return z, pid


def empty_body(label, h):
    return h, lambda x, y, w: empty_zone(label, x, y, w, h, fixed=h)


def close_body(x, y, w):
    kids = empty_zone('Close Years (placeholder)', x, y, 72, 208, fixed=72) + empty_zone('Close Grid (placeholder)', x + 72, y, 552, 208, fixed=552)
    return flow('Close Body', x, y, w, 208, kids, fixed=208)


INFO = [
    ('The close.', "Finance reports contractors from Keystone, Arcadia's HR system. Bridgeway, the vendor system, holds every contractor's order. At 00:00 GMT on the 1st, the close run reads both and compares them, contractor by contractor."),
    ('Gaps.', "A gap is one difference for one contractor: Keystone shows one thing, Bridgeway another. Nine flags say what differs, five risks say what it puts at risk in the report, and three places say where it is aligned: Bridgeway (Vendor Management), Keystone (HR Operations) or the system feed between them (Data Engineering). The words say what differs, not which system is wrong."),
    ('Gap rate.', "Contractors with at least one gap, divided by contractors working in Bridgeway. A change still in the feed that will land by the next run is left out. The 3% target is provisional: it flags risk, it does not certify the report."),
    ('Tickets.', "Open Helix tickets at the close, by the group working them now. A ticket links to a gap through the contractor's ID; a name alone is not enough when two contractors share it, so some tickets link to no gap and, without a contractor, to no group."),
    ('What a flag proves.', "“Active in Keystone, not working in Bridgeway” means Keystone still shows the contractor active after Bridgeway ended them, not that they used any access."),
    ('Data.', "Arcadia Systems, Keystone, Bridgeway and Helix are fictional. All data is synthetic."),
]
info_runs = ''
for i, (lead, txt) in enumerate(INFO):
    info_runs += (f"<run bold='true' fontcolor='#ffffff' fontname='Tableau Semibold' fontsize='10'>{e(lead)}</run>\n"
                  f"<run fontcolor='#ffffff' fontname='Tableau Semibold' fontsize='10'>Æ </run>\n"
                  f"<run fontcolor='#b8c0cc' fontsize='10'>{e(txt)}</run>\n")
    if i < len(INFO) - 1:
        info_runs += "<run>Æ&#10;&#10;</run>\n"


def info_body(x, y, w):
    return text_zone('Info Body', x, y, w, 440, info_runs, BODY_PAD, fixed=440)


POP = []     # (zone xml, zone id, parameter name)
POP.append(popover('Close Popover', 'p_CloseOpen', 216, 92, 624, 'Choose the close', 'd2_popover_line_wide.png', (208, close_body),
                   'Each close is the 00:00 GMT run on the 1st. Dec 2024 replays a Keystone outage; Sep 2023 a Bridgeway one.',
                   close='Close Close') + ('[Parameters].[Parameter 0725102600000006]',))
POP.append(popover('Function Popover', 'p_FunctionOpen', 216, 170, 312, 'Choose functions', 'd2_popover_line_wide.png',
                   empty_body('Function List (placeholder)', 224), 'Choose one or more. None chosen means all functions.',
                   clear=True, close='Function Close') + ('[Parameters].[Parameter 0725102600000007]',))
POP.append(popover('Department Popover', 'p_DepartmentOpen', 216, 248, 624, 'Choose departments', 'd2_popover_line_wide.png',
                   empty_body('Department List (placeholder)', 302), 'Dim: outside the chosen functions. None chosen means all.',
                   clear=True, close='Department Close') + ('[Parameters].[Parameter 0725102600000008]',))
POP.append(popover('Country Popover', 'p_CountryOpen', 216, 326, 624, 'Choose countries', 'd2_popover_line_wide.png',
                   empty_body('Country List (placeholder)', 224), 'None chosen means all countries.',
                   clear=True, close='Country Close') + ('[Parameters].[Parameter 0725102600000009]',))
POP.append(popover('Info Popover', 'p_InfoOpen', 216, 24, 591, 'How to read this page', 'd2_popover_line_info.png',
                   (440, info_body), None) + ('[Parameters].[Parameter 0725102600000010]',))

# floating: direct children of <zones>, last so they sit above the cards; placed after the three test controls
zend = d.index('  </zones>')
d = d[:zend] + ''.join(p[0] for p in POP) + d[zend:]
s = s[:a] + d + s[b:]

# dashboard window: a viewpoint for every sheet placed on it
wi = s.index("<window class='dashboard' maximized='true' name='CW Reconciliation'")
vend = s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vp = ''.join(f"        <viewpoint name='{sh}'>\n          <zoom type='entire-view' />\n        </viewpoint>\n"
             for sh in ('Close Close', 'Country Close', 'Department Close', 'Function Close'))
s = s[:vend] + vp + s[vend:]
# viewpoints stay in name order
vs, ve = s.index('<viewpoints>', wi) + len('<viewpoints>\n'), s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vparts = re.findall(r"        <viewpoint name='[^']*'>\n          <zoom type='entire-view' />\n        </viewpoint>\n", s[vs:ve])
assert ''.join(vparts) == s[vs:ve], 'unexpected viewpoint layout'
s = s[:vs] + ''.join(sorted(vparts, key=lambda v: re.search(r"name='([^']*)'", v).group(1))) + s[ve:]

# ---- visibility ("Control visibility using value") ---------------------------------------------------------
g = lambda: str(uuid.uuid4())
sub = g()
nodes, edges, pairs = '', '', ''
for zxml, zid_, par in POP:
    vz, vin, fn_in, val_out, fnode = g(), g(), g(), g(), g()
    nodes += (f"        <dashboard-zone-visibility-node dashboard-identifier='{dash_id}' node-guid='{vz}' visibility-input-guid='{vin}' zone-id='{zid_}' />\n"
              f"        <single-value-field-node fieldname='{par}' fieldname-input-guid='{fn_in}' node-guid='{fnode}' value-output-guid='{val_out}' />\n")
    edges += f"        <edge from='{val_out}' to='{vin}' />\n"
    pairs += (f"        <pair execution-subgraph-guid='{sub}' node-guid='{vz}' />\n"
              f"        <pair execution-subgraph-guid='{sub}' node-guid='{fnode}' />\n")
dg = (f"  <datagraph>\n    <graph>\n      <properties>\n        <default-execution-subgraph-guid value='{sub}' />\n      </properties>\n"
      f"      <node-execution-subgraphs>\n{pairs}      </node-execution-subgraphs>\n      <nodes>\n{nodes}      </nodes>\n"
      f"      <edges>\n{edges}      </edges>\n      <pin-values />\n    </graph>\n  </datagraph>\n")
assert '<datagraph>' not in s
k = s.index('  </windows>\n') + len('  </windows>\n')
s = s[:k] + dg + s[k:]
# the visibility graph needs these feature flags in the document-format-change manifest (Tableau rejects <datagraph> without them)
m0 = s.index('<document-format-change-manifest>')
m1 = s.index('</document-format-change-manifest>')
man = re.findall(r"    <[^>]+ />\n", s[m0:m1])
for f in ('DatagraphCoreV1', 'DatagraphNodeDashboardZoneVisibilityV1', 'DatagraphNodeSingleValueFieldV1', 'ZoneVisibilityControl'):
    if f"<{f} />" not in s[m0:m1]:
        man.append(f"    <{f} />\n")
s = s[:m0] + '<document-format-change-manifest>\n' + ''.join(sorted(man, key=lambda x: x.strip().replace("_.fcp.", "").lower())) + '  ' + s[m1:]
open(out, 'w', encoding='utf-8').write(s)
print('sheets', len(SHEETS), 'popovers', len(POP), 'last zone id', nid[0], 'dashboard id', dash_id)
