#!/usr/bin/env python3
"""Probeabzug aller Glyphen: Raster mit Hilfslinien (Grundlinie, x-Höhe, Versalhöhe)
und Zellgrenzen (0 und 600 Einheiten).

  proof.py FONT WGHT OUTPREFIX [--cols 20] [--rows 14] [--cell 110] [--names a,b,…]

Erzeugt OUTPREFIX-01.png, -02.png … (eine Seite je cols×rows Glyphen).
"""
import argparse

import freetype
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image, ImageDraw, ImageFont

from labelfont import label_font

ap = argparse.ArgumentParser()
ap.add_argument("font")
ap.add_argument("wght", type=float)
ap.add_argument("out")
ap.add_argument("--cols", type=int, default=20)
ap.add_argument("--rows", type=int, default=14)
ap.add_argument("--cell", type=int, default=110)
ap.add_argument("--names", default="")
a = ap.parse_args()

tt = TTFont(a.font)
order = tt.getGlyphOrder()
names = [n for n in a.names.split(",") if n] or order
upm = tt["head"].unitsPerEm
os2 = tt["OS/2"]
xh, ch = os2.sxHeight, os2.sCapHeight
face = freetype.Face(a.font)
if "fvar" in tt:
    face.set_var_design_coords([a.wght])
C = a.cell
scale = C * 0.62 / upm  # 600 Einheiten ≈ 0,37 Zelle … Glyph mittig
face.set_char_size(int(upm * scale * 64))
label = label_font(10)
per = a.cols * a.rows
idx = {n: i for i, n in enumerate(order)}
for page in range((len(names) + per - 1) // per):
    chunk = names[page * per:(page + 1) * per]
    img = Image.new("L", (a.cols * C, a.rows * C), 255)
    d = ImageDraw.Draw(img)
    for k, n in enumerate(chunk):
        cx, cy = (k % a.cols) * C, (k // a.cols) * C
        base = cy + int(C * 0.70)
        ox = cx + int((C - 600 * scale) / 2)
        d.rectangle([cx, cy, cx + C - 1, cy + C - 1], outline=225)
        for yv, col in ((0, 150), (xh, 200), (ch, 215)):
            y = base - int(yv * scale)
            d.line([cx + 2, y, cx + C - 3, y], fill=col)
        for xv in (0, 600):
            x = ox + int(xv * scale)
            d.line([x, cy + 14, x, cy + C - 14], fill=225)
        face.load_glyph(idx[n], freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = face.glyph
        bm = g.bitmap
        if bm.width and bm.rows:
            arr = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width]
            x = ox + g.bitmap_left
            y = base - g.bitmap_top
            ink = Image.fromarray(arr)
            img.paste(Image.new("L", ink.size, 0), (x, y), ink)
        d.text((cx + 3, cy + C - 12), n[:18], font=label, fill=110)
    img.save(f"{a.out}-{page + 1:02d}.png")
print(f"{len(names)} Glyphen, {(len(names) + per - 1) // per} Seiten")
