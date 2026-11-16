#!/usr/bin/env python3
"""Erzeugt die Krypton-Quellen (UFO-Master + Designspace) aus Source Code Pro.

  prepare.py [--style Upright|Italic]

Ergebnis: sources/<Stil>/Krypton-<Master>.ufo und Krypton[-Italic].designspace
"""
import argparse
import json
import re
import shutil
import unicodedata
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from fontTools.designspaceLib import (AxisDescriptor, AxisLabelDescriptor, AxisMappingDescriptor,
                                      DesignSpaceDocument, DiscreteAxisDescriptor, InstanceDescriptor,
                                      RangeAxisSubsetDescriptor, SourceDescriptor, VariableFontDescriptor)

from ufoLib2.objects import Info

from krypton import config as C
from krypton.alternates import ZERO_PAIRS, l_pairs, relabel_features, swap_glyphs, zero_features
from krypton.italic_fill import fill as italic_fill, missing_names
from krypton.extras import add_case_pairs, add_case_pairs_2
from krypton.hooks import add_hooked
from krypton.ligatures import add_ligatures, features as liga_features
from krypton.clearance import ensure_clearance
from krypton.dots import align_upper_dots, find_dots, square_dots
from krypton.ufo_ops import full_intermediate, load_master
from krypton.xheight import classify, raise_xheight

INFO_KEEP = {"unitsPerEm", "xHeight", "capHeight", "ascender", "descender", "italicAngle",
             "postscriptUnderlinePosition", "postscriptUnderlineThickness", "postscriptIsFixedPitch",
             "openTypeOS2Panose", "openTypeOS2WidthClass", "openTypeOS2UnicodeRanges",
             "openTypeOS2CodePageRanges", "postscriptBlueValues", "postscriptOtherBlues",
             "postscriptStemSnapH", "postscriptStemSnapV", "postscriptBlueScale", "postscriptBlueShift",
             "postscriptBlueFuzz", "postscriptForceBold", "openTypeOS2SubscriptXSize",
             "openTypeOS2SubscriptYSize", "openTypeOS2SubscriptXOffset", "openTypeOS2SubscriptYOffset",
             "openTypeOS2SuperscriptXSize", "openTypeOS2SuperscriptYSize",
             "openTypeOS2SuperscriptXOffset", "openTypeOS2SuperscriptYOffset",
             "openTypeOS2StrikeoutSize", "openTypeOS2StrikeoutPosition", "guidelines"}


def muted_glyphs(style):
    """Im Zwischenmaster von Source Code Pro stummgeschaltete Glyphen."""
    ds = C.UPSTREAM / style / f"SourceCodeVF-{style}.designspace"
    text = ds.read_text()
    m = re.search(r'<source filename="Poles/pole_1/.*?</source>', text, re.S)
    return set(re.findall(r'<glyph mute="1" name="([^"]+)"', m.group(0))) if m else set()


def build_features(style):
    fea = (C.UPSTREAM / C.STYLES[style]["gsub"]).read_text()
    fea = re.sub(r"feature size \{.*?\} size;\n?", "", fea, flags=re.S)
    fea = zero_features(fea)
    if style == "Upright":
        fea = relabel_features(fea)
    else:
        # Die Kursive von Source Code Pro hat die griechischen/kyrillischen Regeln
        # auskommentiert (dort fehlten die Zeichen). Krypton hat sie: wieder aktivieren.
        m = re.search(r"#\tscript grek;.*?#\t\t\t\} BE_LC_SRB;\n", fea, re.S)
        if m:
            fea = fea.replace(m.group(0), re.sub(r"^#", "", m.group(0), flags=re.M))
        fea = fea.replace("#\tsub anoteleia by anoteleia.cap;", "\tsub anoteleia by anoteleia.cap;")
        m = re.search(r"#feature cv10 .*?#\} cv10;", fea, re.S)  # cv10: serbisches б
        if m:
            fea = fea.replace(m.group(0), re.sub(r"^#", "", m.group(0), flags=re.M))
        fea = fea.replace("#\tlookup BE_LC_SRB;", "\tlookup BE_LC_SRB;")  # ss03: serbisches б
    return "# Krypton: GSUB aus Source Code Pro (familyGSUB.fea), ohne 'size'.\n" \
           "# mark/mkmk und GDEF erzeugt ufo2ft aus den Ankern.\n\n" + fea + liga_features()


