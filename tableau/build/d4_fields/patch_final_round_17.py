"""Round 17 (final) for Dashboard #4: usage patch_final_round_17.py in.twb out.twb"""
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
FED = "federated.19gwunf1mzo1gq1cltitv08khlf9"
def U(): return str(uuid.uuid4())
def rep(old, new, cnt=1):
    global t
    assert old in t, old[:90]
    t = t.replace(old, new, cnt)

# ---------- 1. Title/tip constants as real aggregates (same shape as the working KPI 2 tooltip)
IDS = ['088', '101', '105', '111', '112', '113']
for c in IDS:
    n = '0725102600000' + c
    # column definitions: role + wrap body
    def fix_col(m):
        s = m.group(0).replace("role='dimension'", "role='measure'")
        s = re.sub(r"formula='([^']*?&#10;)(.*)'", lambda mm: "formula='%sMIN(%s)'" % (mm.group(1), mm.group(2)), s, flags=re.S)
        return s
    t, k = re.subn(r"<column caption='[^']*' datatype='string' name='\[Calculation_%s\]' role='dimension' type='nominal'>\s*<calculation [^>]*/>\s*</column>" % n, fix_col, t)
    assert k >= 2, (c, k)
    t = t.replace("derivation='None' name='[none:Calculation_%s:nk]'" % n, "derivation='User' name='[usr:Calculation_%s:nk]'" % n)
    t = t.replace("[none:Calculation_%s:nk]" % n, "[usr:Calculation_%s:nk]" % n)

# ---------- 2. Tooltip colours on hover sheets 1,3,4,5; rich tooltip on 2
def sheet_span(name):
    k = t.index("<worksheet name='%s'>" % name); return k, t.index('</worksheet>', k) + 12
def set_sheet(name, fn):
    global t
    a, b = sheet_span(name); t = t[:a] + fn(t[a:b]) + t[b:]
for n in (1, 3, 4, 5):
    def f(w):
        w = w.replace("fontcolor='#13223a' fontname='Tableau Semibold' fontsize='10'", "fontcolor='#13233a' fontname='Tableau Semibold' fontsize='11'")
        w = w.replace("fontcolor='#4a5a73' fontname='Tableau Book' fontsize='9'", "fontcolor='#2b2f36' fontname='Tableau Book' fontsize='10'")
        return w
    set_sheet('KPI Hover %d' % n, f)

def ds_col(cid):
    m = re.search(r"<column caption='[^']*'[^>]*name='\[Calculation_%s\]'[^>]*>.*?</column>" % cid, t, re.S)
    return m.group(0)
# new calcs (datasource level), inserted after 'Show Load Note'
newcols = {
 '0725102600000345': ("KPI 2 Pts Good", 'string', 'measure', 'nominal', '// KPI 2 Pts Good&#10;IF [Calculation_0725102600000061] &lt;= [Calculation_0725102600000063] THEN [Calculation_0725102600000086] END'),
 '0725102600000346': ("KPI 2 Pts Bad", 'string', 'measure', 'nominal', '// KPI 2 Pts Bad&#10;IF [Calculation_0725102600000061] &gt; [Calculation_0725102600000063] THEN [Calculation_0725102600000086] END'),
 '0725102600000347': ("KPI 2 Clear Own", 'string', 'measure', 'nominal', '// KPI 2 Clear Own&#10;IF ZN([Calculation_0725102600000065]) &gt; 0 THEN &quot; &quot; + STR([Calculation_0725102600000065]) + &quot; gaps clear on their own by the next run and are left out.&quot; END'),
 '0725102600000348': ("KPI 2 Strip Bad", 'boolean', 'dimension', 'nominal', '// KPI 2 Strip Bad&#10;{ FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_with_gap] END) } &gt; 0.035 * { FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_working] END) }'),
 '0725102600000349': ("KPI 2 Strip Good", 'boolean', 'dimension', 'nominal', '// KPI 2 Strip Good&#10;NOT { FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_with_gap] END) } &gt; 0.035 * { FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_working] END) }'),
}
xml = ''
for cid, (cap, dt, role, ty, f) in newcols.items():
    xml += "      <column caption='%s' datatype='%s' name='[Calculation_%s]' role='%s' type='%s'>\n        <calculation class='tableau' formula='%s' />\n      </column>\n" % (cap, dt, cid, role, ty, f)
anchor = ds_col('0725102600000211'); i = t.index(anchor) + len(anchor)
t = t[:i] + '\n' + xml.rstrip('\n') + t[i:]
# fix precedence of Strip Good: NOT (a > b)
t = t.replace("NOT { FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_with_gap] END) } &gt; 0.035 * { FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_working] END) }",
              "NOT ({ FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_with_gap] END) } &gt; 0.035 * { FIXED : SUM(IF [Calculation_0725102600000023] THEN [contractors_working] END) })")

