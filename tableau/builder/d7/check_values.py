"""Every number the Who Leads Where page shows for the check leaders, computed from the marts the way the page reads them.

  python3 tableau/builder/d7/check_values.py            # markdown tables for the build guide's check section
  python3 tableau/builder/d7/check_values.py --verify   # the guide's own checks: ties, closures, signal totals

Reads data/marts/mart_org_node.csv, mart_leader_availability.csv and mart_alignment_detail.csv, the same rows as the
Node, Day and Signal rows of tableau/custom_sql_who_leads_where.sql. Arcadia Systems is fictional; all data is synthetic.
"""
import csv
import os
import sys
from collections import defaultdict
from datetime import date

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..')
MARTS = os.path.join(ROOT, 'data', 'marts')
LEADERS = ['W100001', 'W100010', 'W100011', 'W104003']     # the CEO, Isaac Holland (L1), Maria Barnes (L1), Daniela Guerra (L2)
TYPES = ['All', 'Employees', 'Contingent']
WORDS = {'All': 'people', 'Employees': 'employees', 'Contingent': 'contingent workers'}
SIGNALS = [('S1', 'Budgeted in another org'), ('S2', 'Role from another function'), ('M1', 'Country leader for another country'),
           ('M2', 'In two country matrices, or none'), ('M3', 'Matrix inactive or without a leader')]


def rows(name):
    with open(os.path.join(MARTS, name + '.csv'), newline='', encoding='utf-8') as f:
        return list(csv.DictReader(f))


def num(x):
    return int(float(x)) if x not in ('', None) else 0


def comma(n):
    return f'{n:,}'


def pct1(a, b):
    return '0%' if not b else f'{round(100 * a / b, 1)}%'


def span(x):
    if x in ('', None):
        return '–'
    v = float(x)
    return str(int(v)) if v == int(v) else str(round(v, 1))


def day_text(d):
    return f"{d.strftime('%a')}, {d.strftime('%b')} {d.day}"


NODE = {(r['leader_id'], r['worker_type']): r for r in rows('mart_org_node')}
DAY = defaultdict(dict)
for r in rows('mart_leader_availability'):
    DAY[(r['leader_id'], r['worker_type'])][num(r['day_offset'])] = r
SIG = rows('mart_alignment_detail')


def leader(lid, wt='All'):
    n, a = NODE[(lid, wt)], NODE[(lid, 'All')]
    people, gaps = num(n['people']), num(n['gap_people'])
    countries = num(n['countries'])
    head = (f"{a['leader_name']} leads {comma(people)} {WORDS[wt]} in {countries} {'country' if countries == 1 else 'countries'}. "
            f"{comma(gaps)} ({pct1(gaps, people)}) {'shows' if gaps == 1 else 'show'} an alignment gap.")
    today = DAY[(lid, wt)][0]
    return dict(name=a['leader_name'], level=a['leader_level'], title=a['job_title'], head=head, people=people,
                directs=num(n['directs']), indirects=num(n['indirects']), at_work=num(today['at_work']), off=num(today['off']),
                layers=num(n['layers_below']), span=span(n['median_span']), mgr15=num(n['managers_15_plus']),
                mgr1=num(n['managers_one_direct']), gaps=gaps, solid=num(n['solid_line_gap_people']),
                matrix=num(n['matrix_gap_people']), r1=num(a['assignments_naming_former_leader']))


def signals(lid, wt='All'):
    level = NODE[(lid, 'All')]['leader_level']
    col = {'L0': 'l0_leader_id', 'L1': 'l1_leader_id', 'L2': 'l2_leader_id'}[level]
    top = NODE[(lid, 'All')]['parent_leader_id'] == ''    # the CEO: l0_leader_id names the function head, so take every row
    seen = defaultdict(set)
    for r in SIG:
        if (top or r[col] == lid) and (wt == 'All' or r['worker_type'] == wt):
            seen[r['signal_code']].add(r['person_id'])
    return {code: len(seen[code]) for code, _ in SIGNALS}


def calendar(lid, wt='All'):
    out = []
    for off, r in sorted(DAY[(lid, wt)].items()):
        d = date.fromisoformat(r['day'][:10])
        wk = r['is_weekend'] in ('true', 'True', '1')
        out.append(dict(off=off, day=d, weekend=wk, people=num(r['people']), at_work=num(r['at_work']), off_n=num(r['off']),
                        pto=num(r['off_time_off']), leave=num(r['off_leave']), hol=num(r['off_public_holiday']),
                        left=num(r['left_team'])))
    return out


