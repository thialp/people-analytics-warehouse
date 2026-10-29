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
PALE, MIST, AXIS, GRID = '#e4e9f0', '#b9c3d1', '#8c9bb0', '#e7e3dd'
PLUM, SAND, SAND_D, LEVEL = '#5b3a63', '#c2a878', '#8a6a35', '#9aa5b4'
PAPER, RULE, TRACK = '#f6f4f1', '#e0dcd6', '#ece8e2'
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


# ===================================================================================================== headline
s = new('Page Title')
s.pane('Text', enc=ZZ, valign='top', label=[
    [('WORKFORCE COST BRIDGE', 'semi', 10, PLUM)],
    [('{Head Verb}', 'bold', 20, INK), ('{S Change Abs Txt}', 'bold', 20, PLUM), (' to ', 'bold', 20, INK), ('{S Closing Txt}', 'bold', 20, PLUM),
     ('{Head Mid}', 'bold', 20, INK), ('{Head Pct}', 'bold', 20, PLUM), ('{Head Of}', 'bold', 20, INK), ('{Head Driver}', 'bold', 20, PLUM)],
    [('{From Date Text|attr}', 'semi', 11, NAVY), (' to ', 'book', 11, SLATE), ('{To Date Text|attr}', 'semi', 11, NAVY),
     (' · {S Change Pct Str} · {Scope Words|attr} · {S HC Open Str} to {S HC Close Str} people · nominal USD', 'book', 11, SLATE)]])

# ===================================================================================================== factor ribbon
RIB_TIP = [[('{Rib Name}: ', 'semi', 11, NAVY), ('{Rib Val Adds}', 'bold', 11, PLUM), ('{Rib Val Takes}', 'bold', 11, SAND_D)],
           [('{Rib Share Txt}', 'semi', 10, NAVY)], [('{factor_meaning|attr}', 'book', 10, INK)], [('{Rib Tip Extra}', 'book', 9, SLATE)]]


def ribbon(name):
    s = new(name)
    s.filter_member('In Selection', 'true')
    s.filter_member('Is Factor', 'true')
    ro = s.f('Ribbon Order', 'ord')
    s.cols = ro
    s.hide_labels.append(ro)
    return s, ro


s, ro = ribbon('Ribbon Top')
s.pane('Text', enc=ZZ + [('color', 'Cell Kind', 'agg')], valign='top', tooltip=RIB_TIP,
       label=[[('  {Rib Name}', 'book', 9, SLATE)], [('  {Rib Value}', 'bold', 20, None)]])
s, ro = ribbon('Ribbon Bars')
z0 = s.f('Rib Zero', 'agg')
s.cols = f'({ro} / {z0})'
axis_rules = [f"<encoding attr='space' class='0' field='{z0}' field-type='quantitative' max='1.07' min='-0.07' range-type='fixed' scope='cols' type='space' />",
              f"<format attr='display' class='0' field='{z0}' scope='cols' value='false' />", "<format attr='tick-color' value='#00000000' />"]
s.axis_rules += axis_rules
s.pane('GanttBar', enc=ZZ + [('color', 'Rib Bar Kind', 'agg'), ('size', 'Rib Bar Size', 'agg')], size='0.6', transparency='255',
       stroke='false', tooltip=RIB_TIP, refs=s.refband(0, z0, 0, 1, TRACK))
s, ro = ribbon('Ribbon Note')
s.pane('Text', enc=ZZ, valign='top', label=[[('  {Rib Note}', 'book', 9, SLATE)]])

# ===================================================================================================== bridge
s = new('Bridge Title')
s.pane('Text', enc=ZZ, valign='top', label=[
    [('From ', 'bold', 13, NAVY), ('{S Opening Txt}', 'bold', 13, SLATE), (' to ', 'bold', 13, NAVY), ('{S Closing Txt}', 'bold', 13, PLUM),
     (', one factor at a time', 'bold', 13, NAVY)],
    [("Each factor's average effect over every order of the six steps, $M; the axis starts at ", 'book', 10, SLATE),
     ('{Floor Text|attr}', 'semi', 10, NAVY), (' so the factors are visible', 'book', 10, SLATE)]])

s = new('Bridge', deselect=False)
s.filter_member('In Selection', 'true')
fo, fh, fs = s.f('factor_order', 'ord'), s.f('Factor Head', 'dim'), s.f('Factor Sub', 'dim')
s.cols = f'({fo} / ({fh} / {fs}))'
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
no_field_labels(s, 'cols')
s.grid_rows = GRID
floor = s.f('Floor Mark', 'agg')
TIP = [[('{Tip Head} ', 'semi', 11, NAVY), ('{Tip Value Level}', 'bold', 11, NAVY), ('{Tip Value Adds}', 'bold', 11, PLUM),
        ('{Tip Value Takes}', 'bold', 11, SAND_D)],
       [('{factor_meaning|attr}', 'book', 10, INK)], [('{Tip Share}', 'semi', 10, NAVY)], [('{Tip Order}', 'book', 9, SLATE)]]
