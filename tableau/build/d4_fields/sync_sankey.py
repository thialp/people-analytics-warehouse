"""Bring a workbook that already has the native Sankey v2 up to spec_sankey.py: every Sk field's formula and type
(wherever stored), new Sk fields added, obsolete ones removed, and the Sk Colour palette. Sheets, dashboards
and everything that is not an Sk field are untouched.

  python3 sync_sankey.py "in.twb" "out.twb"          (close Tableau first)
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spec_sankey import C, OBSOLETE, PALETTE

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
DS = re.search(r"<datasource caption='CW Reconciliation' inline='true' name='([^']+)'", s).group(1)
esc = lambda t: (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", '&apos;').replace('"', '&quot;').replace('\n', '&#10;'))
unesc = lambda t: t.replace('&apos;', "'").replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


def bounds():
    a = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'"); return a, s.index('</datasource>', a)


a, b = bounds()
cap2int = {unesc(m.group(1)): m.group(2) for m in re.finditer(
    r"<column caption='([^']*)' datatype='\w+'(?: default-format='[^']*')? name='\[(Calculation_\d+)\]'", s[a:b])}
pds = re.search(r"<datasource hasconnection='false' inline='true' name='Parameters' version='[^']+'>.*?</datasource>", s, re.S).group(0)
params = {unesc(m.group(1)): m.group(2) for m in re.finditer(r"<column caption='([^']*)' datatype='\w+'[^>]*? name='\[([^\]]+)\]'", pds)}
sqlcols = set(re.findall(r"<local-name>\[([^\]]+)\]</local-name>", s[a:b]))
assert 'Sk Min H' in cap2int, 'needs v2 (apply_sankey_v2.py) first'
new = [c for c, *_ in C if c not in cap2int]
cid = dict(cap2int)
used = {int(x[-8:]) for x in cap2int.values() if x.startswith('Calculation_07251029')}
for i, c in enumerate(new, max(used, default=0) + 1):
    cid[c] = f'Calculation_07251029{i:08d}'
SPEC = {c: (dt, k, f) for c, dt, k, f in C}


def resolve(f, where):
    def sub(m):
        n = m.group(1)
        if n in params: return f'[Parameters].[{params[n]}]'
        if n in cid: return f'[{cid[n]}]'
        if n in sqlcols: return f'[{n}]'
        raise SystemExit(f'UNRESOLVED [{n}] in {where}')
    return re.sub(r'\[([^\[\]]+)\]', sub, f)


def role_type(dt, kind):
    if kind == 'agg': return 'measure', ('quantitative' if dt in ('integer', 'real') else 'nominal')
    if dt in ('integer', 'real'): return 'measure', 'quantitative'
    return ('dimension', 'ordinal') if dt == 'date' else ('dimension', 'nominal')


FMT = {'Sk Tip Share': 'p0%'}
changed = 0
for cap in [c for c in SPEC if c in cap2int]:
    dt, kind, f = SPEC[cap]; role, typ = role_type(dt, kind); iid = cap2int[cap]
    body = esc('// ' + cap + '\n' + resolve(f, cap))
    pat = re.compile(r"<column caption='" + re.escape(esc(cap)) + r"' datatype='\w+'((?: default-format='[^']*')?) name='\[" + iid +
                     r"\]' role='\w+' type='\w+'>(\s*)<calculation class='tableau' formula='([^']*)' />")
    def sub(m, cap=cap, dt=dt, role=role, typ=typ, iid=iid, body=body):
        global changed
        if m.group(3) != body: changed += 1
        return f"<column caption='{esc(cap)}' datatype='{dt}'{m.group(1)} name='[{iid}]' role='{role}' type='{typ}'>{m.group(2)}<calculation class='tableau' formula='{body}' />"
    s, k = pat.subn(sub, s)
    assert k >= 1, cap
for cap in OBSOLETE:
    if cap in cap2int:
        iid = cap2int[cap]
        s = re.sub(r"\n[ \t]*<column caption='[^']*' datatype='\w+'(?: default-format='[^']*')? name='\[" + iid + r"\]'[^>]*>\s*<calculation[^>]*/>\s*</column>", '', s)
        s = re.sub(r"\n[ \t]*<column-instance column='\[" + iid + r"\]'[^>]*/>", '', s)
        s = re.sub(r"\n[ \t]*<field>[^<]*:" + iid + r":[a-z]+\]</field>", '', s)
if new:
    a, b = bounds()
    g = min(c for c in (s.find('\n      <column-instance ', a, b), s.find('\n      <group ', a, b)) if c != -1) + 1
    add = ''
    for c in new:
        dt, kind, f = SPEC[c]; role, typ = role_type(dt, kind)
        fmt = f" default-format='{FMT[c]}'" if c in FMT else ''
        add += (f"      <column caption='{esc(c)}' datatype='{dt}'{fmt} name='[{cid[c]}]' role='{role}' type='{typ}'>\n"
                f"        <calculation class='tableau' formula='{esc('// ' + c + chr(10) + resolve(f, c))}' />\n      </column>\n")
    s = s[:g] + add + s[g:]
maps = ''.join(f"            <map to='{v.lower()}'>\n              <bucket>&quot;{k}&quot;</bucket>\n            </map>\n" for k, v in PALETTE.items())
maps += "            <map to='#bab0ac'>\n              <bucket>%null%</bucket>\n            </map>\n"
cc = cap2int['Sk Colour']
s, k = re.subn(r"(<encoding attr='color' field='\[none:" + cc + r":nk\]' type='palette'>\n)(.*?)(\s*</encoding>)",
               lambda m: m.group(1) + maps.rstrip('\n') + m.group(3), s, count=1, flags=re.S)
assert k == 1
open(out, 'w', encoding='utf-8').write(s)
print(f'{changed} stored formula copies changed (data source and sheets), {len(new)} added, {len([c for c in OBSOLETE if c in cap2int])} removed; palette of {len(PALETTE)}')
