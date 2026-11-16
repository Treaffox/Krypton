"""Code-Ligaturen (Krypton 0.3.0), abschaltbar und standardmäßig aus: Feature ss10.

  ->  <-  <->  =>  ==  ===  !=  !==

Jede Ligatur belegt genau so viele Zellen wie Zeichen. Technik wie bei
Fira Code: Die ersten Zeichen werden durch den leeren Platzhalter LIG (600
breit) ersetzt, das letzte durch die Ligatur. Diese ist 600 breit und reicht
nach links in die vorigen Zellen (negative x-Werte).

Gebaut wird nur aus Teilen derselben Master: Balken aus - und = (die Enden
werden verschoben, die Anschnitte der Kursive bleiben so erhalten), Pfeil-
spitzen als Komponenten > und <, der Schrägstrich von ≠ mit Steigung und
Strichbreite des /. Alle Master haben damit dieselbe Punktstruktur.
"""
import math

from ufoLib2.objects import Component, Contour, Glyph, Point

from .extras import _decomposed

CELL = 600

# Name: (Zeichenfolge, Bauplan)
LIGATURES = {
    "less_hyphen_greater.liga": ("less hyphen greater", "arrow"),
    "exclam_equal_equal.liga": ("exclam equal equal", "neq"),
    "equal_equal_equal.liga": ("equal equal equal", "eq"),
    "hyphen_greater.liga": ("hyphen greater", "arrow"),
    "less_hyphen.liga": ("less hyphen", "arrow"),
    "equal_greater.liga": ("equal greater", "arrow"),
    "exclam_equal.liga": ("exclam equal", "neq"),
    "equal_equal.liga": ("equal equal", "eq"),
}


def _un(font, name, tan):
    """Konturen als Listen entneigter On-Curve-Punkte (x, y)."""
    d = _decomposed(font, name)
    return [[(p.x - p.y * tan, p.y) for p in c.points if p.type] for c in d.contours]


def _crossings(polys, y):
    xs = []
    for poly in polys:
        n = len(poly)
        for i in range(n):
            (x0, y0), (x1, y1) = poly[i], poly[(i + 1) % n]
            if (y0 <= y < y1) or (y1 <= y < y0):
                xs.append(x0 + (y - y0) * (x1 - x0) / (y1 - y0))
    return sorted(xs)


def _inside_end(polys, yb, yt, side):
    """x, an dem ein waagrechter Balken (yb..yt) im Inneren einer Spitze endet.
    side='right': Balken kommt von links (in >), 'left': von rechts (in <).
    Gesucht ist ein x, das an Unter- und Oberkante des Balkens im gefüllten
    Bereich liegt; genommen wird die Mitte des gemeinsamen Bereichs."""
    def interval(y):
        xs = _crossings(polys, y)
        pairs = [(xs[i], xs[i + 1]) for i in range(0, len(xs) - 1, 2)]
        return max(pairs, key=lambda p: p[1]) if side == "right" else min(pairs, key=lambda p: p[0])
    e = 0.5
    (a0, a1), (b0, b1) = interval(yb + e), interval(yt - e)
    lo, hi = max(a0, b0), min(a1, b1)
    if lo >= hi:
        raise ValueError(f"Balken {yb}..{yt} passt nicht in die Spitze")
    return (lo + hi) / 2


def _bar(contour_pts, tan, left_to=None, right_to=None, left_shift=0.0, right_shift=0.0):
    """Verlängert einen Balken: linke Endpunkte auf x=left_to bzw. um left_shift,
    rechte auf right_to bzw. um right_shift (entneigt gemessen). Der Anschnitt
    der Enden bleibt erhalten."""
    un = [(p.x - p.y * tan, p.y, p.type, p.smooth) for p in contour_pts]
    xs = [x for x, _, _, _ in un]
    mid = (min(xs) + max(xs)) / 2
    lmax = max(x for x in xs if x < mid)  # innerste Kante des linken Endes
    rmin = min(x for x in xs if x >= mid)
    dl = (left_to - lmax) if left_to is not None else left_shift
    dr = (right_to - rmin) if right_to is not None else right_shift
    pts = []
    for x, y, t, s in un:
        x = x + (dl if x < mid else dr)
        pts.append(Point(round(x + y * tan), round(y), t, s))
    return Contour(pts)


def _slash(font, tan, cx, yb, yt):
    """Schrägstrich durch ≠: Steigung und waagrechte Strichbreite wie '/'."""
    polys = _un(font, "slash", tan)
    ys = [y for poly in polys for _, y in poly]
    y0, y1 = min(ys), max(ys)
    ym = (y0 + y1) / 2
    xs = _crossings(polys, ym)
    width = xs[-1] - xs[0]
    xa = _crossings(polys, y0 + 0.25 * (y1 - y0))
    xb = _crossings(polys, y0 + 0.75 * (y1 - y0))
    slope = ((xb[0] + xb[-1]) - (xa[0] + xa[-1])) / 2 / (0.5 * (y1 - y0))  # dx/dy
    ymid = (yb + yt) / 2
    pts = []
    for y, side in ((yb, -1), (yb, 1), (yt, 1), (yt, -1)):  # gegen den Uhrzeigersinn
        x = cx + side * width / 2 + (y - ymid) * slope
        pts.append(Point(round(x + y * tan), round(y), "line"))
    return Contour(pts)


def _y_range(contour):
    ys = [p.y for p in contour.points]
    return min(ys), max(ys)


