"""Arcadia rail info button shapes (transparent PNGs, 64 x 64, shown at 16 x 16 in the rail).
rail_info_open  = circled "i"  (panel closed: click to open)
rail_info_close = circled "x"  (panel open: click to close)
Light slate on the navy rail (matches the 9 pt headings, a little brighter so it reads as clickable).
Usage: python3 make_rail_info_shapes.py"""
import os
from PIL import Image, ImageDraw
from shape_quality import SS, finish, out_size

OUT = os.path.join(os.path.dirname(__file__), "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
S, N = SS, 64
COL = (184, 192, 204, 255)  # #B8C0CC

def shape(path, closed):
    im = Image.new("RGBA", (N * S, N * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((4 * S, 4 * S, (N - 4) * S, (N - 4) * S), outline=COL, width=4 * S)
    if closed:
        for a, b in (((21, 21), (43, 43)), ((43, 21), (21, 43))):
            d.line([(a[0] * S, a[1] * S), (b[0] * S, b[1] * S)], fill=COL, width=4 * S)
    else:
        d.ellipse((28 * S, 15 * S, 36 * S, 23 * S), fill=COL)
        d.rounded_rectangle((28 * S, 28 * S, 36 * S, 49 * S), radius=3 * S, fill=COL)
    finish(im, N, N).save(path)

shape(os.path.join(OUT, "rail_info_open.png"), False)
shape(os.path.join(OUT, "rail_info_close.png"), True)

prev = Image.new("RGB", (240, 80), (19, 35, 58))
for i, n in enumerate(("rail_info_open", "rail_info_close")):
    ic = Image.open(os.path.join(OUT, n + ".png"))
    prev.paste(ic, (30 + i * 100, 8), ic)
prev.save(os.path.join(os.path.dirname(__file__), "rail_info_preview.png"))
print("ok")
