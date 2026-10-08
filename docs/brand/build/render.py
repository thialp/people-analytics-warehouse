import sys
from playwright.sync_api import sync_playwright
jobs = [  # svg, png, css width, background
  ("../arcadia_logo_horizontal.svg", "../arcadia_logo_horizontal.png", 600, "transparent"),
  ("../arcadia_logo_horizontal_reverse.svg", "../arcadia_logo_horizontal_reverse.png", 600, "transparent"),
  ("../arcadia_logo_mark.svg", "../arcadia_logo_mark.png", 400, "transparent"),
]
with sync_playwright() as p:
    b = p.chromium.launch()
    for svg, png, w, bg in jobs:
        pg = b.new_page(device_scale_factor=2)
        src = open(svg).read()
        pg.set_content(f'<html><body style="margin:0;background:{bg}"><div id=l style="width:{w}px;display:inline-block;line-height:0">{src.replace("<svg ", "<svg style=\"width:100%;height:auto\" ",1)}</div></body></html>')
        pg.locator("#l").screenshot(path=png, omit_background=(bg == "transparent"))
    b.close()
