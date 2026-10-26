"""Build doc section 8 (step 5): the rail's items R1 to R27 and the card title placeholders, written into the
dashboard 'CW Reconciliation' of a workbook. Same zone patterns as Dashboard #2's rail (fixed-size items in a
vertical flow container, text zones for headings, bitmap zones for the logo and dividers).

  python3 build_rail.py "in.twb" "out.twb"          (close Tableau first)

Placeholders are empty zones with the capsule look (white, or dark with an outline), named in friendly-name so
step 7 knows which one each control sheet replaces. The three test parameter controls at the top stay until the
rail controls exist.
"""
import re
import sys

src, out = sys.argv[1], sys.argv[2]
s = open(src, encoding='utf-8').read()
H = 850.0
RAIL_X, RAIL_W = 571, 14287                       # 8 px in, 200 px wide, in 100000ths of 1400
a = s.index("<dashboard enable-sort-zone-taborder='true' name='CW Reconciliation'>")
b = s.index('</dashboard>', a)
d = s[a:b]
assert "friendly-name='Rail Top'" not in d, 'already built'
img_dir = re.search(r"param='([^']*/Images and Buttons/)arcadia_kpi_cards_bg_summary\.png'", d).group(1)
max_id = max(int(x) for x in re.findall(r"<zone [^>]*?\bid='(\d+)'", s))
_next = [max_id + 1]


def nid():
    _next[0] += 1
    return _next[0] - 1


def esc(t):
    return t.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


NONE_BORDER = ("<format attr='border-color' value='#000000' />\n<format attr='border-style' value='none' />\n"
               "<format attr='border-width' value='0' />\n")


