"""Build doc 9N revision 5: the flag labels move left of the flag nodes, on their own sheet.

  python3 patch_flag_labels.py "in.twb" "out.twb"          (close Tableau first)

- Sk W 576, Sk X3 436, Sk Y Text (risk and place labels only): new formulas everywhere they are stored
- new calcs Sk Flag Y, Sk Flag X (spec_sankey.py)
- Sankey Native: X axis fixed 0 to 576; Measure Names off the text layer's Color
- new worksheet Sankey Flag Labels (circle marks at x 144, labels to their left, axes 0 to 150 and
  0 to 540 reversed), built from Sankey Native's data source references
"""
import re, sys, uuid
src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
DS = re.search(r"<datasource caption='CW Reconciliation' inline='true' name='([^']+)'", s).group(1)
Q = f'[{DS}]'
assert "<worksheet name='Sankey Native'>" in s, 'build the Sankey Native sheet first'
assert "caption='Sk Flag Y'" not in s, 'already patched'


def esc(t):
    return (t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
             .replace("'", '&apos;').replace('"', '&quot;').replace('\n', '&#10;'))


def iid(cap):
    return re.search(r"<column caption='" + re.escape(cap) + r"'[^>]*? name='\[(Calculation_\d+)\]'", s).group(1)


I = {c: iid(c) for c in ('Sk W', 'Sk X3', 'Sk Y Text', 'Sk Y', 'Sk Show', 'Sk Mark', 'Sk Lbl Header', 'Sk Lbl Name', 'Sk Lbl Count')}
NEWF = {
    'Sk W': '576',
    'Sk X3': '436',
    'Sk Y Text': f'IF ([sk_part] = "Label" OR [sk_part] = "Header") AND [sk_level] > 1 THEN [{I["Sk Y"]}] END',
}
for cap, f in NEWF.items():
    pat = re.compile(r"(<column caption='" + re.escape(cap) + r"'[^>]*name='\[" + I[cap] + r"\]'[^>]*>\s*<calculation class='tableau' formula=')([^']*)(' />)")
    s, n = pat.subn(lambda m: m.group(1) + esc(f'// {cap}\n{f}') + m.group(3), s)
    assert n >= 1, cap

FY, FX = 'Calculation_0725102700000201', 'Calculation_0725102700000202'
NEWC = [('Sk Flag Y', 'real', FY, f'IF ([sk_part] = "Label" OR [sk_part] = "Header") AND [sk_level] = 1 THEN [{I["Sk Y"]}] END'),
        ('Sk Flag X', 'integer', FX, '144')]
def col(cap, dt, cid, f, ind):
    return (f"{ind}<column caption='{cap}' datatype='{dt}' name='[{cid}]' role='measure' type='quantitative'>\n"
            f"{ind}  <calculation class='tableau' formula='{esc('// ' + cap + chr(10) + f)}' />\n{ind}</column>\n")
ds_start = s.index(f"<datasource caption='CW Reconciliation' inline='true' name='{DS}'")
g = s.index('      <group ', ds_start)
s = s[:g] + ''.join(col(*c, '      ') for c in NEWC) + s[g:]

# ---------- Sankey Native: axis 0 to 576, no Measure Names colour on the text layer
a = s.index("<worksheet name='Sankey Native'>"); b = s.index('</worksheet>', a)
w = s[a:b]
w2 = re.sub(r"(field='\[[^\]]+\]\.\[avg:" + re.escape(iid('Sk X')) + r":qk\]' field-type='quantitative' max=')726\.0(')", r"\g<1>576.0\2", w)
assert w2 != w, 'Sk X axis range not found'
w2 = w2.replace(f"              <color column='{Q}.[:Measure Names]' />\n", '')
s = s[:a] + w2 + s[b:]
wa = s.index("<window class='worksheet' name='Sankey Native'>"); wb = s.index('</window>', wa)
s = s[:wa] + s[wa:wb].replace(f"            <card pane-specification-id='2' param='{Q}.[:Measure Names]' type='color' />\n", '') + s[wb:]

# ---------- the new sheet
a = s.index("<worksheet name='Sankey Native'>"); b = s.index('</worksheet>', a) + len('</worksheet>')
native = s[a:b]
deps = re.findall(r"          <datasource-dependencies.*?</datasource-dependencies>\n", native, re.S)
dep_ds = next(d for d in deps if f"datasource='{DS}'" in d)
dep_par = ''.join(d for d in deps if f"datasource='{DS}'" not in d)
extra = (col('Sk Flag Y', 'real', FY, NEWC[0][3], '            ') + col('Sk Flag X', 'integer', FX, '144', '            ')
         + f"            <column-instance column='[{FY}]' derivation='Avg' name='[avg:{FY}:qk]' pivot='key' type='quantitative' />\n"
         + f"            <column-instance column='[{FX}]' derivation='Avg' name='[avg:{FX}:qk]' pivot='key' type='quantitative' />\n")