def deps_for(w, cid, seen=None):
    """ensure column def for cid and its calc deps exist in sheet's federated deps"""
    seen = seen if seen is not None else set()
    if cid in seen: return w
    seen.add(cid)
    d = ds_col(cid)
    f = re.search(r"formula='([^']*)'", d).group(1)
    for ref in re.findall(r"\[Calculation_(\d+)\]", f):
        w = deps_for(w, ref, seen)
    if "name='[Calculation_%s]'" % cid not in w:
        j = w.index("<column-instance", w.index("datasource='%s'>" % FED)) if "<column-instance" in w[w.index("datasource='%s'>" % FED):] else w.index('</datasource-dependencies>', w.index("datasource='%s'>" % FED))
        w = w[:j] + d + '\n            ' + w[j:]
    return w
def inst(w, cid):
    nm = "[usr:Calculation_%s:nk]" % cid
    if nm in w and "<column-instance column='[Calculation_%s]'" % cid in w: return w
    j = w.index('</datasource-dependencies>', w.index("datasource='%s'>" % FED))
    return w[:j] + "<column-instance column='[Calculation_%s]' derivation='User' name='%s' pivot='key' type='nominal' />\n          " % (cid, nm) + w[j:]

def rich2(w):
    for cid in ('0725102600000345', '0725102600000346', '0725102600000347', '0725102600000087', '0725102600000092'):
        w = deps_for(w, cid); w = inst(w, cid)
    F = lambda c: "<[%s].[usr:Calculation_%s:nk]>" % (FED, c)
    runs = [
     ("#13233a", "Tableau Semibold", "12", F('0725102600000092')),
     None,
     ("#2b2f36", "Tableau Book", "10", "Contractors with at least one gap in the rate, divided by contractors working in Bridgeway. "),
     ("#0e7d5f", "Tableau Semibold", "10", F('0725102600000345')),
     ("#b8401f", "Tableau Semibold", "10", F('0725102600000346')),
     ("#2b2f36", "Tableau Book", "10", " a provisional "),
     ("#13233a", "Tableau Semibold", "10", F('0725102600000087')),
     ("#2b2f36", "Tableau Book", "10", " target. "),
     ("#5a6170", "Tableau Book", "10", "The target flags risk; it does not certify the report."),
     ("#5a6170", "Tableau Book", "10", F('0725102600000347')),
    ]
    out = "<customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
    for r in runs:
        if r is None: out += "                <run>Æ&#10;</run>\n"
        else: out += "                <run fontcolor='%s' fontname='%s' fontsize='%s'><![CDATA[%s]]></run>\n" % r
    out += "              </formatted-text>\n            </customized-tooltip>"
    w = re.sub(r"<customized-tooltip.*?</customized-tooltip>", lambda m: out, w, flags=re.S)
    enc = ''.join("<tooltip column='[%s].[usr:Calculation_%s:nk]' />\n              " % (FED, c) for c in ('0725102600000345', '0725102600000346', '0725102600000347', '0725102600000087'))
    w = w.replace("</encodings>", "  " + enc + "</encodings>", 1)
    return w
set_sheet('KPI Hover 2', rich2)

# ---------- 3. Strip sheets + zones + visibility
a, b = sheet_span('Load Note'); ln = t[a:b]
def mk_sheet(name):
    w = ln.replace("name='Load Note'", "name='%s'" % name)
    w = re.sub(r"<simple-id uuid='\{[^}]*\}' />", "<simple-id uuid='{%s}' />" % U().upper(), w)
    w = w.replace("<text column='[usr:Calculation_0725102600000210:nk]' />", "")
    w = re.sub(r"<customized-label>.*?</customized-label>", "", w, flags=re.S)
    return w
sheets = mk_sheet('KPI 2 Strip Bad') + '\n    ' + mk_sheet('KPI 2 Strip Good')
t = t[:b] + '\n    ' + sheets + t[b:]
# window entries
m = re.search(r"<window class='worksheet' name='Load Note'>.*?</window>", t, re.S)
win = m.group(0)
newwin = ''.join('\n    ' + re.sub(r"<simple-id uuid='\{[^}]*\}' />", lambda _m: "<simple-id uuid='{%s}' />" % U().upper(), win.replace("name='Load Note'", "name='%s'" % n)) for n in ('KPI 2 Strip Bad', 'KPI 2 Strip Good'))
t = t[:m.end()] + newwin + t[m.end():]
vp = re.search(r"<viewpoint name='Load Note'>.*?</viewpoint>", t, re.S).group(0)
t = t.replace(vp, vp + ''.join('\n        ' + vp.replace('Load Note', n) for n in ('KPI 2 Strip Bad', 'KPI 2 Strip Good')), 1)
# zones (after KPI Hover 5 in the default layout)
def zone(zid, name, color):
    return ("""        <zone h='471' id='%d' name='%s' show-title='false' w='14429' x='34214' y='10235'>
          <layout-cache type-h='cell' type-w='fixed' />
          <zone-style>
            <format attr='border-color' value='#000000' />
            <format attr='border-style' value='none' />
            <format attr='border-width' value='0' />
            <format attr='margin' value='0' />
            <format attr='background-color' value='%s' />
          </zone-style>
        </zone>
""" % (zid, name, color))
i = t.index("id='276'"); i = t.index('</zone>', i) + 7; i = t.index('\n', i) + 1
t = t[:i] + zone(330, 'KPI 2 Strip Bad', '#ee9a74') + zone(331, 'KPI 2 Strip Good', '#86d4bc') + t[i:]
# datagraph
DASH = '{6548F4FB-B30D-45E2-A1B0-256049E77034}'; SUB = '17fb47e4-dd15-41de-a6be-f1287aff1795'
nodes = edges = pairs = ''
for zid, calc in ((330, '0725102600000348'), (331, '0725102600000349')):
    g_in, g_node, g_out, g_vn, g_vin = U(), U(), U(), U(), U()
    nodes += "        <single-value-field-node fieldname='[%s].[Calculation_%s]' fieldname-input-guid='%s' node-guid='%s' value-output-guid='%s' />\n" % (FED, calc, g_in, g_node, g_out)
    nodes += "        <dashboard-zone-visibility-node dashboard-identifier='%s' node-guid='%s' visibility-input-guid='%s' zone-id='%d' />\n" % (DASH, g_vn, g_vin, zid)
    edges += "        <edge from='%s' to='%s' />\n" % (g_out, g_vin)
    pairs += "        <pair execution-subgraph-guid='%s' node-guid='%s' />\n        <pair execution-subgraph-guid='%s' node-guid='%s' />\n" % (SUB, g_node, SUB, g_vn)