s.pane('Automatic', pane_id=2, enc=[('lod', 'Floor Mark', 'agg')], refs=[s.refline(0, top, floor, '#d5dbe4', 1)])
s.pane('GanttBar', pane_id=3, y_axis=top, order=ORDER, size='2.5', transparency='255', stroke='false', tooltip=TIP,
       enc=[('color', 'Bar Kind', 'agg'), ('size', 'Bar Size', 'tc', ORDER), ('lod', 'Floor Mark', 'agg')])
s.pane('Text', pane_id=4, y_axis=ly, order=ORDER, align='center', valign='center', tooltip=TIP,
       enc=[('color', 'Label Kind', 'agg'), ('lod', 'Floor Mark', 'agg')],
       label=[[('{Bar Label}', 'bold', 10, None)]])

# ===================================================================================================== order of the steps
s = new('Bias Title')
s.pane('Text', enc=ZZ, valign='top', label=[
    [('{Bias Lead}', 'bold', 13, NAVY), ('{Bias Amount}', 'bold', 13, PLUM)],
    [('Shapley vs one fixed order (volume first, currency last), $M', 'book', 10, SLATE)]])


def bias_sheet(name, deselect=True):
    s = new(name, deselect)
    s.filter_member('In Selection', 'true')
    s.filter_member('Is Factor', 'true')
    fo = s.f('factor_order', 'ord')
    s.rows = fo
    s.hide_labels.append(fo)
    s.row_dividers = GRID
    return s


bias_sheet('Bias Names').pane('Text', enc=ZZ, align='left', label=[[('{Factor Head}', 'book', 10, INK)]])
bias_sheet('Bias Shapley').pane('Text', enc=ZZ, align='right', label=[[('{Bias Shap Txt}', 'semi', 10, NAVY)]])
bias_sheet('Bias Seq').pane('Text', enc=ZZ, align='right', label=[[('{Bias Seq Txt}', 'book', 10, SLATE)]])
bias_sheet('Bias Num').pane('Text', enc=ZZ + [('color', 'Bias Label Kind', 'agg')], align='right', label=[[('{Bias Text}', 'semi', 10, None)]])
s = bias_sheet('Bias Bars', deselect=False)
bx = s.f('Bias M', 'sum')
s.cols = bx
s.axis_rules += [f"<format attr='display' class='0' field='{bx}' scope='cols' value='false' />", "<format attr='tick-color' value='#00000000' />"]
s.zeroline = '#d5dbe4'
ap, an = s.f('Bias Axis', 'min'), s.f('Bias Axis Neg', 'min')
refs = [s.refline(0, bx, ap, '#00000000', 0), s.refline(1, bx, an, '#00000000', 0)]
s.pane('Bar', enc=[('color', 'Bias Kind', 'agg'), ('lod', 'Bias Axis', 'min'), ('lod', 'Bias Axis Neg', 'min')], refs=refs,
       size='0.5', transparency='255', stroke='false', labels_show=False,
       tooltip=[[('{Factor Head|attr}', 'semi', 10, NAVY)],
                [('Shapley ', 'book', 10, INK), ('{Bias Shap Txt}', 'semi', 10, NAVY), (' · one fixed order ', 'book', 10, INK),
                 ('{Bias Seq Txt}', 'semi', 10, SLATE), (' · bias ', 'book', 10, INK), ('{Bias Text}', 'bold', 10, PLUM)]])

# ===================================================================================================== five fiscal years
s = new('Year Title')
s.pane('Text', enc=ZZ, valign='top', label=[
    [('{Year Title|attr}', 'bold', 13, NAVY)],
    [('In ', 'book', 10, SLATE), ('{Quiet FY|attr}', 'semi', 10, NAVY), (' headcount changed by only ', 'book', 10, SLATE),
     ('{Quiet HC Txt|attr}', 'semi', 10, NAVY), ('{Quiet Verb|attr}', 'book', 10, SLATE), ('{Quiet Change Txt|attr}', 'bold', 10, PLUM)]])

s = new('Year Table', deselect=False)
s.filter_member('Year Row', 'true')
fy, yl = s.f('fiscal_year', 'ord'), s.f('Year Row Label', 'dim')
co, cn = s.f('Table Col Order', 'ord'), s.f('Table Column', 'dim')
s.rows, s.cols = f'({fy} / {yl})', f'({co} / {cn})'
s.hide_labels += [fy, co]
s.styles.append(f"<style-rule element='label'>\n  <format attr='font-size' field='{yl}' value='10' />\n  <format attr='color' field='{yl}' value='{NAVY}' />\n"
                f"  <format attr='font-size' field='{cn}' value='9' />\n  <format attr='color' field='{cn}' value='{SLATE}' />\n</style-rule>")
