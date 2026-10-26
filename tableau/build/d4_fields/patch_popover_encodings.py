"""Second pass on a Tableau-saved workbook after the popover sheets (step 8).

  python3 patch_popover_encodings.py in.twb out.twb

Tableau keeps a colour / shape assignment only after it has seen the field assigned in the app. So this works on the
file Tableau saved after the first hand assignments (Function State, Function Tick Shape, Close State): it rewrites those
three with their full maps and adds the same entries, in the format Tableau wrote, for Department State, Country State,
Department Tick Shape and Country Tick Shape. It also pushes list labels off the tick (em spaces inside the label run).
"""
import re
import sys

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
PFX = '[none:Calculation_0725102600000'


def pal(n, maps):
    x = f"          <encoding attr='color' field='{PFX}{n}:nk]' type='palette'>\n"
    for b, c in maps:
        x += f"            <map to='{c}'>\n              <bucket>&quot;{b}&quot;</bucket>\n            </map>\n"
    return x + "          </encoding>\n"


def shp(n, names):
    x = f"          <encoding attr='shape' field='{PFX}{n}:nk]' type='shape'>\n"
    for b in names:
        x += f"            <map to='Arcadia D4/{b}.png'>\n              <bucket>&quot;{b}&quot;</bucket>\n            </map>\n"
    return x + "          </encoding>\n"


NEW = {
    ('color', '169'): pal('169', [('current', '#ffffff'), ('on', '#b8c0cc')]),
    ('color', '043'): pal('043', [('off', '#b8c0cc'), ('on', '#ffffff')]),
    ('shape', '046'): shp('046', ['d4_tick_off', 'd4_tick_on']),
    ('color', '044'): pal('044', [('dim', '#56657e'), ('off', '#b8c0cc'), ('on', '#ffffff')]),
    ('color', '045'): pal('045', [('off', '#b8c0cc'), ('on', '#ffffff')]),
    ('shape', '047'): shp('047', ['d4_tick_dim', 'd4_tick_off', 'd4_tick_on']),
    ('shape', '048'): shp('048', ['d4_tick_off', 'd4_tick_on']),
}
ds = s.index("<datasource caption='CW Reconciliation' inline='true'")
rule0 = s.index("<style-rule element='mark'>", ds)
rule1 = s.index('</style-rule>', rule0)
rule = s[rule0:rule1]
for (attr, n), x in NEW.items():
    pat = re.compile(r"          <encoding attr='" + attr + "' field='" + re.escape(f"{PFX}{n}:nk]") + r"'[^>]*>.*?</encoding>\n", re.S)
    if pat.search(rule):
        rule = pat.sub(lambda m: x, rule, count=1)
    else:
        rule = rule[:rule.rindex('\n', 0, len(rule)) + 1] + x if rule.endswith('\n') or True else rule
s = s[:rule0] + rule + s[rule1:]

# list labels: two em spaces in front of the name, inside the same run
n = 0
for sh in ('Function List', 'Department List', 'Country List'):
    k = s.index(f"<worksheet name='{sh}'")
    e = s.index('</worksheet>', k)
    w = s[k:e]
    w2, c = re.subn(r"(<customized-label>\s*<formatted-text>\s*<run [^>]*>)(?:  )?(<!\[CDATA\[)", lambda m: m.group(1) + '  ' + m.group(2), w, count=1)
    n += c
    s = s[:k] + w2 + s[e:]
open(out, 'w', encoding='utf-8').write(s)
print('encodings set', len(NEW), 'labels padded', n)
