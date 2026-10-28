"""Build Seats to Fill.twb from the base workbook (Custom SQL + extract), stage by stage.

  D4_TWB=<Dashboard #4 workbook> python3 build_d5.py BASE OUT STAGE
      BASE   the workbook Tableau saved right after connecting the Custom SQL and extracting (build guide 2.2)
      STAGE  1: KPI band; 2: + main chart, survival, backtest; 3: everything (the published workbook)
  Close the workbook in Tableau first; the output replaces it.
"""
import re
import os
import sys
import uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twb import Sheet, indent, uid, xesc
from model_d5 import model, DS

BASE, OUT, STAGE = sys.argv[1], sys.argv[2], int(sys.argv[3])
src = open(BASE, encoding='utf-8').read()
m = model(src)
DASH = 'Dashboard'
W, H = 1400, 850

NAVY, SLATE, INK, WHITE = '#13233a', '#5a6170', '#1f2329', '#ffffff'
PALE, MIST, AXIS = '#e4e9f0', '#b9c3d1', '#8c9bb0'
TEAL_D, TEAL_M, TEAL_L = '#0f6e56', '#5dcaa5', '#d3eee4'

SHEETS = {}
ACTIONS = {}


def action_id(caption):
    if caption not in ACTIONS:
        import uuid
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


def axis_fixed(s, ref, lo, hi, scope, show=False, spacing=None):
    sp = f" major-origin='{float(lo)}' major-spacing='{float(spacing)}'" if spacing else ''
    s.axis_rules.append(f"<encoding attr='space' class='0' field='{ref}' field-type='quantitative'{sp} max='{hi}' min='{lo}' "
                        f"range-type='fixed' scope='{scope}' type='space' />")
    s.axis_rules.append(f"<format attr='title' class='0' field='{ref}' scope='{scope}' value='' />")
    if not show:
        s.axis_rules.append(f"<format attr='display' class='0' field='{ref}' scope='{scope}' value='false' />")
    s.axis_rules += ["<format attr='tick-color' value='#00000000' />", "<format attr='stroke-size' value='0' />",
                     "<format attr='line-visibility' value='off' />"]


# =====================================================================================================
# Stage 1: the KPI band
# =====================================================================================================
s = new('Page Title')
s.pane('Text', enc=ZZ, label=[[('Seats to Fill', 'bold', 18, NAVY)], [('{Page Subtitle}', 'book', 11, SLATE)]], valign='top')

s = new('Hero Text')
s.pane('Text', enc=ZZ, valign='top', label=[
    [('{Hero Kicker}', 'semi', 9, MIST)],
    [('{F Fills}', 'bold', 36, WHITE), ('   likely {F Fills Lo} to {F Fills Hi}', 'book', 12, PALE)],
    [('{Hero Line 3}', 'book', 10, PALE)]])

s = new('Hero Quota', deselect=False)
s.filter_member('Quota Row', 'true')
x = s.f('Quota From', 'min')
s.cols = x
qy = s.f('Tick X', 'agg')
s.rows = qy
s.axis_rules += [f"<encoding attr='space' class='0' field='{qy}' field-type='quantitative' max='1' min='0' range-type='fixed' scope='rows' type='space' />",
                 f"<format attr='display' class='0' field='{qy}' scope='rows' value='false' />"]
r_att, r_lo, r_hi = s.f('Quota Att Mark', 'agg'), s.f('Quota Lo Mark', 'agg'), s.f('Quota Hi Mark', 'agg')
BANDS = ['#eef0f3', '#dde2e9', '#b9c3d1', '#9fd6c3', '#5dcaa5']
refs = []
for k, col in enumerate(BANDS):
    refs += s.refband(2 * k, x, k * 0.25, (k + 1) * 0.25, col)
refs += s.refband(13, x, r_lo, r_hi, '#ffffff59')
refs += [s.refline(10, x, r_lo, WHITE, 1.5), s.refline(11, x, r_hi, WHITE, 1.5), s.refline(12, x, r_att, WHITE, 3)]
s.pane('GanttBar', enc=[('size', 'Quota Width', 'min'), ('lod', 'Quota Att Mark', 'agg'),
                        ('lod', 'Quota Lo Mark', 'agg'), ('lod', 'Quota Hi Mark', 'agg')], refs=refs, size='1', transparency='0',
       stroke='false')
axis_fixed(s, x, 0, 1.25, 'cols', show=True, spacing=0.25)
s.styles.append(f"<style-rule element='label'>\n  <format attr='font-size' field='{x}' value='8' />\n"
                f"  <format attr='color' field='{x}' value='#8a97a8' />\n</style-rule>")

for k, title, big, lo, hi, line4 in (
        (1, 'KPI 1 Title', 'F To Fill', 'F To Fill Lo', 'F To Fill Hi', 'Waiting Text'),
        (2, 'KPI 2 Title', 'F Vacant', 'F Vacant Lo', 'F Vacant Hi', 'Vacant Change Text')):
    s = new(f'KPI {k}')
    s.pane('Text', enc=ZZ, valign='top', label=[
        [('{' + title + '}', 'book', 10, SLATE)], [('{' + big + '}', 'bold', 30, NAVY)], [(' ', 'book', 6, SLATE)],
        [('Likely {' + lo + '} to {' + hi + '}', 'medium', 11, INK)], [('{' + line4 + '}', 'book', 10, SLATE)]])

s = new('KPI 3')
s.filter_member('Recent Cohort', 'true')
s.filter_member('SV Is Last', 'true', 'tc', ['days_to'])
s.pane('Text', enc=ZZ + [('lod', 'days_to', 'ord')], valign='top', order=['days_to'], label=[
    [('{KPI 3 Title}', 'book', 10, SLATE)], [('{SV Median Days} days', 'bold', 30, NAVY)], [(' ', 'book', 6, SLATE)],
    [('{SV Within 90} within 90 days', 'medium', 11, INK)],
    [('Approved in the past year', 'book', 10, SLATE)]],
    tooltip=None)
KPI3_TIP = ([[('Half the PIDs approved in the last four quarters were filled within ', 'book', 11, INK), ('{SV Median Days} days', 'semi', 11, NAVY),
              ('; ', 'book', 11, INK), ('{SV Within 90}', 'semi', 11, TEAL_D), (' within 90 days, a quarter.', 'book', 11, INK)],
             [('Open PIDs count as still waiting, so recent quarters are not read as fast. The curves on the right show each level.',
               'book', 10, SLATE)]])

