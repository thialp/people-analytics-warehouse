"""Build doc sections 13 and 14 (steps 10 and 11): the gap list with the Overview / Gap list swap, and the timeline card.

  python3 build_gap_timeline.py "after_step9.twb" "out.twb"          (close Tableau first)

Adds the sheets Gap List Title, Gap List, Timeline Title, Timeline; puts the gap-list pair in Card: Main next to the
Sankey pair; swaps the placeholders in Card: Timeline; wires the visibility of the two pairs (Show Overview /
p_ShowList) into the datagraph; adds a temporary p_ShowList control to test the swap (removed in step 14, with the
five open-flag controls). Clicks still do nothing until the actions (step 14).
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
exec(compile(head, 'helpers', 'exec'), globals())
assert "<worksheet name='Gap List'>" not in s, 'already built'
assert "<worksheet name='KPI Cards'>" in s, 'run build_kpi_cards.py first'


def esc(f):
    return f.replace('&', '&amp;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '&#10;')


# ---------------------------------------------------------------- new calcs
NEW = []
_n = [320]


def newcalc(cap, datatype, role, typ, formula, fmt=''):
    cid = f'Calculation_0725102600000{_n[0]}'
    assert cid not in s, cid
    _n[0] += 1
    NEW.append((cap, cid, datatype, role, typ, formula, fmt))
    return cid


newcalc('Timeline Title', 'string', 'dimension', 'nominal', '// Timeline Title\n"Gap rate at each month-end close"')
NEW_RATE2 = newcalc('TL Rate 2', 'real', 'measure', 'quantitative', '// TL Rate 2 (second copy for the dot axis)\n[Calculation_0725102600000195]', " default-format='p0.00%'")
block = ''
for cap, cid, dt, role, typ, f, fmt in NEW:
    block += (f"      <column caption='{cap}' datatype='{dt}'{fmt} name='[{cid}]' role='{role}' type='{typ}'>\n"
              f"        <calculation class='tableau' formula='{esc(f)}' />\n      </column>\n")
k = s.index("      <column caption='Close Field Text'")
s = s[:k] + block + s[k:]

DSX = s[s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'"):]
DSX = DSX[:DSX.index('</datasource>')]
CALC.clear()
for m in re.finditer(r"      <column caption='([^']*)' datatype='(\w+)'[^>]*? name='(\[Calculation_\d+\])'[^>]*>\n.*?\n      </column>\n", DSX, re.S):
    CALC[m.group(1)] = (m.group(3), m.group(0), m.group(2))
CAP_OF.clear()
CAP_OF.update({v[0]: k2 for k2, v in CALC.items()})
D = f'[{DS}]'


def nm(cap):
    return CALC[cap][0].strip('[]')


_sqlcol_helper = sqlcol


def sqlcol(name):
    try:
        return _sqlcol_helper(name)
    except AssertionError:
        m = re.search(r"<local-name>\[" + name + r"\]</local-name>.*?<local-type>(\w+)</local-type>", s, re.S)
        assert m, 'no declaration or metadata for ' + name
        typ = m.group(1)
        role, ty = ('measure', 'quantitative') if typ in ('integer', 'real') else ('dimension', 'ordinal' if typ == 'date' else 'nominal')
        return f"<column datatype='{typ}' name='[{name}]' role='{role}' type='{ty}' />"


def role_of(cap):
    return re.search(r"role='(\w+)'", CALC[cap][1]).group(1)


def tinst(cap):
    base = nm(cap)
    if role_of(cap) == 'measure':
        return f'[usr:{base}:nk]', f"<column-instance column='[{base}]' derivation='User' name='[usr:{base}:nk]' pivot='key' type='nominal' />"
    return f'[none:{base}:nk]', f"<column-instance column='[{base}]' derivation='None' name='[none:{base}:nk]' pivot='key' type='nominal' />"


def qinst(cap):
    base = nm(cap)
    return f'[usr:{base}:qk]', f"<column-instance column='[{base}]' derivation='User' name='[usr:{base}:qk]' pivot='key' type='quantitative' />"


def dims_deps(caps, sqlnames, extra_inst, filters):
    calcs, params, sql = closure(list(dict.fromkeys(caps)))
    sql |= set(sqlnames)
    colx = [CALC[c][1].rstrip('\n') for c in sorted(calcs, key=lambda c: CALC[c][0])] + ['      ' + sqlcol(q) for q in sorted(sql)]
    pdep = ''
    if params:
        pdep = ("          <datasource-dependencies datasource='Parameters'>\n" + ''.join(PARAM[p] for p in sorted(params)) + "          </datasource-dependencies>\n")
    insts = list(extra_inst)
    flt, slices = '', ''
    for c in filters:
        base = nm(c)
        insts.append(f"<column-instance column='[{base}]' derivation='None' name='[none:{base}:nk]' pivot='key' type='nominal' />")
        r = f"{D}.[none:{base}:nk]"
        flt += (f"          <filter class='categorical' column='{r}'>\n            <groupfilter function='member' level='[none:{base}:nk]' member='true' "
                f"user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n          </filter>\n")
        slices += f"            <column>{r}</column>\n"
    return params, pdep, colx, insts, flt, slices


def dep_xml(colx, insts):
    return (f"          <datasource-dependencies datasource='{DS}'>\n{chr(10).join(colx)}\n"
            f"{chr(10).join('            ' + i for i in insts)}\n          </datasource-dependencies>\n")


def window(name):
    return f"""    <window class='worksheet' name='{name}'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
      </cards>
      <viewpoint>
        <zoom type='entire-view' />
      </viewpoint>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </window>
