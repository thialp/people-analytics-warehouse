"""Build doc section 15 (step 12): the ticket card (Ticket Rows, Ticket Bands, Ticket Dots, Tickets Title).

  python3 build_ticket_card.py "saved.twb" "out.twb"          (close Tableau first)

Starts from the Tableau-saved workbook after steps 10 and 11. Reuses the sheet helpers of build_gap_timeline.py.
Colour: the sheets use `Sk Colour` (already palette-mapped: Bridgeway, Keystone, System feed), which returns the place
for a ticket row. Also tidies the export hint of the gap list (shorter text, wider title).
"""
import os, re, sys, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
g_src = open(os.path.join(HERE, 'build_gap_timeline.py'), encoding='utf-8').read()
pre = g_src[g_src.index('HERE = '):g_src.index("title_sheet('Gap List Title'")]
pre = pre.replace("""assert "<worksheet name='Gap List'>" not in s, 'already built'""", """assert "<worksheet name='Ticket Dots'>" not in s, 'already built'""")
pre = pre.replace("""assert "<worksheet name='KPI Cards'>" in s, 'run build_kpi_cards.py first'""", '')
pre = pre.replace("_n = [320]", "_n = [340]")
pre = re.sub(r"newcalc\('Timeline Title'.*\n", "newcalc('Tickets Title', 'string', 'dimension', 'nominal', '// Tickets Title\\\\n\"Open tickets by where they are aligned\"')\n"
             "newcalc('Ticket Row X', 'real', 'measure', 'quantitative', '// Ticket Row X (squares sit at the left of the label column)\\\\n0.05')\n", pre, count=1)
pre = re.sub(r"NEW_RATE2 = newcalc\(.*\n", '', pre, count=1)
exec(compile(pre, 'helpers2', 'exec'), globals())

title_sheet('Tickets Title', 'Tickets Title', 'Tickets Subtitle')

EM = ' '
AX = lambda f, lo, hi, scope, rev=False: (f"            <encoding attr='space' class='0' field='{f}' field-type='quantitative' max='{hi}' min='{lo}' range-type='fixed'"
                                          f"{' reverse=' + chr(39) + 'true' + chr(39) if rev else ''} scope='{scope}' type='space' />\n")
HIDE = lambda f, scope: f"            <format attr='display' class='0' field='{f}' scope='{scope}' value='false' />\n"
FLAT = ("          <style-rule element='table'>\n            <format attr='background-color' value='#00000000' />\n            <format attr='show-null-value-warning' value='false' />\n          </style-rule>\n"
        "          <style-rule element='gridline'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
        "          <style-rule element='zeroline'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
        "          <style-rule element='table-div'>\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n            <format attr='stroke-size' scope='rows' value='0' />\n            <format attr='line-visibility' scope='rows' value='off' />\n          </style-rule>\n"
        "          <style-rule element='header-div'>\n            <format attr='stroke-size' scope='rows' value='0' />\n            <format attr='line-visibility' scope='rows' value='off' />\n            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n          </style-rule>\n")
SEL = "selection-relaxation-option='selection-relaxation-disallow'"


def qmin(cap):
    b = nm(cap)
    return f'[min:{b}:qk]', f"<column-instance column='[{b}]' derivation='Min' name='[min:{b}:qk]' pivot='key' type='quantitative' />"


def tr2(colr, face, size, txt):
    return f"                <run fontcolor='{colr}' fontname='{face}' fontsize='{size}'><![CDATA[{txt}]]></run>\n"


NL = "                <run>Æ&#10;</run>\n"
colour_i, colour_x = tinst('Sk Colour')
PLACE = f'{D}.[none:place:nk]'
PLACE_X = "<column-instance column='[place]' derivation='None' name='[none:place:nk]' pivot='key' type='nominal' />"

# ---------------------------------------------------------------- Ticket Rows: a square and a three-line label per place
caps = ['Ticket Card Row', 'Ticket Row Y', 'Ticket Row X', 'Place Sub', 'Place Open', 'Sk Colour']
params, pdep, colx, insts, flt, slices = dims_deps(caps, ['place'], [], ['Ticket Card Row'])
yi, yx = qmin('Ticket Row Y')
xi, xx = qmin('Ticket Row X')
oi, ox = qinst('Place Open')
si, sx = tinst('Place Sub')
insts += [PLACE_X, yx, xx, ox, sx, colour_x]
view = pdep + dep_xml(colx, insts) + flt + f"          <slices>\n{slices}          </slices>\n"
Y, X, O, S = f'{D}.{yi}', f'{D}.{xi}', f'{D}.{oi}', f'{D}.{si}'
style = (f"          <style-rule element='axis'>\n{AX(X, 0, 1, 'cols')}{AX(Y, 0, 3, 'rows')}{HIDE(X, 'cols')}{HIDE(Y, 'rows')}            <format attr='tick-color' value='#00000000' />\n          </style-rule>\n" + FLAT)
lab = (tr2('#2b2f36', 'Tableau Semibold', '10', f"{EM}<{PLACE}>") + NL + tr2('#5a6171', 'Tableau Book', '9', f"{EM}<{S}>") + NL
       + tr2('#2b2f36', 'Tableau Semibold', '9', f"{EM}<{O}> open"))
