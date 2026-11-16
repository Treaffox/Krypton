"""Höhere x-Höhe für Kleinbuchstaben.

Source Code Pro hat eine niedrige x-Höhe (486 bei 1000 UPM, Regular). Krypton
streckt den Bereich zwischen Grundlinie und x-Höhe um den Faktor K. Alles
oberhalb der x-Höhe (Oberlängen, i-Punkte, Akzente) wird um denselben Betrag
nach oben verschoben, nicht gestaucht. Unterlängen bleiben unverändert.

    y < 0        -> y
    0 <= y <= xh -> y * K
    y > xh       -> y + delta     (delta = xh * (K - 1))

Kursive werden dabei entneigt und wieder geneigt, damit die Neigung erhalten
bleibt.

Betroffen sind
  L  Kleinbuchstaben (Unicode Ll) und ihre unkodierten Varianten (a.a, g.a …)
  M  Akzente, die über Kleinbuchstaben sitzen (_aboveLC/_aboverightLC/_hornLC),
     und freistehende Akzentzeichen (Sk) oberhalb der x-Höhe: nur verschoben
  P  Doppelpunkt und Semikolon: der obere Punkt wandert mit der x-Höhe

Komponenten werden so korrigiert, dass jede Form dort landet, wo sie nach der
Abbildung hingehört, egal ob Basis und Komposit in derselben Klasse sind.
"""
import math
import unicodedata

SHIFT_ANCHORS = ("_aboveLC", "_aboverightLC", "_hornLC")
NO_SCALE_SUFFIXES = {"sups", "supa", "subs", "sinf", "numr", "dnom", "ordn", "sc", "cap"}
PUNCT = {"colon", "semicolon"}


def _cat(font, name):
    g = font[name]
    if g.unicodes:
        return unicodedata.category(chr(g.unicodes[0]))
    return None


def classify(font):
    """Gibt (L, M, P) als Mengen von Glyphnamen zurück."""
    xh = font.info.xHeight
    L, M, P = set(), set(), set()
    by_name = {g.name for g in font}
    for g in font:
        name = g.name
        parts = name.split(".")
        if any(s in NO_SCALE_SUFFIXES for s in parts[1:]):
            continue
        if any(a.name in SHIFT_ANCHORS for a in g.anchors):
            M.add(name)
            continue
        cat = _cat(font, name)
        if cat == "Mn" and not g.anchors:  # Akzent ohne Anker (z. B. Doppelakzente)
            b = g.getBounds(font)
            if b and b.yMin > 0.75 * xh:
                M.add(name)
            continue
        if cat is None and parts[0] in by_name and parts[0] != name:
            cat = _cat(font, parts[0])
        if cat == "Ll":
            L.add(name)
        elif cat == "Sk":
            b = g.getBounds(font)
            if b and b.yMin > 0.75 * xh:
                M.add(name)
        elif parts[0] in PUNCT:
            P.add(name)
    return L, M, P


def raise_xheight(font, k, classes, italic_angle=0.0):
    L, M, P = classes
    xh = font.info.xHeight
    delta = xh * (k - 1)
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0

    def f_low(y):
        if y < 0:
            return y
        if y <= xh:
            return y * k
        return y + delta

    def f_shift(y):
        return y + delta

    def f_punct(y):  # nur Konturen oberhalb der halben x-Höhe, siehe unten
        return y + delta

    def apply(x, y, fn):
        ny = fn(y)
        return x + (ny - y) * tan, ny

    mids = {}
    for g in font:
        try:
            b = g.getBounds(font)
        except KeyError:  # dünner Zwischenmaster: Basis fehlt
            b = None
        if b is not None:
            mids[g.name] = (b.yMin + b.yMax) / 2

    for g in font:
        name = g.name
        if name in L:
            fn = f_low
        elif name in M:
            fn = f_shift
        elif name in P:
            fn = f_punct
        else:
            fn = None
        if fn is not None:
            for c in g.contours:
                if name in P:
                    ymin = min(p.y for p in c.points)
                    if ymin < 0.4 * xh:
                        continue
                for p in c.points:
                    p.x, p.y = (round(v) for v in apply(p.x, p.y, fn))
            for a in g.anchors:
                a.x, a.y = (round(v) for v in apply(a.x, a.y, fn))
        # Komponenten: gewünschte minus tatsächliche Verschiebung ausgleichen.
        # Gestreckte Kleinbuchstaben als Komponente bleiben, wie sie sind.
        for comp in g.components:
            base = comp.baseGlyph
            xx, xy, yx, yy, dx, dy = comp.transformation
            if base not in mids or base in L:
                continue
            y = mids[base] + dy  # Lage im Komposit vor der Umformung
            have = delta if base in M else 0.0
            if fn is None:
                want = 0.0
            elif name in P:
                want = delta if dy > 0.4 * xh else 0.0
            else:
                want = fn(y) - y
            corr = want - have
            if abs(corr) >= 0.5:
                comp.transformation = (xx, xy, yx, yy, round(dx + corr * tan), round(dy + corr))
    font.info.xHeight = round(xh * k)
    if font.info.ascender:
        font.info.ascender = round(font.info.ascender + delta)
    return round(delta)
