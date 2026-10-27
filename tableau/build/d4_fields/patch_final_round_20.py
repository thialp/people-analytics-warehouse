"""Round 20: KPI 2 strip back to a palette-coloured sheet, now a Bar mark that spans the card.
(visibility on a data-source calculation did not follow the filters.) usage: in.twb out.twb"""
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
FED = "federated.19gwunf1mzo1gq1cltitv08khlf9"
U = lambda: str(uuid.uuid4()).upper()

def remove_zone(text, zid):
    while True:
        m = re.search(r"[ \t]*<zone [^>]*\bid='%s'[^>]*>" % zid, text)
        if not m: return text
        i, j = m.start(), m.end()
        if text[j-2:j] == '/>': text = text[:i] + text[j:].lstrip('\n'); continue
        depth, pos = 1, j
        while depth:
            a = text.find('<zone ', pos); b = text.find('</zone>', pos)
            if a != -1 and a < b:
                e = text.find('>', a); depth += 0 if text[e-1] == '/' else 1; pos = e + 1
            else: depth -= 1; pos = b + 7
        text = text[:i] + text[pos:].lstrip('\n')

# 1. remove the two image strips and their visibility wiring and calcs
t = remove_zone(t, '330'); t = remove_zone(t, '331')
lines = t.split('\n'); guids = set()
for l in lines:
    if "zone-id='330'" in l or "zone-id='331'" in l or (("Calculation_0725102600000360]'" in l or "Calculation_0725102600000361]'" in l) and 'single-value' in l):
        guids.update(re.findall(r"(?:node-guid|visibility-input-guid|value-output-guid)='([0-9a-f-]{36})'", l))
t = '\n'.join(l for l in lines if not any(g in l for g in guids))
t = re.sub(r"[ \t]*<column caption='KPI 2 Strip (Risk|Ok)'.*?</column>\n?", '', t, flags=re.S)

# 2. new calc: constant 1 for the bar length
cid = '0725102600000362'
col = "      <column caption='KPI 2 Strip One' datatype='real' name='[Calculation_%s]' role='measure' type='quantitative'>\n        <calculation class='tableau' formula='// KPI 2 Strip One&#10;MIN(1)' />\n      </column>" % cid
anchor = re.search(r"<column caption='Show Load Note'[^>]*>.*?</column>", t, re.S).group(0)
i = t.index(anchor) + len(anchor); t = t[:i] + '\n' + col + t[i:]
colxml = "<column caption='KPI 2 Strip One' datatype='real' name='[Calculation_%s]' role='measure' type='quantitative'>\n              <calculation class='tableau' formula='// KPI 2 Strip One&#10;MIN(1)' />\n            </column>" % cid
INST = "[min:Calculation_%s:qk]" % cid

# 3. sheet (Timeline's dependencies carry rate / selected / target / dot / month)
hk = t.index("<worksheet name='KPI Hover 2'>"); hw = t[hk:t.index('</worksheet>', hk) + 12]
tk = t.index("<worksheet name='Timeline'>"); tw = t[tk:t.index('</worksheet>', tk)]
tdeps = re.search(r"<datasource-dependencies datasource='%s'>.*?</datasource-dependencies>" % FED, tw, re.S).group(0)
w = hw.replace("name='KPI Hover 2'", "name='KPI 2 Strip'")
w = re.sub(r"<simple-id uuid='\{[^}]*\}' />", "<simple-id uuid='{%s}' />" % U(), w)
hdeps = re.search(r"<datasource-dependencies datasource='%s'>.*?</datasource-dependencies>" % FED, w, re.S).group(0)
hc = re.search(r"<column caption='Hover Cell'.*?</column>", hdeps, re.S).group(0)
newdeps = tdeps
j = newdeps.index('<column-instance') if '<column-instance' in newdeps else newdeps.rindex('</datasource-dependencies>')
extra = (hc if "Calculation_0725102600000255]'" not in newdeps else '') + '\n            ' + colxml + '\n            '
newdeps = newdeps[:j] + extra + newdeps[j:]
insts = ["<column-instance column='[Calculation_0725102600000255]' derivation='None' name='[none:Calculation_0725102600000255:nk]' pivot='key' type='nominal' />",
         "<column-instance column='[Calculation_0725102600000197]' derivation='User' name='[usr:Calculation_0725102600000197:nk]' pivot='key' type='nominal' />",
         "<column-instance column='[Calculation_0725102600000200]' derivation='User' name='[usr:Calculation_0725102600000200:nk]' pivot='key' type='nominal' />",
         "<column-instance column='[Calculation_%s]' derivation='Min' name='%s' pivot='key' type='quantitative' />" % (cid, INST)]
