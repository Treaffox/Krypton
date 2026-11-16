// Krypton – Browsertest der Website (Chromium und Firefox).
//   BASE=https://krypton.trfx.de node site/scripts/test-site.mjs [Screenshot-Ordner]
// Ohne BASE: http://localhost:$PORT (Standard 8080) mit Header X-Forwarded-Proto: https (Container lokal).
import { createRequire } from "node:module";
// Playwright aus node_modules neben dem Projekt (npm install) oder aus PLAYWRIGHT_DIR.
const require = createRequire(process.env.PLAYWRIGHT_DIR ? process.env.PLAYWRIGHT_DIR.replace(/\/?$/, "/") : import.meta.url);
const { chromium, firefox } = require("playwright");

// PORT=… prüft einen lokal laufenden Container, BASE=https://… die öffentliche Seite.
const BASE = process.env.BASE || `http://localhost:${process.env.PORT || 8080}`;
const SHOTS = process.argv[2] || "";
const local = !process.env.BASE;
let fails = 0, passes = 0;
const ok = (c, m) => { if (c) passes++; else { fails++; console.log("FEHLER:", m); } };

async function run(type, name) {
  const browser = await type.launch();
  for (const [w, h, mobile] of [[1280, 900, false], [390, 844, true], [320, 640, true]]) {
    const ctx = await browser.newContext({
      viewport: { width: w, height: h }, hasTouch: mobile && name === "chromium", isMobile: mobile && name === "chromium",
      extraHTTPHeaders: local ? { "X-Forwarded-Proto": "https" } : {},
    });
    const page = await ctx.newPage();
    const msgs = [];
    page.on("console", (m) => { if (["error", "warning"].includes(m.type())) msgs.push(m.text()); });
    page.on("pageerror", (e) => msgs.push("pageerror: " + e.message));
    const res = await page.goto(BASE + "/", { waitUntil: "networkidle" });
    const tag = `${name} ${w}px`;
    ok(res.status() === 200, `${tag}: Startseite ${res.status()}`);
    await page.evaluate(() => document.fonts.ready);
    const fontsOk = await page.evaluate(() => document.fonts.check('400 16px "Krypton"'));
    ok(fontsOk, `${tag}: Webfont nicht geladen`);
    const loaded = await page.evaluate(() => [...document.fonts].filter((f) => f.family.includes("Krypton") && f.status === "loaded").length);
    ok(loaded >= 1, `${tag}: keine Krypton-Fontdatei geladen (${loaded})`);
    const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
    ok(overflow <= 0, `${tag}: horizontaler Überlauf ${overflow}px`);
    // Monospace: schmale und breite Zeichen gleich breit
    const mono = await page.evaluate(() => {
      const m = (t) => { const s = document.createElement("span"); s.textContent = t; s.style.fontSize = "100px";
        s.style.whiteSpace = "pre"; document.body.appendChild(s); const w = s.getBoundingClientRect().width; s.remove(); return w; };
      return [m("iiiiiiiiii"), m("MMMMMMMMMM"), m("ääääääääää")];
    });
    ok(Math.abs(mono[0] - mono[1]) < 1 && Math.abs(mono[0] - mono[2]) < 1 && Math.abs(mono[0] - 600) < 2, `${tag}: nicht monospace (${mono.map((x) => x.toFixed(1))})`);
    // Alle Codeblöcke in Krypton (Browser setzen für pre sonst monospace)
    const preFonts = await page.$$eval("pre, code", (es) => es.map((e) => getComputedStyle(e).fontFamily));
    ok(preFonts.length > 3 && preFonts.every((f) => f.includes("Krypton")), `${tag}: pre/code nicht in Krypton (${[...new Set(preFonts)]})`);
    // Code-Ligaturen (ss10): gleiche Breite wie ohne, aber anders gezeichnet; ohne ss10 keine Ligatur
    const ligW = await page.evaluate(() => {
      const m = (feat) => { const s = document.createElement("span"); s.textContent = "a->b x=>y a!==b"; s.style.fontSize = "100px";
        s.style.whiteSpace = "pre"; s.style.fontFeatureSettings = feat; document.body.appendChild(s); const w = s.getBoundingClientRect().width; s.remove(); return w; };
      return [m("normal"), m('"ss10"')];
    });
    ok(Math.abs(ligW[0] - ligW[1]) < 1 && Math.abs(ligW[0] - 900) < 2, `${tag}: Ligaturen ändern die Breite (${ligW})`);
    const ligRow = page.locator("tr", { has: page.locator('code:text-is("ss10")') });
    ok(await ligRow.count() === 1, `${tag}: Feature-Zeile ss10 fehlt`);
    const [shotOff, shotOn] = [await ligRow.locator("td.fx").nth(0).screenshot(), await ligRow.locator("td.fx").nth(1).screenshot()];
    ok(!shotOff.equals(shotOn), `${tag}: ss10 zeichnet keine Ligatur`);
    ok(await page.locator('.chip [data-feature="ss10"]').count() === 1 && await page.locator(".fnote").count() === 1, `${tag}: ss10 im Tester oder Hinweis fehlt`);
    // Editor-Tabs
    await page.locator('.tab[data-tab="py"]').click();
    ok(await page.evaluate(() => !document.querySelector('[data-pane="py"]').hidden && document.querySelector('[data-pane="ts"]').hidden), `${tag}: Editor-Tab`);
    // Tester
    await page.locator('[data-ctl="wght"]').fill("900");
    const tw = await page.evaluate(() => getComputedStyle(document.querySelector(".tester__text")).fontWeight);
    ok(tw === "900", `${tag}: Tester-Gewicht ${tw}`);
    await page.locator('[data-ctl="italic"]').check();
    ok(await page.evaluate(() => getComputedStyle(document.querySelector(".tester__text")).fontStyle) === "italic", `${tag}: Kursiv im Tester`);
    await page.evaluate(() => document.fonts.ready);
    const itl = await page.evaluate(() => [...document.fonts].some((f) => f.family.includes("Krypton") && f.style === "italic" && f.status === "loaded"));
    ok(itl, `${tag}: kursive Schriftdatei nicht geladen`);
    await page.locator('.chip:has([data-feature="ss02"])').click();
    const ff = await page.evaluate(() => getComputedStyle(document.querySelector(".tester__text")).fontFeatureSettings);
    ok(ff.includes("ss02"), `${tag}: Feature ss02 nicht gesetzt (${ff})`);
    await page.selectOption('[data-ctl="text"]', "ru");
    ok((await page.locator(".tester__text").textContent()).startsWith("Съешь"), `${tag}: Textvorlage`);
    // Zeichen: Filter und Auswahl
    await page.locator('.seg__b[data-filter="griechisch"]').click();
    const vis = await page.evaluate(() => [...document.querySelectorAll(".gblock")].filter((b) => !b.hidden).map((b) => b.dataset.group));
    ok(vis.length > 0 && vis.every((g) => g === "griechisch"), `${tag}: Filter Griechisch (${vis})`);
    await page.locator('.seg__b[data-filter="alle"]').click();
    await page.locator('.g[data-cp="00DF"]').click();
    ok((await page.locator("[data-ginfo-cp]").textContent()) === "U+00DF", `${tag}: Zeicheninfo`);
    // Footer
    const links = await page.$$eval(".foot__links a", (as) => as.map((a) => [a.target, a.rel]));
    ok(links.length === 11 && links.every(([t, r]) => t === "_blank" && r.includes("noopener")), `${tag}: Footer-Links ${links.length}`);
    // Downloads erreichbar
    const hrefs = await page.$$eval('a[download]', (as) => [...new Set(as.map((a) => a.href))]);
    for (const h of hrefs) {
      const r = await ctx.request.get(h);
      ok(r.status() === 200 && Number(r.headers()["content-length"] || (await r.body()).length) > 1000, `${tag}: Download ${h} ${r.status()}`);
    }
    ok(msgs.length === 0, `${tag}: Konsole: ${msgs.join(" | ")}`);
    if (SHOTS) {
      await page.evaluate(() => window.scrollTo(0, 0));
      await page.screenshot({ path: `${SHOTS}/${name}-${w}.png`, fullPage: w !== 1280 ? false : false });
      for (const id of ["tester", "code", "gewichte", "prinzip", "zeichen", "download"]) {
        await page.locator("#" + id).scrollIntoViewIfNeeded();
        await page.evaluate((i) => document.getElementById(i).scrollIntoView(), id);
        await page.waitForTimeout(150);
        if (w === 1280 || id === "tester") await page.screenshot({ path: `${SHOTS}/${name}-${w}-${id}.png` });
      }
    }
    await ctx.close();
  }
  // 404
  const ctx = await browser.newContext({ extraHTTPHeaders: local ? { "X-Forwarded-Proto": "https" } : {} });
  const p = await ctx.newPage();
  const r = await p.goto(BASE + "/gibt/es/nicht", { waitUntil: "networkidle" });
  ok(r.status() === 404, `${name}: 404-Seite liefert ${r.status()}`);
  ok(await p.evaluate(() => getComputedStyle(document.body).fontFamily.includes("Krypton")), `${name}: 404 ohne CSS`);
  await browser.close();
}

