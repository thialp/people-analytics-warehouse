"""Gap List polish #2 on the Tableau-saved workbook (extension kept).
- CONTRACTOR reads worker id first, then name (the ids align top to bottom)
- soft fills: the conditional-format colours get an alpha byte (#RRGGBBAA)
- row tooltip in the Sankey tooltip style: place named in its colour, coral for worse (over 90 days, no ticket)
usage: python3 patch_gap_list_tooltip.py in.twb out.twb
"""
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
DS = 'federated.19gwunf1mzo1gq1cltitv08khlf9'
ALPHA = '40'   # 25 percent

# 1. contractor
old = "formula='// CONTRACTOR&#10;[contractor_name] + &quot; · &quot; + [bw_worker_id]'"
assert old in t
t = t.replace(old, "formula='// Contractor&#10;[bw_worker_id] + &quot; · &quot; + [contractor_name]'")

# 2. new tooltip calcs
Q = '&quot;'
CALCS = [  # (id, caption, formula)
    ('0725102600000330', 'GT Place BW', 'IF [place] = %sBridgeway%s THEN %sBridgeway (vendor system)%s END' % (Q, Q, Q, Q)),
    ('0725102600000331', 'GT Place KS', 'IF [place] = %sKeystone%s THEN %sKeystone (HR system)%s END' % (Q, Q, Q, Q)),
    ('0725102600000332', 'GT Place SF', 'IF [place] = %sSystem feed%s THEN %sSystem feed (integration)%s END' % (Q, Q, Q, Q)),
    ('0725102600000333', 'GT Days Hot', 'IF [days_open] &gt; 90 THEN %sOpen %s + STR([days_open]) + %s days%s END' % (Q, Q, Q, Q)),
    ('0725102600000334', 'GT Days Ok', 'IF [days_open] &lt;= 90 THEN %sOpen %s + STR([days_open]) + %s days%s END' % (Q, Q, Q, Q)),
    ('0725102600000335', 'GT Ticket Hot', 'IF ISNULL([ticket_number]) THEN %sNo linked ticket%s END' % (Q, Q)),
    ('0725102600000336', 'GT Ticket Ok', 'IF NOT ISNULL([ticket_number]) THEN [ticket_number] + %s %s + IFNULL([ticket_title], %s%s) + %s · %s + IFNULL([ticket_status], %s%s) END' % (Q, Q, Q, Q, Q, Q, Q, Q)),
]
# the formulas above embed STR(...) pieces; fix the quoting of the Open/days strings
def mk(i, cap, f):
    f = f.replace('%sOpen %s' % (Q, Q), Q + 'Open ' + Q)  # no-op safety
    return ("      <column caption='%s' datatype='string' name='[Calculation_%s]' role='dimension' type='nominal'>\n"
            "        <calculation class='tableau' formula='// %s&#10;%s' />\n      </column>\n") % (cap, i, cap, f)
CALCS[3] = (CALCS[3][0], CALCS[3][1], 'IF [days_open] &gt; 90 THEN %sOpen %s + STR([days_open]) + %s days%s END' % (Q, Q, Q, Q))
# build the day formulas by hand to keep the quotes right
CALCS[3] = ('0725102600000333', 'GT Days Hot', 'IF [days_open] &gt; 90 THEN &quot;Open &quot; + STR([days_open]) + &quot; days&quot; END')
CALCS[4] = ('0725102600000334', 'GT Days Ok', 'IF [days_open] &lt;= 90 THEN &quot;Open &quot; + STR([days_open]) + &quot; days&quot; END')
CALCS[6] = ('0725102600000336', 'GT Ticket Ok', 'IF NOT ISNULL([ticket_number]) THEN [ticket_number] + &quot; &quot; + IFNULL([ticket_title], &quot;&quot;) + &quot; · &quot; + IFNULL([ticket_status], &quot;&quot;) END')
block = ''.join(mk(*c) for c in CALCS)
anchor = "      <column caption='Days open' datatype='integer' name='[Calculation_0725102600000188]' role='measure' type='quantitative'>"
assert t.count(anchor) >= 1
k = t.index(anchor)
t = t[:k] + block + t[k:]

