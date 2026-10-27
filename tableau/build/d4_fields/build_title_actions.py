"""Build doc sections 16 and 17 (steps 13 and 14): page title, load note, and the actions.

  python3 build_title_actions.py "saved.twb" "out.twb"          (close Tableau first)

- Page Title sheet (replaces the placeholder), Load Note sheet in a floating pill (visible only when a load failed)
- zzTrue / zzFalse added to the title sheets so they can be deselected
- parameter actions (popovers, picks, resets, view toggle, info) and the deselect actions
Left for the cleanup pass once the clicks are verified: the test parameter controls (ids 59, 77, 78, 260-264, 281).
"""
import os, re, sys, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
g_src = open(os.path.join(HERE, 'build_gap_timeline.py'), encoding='utf-8').read()
pre = g_src[g_src.index('HERE = '):g_src.index("title_sheet('Gap List Title'")]
pre = pre.replace("""assert "<worksheet name='Gap List'>" not in s, 'already built'""", """assert "<worksheet name='Page Title'>" not in s, 'already built'""")
pre = pre.replace("""assert "<worksheet name='KPI Cards'>" in s, 'run build_kpi_cards.py first'""", '')
pre = pre.replace("_n = [320]", "_n = [350]")
pre = re.sub(r"newcalc\('Timeline Title'.*\n", "newcalc('Page Title Text', 'string', 'dimension', 'nominal', '// Page Title Text\\\\n\"Contingent Workforce Reconciliation\"')\n", pre, count=1)
pre = re.sub(r"NEW_RATE2 = newcalc\(.*\n", '', pre, count=1)
exec(compile(pre, 'helpers3', 'exec'), globals())

# ---------------------------------------------------------------- Page Title (Bold 18 / Book 10)
title_sheet('Page Title', 'Page Title Text', 'Page Subtitle')
name, x, win = SHEETS[-1]
x = x.replace("fontname='Tableau Semibold' fontsize='12'", "fontname='Tableau Bold' fontsize='18'").replace("<run fontcolor='#5a6171' fontsize='9'>", "<run fontcolor='#5a6171' fontsize='10'>")
SHEETS[-1] = (name, x, win)

# ---------------------------------------------------------------- Load Note (one centred line)
li, lx = tinst('Load Note')
params, pdep, colx, insts, flt, slices = dims_deps(['Load Note'], [], [lx], [])
view = pdep + dep_xml(colx, insts)
style = ("          <style-rule element='table'>\n            <format attr='background-color' value='#00000000' />\n          </style-rule>\n" + zero_rules())
pane = (f"          <pane selection-relaxation-option='selection-relaxation-allow'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
        f"            <mark class='Automatic' />\n            <encodings>\n              <text column='{D}.{li}' />\n            </encodings>\n"
        f"            <customized-label>\n              <formatted-text>\n                <run fontcolor='#633806' fontname='Tableau Semibold' fontsize='9'><![CDATA[<{D}.{li}>]]></run>\n              </formatted-text>\n            </customized-label>\n"
        "            <style>\n              <style-rule element='cell'>\n                <format attr='text-align' value='center' />\n                <format attr='vertical-align' value='center' />\n              </style-rule>\n"
        "              <style-rule element='mark'>\n                <format attr='mark-labels-show' value='true' />\n                <format attr='mark-labels-cull' value='false' />\n              </style-rule>\n            </style>\n          </pane>\n")
SHEETS.append(('Load Note', wrap('Load Note', view, style, pane, '', ''), window('Load Note')))

# ---------------------------------------------------------------- into the workbook
w_end = s.index('  </worksheets>')
s = s[:w_end] + ''.join(x[1] for x in SHEETS) + s[w_end:]
win_end = s.rindex('  </windows>')
s = s[:win_end] + ''.join(x[2] for x in SHEETS) + s[win_end:]

# zzTrue / zzFalse on the title sheets
ZT, ZF = nm('zzTrue'), nm('zzFalse')


