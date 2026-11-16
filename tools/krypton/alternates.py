"""Standardformen tauschen.

Krypton nimmt im Aufrechten das l mit Serifen (oben links Anschlag, unten
durchgehender Fuß, wie bei IBM Plex Mono) als Standard. Das l mit
geschwungenem Fuß aus Source Code Pro bleibt über ss04/cv04 erreichbar.
Kursiv hat nur das geschwungene l und bleibt so.
"""
import re

L_FAMILY = {"lslash", "lbelt", "lcat"}


def l_pairs(font):
    pairs = {}
    for g in font:
        if not g.name.endswith(".a"):
            continue
        base = g.name[:-2]
        if base not in font:
            continue
        b = font[base]
        if base == "l" or base in L_FAMILY or any(c.baseGlyph == "l" for c in b.components):
            pairs[base] = g.name
    return pairs


def swap_glyphs(font, pairs):
    """Tauscht Inhalte (Konturen, Komponenten, Anker, Breite) der Paare.
    Namen und Unicodes bleiben, Komponentenverweise werden mitgetauscht."""
    mapping = {}
    for a, b in pairs.items():
        mapping[a], mapping[b] = b, a
    snap = {n: font[n].copy() for n in mapping}
    for n, other in mapping.items():
        g = font[n]
        src = snap[other]
        g.clearContours()
        g.clearComponents()
        g.clearAnchors()
        for c in src.contours:
            g.contours.append(c)
        for c in src.components:
            g.components.append(c)
        for a in src.anchors:
            g.anchors.append(a)
        g.width = src.width
    for g in font:
        for c in g.components:
            if c.baseGlyph in mapping and g.name in mapping:
                c.baseGlyph = mapping[c.baseGlyph]
    return len(pairs)


def relabel_features(fea):
    """ss04/cv04 schalten jetzt das geschwungene l ein."""
    for tag in ("ss04", "cv04"):
        m = re.search(rf"feature {tag} \{{.*?\}} {tag};", fea, re.S)
        if not m:
            continue
        block = m.group(0)
        new = re.sub(r'name 3 1 0x0409 "[^"]*";', 'name 3 1 0x0409 "tailed l";', block)
        new = re.sub(r'\n\s*name 3 1 0x04(08|19) "[^"]*";[^\n]*', "", new)
        fea = fea.replace(block, new)
    return fea


# Durchgestrichene Null als Standard (seit 0.1.0). Die Null mit Punkt
# bleibt über ss08/cv12/salt erreichbar.
ZERO_PAIRS = {"zero": "zero.0", "zero.onum": "zero.0o", "zero.cap": "zero.0c"}


def zero_features(fea):
    """Die Ersetzung ZERO_SLASH führt nach dem Tausch zur Null mit Punkt:
    umbenennen, 'zero' entfernen (das Feature meint laut Spezifikation die
    durchgestrichene Null, die jetzt Standard ist), ss08 'dotted zero' anlegen,
    cv12 neu beschriften."""
    fea = fea.replace("ZERO_SLASH", "ZERO_DOTTED")
    fea = re.sub(r"feature zero \{.*?\} zero;\n?", "", fea, flags=re.S)
    m = re.search(r"feature cv12 \{.*?\} cv12;", fea, re.S)
    if m:
        block = m.group(0)
        new = re.sub(r'name 3 1 0x0409 "[^"]*";', 'name 3 1 0x0409 "dotted zero [0]";', block)
        new = re.sub(r'\n\s*name 3 1 0x04(08|19) "[^"]*";[^\n]*', "", new)
        new = new.replace("(slashed zero)", "(dotted zero)")
        fea = fea.replace(block, new)
    fea = fea.rstrip() + """

#--------------------------------------
feature ss08 { # Stylistic Set 8 (dotted zero) – Krypton
	featureNames {
		name 3 1 0x0409 "dotted zero [0]"; # English US
	};
	lookup ZERO_DOTTED;
} ss08;
"""
    return fea
