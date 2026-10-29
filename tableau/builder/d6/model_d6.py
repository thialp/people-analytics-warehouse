import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from twb import Model  # noqa: E402
from d6_calcs import all_calcs, FORMATS, DTYPES, ROLES  # noqa: E402


def raw_types(src):
    meta = re.search(r'<extract .*?<metadata-records>(.*?)</metadata-records>', src, re.S).group(1)
    out = {}
    for r in re.findall(r"<metadata-record class='column'>(.*?)</metadata-record>", meta, re.S):
        out[re.search(r'<remote-name>(.*?)</remote-name>', r).group(1)] = re.search(r'<local-type>(.*?)</local-type>', r).group(1)
    return out


def ds_name(src):
    return re.search(r"<datasource caption='Workforce Cost Bridge' inline='true' name='(federated\.[a-z0-9]+)'", src).group(1)


PARAMS = {
    'p_Pair': {'dtype': 'integer', 'value': 0, 'members': [str(i) for i in range(17)]},
    'p_Group': {'dtype': 'string', 'value': 'Arcadia Systems'},
    'p_SpanView': {'dtype': 'string', 'value': 'year'},
    'p_PeriodOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_OrgOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
    'p_InfoOpen': {'dtype': 'boolean', 'value': False, 'members': ['true', 'false']},
}
ORDER = ['factor_order', 'Factor Head', 'Factor Sub']       # the bridge's table calculations run along the bars


def model(src):
    m = Model(ds_name(src), raw_types(src), PARAMS)
    for n in ('factor_order', 'fiscal_year', 'view_order'):
        m.raw_role[n] = ('dimension', 'ordinal')
    for k, v in all_calcs():
        m.add(k, v, fmt=FORMATS.get(k), dtype=DTYPES.get(k), role=ROLES.get(k))
    for k in ('Bar Top', 'Bar Size', 'Label Y'):
        m.meta[k]['order'] = ORDER
    return m


if __name__ == '__main__':
    m = model(open(sys.argv[1], encoding='utf-8').read())
    for n in m.order:
        print(f"{n:24} {m.level(n):5} {m.dtype(n):8} {'/'.join(m.role(n))}")
