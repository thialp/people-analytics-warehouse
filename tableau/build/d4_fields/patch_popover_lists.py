"""Third pass (step 8): tick lists carry state in the shape, not in colour.

  python3 patch_popover_lists.py in.twb out.twb

A colour encoding tints the custom tick shapes, so Function List and Department List drop their colour field (Country
List already had; Function State / Department State stay as detail). List names get a fixed light colour.
Dim departments are shown by the d4_tick_dim shape only; the name is not dimmed.
"""
import re
import sys

s = open(sys.argv[1], encoding='utf-8').read()
n = 0
for sh in ('Function List', 'Department List', 'Country List'):
    k = s.index(f"<worksheet name='{sh}'")
    e = s.index('</worksheet>', k)
    w = s[k:e]
    w, c = re.subn(r"\n\s*<color column='[^']*' />", '', w, count=1)
    w, c2 = re.subn(r"(<customized-label>\s*<formatted-text>\s*<run )(?!fontcolor)", r"\1fontcolor='#e4e9f0' ", w, count=1)
    n += c + c2
    s = s[:k] + w + s[e:]
open(sys.argv[2], 'w', encoding='utf-8').write(s)
print('edits', n)
