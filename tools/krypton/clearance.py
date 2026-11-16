"""Mindestabstand zwischen Akzent und Grundform.

Für jedes Kompositum mit einem Akzent oberhalb (Anker _above…) wird geprüft, ob
der Akzent die übrigen Komponenten berührt oder ihnen näher als GAP Einheiten
kommt. Wenn ja, wird der Akzent in 2er-Schritten angehoben (in Kursiven
entlang der Neigung). Betrifft in Source Code Pro vor allem Vietnamesisch mit
Horn (Ỡ ỡ Ớ) und einige Großbuchstaben in Black.
"""
import math

import pathops
from fontTools.pens.transformPen import TransformPen


def _path(font, comp, dy=0.0, tan=0.0, sx=0.0):
    p = pathops.Path()
    xx, xy, yx, yy, dx, cy = comp.transformation
    font[comp.baseGlyph].draw(TransformPen(p.getPen(glyphSet=font), (xx, xy, yx, yy, dx + sx + dy * tan, cy + dy)))
    return p


def _touches(base, mark, gap):
    if abs(pathops.op(base, mark, pathops.PathOp.INTERSECTION).area) > 1:
        return True
    probe = pathops.Path()
    mark.draw(TransformPen(probe.getPen(), (1, 0, 0, 1, 0, -gap)))
    return abs(pathops.op(base, probe, pathops.PathOp.INTERSECTION).area) > 1


def ensure_clearance(font, gap=18, italic_angle=0.0, max_lift=60):
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    above = {g.name for g in font if any(a.name.startswith("_above") for a in g.anchors)}
    fixed = {}
    for g in font:
        comps = list(g.components)
        if len(comps) < 2 or comps[0].baseGlyph in above or comps[0].baseGlyph not in font:
            continue  # nur Grundbuchstabe + Akzent(e), keine zusammengesetzten Akzente
        for i, c in enumerate(comps):
            if i == 0 or c.baseGlyph not in above:
                continue
            base = pathops.Path()
            for j, o in enumerate(comps):
                if j < i:  # nur was darunter liegt: Grundform und frühere Akzente
                    _path(font, o).draw(base.getPen())
            if not _touches(base, _path(font, c, 0, tan), gap):
                continue
            # kleinste Verschiebung: zuerst nur anheben, sonst zusätzlich nach links
            # (bei Horn-Buchstaben steht das Hindernis rechts oben)
            best = None
            for sx in (0, -8, -16, -24, -32, -40):
                for lift in range(0, max_lift + 1, 2):
                    cost = lift + abs(sx) * 0.75
                    if best is not None and cost >= best[0]:
                        break
                    if not _touches(base, _path(font, c, lift, tan, sx), gap):
                        best = (cost, lift, sx)
                        break
            if best:
                _, lift, sx = best
                xx, xy, yx, yy, dx, dy = c.transformation
                c.transformation = (xx, xy, yx, yy, round(dx + sx + lift * tan), dy + lift)
                fixed[g.name] = (lift, sx)
            else:
                fixed[g.name] = "nicht lösbar"
    return fixed
