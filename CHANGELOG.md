# Änderungsprotokoll – Krypton

## [0.3.0] – 2026-11-15

### Neu
- **Code-Ligaturen**, standardmäßig aus, einschaltbar mit `ss10`: `->` `<-` `<->` `=>` `==` `===` `!=` `!==`.
  - Jede Ligatur belegt so viele Zellen wie Zeichen, Spalten und Cursorpositionen bleiben gleich.
  - Längere Folgen wie `-->`, `==>`, `<=>` oder `====` und Ausdrücke wie `a<-1` bleiben unverändert.
  - Die Ligaturen greifen auch zusammen mit `ss01` (tiefer Bindestrich).
  - In VS Code: `"editor.fontLigatures": "'ss10'"`.
- **Kursives Kyrillisch:** ц, ш, щ und џ haben jetzt echte Kursivformen, wie bei IBM Plex Mono Italic:
  - ц ist ein u mit Unterlänge, ш die Form des ɯ, щ ein ш mit Unterlänge.
  - џ ist ein u mit Unterlänge in der Mitte.

### Geändert
- **Rundungen wie Source Code Pro:** Die superelliptisch gestrafften Bögen aus 0.1.0 sind entfernt. Sie machten Bögen an den Schultern dick: In fetten Schnitten wirkten o, p und n dunkler als K, y und t, und das r bekam einen klobigen Bogen. Außerdem kamen sie Brom zu nahe. Krypton hat jetzt die offenen, gleichmäßigen Bögen von Source Code Pro.

### Korrigiert
- њ: Zwei Konturen teilten sich eine Kante (aus Source Code Pro). Manche Rasterizer zeigen dort eine feine Linie. Die Konturen überlappen jetzt flächig.

### Geprüft und bewusst so gelassen
- **Griechisch in der Kursive:** Jeder Kleinbuchstabe wurde mit seinem lateinischen Verwandten verglichen (μ/u, η/n, ι/ı, ν/v, ο/o, ρ/p, τ/t, χ/x) in 200, 400 und 900. Winkel, x-Höhe und Strichführung stimmen überein, eigene Kursivformen sind nicht nötig.
- **в, ъ, ы, ь in der Kursive** bleiben schräggestellte Grundformen. Für die runden Kursivformen wie bei Plex gibt es keine kursive Grundform, aus der sie sich ableiten ließen. Sie müssten von Hand gezeichnet werden.
- **Rahmenzeichen** bleiben 1,4 em hoch und schließen bis Zeilenhöhe 1,4 lückenlos an. Höhere Zeichen würden bei der eingebauten Zeilenhöhe in die Nachbarzeilen ragen: Farbige Blöcke würden dort überdecken, und unter Windows würde der Zeilenabstand mancher Programme wachsen. Viele Terminals, darunter VS Code, Windows Terminal, kitty und WezTerm, zeichnen diese Zeichen ohnehin selbst passend zur Zelle.

## [0.2.0] – 2026-11-15

### Neu
- **12 Zeichen mit Haken und Schwanz**, neu gezeichnet und in allen Gewichten interpolierbar, aufrecht und kursiv:
  - Großformen zu vorhandenen Kleinbuchstaben: Ɓ Ɦ Ɲ Ɽ Ʀ Ʈ Ʝ.
  - Für westafrikanische Sprachen: Ƙ ƙ Ƴ ƴ Ƒ.
  - Damit sind Hausa, Fula, Bambara und Ewe vollständig abgedeckt. Zu jedem Kleinbuchstaben gibt es jetzt auch die Großform.
- Zeichensatz: 1.367 Zeichen.

### Hinweis
- Bei Ƴ und ƴ ist der rechte Arm etwas steiler als bei Y und y, damit der Haken in der Zelle bleibt.

## [0.1.0] – 2026-11-15

Erste Version.

### Neu
- Familie **Krypton**: Monospace mit Gewichtsachse `wght` von 200 (ExtraLight) bis 900 (Black), aufrecht und kursiv. Alle Zeichen sind 600 Einheiten breit (0,6 em). Kombinierende Akzente haben keine eigene Breite.
- Formate: Variable Fonts (TTF), 16 statische Schnitte als OTF und TTF, WOFF2 für das Web. Die statischen TTF sind gehintet (ttfautohint). Blockelemente und Powerline-Zeichen sind davon ausgenommen, damit sie die Zelle exakt füllen. Blockelemente ragen minimal (0,012 em) über die Zelle hinaus und schließen auch im Browser ohne Fugen aneinander.
- **Höhere x-Höhe:** Kleinbuchstaben sind 6 % höher als bei Source Code Pro (515 statt 486 Einheiten im Regular). Oberlängen, i-Punkte und Akzente rücken mit und werden nicht gestaucht.
- **Superelliptische Rundungen:** Bögen sind zur Ecke hin gestrafft, wie bei IBM Plex Mono. Punzen etwas stärker als Außenformen, damit sie offen bleiben.
- **Quadratische Punkte:**
  - Betroffen sind i, j, Umlaute, Punkt, Doppelpunkt, Semikolon, Ausrufe- und Fragezeichen, Auslassungspunkte, der Mittelpunkt und der Punkt der Null-Variante (`ss08`). Sie sind Quadrate gleicher Fläche statt Ellipsen.
  - Der untere Punkt steht genau auf der Grundlinie, der obere Punkt von Doppelpunkt und Semikolon schließt genau mit der x-Höhe ab.