DOUBLE_MARKS = range(0x035C, 0x0363)  # Doppelakzente über/unter zwei Zeichen


def mark_glyphs(font):
    """Kombinierende Akzente: benannte cmb-Glyphen mit Ankern und alle Mn-Zeichen."""
    out = set()
    for g in font:
        if "cmb" in g.name and any(a.name.startswith("_") for a in g.anchors):
            out.add(g.name)
        elif g.unicodes and unicodedata.category(chr(g.unicodes[0])) == "Mn":
            out.add(g.name)
    return sorted(out)


def zero_width_marks(font, marks):
    """Akzente ohne Vorschub. Doppelakzente (SCP: GPOS <-300 0 -600 0>) werden um
    eine halbe Zelle nach links gesetzt, damit sie über der Grenze zweier Zeichen stehen."""
    for n in marks:
        if n not in font:
            continue
        g = font[n]
        if g.width and g.unicodes and g.unicodes[0] in DOUBLE_MARKS:
            shift = -g.width / 2
            for c in g.contours:
                for pt in c.points:
                    pt.x = round(pt.x + shift)
            for a in g.anchors:
                a.x = round(a.x + shift)
        g.width = 0


BLOCK_OVERLAP = 12  # Einheiten über die Zellgrenze (wie die Rahmenlinien von Source Code Pro)


def overlap_blocks(font):
    """Blockelemente (U+2580–U+259F) ragen links und rechts minimal über die Zelle,
    damit nebeneinanderstehende Blöcke im Browser ohne Kantenglättungs-Fugen
    verschmelzen. Nur Punkte genau auf der Zellgrenze werden verschoben."""
    n = 0
    for g in font:
        if not g.unicodes or not (0x2580 <= g.unicodes[0] <= 0x259F) or g.width != 600:
            continue
        if 0x2591 <= g.unicodes[0] <= 0x2593:
            continue  # Schattierungen sind Punktmuster
        for c in g.contours:
            for p in c.points:
                if p.x == 0:
                    p.x = -BLOCK_OVERLAP
                    n += 1
                elif p.x == g.width:
                    p.x = g.width + BLOCK_OVERLAP
                    n += 1
    return n


def fix_shared_segments(font):
    """Zwei Konturen mit einer gemeinsamen Kante (z. B. њ aus Source Code Pro)
    stören manche Rasterizer (fontbakery: overlapping_path_segments). Die Kante
    der späteren Kontur wird um 1 Einheit in deren Inneres verschoben; die
    Konturen überlappen dann flächig statt kantengleich."""
    fixed = []
    for g in font:
        seen = set()
        for ci, c in enumerate(g.contours):
            pts = c.points
            n = len(pts)
            for i, p in enumerate(pts):
                q = pts[i - 1]
                if p.type != "line" or q.type is None:
                    continue
                key = frozenset(((q.x, q.y), (p.x, p.y)))
                if key in seen and ci > 0:
                    xs = [t.x for t in pts]
                    ys = [t.y for t in pts]
                    cx, cy = (min(xs) + max(xs)) / 2, (min(ys) + max(ys)) / 2
                    for t in (q, p):
                        if q.y == p.y:
                            t.y += 1 if cy > t.y else -1
                        else:
                            t.x += 1 if cx > t.x else -1
                    fixed.append(g.name)
            for i, p in enumerate(pts):
                q = pts[i - 1]
                if p.type == "line" and q.type is not None:
                    seen.add(frozenset(((q.x, q.y), (p.x, p.y))))
    return sorted(set(fixed))


