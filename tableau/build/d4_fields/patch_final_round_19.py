"""Round 19: KPI hover deselects, Sankey click no longer flips to the gap list, KPI 2 top strip as two images
switched by a visibility calc. usage: patch_final_round_19.py in.twb out.twb"""
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
FED = "federated.19gwunf1mzo1gq1cltitv08khlf9"
U = lambda: str(uuid.uuid4())
IMG = "/Users/thiagoalpoin/Documents/Tableau/Tableau Public/ArcadiaHR/4 Contingent Workforce Reconciliation/Images and Buttons/"

def remove_zone(text, zid):
    while True:
        m = re.search(r"[ \t]*<zone [^>]*\bid='%s'[^>]*>" % zid, text)
        if not m: return text
        i, j = m.start(), m.end()
        if text[j-2:j] == '/>': text = text[:i] + text[j:].lstrip('\n'); continue
        depth, pos = 1, j
        while depth:
            a = text.find('<zone ', pos); b = text.find('</zone>', pos)
            if a != -1 and a < b:
                e = text.find('>', a); depth += 0 if text[e-1] == '/' else 1; pos = e + 1
            else: depth -= 1; pos = b + 7
        text = text[:i] + text[pos:].lstrip('\n')

# ---- 1. drop the strip sheet from round 18
t = remove_zone(t, '330')
t = re.sub(r"[ \t]*<worksheet name='KPI 2 Strip'>.*?</worksheet>\n?", '', t, flags=re.S)
t = re.sub(r"[ \t]*<window class='worksheet' name='KPI 2 Strip'>.*?</window>\n?", '', t, flags=re.S)
t = re.sub(r"[ \t]*<viewpoint name='KPI 2 Strip'>.*?</viewpoint>\n?", '', t, flags=re.S)

# ---- 2. Sankey click no longer opens the gap list
t, n = re.subn(r"[ \t]*<edit-parameter-action caption='Sankey opens the gap list'.*?</edit-parameter-action>\n?", '', t, flags=re.S)
assert n == 1

# ---- 3. deselect actions for the five KPI hover sheets
pt = t[t.index("<worksheet name='Page Title'>"):]; pt = pt[:pt.index('</worksheet>')]
zzcols = ''.join(re.findall(r"<column caption='zz(?:True|False)'.*?</column>", pt, re.S))
zzinst = ''.join("<column-instance column='[Calculation_0725102600000%s]' derivation='None' name='[none:Calculation_0725102600000%s:nk]' pivot='key' type='nominal' />\n          " % (c, c) for c in ('026', '027'))
acts = ''
for n in range(1, 6):
    name = 'KPI Hover %d' % n
    k = t.index("<worksheet name='%s'>" % name); e = t.index('</worksheet>', k)
    w = t[k:e]
    d0 = w.index("<datasource-dependencies datasource='%s'>" % FED)
    j = w.index('</datasource-dependencies>', d0)
    w = w[:j] + zzcols + '\n          ' + zzinst + w[j:]
    w = w.replace("<encodings>", "<encodings>\n              <lod column='[%s].[none:Calculation_0725102600000026:nk]' />\n              <lod column='[%s].[none:Calculation_0725102600000027:nk]' />" % (FED, FED), 1)
    t = t[:k] + w + t[e:]
    act = "[Action%d_%s]" % (70 + n, uuid.uuid4().hex.upper())
    esc = name.replace(' ', '%20')
    acts += ("""    <action caption='Deselect %s' name='%s'>
      <activation auto-clear='true' type='on-select' />
      <source dashboard='CW Reconciliation' type='sheet' worksheet='%s' />
      <link caption='Deselect %s' delimiter=',' escape='\\' expression='tsl:%s?%%5B%s%%5D.%%5BCalculation_0725102600000027%%5D~s0=&lt;[%s].[Calculation_0725102600000026]~na&gt;' include-null='true' multi-select='true' url-escape='true' />
      <command command='tsc:tsl-filter'>
        <param name='target' value='%s' />
      </command>
    </action>
""" % (name, act, name, name, esc, FED, FED, name))
a0 = t.index('<actions>')
i = t.index('<datasources>', a0)
i = t.rfind('\n', 0, i) + 1
t = t[:i] + acts + t[i:]

