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
BRAND = os.environ.get('D7_BRAND', '/Users/thiagoalpoin/Documents/Claude/Professional Portfolio/tableau/Shared/Brand/')   # the Arcadia logos

PAL = {
    'l': dict(bg='#F4F7F6', rail='#FFFFFF', surface='#FFFFFF', pop='#FFFFFF', line='#DFE6E3', ink='#15201D', muted='#56635F',
              accent='#1F7560', soft='#E1F2EB', gap='#A3611A', chip='#EDF2F0', node='#D3E3DD', open='#A9D3C3', focus='#7DBCA5',
              link='#C7D3CF', linksel='#1F7560', callow='#EEF6F2', calhigh='#9ACFBC', calsel='#F6DFC0', calwe='#F4F7F6',
              logo='arcadia_logo_horizontal.png', name=''),
    'd': dict(bg='#141A19', rail='#0F1413', surface='#1A2120', pop='#1E2725', line='#2A3532', ink='#E9EFEC', muted='#9AA9A4',
              accent='#7FD1B9', soft='#1E3A33', gap='#E3B65C', chip='#202A28', node='#2C3D39', open='#36665A', focus='#4E9C86',
              link='#33413D', linksel='#7FD1B9', callow='#1D2A27', calhigh='#2F6A5B', calsel='#5A4826', calwe='#161D1C',
              logo='arcadia_logo_horizontal_reverse.png', name=' (dark)'),
}

# ===================================================================================================== model
meta = re.search(r'<extract .*?<metadata-records>(.*?)</metadata-records>', src, re.S).group(1)
RAW = {}
for r in re.findall(r"<metadata-record class='column'>(.*?)</metadata-record>", meta, re.S):
    RAW[re.search(r'<remote-name>(.*?)</remote-name>', r).group(1)] = re.search(r'<local-type>(.*?)</local-type>', r).group(1)
DS = re.search(r"<datasource caption='[^']*' inline='true' name='(federated\.[a-z0-9]+)'", src).group(1)

