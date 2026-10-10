#!/usr/bin/env python3
"""Draw the transparent KPI card background that sits under the KPI Cards sheet.

The sheet is 1400 x 110 px, drawn at 2x (2800 x 220) so the cards stay sharp on
high-density screens. Each card is an off-white rounded rectangle with a 1 px
border. Edges are drawn at 8x and averaged down, so they are anti-aliased.

Compensation Walk Summary page (dashboard 1400 x 850, filter rail 216 px wide,
30 px frame on the left, right and bottom, 16 px between cards):

    python3 make_kpi_cards_bg.py --left 246 --card-w 212 --gap 16 \
        --out ../arcadia_kpi_cards_bg_summary.png

Keep the numbers in step with the Tableau parameters on the KPI Cards sheet:
kpi_GridLeft = --left, kpi_CardW = --card-w, kpi_GapX = --gap, kpi_GridTop = --top.
"""
import argparse

from PIL import Image, ImageDraw

SS = 8        # supersampling factor
OUT_SCALE = 2  # delivered scale: 2800 x 220 for a 1400 x 110 sheet

FILL = (0xFB, 0xFB, 0xF8, 255)    # card off-white
BORDER = (0xE4, 0xE3, 0xDD, 255)  # hairline


def build(sheet_w, sheet_h, left, top, card_w, card_h, gap, cards, radius, out):
    k = SS * OUT_SCALE
    img = Image.new("RGBA", (sheet_w * k, sheet_h * k), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    for n in range(cards):
        x0 = (left + n * (card_w + gap)) * k
        y0 = top * k
        x1 = x0 + card_w * k - 1
        y1 = y0 + card_h * k - 1
        # border first, then the fill inset by 1 px
        d.rounded_rectangle([x0, y0, x1, y1], radius=radius * k, fill=BORDER)
        d.rounded_rectangle([x0 + k, y0 + k, x1 - k, y1 - k], radius=(radius - 1) * k, fill=FILL)
    img = img.resize((sheet_w * OUT_SCALE, sheet_h * OUT_SCALE), Image.LANCZOS)
    img.save(out, optimize=True)
    return img.size


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sheet-w", type=int, default=1400)
    ap.add_argument("--sheet-h", type=int, default=110)
    ap.add_argument("--left", type=int, default=246, help="left edge of card 1 (kpi_GridLeft)")
    ap.add_argument("--top", type=int, default=10, help="top edge of the cards inside the sheet (kpi_GridTop)")
    ap.add_argument("--card-w", type=int, default=212, help="kpi_CardW")
    ap.add_argument("--card-h", type=int, default=86, help="kpi_CardH")
    ap.add_argument("--gap", type=int, default=16, help="space between cards (kpi_GapX)")
    ap.add_argument("--cards", type=int, default=5)
    ap.add_argument("--radius", type=int, default=10)
    ap.add_argument("--out", default="arcadia_kpi_cards_bg_summary.png")
    a = ap.parse_args()
    size = build(a.sheet_w, a.sheet_h, a.left, a.top, a.card_w, a.card_h, a.gap, a.cards, a.radius, a.out)
    right = a.left + a.cards * a.card_w + (a.cards - 1) * a.gap
    print(f"{a.out}: {size[0]} x {size[1]}, cards from x {a.left} to x {right}")