"""


def zero_rules():
    return ''.join(f"          <style-rule element='{e}'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
                   for e in ('dropline', 'refline', 'zeroline'))


def wrap(name, view_head, style, panes_xml, rows, cols, extra=''):
    return f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='CW Reconciliation' name='{DS}' />
            <datasource name='Parameters' />
          </datasources>
{view_head}          <aggregation value='true' />
        </view>
        <style>
{style}        </style>
        <panes>
{panes_xml}        </panes>
        <rows>{rows}</rows>
        <cols>{cols}</cols>
{extra}      </table>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </worksheet>
"""


SHEETS = []
SHAPES, COLORS = [], []


def palette(cap, mapping):
    f = f"[none:{nm(cap)}:nk]" if role_of(cap) == 'dimension' else f"[usr:{nm(cap)}:nk]"
    e = f"          <encoding attr='color' field='{f}' type='palette'>\n"
    for b, colr in mapping.items():
        e += f"            <map to='{colr}'>\n              <bucket>&quot;{b}&quot;</bucket>\n            </map>\n"
    return e + "          </encoding>\n"


# ---------------------------------------------------------------- title sheets (one mark, two runs)
def title_sheet(name, title_cap, sub_cap):
    ti, tix = tinst(title_cap)
    si, six = tinst(sub_cap)
    params, pdep, colx, insts, flt, slices = dims_deps([title_cap, sub_cap], [], [tix, six], [])
    view = pdep + dep_xml(colx, insts)
    style = ("          <style-rule element='axis'>\n            <format attr='tick-color' value='#00000000' />\n          </style-rule>\n"
             "          <style-rule element='header'>\n            <format attr='band-color' scope='rows' value='#00000000' />\n            <format attr='border-width' data-class='subtotal' value='0' />\n            <format attr='border-style' data-class='subtotal' value='none' />\n          </style-rule>\n"
             "          <style-rule element='pane'>\n            <format attr='band-color' scope='rows' value='#00000000' />\n            <format attr='border-width' data-class='subtotal' value='0' />\n            <format attr='border-style' data-class='subtotal' value='none' />\n          </style-rule>\n"
             "          <style-rule element='table'>\n            <format attr='background-color' value='#00000000' />\n            <format attr='band-size' scope='rows' value='1' />\n          </style-rule>\n"
             + zero_rules())
    pane = (f"          <pane selection-relaxation-option='selection-relaxation-allow'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
            f"            <mark class='Automatic' />\n            <encodings>\n              <text column='{D}.{si}' />\n              <text column='{D}.{ti}' />\n            </encodings>\n"
            f"            <customized-label>\n              <formatted-text>\n"
            f"                <run fontcolor='#13243a' fontname='Tableau Semibold' fontsize='12'><![CDATA[<{D}.{ti}>]]></run>\n"
            f"                <run>Æ&#10;</run>\n"
            f"                <run fontcolor='#5a6171' fontsize='9'><![CDATA[<{D}.{si}>]]></run>\n"
            f"              </formatted-text>\n            </customized-label>\n"
            f"            <style>\n              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n                <format attr='mark-labels-cull' value='true' />\n              </style-rule>\n"
            f"              <style-rule element='trendline'>\n                <format attr='stroke-size' value='0' />\n                <format attr='line-visibility' value='off' />\n              </style-rule>\n            </style>\n          </pane>\n")
    x = wrap(name, view, style, pane, '', '')
    SHEETS.append((name, x, window(name)))


