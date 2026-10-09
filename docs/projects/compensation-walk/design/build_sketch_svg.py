"""Write Figma-importable SVGs of the Dashboard #2 Summary sketch (1400 x 850), with named layers.

Layer structure follows the Arcadia UI kit: 'Background (export)' (rounded cards, navy rail, control outlines)
and 'Tableau objects' (every sheet, text and control that floats in Tableau).
Usage: python build_sketch_svg.py sketch_data.json .
"""
import json, sys, math, textwrap, os
from xml.sax.saxutils import escape

D = json.load(open(sys.argv[1])); OUT = sys.argv[2]; os.makedirs(OUT, exist_ok=True)
NAVY, TEAL, CORAL, VIOLET, AMBER, GRAY, SLATE, LINE, CARD, PAGE = '#13233A', '#00938D', '#E4572E', '#5B4FB3', '#D98E04', '#8C8A84', '#5A6170', '#E4E3DD', '#FBFBF8', '#F3F3EF'
RAIL_MUTED, RAIL_LINE, RAIL_ACTIVE = '#8FA0BC', '#3A4A63', '#1B3050'
FONT = "Inter, 'Helvetica Neue', Arial, sans-serif"

def T(x, y, s, size=12, w=400, fill=NAVY, anchor='start', ls=None):
    extra = f' letter-spacing="{ls}"' if ls else ''
    return f'<text x="{x}" y="{y}" font-family="{FONT}" font-size="{size}" font-weight="{w}" fill="{fill}" text-anchor="{anchor}"{extra}>{escape(str(s))}</text>'
def R(x, y, w, h, fill='none', stroke=None, rx=0, sw=1, op=None):
    st = f' stroke="{stroke}" stroke-width="{sw}"' if stroke else ''
    o = f' fill-opacity="{op}"' if op is not None else ''
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" fill="{fill}"{st}{o}/>'
def G(name, *items):
    return f'<g id="{escape(name)}">' + ''.join(items) + '</g>'
def L(x1, y1, x2, y2, stroke=LINE, sw=1, dash=None):
    d = f' stroke-dasharray="{dash}"' if dash else ''
    return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{stroke}" stroke-width="{sw}"{d}/>'

fmt0 = lambda n: f'{round(abs(n)):,}'
sg = lambda n: '+' if n > 0 else ('−' if n < 0 else '')

LENS = {
 'fte': dict(open=107553.68, close=108706.49, min=100000, max=110000, step=2000, unit=lambda n: f'${n//1000}k',
             val=lambda n: f'{sg(n)}${fmt0(n)}', tot=lambda n: f'${fmt0(n)}',
             steps=dict(hires=-3270, exits=128, career=631, tenure=3325, market=53, location=17, fte=-11, fringe=279)),
 'tot': dict(open=3000.1, close=3195.5, min=2800, max=3500, step=100, unit=lambda n: f'${n:,}',
             val=lambda n: f'{sg(n)}${abs(n):.1f}M', tot=lambda n: f'${n:,.1f}M',
             steps=dict(hires=411.3, exits=-331.8, career=18.6, tenure=97.7, market=1.6, location=0.5, fte=-10.6, fringe=8.2)),
}
NAME = dict(hires='Hires', exits='Exits', career='Promotions & demotions', tenure='Tenure raises', market='Market adjustments', location='Relocation', fte='FTE changes', fringe='Fringe rates')
SHORT = dict(hires='Hires', exits='Exits', career='Career', tenure='Tenure', market='Market', location='Location', fte='FTE', fringe='Fringe')
WHY = dict(
 hires=dict(fte='4,766 people joined below the opening average pay, so the average fell even though they added cost.', tot='4,766 hires added the most cost of any driver this year.'),
 exits=dict(fte='3,187 people left. Leavers earned slightly less than average, so the average edged up.', tot='3,187 exits removed pay; this offsets most of the hiring cost.'),
 career=dict(fte='Promotions move people up one level at a time. Demotions take a little back.', tot='Promotions +$19.2M, demotions −$0.6M: pay changes with no change in headcount.'),
 tenure=dict(fte='Each person steps up on their hire anniversary. The biggest lift to the average.', tot='Anniversary raises across the whole workforce, +$97.7M.'),
 market=dict(fte='Targeted pay corrections to the market, small this year.', tot='Targeted market corrections, +$1.6M.'),
 location=dict(fte='Moves reset pay to the destination office: international +$0.6M, domestic −$0.1M.', tot='Moves reset pay to the destination: international +$0.6M, domestic −$0.1M.'),
 fte=dict(fte='Part-time changes lowered FTE by 96 while headcount grew.', tot='FTE fell by 96 while headcount grew, −$10.6M.'),
 fringe=dict(fte='Employer-cost rates changed by country. Salaries did not move.', tot='Employer-cost rates changed by country, +$8.2M. No salary change.'))

