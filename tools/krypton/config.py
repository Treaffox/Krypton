"""Zentrale Parameter von Krypton. Designentscheidungen stehen hier, nicht im Code."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
VERSION = (ROOT / "VERSION").read_text().strip()
_major, _minor, _patch = (int(x) for x in VERSION.split("."))
VERSION_MAJOR = _major
VERSION_MINOR = _minor * 100 + _patch  # 0.1.0 -> 0.100 (head.fontRevision)

FAMILY = "Krypton"
PS_FAMILY = "Krypton"
FILE_STEM = "Krypton"
VENDOR_ID = "TRFX"
DESIGNER = "TRFX"
URL = "https://krypton.trfx.de"
COPYRIGHT = (
    "Copyright 2026 TRFX (https://krypton.trfx.de), with Reserved Font Name \"Krypton\". "
    "Based on Source Code Pro, Copyright 2010-2020 Adobe (http://www.adobe.com/), "
    "with Reserved Font Name 'Source'."
)
LICENSE_DESC = (
    "This Font Software is licensed under the SIL Open Font License, Version 1.1. "
    "This license is available with a FAQ at: https://openfontlicense.org"
)
LICENSE_URL = "https://openfontlicense.org"
DESCRIPTION = (
    "Krypton – eine technische Monospace für Code, Terminals und Daten. "
    "Abgeleitet von Source Code Pro, mit höherer x-Höhe, l mit Serifen, durchgestrichener Null "
    "und quadratischen Punkten."
)

UPSTREAM = ROOT / "upstream" / "scp"
SOURCES = ROOT / "sources"
DIST = ROOT / "dist"

STYLES = {
    "Upright": {
        "poles": {"ExtraLight": "Upright/Poles/pole_0/SourceCode-ExtraLight.ufo",
                  "Regular": "Upright/Poles/pole_1/SourceCode-Upright.ufo",
                  "Black": "Upright/Poles/pole_2/SourceCode-Black.ufo"},
        "gsub": "Upright/familyGSUB.fea",
        "suffix": "",
    },
    "Italic": {
        "poles": {"ExtraLight": "Italic/Poles/pole_0/SourceCode-ExtraLightItalic.ufo",
                  "Regular": "Italic/Poles/pole_1/SourceCode-Italic.ufo",
                  "Black": "Italic/Poles/pole_2/SourceCode-BlackItalic.ufo"},
        "gsub": "Italic/familyGSUB.fea",
        "suffix": "Italic",
    },
}

# Designkoordinaten der Master (wie Source Code Pro) und Zuordnung Userspace -> Design.
MASTER_DESIGN = {"ExtraLight": 0, "Regular": 368, "Black": 1000}
WEIGHTS = [  # (Userspace, Name, Designkoordinate)
    (200, "ExtraLight", 0), (300, "Light", 100), (400, "Regular", 368), (500, "Medium", 486),
    (600, "SemiBold", 600), (700, "Bold", 824), (800, "ExtraBold", 912), (900, "Black", 1000),
]
MASTER_WGHT = {"ExtraLight": 200, "Regular": 400, "Black": 900}

# x-Höhe: Faktor für den Bereich Grundlinie–x-Höhe (486 -> ~515 im Regular).
XHEIGHT_K = 1.06


# Vertikale Metriken: Zeilenhöhe 1,257 wie Source Code Pro (hhea). typo = hhea und
# USE_TYPO_METRICS, damit die Zeilenhöhe auf allen Systemen gleich ist. win deckt die
# gesamte Ausdehnung ab (keine abgeschnittenen Zeichen unter Windows); build.py setzt
# win aus der tatsächlichen Ausdehnung beider Stile, WIN ist nur der Startwert.
HHEA = (984, -273, 0)
TYPO = (984, -273, 0)
WIN = (984, 273)

# Mindestabstand Akzent ↔ Grundform (Einheiten). Darunter wird der Akzent angehoben.
ACCENT_GAP = 18
