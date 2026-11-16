"""Text mit HarfBuzz formen (mark/mkmk, Features) und mit FreeType rendern.

  hbproof.py out.png size font.ttf wght "zeile" …
  Zeile mit Features: "feat:ss01,zero|text"
"""
import sys

import freetype
import numpy as np
import uharfbuzz as hb
from PIL import Image

out, size, path, wght = sys.argv[1], int(sys.argv[2]), sys.argv[3], float(sys.argv[4])
lines = sys.argv[5:]
face = hb.Face(hb.Blob.from_file_path(path))
font = hb.Font(face)
if wght:
    font.set_variations({"wght": wght})
sc = size / face.upem
ft = freetype.Face(path)
ft.set_char_size(size * 64)
try:
    ft.set_var_design_coords([wght])
except Exception:
    pass
LH = int(size * 1.6)
img = Image.new("L", (2400, len(lines) * LH + 20), 255)
for li, line in enumerate(lines):
    feats = {}
    if line.startswith("feat:"):
        spec, line = line[5:].split("|", 1)
        feats = {f: True for f in spec.split(",") if f}
    buf = hb.Buffer()
    buf.add_str(line)
    buf.guess_segment_properties()
    hb.shape(font, buf, feats)
    x = 20.0
    base = 10 + li * LH + size * 1.1
    for info, pos in zip(buf.glyph_infos, buf.glyph_positions):
        ft.load_glyph(info.codepoint, freetype.FT_LOAD_RENDER | freetype.FT_LOAD_NO_HINTING)
        g = ft.glyph
        bm = g.bitmap
        if bm.width and bm.rows:
            a = np.array(bm.buffer, dtype=np.uint8).reshape(bm.rows, bm.pitch)[:, :bm.width]
            px = int(round(x + pos.x_offset * sc + g.bitmap_left))
            py = int(round(base - pos.y_offset * sc - g.bitmap_top))
            ink = Image.fromarray(a)
            img.paste(Image.new("L", ink.size, 0), (px, py), ink)
        x += pos.x_advance * sc
img.save(out)