def kpi_cards(lens):
    d = LENS[lens]
    if lens == 'fte':
        cards = [('Opening pay per FTE', '$107,554', 'Jun 30, 2025', NAVY), ('Closing pay per FTE', '$108,706', 'Jun 30, 2026', NAVY),
                 ('Change per FTE', '+$1,153', 'over the period', TEAL), ('Change', '+1.1%', 'of opening pay per FTE', TEAL),
                 ('FTE', '29,396', 'from 27,894 (+1,502)', NAVY)]
    else:
        cards = [('Opening total pay', '$3,000.1M', 'Jun 30, 2025', NAVY), ('Closing total pay', '$3,195.5M', 'Jun 30, 2026', NAVY),
                 ('Change in total pay', '+$195.4M', 'over the period', TEAL), ('Change', '+6.5%', 'of opening total pay', TEAL),
                 ('People', '30,015', 'from 28,436 (+1,579)', NAVY)]
    bg = [R(240 + i * 223, 88, 212, 86, CARD, LINE, 10) for i in range(5)]
    tx = []
    for i, (a, b, c, col) in enumerate(cards):
        x = 240 + i * 223
        tx.append(G(f'KPI card {i+1}', T(x + 16, 110, a, 11, 400, SLATE), T(x + 16, 140, b, 26, 700, col), T(x + 16, 160, c, 11, 400, SLATE)))
    return bg, G('KPI cards (sheet 1400x110 in Tableau)', *tx)

def waterfall(lens):
    d = LENS[lens]; ox, oy = 248, 238; W, H, ml, mr, mt, mb = 624, 252, 50, 8, 22, 30
    pw, ph = W - ml - mr, H - mt - mb
    y = lambda v: oy + mt + ph * (1 - (v - d['min']) / (d['max'] - d['min']))
    keys = list(d['steps']); items = [('Opening', d['open'], 'tot')] + [(SHORT[k], d['steps'][k], 'd') for k in keys] + [('Closing', d['close'], 'tot')]
    st = pw / len(items); bw = 36; out = []
    v = d['min']
    while v <= d['max']:
        out.append(L(ox + ml, y(v), ox + W - mr, y(v)) + T(ox + ml - 6, y(v) + 3, d['unit'](v), 9, 400, SLATE, 'end')); v += d['step']
    run = d['open']; prev = None
    for i, (n, val, t) in enumerate(items):
        cx = ox + ml + st * i + st / 2; x = cx - bw / 2
        if t == 'tot': top, bot, col, lab, run = y(val), y(d['min']), GRAY, d['tot'](val), val
        else:
            a, b = run, run + val; top, bot = y(max(a, b)), y(min(a, b)); col = TEAL if val >= 0 else CORAL; lab = d['val'](val); run = b
        if prev: out.append(L(prev[0] + bw, prev[1], x, prev[1], GRAY, 1, '2 2'))
        out.append(G(f'Bar {i+1} {n}', R(round(x, 1), round(top, 1), bw, round(max(bot - top, 1.5), 1), col), T(round(cx, 1), round(top - 5, 1), lab, 9.5, 600, NAVY, 'middle'), T(round(cx, 1), oy + H - 12, n, 9.5, 400, SLATE, 'middle')))
        prev = (x, y(run))
    title = 'How average pay per FTE moved' if lens == 'fte' else 'How total pay moved'
    sub = ('Axis starts at $100k so the drivers are visible. ' if lens == 'fte' else 'Axis starts at $2,800M so the drivers are visible. ') + 'Gray = opening and closing, teal = adds, coral = subtracts.'
    return G('Waterfall (Gantt bar sheet)', T(258, 214, title, 14, 600, NAVY), T(258, 230, sub, 11, 400, SLATE), *out)

