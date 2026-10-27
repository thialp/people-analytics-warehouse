"""Round 21: the KPI 2 strip ends where card 2's rounded corners begin.

Card 2 spans x 473.5 to 686 px with 10 px corners. The strip moves 8 px in on each side:
x 481, width 198 (zone units: x 34357, w 14143 of 100000 x 1400 px), y and height unchanged.
The zone appears twice (the dashboard and its device layout), so both are moved.
usage: in.twb out.twb
"""
import sys

src, dst = sys.argv[1], sys.argv[2]
t = open(src, encoding='utf-8').read()
old = "w='15286' x='33786' y='10118'"
new = "w='14143' x='34357' y='10118'"
n = t.count(old)
if n == 0:
    sys.exit('KPI 2 Strip zone not found at its round 20 position')
t = t.replace(old, new)
open(dst, 'w', encoding='utf-8').write(t)
print(f'moved {n} KPI 2 Strip zone(s)')
