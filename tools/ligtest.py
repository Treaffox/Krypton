"""Prüft die Code-Ligaturen (ss10) mit HarfBuzz.

  .venv/bin/python tools/ligtest.py [dist/variable/*.ttf …]

Für jede Zeichenfolge steht fest, welche Ligaturen entstehen müssen. Ohne
ss10 darf nie eine Ligatur entstehen. Die Zahl der Glyphen und die Breite
müssen immer der Zahl der Zeichen entsprechen (eine Zelle je Zeichen).
"""
import glob
import sys

import uharfbuzz as hb

CASES = {
    "a->b": ["hyphen_greater.liga"],
    "x<-y": ["less_hyphen.liga"],
    "a<->b": ["less_hyphen_greater.liga"],
    "x=>y": ["equal_greater.liga"],
    "a==b": ["equal_equal.liga"],
    "a===b": ["equal_equal_equal.liga"],
    "a!=b": ["exclam_equal.liga"],
    "a!==b": ["exclam_equal_equal.liga"],
    "f = x => x->y": ["equal_greater.liga", "hyphen_greater.liga"],
    "if (a != b && c == d)": ["exclam_equal.liga", "equal_equal.liga"],
    # bewusst ohne Ligatur
    "-->": [], "<--": [], "==>": [], "<==": [], "<=>": [], "====": [], "!===": [],
    "a<-1": [], "a<-9": [], ">->": [], "<-<": [], "=>>": [], ">=>": [], "<==>": [],
    "!!=": [], "<=": [], ">=": [], "|>": [], "::": [], "->>": [], "<<-": [],
}


def shape(font, text, feats):
    b = hb.Buffer()
    b.add_str(text)
    b.guess_segment_properties()
    hb.shape(font, b, feats)
    names = [font.glyph_to_string(i.codepoint) for i in b.glyph_infos]
    adv = sum(p.x_advance for p in b.glyph_positions)
    return names, adv


def check(path):
    face = hb.Face(hb.Blob.from_file_path(path))
    errors = 0
    for wght in (200, 400, 900):
        font = hb.Font(face)
        font.set_variations({"wght": wght})
        for feats_name, feats in (("ss10", {"ss10": True}), ("ss01+ss10", {"ss01": True, "ss10": True}),
                                  ("aus", {})):
            for text, want in CASES.items():
                names, adv = shape(font, text, feats)
                ligs = [n for n in names if n.endswith(".liga")]
                exp = want if feats else []
                if feats_name == "ss01+ss10":
                    exp = want  # Bindestrich aus ss01 (hyphen.a) muss ebenso greifen
                problems = []
                if ligs != exp:
                    problems.append(f"Ligaturen {ligs} statt {exp}")
                if len(names) != len(text):
                    problems.append(f"{len(names)} Glyphen für {len(text)} Zeichen")
                if adv != 600 * len(text):
                    problems.append(f"Breite {adv} statt {600 * len(text)}")
                if problems:
                    errors += 1
                    print(f"  FEHLER {path.split('/')[-1]} {wght} {feats_name} {text!r}: {'; '.join(problems)}")
    return errors


def main():
    paths = sys.argv[1:] or sorted(glob.glob("dist/variable/*.ttf")) + sorted(glob.glob("dist/otf/*.otf"))
    total = 0
    for p in paths:
        total += check(p)
    print(f"{len(paths)} Dateien, {len(CASES)} Fälle × 3 Gewichte × 3 Feature-Sätze: "
          + ("ok" if not total else f"{total} Fehler"))
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
