import re, json, sys
import os
GUIDE = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..', '..', 'docs', 'projects', 'workforce-planning', 'seats_to_fill_build.md')
def parse(path=GUIDE):
    s=open(path).read()
    blocks=re.findall(r"```\n(.*?)```", s, re.S)
    calcs={}
    for b in blocks:
        cur=None; body=[]
        def flush():
            if cur and any(l.strip() for l in body):
                calcs[cur]='\n'.join(body).strip('\n')
        for line in b.split('\n'):
            m=re.match(r"// (.+)$", line)
            if m:
                flush()
                name=m.group(1)
                name=re.split(r"\s{3,}|\s+\(", name)[0].strip()
                cur=name; body=[]
                # one-line form "// Name   formula" (not used except notes)
            else:
                body.append(line)
        flush()
    return calcs
if __name__=='__main__':
    c=parse()
    for k,v in c.items(): print(repr(k), '|', v.split('\n')[0][:90])
    print(len(c))
