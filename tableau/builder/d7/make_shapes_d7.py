"""Draw the Who Leads Where (case study 7) shapes, light and dark, into a Tableau shapes folder.

    python3 make_shapes_d7.py OUT_DIR [GITHUB_PNG]

OUT_DIR is ~/Documents/My Tableau Repository/Shapes/Arcadia D7. Every file is drawn at 4x its size on the
page. Names end in _l (light) or _d (dark); the workbook picks one with the theme parameter.
Colors are the approved Canopy palette (docs/projects/leadership-scope, design round 2).
"""
import os
import sys

from PIL import Image, ImageDraw, ImageFont

S = 4
THEME = {
    'l': dict(chip='#EDF2F0', accent='#1F7560', on='#FFFFFF', muted='#56635F', ink='#15201D', line='#DFE6E3',
              surface='#FFFFFF', soft='#E1F2EB'),
    'd': dict(chip='#202A28', accent='#7FD1B9', on='#0F1413', muted='#9AA9A4', ink='#E9EFEC', line='#2A3532',
              surface='#1A2120', soft='#1E3A33'),
}
FONT = '/usr/share/fonts/opentype/inter/Inter-SemiBold.otf'
FONT_B = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
FONT_M = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'


def rgb(h, a=255):
    h = h.lstrip('#')
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (a,)


def seg(label, w, h, pos, on, t, size=11):
    """one segment of a pill toggle: pos is 'left', 'mid', 'right' or 'only'"""
    W, H = w * S, h * S
    im = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    r = H // 2
    d.rounded_rectangle([0, 0, W - 1, H - 1], r, fill=rgb(t['chip']))
    if pos in ('mid', 'right'):          # square off the inside edges so segments join into one pill
        d.rectangle([0, 0, r, H - 1], fill=rgb(t['chip']))
    if pos in ('mid', 'left'):
        d.rectangle([W - 1 - r, 0, W - 1, H - 1], fill=rgb(t['chip']))
    if on:
        p = 3 * S
        d.rounded_rectangle([p, p, W - 1 - p, H - 1 - p], (H - 2 * p) // 2, fill=rgb(t['accent']))
    f = ImageFont.truetype(FONT_B if on else FONT_M, size * S)
    tw = d.textlength(label, font=f)
    asc, desc = f.getmetrics()
    d.text(((W - tw) / 2, (H - asc - desc) / 2 + S * 0.5), label, font=f, fill=rgb(t['on'] if on else t['muted']))
    return im


def dot(on, t):
    W = 20 * S
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    if on:
        d = ImageDraw.Draw(im)
        d.ellipse([5 * S, 5 * S, 15 * S, 15 * S], fill=rgb(t['accent']))
    else:                                 # a faint ring, so the shape is never fully empty
        d = ImageDraw.Draw(im)
        d.ellipse([6 * S, 6 * S, 14 * S, 14 * S], outline=rgb(t['line']), width=S)
    return im


def button(kind, t, w=28):
    W = w * S
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([S, S, W - 1 - S, W - 1 - S], 7 * S, fill=rgb(t['surface']), outline=rgb(t['line']), width=S)
    c, lw = rgb(t['ink']), int(1.8 * S)
    m, a = 8 * S, 5 * S                    # inset, arm length
    if kind == 'expand':                   # four corners pointing out
        for (x, y, sx, sy) in ((m, m, 1, 1), (W - m, m, -1, 1), (m, W - m, 1, -1), (W - m, W - m, -1, -1)):
            d.line([(x, y + sy * a), (x, y), (x + sx * a, y)], fill=c, width=lw, joint='curve')
    elif kind == 'collapse':               # four corners pointing in
        k = 4 * S
        for (x, y, sx, sy) in ((m + k, m + k, -1, -1), (W - m - k, m + k, 1, -1), (m + k, W - m - k, -1, 1), (W - m - k, W - m - k, 1, 1)):
            d.line([(x, y + sy * a), (x, y), (x + sx * a, y)], fill=c, width=lw, joint='curve')
    elif kind == 'info':
        im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.ellipse([2 * S, 2 * S, W - 1 - 2 * S, W - 1 - 2 * S], fill=rgb(t['surface']), outline=rgb(t['line']), width=S)
        f = ImageFont.truetype(FONT_B, 13 * S)
        tw = d.textlength('i', font=f)
        asc, desc = f.getmetrics()
        d.text(((W - tw) / 2, (W - asc - desc) / 2), 'i', font=f, fill=rgb(t['accent']))
    elif kind == 'close':
        im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        k = 9 * S
        d.line([(k, k), (W - k, W - k)], fill=rgb(t['muted']), width=2 * S)
        d.line([(W - k, k), (k, W - k)], fill=rgb(t['muted']), width=2 * S)
    return im


def brand(src, t):
    """a GitHub / LinkedIn mark recolored to the theme's ink, on a chip tile"""
    W = 26 * S
    im = Image.new('RGBA', (W, W), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.rounded_rectangle([0, 0, W - 1, W - 1], 7 * S, fill=rgb(t['chip']))
    if src == 'in':                      # LinkedIn: the two letters, in the theme's ink
        f = ImageFont.truetype(FONT_B, 13 * S)
        tw = d.textlength('in', font=f)
        asc, desc = f.getmetrics()
        d.text(((W - tw) / 2, (W - asc - desc) / 2 - S * 0.5), 'in', font=f, fill=rgb(t['ink']))
    elif src and os.path.exists(src):
        g = Image.open(src).convert('RGBA')
        a = g.split()[3]
        if min(a.getextrema()) == 255:   # an opaque icon: use its dark pixels as the mark
            a = g.convert('L').point(lambda v: 255 if v < 128 else 0)
        a = a.resize((15 * S, 15 * S), Image.LANCZOS)
        mark = Image.new('RGBA', a.size, rgb(t['ink']))
        mark.putalpha(a)
        im.alpha_composite(mark, ((W - a.width) // 2, (W - a.height) // 2))
    return im


def main(out, gh=None):
    os.makedirs(out, exist_ok=True)
    n = 0
    for k, t in THEME.items():
        sets = [('worker', [('all', 'All'), ('employees', 'Employees'), ('contingent', 'Contingent')], 62, 28, 9),
                ('count', [('everyone', 'Everyone'), ('atwork', 'At work')], 94, 28, 11),
                ('tree', [('dynamic', 'Dynamic'), ('static', 'Static')], 74, 26, 10.5),
                ('theme', [('light', 'Light'), ('dark', 'Dark')], 64, 26, 10.5)]
        for name, opts, w, h, fs in sets:
            for i, (key, label) in enumerate(opts):
                pos = 'left' if i == 0 else ('right' if i == len(opts) - 1 else 'mid')
                for on in (True, False):
                    seg(label, w, h, pos, on, t, fs).save(os.path.join(out, f'd7_{name}_{key}_{"on" if on else "off"}_{k}.png'))
                    n += 1
        for on in (True, False):
            dot(on, t).save(os.path.join(out, f'd7_dot_{"on" if on else "off"}_{k}.png')); n += 1
        for kind in ('expand', 'collapse', 'info', 'close'):
            button(kind, t).save(os.path.join(out, f'd7_{kind}_{k}.png')); n += 1
        brand(gh, t).save(os.path.join(out, f'd7_github_{k}.png'))
        brand('in', t).save(os.path.join(out, f'd7_linkedin_{k}.png'))
        n += 2
    print(f'wrote {n} shapes to {out}')


if __name__ == '__main__':
    main(*sys.argv[1:])
