"""Step 10/11 polish on a Tableau-saved workbook (keeps the hand-applied Tableau Table extension).

1. Gap List (Tableau Table viz extension): keep one column per field in a clean order, drop the
   leftover duplicate encodings, rename headers to sentence case, WHERE ALIGNED = place only.
2. Gap-rate target 3% -> 3.5% (workbook override; the marts carry 0.035 as well).
usage: python3 patch_gap_list_and_target.py in.twb out.twb
"""
import re, sys, json, html, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
DS = 'federated.19gwunf1mzo1gq1cltitv08khlf9'
FCP = '_.fcp.VizExtensionsDupEncodingUUID.true...encoding-id'

# ---- 1. captions and the WHERE ALIGNED formula
def recap(t, n, old, new):
    a = "<column caption='%s' datatype='string' name='[Calculation_%s]'" % (old, n)
    assert a in t, n
    return t.replace(a, a.replace("caption='%s'" % old, "caption='%s'" % new))
for n, o, nw in [('0725102600000182', 'WHERE ALIGNED', 'Where aligned'), ('0725102600000183', 'WHAT DIFFERS', 'What differs'),
                 ('0725102600000184', 'CONTRACTOR', 'Contractor'), ('0725102600000185', 'KEYSTONE SHOWS', 'Keystone shows'),
                 ('0725102600000186', 'BRIDGEWAY HAS', 'Bridgeway has'), ('0725102600000187', 'TICKET', 'Ticket')]:
    t = recap(t, n, o, nw)
t = t.replace("<column caption='DAYS OPEN' datatype='integer' name='[Calculation_0725102600000188]'",
              "<column caption='Days open' datatype='integer' name='[Calculation_0725102600000188]'")
old = "formula='// WHERE ALIGNED&#10;[place] + CHAR(10) + STR([Calculation_0725102600000120]) + &quot; gaps&quot;'"
assert old in t
t = t.replace(old, "formula='// Where aligned&#10;[place]'")

# ---- 2. Gap List extension columns
i = t.index("<worksheet name='Gap List'"); j = t.index('</worksheet>', i)
w = t[i:j]
def fid(inst): return '[%s].[%s]' % (DS, inst)
cols = [  # (instance, guid or None, width)
    ('none:Calculation_0725102600000182:nk', '{3603A988-123A-4E13-9FB2-55C8E0162F5B}', 100),
    ('none:Calculation_0725102600000183:nk', '{A94406A1-4697-4CFD-BB33-8FDD59C31D53}', 170),
    ('none:Calculation_0725102600000184:nk', '{580C550C-1FCB-41F6-8351-D1BDD3558178}', 190),
    ('none:Calculation_0725102600000185:nk', '{401BD824-3921-46EC-B6A7-96C6FDD4EBB9}', 160),
    ('none:Calculation_0725102600000186:nk', '{949B29CA-5F6C-4A3C-B410-2D49C1608C51}', 160),
    ('none:Calculation_0725102600000187:nk', '{88ADBFB0-AC2E-4D40-AE2E-00D12BA30A74}', 90),
    ('sum:Calculation_0725102600000188:qk', None, 80),
    ('none:gap_id:nk', '{ECA2FFC7-4CE5-43ED-AC2E-729DE86FBD3A}', 90),
]
cols = [(a, g or '{%s}' % str(uuid.uuid4()).upper(), c) for a, g, c in cols]
tips = re.findall(r"^\s*<tooltip %s=.*$" % re.escape(FCP), w, re.M)
assert len(tips) == 13, len(tips)
enc = "<encodings>\n" + "".join(
    "              <lod %s='%s' column='%s' />\n" % (FCP, g, fid(a)) for a, g, _ in cols) + "\n".join(tips) + "\n            </encodings>"
w = re.sub(r"<encodings>.*?</encodings>", lambda m: enc, w, count=1, flags=re.S)
sets = []
for k, (a, g, wd) in enumerate(cols):
    v = json.dumps({"field-id": fid(a), "encoding-type": "detail", "column-index": str(k), "column-width": str(wd)}, separators=(',', ':'))
    sets.append("                <setting key='column-setting-EncodingId:%s-Encoding:detail' value='%s' />" % (g, html.escape(v, quote=True).replace('&#x27;', "'")))
sets += ["                <setting key='dialog-status' value='none-open' />", "                <setting key='setting-key-version' value='V2' />"]
w = re.sub(r"<instance-settings>.*?</instance-settings>", lambda m: "<instance-settings>\n" + "\n".join(sets) + "\n              </instance-settings>", w, count=1, flags=re.S)
# drop the Measure Names filter on DAYS OPEN (it is a plain column now)
w = re.sub(r"\s*<filter class='categorical' column='\[%s\]\.\[:Measure Names\]'>.*?</filter>" % re.escape(DS), '', w, count=1, flags=re.S)
w = w.replace("\n            <column>[%s].[:Measure Names]</column>" % DS, '')
t = t[:i] + w + t[j:]

# ---- 3. target 3.5%
for o, n in [("MIN(IF [Calculation_0725102600000020] THEN [gap_rate_target] END)", "MIN(IF [Calculation_0725102600000020] THEN 0.035 END)"),
             ("// TL Target&#10;MIN([gap_rate_target])", "// TL Target&#10;MIN(0.035)"),
             ("STR(INT(ROUND([Calculation_0725102600000063] * 100, 0))) + &quot;%&quot;", "STR(ROUND([Calculation_0725102600000063] * 100, 1)) + &quot;%&quot;"),
             ("The 3% target is provisional", "The 3.5% target is provisional"),
             ("target 3%.", "target 3.5%.")]:
    assert o in t, o
    t = t.replace(o, n)
open(dst, 'w', encoding='utf-8').write(t)
print('ok', len(t))