def drivers(lens):
    d = LENS[lens]; keys = sorted(d['steps'], key=lambda k: -abs(d['steps'][k])); mx = abs(d['steps'][keys[0]]); out = []
    for i, k in enumerate(keys[:4]):
        v = d['steps'][k]; y0 = 232 + i * 64; w = max(abs(v) / mx * 384, 6)
        lines = textwrap.wrap(WHY[k][lens], 78)[:2]
        parts = [R(910, y0 - 2, 20, 20, NAVY, None, 10), T(920, y0 + 12, i + 1, 10, 600, '#FFFFFF', 'middle'),
                 T(942, y0 + 13, NAME[k], 12.5, 600, NAVY), T(1326, y0 + 13, d['val'](v), 12.5, 700, TEAL if v >= 0 else CORAL, 'end'),
                 R(942, y0 + 20, 384, 5, '#EFEEEA', None, 3), R(942, y0 + 20, round(w, 1), 5, TEAL if v >= 0 else CORAL, None, 3)]
        for j, ln in enumerate(lines): parts.append(T(942, y0 + 40 + j * 13, ln, 10.5, 400, SLATE))
        if i: parts.insert(0, L(910, y0 - 8, 1326, y0 - 8))
        out.append(G(f'Driver {i+1}', *parts))
    return G('Top drivers (dynamic text sheet)', T(910, 214, 'Top drivers, and why', 14, 600, NAVY), T(1326, 214, 'top 4 of 8 · ranked by size', 11, 400, SLATE, 'end'), *out)

def proj(lat, lon, ox, oy):
    x0, x1, y0, y1, W, H = -130, 160, 64, -38, 700, 214
    return ((lon - x0) / (x1 - x0) * W + ox, (y0 - lat) / (y0 - y1) * H + oy)

def stat(x, y, n, label, sub, col):
    return G(f'Stat {label}', L(x, y, x + 310, y), T(x, y + 28, n, 22, 700, col), T(x + len(str(n)) * 13 + 12, y + 28, label, 12.5, 600, NAVY), *[T(x, y + 44 + j * 12, s, 10.5, 400, SLATE) for j, s in enumerate(textwrap.wrap(sub, 62))])

