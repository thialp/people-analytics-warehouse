"""Build Workforce Cost Bridge.twb from the base workbook (Custom SQL + extract, build guide 2.2).

  D4_TWB=<Dashboard #4 workbook> python3 build_d6.py BASE OUT
      BASE   the workbook Tableau saved right after connecting the Custom SQL and extracting
  Close the workbook in Tableau first; the output is a new file beside it.
Every calculation is read from the build guide's code blocks (d6_calcs.py); the sheets, dashboard, popovers and
actions follow the guide's sections 6 to 12.
"""
import os
import re
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twb import Sheet, indent, uid, xesc  # noqa: E402
from model_d6 import model, ORDER  # noqa: E402

BASE, OUT = sys.argv[1], sys.argv[2]
src = open(BASE, encoding='utf-8').read()
m = model(src)
DS = m.ds
DASH = 'Dashboard'
W, H = 1400, 850

NAVY, SLATE, INK, WHITE = '#13233a', '#5a6170', '#1f2329', '#ffffff'
PALE, MIST, AXIS, GRID = '#e4e9f0', '#b9c3d1', '#8c9bb0', '#ecedea'
TEAL, SAND, SAND_D, LEVEL = '#0f6e56', '#b8a888', '#7d6a45', '#8c9bb0'
PALE2, MUTED = '#e4e9f0', '#8fa0b8'

SHEETS, ACTIONS = {}, {}


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


def tip_field(n):
    """a field only on the Tooltip shelf must be an aggregate: a row-level one goes on as ATTR"""
    return '{' + n + ('' if m.level(n) in ('agg', 'tc') else '|attr') + '}'


def label_style(s, ref, size, colour):
    s.styles.append(f"<style-rule element='label'>\n  <format attr='font-size' field='{ref}' value='{size}' />\n"
                    f"  <format attr='color' field='{ref}' value='{colour}' />\n</style-rule>")


def no_field_labels(s, scope):
    s.styles.append(f"<style-rule element='worksheet'>\n  <format attr='display-field-labels' scope='{scope}' value='false' />\n</style-rule>")


# ===================================================================================================== title, KPIs
s = new('Page Title')
s.pane('Text', enc=ZZ, valign='top', label=[[('Workforce Cost Bridge', 'bold', 20, NAVY)], [('{Page Subtitle}', 'book', 11, SLATE)]])

KPIS = [(1, 'K1 Title', 'S Closing Txt', 'K1 Line'), (2, 'K2 Title', 'S Volume Txt', 'K2 Line'),
        (3, 'K3 Title', 'S Rate Txt', 'K3 Line'), (4, 'K4 Title', 'S Mix Txt', 'K4 Line'),
        (5, 'K5 Title', 'S Currency Txt', 'K5 Line')]
for k, t, big, line in KPIS:
    s = new(f'KPI {k}')
    s.pane('Text', enc=ZZ, valign='top', label=[[('{' + t + '}', 'book', 10, SLATE)], [('{' + big + '}', 'bold', 22, NAVY)],
                                                [('{' + line + '}', 'book', 9, SLATE)]])
for k in range(1, 6):
    s = new(f'Hover K{k}')
    hc = s.f('Hover Cell', 'dim')
    s.rows = s.cols = hc
    s.hide_labels.append(hc)
    s.pane('Square', enc=ZZ + [('lod', 'Hover Cell', 'dim')], size='14.5', transparency='0', stroke='false',
           tooltip=[[(tip_field(f'K{k} Tip 1'), 'book', 11, INK)], [(tip_field(f'K{k} Tip 2'), 'book', 10, SLATE)]])

# ===================================================================================================== bridge
s = new('Bridge Title')
s.pane('Text', enc=ZZ, valign='top', label=[[('{Bridge Title}', 'semi', 14, NAVY)], [('{Bridge Subtitle}', 'book', 10, SLATE)]])

s = new('Bridge', deselect=False)
s.filter_member('In Selection', 'true')
fo, fh, fs = s.f('factor_order', 'ord'), s.f('Factor Head', 'dim'), s.f('Factor Sub', 'dim')
s.cols = f'({fo} / ({fh} / {fs}))'
s.hide_labels.append(fo)
top, ly = s.f('Bar Top', 'tc', ORDER), s.f('Label Y', 'tc', ORDER)
s.rows = f'({top} + {ly})'
s.axis_rules += [f"<encoding attr='space' class='0' domain-expand='false' field='{top}' field-type='quantitative' scope='rows' type='space' />",
                 f"<format attr='title' class='0' field='{top}' scope='rows' value='' />",
                 f"<encoding attr='space' class='0' field='{ly}' field-type='quantitative' fold='true' scope='rows' synchronized='true' type='space' />",
                 f"<format attr='display' class='0' field='{ly}' scope='rows' value='false' />",
                 "<format attr='tick-color' value='#00000000' />"]