HOVERS = {
    'Hover Hero': [[('{Subject|attr} should fill about ', 'book', 11, INK), ('{F Fills Str} PIDs', 'semi', 11, NAVY),
                    (' in {Period Label|attr}, ', 'book', 11, INK), ('{F Att Str} of the {P Plan Str}', 'semi', 11, TEAL_D),
                    (' the {Fwd FY|attr} Budget plans.', 'book', 11, INK)],
                   [('{Hero Tip 2}', 'book', 10, SLATE)], [('{Hero Tip 3}', 'book', 10, SLATE)]],
    'Hover KPI 1': [[('{F To Fill Str} PIDs', 'semi', 11, NAVY), (' need filling in {Period Label|attr}: the ', 'book', 11, INK),
                     ('{F Waiting Str}', 'semi', 11, NAVY), ('{Tip Waiting Words|attr}, and the PIDs expected to open during the {Tip Span Word|attr}', 'book', 11, INK)],
                    [('{KPI 1 Tip 2}', 'book', 10, SLATE)]],
    'Hover KPI 2': [[('Of the {F To Fill Str} PIDs to fill in {Period Label|attr}, about ', 'book', 11, INK), ('{F Fills Str}', 'semi', 11, TEAL_D),
                     (' should be filled; ', 'book', 11, INK), ('{F Vacant Str}', 'semi', 11, NAVY), (' would still be vacant at its end.', 'book', 11, INK)],
                    [('<Sheet name="Bridge Tip" maxwidth="420" maxheight="230" filter="<None>">', 'book', 10, INK)],
                    [('The seat bridge · averages of 100 simulated futures, so it adds up exactly', 'book', 9, SLATE)]],
}
for name, tip in HOVERS.items():
    s = new(name)
    hc = s.f('Hover Cell', 'dim')
    s.rows = s.cols = hc
    s.hide_labels.append(hc)
    s.pane('Square', enc=ZZ + [('lod', 'Hover Cell', 'dim')], tooltip=tip, size='14.5', transparency='0', stroke='false')

s = new('Hover KPI 3')                       # the survival numbers need days_to in the view and the last period kept
s.filter_member('Recent Cohort', 'true')
s.filter_member('SV Is Last', 'true', 'tc', ['days_to'])
hc = s.f('Hover Cell', 'dim')
s.rows = s.cols = hc
s.hide_labels.append(hc)
s.pane('Square', enc=ZZ + [('lod', 'Hover Cell', 'dim'), ('lod', 'days_to', 'ord')], tooltip=KPI3_TIP, order=['days_to'],
       size='14.5', transparency='0', stroke='false')

s = new('Bridge Tip', deselect=False)
s.filter_member('Bridge Row', 'true')
cp = s.f('chart_point', 'ord')
cs = s.f('chart_series', 'dim')
s.cols = f'({cp} / {cs})'
s.hide_labels.append(cp)
y = s.f('Bridge Start', 'min')
s.rows = y
axis_fixed_rows = f"<format attr='display' class='0' field='{y}' scope='rows' value='false' />"
s.axis_rules += [f"<format attr='title' class='0' field='{y}' scope='rows' value='' />", axis_fixed_rows,
                 "<format attr='tick-color' value='#00000000' />"]
s.styles.append(f"<style-rule element='label'>\n  <format attr='display' field='{cp}' value='false' />\n"
                f"  <format attr='font-size' field='{cs}' value='9' />\n  <format attr='color' field='{cs}' value='{SLATE}' />\n</style-rule>")
s.hide_labels.clear()
s.pane('GanttBar', enc=[('color', 'Bridge Kind', 'dim'), ('size', 'Bridge Size', 'min')], valign='top', align='center',
       label=[[('{Bridge Label Plain|min}{Bridge Label Plus|min}{Bridge Label Minus|min}', 'semi', 9, NAVY)]],
       cell_fmt="<format attr='text-orientation' value='0' />",
       transparency='255', stroke='false', size='2')
s.styles.append("<style-rule element='worksheet'>\n  <format attr='display-field-labels' scope='cols' value='false' />\n</style-rule>")


