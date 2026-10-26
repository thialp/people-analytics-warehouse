"""Run the native Sankey's Tableau formulas on the DuckDB mart and draw what Tableau should draw.

  python3 verify_sankey.py 2026-06-30 "" > sankey.svg          (close, p_Functions value)

Each calc is translated to SQL (FIXED LODs become window aggregates over the whole table, which is
what a FIXED LOD is when no context filter applies) and computed in dependency order, one column
per calc. Only the numeric and boolean fields the geometry needs are translated, so a pass is
evidence that the formulas place every point where the design says.
"""
import os, re, sys
import duckdb
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import spec, spec_sankey

CLOSE = sys.argv[1] if len(sys.argv) > 1 else '2026-06-30'
FUNCS = sys.argv[2] if len(sys.argv) > 2 else ''
PARAM = {'p_Close': f"DATE '{CLOSE}'", 'p_Functions': f"'{FUNCS}'", 'p_Departments': "''", 'p_Countries': "''",
         'p_SkFlag': "''", 'p_SkRisk': "''", 'p_SkPlace': "''"}
F = {c[0]: c[3] for c in spec.C + spec_sankey.C}
# DuckDB evaluates COUNT(DISTINCT) as a window very slowly; these three count the non-empty nodes, so the
# check uses the equivalent sum (every other formula runs as written)
for col, n in (("F", 9), ("R", 5), ("P", 3)):
    F[f"Sk N{col}"] = " + ".join(f"IIF([Sk {col}{k}] > 0, 1, 0)" for k in range(1, n + 1))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))


def match(s, i, o='(', c=')'):
    d = 0
    for j in range(i, len(s)):
        if s[j] == o: d += 1
        elif s[j] == c:
            d -= 1
            if d == 0: return j
    raise ValueError(s)


def split_args(s):
    out, d, cur = [], 0, ''
    for ch in s:
        if ch in '({': d += 1
        if ch in ')}': d -= 1
        if ch == ',' and d == 0: out.append(cur); cur = ''
        else: cur += ch
    return out + [cur]


def fn(s, name, conv):
    while True:
        m = re.search(r'\b' + name + r'\(', s)
        if not m: return s
        a = m.end() - 1; b = match(s, a)
        s = s[:m.start()] + conv(split_args(s[a + 1:b])) + s[b + 1:]


def to_sql(f, deps):
    f = re.sub(r'//[^\n]*', '', f)
    f = re.sub(r'"([^"]*)"', lambda m: "'" + m.group(1).replace("'", "''") + "'", f)
    def ref(m):
        n = m.group(1)
        if n in PARAM: return PARAM[n]
        if n in F: deps.add(n); return f'"{n}"'
        return f'"{n}"'
    f = re.sub(r'\[([^\[\]]+)\]', ref, f)
    while '{' in f:                                    # FIXED LODs, innermost first is not needed: none nest
        a = f.index('{'); b = match(f, a, '{', '}')
        inner = f[a + 1:b]
        dims, agg = inner.split(':', 1)
        dims = dims.replace('FIXED', '').strip()
        part = f' PARTITION BY {dims}' if dims else ''
        agg = agg.strip()
        over = f' OVER ({part.strip()})'
        for fn_ in ('SUM', 'MIN', 'MAX', 'COUNTD'):           # every aggregate in the LOD becomes a window
            i = 0
            while True:
                m = re.search(r'\b' + fn_ + r'\(', agg[i:])
                if not m: break
                st = i + m.end() - 1; en = match(agg, st)
                agg = agg[:en + 1] + over + agg[en + 1:]; i = en + 1 + len(over)
        f = f[:a] + f'({agg})' + f[b + 1:]
    f = fn(f, 'IIF', lambda a: f'(CASE WHEN {a[0]} THEN {a[1]} ELSE {a[2]} END)')
    f = fn(f, 'COUNTD', lambda a: f'COUNT(DISTINCT {a[0]})')
    f = fn(f, 'ZN', lambda a: f'COALESCE({a[0]}, 0)')
    f = fn(f, 'IFNULL', lambda a: f'COALESCE({a[0]}, {a[1]})')
    f = fn(f, 'FLOAT', lambda a: f'CAST({a[0]} AS DOUBLE)')
    f = fn(f, 'INT', lambda a: f'CAST(TRUNC(CAST({a[0]} AS DOUBLE)) AS INTEGER)')
    f = fn(f, 'MID', lambda a: f'SUBSTRING({a[0]}, {a[1]}, {a[2]})')
    f = fn(f, 'CONTAINS', lambda a: f"contains({a[0].replace('+', '||')}, {a[1].replace('+', '||')})")
    f = re.sub(r'\bELSEIF\b', 'WHEN', f)
    f = re.sub(r'(?<![A-Z])IF\b', 'CASE WHEN', f)
    return f