def moves_panel():
    ox, oy = 258, 562; out = []
    for lon in range(-120, 161, 40): p = proj(0, lon, ox, oy); out.append(L(round(p[0], 1), oy, round(p[0], 1), oy + 214))
    for lat in range(-30, 61, 30): p = proj(lat, 0, ox, oy); out.append(L(ox, round(p[1], 1), ox + 700, round(p[1], 1)))
    for a, b, c, dd, intl, w in sorted(D['flows'], key=lambda f: (-f[4], f[5])):
        p, q = proj(a, b, ox, oy), proj(c, dd, ox, oy); mx = (p[0] + q[0]) / 2; dist = math.hypot(p[0] - q[0], p[1] - q[1]); my = (p[1] + q[1]) / 2 - min(dist * 0.28, 60)
        sw = (0.5 + math.sqrt(w) * 0.35) if intl else (0.8 + math.sqrt(w) * 0.5)
        out.append(f'<path d="M{p[0]:.1f} {p[1]:.1f} Q{mx:.1f} {my:.1f} {q[0]:.1f} {q[1]:.1f}" fill="none" stroke="{CORAL if intl else VIOLET}" stroke-opacity="{0.3 if intl else 0.6}" stroke-width="{sw:.2f}"/>')
    for n, la, lo, cc in D['offices']:
        p = proj(la, lo, ox, oy); out.append(f'<circle cx="{p[0]:.1f}" cy="{p[1]:.1f}" r="2.4" fill="{NAVY}"/>')
    for n, la, lo, anc, dx in [('Austin', 30.27, -97.74, 'start', 6), ('New York', 40.75, -73.97, 'start', 6), ('London', 51.5, -0.09, 'end', -6), ('Bengaluru', 13.09, 77.64, 'start', 6), ('Warsaw', 52.23, 20.98, 'start', 5), ('Sao Paulo', -23.59, -46.68, 'start', 6)]:
        p = proj(la, lo, ox, oy); out.append(T(round(p[0] + dx, 1), round(p[1] + 3, 1), n, 9.5, 600, NAVY, anc))
    leg = G('Legend', L(266, 794, 284, 794, VIOLET, 2), T(290, 797, 'Within one country', 10, 400, SLATE), L(418, 794, 436, 794, CORAL, 2), T(442, 797, 'Across a border', 10, 400, SLATE), T(558, 797, 'Line width = people moved. Real map: footprint background.', 10, 400, SLATE))
    col = G('Stats column', T(1000, 576, '392 office moves in FY26', 11, 400, SLATE),
            stat(1000, 584, '90', 'Within the US', 'Between Austin, New York, Seattle and other US offices.', VIOLET),
            stat(1000, 646, '167', 'Within another country', 'Mostly India: Bengaluru, Hyderabad, Pune.', VIOLET),
            stat(1000, 708, '135', 'Across a border', '118 crossed regions, e.g. Bengaluru to Austin.', CORAL),
            L(1000, 770, 1310, 770), *[T(1000, 786 + j * 12, s, 10.5, 400, SLATE) for j, s in enumerate(textwrap.wrap('Cross-border moves change the fringe rate applied to the person, so they weigh more on the fringe and international drivers.', 62))])
    return G('Panel: Office moves (map sheet)', T(258, 538, 'Where people moved between offices', 14, 600, NAVY), T(258, 554, 'Jun 30, 2025 to Jun 30, 2026 · people who changed office', 11, 400, SLATE), G('Map layers', *out), leg, col)

def career_panel():
    lv = [('L1', 'Associate', 0, 22), ('L2', 'Professional', 210, 34), ('L3', 'Senior', 443, 36), ('L4', 'Lead', 586, 9), ('L5', 'Staff / Manager', 574, 13), ('L6', 'Principal / Sr Mgr', 309, 0), ('L7', 'Director', 15, 0), ('L8', 'Sr Director', 1, 0), ('L9', 'VP', 0, 0)]
    ox, oy, W, H, ml = 258, 562, 720, 254, 40; pw = W - ml - 10; base = oy + 150; sc = 100 / 600; st = pw / len(lv); bw = 34; out = []
    for v in (0, 200, 400, 600): yy = base - v * sc; out.append(L(ox + ml, yy, ox + W - 6, yy) + T(ox + ml - 6, yy + 3, v, 9, 400, SLATE, 'end'))
    for i, (c, n, p, dn) in enumerate(lv):
        cx = ox + ml + st * i + st / 2; x = cx - bw / 2; parts = []
        if p: parts.append(R(round(x, 1), round(base - p * sc, 1), bw, max(p * sc, 1.5), TEAL))
        if dn: parts.append(R(round(x, 1), base, bw, max(dn * sc, 1.5), CORAL) + T(round(cx, 1), round(base + dn * sc + 11, 1), f'−{dn}', 9, 400, CORAL, 'middle'))
        parts += [T(round(cx, 1), round(base - p * sc - 5, 1), p, 9.5, 600, NAVY, 'middle'), T(round(cx, 1), oy + H - 52, c, 9.5, 600, NAVY, 'middle'), T(round(cx, 1), oy + H - 40, n, 8.5, 400, SLATE, 'middle')]
        out.append(G(f'Level {c}', *parts))
    bx, bx2 = ox + ml + st * 6 + 4, ox + ml + st * 8 - 4
    out.append(f'<path d="M{bx:.1f} {base-26} V{base-34} H{bx2:.1f} V{base-26}" fill="none" stroke="{AMBER}" stroke-width="1.5"/>' + T(round((bx + bx2) / 2, 1), base - 42, 'Director and above: 16', 10, 600, NAVY, 'middle'))
    leg = G('Legend', R(266, 800, 10, 8, TEAL), T(280, 807, 'Promoted into the level', 10, 400, SLATE), R(418, 800, 10, 8, CORAL), T(432, 807, 'Demoted into the level', 10, 400, SLATE))
    col = G('Stats column', T(1000, 576, 'Career moves in FY26', 11, 400, SLATE),
            stat(1000, 584, '2,138', 'Promotions', 'One level at a time. Pay effect +$19.2M.', TEAL), stat(1000, 646, '114', 'Demotions', 'Pay effect −$0.6M.', CORAL),
            stat(1000, 708, '16', 'Into Director or Sr Director', '15 into Director, 1 into Senior Director.', NAVY), L(1000, 770, 1310, 770), T(1000, 786, 'Bars count people by the level they moved into.', 10.5, 400, SLATE))
    return G('Panel: Career moves (bar sheet)', T(258, 538, 'Who moved up and down the ladder', 14, 600, NAVY), T(258, 554, 'Jun 30, 2025 to Jun 30, 2026 · people by the level they moved into', 11, 400, SLATE), G('Ladder bars', *out), leg, col)