s.styles.append(f"<style-rule element='label'>\n  <format attr='display' field='{fo}' value='false' />\n"
                f"  <format attr='font-size' field='{fh}' value='9' />\n  <format attr='color' field='{fh}' value='{INK}' />\n"
                f"  <format attr='font-size' field='{fs}' value='8' />\n  <format attr='color' field='{fs}' value='{SLATE}' />\n"
                f"  <format attr='font-size' field='{top}' value='8' />\n  <format attr='color' field='{top}' value='{AXIS}' />\n</style-rule>")
s.hide_labels.clear()
no_field_labels(s, 'cols')
s.grid_rows = GRID
floor = s.f('Floor Mark', 'agg')
TIP = [[('{Tip Head} ', 'semi', 11, NAVY), ('{Tip Value Level}', 'bold', 11, NAVY), ('{Tip Value Adds}', 'bold', 11, TEAL),
        ('{Tip Value Takes}', 'bold', 11, SAND_D)],
       [('{factor_meaning|attr}', 'book', 10, INK)], [('{Tip Share}', 'book', 10, SLATE)], [('{Tip Order}', 'book', 9, SLATE)]]
s.pane('Automatic', pane_id=2, enc=[('lod', 'Floor Mark', 'agg')], refs=[s.refline(0, top, floor, '#d5dbe4', 1)])
s.pane('GanttBar', pane_id=3, y_axis=top, order=ORDER, size='2.5', transparency='255', stroke='false', tooltip=TIP,
       enc=[('color', 'Bar Kind', 'agg'), ('size', 'Bar Size', 'tc', ORDER), ('lod', 'Floor Mark', 'agg')])
s.pane('Text', pane_id=4, y_axis=ly, order=ORDER, align='center', valign='bottom', tooltip=TIP,
       enc=[('color', 'Label Kind', 'agg'), ('lod', 'Floor Mark', 'agg')],
       label=[[('{Bar Label}', 'semi', 10, None)]])

s = new('Bridge Note')
s.pane('Text', enc=ZZ, valign='top', label=[[('Axis starts at {Floor Text|attr} so the factors are visible. ', 'book', 9, SLATE),
                                             ('Teal adds cost, sand takes it away; the six effects add up to the change exactly.', 'book', 9, SLATE)]])

# ===================================================================================================== order of the steps
s = new('Bias Title')
s.pane('Text', enc=ZZ, valign='top', label=[
    [('The order of the steps changes the answer', 'semi', 14, NAVY)], [('{Bias Subtitle}', 'book', 10, SLATE)],
    [('■', 'book', 10, NAVY), (' Shapley (every order)   ', 'book', 9, SLATE), ('■', 'book', 10, MIST),
     (' One fixed order   ', 'book', 9, SLATE), ('Bias = fixed order − Shapley, $M', 'book', 9, SLATE)]])

s = new('Bias Bars', deselect=False)
s.filter_member('In Selection', 'true')
s.filter_member('Is Factor', 'true')
fo, fh = s.f('factor_order', 'ord'), s.f('Factor Head', 'dim')
sh, sq = s.f('Shapley', 'sum'), s.f('One fixed order', 'sum')
MN, MV = f'[{DS}].[:Measure Names]', f'[{DS}].[Multiple Values]'
s.filters.append(f"<filter class='categorical' column='{MN}'>\n  <groupfilter function='union' user:op='manual'>\n"
                 f"    <groupfilter function='member' level='[:Measure Names]' member='&quot;{sh}&quot;' />\n"
                 f"    <groupfilter function='member' level='[:Measure Names]' member='&quot;{sq}&quot;' />\n  </groupfilter>\n</filter>")
s.slices.append(MN)
s.rows = f'({fo} / ({fh} / {MN}))'
s.cols = MV
s.hide_labels += [fo, MN]
label_style(s, fh, 10, INK)
s.axis_rules += [f"<format attr='display' class='0' field='{MV}' scope='cols' value='false' />",
                 "<format attr='tick-color' value='#00000000' />"]
