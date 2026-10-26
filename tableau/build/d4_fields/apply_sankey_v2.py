"""Native Sankey v2 (build doc 9N, revision 6): the extension's look, built natively.

  python3 apply_sankey_v2.py "in.twb" "out.twb"          (close Tableau first)

On a workbook that has the v1 native Sankey (build_sankey.py) and its revision 5 flag-label sheet:
- the Custom SQL (both copies): risk-to-place ribbons split by flag, two label rows per box
- every Sk field to spec_sankey.py: changed formulas rewritten wherever they are stored, new ones added
  (before any column-instance), the fields v2 no longer uses removed
- the Sk Colour palette: 9 flag colours, their ribbon tints, slate risks, the three places
- Sankey Native: X axis 0 to 726; box labels centred (navy, white on the slate risks); flag_code on the
  polygons' Detail (for the highlight action)
- the Sankey Flag Labels sheet, its window and its dashboard zones removed; Sankey Native's zones take
  their width
Version A (the extension sheet) and every non-Sk field are untouched.
"""
import os, re, sys, uuid
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spec_sankey import PARAMS, C, OBSOLETE

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
SQL = open(os.path.join(HERE, '..', '..', 'custom_sql_cw_reconciliation_dashboard.sql'), encoding='utf-8').read().rstrip('\n')
DS = re.search(r"<datasource caption='CW Reconciliation' inline='true' name='([^']+)'", s).group(1)
Q = f'[{DS}]'


def esc_attr(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '&apos;').replace('"', '&quot;').replace('\n', '&#10;'))


