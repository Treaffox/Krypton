"""Fehlende Großbuchstaben zu vorhandenen Kleinbuchstaben (Groß-/Kleinschreibung).

Source Code Pro hat viele IPA- und archaisch-griechische Kleinbuchstaben ohne
Großform. Hier werden nur die ergänzt, die sich ohne neue Zeichnung exakt aus
vorhandenen Formen ergeben:

  Komponente (gleiche Form):  Ɖ=Đ  Ɪ=I  Ɵ=Θ  Ʃ=Σ  Ʌ=Λ  Ϝ=F
  Komponente plus Querstrich:  Ɨ=I+-  Ʉ=U+–
  gespiegelt:                  Ɔ=C gespiegelt   Ɛ=З gespiegelt
  gedreht (180°):              Ɯ=M gedreht      Ʊ=Ω gedreht

Kursive werden vor dem Spiegeln entneigt und danach wieder geneigt.
"""
import math

from fontTools.pens.pointPen import SegmentToPointPen
from fontTools.pens.recordingPen import DecomposingRecordingPen
from ufoLib2.objects import Component, Contour, Glyph, Point

COMPONENT = {0x0189: 0x0110, 0xA7AE: 0x0049, 0x019F: 0x0398, 0x01A9: 0x03A3, 0x0245: 0x039B, 0x03DC: 0x0046}
BARRED = {0x0197: (0x0049, 0x002D), 0x0244: (0x0055, 0x2013)}
MIRROR = {0x0186: 0x0043, 0x0190: 0x0417}
ROTATE = {0x019C: 0x004D, 0x01B1: 0x03A9}


def _cmap(font):
    return {u: g.name for g in font for u in g.unicodes}


def _decomposed(font, name):
    """Konturen eines Glyphs inklusive aufgelöster Komponenten."""
    rec = DecomposingRecordingPen(font)
    font[name].draw(rec)
    out = Glyph()
    rec.replay(SegmentToPointPen(out.getPointPen()))
    return out


def add_case_pairs(font, italic_angle=0.0, names=None):
    """Legt die Glyphen an. names: {codepoint: glyphname} aus dem Referenzmaster,
    damit alle Master dieselben Namen bekommen. Gibt die Namen zurück."""
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    cm = _cmap(font)
    cap = font.info.capHeight or 660
    made = {}

    def new(cp, width=600):
        name = (names or {}).get(cp) or f"uni{cp:04X}"
        g = Glyph(name)
        g.unicodes = [cp]
        g.width = width
        return g

    for cp, src in COMPONENT.items():
        if cp in cm or src not in cm:
            continue
        g = new(cp)
        g.components.append(Component(cm[src]))
        made[cp] = g
    for cp, (base, bar) in BARRED.items():
        if cp in cm or base not in cm or bar not in cm:
            continue
        g = new(cp)
        g.components.append(Component(cm[base]))
        g.components.append(Component(cm[bar]))
        made[cp] = g
    for table, mode in ((MIRROR, "mirror"), (ROTATE, "rotate")):
        for cp, src in table.items():
            if cp in cm or src not in cm:
                continue
            d = _decomposed(font, cm[src])
            g = new(cp, font[cm[src]].width)
            w = g.width
            for c in d.contours:
                pts = [(p.x, p.y, p.type, p.smooth) for p in c.points]
                if mode == "mirror":
                    # entneigen, spiegeln um die Zellmitte, neigen; Laufrichtung umkehren
                    pts = [(w - (x - y * tan) + y * tan, y, t, s) for x, y, t, s in pts]
                    pts = _reverse(pts)
                else:
                    # 180° um die Mitte der Zelle in Versalhöhe; Neigung bleibt erhalten
                    pts = [(w - x, cap - y, t, s) for x, y, t, s in pts]
                g.contours.append(Contour([Point(round(x), round(y), t, s) for x, y, t, s in pts]))
            made[cp] = g
    for cp, g in made.items():
        font.layers.defaultLayer.insertGlyph(g, name=g.name, overwrite=False, copy=False)
        if font.glyphOrder:
            font.glyphOrder = list(font.glyphOrder) + [g.name]
    return {cp: g.name for cp, g in made.items()}


def _reverse(pts):
    """Kehrt die Richtung einer UFO-Kontur um (Punkttypen wandern mit)."""
    if not pts:
        return pts
    # In UFO gehört der Typ eines On-Curve-Punkts zum Segment, das an ihm endet.
    # Umkehren: Reihenfolge umdrehen, dann die Segmenttypen um ein Segment verschieben.
    rev = list(reversed(pts))
    on = [i for i, p in enumerate(rev) if p[2] is not None]
    if not on:
        return rev
    types = [rev[i][2] for i in on]
    # Das Segment B→A (in rev endet es an on[k+1]) hat den Typ, der im Original an B (on[k]) stand.
    new_types = types[-1:] + types[:-1]
    out = list(rev)
    for k, i in enumerate(on):
        x, y, _, s = out[i]
        out[i] = (x, y, new_types[k], s)
    return out


