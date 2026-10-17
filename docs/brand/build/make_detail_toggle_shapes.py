"""Waterfall detail toggle for Dashboard #1 (and #2): 'Summary | By driver'.
Transparent PNGs, 4x of a 76 x 24 px cell (drawn 304 x 96). The grey capsule behind the two cells is the
dashboard item's own background (#ECEBE5, corner radius 12), so the shapes only draw the selected pill and the labels.
Usage: python3 make_detail_toggle_shapes.py"""
from PIL import Image, ImageDraw, ImageFont
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
S, W, H = 4, 304, 96
NAVY, WHITE, SLATE = (19, 35, 58, 255), (255, 255, 255, 255), (91, 107, 128, 255)
OPTIONS = {"summary": "Summary", "drivers": "By driver"}

def segment(label, on, path):
    im = Image.new("RGBA", (W*S, H*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if on:  # navy pill inset inside the grey capsule
        d.rounded_rectangle((6*S, 6*S, (W-6)*S, (H-6)*S), radius=((H-12)//2)*S, fill=NAVY)
    f = ImageFont.truetype(FONT, 36*S)
    d.text((W*S//2, H*S//2), label, font=f, fill=WHITE if on else SLATE, anchor="mm")
    im.resize((W, H), Image.LANCZOS).save(path)

for key, lab in OPTIONS.items():
    for on in (True, False):
        segment(lab, on, f"{OUT}/seg_detail_{key}_{'on' if on else 'off'}.png")

# preview (not used by Tableau): both states on the cream card
pv = Image.new("RGB", (400, 200), (251, 251, 248))
for r, on_key in enumerate(("summary", "drivers")):
    cap = Image.new("RGBA", (W*2, H), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
    d.rounded_rectangle((0, 0, W*2-1, H-1), radius=H//2, fill=(236, 235, 229, 255))
    for i, k in enumerate(OPTIONS):
        cap.alpha_composite(Image.open(f"{OUT}/seg_detail_{k}_{'on' if k == on_key else 'off'}.png"), (i*W, 0))
    cap = cap.resize((W*2//2, H//2), Image.LANCZOS)
    pv.paste(cap, (40, 30 + r*70), cap)
pv.save(os.path.join(os.path.dirname(__file__), "detail_toggle_preview.png"))