def add_zz(sheet):
    global s
    i = s.index(f"<worksheet name='{sheet}'>")
    j = s.index('</worksheet>', i)
    w = s[i:j]
    if ZT in w:
        return
    k = w.index(f"<datasource-dependencies datasource='{DS}'>")
    k = w.index('\n', k) + 1
    w = w[:k] + CALC['zzTrue'][1] + CALC['zzFalse'][1] + w[k:]
    e = w.index('</datasource-dependencies>', k)
    e = w.rindex('\n', 0, e) + 1
    inst = ''.join(f"            <column-instance column='[{c}]' derivation='None' name='[none:{c}:nk]' pivot='key' type='nominal' />\n" for c in (ZT, ZF))
    w = w[:e] + inst + w[e:]
    p = w.index('<encodings>') + len('<encodings>\n')
    w = w[:p] + ''.join(f"              <lod column='{D}.[none:{c}:nk]' />\n" for c in (ZT, ZF)) + w[p:]
    s = s[:i] + w + s[j:]


for sh in ('Page Title', 'Main Title', 'Gap List Title', 'Timeline Title', 'Tickets Title'):
    add_zz(sh)

w0 = s.index('<worksheets>') + len('<worksheets>\n')
w1 = s.index('  </worksheets>')
parts = [(m.group(1), m.group(0)) for m in re.finditer(r"    <worksheet name='([^']*)'>.*?\n    </worksheet>\n", s[w0:w1], re.S)]
assert ''.join(p[1] for p in parts) == s[w0:w1], 'unexpected worksheet layout'
s = s[:w0] + ''.join(b for _, b in sorted(parts, key=lambda p: p[0])) + s[w1:]

# ---------------------------------------------------------------- dashboard zones
a0 = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b0 = s.index('</dashboard>', a0)
d = s[a0:b0]
nid = max(int(i) for i in re.findall(r"<zone [^>]*?\bid='(\d+)'", d)) + 1
STYLE0 = ("<layout-cache type-h='cell' type-w='fixed' />\n<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
          "<format attr='border-width' value='0' />\n<format attr='margin' value='0' />\n</zone-style>\n")


def indent(txt, ind):
    return ''.join(ind + l + '\n' for l in txt.strip('\n').split('\n'))


# the page title placeholder (first tree only)
m = re.search(r"( *)<zone ([^>]*?)friendly-name='Page title \(placeholder\)'([^>]*)>", d)
assert m
start = m.start()
end = d.index('</zone>', start) + len('</zone>')
attrs = re.sub(r"\s*forceUpdate='true'", '', m.group(2) + m.group(3))
attrs = re.sub(r"\s*type-v2='\w+'", '', attrs)
attrs = re.sub(r"\s+", ' ', attrs).strip()
ind = m.group(1)
d = d[:start] + f"{ind}<zone {attrs} name='Page Title' show-title='false'>\n" + indent(STYLE0, ind + '  ') + f"{ind}</zone>" + d[end:]
# the load note pill (floating container + sheet)
LN_C, LN_S = nid, nid + 1
nid += 2
pill = (f"<zone friendly-name='Load note' h='3294' id='{LN_C}' param='vert' type-v2='layout-flow' w='22857' x='75000' y='3529'>\n"
        f"<zone h='3294' id='{LN_S}' name='Load Note' show-title='false' w='22857' x='75000' y='3529'>\n" + STYLE0 + "</zone>\n"
        "<zone-style>\n<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n<format attr='border-width' value='0' />\n"
        "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='14' />\n<format attr='padding' value='0' />\n<format attr='background-color' value='#faeedb' />\n</zone-style>\n</zone>\n")
zend = d.index('  </zones>')
d = d[:zend] + indent(pill, '        ') + d[zend:]
s = s[:a0] + d + s[b0:]

# ---------------------------------------------------------------- datagraph: the pill follows Show Load Note
DASH = '{6548F4FB-B30D-45E2-A1B0-256049E77034}'
dg0 = s.index('<datagraph>')
subg = re.search(r"<default-execution-subgraph-guid value='([^']*)' />", s[dg0:]).group(1)
nidg, fin, vout, vnid, vin = (str(uuid.uuid4()) for _ in range(5))
fld = f"{D}.[{nm('Show Load Note')}]"
pairs = (f"          <pair execution-subgraph-guid='{subg}' node-guid='{nidg}' />\n          <pair execution-subgraph-guid='{subg}' node-guid='{vnid}' />\n")
nodes = (f"        <single-value-field-node fieldname='{fld}' fieldname-input-guid='{fin}' node-guid='{nidg}' value-output-guid='{vout}' />\n"
         f"        <dashboard-zone-visibility-node dashboard-identifier='{DASH}' node-guid='{vnid}' visibility-input-guid='{vin}' zone-id='{LN_C}' />\n")