title_sheet('Gap List Title', 'Gap List Title', 'Gap List Subtitle')
title_sheet('Timeline Title', 'Timeline Title', 'Timeline Subtitle')

# ---------------------------------------------------------------- Gap List (a text table, one row per gap)
GL_ROWS = [('sql', 'place_order', 'ok'), ('calc', 'WHERE ALIGNED', 'nk'), ('sql', 'gap_id', 'nk'), ('calc', 'WHAT DIFFERS', 'nk'),
           ('calc', 'CONTRACTOR', 'nk'), ('calc', 'KEYSTONE SHOWS', 'nk'), ('calc', 'BRIDGEWAY HAS', 'nk'), ('calc', 'TICKET', 'nk')]
GL_DETAIL = ['What differs', 'What it puts at risk', 'Where it is aligned', 'zzTrue', 'zzFalse']
GL_WIDTH = {'WHERE ALIGNED': 80, 'WHAT DIFFERS': 160, 'CONTRACTOR': 110, 'KEYSTONE SHOWS': 130, 'BRIDGEWAY HAS': 130, 'TICKET': 70}
TIP_SQL = ['contractor_name', 'bw_worker_id', 'person_id', 'supplier_name', 'flag_name', 'risk', 'keystone_shows', 'bridgeway_has', 'evidence',
           'next_step', 'ticket_title', 'ticket_status']
caps = ['Gap List Row', 'DAYS OPEN', 'Days Band'] + [c for k_, c, _ in GL_ROWS if k_ == 'calc'] + GL_DETAIL
sqln = [c for k_, c, _ in GL_ROWS if k_ == 'sql'] + ['days_open'] + TIP_SQL
params, pdep, colx, insts, flt, slices = dims_deps(caps, sqln, [], ['Gap List Row'])
rows_refs, lod_refs = [], []
for kd, c, kind in GL_ROWS:
    base = nm(c) if kd == 'calc' else c
    iname = f'[none:{base}:{kind}]'
    insts.append(f"<column-instance column='[{base}]' derivation='None' name='{iname}' pivot='key' type='{'ordinal' if kind == 'ok' else 'nominal'}' />")
    rows_refs.append(f'{D}.{iname}')
for c in GL_DETAIL + ['Days Band']:
    base = nm(c)
    insts.append(f"<column-instance column='[{base}]' derivation='None' name='[none:{base}:nk]' pivot='key' type='nominal' />")
    lod_refs.append(f'{D}.[none:{base}:nk]')
days_i = f"[sum:{nm('DAYS OPEN')}:qk]"
insts.append(f"<column-instance column='[{nm('DAYS OPEN')}]' derivation='Sum' name='{days_i}' pivot='key' type='quantitative' />")
insts.append("<column-instance column='[days_open]' derivation='Max' name='[max:days_open:qk]' pivot='key' type='quantitative' />")
insts.append("<column-instance column='[days_open]' derivation='Sum' name='[sum:days_open:qk]' pivot='key' type='quantitative' />")
for q in TIP_SQL:
    insts.append(f"<column-instance column='[{q}]' derivation='Attribute' name='[attr:{q}:nk]' pivot='key' type='nominal' />")
mn = f'{D}.[:Measure Names]'
mnf = (f"          <filter class='categorical' column='{mn}'>\n            <groupfilter function='union' user:op='manual'>\n"
       f"              <groupfilter function='member' level='[:Measure Names]' member='&quot;{D}.{days_i}&quot;' />\n            </groupfilter>\n          </filter>\n")
