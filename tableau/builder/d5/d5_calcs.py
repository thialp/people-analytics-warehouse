"""Every Dashboard #5 calculation: the guide's code blocks, plus the fields the guide describes in prose."""
import re
from parse_guide import parse

SKIP = {'Comma Pattern'}


def comma(x):
    return (f'IF ISNULL({x}) THEN "–"\n'
            f'ELSEIF ROUND({x}, 0) >= 1000 THEN STR(DIV(INT(ROUND({x}, 0)), 1000)) + "," + RIGHT("00" + STR(INT(ROUND({x}, 0)) % 1000), 3)\n'
            f'ELSE STR(INT(ROUND({x}, 0))) END')


def pct(x):
    return f'STR(INT(ROUND({x} * 100, 0))) + "%"'


def all_calcs():
    g = parse()
    g['BT Title'] = g['BT Title'].replace('STR([BT In Count])', 'STR(INT([BT In Count]))')
    g['Axis Pad'] = 'MIN(1000)'
    g['Hero Line 3'] = '[F Att Str] + " of the " + [P Plan Str] + " in the " + [Fwd FY] + " Budget · " + [Compare Label] + " filled " + [H Fills Compare Str] + " (" + [H Att Compare Str] + ")"'
    g['KPI 2 Title'] = '"Vacant at the end of " + (IF [Is Year] THEN [Fwd FY] ELSE "Q" + STR([Period Start]) END)'
    # every line fits its card when a quarter is chosen
    g['Waiting Text'] = '[F Waiting Str] + (IF [Period Start] = 1 THEN " waiting today" ELSE " waiting as Q" + STR([Period Start]) + " opens" END)'
    g['Vacant Change Text'] = g['Vacant Change Text'].replace('" than as the quarter opens"', '" than as Q" + STR([Period Start]) + " opens"')
    g['Hero Line 3'] = g['Hero Line 3'].replace('\n+ (IF [Is Year] THEN "" ELSE " for " + [Period Quarter Label] END)', '')
    g['BT Subtitle'] = g['BT Subtitle'].replace('"Forecast range one quarter ahead, against what happened · "', '"Forecast one quarter ahead · "')
    g['Quota From'] = '([chart_point] - 1) * 0.25'
    g['Quota Width'] = '0.25'
    g['Quota Att'], g['Quota Lo'], g['Quota Hi'] = '[L Att]', '[L Att Lo]', '[L Att Hi]'
    # no table calculation reads another (nested ones lose their Compute Using): inline them
    TC = ['SV Filled Share', 'SV Median Days', 'SV Within 90', 'BT In Count', 'BT Error']
    for n in ('SV Median Days Str', 'SV Within 90 Str', 'KPI 3 Tip 1', 'BT Title', 'BT Subtitle'):
        for _ in range(3):
            for tcn in TC:
                g[n] = g[n].replace(f'[{tcn}]', '(' + g[tcn].strip() + ')')
    out = [(k, v) for k, v in g.items() if k not in SKIP]
    names = [k for k, _ in out]

    def after(anchor, items):
        i = names.index(anchor) + 1
        for k, v in items:
            out.insert(i, (k, v)); names.insert(i, k); i += 1

    # 5.4 comma-pattern strings
    after('F Band', [
        ('F Fills Str', comma('[F Fills]')), ('F Fills Lo Str', comma('[F Fills Lo]')), ('F Fills Hi Str', comma('[F Fills Hi]')),
        ('F To Fill Str', comma('[F To Fill]')), ('F To Fill Lo Str', comma('[F To Fill Lo]')), ('F To Fill Hi Str', comma('[F To Fill Hi]')),
        ('F Vacant Str', comma('[F Vacant]')), ('F Vacant Lo Str', comma('[F Vacant Lo]')), ('F Vacant Hi Str', comma('[F Vacant Hi]')),
        ('F Waiting Str', comma('[F Waiting]')),
        ('F Backfill Str', comma('(SUM([D Opened Backfill]) / [Draws])')),
        ('F Net New Str', comma('(SUM([D Opened Net New]) / [Draws])')),
        ('F Immediate Str', comma('(SUM([D Opened Immediate]) / [Draws])')),
        ('P Plan Str', comma('[P Plan]')), ('H Fills Compare Str', comma('[H Fills Compare]')),
    ])
    after('F Att Str', [('F Att Lo Str', pct('[F Att Lo]')), ('F Att Hi Str', pct('[F Att Hi]')),
                        ('H Att Compare Str', pct('[H Att Compare]'))])
    after('Quota Hi', [('Quota Band Text', 'IF [chart_point] = 5 THEN "100%+" ELSE STR(([chart_point] - 1) * 25) + "%" END'),
                       ('Quota Att Mark', 'MIN([Quota Att])'), ('Quota Lo Mark', 'MIN([Quota Lo])'),
                       ('Quota Hi Mark', 'MIN([Quota Hi])')])
    # 7.3 / 7.5
    after('Pace Change', [('Quarter Low Str', comma('ROUND([Quarter Low], -1)')),
                          ('Quarter High Str', comma('ROUND([Quarter High], -1)'))])
    after('Q P90', [(f'{q} Str', comma(f'[{q}]')) for q in
                    ('Q Filled', 'Q Budget', 'Q Vacant', 'Q Forecast', 'Q Forecast Vacant', 'Q P10', 'Q P90')])
    after('Axis Pad', [('Chip Row', '[Budget Row] AND [fiscal_quarter] = 2 AND [chart_point] % 2 = 1'),
                       ('Quarter Tick X', '[chart_x] + 0.5'),
                       ('Year Under', 'IF [fiscal_quarter] = 1 THEN [fiscal_year_label] END')]
          + [(f'Ref X{v}', f'MIN({v}.0)') for v in (4, 8, 12, 16, 20)])
    after('SV Within 90 Str', [('Days Plus One', 'MIN([days_to]) + 1')]
          + [(f'Ref D{v}', f'MIN({v + 1}.0)') for v in (29, 59, 89)])
    # backtest drawn on scaffold rows: the range and the average are two Gantt marks of the same width
    after('BT Subtitle', [
        ('QBT Mean', '{ FIXED [quarter_offset] : SUM(IF [BT Row] THEN [filled_mean] END) }'),
        ('QBT Var', '{ FIXED [quarter_offset] : SUM(IF [BT Row] THEN [filled_var] END) }'),
        ('QBT CV', '{ FIXED [quarter_offset] : MIN(IF [BT Row] THEN [filled_shared_cv] END) }'),
        ('QBT Actual', '{ FIXED [quarter_offset] : SUM(IF [BT Row] THEN [actual_filled] END) }'),
        ('QBT SD', 'SQRT([QBT Var] + POWER([QBT CV] * [QBT Mean], 2))'),
        ('QBT Low', 'IF [QBT Mean] - 1.2816 * [QBT SD] < 0 THEN 0 ELSE [QBT Mean] - 1.2816 * [QBT SD] END'),
        ('QBT High', '[QBT Mean] + 1.2816 * [QBT SD]'),
        ('QBT Span Max', '{ MAX([QBT High] - [QBT Low]) }'),
        ('BTS Row', '[Is Scaffold] AND ([chart_series] = "Filled" OR [chart_series] = "Budget") AND NOT ISNULL([QBT Actual])'),
        ('BTS Part', 'IF [chart_series] = "Filled" THEN "range" ELSE "average" END'),
        ('BTS Y', 'IF [chart_series] = "Filled" THEN [QBT Low] ELSE [QBT Mean] - [QBT Span Max] * 0.008 END'),
        ('BTS Size', 'IF [chart_series] = "Filled" THEN [QBT High] - [QBT Low] ELSE [QBT Span Max] * 0.016 END'),
        ('BTS Actual', 'IF [chart_series] = "Filled" THEN [QBT Actual] END'),
        ('BTS In', 'IF [QBT Actual] >= [QBT Low] AND [QBT Actual] <= [QBT High] THEN "in range" ELSE "outside" END'),
    ])
    # 9
    after('BT Error', [('BT Is Last', 'LAST() = 0')])
    # 10
    after('Org Text Dark', [('Loc Text Light', 'IF NOT [Loc Is All] THEN [Loc Field Text] END'),
                            ('Loc Text Dark', 'IF [Loc Is All] THEN [Loc Field Text] END')])
    # 11 list shapes and names
    lst = []
    for lvl, dim in (('Function', 'function_name'), ('Dept', 'department_name'), ('Region', 'region'),
                     ('Country', 'country_name'), ('Office', 'office_name')):
        if lvl in ('Function', 'Region'):
            lst.append((f'{lvl} Shape', f'IF [{lvl} Tick] = "on" THEN "d4_tick_on" ELSE "d4_tick_off" END'))
            lst.append((f'{lvl} Name On', f'IF [{lvl} Tick] <> "dim" THEN MIN([{dim}]) END'))
            lst.append((f'{lvl} Name Dim', f'IF [{lvl} Tick] = "dim" THEN MIN([{dim}]) END'))
        else:
            lst.append((f'{lvl} Shape', f'IF [{lvl} Tick] = "on" OR [{lvl} Tick] = "locked" THEN "d4_tick_on" ELSE "d4_tick_off" END'))
            lst.append((f'{lvl} Name On', f'IF [{lvl} Tick] = "on" OR [{lvl} Tick] = "off" THEN MIN([{dim}]) END'))
            lst.append((f'{lvl} Name Locked', f'IF [{lvl} Tick] = "locked" THEN MIN([{dim}]) END'))
            lst.append((f'{lvl} Name Dim', f'IF [{lvl} Tick] = "dim" THEN MIN([{dim}]) END'))
    lst.append(('Period Shape', 'IF [quarter_offset] = [p_Period] THEN "d4_tick_on" ELSE "d4_tick_off" END'))
    lst.append(('Close X', '"✕"'))
    lst.append(('Tip Waiting Words', 'IF [Period Start] = 1 THEN " waiting today" ELSE " waiting as Q" + STR([Period Start]) + " opens" END'))
    lst.append(('Tip Span Word', 'IF [Is Year] THEN "year." ELSE "quarter." END'))
    lst.append(('Line Tip Head', 'IF [chart_series] = "Filled" OR ([chart_series] = "Forecast" AND [quarter_offset] > 0) '
                'THEN [quarter_label] + ", " + [quarter_months_label] + ": " ELSEIF [chart_series] = "Budget" THEN [quarter_label] + " budget: " END'))
    lst.append(('Line Tip Body', 'IF [chart_series] = "Filled" THEN [Q Filled Str] + " PIDs filled, " + STR(INT(ROUND([Q Filled] / [Q Budget] * 100, 0))) '
                '+ "% of the quarter\'s budget of " + [Q Budget Str] + "." '
                'ELSEIF [chart_series] = "Forecast" AND [quarter_offset] > 0 THEN "about " + [Q Forecast Str] + " fills forecast, likely " '
                '+ [Q P10 Str] + " to " + [Q P90 Str] + "." ELSEIF [chart_series] = "Budget" THEN [Q Budget Str] + " planned fills." END'))
    lst.append(('Tick X', 'MIN(0.6)'))
    lst.append(('List Tick X', 'MIN(9.4)'))
    after('Period Option Text', lst)
    return out