# =====================================================================================================
# Stage 2: main chart, survival, backtest
# =====================================================================================================
if STAGE >= 2:
    LAB = '#8c9bb0'

    def axis_labels(s, ref, size=9, colour=LAB):
        s.styles.append(f"<style-rule element='label'>\n  <format attr='font-size' field='{ref}' value='{size}' />\n"
                        f"  <format attr='color' field='{ref}' value='{colour}' />\n</style-rule>")

    s = new('Main Title')
    s.pane('Text', enc=ZZ, valign='top', label=[[('{Main Title Text}', 'semi', 13, NAVY)], [('{Main Subtitle}', 'book', 10, SLATE)]])

    # --- the chart: fan (polygon) and lines (filled, forecast, budget step) on one synchronised dual axis
    s = new('Main Chart', deselect=False)
    s.filter_member('Main Chart Row', 'true')
    x = s.f('chart_x', 'min')
    fy, ly = s.f('Fan Y', 'min'), s.f('Line Y', 'min')
    s.cols = x
    s.rows = f'({fy} + {ly})'
    axis_fixed(s, x, 0, 24, 'cols', show=False)
    s.axis_rules += [f"<encoding attr='space' class='0' domain-expand='false' field='{fy}' field-type='quantitative' scope='rows' type='space' />",
                     f"<format attr='width' field='{fy}' value='44' />", f"<format attr='width' field='{ly}' value='44' />",
                     f"<format attr='title' class='0' field='{fy}' scope='rows' value='' />",
                     f"<encoding attr='space' class='0' field='{ly}' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />",
                     f"<format attr='display' class='0' field='{ly}' scope='rows' value='false' />"]
    axis_labels(s, fy)
    refs = [s.refline(i + 4, x, s.f(f'Ref X{v}', 'agg'), '#e4e3dd', 1) for i, v in enumerate((4, 8, 12, 16))]
    refs.append(s.refline(8, x, s.f('Ref X20', 'agg'), NAVY, 1, 'dotted', label='Data ends · forecast starts'))
    pf, pt = s.f('Period From', 'min'), s.f('Period To', 'min')
    refs = s.refband(0, x, 20, 24, '#eef7f3') + s.refband(2, x, pf, pt, '#ddefe7') + refs
    s.pane('Automatic', enc=[('lod', f'Ref X{v}', 'agg') for v in (4, 8, 12, 16, 20)] + [('lod', 'Period From', 'min'),
           ('lod', 'Period To', 'min')], pane_id=2, refs=refs)
    s.pane('Polygon', enc=[('path', 'chart_point', 'ord'), ('lod', 'chart_part', 'dim')] + [('lod', f'Ref X{v}', 'agg') for v in (4, 8, 12, 16, 20)],
           pane_id=3, y_axis=fy, color=TEAL_L, transparency='255', stroke='false',
           tooltip=[[('Likely range: 8 in 10 simulated futures', 'book', 9, SLATE)]])
    s.pane('Line', enc=[('path', 'chart_point', 'ord'), ('color', 'chart_series', 'dim')] + [('lod', f'Ref X{v}', 'agg') for v in (4, 8, 12, 16, 20)],
           pane_id=4, y_axis=ly, transparency='255', align='right',
           label=[[('{End Label|min}', 'bold', 10, TEAL_D)]],
           tooltip=[[('{Line Tip Head|attr}', 'semi', 11, NAVY), ('{Line Tip Body|attr}', 'book', 11, INK)], [('{Line Tip 2|attr}', 'book', 10, SLATE)]])

    # --- fiscal-year chips over the chart; quarter and year labels under it (same 0-24 axis, same left axis width)
    def pad_axis(s):
        p = s.f('Axis Pad', 'agg')
        s.rows = p
        s.axis_rules += [f"<encoding attr='space' class='0' field='{p}' field-type='quantitative' max='2000' min='0' range-type='fixed' scope='rows' type='space' />",
                         f"<format attr='title' class='0' field='{p}' scope='rows' value='' />",
                         f"<format attr='width' field='{p}' value='44' />"]
        axis_labels(s, p, 9, WHITE)

    s = new('FY Chips', deselect=False)
    s.filter_member('Chip Row', 'true')
    x = s.f('chart_x', 'min')
    s.cols = x
    axis_fixed(s, x, 0, 24, 'cols', show=False)
    pad_axis(s)
    s.pane('Shape', enc=[('shape', 'FY Chip Shape', 'agg'), ('lod', 'fiscal_year_label', 'dim')], size='5', align='center',
           label=[[('{FY Att}', 'semi', 9, NAVY)]], transparency='255')

    s = new('Quarter Axis', deselect=False)
    s.filter_member('Quarter Tick Row', 'true')
    x = s.f('Quarter Tick X', 'min')
    s.cols = x
    axis_fixed(s, x, 0, 24, 'cols', show=False)
    pad_axis(s)
    s.pane('Text', enc=[('lod', 'quarter_offset', 'ord')], align='center', valign='top',
           label=[[('{Quarter Tick Text}', 'book', 9, LAB)], [('{Year Under}', 'semi', 9, NAVY)]])

    # --- how fast PIDs fill: Kaplan-Meier as a table calculation, one curve per level band
    SVO = ['days_to']
    s = new('Survival', deselect=False)
    s.filter_member('Recent Cohort', 'true')
    x = s.f('days_to', 'cont')
    y = s.f('SV Filled Share', 'tc', SVO)
    s.cols, s.rows = x, y
    axis_fixed(s, x, 0, 150, 'cols', show=True, spacing=30)
    s.axis_rules.append(f"<format attr='text-format' field='{x}' scope='cols' value='*0&quot; days&quot;' />")
    axis_fixed(s, y, 0, 1, 'rows', show=True, spacing=0.5)
    axis_labels(s, y)
    s.styles[-1] = s.styles[-1].replace("</style-rule>", f"  <format attr='font-size' field='{x}' value='8' />\n  <format attr='color' field='{x}' value='{LAB}' />\n</style-rule>")
    refs = [s.refline(i, x, s.f(f'Ref D{v}', 'agg'), '#d5dbe4', 1, 'dotted') for i, v in enumerate((29, 59, 89))]
    s.pane('Line', enc=[('color', 'level_band', 'dim')] + [('lod', f'Ref D{v}', 'agg') for v in (29, 59, 89)], refs=refs,
           order=SVO, transparency='255', extra_mark_fmt="<format attr='line-interpolation' value='step' />",
           tooltip=[[('{level_band}: ', 'semi', 11, NAVY), ('{SV Filled Share}', 'semi', 11, TEAL_D),
                     (' of PIDs filled within {Days Plus One} days.', 'book', 11, INK)]])

    s = new('Level Legend')
    s.filter_member('Recent Cohort', 'true')
    s.filter_member('SV Is Last', 'true', 'tc', SVO)
    lc, lr = s.f('Legend Col', 'ord'), s.f('Legend Row', 'ord')
    s.cols, s.rows = lc, lr
    s.hide_labels += [lc, lr]
    s.pane('Text', enc=ZZ + [('color', 'level_band', 'dim'), ('lod', 'days_to', 'ord')], order=SVO,
           transparency='255', align='left',
           label=[[('━ ', 'bold', 9, None), ('{level_band}', 'book', 9, INK), (' · {SV Median Days Str}', 'book', 9, SLATE)]])

    # --- can we trust it: the method one quarter ahead against what happened
    BTO = ['quarter_offset']
    s = new('Backtest Title')
    s.filter_member('BT Row', 'true')
    s.filter_member('BT Is Last', 'true', 'tc', BTO)
    qo = s.f('quarter_offset', 'ord')
    s.rows = qo
    s.hide_labels.append(qo)
    s.pane('Text', enc=ZZ, order=BTO, valign='top',
           label=[[('{BT Title}', 'semi', 13, NAVY)], [('{BT Subtitle}', 'book', 10, SLATE)]])

    s = new('Backtest', deselect=False)
    s.filter_member('BTS Row', 'true')
    qo, ql = s.f('fiscal_year_label', 'dim'), s.f('Quarter Tick Text', 'dim')
    s.cols = f'({qo} / {ql})'
    lo, act = s.f('BTS Y', 'min'), s.f('BTS Actual', 'min')
    s.rows = f'({lo} + {act})'
    s.axis_rules += [f"<encoding attr='space' class='0' domain-expand='false' field='{lo}' field-type='quantitative' scope='rows' type='space' />",
                     f"<format attr='title' class='0' field='{lo}' scope='rows' value='' />",
                     f"<encoding attr='space' class='0' field='{act}' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />",
                     f"<format attr='display' class='0' field='{act}' scope='rows' value='false' />",
                     "<format attr='tick-color' value='#00000000' />"]
    s.styles.append(f"<style-rule element='label'>\n  <format attr='font-size' field='{qo}' value='8' />\n  <format attr='color' field='{qo}' value='{NAVY}' />\n"
                    f"  <format attr='font-size' field='{ql}' value='8' />\n  <format attr='color' field='{ql}' value='{LAB}' />\n"
                    f"  <format attr='font-size' field='{lo}' value='9' />\n  <format attr='color' field='{lo}' value='{LAB}' />\n</style-rule>")
    s.styles.append("<style-rule element='worksheet'>\n  <format attr='display-field-labels' scope='cols' value='false' />\n</style-rule>")
    tip = [[('{quarter_label|attr}', 'semi', 11, NAVY), (', forecast one quarter ahead: ', 'book', 11, INK),
            ('{QBT Low|min} to {QBT High|min} fills', 'semi', 11, TEAL_D), ('; ', 'book', 11, INK), ('{QBT Actual|min} filled', 'semi', 11, NAVY),
            (', {BTS In|attr}.', 'book', 11, INK)]]
    s.pane('Automatic', pane_id=2, enc=[('lod', 'chart_series', 'dim')])
    s.pane('GanttBar', pane_id=3, y_axis=lo, enc=[('color', 'BTS Part', 'dim'), ('size', 'BTS Size', 'min'), ('lod', 'chart_series', 'dim')],
           size='0.8', transparency='255', stroke='false', tooltip=tip)
    s.pane('Shape', pane_id=4, y_axis=act, enc=[('shape', 'BTS In', 'dim'), ('lod', 'chart_series', 'dim')], size='0.6',
           transparency='255', stroke='false', tooltip=tip)


