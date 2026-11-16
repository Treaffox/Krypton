"""Schrift für Beschriftungen in Probeabzügen (nur Bildbeschriftung, nicht Teil der Schrift).

Reihenfolge: Umgebungsvariable KRYPTON_LABEL_FONT, IBM Plex Mono aus upstream/plex
(optional, siehe scripts/fetch-upstream.sh), gebautes Krypton aus dist/, sonst
die eingebaute Pillow-Schrift.
"""
import os
from pathlib import Path

from PIL import ImageFont

ROOT = Path(__file__).resolve().parents[1]
CANDIDATES = [
    ROOT / "upstream/plex/packages/plex-mono/fonts/complete/ttf/IBMPlexMono-Regular.ttf",
    ROOT / "dist/ttf/Krypton-Regular.ttf",
    ROOT / "fonts/ttf/Krypton-Regular.ttf",
]


def label_font(size):
    env = os.environ.get("KRYPTON_LABEL_FONT")
    for p in ([Path(env)] if env else []) + CANDIDATES:
        if p.is_file():
            return ImageFont.truetype(str(p), size)
    try:
        return ImageFont.load_default(size)
    except TypeError:  # Pillow < 10.1
        return ImageFont.load_default()
