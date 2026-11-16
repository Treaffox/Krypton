"""Rendert Glyphen nach Namen: python tools/glyphs.py out.png size wght font.ttf name1 name2 … ('|' = neue Zeile)"""
import sys

import freetype
import numpy as np
from fontTools.ttLib import TTFont
from PIL import Image

out, size, wght, path = sys.argv[1], int(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
names = sys.argv[5:]
tt = TTFont(path)
order = {n: i for i, n in enumerate(tt.getGlyphOrder())}
face = freetype.Face(path)
face.set_char_size(size * 64)
if "fvar" in tt:
    face.set_var_design_coords([wght])
rows = [[]]
for n in names:
    if n == "|":
        rows.append([])
    elif n in order:
        rows[-1].append(n)
    else:
        print("fehlt:", n)
cell = int(size * 0.6) + 8
lh = int(size * 1.5)
W = max(len(r) for r in rows) * cell + 40
img = Image.new("L", (W, len(rows) * lh + 20), 255)
asc = int(size * 1.0)
for ri, row in enumerate(rows):
    for ci, n in enumerate(row):
        face.load_glyph(order[n], freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = face.glyph
        bm = g.bitmap
        if bm.width and bm.rows:
            a = 255 - np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width]
            x = 20 + ci * cell + g.bitmap_left
            y = 10 + ri * lh + asc - g.bitmap_top
            img.paste(Image.fromarray(a), (x, y), Image.fromarray(255 - a))
img.save(out)
