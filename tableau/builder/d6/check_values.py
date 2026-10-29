"""Every value the Workforce Cost Bridge page shows, computed from the growth-mix mart the way the page computes it.

  python3 tableau/builder/d6/check_values.py            # markdown tables for the build guide's section 13
  python3 tableau/builder/d6/check_values.py --verify   # the guide's own checks: closures, axis floor, text rules

Reads data/marts/mart_workforce_cost_growth_mix.csv (the same rows as tableau/custom_sql_workforce_cost_growth_mix.sql).
Arcadia Systems is fictional; all data is synthetic.
"""
import csv
import math
import os
import sys
from collections import defaultdict
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
MART = os.path.join(ROOT, 'data', 'marts', 'mart_workforce_cost_growth_mix.csv')
MINUS = '−'
FACTORS = ['Volume', 'Workforce mix', 'Location mix', 'Level mix', 'Rate', 'Currency']
SHORT = {'Volume': 'volume', 'Workforce mix': 'workforce', 'Location mix': 'location', 'Level mix': 'level',
         'Rate': 'rate', 'Currency': 'currency'}


def comma(n):
    return f'{n:,}'


def m1(x):
    """$M with one decimal and a comma, no sign: 4,648.1"""
    v = round(abs(x) / 1e6, 1)
    whole = int(v)
    dec = int(round((v - whole) * 10))
    return f'{comma(whole)}.{dec}'


def money(x):
    return f'${m1(x)}M'


def smoney(x):
    return ('+' if round(x / 1e6, 1) >= 0 else MINUS) + money(x)


def snum(x):
    return ('+' if round(x / 1e6, 1) >= 0 else MINUS) + m1(x)


def whole_m(x):
    a = abs(x) / 1e6
    return f'${a:.1f}M' if round(a, 1) < 10 else f'${comma(int(round(a)))}M'


def pct(x):
    return f'{int(round(x * 100))}%'


def spct(x):
    v = round(x * 100, 1)
    return ('+' if v >= 0 else MINUS) + f'{abs(v):.1f}%'


def date_words(d):
    return d.strftime('%b') + f' {d.day}, {d.year}'


def fy(n):
    return f'FY{n % 100:02d}'


def driver_words(f, v):
    return {'Volume': 'more people' if v >= 0 else 'fewer people',
            'Workforce mix': 'the employee and contingent mix',
            'Location mix': 'the country mix',
            'Level mix': 'the grade mix',
            'Rate': 'higher rates' if v >= 0 else 'lower rates',
            'Currency': 'exchange rates'}[f]


def load():
    rows = list(csv.DictReader(open(MART, encoding='utf-8')))
    latest = max(date.fromisoformat(r['to_month_end']) for r in rows)
    pairs = defaultdict(dict)
    for r in rows:
        to = date.fromisoformat(r['to_month_end'])
        off = (latest.year - to.year) * 4 + (latest.month - to.month) // 3
        key = (off, r['group_name'])
        p = pairs[key]
        p.update(to=to, frm=date.fromisoformat(r['from_month_end']), fy=int(r['fiscal_year']),
                 q=r['fiscal_quarter_label'][-2:], view=r['view_name'], view_order=int(r['view_order']),
                 hc0=int(r['opening_headcount']), hc1=int(r['closing_headcount']))
        p.setdefault('shap', {})[r['factor']] = float(r['shapley_effect_usd'])
        p.setdefault('seq', {})[r['factor']] = float(r['sequential_effect_usd'])
        p.setdefault('bias', {})[r['factor']] = float(r['order_bias_usd'])
    return pairs


def page(p, off):
    s = p['shap']
    o, c = s['Opening cost'], s['Closing cost']
    chg = c - o
    is_year = p['q'] == 'Q4'  # the fiscal year's last quarter reads as the year (guide 4.3)
    to_lab = fy(p['fy']) + ('' if is_year else ' ' + p['q'])
    from_lab = fy(p['fy'] - 1) + ('' if is_year else ' ' + p['q'])
    vol = s['Volume']
    mix = s['Workforce mix'] + s['Location mix'] + s['Level mix']
    out = {}
    out['pair'] = to_lab + ' vs ' + from_lab
    out['span'] = date_words(p['frm']) + ' to ' + date_words(p['to'])
    out['k1'] = (f'Total cost, {to_lab}', money(c), f'{smoney(chg)} vs {from_lab} ({spct(chg / o)})')
    share = vol / chg if chg else None
    hc = p['hc1'] - p['hc0']
    hc_txt = 'headcount ' + ('+' if hc >= 0 else MINUS) + comma(abs(hc))
    line = (pct(share) + ' of the change · ' + hc_txt) if share is not None and 0 <= share <= 1 else hc_txt
    out['k2'] = (('More' if vol >= 0 else 'Fewer') + ' people (volume)', smoney(vol), line)
    out['k3'] = (('Higher' if s['Rate'] >= 0 else 'Lower') + ' rates', smoney(s['Rate']), 'pay and bill rates, constant FX')
    out['k4'] = ('Mix of people', smoney(mix),
                 f"level {snum(s['Level mix'])} · location {snum(s['Location mix'])} · workforce {snum(s['Workforce mix'])}")
    out['k5'] = ('Currency', smoney(s['Currency']), f"{smoney(chg - s['Currency'])} before exchange rates")
    drv = max(FACTORS, key=lambda f: abs(s[f]))
    dshare = s[drv] / chg if chg else None
    verb = 'grew' if chg >= 0 else 'fell'
    if dshare is not None and 0.5 <= dshare <= 1:
        out['title'] = f'Cost {verb} {whole_m(chg)}, and {pct(dshare)} of it was {driver_words(drv, s[drv])}'
    else:
        out['title'] = f'Cost {verb} {whole_m(chg)}; the largest effect was {driver_words(drv, s[drv])} ({smoney(s[drv])})'
    f = 0.95 * min(o, c) / 1e6
    step = 10 ** (math.floor(math.log10(f)) - 1)
    floor = math.floor(f / step) * step
    out['floor'] = floor
    lvl, path = o, [o]
    for k in FACTORS:
        lvl += s[k]
        path.append(lvl)
    out['path_min'] = min(path) / 1e6
    out['closes'] = abs(lvl - c) < 0.05  # each stored value is rounded to the cent
    b = p['bias']
    big = max(FACTORS, key=lambda f: abs(b[f]))
    out['bias_sub'] = f'A fixed order would move {big} by {smoney(b[big])}'
    out['bias'] = [(f, snum(s[f]), snum(p['seq'][f]), snum(b[f])) for f in FACTORS]
    out['bars'] = [money(o)] + [snum(s[k]) for k in FACTORS] + [money(c)]
    return out


