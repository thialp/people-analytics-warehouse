"""Dashboard #3 (Workforce Planning) field capsule with a drawn chevron.

The ▾ character in a Tableau label is too small to read as "open a list", so the chevron is part of the
image: a white capsule, 200 x 36 on the dashboard (box 32 tall, 4 transparent rows on top like fld_top),
with a solid navy chevron 10 px wide, 18 px from the right edge. The label (Semibold 9 navy) stays
centred on the image; keep it to about 140 px (22 characters) so it never reaches the chevron.

Usage: python3 docs/brand/build/make_d3_shapes.py && python3 docs/brand/build/organize_shapes.py
Writes docs/brand/shapes/Arcadia/fld_top_chevron.png -> by_dashboard/d3/d3_field_capsule.png
"""
from PIL import Image, ImageDraw, ImageFont
import os
from shape_quality import SS, finish

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "shapes", "Arcadia")
S = SS
NAVY, WHITE = (19, 35, 58, 255), (255, 255, 255, 255)
W, H, DROP = 800, 128, 16            # 4x design grid: 200 x 32 box, 4 px of transparent rows above

im = Image.new("RGBA", (W * S, (H + DROP) * S), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
d.rounded_rectangle((0, DROP * S, W * S - 1, (H + DROP) * S - 1), radius=(H // 2) * S, fill=WHITE)
cx, cy = (W - 72) * S, (DROP + H // 2 + 4) * S        # chevron centre: 18 px from the right edge
w2, h2 = 20 * S, 12 * S                              # 10 x 6 px on the dashboard
d.polygon([(cx - w2, cy - h2), (cx + w2, cy - h2), (cx, cy + h2)], fill=NAVY)
finish(im, W, H + DROP).save(os.path.join(OUT, "fld_top_chevron.png"))

# Preview on the navy band (not used by Tableau)
pv = Image.new("RGBA", (520, 80), NAVY)
f = ImageFont.truetype("/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 24)
for i, txt in enumerate(("FY26 Q3 · Jan – Mar 26", "All organizations")):
    cap = Image.open(os.path.join(OUT, "fld_top_chevron.png")).resize((240, 43), Image.LANCZOS)
    pv.alpha_composite(cap, (12 + i * 256, 18))
    ImageDraw.Draw(pv).text((12 + i * 256 + 120, 18 + 24), txt, font=ImageFont.truetype(
        "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf", 14), fill=NAVY, anchor="mm")
pv.convert("RGB").save(os.path.join(HERE, "d3_field_preview.png"))
print("wrote fld_top_chevron.png")
