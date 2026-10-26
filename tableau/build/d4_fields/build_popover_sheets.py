"""Build doc section 11, stage 2: the popover bodies (year/month grid, tick lists) and the Clear buttons.

  python3 build_popover_sheets.py "after_stage1.twb" "out.twb"          (close Tableau first)

Run build_popovers.py first. This adds the sheets Close Years, Close Grid, Function List, Department List,
Country List, Function Clear, Department Clear, Country Clear and swaps them in for the placeholder zones
(same id and geometry). Clicks still do nothing until the actions (step 14).
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
assert "<worksheet name='Close Grid'>" not in s, 'already built'
assert "<worksheet name='Close Close'>" in s, 'run build_popovers.py first'

NEWCALC = ("      <column caption='Popover Clear Text' datatype='string' name='[Calculation_0725102600000221]' role='dimension' type='nominal'>\n"
           "        <calculation class='tableau' formula='// Popover Clear Text&#10;&quot;Clear all&quot;' />\n      </column>\n")
k = s.index("      <column caption='Close Field Text'")
s = s[:k] + NEWCALC + s[k:]
DSX = s[s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'"):]
DSX = DSX[:DSX.index('</datasource>')]
CALC.clear()
for m in re.finditer(r"      <column caption='([^']*)' datatype='(\w+)' name='(\[Calculation_\d+\])'[^>]*>\n.*?\n      </column>\n", DSX, re.S):
    CALC[m.group(1)] = (m.group(3), m.group(0), m.group(2))
CAP_OF.clear()
CAP_OF.update({v[0]: k2 for k2, v in CALC.items()})

D = f'[{DS}]'
HID = ['Close Panel', 'zzTrue', 'zzFalse']
ONE = [('Is Selected Close', True), ('Is Pop', True)]
SHAPES, COLORS = [], []          # datasource-level encodings


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


def bname(c):
    return nm(c) if c in CALC else c


def is_tc(cap):
    return '<table-calc' in CALC[cap][1]


def tc_nested(cap):
    f = re.search(r"formula='([^']*)'", CALC[cap][1]).group(1)
    return [CAP_OF['[' + d + ']'] for d in re.findall(r"\[(Calculation_\d+)\]", f) if is_tc(CAP_OF['[' + d + ']'])]


def psheet(name, mark, dims, rows=None, cols=None, text=None, color=None, shape=None, filters=ONE, axes=None,
           label=None, size=None, hide_label_of=None, align='left', tooltip='', pads=None):
    """dims: [(caption or sql name, kind)] detail fields. rows/cols: ('min'|'usr'|'tc', caption, kind). axes: {shelf: (min, max, reverse)}."""
    caps = [c for c, _ in dims if c in CALC] + [f[0] for f in filters]
    for sp in [rows] + (cols if isinstance(cols, list) else [cols]):
        if sp:
            caps.append(sp[1])
    for c in (text, color, shape):
        if c and c in CALC:
            caps.append(c)
    caps = list(dict.fromkeys(caps))
    calcs, params, sql = closure(caps)
    sqlnames = [c for c, _ in dims if c not in CALC] + [c for c in (text, color, shape) if c and c not in CALC]
    sql |= set(sqlnames)
    colx = [CALC[c][1].rstrip('\n') for c in sorted(calcs, key=lambda c: CALC[c][0])] + ['      ' + sqlcol(q) for q in sorted(sql)]
    # detail (dimension) instances and their reference names
    dimref = []                                              # (field for table-calc order, instance name)
    insts = []
    for c, kind in dims:
        base = nm(c) if c in CALC else c
        iname = f"[none:{base}:{kind}]"
        insts.append(f"<column-instance column='[{base}]' derivation='None' name='{iname}' pivot='key' type='{'ordinal' if kind == 'ok' else 'nominal'}' />")
        dimref.append((f"{D}.[{base}]", iname))
    for c, val in filters:
        base = nm(c)
        insts.append(f"<column-instance column='[{base}]' derivation='None' name='[none:{base}:nk]' pivot='key' type='nominal' />")
    for extra in (text, color, shape):
        if extra:
            base = bname(extra)
            iname = f"[none:{base}:nk]"
            if not any(i.endswith(f"name='{iname}' pivot='key' type='nominal' />") for i in insts):
                insts.append(f"<column-instance column='[{base}]' derivation='None' name='{iname}' pivot='key' type='nominal' />")
                dimref.append((f"{D}.[{base}]", iname))
    order = ''.join(f"\n                <order field='{f}' />" for f, _ in dimref)

    def shelf(sp):
        if not sp:
            return None
        how, cap, kind = sp
        base = nm(cap)
        if how == 'min':
            iname = f"[min:{base}:qk]"
            insts.append(f"<column-instance column='[{base}]' derivation='Min' name='{iname}' pivot='key' type='quantitative' />")
        elif how == 'usr':
            iname = f"[usr:{base}:qk]"
            insts.append(f"<column-instance column='[{base}]' derivation='User' name='{iname}' pivot='key' type='quantitative' />")
        else:
            q = 'ok' if kind == 'ok' else 'qk'
            iname = f"[usr:{base}:{q}:1]"
            tcx = f"\n              <table-calc ordering-type='Field'>{order}\n              </table-calc>"
            for n2 in dict.fromkeys(tc_nested(cap) + [x for c2 in tc_nested(cap) for x in tc_nested(c2)]):
                tcx += f"\n              <table-calc field='{D}.[{nm(n2)}]' ordering-type='Field'>{order}\n              </table-calc>"
            insts.append(f"<column-instance column='[{base}]' derivation='User' name='{iname}' pivot='key' type='{'ordinal' if kind == 'ok' else 'quantitative'}'>{tcx}\n            </column-instance>")
        return f"{D}.{iname}"

    rows_ref = shelf(rows)
    cols_refs = [shelf(c) for c in (cols if isinstance(cols, list) else [cols])]
    cols_ref = ' / '.join(c for c in cols_refs if c)
    # table-calc column definitions: the nested ones also need their own copy in the dependencies (already via closure)
    flt, slices = '', ''
    for c, val in filters:
        r = f"{D}.[none:{nm(c)}:nk]"
        flt += (f"          <filter class='categorical' column='{r}'>\n            <groupfilter function='member' level='[none:{nm(c)}:nk]' member='true' "
                f"user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n          </filter>\n")
        slices += f"            <column>{r}</column>\n"
    pdep = ''
    if params:
        pdep = ("          <datasource-dependencies datasource='Parameters'>\n" + ''.join(PARAM[p] for p in sorted(params)) + "          </datasource-dependencies>\n")
    ref = lambda c: f"{D}.[none:{bname(c)}:nk]"
    enc = ''
    if shape:
        enc += f"              <shape column='{ref(shape)}' />\n"
    if color:
        enc += f"              <color column='{ref(color)}' />\n"
    if text:
        enc += f"              <text column='{ref(text)}' />\n"
    for f, iname in dimref:
        enc += f"              <lod column='{D}.{iname}' />\n"
    lab = ''
    if label:
        lab = (f"            <customized-label>\n              <formatted-text>\n                <run{label[1]}><![CDATA[<{ref(text)}>]]></run>\n"
               f"              </formatted-text>\n            </customized-label>\n")
    ax = ''
    for shelfref, key, scope in ((rows_ref, 'rows', 'rows'), (cols_refs[-1], 'cols', 'cols')):
        if shelfref and axes and key in axes:
            lo, hi, rev = axes[key]
            ax += (f"            <encoding attr='space' class='0' field='{shelfref}' field-type='quantitative' max='{hi}' min='{lo}' range-type='fixed'"
                   f"{' reverse=' + chr(39) + 'true' + chr(39) if rev else ''} scope='{scope}' type='space' />\n"
                   f"            <format attr='display' class='0' field='{shelfref}' scope='{scope}' value='false' />\n")
    hidelab = ''
    if hide_label_of:
        hidelab = f"          <style-rule element='label'>\n            <format attr='display' field='{hide_label_of}' value='false' />\n          </style-rule>\n"
    zero = ''.join(f"          <style-rule element='{e}'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
                   for e in ('dropline', 'refline', 'zeroline'))
    mk = f"                <format attr='mark-labels-show' value='{'true' if label else 'false'}' />\n                <format attr='mark-labels-cull' value='false' />\n"
    if size:
        mk += f"                <format attr='size' value='{size}' />\n"
    mk += "                <format attr='has-stroke' value='false' />\n"
    if mark == 'Shape':
        mk += "                <format attr='mark-transparency' value='255' />\n"
    tip = "            <customized-tooltip show-buttons='false'>\n              <formatted-text />\n            </customized-tooltip>\n"
    pad = ''
    x = f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='CW Reconciliation' name='{DS}' />
{"            <datasource name='Parameters' />" if params else ''}
          </datasources>
{pdep}          <datasource-dependencies datasource='{DS}'>
{chr(10).join(colx)}
{chr(10).join('            ' + i for i in insts)}
          </datasource-dependencies>
{flt}          <slices>
{slices}          </slices>
          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
{ax}            <format attr='tick-color' value='#00000000' />
            <format attr='stroke-size' value='0' />
            <format attr='line-visibility' value='off' />
          </style-rule>
          <style-rule element='header'>
            <format attr='band-color' scope='rows' value='#00000000' />
            <format attr='border-width' data-class='subtotal' value='0' />
            <format attr='border-style' data-class='subtotal' value='none' />
            <format attr='band-color' scope='cols' value='#00000000' />
          </style-rule>
{hidelab}          <style-rule element='pane'>
            <format attr='band-color' scope='rows' value='#00000000' />
            <format attr='border-width' data-class='subtotal' value='0' />
            <format attr='border-style' data-class='subtotal' value='none' />
            <format attr='band-color' scope='cols' value='#00000000' />
          </style-rule>
          <style-rule element='table'>
            <format attr='background-color' value='#00000000' />
            <format attr='band-size' scope='rows' value='1' />
            <format attr='band-size' scope='cols' value='1' />
          </style-rule>
{zero}          <style-rule element='gridline'>
            <format attr='stroke-size' scope='rows' value='0' />
            <format attr='line-visibility' scope='rows' value='off' />
          </style-rule>
          <style-rule element='table-div'>
            <format attr='stroke-size' scope='rows' value='0' />
            <format attr='line-visibility' scope='rows' value='off' />
            <format attr='stroke-size' scope='cols' value='0' />
            <format attr='line-visibility' scope='cols' value='off' />
          </style-rule>
        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-disallow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
            <encodings>
{enc}            </encodings>
{tip}{lab}            <style>
              <style-rule element='cell'>
                <format attr='text-align' value='{align}' />
                <format attr='vertical-align' value='center' />
              </style-rule>
              <style-rule element='datalabel'>
                <format attr='color-mode' value='auto' />
              </style-rule>
              <style-rule element='mark'>
{mk}              </style-rule>
              <style-rule element='trendline'>
                <format attr='stroke-size' value='0' />
                <format attr='line-visibility' value='off' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows>{rows_ref or ''}</rows>
        <cols>{cols_ref or ''}</cols>
        <tooltip-style tooltip-mode='none' />
      </table>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </worksheet>
"""
    win = f"""    <window class='worksheet' name='{name}'>
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
    return x, win, name


def font(sz, colr, face='Tableau Book'):
    return (f" fontcolor='{colr}'" if colr else '') + f" fontname='{face}' fontsize='{sz}'"


def palette(cap, mapping):
    f = f"[none:{nm(cap)}:nk]"
    e = f"          <encoding attr='color' field='{f}' type='palette'>\n"
    for b, colr in mapping.items():
        e += f"            <map to='{colr}'>\n              <bucket>&quot;{b}&quot;</bucket>\n            </map>\n"
    return e + "          </encoding>\n"


def shapemap(cap, mapping):
    f = f"[none:{nm(cap)}:nk]"
    e = f"          <encoding attr='shape' field='{f}' type='shape'>\n"
    for b in mapping:
        e += f"            <map to='Arcadia D4/{b}.png'>\n              <bucket>&quot;{b}&quot;</bucket>\n            </map>\n"
    return e + "          </encoding>\n"


SH = []
# Close popover: years down, months across
SH.append(psheet('Close Years', 'Text', [('Close Year Label', 'nk')] + [(h, 'nk') for h in HID], rows=('min', 'Close Slot', 'qk'),
                 text='Close Year Label', filters=[('Close Grid Row', True)], axes={'rows': (0, 12, True)}, align='left',
                 label=('Close Year Label', font(9, '#8fa0b8'))))
SH.append(psheet('Close Grid', 'Text', [('Close Pick', 'ok'), ('Close Cell', 'nk'), ('Close State', 'nk')] + [(h, 'nk') for h in HID],
                 rows=('min', 'Close Slot', 'qk'), cols=('min', 'Close Col', 'qk'), text='Close Cell', color='Close State',
                 filters=[('Close Grid Row', True)], axes={'rows': (0, 12, True), 'cols': (0, 24, False)}, align='center',
                 label=('Close Cell', font(10, '#b8c0cc'))))
COLORS.append(palette('Close State', {'current': '#ffffff', 'on': '#b8c0cc'}))
# tick lists
for nmx, sql, st, shp, tog, lrow, ax, ncols in (
        ('Function', 'function_name', 'Function State', 'Function Tick Shape', 'Function Toggle', 'Function List Row', 16, 1),
        ('Department', 'department_name', 'Department State', 'Department Tick Shape', 'Department Toggle', 'Department List Row', 22, 3),
        ('Country', 'country_name', 'Country State', 'Country Tick Shape', 'Country Toggle', 'Country List Row', 16, 3)):
    dims = [(sql, 'nk'), (tog, 'nk'), (st, 'nk'), (shp, 'nk')] + [(h, 'nk') for h in HID]
    if ncols == 1:
        sh = psheet(f'{nmx} List', 'Shape', dims, rows=('tc', 'Function Slot', 'qk'), cols=('usr', 'Tick X', 'qk'), shape=shp, color=st,
                    text=sql, filters=[(lrow, True)], axes={'rows': (0, ax, True), 'cols': (0, 10, False)}, size='1.5',
                    label=(sql, font(10, None)))
    else:
        sh = psheet(f'{nmx} List', 'Shape', dims, rows=('tc', 'Pick Row', 'qk'),
                    cols=[('tc', 'Pick Col', 'ok'), ('usr', 'Tick X', 'qk')], shape=shp, color=st, text=sql, filters=[(lrow, True)],
                    axes={'rows': (0, ax, True), 'cols': (0, 10, False)}, size='1.5', label=(sql, font(9, None)),
                    hide_label_of=f"{D}.[usr:{nm('Pick Col')}:ok:1]")
    SH.append(sh)
    if nmx == 'Function':
        SHAPES.append(shapemap(shp, ['d4_tick_on', 'd4_tick_off']))
        COLORS.append(palette(st, {'on': '#ffffff', 'off': '#b8c0cc'}))
    elif nmx == 'Department':
        SHAPES.append(shapemap(shp, ['d4_tick_on', 'd4_tick_off', 'd4_tick_dim']))
        COLORS.append(palette(st, {'on': '#ffffff', 'off': '#b8c0cc', 'dim': '#56657e'}))
    else:
        SHAPES.append(shapemap(shp, ['d4_tick_on', 'd4_tick_off']))
        COLORS.append(palette(st, {'on': '#ffffff', 'off': '#b8c0cc'}))
SH = [x for x in SH if x]
print('lists built:', [x[2] for x in SH])

# Clear buttons: one Text mark, "Clear all"
for nmx in ('Function', 'Department', 'Country'):
    SH.append(psheet(f'{nmx} Clear', 'Text', [('Empty Text', 'nk')] + [(h, 'nk') for h in HID], text='Popover Clear Text',
                     filters=ONE, align='right', label=('Popover Clear Text', font(9, '#b8c0cc'))))

names = [x[2] for x in SH]
w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[0] for x in SH) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[1] for x in SH) + s[win_end:]
w0 = s.index('<worksheets>') + len('<worksheets>\n')
w1 = s.index('  </worksheets>')
parts = [(m.group(1), m.group(0)) for m in re.finditer(r"    <worksheet name='([^']*)'>.*?\n    </worksheet>\n", s[w0:w1], re.S)]
assert ''.join(p[1] for p in parts) == s[w0:w1], 'unexpected worksheet layout'
s = s[:w0] + ''.join(b for _, b in sorted(parts, key=lambda p: p[0])) + s[w1:]

# palettes and shape maps live in the data source's own mark style rule
enc_all = ''.join(SHAPES) + ''.join(COLORS)
ds_s = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_e = s.index('</datasource>', ds_s)
m = re.search(r"<style-rule element='mark'>\n", s[ds_s:ds_e])
assert m, 'no mark style rule in the data source'
pos = ds_s + m.end()
s = s[:pos] + enc_all + s[pos:]

# swap placeholders for sheets
a = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b = s.index('</dashboard>', a)
d = s[a:b]
PLACE = {'Close Years (placeholder)': 'Close Years', 'Close Grid (placeholder)': 'Close Grid',
         'Function List (placeholder)': 'Function List', 'Department List (placeholder)': 'Department List',
         'Country List (placeholder)': 'Country List', 'Function Popover Clear (placeholder)': 'Function Clear',
         'Department Popover Clear (placeholder)': 'Department Clear', 'Country Popover Clear (placeholder)': 'Country Clear'}
PAD = {'Close Years': "<format attr='padding-top' value='8' />\n<format attr='padding-bottom' value='8' />\n<format attr='padding-left' value='16' />\n",
       'Close Grid': "<format attr='padding-top' value='8' />\n<format attr='padding-bottom' value='8' />\n<format attr='padding-right' value='16' />\n",
       'Function List': "<format attr='padding-top' value='8' />\n<format attr='padding-bottom' value='8' />\n<format attr='padding-left' value='16' />\n",
       'Department List': "<format attr='padding-top' value='8' />\n<format attr='padding-bottom' value='8' />\n<format attr='padding-left' value='16' />\n<format attr='padding-right' value='16' />\n",
       'Country List': "<format attr='padding-top' value='8' />\n<format attr='padding-bottom' value='8' />\n<format attr='padding-left' value='16' />\n<format attr='padding-right' value='16' />\n"}
for ph, sh in PLACE.items():
    m = re.search(r"<zone ([^>]*?)friendly-name='" + re.escape(ph) + r"'([^>]*)>", d)
    assert m, ph
    start = m.start()
    end = d.index('</zone>', start) + len('</zone>')
    attrs = re.sub(r"\s*forceUpdate='true'", '', m.group(1) + m.group(2))
    attrs = re.sub(r"\s*type-v2='\w+'", '', attrs)
    attrs = re.sub(r"\s+", ' ', attrs).strip()
    new = (f"<zone {attrs} name='{sh}' show-title='false'>\n<layout-cache type-h='cell' type-w='fixed' />\n<zone-style>\n"
           f"<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n<format attr='border-width' value='0' />\n"
           f"<format attr='margin' value='0' />\n{PAD.get(sh, '')}</zone-style>\n</zone>")
    d = d[:start] + new + d[end:]
s = s[:a] + d + s[b:]

# the dashboard window needs a viewpoint for every sheet placed on it, kept in name order
wi = s.index("<window class='dashboard' maximized='true' name='CW Reconciliation'")
vend = s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vp = ''.join(f"        <viewpoint name='{sh}'>\n          <zoom type='entire-view' />\n        </viewpoint>\n" for sh in PLACE.values())
s = s[:vend] + vp + s[vend:]
vs, ve = s.index('<viewpoints>', wi) + len('<viewpoints>\n'), s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vparts = re.findall(r"        <viewpoint name='[^']*'>\n          <zoom type='entire-view' />\n        </viewpoint>\n", s[vs:ve])
assert ''.join(vparts) == s[vs:ve], 'unexpected viewpoint layout'
s = s[:vs] + ''.join(sorted(vparts, key=lambda v: re.search(r"name='([^']*)'", v).group(1))) + s[ve:]
open(out, 'w', encoding='utf-8').write(s)
print('sheets', len(SH), 'zones swapped', len(PLACE))