# ---- 4. strip visibility calcs (aggregates; evaluated against the data source with the current parameters)
def ds_col(cid):
    return re.search(r"<column caption='[^']*'[^>]*name='\[Calculation_%s\]'[^>]*>.*?</column>" % cid, t, re.S).group(0)
GAP = "SUM(IF [Calculation_0725102600000023] THEN [contractors_with_gap] END)"
WRK = "SUM(IF [Calculation_0725102600000023] THEN [contractors_working] END)"
cols = {
 '0725102600000360': ("KPI 2 Strip Risk", "// KPI 2 Strip Risk&#10;%s &gt; 0.035 * %s" % (GAP, WRK)),
 '0725102600000361': ("KPI 2 Strip Ok", "// KPI 2 Strip Ok&#10;NOT (%s &gt; 0.035 * %s)" % (GAP, WRK)),
}
assert 'Calculation_0725102600000360' not in t
xml = ''.join("      <column caption='%s' datatype='boolean' name='[Calculation_%s]' role='measure' type='nominal'>\n        <calculation class='tableau' formula='%s' />\n      </column>\n" % (cap, cid, f) for cid, (cap, f) in cols.items())
anchor = ds_col('0725102600000211'); i = t.index(anchor) + len(anchor)
t = t[:i] + '\n' + xml.rstrip('\n') + t[i:]

# ---- 5. two image zones right above the band image, so the cards and hovers stay on top
def img_zone(zid, name, file):
    return ("""        <zone friendly-name='%s' h='471' id='%d' is-centered='0' is-scaled='1' param='%s' type-v2='bitmap' w='15286' x='33786' y='10118'>
          <zone-style>
            <format attr='border-color' value='#000000' />
            <format attr='border-style' value='none' />
            <format attr='border-width' value='0' />
            <format attr='margin' value='0' />
          </zone-style>
        </zone>
""") % (name, zid, IMG + file)
i = t.index("<zone friendly-name='KPI band image'"); i = t.index('>', i) + 1
if t[i-2] != '/':
    i = t.index('</zone>', i) + 7
i = t.index('\n', i) + 1
t = t[:i] + img_zone(330, 'KPI 2 Strip Risk', 'arcadia_kpi2_strip_risk.png') + img_zone(331, 'KPI 2 Strip Ok', 'arcadia_kpi2_strip_ok.png') + t[i:]
DASH = '{6548F4FB-B30D-45E2-A1B0-256049E77034}'; SUB = '17fb47e4-dd15-41de-a6be-f1287aff1795'
nodes = edges = pairs = ''
for zid, calc in ((330, '0725102600000360'), (331, '0725102600000361')):
    g_in, g_node, g_out, g_vn, g_vin = U(), U(), U(), U(), U()
    nodes += "        <single-value-field-node fieldname='[%s].[Calculation_%s]' fieldname-input-guid='%s' node-guid='%s' value-output-guid='%s' />\n" % (FED, calc, g_in, g_node, g_out)
    nodes += "        <dashboard-zone-visibility-node dashboard-identifier='%s' node-guid='%s' visibility-input-guid='%s' zone-id='%d' />\n" % (DASH, g_vn, g_vin, zid)
    edges += "        <edge from='%s' to='%s' />\n" % (g_out, g_vin)
    pairs += "        <pair execution-subgraph-guid='%s' node-guid='%s' />\n        <pair execution-subgraph-guid='%s' node-guid='%s' />\n" % (SUB, g_node, SUB, g_vn)
t = t.replace("      </nodes>", nodes + "      </nodes>", 1)
t = t.replace("      </edges>", edges + "      </edges>", 1)
j = t.rindex("<pair execution-subgraph-guid='%s'" % SUB); j = t.index('\n', j) + 1
t = t[:j] + pairs + t[j:]
open(dst, 'w', encoding='utf-8').write(t)
print('ok')
