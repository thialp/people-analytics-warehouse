"""Build doc section 12 (step 9): the KPI band (sheet `KPI Cards`) and the five hover covers (`KPI Hover 1`-`5`).

  python3 build_kpi_cards.py "after_step8.twb" "out.twb"          (close Tableau first)

KPI Cards is Dashboard #2's trick: a map-style sheet whose marks are points placed with the 16 kpi_ parameters, one
text layer per card title, value and note. Those formulas are copied from #2 (the parameter ids are the same), the
text comes from this workbook's `KPI n Title / Value / Unit / Note / Known / Low`. The hover covers are one-cell
sheets with a transparent Square and the card's tooltip (`KPI n Title`, `KPI n Tip`).
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
assert "<worksheet name='KPI Cards'>" not in s, 'already built'
assert "<worksheet name='Country List'>" in s, 'run the step 8 builders first'

# ---------------------------------------------------------------- new calcs
PID = {k: '[Parameters].[Parameter ' + v + ']' for k, v in dict(
    Scale='0215008197136384', SheetW='0215008197435393', SheetH='0215008197500930', FitX='0215008197574659',
    FitY='0215008197656580', ShiftX='0215008197734405', ShiftY='0215008197779462', GridLeft='0215008197849095',
    GridTop='0215008197922824', CardW='0215008197980169', GapX='0215008198123531', PadX='0215008198180876',
    TitleDY='0215008198262797', ValueDY='0215008198381582', SubDY='0215008198512655').items()}
for v in PID.values():
    assert v[len('[Parameters].'):] in s, 'missing parameter ' + v

NEW = []        # (caption, datatype, role, type, formula)
_n = [230]


def newcalc(cap, datatype, role, typ, formula):
    cid = f'Calculation_0725102600000{_n[0]}'
    assert cid not in s, cid
    _n[0] += 1
    NEW.append((cap, cid, datatype, role, typ, formula))
    return cid


def esc(f):
    return f.replace('&', '&amp;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '&#10;')


def lat(dy):
    return f"-({PID['GridTop']} + {PID[dy]} + {PID['ShiftY']} - {PID['SheetH']} / 2) * {PID['Scale']} * {PID['FitY']}"


def lon(i):
    return (f"({PID['GridLeft']} + {i} * ({PID['CardW']} + {PID['GapX']}) + {PID['PadX']} + {PID['ShiftX']} - {PID['SheetW']} / 2)"
            f" * {PID['Scale']} * {PID['FitX']}")


for cap, dy in (('kpi_lat Title', 'TitleDY'), ('kpi_lat Value', 'ValueDY'), ('kpi_lat Sub', 'SubDY')):
    newcalc(cap, 'real', 'measure', 'quantitative', f'// {cap}\n' + lat(dy))
for i in range(5):
    newcalc(f'kpi_lon C{i + 1}', 'real', 'measure', 'quantitative', f'// kpi_lon C{i + 1} (i = {i})\n' + lon(i))
# the calc ids are needed for the points
tmpid = {c[0]: c[1] for c in NEW}
for kind, latcap in (('Title', 'kpi_lat Title'), ('Value', 'kpi_lat Value'), ('Note', 'kpi_lat Sub')):
    for n in range(1, 6):
        newcalc(f'kpi_pt {kind} {n}', 'spatial', 'measure', 'nominal',
                f'// kpi_pt {kind} {n}\nMAKEPOINT([{tmpid[latcap]}], [{tmpid[f"kpi_lon C{n}"]}])')
newcalc('kpi_Corner TL', 'spatial', 'measure', 'nominal',
        f"// kpi_Corner TL\nMAKEPOINT({PID['SheetH']} / 2 * {PID['Scale']}, -{PID['SheetW']} / 2 * {PID['Scale']})")
newcalc('kpi_Corner BR', 'spatial', 'measure', 'nominal',
        f"// kpi_Corner BR\nMAKEPOINT(-{PID['SheetH']} / 2 * {PID['Scale']}, {PID['SheetW']} / 2 * {PID['Scale']})")
newcalc('Hover Cell', 'string', 'dimension', 'nominal', '// Hover Cell\n"."')

block = ''
for cap, cid, dt, role, typ, f in NEW:
    block += (f"      <column caption='{cap}' datatype='{dt}' name='[{cid}]' role='{role}' type='{typ}'>\n"
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
    """(instance name, column-instance xml) for a string calc used as text"""
    base = nm(cap)
    if role_of(cap) == 'measure':
        return f'[usr:{base}:nk]', f"<column-instance column='[{base}]' derivation='User' name='[usr:{base}:nk]' pivot='key' type='nominal' />"
    return f'[none:{base}:nk]', f"<column-instance column='[{base}]' derivation='None' name='[none:{base}:nk]' pivot='key' type='nominal' />"


def deps(caps, extra_inst, filters):
    calcs, params, sql = closure(list(dict.fromkeys(caps)))
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
    dep = (f"          <datasource-dependencies datasource='{DS}'>\n{chr(10).join(colx)}\n"
           f"{chr(10).join('            ' + i for i in insts)}\n          </datasource-dependencies>\n")
    return params, pdep, dep, flt, slices


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


# ---------------------------------------------------------------- KPI Cards
LATG, LONG_ = f'{D}.[Latitude (generated)]', f'{D}.[Longitude (generated)]'
SEL = 'Is Selected Close'
text_caps = []
for n in range(1, 6):
    for part in ('Title', 'Value', 'Unit', 'Note'):
        c = f'KPI {n} {part}'
        if c in CALC:
            text_caps.append(c)
text_caps += ['KPI 2 Known', 'KPI 2 Low']
pt_caps = [f'kpi_pt {kd} {n}' for n in range(1, 6) for kd in ('Title', 'Value', 'Note')] + ['kpi_Corner TL', 'kpi_Corner BR']
insts = [tinst(c)[1] for c in text_caps]
insts += [f"<column-instance column='[{nm(c)}]' derivation='Collect' name='[clct:{nm(c)}:nk]' pivot='key' type='nominal' />" for c in pt_caps]
params, pdep, dep, flt, slices = deps(text_caps + pt_caps + [SEL], insts, [SEL])

FONT = {'title': ("Tableau Book", '9', '#5a6170'), 'note': ("Tableau Book", '9', '#5a6170'), 'value': ("Tableau Bold", '20', '#13223a')}


def run(face, size, colr, field_inst=None, lead=''):
    txt = f"{lead}<{D}.{field_inst}>"
    return f"                <run fontcolor='{colr}' fontname='{face}' fontsize='{size}'><![CDATA[{txt}]]></run>\n"


def pane(pid, title, text_cap_list, ptcap, kind, valcolor='#13223a'):
    clct = f"<lod column='{D}.[clct:{nm(ptcap)}:nk]' />"
    if text_cap_list is None:
        enc, lab, dl = '', '', ''
    else:
        enc = ''.join(f"<text column='{D}.{tinst(c)[0]}' />\n" for c in text_cap_list)
        if kind == 'value':
            runs = ''
            u = [c for c in text_cap_list[1:]]
            runs += run('Tableau Bold', '20', valcolor, tinst(text_cap_list[0])[0])
            for c in u:
                if c.endswith('Known'):
                    runs += run('Tableau Semibold', '9', '#b8401f', tinst(c)[0], lead='  ')
                elif c.endswith('Low'):
                    runs += run('Tableau Semibold', '9', '#0e7d5f', tinst(c)[0])
                else:
                    runs += run('Tableau Book', '10', '#5a6170', tinst(c)[0], lead='  ')
            lab = f"<customized-label>\n<formatted-text>\n{runs}</formatted-text>\n</customized-label>\n"
            dl = ("<style-rule element='datalabel'>\n<format attr='color-mode' value='user' />\n"
                  f"<format attr='font-family' value='Tableau Bold' />\n<format attr='font-size' value='20' />\n<format attr='color' value='{valcolor}' />\n</style-rule>\n")
        else:
            lab = ''
            face, size, colr = FONT[kind]
            dl = ("<style-rule element='datalabel'>\n<format attr='color-mode' value='user' />\n"
                  f"<format attr='font-family' value='{face}' />\n<format attr='font-size' value='{size}' />\n<format attr='color' value='{colr}' />\n</style-rule>\n")
    cell = ("<style-rule element='cell'>\n<format attr='vertical-align' value='center' />\n<format attr='text-align' value='left' />\n</style-rule>\n"
            if text_cap_list is not None else '')
    labshow = "<format attr='mark-labels-show' value='true' />\n<format attr='mark-labels-cull' value='true' />\n" if text_cap_list is not None else ''
    inert = " inert='true'" if text_cap_list is not None else ''
    return (f"          <pane generated-title='{title}' id='{pid}'{inert} selection-relaxation-option='selection-relaxation-allow'>\n"
            f"<view>\n<breakdown value='auto' />\n</view>\n<mark class='Circle' />\n<mark-sizing mark-sizing-setting='marks-scaling-off' />\n"
            f"<encodings>\n{enc}{clct}\n</encodings>\n{lab}<style>\n{cell}{dl}<style-rule element='mark'>\n"
            f"<format attr='size' value='0.0099999997764825821' />\n{labshow}<format attr='mark-transparency' value='0' />\n</style-rule>\n</style>\n</pane>\n")


IDS = {('Title', 1): 5, ('Value', 1): 4, ('Note', 1): 6, ('Title', 2): 7, ('Value', 2): 8, ('Note', 2): 9, ('Title', 3): 11,
       ('Value', 3): 10, ('Note', 3): 12, ('Title', 4): 13, ('Value', 4): 14, ('Note', 4): 15, ('Title', 5): 16, ('Value', 5): 17, ('Note', 5): 18}
panes = ("          <pane id='1' selection-relaxation-option='selection-relaxation-allow'>\n<view>\n<breakdown value='auto' />\n</view>\n<mark class='Circle' />\n</pane>\n")
panes += pane(21, 'kpi_Corner TL', None, 'kpi_Corner TL', 'x') + pane(20, 'kpi_Corner BR', None, 'kpi_Corner BR', 'x')
for n in (5, 4, 3, 2, 1):
    for kd in ('Note', 'Value', 'Title'):
        cap = f'kpi_pt {kd} {n}'
        if kd == 'Title':
            tl, kind = [f'KPI {n} Title'], 'title'
        elif kd == 'Note':
            tl, kind = [f'KPI {n} Note'], 'note'
        else:
            tl = [f'KPI {n} Value'] + (['KPI 2 Known', 'KPI 2 Low'] if n == 2 else ([f'KPI {n} Unit'] if f'KPI {n} Unit' in CALC else []))
            kind = 'value'
        panes += pane(IDS[(kd, n)], cap, tl, cap, kind, valcolor='#712b13' if n == 4 else '#13223a')
# D2 lists the panes in this order: corners, then notes/values/titles from card 5 down (ids 3 and 1 swap places per card, kept as generated)

kpi = f"""    <worksheet name='KPI Cards'>
      <table>
        <view>
          <datasources>
            <datasource caption='CW Reconciliation' name='{DS}' />
            <datasource name='Parameters' />
          </datasources>
          <mapsources>
            <mapsource name='' />
          </mapsources>
{pdep}{dep}{flt}          <slices>
{slices}          </slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
            <format attr='display' class='0' field='{LATG}' scope='rows' value='false' />
            <format attr='display' class='0' field='{LONG_}' scope='cols' value='false' />
            <format attr='stroke-size' value='0' />
            <format attr='line-visibility' value='off' />
            <format attr='tick-color' value='#00000000' />
          </style-rule>
          <style-rule element='header'>
            <format attr='border-width' data-class='total' value='0' />
            <format attr='border-style' data-class='total' value='none' />
          </style-rule>
          <style-rule element='pane'>
            <format attr='border-width' data-class='total' value='0' />
            <format attr='border-style' data-class='total' value='none' />
          </style-rule>
          <style-rule element='table'>
            <format attr='background-color' value='#00000000' />
          </style-rule>
{zero_rules()}          <style-rule element='gridline'>
            <format attr='stroke-size' scope='rows' value='0' />
            <format attr='line-visibility' scope='rows' value='off' />
            <format attr='stroke-size' scope='cols' value='0' />
            <format attr='line-visibility' scope='cols' value='off' />
          </style-rule>
          <style-rule element='map'>
            <format attr='washout' value='0' />
          </style-rule>
        </style>
        <panes customization-axis='layer'>
{panes}        </panes>
        <rows>{LATG}</rows>
        <cols>{LONG_}</cols>
        <tooltip-style tooltip-mode='none' />
      </table>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </worksheet>