gap_id_ref = f"{D}.[none:gap_id:nk]"
sort = f"          <computed-sort column='{gap_id_ref}' direction='DESC' using='{D}.[max:days_open:qk]' />\n"
slices2 = slices + f"            <column>{mn}</column>\n"
view = pdep + dep_xml(colx, insts) + flt + mnf + sort + f"          <slices>\n{slices2}          </slices>\n"
hide = ''.join(f"            <format attr='display' field='{r}' value='false' />\n" for r in (rows_refs[0], rows_refs[2]))
last = rows_refs[-1]
widths = ''.join(f"            <format attr='width' field='{D}.[none:{nm(c)}:nk]' value='{w}' />\n" for c, w in GL_WIDTH.items())
style = ("          <style-rule element='cell'>\n            <format attr='width' value='46' />\n"
         f"            <format attr='height' field='{last}' value='30' />\n            <format attr='text-align' value='left' />\n            <format attr='vertical-align' value='center' />\n          </style-rule>\n"
         "          <style-rule element='header'>\n            <format attr='band-color' scope='rows' value='#00000000' />\n            <format attr='band-color' scope='cols' value='#00000000' />\n"
         f"{widths}          </style-rule>\n"
         f"          <style-rule element='label'>\n{hide}          </style-rule>\n"
         "          <style-rule element='pane'>\n            <format attr='band-color' scope='rows' value='#00000000' />\n            <format attr='band-color' scope='cols' value='#00000000' />\n          </style-rule>\n"
         "          <style-rule element='table'>\n            <format attr='background-color' value='#00000000' />\n            <format attr='band-size' scope='rows' value='1' />\n            <format attr='band-size' scope='cols' value='1' />\n          </style-rule>\n"
         "          <style-rule element='worksheet'>\n            <format attr='font-size' value='9' />\n            <format attr='font-family' value='Tableau Book' />\n            <format attr='color' value='#2b2f36' />\n          </style-rule>\n"
         + zero_rules()
         + "          <style-rule element='gridline'>\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n          </style-rule>\n"
         "          <style-rule element='table-div'>\n            <format attr='stroke-size' scope='rows' value='1' />\n            <format attr='stroke-color' scope='rows' value='#e4e3dd' />\n            <format attr='line-visibility' scope='rows' value='on' />\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n          </style-rule>\n")


def a(q):
    return f"{D}.[attr:{q}:nk]"


def tr(colr, face, size, txt, bold=False):
    b = " bold='true'" if bold else ''
    return f"                <run{b} fontcolor='{colr}' fontname='{face}' fontsize='{size}'><![CDATA[{txt}]]></run>\n"


NL = "                <run>Æ&#10;</run>\n"
tip = ("            <customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
       + tr('#13243a', 'Tableau Semibold', '10', f"<{a('contractor_name')}>") + NL
       + tr('#5a6171', 'Tableau Book', '9', f"<{a('bw_worker_id')}> · <{a('person_id')}> · <{a('supplier_name')}>") + NL
       + tr('#13243a', 'Tableau Book', '9', f"<{a('flag_name')}> · puts at risk <{a('risk')}>") + NL
       + tr('#13243a', 'Tableau Book', '9', f"Keystone shows: <{a('keystone_shows')}>") + NL
       + tr('#13243a', 'Tableau Book', '9', f"Bridgeway has: <{a('bridgeway_has')}>") + NL
       + tr('#13243a', 'Tableau Book', '9', f"Evidence: <{a('evidence')}>") + NL
       + tr('#13243a', 'Tableau Book', '9', f"Open <{D}.[sum:days_open:qk]> days") + NL
       + tr('#5a6171', 'Tableau Book', '9', f"Next step: <{a('next_step')}>") + NL
       + tr('#13243a', 'Tableau Book', '9', f"Ticket: <{D}.[none:{nm('TICKET')}:nk]> <{a('ticket_title')}> · <{a('ticket_status')}>")
       + "              </formatted-text>\n            </customized-tooltip>\n")
tipcols = [a(q) for q in TIP_SQL if q not in ('ticket_title', 'ticket_status')] + [a('ticket_title'), a('ticket_status'), f"{D}.[sum:days_open:qk]"]
enc = (f"              <text column='{D}.[Multiple Values]' />\n              <color column='{D}.[none:{nm('Days Band')}:nk]' />\n"
       + ''.join(f"              <lod column='{r}' />\n" for r in rows_refs + lod_refs[:-1])
       + ''.join(f"              <tooltip column='{c}' />\n" for c in tipcols))
