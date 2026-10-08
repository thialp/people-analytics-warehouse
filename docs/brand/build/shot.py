"""Render build/map_preview.html to docs/images/workforce_map_preview.png (run via build.sh)."""
import sys
from playwright.sync_api import sync_playwright
url, out = sys.argv[1], sys.argv[2]
with sync_playwright() as p:
    b = p.chromium.launch()
    pg = b.new_page(viewport={"width": 1400, "height": 846}, device_scale_factor=1.5)
    pg.on("pageerror", lambda e: sys.exit(f"page error: {e}"))
    pg.goto(url)
    pg.wait_for_selector("body[data-ready='1']", timeout=15000)
    pg.screenshot(path=out)
    b.close()