"""
SHEETS = [('KPI Cards', kpi, window('KPI Cards'))]

# ---------------------------------------------------------------- KPI Hover 1-5
HC = 'Hover Cell'
for n in range(1, 6):
    ti, tix = tinst(f'KPI {n} Title')
    pi, pix = tinst(f'KPI {n} Tip')
    hbase = nm(HC)
    hinst = f"<column-instance column='[{hbase}]' derivation='None' name='[none:{hbase}:nk]' pivot='key' type='nominal' />"
    params, pdep, dep, flt, slices = deps([HC, f'KPI {n} Title', f'KPI {n} Tip', SEL], [hinst, tix, pix], [SEL])
    href = f'{D}.[none:{hbase}:nk]'
    tip = (f"            <customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
           f"                <run fontcolor='#13223a' fontname='Tableau Semibold' fontsize='10'><![CDATA[<{D}.{ti}>]]></run>\n"
           f"                <run>Æ&#10;</run>\n"
           f"                <run fontcolor='#4a5a73' fontname='Tableau Book' fontsize='9'><![CDATA[<{D}.{pi}>]]></run>\n"
           f"              </formatted-text>\n            </customized-tooltip>\n")
    x = f"""    <worksheet name='KPI Hover {n}'>
      <table>
        <view>
          <datasources>
            <datasource caption='CW Reconciliation' name='{DS}' />
            <datasource name='Parameters' />
          </datasources>
{pdep}{dep}{flt}          <slices>
{slices}          </slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
            <format attr='tick-color' value='#00000000' />
          </style-rule>
          <style-rule element='header'>
            <format attr='band-color' scope='rows' value='#00000000' />
            <format attr='border-width' data-class='subtotal' value='0' />
            <format attr='border-style' data-class='subtotal' value='none' />
          </style-rule>
          <style-rule element='label'>
            <format attr='display' field='{href}' value='false' />
          </style-rule>
          <style-rule element='pane'>
            <format attr='band-color' scope='rows' value='#00000000' />
            <format attr='border-width' data-class='subtotal' value='0' />
            <format attr='border-style' data-class='subtotal' value='none' />
          </style-rule>
          <style-rule element='table'>
            <format attr='background-color' value='#00000000' />
            <format attr='band-size' scope='rows' value='1' />
          </style-rule>
{zero_rules()}          <style-rule element='table-div'>
            <format attr='stroke-size' scope='rows' value='0' />
            <format attr='line-visibility' scope='rows' value='off' />
          </style-rule>
        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-disallow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Square' />
            <mark-sizing mark-sizing-setting='marks-scaling-off' />
            <encodings>
              <lod column='{href}' />
              <tooltip column='{D}.{ti}' />
              <tooltip column='{D}.{pi}' />
            </encodings>
{tip}            <style>
              <style-rule element='mark'>
                <format attr='size' value='14.547999382019043' />
                <format attr='mark-transparency' value='0' />
                <format attr='has-stroke' value='false' />
              </style-rule>
              <style-rule element='trendline'>
                <format attr='stroke-size' value='0' />
                <format attr='line-visibility' value='off' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows>{href}</rows>
        <cols>{href}</cols>
      </table>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </worksheet>
