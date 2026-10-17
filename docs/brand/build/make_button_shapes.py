"""Button shapes for the release 3 rebuild of Dashboards #1 and #2 (transparent PNGs).

Every clickable control becomes a Shape mark that draws one of these images, so a click
never shows a text-mark hover dot or a highlighted label (the text is in the image or in
a label laid over a full-size field image).

Usage: python3 docs/brand/build/make_button_shapes.py
Writes to docs/brand/shapes/Arcadia/ and a preview to docs/brand/build/button_preview.png.

| File | Cell on the dashboard | Drawn at | Used by |
|---|---|---|---|
| seg_worker_{employees,contingent,total}_{on,off} | 80 x 32 | 320 x 128 (label 12 px) | #1 top bar, Worker toggle (capsule #243A57) |
| fld_top | 180 x 36 | 720 x 144 (box 128 tall, 16 transparent rows on top so the label rides 2 px higher) | #1 top bar, Period Field and Group Field (white capsule, same radius as the toggle and Reset) |
| fld_rail | 200 x 32 | 800 x 128 (box 120 tall, 8 transparent rows on top) | #2 rail, Period Field and Group Field (white capsule like fld_top) |
| btn_reset_top_label | 184 x 32 | 736 x 128 | #1 top bar, Reset (outlined capsule: arrow + "Reset to default view") |
| btn_reset_top | 32 x 32 | 128 x 128 | Spare: arrow only, for a narrow header |
| btn_reset_rail | 188 x 30 | 752 x 120 | #2 rail, Reset (outlined button, as published) |
| btn_close | 16 x 16 | 64 x 64 | Both, the x on every popover (slate) |
| btn_close_light | 16 x 16 | 64 x 64 | Both, the x on navy popovers (mist) |
"""
from PIL import Image, ImageDraw, ImageFont
import math
import os
from shape_quality import SS, finish, out_size

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
S = SS  # supersample (shape_quality.py), then shrink once with LANCZOS and sharpen lightly

NAVY = (19, 35, 58, 255)
WHITE = (255, 255, 255, 255)
MIST = (201, 209, 220, 255)
WASH = (228, 227, 221, 255)       # #E4E3DD
SLATE = (90, 97, 112, 255)        # #5A6170
RAIL_TEXT = (184, 192, 204, 255)  # #B8C0CC


def canvas(w, h):
    im = Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))
    return im, ImageDraw.Draw(im)


def save(im, w, h, name):
    finish(im, w, h).save(os.path.join(OUT, name + ".png"))


