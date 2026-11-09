"""Build Who Leads Where.twb (case study 7) from the base workbook Tableau saved right after the Custom SQL was
connected and extracted.

  D4_TWB=<Dashboard #4 workbook> python3 build_d7.py BASE OUT

Close the workbook in Tableau first. One dashboard, 1400 x 850, in two themes: every sheet is written twice (light,
and dark with " (dark)" after its name) and Dynamic Zone Visibility shows one set, driven by the Light / Dark toggle.
Popovers, the expanded tree and the theme are all Dynamic Zone Visibility on calculated booleans (Show Light Pick, ...).
The .twb writer is Dashboard #6's (../d6/twb.py).
"""
import os
import re
import sys
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..', 'd6'))
sys.path.insert(0, HERE)
from twb import Model, Sheet, indent, uid, xesc  # noqa: E402
from d7_calcs import all_calcs, DTYPES, ROLES, SIGNALS  # noqa: E402

BASE, OUT = sys.argv[1], sys.argv[2]
src = open(BASE, encoding='utf-8').read()
W, H = 1400, 850
DASH = 'Who Leads Where'
SHAPES = 'Arcadia D7'
IMG = os.environ.get('D7_IMAGES', '/Users/thiagoalpoin/Documents/Claude/Professional Portfolio/tableau/7 Who Leads Where/Images/')
BRAND = os.environ.get('D7_BRAND', '/Users/thiagoalpoin/Documents/Claude/Professional Portfolio/tableau/Shared/Brand/')   # the Arcadia logos

PAL = {
    'l': dict(bg='#F4F7F6', rail='#FFFFFF', surface='#FFFFFF', pop='#FFFFFF', line='#DFE6E3', ink='#15201D', muted='#56635F',
              accent='#1F7560', soft='#E1F2EB', gap='#A3611A', chip='#EDF2F0', node='#D3E3DD', open='#A9D3C3', focus='#7DBCA5',
              link='#C7D3CF', linksel='#1F7560', ring='#FFFFFF', callow='#EEF6F2', calhigh='#9ACFBC', calsel='#F6DFC0', calwe='#F4F7F6', goldsoft='#E6C48E',
              logo='arcadia_logo_horizontal.png', name=''),
    'd': dict(bg='#141A19', rail='#0F1413', surface='#1A2120', pop='#1E2725', line='#2A3532', ink='#E9EFEC', muted='#9AA9A4',
              accent='#7FD1B9', soft='#1E3A33', gap='#E3B65C', chip='#202A28', node='#34504A', open='#3F7A6A', focus='#58A88F',
              link='#3A4945', linksel='#7FD1B9', ring='#6E8F86', callow='#1D2A27', calhigh='#2F6A5B', calsel='#5A4826', calwe='#161D1C', goldsoft='#8C6A34',
              logo='arcadia_logo_horizontal_reverse.png', name=' (dark)'),
}

# ===================================================================================================== model
meta = re.search(r'<extract .*?<metadata-records>(.*?)</metadata-records>', src, re.S).group(1)
RAW = {}
for r in re.findall(r"<metadata-record class='column'>(.*?)</metadata-record>", meta, re.S):
    RAW[re.search(r'<remote-name>(.*?)</remote-name>', r).group(1)] = re.search(r'<local-type>(.*?)</local-type>', r).group(1)
DS = re.search(r"<datasource caption='[^']*' inline='true' name='(federated\.[a-z0-9]+)'", src).group(1)

PARAMS = {
    'p_Path': {'dtype': 'string', 'value': '|W100001|'},
    'p_Tree': {'dtype': 'string', 'value': 'Dynamic'},
    'p_Worker': {'dtype': 'string', 'value': 'All'},
    'p_Count': {'dtype': 'string', 'value': 'Everyone'},
    'p_Day': {'dtype': 'integer', 'value': 0},
    'p_B0': {'dtype': 'string', 'value': 'W100002'},
    'p_B1': {'dtype': 'string', 'value': 'W100010'},
    'p_Dark': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_Zoom': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_PickOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_CalOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_RulesOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
}
m = Model(DS, RAW, PARAMS, id_prefix='07110700', caption=DASH)
for n in ('point_index', 'day_offset', 'tier'):
    m.raw_role[n] = ('dimension', 'ordinal')
for k, v in all_calcs():
    m.add(k, v, dtype=DTYPES.get(k), role=ROLES.get(k))

SHEETS, ACTIONS = {}, {}
HOVER_LINE = '24'                 # Tableau caps a line at about 30 px: one hover mark per card covers its value band
HOVER_SIZE, HOVER_ALPHA, SPARK_SIZE, BAR_SIZE = '4.6', '1', '0.8', '3.4'    # hover: four 51 px squares cover a card; larger squares make the map fit wider and drift the texts
SIZE = {'seg': '6.2', 'segs': '5.3', 'seg3': '4.5', 'button': '2', 'dot': '1.3', 'brand': '2.2', 'pie': '6'}


def action_id(caption):
    if caption not in ACTIONS:
        ACTIONS[caption] = f'[Action{len(ACTIONS) + 101}_{uuid.uuid4().hex.upper()}]'
    return ACTIONS[caption]


def new(name, deselect=True):
    s = Sheet(m, name)
    if deselect:
        s.deselect = action_id('Deselect ' + name)
        s.f('zzTrue', 'dim'); s.f('zzFalse', 'dim')
    SHEETS[name] = s
    return s


ZZ = [('lod', 'zzTrue'), ('lod', 'zzFalse')]


def how(n):
    if n in m.calcs:
        lv = m.level(n)
        if lv in ('agg', 'tc'):
            return 'agg'
        return 'ord' if m.role(n)[1] == 'ordinal' else 'dim'
    return 'ord' if m.raw_role.get(n, ('', ''))[1] == 'ordinal' else 'dim'


def hide_axis(s, ref, lo=None, hi=None, scope='cols'):
    rng = f" max='{hi}' min='{lo}' range-type='fixed'" if lo is not None else ''
    s.axis_rules += [f"<encoding attr='space' class='0' field='{ref}' field-type='quantitative'{rng} scope='{scope}' type='space' />",
                     f"<format attr='display' class='0' field='{ref}' scope='{scope}' value='false' />",
                     "<format attr='tick-color' value='#00000000' />"]


def no_field_labels(s, scope):
    s.styles.append(f"<style-rule element='worksheet'>\n  <format attr='display-field-labels' scope='{scope}' value='false' />\n</style-rule>")


def tip(n):
    return '{' + n + ('' if n in m.calcs and m.level(n) in ('agg', 'tc') else '|attr') + '}'


_pane = Sheet.pane


def _pane_attr_tips(self, mark, tooltip=None, **kw):
    """a row-level field only on the Tooltip shelf must be an aggregate: {Field} becomes {Field|attr}"""
    if tooltip:
        fix = lambda t: re.sub(r'\{([^{}|]+)\}', lambda mm: tip(mm.group(1)), t)
        tooltip = [[(fix(t), f, z, c) for t, f, z, c in line] for line in tooltip]
    return _pane(self, mark, tooltip=tooltip, **kw)


Sheet.pane = _pane_attr_tips


# ===================================================================================================== map-layer cards
# The KPI cards and the Team pulse tiles are each ONE worksheet: text drawn as map labels. A map puts a point exactly
# where its latitude and longitude say, so every label lands on its card to the pixel; the cards themselves are a PNG
# under the sheet. One sheet instead of 5 (KPIs) or 18 (tiles) matters because Tableau refreshes every sheet on every
# click. Geometry: lon = (x - W/2) * SCALE * FIT_X, lat = -(y - H/2) * SCALE * FIT_Y; two corner points (no fit) pin the
# map's extent to the sheet; FIT stretches for the padding Tableau adds around a fitted map.
SCALE = 0.01
GAP_X = 3                                                        # a label's gap right of its point (lines have none)
FIT_X, FIT_Y = 1.1, 1.1
KW = [218, 217, 218, 217, 218]                                   # the five KPI cards, 12 apart: 1,136 px
KX = [sum(KW[:i]) + 12 * i for i in range(5)]
KPI_W, KPI_H = 1136, 76                                          # the cards' area
KOX = 60                       # the KPI map sheet starts 60 px left of the first card: a fitted map keeps a margin of
KPI_SW = KPI_W + KOX + 24      # about 48 px inside each edge where no text can sit, so the cards stay clear of it
TOX = 20                                                         # the tiles' map sheet reaches 20 px past each side

TW, TH, TGX, TGY = [207, 208], 96, 8, 8                          # the six pulse tiles, two columns, three rows
TILES_W, TILES_H = sum(TW) + TGX, 3 * TH + 2 * TGY
TILES_SW = TILES_W + 2 * TOX
TX = [0, TW[0] + TGX]
TY = [0, TH + TGY, 2 * (TH + TGY)]


