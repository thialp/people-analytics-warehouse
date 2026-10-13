"""Rail toggle shapes for the Workforce Footprint (transparent PNGs, 4x of the cell).
Same look as make_rail_toggle_shapes.py (Compensation Walk): selected = wash pill, navy text;
not selected = light text. Two-option toggles use an 88 x 30 cell, three-option toggles 58 x 30,
so every capsule is 176 px wide in the rail.
Usage: python3 make_footprint_toggle_shapes.py [capsule_hex] [pill_hex]
Output: docs/brand/shapes/Arcadia/seg_fp_<toggle>_<option>_<on|off>.png and footprint_toggle_preview.png
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys

OUT = os.path.join(os.path.dirname(__file__), "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
S, H = 4, 120
NAVY, MIST = (19, 35, 58, 255), (201, 209, 220, 255)
CAP = sys.argv[1].lstrip("#") if len(sys.argv) > 1 else "1D3150"
CAP = tuple(int(CAP[i:i + 2], 16) for i in (0, 2, 4)) + (255,)
PILL = sys.argv[2].lstrip("#") if len(sys.argv) > 2 else "E4E3DD"
PILL = tuple(int(PILL[i:i + 2], 16) for i in (0, 2, 4)) + (255,)

# toggle -> (cell width at 1x, [(option key, label)])
TOGGLES = {
    "lens":   (88, [("headcount", "Headcount"), ("fte", "FTE")]),
    "routes": (58, [("all", "All"), ("3", "3+"), ("10", "10+")]),
    "radius": (58, [("500", "500 km"), ("1000", "1,000"), ("2000", "2,000")]),
}


def segment(label, on, cell_w, path):
    w = cell_w * 4
    im = Image.new("RGBA", (w * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if on:
        d.rounded_rectangle((8 * S, 8 * S, (w - 8) * S, (H - 8) * S), radius=14 * S, fill=PILL)
    size = 40 if cell_w >= 88 else 36
    f = ImageFont.truetype(FONT, size * S)
    d.text((w * S // 2, H * S // 2), label, font=f, fill=NAVY if on else MIST, anchor="mm")
    im.resize((w, H), Image.LANCZOS).save(path)


for toggle, (cell, options) in TOGGLES.items():
    for key, label in options:
        for on in (True, False):
            segment(label, on, cell, f"{OUT}/seg_fp_{toggle}_{key}_{'on' if on else 'off'}.png")

# preview: each capsule with its default option selected, on the rail navy
defaults = {"lens": "headcount", "routes": "3", "radius": "1000"}
pv = Image.new("RGB", (480, 3 * 70), (19, 35, 58))
for r, (toggle, (cell, options)) in enumerate(TOGGLES.items()):
    cap = Image.new("RGBA", (704, H), (0, 0, 0, 0))
    ImageDraw.Draw(cap).rounded_rectangle((0, 0, 703, H - 1), radius=16, fill=CAP)
    for i, (key, _) in enumerate(options):
        on = key == defaults[toggle]
        cap.alpha_composite(Image.open(f"{OUT}/seg_fp_{toggle}_{key}_{'on' if on else 'off'}.png"), (i * cell * 4, 0))
    cap = cap.resize((240, 41), Image.LANCZOS)
    pv.paste(cap, (20, r * 70 + 14), cap)
pv.save(os.path.join(os.path.dirname(__file__), "footprint_toggle_preview.png"))
print("wrote", sum(len(o) for _, o in TOGGLES.values()) * 2, "shapes to", os.path.abspath(OUT))