no_field_labels(s, 'rows')
s.zeroline = '#d5dbe4'
s.pane('Bar', size='0.7', transparency='255', stroke='false', labels_show=True,
       label=[[(f'<{MV}>', 'book', 8, SLATE)]],
       tooltip=[[('{Factor Head}', 'semi', 10, NAVY)],
                [('Shapley {Shapley|sum} · one fixed order {One fixed order|sum} · bias {Bias Text}', 'book', 10, SLATE)]])
s.panes[-1] = s.panes[-1].replace("<encodings>", f"<encodings>\n    <color column='{MN}' />", 1)

s = new('Bias Column')
s.filter_member('In Selection', 'true')
s.filter_member('Is Factor', 'true')
fo = s.f('factor_order', 'ord')
s.rows = fo
s.hide_labels.append(fo)
s.pane('Text', enc=ZZ + [('color', 'Bias Notable', 'agg')], align='right', label=[[('{Bias Text}', 'semi', 10, None)]])

# ===================================================================================================== five fiscal years
s = new('Year Title')
s.pane('Text', enc=ZZ, valign='top', label=[[('{Year Title|attr}', 'semi', 14, NAVY)], [('{Year Subtitle|attr}', 'book', 10, SLATE)]])

s = new('Year Table', deselect=False)
s.filter_member('Year Row', 'true')
fy, yl = s.f('fiscal_year', 'ord'), s.f('Year Row Label', 'dim')
co, cn = s.f('Table Col Order', 'ord'), s.f('Table Column', 'dim')
s.rows, s.cols = f'({fy} / {yl})', f'({co} / {cn})'
s.hide_labels += [fy, co]
s.styles.append(f"<style-rule element='label'>\n  <format attr='font-size' field='{yl}' value='10' />\n  <format attr='color' field='{yl}' value='{NAVY}' />\n"
                f"  <format attr='font-size' field='{cn}' value='9' />\n  <format attr='color' field='{cn}' value='{SLATE}' />\n</style-rule>")
no_field_labels(s, 'rows'); no_field_labels(s, 'cols')
s.pane('Text', enc=[('color', 'Cell Kind', 'agg')], align='left', label=[[('{Cell Text}', 'book', 10, None)]],
       tooltip=[[('{Year Row Label} · {Table Column}: ', 'book', 10, INK), ('{Cell Text}', 'semi', 10, NAVY)]])

s = new('Year Note')
s.pane('Text', enc=ZZ, valign='top', label=[[('{Year Note|attr}', 'book', 9, SLATE)]])

# ===================================================================================================== rail controls


def control(name, shape=None, shape_field=None, lod=(), label=None, tip=None, size='12', mark='Shape', align='left'):
    s = new(name)
    enc = ZZ + [('lod', n, 'agg' if m.level(n) == 'agg' else ('ord' if m.role(n)[1] == 'ordinal' else 'dim')) for n in lod]
    if shape_field:
        enc.append(('shape', shape_field, 'dim'))
    fmt = f"<format attr='shape' value='{shape}' />" if shape else ''
    s.pane(mark, enc=enc, label=label, size=size if mark == 'Shape' else None, transparency='255', stroke='false',
           extra_mark_fmt=fmt, align=align, tooltip=[[(tip, 'book', 9, SLATE)]] if tip else None)
    return s


control('Period Field', shape='Arcadia D4/d4_field_capsule.png', lod=('Toggle Period Panel', 'Close Panel'),
        label=[[('    {Pair Label}', 'semi', 9, NAVY)]], tip='Choose the two dates to compare')
control('Period Sub', mark='Text', label=[[('{Span Text}', 'book', 8, '#8a97a8')]])
control('Org Field', shape_field='Org Capsule Shape', lod=('Toggle Org Panel', 'Close Panel'),
        label=[[('    {Org Text Light}', 'semi', 9, NAVY), ('{Org Text Dark}', 'medium', 9, PALE2)]],
        tip='Choose all of Arcadia or one function')
control('Org Sub', mark='Text', label=[[('{Org Sub Text}', 'book', 8, '#8a97a8')]])
control('Reset', shape='Arcadia D4/d4_reset.png', lod=('Zero Pair', 'Default Group', 'Close Panel'), size='10',
        tip='Reset to default view', align='center')
control('Info Button', shape_field='Info Shape', lod=('Toggle Info', 'Close Panel'), size='2', align='center',
        tip='How the bridge works')
