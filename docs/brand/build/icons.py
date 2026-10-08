"""Build the Arcadia icon set and the Tableau custom-shape pack.

Two steps:

  1. Import (only when refreshing from upstream):
         python3 icons.py --import /path/to/heroicons
     Reads Heroicons' 24 px outline SVGs, keeps the icons listed in ICONS,
     restyles them (Arcadia stroke weight, currentColor) and saves them as
     docs/brand/icons/svg/<arcadia-name>.svg.

  2. Build (default):
         python3 icons.py
     Renders every SVG in docs/brand/icons/svg into each color set below as a
     64 x 64 transparent PNG, writes docs/brand/icons/Arcadia_Tableau_Shapes.zip
     (one folder per set, ready for My Tableau Public Repository/Shapes) and the
     preview sheet docs/brand/icons/arcadia_icons_preview.png.

Needs Python with playwright (Chromium), the same as render.py.
"""
import argparse
import re
import shutil
import zipfile
from pathlib import Path

from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
OUT = HERE.parent / "icons"
SVG_DIR = OUT / "svg"
STROKE = "1.75"  # Heroicons ships 1.5; 1.75 holds up better at Tableau's 16-32 px shape sizes
SIZE = 64        # PNG size: crisp on high-DPI screens, scale down with Tableau's size slider

# Arcadia name -> Heroicons outline name. The prefix groups icons in Tableau's shape picker,
# which sorts by file name.
ICONS = {
    # people and organization
    "people-headcount": "users", "people-team": "user-group", "people-person": "user",
    "people-hire": "user-plus", "people-leaver": "user-minus", "people-profile": "user-circle",
    "people-id": "identification", "people-promotion": "academic-cap", "people-role": "briefcase",
    "org-office": "building-office", "org-campus": "building-office-2", "org-home": "home",
    # movement and trend
    "move-transfer": "arrows-right-left", "trend-up": "arrow-trending-up", "trend-down": "arrow-trending-down",
    "delta-up": "arrow-up-right", "delta-down": "arrow-down-right", "arrow-up": "arrow-up", "arrow-down": "arrow-down",
    # finance
    "fin-currency": "currency-dollar", "fin-pay": "banknotes", "fin-equity": "scale",
    "fin-rate": "receipt-percent", "fin-calculator": "calculator", "fin-budget": "wallet",
    # geography and time
    "geo-globe": "globe-americas", "geo-location": "map-pin", "geo-map": "map",
    "time-calendar": "calendar", "time-period": "calendar-days", "time-clock": "clock",
    # analytics and data
    "viz-bar": "chart-bar", "viz-pie": "chart-pie", "viz-line": "presentation-chart-line",
    "viz-table": "table-cells", "viz-dashboard": "squares-2x2", "viz-filter": "funnel",
    "viz-controls": "adjustments-horizontal", "viz-search": "magnifying-glass",
    "data-warehouse": "circle-stack", "data-formula": "variable", "data-code": "code-bracket",
    # status and data quality
    "status-ok": "check-circle", "status-warning": "exclamation-triangle", "status-alert": "exclamation-circle",
    "status-error": "x-circle", "status-info": "information-circle", "status-help": "question-mark-circle",
    "status-verified": "shield-check", "status-flag": "flag", "status-insight": "light-bulb", "status-star": "star",
    # navigation and actions
    "nav-chevron-down": "chevron-down", "nav-chevron-right": "chevron-right", "nav-external": "arrow-top-right-on-square",
    "act-download": "arrow-down-tray", "act-refresh": "arrow-path", "act-docs": "document-text",
    "act-method": "book-open", "act-link": "link", "act-view": "eye",
    "act-plus": "plus", "act-minus": "minus", "act-close": "x-mark",
}

# Line sets: the icon stroke in one color on a transparent background.
LINE_SETS = {
    "Arcadia Mono": "#000000",   # black: Tableau tints transparent shapes from the Color shelf
    "Arcadia Navy": "#13233A",
    "Arcadia Slate": "#5A6170",
    "Arcadia White": "#FFFFFF",  # for the navy header band
    "Arcadia Teal": "#00938D",
    "Arcadia Coral": "#E4572E",
}
# Badge sets: a white icon on a rounded tile, for KPI cards and status markers.
BADGE_SETS = {
    "Arcadia Badge Navy": "#13233A",
    "Arcadia Badge Teal": "#00938D",
    "Arcadia Badge Coral": "#E4572E",
    "Arcadia Badge Violet": "#5B4FB3",
}


