"""Arcadia toggle + info shapes for Tableau (transparent PNGs, 2x resolution).
Segment cell = 75x32 px on the dashboard, drawn at 300x128 so it stays crisp."""
from PIL import Image, ImageDraw, ImageFont
import os
OUT = os.path.join(os.path.dirname(__file__), "..", "shapes", "Arcadia")
os.makedirs(OUT, exist_ok=True)
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"
if not os.path.exists(FONT):
    FONT = "/usr/share/fonts/opentype/inter/Inter-Bold.otf"
S = 4  # supersample
W, H = 300, 128
NAVY, WHITE, MIST = (19, 35, 58, 255), (255, 255, 255, 255), (201, 209, 220, 255)

def segment(label, on, path):
    im = Image.new("RGBA", (W*S, H*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    if on:  # white pill inset inside the dark capsule
        d.rounded_rectangle((10*S, 10*S, (W-10)*S, (H-10)*S), radius=((H-20)//2)*S, fill=WHITE)
    f = ImageFont.truetype(FONT, 46*S)
    col = NAVY if on else MIST
    d.text((W*S//2, H*S//2), label, font=f, fill=col, anchor="mm")
    im.resize((W, H), Image.LANCZOS).save(path)

for lab in ("Headcount", "FTE"):
    for on in (True, False):
        segment(lab, on, f"{OUT}/seg_{lab.lower()}_{'on' if on else 'off'}.png")

def info(path, closed):
    N = 128
    im = Image.new("RGBA", (N*S, N*S), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    d.ellipse((8*S, 8*S, (N-8)*S, (N-8)*S), outline=WHITE, width=7*S)
    if closed:  # "X" when the panel is open
        for a, b in (((40, 40), (88, 88)), ((88, 40), (40, 88))):
            d.line([(a[0]*S, a[1]*S), (b[0]*S, b[1]*S)], fill=WHITE, width=8*S)
    else:       # "i"
        d.ellipse((57*S, 30*S, 71*S, 44*S), fill=WHITE)
        d.rounded_rectangle((57*S, 54*S, 71*S, 98*S), radius=5*S, fill=WHITE)
    im.resize((N, N), Image.LANCZOS).save(path)
info(f"{OUT}/info_open.png", False)
info(f"{OUT}/info_close.png", True)

# preview of the finished header controls (not used by Tableau)
bg = Image.new("RGB", (640, 120), (19, 35, 58))
cap = Image.new("RGBA", (150*2, 32*2), (0, 0, 0, 0)); cd = ImageDraw.Draw(cap)
cd.rounded_rectangle((0, 0, 299, 63), radius=32, fill=(36, 58, 87, 255))
for i, (lab, on) in enumerate((("Headcount", True), ("FTE", False))):
    seg = Image.open(f"{OUT}/seg_{lab.lower()}_{'on' if on else 'off'}.png").resize((150, 64), Image.LANCZOS)
    cap.alpha_composite(seg, (i*150, 0))
bg.paste(cap, (60, 28), cap)
ic = Image.open(f"{OUT}/info_open.png").resize((64, 64), Image.LANCZOS)
bg.paste(ic, (400, 28), ic)
ic = Image.open(f"{OUT}/info_close.png").resize((64, 64), Image.LANCZOS)
bg.paste(ic, (500, 28), ic)
bg.save(os.path.join(os.path.dirname(__file__), "toggle_preview.png"))
