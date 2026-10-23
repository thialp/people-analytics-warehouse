"""Organise the Tableau shapes by dashboard and draw a contact sheet.

Why: Tableau lists a palette in file-name order, many shapes are white-on-transparent (invisible on
the white palette), and every new dashboard adds more. So each dashboard gets its own palette folder and
its own file-name prefix, and an index picture shows every shape on the background it is used on, with its name.

  shapes/Arcadia/                  (generator output, unchanged; Dashboard #1 as published keeps using it)
  shapes/by_dashboard/shared/      info and close buttons, Summary | By driver toggle
  shapes/by_dashboard/d1/          Dashboard #1  Headcount & FTE Walk
  shapes/by_dashboard/d2/          Dashboard #2  Compensation Walk
  shapes/by_dashboard/fp/          Global Workforce Footprint
  shapes/index/<scope>.png         contact sheet (never copied to Tableau)

File name = <scope>_<sheet>_<option>_<state>.png, lower case, so the list sorts the way the dashboard reads.
Usage: python3 organize_shapes.py   (run after the make_*_shapes.py generators)"""
import os, shutil
from PIL import Image, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "shapes", "Arcadia")
DST = os.path.join(HERE, "..", "shapes", "by_dashboard")
IDX = os.path.join(HERE, "..", "shapes", "index")   # contact sheets live outside the palette folders so Tableau never lists them
FONT = "/usr/share/fonts/opentype/inter/Inter-SemiBold.otf"

MAP = {
    "shared": {
        "info_open": "shared_info_open", "info_close": "shared_info_close",
        "btn_close": "shared_close_dark", "btn_close_light": "shared_close_light",
        "btn_expand_icon": "shared_expand_icon", "btn_collapse_icon": "shared_collapse_icon",
        "seg_detail_summary_on": "shared_detail_summary_on", "seg_detail_summary_off": "shared_detail_summary_off",
        "seg_detail_drivers_on": "shared_detail_drivers_on", "seg_detail_drivers_off": "shared_detail_drivers_off",
    },
    "d1": {
        "fld_top": "d1_field_capsule", "btn_reset_top_label": "d1_reset",
        "seg_worker_employees_on": "d1_workforce_employees_on", "seg_worker_employees_off": "d1_workforce_employees_off",
        "seg_worker_contingent_on": "d1_workforce_contingent_on", "seg_worker_contingent_off": "d1_workforce_contingent_off",
        "seg_worker_total_on": "d1_workforce_total_on", "seg_worker_total_off": "d1_workforce_total_off",
    },
    "d2": {
        "fld_rail": "d2_field_capsule", "btn_reset_rail": "d2_reset",
        "rail_info_open": "d2_info_open", "rail_info_close": "d2_info_close",
        "seg_lens_fte_on": "d2_lens_fte_on", "seg_lens_fte_off": "d2_lens_fte_off",
        "seg_lens_amount_on": "d2_lens_payroll_on", "seg_lens_amount_off": "d2_lens_payroll_off",
        "seg_cost_loaded_on": "d2_cost_loaded_on", "seg_cost_loaded_off": "d2_cost_loaded_off",
        "seg_cost_base_on": "d2_cost_base_on", "seg_cost_base_off": "d2_cost_base_off",
        "seg_currency_constant_on": "d2_currency_constant_on", "seg_currency_constant_off": "d2_currency_constant_off",
        "seg_currency_nominal_on": "d2_currency_nominal_on", "seg_currency_nominal_off": "d2_currency_nominal_off",
    },
    "d3": {
        "fld_top": "d3_field_capsule", "btn_reset_circle": "d3_reset",
        **{f"seg_version_{k}_{s}": f"d3_version_{k}_{s}"
           for k in ("budget", "q1", "q2", "q3") for s in ("on", "off", "na")},
    },
    "fp": {n: "fp_" + n[len("seg_fp_"):] for n in
           (f[:-4] for f in os.listdir(SRC) if f.startswith("seg_fp_") and f.endswith(".png"))},
}

NAVY, CREAM = (19, 35, 58), (251, 251, 248)

def is_light(im):
    px = [p for p in im.convert("RGBA").resize((40, 16)).getdata() if p[3] > 200]
    return bool(px) and sum(sum(p[:3]) / 3 for p in px) / len(px) > 170

def contact_sheet(folder, names):
    f = ImageFont.truetype(FONT, 14)
    tiles = []
    for n in names:
        im = Image.open(os.path.join(folder, n)).convert("RGBA")
        w, h = im.size
        k = min(1, 260 / w)
        im = im.resize((max(1, round(w * k)), max(1, round(h * k))), Image.LANCZOS)
        tiles.append((n, im))
    cols, cw = 3, 300
    rows = (len(tiles) + cols - 1) // cols
    ch = max(im.size[1] for _, im in tiles) + 54
    sheet = Image.new("RGB", (cols * cw, rows * ch), (240, 239, 234))
    d = ImageDraw.Draw(sheet)
    for i, (n, im) in enumerate(tiles):
        x, y = (i % cols) * cw, (i // cols) * ch
        if "detail" in n:
            bg = (236, 235, 229)                    # the grey capsule behind Summary | By driver
        elif any(k in n for k in ("workforce", "lens", "cost", "currency", "version")):
            bg = (36, 58, 87)                       # #243A57, the capsule behind a toggle
        else:
            bg = NAVY if (is_light(im) or "reset" in n) else CREAM  # white-on-transparent shapes are drawn on navy
        d.rectangle((x + 8, y + 8, x + cw - 8, y + ch - 30), fill=bg)
        sheet.paste(im, (x + 8 + (cw - 16 - im.size[0]) // 2, y + 8 + (ch - 38 - im.size[1]) // 2), im)
        d.text((x + 10, y + ch - 24), n[:-4], font=f, fill=(19, 35, 58))
    sheet.save(os.path.join(IDX, os.path.basename(folder) + ".png"), optimize=True)

if os.path.isdir(DST):
    shutil.rmtree(DST)
os.makedirs(IDX, exist_ok=True)
for scope, mapping in MAP.items():
    out = os.path.join(DST, scope)
    os.makedirs(out)
    made = []
    for old, new in sorted(mapping.items(), key=lambda kv: kv[1]):
        src = os.path.join(SRC, old + ".png")
        if os.path.exists(src):
            shutil.copy(src, os.path.join(out, new + ".png"))
            made.append(new + ".png")
    if made:
        contact_sheet(out, made)
    print(f"{scope:7s} {len(made):2d} shapes")
mapped = {o for m in MAP.values() for o in m}
left = sorted(f[:-4] for f in os.listdir(SRC) if f.endswith(".png") and f[:-4] not in mapped)
print("not carried over (obsolete or spare):", ", ".join(left))