no_field_labels(s, 'rows'); no_field_labels(s, 'cols')
s.row_dividers = GRID
s.pane('Text', enc=[('color', 'Cell Kind', 'agg')], align='right',
       label=[[('{Cell Text Hi}', 'bold', 10, None), ('{Cell Text Lo}', 'book', 10, None)]],
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
        label=[[('   {Period Field Text}', 'semi', 10, NAVY)]], tip='Choose the two dates to compare')
for nm, lab in (('Date This', [[('{To Date Text|attr}', 'semi', 9, WHITE)]]), ('Date Against', [[('{From Date Text|attr}', 'semi', 9, WHITE)]]),
                ('Date Span', [[('{Span Line 1|attr}', 'book', 9, MIST)], [('{Span Line 2|attr}', 'book', 9, MIST)]])):
    new(nm).pane('Text', enc=ZZ, label=lab, valign='top')
control('Org Field', shape_field='Org Capsule Shape', lod=('Toggle Org Panel', 'Close Panel'),
        label=[[('   {Org Text Light}', 'semi', 10, NAVY), ('{Org Text Dark}', 'medium', 10, PALE2)]],
        tip='Choose all of Arcadia or one function')
control('Org Sub', mark='Text', label=[[('{Org Sub Text}', 'book', 9, '#8a97a8')]])
control('Reset', shape='Arcadia D4/d4_reset.png', lod=('Zero Pair', 'Default Group', 'Close Panel'), size='10',
        tip='Reset to default view', align='center')
control('Info Button', shape_field='Info Shape', lod=('Toggle Info', 'Close Panel'), size='2', align='center',
        tip='How the bridge works')
control('Rail As Of', mark='Text', label=[[('{Rail Line 1|attr}', 'semi', 9, PALE2)], [('USD at month-end ECB rates', 'book', 8, MIST)],
                                          [('Employees and contingent workers', 'book', 8, MIST)]])
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
           label=label, size='1.8', transparency='255', stroke='false', align='right',
           extra_mark_fmt="<format attr='mark-labels-mode' value='all' />")
    return s


lst('Pair List', ['Pair Offset'], 'Pair Option Row', 'Pair Shape',
    [[('  {Pair Option Name}', 'book', 10, PALE2), ('   {Pair Option Date}', 'book', 9, MUTED)]], ['Pair Offset', 'Close Panel'])
lst('Group List', ['Group Key'], 'Group Option Row', 'Group Shape',
    [[('  {Group Option Name}', 'book', 10, PALE2), ('   {Group Option People}', 'book', 9, MUTED)]], ['group_name', 'Close Panel'])


# ===================================================================================================== datasource
def bucket_map(field, kind, mapping):
    ms = '\n'.join(f"  <map to='{to}'>\n    <bucket>&quot;{xesc(b)}&quot;</bucket>\n  </map>" for b, to in mapping)
    return f"<encoding attr='{kind}' field='{field}' type='{'palette' if kind == 'color' else 'shape'}'>\n{ms}\n</encoding>"


styled, enc_rules = [], []
for n, cols in (('Bar Kind', [('level', LEVEL), ('adds', PLUM), ('takes away', SAND)]),
                ('Label Kind', [('level', NAVY), ('adds', PLUM), ('takes away', SAND_D)]),
                ('Bias Kind', [('adds', PLUM), ('takes away', SAND), ('small', '#d5dbe4')]),
                ('Rib Bar Kind', [('adds', PLUM), ('takes away', SAND)]),
                ('Bias Label Kind', [('adds', PLUM), ('takes away', SAND_D), ('small', AXIS)])):
    enc_rules.append(bucket_map(m.inst(n, 'agg')[0], 'color', cols)); styled.append((n, 'agg'))
# Cell Kind colors text (ribbon values, table) in dark sand; the ribbon bars use their own field so sand stays light there
enc_rules.append(bucket_map(m.inst('Cell Kind', 'agg')[0], 'color', [('adds', PLUM), ('takes away', SAND_D)])); styled.append(('Cell Kind', 'agg'))
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


zones = [sheet_zone('Page Title', 240, 12, 1136, 94)]
zones.append(rule_zone(240, 114, 1136, 2, PLUM))
zones += [sheet_zone('Ribbon Top', 240, 124, 1136, 64), sheet_zone('Ribbon Bars', 240, 194, 1136, 10),
          sheet_zone('Ribbon Note', 240, 208, 1136, 22)]
zones.append(rule_zone(240, 240, 1136, 1, RULE))
for k in range(1, 6):
    zones.append(rule_zone(round(240 + k * 1136 / 6), 126, 1, 108, RULE))
