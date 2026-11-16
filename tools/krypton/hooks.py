"""Haken und Schwänze für Zeichen, die Source Code Pro fehlen (Krypton 0.2.0).

Ein Haken ist ein Strich mit fester Punktstruktur: gerades Stück, Viertelbogen,
gerades Endstück, flacher Abschluss. Die Maße (Strichstärke, Radius, Längen)
werden je Master aus der Grundform gemessen. Die Punktstruktur ist in allen
Mastern gleich, die Glyphen bleiben interpolierbar.

Kanonische Lage: Der Strich läuft von y=0 nach unten (−y), x ∈ [0, w], und biegt
nach +x ab. Die Außenkante ist x=0. Für die echte Lage wird mit zwei Einheits-
vektoren abgebildet: `along` (Laufrichtung) und `turn` (Abbiegerichtung).

Gezeichnet werden:
  Ʈ Ɽ  Stamm nach unten verlängert, Haken nach rechts (Grundform als Komponente)
  Ɲ Ƒ  Stamm nach unten verlängert, Haken nach links
  Ʀ    Stamm ragt über die Versalhöhe (wie Noto/DejaVu)
  Ɦ Ƙ ƙ  Stamm oben gekürzt, Haken nach oben und rechts (vor dem Nachbarstrich)
  Ɓ    Haken oben links: Querstrich nach links, dann nach unten
  Ƴ ƴ  oberer rechter Arm endet in einem Haken nach rechts und unten
        (Arm dafür nach links geschert, Haken bleibt in der Zelle)
"""
import math

from ufoLib2.objects import Anchor, Component, Contour, Glyph, Point

from .extras import _cmap, _decomposed, _reverse

K = 0.5523  # Kreisnäherung mit kubischen Bézierkurven


def _canonical(w, E, Ro, T):
    """Punkte (x, y, typ) der kanonischen Hakenkontur, gegen den Uhrzeigersinn."""
    Ri = Ro - w
    return [
        (0, 0, "line"),
        (0, -E, "line"),
        (0, -E - K * Ro, None), (Ro - K * Ro, -E - Ro, None), (Ro, -E - Ro, "curve"),
        (Ro + T, -E - Ro, "line"),
        (Ro + T, -E - Ro + w, "line"),
        (Ro, -E - Ri, "line"),
        (Ro - K * Ri, -E - Ri, None), (w, -E - K * Ri, None), (w, -E, "curve"),
        (w, 0, "line"),
    ]


def hook_contour(origin, along, turn, w, E, Ro, T, tan=0.0):
    """Bildet den kanonischen Haken ab. origin: Außenkante am Startpunkt
    (entneigte Koordinaten). along/turn: Einheitsvektoren."""
    ox, oy = origin
    ax, ay = along
    tx, ty = turn
    pts = []
    for x, y, t in _canonical(w, E, Ro, T):
        # kanonisch: +x -> turn, −y -> along
        px = ox + x * tx + (-y) * ax
        py = oy + x * ty + (-y) * ay
        pts.append((px, py, t, False))
    det = tx * (-ay) - ty * (-ax)  # Orientierung von (turn, −along)
    if det < 0:
        pts = _reverse(pts)
    return Contour([Point(round(x + y * tan), round(y), t, s) for x, y, t, s in pts])


def _rect(x0, y0, x1, y1, tan=0.0):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]  # gegen den Uhrzeigersinn
    return Contour([Point(round(x + y * tan), round(y), "line") for x, y in pts])


def _un(g, tan):
    """On-Curve-Punkte (entneigt) aller Konturen: [(x, y, punkt)]"""
    return [(p.x - p.y * tan, p.y, p) for c in g.contours for p in c.points if p.type]


def _stem_bottom(d, tan, which="left"):
    """Stammkanten an der Grundlinie: die beiden kleinsten (oder größten) x bei y=yMin."""
    pts = _un(d, tan)
    y0 = min(y for _, y, _ in pts)
    xs = sorted(x for x, y, _ in pts if abs(y - y0) < 1)
    return (xs[0], xs[1]) if which == "left" else (xs[-2], xs[-1])


def _top_points(d, tan, which="left"):
    """Die beiden Punkte ganz oben links (bzw. rechts): [(x, y, punkt), …]"""
    pts = _un(d, tan)
    ytop = max(y for _, y, _ in pts)
    top = sorted([p for p in pts if abs(p[1] - ytop) < 1], key=lambda p: p[0])
    return top[:2] if which == "left" else top[-2:]


def _new(name, cp, width=600):
    g = Glyph(name)
    g.unicodes = [cp] if cp else []
    g.width = width
    return g


