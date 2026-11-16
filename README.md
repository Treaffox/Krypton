# Krypton

> **THIS FONT IS VIBE CODED USING CLAUDE CODE**

Technische Monospace für Code, Terminals und Daten. Sachlich und ruhig, mit
höherer x-Höhe, offenen Bögen, quadratischen Punkten und durchgestrichener Null.
Gewichte von 200 bis 900, aufrecht und kursiv. Website und Testseite:
https://krypton.trfx.de

Version und Änderungen: `VERSION`, `CHANGELOG.md`. Lizenz: SIL Open Font
License 1.1 (`LICENSE`), Reserved Font Name „Krypton“.

## Dateien

Im Download-Paket liegen die Ordner direkt im Hauptverzeichnis, im
Quell-Repository unter `fonts/`.

| Ordner | Inhalt |
|---|---|
| `variable/` | `Krypton[wght].ttf`, `Krypton-Italic[wght].ttf`: eine Datei je Stil, alle Gewichte |
| `otf/` | 16 statische Schnitte (Desktop, Druck) |
| `ttf/` | 16 statische Schnitte, gehintet (Windows, kleine Größen) |
| `webfonts/` | WOFF2 der Variable Fonts und der statischen Schnitte |

## Im Web einbinden

**Empfohlen: fester Link.** Unter `https://krypton.trfx.de/latest/krypton.css` liegt
immer die neueste Version, ebenso die Schriftdateien im Ordner `/latest/` (gleiche
Namen, ohne Versionsnummer). Wird Krypton aktualisiert, muss keine App geändert
werden. Dazu `Krypton-latest.zip` und `version.json`. Die Adressen antworten mit
`Cache-Control: no-cache` (Browser fragen per ETag nach und laden nur bei neuer
Version neu) und erlauben fremde Seiten (CORS).

```html
<link rel="stylesheet" href="https://krypton.trfx.de/latest/krypton.css">
<style>code, pre, kbd, samp { font-family: "Krypton", ui-monospace, monospace; }</style>
```

**Fallback: selbst hosten.** Ist der Link nicht erreichbar oder erlaubt die App keine
fremden Quellen, lädt sie die neueste Version selbst herunter und liefert sie von
der eigenen Domain aus. `https://krypton.trfx.de/latest/version.json` nennt die aktuelle
Version, daran erkennt die App, ob ihre Kopie noch aktuell ist.

```sh
curl -fsSLO https://krypton.trfx.de/latest/Krypton-VF.woff2
curl -fsSLO https://krypton.trfx.de/latest/Krypton-Italic-VF.woff2
```

```css
@font-face {
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
code, pre, kbd, samp { font-family: "Krypton", ui-monospace, monospace; }
```

## Im Editor und Terminal

Nach der Installation der OTF- oder TTF-Dateien heißt die Schrift überall
„Krypton“, zum Beispiel in VS Code: `"editor.fontFamily": "Krypton"`.

Code-Ligaturen sind aus. Einschalten in VS Code mit
`"editor.fontLigatures": "'ss10'"`, in kitty mit `font_features Krypton-Regular +ss10`,
im Web mit `font-feature-settings: "ss10"`.

Die eingebaute Zeilenhöhe ist 1,257. Rahmen- und Blockzeichen (┌─┐ █ ░) reichen
von −0,4 bis 1,0 em und schließen bei einer Zeilenhöhe bis 1,4 lückenlos an.
Viele Terminals (VS Code, Windows Terminal, kitty, WezTerm) zeichnen diese
Zeichen selbst passend zur Zelle, dort gilt die Grenze nicht.

## OpenType-Features

| Feature | Wirkung |
|---|---|
| `ss01` | Bindestrich und Stern tiefer, auf Höhe der Kleinbuchstaben |
| `ss02` | einstöckiges a (kursiv: zweistöckiges a), geschwungenes β (aufrecht) |
| `ss03` | einstöckiges g, geschwungenes θ (aufrecht), serbisches б |
| `ss04` | l mit geschwungenem Fuß wie in Source Code Pro (aufrecht; kursiv ist das l immer so) |
| `ss05` | samisches Ŋ, offenes φ (aufrecht) |
| `ss06` | Dollarzeichen mit durchgehendem Strich |
| `ss07` | 1 ohne Fuß |
| `ss08` | Null mit quadratischem Punkt statt Schrägstrich (auch `cv12`) |
| `ss10` | Code-Ligaturen `->` `<-` `<->` `=>` `==` `===` `!=` `!==`, je Zeichen eine Zelle (standardmäßig aus) |
| `cv01` … `cv17` | dieselben Varianten einzeln schaltbar (nicht alle Nummern belegt) |
| `frac`, `sups`, `subs`, `numr`, `dnom`, `sinf`, `ordn`, `onum`, `case` | Brüche, hoch-/tiefgestellt, Ordinalzeichen, Mediävalziffern, Satzzeichen für Versalien |

## Selbst bauen

Im Quell-Repository. Die Quellen werden aus Source Code Pro abgeleitet
(`tools/prepare.py`) und mit fontmake gebaut. Gebraucht werden Python 3.12 und Git.

```sh
sh tools/fetch_upstream.sh           # Source Code Pro in dem Stand, auf dem Krypton aufbaut → upstream/scp
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python tools/build.py      # prepare + fontmake + Hinting + WOFF2 → dist/
.venv/bin/python tools/check.py      # Prüfungen
.venv/bin/python tools/ligtest.py    # Code-Ligaturen (HarfBuzz)
```

Die Gestaltungsparameter (x-Höhe, Metriken) stehen in
`tools/krypton/config.py`. Die Website entsteht mit `tools/site.py` in
`site/dist`. Ihre Browsertests in `site/scripts` brauchen Node.js und
`npm install` in `site/`.

## Herkunft und Dank

Krypton baut auf **Source Code Pro** von Paul D. Hunt / Adobe auf (OFL 1.1).
Vorbild für einzelne Formen (l mit Serifen, quadratische Punkte) war
**IBM Plex Mono** von Mike Abbink und Bold Monday. Outlines aus Plex Mono sind
nicht enthalten.