control('Rail As Of', mark='Text', label=[[('{Rail Line 1}', 'semi', 9, PALE2)], [('Nominal USD, ECB month-end rates', 'book', 9, MIST)],
                                          [('Employees and contingent workers', 'book', 9, MIST)]])
for p in ('Period', 'Org', 'Info'):
    control(f'{p} Close', mark='Text', lod=('Close Panel',), label=[[('{Close X}', 'book', 12, '#b8c0cc')]], tip='Close',
            align='center')

LISTS = []


def lst(name, rows, flt, shape, label, lod):
    s = new(name)
    s.filter_member(flt, 'true')
    refs = [s.f(r, 'ord' if (r in m.raw_role or (r in m.calcs and m.role(r)[1] == 'ordinal')) else 'dim') for r in rows]
    s.rows = refs[0] if len(refs) == 1 else '(' + ' / '.join(refs) + ')'
    s.hide_labels += refs
    s.cell_size = (None, 22, refs[-1])
    tx = s.f('Tick X', 'agg')
    s.cols = tx
    s.axis_rules += [f"<encoding attr='space' class='0' field='{tx}' field-type='quantitative' max='10' min='0' range-type='fixed' scope='cols' type='space' />",
                     f"<format attr='display' class='0' field='{tx}' scope='cols' value='false' />", "<format attr='tick-color' value='#00000000' />",
                     "<format attr='stroke-size' value='0' />", "<format attr='line-visibility' value='off' />"]
    no_field_labels(s, 'rows')
    LISTS.append(name)
    s.pane('Shape', enc=ZZ + [('shape', shape, 'agg')] + [('lod', n, 'ord' if (n in m.raw_role or (n in m.calcs and m.role(n)[1] == 'ordinal')) else 'dim') for n in lod],
           label=label, size='8', transparency='255', stroke='false', align='right',
           extra_mark_fmt="<format attr='mark-labels-mode' value='all' />")
    return s


lst('Pair List', ['Pair Offset'], 'Pair Option Row', 'Pair Shape',
    [[('  {Pair Option Name}', 'book', 10, PALE2), ('   {Pair Option Date}', 'book', 9, MUTED)]], ['Pair Offset', 'Close Panel'])
lst('Group List', ['view_order', 'group_name'], 'Group Option Row', 'Group Shape',
    [[('  {Group Option Name}', 'book', 10, PALE2), ('   {Group Option People}', 'book', 9, MUTED)]], ['group_name', 'Close Panel'])


# ===================================================================================================== datasource
def bucket_map(field, kind, mapping):
    ms = '\n'.join(f"  <map to='{to}'>\n    <bucket>&quot;{xesc(b)}&quot;</bucket>\n  </map>" for b, to in mapping)
    return f"<encoding attr='{kind}' field='{field}' type='{'palette' if kind == 'color' else 'shape'}'>\n{ms}\n</encoding>"


styled, enc_rules = [], []
for n, cols in (('Bar Kind', [('level', LEVEL), ('adds', TEAL), ('takes away', SAND)]),
                ('Label Kind', [('level', NAVY), ('adds', TEAL), ('takes away', SAND_D)]),
                ('Cell Kind', [('adds', TEAL), ('takes away', SAND_D)]),
                ('Bias Notable', [('notable', NAVY), ('small', AXIS)])):
    enc_rules.append(bucket_map(m.inst(n, 'agg')[0], 'color', cols)); styled.append((n, 'agg'))
enc_rules.append(f"<encoding attr='color' field='[:Measure Names]' type='palette'>\n"
                 f"  <map to='{NAVY}'>\n    <bucket>&quot;[{DS}].{m.inst('Shapley', 'sum')[0]}&quot;</bucket>\n  </map>\n"
                 f"  <map to='{MIST}'>\n    <bucket>&quot;[{DS}].{m.inst('One fixed order', 'sum')[0]}&quot;</bucket>\n  </map>\n</encoding>")
TICK = [('d4_tick_on', 'Arcadia D4/d4_tick_on.png'), ('d4_tick_off', 'Arcadia D4/d4_tick_off.png')]
for n in ('Pair Shape', 'Group Shape'):
    enc_rules.append(bucket_map(m.inst(n, 'agg')[0], 'shape', TICK)); styled.append((n, 'agg'))
enc_rules.append(bucket_map(m.inst('Org Capsule Shape', 'dim')[0], 'shape',
                            [('d4_field_capsule', 'Arcadia D4/d4_field_capsule.png'), ('d4_field_capsule_dark', 'Arcadia D4/d4_field_capsule_dark.png')]))