FORMATS = {}
for n in ('F Fills', 'F Fills Lo', 'F Fills Hi', 'F To Fill', 'F To Fill Lo', 'F To Fill Hi', 'F Vacant', 'F Vacant Lo',
          'F Vacant Hi', 'F Waiting', 'P Plan', 'H Fills Compare', 'V Now', 'F Vacant Change', 'BT Low', 'BT High',
          'BT Actual', 'BT Mean', 'Bridge Label Plain', 'Q Filled', 'Q Budget', 'Line Y', 'Fan Y', 'End Label',
          'SV Median Days', 'Axis Pad', 'QBT Low', 'QBT High', 'QBT Actual', 'QBT Mean', 'BTS Y', 'BTS Actual'):
    FORMATS[n] = 'n#,##0;-#,##0'
for n in ('Quota From', 'F Att', 'F Att Lo', 'F Att Hi', 'H Att Compare', 'FY Att', 'SV Filled Share', 'SV Within 90'):
    FORMATS[n] = 'p0%'
FORMATS['Bridge Label Plus'] = '*+#,##0;-#,##0'
FORMATS['Bridge Label Minus'] = '*"−"#,##0'

DTYPES = {'Zero Period': 'integer', 'Period Start': 'integer', 'Period End': 'integer', 'Legend Col': 'integer',
          'Legend Row': 'integer', 'Quota From': 'real', 'Quota Width': 'real', 'Period From': 'integer',
          'Period To': 'integer', 'Draws': 'integer', 'L Draws': 'integer', 'BT Low': 'real'}
ROLES = {'Legend Col': ('dimension', 'ordinal'), 'Legend Row': ('dimension', 'ordinal'), 'Zero Period': ('dimension', 'ordinal')}

if __name__ == '__main__':
    for k, v in all_calcs():
        print(k)
