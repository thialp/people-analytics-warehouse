import re, sys
sys.path.insert(0, __import__('os').path.dirname(__file__))
from spec import PARAMS, C, EXISTING

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
DS = 'federated.19gwunf1mzo1gq1cltitv08khlf9'

# --- what is in the workbook now
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_end = s.index('</datasource>', ds_start)
ds_xml = s[ds_start:ds_end]
existing = {}  # caption -> internal
for m in re.finditer(r"<column caption='([^']*)' datatype='\w+'(?: default-format='[^']*')? name='\[(Calculation_\d+)\]'", ds_xml):
    existing[m.group(1).replace('&apos;', "'")] = m.group(2)
sqlcols = set(re.findall(r"<local-name>\[([^\]]+)\]</local-name>", ds_xml))
assert "name='Parameters'" not in s, 'workbook already has a Parameters data source'
for cap, _, _, _ in C:
    assert cap not in existing, f'calc already exists: {cap}'
for old in EXISTING:
    assert old in existing, f'missing spike calc: {old}'

# --- internal names
pid = {p[0]: f'Parameter 07251026{i:08d}' for i, p in enumerate(PARAMS, 1)}
cid = {cap: f'Calculation_07251026{i:08d}' for i, (cap, *_) in enumerate(C, 1)}
cap2int = dict(existing)
for old, (new, _) in EXISTING.items():
    cap2int[new] = existing[old]
cap2int.update(cid)

def resolve(f, where):
    def sub(m):
        n = m.group(1)
        if n in pid: return f'[Parameters].[{pid[n]}]'
        if n in cap2int: return f'[{cap2int[n]}]'
        if n in sqlcols: return f'[{n}]'
        raise SystemExit(f'UNRESOLVED [{n}] in {where}')
    return re.sub(r'\[([^\[\]]+)\]', sub, f)

def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '&apos;').replace('"', '&quot;').replace('\n', '&#10;'))

def role_type(dt, kind):
    if kind in ('agg', 'tc'):
        return 'measure', ('quantitative' if dt in ('integer', 'real') else 'nominal')
    if dt in ('integer', 'real'): return 'measure', 'quantitative'
    if dt == 'date': return 'dimension', 'ordinal'
    return 'dimension', 'nominal'

def col_xml(cap, dt, kind, f, ind):
    role, typ = role_type(dt, kind)
    fmt = " default-format='p0.00%'" if cap in ('K Rate', 'K Rate Prior', 'TL Rate', 'K Target', 'TL Target') else ''
    body = esc(f'// {cap}\n' + resolve(f, cap))
    return (f"{ind}<column caption='{esc(cap)}' datatype='{dt}'{fmt} name='[{cid[cap]}]' role='{role}' type='{typ}'>\n"
            f"{ind}  <calculation class='tableau' formula='{body}' />\n{ind}</column>\n")

# deps of each calc (captions)
deps = {cap: set(re.findall(r'\[([^\[\]]+)\]', f)) for cap, _, _, f in C}
for old, (new, f) in EXISTING.items():
    deps[new] = set(re.findall(r'\[([^\[\]]+)\]', f))

# --- 1. Parameters data source
plines = ["    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>\n",
          "      <aliases enabled='yes' />\n"]
latest = cid['Latest Close']
for cap, dt, dom, val in PARAMS:
    role, typ = ('measure', 'quantitative') if dt == 'date' else ('measure', 'nominal')
    dvf = f" default-value-field='[{DS}].[{latest}]'" if cap == 'p_Close' else ''
    v = esc(val)
    plines.append(f"      <column caption='{cap}' datatype='{dt}'{dvf} name='[{pid[cap]}]' param-domain-type='{dom}' role='{role}' type='{typ}' value='{v}'>\n")
    plines.append(f"        <calculation class='tableau' formula='{v}' />\n")
    if dt == 'boolean':
        plines.append("        <members>\n          <member value='true' />\n          <member value='false' />\n        </members>\n")
    plines.append("      </column>\n")
plines.append("    </datasource>\n")
anchor = '\n  <datasources>\n'
assert s.count(anchor) == 1
s = s.replace(anchor, anchor + ''.join(plines), 1)

# --- 2. rewrite the existing spike calcs everywhere (data source + sheet copies)
def rewrite_existing(s):
    for old, (new, f) in EXISTING.items():
        iid = existing[old]
        pat = re.compile(r"(<column caption=')([^']*)('[^>]*name='\[" + iid + r"\]'[^>]*>\s*<calculation class='tableau' formula=')([^']*)(' />)")
        n = 0
        def sub(m):
            nonlocal n; n += 1
            return m.group(1) + esc(new) + m.group(3) + esc(f'// {new}\n' + resolve(f, new)) + m.group(5)
        s = pat.sub(sub, s)
        assert n >= 1, old
    return s
s = rewrite_existing(s)

# --- 3. new calcs into the data source, before its first <group
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
g = s.index('      <group ', ds_start)
s = s[:g] + ''.join(col_xml(cap, dt, k, f, '      ') for cap, dt, k, f in C) + s[g:]

# --- 4. Sankey sheet dependencies: add the new calcs its rewritten fields need
def closure(caps):
    seen, todo = set(), list(caps)
    while todo:
        c = todo.pop()
        for d in deps.get(c, ()):
            if d in cid and d not in seen:
                seen.add(d); todo.append(d)
    return seen
need = closure([new for _, (new, _) in EXISTING.items()])
spec_by = {c[0]: c for c in C}
dep_open = f"<datasource-dependencies datasource='{DS}'>"
ws = s.index("<worksheet name='Sankey'>")
a = s.index(dep_open, ws) + len(dep_open)
b = s.index('          </datasource-dependencies>', a)
block = s[a:b]
items = re.findall(r"\n            <column(?:-instance)? [^\n]*?/>|\n            <column [^\n]*?>\n.*?\n            </column>", block, re.S)
assert ''.join(items) == block.rstrip('\n') or ''.join(items) + '\n' == block, 'unexpected dependency layout'
present_sql = set(re.findall(r"name='\[([a-z_]+)\]'", block))
for c in sorted(need):
    items.append('\n' + col_xml(*spec_by[c], '            ').rstrip('\n'))
# SQL columns the new calcs use, if missing from the sheet copy
sqlmeta = {}
for m in re.finditer(r"\n      (<column (?:aggregation='\w+' )?datatype='\w+' name='\[([a-z_]+)\]'[^>]*/>)", s[ds_start:]):
    sqlmeta.setdefault(m.group(2), m.group(1))
used_sql = set()
for c in need | {new for _, (new, _) in EXISTING.items()}:
    used_sql |= {d for d in deps[c] if d in sqlcols}
for col in sorted(used_sql - present_sql):
    meta = s[ds_start:ds_start + 400000]
    m = re.search(r"<metadata-record class='column'>\s*<remote-name>" + col + r"</remote-name>.*?<local-type>(\w+)</local-type>", meta, re.S)
    dt = m.group(1)
    role, typ = ('measure', 'quantitative') if dt in ('integer', 'real') else ('dimension', 'ordinal' if dt == 'date' else 'nominal')
    items.append(f"\n            " + sqlmeta.get(col, f"<column datatype='{dt}' name='[{col}]' role='{role}' type='{typ}' />"))
def key(it):
    return re.search(r"name='\[([^\]]+)\]'", it).group(1)
items.sort(key=key)
s = s[:a] + ''.join(items) + '\n' + s[b:]

open(out, 'w', encoding='utf-8').write(s)
print('params', len(PARAMS), 'new calcs', len(C), 'rewritten', len(EXISTING), 'sankey deps added', len(need))