# =====================================================================================================
# Stage 3: rail, popovers
# =====================================================================================================
if STAGE >= 3:
    PALE2, MUTED, DIMC, HEAD = '#e4e9f0', '#8fa0b8', '#4f6178', '#8fa0b8'

    def control(name, shape=None, shape_field=None, lod=(), label=None, tip=None, size='12', mark='Shape',
                align='left', scaffold=True):
        s = new(name)
        if scaffold:
            s.filter_member('Is Scaffold', 'true')
        enc = ZZ + [('lod', n, 'dim') for n in lod]
        if shape_field:
            enc.append(('shape', shape_field, 'dim'))
        fmt = f"<format attr='shape' value='{shape}' />" if shape else ''
        s.pane(mark, enc=enc, label=label, size=size if mark == 'Shape' else None, transparency='255', stroke='false',
               extra_mark_fmt=fmt, align=align, tooltip=[[(tip, 'book', 9, SLATE)]] if tip else None)
        return s

    control('Period Field', shape='Arcadia D4/d4_field_capsule.png', lod=('Toggle Period Panel', 'Close Panel'),
            label=[[('    {Period Field Text}', 'semi', 9, NAVY)]], tip='Choose the period')
    control('Org Field', shape_field='Org Capsule Shape', lod=('Toggle Org Panel', 'Close Panel'),
            label=[[('    {Org Text Light}', 'semi', 9, NAVY), ('{Org Text Dark}', 'medium', 9, PALE2)]],
            tip='Choose functions and departments')
    control('Loc Field', shape_field='Loc Capsule Shape', lod=('Toggle Loc Panel', 'Close Panel'),
            label=[[('    {Loc Text Light}', 'semi', 9, NAVY), ('{Loc Text Dark}', 'medium', 9, PALE2)]],
            tip='Choose regions, countries and offices')
    control('Org Sub', mark='Text', label=[[('{Org Sub Text}', 'book', 9, '#8a97a8')]])
    control('Loc Sub', mark='Text', label=[[('{Loc Sub Text}', 'book', 9, '#8a97a8')]])
    s = control('Reset', shape='Arcadia D4/d4_reset.png', lod=('Empty Text', 'Close Panel'), size='10.6',
                tip='Reset to default view', align='center')
    s.panes[-1] = s.panes[-1].replace("</encodings>", f"  <lod column='{s.f('Zero Period', 'ord')}' />\n  </encodings>")
    control('Info Button', shape_field='Info Shape', lod=('Toggle Info', 'Close Panel'), size='2', align='center',
            tip='How the forecast works')
    control('Rail As Of', mark='Text', label=[[('{Rail Line 1}', 'semi', 9, PALE2)], [('{Rail Line 2}', 'book', 9, MIST)],
                                              [('{Draws} simulated futures', 'book', 9, MIST)]])
    for p in ('Period', 'Org', 'Loc'):
        control(f'{p} Close', mark='Text', lod=('Close Panel',), label=[[('{Close X}', 'book', 12, '#b8c0cc')]], tip='Close',
                align='center')

    LISTS = []

    def lst(name, rows, hidden, shape, label, lod, filters=(), base='Is Quarter'):
        s = new(name)
        if base == 'Is Quarter':
            s.filter_member('Is Quarter', 'true')
        for f_, mem in filters:
            s.filter_member(f_, mem)
        refs = [s.f(r, 'ord' if r == 'quarter_offset' else 'dim') for r in rows]
        s.rows = refs[0] if len(refs) == 1 else '(' + ' / '.join(refs) + ')'
        for r in refs:
            if r in [s.f(h, 'ord' if h == 'quarter_offset' else 'dim') for h in hidden]:
                s.hide_labels.append(r)
        heads = [r for r in refs if r not in s.hide_labels]
        if heads:
            s.styles.append("<style-rule element='label'>\n" + ''.join(
                f"  <format attr='font-size' field='{r}' value='9' />\n  <format attr='color' field='{r}' value='{HEAD}' />\n"
                for r in heads) + "</style-rule>")
        s.cell_size = (None, 18, refs[-1])
        tx = s.f('Tick X', 'agg')
        s.cols = tx
        s.axis_rules += [f"<encoding attr='space' class='0' field='{tx}' field-type='quantitative' max='10' min='0' range-type='fixed' scope='cols' type='space' />",
                         f"<format attr='display' class='0' field='{tx}' scope='cols' value='false' />", "<format attr='tick-color' value='#00000000' />",
                         "<format attr='stroke-size' value='0' />", "<format attr='line-visibility' value='off' />"]
        s.styles.append("<style-rule element='worksheet'>\n  <format attr='display-field-labels' scope='rows' value='false' />\n</style-rule>")
        LISTS.append(name)
        hw = 'agg' if m.level(shape) == 'agg' else 'dim'
        s.pane('Shape', enc=ZZ + [('shape', shape, hw)] + [('lod', n, 'agg' if n in m.calcs and m.level(n) == 'agg' else ('ord' if n == 'quarter_offset' else 'dim')) for n in lod],
               label=label, size='1.8', transparency='255', stroke='false', align='right',
               extra_mark_fmt="<format attr='mark-labels-mode' value='all' />")
        return s

    NL = lambda on, lock, dim: [[('  {' + on + '}', 'book', 10, PALE2)] + ([('  {' + lock + '}', 'book', 10, MUTED)] if lock else [])
                                + [('  {' + dim + '}', 'book', 10, DIMC)]]
    lst('Period List', ['quarter_offset'], ['quarter_offset'], 'Period Shape',
        [[('  {Period Option Text}', 'book', 10, PALE2)]], ['quarter_offset', 'Close Panel'],
        filters=[('Is Scaffold', 'true'), ('chart_series', 'Forecast')], base=None)
    lst('Function List', ['function_name'], ['function_name'], 'Function Shape', NL('Function Name On', None, 'Function Name Dim'),
        ['Function Pick', 'Function DeptOff Pick'])
    lst('Dept List', ['Dept Key'], ['Dept Key'], 'Dept Shape',
        NL('Dept Name On', 'Dept Name Locked', 'Dept Name Dim'), ['Dept Pick'], filters=[('Dept Visible', 'true')])
    lst('Region List', ['region'], ['region'], 'Region Shape', NL('Region Name On', None, 'Region Name Dim'),
        ['Region Pick', 'Region CountryOff Pick', 'Region OfficeOff Pick'])
    lst('Country List', ['Country Key'], ['Country Key'], 'Country Shape',
        NL('Country Name On', 'Country Name Locked', 'Country Name Dim'), ['Country Pick', 'Country OfficeOff Pick'],
        filters=[('Country Visible', 'true')])
    # one row per office, no country groups: a group of one row drops its label, so the country rides in the label
    lst('Office List', ['Office Key'], ['Office Key'], 'Office Shape',
        [[('  {country_name|attr} · ', 'book', 10, MUTED), ('{Office Name On}', 'book', 10, PALE2),
          ('{Office Name Locked}', 'book', 10, MUTED), ('{Office Name Dim}', 'book', 10, DIMC)]],
        ['Office Pick'], filters=[('Office Visible', 'true')])

