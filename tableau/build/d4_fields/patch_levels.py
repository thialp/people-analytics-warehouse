"""Take the counts out of the Sankey's three level fields (build doc 9.3 fallback).

The Sankey extension saves each node colour under the node's full text. With the count in the
text ("One person, two IDs (28)") a node is a different node at every close and under every
filter, so its colour resets. This patch makes the three level fields plain names and rewrites the
extension's saved colour map to match, so the colours already chosen carry over.

  python3 patch_levels.py "in.twb" "out.twb"      (close Tableau first)
"""
import re, sys, json, html

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '&apos;').replace('"', '&quot;').replace('\n', '&#10;'))


def iid(cap):
    m = re.search(r"<column caption='" + re.escape(cap) + r"'[^>]*? name='\[(Calculation_\d+)\]'", s)
    assert m, f'missing calc {cap}'
    return m.group(1)


ID = {c: iid(c) for c in ('What differs', 'What it puts at risk', 'Where it is aligned',
                         'Sankey Anchor', 'First Flag', 'First Risk', 'Sankey Gap Row')}
assert "caption='First Flag Name'" not in s, 'already patched'
NEW = 'Calculation_0725102600000301'
DS = re.search(r"<datasource caption='CW Reconciliation' inline='true' name='([^']+)'", s).group(1)

NEW_CALC = ('First Flag Name', 'string',
            f"{{ FIXED : MIN(IF [{ID['Sankey Gap Row']}] AND [flag_label] = [{ID['First Flag']}] THEN [flag_name] END) }}")

FORMULAS = {
    'What differs': f"IF [{ID['Sankey Anchor']}] THEN [{NEW}] ELSE [flag_name] END",
    'What it puts at risk': f"IF [{ID['Sankey Anchor']}] THEN [{ID['First Risk']}] ELSE [risk] END",
    'Where it is aligned': "[place_label]",
}


def col(ind):
    cap, dt, f = NEW_CALC
    return (f"{ind}<column caption='{cap}' datatype='{dt}' name='[{NEW}]' role='dimension' type='nominal'>\n"
            f"{ind}  <calculation class='tableau' formula='{esc('// ' + cap + chr(10) + f)}' />\n{ind}</column>\n")


# 1. new calc: data source (before its first <group) and the Sankey sheet's dependencies
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
g = s.index('      <group ', ds_start)
s = s[:g] + col('      ') + s[g:]
ws = s.index("<worksheet name='Sankey'>")
dep = s.index(f"<datasource-dependencies datasource='{DS}'>", ws)
dep_end = s.index('</datasource-dependencies>', dep)
first_col = s.index('            <column ', dep)
s = s[:first_col] + col('            ') + s[first_col:]

# 2. the three level formulas, in the data source and in every sheet copy
for cap, f in FORMULAS.items():
    pat = re.compile(r"(<column caption='" + re.escape(cap) + r"'[^>]*name='\[" + ID[cap] +
                     r"\]'[^>]*>\s*<calculation class='tableau' formula=')([^']*)(' />)")
    s, n = pat.subn(lambda m: m.group(1) + esc(f'// {cap}\n{f}') + m.group(3), s)
    assert n >= 1, cap

# 3. colour map: strip the trailing count, keep the first colour chosen for each name
m = re.search(r"(<setting key='color-map' value=')([^']*)(' />)", s)
cmap = json.loads(html.unescape(m.group(2)))
new = {}
for level, pairs in cmap.items():
    seen = {}
    for name, colour in pairs:
        base = re.sub(r' \(\d+\)$', '', name)
        seen.setdefault(base, colour)
    new[level] = [[k, v] for k, v in seen.items()]
s = s[:m.start(2)] + esc(json.dumps(new, separators=(',', ':'))) + s[m.end(2):]
open(out, 'w', encoding='utf-8').write(s)
for level, pairs in new.items():
    print(level)
    for k, v in pairs:
        print('   ', v.ljust(18), k)