t = t.replace("      </nodes>", nodes + "      </nodes>", 1)
t = t.replace("      </edges>", edges + "      </edges>", 1)
j = t.rindex("<pair execution-subgraph-guid='%s'" % SUB); j = t.index('\n', j) + 1
t = t[:j] + pairs + t[j:]

# ---------- 4. Timeline selected dot colours (peach above target, light teal below)
pal = re.search(r"<encoding attr='color' field='\[usr:Calculation_0725102600000200:nk\]' type='palette'>.*?</encoding>", t, re.S).group(0)
newpal = """<encoding attr='color' field='[usr:Calculation_0725102600000200:nk]' type='palette'>
            <map to='#ee9a74'>
              <bucket>&quot;selected above&quot;</bucket>
            </map>
            <map to='#86d4bc'>
              <bucket>&quot;selected below&quot;</bucket>
            </map>
            <map to='#ffffff'>
              <bucket>&quot;other&quot;</bucket>
            </map>
          </encoding>"""
t = t.replace(pal, newpal, 1)

# ---------- 5. Rail: logo on its own row, info button below it
i = t.index("friendly-name='Rail Top'"); i = t.rfind('<zone', 0, i)
j = t.index("id='94'", i); j = t.rfind('<zone', 0, j)
old = t[i:j]
logo = re.search(r"<zone fixed-size='148'.*?</zone>", old, re.S).group(0)
logo = logo.replace("fixed-size='148'", "fixed-size='40'").replace("w='10571'", "w='14287'")
info = re.search(r"<zone fixed-size='28' h='4706' id='93'.*?</zone>", old, re.S).group(0)
info = info.replace("h='4706'", "h='3294'").replace("w='2000'", "w='2000'").replace("y='2824'", "y='9412'")
logo = logo.replace("y='2824'", "y='2824'")
zs = re.search(r"<zone-style>.*?</zone-style>", logo, re.S).group(0)
new = ("""<zone fixed-size='80' friendly-name='Rail Top' h='9412' id='90' is-fixed='true' param='vert' type-v2='layout-flow' w='14287' x='571' y='2824'>
            %s
            <zone fixed-size='12' h='1412' id='92' is-fixed='true' type-v2='empty' w='14287' x='571' y='7530'>
              %s
            </zone>
            <zone fixed-size='28' friendly-name='Info Row' h='3294' id='323' is-fixed='true' param='horz' type-v2='layout-flow' w='14287' x='571' y='8942'>
              %s
              <zone fixed-size='28' h='3294' id='324' type-v2='empty' w='12287' x='2571' y='8942'>
                %s
              </zone>
            </zone>
          </zone>
          """) % (logo.replace("y='2824'", "y='2824'"), zs, info.replace("y='9412'", "y='8942'"), zs)
t = t[:i] + new + t[j:]
# shift following rail children by +4706 and shrink the flexible blank
DY = 4706
rs = t.rindex("friendly-name='Rail'", 0, t.index("id='94'", i)); rs = t.rfind('<zone', 0, rs)
re_ = t.index("id='118'", i); re_ = t.index('</zone>', re_) + 7
seg = t[i + len(new):re_]
def shift(m):
    return m.group(1) + str(int(m.group(2)) + DY) + m.group(3)
seg = re.sub(r"(<zone [^>]*\bid='(?:9[4-9]|10\d|11[0-6])'[^>]*? y=')(\d+)(')", shift, seg)
seg = seg.replace("h='32467' id='116'", "h='%d' id='116'" % (32467 - DY))
t = t[:i + len(new)] + seg + t[re_:]
open(dst, 'w', encoding='utf-8').write(t)
print('ok')