// Fester Link /latest/: immer die neueste Version, CORS, no-cache mit ETag.
{
  const h = local ? { "X-Forwarded-Proto": "https", Origin: "https://fremd.example" } : { Origin: "https://fremd.example" };
  const get = (p) => fetch(BASE + p, { headers: h });
  const ver = await (await get("/latest/version.json")).json();
  const css = await get("/latest/krypton.css");
  const cssText = await css.text();
  ok(css.status === 200 && (css.headers.get("content-type") || "").startsWith("text/css"), "/latest/krypton.css: 200 und text/css");
  ok(cssText.includes(`Krypton ${ver.version}`), "/latest/krypton.css nennt die aktuelle Version");
  ok(/font-weight: 200 900/.test(cssText) && /font-style: italic/.test(cssText), "/latest/krypton.css: Variable Gewichte, aufrecht und kursiv");
  for (const f of ["Krypton-VF.woff2", "Krypton-Italic-VF.woff2"]) {
    ok(cssText.includes(`url("${f}")`), `/latest/krypton.css verweist auf ${f}`);
    const r = await get("/latest/" + f);
    const b = Buffer.from(await r.arrayBuffer());
    ok(r.status === 200 && b.subarray(0, 4).toString() === "wOF2", `/latest/${f}: 200 und WOFF2`);
    ok(r.headers.get("access-control-allow-origin") === "*", `/latest/${f}: CORS erlaubt fremde Seiten`);
    ok(/no-cache/.test(r.headers.get("cache-control") || "") && !!r.headers.get("etag"), `/latest/${f}: no-cache mit ETag`);
    const pinned = Buffer.from(await (await get("/assets/fonts/" + f)).arrayBuffer());
    ok(b.equals(pinned), `/latest/${f} gleicht der Schrift der Seite`);
  }
  ok((css.headers.get("access-control-allow-origin") || "") === "*", "/latest/krypton.css: CORS");
  const z = await get("/latest/Krypton-latest.zip");
  ok(z.status === 200 && Buffer.from(await z.arrayBuffer()).subarray(0, 2).toString() === "PK", "/latest/Krypton-latest.zip: 200 und ZIP");
  ok((await get("/latest/gibt-es-nicht.woff2")).status === 404, "/latest/ unbekannte Datei: 404");
}

await run(chromium, "chromium");
await run(firefox, "firefox");
console.log(`${passes} bestanden, ${fails} fehlgeschlagen`);
process.exit(fails ? 1 : 0);
