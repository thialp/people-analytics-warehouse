"""Dashboard #5 (Seats to Fill) shapes and legend images, drawn like Dashboard #4's.

  python3 docs/brand/build/make_d5_shapes.py     writes docs/brand/shapes/by_dashboard/d5/*.png

Designed on the 4x grid, drawn at SS x that and shrunk once (shape_quality.finish); delivered at 3 px per
dashboard px.

  d5_chip_teal       56 x 18   pill #9FD6C3 (the 75-100% and 100%+ bands): a fiscal year at or above 75% of plan
  d5_chip_slate      56 x 18   pill #B9C3D1 (the bands under 75%)
                               Tableau writes the percentage on top (FY Chips sheet, build guide 7.4)
  d5_main_legend     600 x 20  image: PIDs filled (navy line), Forecast (teal line), Likely range (teal light),
                               Budget (slate line)
  d5_backtest_legend 388 x 18  image: Forecast range, Average, Actual in range (filled), Outside (open)

The chips are shapes (Shapes/Arcadia D5); the two legends are images placed on the dashboard (Fit Image).
"""
import os
import sys
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from shape_quality import SS, finish

OUT = os.path.join(HERE, "..", "shapes", "by_dashboard", "d5")
os.makedirs(OUT, exist_ok=True)
S = SS
NAVY, SLATE, INK = (19, 35, 58, 255), (90, 97, 112, 255), (31, 35, 41, 255)
TEAL_D, TEAL_L = (15, 110, 86, 255), (211, 238, 228, 255)
CHIP_TEAL, CHIP_SLATE = (159, 214, 195, 255), (185, 195, 209, 255)
BOOK = "/usr/share/fonts/opentype/inter/Inter-Regular.otf"


def canvas(w, h):
    return Image.new("RGBA", (w * S, h * S), (0, 0, 0, 0))


def chip(colour):
    W, H = 224, 72                                     # 56 x 18
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((0, 0, W * S - 1, H * S - 1), radius=(H // 2) * S, fill=colour)
    return finish(im, W, H)


def legend(items, w, h, gap=72):
    """items: (kind, colour, label); kind line, dash, band, dot, ring. Drawn on the 4x grid."""
    W, H = w * 4, h * 4
    im = canvas(W, H)
    d = ImageDraw.Draw(im)
    font = ImageFont.truetype(BOOK, 42 * S)            # 10.5 dashboard px
    x, cy = 0, H // 2
    for kind, colour, label in items:
        if kind in ("line", "dash"):
            seg = 56
            if kind == "line":
                d.line((x * S, cy * S, (x + seg) * S, cy * S), fill=colour, width=9 * S)
            else:
                for k in range(0, seg, 20):
                    d.line(((x + k) * S, cy * S, (x + min(k + 12, seg)) * S, cy * S), fill=colour, width=8 * S)
            x += seg + 20
        elif kind == "band":
            d.rounded_rectangle((x * S, (cy - 18) * S, (x + 56) * S, (cy + 18) * S), radius=8 * S, fill=colour)
            x += 56 + 20
        elif kind == "tick":
            d.rounded_rectangle((x * S, (cy - 18) * S, (x + 40) * S, (cy + 18) * S), radius=8 * S, fill=TEAL_L)
            d.line(((x + 2) * S, cy * S, (x + 38) * S, cy * S), fill=colour, width=8 * S)
            x += 40 + 20
        elif kind in ("dot", "ring"):
            r = 16
            box = ((x) * S, (cy - r) * S, (x + 2 * r) * S, (cy + r) * S)
            if kind == "dot":
                d.ellipse(box, fill=colour)
            else:
                d.ellipse(box, outline=colour, width=6 * S)
            x += 2 * r + 20
        tb = d.textbbox((0, 0), label, font=font)
        d.text((x * S, cy * S - (tb[1] + tb[3]) / 2), label, font=font, fill=SLATE)
        x += (tb[2] - tb[0]) / S + gap
    return finish(im, W, H)


def main():
    chip(CHIP_TEAL).save(os.path.join(OUT, "d5_chip_teal.png"))
    chip(CHIP_SLATE).save(os.path.join(OUT, "d5_chip_slate.png"))
    legend([("line", NAVY, "PIDs filled"), ("line", TEAL_D, "Forecast"), ("band", TEAL_L, "Likely range"),
            ("line", SLATE, "Budget")], 600, 20).save(os.path.join(OUT, "d5_main_legend.png"))
    legend([("band", TEAL_L, "Forecast range"), ("tick", TEAL_D, "Average"), ("dot", NAVY, "Actual, in range"),
            ("ring", NAVY, "Outside")], 388, 18, gap=48).save(os.path.join(OUT, "d5_backtest_legend.png"))
    for f in sorted(os.listdir(OUT)):
        im = Image.open(os.path.join(OUT, f))
        print(f"   {f:<24}{im.size[0]:>5} x {im.size[1]}")


if __name__ == "__main__":
    main()
