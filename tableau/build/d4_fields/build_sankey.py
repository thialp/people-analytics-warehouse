"""Add the native Sankey to the Dashboard #4 workbook (build doc section 9N).

  python3 build_sankey.py "in.twb" "out.twb"            (close Tableau first)

1. puts tableau/custom_sql_cw_reconciliation_dashboard.sql (with flag_short and the Sankey scaffold)
   into both copies of the Custom SQL in the workbook, and registers its four new columns
   (flag_short, sk_part, sk_level, sk_point) in the live connection's metadata; an extract refresh
   in Tableau then rebuilds the extract with them;
2. adds the parameters and Sk calcs of spec_sankey.py. Existing fields are only read: the extension
   Sankey (version A) and everything it uses stay as they are.
It stops if a reference does not resolve or an Sk field already exists.
"""
import os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from spec_sankey import PARAMS, C

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
SQL = open(os.path.join(HERE, '..', '..', 'custom_sql_cw_reconciliation_dashboard.sql'), encoding='utf-8').read().rstrip('\n')
DS = re.search(r"<datasource caption='CW Reconciliation' inline='true' name='([^']+)'", s).group(1)


def esc_attr(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '&apos;').replace('"', '&quot;').replace('\n', '&#10;'))


def esc_text(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace("'", '&apos;').replace('"', '&quot;')


def unesc(t):
    return t.replace('&apos;', "'").replace('&quot;', '"').replace('&lt;', '<').replace('&gt;', '>').replace('&amp;', '&')


# ---------- what the workbook has
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_end = s.index('</datasource>', ds_start)
cap2int = {}
for m in re.finditer(r"<column caption='([^']*)' datatype='\w+'(?: default-format='[^']*')? name='\[(Calculation_\d+)\]'", s[ds_start:ds_end]):
    cap2int[unesc(m.group(1))] = m.group(2)
pds = re.search(r"<datasource hasconnection='false' inline='true' name='Parameters' version='[^']+'>.*?</datasource>", s, re.S)
params = {unesc(m.group(1)): m.group(2) for m in re.finditer(r"<column caption='([^']*)' datatype='\w+'[^>]*? name='\[([^\]]+)\]'", pds.group(0))}
NEWCOLS = [('flag_short', 'string'), ('sk_part', 'string'), ('sk_level', 'integer'), ('sk_point', 'integer')]
sqlcols = set(re.findall(r"<local-name>\[([^\]]+)\]</local-name>", s[ds_start:ds_end])) | {c for c, _ in NEWCOLS}
for cap, *_ in C:
    assert cap not in cap2int, f'already in the workbook: {cap}'
for p, *_ in PARAMS:
    assert p not in params, f'parameter already in the workbook: {p}'
assert not re.search(r"<local-name>\[flag_short\]</local-name>", s), 'flag_short already registered'

pid = {p[0]: f'Parameter 07251027{i:08d}' for i, p in enumerate(PARAMS, 1)}
cid = {cap: f'Calculation_07251027{i:08d}' for i, (cap, *_) in enumerate(C, 1)}
allparams = {**params, **pid}
allcalcs = {**cap2int, **cid}


def resolve(f, where):
    def sub(m):
        n = m.group(1)
        if n in allparams: return f'[Parameters].[{allparams[n]}]'
        if n in allcalcs: return f'[{allcalcs[n]}]'
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
def col_xml(cap, dt, kind, f, ind='      '):
    role, typ = role_type(dt, kind)
    fmt = f" default-format='{FMT[cap]}'" if cap in FMT else ''
    body = esc_attr(f'// {cap}\n' + resolve(f, cap))
    return (f"{ind}<column caption='{esc_attr(cap)}' datatype='{dt}'{fmt} name='[{cid[cap]}]' role='{role}' type='{typ}'>\n"
            f"{ind}  <calculation class='tableau' formula='{body}' />\n{ind}</column>\n")


# ---------- 1. the Custom SQL, both copies
rel = re.compile(r"(<relation connection='[^']+' name='Custom SQL Query' type='text'>)(.*?)(</relation>)", re.S)
s, n = rel.subn(lambda m: m.group(1) + esc_text(SQL) + m.group(3), s)
assert n == 2, f'expected two copies of the Custom SQL, found {n}'

# ---------- 2. the new columns in the live connection's metadata (after load_note)
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
mr_end = s.index('</metadata-records>', ds_start)
last_ord = max(int(x) for x in re.findall(r"<ordinal>(\d+)</ordinal>", s[ds_start:mr_end]))
obj = re.search(r"<object-id>(\[_[0-9A-F]+\])</object-id>", s[ds_start:mr_end]).group(1)
recs = ''
for k, (c, t) in enumerate(NEWCOLS, 1):
    if t == 'string':
        body = (f"            <remote-type>130</remote-type>\n            <local-name>[{c}]</local-name>\n"
                f"            <parent-name>[Custom SQL Query]</parent-name>\n            <remote-alias>{c}</remote-alias>\n"
                f"            <ordinal>{last_ord + k}</ordinal>\n            <local-type>string</local-type>\n"
                f"            <aggregation>Count</aggregation>\n            <width>4000</width>\n            <contains-null>true</contains-null>\n"
                f"            <padded-semantics>true</padded-semantics>\n            <collation flag='2147483649' name='LEN_RUS_S2_VWIN' />\n"
                f"            <attributes>\n              <attribute datatype='string' name='DebugRemoteType'>&quot;SQL_WVARCHAR&quot;</attribute>\n"
                f"              <attribute datatype='string' name='DebugWireType'>&quot;SQL_C_WCHAR&quot;</attribute>\n            </attributes>\n")
    else:
        body = (f"            <remote-type>3</remote-type>\n            <local-name>[{c}]</local-name>\n"
                f"            <parent-name>[Custom SQL Query]</parent-name>\n            <remote-alias>{c}</remote-alias>\n"
                f"            <ordinal>{last_ord + k}</ordinal>\n            <local-type>integer</local-type>\n"
                f"            <aggregation>Sum</aggregation>\n            <precision>10</precision>\n            <contains-null>true</contains-null>\n"
                f"            <attributes>\n              <attribute datatype='string' name='DebugRemoteType'>&quot;SQL_INTEGER&quot;</attribute>\n"
                f"              <attribute datatype='string' name='DebugWireType'>&quot;SQL_C_SLONG&quot;</attribute>\n            </attributes>\n")
    recs += (f"          <metadata-record class='column'>\n            <remote-name>{c}</remote-name>\n" + body +
             f"            <object-id>{obj}</object-id>\n          </metadata-record>\n")
s = s[:mr_end] + recs.lstrip(' ') + '        ' + s[mr_end:]

# ---------- 3. parameters
pend = s.index('</datasource>', s.index("name='Parameters' version="))
plines = ''
for cap, dt, dom, val in PARAMS:
    v = esc_attr(val)
    plines += (f"      <column caption='{cap}' datatype='{dt}' name='[{pid[cap]}]' param-domain-type='{dom}' role='measure' type='nominal' value='{v}'>\n"
               f"        <calculation class='tableau' formula='{v}' />\n      </column>\n")
s = s[:pend] + plines.lstrip(' ') + '    ' + s[pend:]

# ---------- 4. calcs, before the data source's first <group
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
ds_close = s.index('</datasource>', ds_start)
cands = [s.find(t, ds_start, ds_close) for t in ('\n      <column-instance ', '\n      <group ')]
g = min(c for c in cands if c != -1) + 1          # new columns go before any column-instance (schema order)
s = s[:g] + ''.join(col_xml(*c) for c in C) + s[g:]

open(out, 'w', encoding='utf-8').write(s)
print(f'Custom SQL replaced (2 copies), 4 columns registered (ordinals {last_ord + 1} to {last_ord + 4}), '
      f'{len(PARAMS)} parameters, {len(C)} Sk calcs')
