#!/usr/bin/env python3
"""Baut die öffentliche Seite krypton.trfx.de nach site/dist/.

  site.py

Voraussetzung: tools/build.py ist gelaufen (dist/ enthält die Fonts).
Alles, was hier landet, ist öffentlich: keine Host-Pfade, Server, Ports oder
internen Namen in Texte schreiben.
"""
import html
import json
import re
import shutil
import sys
import unicodedata
import zipfile
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from fontTools.ttLib import TTFont
from PIL import Image
from krypton import config as C

SITE = C.ROOT / "site"
STATIC = SITE / "static"
OUT = SITE / "dist"
V = C.VERSION
VF_UP = C.DIST / "variable" / f"{C.FILE_STEM}[wght].ttf"

GITHUB_URL = "https://github.com/Treaffox/Krypton"
GH_ICON = '<svg class="gh" viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false"><path fill="currentColor" d="M12 .5C5.37.5 0 5.87 0 12.5c0 5.3 3.438 9.8 8.205 11.385.6.113.82-.258.82-.577 0-.285-.01-1.04-.015-2.04-3.338.724-4.042-1.61-4.042-1.61-.546-1.385-1.335-1.755-1.335-1.755-1.087-.744.084-.729.084-.729 1.205.084 1.838 1.236 1.838 1.236 1.07 1.835 2.809 1.305 3.495.998.108-.776.417-1.305.76-1.605-2.665-.3-5.466-1.332-5.466-5.93 0-1.31.465-2.38 1.235-3.22-.135-.303-.54-1.523.105-3.176 0 0 1.005-.322 3.3 1.23.96-.267 1.98-.399 3-.405 1.02.006 2.04.138 3 .405 2.28-1.552 3.285-1.23 3.285-1.23.645 1.653.24 2.873.12 3.176.765.84 1.23 1.91 1.23 3.22 0 4.61-2.805 5.625-5.475 5.92.42.36.81 1.096.81 2.22 0 1.606-.015 2.896-.015 3.286 0 .315.21.69.825.57C20.565 22.295 24 17.8 24 12.5 24 5.87 18.627.5 12 .5z"/></svg>'
FOOTER_LINKS = [
    ("Datenschutz", "https://www.trfx.de/dsb"), ("AGB", "https://www.trfx.de/agb"),
    ("Impressum", "https://www.trfx.de/impressum"), ("Kontakt", "https://www.trfx.de/contact"),
    ("Sache des Tages", "https://www.trfx.de/sdt"), ("Server Status", "https://status.trfx.de/"),
    ("Socials", "https://www.trfx.de/socials"), ("SSO", "https://github.com/Treaffox/selfhosted-sso"),
    ("SAINT", "https://github.com/Treaffox/saint-monitoring"), ("TPN", "https://push.trfx.de/"),
    ("Twitch Logs", "https://logs.trfx.de/"),
]

WEIGHTS = [(u, n) for u, n, _ in C.WEIGHTS]

BLOCKS = [
    (0x0020, 0x007F, "Basis-Latein", "latein"), (0x00A0, 0x00FF, "Latein-1, Ergänzung", "latein"),
    (0x0100, 0x017F, "Latein, erweitert A", "latein"), (0x0180, 0x024F, "Latein, erweitert B", "latein"),
    (0x0250, 0x02AF, "IPA", "latein"), (0x02B0, 0x02FF, "Modifikatoren", "symbole"),
    (0x0300, 0x036F, "Kombinierende Diakritika", "latein"), (0x0370, 0x03FF, "Griechisch", "griechisch"),
    (0x0400, 0x04FF, "Kyrillisch", "kyrillisch"), (0x0500, 0x052F, "Kyrillisch, Ergänzung", "kyrillisch"),
    (0x1D00, 0x1DBF, "Phonetische Erweiterungen", "latein"),
    (0x1E00, 0x1EFF, "Latein, erweitert zusätzlich", "latein"), (0x1F00, 0x1FFF, "Griechisch, erweitert", "griechisch"),
    (0x2000, 0x206F, "Interpunktion", "symbole"), (0x2070, 0x209F, "Hoch- und Tiefstellung", "ziffern"),
    (0x20A0, 0x20CF, "Währungen", "symbole"), (0x2100, 0x214F, "Buchstabenartige Symbole", "symbole"),
    (0x2150, 0x218F, "Zahlzeichen", "ziffern"), (0x2190, 0x21FF, "Pfeile", "symbole"),
    (0x2200, 0x22FF, "Mathematische Operatoren", "symbole"), (0x2300, 0x23FF, "Technische Zeichen", "symbole"),
    (0x2400, 0x243F, "Steuerzeichen-Symbole", "symbole"), (0x2460, 0x24FF, "Umschlossene Zeichen", "ziffern"),
    (0x2500, 0x257F, "Rahmen", "rahmen"), (0x2580, 0x259F, "Blockelemente", "rahmen"),
    (0x25A0, 0x25FF, "Geometrische Formen", "symbole"), (0x2600, 0x27BF, "Verschiedene Symbole", "symbole"),
    (0x27C0, 0x2BFF, "Weitere Pfeile und Symbole", "symbole"),
    (0x2C60, 0x2C7F, "Latein, erweitert C", "latein"), (0x2E00, 0x2E7F, "Ergänzende Interpunktion", "symbole"),
    (0xA700, 0xA7FF, "Latein, erweitert D", "latein"), (0xE000, 0xF8FF, "Powerline (privater Bereich)", "rahmen"),
    (0xFB00, 0xFB4F, "Ligaturen", "latein"), (0xFFF0, 0xFFFF, "Sonderzeichen", "symbole"),
]
GROUPS = [("alle", "Alle"), ("latein", "Latein"), ("griechisch", "Griechisch"), ("kyrillisch", "Kyrillisch"),
          ("ziffern", "Ziffern"), ("rahmen", "Rahmen"), ("symbole", "Symbole")]