pane = (f"          <pane id='2' {SEL}>\n            <view>\n              <breakdown value='auto' />\n            </view>\n            <mark class='Square' />\n"
        f"            <encodings>\n              <lod column='{PLACE}' />\n              <text column='{O}' />\n              <text column='{S}' />\n              <text column='{PLACE}' />\n"
        f"              <color column='{D}.{colour_i}' />\n            </encodings>\n"
        f"            <customized-label>\n              <formatted-text>\n{lab}              </formatted-text>\n            </customized-label>\n"
        "            <style>\n              <style-rule element='cell'>\n                <format attr='text-align' value='right' />\n                <format attr='vertical-align' value='center' />\n              </style-rule>\n"
        "              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n                <format attr='mark-labels-mode' value='all' />\n                <format attr='size' value='0.2' />\n                <format attr='mark-labels-cull' value='false' />\n              </style-rule>\n            </style>\n          </pane>\n")
SHEETS.append(('Ticket Rows', wrap('Ticket Rows', view, style, pane, Y, X, ''), window('Ticket Rows')))

# ---------------------------------------------------------------- Ticket Bands: three age labels over the dot grid
caps = ['Ticket Card Row', 'Band X', 'Band Open', 'Sk Colour']
params, pdep, colx, insts, flt, slices = dims_deps(caps, ['age_band'], [], ['Ticket Card Row'])
bxi, bxx = qmin('Band X')
boi, box = qinst('Band Open')
BAND = f'{D}.[none:age_band:nk]'
insts += ["<column-instance column='[age_band]' derivation='None' name='[none:age_band:nk]' pivot='key' type='nominal' />", bxx, box]
view = pdep + dep_xml(colx, insts) + flt + f"          <slices>\n{slices}          </slices>\n"
BX, BO = f'{D}.{bxi}', f'{D}.{boi}'
style = (f"          <style-rule element='axis'>\n{AX(BX, 0, 3, 'cols')}{HIDE(BX, 'cols')}            <format attr='tick-color' value='#00000000' />\n          </style-rule>\n" + FLAT)
lab = tr2('#6b7079', 'Tableau Semibold', '9', f"<{BAND}>") + NL + tr2('#2b2f36', 'Tableau Book', '9', f"<{BO}> open")
pane = (f"          <pane id='2' {SEL}>\n            <view>\n              <breakdown value='auto' />\n            </view>\n            <mark class='Text' />\n"
        f"            <encodings>\n              <lod column='{BAND}' />\n              <text column='{BO}' />\n              <text column='{BAND}' />\n            </encodings>\n"
        f"            <customized-label>\n              <formatted-text>\n{lab}              </formatted-text>\n            </customized-label>\n"
        "            <style>\n              <style-rule element='cell'>\n                <format attr='text-align' value='center' />\n                <format attr='vertical-align' value='center' />\n              </style-rule>\n"
        "              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n                <format attr='mark-labels-cull' value='false' />\n              </style-rule>\n            </style>\n          </pane>\n")
SHEETS.append(('Ticket Bands', wrap('Ticket Bands', view, style, pane, '', BX, ''), window('Ticket Bands')))

# ---------------------------------------------------------------- Ticket Dots: one circle per ticket, packed by the warehouse
TIPS = ['ticket_title', 'current_group', 'age_days', 'ticket_state', 'link_tier']
caps = ['Ticket Card Row', 'Sk Colour']
params, pdep, colx, insts, flt, slices = dims_deps(caps, ['dot_x', 'dot_y', 'ticket_number'] + TIPS, [], ['Ticket Card Row'])
insts += [colour_x, "<column-instance column='[dot_x]' derivation='Avg' name='[avg:dot_x:qk]' pivot='key' type='quantitative' />",
          "<column-instance column='[dot_y]' derivation='Avg' name='[avg:dot_y:qk]' pivot='key' type='quantitative' />",
          "<column-instance column='[ticket_number]' derivation='None' name='[none:ticket_number:nk]' pivot='key' type='nominal' />"]
