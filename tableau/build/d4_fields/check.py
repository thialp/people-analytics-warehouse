import re, sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from spec import PARAMS, C, EXISTING
import spec_sankey
params={p[0] for p in PARAMS}|{p[0] for p in spec_sankey.PARAMS}
C=C+spec_sankey.C
F={cap:(k,f) for cap,dt,k,f in C}
for old,(new,f) in EXISTING.items():
    k='row' if new in ('What differs','What it puts at risk','Where it is aligned') else 'agg'
    F[new]=(k,f)
AGG=('SUM','MIN','MAX','COUNTD','AVG','ATTR','COUNT')
TC=('INDEX','SIZE')
level={}
def lev(cap):
    if cap in level: return level[cap]
    k,f=F[cap]
    level[cap]='?'
    r=scan(f,cap)
    level[cap]=r; return r
def reflevel(n):
    if n in params: return 'const'
    if n in F: return lev(n)
    return 'row'
errs=[]
def scan(f,cap):
    f2=re.sub(r'"[^"]*"','""',f)
    # bracket checks
    for a,b in ('()','{}','[]'):
        if f2.count(a)!=f2.count(b): errs.append(f'{cap}: unbalanced {a}{b}')
    ifs=len(re.findall(r'\bIF\b',f2))+len(re.findall(r'\bCASE\b',f2)); ends=len(re.findall(r'\bEND\b',f2))
    if ifs!=ends: errs.append(f'{cap}: IF/CASE {ifs} vs END {ends}')
    toks=re.findall(r'\{|\}|\(|\)|\[[^\]]+\]|[A-Z_]+(?=\s*\()',f2)
    stack=[]; top=set()
    pend=None
    for t in toks:
        if t=='{': stack.append('lod'); continue
        if t=='}':
            stack.pop()
            if not any(x in('agg','lod') for x in stack): top.add('row')
            continue
        if t in AGG or t in TC: pend=t; continue
        if t=='(':
            stack.append('agg' if pend in AGG else 'tc' if pend in TC else 'p'); pend=None; continue
        if t==')':
            x=stack.pop()
            if x=='agg' and not any(y in('agg','lod') for y in stack): top.add('agg')
            if x=='tc': top.add('agg')
            continue
        pend=None
        if t.startswith('['):
            n=t[1:-1]; L=reflevel(n)
            inside=any(y in('agg','lod') for y in stack)
            if inside:
                if L=='agg': errs.append(f'{cap}: aggregate {n} inside an aggregate/LOD')
            else:
                if L in('row','agg'): top.add(L)
    if 'row' in top and 'agg' in top: errs.append(f'{cap}: MIXES row-level and aggregate')
    return 'agg' if 'agg' in top else 'row' if 'row' in top else 'const'
for cap in F: lev(cap)
for cap,(k,f) in F.items():
    L=level[cap]
    if k in('agg','tc') and L!='agg': errs.append(f'{cap}: declared {k} but is {L}')
    if k=='row' and L=='agg': errs.append(f'{cap}: declared row but is aggregate')
print('\n'.join(errs) or 'no problems'); print(len(F),'formulas checked')