def fix_degenerate(font):
    fixed = 0
    for g in font:
        for c in g.contours:
            pts = c.points
            n = len(pts)
            for i, p in enumerate(pts):
                q = pts[i - 1]
                if p.type in ("line", "curve") and q.type is not None and (p.x, p.y) == (q.x, q.y) and n > 2:
                    nxt = pts[(i + 1) % n]
                    p.x += 1 if nxt.x - p.x >= 0 else -1
                    fixed += 1
    return fixed


def set_info(font, master, style, win):
    keep = {k: getattr(font.info, k) for k in INFO_KEEP}
    font.info = Info()
    info = font.info
    for k, v in keep.items():
        if v is not None:
            setattr(info, k, v)
    suffix = C.STYLES[style]["suffix"]
    info.familyName = C.FAMILY
    info.styleName = suffix if (master == "Regular" and suffix) else (master + " " + suffix).strip()
    info.versionMajor, info.versionMinor = C.VERSION_MAJOR, C.VERSION_MINOR
    info.openTypeNameVersion = f"Version {C.VERSION_MAJOR}.{C.VERSION_MINOR:03d}; Krypton {C.VERSION}"
    info.copyright = C.COPYRIGHT
    info.openTypeNameDesigner = C.DESIGNER
    info.openTypeNameDesignerURL = C.URL
    info.openTypeNameManufacturer = "TRFX"
    info.openTypeNameManufacturerURL = C.URL
    info.openTypeNameLicense = C.LICENSE_DESC
    info.openTypeNameLicenseURL = C.LICENSE_URL
    info.openTypeNameDescription = C.DESCRIPTION
    info.openTypeOS2VendorID = C.VENDOR_ID
    info.openTypeOS2WeightClass = C.MASTER_WGHT[master]
    info.openTypeOS2Type = []  # fsType 0: installierbar
    info.postscriptIsFixedPitch = True
    info.openTypeHheaAscender, info.openTypeHheaDescender, info.openTypeHheaLineGap = C.HHEA
    info.openTypeOS2TypoAscender, info.openTypeOS2TypoDescender, info.openTypeOS2TypoLineGap = C.TYPO
    info.openTypeOS2WinAscent, info.openTypeOS2WinDescent = win
    info.openTypeOS2Selection = [7]  # USE_TYPO_METRICS: Zeilenhöhe überall aus typo = hhea
    pan = list(info.openTypeOS2Panose or [2, 11, 5, 9, 3, 4, 3, 2, 2, 4])
    pan[3] = 9  # bProportion = monospaced
    info.openTypeOS2Panose = pan
    if suffix:
        info.italicAngle = info.italicAngle or -11
    else:
        info.italicAngle = 0
    info.postscriptSlantAngle = info.italicAngle


def build_designspace(style, paths):
    st = C.STYLES[style]
    italic = bool(st["suffix"])
    doc = DesignSpaceDocument()
    doc.formatVersion = "5.0"
    doc.elidedFallbackName = "Regular"
    wght = AxisDescriptor(tag="wght", name="Weight", minimum=200, default=400, maximum=900,
                          map=[(u, d) for u, _, d in C.WEIGHTS])
    wght.axisLabels = [AxisLabelDescriptor(name=n, userValue=u, elidable=(u == 400),
                                           linkedUserValue=700 if u == 400 else None)
                       for u, n, _ in C.WEIGHTS]
    ital = DiscreteAxisDescriptor(tag="ital", name="Italic", values=[1 if italic else 0],
                                  default=1 if italic else 0)
    ital.axisLabels = [AxisLabelDescriptor(name="Italic", userValue=1)] if italic else \
        [AxisLabelDescriptor(name="Roman", userValue=0, elidable=True, linkedUserValue=1)]
    doc.axes = [wght, ital]
    for master, path in paths.items():
        s = SourceDescriptor(filename=path.name, familyName=C.FAMILY,
                             styleName=(master + (" " + st["suffix"] if italic else "")).strip(),
                             designLocation={"Weight": C.MASTER_DESIGN[master], "Italic": 1 if italic else 0})
        if master == "Regular":
            s.copyLib = s.copyInfo = s.copyGroups = s.copyFeatures = True
        doc.addSource(s)
    for u, n, d in C.WEIGHTS:
        if italic:
            style_name = "Italic" if n == "Regular" else f"{n} Italic"
            ps = f"{C.PS_FAMILY}-{'Italic' if n == 'Regular' else n + 'Italic'}"
        else:
            style_name, ps = n, f"{C.PS_FAMILY}-{n}"
        if n in ("Regular", "Bold"):
            smf = C.FAMILY
            sms = ("bold " if n == "Bold" else "") + ("italic" if italic else "regular")
            sms = sms.replace("bold regular", "bold")
        else:
            smf, sms = f"{C.FAMILY} {n}", ("italic" if italic else "regular")
        doc.addInstance(InstanceDescriptor(
            familyName=C.FAMILY, styleName=style_name, postScriptFontName=ps,
            styleMapFamilyName=smf, styleMapStyleName=sms, filename=f"instances/{ps}.ufo",
            designLocation={"Weight": d, "Italic": 1 if italic else 0}))
    vf_name = f"{C.FILE_STEM}{'-Italic' if italic else ''}[wght]"
    doc.addVariableFont(VariableFontDescriptor(name=vf_name, filename=vf_name,
                                               axisSubsets=[RangeAxisSubsetDescriptor(name="Weight")]))
    return doc