edges = f"        <edge from='{vout}' to='{vin}' />\n"
for tag, ins in (('</node-execution-subgraphs>', pairs), ('</nodes>', nodes), ('</edges>', edges)):
    p = s.index(tag, dg0)
    p = s.rfind('\n', 0, p) + 1
    s = s[:p] + ins + s[p:]
    dg0 = s.index('<datagraph>')

# ---------------------------------------------------------------- actions
PARAM_ID = {'p_Close': ('Parameter 0725102600000001', 'd:2026-06-30'), 'p_Functions': ('Parameter 0725102600000002', 's:LROOT:'),
            'p_Departments': ('Parameter 0725102600000003', 's:LROOT:'), 'p_Countries': ('Parameter 0725102600000004', 's:LROOT:'),
            'p_ShowList': ('Parameter 0725102600000005', 'b:false'), 'p_CloseOpen': ('Parameter 0725102600000006', 'b:false'),
            'p_FunctionOpen': ('Parameter 0725102600000007', 'b:false'), 'p_DepartmentOpen': ('Parameter 0725102600000008', 'b:false'),
            'p_CountryOpen': ('Parameter 0725102600000009', 'b:false'), 'p_InfoOpen': ('Parameter 0725102600000010', 'b:false')}
OPENS = ['p_CloseOpen', 'p_FunctionOpen', 'p_DepartmentOpen', 'p_CountryOpen', 'p_InfoOpen']
ACTS = []   # (caption, source sheet, source calc caption, target param)


def A_(cap, sheet, field, param):
    ACTS.append((cap, sheet, field, param))


A_('Open close popover', 'Close Field', 'Toggle Close Panel', 'p_CloseOpen')
for o in OPENS[1:]:
    A_('Close opens: ' + o[2:-4].lower(), 'Close Field', 'Close Panel', o)
A_('Set close', 'Close Grid', 'Close Pick', 'p_Close')
A_('Close popover on pick', 'Close Grid', 'Close Panel', 'p_CloseOpen')
A_('Close popover on x', 'Close Close', 'Close Panel', 'p_CloseOpen')
for grp, flag, tog, lst, param in (('Function', 'p_FunctionOpen', 'Toggle Function Panel', 'Function Toggle', 'p_Functions'),
                                   ('Department', 'p_DepartmentOpen', 'Toggle Department Panel', 'Department Toggle', 'p_Departments'),
                                   ('Country', 'p_CountryOpen', 'Toggle Country Panel', 'Country Toggle', 'p_Countries')):
    A_(f'Open {grp.lower()} popover', f'{grp} Field', tog, flag)
    for o in OPENS:
        if o != flag:
            A_(f'{grp} opens: ' + o[2:-4].lower() + ' closes', f'{grp} Field', 'Close Panel', o)
    A_(f'Toggle {grp.lower()}', f'{grp} List', lst, param)
    A_(f'Clear {grp.lower()}s', f'{grp} Clear', 'Empty Text', param)
    A_(f'{grp} popover on x', f'{grp} Close', 'Close Panel', flag)
A_('Set view', 'Show Toggle', 'Show Pick', 'p_ShowList')
for o in OPENS:
    A_('Show closes: ' + o[2:-4].lower(), 'Show Toggle', 'Close Panel', o)
A_('Reset close', 'Reset', 'Default Close', 'p_Close')
for p_ in ('p_Functions', 'p_Departments', 'p_Countries'):
    A_('Reset ' + p_[2:].lower(), 'Reset', 'Empty Text', p_)
A_('Reset view', 'Reset', 'zzFalse', 'p_ShowList')
for o in OPENS:
    A_('Reset closes: ' + o[2:-4].lower(), 'Reset', 'Close Panel', o)
A_('Open info', 'Info Button', 'Toggle Info', 'p_InfoOpen')
for o in OPENS[:-1]:
    A_('Info opens: ' + o[2:-4].lower() + ' closes', 'Info Button', 'Close Panel', o)