def add_ligatures(font, italic_angle=0.0):
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    need = {"hyphen", "less", "greater", "equal", "exclam", "slash"}
    if not need <= set(font.keys()):
        return []
    made = []
    lig = Glyph("LIG")
    lig.width = CELL
    font.layers.defaultLayer.insertGlyph(lig, name="LIG", overwrite=True, copy=False)
    made.append("LIG")
    gt = _un(font, "greater", tan)
    lt = _un(font, "less", tan)
    hyphen = _decomposed(font, "hyphen").contours
    equal = sorted(_decomposed(font, "equal").contours, key=lambda c: _y_range(c)[0])

    for name, (seq, kind) in LIGATURES.items():
        chars = seq.split()
        n = len(chars)
        off = -(n - 1) * CELL  # x-Versatz der ersten Zelle
        g = Glyph(name)
        g.width = CELL
        if kind == "arrow":
            bars = equal if "equal" in chars else hyphen
            head_r = chars[-1] == "greater"
            head_l = chars[0] == "less"
            if head_r:
                g.components.append(Component("greater"))
            if head_l:
                g.components.append(Component("less", (1, 0, 0, 1, off, 0)))
            for c in bars:
                yb, yt = _y_range(c)
                right_to = _inside_end(gt, yb, yt, "right") if head_r else None
                left_to = _inside_end(lt, yb, yt, "left") + off if head_l else None
                # ohne Spitze: Balken beginnt bzw. endet wie das Zeichen in seiner Zelle
                if not head_l:
                    g.contours.append(_bar(c.points, tan, left_shift=off, right_to=right_to))
                elif not head_r:
                    g.contours.append(_bar(c.points, tan, left_to=left_to))
                else:
                    g.contours.append(_bar(c.points, tan, left_to=left_to, right_to=right_to))
        else:  # eq, neq: Gleichheitsbalken über alle Zellen
            for c in equal:
                g.contours.append(_bar(c.points, tan, left_shift=off))
            if kind == "neq":  # Schrägstrich in der Mitte aller Zellen
                # Höhe wie der Schrägstrich des eingebauten ≠
                ne = _decomposed(font, "notequal").getBounds() if "notequal" in font else None
                if ne:
                    yb, yt = ne.yMin, ne.yMax
                else:
                    yb, yt = _y_range(equal[0])[0], _y_range(equal[-1])[1]
                    yb, yt = yb - 0.45 * (yt - yb), yt + 0.45 * (yt - yb)
                g.contours.append(_slash(font, tan, (off + CELL) / 2, yb, yt))
        font.layers.defaultLayer.insertGlyph(g, name=name, overwrite=True, copy=False)
        made.append(name)
    if font.glyphOrder:
        font.glyphOrder = list(font.glyphOrder) + [n for n in made if n not in font.glyphOrder]
    return made


DIGITS = "[zero one two three four five six seven eight nine]"

# Ignorierregeln je Ligatur: längere Folgen (-->, ==>, <=>, ====) und
# Vergleiche mit negativen Zahlen (a<-1) bleiben unverändert.
IGNORE = {
    "less_hyphen_greater.liga": ["less less' hyphen greater", "less' hyphen greater greater",
                                 "less' hyphen greater hyphen", "hyphen less' hyphen greater"],
    "exclam_equal_equal.liga": ["exclam exclam' equal equal", "exclam' equal equal equal"],
    "equal_equal_equal.liga": ["equal equal' equal equal", "equal' equal equal equal",
                               "[less greater exclam] equal' equal equal"],
    "hyphen_greater.liga": ["hyphen hyphen' greater", "hyphen' greater greater",
                            "[less greater] hyphen' greater"],
    "less_hyphen.liga": ["less less' hyphen", "less' hyphen hyphen", "less' hyphen " + DIGITS,
                         "less' hyphen [less greater]"],
    "equal_greater.liga": ["equal equal' greater", "equal' greater greater",
                           "[less greater exclam] equal' greater", "equal' greater equal"],
    "exclam_equal.liga": ["exclam exclam' equal", "exclam' equal equal"],
    "equal_equal.liga": ["equal equal' equal", "equal' equal equal",
                         "[less greater exclam] equal' equal", "equal' equal [greater less]"],
}


def features():
    """GSUB-Regeln (Feature ss10). Längere Folgen zuerst."""
    out = ["", "#--------------------------------------",
           "# Krypton: Code-Ligaturen (ss10), siehe tools/krypton/ligatures.py",
           "# Bindestrich auch in der Form aus ss01/cv14 (hyphen.a)",
           "@KRY_HYPHEN = [hyphen hyphen.a];"]
    cls = lambda t: " ".join("@KRY_HYPHEN" if w == "hyphen" else
                             ("@KRY_HYPHEN'" if w == "hyphen'" else w) for w in t.split())
    names = []
    for name, (seq, _) in LIGATURES.items():
        chars = seq.split()
        lk = "LIGA_" + name.replace(".liga", "").upper()
        names.append(lk)
        out.append(f"lookup {lk} {{")
        for ig in IGNORE.get(name, []):
            out.append(f"\tignore sub {cls(ig)};")
        n = len(chars)
        for i in range(n):
            back = ["LIG"] * i
            mark = chars[i] + "'"
            ahead = chars[i + 1:]
            by = name if i == n - 1 else "LIG"
            out.append("\tsub " + cls(" ".join(back + [mark] + ahead)) + f" by {by};")
        out.append(f"}} {lk};")
    out.append("")
    out.append("feature ss10 { # Stylistic Set 10 (code ligatures) – Krypton")
    out.append("\tfeatureNames {")
    out.append('\t\tname 3 1 0x0409 "code ligatures"; # English US')
    out.append("\t};")
    for lk in names:
        out.append(f"\tlookup {lk};")
    out.append("} ss10;")
    return "\n".join(out) + "\n"