FEATURES = [
    ("ss08", "Null mit quadratischem Punkt statt Schrägstrich", "0x00FF 1000"),
    ("ss01", "Bindestrich und Stern tiefer, auf Höhe der Kleinbuchstaben", "a-b *ptr"),
    ("ss02", "Einstöckiges a, geschwungenes β", "data β"),
    ("ss03", "Einstöckiges g, geschwungenes θ, serbisches б", "logging θ"),
    ("ss04", "l mit geschwungenem Fuß", "lille"),
    ("ss05", "Samisches Ŋ, offenes φ", "Ŋ φ"),
    ("ss06", "Dollarzeichen mit durchgehendem Strich", "$PATH $1"),
    ("ss07", "1 ohne Fuß", "v1.10 11:11"),
    ("ss10", "Code-Ligaturen: Pfeile und Vergleiche, jede in so vielen Zellen wie Zeichen", "a->b x=>y a!=b"),
    ("onum", "Mediävalziffern", "Version 2048"),
    ("frac", "Echte Brüche", "1/2 3/4 7/8"),
    ("sups", "Hochgestellt", "x2 m3"),
    ("case", "Satzzeichen für Versalien", "(HTTP)-[GET]"),
]
TESTER_FEATURES = ["ss08", "ss10", "ss01", "ss02", "ss03", "ss04", "ss06", "ss07", "onum", "case"]

TEXTS = {
    "code": ("const res = await fetch(`/api/v1/items?limit=${n}`);\n"
             "if (!res.ok) throw new Error(\"HTTP \" + res.status);\n"
             "for (const [i, x] of items.entries()) {\n"
             "  total += x.price * 1.19; // 0O 1lI |!\n}"),
    "de": "Zwölf Boxkämpfer jagen Viktor quer über den großen Sylter Deich. 0O 1lI |! {} [] () <> != == =>",
    "en": "The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.",
    "el": "Ξεσκεπάζω την ψυχοφθόρα βδελυγμία. Γαζέες καὶ μυρτιὲς δὲν θὰ βρῶ πιὰ στὸ χρυσαφὶ ξέφωτο.",
    "ru": "Съешь же ещё этих мягких французских булок, да выпей чаю. Широкая электрификация южных губерний.",
    "vi": "Tiếng Việt có dấu: Đường đến trường hôm nay thật đẹp và yên bình.",
    "afr": "Hausa: Ɓɓ Ɗɗ Ƙƙ Ƴƴ\nFula: Ɓɓ Ɗɗ Ŋŋ Ɲɲ Ƴƴ\nEwe: Ɛɛ Ɔɔ Ƒƒ Ʋʋ Ŋŋ Ɣɣ\nBambara: Ɛɛ Ɔɔ Ɲɲ Ŋŋ",
    "box": "┌──────────┬────────┐\n│ Dienst   │ Status │\n├──────────┼────────┤\n│ web      │ ● ok   │\n│ worker   │ ▲ warn │\n└──────────┴────────┘",
}
TEXT_LABELS = [("code", "Code"), ("de", "Deutsch"), ("en", "Englisch"), ("el", "Griechisch"),
               ("ru", "Russisch"), ("vi", "Vietnamesisch"), ("afr", "Westafrika"), ("box", "Rahmen")]

# Codebeispiele für die Editor-Ansicht (Hervorhebung über Klassen, CSP-tauglich)
SAMPLES = [
    ("ts", "server.ts", "typescript", """import { createServer } from "node:http";

// Antwortet auf /health mit Status und Laufzeit.
const started = Date.now();
const port = Number(process.env.PORT ?? 3000);

createServer((req, res) => {
  if (req.url !== "/health") {
    res.writeHead(404).end();
    return;
  }
  const uptime = (Date.now() - started) / 1000;
  res.writeHead(200, { "Content-Type": "application/json" });
  res.end(JSON.stringify({ ok: true, uptime, version: "0.1.0" }));
}).listen(port);"""),
    ("py", "stats.py", "python", """from dataclasses import dataclass
from statistics import mean


@dataclass
class Reading:
    sensor: str
    value: float  # in °C


def summary(rows: list[Reading]) -> dict[str, float]:
    \"\"\"Mittelwert, Minimum und Maximum je Sensor.\"\"\"
    out = {}
    for name in {r.sensor for r in rows}:
        v = [r.value for r in rows if r.sensor == name]
        out[name] = round(mean(v), 2)
    return out"""),
    ("sh", "deploy.sh", "shell", """#!/bin/sh
set -eu

# Bauen, prüfen, ausrollen
VERSION=$(cat VERSION)
URL=${URL:-https://example.org}
docker compose build --pull
docker compose up -d

for i in 1 2 3 4 5; do
  if wget -q -O /dev/null "$URL/health"; then
    echo "ok: $VERSION läuft"
    exit 0
  fi
  sleep 2
done
echo "Fehler: Healthcheck" >&2; exit 1"""),
]