pane = (f"          <pane selection-relaxation-option='selection-relaxation-allow'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
        f"            <mark class='Text' />\n            <encodings>\n{enc}            </encodings>\n{tip}"
        "            <style>\n              <style-rule element='cell'>\n                <format attr='text-align' value='left' />\n                <format attr='vertical-align' value='center' />\n              </style-rule>\n"
        "              <style-rule element='datalabel'>\n                <format attr='font-family' value='Tableau Semibold' />\n                <format attr='font-size' value='9' />\n              </style-rule>\n"
        "              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n                <format attr='mark-labels-cull' value='true' />\n              </style-rule>\n"
        "              <style-rule element='pane'>\n                <format attr='minwidth' value='-1' />\n                <format attr='maxwidth' value='-1' />\n              </style-rule>\n"
        "            </style>\n          </pane>\n")
x = wrap('Gap List', view, style, pane, ' / '.join(rows_refs), mn, "        <tooltip-style tooltip-mode='sticky' />\n")
SHEETS.append(('Gap List', x, window('Gap List')))
COLORS.append(palette('Days Band', {'over 90': '#b8401f', '90 or less': '#13233a'}))

# ---------------------------------------------------------------- Timeline (line + dots, dual axis, target line)
MONTH = f"[none:month_end_date:qk]"
caps = ['Timeline Row', 'TL Rate', 'TL Rate 2', 'TL Dot', 'TL Label', 'TL Target']
params, pdep, colx, insts, flt, slices = dims_deps(caps, ['month_end_date', 'contractors_with_gap', 'contractors_working'], [], ['Timeline Row'])
insts.append("<column-instance column='[month_end_date]' derivation='None' name='[none:month_end_date:qk]' pivot='key' type='quantitative' />")
i1, x1 = qinst('TL Rate')
i2, x2 = qinst('TL Rate 2')
it, xt = qinst('TL Target')
idot, xdot = tinst('TL Dot')
ilab, xlab = tinst('TL Label')
insts += [x1, x2, xt, xdot, xlab,
          "<column-instance column='[contractors_with_gap]' derivation='Sum' name='[sum:contractors_with_gap:qk]' pivot='key' type='quantitative' />",
          "<column-instance column='[contractors_working]' derivation='Sum' name='[sum:contractors_working:qk]' pivot='key' type='quantitative' />"]
view = pdep + dep_xml(colx, insts) + flt + f"          <slices>\n{slices}          </slices>\n"
M = f'{D}.{MONTH}'
R1, R2, RT = f'{D}.{i1}', f'{D}.{i2}', f'{D}.{it}'
style = (f"          <style-rule element='axis'>\n"
         f"            <encoding attr='space' class='0' field='{M}' field-type='quantitative' major-origin='#2021-06-01#' major-spacing='3.0' major-units='months' scope='cols' type='space' />\n"
         f"            <format attr='title' class='0' field='{M}' scope='cols' value='' />\n"
         f"            <encoding attr='space' class='0' domain-expand='false' field='{R1}' field-type='quantitative' scope='rows' type='space' />\n"
         f"            <encoding attr='space' class='0' field='{R2}' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />\n"
         f"            <format attr='title' class='0' field='{R1}' scope='rows' value='' />\n"
         f"            <format attr='display' class='0' field='{R2}' scope='rows' value='false' />\n"
         f"            <format attr='text-format' field='{R1}' scope='rows' value='*0.0%' />\n"
         "            <format attr='tick-color' value='#00000000' />\n          </style-rule>\n"
         "          <style-rule element='header'>\n            <format attr='border-width' data-class='total' value='0' />\n            <format attr='border-style' data-class='total' value='none' />\n          </style-rule>\n"
         f"          <style-rule element='label'>\n            <format attr='text-format' field='{M}' value='*mmm yy' />\n            <format attr='font-size' field='{M}' value='8' />\n            <format attr='color' field='{M}' value='#6b7079' />\n"
         f"            <format attr='font-size' field='{R1}' value='8' />\n            <format attr='color' field='{R1}' value='#6b7079' />\n          </style-rule>\n"
         "          <style-rule element='pane'>\n            <format attr='border-width' data-class='total' scope='rows' value='0' />\n            <format attr='border-style' data-class='total' scope='rows' value='none' />\n          </style-rule>\n"
         "          <style-rule element='table'>\n            <format attr='background-color' value='#00000000' />\n            <format attr='show-null-value-warning' value='false' />\n          </style-rule>\n"
         "          <style-rule element='refline'>\n            <format attr='fill-above' id='refline0' value='#00000000' />\n            <format attr='fill-below' id='refline0' value='#00000000' />\n"
         "            <format attr='stroke-size' id='refline0' value='1' />\n            <format attr='stroke-color' id='refline0' value='#8c8a84' />\n            <format attr='line-pattern-only' id='refline0' value='dashed' />\n            <format attr='line-visibility' id='refline0' value='on' />\n          </style-rule>\n"
         "          <style-rule element='gridline'>\n            <format attr='line-visibility' value='on' />\n            <format attr='line-pattern-only' value='solid' />\n            <format attr='stroke-color' value='#e4e3dd' />\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n          </style-rule>\n"
         "          <style-rule element='zeroline'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
         "          <style-rule element='table-div'>\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n            <format attr='stroke-size' scope='rows' value='0' />\n            <format attr='line-visibility' scope='rows' value='off' />\n          </style-rule>\n"
         "          <style-rule element='header-div'>\n            <format attr='stroke-size' scope='rows' value='0' />\n            <format attr='line-visibility' scope='rows' value='off' />\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n          </style-rule>\n")