def import_from_heroicons(src: Path) -> None:
    outline = src / "optimized" / "24" / "outline"
    SVG_DIR.mkdir(parents=True, exist_ok=True)
    for old in SVG_DIR.glob("*.svg"):
        old.unlink()
    for name, hero in ICONS.items():
        svg = (outline / f"{hero}.svg").read_text()
        svg = re.sub(r'\s(aria-hidden|data-slot)="[^"]*"', "", svg)
        svg = svg.replace('stroke-width="1.5"', f'stroke-width="{STROKE}"')
        svg = svg.replace("<svg ", f'<svg width="24" height="24" ', 1)
        svg = svg.replace("<svg ", f"<svg data-arcadia=\"{name}\" data-source=\"heroicons/{hero}\" ", 1)
        (SVG_DIR / f"{name}.svg").write_text(svg.strip() + "\n")
    shutil.copy(src / "LICENSE", OUT / "LICENSE-heroicons.txt")
    print(f"Imported {len(ICONS)} icons into {SVG_DIR.relative_to(HERE.parent.parent.parent)}")


def tile(svg: str, color: str, badge: str | None) -> str:
    icon = svg.replace("currentColor", color)
    if badge is None:
        inner = icon.replace("<svg ", f'<svg style="position:absolute;inset:4px;width:{SIZE - 8}px;height:{SIZE - 8}px" ', 1)
        return f'<div id="t" style="position:relative;width:{SIZE}px;height:{SIZE}px">{inner}</div>'
    pad = 16
    inner = icon.replace("<svg ", f'<svg style="position:absolute;inset:{pad}px;width:{SIZE - 2 * pad}px;height:{SIZE - 2 * pad}px" ', 1)
    return (f'<div id="t" style="position:relative;width:{SIZE}px;height:{SIZE}px;border-radius:14px;'
            f'background:{badge}">{inner}</div>')


def build() -> None:
    svgs = sorted(SVG_DIR.glob("*.svg"))
    stage = HERE / "_shapes"
    shutil.rmtree(stage, ignore_errors=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(device_scale_factor=1)
        jobs = [(s, c, None) for s, c in LINE_SETS.items()] + [(s, "#FFFFFF", bg) for s, bg in BADGE_SETS.items()]
        for set_name, color, badge in jobs:
            folder = stage / set_name
            folder.mkdir(parents=True)
            for f in svgs:
                page.set_content(f'<html><body style="margin:0;background:transparent">{tile(f.read_text(), color, badge)}</body></html>')
                page.locator("#t").screenshot(path=str(folder / f"{f.stem}.png"), omit_background=True)
        # preview sheet for the README
        cells = "".join(
            f'<div class="c">{f.read_text().replace("currentColor", "#13233A").replace("<svg ", "<svg class=i ", 1)}<span>{f.stem}</span></div>'
            for f in svgs)
        page.set_viewport_size({"width": 1240, "height": 800})
        page.set_content(
            '<html><head><style>body{margin:0;font:12px Inter,Arial,sans-serif;color:#5A6170;background:#FBFBF8}'
            '#g{display:grid;grid-template-columns:repeat(8,1fr);gap:8px;padding:24px;width:1192px}'
            '.c{display:flex;flex-direction:column;align-items:center;gap:8px;padding:14px 4px;background:#F3F3EF;border-radius:8px}'
            '.i{width:28px;height:28px}</style></head>'
            f'<body><div id="g">{cells}</div></body></html>')
        page.locator("#g").screenshot(path=str(OUT / "arcadia_icons_preview.png"))
        browser.close()
    zpath = OUT / "Arcadia_Tableau_Shapes.zip"
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for png in sorted(stage.rglob("*.png")):
            z.write(png, png.relative_to(stage).as_posix())
    shutil.rmtree(stage)
    n_sets = len(LINE_SETS) + len(BADGE_SETS)
    print(f"Wrote {zpath.name}: {n_sets} sets x {len(svgs)} icons, and arcadia_icons_preview.png")


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--import", dest="src", type=Path, help="path to a heroicons checkout to import from")
    args = ap.parse_args()
    if args.src:
        import_from_heroicons(args.src)
    build()