KEYWORDS = {
    "typescript": r"import|from|const|let|if|return|new|throw|for|of|await|async|true|false|null|undefined",
    "python": r"from|import|class|def|return|for|in|if|not|and|or|None|True|False",
    "shell": r"set|if|then|fi|for|in|do|done|echo|exit|sleep",
}


def esc(s):
    return html.escape(s, quote=True)


def highlight(src, lang):
    """Sehr einfache Hervorhebung: Kommentare, Zeichenketten, Zahlen, Schlüsselwörter."""
    kw = KEYWORDS[lang]
    com = r"#[^\n]*" if lang in ("python", "shell") else r"//[^\n]*"
    tok = re.compile(
        rf'(?P<c>{com})|(?P<s>"""[\s\S]*?"""|"(?:\\.|[^"\\])*"|`[^`]*`|\'[^\'\n]*\')'
        rf'|(?P<n>\b\d+(?:\.\d+)?\b)|(?P<k>\b(?:{kw})\b)|(?P<f>\b[A-Za-z_]\w*(?=\())')
    out, pos = [], 0
    for m in tok.finditer(src):
        out.append(esc(src[pos:m.start()]))
        out.append(f'<span class="t-{m.lastgroup}">{esc(m.group(0))}</span>')
        pos = m.end()
    out.append(esc(src[pos:]))
    return "".join(out)


def terminal():
    """Terminal-Ausgabe mit Kastenzeichen, Breiten exakt gezählt."""
    W = 46
    def row(s):
        return "│ " + s.ljust(W - 4) + " │"
    def bar(frac, n=20):
        full = int(frac * n)
        return "█" * full + "░" * (n - full)
    lines = [
        "┌─ status " + "─" * (W - 11) + "┐",
        row(f"cpu   {bar(0.62)}  62 %"),
        row(f"mem   {bar(0.41)}  41 %"),
        row(f"disk  {bar(0.87)}  87 %"),
        "├" + "─" * (W - 2) + "┤",
        row("dienst        port    status      zeit"),
        row("web           8080    ● läuft     12d"),
        row("worker        —       ● läuft     12d"),
        row("cron          —       ▲ wartet    03:00"),
        "└" + "─" * (W - 2) + "┘",
        "",
        "$ tree -L 2 src",
        "src",
        "├── api",
        "│   ├── health.ts",
        "│   └── items.ts",
        "└── main.ts",
        "",
        "2 directories, 3 files",
    ]
    assert all(len(l) == W for l in lines[:10]), [len(l) for l in lines[:10]]
    return "\n".join(lines)


def md_inline(s):
    s = esc(s)
    s = re.sub(r"`([^`]+)`", r"<code>\1</code>", s)
    s = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", s)
    s = re.sub(r"\[([^\]]+)\]\((https?://[^)]+)\)",
               r'<a href="\2" target="_blank" rel="noopener noreferrer">\1</a>', s)
    return s


def md_to_html(text):
    out, in_list, para = [], False, []

    def flush():
        nonlocal para
        if para:
            out.append("<p>" + md_inline(" ".join(para)) + "</p>")
            para = []

    for line in text.splitlines():
        if line.startswith("# "):
            flush()
            continue
        if line.startswith("## ") or line.startswith("### "):
            flush()
            if in_list:
                out.append("</ul>"); in_list = False
            lvl = 3 if line.startswith("## ") else 4
            out.append(f"<h{lvl}>{md_inline(line.split(' ', 1)[1])}</h{lvl}>")
        elif line.startswith("- "):
            flush()
            if not in_list:
                out.append("<ul>"); in_list = True
            out.append(f"<li>{md_inline(line[2:])}</li>")
        elif not line.strip():
            flush()
            if in_list:
                out.append("</ul>"); in_list = False
        else:
            if in_list:
                out.append("</ul>"); in_list = False
            para.append(line.strip())
    flush()
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def block_of(cp):
    for a, z, name, grp in BLOCKS:
        if a <= cp <= z:
            return name, grp
    return "Weitere", "symbole"