def sheet_xml(sh):
    i = s.index(f"<worksheet name='{sh}'>")
    return s[i:s.index('</worksheet>', i)]


def inst_of(sh, cap):
    base = nm(cap)
    m_ = re.search(r"name='(\[\w+:%s:\w+\])'" % base, sheet_xml(sh))
    assert m_, (sh, cap)
    return m_.group(1)


existing = max(int(n) for n in re.findall(r"name='\[Action(\d+)_", s))
cnt = [existing]
out = ''
for cap, sh, fld, prm in ACTS:
    cnt[0] += 1
    pid, clear = PARAM_ID[prm]
    src = f"[{DS}].{inst_of(sh, fld)}"
    out += (f"    <edit-parameter-action caption='{cap}' name='[Action{cnt[0]}_{uuid.uuid4().hex.upper()}]'>\n      <activation type='on-select' />\n"
            f"      <source dashboard='CW Reconciliation' type='sheet' worksheet='{sh}' />\n      <agg-type type='attr' />\n      <clear-option type='do-nothing' value='{clear}' />\n"
            f"      <params>\n        <param name='source-field' value='{src}' />\n        <param name='target-parameter' value='[Parameters].[{pid}]' />\n      </params>\n    </edit-parameter-action>\n")
edit_xml, out = out, ''
# deselect (filter the sheet to itself on zzFalse = zzTrue, auto-clear): the Dashboard #2 pattern
DES = ['Page Title', 'Main Title', 'Gap List Title', 'Timeline Title', 'Tickets Title', 'Rail As Of', 'Close Field', 'Function Field', 'Department Field', 'Country Field',
       'Show Toggle', 'Reset', 'Info Button', 'Close Grid', 'Close Close', 'Function List', 'Function Clear', 'Function Close', 'Department List', 'Department Clear',
       'Department Close', 'Country List', 'Country Clear', 'Country Close']
dsq = f'%5B{DS}%5D'
for sh in DES:
    assert ZT in sheet_xml(sh) and ZF in sheet_xml(sh), sh
    cnt[0] += 1
    enc = sh.replace(' ', '%20')
    out += (f"    <action caption='Deselect {sh}' name='[Action{cnt[0]}_{uuid.uuid4().hex.upper()}]'>\n      <activation auto-clear='true' type='on-select' />\n"
            f"      <source dashboard='CW Reconciliation' type='sheet' worksheet='{sh}' />\n"
            f"      <link caption='Deselect {sh}' delimiter=',' escape='\\' expression='tsl:{enc}?{dsq}.%5B{ZF}%5D~s0=&lt;[{DS}].[{ZT}]~na&gt;' include-null='true' multi-select='true' url-escape='true' />\n"
            f"      <command command='tsc:tsl-filter'>\n        <param name='target' value='{sh}' />\n      </command>\n    </action>\n")
# the schema wants every <action> before the first <edit-parameter-action>
p = s.index('<edit-parameter-action')
p = s.rfind('\n', 0, p) + 1
s = s[:p] + out + s[p:]
p = s.index('</actions>')
p = s.rfind('\n', 0, p) + 1
s = s[:p] + edit_xml + s[p:]

# viewpoints for the two new sheets
wi = s.index("<window class='dashboard' maximized='true' name='CW Reconciliation'")
placed = ['Page Title', 'Load Note']
vend = s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
s = s[:vend] + ''.join(f"        <viewpoint name='{n}'>\n          <zoom type='entire-view' />\n        </viewpoint>\n" for n in placed) + s[vend:]
vs, ve = s.index('<viewpoints>', wi) + len('<viewpoints>\n'), s.rfind('\n', 0, s.index('</viewpoints>', wi)) + 1
vparts = re.findall(r"        <viewpoint name='[^']*'>\n          <zoom type='[a-z-]+' />\n        </viewpoint>\n", s[vs:ve])
assert ''.join(vparts) == s[vs:ve], 'unexpected viewpoint layout'
s = s[:vs] + ''.join(sorted(vparts, key=lambda v: re.search(r"name='([^']*)'", v).group(1))) + s[ve:]
open(out_path := sys.argv[2], 'w', encoding='utf-8').write(s)
print('actions', len(ACTS), 'deselect', len(DES), 'pill', LN_C, LN_S)