def seg(x, y, w, a, b, on):  # segmented capsule; on = 0 or 1
    h = 30; half = w / 2
    bgs = R(x, y, w, h, 'none', RAIL_LINE, 15)
    onr = f'<rect x="{x + (0 if on == 0 else half)}" y="{y}" width="{half}" height="{h}" rx="15" fill="#FFFFFF"/>'
    return bgs, G(f'Toggle {a}/{b}', onr, T(x + half / 2, y + 19, a, 11, 600 if on == 0 else 400, NAVY if on == 0 else '#C9D2E2', 'middle'), T(x + half * 1.5, y + 19, b, 11, 600 if on == 1 else 400, NAVY if on == 1 else '#C9D2E2', 'middle'))

def build(lens, panel, name):
    bg = [R(0, 0, 1400, 850, PAGE), R(0, 0, 216, 850, NAVY)]
    kbg, kfg = kpi_cards(lens)
    bg += kbg + [R(240, 186, 640, 314, CARD, LINE, 10), R(892, 186, 452, 314, CARD, LINE, 10), R(240, 512, 1104, 306, CARD, LINE, 10)]
    bg += [R(20, 98, 176, 34, 'none', RAIL_LINE), R(20, 138, 176, 34, 'none', RAIL_LINE), R(20, 508, 176, 34, 'none', RAIL_LINE), R(20, 734, 176, 26, 'none', RAIL_LINE)]
    bg += [R(20, 182, 86, 26, '#FFFFFF'), R(110, 182, 86, 26, 'none', RAIL_LINE), R(20, 212, 86, 26, 'none', RAIL_LINE), R(110, 212, 86, 26, 'none', RAIL_LINE), R(0, 288, 216, 30, RAIL_ACTIVE), R(0, 288, 3, 30, TEAL)]
    s1b, s1 = seg(20, 616, 176, 'Per FTE', 'Total', 0 if lens == 'fte' else 1); s2b, s2 = seg(20, 652, 176, 'Loaded', 'Base', 0); s3b, s3 = seg(20, 688, 176, 'Constant FX', 'Nominal', 0)
    pb = [R(1124, 524, 220, 30, 'none', NAVY, 15)]
    pon = 0 if panel == 'mov' else 1
    pill = G('Panel toggle', f'<rect x="{1124 + (0 if pon == 0 else 110)}" y="524" width="110" height="30" rx="15" fill="{NAVY}"/>',
             T(1179, 543, 'Office moves', 12, 600, '#FFFFFF' if pon == 0 else NAVY, 'middle'), T(1289, 543, 'Career moves', 12, 600, '#FFFFFF' if pon == 1 else NAVY, 'middle'))
    bg += [s1b, s2b, s3b] + pb
    chips = [(20, 182, 'FY26', 1), (110, 182, 'FY25', 0), (20, 212, 'Last 4 qtrs', 0), (110, 212, 'Monthly', 0)]
    rail = G('Filter rail (vertical)',
        G('Logo', f'<path d="M24 50 L37 24 L50 50" fill="none" stroke="#FFFFFF" stroke-width="3.2" stroke-linejoin="round" stroke-linecap="round"/><circle cx="37" cy="41" r="3.4" fill="{TEAL}"/>', T(60, 43, 'Arcadia Systems', 16, 600, '#FFFFFF')),
        G('Period', T(20, 86, 'PERIOD', 10, 600, RAIL_MUTED, ls='1.2'), T(32, 120, 'FROM', 10, 400, RAIL_MUTED), T(66, 120, 'Jun 30, 2025', 12, 400, '#FFFFFF'), T(180, 120, '▾', 11, 400, '#FFFFFF', 'end'),
          T(32, 160, 'TO', 10, 400, RAIL_MUTED), T(66, 160, 'Jun 30, 2026', 12, 400, '#FFFFFF'), T(180, 160, '▾', 11, 400, '#FFFFFF', 'end'),
          *[G(f'Quick pick {t}', T(x + 43, y + 17, t, 11, 600 if on else 400, NAVY if on else '#C9D2E2', 'middle')) for x, y, t, on in chips]),
        G('View by', T(20, 276, 'VIEW BY', 10, 600, RAIL_MUTED, ls='1.2'), *[T(27, 307 + i * 30, v, 12.5, 600 if i == 0 else 400, '#FFFFFF' if i == 0 else '#C9D2E2') for i, v in enumerate(['Company', 'Function', 'Leader', 'Department', 'Office', 'Country'])]),
        G('Group', T(20, 496, 'GROUP', 10, 600, RAIL_MUTED, ls='1.2'), T(32, 529, 'Search groups', 12, 400, RAIL_MUTED), T(20, 568, 'All of Arcadia', 12, 600, '#FFFFFF'), T(104, 568, '· 30,015', 12, 400, RAIL_MUTED)),
        G('Measures', T(20, 604, 'MEASURES', 10, 600, RAIL_MUTED, ls='1.2'), s1, s2, s3, T(108, 751, 'Reset filters', 11, 400, '#C9D2E2', 'middle')),
        T(20, 800, 'Data as of Jun 30, 2026.', 10, 400, RAIL_MUTED), T(20, 813, 'Fictional company; data generated', 10, 400, RAIL_MUTED), T(20, 826, 'by Claude Code.', 10, 400, RAIL_MUTED))
    # view rows: first row text baseline fix (rows start at y=288, 30 tall -> baseline y+19)
    title = G('Title and navigation', T(240, 42, 'Compensation Walk', 22, 700, NAVY), T(240, 62, 'Company · Jun 30, 2025 to Jun 30, 2026 · Loaded cost · Constant currency', 12, 400, SLATE),
              T(1344, 42, 'Methodology', 12.5, 400, SLATE, 'end'), T(1252, 42, 'Diagnostics', 12.5, 400, SLATE, 'end'), T(1170, 42, 'Drivers', 12.5, 400, SLATE, 'end'), T(1100, 42, 'Summary', 12.5, 600, NAVY, 'end'), R(1056, 50, 44, 2, TEAL))
    panel_g = moves_panel() if panel == 'mov' else career_panel()
    callouts = G('Callouts (delete before export)', *[G(f'Callout {l}', f'<circle cx="{cx}" cy="{cy}" r="11" fill="{AMBER}" stroke="#FFFFFF" stroke-width="2"/>', T(cx, cy + 4, l, 11, 700, NAVY, 'middle')) for l, cx, cy in [('A', 199, 87), ('B', 1337, 89), ('C', 873, 187), ('D', 1337, 187), ('E', 1337, 513)]])
    foot = T(240, 840, 'Sketch of the Summary page. FY26, Company, loaded cost, constant currency. Fictional company; synthetic data generated by Claude Code.', 10.5, 400, SLATE)
    objs = G('Tableau objects', rail, title, kfg, waterfall(lens), drivers(lens), G('Panel container (dynamic zone visibility)', pill, panel_g), foot, callouts)
    svg = f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="850" viewBox="0 0 1400 850">' + G('Background (export)', *bg) + objs + '</svg>'
    open(os.path.join(OUT, name), 'w').write(svg)

