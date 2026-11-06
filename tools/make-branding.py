#!/usr/bin/env python3
"""Generate the Null Server boot-menu splash from the Null mark geometry.

Writes branding/boot-splash.svg (the design, needs Silkscreen/VT323) and
branding/boot-splash.png (640x480, what the ISO's boot menu shows).

Rendering: Chromium through Playwright (the same renderer the Null OS repo's
CI uses for previews). Fonts: pass a folder with silkscreen.woff2 and
vt323.woff2 (the Null Grid browser's fonts) as FONTS=...; without it the
text falls back to monospace.

  FONTS=/path/to/null-grid/fonts python3 tools/make-branding.py
"""
import base64
import importlib.util
import os
import random
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
spec = importlib.util.spec_from_file_location(
    "null_mark", os.path.join(ROOT, "config/includes.chroot/usr/share/null-server/null-mark.py"))
mark = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mark)

BG, CYAN, PINK, TEXT, DIM = "#0a0a0f", "#00e5ff", "#ff2e88", "#c9d4e3", "#4a5a70"
MARK_PATH = mark.svg_path(flip_height=720)


def mark_group(x, y, size, color, glow=None):
    s = size / mark.CELL_W
    g = ""
    if glow:
        g += (f'<g transform="translate({x},{y}) scale({s})" filter="url(#glow)" opacity="0.85">'
              f'<path d="{MARK_PATH}" fill="{glow}" fill-rule="nonzero"/></g>')
    g += f'<g transform="translate({x},{y}) scale({s})"><path d="{MARK_PATH}" fill="{color}" fill-rule="nonzero"/></g>'
    return g


def rain(w, h, n, seed):
    rnd = random.Random(seed)
    out = []
    for _ in range(n):
        x, y = rnd.uniform(0, w), rnd.uniform(-h * 0.1, h)
        L, op = rnd.uniform(30, 140), rnd.uniform(0.05, 0.22)
        col = CYAN if rnd.random() < 0.85 else PINK
        out.append(f'<line x1="{x:.0f}" y1="{y:.0f}" x2="{x - L * 0.08:.0f}" y2="{y + L:.0f}" '
                   f'stroke="{col}" stroke-opacity="{op:.2f}" stroke-width="1.5"/>')
    return "".join(out)


def font_face(fonts):
    if not fonts:
        return ""
    css = ""
    for fam, fn in (("Silkscreen", "silkscreen.woff2"), ("VT323", "vt323.woff2")):
        p = os.path.join(fonts, fn)
        if os.path.exists(p):
            data = base64.b64encode(open(p, "rb").read()).decode()
            css += f"@font-face{{font-family:'{fam}';src:url(data:font/woff2;base64,{data}) format('woff2');}}"
    return f"<style>{css}</style>" if css else ""


def splash_svg(w=640, h=480, fonts=None):
    size = 92
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            + font_face(fonts) +
            '<defs><filter id="glow" x="-50%" y="-50%" width="200%" height="200%"><feGaussianBlur stdDeviation="18"/></filter></defs>'
            f'<rect width="{w}" height="{h}" fill="{BG}"/>'
            + rain(w, h, 70, seed=17) +
            mark_group(46, 18, size, CYAN, glow=CYAN) +
            f'<text x="170" y="74" font-family="Silkscreen, monospace" font-size="34" letter-spacing="6" fill="{TEXT}">NULL SERVER</text>'
            f'<text x="172" y="104" font-family="VT323, monospace" font-size="22" letter-spacing="2" fill="{DIM}">debian based // headless // neon lab</text>'
            f'<line x1="0" y1="{h - 60}" x2="{w}" y2="{h - 60}" stroke="{PINK}" stroke-opacity="0.5" stroke-width="1.5"/>'
            '</svg>')


def main():
    fonts = os.environ.get("FONTS")
    svg = splash_svg(fonts=fonts)
    out_dir = os.path.join(ROOT, "branding")
    os.makedirs(out_dir, exist_ok=True)
    png = os.path.join(out_dir, "boot-splash.png")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 640, "height": 480}, device_scale_factor=1)
        pg.set_content(f'<html><body style="margin:0;background:{BG}">{svg}</body></html>')
        pg.wait_for_timeout(300)
        pg.screenshot(path=png, clip={"x": 0, "y": 0, "width": 640, "height": 480})
        b.close()
    # The SVG the bootloader config gets only wraps the PNG, so no renderer
    # in the build needs the fonts
    data = base64.b64encode(open(png, "rb").read()).decode()
    with open(os.path.join(out_dir, "boot-splash.svg"), "w") as f:
        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" '
                f'width="640" height="480" viewBox="0 0 640 480">'
                f'<image width="640" height="480" xlink:href="data:image/png;base64,{data}"/></svg>')
    print("wrote", png)


if __name__ == "__main__":
    sys.exit(main())