# =====================================================================================================
# datasource
# =====================================================================================================
def bucket_map(ref_inst, kind, mapping):
    ms = '\n'.join(f"  <map to='{to}'>\n    <bucket>&quot;{xesc(b)}&quot;</bucket>\n  </map>" for b, to in mapping)
    return f"<encoding attr='{kind}' field='{ref_inst}' type='{'palette' if kind == 'color' else 'shape'}'>\n{ms}\n</encoding>"


styled = []
enc_rules = []
SERIES = [('Band 1', '#eef0f3'), ('Band 2', '#dde2e9'), ('Band 3', '#b9c3d1'), ('Band 4', '#9fd6c3'), ('Band 5', '#5dcaa5'),
          ('Filled', NAVY), ('Forecast', TEAL_D), ('Budget', SLATE)]
enc_rules.append(bucket_map(m.inst('chart_series', 'dim')[0], 'color', SERIES)); styled.append(('chart_series', 'dim'))
KINDS = [('waiting', NAVY), ('opens', '#9fb0c6'), ('to fill', TEAL_D), ('filled', TEAL_M), ('vacant', SLATE)]
enc_rules.append(bucket_map(m.inst('Bridge Kind', 'dim')[0], 'color', KINDS)); styled.append(('Bridge Kind', 'dim'))
LEVELS = [('L1-L2', '#13233a'), ('L3-L4', '#4a5d78'), ('L5-L6', '#8c9bb0'), ('L7+', '#b8a888')]
enc_rules.append(bucket_map(m.inst('level_band', 'dim')[0], 'color', LEVELS)); styled.append(('level_band', 'dim'))
if STAGE >= 2:
    enc_rules.append(bucket_map(m.inst('BTS In', 'dim')[0], 'shape', [('in range', 'Arcadia D5/d5_dot_in.png'),
                                                                     ('outside', 'Arcadia D5/d5_dot_out.png')]))
    styled.append(('BTS In', 'dim'))
    enc_rules.append(bucket_map(m.inst('BTS Part', 'dim')[0], 'color', [('range', TEAL_L), ('average', TEAL_D)]))
    styled.append(('BTS Part', 'dim'))
    enc_rules.append(bucket_map(m.inst('FY Chip Shape', 'agg')[0], 'shape',
                                [('d5_chip_teal', 'Arcadia D5/d5_chip_teal.png'), ('d5_chip_slate', 'Arcadia D5/d5_chip_slate.png')]))
    styled.append(('FY Chip Shape', 'agg'))
if STAGE >= 3:
    TICK = [('d4_tick_on', 'Arcadia D4/d4_tick_on.png'), ('d4_tick_off', 'Arcadia D4/d4_tick_off.png')]
    for n in ('Function Shape', 'Dept Shape', 'Region Shape', 'Country Shape', 'Office Shape'):
        enc_rules.append(bucket_map(m.inst(n, 'agg')[0], 'shape', TICK)); styled.append((n, 'agg'))
    enc_rules.append(bucket_map(m.inst('Period Shape', 'dim')[0], 'shape', TICK)); styled.append(('Period Shape', 'dim'))
    CAPS = [('d4_field_capsule', 'Arcadia D4/d4_field_capsule.png'), ('d4_field_capsule_dark', 'Arcadia D4/d4_field_capsule_dark.png')]
    for n in ('Org Capsule Shape', 'Loc Capsule Shape'):
        enc_rules.append(bucket_map(m.inst(n, 'dim')[0], 'shape', CAPS)); styled.append((n, 'dim'))
    enc_rules.append(bucket_map(m.inst('Info Shape', 'dim')[0], 'shape',
                                [('d2_info_open', 'Arcadia D4/d2_info_open.png'), ('d2_info_close', 'Arcadia D4/d2_info_close.png')]))
    styled.append(('Info Shape', 'dim'))

ds_insts = '\n'.join(m.inst_decl(n, h) for n, h in styled)
group = (f"<group caption='Action (zzFalse)' hidden='true' name='[Action (zzFalse)]' name-style='unqualified' user:auto-column='sheet_link'>\n"
         f"  <groupfilter function='crossjoin'>\n    <groupfilter function='level-members' level='[{m.cid['zzFalse']}]' />\n  </groupfilter>\n</group>")
calc_decls = '\n'.join(m.decl(c) for c in m.order)
raw_over = '\n'.join(m.raw_decl(r) for r in sorted(set(m.raw_role) | {'level_band', 'chart_series', 'country_name'}))
ds_style = "<style>\n  <style-rule element='mark'>\n" + indent('\n'.join(enc_rules), 4) + "\n  </style-rule>\n</style>"
ds_params = "<datasource-dependencies datasource='Parameters'>\n" + indent('\n'.join(m.param_decl(p) for p in m.params), 2) + "\n</datasource-dependencies>"

out = src
d4 = open(os.environ.get('D4_TWB', 'Contingent Workforce Reconciliation.twb'), encoding='utf-8').read()   # its feature manifest is reused
man = r'  <document-format-change-manifest>.*?</document-format-change-manifest>\n'
out = out.replace(re.search(man, out, re.S).group(0), re.search(man, d4, re.S).group(0), 1)
pds = ("    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>\n      <aliases enabled='yes' />\n"
       + indent('\n'.join(m.param_decl(p) for p in m.params), 6) + "\n    </datasource>\n")
out = out.replace("  <datasources>\n", "  <datasources>\n" + pds, 1)
old_cc = "      <column datatype='string' name='[country_name]' role='dimension' semantic-role='[Country].[ISO3166_2]' type='nominal' />\n"
assert old_cc in out
out = out.replace(old_cc, indent(calc_decls + '\n' + raw_over + '\n' + ds_insts + '\n' + group, 6) + '\n', 1)
lay = "      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />\n"
assert lay in out
out = out.replace(lay, lay + indent(ds_style, 6) + '\n', 1)
sv = "      </semantic-values>\n"
assert out.count(sv) == 1
out = out.replace(sv, sv + indent(ds_params, 6) + '\n', 1)

# =====================================================================================================
# dashboard
# =====================================================================================================
def z(px, py, pw, ph):
    return (f"h='{round(ph / H * 100000)}' w='{round(pw / W * 100000)}' x='{round(px / W * 100000)}' "
            f"y='{round(py / H * 100000)}'")


zid = [10]


def nid():
    zid[0] += 1
    return zid[0]


NOB = ("<zone-style>\n  <format attr='border-color' value='#000000' />\n  <format attr='border-style' value='none' />\n"
       "  <format attr='border-width' value='0' />\n  <format attr='margin' value='0' />\n</zone-style>")


def sheet_zone(name, px, py, pw, ph, fixed=None):
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    return (f"<zone {z(px, py, pw, ph)}{fx} id='{nid()}' name='{xesc(name)}' show-title='false'>\n" + indent(NOB, 2) + "\n</zone>")


