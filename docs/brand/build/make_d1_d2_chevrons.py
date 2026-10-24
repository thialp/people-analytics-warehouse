"""Drawn chevron for the Dashboard #1 and #2 field capsules (same idea as make_d3_shapes.py).

The typed "▾" in a Tableau label is too small to read as "open a list", so the chevron is part of the
image. This script opens the existing white capsule (d1_field_capsule, d2_field_capsule) and draws a solid
navy chevron 10 x 6 dashboard pixels, 18 px from the right edge, one pixel below the middle of the box,
exactly where d3_field_capsule has it. It is idempotent: it always starts from the capsule alone
(the capsule is the white area, so the old chevron is painted white again before the new one is drawn).

Usage:  python3 docs/brand/build/make_d1_d2_chevrons.py
"""
from PIL import Image, ImageDraw
import os

HERE = os.path.dirname(os.path.abspath(__file__))
DST = os.path.join(HERE, "..", "shapes", "by_dashboard")
NAVY, WHITE = (19, 35, 58, 255), (255, 255, 255, 255)
SS = 8


def add_chevron(path, scale=3):
    im = Image.open(path).convert("RGBA")
    w, h = im.size
    # opaque box of the capsule: top row of the capsule (the rows above are transparent padding)
    top = next(y for y in range(h) if im.getpixel((w // 2, y))[3] > 200)
    box_h = h - top
    cx = w - 18 * scale
    cy = top + box_h / 2 + 1 * scale
    # wipe an earlier chevron (white again), then draw at 8x and shrink
    d0 = ImageDraw.Draw(im)
    d0.rectangle((cx - 8 * scale, cy - 5 * scale, cx + 8 * scale, cy + 5 * scale), fill=WHITE)
    big = Image.new("RGBA", (w * SS, h * SS), (0, 0, 0, 0))
    d = ImageDraw.Draw(big)
    hw, hh = 5 * scale * SS, 3 * scale * SS
    X, Y = cx * SS, cy * SS
    d.polygon([(X - hw, Y - hh), (X + hw, Y - hh), (X, Y + hh)], fill=NAVY)
    layer = big.resize((w, h), Image.LANCZOS)
    im.alpha_composite(layer)
    im.save(path)
    return path


for name in ("d1/d1_field_capsule.png", "d2/d2_field_capsule.png"):
    print("wrote", add_chevron(os.path.join(DST, name)))