insts += [f"<column-instance column='[{q}]' derivation='Attribute' name='[attr:{q}:{'qk' if q == 'age_days' else 'nk'}]' pivot='key' type='{'quantitative' if q == 'age_days' else 'nominal'}' />" for q in TIPS]
view = pdep + dep_xml(colx, insts) + flt + f"          <slices>\n{slices}          </slices>\n"
DX, DY, TN = f'{D}.[avg:dot_x:qk]', f'{D}.[avg:dot_y:qk]', f'{D}.[none:ticket_number:nk]'
A = lambda q: f"{D}.[attr:{q}:{'qk' if q == 'age_days' else 'nk'}]"
style = (f"          <style-rule element='axis'>\n{AX(DX, 0, 3, 'cols')}{AX(DY, 0, 3, 'rows')}{HIDE(DX, 'cols')}{HIDE(DY, 'rows')}            <format attr='tick-color' value='#00000000' />\n          </style-rule>\n"
         + FLAT + "          <style-rule element='refline'>\n"
         + ''.join(f"            <format attr='{a_}' id='refline{n}' value='{v}' />\n" for n in range(4) for a_, v in (('fill-above', '#00000000'), ('fill-below', '#00000000'), ('stroke-size', '1'), ('stroke-color', '#e4e3dd'), ('line-pattern-only', 'solid'), ('line-visibility', 'on')))
         + "          </style-rule>\n")
refl = ''.join(f"            <reference-line axis-column='{ax}' enable-instant-analytics='false' formula='constant' id='refline{n}' label-type='none' scope='per-pane' tooltip-type='none' value='{v}' z-order='1' />\n"
               for n, (ax, v) in enumerate([(DX, 1), (DX, 2), (DY, 1), (DY, 2)]))
tip = ("            <customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
       + tr2('#13243a', 'Tableau Semibold', '10', f"<{A('ticket_title')}>") + NL
       + tr2('#5a6171', 'Tableau Book', '9', f"<{TN}>") + NL
       + tr2('#13243a', 'Tableau Book', '9', f"<{A('current_group')}> · <{A('age_days')}> days open · <{A('ticket_state')}>") + NL
       + tr2('#5a6171', 'Tableau Book', '9', f"Linked by <{A('link_tier')}>")
       + "              </formatted-text>\n            </customized-tooltip>\n")
pane = (f"          <pane id='2' {SEL}>\n            <view>\n              <breakdown value='auto' />\n            </view>\n            <mark class='Circle' />\n"
        f"            <encodings>\n              <lod column='{TN}' />\n              <color column='{D}.{colour_i}' />\n"
        + ''.join(f"              <tooltip column='{A(q)}' />\n" for q in TIPS) + f"            </encodings>\n{refl}{tip}"
        "            <style>\n              <style-rule element='mark'>\n                <format attr='size' value='0.12' />\n                <format attr='mark-labels-show' value='false' />\n                <format attr='mark-transparency' value='230' />\n              </style-rule>\n            </style>\n          </pane>\n")
SHEETS.append(('Ticket Dots', wrap('Ticket Dots', view, style, pane, DY, DX, "        <tooltip-style tooltip-mode='sticky' />\n"), window('Ticket Dots')))

# ---------------------------------------------------------------- into the workbook (as build_gap_timeline.py)
w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[1] for x in SHEETS) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[2] for x in SHEETS) + s[win_end:]
w0 = s.index('<worksheets>') + len('<worksheets>\n')
w1 = s.index('  </worksheets>')
parts = [(m.group(1), m.group(0)) for m in re.finditer(r"    <worksheet name='([^']*)'>.*?\n    </worksheet>\n", s[w0:w1], re.S)]
assert ''.join(p[1] for p in parts) == s[w0:w1], 'unexpected worksheet layout'
s = s[:w0] + ''.join(b for _, b in sorted(parts, key=lambda p: p[0])) + s[w1:]

# ---------------------------------------------------------------- dashboard
a0 = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b0 = s.index('</dashboard>', a0)
d = s[a0:b0]
nid = max(int(i) for i in re.findall(r"<zone [^>]*?\bid='(\d+)'", d)) + 1
STYLE0 = ("<layout-cache type-h='cell' type-w='fixed' />\n<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
          "<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n</zone-style>\n")
ZS = "<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n</zone-style>\n"


def indent(txt, ind):
    return ''.join(ind + l + '\n' for l in txt.strip('\n').split('\n'))


