"""Kleine Größen mit Hinting (FreeType, wie unter Linux/Windows-ähnlich), 3× vergrößert.

  smallsizes.py out.png label=font.ttf …
"""
import sys

from PIL import Image, ImageDraw, ImageFont

from labelfont import label_font

TEXT = ["fn parse(s: &str) -> Result<u32, Error> { // 0O 1lIi|",
        "if (x != null && y >= 0x1F) return arr[i++]; ÄÖÜ äöü ß",
        "┌──────┬──────┐ ░▒▓█ ▏▎▍▌▋▊▉ {[(<=>)]} @#$%&*"]
SIZES = [9, 10, 11, 12, 13, 14, 16]
out = sys.argv[1]
fonts = [a.split("=", 1) for a in sys.argv[2:]]
lab = label_font(11)
W = 600
H = 10 + len(fonts) * (16 + sum(int(s * 1.3) * len(TEXT) + 4 for s in SIZES) + 8)
img = Image.new("L", (W, H), 255)
d = ImageDraw.Draw(img)
y = 6
for name, path in fonts:
    d.text((4, y), name, font=lab, fill=120)
    y += 16
    for s in SIZES:
        f = ImageFont.truetype(path, s)
        for t in TEXT:
            d.text((4, y), t, font=f, fill=0)
            y += int(s * 1.3)
        y += 4
    y += 8
img = img.resize((W * 3, H * 3), Image.NEAREST)
img.save(out)