def glyph_grid(font):
    cmap = font.getBestCmap()
    has_dotted = 0x25CC in cmap
    blocks = {}
    for cp in sorted(cmap):
        if cp < 0x20 or (0x7F <= cp < 0xA0):
            continue
        name, grp = block_of(cp)
        blocks.setdefault((name, grp), []).append(cp)
    parts = []
    for (name, grp), cps in blocks.items():
        cells = []
        for cp in cps:
            ch = chr(cp)
            uname = unicodedata.name(ch, "")
            if not uname and 0xE0A0 <= cp <= 0xE0D4:
                uname = "POWERLINE SYMBOL"
            cat = unicodedata.category(ch)
            shown = ch
            if cat.startswith("M"):
                shown = ("◌" if has_dotted else " ") + ch
            elif cat.startswith("Z") or cat == "Cf":
                shown = " "
            label = f"U+{cp:04X} {uname}".strip()
            cells.append(f'<button type="button" class="g" data-cp="{cp:04X}" data-n="{esc(uname)}" '
                         f'aria-label="{esc(label)}">{esc(shown)}</button>')
        parts.append(f'<section class="gblock" data-group="{grp}"><h3>{esc(name)} '
                     f'<span class="count">{len(cps)}</span></h3><div class="ggrid">{"".join(cells)}</div></section>')
    return "\n".join(parts), sum(1 for cp in cmap if cp >= 0x20 and not (0x7F <= cp < 0xA0))


