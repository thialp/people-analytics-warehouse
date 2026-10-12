"""Arcadia rail divider: a transparent PNG that replaces a 24 px Blank in the rail.
Drawn at 2x (400 x 48) so it stays crisp when Tableau scales it to 200 x 24.
The line is white at 14% opacity, 1 px (2 px at 2x), centered vertically, full width.
Usage: python3 make_rail_divider.py [out_path]"""
import sys, os
from PIL import Image, ImageDraw

W, H = 400, 48          # 2x of the 200 x 24 item
ALPHA = int(255 * 0.14)
out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(__file__), "..", "arcadia_rail_divider.png")

im = Image.new("RGBA", (W, H), (0, 0, 0, 0))
d = ImageDraw.Draw(im)
y = H // 2 - 1
d.rectangle((0, y, W - 1, y + 1), fill=(255, 255, 255, ALPHA))
im.save(out)

# preview over the rail navy (not used by Tableau)
prev = Image.new("RGBA", (W, 3 * H), (19, 35, 58, 255))
for i in range(3):
    prev.alpha_composite(im, (0, i * H))
prev.convert("RGB").save(os.path.join(os.path.dirname(out), "build", "rail_divider_preview.png"))
print(out, im.size)