zones.append(rule_zone(240, 258, 708, 2, PLUM))
zones += [sheet_zone('Bridge Title', 240, 268, 708, 52), sheet_zone('Bridge', 240, 324, 708, 462)]
zones.append(text_zone(240, 792, 708, 18, [('Plum adds cost', PLUM, 9, 'Semibold'), (', ', SLATE, 9, 'Book'),
                                            ('sand takes it away', SAND_D, 9, 'Semibold'),
                                            ('; the six effects add up to the change exactly.', SLATE, 9, 'Book')]))
zones.append(rule_zone(988, 258, 388, 2, PLUM))
zones.append(sheet_zone('Bias Title', 988, 268, 388, 52))
for (lbl, x0, w0, al) in (('Factor', 988, 104, 'left'), ('Shapley', 1092, 64, 'right'), ('Fixed order', 1156, 72, 'right'), ('Bias', 1228, 48, 'right')):
    zones.append(text_zone(x0, 326, w0, 16, [(lbl, AXIS, 9, 'Book')])
                 .replace("<run fontcolor", f"<run fontalignment='{ {'left': 0, 'center': 1, 'right': 2}[al] }' fontcolor", 1))
for name, x0, w0 in (('Bias Names', 988, 104), ('Bias Shapley', 1092, 64), ('Bias Seq', 1156, 72), ('Bias Num', 1228, 48), ('Bias Bars', 1280, 96)):
    zones.append(sheet_zone(name, x0, 344, w0, 150))
zones.append(rule_zone(988, 512, 388, 2, PLUM))
zones += [sheet_zone('Year Title', 988, 522, 388, 70), sheet_zone('Year Table', 988, 594, 388, 194), sheet_zone('Year Note', 988, 792, 388, 18)]
zones.append(text_zone(240, 828, 1136, 16, [(
    'Arcadia Systems is fictional; all data is synthetic. Executive officers excluded. Effects are Shapley values: each '
    "factor's average effect over every order of the six steps, so they add up to the change.", SLATE, 9, 'Book')]))
zones.append(rule_zone(0, 0, 216, 850, NAVY))
zones.append(image_zone(D4IMG + 'arcadia_logo_horizontal_reverse.png', 12, 24, 156, 40))
zones.append(sheet_zone('Info Button', 178, 30, 28, 28))
for lbl, y in (('COMPARE', 100), ('ORGANIZATION', 270)):
    zones.append(text_zone(12, y, 192, 16, [(lbl, '#b8c4d6', 8, 'Semibold')], pad=(0, 0, 0, 4)))
zones.append(sheet_zone('Period Field', 12, 120, 192, 34))
for key, sheet, y, h in (('This', 'Date This', 168, 20), ('Against', 'Date Against', 188, 20), ('Span', 'Date Span', 208, 34)):
    zones.append(text_zone(12, y, 62, h, [(key, MUTED, 9, 'Book')], pad=(3, 0, 0, 4)))
    zones.append(sheet_zone(sheet, 74, y, 138, h))
zones += [sheet_zone('Org Field', 12, 290, 192, 34), sheet_zone('Org Sub', 12, 330, 192, 18),
          image_zone(D4IMG + 'arcadia_rail_divider.png', 12, 364, 192, 24), sheet_zone('Reset', 12, 400, 192, 32),
          sheet_zone('Rail As Of', 12, 762, 192, 60)]

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


zones.append(popover('Period', 'p_PeriodOpen', 216, 156, 360, 470, 'Compare', sheet_zone('Pair List', 228, 201, 348, 395),
                     'Each choice compares a quarter-end with the same date a year before.'))
zones.append(popover('Org', 'p_OrgOpen', 216, 326, 360, 300, 'Organization', sheet_zone('Group List', 228, 371, 348, 225),
                     'Each function is its own bridge: its effects add up to its own change.'))
INFO = [('What is measured.', "Total workforce cost on a date: employees' loaded pay run-rate (base pay × FTE × (1 + the country's fringe rate)) plus contingent workers' annualized bill run-rate, converted to USD at the ECB rate on that date. It is a run-rate, not spend: what a year would cost at that day's workforce and pay."),
        ('The six factors.', 'Cost is people × the mix of people × what each costs × currency. Volume is the number of people; workforce mix the balance of employees and contingent workers; location mix the countries; level mix the grades (or contingent types); rate the cost per head at constant exchange rates; currency what exchange rates did to the reported cost.'),
        ('Why Shapley.', 'Moving the factors one at a time explains the change exactly, but the answer depends on the order: the factor moved first is valued at the old levels of the others. Shapley gives each factor its average effect over all 720 orders, so none is favored, and the six effects still add up to the change exactly. The table on the right shows how far one fixed order would drift.'),
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
        "      <style>\n        <style-rule element='table'>\n          <format attr='background-color' value='#f6f4f1' />\n        </style-rule>\n      </style>\n"
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