styled.append(('Org Capsule Shape', 'dim'))
enc_rules.append(bucket_map(m.inst('Info Shape', 'dim')[0], 'shape',
                            [('d2_info_open', 'Arcadia D4/d2_info_open.png'), ('d2_info_close', 'Arcadia D4/d2_info_close.png')]))
styled.append(('Info Shape', 'dim'))

ds_insts = '\n'.join(m.inst_decl(n, h) for n, h in styled)
group = (f"<group caption='Action (zzFalse)' hidden='true' name='[Action (zzFalse)]' name-style='unqualified' user:auto-column='sheet_link'>\n"
         f"  <groupfilter function='crossjoin'>\n    <groupfilter function='level-members' level='[{m.cid['zzFalse']}]' />\n  </groupfilter>\n</group>")
calc_decls = '\n'.join(m.decl(c) for c in m.order)
raw_over = '\n'.join(m.raw_decl(r) for r in sorted(m.raw_role))
ds_style = "<style>\n  <style-rule element='mark'>\n" + indent('\n'.join(enc_rules), 4) + "\n  </style-rule>\n</style>"
ds_params = "<datasource-dependencies datasource='Parameters'>\n" + indent('\n'.join(m.param_decl(p) for p in m.params), 2) + "\n</datasource-dependencies>"

out = src
d4 = open(os.environ.get('D4_TWB', 'Arcadia CW Reconciliation.twb'), encoding='utf-8').read()   # its feature manifest is reused
man = r'  <document-format-change-manifest>.*?</document-format-change-manifest>\n'
out = out.replace(re.search(man, out, re.S).group(0), re.search(man, d4, re.S).group(0), 1)
pds = ("    <datasource hasconnection='false' inline='true' name='Parameters' version='18.1'>\n      <aliases enabled='yes' />\n"
       + indent('\n'.join(m.param_decl(p) for p in m.params), 6) + "\n    </datasource>\n")
out = out.replace("  <datasources>\n", "  <datasources>\n" + pds, 1)
anchor = re.search(r"      <column caption='Workforce Cost Bridge' datatype='table' [^\n]*\n", out).group(0)
out = out.replace(anchor, anchor + indent(calc_decls + '\n' + raw_over + '\n' + ds_insts + '\n' + group, 6) + '\n', 1)   # before <extract>
lay = "      <layout dim-ordering='alphabetic' measure-ordering='alphabetic' show-structure='true' />\n"
assert out.count(lay) == 1
out = out.replace(lay, lay + indent(ds_style, 6) + '\n', 1)
sv = "      </semantic-values>\n"
assert out.count(sv) == 1
out = out.replace(sv, sv + indent(ds_params, 6) + '\n', 1)

# ===================================================================================================== dashboard


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
    return f"<zone {z(px, py, pw, ph)}{fx} id='{nid()}' name='{xesc(name)}' show-title='false'>\n" + indent(NOB, 2) + "\n</zone>"