PARAMS = {
    'p_Focus': {'dtype': 'string', 'value': 'W100010'},          # Isaac Holland, L1, Software Engineering
    'p_Open': {'dtype': 'string', 'value': ''},
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
        [('{Head Leads}', 'semi', 18, ink), ('{Head People}', 'semi', 18, ac), ('{Head In}', 'semi', 18, ink),
         ('{Head Gaps}', 'semi', 18, gp), ('{Head Tail}', 'semi', 18, ink)]],
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
    for i, (lab, v, note, col, tp) in enumerate(KPI, 1):
        text_sheet(f'KPI {i}', [[(lab, 'semi', 7.5, mu)], [('{' + v + '}', 'semi', 18, col)], [('{' + note + '}', 'book', 8, mu)]], tooltip=tp)

    # ---------------------------------------------------------------- rail
    s = sh('Org Field')
    s.pane('Text', enc=ZZ + [('lod', n, how(n)) for n in ('Toggle Pick', 'Pick B0 Default', 'Pick B1 Default', 'Close Panel')],
           valign='top', label=[[('L0   ', 'semi', 8.5, mu), ('{Org L0 Text}', 'book', 9, ink)],
                                [('L1   ', 'semi', 8.5, ac), ('{Org L1 Text}', 'bold', 9.5, ink)],
                                [('L2   ', 'semi', 8.5, mu), ('{Org L2 Text}', 'book', 9, ink)],
                                [('{Org Below Text}', 'semi', 9, ac)]],
           tooltip=[[('Open any leader\'s organization (L0, L1 or L2)', 'semi', 9, ink)]])

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
              'Everyone in the organization, or only those at work on the chosen day')
    seg_sheet('Tree Toggle', 'Seg Row', 'Seg Key', 'Tree Shape', ['Seg Mode'], SIZE['segs'],
              'Dynamic: one level at a time · Static: three levels at once')
    seg_sheet('Tree Toggle Wide', 'Seg Row', 'Seg Key', 'Tree Shape', ['Seg Mode'], SIZE['segs'],
              'Dynamic: one level at a time · Static: three levels at once')
    seg_sheet('Theme Toggle', 'Seg Row', 'Seg Key', 'Theme Shape', ['Theme Is Dark', 'Close Panel'], SIZE['segs'], 'Light or dark page')

    s = sh('Cal Field')
    s.pane('Text', enc=ZZ + [('lod', n, how(n)) for n in ('Toggle Cal', 'Close Panel')], valign='top',
           label=[[('{Day Lead}', 'bold', 9.5, ink)], [('{Cal Field Value}', 'semi', 9, ac)], [('{Cal Field Note}', 'book', 8, mu)]],
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
    text_sheet('Rail As Of', [[('{Rail As Of}', 'book', 8, mu)], [('Executive officers lead but are not counted', 'book', 8, mu)]])

    # ---------------------------------------------------------------- the tree
    text_sheet('Tree Hint', [[('{Tree Hint}', 'book', 8.5, mu)]])
    text_sheet('Tree Hint Wide', [[('{Tree Hint}', 'book', 8.5, mu)]])
    TIP = [[('{leader_name|attr}', 'bold', 10, ink), ('  {leader_level|attr}', 'semi', 9, ac)],
           [('{job_title|attr}', 'book', 9, mu)],
           [('{Tip People|attr}', 'book', 9, ink)],
           [('{Tip Gaps|attr}', 'semi', 9, gp)],
           [('{Tip At Work|attr}', 'book', 9, ink)],
           [('{Tip Action|attr}', 'semi', 9, ac)]]
    ACT = ['Focus Target', 'Open Target', 'Dynamic Text']
    for name in ('Tree', 'Tree Wide'):
        s = sh(name, deselect=True)
        s.filter_member('In Tree View', 'true')
        x = s.f('x', 'min')
        yl, yn = s.f('Y Link', 'min'), s.f('Y Node', 'min')
        s.cols, s.rows = x, f'({yl} + {yn})'
        s.axis_rules += [f"<encoding attr='space' class='0' field='{x}' field-type='quantitative' max='1.04' min='-0.04' range-type='fixed' scope='cols' type='space' />",
                         f"<format attr='display' class='0' field='{x}' scope='cols' value='false' />",
                         f"<encoding attr='space' class='0' field='{yl}' field-type='quantitative' max='0.42' min='-3.42' range-type='fixed' scope='rows' type='space' />",
                         f"<format attr='display' class='0' field='{yl}' scope='rows' value='false' />",
                         f"<encoding attr='space' class='0' field='{yn}' field-type='quantitative' fold='true' max='0.42' min='-3.42' range-type='fixed' scope='rows' synchronized='true' type='space' />",
                         f"<format attr='display' class='0' field='{yn}' scope='rows' value='false' />",
                         "<format attr='tick-color' value='#00000000' />"]
        s.pane('Automatic', pane_id=2, enc=[])
        s.pane('Line', pane_id=3, y_axis=yl, size='0.6', transparency='255',
               enc=ZZ + [('path', 'point_index', 'ord'), ('lod', 'node_id', 'dim'), ('lod', 'mark_type', 'dim'), ('color', 'Link Kind', 'dim')]
               + [('lod', n, 'dim') for n in ACT], tooltip=TIP)
        s.pane('Pie', pane_id=4, y_axis=yn, size=SIZE['pie'], transparency='255', stroke='false', align='center', valign='bottom',
               enc=ZZ + [('lod', 'Wedge Order', 'ord'), ('lod', 'node_id', 'dim'), ('color', 'Pie Color', 'dim'), ('size', 'Pie Size', 'min'), ('wedge-size', 'Pie Angle', 'sum')]
               + [('lod', n, 'dim') for n in ACT],
               label=[[('{Node Label Name}', 'semi', 8.5, ink)], [('{Node Label Count}', 'book', 8, mu)]], tooltip=TIP,
               extra_mark_fmt="<format attr='mark-labels-mode' value='all' />")

    # ---------------------------------------------------------------- the alignment panel
    for key, flt, total in (('Solid', 'Is Solid', 'Solid Total'), ('Matrix', 'Is Matrix', 'Matrix Total'), ('Role', 'Is Role', 'Role Total')):
        line = {'Solid': 'SOLID LINE', 'Matrix': 'MATRIX LINE', 'Role': 'ROLE ASSIGNMENTS'}[key]
        text_sheet(f'Align Head {key}', [[(line, 'semi', 7.5, mu), ('   ·   ', 'book', 7.5, mu), ('{' + total + '}', 'semi', 7.5, ink)]])
        s = sh(f'Align {key}')
        s.filter_member('Sig Scaffold', 'true')
        s.filter_member(flt, 'true')
        o = s.f('Sig Order', 'ord')
        s.rows = o
        s.hide_labels.append(o)
        no_field_labels(s, 'rows')
        s.cell_size = (None, 46, o)
        s.pane('Text', enc=ZZ + [('lod', 'signal_code', 'dim')], valign='center', align='left',
               label=[[('{Sig Count Txt}', 'bold', 9.5, ink), ('   {signal_name}', 'book', 9.5, ink)],
                      [('{Sig Bar}', 'book', 7, gp), ('{Sig Track}', 'book', 7, P['chip'])]],
               tooltip=[[('{signal_name}', 'bold', 10, ink), ('  ·  {Sig Count Txt} {Worker Words}', 'book', 10, gp)],
                        [('{Sig Rule}', 'book', 9, ink)], [('Good partner to ask: ', 'book', 9, mu), ('{Sig Partner}', 'semi', 9, ink)]])

    # ---------------------------------------------------------------- the leader picker
    for col, flt in (('Pick L0', 'Pick Row L0'), ('Pick L1', 'Pick Row L1'), ('Pick L2', 'Pick Row L2')):
        s = sh(col)
        s.filter_member(flt, 'true')
        rk, li = s.f('Pick Rank', 'ord'), s.f('leader_id', 'dim')
        s.rows = f'({rk} / {li})'
        s.hide_labels += [rk, li]
        no_field_labels(s, 'rows')
        s.cell_size = (None, 30, li)
        tx = s.f('Tick X', 'agg')
        s.cols = tx
        hide_axis(s, tx, 0, 10)
        acts = {'Pick L0': ['leader_id', 'Empty Text'], 'Pick L1': ['leader_id', 'Empty Text'], 'Pick L2': ['leader_id', 'Empty Text', 'Close Panel']}[col]
        s.pane('Shape', enc=ZZ + [('shape', 'Pick Shape', 'dim')] + [('lod', n, how(n)) for n in acts], size=SIZE['dot'],
               transparency='255', stroke='false', align='right',
               label=[[('{leader_name}', 'semi', 9.5, ink), ('   {Pick People}', 'book', 8.5, mu)]],
               tooltip=[[('{leader_name}', 'bold', 10, ink), ('  {leader_level}', 'semi', 9, ac)], [('{Pick Sub}', 'book', 9, mu)],
                        [('Click to open their organization' + ('' if col == 'Pick L2' else ' and see the leaders below'), 'semi', 9, ac)]],
               extra_mark_fmt="<format attr='mark-labels-mode' value='all' />")
    text_sheet('Pick Head L1', [[('{Pick Head L1}', 'semi', 7.5, mu)]])
    text_sheet('Pick Head L2', [[('{Pick Head L2}', 'semi', 7.5, mu)]])

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
CTX = {'KPI 2': 'Ctx Days', 'Cal Field': 'Ctx Days', 'Calendar': 'Ctx Days', 'Cal Summary': 'Ctx Days',
       'Tree': 'Ctx Tree', 'Tree Wide': 'Ctx Tree'}
for name, sh_ in SHEETS.items():
    sh_.filter_member(CTX.get(name.replace(' (dark)', ''), 'Ctx Leaders'), 'true')
    sh_.filters.insert(0, sh_.filters.pop().replace("'>\n", "' context='true'>\n", 1))

# ===================================================================================================== datasource styles
def bucket_map(field, kind, mapping):
    ms = '\n'.join(f"  <map to='{to}'>\n    <bucket>&quot;{xesc(b)}&quot;</bucket>\n  </map>" for b, to in mapping)
    return f"<encoding attr='{kind}' field='{field}' type='{'palette' if kind == 'color' else 'shape'}'>\n{ms}\n</encoding>"


enc_rules, styled = [], []
for n, keys in (('Pie Color', ('gap', 'focus', 'open', 'node', 'none')), ('Link Kind', ('sel', 'link')), ('Cal Kind', ('we', 'sel', 'high', 'low'))):
    colours = {'none': 'surface', 'gap': 'gap', 'focus': 'focus', 'open': 'open', 'node': 'node', 'sel': 'linksel', 'link': 'link',
               'we': 'calwe', 'high': 'calhigh', 'low': 'callow'}
    mp = []
    for th in ('l', 'd'):
        for k in keys:
            c = PAL[th]['calsel'] if (n == 'Cal Kind' and k == 'sel') else PAL[th][colours[k]]
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


class Page:
    def __init__(self, show):
        self.zones, self.show = [], show

    def add(self, xml, show=None):
        i = re.search(r" id='(\d+)'", xml).group(1)
        VIS[i] = show or self.show
        self.zones.append(xml)

    def sheet(self, name, px, py, pw, ph, show=None):
        self.add(f"<zone {z(px, py, pw, ph)} id='{nid()}' name='{xesc(name)}' show-title='false'>\n" + indent(style(), 2) + "\n</zone>", show)

    def box(self, px, py, pw, ph, bg, border=None, radius=None, show=None):
        self.add(f"<zone {z(px, py, pw, ph)} id='{nid()}' type-v2='empty'>\n" + indent(style(bg, border, radius), 2) + "\n</zone>", show)

    def text(self, px, py, pw, ph, runs, show=None, pad=(0, 0, 0, 0), align=None):
        rr = []
        for t, c, sz, f in runs:
            if t == '\n':
                rr.append("    <run>Æ&#10;</run>")
            else:
                al = f" fontalignment='{ {'left': 0, 'center': 1, 'right': 2}[align] }'" if align else ''
                rr.append(f"    <run{al} fontcolor='{c}' fontname='Tableau {f}' fontsize='{sz}'>{xesc(t)}</run>")
        self.add(f"<zone {z(px, py, pw, ph)} id='{nid()}' type-v2='text'>\n  <formatted-text>\n" + '\n'.join(rr)
                 + "\n  </formatted-text>\n" + indent(style(pad=pad), 2) + "\n</zone>", show)

    def image(self, path, px, py, pw, ph, show=None):
        self.add(f"<zone {z(px, py, pw, ph)} id='{nid()}' is-centered='0' is-scaled='1' param='{xesc(path)}' type-v2='bitmap' />", show)


def layout(th, S):
    P = PAL[th]
    T = 'Light' if th == 'l' else 'Dark'
    pg = Page(f'Show {T}')
    ink, mu, ac = P['ink'], P['muted'], P['accent']
    if th == 'd':
        pg.box(0, 0, W, H, P['bg'])                                     # the dark page covers the light dashboard background
    # rail
    pg.box(0, 0, 216, H, P['rail'])
    pg.box(216, 0, 1, H, P['line'])
    pg.image(BRAND + P['logo'], 16, 20, 150, 41)
    pg.box(14, 76, 188, 1, P['line'])
    pg.text(14, 86, 196, 48, [('Who Leads Where', ink, 15, 'Bold'), ('\n', 0, 0, 0), ('Leadership scope & org design', mu, 9, 'Book')])
    pg.box(14, 138, 188, 52, P['soft'], radius=9)
    pg.text(20, 142, 180, 46, [('People Analytics · full company', ac, 8, 'Semibold'), ('\n', 0, 0, 0),
                               ('Leaders see only their own branch', mu, 8, 'Book')])
    for lab, y in (('ORGANIZATION', 200), ('COUNT', 312), ('SHOW', 372), ('AT WORK ON', 432)):
        pg.text(14, y, 190, 16, [(lab, mu, 7.5, 'Semibold')])
    pg.box(14, 218, 188, 80, P['surface'], P['line'], 10)
    pg.sheet(S['Org Field'], 22, 223, 176, 72)
    pg.sheet(S['Worker Toggle'], 14, 330, 188, 30)
    pg.sheet(S['Count Toggle'], 14, 390, 188, 30)
    pg.box(14, 450, 188, 60, P['surface'], P['line'], 10)
    pg.sheet(S['Cal Field'], 22, 455, 176, 52)
    pg.sheet(S['Rail As Of'], 14, 716, 196, 34)
    pg.box(14, 758, 188, 1, P['line'])
    pg.text(14, 768, 196, 18, [('Built by ', mu, 8.5, 'Book'), ('Thiago Alpoin', ink, 8.5, 'Semibold')])
    pg.sheet(S['Credit GitHub'], 14, 790, 30, 30)
    pg.sheet(S['Credit LinkedIn'], 50, 790, 30, 30)
    # headline, theme, KPIs
    pg.sheet(S['Headline'], 240, 14, 990, 92)
    pg.sheet(S['Theme Toggle'], 1240, 20, 136, 28)
    pg.box(240, 116, 1136, 80, P['surface'], P['line'], 12)
    for k in range(5):
        if k:
            pg.box(240 + round(1136 * k / 5), 117, 1, 78, P['line'])
        pg.sheet(S[f'KPI {k + 1}'], 240 + round(1136 * k / 5) + 12, 122, round(1136 / 5) - 18, 70)
    # tree card, narrow and wide
    for show, wcard in ((f'Show {T} Narrow', 806), (f'Show {T} Wide', 1136)):
        wide = wcard == 1136
        pg.box(240, 210, wcard, 622, P['surface'], P['line'], 14, show=show)
        pg.text(256, 220, 220, 24, [('The organization', ink, 11.5, 'Semibold')], show=show)
        pg.sheet(S['Tree Toggle Wide' if wide else 'Tree Toggle'], 240 + wcard - 16 - 30 - 10 - 152, 218, 152, 28, show=show)
        pg.sheet(S['Expand Wide' if wide else 'Expand'], 240 + wcard - 16 - 30, 217, 30, 30, show=show)
        pg.sheet(S['Tree Hint Wide' if wide else 'Tree Hint'], 256, 248, wcard - 32, 20, show=show)
        pg.sheet(S['Tree Wide' if wide else 'Tree'], 248, 270, wcard - 16, 530, show=show)
        pg.text(256, 806, wcard - 32, 18, [('Circle size = people led  ·  ', mu, 8, 'Book'), ('amber slice', P['gap'], 8, 'Semibold'),
                                           (' = share with an alignment gap  ·  click a leader to show their team, again to open it', mu, 8, 'Book')],
                show=show)
    # alignment panel (narrow only)
    show = f'Show {T} Narrow'
    pg.box(1060, 210, 316, 622, P['surface'], P['line'], 14, show=show)
    pg.text(1076, 220, 250, 24, [('Org design alignment', ink, 11.5, 'Semibold')], show=show)
    pg.sheet(S['Info'], 1338, 219, 26, 26, show=show)
    pg.text(1076, 246, 290, 18, [('Where records differ from the org design', mu, 8.5, 'Book')], show=show)
    y = 274
    for key, n in (('Solid', 2), ('Matrix', 3), ('Role', 1)):
        pg.sheet(S[f'Align Head {key}'], 1076, y, 286, 18, show=show)
        pg.box(1076, y + 19, 286, 1, P['line'], show=show)
        pg.sheet(S[f'Align {key}'], 1072, y + 22, 292, 46 * n, show=show)
        y += 22 + 46 * n + 14
    pg.box(1072, 716, 292, 104, P['chip'], radius=10, show=show)
    pg.text(1082, 722, 274, 94, [('Leading people in other regions is expected at L0 to L2 and is never flagged. Signals are flags, not errors: '
                                  'many have a good business reason. Hover a signal for when it shows and who to ask.', mu, 8.5, 'Book')], show=show)
    # popovers
    show = f'Show {T} Pick'
    pg.box(224, 96, 780, 590, P['pop'], P['line'], 16, show=show)
    pg.text(244, 108, 560, 24, [("Open any leader's organization", ink, 12, 'Semibold')], show=show)
    pg.text(244, 132, 640, 18, [('Click a name to open it and see the leaders below; the tree, KPIs and panel follow your pick', mu, 8.5, 'Book')], show=show)
    pg.sheet(S['Pick Close'], 968, 104, 28, 28, show=show)
    pg.text(244, 160, 236, 18, [('L0 · EXECUTIVE LEADERSHIP', mu, 7.5, 'Semibold')], show=show)
    pg.sheet(S['Pick Head L1'], 494, 160, 236, 18, show=show)
    pg.sheet(S['Pick Head L2'], 744, 160, 250, 18, show=show)
    pg.sheet(S['Pick L0'], 238, 180, 244, 460, show=show)
    pg.sheet(S['Pick L1'], 488, 180, 244, 460, show=show)
    pg.sheet(S['Pick L2'], 738, 180, 256, 460, show=show)
    pg.text(244, 650, 740, 30, [('On Tableau Cloud a leader sees only their own branch (row-level security on their work email); '
                                 'People Analytics sees every branch.', mu, 8, 'Book')], show=show)
    show = f'Show {T} Cal'
    pg.box(224, 300, 540, 500, P['pop'], P['line'], 16, show=show)
    pg.sheet(S['Cal Title'], 244, 312, 470, 44, show=show)
    pg.sheet(S['Cal Close'], 728, 308, 28, 28, show=show)
    for i, d in enumerate(('Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun')):
        pg.text(238 + i * 73, 360, 73, 16, [(d, mu, 8, 'Book')], show=show, align='center')
    pg.sheet(S['Calendar'], 238, 378, 512, 330, show=show)
    pg.sheet(S['Cal Summary'], 244, 716, 506, 76, show=show)
    show = f'Show {T} Rules'
    pg.box(300, 64, 1000, 600, P['pop'], P['line'], 16, show=show)
    pg.text(322, 78, 800, 26, [('Org design alignment', ink, 13, 'Semibold')], show=show)
    pg.sheet(S['Rules Close'], 1262, 74, 28, 28, show=show)
    pg.text(322, 108, 950, 44, [("A leader's org design is the org units they lead and the job families their function hires; the matrix line "
                                 'follows where people sit. Each signal marks where a record departs from that design. Many have a good '
                                 'business reason; the flag simply makes them visible.', mu, 9, 'Book')], show=show)
    cols = ((322, 130, 'LINE'), (452, 230, 'SIGNAL'), (682, 430, 'WHEN IT SHOWS'), (1112, 170, 'GOOD PARTNER TO ASK'))
    for x0, w0, lab in cols:
        pg.text(x0, 160, w0, 18, [(lab, mu, 7.5, 'Semibold')], show=show)
    pg.box(322, 180, 960, 1, P['line'], show=show)
    rows = [(s[2], s[1], s[3], s[4]) for s in SIGNALS] + [('Geography', 'Leads people in other regions',
                                                          'Context only (countries led): expected at L0, L1 and L2, never flagged.', '–')]
    for i, r in enumerate(rows):
        y0 = 186 + i * 54
        for (x0, w0, _), t, (c, f) in zip(cols, r, ((mu, 'Book'), (ink, 'Semibold'), (ink, 'Book'), (mu, 'Book'))):
            pg.text(x0, y0, w0 - 10, 50, [(t, c, 9, f)], show=show)
        pg.box(322, y0 + 50, 960, 1, P['line'], show=show)
    pg.text(322, 572, 960, 80, [('Spans and layers (15 or more directs, one direct) appear in the KPIs as information. Executive officers are leaders here '
                                 'but stay out of every count. Matrix signals apply to people Keystone holds; a contingent worker Keystone does not know '
                                 'is case study 4\'s reconciliation gap.', mu, 8.5, 'Book')], show=show)
    return pg.zones


zones = layout('l', L) + layout('d', D)
DASH_UID = uid()
dash = (f"  <dashboards>\n    <dashboard enable-sort-zone-taborder='true' name='{DASH}'>\n"
        f"      <style>\n        <style-rule element='table'>\n          <format attr='background-color' value='{PAL['l']['bg']}' />\n        </style-rule>\n      </style>\n"
        f"      <size maxheight='{H}' maxwidth='{W}' minheight='{H}' minwidth='{W}' sizing-mode='fixed' />\n      <zones>\n"
        + indent('\n'.join(zones), 8) + f"\n      </zones>\n      <simple-id uuid='{DASH_UID}' />\n    </dashboard>\n  </dashboards>\n")
dash = re.sub(r"<zone (?=[^>]*id='(\d+)')", lambda mm: "<zone hidden-by-user='true' " if not VIS[mm.group(1)].startswith('Show Light') or
              any(k in VIS[mm.group(1)] for k in ('Wide', 'Pick', 'Cal', 'Rules')) else "<zone ", dash)

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
          (f'Picker L0 default{sfx}', S['Org Field'], 'p_B0', 'Pick B0 Default'),
          (f'Picker L1 default{sfx}', S['Org Field'], 'p_B1', 'Pick B1 Default'),
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
          (f'Pick L0 browse{sfx}', S['Pick L0'], 'p_B0', 'leader_id'),
          (f'Pick L0 focus{sfx}', S['Pick L0'], 'p_Focus', 'leader_id'),
          (f'Pick L0 open{sfx}', S['Pick L0'], 'p_Open', 'Empty Text'),
          (f'Pick L0 clears L1{sfx}', S['Pick L0'], 'p_B1', 'Empty Text'),
          (f'Pick L1 browse{sfx}', S['Pick L1'], 'p_B1', 'leader_id'),
          (f'Pick L1 focus{sfx}', S['Pick L1'], 'p_Focus', 'leader_id'),
          (f'Pick L1 open{sfx}', S['Pick L1'], 'p_Open', 'Empty Text'),
          (f'Pick L2 focus{sfx}', S['Pick L2'], 'p_Focus', 'leader_id'),
          (f'Pick L2 open{sfx}', S['Pick L2'], 'p_Open', 'Empty Text'),
          (f'Pick L2 closes{sfx}', S['Pick L2'], 'p_PickOpen', 'Close Panel'),
          (f'Pick day{sfx}', S['Calendar'], 'p_Day', 'day_offset'),
          (f'Pick day closes{sfx}', S['Calendar'], 'p_CalOpen', 'Close Panel')]
    for nm in ('Tree', 'Tree Wide'):
        T += [(f'{nm} focus{sfx}', S[nm], 'p_Focus', 'Focus Target'), (f'{nm} open{sfx}', S[nm], 'p_Open', 'Open Target'),
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
LISTS = [n for n in names if n.startswith(('Pick L0', 'Pick L1', 'Pick L2', 'Align Solid', 'Align Matrix', 'Align Role'))]
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