def container(fname, px, py, pw, ph, children, bg, border=None, radius=14, pad=(18, 22, 18, 22)):
    t, r, b, l = pad
    st = [f"<format attr='border-color' value='{border or '#000000'}' />",
          f"<format attr='border-style' value='{'solid' if border else 'none'}' />",
          f"<format attr='border-width' value='{1 if border else 0}' />",
          f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='{radius}' />",
          f"<format attr='padding-top' value='{t}' />", f"<format attr='padding-right' value='{r}' />",
          f"<format attr='padding-bottom' value='{b}' />", f"<format attr='padding-left' value='{l}' />",
          f"<format attr='background-color' value='{bg}' />"]
    return (f"<zone friendly-name='{fname}' {z(px, py, pw, ph)} id='{nid()}' param='vert' type-v2='layout-flow'>\n"
            + indent('\n'.join(children), 2) + "\n  <zone-style>\n" + indent('\n'.join(st), 4) + "\n  </zone-style>\n</zone>")


def text_zone(px, py, pw, ph, runs, pad=None, fixed=None):
    rr = '\n'.join(("    <run>Æ&#10;&#10;</run>" if t == '\n\n' else "    <run>Æ&#10;</run>") if t in ('\n', '\n\n') else f"    <run fontcolor='{c}' fontname='Tableau {f}' fontsize='{sz}'>{xesc(t)}</run>"
                   for t, c, sz, f in runs)
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    nob = NOB
    if pad:
        t_, r_, b_, l_ = pad
        nob = NOB.replace("</zone-style>", f"  <format attr='padding-top' value='{t_}' />\n  <format attr='padding-right' value='{r_}' />\n"
                          f"  <format attr='padding-bottom' value='{b_}' />\n  <format attr='padding-left' value='{l_}' />\n</zone-style>")
    return (f"<zone {z(px, py, pw, ph)}{fx} id='{nid()}' type-v2='text'>\n  <formatted-text>\n{rr}\n  </formatted-text>\n"
            + indent(nob, 2) + "\n</zone>")


zones = [sheet_zone('Page Title', 240, 16, 1136, 56)]
zones.append(container('Hero', 240, 86, 452, 172, [sheet_zone('Hero Text', 262, 98, 408, 104, 104),
                                                    sheet_zone('Hero Quota', 262, 202, 408, 44, 44)], NAVY, pad=(12, 22, 12, 22)))
for k, x0 in ((1, 704), (2, 932), (3, 1160)):
    zones.append(container(f'KPI {k}', x0, 86, 216, 172, [sheet_zone(f'KPI {k}', x0 + 20, 104, 176, 136)], WHITE,
                           border='#e4e3dd', pad=(18, 20, 18, 20)))
zones.append(sheet_zone('Hover Hero', 240, 86, 452, 172))
zones.append(sheet_zone('Hover KPI 1', 704, 86, 216, 172))
zones.append(sheet_zone('Hover KPI 2', 932, 86, 216, 172))
zones.append(sheet_zone('Hover KPI 3', 1160, 86, 216, 172))
IMG = '/Users/thiagoalpoin/Documents/Tableau/Tableau Public/ArcadiaHR/5 Seats to Fill/Images and Buttons/'


def image_zone(file, px, py, pw, ph, fixed=None):
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    return (f"<zone {z(px, py, pw, ph)}{fx} id='{nid()}' is-centered='0' is-scaled='1' param='{xesc(IMG + file)}' type-v2='bitmap' />")


def image_zone_any(path, px, py, pw, ph):
    return (f"<zone {z(px, py, pw, ph)} id='{nid()}' is-centered='0' is-scaled='1' param='{xesc(path)}' type-v2='bitmap' />")


def rule_zone(px, py, pw, ph, colour=NAVY):
    return (f"<zone {z(px, py, pw, ph)} id='{nid()}' type-v2='empty'>\n  <zone-style>\n"
            f"    <format attr='background-color' value='{colour}' />\n  </zone-style>\n</zone>")


if STAGE >= 2:
    zones.append(container('Card: Main', 240, 272, 724, 540, [
        sheet_zone('Main Title', 254, 288, 696, 50, 50), sheet_zone('FY Chips', 254, 338, 696, 28, 28),
        sheet_zone('Main Chart', 254, 366, 696, 368, 368), sheet_zone('Quarter Axis', 254, 734, 696, 34, 34),
        image_zone('d5_main_legend.png', 254, 770, 600, 20, 20)], WHITE, border='#e4e3dd', pad=(16, 14, 8, 14)))
    zones.append(rule_zone(988, 272, 388, 2))
    zones.append(text_zone(988, 282, 388, 46, [('How long PIDs wait, by level', NAVY, 13, 'Semibold'), ('\n', None, None, None),
                                                ('Share filled by days waited; PIDs approved in the past year', SLATE, 10, 'Book')]))
    zones.append(sheet_zone('Survival', 984, 330, 392, 158))
    zones.append(sheet_zone('Level Legend', 988, 506, 388, 40))
    zones.append(rule_zone(988, 562, 388, 2))
    zones.append(sheet_zone('Backtest Title', 988, 572, 388, 48))
    zones.append(sheet_zone('Backtest', 984, 620, 392, 160))
    zones.append(image_zone('d5_backtest_legend.png', 988, 786, 388, 18))
    zones.append(text_zone(240, 826, 1136, 16, [(
        'Arcadia Systems is fictional; all data is synthetic. Executive officers excluded. Forecast = the average of 100 simulated '
        'futures; the range holds 8 in 10 of them (10th to 90th percentile).', SLATE, 9, 'Book')]))
else:
    zones.append(sheet_zone('Bridge Tip', 240, 300, 420, 230))
zones.append(f"<zone {z(0, 0, 216, 850)} id='{nid()}' type-v2='empty'>\n  <zone-style>\n    <format attr='background-color' value='{NAVY}' />\n  </zone-style>\n</zone>")

D4IMG = '/Users/thiagoalpoin/Documents/Tableau/Tableau Public/ArcadiaHR/4 Contingent Workforce Reconciliation/Images and Buttons/'
VIS = {}          # parameter -> popover zone id


def hide(x):
    return x.replace("<zone ", "<zone hidden-by-user='true' ")


def popover(name, param, px, py, pw, ph, title, body, footer):
    """navy vertical container: header (title + close), a 1 px line, the body, the footer"""
    head_children = [text_zone(px, py, pw - 40, 44, [(title, WHITE, 12, 'Bold')], pad=(14, 0, 0, 16))]
    if body is not None and name != 'Info':
        head_children.append(sheet_zone(f'{name} Close', px + pw - 40, py, 40, 44, 40))
    head = flow(f'{name} Popover Header', px, py, pw, 44, head_children, 'horz', fixed=44)
    line = rule_zone(px, py + 44, pw, 1, '#2b3d57').replace("<zone ", "<zone fixed-size='1' is-fixed='true' ", 1)
    foot_h = 30 if footer else 0
    if "fixed-size=" not in body.split('>', 1)[0]:
        body = body.replace("<zone ", f"<zone fixed-size='{ph - 45 - foot_h}' is-fixed='true' ", 1)   # the footer stays at the bottom
    k = body.rfind("</zone-style>")                     # 12 px between the rail edge and the first column
    body = body[:k] + "  <format attr='padding-left' value='12' />\n" + body[k:]
    parts = [head, line, body]
    if footer:
        parts.append(text_zone(px, py + ph - 30, pw, 30, [(footer, '#8fa0b8', 9, 'Book')], fixed=30, pad=(6, 16, 0, 16)))
    x = flow(f'{name} Popover', px, py, pw, ph, parts, 'vert', bg=NAVY, radius_right=10)
    zid_ = re.search(r"friendly-name='" + name + r" Popover' [^>]*id='(\d+)'", x).group(1)
    VIS[param] = zid_
    return hide_all(x)


