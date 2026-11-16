#!/usr/bin/env python3
"""Findet Komposita, in denen sich Komponenten (Akzent und Grundbuchstabe)
überschneiden oder sehr nah kommen. Prüft statische TTF.

  collisions.py FONT.ttf [--gap 20]
"""
import argparse

import pathops
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont

ap = argparse.ArgumentParser()
ap.add_argument("fonts", nargs="+")
ap.add_argument("--gap", type=int, default=12)
a = ap.parse_args()

for path in a.fonts:
    f = TTFont(path)
    gs = f.getGlyphSet()
    glyf = f["glyf"]
    cmap = {v: k for k, v in f.getBestCmap().items()}
    hits = []
    for name in f.getGlyphOrder():
        g = glyf[name]
        if not g.isComposite() or len(g.components) < 2:
            continue
        paths = []
        for c in g.components:
            p = pathops.Path()
            t = (1, 0, 0, 1, c.x, c.y)
            if hasattr(c, "transform"):
                (xx, xy), (yx, yy) = c.transform
                t = (xx, xy, yx, yy, c.x, c.y)
            gs[c.glyphName].draw(TransformPen(p.getPen(glyphSet=gs), t))
            paths.append((c.glyphName, p))
        base_name, base = paths[0]
        for mname, m in paths[1:]:
            inter = pathops.op(base, m, pathops.PathOp.INTERSECTION)
            area = abs(inter.area)
            if area > 4:
                hits.append((name, mname, "überschneidet", round(area)))
                continue
            # Abstand: Akzent um gap nach unten/oben verschieben und erneut prüfen
            for dy in (-a.gap, a.gap):
                moved = pathops.Path()
                m.draw(TransformPen(moved.getPen(), (1, 0, 0, 1, 0, dy)))
                if abs(pathops.op(base, moved, pathops.PathOp.INTERSECTION).area) > 4:
                    hits.append((name, mname, f"Abstand < {a.gap}", 0))
                    break
    print(f"{path.split('/')[-1]}: {len(hits)} Treffer")
    for h in hits:
        u = cmap.get(h[0])
        print(f"  {h[0]}{' U+%04X' % u if u else ''}  {h[1]}: {h[2]} {h[3] or ''}")