# ---------------------------------------------------------------------------
# Phase 2: weitere Großformen aus Kleinbuchstaben und Teilen
#
# Gestreckt: Der Kleinbuchstabe wird vertikal auf Versalhöhe gebracht. Nur der
# Mittelteil wird gestreckt; oberes und unteres Band (je 16 % der Höhe) werden
# nur verschoben, damit waagrechte Striche ihre Stärke behalten.
#   Quelle (lo, hi) -> Ziel (lo', hi'); Werte: "xh", "cap", "desc" (= yMin), Zahl
REMAP = {
    0x0194: (0x0263, (0, "xh"), (0, "cap")),          # Ɣ aus ɣ (Schleife unter der Grundlinie bleibt)
    0x01B7: (0x0292, ("desc", "xh"), (-12, "cap")),   # Ʒ aus ʒ (steht auf der Grundlinie)
    0x01B2: (0x028B, (-12, "xh"), (-12, "cap")),      # Ʋ aus ʋ
    0xA78D: (0x0265, ("desc", "xh"), (0, "cap")),     # Ɥ aus ɥ
    0x03D8: (0x03D9, (0, "xh"), (0, "cap")),          # Ϙ aus ϙ (Stiel unter der Grundlinie bleibt)
    0x03DA: (0x03DB, (0, "xh"), (0, "cap")),          # Ϛ aus ϛ
    0x03E0: (0x03E1, (0, "top"), (0, "cap")),         # Ϡ aus ϡ
    0xA7B2: ("jcrossedtail.d", (0, "xh"), (0, "cap")),  # Ʝ aus ʝ ohne Punkt (Schwanz unten bleibt)
}


def _remap_y(y, lo, hi, nlo, nhi, band):
    if y <= lo + band:
        return y + (nlo - lo)
    if y >= hi - band:
        return y + (nhi - hi)
    a, b = lo + band, hi - band
    na, nb = nlo + band, nhi - band
    return na + (y - a) * (nb - na) / (b - a)


def add_case_pairs_2(font, italic_angle=0.0, names=None):
    tan = math.tan(math.radians(-italic_angle)) if italic_angle else 0.0
    cm = _cmap(font)
    xh, cap = font.info.xHeight, font.info.capHeight
    made = {}

    def new(cp):
        g = Glyph((names or {}).get(cp) or f"uni{cp:04X}")
        g.unicodes = [cp]
        g.width = 600
        return g

    for cp, (src, (slo, shi), (dlo, dhi)) in REMAP.items():
        sname = src if isinstance(src, str) else cm.get(src)
        if cp in cm or sname not in font:
            continue
        d = _decomposed(font, sname)
        b = font[sname].getBounds(font)
        val = {"xh": xh, "cap": cap, "desc": b.yMin, "top": b.yMax}
        lo, hi = val.get(slo, slo), val.get(shi, shi)
        nlo, nhi = val.get(dlo, dlo), val.get(dhi, dhi)
        band = 0.16 * (hi - lo)
        g = new(cp)
        for c in d.contours:
            pts = []
            for p in c.points:
                ux = p.x - p.y * tan
                ny = _remap_y(p.y, lo, hi, nlo, nhi, band)
                pts.append(Point(round(ux + ny * tan), round(ny), p.type, p.smooth))
            g.contours.append(Contour(pts))
        made[cp] = g

    # Ɬ = L + Gürtel aus ɬ (eigene Kontur in ɬ), mittig auf den L-Stamm
    if 0xA7AD not in cm and 0x026C in cm and 0x004C in cm:
        lb, L = font[cm[0x026C]], font[cm[0x004C]]
        belt = [c for c in lb.contours]
        if len(belt) == 1 and lb.components:
            un = lambda p: (p.x - p.y * tan, p.y)
            top = max(p.y for c in L.contours for p in c.points)
            xs = [un(p)[0] for c in L.contours for p in c.points if p.y == top]
            stem_c = (min(xs) + max(xs)) / 2
            bx = [un(p)[0] for p in belt[0].points]
            by = [p.y for p in belt[0].points]
            dx = stem_c - (min(bx) + max(bx)) / 2
            dy = cap / 2 - (min(by) + max(by)) / 2
            g = new(0xA7AD)
            g.components.append(Component(cm[0x004C]))
            g.contours.append(Contour([Point(round(un(p)[0] + dx + (p.y + dy) * tan), round(p.y + dy), p.type, p.smooth)
                                       for p in belt[0].points]))
            made[0xA7AD] = g

    # Ϗ = K + Schwanz aus ϗ (eigene Kontur in ϗ), an das rechte Bein von K
    if 0x03CF not in cm and 0x03D7 in cm and 0x004B in cm:
        kai, K = font[cm[0x03D7]], font[cm[0x004B]]
        if len(kai.contours) == 1 and kai.components:
            base = font[kai.components[0].baseGlyph]
            def leg(gl):
                d = _decomposed(font, gl.name)
                return max(p.x for c in d.contours for p in c.points if p.y == 0)
            dx = leg(K) - leg(base)
            g = new(0x03CF)
            g.components.append(Component(cm[0x004B]))
            g.contours.append(Contour([Point(p.x + dx, p.y, p.type, p.smooth) for p in kai.contours[0].points]))
            made[0x03CF] = g

    for cp, g in made.items():
        font.layers.defaultLayer.insertGlyph(g, name=g.name, overwrite=False, copy=False)
        if font.glyphOrder:
            font.glyphOrder = list(font.glyphOrder) + [g.name]
    return {cp: g.name for cp, g in made.items()}


# Nicht automatisch erzeugt: Ɓ Ɦ Ɲ Ɽ Ʀ Ʈ Ʝ. Versuch 2026-11-15: Haken/Schwanz als
# Differenz (Kleinbuchstabe mit − ohne Zusatz) auszuschneiden ergab je Master
# verschiedene Konturstrukturen (nicht interpolierbar) und kursiv gar keine
# brauchbaren Teile. Diese Zeichen brauchen echte Zeichenarbeit.