c0 = d.index("<zone friendly-name='Card: Tickets'")
c1 = d.index('</zone>', d.index("friendly-name='Ticket body (placeholder)'")) + len('</zone>\n')   # the end of the second placeholder
ph0 = d.index("<zone fixed-size='44' forceUpdate='true' friendly-name='Open tickets by where they are aligned (placeholder)'", c0)
ind = ' ' * 10
BX0, BY0 = 74071, 65529
BW, BH = 22572, 28000
LW = 6857                       # 96 px
CH = 3294                       # 28 px
u = lambda **k: ' '.join(f"{a_}='{b_}'" for a_, b_ in k.items())
zid = lambda: (lambda n: (globals().__setitem__('nid', n + 1), n)[1])(nid)
z_title, z_body, z_left, z_corner, z_rows, z_right, z_bands, z_dots = [zid() for _ in range(8)]
new = (f"{ind}<zone fixed-size='44' h='5176' id='{z_title}' is-fixed='true' name='Tickets Title' show-title='false' w='{BW}' x='{BX0}' y='60353'>\n" + indent(STYLE0, ind + '  ') + f"{ind}</zone>\n"
       f"{ind}<zone friendly-name='Ticket Body' h='{BH}' id='{z_body}' param='horz' type-v2='layout-flow' w='{BW}' x='{BX0}' y='{BY0}'>\n"
       f"{ind}  <zone fixed-size='96' friendly-name='Ticket Labels' h='{BH}' id='{z_left}' is-fixed='true' param='vert' type-v2='layout-flow' w='{LW}' x='{BX0}' y='{BY0}'>\n"
       f"{ind}    <zone fixed-size='28' h='{CH}' id='{z_corner}' is-fixed='true' type-v2='empty' w='{LW}' x='{BX0}' y='{BY0}'>\n" + indent(ZS, ind + '      ') + f"{ind}    </zone>\n"
       f"{ind}    <zone h='{BH - CH}' id='{z_rows}' name='Ticket Rows' show-title='false' w='{LW}' x='{BX0}' y='{BY0 + CH}'>\n" + indent(STYLE0, ind + '      ') + f"{ind}    </zone>\n"
       f"{ind}  </zone>\n"
       f"{ind}  <zone friendly-name='Ticket Grid' h='{BH}' id='{z_right}' param='vert' type-v2='layout-flow' w='{BW - LW}' x='{BX0 + LW}' y='{BY0}'>\n"
       f"{ind}    <zone fixed-size='28' h='{CH}' id='{z_bands}' is-fixed='true' name='Ticket Bands' show-title='false' w='{BW - LW}' x='{BX0 + LW}' y='{BY0}'>\n" + indent(STYLE0, ind + '      ') + f"{ind}    </zone>\n"
       f"{ind}    <zone h='{BH - CH}' id='{z_dots}' name='Ticket Dots' show-title='false' w='{BW - LW}' x='{BX0 + LW}' y='{BY0 + CH}'>\n" + indent(STYLE0, ind + '      ') + f"{ind}    </zone>\n"
       f"{ind}  </zone>\n{ind}</zone>\n")
d = d[:ph0] + new + d[c1:]
# gap list: shorter export hint, wider title
HINT_W = 90
HX = 955 - HINT_W
d, n1 = re.subn(r"(<zone fixed-size=')\d+(' forceUpdate='true' h='\d+' id='294' is-fixed='true' type-v2='text' w=')\d+(' x=')\d+(')", rf"\g<1>{HINT_W}\g<2>{round(HINT_W*100000/1400)}\g<3>{round(HX*100000/1400)}\g<4>", d, count=1)
d, n2 = re.subn(r"Click the icon to export to Excel", 'Export to Excel:', d)
d, n3 = re.subn(r"(<zone h='\d+' id='279' name='Gap List Title' show-title='false' w=')\d+(')", rf"\g<1>{round((HX - 246 - 17 - 6)*100000/1400)}\g<2>", d, count=1)
assert n1 == 1 and n2 >= 1 and n3 == 1, (n1, n2, n3)
s = s[:a0] + d + s[b0:]
# viewpoints
wi = s.index("<window class='dashboard' maximized='true' name='CW Reconciliation'")
placed = ['Tickets Title', 'Ticket Rows', 'Ticket Bands', 'Ticket Dots']
vend = s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
s = s[:vend] + ''.join(f"        <viewpoint name='{n}'>\n          <zoom type='entire-view' />\n        </viewpoint>\n" for n in placed) + s[vend:]
vs, ve = s.index('<viewpoints>', wi) + len('<viewpoints>\n'), s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vparts = re.findall(r"        <viewpoint name='[^']*'>\n          <zoom type='[a-z-]+' />\n        </viewpoint>\n", s[vs:ve])
assert ''.join(vparts) == s[vs:ve], 'unexpected viewpoint layout'
s = s[:vs] + ''.join(sorted(vparts, key=lambda v: re.search(r"name='([^']*)'", v).group(1))) + s[ve:]
open(out, 'w', encoding='utf-8').write(s)
print('ticket card zones', z_title, z_body, z_left, z_corner, z_rows, z_right, z_bands, z_dots)