dep_ds = dep_ds.replace('          </datasource-dependencies>\n', extra + '          </datasource-dependencies>\n')
flt = re.search(r"          <filter class='categorical' column='[^']*\[none:" + I['Sk Show'] + r":nk\]'>.*?</filter>\n", native, re.S).group(0)
sl = re.search(r"          <slices>.*?</slices>\n", native, re.S).group(0)
t = lambda c: f"{Q}.[none:{I[c]}:nk]"
sheet = f"""<worksheet name='Sankey Flag Labels'>
      <table>
        <view>
          <datasources>
            <datasource caption='CW Reconciliation' name='{DS}' />
            <datasource name='Parameters' />
          </datasources>
{dep_ds}{dep_par}{flt}{sl}          <aggregation value='true' />
        </view>
        <style>
          <style-rule element='axis'>
            <encoding attr='space' class='0' field='{Q}.[avg:{FX}:qk]' field-type='quantitative' max='150.0' min='0.0' range-type='fixed' scope='cols' type='space' />
            <encoding attr='space' class='0' field='{Q}.[avg:{FY}:qk]' field-type='quantitative' max='540.0' min='0.0' range-type='fixed' reverse='true' scope='rows' type='space' />
            <format attr='display' class='0' field='{Q}.[avg:{FX}:qk]' scope='cols' value='false' />
            <format attr='display' class='0' field='{Q}.[avg:{FY}:qk]' scope='rows' value='false' />
          </style-rule>
          <style-rule element='gridline'>
            <format attr='line-visibility' value='off' />
          </style-rule>
          <style-rule element='zeroline'>
            <format attr='line-visibility' value='off' />
          </style-rule>
          <style-rule element='table'>
            <format attr='show-null-value-warning' value='false' />
          </style-rule>
        </style>
        <panes>
          <pane selection-relaxation-option='selection-relaxation-disallow'>
            <view>
              <breakdown value='auto' />
            </view>
            <mark class='Circle' />
            <mark-sizing mark-sizing-setting='marks-scaling-off' />
            <encodings>
              <text column='{t("Sk Lbl Header")}' />
              <text column='{t("Sk Lbl Name")}' />
              <text column='{t("Sk Lbl Count")}' />
              <lod column='{t("Sk Mark")}' />
            </encodings>
            <customized-tooltip show-buttons='false'>
              <formatted-text />
            </customized-tooltip>
            <customized-label>
              <formatted-text>
                <run fontalignment='2' fontcolor='#6b7079' fontsize='8'><![CDATA[<{t("Sk Lbl Header")}>]]></run>
                <run fontalignment='2' fontcolor='#13243a' fontname='Tableau Semibold'><![CDATA[<{t("Sk Lbl Name")}> ]]></run>
                <run fontalignment='2' fontcolor='#6b7079'><![CDATA[<{t("Sk Lbl Count")}>]]></run>
              </formatted-text>
            </customized-label>
            <style>
              <style-rule element='cell'>
                <format attr='text-align' value='left' />
                <format attr='vertical-align' value='center' />
              </style-rule>
              <style-rule element='mark'>
                <format attr='size' value='0.0099999997764825821' />
                <format attr='mark-transparency' value='0' />
                <format attr='has-stroke' value='false' />
                <format attr='mark-labels-show' value='true' />
                <format attr='mark-labels-cull' value='false' />
              </style-rule>
            </style>
          </pane>
        </panes>
        <rows>{Q}.[avg:{FY}:qk]</rows>
        <cols>{Q}.[avg:{FX}:qk]</cols>
      </table>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </worksheet>"""
s = s[:b] + '\n    ' + sheet + s[b:]

wa = s.index("<window class='worksheet' name='Sankey Native'>"); wb = s.index('</window>', wa) + len('</window>')
win = f"""
    <window class='worksheet' name='Sankey Flag Labels'>
      <cards>
        <edge name='left'>
          <strip size='160'>
            <card type='pages' />
            <card type='filters' />
            <card type='marks' />
          </strip>
        </edge>
        <edge name='top'>
          <strip size='2147483647'>
            <card type='columns' />
          </strip>
          <strip size='2147483647'>
            <card type='rows' />
          </strip>
          <strip size='31'>
            <card type='title' />
          </strip>
        </edge>
      </cards>
      <simple-id uuid='{{{str(uuid.uuid4()).upper()}}}' />
    </window>"""
s = s[:wb] + win + s[wb:]
open(out, 'w', encoding='utf-8').write(s)
print('patched: 3 formulas, 2 calcs, Sankey Native axis 0 to 576, sheet Sankey Flag Labels')