- **Durchgestrichene Null** als Standard, aufrecht und kursiv, auch bei Mediävalziffern (`onum`) und `case`. Die Null mit quadratischem Punkt gibt es über `ss08` (oder `cv12`). Das Feature `zero` entfällt, weil die durchgestrichene Null bereits Standard ist.
- **l mit Serifen** als Standard im Aufrechten: oben ein Anschlag, unten ein durchgehender Fuß. Damit unterscheiden sich l, 1, I und | auf einen Blick. Das l mit geschwungenem Fuß gibt es über `ss04`/`cv04`.
- **Griechisch und Kyrillisch in der Kursive:** Kyrillische Buchstaben bekommen echte Kursivformen, wie bei IBM Plex Mono Italic: а, е, и → u, п → n, т → m, г als gespiegeltes s, д mit Schleife (∂-Form) und weitere. Die übrigen griechischen und kyrillischen Zeichen sind schräggestellte Grundformen. Die Sprachregeln (`locl`: serbisches б, griechische und kyrillische Akzentformen; `case`) gelten aufrecht und kursiv.
- **Zusätzliche Großbuchstaben** zu vorhandenen Kleinbuchstaben (21 Zeichen, die Source Code Pro fehlen): Ɔ Ɛ Ɯ Ʊ Ɖ Ɪ Ɵ Ʃ Ʌ Ϝ Ɨ Ʉ Ɣ Ʒ Ʋ Ɥ Ɬ Ϗ Ϙ Ϛ Ϡ.
- **Akzente:**
  - Kombinierende Akzente lassen sich auch auf bereits akzentuierten Buchstaben stapeln (ä + ◌̈, ọ + ◌́ …), in allen Gewichten variabel (`mark`, `mkmk`).
  - Akzente halten einen Mindestabstand zur Grundform. Bei vietnamesischen Buchstaben mit Horn (Ỡ ỡ Ớ) berühren sie sich in Black nicht mehr.
- **Zeilenhöhe** 1,257 auf allen Systemen gleich (hhea = typo, USE_TYPO_METRICS). Die Win-Metriken decken alle Zeichen ab, unter Windows wird nichts abgeschnitten.
- Zeichensatz: 1.355 Zeichen. Latein erweitert (inklusive Vietnamesisch), Griechisch, Kyrillisch, IPA, Rahmen- und Blockelemente, Powerline-Symbole, Pfeile, Mathematik.
- Features: `ss01`–`ss08`, Zeichenvarianten (`cv01`, `cv02`, `cv04`, `cv06`–`cv12`, `cv14`–`cv17`), `case`, `frac`, `sups`, `subs`, `numr`, `dnom`, `sinf`, `ordn`, `onum`, `locl`.

### Herkunft
- Basis ist **Source Code Pro** (Adobe, OFL 1.1). Der Name „Source“ ist dort reservierter Schriftname und kommt in Krypton nicht vor.
- Gestaltungsvorbilder: **IBM Plex Mono** (gestraffte Bögen, l mit Serifen, höhere x-Höhe) und **Brom** (quadratische Punkte). Outlines aus Plex Mono sind nicht enthalten.

### Bekannte Einschränkungen
- Griechisch in der Kursive und die übrigen kyrillischen Buchstaben sind schräggestellte Grundformen, keine eigens gezeichneten Kursivformen.
- Zu 7 seltenen Kleinbuchstaben fehlt noch die Großform, wie bei Source Code Pro: ɓ ɦ ɲ ɽ ʀ ʈ ʝ (Ɓ Ɦ Ɲ Ɽ Ʀ Ʈ Ʝ). Sie lassen sich nicht aus vorhandenen Formen ableiten und müssen gezeichnet werden. Großschreibung dieser Zeichen fällt bis dahin auf eine andere Schrift zurück.
- Ligaturen für Code (`->`, `!=` …) gibt es nicht. Jedes Zeichen bleibt sichtbar einzeln, wie bei Source Code Pro und IBM Plex Mono.
- Rahmenzeichen reichen von −0,4 bis 1,0 em und schließen bei einer Zeilenhöhe bis 1,4 lückenlos an. Bei größerem Zeilenabstand entstehen Lücken zwischen den Zeilen.
