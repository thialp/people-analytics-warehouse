"""Gap List card layout: the title floats over the top of the list (aligned with the extension's export icon),
a small export hint sits left of the icon, and the list fills the card.
usage: python3 patch_gap_card_layout.py in.twb out.twb  (default layout only; the Phone layout is left alone)"""
import re, sys, uuid
src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
D = "{6548F4FB-B30D-45E2-A1B0-256049E77034}"
PX = lambda px, base: round(px * 100000 / base)
c0 = t.index("<zone friendly-name='Card: Main'")
c1 = t.index("<zone friendly-name='Card: Timeline'", c0)
card = t[c0:c1]
# 1. take the title out of the flow
m = re.search(r"\s*<zone fixed-size='44' h='5176' id='279'.*?</zone>", card, re.S)
assert m
card = card[:m.start()] + card[m.end():]
# 2. list fills the card (inner 726 x 590 px)
old = "<zone h='64000' id='280' name='Gap List' show-title='false' w='51715' x='18785' y='29529'>"
assert old in card
card = card.replace(old, "<zone h='%d' id='280' name='Gap List' show-title='false' w='51715' x='18785' y='24353'>" % PX(590, 850))
assert "fixed-size-h='544'" in card
card = card.replace("fixed-size-h='544'", "fixed-size-h='590'")
# 3. floating title + hint right after the card (above the list in z-order)
NOBORDER = ("<zone-style>\n              <format attr='border-color' value='#000000' />\n              <format attr='border-style' value='none' />\n"
            "              <format attr='border-width' value='0' />\n              <format attr='margin' value='0' />\n            </zone-style>")
HINT_X, HINT_W = 805, 150   # px, right edge 32 px left of the card's inner right edge
title = ("        <zone h='%d' id='279' name='Gap List Title' show-title='false' w='%d' x='18785' y='24353'>\n"
         "          <layout-cache type-h='cell' type-w='fixed' />\n          %s\n        </zone>\n") % (PX(40, 850), PX(HINT_X - 246 - 17 - 6, 1400), NOBORDER)
hint = ("        <zone fixed-size='%d' forceUpdate='true' h='%d' id='294' is-fixed='true' type-v2='text' w='%d' x='%d' y='%d'>\n"
        "          <formatted-text>\n            <run fontalignment='2' fontcolor='#6b7079' fontname='Tableau Book' fontsize='8'>Click the icon to export to Excel</run>\n          </formatted-text>\n"
        "          %s\n        </zone>\n") % (HINT_W, PX(16, 850), PX(HINT_W, 1400), PX(HINT_X, 1400), PX(209, 850), NOBORDER)
t = t[:c0] + card + title + hint + t[c1:]
# 4. visibility: the hint follows p_ShowList like the title and the list
ng, ig = str(uuid.uuid4()), str(uuid.uuid4())
node = "        <dashboard-zone-visibility-node dashboard-identifier='%s' node-guid='%s' visibility-input-guid='%s' zone-id='294' />\n" % (D, ng, ig)
k = t.index("</nodes>"); k = t.rindex('\n', 0, k) + 1
t = t[:k] + node + t[k:]
edge = "        <edge from='04208a01-8190-482e-b13f-a63b2642a628' to='%s' />\n" % ig
k = t.index("</edges>"); k = t.rindex('\n', 0, k) + 1
t = t[:k] + edge + t[k:]
pair = "        <pair execution-subgraph-guid='17fb47e4-dd15-41de-a6be-f1287aff1795' node-guid='%s' />\n" % ng
k = t.index("</node-execution-subgraphs>"); 
# insert after the last pair of that subgraph
last = t.rindex("<pair execution-subgraph-guid='17fb47e4-dd15-41de-a6be-f1287aff1795'", 0, k)
e = t.index('\n', last) + 1
t = t[:e] + pair + t[e:]
# 5. shorter subtitle (the title row now shares its width with the hint)
o = "Oldest first. Hover a row for the evidence, the next step and the ticket. Click a node in the Overview to narrow the list."
assert t.count(o) >= 1
t = t.replace(o, "Oldest first. Hover a row for the evidence and next step. Click a node in the Overview to narrow the list.")
open(dst, 'w', encoding='utf-8').write(t); print('ok')
