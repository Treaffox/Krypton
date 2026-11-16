"""Griechisch und Kyrillisch für die Kursive.

Die Kursive von Source Code Pro enthält nur Latein. Krypton ergänzt alle
Zeichen, die es nur im Aufrechten gibt:

1. Buchstaben, die in der Kursive wie ein lateinischer Buchstabe aussehen,
   verweisen auf dessen echte Kursivform (а→a, е→e, и→u, п→n, т→m …, Α→A …).
   So bekommen kyrillisches а, и, п, т die richtigen kursiven Formen.
   Dazu echte Kursivformen: г (gespiegeltes s), д (∂), ц/ш/щ (aus u und ɯ).
2. Komposita (ё, й, ά …) werden mit denselben Komponenten nachgebaut.
3. Alles andere wird aus dem Aufrechten schräggestellt (Oblique um die halbe
   x-Höhe, damit die Formen in der Zelle mittig bleiben).
"""
import math

from ufoLib2.objects import Anchor, Component, Contour, Glyph, Point

HOMOGLYPHS = {
    # Kyrillisch klein
    0x0430: 0x61, 0x0435: 0x65, 0x043E: 0x6F, 0x0440: 0x70, 0x0441: 0x63, 0x0443: 0x79,
    0x0445: 0x78, 0x0438: 0x75, 0x043F: 0x6E, 0x0442: 0x6D, 0x0456: 0x69, 0x0458: 0x6A,
    0x0455: 0x73, 0x04BB: 0x68,
    # Kyrillisch groß
    0x0410: 0x41, 0x0412: 0x42, 0x0415: 0x45, 0x041A: 0x4B, 0x041C: 0x4D, 0x041D: 0x48,
    0x041E: 0x4F, 0x0420: 0x50, 0x0421: 0x43, 0x0422: 0x54, 0x0425: 0x58, 0x0406: 0x49,
    0x0408: 0x4A, 0x0405: 0x53, 0x04AE: 0x59, 0x04C0: 0x49,
    # Griechisch
    0x0391: 0x41, 0x0392: 0x42, 0x0395: 0x45, 0x0396: 0x5A, 0x0397: 0x48, 0x0399: 0x49,
    0x039A: 0x4B, 0x039C: 0x4D, 0x039D: 0x4E, 0x039F: 0x4F, 0x03A1: 0x50, 0x03A4: 0x54,
    0x03A5: 0x59, 0x03A7: 0x58, 0x03BF: 0x6F,
}


def _cmap(font):
    return {u: g.name for g in font for u in g.unicodes}


# Echte Kursivformen, die sich aus vorhandenen Kursiven ergeben (wie IBM Plex Mono Italic):
#   г → gespiegeltes s,  д → ∂ (Form mit Schleife und Oberlänge)
CURSIVE_MIRROR = {0x0433: 0x0073}
CURSIVE_COMPONENT = {0x0434: 0x2202}
# Kursivformen aus u und ɯ (wie IBM Plex Mono Italic):
#   ц → u mit Unterlänge,  ш → ɯ (rechter Stamm endet auf der Grundlinie),
#   щ → ш mit Unterlänge,  џ → u mit Unterlänge in der Mitte.
#   Die Unterlänge ist so tief wie im Aufrechten.
CURSIVE_BUILD = {0x0446: (0x0075, "right"), 0x0448: (0x026F, None), 0x0449: (0x026F, "right"),
                 0x045F: (0x0075, "center")}


def _cursive_build(upright, src, italic, ic, cp, itan, g):
    """Baut ц/ш/щ als Konturen (gleiche Punktstruktur in allen Mastern)."""
    from .extras import _decomposed
    from .hooks import _rect
    base, tail = CURSIVE_BUILD[cp]
    ref = ic[base]
    d = _decomposed(italic, ref)
    for c in d.contours:
        pts = []
        for p in c.points:
            x, y = p.x, p.y
            ux = x - y * itan
            if base == 0x026F and p.type == "line" and y < -5 and ux > 300:
                y, x = 0, round(ux)  # Stamm des ɯ auf die Grundlinie kürzen
            pts.append(Point(x, y, p.type, p.smooth))
        g.contours.append(Contour(pts))
    if tail:
        bottom = sorted(p.x - p.y * itan for c in g.contours for p in c.points
                        if p.type and abs(p.y) < 1 and p.x - p.y * itan > 300)
        x0, x1 = bottom[-2], bottom[-1]  # rechter Stamm an der Grundlinie
        w = x1 - x0
        depth = min(p.y for c in _decomposed(upright, src.name).contours for p in c.points)
        if tail == "right":
            g.contours.append(_rect(x0, depth, x1, w, itan))
        else:  # Mitte des Bogens: zwischen linker Außenkante und rechtem Stamm
            left = min(p.x - p.y * itan for c in g.contours for p in c.points if p.type)
            cx = (left + x0) / 2
            g.contours.append(_rect(cx - w / 2, depth, cx + w / 2, 0.5 * w, itan))
    for a in italic[ref].anchors:
        g.anchors.append(Anchor(a.x, a.y, name=a.name))

# Unkodierte Glyphen, die die griechischen/kyrillischen Regeln (locl, case) brauchen
EXTRA = ("be.srb", "anoteleia.cap", "brevecmb.cyr", "brevecmb.cyrcap", "tonoscmb", "variacmb",
         "aspercmb", "leniscmb")