# measured on the dashboard (Nov 8, with D7_CALIB=1 dots on the card edges): with every mark inside the corners' frame the
# map is exact, and a label lands about 5 px right of its point; positions are aimed at (x - a) / b so each lands on x
CAL = {('KPI', 'x'): (5.0, 1.0), ('KPI', 'y'): (0.0, 1.0), ('Tiles', 'x'): (0.0, 1.0), ('Tiles', 'y'): (0.0, 1.0)}
OFF = {'KPI': KOX, 'Tiles': TOX}                                 # card x = sheet x - OFF
_W = {'KPI': (KPI_SW, KPI_H), 'Tiles': (TILES_SW, TILES_H)}


def _lon(x, sheet, label=True):
    a, b = CAL[(sheet, 'x')] if label else (CAL[(sheet, 'x')][0] - GAP_X, CAL[(sheet, 'x')][1])
    return ((x + OFF[sheet] - a) / b - _W[sheet][0] / 2) * SCALE * FIT_X


def _lat(y, sheet):
    a, b = CAL[(sheet, 'y')]
    return -((y - a) / b - _W[sheet][1] / 2) * SCALE * FIT_Y


def pt(x, y, sheet, label=True):
    return f'MAKEPOINT({_lat(y, sheet):.6f}, {_lon(x, sheet, label):.6f})'


GEO = {}


def geo(name, formula):
    m.add(name, formula, dtype='spatial', role=('measure', 'nominal'))
    GEO[name] = True
    return name


for nm, w, h in (('KPI', KPI_SW, KPI_H), ('Tiles', TILES_SW, TILES_H)):
    geo(f'{nm} Corner TL', f'MAKEPOINT({h / 2 * SCALE:.6f}, {-w / 2 * SCALE:.6f})')
    geo(f'{nm} Corner BR', f'MAKEPOINT({-h / 2 * SCALE:.6f}, {w / 2 * SCALE:.6f})')
for k in range(5):
    for row, y in (('Title', 15), ('Value', 38), ('Note', 61)):
        geo(f'KPI pt {row} {k + 1}', pt(KX[k] + 12, y, 'KPI'))
    # every mark must stay inside the corners' frame (about 55 px in from each sheet edge, the room Tableau's fit padding
    # takes): one mark outside and Tableau refits the map to the marks, and every text drifts. So card 5's last square
    # stops at the frame (centre at card x 1,075, edge 1,100)
    for j, f in enumerate((1 / 8, 3 / 8, 5 / 8, 7 / 8)):
        geo(f'KPI pt Hover {k + 1}{"abcd"[j]}', pt(min(KX[k] + KW[k] * f, 1075), 38, 'KPI', False))
    # one hover mark per card: a thick invisible line across the card's middle, drawn through the 31 day rows every leader
    # has (round ends ~32 px; the last card stops at the frame)
    x0, x1 = KX[k] + 36, min(KX[k] + KW[k] - 36, 1068)
    lon0 = _lon(x0, 'KPI', False)
    geo(f'KPI pt Hover Line {k + 1}', f'IF [Renew Row] THEN MAKEPOINT({_lat(38, "KPI"):.6f}, {lon0:.6f} + '
        f'{(x1 - x0) * SCALE * FIT_X / CAL[("KPI", "x")][1] / 30:.6f} * [day_offset]) END')
    geo(f'KPI pt Calib {k + 1}', pt(KX[k], 38, 'KPI', False))        # D7_CALIB=1 draws a dot here: each card's left edge