def prepare_style(style, log):
    st = C.STYLES[style]
    t0 = time.time()
    poles = {m: load_master(C.UPSTREAM / p) for m, p in st["poles"].items()}
    angle = float(poles["ExtraLight"].info.italicAngle or 0.0)
    muted = muted_glyphs(style)
    regular, bad, used = full_intermediate(poles["ExtraLight"], poles["Black"],
                                           C.MASTER_DESIGN["Regular"] / 1000, poles["Regular"], muted)
    log[f"{style}.regular"] = {"incompatible": bad, "from_pole": len(used), "muted": sorted(muted)}
    masters = {"ExtraLight": poles["ExtraLight"], "Regular": regular, "Black": poles["Black"]}
    if style == "Italic":  # Griechisch/Kyrillisch aus dem Aufrechten ergänzen
        up = C.STYLES["Upright"]["poles"]
        upoles = {m: load_master(C.UPSTREAM / p) for m, p in up.items()}
        ureg, _, _ = full_intermediate(upoles["ExtraLight"], upoles["Black"],
                                       C.MASTER_DESIGN["Regular"] / 1000, upoles["Regular"],
                                       muted_glyphs("Upright"))
        umasters = {"ExtraLight": upoles["ExtraLight"], "Regular": ureg, "Black": upoles["Black"]}
        names = missing_names(ureg, regular)
        for m, f in masters.items():
            log[f"{style}.fill.{m}"] = italic_fill(umasters[m], f, names, angle)
        log[f"{style}.fill_glyphs"] = len(names)
    for f in masters.values():  # durchgestrichene Null als Standard
        swap_glyphs(f, ZERO_PAIRS)
    if style == "Upright":  # l mit Serifen als Standard
        pairs = l_pairs(regular)
        for f in masters.values():
            swap_glyphs(f, pairs)
        log[f"{style}.l_swapped"] = sorted(pairs)

    case_names = add_case_pairs(masters["Regular"], angle)
    case_names.update(add_case_pairs_2(masters["Regular"], angle))
    case_names.update(add_hooked(masters["Regular"], angle))
    for m in ("ExtraLight", "Black"):
        add_case_pairs(masters[m], angle, case_names)
        add_case_pairs_2(masters[m], angle, case_names)
        add_hooked(masters[m], angle, case_names)
    log[f"{style}.case_pairs"] = sorted(case_names.values())

    ref = masters["Regular"]
    classes = classify(ref)
    log[f"{style}.xheight_classes"] = {"lowercase": len(classes[0]), "marks": len(classes[1]),
                                       "punct": sorted(classes[2])}
    dot_sel = find_dots(ref)
    for m in ("ExtraLight", "Black"):
        other = find_dots(masters[m])
        diff = sorted(set(dot_sel) ^ set(other))
        if diff:
            log[f"{style}.dots_mismatch_{m}"] = diff
    dot_sel = {k: v for k, v in dot_sel.items()
               if all(find_dots(masters[m]).get(k) == v for m in ("ExtraLight", "Black"))}
    log[f"{style}.dots"] = sorted(dot_sel)
    marks = mark_glyphs(ref)

    out_dir = C.SOURCES / style
    if out_dir.is_dir() and out_dir.parent == C.SOURCES:
        shutil.rmtree(out_dir)  # nur erzeugte Quellen
    out_dir.mkdir(parents=True, exist_ok=True)

    for m, f in masters.items():
        rep = {"xheight_delta": raise_xheight(f, C.XHEIGHT_K, classes, angle)}
        rep["dots_squared"] = square_dots(f, dot_sel, angle)
        rep["upper_dots"] = align_upper_dots(f, angle)
        rep["degenerate_fixed"] = fix_degenerate(f)
        rep["shared_segments_fixed"] = fix_shared_segments(f)
        rep["block_points"] = overlap_blocks(f)
        rep["accent_clearance"] = ensure_clearance(f, C.ACCENT_GAP, angle)
        zero_width_marks(f, marks)  # statt Ausgleich per GPOS wie in Source Code Pro
        if "ZWNBS" in f:
            f["ZWNBS"].width = 0
        rep["xheight"] = f.info.xHeight
        rep["ligatures"] = len(add_ligatures(f, angle))  # aus den fertigen Formen
        log[f"{style}.{m}"] = rep

    # Gesamtausdehnung nur fürs Protokoll
    ymax, ymin = C.HHEA[0], C.HHEA[1]
    for f in masters.values():
        for g in f:
            b = g.getBounds(f)
            if b:
                ymax, ymin = max(ymax, b.yMax), min(ymin, b.yMin)
    log[f"{style}.bbox"] = (int(ymax), int(ymin))
    win = C.WIN  # wie Source Code Pro; Kastenzeichen ragen absichtlich darüber hinaus

    paths = {}
    for m, f in masters.items():
        f.features.text = build_features(style)
        f.lib["public.openTypeCategories"] = {g.name: ("mark" if g.name in marks else "base") for g in f}
        for k in [k for k in f.lib if k.startswith("com.typemytype") or k.startswith("com.adobe")]:
            del f.lib[k]
        f.groups.clear()
        # Für Hinting und Prüfwerkzeuge: keine verschachtelten oder transformierten Komponenten
        f.lib["com.github.googlei18n.ufo2ft.filters"] = [
            # Komposita (ä, ọ, Ä …) erben die Anker ihrer Komponenten, damit weitere
            # kombinierende Akzente darauf gestapelt werden (mark/mkmk)
            {"name": "propagateAnchors", "pre": True},
            {"name": "flattenComponents", "pre": True},
            {"name": "decomposeTransformedComponents", "pre": True},
        ]
        f.kerning.clear()
        set_info(f, m, style, win)
        name = f"{C.FILE_STEM}-{st['suffix']}" if (m == "Regular" and st["suffix"]) else \
            f"{C.FILE_STEM}-{m}{st['suffix']}"
        path = out_dir / f"{name}.ufo"
        f.save(path, overwrite=True)
        paths[m] = path
    doc = build_designspace(style, paths)
    ds = out_dir / f"{C.FILE_STEM}{'-Italic' if st['suffix'] else ''}.designspace"
    doc.write(ds)
    log[f"{style}.seconds"] = round(time.time() - t0, 1)
    return ds


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--style", choices=list(C.STYLES), action="append")
    a = ap.parse_args()
    log = {}
    for style in a.style or list(C.STYLES):
        print("designspace:", prepare_style(style, log))
    C.SOURCES.mkdir(exist_ok=True)
    (C.SOURCES / "prepare-log.json").write_text(json.dumps(log, indent=1, ensure_ascii=False))
    for k, v in log.items():
        s = json.dumps(v, ensure_ascii=False)
        print(k, s[:300])


if __name__ == "__main__":
    main()
