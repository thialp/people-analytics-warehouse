"""Draw the card pictures that sit under the two map-layer sheets of Who Leads Where, light and dark, at 2x.

    python3 make_cards_d7.py OUT_DIR

d7_kpi_cards_{l,d}.png    1136 x 76: the five KPI cards (surface fill, 1 px line border, 12 px corners), 12 px apart
d7_pulse_tiles_{l,d}.png   423 x 304: the six Team pulse tiles (page-background fill, 10 px corners), 8 px apart
The geometry matches build_d7.py (KW, TW, TH); the dashboard puts each picture at the map sheet's exact position.
"""
import os
import sys

from PIL import Image, ImageDraw

S = 2
PAL = {'l': dict(bg='#F4F7F6', surface='#FFFFFF', line='#DFE6E3'),
       'd': dict(bg='#141A19', surface='#1A2120', line='#2A3532')}
KW = [218, 217, 218, 217, 218]
TW, TH, GAP = [207, 208], 96, 8


def rgb(h):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def kpi(t):
    im = Image.new('RGBA', (1136 * S, 76 * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = 0
    for w in KW:
        d.rounded_rectangle([x * S, 0, (x + w) * S - 1, 76 * S - 1], 12 * S, fill=rgb(t['surface']), outline=rgb(t['line']), width=S)
        x += w + 12
    return im


def tiles(t):
    W, H = sum(TW) + GAP, 3 * TH + 2 * GAP
    im = Image.new('RGBA', (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    for r in range(3):
        x = 0
        for w in TW:
            y = r * (TH + GAP)
            d.rounded_rectangle([x * S, y * S, (x + w) * S - 1, (y + TH) * S - 1], 10 * S, fill=rgb(t['bg']))
            x += w + GAP
    return im


def main(out):
    os.makedirs(out, exist_ok=True)
    for k, t in PAL.items():
        kpi(t).save(os.path.join(out, f'd7_kpi_cards_{k}.png'))
        tiles(t).save(os.path.join(out, f'd7_pulse_tiles_{k}.png'))
    print('wrote 4 pictures to', out)


if __name__ == '__main__':
    main(sys.argv[1])
