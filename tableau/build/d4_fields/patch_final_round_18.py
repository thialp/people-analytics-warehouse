"""Round 18: KPI 2 top strip as a palette-coloured sheet (TL Dot palette) instead of two visibility-switched zones.
usage: patch_final_round_18.py in.twb out.twb"""
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
FED = "federated.19gwunf1mzo1gq1cltitv08khlf9"
U = lambda: str(uuid.uuid4()).upper()

# 1. remove the two visibility strips
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
t = remove_zone(t, '330'); t = remove_zone(t, '331')
for n in ('KPI 2 Strip Bad', 'KPI 2 Strip Good'):
    t = re.sub(r"[ \t]*<worksheet name='%s'>.*?</worksheet>\n?" % n, '', t, flags=re.S)
    t = re.sub(r"[ \t]*<window class='worksheet' name='%s'>.*?</window>\n?" % n, '', t, flags=re.S)
    t = re.sub(r"[ \t]*<viewpoint name='%s'>.*?</viewpoint>\n?" % n, '', t, flags=re.S)
lines = t.split('\n'); keep = []
guids = set()
for l in lines:
    if "zone-id='330'" in l or "zone-id='331'" in l or "Calculation_0725102600000348]'" in l and 'single-value' in l or "Calculation_0725102600000349]'" in l and 'single-value' in l:
        guids.update(re.findall(r"(?:node-guid|visibility-input-guid|value-output-guid)='([0-9a-f-]{36})'", l))
for l in lines:
    if any(g in l for g in guids): continue
    keep.append(l)
t = '\n'.join(keep)
t = re.sub(r"[ \t]*<column caption='KPI 2 Strip (Bad|Good)'.*?</column>\n?", '', t, flags=re.S)

# 2. new sheet: Square, Hover-style fill, coloured by TL Dot (palette already set), only the selected close
hk = t.index("<worksheet name='KPI Hover 2'>"); hw = t[hk:t.index('</worksheet>', hk) + 12]
tk = t.index("<worksheet name='Timeline'>"); tw = t[tk:t.index('</worksheet>', tk)]
tdeps = re.search(r"<datasource-dependencies datasource='%s'>.*?</datasource-dependencies>" % FED, tw, re.S).group(0)
w = hw.replace("name='KPI Hover 2'", "name='KPI 2 Strip'")
w = re.sub(r"<simple-id uuid='\{[^}]*\}' />", "<simple-id uuid='{%s}' />" % U(), w)
# dependencies: Timeline's block (has rate, selected, target, dot, month) + hover cell
hdeps = re.search(r"<datasource-dependencies datasource='%s'>.*?</datasource-dependencies>" % FED, w, re.S).group(0)
hc = re.search(r"<column caption='Hover Cell'.*?</column>", hdeps, re.S).group(0)
newdeps = tdeps
if "Calculation_0725102600000255" not in newdeps:
    j = newdeps.index('<column-instance') if '<column-instance' in newdeps else newdeps.rindex('</datasource-dependencies>')
    newdeps = newdeps[:j] + hc + "\n            " + newdeps[j:]
for inst in ("<column-instance column='[Calculation_0725102600000255]' derivation='None' name='[none:Calculation_0725102600000255:nk]' pivot='key' type='nominal' />",
             "<column-instance column='[Calculation_0725102600000197]' derivation='User' name='[usr:Calculation_0725102600000197:nk]' pivot='key' type='nominal' />",
             "<column-instance column='[Calculation_0725102600000200]' derivation='User' name='[usr:Calculation_0725102600000200:nk]' pivot='key' type='nominal' />"):
    nm = re.search(r"name='(\[[^']*\])'", inst).group(1)
    if nm not in newdeps:
        newdeps = newdeps.replace('</datasource-dependencies>', inst + '\n          </datasource-dependencies>')
if "[none:month_end_date:qk]" not in newdeps:
    newdeps = newdeps.replace('</datasource-dependencies>', "<column-instance column='[month_end_date]' derivation='None' name='[none:month_end_date:qk]' pivot='key' type='quantitative' />\n          </datasource-dependencies>")
w = w.replace(hdeps, newdeps)
# filter on the selected close
filt = ("<filter class='categorical' column='[%s].[usr:Calculation_0725102600000197:nk]'>\n"
        "            <groupfilter function='member' level='[usr:Calculation_0725102600000197:nk]' member='true' user:ui-domain='database' user:ui-enumeration='inclusive' user:ui-marker='enumerate' />\n"
        "          </filter>\n          <slices>\n            <column>[%s].[usr:Calculation_0725102600000197:nk]</column>\n          </slices>\n          ") % (FED, FED)
w = w.replace("<aggregation value='true' />", filt + "<aggregation value='true' />", 1)
# pane
enc = ("<encodings>\n              <lod column='[%s].[none:Calculation_0725102600000255:nk]' />\n"
       "              <lod column='[%s].[none:month_end_date:qk]' />\n"
       "              <color column='[%s].[usr:Calculation_0725102600000200:nk]' />\n            </encodings>") % (FED, FED, FED)
w = re.sub(r"<encodings>.*?</encodings>", enc, w, count=1, flags=re.S)
w = re.sub(r"\s*<customized-tooltip.*?</customized-tooltip>", "", w, flags=re.S)
if '<tooltip-style' not in w:
    w = w.replace("</table>", "<tooltip-style tooltip-mode='none' />\n      </table>", 1)
t = t[:hk] + t[hk:t.index('</worksheet>', hk) + 12] + '\n    ' + w + t[t.index('</worksheet>', hk) + 12:]

# window + viewpoint
m = re.search(r"<window class='worksheet' name='KPI Hover 2'>.*?</window>", t, re.S)
win = re.sub(r"<simple-id uuid='\{[^}]*\}' />", "<simple-id uuid='{%s}' />" % U(), m.group(0).replace("name='KPI Hover 2'", "name='KPI 2 Strip'"))
t = t[:m.end()] + '\n    ' + win + t[m.end():]
vp = re.search(r"<viewpoint name='KPI Hover 2'>.*?</viewpoint>", t, re.S).group(0)
t = t.replace(vp, vp + '\n        ' + vp.replace('KPI Hover 2', 'KPI 2 Strip'), 1)

# 3. zone: exactly the card width (473.5 to 686 px), top of the card (86 px)
zone = """        <zone h='471' id='330' name='KPI 2 Strip' show-title='false' w='15179' x='33821' y='10118'>
          <layout-cache type-h='cell' type-w='fixed' />
          <zone-style>
            <format attr='border-color' value='#000000' />
            <format attr='border-style' value='none' />
            <format attr='border-width' value='0' />
            <format attr='margin' value='0' />
          </zone-style>
        </zone>
"""
i = t.index("id='276'"); i = t.index('</zone>', i) + 7; i = t.index('\n', i) + 1
t = t[:i] + zone + t[i:]
open(dst, 'w', encoding='utf-8').write(t)
print('ok')