def hide_all(x):
    return re.sub(r"<zone (?!hidden-by-user)", "<zone hidden-by-user='true' ", x)


def flow(fname, px, py, pw, ph, children, param, fixed=None, bg=None, radius_right=None):
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    st = ["<format attr='border-color' value='#000000' />", "<format attr='border-style' value='none' />",
          "<format attr='border-width' value='0' />", "<format attr='margin' value='0' />"]
    if radius_right:
        st += ["<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='4' />",
               "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-top-left' value='0' />",
               f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-top-right' value='{radius_right}' />",
               "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-bottom-left' value='0' />",
               f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-bottom-right' value='{radius_right}' />",
               "<format attr='padding' value='0' />"]
    if bg:
        st.append(f"<format attr='background-color' value='{bg}' />")
    return (f"<zone friendly-name='{fname}' {z(px, py, pw, ph)}{fx} id='{nid()}' param='{param}' type-v2='layout-flow'>\n"
            + indent('\n'.join(children), 2) + "\n  <zone-style>\n" + indent('\n'.join(st), 4) + "\n  </zone-style>\n</zone>")


if STAGE >= 3:
    # the rail (floating items over the navy panel)
    zones.append(image_zone_any(D4IMG + 'arcadia_logo_horizontal_reverse.png', 8, 24, 160, 40))
    zones.append(sheet_zone('Info Button', 180, 30, 28, 28))
    for lbl, y in (('PERIOD', 92), ('ORGANIZATION', 172), ('LOCATION', 252)):
        zones.append(text_zone(8, y, 200, 16, [(lbl, '#b8c4d6', 8, 'Semibold')], pad=(0, 0, 0, 4)))
    zones.append(sheet_zone('Period Field', 8, 110, 200, 32))
    zones.append(sheet_zone('Org Field', 8, 190, 200, 32))
    zones.append(sheet_zone('Org Sub', 8, 222, 200, 20))
    zones.append(sheet_zone('Loc Field', 8, 270, 200, 32))
    zones.append(sheet_zone('Loc Sub', 8, 302, 200, 20))
    zones.append(image_zone_any(D4IMG + 'arcadia_rail_divider.png', 8, 332, 200, 24))
    zones.append(sheet_zone('Reset', 8, 362, 200, 32))
    zones.append(sheet_zone('Rail As Of', 8, 766, 200, 60))
    # popovers
    zones.append(popover('Period', 'p_PeriodOpen', 216, 108, 360, 190, 'Period',
                         sheet_zone('Period List', 224, 153, 360, 115), 'Time to fill and the backtest stay the same.'))
    org_body = flow('Org Body', 224, 185, 640, 625, [sheet_zone('Function List', 224, 185, 220, 625, 220),
                                                     sheet_zone('Dept List', 444, 185, 420, 625)], 'horz')
    zones.append(popover('Org', 'p_OrgOpen', 216, 140, 640, 700, 'Organization', org_body,
                         'Every department starts ticked. The last one ticked stays; a greyed one has nothing in the chosen locations.'))
    loc_body = flow('Loc Body', 224, 175, 640, 645, [sheet_zone('Region List', 224, 175, 180, 645, 180),
                                                     sheet_zone('Country List', 404, 175, 200, 645, 200),
                                                     sheet_zone('Office List', 604, 175, 260, 645)], 'horz')
    zones.append(popover('Loc', 'p_LocOpen', 216, 130, 640, 720, 'Location', loc_body,
                         'Every country and office starts ticked.'))
    INFO = [('How the forecast works.', 'We learned how quickly each kind of PID gets filled and how often PIDs open, simulated the next fiscal year 100 times, and tested the same method on eight quarters that already happened.'),
            ('The numbers.', 'Each number is the average of the 100 simulated futures, so they add up; a range holds 8 in 10 of them. Plan attainment is forecast fills over the fiscal year\'s Budget, set before the year.'),
            ('Time to fill.', 'Kaplan–Meier over the PIDs approved in the last four quarters: open PIDs count as still waiting, so recent quarters are not read as fast.'),
            ('Limits.', 'The near future is assumed to look like the recent past. A new office is forecast only from its own history. A company-wide event, such as a hiring freeze, is outside the range.'),
            ('Contingent workers', 'are not forecast here: the FY27 Budget plans 13,097 at year end.'),
            ('Data.', 'Arcadia Systems is fictional; all data is synthetic. Executive officers are excluded.')]
    runs = []
    for k, (lead, body) in enumerate(INFO):
        if k:
            runs.append(('\n\n', None, None, None))
        runs += [(lead + ' ', WHITE, 10, 'Semibold'), (body, '#b8c0cc', 10, 'Book')]
    zones.append(popover('Info', 'p_InfoOpen', 216, 24, 591, 420, 'How to read this page',
                         text_zone(224, 69, 591, 375, runs, pad=(12, 16, 0, 16), fixed=375), None))

DASH_UID = uid()
dash = (f"  <dashboards>\n    <dashboard enable-sort-zone-taborder='true' name='{DASH}'>\n"
        "      <style>\n        <style-rule element='table'>\n          <format attr='background-color' value='#f3f3ef' />\n        </style-rule>\n      </style>\n"
        f"      <size maxheight='{H}' maxwidth='{W}' minheight='{H}' minwidth='{W}' sizing-mode='fixed' />\n      <zones>\n"
        + indent('\n'.join(zones), 8) + f"\n      </zones>\n      <simple-id uuid='{DASH_UID}' />\n    </dashboard>\n  </dashboards>\n")

# =====================================================================================================
# actions (deselects)
# =====================================================================================================
def q(t):
    return t.replace(' ', '%20')


acts = []
for name, sh in SHEETS.items():
    if not sh.deselect:
        continue
    cap = 'Deselect ' + name
    expr = f"tsl:{q(name)}?%5B{DS}%5D.%5B{m.cid['zzFalse']}%5D~s0=&lt;[{DS}].[{m.cid['zzTrue']}]~na&gt;"
    acts.append(f"<action caption='{cap}' name='{action_id(cap)}'>\n  <activation auto-clear='true' type='on-select' />\n"
                f"  <source dashboard='{DASH}' type='sheet' worksheet='{xesc(name)}' />\n"
                f"  <link caption='{cap}' delimiter=',' escape='\\' expression='{expr}' include-null='true' multi-select='true' url-escape='true' />\n"
                f"  <command command='tsc:tsl-filter'>\n    <param name='target' value='{xesc(name)}' />\n  </command>\n</action>")
