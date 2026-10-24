"""Dashboard #3 popover lines: transparent PNGs with a 1 px line (white at 14%, like the rail divider).
Drawn at 2x so they stay crisp when Tableau fits them to the item size.

  d3_popover_line_wide.png      1728 x 18  -> item 864 x 9   (under the Period and View popover headers; 16 px inset each side)
  d3_popover_line_info.png       820 x 18  -> item 410 x 9   (under the Info popover header; 16 px inset each side)
  d3_popover_divider_period.png   48 x 384 -> item 24 x 192  (between Span List and Period Panel; 8 px inset top and bottom)
  d3_popover_divider_group.png    48 x 604 -> item 24 x 302  (between View List and Group Panel; 8 px inset top and bottom)

Usage: python3 docs/brand/build/make_d3_popover_lines.py docs/brand/shapes/by_dashboard/d3   (the four files are committed there)"""
import os, sys
from PIL import Image, ImageDraw

ALPHA = int(255 * 0.14)
out = sys.argv[1] if len(sys.argv) > 1 else "."


def hline(name, w, h, inset):
    im = Image.new("RGBA", (2 * w, 2 * h), (0, 0, 0, 0))
    y = h - 1                                   # 2 px at 2x, centred
    ImageDraw.Draw(im).rectangle((2 * inset, y, 2 * (w - inset) - 1, y + 1), fill=(255, 255, 255, ALPHA))
    im.save(os.path.join(out, name)); print(name, im.size)


def vline(name, w, h, inset):
    im = Image.new("RGBA", (2 * w, 2 * h), (0, 0, 0, 0))
    x = w - 1
    ImageDraw.Draw(im).rectangle((x, 2 * inset, x + 1, 2 * (h - inset) - 1), fill=(255, 255, 255, ALPHA))
    im.save(os.path.join(out, name)); print(name, im.size)


hline("d3_popover_line_wide.png", 864, 9, 16)
hline("d3_popover_line_info.png", 410, 9, 16)
vline("d3_popover_divider_period.png", 24, 192, 8)
vline("d3_popover_divider_group.png", 24, 302, 8)