def add_hooked(font, italic_angle=0.0, names=None, desc=-200):
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    cm = _cmap(font)
    cap = font.info.capHeight
    made = {}

    def name(cp):
        return (names or {}).get(cp) or f"uni{cp:04X}"

    # --- Stamm unten verlängert, Haken nach rechts/links (Komponente + Haken)
    for cp, base, side in ((0x01AE, 0x0054, "right"), (0x2C64, 0x0052, "right"),
                           (0x019D, 0x004E, "left"), (0x0191, 0x0046, "left")):
        if cp in cm or base not in cm:
            continue
        d = _decomposed(font, cm[base])
        x0, x1 = _stem_bottom(d, tan, "left")
        w = x1 - x0
        ya = w  # Start im Stamm
        Ro = 1.4 * w
        if side == "right":
            E = ya - desc - Ro
            T = 0.5 * w
            c = hook_contour((x0, ya), (0, -1), (1, 0), w, E, Ro, T, tan)
        else:
            # nach links ist wenig Platz: Radius und Endstück an den Zellrand anpassen
            Ro = max(1.2 * w, min(1.4 * w, x1 + 30))
            T = max(0.0, min(0.5 * w, x1 + 30 - Ro))
            E = ya - desc - Ro
            c = hook_contour((x1, ya), (0, -1), (-1, 0), w, E, Ro, T, tan)
        g = _new(name(cp), cp)
        g.components.append(Component(cm[base]))
        g.contours.append(c)
        made[cp] = g

    # --- Ʀ: R, Stamm ragt über die Versalhöhe
    if 0x01A6 not in cm and 0x0052 in cm:
        d = _decomposed(font, cm[0x0052])
        x0, x1 = _stem_bottom(d, tan, "left")
        w = x1 - x0
        g = _new(name(0x01A6), 0x01A6)
        g.components.append(Component(cm[0x0052]))
        g.contours.append(_rect(x0, cap - w, x1, cap + 0.17 * cap, tan))
        made[0x01A6] = g

    # --- Ɦ Ƙ ƙ: Stamm oben gekürzt, Haken nach oben und rechts. Der Haken endet
    # mit Abstand vor dem nächsten Strich (rechter Stamm von H, oberer Arm von K).
    for cp, base, neighbour in ((0xA7AA, 0x0048, True), (0x0198, 0x004B, True), (0x0199, 0x006B, False)):
        if cp in cm or base not in cm:
            continue
        d = _decomposed(font, cm[base])
        (xa, ytop, pa), (xb, _, pb) = _top_points(d, tan, "left")
        w = xb - xa
        Ro, T = 1.35 * w, 0.55 * w
        if neighbour:
            (xn, _, _), _ = _top_points(d, tan, "right")
            room = xn - 0.6 * w - xa  # bis kurz vor den Nachbarstrich
            Ro = max(1.12 * w, min(Ro, room - 0.1 * w))
            T = max(0.0, min(T, room - Ro))
        for p in (pa, pb):  # Stamm oben um den Radius kürzen
            p.y = round(p.y - Ro)
            p.x = round(p.x - Ro * tan)
        ya = ytop - Ro - w  # Start im (gekürzten) Stamm
        E = ytop - Ro - ya
        g = _new(name(cp), cp)
        for c in d.contours:
            g.contours.append(c)
        g.contours.append(hook_contour((xa, ya), (0, 1), (1, 0), w, E, Ro, T, tan))
        for a in font[cm[base]].anchors:
            g.anchors.append(Anchor(a.x, a.y, name=a.name))
        made[cp] = g

    # --- Ɓ: oben links Querstrich nach links, dann nach unten
    if 0x0181 not in cm and 0x0042 in cm:
        d = _decomposed(font, cm[0x0042])
        x0, x1 = _stem_bottom(d, tan, "left")
        w = x1 - x0
        inner_top = max(max(p.y for p in c.points) for c in d.contours[1:]) if len(d.contours) > 1 else cap - w
        th = cap - inner_top  # Stärke des oberen Querstrichs
        Ro = max(1.2 * th, min(1.4 * th, x0 + 40))
        start = x0 + 0.5 * w
        E = start - x0
        g = _new(name(0x0181), 0x0181)
        g.components.append(Component(cm[0x0042]))
        g.contours.append(hook_contour((start, cap), (-1, 0), (0, -1), th, E, Ro, 0.35 * th, tan))
        made[0x0181] = g

    # --- Ƴ ƴ: Der obere rechte Arm endet in einem Haken nach rechts und unten.
    # Damit der Haken in die Zelle passt, wird der rechte Arm oberhalb eines
    # Drehpunkts nach links geschert (oben um `shift`, am Drehpunkt um 0). Der Arm
    # wird etwas steiler, behält aber seine Strichstärke.
    for cp, base, pivot_k in ((0x01B3, 0x0059, 0.42), (0x01B4, 0x0079, 0.0)):
        if cp in cm or base not in cm:
            continue
        d = _decomposed(font, cm[base])
        (xa, ytop, pa), (xb, _, pb) = _top_points(d, tan, "right")
        span = xb - xa
        th = 0.7 * span
        Ro = 1.1 * th
        shift = max(0.0, xb + Ro - 610)
        y_piv = pivot_k * ytop
        for c in d.contours:
            for p in c.points:
                ux = p.x - p.y * tan
                if ux > 300 and p.y > y_piv:
                    ux -= shift * (p.y - y_piv) / (ytop - y_piv)
                    p.x = round(ux + p.y * tan)
        xb2 = xb - shift
        start = xb2 - 0.5 * span
        g = _new(name(cp), cp)
        for c in d.contours:
            g.contours.append(c)
        g.contours.append(hook_contour((start, ytop), (1, 0), (0, -1), th, xb2 - start, Ro, 0.45 * th, tan))
        for a in font[cm[base]].anchors:
            g.anchors.append(Anchor(a.x, a.y, name=a.name))
        made[cp] = g

    for cp, g in made.items():
        font.layers.defaultLayer.insertGlyph(g, name=g.name, overwrite=False, copy=False)
        if font.glyphOrder:
            font.glyphOrder = list(font.glyphOrder) + [g.name]
    return {cp: g.name for cp, g in made.items()}