TIPW = (f"            <customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
        + tr('#13243a', 'Tableau Semibold', '10', f"<{M}> close: <{R1}>") + NL
        + tr('#5a6171', 'Tableau Book', '9', f"<{D}.[sum:contractors_with_gap:qk]> of <{D}.[sum:contractors_working:qk]> contractors")
        + "              </formatted-text>\n            </customized-tooltip>\n")
tipenc = (f"              <tooltip column='{R1}' />\n              <tooltip column='{D}.[sum:contractors_with_gap:qk]' />\n              <tooltip column='{D}.[sum:contractors_working:qk]' />\n")
lods = f"              <lod column='{RT}' />\n              <lod column='{M}' />\n"
refl = (f"            <reference-line axis-column='{R1}' enable-instant-analytics='false' formula='max' id='refline0' label-type='none' scope='per-pane' tooltip-type='none' value-column='{RT}' z-order='1' />\n")
panes = (f"          <pane id='2' selection-relaxation-option='selection-relaxation-disallow'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
         f"            <mark class='Automatic' />\n            <encodings>\n{lods}{tipenc}            </encodings>\n{refl}{TIPW}"
         "            <style>\n              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='false' />\n                <format attr='mark-transparency' value='255' />\n              </style-rule>\n            </style>\n          </pane>\n"
         f"          <pane id='3' selection-relaxation-option='selection-relaxation-disallow' y-axis-name='{R1}'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
         f"            <mark class='Line' />\n            <encodings>\n{lods}{tipenc}            </encodings>\n{TIPW}"
         "            <style>\n              <style-rule element='mark'>\n                <format attr='mark-color' value='#13233a' />\n                <format attr='mark-transparency' value='255' />\n                <format attr='mark-labels-show' value='false' />\n              </style-rule>\n            </style>\n          </pane>\n"
         f"          <pane id='4' selection-relaxation-option='selection-relaxation-disallow' y-axis-name='{R2}'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
         f"            <mark class='Circle' />\n            <mark-sizing mark-sizing-setting='marks-scaling-off' />\n            <encodings>\n{lods}{tipenc}"
         f"              <text column='{D}.{ilab}' />\n              <color column='{D}.{idot}' />\n            </encodings>\n{TIPW}"
         f"            <customized-label>\n              <formatted-text>\n                <run>&lt;</run>\n                <run>{D}.{ilab}</run>\n                <run>&gt;</run>\n              </formatted-text>\n            </customized-label>\n"
         "            <style>\n              <style-rule element='cell'>\n                <format attr='vertical-align' value='top' />\n                <format attr='text-align' value='auto' />\n              </style-rule>\n"
         "              <style-rule element='datalabel'>\n                <format attr='color-mode' value='match' />\n                <format attr='font-family' value='Tableau Semibold' />\n                <format attr='font-size' value='10' />\n              </style-rule>\n"
         "              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n                <format attr='mark-labels-mode' value='all' />\n                <format attr='size' value='0.6' />\n"
         "                <format attr='has-stroke' value='true' />\n                <format attr='stroke-color' value='#13233a' />\n                <format attr='mark-labels-cull' value='true' />\n                <format attr='mark-transparency' value='255' />\n              </style-rule>\n            </style>\n          </pane>\n")
