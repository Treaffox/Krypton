"""Quadratische Punkte.

Source Code Pro zeichnet Punkte als Ellipsen aus vier Kurven. Krypton ersetzt
sie durch Quadrate gleicher Fläche (ein Quadrat wirkt sonst zu groß). Die Mitte
bleibt, ein Punkt auf der Grundlinie sitzt danach genau auf der Grundlinie
(ohne Überhang).

Die Auswahl wird in einem vollständigen Master getroffen und in allen Mastern
gleich angewendet; die neue Kontur hat überall vier Punkte, die Master bleiben
kompatibel.
"""
import math
import re

from fontTools.pens.areaPen import AreaPen
from fontTools.pens.boundsPen import BoundsPen
from ufoLib2.objects import Point

# Rasterzeichen, Symbole und Ringe bleiben rund.
EXCLUDE = re.compile(r"(shade|circledotted|smileface|robot|fisheye|degree|ring|clickbilabial)")


def _bounds(contour):
    bp = BoundsPen(None)
    contour.draw(bp)
    return bp.bounds


def _is_dot(contour, others, max_size):
    on = [p for p in contour.points if p.type]
    if len(on) != 4 or any(p.type != "curve" for p in on) or len(contour.points) != 12:
        return False
    x0, y0, x1, y1 = _bounds(contour)
    w, h = x1 - x0, y1 - y0
    if w <= 0 or h <= 0 or max(w, h) > max_size or not (0.6 < h / w < 1.6):
        return False
    ap = AreaPen()
    contour.draw(ap)
    if ap.value <= 0 or not (0.70 < ap.value / (w * h) < 0.86):  # gefüllte Ellipse
        return False
    for o in others:  # Ring oder Punze innerhalb? Dann kein Punkt
        ox0, oy0, ox1, oy1 = _bounds(o)
        if ox0 > x0 and ox1 < x1 and oy0 > y0 and oy1 < y1:
            return False
    return True


def find_dots(font, max_size=280):
    found = {}
    for g in font:
        if EXCLUDE.search(g.name):
            continue
        cs = list(g.contours)
        for i, c in enumerate(cs):
            if _is_dot(c, cs[:i] + cs[i + 1:], max_size):
                found.setdefault(g.name, []).append(i)
    return found


def square_dots(font, selection, italic_angle=0.0):
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    n = 0
    for name, idxs in selection.items():
        if name not in font:
            continue
        g = font[name]
        for i in idxs:
            if i >= len(g.contours):
                continue
            c = g.contours[i]
            # entneigt messen: Mitte und Fläche
            pts = [(p.x - p.y * tan, p.y) for p in c.points]
            ys = [y for _, y in pts]
            y0, y1 = min(ys), max(ys)
            ap = AreaPen()
            c.draw(ap)
            area = abs(ap.value)
            cy = (y0 + y1) / 2
            # Mitte waagrecht: Mittelwert der Extrempunkte links/rechts (on-curve)
            on = [(x, y) for (x, y), p in zip(pts, c.points) if p.type]
            xs = [x for x, _ in on]
            cx = (min(xs) + max(xs)) / 2
            side = math.sqrt(area)
            by = cy - side / 2
            if abs(by) <= 16:  # Punkt auf der Grundlinie
                by = 0.0
            sq = [(cx - side / 2, by), (cx + side / 2, by), (cx + side / 2, by + side), (cx - side / 2, by + side)]
            # gegen den Uhrzeigersinn wie die Ellipse (Fläche > 0)
            del c.points[:]
            for x, y in sq:
                c.points.append(Point(round(x + y * tan), round(y), "line"))
            n += 1
    return n


UPPER_DOT_GLYPHS = ("colon", "semicolon", "anoteleia")


def align_upper_dots(font, italic_angle=0.0):
    """Quadratische Punkte haben keinen Überhang: Der obere Punkt von : ; und der
    griechischen Ano Teleia schließt oben genau mit der x-Höhe ab (unten sitzt der
    Punkt genau auf der Grundlinie)."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    xh = font.info.xHeight
    done = {}
    for name in UPPER_DOT_GLYPHS:
        if name not in font:
            continue
        for c in font[name].components:
            if c.baseGlyph != "period" or "period" not in font:
                continue
            b = font["period"].getBounds(font)
            xx, xy, yx, yy, dx, dy = c.transformation
            if dy < 0.3 * xh:
                continue  # unterer Punkt
            corr = xh - (b.yMax + dy)
            if corr:
                c.transformation = (xx, xy, yx, yy, round(dx + corr * tan), round(dy + corr))
                done[name] = corr
    return done