# 1. Worker toggle segments (same look as seg_headcount_* on Dashboard #1)
def segment(label, on, name, w=320, h=128):
    im, d = canvas(w, h)
    if on:
        d.rounded_rectangle((10 * S, 10 * S, (w - 10) * S, (h - 10) * S), radius=((h - 20) // 2) * S, fill=WHITE)
    f = ImageFont.truetype(FONT, 47 * S)
    d.text((w * S // 2, h * S // 2), label, font=f, fill=NAVY if on else MIST, anchor="mm")
    save(im, w, h, name)


for key, label in (("employees", "Employees"), ("contingent", "Contingent"), ("total", "Total")):
    for on in (True, False):
        segment(label, on, f"seg_worker_{key}_{'on' if on else 'off'}")


# 2. Field backgrounds (the text is the mark's label, laid over the image)
def field(name, w, h, fill, radius, drop=0):
    """drop = extra transparent rows above the box (4x grid px). Tableau centres the label on the image,
    so drawing the box lower moves the text up inside it."""
    im, d = canvas(w, h + drop)
    d.rounded_rectangle((0, drop * S, w * S - 1, (h + drop) * S - 1), radius=radius * S, fill=fill)
    save(im, w, h + drop, name)


field("fld_top", 720, 128, WHITE, 64, drop=16)  # 16 grid px of padding above = box sits 2 dashboard px below the canvas centre, so the label rides 2 px higher in it
field("fld_rail", 800, 120, WHITE, 60, drop=8)  # white capsule like fld_top; 8 grid px above = label rides 1 px higher


# 3. Reset: a circular arrow
def reset_arrow(d, cx, cy, r, width, col):
    box = (cx - r, cy - r, cx + r, cy + r)
    d.arc(box, start=-60, end=230, fill=col, width=width)
    a = math.radians(-60)
    tip = (cx + r * math.cos(a), cy + r * math.sin(a))
    L = width * 2.2
    d.polygon([
        (tip[0] + L * 0.9, tip[1] - L * 0.15),
        (tip[0] - L * 0.55, tip[1] - L * 0.95),
        (tip[0] - L * 0.25, tip[1] + L * 0.85),
    ], fill=col)


im, d = canvas(128, 128)
reset_arrow(d, 64 * S, 66 * S, 38 * S, 9 * S, WHITE)
save(im, 128, 128, "btn_reset_top")

# #1 top bar: a capsule, arrow + words, so it reads as a button and not as a loading spinner
w, h = 736, 128
im, d = canvas(w, h)
d.rounded_rectangle((4 * S, 4 * S, (w - 4) * S, (h - 4) * S), radius=((h - 8) // 2) * S, outline=(255, 255, 255, 120), width=4 * S)
f = ImageFont.truetype(FONT, 52 * S)
label = "Reset to default view"
ar, gap = 22, 18                      # arrow radius and gap, px at 4x scale
tw = d.textlength(label, font=f) / S
group = 2 * ar + gap + tw
x0 = (w - group) / 2                  # centre arrow + words as one group
reset_arrow(d, int((x0 + ar) * S), 66 * S, ar * S, 6 * S, WHITE)
d.text((int((x0 + 2 * ar + gap) * S), h * S // 2), label, font=f, fill=WHITE, anchor="lm")
save(im, w, h, "btn_reset_top_label")

w, h = 752, 120
im, d = canvas(w, h)
d.rounded_rectangle((4 * S, 4 * S, (w - 4) * S, (h - 4) * S), radius=((h - 8) // 2) * S, outline=(255, 255, 255, 120), width=4 * S)
reset_arrow(d, 150 * S, 61 * S, 17 * S, 5 * S, WHITE)
f = ImageFont.truetype(FONT, 40 * S)
d.text((190 * S, h * S // 2), "Reset to default view", font=f, fill=WHITE, anchor="lm")
save(im, w, h, "btn_reset_rail")


# 4. Close (x)
def close(name, col):
    im, d = canvas(64, 64)
    for a, b in (((18, 18), (46, 46)), ((46, 18), (18, 46))):
        d.line([(a[0] * S, a[1] * S), (b[0] * S, b[1] * S)], fill=col, width=6 * S)
    save(im, 64, 64, name)


close("btn_close", SLATE)
close("btn_close_light", RAIL_TEXT)


# Preview (not used by Tableau): #1 top bar and #2 rail controls
pv = Image.new("RGBA", (1000, 260), (19, 35, 58, 255))
pd = ImageDraw.Draw(pv)
lab = ImageFont.truetype(FONT, 18)
pd.text((24, 14), "Dashboard #1 top bar", font=lab, fill=MIST)
for i, (n, txt) in enumerate((("fld_top", "FY26 · Jun 25 → Jun 26"), ("fld_top", "Commercial"))):
    im = Image.open(os.path.join(OUT, n + ".png")).resize((216, 38), Image.LANCZOS)
    pv.alpha_composite(im, (24 + i * 228, 48))
    pd.text((24 + i * 228 + 100, 67), txt, font=ImageFont.truetype(FONT, 14), fill=NAVY, anchor="mm")
    x0 = 24 + i * 228 + 100 + pd.textlength(txt, font=ImageFont.truetype(FONT, 14)) / 2 + 8
    pd.polygon([(x0, 64), (x0 + 8, 64), (x0 + 4, 70)], fill=NAVY)  # the label's chevron, as Tableau draws it
cap = Image.new("RGBA", (288, 38), (0, 0, 0, 0))
ImageDraw.Draw(cap).rounded_rectangle((0, 0, 287, 37), radius=19, fill=(36, 58, 87, 255))
for i, (k, on) in enumerate((("employees", True), ("contingent", False), ("total", False))):
    seg = Image.open(os.path.join(OUT, f"seg_worker_{k}_{'on' if on else 'off'}.png")).resize((96, 38), Image.LANCZOS)
    cap.alpha_composite(seg, (i * 96, 0))
pv.alpha_composite(cap, (486, 48))
for x, n in ((800, "btn_reset_top"), (860, "info_open")):
    pv.alpha_composite(Image.open(os.path.join(OUT, n + ".png")).resize((38, 38), Image.LANCZOS), (x, 48))
pd.text((24, 120), "Dashboard #2 rail", font=lab, fill=MIST)
im = Image.open(os.path.join(OUT, "fld_rail.png")).resize((240, 36), Image.LANCZOS)
pv.alpha_composite(im, (24, 154))
pd.text((36, 172), "Commercial", font=ImageFont.truetype(FONT, 14), fill=NAVY, anchor="lm")
pd.polygon([(124, 169), (132, 169), (128, 175)], fill=NAVY)
pv.alpha_composite(Image.open(os.path.join(OUT, "btn_reset_rail.png")).resize((226, 36), Image.LANCZOS), (290, 154))
for x, n in ((560, "btn_close_light"), (600, "rail_info_open")):
    pv.alpha_composite(Image.open(os.path.join(OUT, n + ".png")).resize((24, 24), Image.LANCZOS), (x, 160))
card = Image.new("RGBA", (40, 40), (251, 251, 248, 255))
card.alpha_composite(Image.open(os.path.join(OUT, "btn_close.png")).resize((24, 24), Image.LANCZOS), (8, 8))
pv.alpha_composite(card, (640, 152))
pv.convert("RGB").save(os.path.join(HERE, "button_preview.png"))
print("wrote", len([f for f in os.listdir(OUT) if f.startswith(("seg_worker", "fld_", "btn_reset", "btn_close"))]), "files")
