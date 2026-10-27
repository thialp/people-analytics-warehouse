"""Round 16 fixes for Dashboard #4 (from Thiago's review of rev 28).
usage: patch_feedback_round_16.py in.twb out.twb
"""
import re, sys
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
def sub1(old, new, cnt=1):
    global t
    assert t.count(old) >= 1, old[:80]
    t = t.replace(old, new, cnt)

# 1. Department tick: two states (in the current filter = on, else off) and a repaired shape map
sub1("IF [Calculation_0725102600000040] THEN &quot;d4_tick_on&quot; ELSEIF [Calculation_0725102600000042] THEN &quot;d4_tick_off&quot; ELSE &quot;d4_tick_dim&quot; END",
     "IF [Calculation_0725102600000042] AND ([Parameters].[Parameter 0725102600000003] = &quot;&quot; OR [Calculation_0725102600000040]) THEN &quot;d4_tick_on&quot; ELSE &quot;d4_tick_off&quot; END")
sub1("""<map to='Arcadia D4/d4_tick_on.png'>
              <bucket>&quot;d4_tick_dim&quot;</bucket>
            </map>
            <map to='plus'>
              <bucket>&quot;d4_tick_on&quot;</bucket>
            </map>""",
     """<map to='Arcadia D4/d4_tick_on.png'>
              <bucket>&quot;d4_tick_on&quot;</bucket>
            </map>""")

# 2. Ticket Rows zone had zero height
sub1("<zone h='0' id='303' name='Ticket Rows' show-title='false' w='6857' x='74071' y='68823'>\n                <layout-cache type-h='cell' type-w='fixed' />",
     "<zone h='24706' id='303' name='Ticket Rows' show-title='false' w='6857' x='74071' y='68823'>\n                <layout-cache minheight='100' minwidth='50' type-h='scalable' type-w='fixed' />")
sub1("<zone fixed-size='280' h='0' id='303' is-fixed='true' name='Ticket Rows' show-title='false' w='6857' x='74071' y='68823'>",
     "<zone h='24706' id='303' name='Ticket Rows' show-title='false' w='6857' x='74071' y='68823'>")

# 3. Ticket dots: larger, opaque
sub1("<format attr='size' value='0.12' />\n                <format attr='mark-labels-show' value='false' />\n                <format attr='mark-transparency' value='230' />",
     "<format attr='size' value='0.4' />\n                <format attr='mark-labels-show' value='false' />\n                <format attr='mark-transparency' value='255' />\n                <format attr='has-stroke' value='true' />\n                <format attr='stroke-color' value='#ffffff' />")

# 4. KPI 2 title shorter
sub1("&quot;Gap rate at the close · target &quot; + [Calculation_0725102600000087]", "&quot;Gap rate · target &quot; + [Calculation_0725102600000087]")

# 5. Load note: remove zones, visibility wiring
def remove_zone(text, zid, count_all=True):
    out = text
    while True:
        m = re.search(r"[ \t]*<zone [^>]*\bid='%s'[^>]*>" % zid, out)
        if not m: return out
        i = m.start(); j = m.end()
        if out[m.end()-2:m.end()] == '/>':
            out = out[:i] + out[j:].lstrip('\n'); continue
        depth = 1; pos = j
        while depth:
            a = out.find('<zone ', pos); b = out.find('</zone>', pos)
            if a != -1 and a < b:
                e = out.find('>', a); depth += 0 if out[e-1] == '/' else 1; pos = e + 1
            else:
                depth -= 1; pos = b + 7
        out = out[:i] + out[pos:].lstrip('\n')
t = remove_zone(t, '307')
t = remove_zone(t, '308')
lines = t.split('\n')
bad = ("node-guid='11127101-d5e0", "node-guid='9b9d735a-d238", "to='205756bc-011f")
lines = [l for l in lines if not any(b in l for b in bad)]
t = '\n'.join(lines)

# 6. Sankey tooltip colours (prototype palette)
k = t.index("<worksheet name='Sankey Native'>"); e = t.index('</worksheet>', k); w = t[k:e]
a = w.index("<pane id='1'"); b = w.index('</customized-tooltip>', a); tip = w[a:b]
def recolour(tip, calc, color, name=None, size='10', italic=False):
    pat = re.compile(r"<run ([^>]*)><!\[CDATA\[((?:(?!\]\]>).)*?Calculation_0725102700000%s:(?:(?!\]\]>).)*?)\]\]>" % calc, re.S)
    def f(m):
        attrs = "fontcolor='%s'" % color
        if name: attrs += " fontname='%s'" % name
        attrs += " fontsize='%s'" % size
        if italic: attrs += " italic='true'"
        return "<run %s><![CDATA[%s]]>" % (attrs, m.group(2))
    new, n = pat.subn(f, tip); assert n >= 1, calc; return new
tip = recolour(tip, '091', '#13233a', 'Tableau Semibold', '13')
tip = recolour(tip, '092', '#5a6170', None, '10', True)
tip = recolour(tip, '093', '#13233a', 'Tableau Semibold', '10')
tip = recolour(tip, '094', '#13233a', 'Tableau Semibold', '10')
for c in ('101', '105'): tip = recolour(tip, c, '#5a6170', None, '10')
tip = recolour(tip, '102', '#b8401f', 'Tableau Semibold', '10')
tip = recolour(tip, '103', '#0e7d5f', 'Tableau Semibold', '10')
tip = recolour(tip, '104', '#5a6170', None, '10')
tip = recolour(tip, '106', '#2b2f36', 'Tableau Semibold', '10')
tip = recolour(tip, '117', '#5a6170', None, '10')
tip = recolour(tip, '111', '#5a6170', None, '10')
tip = recolour(tip, '112', '#b86400', 'Tableau Semibold', '10')
tip = recolour(tip, '113', '#5650a0', 'Tableau Semibold', '10')
tip = recolour(tip, '114', '#0e7d5f', 'Tableau Semibold', '10')
tip = recolour(tip, '131', '#5a6170', None, '10')
tip = recolour(tip, '126', '#b8401f', 'Tableau Semibold', '10')
tip = recolour(tip, '127', '#b8401f', 'Tableau Semibold', '10')
tip = recolour(tip, '133', '#5a6170', None, '10', True)
w = w[:a] + tip + w[b:]
t = t[:k] + w + t[e:]

# 7. Timeline: non-current dots hollow (white fill, navy outline), selected dot navy
anchor = t.index("<encoding attr='color' field='[none:Calculation_0725102700000084:nk]' type='palette'>")
pal = """<encoding attr='color' field='[usr:Calculation_0725102600000200:nk]' type='palette'>
            <map to='#13233a'>
              <bucket>&quot;selected above&quot;</bucket>
            </map>
            <map to='#13233a'>
              <bucket>&quot;selected below&quot;</bucket>
            </map>
            <map to='#ffffff'>
              <bucket>&quot;other&quot;</bucket>
            </map>
          </encoding>
          """
t = t[:anchor] + pal + t[anchor:]
open(dst, 'w', encoding='utf-8').write(t)
print('ok')