x = wrap('Timeline', view, style, panes, f'({R1} + {R2})', M, "        <tooltip-style tooltip-mode='sticky' />\n")
SHEETS.append(('Timeline', x, window('Timeline')))
COLORS.append(palette('TL Dot', {'selected above': '#b8401f', 'selected below': '#0e7d5f', 'other': '#ffffff'}))

# ---------------------------------------------------------------- sheets into worksheets / windows, sorted
w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[1] for x in SHEETS) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[2] for x in SHEETS) + s[win_end:]
w0 = s.index('<worksheets>') + len('<worksheets>\n')
w1 = s.index('  </worksheets>')
parts = [(m.group(1), m.group(0)) for m in re.finditer(r"    <worksheet name='([^']*)'>.*?\n    </worksheet>\n", s[w0:w1], re.S)]
assert ''.join(p[1] for p in parts) == s[w0:w1], 'unexpected worksheet layout'
s = s[:w0] + ''.join(b for _, b in sorted(parts, key=lambda p: p[0])) + s[w1:]

# palettes live in the data source's own mark style rule
ds_s = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_e = s.index('</datasource>', ds_s)
m = re.search(r"<style-rule element='mark'>\n", s[ds_s:ds_e])
assert m, 'no mark style rule in the data source'
pos = ds_s + m.end() + s[ds_s + m.end():ds_e].index('</style-rule>')
pos = s.rfind('\n', 0, pos) + 1
s = s[:pos] + ''.join(COLORS) + s[pos:]

# ---------------------------------------------------------------- dashboard zones
a0 = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b0 = s.index('</dashboard>', a0)
d = s[a0:b0]
nid = max(int(i) for i in re.findall(r"<zone [^>]*?\bid='(\d+)'", d)) + 1
STYLE0 = ("<layout-cache type-h='cell' type-w='fixed' />\n<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
          "<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n</zone-style>\n")


def indent(txt, ind):
    return ''.join(ind + l + '\n' for l in txt.strip('\n').split('\n'))


# Card: Timeline: swap the two placeholders (same id and geometry)
for ph, sh in (("Gap rate at each month-end close (placeholder)", 'Timeline Title'), ("Timeline (placeholder)", 'Timeline')):
    m = re.search(r"( *)<zone ([^>]*?)friendly-name='" + re.escape(ph) + r"'([^>]*)>", d)
    assert m, ph
    start = m.start()
    end = d.index('</zone>', start) + len('</zone>')
    attrs = re.sub(r"\s*forceUpdate='true'", '', m.group(2) + m.group(3))
    attrs = re.sub(r"\s*type-v2='\w+'", '', attrs)
    attrs = re.sub(r"\s+", ' ', attrs).strip()
    ind = m.group(1)
    new = f"{ind}<zone {attrs} name='{sh}' show-title='false'>\n" + indent(STYLE0, ind + '  ') + f"{ind}</zone>"
    d = d[:start] + new + d[end:]

# Card: Main: the gap-list pair after Main Panel (id 48)
m = re.search(r"( *)<zone friendly-name='Main Panel'[^>]*>", d)
assert m
ind = m.group(1)
pend = d.index('</zone>', d.index("name='Sankey Native'", m.start()))       # end of Sankey Native
pend = d.index('</zone>', pend + 1) + len('</zone>\n')                           # end of Main Panel
GT, GL = nid, nid + 1
pair = (f"{ind}<zone fixed-size='44' h='5176' id='{GT}' is-fixed='true' name='Gap List Title' show-title='false' w='51715' x='18785' y='93529'>\n" + indent(STYLE0, ind + '  ') + f"{ind}</zone>\n"
        f"{ind}<zone h='28000' id='{GL}' name='Gap List' show-title='false' w='51715' x='18785' y='98705'>\n" + indent(STYLE0, ind + '  ') + f"{ind}</zone>\n")
d = d[:pend] + pair + d[pend:]
nid += 2
# temporary p_ShowList control to test the swap (removed in step 14)
zend = d.index('  </zones>')
SHOWCTL = nid
d = d[:zend] + f"<zone h='5176' id='{SHOWCTL}' mode='compact' param='[Parameters].[Parameter 0725102600000005]' type-v2='paramctrl' w='7400' x='62000' y='13000' />\n" + d[zend:]
nid += 1
s = s[:a0] + d + s[b0:]
ids = {n: int(re.search(rf"<zone [^>]*?\bid='(\d+)'[^>]*name='{n}'", s).group(1)) for n in ('Main Title',)}
MAIN_TITLE = ids['Main Title']
MAIN_PANEL = int(re.search(r"<zone friendly-name='Main Panel'[^>]*?\bid='(\d+)'", s).group(1))

