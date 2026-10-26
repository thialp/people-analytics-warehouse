"""Second pass on the rail sheets, applied to the workbook Tableau saved (so the shape assignments Thiago made stay).

  python3 patch_rail_sheets.py "in.twb" "out.twb"          (close Tableau first)

 - p_ShowList back to its default (False): the page opens on Overview
 - Info Shape: both values mapped (Tableau lists only the value showing at the time)
 - capsule sheets (Close, Function, Department, Country Field, Reset): shape size 11.27 -> SIZE, so the capsule fills the 200 px item
 - dark capsules: a leading space inside the label (em space + en space), so the word clears the rounded end
 - Show Toggle: no table dividers (they drew a line above and below the pills)
"""
import re
import sys

SIZE = '13.6'
s = open(sys.argv[1], encoding='utf-8').read()


def sheet_span(name):
    a = s.index(f"<worksheet name='{name}'")
    return a, s.index('</worksheet>', a) + len('</worksheet>')


# 1. p_ShowList default
n0 = s.count("caption='p_ShowList'")
s = re.sub(r"(<column caption='p_ShowList'[^>]*?value=')true('[^>]*>\s*<calculation class='tableau' formula=')true(')", r"\1false\2false\3", s)
assert "caption='p_ShowList' datatype='boolean' name='[Parameter 0725102600000005]' param-domain-type='list' role='measure' type='nominal' value='true'" not in s

# 2. Info Shape: both values
m = re.search(r"(<encoding attr='shape' field='\[none:Calculation_0725102600000160:nk\]'[^>]*>\n)(.*?)(\n\s*</encoding>)", s, re.S)
assert m
if 'd2_info_close' not in m.group(2):
    pal = 'Arcadia D4'
    add = ("\n            <map to='Arcadia D4/d2_info_close.png'>\n              <bucket>&quot;d2_info_close&quot;</bucket>\n            </map>")
    s = s[:m.end(2)] + add + s[m.end(2):]

# 3. capsule sizes
for nm in ('Close Field', 'Function Field', 'Department Field', 'Country Field', 'Reset'):
    a, b = sheet_span(nm)
    blk = s[a:b]
    assert "<format attr='size' value='11.27" in blk, nm
    blk = re.sub(r"(<format attr='size' value=')11\.27\d*(')", r"\g<1>" + SIZE + r"\2", blk)
    s = s[:a] + blk + s[b:]

# 4. leading space in the dark capsule labels
for nm in ('Function Field', 'Department Field', 'Country Field'):
    a, b = sheet_span(nm)
    blk = s[a:b]
    if ' ' not in blk:
        blk, n = re.subn(r"(<customized-label>\s*<formatted-text>\n)(\s*)(<run )", lambda m: m.group(1) + m.group(2) + "<run fontcolor='#E4E9F0' fontname='Tableau Medium' fontsize='9'>  </run>\n" + m.group(2) + m.group(3), blk, count=1)
        assert n == 1, nm
    s = s[:a] + blk + s[b:]

# 5. Show Toggle dividers
a, b = sheet_span('Show Toggle')
blk = s[a:b]
if "element='table-div'" not in blk:
    rule = ("          <style-rule element='table-div'>\n            <format attr='stroke-size' scope='rows' value='0' />\n"
            "            <format attr='line-visibility' scope='rows' value='off' />\n"
            "            <format attr='stroke-size' scope='cols' value='0' />\n            <format attr='line-visibility' scope='cols' value='off' />\n          </style-rule>\n")
    i = blk.index("          <style-rule element='dropline'>")
    blk = blk[:i] + rule + blk[i:]
s = s[:a] + blk + s[b:]
open(sys.argv[2], 'w', encoding='utf-8').write(s)
print('patched; p_ShowList entries', n0)