def missing_names(upright, italic):
    """Glyphen, die im Aufrechten kodiert sind (oder von solchen gebraucht
    werden) und in der Kursive fehlen, plus EXTRA."""
    ic = _cmap(italic)
    want = [g.name for g in upright if g.unicodes and not any(u in ic for u in g.unicodes)
            and g.name not in italic]
    want += [n for n in EXTRA if n in upright and n not in italic and n not in want]
    todo, seen = list(want), set(want)
    while todo:  # Komponenten nachziehen
        n = todo.pop()
        for c in upright[n].components:
            if c.baseGlyph not in italic and c.baseGlyph not in seen:
                seen.add(c.baseGlyph)
                todo.append(c.baseGlyph)
    order = [n for n in upright.glyphOrder if n in seen] if upright.glyphOrder else sorted(seen)
    return order + sorted(seen - set(order))


def fill(upright, italic, names, angle):
    tan = math.tan(math.radians(-angle))
    itan = tan  # Neigung der vorhandenen Kursiven (zum Entneigen beim Spiegeln)
    pivot = (upright.info.xHeight or 480) / 2
    ic = _cmap(italic)
    sx = lambda x, y: round(x + (y - pivot) * tan)
    added = {"homoglyph": 0, "composite": 0, "oblique": 0}
    for n in names:
        src = upright[n]
        g = Glyph(n)
        g.width = src.width
        g.unicodes = list(src.unicodes)
        cp = src.unicodes[0] if src.unicodes else None
        latin = HOMOGLYPHS.get(cp) if cp else None
        if cp in CURSIVE_MIRROR and CURSIVE_MIRROR[cp] in ic:
            from .extras import _decomposed, _reverse
            ref = ic[CURSIVE_MIRROR[cp]]
            w = italic[ref].width
            for c in _decomposed(italic, ref).contours:
                pts = [(w - (p.x - p.y * itan) + p.y * itan, p.y, p.type, p.smooth) for p in c.points]
                g.contours.append(Contour([Point(round(x), y, t, sm) for x, y, t, sm in _reverse(pts)]))
            for a in italic[ref].anchors:
                g.anchors.append(Anchor(round(w - (a.x - a.y * itan) + a.y * itan), a.y, name=a.name))
            added["cursive"] = added.get("cursive", 0) + 1
        elif cp in CURSIVE_BUILD and CURSIVE_BUILD[cp][0] in ic:
            _cursive_build(upright, src, italic, ic, cp, itan, g)
            added["cursive"] = added.get("cursive", 0) + 1
        elif cp in CURSIVE_COMPONENT and CURSIVE_COMPONENT[cp] in ic:
            # als Kontur kopieren (keine Komponente): so wird die Schleife wie ein
            # Kleinbuchstabe auf die neue x-Höhe gestreckt
            from .extras import _decomposed
            ref = ic[CURSIVE_COMPONENT[cp]]
            for c in _decomposed(italic, ref).contours:
                g.contours.append(Contour([Point(p.x, p.y, p.type, p.smooth) for p in c.points]))
            added["cursive"] = added.get("cursive", 0) + 1
        elif latin is not None and latin in ic:
            g.components.append(Component(ic[latin]))
            for a in italic[ic[latin]].anchors:
                g.anchors.append(Anchor(a.x, a.y, name=a.name))
            added["homoglyph"] += 1
        else:
            for c in src.contours:
                g.contours.append(Contour([Point(sx(p.x, p.y), p.y, p.type, p.smooth) for p in c.points]))
            for c in src.components:
                xx, xy, yx, yy, dx, dy = c.transformation
                # Basis ist selbst um pivot geneigt; der Versatz dy wandert mit der Neigung
                g.components.append(Component(c.baseGlyph, (xx, xy, yx, yy, round(dx + dy * tan), dy)))
            for a in src.anchors:
                g.anchors.append(Anchor(sx(a.x, a.y), a.y, name=a.name))
            added["composite" if src.components and not src.contours else "oblique"] += 1
        italic.layers.defaultLayer.insertGlyph(g, name=n, overwrite=False, copy=False)
    if italic.glyphOrder:
        italic.glyphOrder = list(italic.glyphOrder) + [n for n in names if n not in italic.glyphOrder]
    added["anchored"] = sum(_place_marks(italic, italic[n]) for n in names)
    return added


def _place_marks(font, g):
    """Setzt Akzentkomponenten über die Anker der kursiven Basis statt mit den
    Versätzen aus dem Aufrechten. Gibt die Zahl der neu gesetzten Akzente zurück."""
    comps = list(g.components)
    if len(comps) < 2 or comps[0].baseGlyph not in font:
        return 0
    base = comps[0]
    bdx, bdy = base.transformation[4], base.transformation[5]
    points = {a.name: (a.x + bdx, a.y + bdy) for a in font[base.baseGlyph].anchors}
    n = 0
    for c in comps[1:]:
        if c.baseGlyph not in font:
            continue
        mark = font[c.baseGlyph]
        att = [a for a in mark.anchors if a.name.startswith("_") and a.name[1:] in points]
        if not att:
            continue
        a = att[0]
        px, py = points[a.name[1:]]
        dx, dy = px - a.x, py - a.y
        xx, xy, yx, yy = c.transformation[:4]
        c.transformation = (xx, xy, yx, yy, round(dx), round(dy))
        n += 1
        for m in mark.anchors:  # Stapeln: Anker des Akzents gelten für den nächsten
            if not m.name.startswith("_"):
                points[m.name] = (m.x + dx, m.y + dy)
    return n