# ---------------------------------------------------------------- datagraph: the two pairs
DASH = '{6548F4FB-B30D-45E2-A1B0-256049E77034}'
dg0 = s.index('<datagraph>')
subg = re.search(r"<default-execution-subgraph-guid value='([^']*)' />", s[dg0:]).group(1)
g = lambda: str(uuid.uuid4())
pairs, nodes, edges = '', '', ''


def value_node(field):
    nid_, fin, vout = g(), g(), g()
    global pairs, nodes
    pairs += f"          <pair execution-subgraph-guid='{subg}' node-guid='{nid_}' />\n"
    nodes += f"        <single-value-field-node fieldname='{field}' fieldname-input-guid='{fin}' node-guid='{nid_}' value-output-guid='{vout}' />\n"
    return vout


def vis_node(zone_id, vout):
    nid_, vin = g(), g()
    global pairs, nodes, edges
    pairs += f"          <pair execution-subgraph-guid='{subg}' node-guid='{nid_}' />\n"
    nodes += f"        <dashboard-zone-visibility-node dashboard-identifier='{DASH}' node-guid='{nid_}' visibility-input-guid='{vin}' zone-id='{zone_id}' />\n"
    edges += f"        <edge from='{vout}' to='{vin}' />\n"


v_list = value_node('[Parameters].[Parameter 0725102600000005]')
vis_node(GT, v_list)
vis_node(GL, v_list)
v_over = value_node(f"{D}.[{CALC['Show Overview'][0].strip('[]')}]")
vis_node(MAIN_TITLE, v_over)
vis_node(MAIN_PANEL, v_over)
p0 = s.index('</node-execution-subgraphs>', dg0)
p0 = s.rfind('\n', 0, p0) + 1
s = s[:p0] + pairs + s[p0:]
dg0 = s.index('<datagraph>')
p1 = s.index('</nodes>', dg0)
s = s[:s.rfind('\n', 0, p1) + 1] + nodes + s[s.rfind('\n', 0, p1) + 1:]
p2 = s.index('</edges>', dg0)
s = s[:s.rfind('\n', 0, p2) + 1] + edges + s[s.rfind('\n', 0, p2) + 1:]

# ---------------------------------------------------------------- viewpoints for the four sheets on the dashboard
wi = s.index("<window class='dashboard' maximized='true' name='CW Reconciliation'")
placed = ['Gap List Title', 'Gap List', 'Timeline Title', 'Timeline']
vend = s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vp = ''.join(f"        <viewpoint name='{n}'>\n          <zoom type='entire-view' />\n        </viewpoint>\n" for n in placed)
s = s[:vend] + vp + s[vend:]
vs, ve = s.index('<viewpoints>', wi) + len('<viewpoints>\n'), s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vparts = re.findall(r"        <viewpoint name='[^']*'>\n          <zoom type='entire-view' />\n        </viewpoint>\n", s[vs:ve])
assert ''.join(vparts) == s[vs:ve], 'unexpected viewpoint layout'
s = s[:vs] + ''.join(sorted(vparts, key=lambda v: re.search(r"name='([^']*)'", v).group(1))) + s[ve:]
open(out, 'w', encoding='utf-8').write(s)
print('sheets', [x[0] for x in SHEETS], 'zones', GT, GL, SHOWCTL, 'hidden Main', MAIN_TITLE, MAIN_PANEL)

# reference-line tooltips need their manifest flag (else error D2E8DA72: 'tooltip-type' not declared)
s = open(out, encoding='utf-8').read()
m0 = s.index('<document-format-change-manifest>')
m1 = s.index('</document-format-change-manifest>')
man = re.findall(r"    <[^>]+ />\n", s[m0:m1])
for f in ('CustomReferenceLineTooltips',):
    if f"<{f} />" not in s[m0:m1]:
        man.append(f"    <{f} />\n")
s = s[:m0] + '<document-format-change-manifest>\n' + ''.join(sorted(man, key=lambda x: x.strip().replace("_.fcp.", "").lower())) + '  ' + s[m1:]
open(out, 'w', encoding='utf-8').write(s)
