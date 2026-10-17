"""Rail toggle shapes for the Compensation Walk (transparent PNGs, 4x of an 88x30 cell).
Usage: python3 make_rail_toggle_shapes.py [capsule_hex] [pill_hex]
  capsule_hex: only used for the preview. pill_hex: fill of the selected option (default E4E3DD, the brand border/wash)"""
from PIL import Image, ImageDraw, ImageFont
import os, sys
from shape_quality import SS, finish, out_size
OUT = os.path.join(os.path.dirname(__file__), "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
S, W, H = SS, 352, 120
NAVY, MIST = (19, 35, 58, 255), (201, 209, 220, 255)
CAP = sys.argv[1].lstrip("#") if len(sys.argv) > 1 else "1D3150"
CAP = tuple(int(CAP[i:i+2], 16) for i in (0, 2, 4)) + (255,)
PILL = sys.argv[2].lstrip("#") if len(sys.argv) > 2 else "E4E3DD"
WHITE = tuple(int(PILL[i:i+2], 16) for i in (0, 2, 4)) + (255,)

OPTIONS = {
    "lens_fte": "Avg per FTE", "lens_amount": "Total payroll",
    "cost_loaded": "Loaded", "cost_base": "Base",
    "currency_constant": "Constant", "currency_nominal": "Nominal",
}

def segment(label, on, path):
    im = Image.new("RGBA", (W*S, H*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if on:
        d.rounded_rectangle((8*S, 8*S, (W-8)*S, (H-8)*S), radius=14*S, fill=WHITE)
    f = ImageFont.truetype(FONT, 40*S)
    d.text((W*S//2, H*S//2), label, font=f, fill=NAVY if on else MIST, anchor="mm")
    finish(im, W, H).save(path)

for key, lab in OPTIONS.items():
    for on in (True, False):
        segment(lab, on, f"{OUT}/seg_{key}_{'on' if on else 'off'}.png")

# preview: three capsules on the rail navy
pv = Image.new("RGB", (240*2, 3*70), (19, 35, 58))
for r, (a, b) in enumerate((("lens_fte", "lens_amount"), ("cost_loaded", "cost_base"), ("currency_constant", "currency_nominal"))):
    cap = Image.new("RGBA", (352*2, 120), (0, 0, 0, 0)); d = ImageDraw.Draw(cap)
    d.rounded_rectangle((0, 0, 703, 119), radius=16, fill=CAP)
    for i, (k, on) in enumerate(((a, True), (b, False))):
        cap.alpha_composite(Image.open(f"{OUT}/seg_{k}_{'on' if on else 'off'}.png"), (i*352, 0))
    cap = cap.resize((240, 41), Image.LANCZOS)
    pv.paste(cap, (20, r*70+14), cap)
pv = pv.resize((480, 210))
pv.save(os.path.join(os.path.dirname(__file__), "rail_toggle_preview.png"))
