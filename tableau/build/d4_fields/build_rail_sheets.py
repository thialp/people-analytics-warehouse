"""Build doc section 10 (step 7): the rail control sheets, written into a workbook and placed on the dashboard.

  python3 build_rail_sheets.py "in.twb" "out.twb"          (close Tableau first)

Sheets (one Shape mark each, Dashboard #2's pattern): Close Field, Function Field, Department Field, Country Field,
Show Toggle (two marks), Reset, Info Button, Rail As Of (text). Each replaces the placeholder zone of the same name
made by build_rail.py (same id, same geometry). Shapes come from the palette `Arcadia D4`. The three test parameter
controls stay until the actions exist (step 14), because the sheets only draw the controls; clicks need the actions.
"""
import re
import sys
import uuid

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
DS = re.search(r"<datasource caption='CW Reconciliation' inline='true' name='(federated\.[a-z0-9]+)'", s).group(1)
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_end = s.index('</datasource>', ds_start)
DSX = s[ds_start:ds_end]
PAR_start = s.index("<datasource hasconnection='false' inline='true' name='Parameters'")
PARX = s[PAR_start:s.index('</datasource>', PAR_start)]
for n in ('Close Field', 'Show Toggle', 'Rail As Of'):
    assert f"<worksheet name='{n}'>" not in s, 'already built'


def esc(t):
    return t.replace('&', '&amp;').replace("'", '&apos;').replace('<', '&lt;').replace('>', '&gt;')


CALC = {}                                           # caption -> (name, xml)
for m in re.finditer(r"      <column caption='([^']*)' datatype='(\w+)' name='(\[Calculation_\d+\])'[^>]*>\n.*?\n      </column>\n", DSX, re.S):
    CALC[m.group(1)] = (m.group(3), m.group(0), m.group(2))
PARAM = {}
for m in re.finditer(r"      <column caption='([^']*)'[^>]*name='(\[Parameter \d+\])'[^>]*>\n.*?\n      </column>\n", PARX, re.S):
    PARAM[m.group(2)] = m.group(0)
CAP_OF = {v[0]: k for k, v in CALC.items()}


def unesc_formula(x):
    return x


def closure(captions):
    """All calcs, parameters and SQL columns the given calcs need (transitively)."""
    calcs, params, sql = [], set(), set()
    todo = list(captions)
    seen = set()
    while todo:
        c = todo.pop()
        if c in seen:
            continue
        seen.add(c)
        calcs.append(c)
        f = re.search(r"formula='([^']*)'", CALC[c][1]).group(1)
        for d in re.findall(r"\[(Calculation_\d+)\]", f):
            todo.append(CAP_OF['[' + d + ']'])
        for p in re.findall(r"\[Parameters\]\.\[(Parameter \d+)\]", f):
            params.add('[' + p + ']')
        for q in re.findall(r"(?<![\w.])\[([a-z][a-z_0-9]*)\]", f):
            sql.add(q)
    return calcs, params, sql


def sqlcol(name):
    m = re.search(r"<column (?:aggregation='\w+' )?datatype='\w+' name='\[" + name + r"\]' role='\w+' type='\w+' />", s)
    assert m, 'no declaration of SQL column ' + name
    return m.group(0)


def inst(cap, kind='nk'):
    nm = CALC[cap][0].strip('[]')
    typ = 'ordinal' if kind == 'ok' else 'nominal'
    return (f"<column-instance column='[{nm}]' derivation='None' name='[none:{nm}:{kind}]' pivot='key' type='{typ}' />",
            f"[{DS}].[none:{nm}:{kind}]", f"[none:{nm}:{kind}]")