def style(ind, extra='', border=NONE_BORDER, radius=None, bg=None):
    lines = border.strip().split('\n')
    if radius is not None:
        lines.append(f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='{radius}' />")
    lines.append("<format attr='margin' value='0' />")
    if extra:
        lines += extra.strip().split('\n')
    if bg:
        lines.append(f"<format attr='background-color' value='{bg}' />")
    return (f"{ind}<zone-style>\n" + ''.join(f"{ind}  {l}\n" for l in lines) + f"{ind}</zone-style>\n")


def y_units(px):
    return round(px / H * 100000)


class Cursor:
    y = 0


def zone(ind, px, kind, **kw):
    """One fixed-size item in the vertical rail (px tall)."""
    y0 = y_units(Cursor.y)
    h = y_units(Cursor.y + px) - y0
    Cursor.y += px
    fr = f" friendly-name='{kw['name']}'" if kw.get('name') else ''
    fixed = f"fixed-size='{px}' " if px else ''
    base = f"{ind}<zone {fixed}{fr.strip()} h='{h}' id='{nid()}' is-fixed='true'".replace('  ', ' ')
    if kind == 'empty':
        return (f"{base} type-v2='empty' w='{RAIL_W}' x='{RAIL_X}' y='{y0}'>\n"
                + style(ind + '  ', radius=kw.get('radius'), bg=kw.get('bg'), border=kw.get('border', NONE_BORDER))
                + f"{ind}</zone>\n")
    if kind == 'text':
        return (f"{base} forceUpdate='true' type-v2='text' w='{RAIL_W}' x='{RAIL_X}' y='{y0}'>\n"
                f"{ind}  <formatted-text>\n{kw['runs']}{ind}  </formatted-text>\n" + style(ind + '  ') + f"{ind}</zone>\n")
    if kind == 'image':
        return (f"{base} is-centered='0' is-scaled='1' param='{img_dir}{kw['file']}' type-v2='bitmap' "
                f"w='{RAIL_W}' x='{RAIL_X}' y='{y0}'>\n" + style(ind + '  ', extra="<format attr='padding' value='0' />") + f"{ind}</zone>\n")
    raise ValueError(kind)


def run(color, text, font='Tableau Semibold', size=8):
    return f"            <run fontcolor='{color}' fontname='{font}' fontsize='{size}'>{esc(text)}</run>\n"


I = '          '
def heading(text):
    return zone(I, 16, 'text', runs=run('#b8c4d6', text))


DARK_BORDER = ("<format attr='border-color' value='#4a5b73' />\n<format attr='border-style' value='solid' />\n"
               "<format attr='border-width' value='1' />\n")
RESET_BORDER = ("<format attr='border-color' value='#8a97a8' />\n<format attr='border-style' value='solid' />\n"
                "<format attr='border-width' value='1' />\n")
items = []
items.append(zone(I, 24, 'empty'))                                                           # R1
# R2: logo, blank, info placeholder in a horizontal container
y0 = y_units(Cursor.y); h = y_units(Cursor.y + 40) - y0
top_id = nid()
Cursor.y += 40
def hz(ind, px, kind, w_px, **kw):
    x_u = 0
    w = round(w_px / 1400 * 100000)
    base = f"{ind}<zone fixed-size='{w_px}' h='{h}' id='{nid()}' is-fixed='true'"
    if kind == 'empty':
        return (f"{base}{(' friendly-name=' + chr(39) + kw['name'] + chr(39)) if kw.get('name') else ''} type-v2='empty' w='{w}' x='{RAIL_X}' y='{y0}'>\n"
                + style(ind + '  ') + f"{ind}</zone>\n")
    return (f"{base} is-centered='0' is-scaled='1' param='{img_dir}{kw['file']}' type-v2='bitmap' w='{w}' x='{RAIL_X}' y='{y0}'>\n"
            + style(ind + '  ', extra="<format attr='padding' value='0' />") + f"{ind}</zone>\n")
items.append(f"{I}<zone fixed-size='40' friendly-name='Rail Top' h='{h}' id='{top_id}' is-fixed='true' param='horz' type-v2='layout-flow' w='{RAIL_W}' x='{RAIL_X}' y='{y0}'>\n"
             + hz(I + '  ', 40, 'image', 148, file='arcadia_logo_horizontal_reverse.png')
             + hz(I + '  ', 40, 'empty', 24)
             + hz(I + '  ', 40, 'empty', 28, name='Info button (placeholder)')
             + f"{I}</zone>\n")
items.append(zone(I, 28, 'empty'))                                                           # R3
items.append(heading('POINT IN TIME'))                                                        # R4
items.append(zone(I, 6, 'empty'))
items.append(zone(I, 32, 'empty', name='Close field (placeholder)', radius=16, bg='#ffffff'))  # R6
for label, ph in (('FUNCTION', 'Function'), ('DEPARTMENT', 'Department'), ('COUNTRY', 'Country')):
    items.append(zone(I, 24, 'empty'))
    items.append(heading(label))
    items.append(zone(I, 6, 'empty'))
    items.append(zone(I, 32, 'empty', name=f'{ph} field (placeholder)', radius=16, bg='#1b2d45', border=DARK_BORDER))
items.append(zone(I, 24, 'image', file='arcadia_rail_divider.png'))                          # R19
items.append(heading('SHOW'))
items.append(zone(I, 6, 'empty'))
items.append(zone(I, 32, 'empty', name='Show toggle (placeholder)', radius=16, bg='#1b2d45'))   # R22
items.append(zone(I, 24, 'image', file='arcadia_rail_divider.png'))
items.append(zone(I, 32, 'empty', name='Reset (placeholder)', radius=16, border=RESET_BORDER))  # R24
flex = int(H - Cursor.y - 36 - 24)
y0 = y_units(Cursor.y); h = y_units(Cursor.y + flex) - y0; Cursor.y += flex
items.append(f"{I}<zone h='{h}' id='{nid()}' type-v2='empty' w='{RAIL_W}' x='{RAIL_X}' y='{y0}'>\n" + style(I + '  ') + f"{I}</zone>\n")  # R25
items.append(zone(I, 36, 'text', name='Rail as-of (placeholder)',
                  runs=run('#e4e9f0', 'Data as of Jun 30, 2026', size=9) + run('#b9c3d1', '\nRefreshed daily at 00:00 GMT', font='Tableau Book', size=9)))
items.append(zone(I, 24, 'empty'))                                                            # R27
assert Cursor.y == 850, Cursor.y

rail_start = d.index("<zone friendly-name='Rail'")
rail_open_end = d.index('>', rail_start) + 1
old_child_start = d.index("<zone h='100000' id='34' type-v2='empty'", rail_open_end)
old_child_end = d.index('</zone>', old_child_start) + len('</zone>')
d = d[:old_child_start] + '\n' + ''.join(items).rstrip('\n') + d[old_child_end:]


# card title placeholders (8.4): a text title and a flexible blank in each of the two right-hand cards
def card_children(card, title, sub, title_px, body_name):
    global d
    i = d.index(f"<zone friendly-name='{card}'")
    j = d.index('<zone-style>', i)                                   # the card's own style follows its children
    ind = '          '
    cy = {'Card: Timeline': 22353, 'Card: Tickets': 58353}[card]
    t = (f"{ind}<zone fixed-size='{title_px}' forceUpdate='true' friendly-name='{title} (placeholder)' h='{y_units(title_px)}' id='{nid()}' is-fixed='true' type-v2='text' w='23500' x='73200' y='{cy + 800}'>\n"
         f"{ind}  <formatted-text>\n"
         f"{ind}    <run fontcolor='#13243a' fontname='Tableau Semibold' fontsize='12'>{esc(title)}</run>\n"
         f"{ind}    <run fontcolor='#5a6171' fontsize='9'>\n{esc(sub)}</run>\n"
         f"{ind}  </formatted-text>\n" + style(ind + '  ', extra="<format attr='padding' value='0' />") + f"{ind}</zone>\n"
         f"{ind}<zone friendly-name='{body_name} (placeholder)' h='{y_units(200)}' id='{nid()}' type-v2='empty' w='23500' x='73200' y='{cy + 800 + y_units(title_px)}'>\n"
         + style(ind + '  ') + f"{ind}</zone>\n")
    d = d[:j] + t + '        ' + d[j:]


card_children('Card: Timeline', 'Gap rate at each month-end close',
              'Contractors with a gap divided by contractors working in Bridgeway · last 13 closes', 56, 'Timeline')
card_children('Card: Tickets', 'Open tickets by where they are aligned',
              'One dot per Helix ticket open at the close', 44, 'Ticket body')
s = s[:a] + d + s[b:]
open(out, 'w', encoding='utf-8').write(s)
print(f'rail built: {len(items)} top-level items, last zone id {_next[0] - 1}')