def esc_text(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", '&apos;').replace('"', '&quot;')


def unesc(t):
    return t.replace('&apos;', "'").replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def ds_bounds():
    a = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
    return a, s.index('</datasource>', a)


a, b = ds_bounds()
cap2int = {unesc(m.group(1)): m.group(2) for m in re.finditer(
    r"<column caption='([^']*)' datatype='\w+'(?: default-format='[^']*')? name='\[(Calculation_\d+)\]'", s[a:b])}
pds = re.search(r"<datasource hasconnection='false' inline='true' name='Parameters' version='[^']+'>.*?</datasource>", s, re.S).group(0)
params = {unesc(m.group(1)): m.group(2) for m in re.finditer(r"<column caption='([^']*)' datatype='\w+'[^>]*? name='\[([^\]]+)\]'", pds)}
sqlcols = set(re.findall(r"<local-name>\[([^\]]+)\]</local-name>", s[a:b]))
assert 'Sk Row' in cap2int and "<worksheet name='Sankey Native'>" in s, 'needs the v1 native Sankey'
assert 'Sk Min H' not in cap2int, 'already v2'
for p, *_ in PARAMS:
    assert p in params, p

new_caps = [c for c, *_ in C if c not in cap2int]
cid = dict(cap2int)
for i, c in enumerate(new_caps, 1):
    cid[c] = f'Calculation_07251028{i:08d}'


def resolve(f, where):
    def sub(m):
        n = m.group(1)
        if n in params: return f'[Parameters].[{params[n]}]'
        if n in cid: return f'[{cid[n]}]'
        if n in sqlcols: return f'[{n}]'
        raise SystemExit(f'UNRESOLVED [{n}] in {where}')
    return re.sub(r'\[([^\[\]]+)\]', sub, f)


def role_type(dt, kind):
    if kind == 'agg':
        return 'measure', ('quantitative' if dt in ('integer', 'real') else 'nominal')
    if dt in ('integer', 'real'): return 'measure', 'quantitative'
    if dt == 'date': return 'dimension', 'ordinal'
    return 'dimension', 'nominal'


FMT = {'Sk Tip Share': 'p0%'}
SPEC = {c: (dt, k, f) for c, dt, k, f in C}


def col_xml(cap, ind):
    dt, kind, f = SPEC[cap]
    role, typ = role_type(dt, kind)
    fmt = f" default-format='{FMT[cap]}'" if cap in FMT else ''
    return (f"{ind}<column caption='{esc_attr(cap)}' datatype='{dt}'{fmt} name='[{cid[cap]}]' role='{role}' type='{typ}'>\n"
            f"{ind}  <calculation class='tableau' formula='{esc_attr('// ' + cap + chr(10) + resolve(f, cap))}' />\n{ind}</column>\n")


# ---------- 1. Custom SQL
rel = re.compile(r"(<relation connection='[^']+' name='Custom SQL Query' type='text'>)(.*?)(</relation>)", re.S)
s, n = rel.subn(lambda m: m.group(1) + esc_text(SQL) + m.group(3), s)
assert n == 2

# ---------- 2. existing Sk fields: new formula and type, everywhere they are stored (data source and sheet copies)
for cap in [c for c, *_ in C if c in cap2int]:
    dt, kind, f = SPEC[cap]
    role, typ = role_type(dt, kind)
    iid = cap2int[cap]
    pat = re.compile(r"<column caption='" + re.escape(esc_attr(cap)) + r"' datatype='\w+'((?: default-format='[^']*')?) name='\[" + iid +
                     r"\]' role='\w+' type='\w+'>\s*<calculation class='tableau' formula='[^']*' />")
    def sub(m, cap=cap, dt=dt, role=role, typ=typ, iid=iid, f=f):
        return (f"<column caption='{esc_attr(cap)}' datatype='{dt}'{m.group(1)} name='[{iid}]' role='{role}' type='{typ}'>\n"
                f"        <calculation class='tableau' formula='{esc_attr('// ' + cap + chr(10) + resolve(f, cap))}' />")
    s, k = pat.subn(sub, s)
    assert k >= 1, cap

# ---------- 3. obsolete fields out: their definitions and any column-instance of them, in the data source and the sheets
for cap in OBSOLETE:
    if cap not in cap2int: continue
    iid = cap2int[cap]
    s = re.sub(r"\n[ \t]*<column caption='[^']*' datatype='\w+'(?: default-format='[^']*')? name='\[" + iid +
               r"\]' role='\w+' type='\w+'>\s*<calculation class='tableau' formula='[^']*' />\s*</column>", '', s)
    s = re.sub(r"\n[ \t]*<column-instance column='\[" + iid + r"\]'[^>]*/>", '', s)
    s = re.sub(r"\n[ \t]*<field>[^<]*:" + iid + r":[a-z]+\]</field>", '', s)          # window highlight lists

# ---------- 4. new fields into the data source, before any column-instance
a, b = ds_bounds()
cands = [s.find(t, a, b) for t in ('\n      <column-instance ', '\n      <group ')]
g = min(c for c in cands if c != -1) + 1
s = s[:g] + ''.join(col_xml(c, '      ') for c in new_caps) + s[g:]

# ---------- 5. the Sk Colour palette
def tint(h, a=0.45):
    h = h.lstrip('#'); r, g_, b_ = (int(h[i:i + 2], 16) for i in (0, 2, 4))
    return '#%02X%02X%02X' % tuple(round(a * v + (1 - a) * 255) for v in (r, g_, b_))
FCOL = {'F01': '#FF9D9A', 'F02': '#59A14F', 'F03': '#FFBE7D', 'F04': '#E15759', 'F05': '#FABFD2', 'F06': '#8CD17D',
        'F07': '#D4A6C8', 'F08': '#F1CE63', 'F09': '#A0CBE8'}
PAL = {**FCOL, **{f'{k} ribbon': tint(v) for k, v in FCOL.items()}, 'Risk': '#4F6980', 'Risk ribbon': tint('#4F6980'),
       'Bridgeway': '#F89217', 'Keystone': '#7873C0', 'System feed': '#21B087'}
maps = ''.join(f"            <map to='{v.lower()}'>\n              <bucket>&quot;{k}&quot;</bucket>\n            </map>\n" for k, v in PAL.items())
maps += "            <map to='#bab0ac'>\n              <bucket>%null%</bucket>\n            </map>\n"
cc = cap2int['Sk Colour']
pal = re.compile(r"(<encoding attr='color' field='\[none:" + cc + r":nk\]' type='palette'>\n)(.*?)(\s*</encoding>)", re.S)
s, k = pal.subn(lambda m: m.group(1) + maps.rstrip('\n') + m.group(3), s, count=1)
assert k == 1, 'Sk Colour palette not found'

# ---------- 6. Sankey Native: axis, labels, flag_code for the highlight, its dependencies
a = s.index("<worksheet name='Sankey Native'>"); b = s.index('</worksheet>', a)
w = s[a:b]
sx = cid['Sk X']
w = re.sub(r"(field='\[[^\]]+\]\.\[avg:" + sx + r":qk\]' field-type='quantitative' max=')\d+\.0(')", r"\g<1>726.0\2", w)
t = lambda c: f"{Q}.[none:{cid[c]}:nk]"
p2 = re.search(r"(<pane id='2'.*?<encodings>\n)(.*?)(\s*</encodings>)", w, re.S)
enc = (f"              <text column='{t('Sk Lbl Header')}' />\n              <text column='{t('Sk Lbl Dark')}' />\n"
       f"              <text column='{t('Sk Lbl White')}' />\n              <lod column='{t('Sk Mark')}' />")
w = w[:p2.start(2)] + enc + w[p2.end(2):]
lab = re.search(r"(<pane id='2'.*?<customized-label>\s*<formatted-text>\n)(.*?)(\s*</formatted-text>)", w, re.S)
runs = (f"                <run fontalignment='1' fontcolor='#6b7079' fontsize='8'><![CDATA[<{t('Sk Lbl Header')}>]]></run>\n"
        f"                <run fontalignment='1' fontcolor='#13243a' fontsize='8'><![CDATA[<{t('Sk Lbl Dark')}>]]></run>\n"
        f"                <run fontalignment='1' fontcolor='#ffffff' fontsize='8'><![CDATA[<{t('Sk Lbl White')}>]]></run>")
w = w[:lab.start(2)] + runs + w[lab.end(2):]
w = re.sub(r"(<pane id='2'.*?<format attr='text-align' value=')\w+(')", r"\g<1>center\2", w, count=1, flags=re.S)
p1 = re.search(r"(<pane id='1'.*?<encodings>\n)", w, re.S)
w = w[:p1.end()] + f"              <lod column='{Q}.[none:flag_code:nk]' />\n" + w[p1.end():]
# dependencies: every Sk field the sheet's fields reach that it does not list yet, and the new column-instances
dep_open = f"<datasource-dependencies datasource='{DS}'>"
d0 = w.index(dep_open); d1 = w.index('</datasource-dependencies>', d0)
dep = w[d0:d1]
have = set(re.findall(r"<column caption='[^']*' datatype='\w+'[^>]*? name='\[(Calculation_\d+)\]'", dep))
add = ''.join(col_xml(c, '            ') for c, *_ in C if cid[c] not in have)
inst = ''.join(f"            <column-instance column='[{cid[c]}]' derivation='None' name='[none:{cid[c]}:nk]' pivot='key' type='nominal' />\n"
               for c in ('Sk Lbl Dark', 'Sk Lbl White') if f"name='[none:{cid[c]}:nk]'" not in dep)
if "name='[none:flag_code:nk]'" not in dep:
    inst += f"            <column-instance column='[flag_code]' derivation='None' name='[none:flag_code:nk]' pivot='key' type='nominal' />\n"
    if "name='[flag_code]'" not in dep:
        inst += "            <column datatype='string' name='[flag_code]' role='dimension' type='nominal' />\n"
w = w[:d1] + add + inst + '          ' + w[d1:].lstrip(' ')
s = s[:a] + w + s[b:]

# ---------- 7. the flag-label sheet goes; Sankey Native takes its width on the dashboards
if "<worksheet name='Sankey Flag Labels'>" in s:
    s = re.sub(r"\n[ \t]*<worksheet name='Sankey Flag Labels'>.*?</worksheet>", '', s, flags=re.S)
    s = re.sub(r"\n[ \t]*<window class='worksheet' name='Sankey Flag Labels'>.*?</window>", '', s, flags=re.S)
    # each layout (default, phone) has the label zone followed by the Sankey Native zone: the label zone goes,
    # Sankey Native starts where it started and takes both widths. Tile zones hold no other zones.
    while True:
        m = re.search(r"\n[ \t]*<zone [^>]*name='Sankey Flag Labels'[^>]*>.*?</zone>", s, re.S)
        if not m: break
        lab = re.search(r"<zone [^>]*>", m.group(0)).group(0)
        lx = re.search(r" x='(\d+)'", lab).group(1); lw = int(re.search(r" w='(\d+)'", lab).group(1))
        s = s[:m.start()] + s[m.end():]
        n = re.compile(r"<zone [^>]*name='Sankey Native'[^>]*>").search(s, m.start())
        nz = n.group(0)
        nw = int(re.search(r" w='(\d+)'", nz).group(1))
        nz2 = re.sub(r" w='\d+'", f" w='{lw + nw}'", re.sub(r" x='\d+'", f" x='{lx}'", nz))
        s = s[:n.start()] + nz2 + s[n.end():]
    s = re.sub(r"\n[ \t]*<viewpoint name='Sankey Flag Labels'(?: />|>.*?</viewpoint>)", '', s, flags=re.S)
    s = re.sub(r"\n[ \t]*<thumbnail [^>]*name='Sankey Flag Labels'[^>]*>.*?</thumbnail>", '', s, flags=re.S)
    assert "name='Sankey Flag Labels'" not in s, 'a Sankey Flag Labels reference is left'

open(out, 'w', encoding='utf-8').write(s)
print(f'v2: Custom SQL (2 copies); {len([c for c in SPEC if c in cap2int])} Sk fields rewritten, {len(new_caps)} added, '
      f'{len([c for c in OBSOLETE if c in cap2int])} removed; palette of {len(PAL)}; Sankey Native relabelled; flag-label sheet removed')