"""
    SHEETS.append((f'KPI Hover {n}', x, window(f'KPI Hover {n}')))

# ---------------------------------------------------------------- put the sheets in, sorted
w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[1] for x in SHEETS) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[2] for x in SHEETS) + s[win_end:]
w0 = s.index('<worksheets>') + len('<worksheets>\n')
w1 = s.index('  </worksheets>')
parts = [(m.group(1), m.group(0)) for m in re.finditer(r"    <worksheet name='([^']*)'>.*?\n    </worksheet>\n", s[w0:w1], re.S)]
assert ''.join(p[1] for p in parts) == s[w0:w1], 'unexpected worksheet layout'
s = s[:w0] + ''.join(b for _, b in sorted(parts, key=lambda p: p[0])) + s[w1:]

# ---------------------------------------------------------------- dashboard zones: right after the KPI band image
a = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b = s.index('</dashboard>', a)
d = s[a:b]
nid = max(int(i) for i in re.findall(r"<zone [^>]*?\bid='(\d+)'", d)) + 1
m = re.search(r"( *)<zone friendly-name='KPI band image'[^>]*/>\n", d)
assert m, 'KPI band image zone not found'
ind = m.group(1)


def px(v, total):
    return round(v * 100000 / total)


def zone(zid, name, x, y, w, h):
    inner = ("<layout-cache type-h='cell' type-w='fixed' />\n<zone-style>\n<format attr='border-color' value='#000000' />\n"
             "<format attr='border-style' value='none' />\n<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n</zone-style>\n")
    inner = ''.join(ind + '  ' + l + '\n' for l in inner.strip('\n').split('\n'))
    return (f"{ind}<zone h='{px(h, 850)}' id='{zid}' name='{name}' show-title='false' w='{px(w, 1400)}' x='{px(x, 1400)}' y='{px(y, 850)}'>\n"
            f"{inner}{ind}</zone>\n")


new = zone(nid, 'KPI Cards', 0, 76, 1400, 110)
for i in range(5):
    new += zone(nid + 1 + i, f'KPI Hover {i + 1}', 246 + 228 * i, 88, 212, 86)
d = d[:m.end()] + new + d[m.end():]
s = s[:a] + d + s[b:]

# the dashboard window needs a viewpoint for every sheet placed on it, kept in name order
wi = s.index("<window class='dashboard' maximized='true' name='CW Reconciliation'")
vend = s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vp = ''.join(f"        <viewpoint name='{n}'>\n          <zoom type='entire-view' />\n        </viewpoint>\n" for n, _, _ in SHEETS)
s = s[:vend] + vp + s[vend:]
vs, ve = s.index('<viewpoints>', wi) + len('<viewpoints>\n'), s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vparts = re.findall(r"        <viewpoint name='[^']*'>\n          <zoom type='entire-view' />\n        </viewpoint>\n", s[vs:ve])
assert ''.join(vparts) == s[vs:ve], 'unexpected viewpoint layout'
s = s[:vs] + ''.join(sorted(vparts, key=lambda v: re.search(r"name='([^']*)'", v).group(1))) + s[ve:]
open(out, 'w', encoding='utf-8').write(s)
print('sheets', [x[0] for x in SHEETS], 'zones from id', nid, 'new calcs', len(NEW))

# map layers need their manifest flags (else error D2E8DA72: 'customization-axis', 'generated-title', 'inert' not declared)
s = open(out, encoding='utf-8').read()
m0 = s.index('<document-format-change-manifest>')
m1 = s.index('</document-format-change-manifest>')
man = re.findall(r"    <[^>]+ />\n", s[m0:m1])
for f in ('Layers', 'LayerControlWidget', 'MapboxVectorStylesAndLayers', 'IndividualControlFormatting', 'PatternedLineMarks'):
    if f"<{f} />" not in s[m0:m1]:
        man.append(f"    <{f} />\n")
s = s[:m0] + '<document-format-change-manifest>\n' + ''.join(sorted(man, key=lambda x: x.strip().replace("_.fcp.", "").lower())) + '  ' + s[m1:]
open(out, 'w', encoding='utf-8').write(s)