for inst in insts:
    nm = re.search(r"name='(\[[^']*\])'", inst).group(1)
    if nm not in newdeps:
        newdeps = newdeps.replace('</datasource-dependencies>', inst + '\n          </datasource-dependencies>')
if "[none:month_end_date:qk]" not in newdeps:
    newdeps = newdeps.replace('</datasource-dependencies>', "<column-instance column='[month_end_date]' derivation='None' name='[none:month_end_date:qk]' pivot='key' type='quantitative' />\n          </datasource-dependencies>")
w = w.replace(hdeps, newdeps)
filt = ("<filter class='categorical' column='[%s].[usr:Calculation_0725102600000197:nk]'>\n"
        "            <groupfilter function='member' level='[usr:Calculation_0725102600000197:nk]' member='true' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n"
        "          </filter>\n          <slices>\n            <column>[%s].[usr:Calculation_0725102600000197:nk]</column>\n          </slices>\n          ") % (FED, FED)
w = w.replace("<aggregation value='true' />", filt + "<aggregation value='true' />", 1)
# axis: fixed 0..1, hidden
axis_rule = ("<style-rule element='axis'>\n"
             "            <encoding attr='space' class='0' field='[%s].%s' field-type='quantitative' max='1.0' min='0.0' range-type='fixed' scope='cols' type='space' />\n"
             "            <format attr='display' class='0' field='[%s].%s' scope='cols' value='false' />\n"
             "            <format attr='tick-color' value='#00000000' />\n          </style-rule>") % (FED, INST, FED, INST)
w = re.sub(r"<style-rule element='axis'>.*?</style-rule>", lambda m: axis_rule, w, count=1, flags=re.S)
# pane: Bar mark
pane = ("<pane selection-relaxation-option='selection-relaxation-disallow'>\n            <view>\n              <breakdown value='auto' />\n            </view>\n"
        "            <mark class='Bar' />\n            <encodings>\n"
        "              <lod column='[%s].[none:Calculation_0725102600000255:nk]' />\n"
        "              <lod column='[%s].[none:month_end_date:qk]' />\n"
        "              <color column='[%s].[usr:Calculation_0725102600000200:nk]' />\n            </encodings>\n"
        "            <style>\n              <style-rule element='mark'>\n                <format attr='size' value='1.0' />\n                <format attr='mark-transparency' value='255' />\n                <format attr='has-stroke' value='false' />\n              </style-rule>\n            </style>\n          </pane>") % (FED, FED, FED)
w = re.sub(r"<pane .*?</pane>", lambda m: pane, w, count=1, flags=re.S)
w = re.sub(r"<cols>.*?</cols>", "<cols>[%s].%s</cols>" % (FED, INST), w, count=1, flags=re.S)
if '<tooltip-style' not in w:
    w = w.replace("</table>", "<tooltip-style tooltip-mode='none' />\n      </table>", 1)
e = t.index('</worksheet>', hk) + 12
t = t[:e] + '\n    ' + w + t[e:]
m = re.search(r"<window class='worksheet' name='KPI Hover 2'>.*?</window>", t, re.S)
win = re.sub(r"<simple-id uuid='\{[^}]*\}' />", "<simple-id uuid='{%s}' />" % U(), m.group(0).replace("name='KPI Hover 2'", "name='KPI 2 Strip'"))
t = t[:m.end()] + '\n    ' + win + t[m.end():]
vp = re.search(r"<viewpoint name='KPI Hover 2'>.*?</viewpoint>", t, re.S).group(0)
t = t.replace(vp, vp + '\n        ' + vp.replace('KPI Hover 2', 'KPI 2 Strip'), 1)

# 4. zone (above the band image, below the cards and hovers)
zone = """        <zone h='471' id='330' name='KPI 2 Strip' show-title='false' w='15286' x='33786' y='10118'>
          <layout-cache type-h='cell' type-w='fixed' />
          <zone-style>
            <format attr='border-color' value='#000000' />
            <format attr='border-style' value='none' />
            <format attr='border-width' value='0' />
            <format attr='margin' value='0' />
          </zone-style>
        </zone>
"""
i = t.index("<zone friendly-name='KPI band image'"); i = t.index('>', i) + 1
if t[i-2] != '/': i = t.index('</zone>', i) + 7
i = t.index('\n', i) + 1
t = t[:i] + zone + t[i:]

# 5. deselect for the strip sheet is not needed (no marks to select: tooltips and selection are off)
open(dst, 'w', encoding='utf-8').write(t)
print('ok')