def flow(fname, px, py, pw, ph, children, param, fixed=None, bg=None, radius_right=None, border=None, radius=None, pad=None):
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    st = [f"<format attr='border-color' value='{border or '#000000'}' />",
          f"<format attr='border-style' value='{'solid' if border else 'none'}' />",
          f"<format attr='border-width' value='{1 if border else 0}' />", "<format attr='margin' value='0' />"]
    if radius:
        st.append(f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='{radius}' />")
    if radius_right:
        st += ["<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius' value='4' />",
               "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-top-left' value='0' />",
               f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-top-right' value='{radius_right}' />",
               "<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-bottom-left' value='0' />",
               f"<_.fcp.DashboardRoundedCorners.true...format attr='corner-radius-bottom-right' value='{radius_right}' />",
               "<format attr='padding' value='0' />"]
    if pad:
        t, r, b, l = pad
        st += [f"<format attr='padding-top' value='{t}' />", f"<format attr='padding-right' value='{r}' />",
               f"<format attr='padding-bottom' value='{b}' />", f"<format attr='padding-left' value='{l}' />"]
    if bg:
        st.append(f"<format attr='background-color' value='{bg}' />")
    return (f"<zone friendly-name='{fname}' {z(px, py, pw, ph)}{fx} id='{nid()}' param='{param}' type-v2='layout-flow'>\n"
            + indent('\n'.join(children), 2) + "\n  <zone-style>\n" + indent('\n'.join(st), 4) + "\n  </zone-style>\n</zone>")


def card(fname, px, py, pw, ph, children, pad=(16, 14, 12, 14)):
    return flow(fname, px, py, pw, ph, children, 'vert', bg=WHITE, border='#e4e3dd', radius=14, pad=pad)


def text_zone(px, py, pw, ph, runs, pad=None, fixed=None):
    rr = '\n'.join(("    <run>Æ&#10;&#10;</run>" if t == '\n\n' else "    <run>Æ&#10;</run>") if t in ('\n', '\n\n')
                   else f"    <run fontcolor='{c}' fontname='Tableau {f}' fontsize='{sz}'>{xesc(t)}</run>" for t, c, sz, f in runs)
    fx = f" fixed-size='{fixed}' is-fixed='true'" if fixed else ''
    nob = NOB
    if pad:
        t_, r_, b_, l_ = pad
        nob = NOB.replace("</zone-style>", f"  <format attr='padding-top' value='{t_}' />\n  <format attr='padding-right' value='{r_}' />\n"
                          f"  <format attr='padding-bottom' value='{b_}' />\n  <format attr='padding-left' value='{l_}' />\n</zone-style>")
    return f"<zone {z(px, py, pw, ph)}{fx} id='{nid()}' type-v2='text'>\n  <formatted-text>\n{rr}\n  </formatted-text>\n" + indent(nob, 2) + "\n</zone>"


def rule_zone(px, py, pw, ph, colour=NAVY):
    return (f"<zone {z(px, py, pw, ph)} id='{nid()}' type-v2='empty'>\n  <zone-style>\n"
            f"    <format attr='background-color' value='{colour}' />\n  </zone-style>\n</zone>")


D4IMG = '/Users/thiagoalpoin/Documents/Tableau/Tableau Public/ArcadiaHR/4 Contingent Workforce Reconciliation/Images and Buttons/'


def image_zone(path, px, py, pw, ph):
    return f"<zone {z(px, py, pw, ph)} id='{nid()}' is-centered='0' is-scaled='1' param='{xesc(path)}' type-v2='bitmap' />"


zones = [sheet_zone('Page Title', 240, 16, 1136, 56)]
KX = (240, 470, 700, 930, 1160)
for k, x0 in enumerate(KX, 1):
    zones.append(card(f'KPI {k}', x0, 86, 216, 86, [sheet_zone(f'KPI {k}', x0 + 14, 98, 188, 62)], pad=(12, 14, 12, 14)))
for k, x0 in enumerate(KX, 1):
    zones.append(sheet_zone(f'Hover K{k}', x0, 86, 216, 86))
zones.append(card('Card: Bridge', 240, 186, 724, 626, [sheet_zone('Bridge Title', 254, 202, 696, 50, 50),
                                                       sheet_zone('Bridge', 254, 252, 696, 512, 512),
                                                       sheet_zone('Bridge Note', 254, 764, 696, 36, 36)]))
bias_row = flow('Bias Row', 1002, 276, 360, 200, [sheet_zone('Bias Bars', 1002, 276, 304, 200, 304),
                                                  sheet_zone('Bias Column', 1306, 276, 56, 200)], 'horz', fixed=200)
zones.append(card('Card: Order', 988, 186, 388, 302, [sheet_zone('Bias Title', 1002, 202, 360, 74, 74), bias_row]))
zones.append(card('Card: Years', 988, 502, 388, 310, [sheet_zone('Year Title', 1002, 518, 360, 58, 58),
                                                      sheet_zone('Year Table', 1002, 576, 360, 204, 204),
                                                      sheet_zone('Year Note', 1002, 780, 360, 20, 20)]))
zones.append(text_zone(240, 826, 1136, 16, [(
    'Arcadia Systems is fictional; all data is synthetic. Executive officers excluded. Effects are Shapley values: each '
    "factor's average effect over every order of the six steps, so they add up to the change.", SLATE, 9, 'Book')]))
zones.append(rule_zone(0, 0, 216, 850, NAVY))
zones.append(image_zone(D4IMG + 'arcadia_logo_horizontal_reverse.png', 8, 24, 160, 40))
zones.append(sheet_zone('Info Button', 180, 30, 28, 28))
for lbl, y in (('PERIOD', 132), ('ORGANIZATION', 228)):
    zones.append(text_zone(8, y, 200, 16, [(lbl, '#b8c4d6', 8, 'Semibold')], pad=(0, 0, 0, 4)))
zones += [sheet_zone('Period Field', 8, 154, 200, 32), sheet_zone('Period Sub', 8, 186, 200, 18),
          sheet_zone('Org Field', 8, 250, 200, 32), sheet_zone('Org Sub', 8, 282, 200, 18),
          image_zone(D4IMG + 'arcadia_rail_divider.png', 8, 324, 200, 24), sheet_zone('Reset', 8, 348, 200, 32),
          sheet_zone('Rail As Of', 8, 770, 200, 56)]

VIS = {}


def hide_all(x):
    return re.sub(r"<zone (?!hidden-by-user)", "<zone hidden-by-user='true' ", x)


def popover(name, param, px, py, pw, ph, title, body, footer):
    head = flow(f'{name} Popover Header', px, py, pw, 44,
                [text_zone(px, py, pw - 40, 44, [(title, WHITE, 12, 'Bold')], pad=(14, 0, 0, 12)),
                 sheet_zone(f'{name} Close', px + pw - 40, py, 40, 44, 40)], 'horz', fixed=44)
    line = rule_zone(px, py + 44, pw, 1, '#2b3d57').replace("<zone ", "<zone fixed-size='1' is-fixed='true' ", 1)
    foot_h = 30 if footer else 0
    body = body.replace("<zone ", f"<zone fixed-size='{ph - 45 - foot_h}' is-fixed='true' ", 1)
    k = body.rfind("</zone-style>")
    body = body[:k] + "  <format attr='padding-left' value='12' />\n" + body[k:]
    parts = [head, line, body]
    if footer:
        parts.append(text_zone(px, py + ph - 30, pw, 30, [(footer, '#8fa0b8', 9, 'Book')], fixed=30, pad=(6, 12, 0, 12)))
    x = flow(f'{name} Popover', px, py, pw, ph, parts, 'vert', bg=NAVY, radius_right=10)
    VIS[param] = re.search(r"friendly-name='" + name + r" Popover' [^>]*id='(\d+)'", x).group(1)
    return hide_all(x)


zones.append(popover('Period', 'p_PeriodOpen', 216, 132, 360, 470, 'Compare', sheet_zone('Pair List', 228, 177, 348, 395),
                     'Each choice compares a quarter-end with the same date a year before.'))
zones.append(popover('Org', 'p_OrgOpen', 216, 228, 360, 300, 'Organization', sheet_zone('Group List', 228, 273, 348, 225),
                     'Each function is its own bridge: its effects add up to its own change.'))
INFO = [('What is measured.', "Total workforce cost on a date: employees' loaded pay run-rate (base pay × FTE × (1 + the country's fringe rate)) plus contingent workers' annualized bill run-rate, converted to USD at the ECB rate on that date. It is a run-rate, not spend: what a year would cost at that day's workforce and pay."),
        ('The six factors.', 'Cost is people × the mix of people × what each costs × currency. Volume is the number of people; workforce mix the balance of employees and contingent workers; location mix the countries; level mix the grades (or contingent types); rate the cost per head at constant exchange rates; currency what exchange rates did to the reported cost.'),
        ('Why Shapley.', 'Moving the factors one at a time explains the change exactly, but the answer depends on the order: the factor moved first is valued at the old levels of the others. Shapley gives each factor its average effect over all 720 orders, so none is favored, and the six effects still add up to the change exactly. The card on the right shows how far one fixed order would drift.'),
        ('Limits.', 'Bonus, equity and allowances are not in the run-rate. A grade or country that appears on one date only counts as mix, never as rate.'),
        ('Data.', 'Arcadia Systems is fictional; all data is synthetic. Executive officers are excluded.')]
runs = []
for k, (lead, body) in enumerate(INFO):
    if k:
        runs.append(('\n\n', None, None, None))
    runs += [(lead + ' ', WHITE, 10, 'Semibold'), (body, '#b8c0cc', 10, 'Book')]
zones.append(popover('Info', 'p_InfoOpen', 216, 24, 591, 420, 'How the bridge works',
                     text_zone(228, 69, 579, 375, runs, pad=(12, 16, 0, 4)), None))

DASH_UID = uid()
dash = (f"  <dashboards>\n    <dashboard enable-sort-zone-taborder='true' name='{DASH}'>\n"
        "      <style>\n        <style-rule element='table'>\n          <format attr='background-color' value='#f3f3ef' />\n        </style-rule>\n      </style>\n"
        f"      <size maxheight='{H}' maxwidth='{W}' minheight='{H}' minwidth='{W}' sizing-mode='fixed' />\n      <zones>\n"
        + indent('\n'.join(zones), 8) + f"\n      </zones>\n      <simple-id uuid='{DASH_UID}' />\n    </dashboard>\n  </dashboards>\n")

# ===================================================================================================== actions


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
T = [('Open period popover', 'Period Field', 'p_PeriodOpen', 'Toggle Period Panel')]
T += [(f'Period closes {p}', 'Period Field', p, 'Close Panel') for p in ('p_OrgOpen', 'p_InfoOpen')]
T += [('Set pair', 'Pair List', 'p_Pair', 'Pair Offset'), ('Close period popover on pick', 'Pair List', 'p_PeriodOpen', 'Close Panel'),
      ('Period popover on x', 'Period Close', 'p_PeriodOpen', 'Close Panel'),
      ('Open org popover', 'Org Field', 'p_OrgOpen', 'Toggle Org Panel')]
T += [(f'Org closes {p}', 'Org Field', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_InfoOpen')]
T += [('Set group', 'Group List', 'p_Group', 'group_name'), ('Close org popover on pick', 'Group List', 'p_OrgOpen', 'Close Panel'),
      ('Org popover on x', 'Org Close', 'p_OrgOpen', 'Close Panel'),
      ('Reset pair', 'Reset', 'p_Pair', 'Zero Pair'), ('Reset group', 'Reset', 'p_Group', 'Default Group')]
T += [(f'Reset closes {p}', 'Reset', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_OrgOpen', 'p_InfoOpen')]
T += [('Open info', 'Info Button', 'p_InfoOpen', 'Toggle Info')]
T += [(f'Info closes {p}', 'Info Button', p, 'Close Panel') for p in ('p_PeriodOpen', 'p_OrgOpen')]
T += [('Info popover on x', 'Info Close', 'p_InfoOpen', 'Close Panel')]
PA = []
for cap, sheet, target, field in T:
    if field in m.calcs:
        how = 'agg' if m.level(field) == 'agg' else ('ord' if m.role(field)[1] == 'ordinal' else 'dim')
    else:
        how = 'dim'
    PA.append(f"<edit-parameter-action caption='{cap}' name='{action_id(cap)}'>\n  <activation type='on-select' />\n"
              f"  <source dashboard='{DASH}' type='sheet' worksheet='{xesc(sheet)}' />\n  <agg-type type='attr' />\n"
              f"  <clear-option type='do-nothing' value='b:false' />\n  <params>\n"
              f"    <param name='source-field' value='{m.ref(field, how)}' />\n"
              f"    <param name='target-parameter' value='[Parameters].[{m.pid[target]}]' />\n  </params>\n</edit-parameter-action>")
acts += PA          # every <action> before any <edit-parameter-action>
out = out.replace("  <worksheets>\n", "  <actions>\n" + indent('\n'.join(acts), 4) + "\n  </actions>\n  <worksheets>\n", 1)
for sh in SHEETS.values():         # a field on Rows or Columns is never repeated on the Tooltip shelf
    for i, pn in enumerate(sh.panes):
        for r in re.findall(r"<tooltip column='([^']+)' />", pn):
            if r in sh.rows or r in sh.cols:
                pn = pn.replace(f"<tooltip column='{r}' />", '')
        sh.panes[i] = re.sub(r'\n\s*\n', '\n', pn)
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
vps = '\n'.join(f"    <viewpoint name='{xesc(n)}'>\n      <zoom type='{'fit-width' if n in LISTS else 'entire-view'}' />\n    </viewpoint>" for n in sorted(names))
dwin = (f"<window class='dashboard' maximized='true' name='{DASH}'>\n  <viewpoints>\n{vps}\n  </viewpoints>\n"
        f"  <active id='-1' />\n  <simple-id uuid='{uid()}' />\n</window>")
out = re.sub(r"<window class='worksheet' maximized='true' name=", "<window class='worksheet' name=", out)
out = out.replace("  </windows>\n", indent('\n'.join(ws_window(n) for n in names) + '\n' + dwin, 4) + "\n  </windows>\n", 1)

nodes, pairs, edges = [], [], []
for p, zid_ in VIS.items():
    pn, pin, pout, zn, zin = (str(uuid.uuid4()) for _ in range(5))
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
print('calcs', len(m.order), 'sheets', len(SHEETS), 'actions', len(acts), f'({len(PA)} parameter)')
