"""Dashboard #3 (Workforce Planning) shapes for Tableau: the plan-version toggle and the round Reset.

Usage: python3 docs/brand/build/make_d3_shapes.py && python3 docs/brand/build/organize_shapes.py
Writes the source files to docs/brand/shapes/Arcadia/; organize_shapes.py copies them to
docs/brand/shapes/by_dashboard/d3/ under their d3_ names (palette "Arcadia D3").

| Source file | d3 name | Cell on the dashboard | Used by |
|---|---|---|---|
| seg_version_{budget,q1,q2,q3}_{on,off,na} | d3_version_{budget,q1,q2,q3}_{on,off,na} | 98 x 32 | Version toggle (capsule #243A57, 392 wide) |
| btn_reset_circle | d3_reset | 32 x 32 | Reset (ring like the info button, arrow inside) |

States: on = white pill, navy words (the plan in use); off = mist words (a plan you can pick);
na = dim words, no pill (this plan has nothing for the chosen period: the click does nothing).
The words are the whole label, so the toggle reads without a tooltip:
Budget | Q1 reforecast | Q2 reforecast | Q3 reforecast.
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os
from shape_quality import SS, finish

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
S = SS

NAVY = (19, 35, 58, 255)
WHITE = (255, 255, 255, 255)
MIST = (201, 209, 220, 255)       # #C9D1DC, the off words on #1's toggle
DIM = (110, 123, 147, 255)        # #6E7B93, the greyed option colour used on the pickers
RING = (255, 255, 255, 120)       # the Reset / info outline

W, H = 392, 128                   # 98 x 32 on the dashboard, 4x design grid
LABELS = (("budget", "Budget"), ("q1", "Q1 reforecast"), ("q2", "Q2 reforecast"), ("q3", "Q3 reforecast"))
FONT_PX = 42                      # 10.5 px on the dashboard; "Q1 reforecast" is about 74 px wide in a 98 px cell


def canvas(w, h):
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def segment(label, state, name):
    im, d = canvas(W, H)
    if state == "on":
        d.rounded_rectangle((10 * S, 10 * S, (W - 10) * S, (H - 10) * S), radius=((H - 20) // 2) * S, fill=WHITE)
    f = ImageFont.truetype(FONT, FONT_PX * S)
    col = {"on": NAVY, "off": MIST, "na": DIM}[state]
    d.text((W * S // 2, H * S // 2), label, font=f, fill=col, anchor="mm")
    finish(im, W, H).save(os.path.join(OUT, name + ".png"))
    return d.textlength(label, font=f) / S / 4      # words width on the dashboard, px


widest = 0
for key, label in LABELS:
    for state in ("on", "off", "na"):
        widest = max(widest, segment(label, state, f"seg_version_{key}_{state}"))


def reset_arrow(d, cx, cy, r, width, col):
    d.arc((cx - r, cy - r, cx + r, cy + r), start=-60, end=230, fill=col, width=width)
    a = math.radians(-60)
    tip = (cx + r * math.cos(a), cy + r * math.sin(a))
    L = width * 2.2
    d.polygon([(tip[0] + L * 0.9, tip[1] - L * 0.15), (tip[0] - L * 0.55, tip[1] - L * 0.95),
               (tip[0] - L * 0.25, tip[1] + L * 0.85)], fill=col)


N = 128
im, d = canvas(N, N)
d.ellipse((4 * S, 4 * S, (N - 4) * S, (N - 4) * S), outline=RING, width=4 * S)
reset_arrow(d, 64 * S, 66 * S, 26 * S, 8 * S, WHITE)
finish(im, N, N).save(os.path.join(OUT, "btn_reset_circle.png"))

# Preview of the #3 header controls on the navy band (not used by Tableau)
pv = Image.new("RGBA", (1000, 120), NAVY)
pd = ImageDraw.Draw(pv)
pd.text((24, 12), "COMPARE WITH", font=ImageFont.truetype(FONT, 13), fill=(184, 196, 214, 255))
cap = Image.new("RGBA", (392 * 2, 32 * 2), (0, 0, 0, 0))
ImageDraw.Draw(cap).rounded_rectangle((0, 0, 392 * 2 - 1, 63), radius=32, fill=(36, 58, 87, 255), outline=(255, 255, 255, 120), width=2)
for i, (key, _) in enumerate(LABELS):
    st = "on" if i == 0 else ("na" if i == 3 else "off")
    seg = Image.open(os.path.join(OUT, f"seg_version_{key}_{st}.png")).resize((196, 64), Image.LANCZOS)
    cap.alpha_composite(seg, (i * 196, 0))
pv.alpha_composite(cap, (24, 40))
for x, n in ((840, "btn_reset_circle"), (910, "info_open")):
    pv.alpha_composite(Image.open(os.path.join(OUT, n + ".png")).resize((64, 64), Image.LANCZOS), (x, 40))
pv.convert("RGB").save(os.path.join(HERE, "d3_header_preview.png"))
print(f"wrote 13 files; widest label {widest:.0f} px in a 98 px cell")