# 3. Gap List worksheet
i = t.index("<worksheet name='Gap List'"); j = t.index('</worksheet>', i)
w = t[i:j]
# dependencies
a2 = anchor
assert a2 in w, 'worksheet dependency anchor'
dep_cols = ''.join(mk(*c).replace('      <column', '            <column', 1) for c in CALCS)
w = w.replace(a2, dep_cols + a2, 1) if False else w
inst = ''.join("            <column-instance column='[Calculation_%s]' derivation='Attribute' name='[attr:Calculation_%s:nk]' pivot='key' type='nominal' />\n" % (c[0], c[0]) for c in CALCS)
k = w.index(anchor.strip())
k = w.rindex('\n', 0, k) + 1
w = w[:k] + dep_cols + inst + w[k:]
# tooltip encodings
tip = ''.join("              <tooltip _.fcp.VizExtensionsDupEncodingUUID.true...encoding-id='{%s}' column='[%s].[attr:Calculation_%s:nk]' />\n" % (str(uuid.uuid4()).upper(), DS, c[0]) for c in CALCS)
w = w.replace('            </encodings>', tip + '            </encodings>', 1)
# the tooltip text
def F(n): return '<[%s].[attr:%s:nk]>' % (DS, n)
def run(txt, color, font='Tableau Book', size=9): return "                <run fontcolor='%s' fontname='%s' fontsize='%s'><![CDATA[%s]]></run>\n" % (color, font, size, txt)
NL = "                <run>Æ&#10;</run>\n"
NAVY, SLATE, CORAL, BW, KS, SF = '#13233a', '#5a6171', '#b8401f', '#b86400', '#5650a0', '#0e7d5f'
c = lambda n: F('Calculation_' + n)
x = "            <customized-tooltip show-buttons='false'>\n              <formatted-text>\n"
x += run(F('contractor_name'), NAVY, 'Tableau Semibold', 10) + NL
x += run(F('bw_worker_id') + ' · ' + F('person_id') + ' · ' + F('supplier_name'), SLATE) + NL
x += run('Aligned in: ', NAVY) + run(c('0725102600000330'), BW, 'Tableau Semibold') + run(c('0725102600000331'), KS, 'Tableau Semibold') + run(c('0725102600000332'), SF, 'Tableau Semibold') + NL
x += run(F('flag_name'), NAVY, 'Tableau Semibold') + run(' · puts at risk ', SLATE) + run(F('risk'), NAVY, 'Tableau Semibold') + NL
x += run('Keystone shows: ' + F('keystone_shows'), NAVY) + NL
x += run('Bridgeway has: ' + F('bridgeway_has'), NAVY) + NL
x += run('Evidence: ' + F('evidence'), NAVY) + NL
x += run(c('0725102600000333'), CORAL, 'Tableau Semibold') + run(c('0725102600000334'), NAVY, 'Tableau Semibold') + NL
x += run(c('0725102600000335'), CORAL, 'Tableau Semibold') + run(c('0725102600000336'), NAVY) + NL
x += run('Next step: ' + F('next_step'), SLATE)
x += "              </formatted-text>\n            </customized-tooltip>"
w, n = re.subn(r"<customized-tooltip.*?</customized-tooltip>", lambda m: x, w, count=1, flags=re.S)
assert n == 1
# soft fills
for col in ['f89217', '7873c0', '21b087', 'b8401f']:
    pat = '\\&quot;#%s\\&quot;' % col
    assert w.count(pat) == 1, (col, w.count(pat))
    w = w.replace(pat, '\\&quot;#%s%s\\&quot;' % (col, ALPHA))
t = t[:i] + w + t[j:]
open(dst, 'w', encoding='utf-8').write(t)
print('ok')