PA = []
if STAGE >= 3:
    T = [('Open period popover', 'Period Field', 'p_PeriodOpen', 'Toggle Period Panel')]
    T += [(f'Period closes {p}', 'Period Field', p, 'Close Panel') for p in ('p_OrgOpen', 'p_LocOpen', 'p_InfoOpen')]
    T += [('Set period', 'Period List', 'p_Period', 'quarter_offset'), ('Close period popover on pick', 'Period List', 'p_PeriodOpen', 'Close Panel'),
          ('Period popover on x', 'Period Close', 'p_PeriodOpen', 'Close Panel'),
          ('Open org popover', 'Org Field', 'p_OrgOpen', 'Toggle Org Panel')]
    T += [(f'Org closes {p}', 'Org Field', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_LocOpen', 'p_InfoOpen')]
    T += [('Toggle function', 'Function List', 'p_Functions', 'Function Pick'),
          ('Function cleans departments', 'Function List', 'p_DeptOff', 'Function DeptOff Pick'),
          ('Toggle department', 'Dept List', 'p_DeptOff', 'Dept Pick'),
          ('Org popover on x', 'Org Close', 'p_OrgOpen', 'Close Panel'),
          ('Open loc popover', 'Loc Field', 'p_LocOpen', 'Toggle Loc Panel')]
    T += [(f'Loc closes {p}', 'Loc Field', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_OrgOpen', 'p_InfoOpen')]
    T += [('Toggle region', 'Region List', 'p_Regions', 'Region Pick'),
          ('Region cleans countries', 'Region List', 'p_CountryOff', 'Region CountryOff Pick'),
          ('Region cleans offices', 'Region List', 'p_OfficeOff', 'Region OfficeOff Pick'),
          ('Toggle country', 'Country List', 'p_CountryOff', 'Country Pick'),
          ('Country cleans offices', 'Country List', 'p_OfficeOff', 'Country OfficeOff Pick'),
          ('Toggle office', 'Office List', 'p_OfficeOff', 'Office Pick'),
          ('Loc popover on x', 'Loc Close', 'p_LocOpen', 'Close Panel')]
    T += [(f'Reset {p}', 'Reset', p, 'Empty Text') for p in ('p_Functions', 'p_DeptOff', 'p_Regions', 'p_CountryOff', 'p_OfficeOff')]
    T += [('Reset period', 'Reset', 'p_Period', 'Zero Period')]
    T += [(f'Reset closes {p}', 'Reset', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_OrgOpen', 'p_LocOpen', 'p_InfoOpen')]
    T += [('Open info', 'Info Button', 'p_InfoOpen', 'Toggle Info')]
    T += [(f'Info closes {p}', 'Info Button', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_OrgOpen', 'p_LocOpen')]
    for cap, sheet, target, field in T:
        how = 'agg' if field in m.calcs and m.level(field) == 'agg' else ('ord' if field in ('quarter_offset', 'Zero Period') else 'dim')
        PA.append(f"<edit-parameter-action caption='{cap}' name='{action_id(cap)}'>\n  <activation type='on-select' />\n"
                  f"  <source dashboard='{DASH}' type='sheet' worksheet='{xesc(sheet)}' />\n  <agg-type type='attr' />\n"
                  f"  <clear-option type='do-nothing' value='b:false' />\n  <params>\n"
                  f"    <param name='source-field' value='{m.ref(field, how)}' />\n"
                  f"    <param name='target-parameter' value='[Parameters].[{m.pid[target]}]' />\n  </params>\n</edit-parameter-action>")
acts += PA
actions_xml = "  <actions>\n" + indent('\n'.join(acts), 4) + "\n  </actions>\n"
out = out.replace("  <worksheets>\n", actions_xml + "  <worksheets>\n", 1)
out = out.replace("  </worksheets>\n", indent('\n'.join(s.xml() for s in SHEETS.values()), 4) + "\n  </worksheets>\n", 1)
out = out.replace("  <windows source-height='30'>\n", dash + "  <windows source-height='30'>\n", 1)


def ws_window(name):
    return (f"<window class='worksheet' name='{xesc(name)}'>\n  <cards>\n    <edge name='left'>\n      <strip size='160'>\n"
            "        <card type='pages' />\n        <card type='filters' />\n        <card type='marks' />\n      </strip>\n    </edge>\n"
            "    <edge name='top'>\n      <strip size='2147483647'>\n        <card type='columns' />\n      </strip>\n"
            "      <strip size='2147483647'>\n        <card type='rows' />\n      </strip>\n      <strip size='31'>\n        <card type='title' />\n"
            "      </strip>\n    </edge>\n  </cards>\n  <viewpoint>\n    <zoom type='entire-view' />\n  </viewpoint>\n"
            f"  <simple-id uuid='{uid()}' />\n</window>")


names = list(SHEETS)
LISTS = globals().get('LISTS', [])
vps = '\n'.join(f"    <viewpoint name='{xesc(n)}'>\n      <zoom type='{'fit-width' if n in LISTS else 'entire-view'}' />\n    </viewpoint>" for n in sorted(names))
dwin = (f"<window class='dashboard' maximized='true' name='{DASH}'>\n  <viewpoints>\n{vps}\n  </viewpoints>\n"
        f"  <active id='-1' />\n  <simple-id uuid='{uid()}' />\n</window>")
out = out.replace("    <window class='worksheet' maximized='true' name='Checkpoint'>", "    <window class='worksheet' name='Checkpoint'>", 1)
out = out.replace("  </windows>\n", indent('\n'.join(ws_window(n) for n in names) + '\n' + dwin, 4) + "\n  </windows>\n", 1)
if STAGE >= 3:
    nodes, pairs, edges = [], [], []
    for p, zid_ in VIS.items():
        pn, pin, pout = (str(uuid.uuid4()) for _ in range(3))
        zn, zin = str(uuid.uuid4()), str(uuid.uuid4())
        nodes.append(f"<single-value-field-node fieldname='[Parameters].[{m.pid[p]}]' fieldname-input-guid='{pin}' node-guid='{pn}' value-output-guid='{pout}' />")
        nodes.append(f"<dashboard-zone-visibility-node dashboard-identifier='{DASH_UID}' node-guid='{zn}' visibility-input-guid='{zin}' zone-id='{zid_}' />")
        pairs += [pn, zn]
        edges.append(f"<edge from='{pout}' to='{zin}' />")
    sub = str(uuid.uuid4())
    graph = ("  <datagraph>\n    <graph>\n      <properties>\n        <default-execution-subgraph-guid value='" + sub + "' />\n      </properties>\n"
             "      <node-execution-subgraphs>\n" + ''.join(f"        <pair execution-subgraph-guid='{sub}' node-guid='{g}' />\n" for g in pairs)
             + "      </node-execution-subgraphs>\n      <nodes>\n" + ''.join(f"        {n}\n" for n in nodes) + "      </nodes>\n      <edges>\n"
             + ''.join(f"        {e}\n" for e in edges) + "      </edges>\n    </graph>\n  </datagraph>\n")
    out = out.replace("  </windows>\n", "  </windows>\n" + graph, 1)
open(OUT, 'w', encoding='utf-8').write(out)
print('calcs', len(m.order), 'sheets', len(SHEETS), 'actions', len(acts))