build('fte', 'mov', 'Compensation_Summary_PerFTE_OfficeMoves.svg')
build('tot', 'car', 'Compensation_Summary_Total_CareerMoves.svg')

# ---- colors and button states sheet ----
def sw(x, y, hexv, role, use):
    return G(f'Swatch {role}', R(x, y, 56, 56, hexv, LINE, 6), T(x + 68, y + 20, role, 13, 600, NAVY), T(x + 68, y + 38, hexv, 11, 500, SLATE), T(x + 68, y + 53, use, 10.5, 400, SLATE))
cols = [(NAVY, 'Navy', 'Rail, titles, active toggle'), (TEAL, 'Teal', 'Increase, hires, active marker'), (CORAL, 'Coral', 'Decrease, exits, cross-border'), (VIOLET, 'Violet', 'Moves within one country'),
        (AMBER, 'Amber', 'One highlight only; callouts'), (GRAY, 'Warm gray', 'Opening and Closing bars'), (SLATE, 'Slate', 'Secondary text'), (LINE, 'Light gray', 'Gridlines, card border'), (CARD, 'Off-white', 'Card'), (PAGE, 'Stone', 'Page'),
        (RAIL_MUTED, 'Rail muted', 'Section labels on navy'), (RAIL_LINE, 'Rail line', 'Control outlines on navy'), (RAIL_ACTIVE, 'Rail active', 'Active view row')]
