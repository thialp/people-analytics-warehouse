"""Draws docs/brand/arcadia_palettes.png from docs/brand/Preferences.tps (the one source).

    python3 docs/brand/build/make_palette_sheet.py
"""
import asyncio
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from playwright.async_api import async_playwright

BRAND = Path(__file__).resolve().parents[1]
USE = {
    "Arcadia 1 Categorical": "Roles: growth, decline, movement, one highlight",
    "Arcadia 2 Categorical Extended": "Identity for up to nine groups",
    "Arcadia 3 Categorical Light": "Large labelled fills with navy text (Sankey nodes)",
    "Arcadia 4 Systems": "Bridgeway (vendor system), Keystone (HR system), System feed",
    "Arcadia 5 Status": "On track, watch, at risk, no status",
    "Arcadia 6 Neutrals": "Navy to white: ink, rail, borders, text, totals, page, card",
    "Arcadia 7 Teal Sequential": "Magnitude",
    "Arcadia 8 Navy Sequential": "Quiet magnitude",
    "Arcadia 9 Coral-Teal Diverging": "Decline to growth, gray at zero",
}
LABELS = {
    "Arcadia 4 Systems": ["Bridgeway", "Keystone", "System feed"],
    "Arcadia 5 Status": ["On track", "Watch", "At risk", "No status"],
    "Arcadia 6 Neutrals": ["Navy", "Navy 2", "Slate", "Text gray", "Steel", "Silver", "Mist",
                           "Warm gray", "Hairline", "Page", "Card", "White"],
}


def lum(h):
    c = [int(h[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.03928 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def page():
    root = ET.parse(BRAND / "Preferences.tps").getroot()
    rows = []
    for p in root.iter("color-palette"):
        name, colors = p.get("name"), [c.text.strip() for c in p.iter("color")]
        labels = LABELS.get(name, [""] * len(colors))
        cells = "".join(
            f'<div class="sw"><div class="chip" style="background:{c};{"border:1px solid #D9D8D2;" if lum(c) > 0.85 else ""}"></div>'
            f'<div class="hex">{c}</div><div class="lab">{l}</div></div>' for c, l in zip(colors, labels))
        rows.append(f'<div class="row"><div class="name">{name}<span>{USE[name]} · {p.get("type")}</span></div><div class="cells">{cells}</div></div>')
    return f"""<!doctype html><html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
<style>body{{margin:0;background:#F3F3EF;font-family:Inter,sans-serif;color:#13233A}}
.wrap{{width:1400px;padding:32px 40px;box-sizing:border-box}}h1{{font-size:24px;margin:0 0 4px}}
.sub{{font-size:13px;color:#5A6170;margin-bottom:20px}}
.row{{display:flex;gap:24px;background:#FBFBF8;border:1px solid #E4E3DD;border-radius:8px;padding:14px 18px;margin-bottom:10px}}
.name{{width:250px;font-weight:700;font-size:14px;display:flex;flex-direction:column;gap:4px}}
.name span{{font-weight:400;font-size:11.5px;color:#5A6170}}
.cells{{display:flex;gap:9px;flex-wrap:wrap}}.sw{{width:72px}}.chip{{height:40px;border-radius:6px;box-sizing:border-box}}
.hex{{font-size:11px;font-weight:600;margin-top:5px}}.lab{{font-size:10.5px;color:#5A6170}}</style></head>
<body><div class="wrap"><h1>Arcadia palettes for Tableau</h1>
<div class="sub">One source: docs/brand/Preferences.tps. Pick from these under Edit Colors; never the eyedropper.</div>
{''.join(rows)}</div></body></html>"""


async def main():
    out = BRAND / "build" / "palette_sheet.html"
    out.write_text(page())
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page(viewport={"width": 1400, "height": 800})
        await pg.goto(out.as_uri())
        await pg.wait_for_timeout(800)
        await pg.screenshot(path=str(BRAND / "arcadia_palettes.png"), full_page=True)
        await b.close()
    out.unlink()

asyncio.run(main())
