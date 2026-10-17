"""Shared output quality for every Tableau button/shape generator.

Shapes are designed on a 4x grid (a 80 x 32 cell is drawn 320 x 128). Two knobs:

  SS     supersampling while drawing (8 = very clean anti-aliased edges and letters)
  SCALE  delivered pixels per dashboard pixel (default 3)

Run any generator with SHAPE_SCALE=2|3|4|6 to change the delivered size, for example
  SHAPE_SCALE=6 python3 make_button_shapes.py
The drawing is always done at SS x the 4x grid and shrunk once with LANCZOS, then given a light
unsharp mask so thin strokes and small letters stay crisp after Tableau scales them.
"""
import os
from PIL import Image, ImageFilter

SS = 8
SCALE = float(os.environ.get("SHAPE_SCALE", "3"))
SHARPEN = os.environ.get("SHAPE_SHARPEN", "1") != "0"


def out_size(w, h):
    """Delivered pixel size for a shape designed on the 4x grid as w x h."""
    return max(1, round(w * SCALE / 4)), max(1, round(h * SCALE / 4))


def finish(im, w, h):
    """Shrink a supersampled canvas to the delivered size and sharpen lightly (alpha untouched)."""
    ow, oh = out_size(w, h)
    im = im.resize((ow, oh), Image.LANCZOS)
    if SHARPEN:
        r, g, b, a = im.split()
        rgb = Image.merge("RGB", (r, g, b)).filter(ImageFilter.UnsharpMask(radius=0.6, percent=60, threshold=0))
        im = Image.merge("RGBA", (*rgb.split(), a))
    return im