NEED = ['Sk X', 'Sk Y', 'Sk Show', 'Sk Draw', 'Sk N', 'Sk Node H']
sql, order, seen = {}, [], set()
def visit(n):
    if n in seen: return
    seen.add(n)
    deps = set()
    sql[n] = to_sql(F[n], deps)
    for d in sorted(deps): visit(d)
    order.append(n)
for n in NEED: visit(n)

con = duckdb.connect()
con.execute(f"ATTACH '{os.path.join(ROOT, 'warehouse', 'arcadia.duckdb')}' AS w (READ_ONLY)")
con.execute("CREATE TABLE t0 AS SELECT * FROM w.marts.mart_cw_reconciliation_dashboard")
for i, n in enumerate(order):                       # one table per step: a flat plan, however deep the chain
    con.execute(f'CREATE TABLE t{i + 1} AS SELECT *, {sql[n]} AS "{n}" FROM t{i}')
    con.execute(f'DROP TABLE t{i}')
q = f'SELECT * FROM t{len(order)}'
rows = con.execute(f"""SELECT sk_part, sk_level, flag_code, risk, place, sk_point, "Sk X", "Sk Y", "Sk Draw", "Sk N", "Sk Node H"
                       FROM ({q}) WHERE row_type = 'Sankey' AND "Sk Show" ORDER BY "Sk Draw", sk_part, sk_level, flag_code, risk, place, sk_point""").fetchall()
FCOL = spec_sankey.FLAG_COLOURS
PCOL = {'Bridgeway': '#F89217', 'Keystone': '#7873C0', 'System feed': '#21B087'}
SHORT = dict(con.execute("SELECT DISTINCT flag_code, flag_short FROM w.marts.mart_cw_reconciliation_dashboard WHERE flag_short IS NOT NULL").fetchall())
PL = {'Bridgeway': 'Bridgeway (vendor system)', 'Keystone': 'Keystone (HR system)', 'System feed': 'System feed (integration)'}
polys, labels = {}, []
for part, lvl, f, r, p, pt, x, y, draw, n, nh in rows:
    if part in ('Link', 'Node'):
        polys.setdefault((draw, part, lvl, f, r, p), []).append((pt, x, y))
    else:
        labels.append((part, lvl, f, r, p, pt, x, y, n))
svg = []
for key in sorted(polys, key=lambda k: (k[0], k[1])):
    draw, part, lvl, f, r, p = key
    pts = sorted(polys[key])
    if part == 'Link':
        col, op = (FCOL[f], 0.45) if lvl == 1 else ('#4F6980', 0.45)
    else:
        col, op = ({1: FCOL.get(f), 2: '#4F6980', 3: PCOL.get(p)}[lvl], 1)
    svg.append(f'<polygon points="{" ".join(f"{x:.1f},{y:.1f}" for _, x, y in pts)}" fill="{col}" fill-opacity="{op}"/>')
for part, lvl, f, r, p, pt, x, y, n in labels:
    if part == 'Header':
        t, fill, size = {1: 'What differs', 2: 'What it puts at risk', 3: 'Where it is aligned'}[lvl], '#2B2F36', 9
    else:
        t = ({1: SHORT.get(f), 2: r, 3: PL.get(p)}[lvl]) if pt == 0 else f'({n})'
        fill, size = ('#FFFFFF' if lvl == 2 else '#13233A'), 10.5
    svg.append(f'<text x="{x:.1f}" y="{y + 3.5:.1f}" font-size="{size}" text-anchor="middle" fill="{fill}">{t}</text>')
print(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 726 540" width="726" height="540" font-family="Helvetica"><rect width="726" height="540" fill="#fff"/>{"".join(svg)}</svg>')
print(f'{len(order)} calcs computed; {len(polys)} polygons, {len(labels)} labels', file=sys.stderr)