def tables():
    print('### Headline and KPIs (All)\n')
    print('| Leader | Headline | People led | At work today | Layers below | Median span | Alignment gaps |')
    print('|---|---|---:|---:|---:|---:|---:|')
    for lid in LEADERS:
        v = leader(lid)
        print(f"| {v['name']} ({v['level']}) | {v['head']} | {comma(v['people'])} ({v['directs']} directs · {comma(v['indirects'])} indirect) "
              f"| {comma(v['at_work'])} ({comma(v['off'])} off) | {v['layers']} | {v['span']} ({v['mgr15']} lead 15+ · {v['mgr1']} lead one) "
              f"| {comma(v['gaps'])} ({comma(v['solid'])} solid · {comma(v['matrix'])} matrix) |")
    print('\n### The worker toggle (people led / at work today / alignment gaps)\n')
    print('| Leader | All | Employees | Contingent |')
    print('|---|---|---|---|')
    for lid in LEADERS:
        cells = []
        for wt in TYPES:
            v = leader(lid, wt)
            cells.append(f"{comma(v['people'])} / {comma(v['at_work'])} / {comma(v['gaps'])}")
        print(f"| {leader(lid)['name']} | " + ' | '.join(cells) + ' |')
    print('\n### Org design alignment panel (All)\n')
    print('| Signal | ' + ' | '.join(leader(lid)['name'] for lid in LEADERS) + ' |')
    print('|---|' + '---:|' * len(LEADERS))
    sig = {lid: signals(lid) for lid in LEADERS}
    for code, name in SIGNALS:
        print(f'| {name} | ' + ' | '.join(comma(sig[lid][code]) for lid in LEADERS) + ' |')
    print('| Still naming a former leader (assignments) | ' + ' | '.join(str(leader(lid)['r1']) for lid in LEADERS) + ' |')
    print('\n### Calendar, Isaac Holland (All)\n')
    print('| Day | At work | Of | Off (time off, leave, holiday) | Left the team |')
    print('|---|---:|---:|---|---:|')
    cal = calendar('W100010')
    for c in cal:
        if c['off'] in (0, 1, 3) or c['off'] == cal[-1]['off']:
            v = 'Weekend' if c['weekend'] else comma(c['at_work'])
            print(f"| {day_text(c['day'])} | {v} | {comma(c['people'])} | {comma(c['off_n'])} ({comma(c['pto'])}, {comma(c['leave'])}, {comma(c['hol'])}) "
                  f"| {comma(c['left'])} |")
    wd = [c for c in cal if not c['weekend']]
    q = min(wd, key=lambda c: (c['at_work'], c['day']))
    print(f"\nCalendar summary: The quietest weekday is {day_text(q['day'])}: {comma(q['at_work'])} at work.")


def verify():
    problems = []
    for (lid, wt), n in NODE.items():
        if wt != 'All':
            continue
        a, e, c = (num(NODE[(lid, t)]['people']) for t in TYPES)
        if a != e + c:
            problems.append(f'{lid}: All {a} != Employees {e} + Contingent {c}')
        if num(n['people']) != num(n['directs']) + num(n['indirects']):
            problems.append(f'{lid}: people != directs + indirects')
        if num(n['gap_people']) > num(n['people']):
            problems.append(f'{lid}: more gaps than people')
    for key, days in DAY.items():
        for off, r in days.items():
            if r['is_weekend'] in ('true', 'True', '1'):          # nobody is scheduled on a weekend: the page shows "Weekend"
                continue
            if num(r['at_work']) + num(r['off']) != num(r['people']):
                problems.append(f'{key} day {off}: at work + off != people')
            if num(r['off_time_off']) + num(r['off_leave']) + num(r['off_public_holiday']) != num(r['off']):
                problems.append(f'{key} day {off}: off parts do not add up')
    ceo = leader('W100001')
    for want, got, what in ((41934, ceo['people'], 'CEO people'), (2057, ceo['gaps'], 'CEO gaps'),
                            (30005, leader('W100001', 'Employees')['people'], 'employees'),
                            (11929, leader('W100001', 'Contingent')['people'], 'contingent workers in a tree (11,941 less 12 with no manager employed)')):
        if want != got:
            problems.append(f'{what}: {got}, expected {want}')
    for lid in LEADERS:
        v, s = leader(lid), signals(lid)
        if s['S1'] + s['S2'] < v['solid'] or s['M1'] + s['M2'] + s['M3'] < v['matrix']:
            problems.append(f'{lid}: the panel shows fewer signal people than the KPI note')
    print(f'{len(NODE) // 3} leaders, {sum(len(d) for d in DAY.values())} leader-days; problems: {len(problems)}')
    for p in problems[:20]:
        print('  ' + p)
    return not problems


if __name__ == '__main__':
    if '--verify' in sys.argv:
        sys.exit(0 if verify() else 1)
    tables()