def build_zip(dst):
    stem = f"{C.FILE_STEM}-{V}"
    with zipfile.ZipFile(dst, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for sub in ("variable", "otf", "ttf", "webfonts"):
            for p in sorted((C.DIST / sub).iterdir()):
                z.write(p, f"{stem}/{sub}/{p.name}")
        for name in ("LICENSE", "README.md", "CHANGELOG.md", "VERSION"):
            z.write(C.ROOT / name, f"{stem}/{name if name != 'LICENSE' else 'LICENSE.txt'}")


def human(n):
    return f"{n / 1024 / 1024:.1f} MB".replace(".", ",") if n > 1024 * 1024 else f"{round(n / 1024)} KB"


def page(title, body, desc):
    return f"""<!doctype html>
<html lang="de">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<base href="/">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<meta name="color-scheme" content="light dark">
<link rel="icon" href="assets/brand/favicon-64.png?v={V}" type="image/png">
<link rel="apple-touch-icon" href="assets/brand/apple-touch-icon.png?v={V}">
<link rel="preload" href="assets/fonts/Krypton-VF.woff2?v={V}" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="assets/krypton.css?v={V}">
</head>
<body>
<a class="skip" href="#inhalt">Zum Inhalt springen</a>
<header class="top">
  <div class="wrap top__inner">
    <a class="brand" href="/" aria-label="Krypton, Startseite">
      <img class="brand__logo" src="assets/brand/trfx-logo.svg?v={V}" alt="TRFX.DE" width="122" height="18">
      <span class="brand__name">Krypton</span>
    </a>
    <nav class="nav" aria-label="Hauptnavigation">
      <a href="/#tester">Tester</a><a href="/#code">Code</a><a href="/#gewichte">Gewichte</a>
      <a href="/#prinzip">Prinzip</a><a href="/#zeichen">Zeichen</a><a href="/#features">Features</a>
      <a href="/#download">Download</a><a href="/#aenderungen">Änderungen</a><a class="nav__gh" href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer" title="Krypton auf GitHub (Open Source)">{GH_ICON}GitHub</a>
    </nav>
    <span class="ver" title="Aktuelle Version">v{V}</span>
  </div>
</header>
<main id="inhalt">
{body}
</main>
<footer class="foot">
  <div class="wrap foot__inner">
    <p class="foot__copy">© <span data-year>{date.today().year}</span> TRFX.DE - Alle Rechte vorbehalten.</p>
    <ul class="foot__links">
      <li><a class="foot__gh" href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">{GH_ICON}Krypton auf GitHub</a></li>
      {"".join(f'<li><a href="{u}" target="_blank" rel="noopener noreferrer">{esc(t)}</a></li>' for t, u in FOOTER_LINKS)}
    </ul>
  </div>
</footer>
<script src="assets/krypton.js?v={V}" defer></script>
</body>
</html>
"""


def section(num, sid, title, lead, inner, cls=""):
    lead_html = f'<p class="lead">{lead}</p>' if lead else ""
    return f"""<section class="sec {cls}" id="{sid}" aria-labelledby="{sid}-t">
  <div class="wrap">
    <header class="sec__head"><span class="sec__num">{num}</span><h2 id="{sid}-t">{title}</h2>{lead_html}</header>
    {inner}
  </div>
</section>"""


STABLE_CSS = """/* Krypton {{V}} – https://krypton.trfx.de/ – SIL Open Font License 1.1
   Fester Link: liegt immer die neueste Version. Nur diese Datei einbinden. */
@font-face {
  font-family: "Krypton";
  src: url("Krypton-VF.woff2") format("woff2");
  font-weight: 200 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Krypton";
  src: url("Krypton-Italic-VF.woff2") format("woff2");
  font-weight: 200 900;
  font-style: italic;
  font-display: swap;
}
"""


def build():
    if OUT.exists():
        shutil.rmtree(OUT)
    for d in ("assets/fonts", "assets/brand", "downloads", "latest"):
        (OUT / d).mkdir(parents=True)

    web = C.DIST / "webfonts"
    shutil.copy(web / f"{C.FILE_STEM}[wght].woff2", OUT / "assets/fonts/Krypton-VF.woff2")
    shutil.copy(web / f"{C.FILE_STEM}-Italic[wght].woff2", OUT / "assets/fonts/Krypton-Italic-VF.woff2")
    # Fester Link: immer die neueste Version, Dateinamen ohne Version.
    shutil.copy(web / f"{C.FILE_STEM}[wght].woff2", OUT / "latest/Krypton-VF.woff2")
    shutil.copy(web / f"{C.FILE_STEM}-Italic[wght].woff2", OUT / "latest/Krypton-Italic-VF.woff2")
    (OUT / "latest/krypton.css").write_text(STABLE_CSS.replace("{{V}}", V))
    shutil.copy(STATIC / "brand" / "trfx-logo.svg", OUT / "assets/brand" / "trfx-logo.svg")
    fav = Image.open(STATIC / "brand/favicon.png").convert("RGBA")
    fav.resize((64, 64), Image.LANCZOS).save(OUT / "assets/brand/favicon-64.png", optimize=True)
    fav.resize((180, 180), Image.LANCZOS).save(OUT / "assets/brand/apple-touch-icon.png", optimize=True)
    zip_name = f"{C.FILE_STEM}-{V}.zip"
    build_zip(OUT / "downloads" / zip_name)
    shutil.copy(OUT / "downloads" / zip_name, OUT / "latest/Krypton-latest.zip")
    shutil.copy(C.ROOT / "LICENSE", OUT / "downloads/LICENSE.txt")
    for p in sorted((C.DIST / "variable").glob("*.ttf")) + sorted(web.glob("*[[]wght[]].woff2")):
        shutil.copy(p, OUT / "downloads" / p.name)
    for name in ("krypton.css", "krypton.js"):
        (OUT / "assets" / name).write_text((SITE / "src" / name).read_text().replace("{{V}}", V))

    font = TTFont(VF_UP)
    grid_html, n_chars = glyph_grid(font)
    n_glyphs = len(font.getGlyphOrder())
    sizes = {p.name: p.stat().st_size for p in (OUT / "downloads").iterdir()}
    fmt = lambda n: f"{n:,}".replace(",", ".")

    def dl(name):
        return "downloads/" + name.replace("[", "%5B").replace("]", "%5D")

    hero = f"""<section class="hero" aria-labelledby="hero-t">
  <div class="wrap">
    <p class="kicker">Eine Schrift von TRFX.DE · Version {V} · Open Font License</p>
    <h1 id="hero-t" class="hero__title">Krypton<span class="hero__cursor" aria-hidden="true">_</span></h1>
    <p class="hero__lead">Eine technische Monospace für Code, Terminals und Daten. Feste Breite, höhere x-Höhe, durchgestrichene Null und quadratische Punkte. Von ExtraLight bis Black.</p>
    <div class="hero__cta">
      <a class="btn btn--solid" href="{dl(zip_name)}" download>Herunterladen <span class="btn__meta">ZIP · {human(sizes[zip_name])}</span></a>
      <a class="btn" href="/#tester">Ausprobieren</a>
      <a class="btn btn--gh" href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">{GH_ICON}Auf GitHub <span class="btn__meta">Open Source</span></a>
    </div>
    <dl class="facts">
      <div><dt>Gewichte</dt><dd>200–900</dd></div>
      <div><dt>Stile</dt><dd>Aufrecht, Kursiv</dd></div>
      <div><dt>Zeichen</dt><dd>{fmt(n_chars)}</dd></div>
      <div><dt>Glyphen</dt><dd>{fmt(n_glyphs)}</dd></div>
      <div><dt>Zeichenbreite</dt><dd>0,6 em</dd></div>
    </dl>
  </div>
</section>"""

    feat_chips = "".join(
        f'<label class="chip"><input type="checkbox" data-feature="{t}"><span>{t}</span></label>'
        for t in TESTER_FEATURES)
    text_opts = "".join(f'<option value="{k}">{esc(l)}</option>' for k, l in TEXT_LABELS)
    tester = section("01", "tester", "Tester", "Text anklicken und eigenen Text schreiben.", f"""
<div class="tester" data-texts='{esc(json.dumps(TEXTS, ensure_ascii=False))}'>
  <div class="tester__controls">
    <label class="ctl"><span class="ctl__l">Gewicht <output data-out="wght">400</output></span>
      <input type="range" min="200" max="900" step="1" value="400" data-ctl="wght"></label>
    <label class="ctl"><span class="ctl__l">Größe <span><output data-out="size">32</output> px</span></span>
      <input type="range" min="10" max="160" step="1" value="32" data-ctl="size"></label>
    <label class="ctl"><span class="ctl__l">Zeilenabstand <output data-out="lh">1,40</output></span>
      <input type="range" min="100" max="200" step="5" value="140" data-ctl="lh"></label>
    <label class="ctl ctl--inline"><input type="checkbox" data-ctl="italic"> Kursiv</label>
    <label class="ctl"><span class="ctl__l">Text</span>
      <select data-ctl="text">{text_opts}</select></label>
    <fieldset class="chips"><legend>OpenType-Features</legend>{feat_chips}</fieldset>
  </div>
  <div class="tester__stage">
    <div class="tester__text" contenteditable="true" spellcheck="false" role="textbox" aria-multiline="true" aria-label="Testtext">{esc(TEXTS["code"])}</div>
  </div>
</div>""")

    tabs = "".join(f'<button type="button" class="tab{" is-on" if i == 0 else ""}" data-tab="{k}" '
                   f'aria-pressed="{"true" if i == 0 else "false"}">{esc(f)}</button>'
                   for i, (k, f, _, _) in enumerate(SAMPLES))
    panes = "".join(
        f'<pre class="ed__pane" data-pane="{k}" tabindex="0" aria-label="Beispiel {k}"{"" if i == 0 else " hidden"}><code>'
        + "".join(f'<span class="ln">{highlight(l, lang) or " "}</span>' for l in src.split("\n"))
        + "</code></pre>"
        for i, (k, _, lang, src) in enumerate(SAMPLES))
    code = section("02", "code", "Code", "So sieht Krypton im Editor und im Terminal aus.", f"""
<div class="codegrid">
  <div class="ed">
    <div class="ed__bar"><div class="tabs" role="group" aria-label="Beispiel wählen">{tabs}</div>
      <label class="ctl ctl--inline ed__w"><input type="range" min="200" max="900" value="400" data-ed-wght aria-label="Gewicht im Editor"> <output data-out="edwght">400</output></label></div>
    {panes}
  </div>
  <div class="term">
    <div class="term__bar" aria-hidden="true"><span></span><span></span><span></span></div>
    <pre tabindex="0" aria-label="Terminal-Ausgabe mit Rahmen- und Blockzeichen">{esc(terminal())}</pre>
  </div>
</div>""")

    rows = "".join(
        f'<li class="wf__row w{w}"><span class="wf__meta"><b>{w}</b> {n}</span>'
        f'<span class="wf__text" contenteditable="true" spellcheck="false">fn main() {{ let x = 0x2A; }}</span></li>'
        for w, n in WEIGHTS)
    para = ("Eine Monospace muss bei 13 Pixeln im Editor genauso funktionieren wie groß auf einer Folie. "
            "Krypton hat eine hohe x-Höhe, offene Punzen und klar getrennte Formen für 0 und O, 1, l und I.")
    weights = section("03", "gewichte", "Gewichte",
                      "Acht Schnitte, stufenlos als Variable Font, jeweils aufrecht und kursiv.", f"""
<div class="wf-tools"><label class="ctl ctl--inline"><input type="checkbox" data-wf-italic> Kursiv</label></div>
<ul class="wf">{rows}</ul>
<div class="legib">
  <article class="legib__col w300"><h3>Light 300</h3><p>{esc(para)}</p></article>
  <article class="legib__col w400"><h3>Regular 400</h3><p>{esc(para)}</p></article>
  <article class="legib__col w700"><h3>Bold 700</h3><p>{esc(para)}</p></article>
</div>""")

    principle = section("04", "prinzip", "Prinzip", "", f"""
<div class="prin">
  <div class="prin__show" aria-label="Leicht verwechselbare Zeichen">
    <span>0O</span><span>1lI|</span><span>rn m</span><span>5S 2Z</span><span>.,:;</span><span>{{}}[]()</span>
  </div>
  <ul class="prin__list">
    <li><h3>Höhere x-Höhe</h3><p>Kleinbuchstaben sind 6 % höher als bei Source Code Pro. Code bleibt auch in kleinen Größen gut lesbar. Oberlängen und Akzente rücken mit und werden nicht gestaucht.</p></li>
    <li><h3>Offene Bögen</h3><p>Die Rundungen von Source Code Pro bleiben unverändert: offen, gleichmäßig im Strich und ruhig im Grauwert, auch in fetten Schnitten.</p></li>
    <li><h3>Quadratische Punkte</h3><p>i, j, Umlaute und alle Satzzeichen haben quadratische Punkte. Punkt, Komma, Doppelpunkt und Semikolon sind dadurch klar unterscheidbar.</p></li>
    <li><h3>Durchgestrichene Null</h3><p>Die 0 ist durchgestrichen und kann nicht mit O verwechselt werden. Wer die Null mit Punkt lieber mag, schaltet sie mit <code>ss08</code> ein, dann auch mit quadratischem Punkt.</p></li>
    <li><h3>Das l mit Serifen</h3><p>Das l hat oben einen Anschlag und unten einen durchgehenden Fuß. 1, l, I und | lassen sich so auf einen Blick unterscheiden.</p></li>
    <li><h3>Feste Breite</h3><p>Jedes Zeichen ist 0,6 em breit, Akzente setzen sich ohne eigene Breite darüber. Spalten, Tabellen und Rahmen stehen exakt untereinander.</p></li>
    <li><h3>Herkunft</h3><p>Basis ist Source Code Pro von Adobe, unter der Open Font License. Das l mit Serifen und die fast quadratischen Punkte orientieren sich an IBM Plex Mono.</p></li>
  </ul>
</div>""")

    group_btns = "".join(f'<button type="button" class="seg__b{" is-on" if k == "alle" else ""}" data-filter="{k}" '
                         f'aria-pressed="{"true" if k == "alle" else "false"}">{esc(l)}</button>'
                         for k, l in GROUPS)
    glyphs = section("05", "zeichen", "Zeichen",
                     f"{fmt(n_chars)} Zeichen. Klick auf ein Zeichen kopiert es.", f"""
<div class="gtools"><div class="seg" role="group" aria-label="Schriftsystem filtern">{group_btns}</div>
  <label class="ctl ctl--inline"><input type="range" min="200" max="900" value="400" data-g-wght aria-label="Gewicht der Zeichenübersicht"> <output data-out="gwght">400</output></label></div>
<div class="gwrap">
  <div class="ginfo" aria-live="polite"><div class="ginfo__ch" data-ginfo-ch>@</div><p class="ginfo__cp" data-ginfo-cp>U+0040</p><p class="ginfo__n" data-ginfo-n>Zeichen auswählen</p></div>
  <div class="gblocks">{grid_html}</div>
</div>""")

    feat_rows = "".join(
        f'<tr><th scope="row"><code>{t}</code></th><td>{esc(d)}</td>'
        f'<td class="fx">{esc(s)}</td><td class="fx ff-{t}">{esc(s)}</td></tr>'
        for t, d, s in FEATURES)
    features = section("06", "features", "Features", "Jeweils ohne und mit Feature.", f"""
<div class="tablewrap" tabindex="0" role="region" aria-label="Feature-Tabelle"><table class="ftable"><thead><tr><th scope="col">Tag</th><th scope="col">Wirkung</th><th scope="col">Aus</th><th scope="col">An</th></tr></thead>
<tbody>{feat_rows}</tbody></table></div>
<p class="fnote">Die Code-Ligaturen <code>-&gt; &lt;- &lt;-&gt; =&gt; == === != !==</code> sind standardmäßig aus. In VS Code schaltet <code>"editor.fontLigatures": "'ss10'"</code> sie ein, im Web <code>font-feature-settings: "ss10"</code>. Längere Folgen wie <code>--&gt;</code> oder <code>&lt;=&gt;</code> und Ausdrücke wie <code>a&lt;-1</code> bleiben unverändert.</p>""")

    css_snip = """<link rel="stylesheet" href="https://krypton.trfx.de/latest/krypton.css">

<style>
  code, pre, kbd, samp { font-family: "Krypton", ui-monospace, monospace; }
</style>"""
    css_self = """@font-face {
  font-family: "Krypton";
  src: url("/fonts/Krypton-VF.woff2") format("woff2");
  font-weight: 200 900;
  font-style: normal;
  font-display: swap;
}
@font-face {
  font-family: "Krypton";
  src: url("/fonts/Krypton-Italic-VF.woff2") format("woff2");
  font-weight: 200 900;
  font-style: italic;
  font-display: swap;
}
code, pre, kbd, samp { font-family: "Krypton", ui-monospace, monospace; }"""
    fetch_snip = """# Neueste Version holen und selbst hosten
mkdir -p fonts && cd fonts
curl -fsSLO https://krypton.trfx.de/latest/Krypton-VF.woff2
curl -fsSLO https://krypton.trfx.de/latest/Krypton-Italic-VF.woff2
curl -fsS https://krypton.trfx.de/latest/version.json   # welche Version ist das?"""
    vscode = """{
  "editor.fontFamily": "Krypton, monospace",
  "editor.fontSize": 14,
  "editor.lineHeight": 1.5,
  "terminal.integrated.fontFamily": "Krypton"
}"""
    files = [
        (f"{C.FILE_STEM}[wght].woff2", "Variable Font, aufrecht, Web"),
        (f"{C.FILE_STEM}-Italic[wght].woff2", "Variable Font, kursiv, Web"),
        (f"{C.FILE_STEM}[wght].ttf", "Variable Font, aufrecht, Desktop"),
        (f"{C.FILE_STEM}-Italic[wght].ttf", "Variable Font, kursiv, Desktop"),
    ]
    file_rows = "".join(
        f'<li><a href="{dl(n)}" download><span class="dl__n">{esc(n)}</span><span class="dl__d">{esc(d)}</span>'
        f'<span class="dl__s">{human(sizes[n])}</span></a></li>' for n, d in files)
    download = section("07", "download", "Download",
                       "Frei nutzbar unter der SIL Open Font License 1.1, auch kommerziell.", f"""
<div class="dl">
  <a class="dl__main" href="{dl(zip_name)}" download>
    <span class="dl__title">Komplettpaket {V}</span>
    <span class="dl__sub">Variable Fonts, 16 OTF, 16 TTF (gehintet), WOFF2, Lizenz, Änderungsprotokoll</span>
    <span class="dl__size">ZIP · {human(sizes[zip_name])}</span>
  </a>
  <ul class="dl__files">{file_rows}</ul>
</div>
<div class="embed">
<h3>Einbinden: fester Link</h3>
<p>Apps binden Krypton über <a href="latest/krypton.css"><code>https://krypton.trfx.de/latest/krypton.css</code></a> ein. Unter diesem Link und unter den gleichen Dateinamen im Ordner <code>/latest/</code> liegt immer die neueste Version. Wenn eine neue Schrift erscheint, muss keine App angepasst werden. Dort liegen auch <code>Krypton-latest.zip</code> (komplettes Paket) und <code>version.json</code> (aktuelle Version). Die Adressen antworten mit <code>Cache-Control: no-cache</code> und erlauben die Einbindung von fremden Seiten (CORS). Browser fragen kurz per ETag nach und laden nur bei einer neuen Version neu.</p>
<p><strong>Fallback:</strong> Ist der Link nicht erreichbar oder darf die App keine fremden Quellen laden (strenge CSP, Offline, Datenschutz), lädt sie die neueste Version selbst herunter und liefert sie von der eigenen Domain aus. Die Version steht in <a href="latest/version.json"><code>/latest/version.json</code></a>, daran lässt sich erkennen, ob die lokale Kopie noch aktuell ist.</p>
</div>
<div class="snips">
  <div class="code"><div class="code__bar"><span>HTML · fester Link (empfohlen)</span><button type="button" class="code__copy" data-copy="#css-snippet">Kopieren</button></div>
  <pre id="css-snippet" tabindex="0"><code>{esc(css_snip)}</code></pre></div>
  <div class="code"><div class="code__bar"><span>Shell · Fallback: neueste Version holen</span><button type="button" class="code__copy" data-copy="#fetch-snippet">Kopieren</button></div>
  <pre id="fetch-snippet" tabindex="0"><code>{esc(fetch_snip)}</code></pre></div>
  <div class="code"><div class="code__bar"><span>CSS · Fallback: selbst gehostet</span><button type="button" class="code__copy" data-copy="#css-self-snippet">Kopieren</button></div>
  <pre id="css-self-snippet" tabindex="0"><code>{esc(css_self)}</code></pre></div>
  <div class="code"><div class="code__bar"><span>VS Code · settings.json</span><button type="button" class="code__copy" data-copy="#vscode-snippet">Kopieren</button></div>
  <pre id="vscode-snippet" tabindex="0"><code>{esc(vscode)}</code></pre></div>
</div>
<div class="oss"><h3>{GH_ICON}Open Source auf GitHub</h3>
<p>Quellcode, Build-Skripte und Schriftquellen liegen öffentlich auf GitHub.</p>
<ul class="oss__links">
<li><a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">Repository</a></li>
<li><a href="{GITHUB_URL}/issues" target="_blank" rel="noopener noreferrer">Issues</a></li>
<li><a href="{GITHUB_URL}/releases" target="_blank" rel="noopener noreferrer">Releases</a></li>
<li><a href="{GITHUB_URL}/blob/main/LICENSE" target="_blank" rel="noopener noreferrer">Lizenz im Repository</a></li>
</ul></div>
<div class="license"><h3>Lizenz</h3>
<p>Krypton steht unter der <a href="downloads/LICENSE.txt">SIL Open Font License 1.1</a> (Quellcode auf <a href="{GITHUB_URL}" target="_blank" rel="noopener noreferrer">GitHub</a>). Die Schrift darf frei benutzt, eingebettet, weitergegeben und verändert werden, auch kommerziell. Nur der Verkauf der Schriftdateien allein ist nicht erlaubt. Veränderte Fassungen dürfen nicht „Krypton“ heißen (Reserved Font Name). Krypton baut auf Source Code Pro (© Adobe) auf, ebenfalls unter der Open Font License.</p></div>""")

    changelog = section("08", "aenderungen", "Änderungen", "",
                        f'<div class="log">{md_to_html((C.ROOT / "CHANGELOG.md").read_text())}</div>')

    body = "\n".join([hero, tester, code, weights, principle, glyphs, features, download, changelog])
    desc = ("Krypton: technische Monospace für Code und Terminals. Gewichte 200 bis 900, aufrecht und kursiv, "
            f"{fmt(n_chars)} Zeichen. Frei unter der Open Font License.")
    (OUT / "index.html").write_text(page(f"Krypton – Monospace {V}", body, desc), encoding="utf-8")

    nf = """<section class="hero hero--404"><div class="wrap">
<p class="kicker">Fehler 404</p><h1 class="hero__title">Nicht gefunden<span class="hero__cursor" aria-hidden="true">_</span></h1>
<p class="hero__lead">Diese Seite gibt es nicht. Zur <a href="/">Startseite</a>.</p></div></section>"""
    (OUT / "404.html").write_text(page("Nicht gefunden – Krypton", nf, "Seite nicht gefunden."), encoding="utf-8")
    (OUT / "robots.txt").write_text("User-agent: *\nAllow: /\n")
    vj = json.dumps(
        {"name": "Krypton", "version": V, "characters": n_chars, "glyphs": n_glyphs,
         "license": "OFL-1.1", "repository": GITHUB_URL, "download": "/" + dl(zip_name)}, ensure_ascii=False, indent=1) + "\n"
    (OUT / "version.json").write_text(vj)
    (OUT / "latest/version.json").write_text(vj)
    total = sum(p.stat().st_size for p in OUT.rglob("*") if p.is_file())
    print(f"site/dist: {sum(1 for p in OUT.rglob('*') if p.is_file())} Dateien, {human(total)}; "
          f"{n_chars} Zeichen, {n_glyphs} Glyphen, ZIP {human(sizes[zip_name])}")


if __name__ == "__main__":
    build()
