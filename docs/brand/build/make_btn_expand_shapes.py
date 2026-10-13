"""Arcadia card button shapes for Expand / Collapse (transparent PNGs, 64 x 64, shown at about 14 x 14).
btn_expand_icon   = two diagonal arrows pointing out (card is compact: click to expand)
btn_collapse_icon = two diagonal arrows pointing in  (card is expanded: click to collapse)
Navy #13233A, for the light cards. Usage: python3 make_btn_expand_shapes.py"""
import os
from PIL import Image, ImageDraw

OUT = os.path.join(os.path.dirname(__file__), "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
S, N, W = 4, 64, 6
COL = (19, 35, 58, 255)

def line(d, pts):
    d.line([(x * S, y * S) for x, y in pts], fill=COL, width=W * S, joint="curve")
    for x, y in (pts[0], pts[-1]):
        d.ellipse(((x - W / 2) * S, (y - W / 2) * S, (x + W / 2) * S, (y + W / 2) * S), fill=COL)

def icon(path, out):
    im = Image.new("RGBA", (N * S, N * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if out:  # arrow heads at the two outer corners
        line(d, [(34, 30), (53, 11)]); line(d, [(40, 11), (53, 11), (53, 24)])
        line(d, [(30, 34), (11, 53)]); line(d, [(24, 53), (11, 53), (11, 40)])
    else:    # arrow heads near the centre, pointing in
        line(d, [(53, 11), (36, 28)]); line(d, [(36, 15), (36, 28), (49, 28)])
        line(d, [(11, 53), (28, 36)]); line(d, [(28, 49), (28, 36), (15, 36)])
    im.resize((N, N), Image.LANCZOS).save(path)

icon(os.path.join(OUT, "btn_expand_icon.png"), True)
icon(os.path.join(OUT, "btn_collapse_icon.png"), False)

prev = Image.new("RGB", (260, 90), (251, 251, 248))
for i, n in enumerate(("btn_expand_icon", "btn_collapse_icon")):
    ic = Image.open(os.path.join(OUT, n + ".png"))
    prev.paste(ic, (30 + i * 120, 12), ic)
    prev.paste(ic.resize((16, 16), Image.LANCZOS), (100 + i * 120, 36), ic.resize((16, 16), Image.LANCZOS))
prev.save(os.path.join(os.path.dirname(__file__), "btn_expand_preview.png"))
print("ok")