def sheet_xml(name, lods, text=(), shape=None, filters=(), cols=None, manual=None, hide_col=False,
              shape_default=None, size='11.27', tooltip=None, label=None, label_align='center', mark='Shape',
              bg='#00000000', worksheet_font=None):
    """lods/text/filters: captions. shape: (caption, {bucket: file}) for a shape field. cols: caption."""
    used = list(dict.fromkeys(list(lods) + list(text) + [f[0] for f in filters] + ([cols] if cols else []) + ([shape[0]] if shape else [])))
    kinds = {c: ('ok' if CALC[c][2] == 'date' else 'nk') for c in used}
    calcs, params, sql = closure(used)
    colx = []
    for c in sorted(calcs, key=lambda c: CALC[c][0]):
        colx.append(CALC[c][1].rstrip('\n'))
    for q in sorted(sql):
        x = sqlcol(q)
        if x:
            colx.append('      ' + x)
    insts = [inst(c, kinds[c])[0] for c in used]
    dep = [f"<datasource-dependencies datasource='{DS}'>"] + ['        ' + c.lstrip() if False else c for c in colx] + ['            ' + i for i in insts] + ['          </datasource-dependencies>']
    pdep = ''
    if params:
        pdep = ("          <datasource-dependencies datasource='Parameters'>\n"
                + ''.join(PARAM[p] for p in sorted(params)) + "          </datasource-dependencies>\n")
    ref = {c: inst(c, kinds[c]) for c in used}
    flt = ''
    for c, val in filters:
        r = ref[c]
        flt += (f"          <filter class='categorical' column='{r[1]}'>\n"
                f"            <groupfilter function='member' level='{r[2]}' member='{'true' if val else 'false'}' user:ui-domain='database' "
                f"user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n          </filter>\n")
    srt = ''
    if manual:
        srt = (f"          <manual-sort column='{ref[cols][1]}' direction='ASC'>\n            <dictionary>\n"
               + ''.join(f"              <bucket>&quot;{b}&quot;</bucket>\n" for b in manual) + "            </dictionary>\n          </manual-sort>\n")
    slices = ''.join(f"            <column>{ref[c][1]}</column>\n" for c, _ in filters) + (f"            <column>{ref[cols][1]}</column>\n" if cols else '')
    enc = ''
    if shape:
        enc += f"              <shape column='{ref[shape[0]][1]}' />\n"
    for c in lods:
        enc += f"              <lod column='{ref[c][1]}' />\n"
    for c in text:
        enc += f"              <text column='{ref[c][1]}' />\n"
    shape_enc = ''
    if shape:
        shape_enc = f"          <encoding attr='shape' field='{ref[shape[0]][1]}' palette='Arcadia D4' type='shape'>\n"
        for b, fnm in shape[1].items():
            shape_enc += f"            <map to='Arcadia D4/{fnm}.png'>\n              <bucket>&quot;{b}&quot;</bucket>\n            </map>\n"
        shape_enc += "          </encoding>\n"
    tip = ''
    if tooltip:
        tip = (f"            <customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
               f"                <run fontcolor='#5a6170' fontsize='9'>{esc(tooltip)}</run>\n              </formatted-text>\n            </customized-tooltip>\n")
    lab = ''
    if label:
        runs = ''
        for i, (cap, font, colr, sz) in enumerate(label):
            if i:
                runs += "                <run>Æ&#10;</run>\n"
            runs += (f"                <run fontcolor='{colr}' fontname='{font}' fontsize='{sz}'><![CDATA[<{ref[cap][1]}>]]></run>\n")
        lab = f"            <customized-label>\n              <formatted-text>\n{runs}              </formatted-text>\n            </customized-label>\n"
    mark_style = f"                <format attr='mark-labels-show' value='{'true' if label else 'false'}' />\n                <format attr='mark-labels-cull' value='false' />\n"
    if mark == 'Shape':
        mark_style += f"                <format attr='size' value='{size}' />\n"
        if shape_default:
            mark_style += f"                <format attr='shape' value='Arcadia D4/{shape_default}.png' />\n"
        mark_style += "                <format attr='mark-color' value='#1d3150' />\n                <format attr='has-stroke' value='false' />\n                <format attr='mark-transparency' value='255' />\n"
    colhide = ''
    if hide_col:
        colhide = (f"          <style-rule element='label'>\n            <format attr='display' field='{ref[cols][1]}' value='false' />\n          </style-rule>\n")
    wsrule = ''
    if hide_col:
        wsrule = "          <style-rule element='worksheet'>\n            <format attr='display-field-labels' scope='cols' value='false' />\n          </style-rule>\n"
    zero = ("          <style-rule element='dropline'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
            "          <style-rule element='refline'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n"
            "          <style-rule element='zeroline'>\n            <format attr='stroke-size' value='0' />\n            <format attr='line-visibility' value='off' />\n          </style-rule>\n")
    x = f"""    <worksheet name='{name}'>
      <table>
        <view>
          <datasources>
            <datasource caption='CW Reconciliation' name='{DS}' />
{"            <datasource name='Parameters' />" if params else ''}
          </datasources>
{pdep}          {chr(10).join(dep)}
{flt}{srt}          <slices>
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
            <format attr='background-color' value='{bg}' />
          </style-rule>
{colhide}          <style-rule element='pane'>
            <format attr='band-color' scope='rows' value='#00000000' />
            <format attr='border-width' data-class='subtotal' value='0' />
            <format attr='border-style' data-class='subtotal' value='none' />
            <format attr='background-color' value='{bg}' />
          </style-rule>
          <style-rule element='table'>
            <format attr='band-size' scope='rows' value='1' />
            <format attr='background-color' value='{bg}' />
          </style-rule>
{wsrule}{zero}        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-disallow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='{mark}' />
            <mark-sizing mark-sizing-setting='marks-scaling-off' />
            <encodings>
{enc}            </encodings>
{tip}{lab}            <style>
              <style-rule element='cell'>
                <format attr='vertical-align' value='center' />
                <format attr='text-align' value='{label_align}' />
              </style-rule>
              <style-rule element='mark'>
{mark_style}              </style-rule>
              <style-rule element='trendline'>
                <format attr='stroke-size' value='0' />
                <format attr='line-visibility' value='off' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows />
        <cols>{ref[cols][1] if cols else ''}</cols>
        <tooltip-style tooltip-mode='sticky' />
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
    return x, win, shape_enc.replace(f"field='{ref[shape[0]][1]}'", f"field='{ref[shape[0]][2]}'") if shape else ''


ONE = [('Is Selected Close', True), ('Is Pop', True)]
HID = ['zzFalse', 'zzTrue', 'Close Panel']
NAVY, LIGHT = '#13233A', '#E4E9F0'
SHEETS = []
SHEETS.append(sheet_xml('Close Field', ['Toggle Close Panel'] + HID, text=['Close Field Text'], filters=ONE,
                        shape_default='d4_field_capsule', tooltip='Choose the close',
                        label=[('Close Field Text', 'Tableau Semibold', NAVY, '9')]))
for nm, t, tog in (('Function', 'Function Field Text', 'Toggle Function Panel'),
                   ('Department', 'Department Field Text', 'Toggle Department Panel'),
                   ('Country', 'Country Field Text', 'Toggle Country Panel')):
    SHEETS.append(sheet_xml(f'{nm} Field', [tog] + HID, text=[t], filters=ONE, shape_default='d4_field_capsule_dark',
                            tooltip=f'Choose {nm.lower()}' + ('s' if nm != 'Country' else ' or countries') if False else f'Choose {nm.lower()}',
                            label=[(t, 'Tableau Medium', LIGHT, '9')], label_align='left'))
SHEETS.append(sheet_xml('Show Toggle', ['Show Pick'] + HID, filters=[('Toggle Row', True)], cols='Toggle Option',
                        manual=['Overview', 'Gap list'], hide_col=True, size='5.65',
                        shape=('Show Shape', {'d4_show_overview_on': 'd4_show_overview_on', 'd4_show_overview_off': 'd4_show_overview_off',
                                              'd4_show_gaplist_on': 'd4_show_gaplist_on', 'd4_show_gaplist_off': 'd4_show_gaplist_off'}),
                        shape_default='d4_show_overview_on', tooltip='Overview or gap list'))
SHEETS.append(sheet_xml('Reset', ['Default Close', 'Empty Text', 'zzFalse', 'Close Panel', 'zzTrue'], filters=ONE,
                        shape_default='d4_reset', tooltip='Reset to default view'))
SHEETS.append(sheet_xml('Info Button', ['Toggle Info'] + HID, filters=ONE, size='3',
                        shape=('Info Shape', {'d2_info_open': 'd2_info_open', 'd2_info_close': 'd2_info_close'}),
                        shape_default='d2_info_open', tooltip='What this page shows'))
SHEETS.append(sheet_xml('Rail As Of', ['zzFalse', 'zzTrue'], text=['Rail As Of Line 1', 'Rail As Of Line 2'], filters=ONE, mark='Automatic',
                        label=[('Rail As Of Line 1', 'Tableau Semibold', LIGHT, '9'), ('Rail As Of Line 2', 'Tableau Book', '#B9C3D1', '9')],
                        label_align='left'))

# worksheets and windows
w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[0] for x in SHEETS) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[1] for x in SHEETS) + s[win_end:]

# shape maps live in the data source's own style rule
enc_all = ''.join(x[2] for x in SHEETS)
ds_s = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_e = s.index('</datasource>', ds_s)
seg = s[ds_s:ds_e]
m = re.search(r"<style-rule element='mark'>\n", seg)
if m:
    pos = ds_s + m.end()
    s = s[:pos] + enc_all + s[pos:]
elif '<style>' in seg:
    pos = ds_s + seg.index('<style>') + len('<style>\n')
    s = s[:pos] + "        <style-rule element='mark'>\n" + enc_all + "        </style-rule>\n" + s[pos:]
else:
    lay = ds_s + seg.index('<layout ')
    lay = s.index('/>', lay) + 2
    s = s[:lay] + "\n      <style>\n        <style-rule element='mark'>\n" + enc_all + "        </style-rule>\n      </style>" + s[lay:]

# dashboard zones: swap each placeholder for its sheet, same id and geometry
a = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b = s.index('</dashboard>', a)
d = s[a:b]
PLACE = {'Close field (placeholder)': 'Close Field', 'Function field (placeholder)': 'Function Field',
         'Department field (placeholder)': 'Department Field', 'Country field (placeholder)': 'Country Field',
         'Show toggle (placeholder)': 'Show Toggle', 'Reset (placeholder)': 'Reset',
         'Info button (placeholder)': 'Info Button', 'Rail as-of (placeholder)': 'Rail As Of'}
NONE_STYLE = ("<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
              "<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n</zone-style>")
TOGGLE_STYLE = ("<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
                "<format attr='border-width' value='0' />\n<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='16' />\n"
                "<format attr='margin' value='0' />\n<format attr='background-color' value='#1b2d45' />\n</zone-style>")
n_done = 0
for ph, sh in PLACE.items():
    m = re.search(r"<zone ([^>]*?)friendly-name='" + re.escape(ph) + r"'([^>]*)>", d)
    assert m, ph
    start = m.start()
    # end of this zone: first </zone> after its own style (placeholders have no child zones)
    end = d.index('</zone>', start) + len('</zone>')
    attrs = (m.group(1) + m.group(2))
    attrs = re.sub(r"\s*forceUpdate='true'", '', attrs)
    attrs = re.sub(r"\s*type-v2='\w+'", '', attrs)
    attrs = re.sub(r"\s+", ' ', attrs).strip()
    style = TOGGLE_STYLE if sh == 'Show Toggle' else NONE_STYLE
    new = f"<zone {attrs} name='{sh}' show-title='false'>\n<layout-cache type-h='cell' type-w='fixed' />\n{style}\n</zone>"
    d = d[:start] + new + d[end:]
    n_done += 1
s = s[:a] + d + s[b:]
open(out, 'w', encoding='utf-8').write(s)
print('sheets', len(SHEETS), 'zones swapped', n_done)
