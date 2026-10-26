"""Dashboard #4 (Contingent Workforce Reconciliation) rail shapes, drawn like Dashboard #2 and #3's.

  python3 docs/brand/build/make_d4_shapes.py        writes docs/brand/shapes/by_dashboard/d4/*.png
                                                    and docs/brand/build/d4_shapes_preview.png

All shapes are designed on the 4x grid (a 200 x 32 box is 800 x 128), drawn at SS x that and shrunk once
(shape_quality.finish), so they match the other dashboards' edges. Delivered at 3 px per dashboard px.

  d4_field_capsule        200 x 32  white capsule, navy chevron 18 px from the right (Point in time)
  d4_field_capsule_dark   200 x 32  #1B2D45 capsule, #4A5B73 outline, light chevron (Function, Department, Country)
  d4_show_overview_on/off, d4_show_gaplist_on/off
                          100 x 32  white pill with navy words when on; light words only when off. They sit on the
                                    navy capsule of the `Show Toggle` sheet (build doc 10.2)
  d4_reset                200 x 32  outlined capsule, the reset arrow and "Reset to default view"
  d4_tick_on/off/dim       12 x 12  teal square with a white tick; outlined #B8C0CC; outlined #56657E (dim)
"""
import math
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from shape_quality import SS, finish

OUT = os.path.join(HERE, "..", "shapes", "by_dashboard", "d4")
os.makedirs(OUT, exist_ok=True)
NAVY, WHITE = (19, 35, 58, 255), (255, 255, 255, 255)
DARK, DARK_LINE, LIGHT = (27, 45, 69, 255), (74, 91, 115, 255), (185, 195, 209, 255)   # #1B2D45 #4A5B73 #B9C3D1
RESET_LINE = (138, 151, 168, 255)                                                      # #8A97A8
TEAL, TICK_OFF, TICK_DIM = (93, 202, 165, 255), (184, 192, 204, 255), (86, 101, 126, 255)
SEMI = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
S = SS


def canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def chevron(d, cx, cy, colour):
    w2, h2 = 20 * S, 12 * S                                   # 10 x 6 dashboard px
    d.polygon([(cx - w2, cy - h2), (cx + w2, cy - h2), (cx, cy + h2)], fill=colour)


def capsule(dark):
    W, H = 800, 128
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    if dark:
        d.rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=(H // 2) * S, fill=DARK_LINE)
        d.rounded_rectangle((4 * S, 4 * S, (W - 4) * S - 1, (H - 4) * S - 1), radius=(H // 2 - 4) * S, fill=DARK)
    else:
        d.rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=(H // 2) * S, fill=WHITE)
    chevron(d, (W - 72) * S, (H // 2 + 4) * S, LIGHT if dark else NAVY)
    return finish(im, W, H)


def toggle(word, on):
    W, H = 400, 128                                            # 100 x 32
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    if on:
        d.rounded_rectangle((8 * S, 8 * S, (W - 8) * S - 1, (H - 8) * S - 1), radius=(H // 2 - 8) * S, fill=WHITE)
    font = ImageFont.truetype(SEMI, 40 * S)                    # about 10 px on the page
    d.text((W * S // 2, H * S // 2 + 1 * S), word, font=font, fill=NAVY if on else LIGHT, anchor="mm")
    return finish(im, W, H)


def reset():
    W, H = 800, 128
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=(H // 2) * S, fill=RESET_LINE)
    d.rounded_rectangle((4 * S, 4 * S, (W - 4) * S - 1, (H - 4) * S - 1), radius=(H // 2 - 4) * S, fill=(0, 0, 0, 0))
    font = ImageFont.truetype(SEMI, 40 * S)
    text = "Reset to default view"
    tw = d.textlength(text, font=font)
    icon = 44 * S
    gap = 16 * S
    x0 = (W * S - (icon + gap + tw)) / 2
    cx, cy, r = x0 + icon / 2, H * S / 2, 17 * S
    d.arc((cx - r, cy - r, cx + r, cy + r), start=-60, end=250, fill=WHITE, width=int(5 * S))
    a = math.radians(-60)                                      # arrow head at the open end of the arc
    px, py = cx + r * math.cos(a), cy + r * math.sin(a)
    d.polygon([(px - 5 * S, py - 17 * S), (px + 17 * S, py - 5 * S), (px - 3 * S, py + 8 * S)], fill=WHITE)
    d.text((x0 + icon + gap, H * S / 2 + 1 * S), text, font=font, fill=WHITE, anchor="lm")
    return finish(im, W, H)


def tick(kind):
    W = H = 48                                                 # 12 x 12
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    box = (3 * S, 3 * S, (W - 3) * S - 1, (H - 3) * S - 1)
    if kind == "on":
        d.rounded_rectangle(box, radius=6 * S, fill=TEAL)
        d.line([(14 * S, 25 * S), (21 * S, 32 * S), (34 * S, 16 * S)], fill=WHITE, width=int(5 * S), joint="curve")
    else:
        d.rounded_rectangle(box, radius=6 * S, outline=TICK_OFF if kind == "off" else TICK_DIM, width=int(3.5 * S))
    return finish(im, W, H)


FILES = {
    "d4_field_capsule": capsule(False),
    "d4_field_capsule_dark": capsule(True),
    "d4_show_overview_on": toggle("Overview", True),
    "d4_show_overview_off": toggle("Overview", False),
    "d4_show_gaplist_on": toggle("Gap list", True),
    "d4_show_gaplist_off": toggle("Gap list", False),
    "d4_reset": reset(),
    "d4_tick_on": tick("on"),
    "d4_tick_off": tick("off"),
    "d4_tick_dim": tick("dim"),
}
for name, im in FILES.items():
    im.save(os.path.join(OUT, name + ".png"))
    print("wrote", name, im.size)

# Preview on the navy rail (not used by Tableau)
pv = Image.new("RGBA", (640, 300), NAVY)
y = 12
for name in ("d4_field_capsule", "d4_field_capsule_dark", "d4_reset"):
    im = FILES[name].resize((300, 48), Image.LANCZOS)
    pv.alpha_composite(im, (12, y)); y += 58
bar = Image.new("RGBA", (300, 48), (0, 0, 0, 0))
ImageDraw.Draw(bar).rounded_rectangle((0, 0, 299, 47), radius=24, fill=DARK)
bar.alpha_composite(FILES["d4_show_overview_on"].resize((150, 48), Image.LANCZOS), (0, 0))
bar.alpha_composite(FILES["d4_show_gaplist_off"].resize((150, 48), Image.LANCZOS), (150, 0))
pv.alpha_composite(bar, (12, y)); y += 58
bar2 = Image.new("RGBA", (300, 48), (0, 0, 0, 0))
ImageDraw.Draw(bar2).rounded_rectangle((0, 0, 299, 47), radius=24, fill=DARK)
bar2.alpha_composite(FILES["d4_show_overview_off"].resize((150, 48), Image.LANCZOS), (0, 0))
bar2.alpha_composite(FILES["d4_show_gaplist_on"].resize((150, 48), Image.LANCZOS), (150, 0))
pv.alpha_composite(bar2, (12, y))
for i, k in enumerate(("on", "off", "dim")):
    pv.alpha_composite(FILES[f"d4_tick_{k}"].resize((36, 36), Image.LANCZOS), (360 + i * 60, 20))
pv.convert("RGB").save(os.path.join(HERE, "d4_shapes_preview.png"))
