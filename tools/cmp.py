"""Vergleichsbild mehrerer Schriften: python tools/cmp.py out.png size "text" label=font.ttf ..."""
import sys
from PIL import Image, ImageDraw, ImageFont

from labelfont import label_font

out, size, text = sys.argv[1], int(sys.argv[2]), sys.argv[3].replace("\\n", "\n")
fonts = [a.split("=", 1) for a in sys.argv[4:]]
lines = text.split("\n")
lh = int(size * 1.35)
W = 2400
H = 40 + len(fonts) * (len(lines) * lh + 70)
img = Image.new("L", (W, H), 255)
d = ImageDraw.Draw(img)
lab = label_font(22)
y = 20
for name, path in fonts:
    d.text((20, y), name, font=lab, fill=120)
    y += 34
    path, _, var = path.partition("@")
    f = ImageFont.truetype(path, size)
    if var:
        f.set_variation_by_axes([float(v) for v in var.split(",")])
    for ln in lines:
        d.text((20, y), ln, font=f, fill=0)
        y += lh
    y += 36
img.save(out)