TILE_KEYS = ('Growth', 'Renew', 'Mix', 'Gap', 'Coach', 'Hub')
for i, key in enumerate(TILE_KEYS):
    x0, y0, w0 = TX[i % 2], TY[i // 2], TW[i % 2]
    for row, y in (('Label', 13), ('Value', 33), ('Note', TH - 13)):
        geo(f'Tiles pt {row} {key}', pt(x0 + 12, y0 + y, 'Tiles'))
    a_x, b_x = x0 + 12, w0 - 24                                  # sparks and bars run from x0 + 12 across w0 - 24 px
    bx = CAL[('Tiles', 'x')][1]
    ay, by = CAL[('Tiles', 'y')]
    lon0, per_px_x = _lon(a_x, 'Tiles', False), SCALE * FIT_X / bx
    if key in ('Growth', 'Gap', 'Renew'):
        row, xf, yf, n = {'Growth': ('Pulse Row', 'month_index', 'people', 12), 'Gap': ('Pulse Row', 'month_index', 'gap_people', 12),
                          'Renew': ('Renew Row', 'day_offset', 'left_team', 30)}[key]
        lo = f'{{FIXED : MIN(IF [{row}] THEN [{yf}] END)}}'
        hi = f'{{FIXED : MAX(IF [{row}] THEN [{yf}] END)}}'
        top, ht = y0 + 46, 24
        lon = f'{lon0:.6f} + {b_x * per_px_x / n:.6f} * [{xf}]'
        frac = f'IIF({hi} > {lo}, ([{yf}] - {lo}) / ({hi} - {lo}), 0.5)'
        lat = f'{_lat(top + ht, "Tiles"):.6f} + {ht * SCALE * FIT_Y / by:.6f} * {frac}'
        geo(f'Tiles pt Spark {key}', f'IF [{row}] THEN MAKEPOINT({lat}, {lon}) END')
    else:
        # a bar is a thick line through all 13 month rows (a point on every row keeps the line unbroken)
        share = {'Mix': 'Mix Now', 'Coach': 'Coach Share', 'Hub': 'Hub Now'}[key]
        lat = f'{_lat(y0 + 62, "Tiles"):.6f}'
        geo(f'Tiles pt Track {key}', f'IF [Pulse Row] THEN MAKEPOINT({lat}, {lon0:.6f} + {b_x * per_px_x / 12:.6f} * [month_index]) END')
        geo(f'Tiles pt Fill {key}', f'IF [Pulse Row] THEN MAKEPOINT({lat}, {lon0:.6f} + {b_x * per_px_x / 12:.6f} * [month_index] * IFNULL([{share}], 0)) END')

_inst, _inst_decl = Model.inst, Model.inst_decl


def _inst_geo(self, name, how='auto'):
    if name in GEO and how in ('auto', 'clct'):
        return f'[clct:{self.cid[name]}:nk]', 'clct'
    return _inst(self, name, how)


def _inst_decl_geo(self, name, how='auto', order=None):
    if name in GEO and how in ('auto', 'clct'):
        c = self.cid[name]
        return f"<column-instance column='[{c}]' derivation='Collect' name='[clct:{c}:nk]' pivot='key' type='nominal' />"
    return _inst_decl(self, name, how, order)


Model.inst, Model.inst_decl = _inst_geo, _inst_decl_geo
LATLON = (f'[{DS}].[Latitude (generated)]', f'[{DS}].[Longitude (generated)]')


def map_sheet(s, nm):
    """turn a Sheet into a borderless map; layers are added with map_layer"""
    s.rows, s.cols = LATLON
    s.axis_rules += [f"<format attr='display' class='0' field='{LATLON[0]}' scope='rows' value='false' />",
                     f"<format attr='display' class='0' field='{LATLON[1]}' scope='cols' value='false' />",
                     "<format attr='tick-color' value='#00000000' />"]
    s.styles.append("<style-rule element='map'>\n  <format attr='washout' value='0' />\n</style-rule>")
    s.is_map = True
    s.pane('Circle', pane_id=1)
    for c in ('TL', 'BR'):                      # not inert: a map fits its interactive marks, so the corners set the extent
        map_layer(s, f'{nm} Corner {c}', 'Circle', inert=False, transparency='1')   # alpha 0 marks are left out of the fit


def map_layer(s, point, mark='Circle', label=None, enc=(), size='0.01', color=None, align='right', valign='center', tooltip=None,
              transparency='0', inert=None):
    pid = len(s.panes) + 1
    s.pane(mark, pane_id=pid, enc=ZZ + list(enc) + [('lod', point, 'clct')], label=label, tooltip=tooltip, size=size,
           transparency=transparency, color=color, align=align, valign=valign, stroke='false' if mark != 'Line' else None)
    inert = '' if (tooltip or inert is False) else " inert='true'"
    s.panes[-1] = s.panes[-1].replace(f"<pane id='{pid}' ", f"<pane generated-title='{xesc(point)}' id='{pid}'{inert} ", 1)


_xml = Sheet.xml


def _xml_map(self):
    x = _xml(self)
    if getattr(self, 'is_map', False):
        x = x.replace("\n    <panes>\n", "\n    <panes customization-axis='layer'>\n", 1)
        x = re.sub(r"(      </datasources>\n)", r"\1      <mapsources>\n        <mapsource name='' />\n      </mapsources>\n", x, count=1)
    return x


Sheet.xml = _xml_map


# ===================================================================================================== sheets, per theme
def page(th):
    P = PAL[th]
    sfx = P['name']
    ink, mu, ac, gp = P['ink'], P['muted'], P['accent'], P['gap']
    S = {}

    def sh(name, deselect=True):
        s = new(name + sfx, deselect)
        S[name] = s.name
        return s

    def text_sheet(name, label, tooltip=None, valign='top', align='left'):
        s = sh(name)
        s.pane('Text', enc=ZZ, label=label, tooltip=tooltip, valign=valign, align=align)
        return s

    # ---------------------------------------------------------------- headline and KPIs
    text_sheet('Headline', [
        [('{Head Eyebrow}', 'semi', 8, mu)],
        [('{Head Leads}', 'semi', 16, ink), ('{Head People}', 'semi', 16, ac), ('{Head In}', 'semi', 16, ink),
         ('{Head Gaps}', 'semi', 16, gp), ('{Head Tail}', 'semi', 16, ink)]],
        tooltip=[[('{F Name}', 'bold', 10, ink), (' · ', 'book', 10, mu), ('{F Title}', 'book', 10, ink)],
                 [('{F Office}', 'book', 9, mu), (', ', 'book', 9, mu), ('{F Country}', 'book', 9, mu)],
                 [('Alignment gaps are flags, not errors: many have a good business reason.', 'book', 9, mu)]])
    KPI = [('PEOPLE LED', 'K1 Value', 'K1 Note', ink,
            [[('{F People Txt}', 'bold', 10, ink), (' {Worker Words} below {F Name}', 'book', 10, ink)],
             [('{K1 Note}', 'book', 9, mu), (' through ', 'book', 9, mu), ('{F Managers Below}', 'semi', 9, ink), (' managers', 'book', 9, mu)],
             [('Executive officers lead but are not counted.', 'book', 9, mu)]]),
           ('AT WORK', 'K2 Value', 'K2 Note', ac,
            [[('{K2 Value}', 'bold', 10, ac), (' at work on {Day Text}', 'book', 10, ink)],
             [('Off: ', 'book', 9, mu), ('{F Day Off PTO}', 'semi', 9, ink), (' time off · ', 'book', 9, mu), ('{F Day Off Leave}', 'semi', 9, ink),
              (' leave · ', 'book', 9, mu), ('{F Day Off Holiday}', 'semi', 9, ink), (' public holiday', 'book', 9, mu)],
             [('A half day counts as at work. Pick another day in the rail.', 'book', 9, mu)]]),
           ('LAYERS BELOW', 'K3 Value', 'K3 Note', ink,
            [[('{K3 Value}', 'bold', 10, ink), (' layers of management below {F Name}', 'book', 10, ink)],
             [('{K3 Note}', 'book', 9, mu)]]),
           ('MEDIAN SPAN', 'K4 Value', 'K4 Note', ink,
            [[('Median span of control: ', 'book', 10, ink), ('{K4 Value}', 'bold', 10, ink), (' direct reports', 'book', 10, ink)],
             [('Across every manager in the organization, {F Name} included', 'book', 9, mu)],
             [('{F Mgr 15}', 'semi', 9, ink), (' managers lead 15 or more; ', 'book', 9, mu), ('{F Mgr One}', 'semi', 9, ink),
              (' lead only one', 'book', 9, mu)]]),
           ('ALIGNMENT GAPS', 'K5 Value', 'K5 Note', gp,
            [[('{K5 Value}', 'bold', 10, gp), (' {Worker Words} with at least one alignment signal', 'book', 10, ink)],
             [('Solid line: ', 'book', 9, mu), ('{F Solid Gaps}', 'semi', 9, ink), (' · Matrix line: ', 'book', 9, mu), ('{F Matrix Gaps}', 'semi', 9, ink)],
             [('Flags, not errors: see Org design alignment on the right.', 'book', 9, mu)]])]
    # the five KPI cards: one map sheet (title, value and note per card; one invisible thick line per card carries its tooltip)
    s = sh('KPI Map')
    map_sheet(s, 'KPI')
    for i, (lab, v, note, col, tp) in enumerate(KPI, 1):
        map_layer(s, f'KPI pt Title {i}', label=[[(lab, 'semi', 7.5, mu)]])
        map_layer(s, f'KPI pt Value {i}', label=[[('{' + v + '}', 'semi', 18, col)]])
        map_layer(s, f'KPI pt Note {i}', label=[[('{' + note + '}', 'book', 8, mu)]])
        if os.environ.get('D7_CALIB'):
            map_layer(s, f'KPI pt Calib {i}', 'Circle', size='0.6', transparency='255', color='#FF00FF')
        map_layer(s, f'KPI pt Hover Line {i}', 'Line', enc=[('path', 'day_offset', 'ord')], size=HOVER_LINE, tooltip=tp,
                  transparency=HOVER_ALPHA, color=ink)

    # ---------------------------------------------------------------- rail
    ORG_ACT = ('Toggle Pick', 'Close Panel')
    s = sh('Org Field')
    s.filter_member('Org Row', 'true')
    dp = s.f('depth_from_top', 'ord')
    s.rows = dp
    s.hide_labels.append(dp)
    no_field_labels(s, 'rows')
    s.cell_size = (None, 20, dp)
    s.pane('Text', enc=ZZ + [('lod', n, how(n)) for n in ORG_ACT], valign='center', align='left',
           label=[[('{Lvl}', 'semi', 7.5, mu), ('{Org Row Other}', 'book', 9, ink), ('{Org Row Focus}', 'bold', 9.5, ac)]],
           tooltip=[[('{Org Row Tip}', 'book', 9, ink)], [("Click to open any leader's organization", 'semi', 9, ac)]])
    def seg_sheet(name, row_filter, key, shape, act_fields, size, tiptext):
        s = sh(name)
        s.filter_member(row_filter, 'true')
        k = s.f(key, 'ord')
        s.cols = k
        s.hide_labels.append(k)
        no_field_labels(s, 'cols')
        s.pane('Shape', enc=ZZ + [('shape', shape, 'dim')] + [('lod', n, how(n)) for n in act_fields], size=size,
               transparency='255', stroke='false', align='center', tooltip=[[(tiptext, 'book', 9, mu)]])
        return s

    seg_sheet('Worker Toggle', 'Worker Row', 'Worker Key', 'Worker Shape', ['worker_type'], SIZE['seg3'],
              'Count employees, contingent workers, or both')
    seg_sheet('Count Toggle', 'Seg Row', 'Seg Key', 'Count Shape', ['Count Option'], SIZE['seg'],
              "What the tree's circles count: everyone, or only those at work on the day below")
    seg_sheet('Tree Toggle', 'Seg Row', 'Seg Key', 'Tree Shape', ['Seg Mode'], SIZE['segs'],
              'Dynamic: one level at a time · Static: three levels at once')
    seg_sheet('Tree Toggle Wide', 'Seg Row', 'Seg Key', 'Tree Shape', ['Seg Mode'], SIZE['segs'],
              'Dynamic: one level at a time · Static: three levels at once')
    seg_sheet('Theme Toggle', 'Seg Row', 'Seg Key', 'Theme Shape', ['Theme Is Dark', 'Close Panel'], SIZE['segs'], 'Light or dark page')

    s = sh('Cal Field')
    s.pane('Text', enc=ZZ + [('lod', n, how(n)) for n in ('Toggle Cal', 'Close Panel')], valign='top',
           label=[[('{Day Lead}', 'bold', 9.5, ink), ('   ›', 'semi', 9.5, ac)], [('{Cal Field Value}', 'semi', 10, ac)]],
           tooltip=[[('Pick a day in the next 30 days', 'semi', 9, ink)]])

    def button_sheet(name, shape, act_fields, size, tiptext, row='Focus Row'):
        s = sh(name)
        s.filter_member(row, 'true')
        s.pane('Shape', enc=ZZ + [('shape', shape, 'dim')] + [('lod', n, how(n)) for n in act_fields], size=size,
               transparency='255', stroke='false', align='center', tooltip=[[(tiptext, 'book', 9, mu)]] if tiptext else None)
        return s

    button_sheet('Expand', 'Zoom Shape', ['Toggle Zoom'], SIZE['button'], 'Expand the tree')
    button_sheet('Expand Wide', 'Zoom Shape', ['Toggle Zoom'], SIZE['button'], 'Back to the tree and the alignment panel')
    button_sheet('Info', 'Info Shape', ['Toggle Rules', 'Close Panel'], SIZE['button'], 'How alignment is read')
    for p in ('Pick', 'Cal', 'Rules'):
        button_sheet(f'{p} Close', 'Close Shape', ['Close Panel'], SIZE['button'], 'Close')
    button_sheet('Credit GitHub', 'GitHub Shape', [], SIZE['brand'], 'Thiago Alpoin on GitHub')
    button_sheet('Credit LinkedIn', 'LinkedIn Shape', [], SIZE['brand'], 'Thiago Alpoin on LinkedIn')
    text_sheet('Org Sub', [[('{Org Sub}', 'book', 7.5, mu)]])
    text_sheet('Footnote', [[('{Footnote}', 'book', 9, mu)]], valign='center')

    # ---------------------------------------------------------------- the tree
    text_sheet('Tree Hint', [[('{Tree Hint}', 'book', 8.5, mu)]])
    text_sheet('Tree Hint Wide', [[('{Tree Hint}', 'book', 8.5, mu)]])
    TIP = [[('{leader_name|attr}', 'bold', 10, ink), ('  {N Lvl}', 'semi', 9, ac)],
           [('{job_title|attr}', 'book', 9, mu)],
           [('{Tip People|attr}', 'book', 9, ink)],
           [('{Tip Gaps|attr}', 'semi', 9, gp)],
           [('{Tip At Work|attr}', 'book', 9, ink)],
           [('{Tip Action|attr}', 'semi', 9, ac)]]
    ACT = ['Focus Target', 'Path Target', 'Dynamic Text']
    for name in ('Tree', 'Tree Wide'):
        s = sh(name, deselect=True)
        s.filter_member('In Tree View', 'true')
        x = s.f('X Plot', 'min')
        yl, yn = s.f('Y Link', 'min'), s.f('Y Node', 'min')
        s.cols, s.rows = x, f'({yl} + {yn})'
        # automatic ranges without zero: Dynamic is one company tree, so the view pans and zooms to the part on the page
        # (Tableau animates the move); Static fits its 0 to 1 canvas
        s.axis_rules += [f"<encoding attr='space' class='0' domain-expand='false' field='{x}' field-type='quantitative' scope='cols' type='space' />",
                         f"<format attr='display' class='0' field='{x}' scope='cols' value='false' />",
                         f"<encoding attr='space' class='0' domain-expand='false' field='{yl}' field-type='quantitative' scope='rows' type='space' />",
                         f"<format attr='display' class='0' field='{yl}' scope='rows' value='false' />",
                         f"<encoding attr='space' class='0' domain-expand='false' field='{yn}' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />",
                         f"<format attr='display' class='0' field='{yn}' scope='rows' value='false' />",
                         "<format attr='tick-color' value='#00000000' />"]
        s.pane('Automatic', pane_id=2, enc=[])
        s.pane('Line', pane_id=3, y_axis=yl, size='0.6', transparency='255',
               enc=ZZ + [('path', 'point_index', 'ord'), ('lod', 'node_id', 'dim'), ('lod', 'mark_type', 'dim'), ('color', 'Link Kind', 'dim')]
               + [('lod', n, 'dim') for n in ACT])
        s.pane('Pie', pane_id=4, y_axis=yn, size=SIZE['pie'], transparency='255', stroke='true' if th == 'd' else 'false', align='center', valign='bottom',
               enc=ZZ + [('lod', 'Wedge Order', 'ord'), ('lod', 'node_id', 'dim'), ('color', 'Pie Color', 'dim'), ('size', 'Pie Size', 'min'), ('wedge-size', 'Pie Angle', 'sum')]
               + [('lod', n, 'dim') for n in ACT],
               label=[[('{Node Label Name}', 'semi', 8.5, ink)], [('{Node Label Count}', 'book', 8, mu)]], tooltip=TIP,
               extra_mark_fmt="<format attr='mark-labels-mode' value='all' />" + (f"<format attr='stroke-color' value='{P['ring']}' />" if th == 'd' else ''))

    # ---------------------------------------------------------------- the Team pulse card
    good, bad, neutral = ac, gp, mu
    text_sheet('Pulse Sub', [[('{Pulse Sub}', 'book', 8.5, mu)]])
    text_sheet('Pulse State', [[('{Cov State Good}', 'semi', 8, good), ('{Cov State Bad}', 'semi', 8, bad)]], valign='center', align='center')
    text_sheet('Pulse Hero', [
        [('{Cov Value Good}', 'bold', 24, good), ('{Cov Value Bad}', 'bold', 24, bad), ('{Cov Sub}', 'book', 9.5, mu)]],
        valign='center',
        tooltip=[[('Share of the team at work today, after time off, leave and public holidays', 'semi', 9, ink)],
                 [('The floor (', 'book', 9, mu), ('{Floor Txt}', 'semi', 9, ink), (') is the coverage a leader plans to keep; a Tableau Pulse threshold on Tableau Cloud', 'book', 9, mu)]])
    s = sh('Pulse Week')
    s.filter_member('Week Row', 'true')
    do = s.f('day_offset', 'ord')
    s.cols = do
    s.hide_labels.append(do)
    no_field_labels(s, 'cols')
    cv = s.f('Cov Day', 'sum')
    s.rows = cv
    hide_axis(s, cv, 0.5, 1.06, scope='rows')
    fl = s.f('Floor Mark', 'agg')
    s.pane('Bar', enc=ZZ + [('color', 'Cov Kind', 'dim'), ('lod', 'Floor Mark', 'agg')], size='1.3', transparency='255', stroke='false',
           align='center', refs=[s.refline(0, cv, fl, mu, 1, 'dashed')],
           tooltip=[[('{Cov Day Label}', 'bold', 10, ink), ('  {Cov Day Pct} at work', 'book', 10, ink)],
                    [('{at_work|sum}', 'semi', 9, ink), (' of ', 'book', 9, mu), ('{people|sum}', 'semi', 9, ink), (' · floor ', 'book', 9, mu), ('{Floor Txt}', 'semi', 9, ink)]])
    s = sh('Pulse Days')
    s.filter_member('Week Row', 'true')
    do = s.f('day_offset', 'ord')
    s.cols = do
    s.hide_labels.append(do)
    no_field_labels(s, 'cols')
    s.pane('Text', enc=ZZ, valign='top', align='center',
           label=[[('{Cov Day Label}', 'semi', 8.5, ink)], [('{Cov Day Pct}', 'book', 8.5, mu)]])
    s.tooltip_off = True
    text_sheet('Pulse Insight', [[('{Insight Lead}', 'bold', 9, ink), ('{Insight Body}', 'book', 9, ink)]])
    TILES = [('Growth', 'TEAM GROWTH', '{Growth Txt}', [('  {Growth Chip Good}', 'semi', 8.5, good), ('{Growth Chip Bad}', 'semi', 8.5, bad)], '{Ago Label}'),
             ('Renew', 'RENEWALS AHEAD', '{Renew Txt}', [('  {Renew Chip}', 'semi', 8.5, neutral)], '{Renew Note}'),
             ('Mix', 'CONTINGENT MIX', '{Mix Txt}', [('  {Mix Chip}', 'semi', 8.5, neutral)], '{Mix Note}'),
             ('Gap', 'ALIGNMENT TREND', '{Gap Txt}', [('  {Gap Chip Good}', 'semi', 8.5, good), ('{Gap Chip Bad}', 'semi', 8.5, bad)], 'people with a gap, {Ago Label}'),
             ('Coach', 'COACHING CAPACITY', '{Coach Txt}', [], '{Coach Note}'),
             ('Hub', 'IN THE HUB', '{Hub Txt}', [('  {Hub Chip Good}', 'semi', 8.5, good), ('{Hub Chip Bad}', 'semi', 8.5, bad)], '{Hub Note}')]
    # the six tiles: one map sheet (label, value and chips, note; sparks and bars as line layers)
    s = sh('Tiles Map')
    map_sheet(s, 'Tiles')
    for key, lab, val, chips, note in TILES:
        map_layer(s, f'Tiles pt Label {key}', label=[[(lab, 'semi', 7.5, mu)]])
        map_layer(s, f'Tiles pt Value {key}', label=[[(val, 'bold', 16, ink)] + chips])
        map_layer(s, f'Tiles pt Note {key}', label=[[(note, 'book', 8, mu)]])
        if key in ('Growth', 'Gap', 'Renew'):
            xf = 'day_offset' if key == 'Renew' else 'month_index'
            enc = [('path', xf, 'ord')] + ([('color', 'Gap Trend Kind', 'dim')] if key == 'Gap' else [])
            map_layer(s, f'Tiles pt Spark {key}', 'Line', enc=enc, size=SPARK_SIZE, transparency='255',
                      color=None if key == 'Gap' else (good if key == 'Growth' else mu))
        else:
            map_layer(s, f'Tiles pt Track {key}', 'Line', enc=[('path', 'month_index', 'ord')], size=BAR_SIZE, transparency='255', color=P['chip'])
            map_layer(s, f'Tiles pt Fill {key}', 'Line', enc=[('path', 'month_index', 'ord')], size=BAR_SIZE, transparency='255', color=good)

    # ---------------------------------------------------------------- the leader picker
    for k in range(7):
        col = f'Pick L{k}'
        s = sh(col)
        s.filter_member(f'Pick Row L{k}', 'true')
        rk, li = s.f('Pick Rank', 'ord'), s.f('leader_id', 'dim')
        s.rows = f'({rk} / {li})'
        s.hide_labels += [rk, li]
        no_field_labels(s, 'rows')
        s.cell_size = (None, 30, li)
        tx = s.f('Tick X', 'agg')
        s.cols = tx
        hide_axis(s, tx, 0, 10)
        s.pane('Shape', enc=ZZ + [('shape', 'Pick Shape', 'dim')] + [('lod', n, how(n)) for n in ('leader_id', 'path', 'Pick Keep Open')],
               size=SIZE['dot'], transparency='255', stroke='false', align='right',
               label=[[('{leader_name}', 'semi', 9, ink), ('  {Pick People}', 'book', 8, mu)]],
               tooltip=[[('{leader_name}', 'bold', 10, ink), ('  {Lvl}', 'semi', 9, ac)], [('{Pick Sub}', 'book', 9, mu)],
                        [('{people}', 'semi', 9, ink), (' people led, directly and indirectly', 'book', 9, mu)],
                        [('Click to open their organization' + ('' if k == 6 else ' and see the leaders below'), 'semi', 9, ac)]],
               extra_mark_fmt="<format attr='mark-labels-mode' value='all' />")
        if k:
            text_sheet(f'Pick Head L{k}', [[(f'{{Pick Head L{k}}}', 'semi', 7.5, mu)]])

    # ---------------------------------------------------------------- the calendar
    text_sheet('Cal Title', [[('{Cal Title}', 'semi', 12, ink)],
                             [('At work each day after time off, leave and public holidays · click a day', 'book', 8.5, mu)]])
    s = sh('Calendar')
    s.filter_member('Cal Row', 'true')
    wk, dw = s.f('Cal Week', 'ord'), s.f('Cal DOW', 'ord')
    s.rows, s.cols = wk, dw
    s.hide_labels += [wk, dw]
    no_field_labels(s, 'rows'); no_field_labels(s, 'cols')
    s.pane('Square', enc=ZZ + [('color', 'Cal Kind', 'dim'), ('lod', 'day_offset', 'ord'), ('lod', 'Close Panel', 'dim')],
           size='4.2', transparency='255', stroke='false', align='center', valign='center',
           label=[[('{Cal Day Label}', 'book', 7.5, mu)], [('{Cal Value}', 'bold', 9.5, ink)], [('{Cal Off}', 'book', 7.5, mu)]],
           tooltip=[[('{Cal Tip}', 'bold', 10, ink)], [('{Cal Value}', 'semi', 9, ac), (' at work of ', 'book', 9, ink), ('{people|sum}', 'semi', 9, ink)],
                    [('Off: ', 'book', 9, mu), ('{off_time_off|sum}', 'semi', 9, ink), (' time off · ', 'book', 9, mu), ('{off_leave|sum}', 'semi', 9, ink),
                     (' leave · ', 'book', 9, mu), ('{off_public_holiday|sum}', 'semi', 9, ink), (' holiday', 'book', 9, mu)],
                    [('Left the team by then: ', 'book', 9, mu), ('{left_team|sum}', 'semi', 9, ink)]])
    text_sheet('Cal Summary', [[('{Quiet Text}', 'semi', 9, ac)], [('{Left Text}', 'book', 8.5, mu)],
                               [('Requests are known only once they are made, so days further out show fewer people off.', 'book', 8, mu)]])
    return S


L, D = page('l'), page('d')

# every sheet gets a context filter, so its FIXED reads scan only the rows it needs (see Ctx Leaders in d7_calcs.py)
CTX = {'KPI Map': 'Ctx Pulse', 'Tiles Map': 'Ctx Pulse', 'Cal Field': 'Ctx Days', 'Calendar': 'Ctx Days', 'Cal Summary': 'Ctx Days',
       'Tree': 'Ctx Tree', 'Tree Wide': 'Ctx Tree'}
CTX.update({n: 'Ctx Pulse' for n in ('Pulse Sub', 'Pulse State', 'Pulse Hero', 'Pulse Week', 'Pulse Days', 'Pulse Insight')})
# ... and the context also says when the sheet can be seen: its theme, its popover, the narrow or the wide tree. Tableau
# refreshes every sheet on every click, hidden ones included; a hidden sheet's context is then FALSE (a parameter-only
# test, folded before the query), so it compiles and returns nothing instead of running its full query
NARROW = {'Tree', 'Tree Hint', 'Tree Toggle', 'Expand', 'Info', 'Pulse Sub', 'Pulse State', 'Pulse Hero', 'Pulse Week', 'Pulse Days',
          'Pulse Insight', 'Tiles Map'}
POPOVER = {'Cal Title': 'p_CalOpen', 'Calendar': 'p_CalOpen', 'Cal Summary': 'p_CalOpen', 'Cal Close': 'p_CalOpen', 'Rules Close': 'p_RulesOpen'}


def seen(base, dark):
    conds = [('Dark', '[p_Dark]') if dark else ('Light', 'NOT [p_Dark]')]
    if base.startswith('Pick '):
        conds.append(('Pick', '[p_PickOpen]'))
    elif base in POPOVER:
        conds.append((POPOVER[base][2:-4], f'[{POPOVER[base]}]'))
    elif base.endswith('Wide'):
        conds.append(('Wide', '[p_Zoom]'))
    elif base in NARROW:
        conds.append(('Narrow', 'NOT [p_Zoom]'))
    return conds


for name, sh_ in SHEETS.items():
    base = name.replace(' (dark)', '')
    ctx = CTX.get(base, 'Ctx Leaders')
    conds = seen(base, name != base)
    key = ctx + ' · ' + ' '.join(c[0] for c in conds)
    if key not in m.calcs:
        m.add(key, f'[{ctx}] AND ' + ' AND '.join(c[1] for c in conds))
    sh_.filter_member(key, 'true')
    sh_.filters.insert(0, sh_.filters.pop().replace("'>\n", "' context='true'>\n", 1))

# ===================================================================================================== datasource styles
def bucket_map(field, kind, mapping):
    ms = '\n'.join(f"  <map to='{to}'>\n    <bucket>&quot;{xesc(b)}&quot;</bucket>\n  </map>" for b, to in mapping)
    return f"<encoding attr='{kind}' field='{field}' type='{'palette' if kind == 'color' else 'shape'}'>\n{ms}\n</encoding>"


enc_rules, styled = [], []
for n, keys in (('Pie Color', ('gap', 'focus', 'open', 'node', 'none')), ('Link Kind', ('sel', 'link')), ('Cal Kind', ('we', 'sel', 'high', 'low')),
                ('Cov Kind', ('today', 'ok', 'low')), ('Gap Trend Kind', ('good', 'bad'))):
    colours = {'none': 'surface', 'gap': 'gap', 'focus': 'focus', 'open': 'open', 'node': 'node', 'sel': 'linksel', 'link': 'link',
               'we': 'calwe', 'high': 'calhigh', 'low': 'callow', 'today': 'accent', 'ok': 'calhigh', 'good': 'accent', 'bad': 'gap'}
    mp = []
    for th in ('l', 'd'):
        for k in keys:
            c = PAL[th]['calsel'] if (n == 'Cal Kind' and k == 'sel') else PAL[th]['goldsoft'] if (n == 'Cov Kind' and k == 'low') else PAL[th][colours[k]]
            mp.append((f'{k}_{th}', c))
    enc_rules.append(bucket_map(m.inst(n, 'dim')[0], 'color', mp)); styled.append((n, 'dim'))
shape_files = sorted(f[:-4] for f in os.listdir(os.environ.get('D7_SHAPES', os.path.join(HERE, 'shapes'))) if f.endswith('.png'))
for n, pre in (('Worker Shape', 'd7_worker_'), ('Count Shape', 'd7_count_'), ('Tree Shape', 'd7_tree_'), ('Theme Shape', 'd7_theme_'),
               ('Zoom Shape', ('d7_expand', 'd7_collapse')), ('Info Shape', 'd7_info'), ('Close Shape', 'd7_close'),
               ('GitHub Shape', 'd7_github'), ('LinkedIn Shape', 'd7_linkedin'), ('Pick Shape', 'd7_dot_')):
    pres = pre if isinstance(pre, tuple) else (pre,)
    files = [f for f in shape_files if f.startswith(pres)]
    enc_rules.append(bucket_map(m.inst(n, 'dim')[0], 'shape', [(f, f'{SHAPES}/{f}.png') for f in files])); styled.append((n, 'dim'))

ds_insts = '\n'.join(m.inst_decl(n, h) for n, h in styled)
group = (f"<group caption='Action (zzFalse)' hidden='true' name='[Action (zzFalse)]' name-style='unqualified' user:auto-column='sheet_link'>\n"
         f"  <groupfilter function='crossjoin'>\n    <groupfilter function='level-members' level='[{m.cid['zzFalse']}]' />\n  </groupfilter>\n</group>")
calc_decls = '\n'.join(m.decl(c) for c in m.order)
raw_over = '\n'.join(m.raw_decl(r) for r in sorted(m.raw_role))
ds_style = "<style>\n  <style-rule element='mark'>\n" + indent('\n'.join(enc_rules), 4) + "\n  </style-rule>\n</style>"
ds_params = "<datasource-dependencies datasource='Parameters'>\n" + indent('\n'.join(m.param_decl(p) for p in m.params), 2) + "\n</datasource-dependencies>"

out = src
d4 = open(os.environ['D4_TWB'], encoding='utf-8').read()
man = r'  <document-format-change-manifest>.*?</document-format-change-manifest>\n'
out = out.replace(re.search(man, out, re.S).group(0), re.search(man, d4, re.S).group(0), 1)
out = re.sub(r"<datasource caption='[^']*' inline='true' name='" + re.escape(DS) + "'", f"<datasource caption='{DASH}' inline='true' name='{DS}'", out, count=1)
pds = ("    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>\n      <aliases enabled='yes' />\n"
       + indent('\n'.join(m.param_decl(p) for p in m.params), 6) + "\n    </datasource>\n")
out = out.replace("  <datasources>\n", "  <datasources>\n" + pds, 1)
# animations on for the whole workbook: a click grows the tree out of the leader instead of redrawing it
assert out.count("  </preferences>\n") == 1
out = out.replace("  </preferences>\n", "  </preferences>\n  <style>\n    <style-rule element='animation'>\n"
                  "      <format attr='animation-on' value='ao-on' />\n    </style-rule>\n  </style>\n", 1)
ext = "      <extract "
assert out.count(ext) == 1
out = out.replace(ext, indent(calc_decls + '\n' + raw_over + '\n' + ds_insts + '\n' + group, 6) + '\n' + ext, 1)   # after every base column
lay = "      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />\n"
assert out.count(lay) == 1
out = out.replace(lay, lay + indent(ds_style, 6) + '\n', 1)
sv = re.search(r"      <semantic-values>.*?</semantic-values>\n", out, re.S).group(0)
out = out.replace(sv, sv + indent(ds_params, 6) + '\n', 1)

# ===================================================================================================== dashboard zones
zid = [10]
VIS = {}            # zone id -> calc that shows it


def nid():
    zid[0] += 1
    return zid[0]


def z(px, py, pw, ph):
    return f"h='{round(ph / H * 100000)}' w='{round(pw / W * 100000)}' x='{round(px / W * 100000)}' y='{round(py / H * 100000)}'"


def style(bg=None, border=None, radius=None, pad=None):
    st = [f"<format attr='border-color' value='{border or '#000000'}' />",
          f"<format attr='border-style' value='{'solid' if border else 'none'}' />",
          f"<format attr='border-width' value='{1 if border else 0}' />", "<format attr='margin' value='0' />"]
    if radius:
        st.append(f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='{radius}' />")
    if pad:
        t, r, b, l = pad
        st += [f"<format attr='padding-top' value='{t}' />", f"<format attr='padding-right' value='{r}' />",
               f"<format attr='padding-bottom' value='{b}' />", f"<format attr='padding-left' value='{l}' />"]
    if bg:
        st.append(f"<format attr='background-color' value='{bg}' />")
    return "<zone-style>\n" + indent('\n'.join(st), 2) + "\n</zone-style>"


# ----------------------------------------------------------------- containers
# Every card is one floating layout container; everything inside it is tiled. A node's `size` is its fixed size along
# its parent's direction (height in a vertical container, width in a horizontal one); None shares what is left.
HIDE = {}           # zone id -> hidden when the workbook opens


class N:
    def __init__(self, kind, size=None, kids=(), **kw):
        self.kind, self.size, self.kids, self.kw = kind, size, list(kids), kw


def V(kids, size=None, **kw):
    return N('vert', size, kids, **kw)


def Hz(kids, size=None, **kw):
    return N('horz', size, kids, **kw)


def Sh(name, size=None, **kw):
    return N('sheet', size, name=name, **kw)


def Tx(runs, size=None, **kw):
    return N('text', size, runs=runs, **kw)


def Gap(size=None, bg=None):
    return N('empty', size, bg=bg)


def Img(path, size=None):
    return N('image', size, path=path)


def place(n, x, y, w, h):
    n.rect = (x, y, w, h)
    if n.kind not in ('vert', 'horz'):
        return
    t, r, b, l = n.kw.get('pad') or (0, 0, 0, 0)
    ix, iy, iw, ih = x + l, y + t, w - l - r, h - t - b
    total = ih if n.kind == 'vert' else iw
    fixed = sum(k.size for k in n.kids if k.size is not None)
    flex = [k for k in n.kids if k.size is None]
    left = total - fixed
    assert left >= 0, (n.kw.get('fname'), total, fixed)
    share = {id(k): left // len(flex) + (1 if i < left % len(flex) else 0) for i, k in enumerate(flex)} if flex else {}
    pos = iy if n.kind == 'vert' else ix
    for k in n.kids:
        s = k.size if k.size is not None else share[id(k)]
        if n.kind == 'vert':
            place(k, ix, pos, iw, s)
        else:
            place(k, pos, iy, s, ih)
        pos += s


def emit(n, hide, in_flow):
    x, y, w, h = n.rect
    i = nid()
    HIDE[str(i)] = hide
    fx = f" fixed-size='{n.size}' is-fixed='true'" if in_flow and n.size is not None else ''
    kw = n.kw
    st = style(kw.get('bg'), kw.get('border'), kw.get('radius'), kw.get('pad'))
    if n.kind in ('vert', 'horz'):
        kids = '\n'.join(emit(k, hide, True) for k in n.kids)
        fn = f" friendly-name='{xesc(kw['fname'])}'" if kw.get('fname') else ''
        return (f"<zone{fn} {z(x, y, w, h)}{fx} id='{i}' param='{n.kind}' type-v2='layout-flow'>\n" + indent(kids, 2) + '\n'
                + indent(st, 2) + "\n</zone>")
    if n.kind == 'sheet':
        return f"<zone {z(x, y, w, h)}{fx} id='{i}' name='{xesc(kw['name'])}' show-title='false'>\n" + indent(st, 2) + "\n</zone>"
    if n.kind == 'empty':
        return f"<zone {z(x, y, w, h)}{fx} id='{i}' type-v2='empty'>\n" + indent(st, 2) + "\n</zone>"
    if n.kind == 'image':
        return f"<zone {z(x, y, w, h)}{fx} id='{i}' is-centered='0' is-scaled='1' param='{xesc(kw['path'])}' type-v2='bitmap' />"
    rr = []
    al = kw.get('align')
    for t, c, sz, f in kw['runs']:
        if t == '\n':
            rr.append("    <run>Æ&#10;</run>")
        else:
            a_ = f" fontalignment='{ {'left': 0, 'center': 1, 'right': 2}[al] }'" if al else ''
            rr.append(f"    <run{a_} fontcolor='{c}' fontname='Tableau {f}' fontsize='{sz}'>{xesc(t)}</run>")
    return f"<zone {z(x, y, w, h)}{fx} id='{i}' type-v2='text'>\n  <formatted-text>\n" + '\n'.join(rr) + "\n  </formatted-text>\n" + indent(st, 2) + "\n</zone>"


def opens_hidden(show):
    return not show.startswith('Show Light') or any(k in show for k in ('Wide', 'Pick', 'Cal', 'Rules'))


class Page:
    def __init__(self, show):
        self.zones, self.show = [], show

    def root(self, node, x, y, w, h, show=None):
        """one floating container (or item); its visibility calc drives everything inside it"""
        show = show or self.show
        place(node, x, y, w, h)
        start = zid[0] + 1
        self.zones.append(emit(node, opens_hidden(show), False))
        VIS[str(start)] = show


X0 = 240 + sum(KW[:3]) + 3 * 12                                  # the Team pulse card lines up with the fourth KPI card
PW = 240 + 1136 - X0
CY, CH = 160, 662


def layout(th, S):
    P = PAL[th]
    T = 'Light' if th == 'l' else 'Dark'
    pg = Page(f'Show {T}')
    ink, mu, ac = P['ink'], P['muted'], P['accent']
    lab = lambda t: Tx([(t, mu, 7.5, 'Semibold')], 18)
    if th == 'd':
        pg.root(Gap(bg=P['bg']), 0, 0, W, H)                         # the dark page covers the light dashboard background
    # ---- the five KPI cards: the card picture, and the KPI map sheet on top of it; both go before the rail, which
    # covers the map sheet's empty left edge (the sheet starts KOX px left of the cards)
    pg.root(Img(IMG + f'd7_kpi_cards_{th}.png'), 240, 72, KPI_W, KPI_H)
    pg.root(Sh(S['KPI Map']), 240 - KOX, 72, KPI_SW, KPI_H)
    # ---- the rail
    rail = V([
        Hz([Img(BRAND + P['logo'], 150), Gap()], 41),
        Gap(15), Gap(1, P['line']), Gap(10),
        Tx([('Who Leads Where', ink, 15, 'Bold'), ('\n', 0, 0, 0), ('Leadership scope & org design', mu, 9, 'Book')], 46),
        Gap(18), lab('ORGANIZATION'), Sh(S['Org Sub'], 16), Gap(4),
        V([Sh(S['Org Field'])], 182, bg=P['surface'], border=P['line'], radius=10, pad=(8, 8, 8, 8)),
        Gap(24), lab('WORKFORCE'), Gap(2), Hz([Sh(S['Worker Toggle'])], 30, bg=P['chip'], radius=15, pad=(1, 2, 1, 2)),
        Gap(22), lab('TREE COUNTS'), Gap(2), Hz([Sh(S['Count Toggle'])], 30, bg=P['chip'], radius=15, pad=(1, 2, 1, 2)),
        Gap(22), Tx([('CALENDAR', mu, 7.5, 'Semibold'), ('\n', 0, 0, 0), ('Click the card to pick a day', mu, 7.5, 'Book')], 30), Gap(4),
        V([Sh(S['Cal Field'])], 50, bg=P['surface'], border=P['line'], radius=10, pad=(5, 8, 3, 8)),
        Gap(),
        Gap(1, P['line']), Gap(8),
        Tx([('Built by ', mu, 8.5, 'Book'), ('Thiago Alpoin', ink, 8.5, 'Semibold')], 18), Gap(4),
        Hz([Sh(S['Credit GitHub'], 30), Gap(6), Sh(S['Credit LinkedIn'], 30), Gap()], 30),
    ], fname=f'Rail {T}', bg=P['rail'], pad=(20, 14, 26, 14))
    pg.root(rail, 0, 0, 216, H)
    pg.root(Gap(bg=P['line']), 216, 0, 1, H)
    # ---- the headline on one line, the theme toggle at its right end; the five KPI cards
    pg.root(Hz([Sh(S['Headline']), V([Sh(S['Theme Toggle'], 26), Gap()], 136)], fname=f'Header {T}'), 240, 6, 1136, 58)
    # ---- the tree card, narrow (beside the Team pulse) and wide
    for show, wcard in ((f'Show {T} Narrow', X0 - 12 - 240), (f'Show {T} Wide', 1136)):
        wide = 'Wide' in show
        w_ = ' Wide' if wide else ''
        card = V([
            Hz([Tx([('The organization', ink, 11.5, 'Semibold')]), Sh(S['Tree Toggle' + w_], 152), Gap(10), Sh(S['Expand' + w_], 30)], 30, pad=(0, 8, 0, 8)),
            Gap(2),
            Hz([Sh(S['Tree Hint' + w_])], 22, pad=(0, 8, 0, 8)),
            Sh(S['Tree' + w_]),
        ], fname=f'Card Tree{w_} {T}', bg=P['surface'], border=P['line'], radius=14, pad=(8, 8, 8, 8))
        pg.root(card, 240, CY, wcard, CH, show=show)
    # ---- the Team pulse card: the coverage hero, then six tiles in two columns
    tiles = Gap(TILES_H)          # room for the six tiles: their picture and the Tiles map sheet float here at full size
    hero = V([
        Hz([Tx([('TEAM COVERAGE · TODAY', mu, 7.5, 'Semibold')], pad=(3, 0, 0, 0)), V([Sh(S['Pulse State'])], 150, bg=P['soft'], radius=11, pad=(1, 2, 1, 2))], 22),
        Sh(S['Pulse Hero'], 44),
        Sh(S['Pulse Week'], 92),
        Sh(S['Pulse Days'], 34),
        Gap(12),
        Sh(S['Pulse Insight']),
    ], 272, bg=P['bg'], radius=12, pad=(8, 12, 4, 12))
    pulse = V([
        Hz([Tx([('Team pulse', ink, 11.5, 'Semibold')], pad=(2, 0, 0, 4)), Sh(S['Info'], 26)], 26),
        Sh(S['Pulse Sub'], 20), Gap(6),
        hero, Gap(10),
        tiles, Gap(),
    ], fname=f'Card Team pulse {T}', bg=P['surface'], border=P['line'], radius=14, pad=(10, 12, 12, 12))
    pg.root(pulse, X0, CY, PW, CH, show=f'Show {T} Narrow')
    tx, ty, tw_, th_ = tiles.rect
    pg.root(Img(IMG + f'd7_pulse_tiles_{th}.png'), tx, ty, TILES_W, TILES_H, show=f'Show {T} Narrow')
    pg.root(Sh(S['Tiles Map']), tx - TOX, ty, TILES_SW, TILES_H, show=f'Show {T} Narrow')
    # ---- the footnote
    pg.root(Sh(S['Footnote']), 240, CY + CH + 4, 1136, 18)
    # ---- popovers
    pick = V([
        Hz([Tx([("Open any leader's organization", ink, 12, 'Semibold')]), Sh(S['Pick Close'], 28)], 28),
        Tx([('Click a name to open it and see the leaders below; the tree, KPIs and panel follow your pick. ', mu, 8.5, 'Book'),
            ('The number beside each name is everyone they lead, directly and indirectly.', mu, 8.5, 'Book')], 22),
        Gap(8),
        Hz([Tx([('CEO AND EXECUTIVES', mu, 7.5, 'Semibold')], 160)] + [Sh(S[f'Pick Head L{k}'], 160 if k < 6 else None) for k in range(1, 7)], 18),
        Hz([Sh(S[f'Pick L{k}'], 160 if k < 6 else None) for k in range(7)], 460),
        Tx([('On Tableau Cloud a leader sees only their own branch (row-level security on their work email); '
             'People Analytics sees every branch.', mu, 8, 'Book')], pad=(8, 0, 0, 0)),
    ], fname=f'Popover Pick {T}', bg=P['pop'], border=P['line'], radius=16, pad=(10, 12, 8, 14))
    pg.root(pick, 224, 96, 1156, 590, show=f'Show {T} Pick')
    cal = V([
        Hz([Sh(S['Cal Title']), V([Sh(S['Cal Close'], 28), Gap()], 28)], 44),
        Hz([Tx([(d, mu, 8, 'Book')], 73, align='center') for d in ('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat')]
           + [Tx([('Sun', mu, 8, 'Book')], align='center')], 18),
        Sh(S['Calendar'], 330),
        Sh(S['Cal Summary'], pad=(8, 6, 0, 6)),
    ], fname=f'Popover Calendar {T}', bg=P['pop'], border=P['line'], radius=16, pad=(10, 14, 8, 14))
    pg.root(cal, 224, 300, 540, 500, show=f'Show {T} Cal')
    cols = (130, 230, 430, None)
    heads = ('LINE', 'SIGNAL', 'WHEN IT SHOWS', 'GOOD PARTNER TO ASK')
    rows = [(s[2], s[1], s[3], s[4]) for s in SIGNALS] + [('Geography', 'Leads people in other regions',
                                                          'Context only (countries led): expected for executives, L1 and L2, never flagged.', '–')]
    body = [Hz([Tx([(h_, mu, 7.5, 'Semibold')], w0) for w0, h_ in zip(cols, heads)], 18), Gap(1, P['line']), Gap(5)]
    for r in rows:
        body += [Hz([Tx([(t, c, 9, f)], w0, pad=(0, 10, 0, 0)) for w0, t, (c, f) in
                     zip(cols, r, ((mu, 'Book'), (ink, 'Semibold'), (ink, 'Book'), (mu, 'Book')))], 48), Gap(1, P['line']), Gap(5)]
    rules = V([
        Hz([Tx([('Org design alignment', ink, 13, 'Semibold')]), Sh(S['Rules Close'], 28)], 28),
        Tx([("A leader's org design is the org units they lead and the job families their function hires; the matrix line "
             'follows where people sit. Each signal marks where a record departs from that design. Many have a good '
             'business reason; the flag simply makes them visible.', mu, 9, 'Book')], 48),
        Gap(8),
        *body,
        Tx([('Spans and layers (15 or more directs, one direct) appear in the KPIs as information. Executive officers are leaders here '
             'but stay out of every count. Matrix signals apply to people Keystone holds; a contingent worker Keystone does not know '
             "is case study 4's reconciliation gap.", mu, 8.5, 'Book')], pad=(4, 0, 0, 0)),
    ], fname=f'Popover Alignment {T}', bg=P['pop'], border=P['line'], radius=16, pad=(12, 14, 8, 22))
    pg.root(rules, 300, 64, 1000, 600, show=f'Show {T} Rules')
    return pg.zones


zones = layout('l', L) + layout('d', D)
DASH_UID = uid()
dash = (f"  <dashboards>\n    <dashboard enable-sort-zone-taborder='true' name='{DASH}'>\n"
        f"      <style>\n        <style-rule element='table'>\n          <format attr='background-color' value='{PAL['l']['bg']}' />\n        </style-rule>\n      </style>\n"
        f"      <size maxheight='{H}' maxwidth='{W}' minheight='{H}' minwidth='{W}' sizing-mode='fixed' />\n      <zones>\n"
        + indent('\n'.join(zones), 8) + f"\n      </zones>\n      <simple-id uuid='{DASH_UID}' />\n    </dashboard>\n  </dashboards>\n")
dash = re.sub(r"<zone (?=[^>]*id='(\d+)')", lambda mm: "<zone hidden-by-user='true' " if HIDE[mm.group(1)] else "<zone ", dash)

# ===================================================================================================== actions
acts = []
for name, sh in SHEETS.items():
    if not sh.deselect:
        continue
    cap = 'Deselect ' + name
    expr = f"tsl:{name.replace(' ', '%20').replace('(', '%28').replace(')', '%29')}?%5B{DS}%5D.%5B{m.cid['zzFalse']}%5D~s0=&lt;[{DS}].[{m.cid['zzTrue']}]~na&gt;"
    acts.append(f"<action caption='{xesc(cap)}' name='{action_id(cap)}'>\n  <activation auto-clear='true' type='on-select' />\n"
                f"  <source dashboard='{DASH}' type='sheet' worksheet='{xesc(name)}' />\n"
                f"  <link caption='{xesc(cap)}' delimiter=',' escape='\\' expression='{expr}' include-null='true' multi-select='true' url-escape='true' />\n"
                f"  <command command='tsc:tsl-filter'>\n    <param name='target' value='{xesc(name)}' />\n  </command>\n</action>")
T = []
for S in (L, D):
    sfx = '' if S is L else ' (dark)'
    T += [(f'Worker{sfx}', S['Worker Toggle'], 'p_Worker', 'worker_type'),
          (f'Count{sfx}', S['Count Toggle'], 'p_Count', 'Count Option'),
          (f'Theme{sfx}', S['Theme Toggle'], 'p_Dark', 'Theme Is Dark')]
    for p in ('p_PickOpen', 'p_CalOpen', 'p_RulesOpen'):
        T.append((f'Theme closes {p}{sfx}', S['Theme Toggle'], p, 'Close Panel'))
    for nm in ('Tree Toggle', 'Tree Toggle Wide'):
        T.append((f'{nm}{sfx}', S[nm], 'p_Tree', 'Seg Mode'))
    for nm in ('Expand', 'Expand Wide'):
        T.append((f'{nm}{sfx}', S[nm], 'p_Zoom', 'Toggle Zoom'))
    T += [(f'Open picker{sfx}', S['Org Field'], 'p_PickOpen', 'Toggle Pick'),
          (f'Picker closes cal{sfx}', S['Org Field'], 'p_CalOpen', 'Close Panel'),
          (f'Picker closes rules{sfx}', S['Org Field'], 'p_RulesOpen', 'Close Panel'),
          (f'Open calendar{sfx}', S['Cal Field'], 'p_CalOpen', 'Toggle Cal'),
          (f'Calendar closes picker{sfx}', S['Cal Field'], 'p_PickOpen', 'Close Panel'),
          (f'Calendar closes rules{sfx}', S['Cal Field'], 'p_RulesOpen', 'Close Panel'),
          (f'Open rules{sfx}', S['Info'], 'p_RulesOpen', 'Toggle Rules'),
          (f'Rules closes picker{sfx}', S['Info'], 'p_PickOpen', 'Close Panel'),
          (f'Rules closes calendar{sfx}', S['Info'], 'p_CalOpen', 'Close Panel'),
          (f'Close picker{sfx}', S['Pick Close'], 'p_PickOpen', 'Close Panel'),
          (f'Close calendar{sfx}', S['Cal Close'], 'p_CalOpen', 'Close Panel'),
          (f'Close rules{sfx}', S['Rules Close'], 'p_RulesOpen', 'Close Panel'),
          (f'Pick day{sfx}', S['Calendar'], 'p_Day', 'day_offset'),
          (f'Pick day closes{sfx}', S['Calendar'], 'p_CalOpen', 'Close Panel')]
    for k in range(7):
        T += [(f'Pick L{k} path{sfx}', S[f'Pick L{k}'], 'p_Path', 'path'),
              (f'Pick L{k} open{sfx}', S[f'Pick L{k}'], 'p_PickOpen', 'Pick Keep Open')]
    for nm in ('Tree', 'Tree Wide'):
        T += [(f'{nm} path{sfx}', S[nm], 'p_Path', 'Path Target'),
              (f'{nm} mode{sfx}', S[nm], 'p_Tree', 'Dynamic Text')]
    for cap, sheet, url in (('GitHub', S['Credit GitHub'], 'https://github.com/thialp'),
                            ('LinkedIn', S['Credit LinkedIn'], 'https://www.linkedin.com/in/thiagoalpoin')):
        acts.append(f"<action caption='Open {cap}{sfx}' name='{action_id('Open ' + cap + sfx)}'>\n  <activation type='on-select' />\n"
                    f"  <source dashboard='{DASH}' type='sheet' worksheet='{xesc(sheet)}' />\n"
                    f"  <link caption='Open {cap}' expression='{url}' include-null='true' url-escape='true' />\n</action>")
PA = []
for cap, sheet, target, field in T:
    PA.append(f"<edit-parameter-action caption='{xesc(cap)}' name='{action_id(cap)}'>\n  <activation type='on-select' />\n"
              f"  <source dashboard='{DASH}' type='sheet' worksheet='{xesc(sheet)}' />\n  <agg-type type='attr' />\n"
              f"  <clear-option type='do-nothing' value='b:false' />\n  <params>\n"
              f"    <param name='source-field' value='{m.ref(field, how(field))}' />\n"
              f"    <param name='target-parameter' value='[Parameters].[{m.pid[target]}]' />\n  </params>\n</edit-parameter-action>")
acts += PA
out = out.replace("  <worksheets>\n", "  <actions>\n" + indent('\n'.join(acts), 4) + "\n  </actions>\n  <worksheets>\n", 1)
for sh in SHEETS.values():
    for i, pn in enumerate(sh.panes):
        for r in re.findall(r"<tooltip column='([^']+)' />", pn):
            if r in sh.rows or r in sh.cols:
                pn = pn.replace(f"<tooltip column='{r}' />", '')
        sh.panes[i] = re.sub(r'\n\s*\n', '\n', pn)
out = re.sub(r"  <worksheets>\n.*?  </worksheets>\n", lambda _: "  <worksheets>\n" + indent('\n'.join(s.xml() for s in SHEETS.values()), 4)
             + "\n  </worksheets>\n", out, count=1, flags=re.S)
out = out.replace("  <windows source-height='30'>\n", dash + "  <windows source-height='30'>\n", 1)


def ws_window(name):
    return (f"<window class='worksheet' name='{xesc(name)}'>\n  <cards>\n    <edge name='left'>\n      <strip size='160'>\n"
            "        <card type='pages' />\n        <card type='filters' />\n        <card type='marks' />\n      </strip>\n    </edge>\n"
            "    <edge name='top'>\n      <strip size='2147483647'>\n        <card type='columns' />\n      </strip>\n"
            "      <strip size='2147483647'>\n        <card type='rows' />\n      </strip>\n      <strip size='31'>\n        <card type='title' />\n"
            "      </strip>\n    </edge>\n  </cards>\n  <viewpoint>\n    <zoom type='entire-view' />\n  </viewpoint>\n"
            f"  <simple-id uuid='{uid()}' />\n</window>")


names = list(SHEETS)
LISTS = [n for n in names if n.startswith(('Pick L', 'Align Solid', 'Align Matrix', 'Align Role', 'Org Field'))]
vps = '\n'.join(f"    <viewpoint name='{xesc(n)}'>\n      <zoom type='{'fit-width' if n in LISTS else 'entire-view'}' />\n    </viewpoint>" for n in sorted(names))
dwin = (f"<window class='dashboard' maximized='true' name='{DASH}'>\n  <viewpoints>\n{vps}\n  </viewpoints>\n"
        f"  <active id='-1' />\n  <simple-id uuid='{uid()}' />\n</window>")
out = re.sub(r"    <window class='worksheet' maximized='true' name='Sheet 1'>.*?</window>\n", '', out, flags=re.S)
out = out.replace("  </windows>\n", indent('\n'.join(ws_window(n) for n in names) + '\n' + dwin, 4) + "\n  </windows>\n", 1)

nodes, pairs, edges = [], [], []
fieldnode = {}
for zid_, calc in VIS.items():
    if calc not in fieldnode:
        pn, pin, pout = (str(uuid.uuid4()) for _ in range(3))
        nodes.append(f"<single-value-field-node fieldname='[{DS}].[{m.cid[calc]}]' fieldname-input-guid='{pin}' node-guid='{pn}' value-output-guid='{pout}' />")
        pairs.append(pn)
        fieldnode[calc] = pout
    zn, zin = str(uuid.uuid4()), str(uuid.uuid4())
    nodes.append(f"<dashboard-zone-visibility-node dashboard-identifier='{DASH_UID}' node-guid='{zn}' visibility-input-guid='{zin}' zone-id='{zid_}' />")
    pairs.append(zn)
    edges.append(f"<edge from='{fieldnode[calc]}' to='{zin}' />")
sub = str(uuid.uuid4())
graph = ("  <datagraph>\n    <graph>\n      <properties>\n        <default-execution-subgraph-guid value='" + sub + "' />\n      </properties>\n"
         "      <node-execution-subgraphs>\n" + ''.join(f"        <pair execution-subgraph-guid='{sub}' node-guid='{g}' />\n" for g in pairs)
         + "      </node-execution-subgraphs>\n      <nodes>\n" + ''.join(f"        {n}\n" for n in nodes) + "      </nodes>\n      <edges>\n"
         + ''.join(f"        {e}\n" for e in edges) + "      </edges>\n    </graph>\n  </datagraph>\n")
out = out.replace("  </windows>\n", "  </windows>\n" + graph, 1)
out = re.sub(r"fontsize='(\d+)\.5'", lambda mm: f"fontsize='{int(mm.group(1)) + 1}'", out)   # Tableau takes whole points only
open(OUT, 'w', encoding='utf-8').write(out)
print('calcs', len(m.order), 'sheets', len(SHEETS), 'zones', len(zones), 'actions', len(acts), f'({len(PA)} parameter)')