def floor_text(floor):
    return f'${floor / 1000:.1f}B' if floor >= 1000 else f'${floor:,.0f}M'


def table(pairs, group):
    yrs = sorted([(off, p) for (off, g), p in pairs.items() if g == group and off % 4 == 0], key=lambda t: -t[0])
    rows = []
    for off, p in yrs:
        s = p['shap']
        rows.append((fy(p['fy']), snum(s['Volume']), snum(s['Workforce mix'] + s['Location mix'] + s['Level mix']),
                     snum(s['Rate']), snum(s['Currency'])))
    rates = [p['shap']['Rate'] for _, p in yrs]
    cur = [p['shap']['Currency'] for _, p in yrs]
    n = sum(r > 0 for r in rates)
    t1 = 'Rates rose every year' if n == len(rates) else 'Rates fell every year' if n == 0 else f'Rates rose in {n} of {len(rates)} years'
    t2 = ('currency swung both ways' if min(cur) < 0 < max(cur)
          else 'currency lowered cost every year' if max(cur) < 0 else 'currency raised cost every year')
    return t1 + '; ' + t2, rows


def main():
    pairs = load()
    groups = sorted({g for (_, g) in pairs}, key=lambda g: (pairs[(0, g)]['view_order'], g))
    if '--verify' in sys.argv:
        bad = 0
        for (off, g), p in pairs.items():
            o = page(p, off)
            if not o['closes']:
                print('does not close', off, g); bad += 1
            if o['path_min'] < o['floor']:
                print('path below floor', off, g, o['path_min'], o['floor']); bad += 1
        worst = min(page(p, off)['path_min'] / (min(p['shap']['Opening cost'], p['shap']['Closing cost']) / 1e6)
                    for (off, g), p in pairs.items())
        print(f'{len(pairs)} pairs x groups; lowest path / min(opening, closing) = {worst:.4f}; problems: {bad}')
        return
    print('### Company, every pair\n')
    print('| p_Pair | Pair | Span | Total cost | Change | Volume | Workforce mix | Location mix | Level mix | Rate | Currency | Axis floor |')
    print('|---:|---|---|---:|---|---:|---:|---:|---:|---:|---:|---:|')
    for off in range(17):
        p = pairs[(off, 'Arcadia Systems')]
        o = page(p, off)
        print(f"| {off} | {o['pair']} | {o['span']} | {o['k1'][1]} | {o['k1'][2].split(' vs ')[0]} ({o['k1'][2].split('(')[1]} | "
              + ' | '.join(o['bars'][1:7]) + f" | {floor_text(o['floor'])} |")
    print('\n### Page texts, company, every pair\n')
    print('| p_Pair | Bridge title | KPI 2 line | KPI 5 line | Order-bias subtitle |')
    print('|---:|---|---|---|---|')
    for off in range(17):
        o = page(pairs[(off, 'Arcadia Systems')], off)
        print(f"| {off} | {o['title']} | {o['k2'][0]} · {o['k2'][2]} | {o['k5'][2]} | {o['bias_sub']} |")
    print('\n### Each group, the latest pair (p_Pair 0)\n')
    print('| Group | Total cost | Change | Volume | Workforce mix | Location mix | Level mix | Rate | Currency | Axis floor | Bridge title |')
    print('|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---|')
    for g in groups:
        o = page(pairs[(0, g)], 0)
        print(f"| {g} | {o['k1'][1]} | {o['k1'][2].split(' vs ')[0]} | " + ' | '.join(o['bars'][1:7])
              + f" | {floor_text(o['floor'])} | {o['title']} |")
    print('\n### Order bias, the latest pair\n')
    for g in ['Arcadia Systems', 'Technology']:
        o = page(pairs[(0, g)], 0)
        print(f'**{g}** · subtitle "{o["bias_sub"]}"\n')
        print('| Factor | Shapley | Sequential | Bias |')
        print('|---|---:|---:|---:|')
        for f, a, b2, c in o['bias']:
            print(f'| {f} | {a} | {b2} | {c} |')
        print()
    print('### Five-year table\n')
    for g in ['Arcadia Systems', 'Technology', 'People']:
        t, rows = table(pairs, g)
        print(f'**{g}** · title "{t}"\n')
        print('| FY | Volume | Mix | Rate | Currency |')
        print('|---|---:|---:|---:|---:|')
        for r in rows:
            print('| ' + ' | '.join(r) + ' |')
        print()
    o = page(pairs[(0, 'Arcadia Systems')], 0)
    print('### KPI band, company, latest pair\n')
    for k in ['k1', 'k2', 'k3', 'k4', 'k5']:
        print(f'- {o[k][0]} · **{o[k][1]}** · {o[k][2]}')


if __name__ == '__main__':
    main()