sws = [sw(40 + (i % 3) * 440, 100 + (i // 3) * 82, h, r, u) for i, (h, r, u) in enumerate(cols)]
def pillrow(y, label, items, on_i, dark=False):
    parts = [T(40, y + 19, label, 12, 600, NAVY)]
    if dark: parts.append(R(208, y - 6, 276, 42, NAVY, None, 6))
    x = 220
    for i, t in enumerate(items):
        on = i == on_i; w = 120
        fill = (NAVY if on else '#FFFFFF') if not dark else ('#FFFFFF' if on else NAVY)
        txt = ('#FFFFFF' if on else NAVY) if not dark else (NAVY if on else '#C9D2E2')
        stroke = NAVY if not dark else RAIL_LINE
        parts.append(R(x, y, w, 30, fill, stroke, 15) + T(x + w / 2, y + 19, t, 12, 600, txt, 'middle')); x += w + 14
    return G(label, *parts)
btn = [pillrow(540, 'Lens (on page)', ['Per FTE', 'Total'], 0), pillrow(582, 'Lens (on navy rail)', ['Per FTE', 'Total'], 1, True), pillrow(620, 'Panel toggle', ['Office moves', 'Career moves'], 0),
       pillrow(664, 'Cost (navy rail)', ['Loaded', 'Base'], 0, True), pillrow(706, 'Currency (navy rail)', ['Constant FX', 'Nominal'], 1, True)]
notes = [T(40, 780, 'State rules: On = filled (white on navy rail, navy on page). Off = outline only. Capsule radius 15 (Tableau Corner Radius 16). Cards radius 10. Rail controls radius 0.', 11, 400, SLATE),
         T(40, 798, 'Each toggle is a parameter (p_Lens, p_Cost, p_Currency, p_Panel). Use one custom-shape PNG per state, as in Dashboard #1 (Header/Pill Shape).', 11, 400, SLATE)]
sheet = f'<svg xmlns="http://www.w3.org/2000/svg" width="1400" height="850" viewBox="0 0 1400 850">' + R(0, 0, 1400, 850, PAGE) + T(40, 50, 'Dashboard #2 colors and button states', 22, 700, NAVY) + T(40, 74, 'Same palette as Dashboard #1 (Arcadia Categorical) plus three rail tones.', 12, 400, SLATE) + G('Colors', *sws) + T(40, 520, 'BUTTONS AND TOGGLES', 10, 600, SLATE, ls='1.2') + G('Buttons', *btn) + G('Notes', *notes) + '</svg>'
open(os.path.join(OUT, 'Compensation_Colors_and_Buttons.svg'), 'w').write(sheet)
print('ok')
