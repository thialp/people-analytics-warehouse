import os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twb import Model
from d5_calcs import all_calcs, FORMATS, DTYPES, ROLES

BASE = os.environ.get('D5_BASE', 'base.twb')
DS = 'federated.1vgrow40tivg5f1br0e6d1tur3nh'

def raw_types(src):
    meta = re.search(r'<extract .*?<metadata-records>(.*?)</metadata-records>', src, re.S).group(1)
    out = {}
    for r in re.findall(r"<metadata-record class='column'>(.*?)</metadata-record>", meta, re.S):
        out[re.search(r'<remote-name>(.*?)</remote-name>', r).group(1)] = re.search(r'<local-type>(.*?)</local-type>', r).group(1)
    return out

PARAMS = {
    'p_Functions': {'dtype': 'string', 'value': ''}, 'p_DeptOff': {'dtype': 'string', 'value': ''},
    'p_Regions': {'dtype': 'string', 'value': ''}, 'p_CountryOff': {'dtype': 'string', 'value': ''},
    'p_OfficeOff': {'dtype': 'string', 'value': ''},
    'p_Period': {'dtype': 'integer', 'value': 0, 'members': ['0', '1', '2', '3', '4']},
    'p_PeriodOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_OrgOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_LocOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_InfoOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
}
DIMS_ORD = ['quarter_offset', 'fy_offset', 'fiscal_quarter', 'draw', 'period', 'days_from', 'origin_quarter_offset',
            'horizon', 'chart_point']

def model(src):
    m = Model(DS, raw_types(src), PARAMS)
    for n in DIMS_ORD:
        m.raw_role[n] = ('dimension', 'ordinal')
    m.raw_role['days_to'] = ('dimension', 'quantitative')
    m.aliases['level_band'] = [('L1-L2', 'L1–L2 Associate'), ('L3-L4', 'L3–L4 Senior'), ('L5-L6', 'L5–L6 Manager'),
                               ('L7+', 'L7+ Director')]
    m.aliases['chart_series'] = [('Immediate refills', 'Refills'), ('To fill', 'To fill'), ('Vacant', 'Vacant at end')]
    for k, v in all_calcs():
        m.add(k, v, fmt=FORMATS.get(k), dtype=DTYPES.get(k), role=ROLES.get(k))
        if k.startswith('SV ') or k.startswith('KPI 3'):
            m.meta[k]['order'] = ['days_to']
        if k.startswith('BT '):
            m.meta[k]['order'] = ['quarter_offset']
    return m

if __name__ == '__main__':
    m = model(open(BASE).read())
    for n in m.order:
        p = m.plain(n)
        wrapped = 'MIN([' in p and p != m.calcs[n]
        print(f"{n:28} {m.level(n):5} {m.dtype(n):8} {'/'.join(m.role(n))}" + ('   WRAP' if p.replace(' ', '') != m.calcs[n].replace(' ', '') else ''))
