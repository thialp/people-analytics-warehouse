"""Every Dashboard #6 calculation: the guide's code blocks, the number patterns of section 4.4 expanded in place,
and the text fields the guide lists in a table (section 5)."""
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'd5'))
from parse_guide import parse  # noqa: E402

GUIDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'docs', 'projects',
                     'workforce-cost-bridge', 'cost_bridge_build.md')
PATTERNS = ('M1 Pattern', 'Sign Pattern', 'Comma Pattern', 'Pct1 Pattern')


def patterns(g):
    return {k.split()[0]: g[k] for k in PATTERNS}


def fill(pattern, x):
    return '(' + re.sub(r'\bx\b', lambda _: '(' + x + ')', pattern) + ')'


def expand(f, P):
    """<M1 on EXPR>, <Sign on EXPR>, <Comma on EXPR>, <Pct1 on EXPR> become the pattern with EXPR in place of x"""
    return re.sub(r'<(M1|Sign|Comma|Pct1) on ([^<>]+?)>', lambda mm: fill(P[mm.group(1)], mm.group(2).strip()), f)


def all_calcs():
    g = parse(GUIDE)
    P = patterns(g)
    out = [(k, expand(v, P)) for k, v in g.items() if k not in PATTERNS]
    names = [k for k, _ in out]

    def after(anchor, items):
        i = names.index(anchor) + 1
        for k, v in items:
            out.insert(i, (k, v)); names.insert(i, k); i += 1

    money = lambda x: f'"$" + {fill(P["M1"], x)} + "M"'
    smoney = lambda x: f'{fill(P["Sign"], x)} + "$" + {fill(P["M1"], x)} + "M"'
    snum = lambda x: f'{fill(P["Sign"], x)} + {fill(P["M1"], x)}'
    after('S Vol Share', [
        ('S Opening Txt', money('[S Opening]')), ('S Closing Txt', money('[S Closing]')),
        ('S Change Txt', smoney('[S Change]')), ('S Volume Txt', smoney('[S Volume]')), ('S Rate Txt', smoney('[S Rate]')),
        ('S Mix Txt', smoney('[S Mix]')), ('S Currency Txt', smoney('[S Currency]')),
        ('S Constant Txt', smoney('[S Constant Change]')), ('S Currency Abs Txt', money('[S Currency]')),
        ('S Workforce Num', snum('[S Workforce]')), ('S Location Num', snum('[S Location]')), ('S Level Num', snum('[S Level]')),
        ('S HC Open Str', fill(P['Comma'], '[S HC Open]')), ('S HC Close Str', fill(P['Comma'], '[S HC Close]')),
        ('S HC Change Str', f'(IF [S HC Change] >= 0 THEN "+" ELSE "−" END) + {fill(P["Comma"], "[S HC Change]")}'),
        ('S Change Pct Str', f'(IF ROUND([S Change Pct] * 100, 1) >= 0 THEN "+" ELSE "−" END) + {fill(P["Pct1"], "[S Change Pct]")} + "%"'),
        ('S Vol Share Str', 'STR(INT(ROUND([S Vol Share] * 100, 0))) + "%"'),
    ])
    # helpers for the layout
    after('Bar Size', [('Floor Mark', 'MIN([Axis Floor])')])
    after('Bias Notable', [('Shapley', '[Effect M]'), ('One fixed order', '[Seq M]')])
    after('Group Option People', [('Tick X', 'MIN(0.6)'), ('Close X', '"✕"')])
    return out


M_FMT = '*+#,##0.0;"−"#,##0.0'
FORMATS = {'Bar Top': '*$#,##0"M"', 'Label Y': '*$#,##0"M"', 'Shapley': M_FMT, 'One fixed order': M_FMT}
DTYPES = {'Pair Offset': 'integer', 'Zero Pair': 'integer', 'Table Col Order': 'integer', 'Latest To': 'date',
          'Driver Order': 'integer', 'Step M': 'real', 'Effect M': 'real', 'Seq M': 'real', 'Bias M': 'real', 'Shapley': 'real',
          'One fixed order': 'real', 'Floor Raw': 'real', 'Floor Step': 'real', 'Axis Floor': 'real',
          'Y Years': 'integer', 'Y Rate Up': 'integer'}
ROLES = {'Pair Offset': ('dimension', 'ordinal'), 'Zero Pair': ('dimension', 'ordinal'),
         'Table Col Order': ('dimension', 'ordinal')}

if __name__ == '__main__':
    for k, v in all_calcs():
        print(f'--- {k}\n{v}')
